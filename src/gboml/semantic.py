from gboml.ast import *
from gboml.scope import *
from gboml.tools.tree_modifier import visit, visit_hier, modify_hier
from gboml.reserved_definitions import GBOML_RESERVED_DEFINITIONS

from graphlib import TopologicalSorter, CycleError
from typing import NamedTuple, Optional

def _add_dep(deps: dict[VarOrParamDefinition, set[VarOrParamDefinition]], hier: list[HierTypes], dep: Optional[Scope]) -> None:
    if dep is not None and isinstance(dep, VarOrParamDefScope) and (parent_def := get_parent_from_hier(hier, VarOrParamDefinition)) is not None:
        if parent_def in deps:
            deps[parent_def].add(dep.ast)
        else:
            deps[parent_def] = {dep.ast}


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

    scope = get_scope_after_expr(elem)
    # a single PathRoot as array element, DictEntry value or ExpressionFunctionCall could be a function_call without argument (even if definition has 1+ arg)
    if not (isinstance(hier[-2], Array) and elem in hier[-2].content
            or isinstance(hier[-2], DictEntry) and elem is hier[-2].value
            or isinstance(hier[-2], ExpressionFunctionCall) and elem in hier[-2].operands):
        _check_fct_use_and_def(elem, scope)
    _add_dep(deps, hier, scope)


def _check_fct_scoping(elem: ExpressionFunctionCall, hier: list[HierTypes], deps: dict[VarOrParamDefinition, set[VarOrParamDefinition]]) -> None:
    _check_fct_use_and_def(elem, scope := get_scope_after_expr(elem))
    _add_dep(deps, hier, scope)


def _check_node_or_hyperedge_indices(elem: NodeDefinition|HyperEdgeDefinition) -> None:
    if not elem.indices:
        return
    for index in elem.indices:
        try:
            elem.semantic.scope[index]
        except KeyError:
            raise KeyError(f"{elem} {elem.meta} index {index} can not be used in this scope")


def _topo_sort(globalScope: GlobalScope, deps) -> tuple[Definition]:
    """ Performs the topological sort for VarOrParamDefinition elements (if there's a circular dependency, an error is raised), and returns the sorted elements (should be evaluated in the same order) """
    ts = TopologicalSorter()
    add_node = lambda definition: ts.add(definition, *deps.get(definition, frozenset()))
    visit(globalScope.ast, dict.fromkeys(VarOrParamDefinition.__args__, add_node))
    try:
        return tuple(filter(lambda elem: isinstance(elem, Definition), ts.static_order()))
    except CycleError as err:  # default error too long to print, so raise from None
        raise RuntimeError("Circular dependency found!", list(map(lambda dep: (dep.semantic.scope.path_to_str(), dep.meta), err.args[1]))) from None

def semantic_check(tree: GBOMLGraph) -> tuple[Definition]:
    """ Raises errors if we use non-declared variables, or use vars out of their scope, cyclic dependencies for vars&params, etc; Returns a tuple of params that should be evaluated in the same order. """
    # check if variables are in scope, and store deps
    deps: dict[VarOrParamDefinition, set[VarOrParamDefinition]] = {}
    visit_hier(tree, set(HierTypes.__args__), {ExpressionFunctionCall: lambda elem,hier: _check_fct_scoping(elem, hier, deps)} | dict.fromkeys((ExpressionDotCall, PathRoot), lambda elem,hier: _check_var_or_param_scoping(elem, hier, deps)) | dict.fromkeys((NodeDefinition, HyperEdgeDefinition), lambda elem,_: _check_node_or_hyperedge_indices(elem)))

    return _topo_sort(tree.semantic.scope, deps)


# TODO list
#
# VariableDefinition indices are NOT checked
#
# should we store conversion from gboml ast -> python ast for each node?
#
# Add support for params importing a csv
#
# Should we forbid A.B.C.param ? C.B.A.param is always allowed because of parent.parent.parent.param
#
# I think modify() does not work if by_before AND by_after change the whole node
# ; also: prefer using by_after for all modify/modify_hier when possible (because e.g. only by_after works for replacing a whole node to a simple int)
#
# a1 = 1(5); should not be accepted by Lark
#
# VarOrParam values propagation:
# DO NOT EVALUATE VALUES IF NOT USED (aka only evaluate the varorparams from objective/contraint expressions)
# using the list returned by the toposort, know which nodes don't do anything with iterable and propagate scalar value for these ones
# once done, do 2nd pass to check for all types (e.g. array declaration vs use (like _check_fct_use_and_def); cannot ExpressionFunctionCall on a STRING/Array/Dictionary, no allowed operation with STRING, ...)
# also, Activations should be processed (non-conditional ones are already processed by tree_post_process.py): the conditions should only contains params (no variables)
# make sure Activations are well done, lots of edge cases (e.g. if conditionnally deactivate an already deactivated constraint, should drop completely the conditionnally constraint)
#
# Can params use vars in their expression ? At least forbid it in GLOBAL and TIMEHOZIRON
#
# Allow TIMEHORIZON to use global variables (as it already can use node's params)
#
# Documentation in folder docs (for readthedocs.io)
# say that adding Function(Constraint) needs to be done in reserved_keywords.py; say that multine comment /* */ is supported
#
# Errors
# Should not stop at first error, and should be nicer print ('B.param', not ExpressionDotCall(lhs=PathRoot(name='B'), rhs='param')) by e.g. defining a short_string() in gboml.ast
# Can be implemented with function decorator or separate additionnal argument to all functions
#
# Production tests:
# - use pyright to check for correct typing of method etc
# - add test to check 'assert Operator("<") is Operator.lesser' and 'assert Operator("<") == Operator.lesser'
