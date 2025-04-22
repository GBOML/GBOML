from gboml.ast import *
from gboml.factorization import factorize_gboml
from gboml.scope import get_scope_after_expr, EmptyScopeVarid
from gboml.tools.tree_modifier import visit, visit_hier
from collections.abc import Iterable
from itertools import repeat
from math import prod
import numpy as np
from typing import Any
from scipy.sparse import csr_matrix

def _is_varid_in_gboml(root: GBOMLObject, varid: str) -> bool:
    """ Search in GBOMLObject if it contains a element referencing a Loop.varid (the "x" in "... for x in [0:1]") """
    result = False
    def f(elem):
        nonlocal result
        if not result and isinstance(indexing_param := get_scope_after_expr(elem), EmptyScopeVarid) and indexing_param.name == varid:
            result = True
    visit(root, dict.fromkeys((ExpressionDotCall, PathRoot), f))
    return result

def _repeat_if_needed(repeat_times: int, *objects):
    """ Repeat non-iterable inputs if at least one is iterable (all iterable ones must have their lengths equal to repeat_times) """
    if any(len(obj) != repeat_times for obj in objects if isinstance(obj, Iterable)):
        raise RuntimeError
    return [obj if isinstance(obj, Iterable) else np.repeat(obj, repeat_times) for obj in objects]

def _evaluate_vars_coefs_indices(indexed_vars_to_coefs, repeat, param_defs):
    for (var_name, var_idx), coef in indexed_vars_to_coefs.items():
        yield var_name, *_repeat_if_needed(repeat, gboml_eval(var_idx, param_defs), gboml_eval(coef, param_defs))

def matrix_generation(tree: GBOMLGraph, param_defs: dict[str, Any]):
    """
    :param tree: the whole GBOMLGraph, ready for evaluation
    :param param_defs: a dictionary with key=ParameterDefinition.semantic.scope.path_to_str() and value is the already-evaluated value of GBOML ParameterDefinition
    :returns: A_eq, b_eq, A_ineq, b_ineq, objectives, obj_offsets
    :raises: RuntimeError if a constraint is non-linear or if it contains no variable
    """
    var_maps_col = {}  # maps variable's path_to_str() to the 1st column number allocated to it  # TODO there is currently no detection if index out of range
    csr_cols = 0  # number of columns in the final matrix
    def update_var_maps_col(var: VariableDefinition) -> None:
        nonlocal csr_cols
        var_maps_col[var.semantic.scope.path_to_str()] = csr_cols
        csr_cols += prod(map(lambda idx: gboml_eval(idx, param_defs), var.indices)) if var.indices else 1
    visit(tree, {VariableDefinition: update_var_maps_col})
    csr_indptr_eq: list[int] = [0]
    csr_indices_eq: list[int] = []
    csr_values_eq: list[float] = []
    indep_terms_eq = []
    csr_indptr_ineq: list[int] = [0]
    csr_indices_ineq: list[int] = []
    csr_values_ineq: list[float] = []
    indep_terms_ineq = []

    def add_coefs_and_term_from_constr(c: StdConstraint, hier: list[Loop]) -> None:
        indexed_vars_to_coefs, term = factorize_gboml(c, param_defs)
        csr_indptr = csr_indptr_eq if c.op == Operator.equal else csr_indptr_ineq
        csr_indices = csr_indices_eq if c.op == Operator.equal else csr_indices_ineq
        csr_values = csr_values_eq if c.op == Operator.equal else csr_values_ineq
        indep_terms = indep_terms_eq if c.op == Operator.equal else indep_terms_ineq

        idx_loops_on_constr = 0  # hier[idx_loops_on_constr:] are all the Loops that generate the constr
        child = c
        while hier and -idx_loops_on_constr < len(hier) and hier[idx_loops_on_constr - 1].child is child:
            idx_loops_on_constr -= 1
            child = hier[idx_loops_on_constr]
        del child

        # TODO support more than one Loop
        if idx_loops_on_constr and _is_varid_in_gboml(c, hier[-1].varid):
            loop_iterable = gboml_eval(hier[-1].on, param_defs)
            if hier[-1].condition is not None:
                loop_iterable = loop_iterable[np.nonzero(gboml_eval(hier[-1].condition, param_defs | {hier[-1].varid: loop_iterable}))]
            tmp = np.zeros((len(loop_iterable), csr_cols))  # TODO use something using less mem
            param_defs_with_varid = param_defs | {hier[-1].varid: loop_iterable}
            try:
                for var_name, indices_eval, coefs_eval in _evaluate_vars_coefs_indices(indexed_vars_to_coefs, len(loop_iterable), param_defs_with_varid):
                    tmp[range(len(loop_iterable)), var_maps_col[var_name] + indices_eval] += coefs_eval
            except NameError:
                raise RuntimeError(f"{c.meta}: non-linear constraint.")
            indep_terms.extend(*_repeat_if_needed(len(loop_iterable), gboml_eval(term, param_defs_with_varid)))

        else:
            tmp = np.zeros((1,csr_cols))
            try:
                for (var_name, var_idx), coef in indexed_vars_to_coefs.items():
                    tmp[0, var_maps_col[var_name] + gboml_eval(var_idx, param_defs)] = gboml_eval(coef, param_defs)
            except NameError:
                raise RuntimeError(f"{c.meta}: non-linear constraint.")
            indep_terms.append(gboml_eval(term, param_defs))
        for i in tmp:
            if (nonzero_indices := np.flatnonzero(i)).any():
                csr_values.extend(i[nonzero_indices])
                csr_indices.extend(nonzero_indices)
                csr_indptr.append(len(csr_indices))
            else:
                raise RuntimeError(f"{c.meta}: no variable in constraint.")
    visit_hier(tree, {Loop}, {StdConstraint: add_coefs_and_term_from_constr})
    return csr_matrix((csr_values_eq, csr_indices_eq, csr_indptr_eq), shape=(len(csr_indptr_eq) - 1, csr_cols)), indep_terms_eq,\
        csr_matrix((csr_values_ineq, csr_indices_ineq, csr_indptr_ineq), shape=(len(csr_indptr_ineq) - 1, csr_cols)), indep_terms_ineq
