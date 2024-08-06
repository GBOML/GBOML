from gboml.ast import *
from gboml.scope import *
from gboml.tools.tree_modifier import visit, visit_hier, modify_hier

from graphlib import TopologicalSorter, CycleError
from typing import NamedTuple
import dataclasses

ObjectsWithScopeOrDefs = ObjectsWithScope|VarOrParamDefinition
GenobjsOrGenattrs = GeneratedObjectsType|Array|FunctionConstraint|ExpressionFunctionCall

def _get_scope_from_hier(hier: list[ObjectsWithScopeOrDefs]) -> Scope:
    return next(hier_item.semantic.scope for hier_item in reversed(hier) if hier_item.semantic.scope is not None)

def _get_parent_from_hier(hier: list[ObjectsWithScopeOrDefs], _type: type[ObjectsWithScopeOrDefs]) -> ObjectsWithScopeOrDefs|None:
    return next((hier_item for hier_item in reversed(hier) if isinstance(hier_item, _type)), None)

def _add_dep(deps: dict[VarOrParamDefinition, set[VarOrParamDefinition]], hier: list[ObjectsWithScopeOrDefs], dep: Scope) -> None:
    if isinstance(dep, VarOrParamDefScope) and (parent_def := _get_parent_from_hier(hier, VarOrParamDefinition)) is not None:
        if parent_def in deps:
            deps[parent_def].add(dep.ast)
        else:
            deps[parent_def] = {dep.ast}


def _get_scope_after_expr(elem: ExpressionDotCall|ExpressionFunctionCall|PathRoot, scope: Scope) -> Scope:
    assert isinstance(path_root := getattr(elem, 'lhs', elem), PathRoot)  # either lhs or elem needs to be PathRoot

    try:
        scope = scope[path_root.name]
        if isinstance(elem, ExpressionDotCall):
            if isinstance(scope, VarOrParamDefScope):
                raise KeyError
            scope = scope[elem.rhs]
    except KeyError:
        raise RuntimeError(f"{elem} {elem.meta}: cannot be used in this scope")
    return scope


def _likeloop_to_baseloop(elem: LikeLoop, hier: list[ObjectsWithScopeOrDefs]) -> BaseLoop:
    if not isinstance(index_param_def := getattr(_get_scope_after_expr(elem.on, _get_scope_from_hier(hier)), 'ast', None), IndexingParameterDefinition):
        raise RuntimeError(f"{elem} {elem.meta}: {elem.on} is not an IndexingParameterDefinition")
    return BaseLoop(elem.child, elem.varid, index_param_def.value, elem.condition, meta=elem.meta, semantic=elem.semantic)


def _mark_implicit_loops(elem: ExpressionDotCall|PathRoot, hier: list[ObjectsWithScopeOrDefs|GenobjsOrGenattrs|ImplicitLoop], implicit_loops: dict[GenobjsOrGenattrs|ExpressionObj, set[ImplicitLoop]]) -> ExpressionDotCall|PathRoot:
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


def _add_implicit_loops(elem: GenobjsOrGenattrs|ExpressionObj, hier: list[ObjectsWithScopeOrDefs|GenobjsOrGenattrs|ImplicitLoop], implicit_loops: dict[GenobjsOrGenattrs|ExpressionObj, set[ImplicitLoop]]) -> GenobjsOrGenattrs|ExpressionObj:
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


def _check_fct_use_and_def(elem: ExpressionDotCall|ExpressionFunctionCall|PathRoot, scope: Scope) -> None:
    """ Compare function usage and definition """  # TODO more generic to check also for array/indices
    if not scope:
        return

    if isinstance(scope, ScopedFunctionDefinition) != isinstance(elem, ExpressionFunctionCall):
        raise RuntimeError(f"{elem} {elem.meta}: used as {'function' if isinstance(elem, ExpressionFunctionCall) else 'non-fonction'} "
                           f"but declared as {'function' if isinstance(scope, ScopedFunctionDefinition) else 'non-fonction'} {scope.ast.meta}!")
    elif isinstance(scope, ScopedFunctionDefinition) and isinstance(elem, ExpressionFunctionCall) and all(not isinstance(arg, Loop) for arg in elem.operands) and len(elem.operands) != len(scope.ast.args):
        raise RuntimeError(f"{elem} {elem.meta}: function call got {len(elem.operands)} arguments but declared with {len(scope.ast.args)} arguments at {scope.ast.meta}.")


def _check_var_or_param_scoping(elem: ExpressionDotCall|PathRoot, hier: list[ObjectsWithScopeOrDefs], deps: dict[VarOrParamDefinition, set[VarOrParamDefinition]]) -> None:
    """ Checks if elem is accessible in the current scope (if not, an error is raised), adds elem to its VarOrParamDefinition parent's dependencies """
    if not isinstance(getattr(elem, 'lhs', elem), PathRoot):
        return  # if both elem and lhs are not PathRoot, cannot check anything

    _add_dep(deps, hier, _get_scope_after_expr(elem, _get_scope_from_hier(hier)))


