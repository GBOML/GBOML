import numpy as np
from scipy.sparse import coo_matrix


def solver_xpress(matrix_a: coo_matrix, vector_b: np.ndarray, vector_c: np.ndarray, objective_offset: float,
                  name_tuples: list) -> tuple:
    try:

        import xpress as xp
    except ImportError:

        print("Warning: Did not find the CyLP package")
        exit(0)
    print("hi")

    model = xp.problem()
    matrix_a = matrix_a.astype(float)

    var_list = []
    is_milp = False
    for _, variable_indexes in name_tuples:

        for index, _, var_type, var_size in variable_indexes:

            if var_type == "integer":
                is_milp = True
                for _ in range(var_size):
                    var_list.append(xp.var(vartype=xp.integer, lb=float('-inf')))
            elif var_type == "binary":
                is_milp = True
                for _ in range(var_size):
                    var_list.append(xp.var(vartype=xp.binary))
            else:
                for _ in range(var_size):
                    var_list.append(xp.var(vartype=xp.continuous, lb=float('-inf')))
    var_array = np.array(var_list)
    model.addVariable(var_array)
    data, row, col = matrix_a.data, matrix_a.row, matrix_a.col
    nb_constraints, nb_vars = matrix_a.shape
    for index_constraint in range(nb_constraints):
        indexes = np.where(row == index_constraint)
        columns = col[indexes]
        lhs_constraint = xp.Dot(data[indexes], var_array[columns])
        model.addConstraint(lhs_constraint <= vector_b[index_constraint])

    objective = xp.Dot(vector_c, var_array) + objective_offset
    model.setObjective(objective)
    option_info = {}
    try:

        with open('xpress.opt', 'r') as optfile:

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

                            print("Skipping option \'%s\' with invalid given value \'%s\' (expected %s)"
                                  % (option[0], option[1], parinfo[1]))
                        else:

                            model.setControl(key, value)
                            option_info[key] = value
                    else:

                        print("Skipping option \'%s\' with no given value" % option[0])
                else:

                    print("Skipping unknown option \'%s\'" % option[0])

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

    solver_info = {"name": "xpress", "algorithm": "unknown", "status": status, "options": option_info}
    return solution, objective, status, solver_info


def solver_clp(matrix_a: coo_matrix, vector_b: np.ndarray, vector_c: np.ndarray, objective_offset: float,
               name_tuples: list) -> tuple:
    """
    solver_clp function: takes as input the matrix A, the vectors b and C. It returns the solution
    of the problem : min C^T x s.t. A x <= b
    found by the clp solver
    INPUT : A -> coo_matrix of constraints
            b -> np.ndarray of independant terms of each constraint
            C -> np.ndarray of objective vector
    """
    # CYLP IMPORT
    try:

        from cylp.cy import CyCbcModel, CyClpSimplex
        from cylp.py.modeling.CyLPModel import CyLPModel, CyLPArray
    except ImportError:

        print("Warning: Did not find the CyLP package")
        exit(0)

    model = CyLPModel()
    # Compute model info
    nvars = np.shape(vector_c)[1]
    # solver = CyClpSimplex()
    additional_var_bool = False
    if nvars == 1:

        additional_var_bool = True
        nvars = 2
        line, col = matrix_a.shape
        matrix_a = coo_matrix((matrix_a.data, (matrix_a.row, matrix_a.col)), shape=(line, col+1))
        vector_c = np.append(vector_c[0], [0])
    # Build CLP model
    c = CyLPArray(vector_c)
    variables = model.addVariable('variables', nvars, isInt=False)
    model.addConstraint(matrix_a * variables <= vector_b)
    model.objective = c * variables
    print("model object " + str(type(model.objective)))
    # Solve model
    s = CyClpSimplex(model)
    for _, variable_indexes in name_tuples:

        for index, _, var_type, var_size in variable_indexes:

            if var_type == "integer":

                s.setInteger(variables[index:index+var_size])
            if var_type == "binary":

                s.setInteger(variables[index:index+var_size])
                s += 0.0 <= variables[index:index+var_size] <= 1
    cbc_model = s.getCbcModel()
    cbc_model.solve()
    # Return solution
    solver_info = {}
    solver_info["name"] = "clp"
    solver_info["algorithm"] = "primal simplex"
    solver_info["status"] = cbc_model.status
    solution = None
    objective = None
    status_code = cbc_model.status
    if status_code == "solution":

        status = "optimal"
        solution = cbc_model.primalVariableSolution['variables']
        if additional_var_bool:

            solution = solution[0:len(solution)-1]
        objective = cbc_model.objectiveValue + objective_offset
    elif status_code == "unset":

        status = "unbounded"
        objective = float('-inf')
    elif status_code == 'relaxation infeasible':

        status = "infeasible"
        objective = float("inf")
    else:

        status = "unknown"
    return solution, objective, status, solver_info


