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


def scipy_solver(matrix_a: coo_matrix, vector_b: np.ndarray,
                 vector_c: np.ndarray,
                 objective_offset: float, name_tuples: dict) -> tuple:
    """scipy_solver

        takes as input the matrix A, the vectors b and c. It returns the
        solution of the problem : min c^T * x s.t. A * x <= b found by the
        scipy's linprog solver

        Args:
            A -> coo_matrix of constraints
            b -> np.ndarray of independent terms of each constraint
            c -> np.ndarray of objective vector
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

    # Generate the model
    result = linprog(vector_c, A_ub=matrix_a.toarray(),
                     b_ub=vector_b,
                     bounds=x0_bounds,
                     options={"lstsq": True, "disp": True,
                              "cholesky": False, "sym_pos": False})

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