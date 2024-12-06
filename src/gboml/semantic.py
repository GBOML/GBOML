from gboml.ast import *
from gboml.scope import *
from gboml.tools.tree_modifier import visit, visit_hier, modify_hier
from gboml.reserved_definitions import GBOML_RESERVED_DEFINITIONS

from graphlib import TopologicalSorter, CycleError
from typing import NamedTuple, Optional, Any
import ast
from collections.abc import Iterable
import dataclasses
from math import prod
import numpy as np
from scipy.sparse import csr_matrix

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


def _topo_sort(globalScope: GlobalScope, deps) -> tuple[VarOrParamDefScope]:
    """ Performs the topological sort for VarOrParamDefinition elements (if there's a circular dependency, an error is raised), and returns the sorted elements (should be evaluated in the same order) """
    ts = TopologicalSorter()
    add_node = lambda definition: ts.add(definition, *deps.get(definition, frozenset()))
    visit(globalScope.ast, dict.fromkeys(VarOrParamDefinition.__args__, add_node))
    try:
        return tuple(ts.static_order())
    except CycleError as err:  # default error too long to print, so raise from None
        raise RuntimeError("Circular dependency found!", list(map(lambda dep: (dep.semantic.scope.path_to_str(), dep.meta), err.args[1]))) from None


def _compile_from_gboml(root: GBOMLObject|int):
    return compile(ast.fix_missing_locations(ast.Expression(to_python_ast(root))), "", mode="eval")

def _evaluate_from_compiled_expr(compiled_expr, local_defs: dict[str, Any]):
    return eval(compiled_expr, {'$range': np.arange}, local_defs)

def _evaluate_from_gboml(root: GBOMLObject|int, local_defs: dict[str, Any]):
    return root if isinstance(root, int) else _evaluate_from_compiled_expr(_compile_from_gboml(root), local_defs)

def _process_constraint(c: Constraint, var_maps: dict[str, int], param_defs: dict[str, Any]) -> tuple[dict[tuple[str, Optional[Expression]], Expression], Expression]:
    """ Returns a tuple(indexed_vars_to_coefs, independant_term) for a given Constraint """
    new_line = [0] * len(var_maps)
    indep_term = 0
    indexed_vars_to_coefs: dict[tuple[str, Optional[Expression]], Expression] = {}  # {(var.path_to_str(), index_as_gboml_ast): coef_as_gboml_ast}
    def add_variable_in_constr(elem: ExpressionDotCall|ExpressionArrayCall|PathRoot, hier: list[ExpressionOp|ExpressionArrayCall], sign: int) -> None:
        """ Returns 0 (to remove the variable for the indep term calculation) and adds the var coef to the approriate entry in indexed_vars_to_coefs """
        if isinstance(elem, ExpressionArrayCall):
            return 0 if elem.lhs == 0 else elem

        if isinstance(scope := get_scope_after_expr(elem), ScopedVariableDefinition):
            coef = sign
            sign_has_changed = False
            var_idx = hier[-1].rhs if hier and isinstance(hier[-1], ExpressionArrayCall) and hier[-1].lhs is elem else 0
            for op in filter(lambda o: isinstance(o, ExpressionOp), reversed(hier)):
                op_new = dataclasses.replace(op, operands=tuple(operand for operand in op.operands if operand is not elem))
                if len(op_new.operands) != len(op.operands):
                    match op.operator:
                        case Operator.plus:
                            pass
                        case Operator.minus:
                            if op.operands[0] is not elem:
                                sign_has_changed = not sign_has_changed
                        case Operator.unary_minus:
                            sign_has_changed = not sign_has_changed
                        case Operator.times:
                            coef = ExpressionOp(Operator.times, (coef, op_new.operands[0] if len(op_new.operands) == 1 else op_new))
                            # try:
                                # coef *= _evaluate_from_gboml(op_new, param_defs, c.semantic.scope)
                            # except NameError:
                                # raise RuntimeError(f"Non-linear Constraint at {c.meta} on variable {scope.path_to_str()}")
                        case Operator.divide:
                            if op.operands[0] is not elem:
                                raise RuntimeError(f"Variable {scope.path_to_str()} is in the denominator, non-linear Constraint at {c.meta}.")
                            coef = ExpressionOp(Operator.divide, (coef, op_new.operands[0] if len(op_new.operands) == 1 else op_new))
                            # try:
                                # coef /= _evaluate_from_gboml(op_new, param_defs, c.semantic.scope)
                            # except NameError:
                                # raise RuntimeError(f"Non-linear Constraint at {c.meta} on variable {scope.path_to_str()}")
                        case _:
                            raise RuntimeError(f"Unsupported ExpressionOp {op.operator} applied to {scope.path_to_str()}. Ensure that Constraint at {c.meta} is linear.")
                elem = op

            if sign_has_changed:
                coef = -coef if isinstance(coef, int) else ExpressionOp(Operator.unary_minus, (coef,))
            
            key = (scope.path_to_str(), var_idx)
            match indexed_vars_to_coefs.pop(key, None):
                case int(value) if value: coef = coef + value if isinstance(coef, int) else ExpressionOp(Operator.plus, (coef, value))
                case ExpressionOp(operator=Operator.plus, operands=operands): coef = ExpressionOp(Operator.plus, operands + (coef,))
                case ExpressionOp() as expr_op: coef = ExpressionOp(Operator.plus, (expr_op, coef))
            if coef:
                indexed_vars_to_coefs[key] = coef
            return 0
        return elem

    if isinstance(c, StdConstraint):
        lhs_indep = modify_hier(c.lhs, {ExpressionOp, ExpressionArrayCall}, by_after=dict.fromkeys((ExpressionDotCall, ExpressionArrayCall, PathRoot), lambda elem,hier: add_variable_in_constr(elem, hier, +1)))
        rhs_indep = modify_hier(c.rhs, {ExpressionOp, ExpressionArrayCall}, by_after=dict.fromkeys((ExpressionDotCall, ExpressionArrayCall, PathRoot), lambda elem,hier: add_variable_in_constr(elem, hier, -1)))
        indep_term = ExpressionOp(Operator.minus, (rhs_indep, lhs_indep))

    return indexed_vars_to_coefs, indep_term