def solver_gurobi(matrix_a: coo_matrix, vector_b: np.ndarray, vector_c: np.ndarray,
                  objective_offset: float, name_tuples: dict) -> tuple:
    """
    solver_gurobi function: takes as input the matrix A, the vectors b and C. It returns the solution
    of the problem : min C^T x s.t. A x <= b
    found by the gurobi solver
    INPUT : A -> coo_matrix of constraints
            b -> np.ndarray of independant terms of each constraint
            C -> np.ndarray of objective vector
    """

    # GUROBI IMPORT
    try:

        import gurobipy as grbp
        from gurobipy import GRB
    except ImportError:

        print("Warning: Did not find the gurobipy package")
        exit(0)
    solution = None
    objective = None
    # Build Gurobi model
    matrix_a = matrix_a.astype(float)
    _, n = np.shape(matrix_a)
    b = vector_b.reshape(-1)
    vector_c = vector_c.reshape(-1)
    model = grbp.Model()
    x = model.addMVar(shape=n, lb=-float('inf'), ub=float('inf'), vtype=GRB.CONTINUOUS, name="x")
    model.addMConstr(matrix_a, x, '<', b)
    model.setObjective(vector_c @ x + objective_offset, GRB.MINIMIZE)
    for _, variable_indexes in name_tuples:

        for index, _, var_type, var_size in variable_indexes:

            if var_type == "integer":

                x[index:index+var_size].vtype = GRB.INTEGER
            if var_type == "binary":

                x[index:index+var_size].vtype = GRB.BINARY
    solver_info = dict()
    solver_info["name"] = "gurobi"
    print("\nReading Gurobi options from file gurobi.opt")
    option_info = {}
    try:

        with open('gurobi.opt', 'r') as optfile:

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

    return solution, objective, status, solver_info


def solver_cplex(matrix_a: coo_matrix, vector_b: np.ndarray, vector_c: np.ndarray,
                 objective_offset: float, name_tuples: dict) -> tuple:
    """
    solver_cplex function: takes as input the matrix A, the vectors b and C. It returns the solution
    of the problem : min C^T x s.t. A x <= b
    found by the cplex solver
    INPUT : A -> coo_matrix of constraints
            b -> np.ndarray of independant terms of each constraint
            C -> np.ndarray of objective vector
    """
    try:

        import cplex   
    except ImportError:

        print("Warning: Did not find the CPLEX package")
        exit(0)

    matrix_a_zipped = zip(matrix_a.row.tolist(), matrix_a.col.tolist(), matrix_a.data)
    m, n = np.shape(matrix_a)
    vector_b = list(vector_b.reshape(-1))
    vector_c = vector_c.tolist()[0]
    model = cplex.Cplex()
    model.variables.add(obj=vector_c, lb=[-cplex.infinity]*n, ub=[cplex.infinity]*n)
    for _, variable_indexes in name_tuples:

        for index, _, var_type, var_size in variable_indexes:
            
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
    solver_info = {}
    solver_info["name"] = "cplex"
    print("\nReading CPLEX options from file cplex.opt")
    option_info = {}
    try:

        with open('cplex.opt', 'r') as optfile:

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

                            print("Skipping option \'%s\' with invalid given value \'%s\' (expected %s)"
                                  % (option[0], option[1], key.type()))
                        else:

                            name = key.__repr__().split(".", 1)[1]
                            print("Setting option \'%s\' to value \'%s\'"
                                  % (name, value))
                            key.set(value)
                            option_info[name] = value
                    else:

                        print("Skipping option \'%s\' with no given value" % option[0])
    solver_info["options"] = option_info
    print("")
    solution = None
    objective = None
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
    return solution, objective, status, solver_info


def solver_scipy(matrix_a: coo_matrix, vector_b: np.ndarray, vector_c: np.ndarray,
                 objective_offset: float, name_tuples: dict) -> tuple:
    """
    solver_scipy function: takes as input the matrix A, the vectors b and C. It returns the solution
    of the problem : min C^T x s.t. A x <= b
    found by the scipy linprog solver
    INPUT : A -> coo_matrix of constraints
            b -> np.ndarray of independant terms of each constraint
            C -> np.ndarray of objective vector
    """
    # LINPROG IMPORT
    from scipy.optimize import linprog
    x0_bounds = (None, None)
    result = linprog(vector_c, A_ub=matrix_a.toarray(), b_ub=vector_b, bounds=x0_bounds,
                     options={"lstsq": True, "disp": True, "cholesky": False, "sym_pos": False})
    solver_info = {}
    solver_info["name"] = "linprog"
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
