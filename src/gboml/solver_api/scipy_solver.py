# Copyright (C) 2020 - 2022
# Bardhyl Miftari, Mathias Berger, Hatim Djelassi, Damien Ernst,
# University of Liege .
# Licensed under the MIT License (see LICENSE file).


"""Scipy linprog Solver file, contains the interface to Linprog solver .

Takes the matrix A, the vector b and vector c as input of the problem
    min : c^T * X s.t. A * X <= b
and passes it to the linprog solver.

  Typical usage example:

   solution, objective, status, solver_info = scipy_solver(matrix_a, vector_b,
                                                           vector_c,
                                                           objective_offset,
                                                           name_tuples)
   print("the solution is "+str(solution))
   print("the objective found : "+str(objective))
"""

import numpy as np
from scipy.sparse import coo_matrix
from gboml.compiler.utils import flat_nested_list_to_two_level


def scipy_solver(matrix_a_eq: coo_matrix, vector_b_eq: np.ndarray,
                 matrix_a_ineq: coo_matrix, vector_b_ineq: np.ndarray,
                 vector_c: np.ndarray, objective_offset: float,
                 name_tuples: dict) -> tuple:
    """scipy_solver

        takes as input the matrix A, the vectors b and c. It returns the
        solution of the problem : min c^T * x s.t. A * x <= b found by the
        scipy's linprog solver

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

    from scipy.optimize import linprog
    x0_bounds = (None, None)

    """
    flat_name_tuples = flat_nested_list_to_two_level(name_tuples)
    integrality_array = []
    bounds = []
    for index, _, var_type, var_size in flat_name_tuples:
        if var_type == "continuous":
            integrality_array.append(0)
            bounds.append((None, None))
        elif var_type == "integer":
            integrality_array.append(1)
            bounds.append((None, None))
        elif var_type == "binary":
            integrality_array.append(1)
            bounds.append((0, 1))
    """
    # Generate the model
    result = linprog(vector_c, A_ub=matrix_a_ineq.toarray(), b_ub=vector_b_ineq, A_eq=matrix_a_eq.toarray(),
                     b_eq=vector_b_eq, method='highs', bounds=(None, None))

    # Retrieve solver info and solution
    solver_info = {"name": "linprog"}
    status_flag = result.success
    solver_info["status"] = status_flag
    solution = None
    objective = None
    if status_flag:

        status = "optimal"
        solution = result.x
        objective = result.fun+objective_offset
    else:

        status = "unknown"
    return solution, objective, status, solver_info
