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
from gboml.compiler.utils import flat_nested_list_to_two_level, read_attributes_in_file
import os

def xpress_solver(matrix_a_eq: coo_matrix, vector_b_eq: np.ndarray,
                  matrix_a_ineq: coo_matrix, vector_b_ineq: np.ndarray,
                  vector_c: np.ndarray, objective_offset: float,
                  name_tuples: list,
                  opt_file: str = None,
                  details = False) -> tuple:
    """xpress_solver

        takes as input the matrix A, the vectors b and c. It returns
        the solution of the problem : min c^T * x s.t. A * x <= b found
        by the xpress solver

        Args:
            matrix_a_eq -> coo_matrix of equality constraints
            vector_b_eq -> np.ndarray of independent terms of each equality constraint
            matrix_a_ineq -> coo_matrix of inequality constraints
            vector_b_eq -> np.ndarray of independent terms of each inequality constraint
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
    matrix_a_eq = matrix_a_eq.astype(float)
    matrix_a_ineq = matrix_a_ineq.astype(float)
    _, nb_columns = vector_c.shape

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
    nb_constraints_ineq, _ = matrix_a_ineq.shape
    csr_matrix_a_ineq = matrix_a_ineq.tocsr()
    csr_data, csr_indices, csr_ptr = csr_matrix_a_ineq.data, \
                                     csr_matrix_a_ineq.indices, \
                                     csr_matrix_a_ineq.indptr

    for i in range(nb_constraints_ineq):
        pt = slice(csr_ptr[i], csr_ptr[i+1])
        columns = csr_indices[pt]
        values = csr_data[pt]
        lhs_constraint = xp.Dot(np.array(values), var_array[columns])
        model.addConstraint(lhs_constraint <= vector_b_ineq[i])

    nb_constraints_eq, _ = matrix_a_eq.shape
    csr_matrix_a_eq = matrix_a_eq.tocsr()
    csr_data, csr_indices, csr_ptr = csr_matrix_a_eq.data, \
                                     csr_matrix_a_eq.indices, \
                                     csr_matrix_a_eq.indptr
    for i in range(nb_constraints_eq):
        pt = slice(csr_ptr[i], csr_ptr[i+1])
        columns = csr_indices[pt]
        values = csr_data[pt]
        lhs_constraint = xp.Dot(np.array(values), var_array[columns])
        model.addConstraint(lhs_constraint == vector_b_eq[i])

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
                            value = int(option[1])
                            model.setControl(key, value)
                        except ValueError as e:

                            print("Skipping option \'%s\' with invalid "
                                  "given value \'%s\' (expected %s)"
                                  % (option[0], option[1], parinfo[1]))
                        else:
                            
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
    constraints_additional_info_ineq = dict()
    constraints_additional_info_eq = dict()

    if details is not False:
        if isinstance(details, str):
            attributes_to_get = read_attributes_in_file(details)
        else:
            attributes_to_get = ["dual", "slack", "reduced_cost"]

        attributes_constraints = {"dual": model.getDual,
                                  "slack": model.getSlack
                                 }
        attributes_variables = {"reduced_cost": model.getRCost
                                }
        for attr_name in attributes_to_get:
            if attr_name in attributes_constraints.keys():
                function = attributes_constraints[attr_name]
                try:
                    constr_attribute_info = function()
                    constraints_additional_info_ineq[attr_name] = constr_attribute_info[:nb_constraints_ineq]
                    constraints_additional_info_eq[attr_name] = constr_attribute_info[nb_constraints_ineq:]
                except RuntimeError:
                    print("Unable to retrieve ", attr_name, " information for constraints")
            elif attr_name in attributes_variables.keys():
                function = attributes_variables[attr_name]
                try:
                    variables_additional_information[attr_name] = function()
                except RuntimeError:
                    print("Unable to retrieve ", attr_name, " information for variables")
            else:
                print("Warning : Unable to retrieve ", attr_name,
                      " information")

    constraints_additional_information = {"eq": constraints_additional_info_eq,
                                          "ineq": constraints_additional_info_ineq}

    return solution, objective, status, solver_info, \
           constraints_additional_information, \
           variables_additional_information