def _is_varid_in_gboml(root: GBOMLObject, varid: str) -> bool:
    result = False
    def f(elem):
        nonlocal result
        if not result and isinstance(indexing_param := get_scope_after_expr(elem), EmptyScopeVarid) and indexing_param.name == varid:
            result = True
    visit(root, dict.fromkeys((ExpressionDotCall, PathRoot), f))
    return result

def semantic_check(tree: GBOMLGraph) -> None:
    # check if variables are in scope, and store deps
    deps: dict[VarOrParamDefinition, set[VarOrParamDefinition]] = {}
    visit_hier(tree, set(HierTypes.__args__), {ExpressionFunctionCall: lambda elem,hier: _check_fct_scoping(elem, hier, deps)} | dict.fromkeys((ExpressionDotCall, PathRoot), lambda elem,hier: _check_var_or_param_scoping(elem, hier, deps)) | dict.fromkeys((NodeDefinition, HyperEdgeDefinition), lambda elem,_: _check_node_or_hyperedge_indices(elem)))

    sorted_varorparam_defs = _topo_sort(tree.semantic.scope, deps)
    del deps
    print(sorted_varorparam_defs)
    param_defs = {}
    for d in filter(lambda x: isinstance(x, Definition), sorted_varorparam_defs):
        if isinstance(d, FunctionDefinition | FunctionConstraintDefinition):  # TODO this is to skip global defs like len() - should do proper condition
            continue
        param_defs[d.semantic.scope.path_to_str()] = _evaluate_from_gboml(d, param_defs)
    print("all params values: ", param_defs, len(param_defs))
    del sorted_varorparam_defs

    var_maps = {}  # maps variable's path_to_str() to the 1st column number allocated to it
    var_cols = 0  # number of columns in the final matrix
    var_rows = 0  # number of rows (nbr of constraints) in the final matrix
    def update_var_maps(var: VariableDefinition) -> None:
        nonlocal var_cols
        var_maps[var.semantic.scope.path_to_str()] = var_cols
        var_cols += prod(map(lambda idx: _evaluate_from_gboml(idx, param_defs), var.indices)) if var.indices else 1
    def constr_count(_):
        nonlocal var_rows
        var_rows += 1
    visit(tree, {VariableDefinition: update_var_maps, Constraint: constr_count})
    # del var_cols, var_rows  # TODO incorrect var_rows since could be generated

    print("variables mapping idx: ", var_maps)
    var_coefs: list[list[float]] = []
    indep_terms: list[float] = []
    
    def _evaluate_vars_coefs_indices(indexed_vars_to_coefs, repeat, param_defs):
        for (var_name, var_idx), coef in indexed_vars_to_coefs.items():
            indices_eval = _evaluate_from_gboml(var_idx, param_defs)
            coefs_eval = _evaluate_from_gboml(coef, param_defs)
            indices_is_iter = isinstance(indices_eval, Iterable)
            coefs_is_iter = isinstance(coefs_eval, Iterable)
            if indices_is_iter and coefs_is_iter and len(coefs_eval) != len(indices_eval): raise RuntimeError
            if not indices_is_iter and coefs_is_iter: indices_eval = np.repeat(indices_eval, repeat)
            if indices_is_iter and not coefs_is_iter: coefs_eval = np.repeat(coefs_eval, repeat)
            if not indices_is_iter and not coefs_is_iter:
                indices_eval = np.repeat(indices_eval, repeat)
                coefs_eval = np.repeat(coefs_eval, repeat)
            yield var_name, indices_eval, coefs_eval
    def add_coefs_and_term(c: Constraint, hier: list[Loop]) -> None:
        indexed_vars_to_coefs, term = _process_constraint(c, var_maps, param_defs)
        new_var_coefs = np.zeros(var_cols)

        idx_loops_on_constr = 0
        child = c
        while hier and -idx_loops_on_constr < len(hier) and hier[idx_loops_on_constr - 1].child is child:
            idx_loops_on_constr -= 1
            child = hier[idx_loops_on_constr]
        
        if idx_loops_on_constr and _is_varid_in_gboml(c, hier[-1].varid):
            loop_iterable = _evaluate_from_gboml(hier[-1].on, param_defs)
            param_defs_with_varid = param_defs | {hier[-1].varid: loop_iterable}
            if hier[-1].condition is not None:
                loop_iterable = loop_iterable[np.nonzero(_evaluate_from_gboml(hier[-1].condition, param_defs_with_varid))]
            tmp = np.zeros((len(loop_iterable), var_cols))
            for var_name, indices_eval, coefs_eval in _evaluate_vars_coefs_indices(indexed_vars_to_coefs, len(loop_iterable), param_defs | {hier[-1].varid: loop_iterable}):
                tmp[range(len(loop_iterable)), var_maps[var_name] + indices_eval] += coefs_eval
            for i in tmp:
                var_coefs.append(i)
        else:
            for (var_name, var_idx), coef in indexed_vars_to_coefs.items():
                new_var_coefs[var_maps[var_name] + _evaluate_from_gboml(var_idx, param_defs)] = _evaluate_from_gboml(coef, param_defs)
            var_coefs.append(new_var_coefs)
        indep_terms.append(_evaluate_from_gboml(term, param_defs))
    visit_hier(tree, {Loop}, {Constraint: add_coefs_and_term})
    print("matrices:\n", var_coefs, indep_terms)

# enregistrer pas direct (en évaluation) dans matrice mais symboliquement par variabble(et idx) différentes; car mieux pour générer des arrays pour les variables indiçantes si dans coef
# simplement partir de feuille si c'est une variable, remonter jusqu'à root en faisant les bonnes opérations (ne pas oublier: checker si linéaire). additionner les coef si plusieurs fois la variable avec GBOML.add
# pour terme indépendant, même chose (AST symbolique) en mettant tous les variables = 0

# A=( colonne=param ligne=contrainte) x=(vars) = b=(const part from constraints)

# factorisation: tuple (coefficient de variable, indice de variable possiblement None)
# gen: loop generateur (implicit et/ou explicite)
# sign: <= == >=
# terme indépendant

# TODO quand on évalue les indices faudrait-il enregistrer la conversion ASTGboml -> ASTPython?

# TODO use by_after for all modify/modify_hier when possible


# TODOOOOOOOOOOO check VariableDefinition indices

# TODO list
#
# Add support for params importing a csv
#
# Should we forbid A.B.C.param ? C.B.A.param is always allowed because of parent.parent.parent.param
#
# I think modify() does not work if by_before AND by_after change the whole node
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
