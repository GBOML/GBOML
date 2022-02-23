# Copyright (C) 2020 - 2022
# Bardhyl Miftari, Mathias Berger, Hatim Djelassi, Damien Ernst,
# University of Liege .
# Licensed under the MIT License (see LICENSE file).


"""Cplex Solver file, contains the interface to Cplex solver .

Takes the matrix A, the vector b and vector c as input of the problem
    min : c^T * X s.t. A * X <= b
and passes it to the cplex solver.

  Typical usage example:

   solution, objective, status, solver_info = cplex_solver(matrix_a, vector_b,
                                                           vector_c,
                                                           objective_offset,
                                                           name_tuples)
   print("the solution is "+str(solution))
   print("the objective found : "+str(objective))
"""
from gboml.compiler.utils import flat_nested_list_to_two_level

import numpy as np
from scipy.sparse import coo_matrix
import time
import os


def cplex_solver(matrix_a: coo_matrix, vector_b: np.ndarray,
                 vector_c: np.ndarray,
                 objective_offset: float,
                 name_tuples: dict,
                 opt_file: str = None,
                 details = False) -> tuple:
    """cplex_solver

        takes as input the matrix A, the vectors b and c. It returns
        the solution of the problem : min c^T * x s.t. A * x <= b found
        by the cplex solver

        Args:
            A -> coo_matrix of constraints
            b -> np.ndarray of independent terms of each constraint
            c -> np.ndarray of objective vector
            objective_offset -> float of the objective offset
            name_tuples -> dictionary of <node_name variables> used
                           to get the type
            opt_file -> optimization parameters file
        Returns:
            solution -> np.ndarray of the flat solution
            objective -> float of the objective value
            status -> solution status
            solver_info -> dictionary of solver information

    """
    try:

        import cplex
    except ImportError:

        print("Warning: Did not find the CPLEX package")
        exit(0)

    if opt_file is None:
        opt_file = 'src/gboml/solver_api/cplex.opt'

    # Convert to appropriate structure
    matrix_a_zipped = zip(matrix_a.row.tolist(), matrix_a.col.tolist(),
                          matrix_a.data)
    m, n = np.shape(matrix_a)
    vector_b = list(vector_b.reshape(-1))
    vector_c = vector_c.tolist()[0]

    # Generate model
    model = cplex.Cplex()
    model.variables.add(obj=vector_c, lb=[-cplex.infinity]*n,
                        ub=[cplex.infinity]*n)
    flat_name_tuples = flat_nested_list_to_two_level(name_tuples)

    for index, _, var_type, var_size in flat_name_tuples:

        if var_type == "integer":

            i = index
            while i < index+var_size:

                model.variables.set_types(i, model.variables.type.integer)
                i = i+1
        if var_type == "binary":

            i = index
            while i < index+var_size:

                model.variables.set_types(i, model.variables.type.binary)
                i = i+1

    model.linear_constraints.add(senses=['L']*m, rhs=vector_b)
    model.linear_constraints.set_coefficients(matrix_a_zipped)
    model.objective.set_sense(model.objective.sense.minimize)
    model.objective.set_offset(objective_offset)

    # Retrieve solver information
    solver_info = {"name": "cplex"}
    print("\nReading CPLEX options from file cplex.opt")
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

                    key = getattr(model.parameters, option[0])
                    assert(isinstance(key, cplex._internal._parameter_classes.Parameter))
                except AttributeError as e:

                    print("Skipping unknown option \'%s\'" % option[0])
                except AssertionError as e:

                    print("Skipping unknown option \'%s\'" % option[0])
                else:

                    if len(option) == 2:

                        try:

                            value = key.type()(option[1])
                        except ValueError as e:

                            print("Skipping option \'%s\' "
                                  "with invalid given value \'%s\' "
                                  "(expected %s)"
                                  % (option[0], option[1], key.type()))
                        else:

                            name = key.__repr__().split(".", 1)[1]
                            print("Setting option \'%s\' to value \'%s\'"
                                  % (name, value))
                            key.set(value)
                            option_info[name] = value
                    else:

                        print("Skipping option \'%s\' with no given value"
                              % option[0])
    solver_info["options"] = option_info
    print("")
    solution = None
    objective = None

    # Solve the problem
    try:

        model.solve()
        status_code = model.solution.get_status()
        solver_info["status"] = status_code
        if status_code == 1 or status_code == 101:

            status = "optimal"
            solution = np.array(model.solution.get_values())
            objective = model.solution.get_objective_value()
        elif status_code == 2 or status_code == 118:

            status = "unbounded"
            objective = float('-inf')
        elif status_code == 3 or status_code == 103:

            status = "infeasible"
            objective = float('inf')
        elif status_code == 23 or status_code == 127:

            status = "feasible"
            solution = np.array(model.solution.get_values())
            objective = model.solution.get_objective_value()
        else:

            status = "unknown"
    except RuntimeError as e:

        print(e)
        status = "error"

    constraints_additional_information = dict()
    variables_additional_information = dict()
    if details:
        attributes_to_retrieve_constraints = [
                                              ["dual",
                                               model.solution.get_dual_values],
                                              ["slack",
                                               model.solution.get_linear_slacks],
                                              ]
        attributes_to_retrieve_variables = [
                                              ["basis",
                                               model.solution.basis.get_basis, 0],
                                              ["dual_norms",
                                               model.solution.basis.get_dual_norms,
                                               slice(0, 2)]
                                             ]

        for name, function in attributes_to_retrieve_constraints:
            try:
                constraints_additional_information[name] = function()
            except cplex.exceptions.errors.CplexSolverError:
                print("Unable to retrieve ", name, " information for constraints")

        for name, function, index in attributes_to_retrieve_variables:
            try:
                variables_additional_information[name] = function()[index]
            except cplex.exceptions.errors.CplexSolverError:
                print("Unable to retrieve ", name, " information for variables")

    return solution, objective, status, solver_info, \
           constraints_additional_information, \
           variables_additional_information