def _check_fct_scoping(elem: ExpressionFunctionCall, hier: list[ObjectsWithScopeOrDefs], deps: dict[VarOrParamDefinition, set[VarOrParamDefinition]]) -> None:
    if not isinstance(left_elem := elem.lhs, PathRoot) or isinstance(left_elem, ExpressionDotCall) and not isinstance(left_elem.lhs, PathRoot):
        return  # only functions like f(), A.f() can be checked

    _check_fct_use_and_def(elem, scope := _get_scope_after_expr(left_elem, _get_scope_from_hier(hier)))
    _add_dep(deps, hier, scope)


def _check_node_or_hyperedge_indices(elem: NodeDefinition|HyperEdgeDefinition, hier: list[ObjectsWithScopeOrDefs]) -> None:
    if not elem.indices:
        return
    scope = _get_scope_from_hier(hier)
    for index in elem.indices:
        try:
            scope[index]
        except KeyError:
            raise KeyError(f"{elem} {elem.meta} index {index} can not be used in this scope")


def _topo_sort(globalScope: GlobalScope, deps) -> list[VarOrParamDefScope]:
    """ Performs the topological sort for VarOrParamDefinition elements (if there's a circular dependency, an error is raised), and returns the sorted elements in a map """
    ts = TopologicalSorter()
    add_node = lambda definition: ts.add(definition, *deps.get(definition, frozenset()))
    visit(globalScope.ast, dict.fromkeys(VarOrParamDefinition.__args__, add_node))
    try:
        return list(ts.static_order())
    except CycleError as err:  # default error too long to print, so raise from None
        raise RuntimeError("Circular dependency found!", list(map(lambda dep: (dep.path_to_str(), dep.ast.meta), err.args[1]))) from None


def semantic_check(globalScope: GlobalScope) -> GlobalScope:
    # check if variables are in scope, and store deps
    deps: dict[VarOrParamDefinition, set[VarOrParamDefinition]] = {}
    visit_hier(globalScope.ast, set(ObjectsWithScopeOrDefs.__args__), {ExpressionFunctionCall: lambda elem,hier: _check_fct_scoping(elem, hier, deps)} | dict.fromkeys((ExpressionDotCall, PathRoot), lambda elem,hier: _check_var_or_param_scoping(elem, hier, deps)) | dict.fromkeys((NodeDefinition, HyperEdgeDefinition), _check_node_or_hyperedge_indices))

    _topo_sort(globalScope, deps)  # TODO propagate scalar values in the order of the returned list
    del deps

    # add implicit loops in GBOMLGraph (and while we're at it, convert LikeLoops to BaseLoops)
    new_ast = modify_hier(globalScope.ast, set(ObjectsWithScopeOrDefs.__args__), {LikeLoop: _likeloop_to_baseloop})
    implicit_loops: dict[GenobjsOrGenattrs|ExpressionObj, set[ImplicitLoop]] = {}
    new_ast = modify_hier(new_ast, GeneratedObjects | {*ObjectsWithScopeOrDefs.__args__, ImplicitLoop, Array, FunctionConstraint, ExpressionFunctionCall},
                by_before=dict.fromkeys((ExpressionDotCall, PathRoot), lambda elem,hier: _mark_implicit_loops(elem, hier, implicit_loops)),
                by_after=dict.fromkeys(GenobjsOrGenattrs.__args__ + (ExpressionObj,), lambda elem,hier: _add_implicit_loops(elem, hier, implicit_loops)))
    return dataclasses.replace(globalScope, ast=new_ast)

# TODO
# know which one of the nodes of the DAG does not do anything with iterable and mark their types
# TODO then propagate varorparams values to varorparams not depending on iterables (for that I can create a new function in ASTNodes that takes a scope as arg)

# TODO define short_string() at least for Path + ExpressionFunctionCall + Meta (in fact, could literally store it in Meta - or only store start+end line/col and reload text file as needed?) for easier-to-read errors

# TODO documentation in folder docs (for readthedocs.io)
# don't forget to add 'parent'

# TODO SOS1 and SOS2 functions are FunctionConstraint definitions, reserved keyword of the GBOML language
# FunctionConstraint can only be SOS1 and SOS2 (could add some of them later in Python but not in GBOML); SOS1 and SOS2 can only be used as FunctionConstraints

# TODO
#NODE A[u] (with u in [:2] IndexParamDef parameter from parent node) is NOT valid; should it be?
# where implicit loop in 'a = {f(u)}' inside function or inside array

# TODO we should be able to semantic check A.B.C.D.E.x

# function decorator ↓ (or separate additionnal argument to all functions)
# TODO define function to raise error; TODO do not stop at first error
# what about attaching error to a new scope.variable? if that var already has an error, don't add another one; at the end simply visit() and raise all errors

# TODO I assumed reserved_definitions function all only take 1 arg (array). Is that true (we could force the user to create an array ?)

# TODO in production tests, 
# - use check.py to check AST types are respected
# - use pyright to check for correct typing of method etc
