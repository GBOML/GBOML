from gboml.ast import *
from gboml.scope import *
from gboml.tools.tree_modifier import visit, visit_hier, modify_hier
from gboml.reserved_definitions import GBOML_RESERVED_DEFINITIONS

from graphlib import TopologicalSorter, CycleError
from typing import NamedTuple, Optional
import dataclasses

HierTypes = ObjectsWithScope|VarOrParamDefinition|ExpressionFunctionCall|ExpressionArrayCall|ExpressionDotCall|PathRoot
GenobjsOrGenattrs = GeneratedObjectsType|Array|FunctionConstraint|ExpressionFunctionCall

def _get_scope_from_hier(hier: list[HierTypes]) -> Scope:
    return next(hier_item.semantic.scope for hier_item in reversed(hier) if hier_item.semantic.scope is not None)

def _get_parent_from_hier(hier: list[HierTypes], _type: type[HierTypes]) -> HierTypes|None:
    return next((hier_item for hier_item in reversed(hier) if isinstance(hier_item, _type)), None)

def _add_dep(deps: dict[VarOrParamDefinition, set[VarOrParamDefinition]], hier: list[HierTypes], dep: Optional[Scope]) -> None:
    if dep is not None and isinstance(dep, VarOrParamDefScope) and (parent_def := _get_parent_from_hier(hier, VarOrParamDefinition)) is not None:
        if parent_def in deps:
            deps[parent_def].add(dep.ast)
        else:
            deps[parent_def] = {dep.ast}


def _get_scope_after_expr(elem: ExpressionDotCall|ExpressionFunctionCall|PathRoot, scope: Scope) -> Optional[Scope]:
    """ Returns the scope after looking for expression 'elem' or None if it is impossible to know (e.g. a().x); Raises an error if cannot find the scope. """

    names = []
    if not isinstance(child := elem, PathRoot):
        if isinstance(child, ExpressionDotCall):
            names.append(child.rhs)
        while isinstance(child := child.lhs, ExpressionDotCall):
            names.append(child.rhs)
        if not isinstance(child, PathRoot):
            return None  # cannot check existence

    try:
        scope = scope[child.name]  # at this time, child is sure to be PathRoot
        while names:
            if isinstance(scope, VarOrParamDefScope):
                raise KeyError
            scope = scope[names.pop()]
    except KeyError:
        raise RuntimeError(f"{elem} {elem.meta}: cannot be used in this scope")
    return scope


def _likeloop_to_baseloop(elem: LikeLoop, hier: list[HierTypes]) -> BaseLoop:
    if not isinstance(index_param_def := getattr(_get_scope_after_expr(elem.on, _get_scope_from_hier(hier)), 'ast', None), IndexingParameterDefinition):
        raise RuntimeError(f"{elem} {elem.meta}: {elem.on} is not an IndexingParameterDefinition")
    return BaseLoop(elem.child, elem.varid, index_param_def.value, elem.condition, meta=elem.meta, semantic=elem.semantic)


def _mark_implicit_loops(elem: ExpressionDotCall|PathRoot, hier: list[HierTypes|GenobjsOrGenattrs|ImplicitLoop], implicit_loops: dict[GenobjsOrGenattrs|ExpressionObj, set[ImplicitLoop]]) -> ExpressionDotCall|PathRoot:
    """ If an elem references is an IndexingParameterDefinition, mark a new ImplicitLoop in implicit_loops (key=future child of ImplicitLoop, val=ImplicitLoops) """
    if not isinstance(getattr(elem, 'lhs', elem), PathRoot):
        return elem  # if both elem and lhs are not PathRoot, cannot check anything

    if (parent := _get_parent_from_hier(hier, GenobjsOrGenattrs|ImplicitLoop)) is not None and isinstance(index_param_def := getattr(_get_scope_after_expr(elem, _get_scope_from_hier(hier)), 'ast', None), IndexingParameterDefinition):
        new_loop = ImplicitLoop(None, None, varid=index_param_def.name, on=index_param_def.value, meta=parent.meta)
        # do not add ImplicitLoop if already present in hier (could only be with varid='t' at this time)
        if any(isinstance(hier_item, ImplicitLoop) and hier_item.varid == new_loop.varid == 't' for hier_item in hier):
            return  # TODO throw error if the loop from hier does not have IndexParam as child?

        if parent in implicit_loops:
            implicit_loops[parent].add(new_loop)
        else:
            implicit_loops[parent] = {new_loop}

    return elem


def _add_implicit_loops(elem: GenobjsOrGenattrs|ExpressionObj, hier: list[HierTypes|GenobjsOrGenattrs|ImplicitLoop], implicit_loops: dict[GenobjsOrGenattrs|ExpressionObj, set[ImplicitLoop]]) -> GenobjsOrGenattrs|ExpressionObj:
    new_elem = elem
    for loop in implicit_loops.get(elem, []):
        match elem:
            case Array():
                print('arr')  # TODO, array and fcts need to know on which argument the ImplicitLoop(s) are
            case FunctionConstraint() | ExpressionFunctionCall():
                print('fct')
            case _:
                print('default')
        new_elem = dataclasses.replace(loop, child=new_elem)
    return new_elem


