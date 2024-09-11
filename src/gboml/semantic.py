from gboml.ast import *
from gboml.scope import *
from gboml.tools.tree_modifier import visit, visit_hier, modify_hier
from gboml.reserved_definitions import GBOML_RESERVED_DEFINITIONS

from graphlib import TopologicalSorter, CycleError
from typing import NamedTuple, Optional
import dataclasses

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

    scope = get_scope_after_expr(elem, get_scope_from_hier(hier))
    # a single PathRoot as array element, DictEntry value or ExpressionFunctionCall could be a function_call without argument (even if definition has 1+ arg)
    if not ((isinstance(hier[-2], Array) and elem in hier[-2].content
             or isinstance(hier[-2], DictEntry) and elem is hier[-2].value
             or isinstance(hier[-2], ExpressionFunctionCall) and elem in hier[-2].operands
            ) and isinstance(elem, PathRoot)):
        _check_fct_use_and_def(elem, scope)
    _add_dep(deps, hier, scope)


def _check_fct_scoping(elem: ExpressionFunctionCall, hier: list[HierTypes], deps: dict[VarOrParamDefinition, set[VarOrParamDefinition]]) -> None:

    _check_fct_use_and_def(elem, scope := get_scope_after_expr(elem, get_scope_from_hier(hier)))
    _add_dep(deps, hier, scope)


def _check_node_or_hyperedge_indices(elem: NodeDefinition|HyperEdgeDefinition, hier: list[HierTypes]) -> None:
    if not elem.indices:
        return
    scope = get_scope_from_hier(hier)
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


def semantic_check(tree: GBOMLGraph) -> None:
    # check if variables are in scope, and store deps
    deps: dict[VarOrParamDefinition, set[VarOrParamDefinition]] = {}
    visit_hier(tree, set(HierTypes.__args__), {ExpressionFunctionCall: lambda elem,hier: _check_fct_scoping(elem, hier, deps)} | dict.fromkeys((ExpressionDotCall, PathRoot), lambda elem,hier: _check_var_or_param_scoping(elem, hier, deps)) | dict.fromkeys((NodeDefinition, HyperEdgeDefinition), _check_node_or_hyperedge_indices))

    sorted_varorparam_defs = _topo_sort(tree.semantic.scope, deps)
    del deps

# TODO list
#
# VarOrParam values propagation:
# using the list returned by the toposort, know which nodes don't do anything with iterable and propagate scalar value for these ones
# once done, do 2nd pass to check for array declaration vs use (like _check_fct_use_and_def)
# also, Activations should be processed (non-conditional ones are already processed by tree_post_process.py): the conditions should only contains params (no variables)
# make sure Activations are well done, lots of edge cases (e.g. if conditionnally deactivate an already deactivated constraint, should drop completely the conditionnally constraint)
#
# Documentation in folder docs (for readthedocs.io)
# don't forget to add 'parent', say that adding Function(Constraint) needs to be done in reserved_keywords.py
#
# Errors
# Should not stop at first error, and should be nicer print ('B.param', not ExpressionDotCall(lhs=PathRoot(name='B'), rhs='param')) by e.g. defining a short_string() in gboml.ast
# Can be implemented with function decorator or separate additionnal argument to all functions
#
# Production tests:
# - use check.py to check AST types are respected
# - use pyright to check for correct typing of method etc
