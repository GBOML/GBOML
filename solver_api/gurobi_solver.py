"""Gurobi Solver file, contains the interface to Gurobi solver .

Takes the matrix A, the vector b and vector c as input of the problem
    min : c^T * X s.t. A * X <= b
and passes it to the gurobi solver.

  Typical usage example:

   solution, objective, status, solver_info = gurobi_solver(matrix_a, vector_b, vector_c,
                                                            objective_offset, name_tuples)
   print("the solution is "+str(solution))
   print("the objective found : "+str(objective))
"""

import numpy as np
from scipy.sparse import coo_matrix


def gurobi_solver(matrix_a: coo_matrix, vector_b: np.ndarray, vector_c: np.ndarray,
                  objective_offset: float, name_tuples: dict, factor_map: dict) -> tuple:
    """gurobi_solver

        takes as input the matrix A, the vectors b and c. It returns the solution
        of the problem : min c^T * x s.t. A * x <= b found by the gurobi solver

        Args:
            A -> coo_matrix of constraints
            b -> np.ndarray of independent terms of each constraint
            c -> np.ndarray of objective vector
            objective_offset -> float of the objective offset
            name_tuples -> dictionary of <node_name variables> used to get the type

        Returns:
            solution -> np.ndarray of the flat solution
            objective -> float of the objective value
            status -> solution status
            solver_info -> dictionary of solver information

    """

    try:
        import gurobipy as grbp
        from gurobipy import GRB

    except ImportError:
        print("Warning: Did not find the gurobipy package")
        exit(0)

    print(factor_map)

    solution = None
    objective = None

    # Fix shapes and types of input
    matrix_a = matrix_a.astype(float)
    _, n = np.shape(matrix_a)
    b = vector_b.reshape(-1)
    vector_c = vector_c.reshape(-1)

    # Build Gurobi model
    model = grbp.Model()
    x = model.addMVar(shape=n, lb=-float('inf'), ub=float('inf'), vtype=GRB.CONTINUOUS, name="x")
    model.addMConstr(matrix_a, x, '<', b)
    model.setObjective(vector_c @ x + objective_offset, GRB.MINIMIZE)

    for _, variable_indexes in name_tuples:

        for index, _, var_type, var_size in variable_indexes:

            if var_type == "integer":
                x[index:index + var_size].vtype = GRB.INTEGER
            if var_type == "binary":
                x[index:index + var_size].vtype = GRB.BINARY

    # Gather and retrieve solver information
    solver_info = dict()
    solver_info["name"] = "gurobi"
    print("\nReading Gurobi options from file gurobi.opt")
    option_info = {}

    try:

        with open('solver_api/gurobi.opt', 'r') as optfile:
            lines = optfile.readlines()
    except IOError:

        print("Options file not found")
    else:

        for line in lines:

            line = line.strip()
            option = line.split(" ", 1)
            if option[0] != "":

                parinfo = model.getParamInfo(option[0])
                if parinfo:

                    if len(option) == 2:

                        key = option[0]
                        try:

                            value = parinfo[1](option[1])
                        except ValueError as e:

                            print("Skipping option \'%s\' with invalid given value \'%s\' (expected %s)"
                                  % (option[0], option[1], parinfo[1]))
                        else:

                            model.setParam(key, value)
                            option_info[key] = value
                    else:

                        print("Skipping option \'%s\' with no given value" % option[0])
                else:

                    print("Skipping unknown option \'%s\'" % option[0])

    solver_info["options"] = option_info
    print("")

    # Solve model and return solution
    try:

        model.optimize()
        status_code = model.getAttr("Status")
        solver_info["status"] = status_code
        solution = None
        objective = None
        if status_code == 2:

            status = "optimal"
            solution = x.X
            objective = model.getObjective().getValue()
        elif status_code == 3:

            status = "infeasible"
            objective = float('inf')
        elif status_code == 5:

            status = "unbounded"
            objective = float('-inf')
        elif status_code == 13:

            status = "feasible"
            solution = x.X
            objective = model.getObjective().getValue()
        else:

            status = "unknown"
    except RuntimeError as e:

        print(e)
        status = "error"

    constraints_additional_information = dict()
    variables_additional_information = dict()
    attributes_to_retrieve_constraints = ["Pi", "CBasis", "SARHSLow", "SARHSUp"]
    attributes_to_retrieve_variables = ["VBasis", "SAObjLow", "SAObjUp", "SALBLow", "SALBUp", "SAUBLow", "SAUBUp"]

    for attribute in attributes_to_retrieve_constraints:
        try:
            constraints_additional_information[attribute] = model.getAttr(attribute, model.getConstrs())
        except grbp.GurobiError:
            print("Warning : Unable to retrieve ", attribute, " information for constraints")

    factor_add_info = {}
    for node_name in factor_map.keys():
        node_dict = {}
        for constraint_name in factor_map[node_name].keys():
            range_concerned = factor_map[node_name][constraint_name]
            print(range_concerned)
            constraint_attributes = {}
            for attribute in constraints_additional_information.keys():
                constraint_attributes[attribute] = constraints_additional_information[attribute][range_concerned]

            node_dict[constraint_name] = constraint_attributes
        factor_add_info[node_name] = node_dict
    print(factor_add_info)

    for attribute in attributes_to_retrieve_variables:
        try:
            variables_additional_information[attribute] = model.getAttr(attribute, model.getVars())
        except grbp.GurobiError:
            print("Warning : Unable to retrieve ", attribute, " information for variables")

    return solution, objective, status, solver_info, constraints_additional_information, \
           variables_additional_information
