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
from gboml.compiler.utils import flat_nested_list_to_two_level, read_attributes_in_file

import numpy as np
from scipy.sparse import coo_matrix
import time
import os

def get_parameter_recursively(parameter_name, parameters):
    nb_values = len(parameter_name.split(".", 1))
    if nb_values == 1:
        key = getattr(parameters, parameter_name)
        return key
    else:
        file, rest = parameter_name.split(".", 1)
        key = getattr(parameters, file)
        return get_parameter_recursively(rest, key)


def cplex_solver(matrix_a_eq: coo_matrix, vector_b_eq: np.ndarray,
                 matrix_a_ineq: coo_matrix, vector_b_ineq: np.ndarray,
                 vector_c: np.ndarray,
                 objective_offset: float,
                 name_tuples: dict,
                 opt_file: str = None,
                 details=False,
                 option_dict: dict = None) -> tuple:
    """cplex_solver

        takes as input the matrix A, the vectors b and c. It returns
        the solution of the problem : min c^T * x s.t. A * x <= b found
        by the cplex solver

        Args:
            matrix_a_eq -> coo_matrix of equality constraints
            vector_b_eq -> np.ndarray of independent terms of each equality constraint
            matrix_a_ineq -> coo_matrix of inequality constraints
            vector_b_eq -> np.ndarray of independent terms of each inequality constraint
            c -> np.ndarray of objective vector
            objective_offset -> float of the objective offset
            name_tuples -> dictionary of <node_name variables> used
                           to get the type
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
    try:

        import cplex
    except ImportError:

        print("Warning: Did not find the CPLEX package")
        exit(0)

    if opt_file is None:
        opt_file = 'src/gboml/solver_api/cplex.opt'

    line_ineq, _ = np.shape(matrix_a_ineq)
    line_eq, _ = np.shape(matrix_a_eq)
    matrix_a_row = matrix_a_eq.row + line_ineq
    # Convert to appropriate structure
    matrix_a_zipped = zip(matrix_a_ineq.row.tolist()+matrix_a_row.tolist(),
                          matrix_a_ineq.col.tolist()+matrix_a_eq.col.tolist(),
                          np.concatenate((matrix_a_ineq.data, matrix_a_eq.data)))


    vector_b = np.concatenate((vector_b_ineq, vector_b_eq))
    vector_b = list(vector_b.reshape(-1))
    _, nb_col = vector_c.shape
    vector_c = vector_c.tolist()[0]
    # Generate model
    model = cplex.Cplex()
    model.variables.add(obj=vector_c, lb=[-cplex.infinity]*nb_col,
                        ub=[cplex.infinity]*nb_col)
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

    model.linear_constraints.add(senses=['L']*line_ineq+['E']*line_eq, rhs=vector_b)
    model.linear_constraints.set_coefficients(matrix_a_zipped)
    model.objective.set_sense(model.objective.sense.minimize)
    model.objective.set_offset(objective_offset)

    # Retrieve solver information
    solver_info = {"name": "cplex"}
    print("\nReading CPLEX options from file cplex.opt")
    option_info = {}
    new_dict_options_from_file = option_dict.copy()
    try:

        with open(opt_file, 'r') as optfile:

            lines = optfile.readlines()
    except IOError:

        print("Options file not found")
    else:
        for line in lines:

            line = line.strip()
            option = line.split(" ", 1)
            if option[0] != "" and option[0] not in new_dict_options_from_file :
                if len(option) == 2:
                    new_dict_options_from_file[option[0]] = option[1]
                else:
                    print("Skipping option \'%s\' with no given value"
                          % option[0])
            else:
                print("Skipping option \'%s\' as redefined in function call"
                      % option[0])


    for option_name, option_value in new_dict_options_from_file.items():
        try:
            key = get_parameter_recursively(option_name, model.parameters)
            assert(isinstance(key, cplex._internal._parameter_classes.Parameter))
        except AttributeError as e:

            print("Skipping unknown option \'%s\'" % option_name)
        except AssertionError as e:
            print("Skipping unknown option \'%s\'" % option_name)
        else:
                try:
                    value = key.type()(option_value)
                except ValueError as e:

                    print("Skipping option \'%s\' "
                          "with invalid given value \'%s\' "
                          "(expected %s)"
                          % (option_name, option_value, key.type()))
                else:

                    name = key.__repr__().split(".", 1)[1]
                    print("Setting option \'%s\' to value \'%s\'"
                          % (name, value))
                    key.set(value)
                    option_info[name] = value


    solver_info["options"] = option_info
    solution = None
    objective = None

    # Solve the problem
    try:

        model.solve()
        status_code = model.solution.get_status()
        solver_info["status"] = status_code

        stopped = [102, 10, 11, 12, 13, 107]
        if status_code == 1 or status_code == 101:

            status = "optimal"
            solution = np.array(model.solution.get_values())
            objective = model.solution.get_objective_value()

        elif status_code in stopped:
            status = "sub-optimal stopped"
            solution = np.array(model.solution.get_values())
            objective = model.solution.get_objective_value()

        elif status_code == 2 or status_code == 118:

            status = "unbounded"
            objective = float('-inf')
        elif status_code == 3 or status_code == 103 or status_code == 108:

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
    constraints_additional_info_ineq = dict()
    constraints_additional_info_eq = dict()

    if details is not False:
        if isinstance(details, str):
            attributes_to_get = read_attributes_in_file(details)
        else:
            attributes_to_get = ["dual", "slack", "basis", "dual_norms"]

        attributes_constraints = {"dual": model.solution.get_dual_values,
                                  "slack": model.solution.get_linear_slacks}
        attributes_variables = {"reduced_cost": [model.solution.get_reduced_costs, slice(None)],
                                "basis": [model.solution.basis.get_basis, 0],
                                "dual_norms": [model.solution.basis.get_dual_norms, slice(0, 2)]}
        for attr_name in attributes_to_get:
            if attr_name in attributes_constraints.keys():
                function = attributes_constraints[attr_name]
                try:
                    constr_attribute_info = function()
                    constraints_additional_info_ineq[attr_name] = constr_attribute_info[:line_ineq]
                    constraints_additional_info_eq[attr_name] = constr_attribute_info[line_ineq:]
                except cplex.exceptions.errors.CplexSolverError:
                    print("Unable to retrieve ", attr_name, " information for constraints")
            elif attr_name in attributes_variables.keys():
                function, index = attributes_variables[attr_name]
                try:
                    variables_additional_information[attr_name] = function()[index]
                except cplex.exceptions.errors.CplexSolverError:
                    print("Unable to retrieve ", attr_name, " information for variables")
            else:
                print("Warning : Unable to retrieve ", attr_name,
                      " information")

    constraints_additional_information = {"eq": constraints_additional_info_eq,
                                          "ineq": constraints_additional_info_ineq}
    return solution, objective, status, solver_info, \
           constraints_additional_information, \
           variables_additional_information
