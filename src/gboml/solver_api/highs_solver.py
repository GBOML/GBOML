# Copyright (C) 2020 - 2022
# Bardhyl Miftari, Mathias Berger, Hatim Djelassi, Damien Ernst,
# University of Liege .
# Licensed under the MIT License (see LICENSE file).


"""Highs Solver file, contains the interface to DSP solver .

Takes the matrix A, the vector b and vector c as input of the problem
    min : c^T * X s.t. A * X <= b
and passes it to the dsp solver.

  Typical usage example:

   solution, objective, status, solver_info = dsp_solver(matrix_a, vector_b,
                                                        vector_c,
                                                        objective_offset,
                                                        name_tuples,
                                                        structure_indexes)
   print("the solution is "+str(solution))
   print("the objective found : "+str(objective))
"""

import numpy as np
from scipy.sparse import coo_matrix, csr_matrix
from gboml.compiler.utils import flat_nested_list_to_two_level

from .pyhighs import PyHighs


def highs_solver(matrix_a_eq: coo_matrix, vector_b_eq: np.ndarray,
                 matrix_a_ineq: coo_matrix, vector_b_ineq: np.ndarray,
                 vector_c: np.ndarray,
                 objective_offset: float, name_tuples: dict) -> tuple:
    """highs_solver

        takes as input the matrix A, the vectors b and c. It returns the
        solution of the problem : min c^T * x s.t. A * x <= b found by
        the Highs solver

        Args:
            matrix_a_eq -> coo_matrix of equality constraints
            vector_b_eq -> np.ndarray of independent terms of each equality constraint
            matrix_a_ineq -> coo_matrix of inequality constraints
            vector_b_eq -> np.ndarray of independent terms of each inequality constraint
            vector_c -> np.ndarray of objective vector
            objective_offset -> float of the objective offset
            name_tuples -> dictionary of <node_name variables> used to get
                           the type

        Returns:
            solution -> np.ndarray of the flat solution
            objective -> float of the objective value
            status -> solution status
            solver_info -> dictionary of solver information

    """

    nb_constr_eq, _ = np.shape(matrix_a_eq)
    nb_constr_ineq, _ = np.shape(matrix_a_ineq)
    _, nb_cols = vector_c.shape

    nb_rows = nb_constr_eq+nb_constr_ineq
    nb_values_ineq = len(matrix_a_ineq.data)
    nb_values = len(matrix_a_eq.data)+nb_values_ineq

    csr_matrix_a_eq = csr_matrix(matrix_a_eq)
    csr_matrix_a_ineq = csr_matrix(matrix_a_ineq)

    vector_c = vector_c[-1]
    py_highs = PyHighs()
    highs_model = py_highs.Highs_create()

    col_types = [0] * nb_cols
    col_lower = [-float('inf')]*nb_cols
    col_upper = [float('inf')]*nb_cols
    flat_name_tuples = flat_nested_list_to_two_level(name_tuples)
    is_milp = False
    row_lower = [-float('inf')]*nb_constr_ineq+vector_b_eq.tolist()
    row_upper = vector_b_ineq.tolist()+vector_b_eq.tolist()
    for index, _, var_type, var_size in flat_name_tuples:

        if var_type == "integer":
            col_types[index:index + var_size] = [1] * var_size
            is_milp = True

        if var_type == "binary":
            col_types[index:index + var_size] = [1] * var_size
            col_lower[index:index + var_size] = [0] * var_size
            col_upper[index:index + var_size] = [1] * var_size
            is_milp = True

    constr_eq_val, constr_eq_row, constr_eq_col = csr_matrix_a_eq.data, csr_matrix_a_eq.indptr, \
                                                  csr_matrix_a_eq.indices
    constr_ineq_val, constr_ineq_row, constr_ineq_col = csr_matrix_a_ineq.data, csr_matrix_a_ineq.indptr,\
                                                        csr_matrix_a_ineq.indices

    all_constraints_matrix_val = np.concatenate((constr_ineq_val, constr_eq_val))
    all_constraints_matrix_col = np.concatenate((constr_ineq_col, constr_eq_col))
    all_constraints_matrix_row = np.concatenate((constr_ineq_row[:-1], constr_eq_row+nb_values_ineq))

    if is_milp is True:
        status = py_highs.Highs_passMip(highs_model, nb_cols,
                                        nb_rows, nb_values, 2, 1,
                                        objective_offset, vector_c, col_lower,
                                        col_upper, row_lower, row_upper,
                                        all_constraints_matrix_row,
                                        all_constraints_matrix_col,
                                        all_constraints_matrix_val, col_types)
    else:
        status = py_highs.Highs_passLp(highs_model, nb_cols,
                                       nb_rows, nb_values, 2, 1,
                                       objective_offset, vector_c, col_lower,
                                       col_upper, row_lower, row_upper,
                                       all_constraints_matrix_row,
                                       all_constraints_matrix_col,
                                       all_constraints_matrix_val)
    py_highs.Highs_setBoolOptionValue(highs_model, "run_crossover", False)
    py_highs.Highs_setStringOptionValue(highs_model, "solver", "ipm")
    py_highs.Highs_setStringOptionValue(highs_model, "parallel", "on")
    py_highs.Highs_setStringOptionValue(highs_model, "presolve", "on")
    #py_highs.Highs_setStringOptionValue(highs_model, "ranging", "off")
    py_highs.Highs_run(highs_model)
    solver_info = dict()
    status, lp_primal, _, _, _ = py_highs.Highs_getSolution(highs_model)
    objective = py_highs.Highs_getObjectiveValue(highs_model)

    if status == 0:

        solver_info["status"] = "optimal"
        status = "optimal"
    if status == -1:
        solver_info["status"] = "error"
        status = "error"
    if status == 1:
        solver_info["status"] = "warning"
        status = "unknown"

    solution = lp_primal

    return solution, objective, status, solver_info
