# Copyright (C) 2020 - 2022
# Bardhyl Miftari, Mathias Berger, Hatim Djelassi, Damien Ernst,
# University of Liege .
# Licensed under the MIT License (see LICENSE file).


"""CLP Solver file, contains the interface to CLP/CBC solver .

Takes the matrix A, the vector b and vector c as input of the problem
    min : c^T * X s.t. A * X <= b
and passes it to the CLP/CBC solver.

  Typical usage example:

   solution, objective, status, solver_info = clp_solver(matrix_a,
                                                        vector_b,
                                                        vector_c,
                                                         objective_offset,
                                                         name_tuples)
   print("the solution is "+str(solution))
   print("the objective found : "+str(objective))
"""

import numpy as np
from scipy.sparse import coo_matrix
from gboml.compiler.utils import flat_nested_list_to_two_level


def clp_solver(matrix_a_eq: coo_matrix, vector_b_eq: np.ndarray,
               matrix_a_ineq: coo_matrix, vector_b_ineq: np.ndarray,
               vector_c: np.ndarray,
               objective_offset: float,
               name_tuples: list) -> tuple:
    """clp_solver

        takes as input the matrix A, the vectors b and c. It returns the
        solution of the problem : min c^T * x s.t. A * x <= b found by
        the clp/cbc solver

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

    try:

        from cylp.cy import CyClpSimplex
        from cylp.py.modeling.CyLPModel import CyLPModel, CyLPArray
    except ImportError as e:
        print(e)
        print("Warning: Did not find the CyLP package")
        exit(0)

    nvars = np.shape(vector_c)[1]
    additional_var_bool = False

    # CyLPModel with one variable creates an error
    # To go around this problem, we create another variable
    # which is never used and add it to the model
    if nvars == 1:

        additional_var_bool = True
        nvars = 2
        line, col = matrix_a_eq.shape
        matrix_a_eq = coo_matrix((matrix_a_eq.data, (matrix_a_eq.row, matrix_a_eq.col)),
                                 shape=(line, col+1))
        line, col = matrix_a_ineq.shape
        matrix_a_ineq = coo_matrix((matrix_a_ineq.data, (matrix_a_ineq.row, matrix_a_ineq.col)),
                                   shape=(line, col+1))
        vector_c = np.append(vector_c[0], [0])

    # Build CLP model
    model = CyLPModel()
    c = CyLPArray(vector_c)
    variables = model.addVariable('variables', nvars, isInt=False)
    model.addConstraint(matrix_a_ineq * variables <= vector_b_ineq)
    model.addConstraint(matrix_a_eq * variables == vector_b_eq)
    model.objective = c * variables
    s = CyClpSimplex(model)
    flat_name_tuples = flat_nested_list_to_two_level(name_tuples)

    is_integer = False
    for index, _, var_type, var_size in flat_name_tuples:

        if var_type == "integer":
            is_integer = True
            s.setInteger(variables[index:index+var_size])
        if var_type == "binary":
            is_integer = True
            s.setInteger(variables[index:index+var_size])
            s += 0.0 <= variables[index:index+var_size] <= 1

    solution = dict()
    if is_integer :
    # Get cbc equivalent of that build clp model to exploit variable types
        cbc_model = s.getCbcModel()
        # Solve the model
        cbc_model.solve()

        # Gather and retrieve solver information
        solver_info = {"name": "cbc", "algorithm": "primal/dual simplex",
                       "status": cbc_model.status}
        status_code = cbc_model.status
        solver = cbc_model
    else:
        s.initialSolve()
        status_code = s.getStatusCode()
        if status_code == 0:
            status_code = "solution"
        elif status_code == 1 or status_code == 2:
            status_code = "infeasible"
        else:
            status_code = "unknown"

        solver_info = {"name": "clp", "algorithm": "primal/dual simplex",
                       "status": status_code}
        solver = s
    solution = None
    objective = None
    if status_code == "solution":
        status = "optimal"
        solution = solver.primalVariableSolution['variables']

        # if we added an additional variable artificially
        # we remove it
        if additional_var_bool:

            solution = solution[0:len(solution)-1]
        objective = solver.objectiveValue + objective_offset
    elif status_code == "unset":

        status = "unbounded"
        objective = float('-inf')
    elif status_code == 'relaxation infeasible':

        status = "infeasible"
        objective = float("inf")
    else:

        status = "unknown"
    return solution, objective, status, solver_info
