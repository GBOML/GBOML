# Copyright (C) 2020 - 2022
# Bardhyl Miftari, Mathias Berger, Hatim Djelassi, Damien Ernst,
# University of Liege .
# Licensed under the MIT License (see LICENSE file).


"""CBC solver .

Takes the matrix A, the vector b and vector c as input of the problem
    min : c^T * X s.t. A * X <= b
and passes it to the CLP/CBC solver.

  Typical usage example:

   solution, objective, status, solver_info = cbc_solver(matrix_a,
                                                         vector_b,
                                                         vector_c,
                                                         objective_offset,
                                                         name_tuples)
   print("the solution is "+str(solution))
   print("the objective found : "+str(objective))
"""

import numpy as np
from gboml.compiler.utils import flat_nested_list_to_two_level

from scipy.sparse import coo_matrix, csc_matrix
from .pycbc import PyCBC


def cbc_solver(matrix_a_eq: coo_matrix, vector_b_eq: np.ndarray,
               matrix_a_ineq: coo_matrix, vector_b_ineq: np.ndarray,
               vector_c: np.ndarray,
               objective_offset: float,
               name_tuples: dict,
               opt_file: str = None,
               option_dict: dict = None) -> tuple:
    """cbc_solver

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
            opt_file -> optimization parameters file
            option_dict -> alternative to optimization parameters file that associates
                           key = <option to set>, value= value

        Returns:
            solution -> np.ndarray of the flat solution
            objective -> float of the objective value
            status -> solution status
            solver_info -> dictionary of solver information

    """
    if option_dict is None:
        option_dict = dict()

    nvars = np.shape(vector_c)[1]
    eq_data, eq_row, eq_col = matrix_a_eq.data, matrix_a_eq.row, matrix_a_eq.col
    nb_row_eq, _ = matrix_a_eq.shape
    ineq_data, ineq_row, ineq_col = matrix_a_ineq.data, matrix_a_ineq.row, matrix_a_ineq.col
    nb_row_ineq, _ = matrix_a_ineq.shape
    all_rows = np.concatenate((ineq_row, np.array(eq_row)+nb_row_ineq))
    all_col = np.concatenate((ineq_col, eq_col))
    all_data = np.concatenate((ineq_data, eq_data))

    flat_name_tuples = flat_nested_list_to_two_level(name_tuples)
    row_lower = [-float('inf')] * nb_row_ineq + vector_b_eq.tolist()
    row_upper = vector_b_ineq.tolist() + vector_b_eq.tolist()
    col_lower = [-float('inf')] * nvars
    col_upper = [float('inf')] * nvars
    col_types = [0] * nvars

    for index, _, var_type, var_size in flat_name_tuples:

        if var_type == "integer":
            col_types[index:index + var_size] = [1] * var_size

        if var_type == "binary":
            col_types[index:index + var_size] = [1] * var_size
            col_lower[index:index + var_size] = [0] * var_size
            col_upper[index:index + var_size] = [1] * var_size

    merged_matrices = coo_matrix((all_data, (all_rows, all_col)), shape=(nb_row_ineq+nb_row_eq, nvars)).tocsc()
    index, indptr, data = merged_matrices.indices, merged_matrices.indptr, merged_matrices.data
    cbc_lib = PyCBC()
    cbc_model = cbc_lib.Cbc_newModel()
    cbc_lib.Cbc_loadProblem(cbc_model, nvars, nb_row_ineq+nb_row_eq, indptr, index, data,
                            col_lower, col_upper, vector_c[0], row_lower, row_upper)

    for i, col_type in enumerate(col_types):
        if col_type == 1:
            cbc_lib.Cbc_setInteger(cbc_model, i)

    new_dict_options_from_file = option_dict.copy()
    solver_info = dict()
    all_options_types = {
        "string": [str, cbc_lib.Cbc_setParameter]
    }

    special_options = {
        "gap": [float, cbc_lib.Cbc_setAllowableGap],
        "max_time": [float, cbc_lib.Cbc_setMaximumSeconds],
        "fraction_gap": [float, cbc_lib.Cbc_setAllowableFractionGap],
        "max_nb_solutions": [float, cbc_lib.Cbc_setMaximumSolutions]
    }

    try:
        if opt_file is not None:
            with open(opt_file, 'r') as optfile:
                lines = optfile.readlines()
            for line in lines:
                line = line.strip()
                option = line.split(" ", 2)
                if option[0] in all_options_types and option[0] not in new_dict_options_from_file:
                    if len(option) == 3:
                        new_dict_options_from_file[option[1]] = [option[0], option[2]]
                    else:
                        print("Skipping option \'%s\' with no given value"
                              % option[0])
                else:
                    print("Skipping option \'%s\' as redefined in function call"
                          % option[0])
    except IOError:

        print("Options file not found")

    option_info = dict()

    for option_name, [option_type, option_value] in new_dict_options_from_file.items():
        try:
            if option_name in special_options:
                type_val, function = special_options[option_name]
                value = type_val(option_value)
                status = function(cbc_model, value)
                option_info[option_name] = value

            else:
                type_val, function = all_options_types[option_type]
                value = type_val(option_value)
                status = function(cbc_model, option_name, value)
                option_info[option_name] = value

        except ValueError as e:
            print("Skipping option \'%s\' "
                  "with invalid given value \'%s\' "
                  "(expected %s)"
                  % (option_name, option_value, type_val))
        except Exception as e:
            print("Skipping option \'%s\' "
                  "with invalid given value \'%s\' "
                  "(expected %s)"
                  % (option_name, option_value, type_val))
        else:
            if status == -1:
                print("Skipping option \'%s\' "
                      "with invalid given value \'%s\' "
                      "(expected %s)"
                      % (option_name, option_value, type_val))
            else:
                print("Setting option \'%s\' to value \'%s\'"
                      % (option_name, value))

    status_code = cbc_lib.Cbc_solve(cbc_model)
    solution = []
    objective = 0
    status = "unknown"
    solver_info["status"] = status_code
    solver_info["options"] = option_info
    if status_code == 0 or status_code == 1:
        secondary_status_opt = cbc_lib.Cbc_isProvenOptimal(cbc_model)
        secondary_status_inf = cbc_lib.Cbc_isProvenInfeasible(cbc_model)
        secondary_status_timeout = cbc_lib.Cbc_isSecondsLimitReached(cbc_model)
        secondary_status_gap = cbc_lib.Cbc_isSolutionLimitReached(cbc_model)
        if secondary_status_opt == 1:
            status = "optimal"
            solution = cbc_lib.Cbc_getColSolution(cbc_model, nvars)
            objective = cbc_lib.Cbc_getObjValue(cbc_model)+objective_offset
        elif secondary_status_inf:
            status = "infeasible"
        elif secondary_status_gap or secondary_status_timeout:
            status = "sub-optimal stopped"
            solution = cbc_lib.Cbc_getColSolution(cbc_model, nvars)
            objective = cbc_lib.Cbc_getObjValue(cbc_model)+objective_offset
    else:
        status = "unknown"

    return solution, objective, status, solver_info