def _check_fct_use_and_def(elem: ExpressionDotCall|ExpressionFunctionCall|PathRoot, scope: Optional[Scope]) -> None:
    """ Compare function usage and definition """
    if not scope:
        return

    if isinstance(scope, ScopedFunctionDefinition) != isinstance(elem, ExpressionFunctionCall):
        raise RuntimeError(f"{elem} {elem.meta}: used as {'function' if isinstance(elem, ExpressionFunctionCall) else 'non-fonction'} "
                           f"but declared as {'function' if isinstance(scope, ScopedFunctionDefinition) else 'non-fonction'} {scope.ast.meta}!")
    elif isinstance(scope, ScopedFunctionDefinition) and isinstance(elem, ExpressionFunctionCall) and (
            not elem.operands or scope.ast not in GBOML_RESERVED_DEFINITIONS and all(not isinstance(arg, Loop) for arg in elem.operands) and len(elem.operands) != len(scope.ast.args)):
        raise RuntimeError(f"{elem} {elem.meta}: function call got {len(elem.operands)} arguments but declared with {len(scope.ast.args)} arguments at {scope.ast.meta}.")


def _check_var_or_param_scoping(elem: ExpressionDotCall|PathRoot, hier: list[HierTypes], deps: dict[VarOrParamDefinition, set[VarOrParamDefinition]]) -> None:
    """ Checks if elem is accessible in the current scope (if not, an error is raised), adds elem to its VarOrParamDefinition parent's dependencies """
    if isinstance(hier[-2], ExpressionFunctionCall|ExpressionDotCall) and hier[-2].lhs is elem:
        return

    _check_fct_use_and_def(elem, scope := _get_scope_after_expr(elem, _get_scope_from_hier(hier)))
    _add_dep(deps, hier, scope)


def _check_fct_scoping(elem: ExpressionFunctionCall, hier: list[HierTypes], deps: dict[VarOrParamDefinition, set[VarOrParamDefinition]]) -> None:

    _check_fct_use_and_def(elem, scope := _get_scope_after_expr(elem, _get_scope_from_hier(hier)))
    _add_dep(deps, hier, scope)


def _check_node_or_hyperedge_indices(elem: NodeDefinition|HyperEdgeDefinition, hier: list[HierTypes]) -> None:
    if not elem.indices:
        return
    scope = _get_scope_from_hier(hier)
    for index in elem.indices:
        try:
            scope[index]
        except KeyError:
            raise KeyError(f"{elem} {elem.meta} index {index} can not be used in this scope")


def _topo_sort(globalScope: GlobalScope, deps) -> tuple[VarOrParamDefScope]:
    """ Performs the topological sort for VarOrParamDefinition elements (if there's a circular dependency, an error is raised), and returns the sorted elements in a map """
    ts = TopologicalSorter()
    add_node = lambda definition: ts.add(definition, *deps.get(definition, frozenset()))
    visit(globalScope.ast, dict.fromkeys(VarOrParamDefinition.__args__, add_node))
    try:
        return tuple(ts.static_order())
    except CycleError as err:  # default error too long to print, so raise from None
        raise RuntimeError("Circular dependency found!", list(map(lambda dep: (dep.path_to_str(), dep.ast.meta), err.args[1]))) from None


def semantic_check(globalScope: GlobalScope) -> GlobalScope:
    # check if variables are in scope, and store deps
    deps: dict[VarOrParamDefinition, set[VarOrParamDefinition]] = {}
    visit_hier(globalScope.ast, set(HierTypes.__args__), {ExpressionFunctionCall: lambda elem,hier: _check_fct_scoping(elem, hier, deps)} | dict.fromkeys((ExpressionDotCall, PathRoot), lambda elem,hier: _check_var_or_param_scoping(elem, hier, deps)) | dict.fromkeys((NodeDefinition, HyperEdgeDefinition), _check_node_or_hyperedge_indices))

    sorted_varorparam_defs = _topo_sort(globalScope, deps)  # TODO propagate scalar values in the order of the returned list, and store which variables are arrays, then do 2nd pass to check for array declaration vs use (like _check_fct_use_and_def)
    del deps

    # add implicit loops in GBOMLGraph (and while we're at it, convert LikeLoops to BaseLoops)
    new_ast = modify_hier(globalScope.ast, set(HierTypes.__args__), {LikeLoop: _likeloop_to_baseloop})
    implicit_loops: dict[GenobjsOrGenattrs|ExpressionObj, set[ImplicitLoop]] = {}
    new_ast = modify_hier(new_ast, GeneratedObjects | {*HierTypes.__args__, ImplicitLoop, Array, FunctionConstraint, ExpressionFunctionCall},
                by_before=dict.fromkeys((ExpressionDotCall, PathRoot), lambda elem,hier: _mark_implicit_loops(elem, hier, implicit_loops)),
                by_after=dict.fromkeys(GenobjsOrGenattrs.__args__ + (ExpressionObj,), lambda elem,hier: _add_implicit_loops(elem, hier, implicit_loops)))
    return dataclasses.replace(globalScope, ast=new_ast)

# TODO list
#
# VarOrParam values propagation:
# using the list returned by the toposort, know which nodes don't do anything with iterable and propagate scalar value for these ones
# once done, do 2nd pass to check for array declaration vs use (like _check_fct_use_and_def)
#
# Documentation in folder docs (for readthedocs.io)
# don't forget to add 'parent', say that adding Function(Constraint) needs to be done in reserved_keywords.py
#
# SOS1 and SOS2 functions are FunctionConstraint definitions, reserved keyword of the GBOML language
# FunctionConstraint can only be SOS1 and SOS2 (could add some of them later in Python in but not in GBOML); SOS1 and SOS2 can only be used as FunctionConstraints
#
# Errors
# Should not stop at first error, and should be nicer print ('B.param', not ExpressionDotCall(lhs=PathRoot(name='B'), rhs='param')) by e.g. defining a short_string() in gboml.ast
# Can be implemented with function decorator or separate additionnal argument to all functions
# TODO define function to raise error; TODO do not stop at first error
#
# Production tests:
# - use check.py to check AST types are respected
# - use pyright to check for correct typing of method etc
