# Copyright (C) 2020 - 2022
# Bardhyl Miftari, Mathias Berger, Hatim Djelassi, Damien Ernst,
# University of Liege .
# Licensed under the MIT License (see LICENSE file).

"""Xpress Solver file, contains the interface to Xpress solver .

Takes the matrix A, the vector b and vector c as input of the problem
    min : c^T * X s.t. A * X <= b
and passes it to the xpress solver.

  Typical usage example:

   solution, objective, status, solver_info = xpress_solver(matrix_a, vector_b,
                                                            vector_c,
                                                            objective_offset,
                                                            name_tuples)
   print("the solution is "+str(solution))
   print("the objective found : "+str(objective))
"""

import numpy as np
from scipy.sparse import coo_matrix, csr_matrix
from gboml.compiler.utils import flat_nested_list_to_two_level


def xpress_solver(matrix_a: coo_matrix, vector_b: np.ndarray,
                  vector_c: np.ndarray, objective_offset: float,
                  name_tuples: list,
                  opt_file: str = None,
                  details = False) -> tuple:
    """xpress_solver

        takes as input the matrix A, the vectors b and c. It returns
        the solution of the problem : min c^T * x s.t. A * x <= b found
        by the xpress solver

        Args:
            A -> coo_matrix of constraints
            b -> np.ndarray of independent terms of each constraint
            c -> np.ndarray of objective vector
            objective_offset -> float of the objective offset
            name_tuples -> dictionary of <node_name variables> used to get
                           the type
            opt_file -> optimization parameters file

        Returns:
            solution -> np.ndarray of the flat solution
            objective -> float of the objective value
            status -> solution status
            solver_info -> dictionary of solver information

    """

    try:

        import xpress as xp
    except ImportError:

        print("Warning: Did not find the CyLP package")
        exit(0)

    if opt_file is None:
        opt_file = 'src/gboml/solver_api/xpress.opt'

    # Generating the model
    model = xp.problem()
    matrix_a = matrix_a.astype(float)
    _, nb_columns = matrix_a.shape

    var_list = [xp.var(vartype=xp.continuous, lb=float('-inf'))
                for _ in range(nb_columns)]
    flat_name_tuples = flat_nested_list_to_two_level(name_tuples)
    is_milp = False
    for index, _, var_type, var_size in flat_name_tuples:
        if var_type == "integer":
            is_milp = True
            for i in range(var_size):
                var_list[index+i] = xp.var(vartype=xp.integer, lb=float('-inf'))
        elif var_type == "binary":
            is_milp = True
            for i in range(var_size):
                var_list[index+i] = xp.var(vartype=xp.binary)

    var_array = np.array(var_list)
    model.addVariable(var_array)
    nb_constraints, _ = matrix_a.shape
    csr_matrix_format_a = matrix_a.tocsr()
    csr_data, csr_indices, csr_ptr = csr_matrix_format_a.data, \
                                     csr_matrix_format_a.indices, \
                                     csr_matrix_format_a.indptr

    for i in range(nb_constraints):
        pt = slice(csr_ptr[i], csr_ptr[i+1])
        columns = csr_indices[pt]
        values = csr_data[pt]
        lhs_constraint = xp.Dot(np.array(values), var_array[columns])
        model.addConstraint(lhs_constraint <= vector_b[i])

    objective = xp.Dot(vector_c.reshape(-1), var_array) + objective_offset
    model.setObjective(objective)

    # Retrieve solver information
    option_info = {}
    try:

        with open(opt_file, 'r') as optfile:

            lines = optfile.readlines()
    except IOError:

        print("Options file not found")
    else:

        for line in lines:

            line = line.strip()
            option = line.split(" ", 1)
            if option[0] != "":
                try:
                    parinfo = getattr(model.controls, option[0])
                except AttributeError as e:
                    print("Skipping unknown option \'%s\'" % option[0])
                    continue
                if parinfo:

                    if len(option) == 2:

                        key = option[0]
                        try:
                            value = parinfo
                        except ValueError as e:

                            print("Skipping option \'%s\' with invalid "
                                  "given value \'%s\' (expected %s)"
                                  % (option[0], option[1], parinfo[1]))
                        else:

                            model.setControl(key, value)
                            option_info[key] = value
                    else:

                        print("Skipping option \'%s\' with no given value"
                              % option[0])
                else:

                    print("Skipping unknown option \'%s\'" % option[0])

    # Solve the model and generate output
    model.solve()
    solution = np.array(model.getSolution())
    objective = model.getObjVal()

    status = model.getProbStatus()
    if (status == 1 and not is_milp) or (is_milp and status == 6):
        status = "optimal"
    elif (status == 2 and not is_milp) or (is_milp and status == 5):
        status = "infeasible"
    else:
        status = "unknown"

    solver_info = {"name": "xpress", "algorithm": "unknown",
                   "status": status,
                   "options": option_info}

    constraints_additional_information = dict()
    variables_additional_information = dict()

    attributes_to_retrieve_constraints = [
        ["dual", model.getDual],
        ["slack", model.getSlack],
    ]
    attributes_to_retrieve_variables = [
        ["reduced_cost", model.getRCost],
    ]

    if details:
        for name, function in attributes_to_retrieve_constraints:
            try:
                constraints_additional_information[name] = function()
            except RuntimeError:
                print("Unable to retrieve ", name, " information for constraints")

        for name, function in attributes_to_retrieve_variables:
            try:
                variables_additional_information[name] = function()
            except RuntimeError:
                print("Unable to retrieve ", name, " information for variables")

    return solution, objective, status, solver_info, \
           constraints_additional_information, \
           variables_additional_information
