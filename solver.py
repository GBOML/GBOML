import numpy as np
import time 
from scipy.sparse import coo_matrix

def solver_clp(A:coo_matrix,b:np.ndarray,C:np.ndarray)->tuple:
    """
	solver_clp function: takes as input the matrix A, the vectors b and C. It returns the solution
    of the problem : min C^T x s.t. A x <= b
    found by the clp solver
    INPUT : A -> coo_matrix of constraints
            b -> np.ndarray of independant terms of each constraint
            C -> np.ndarray of objective vector
    """
    #CYLP IMPORT
    try:
        from cylp.cy import CyClpSimplex
        from cylp.py.modeling.CyLPModel import CyLPArray
    except:
        print("Warning: Did not find the CyLP package")
        exit(0)

    # Initialize local time
    start_time = time.time()

    # Compute model info
    nvars = np.shape(C)[1]

    # Build CLP model
    c = CyLPArray(C)
    solver = CyClpSimplex()
    variables = solver.addVariable('variables', nvars)
    solver.addConstraint(A * variables <= b)

    if nvars == 1:
        solver.objectiveCoefficients = np.array([np.squeeze(C)])
    else:
        solver.objective = c * variables

    # Solve model
    solver.primal()

    # Return solution
    solver_info = {}
    solver_info["name"] = "clp"
    solver_info["algorithm"] = "primal simplex"
    solver_info["status"] = solver.getStatusString()

    solution = None
    objective = None
    status_code = solver.getStatusCode()
    if status_code == -1:
        status = "unknown"
    elif status_code == 0:
        status = "optimal"
        solution = solver.primalVariableSolution['variables']
        objective = solver.objectiveValue
    elif status_code == 1:
        status = "infeasible"
        objective = float('inf')
    elif status_code == 2:
        status = "unbounded"
        objective = float('-inf')
    elif status_code == 3:
        status = "unknown"
    elif status_code == 4:
        status = "error"
    elif status_code == 5:
        status = "unknown"
    else:
        status = "unknown"

    return solution, objective, status, solver_info

def solver_gurobi(A:coo_matrix,b:np.ndarray,C:np.ndarray)->tuple:
    """
	solver_gurobi function: takes as input the matrix A, the vectors b and C. It returns the solution
    of the problem : min C^T x s.t. A x <= b
    found by the gurobi solver
    INPUT : A -> coo_matrix of constraints
            b -> np.ndarray of independant terms of each constraint
            C -> np.ndarray of objective vector
    """

    #GUROBI IMPORT
    try:
        import gurobipy as grbp
        from gurobipy import GRB
    except:
        print("Warning: Did not find the gurobipy package")
        exit(0)

    solution = None
    objective = None

    # Build Gurobi model
    A = A.astype(float)
    _, n = np.shape(A)
    b = b.reshape(-1)
    C = C.reshape(-1)

    model = grbp.Model()
    x = model.addMVar(shape=n, lb=-float('inf'), ub=float('inf'), vtype=GRB.CONTINUOUS, name="x")
    model.addMConstr(A, x, '<', b)
    model.setObjective(C @ x, GRB.MINIMIZE)
    model.setParam('Method',2)          # uses a barrier method
    model.setParam('BarHomogeneous',1)  # uses a barrier variant with better numerical stability
    model.setParam('Crossover',0)       # disables crossover (returns a nonbasic solution)

    # Solve model and return solution
    try:
        model.optimize()

        solver_info = {}
        solver_info["name"] = "gurobi"
        solver_info["algorithm"] = "barrier"
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

def solver_cplex(A:coo_matrix,b:np.ndarray,C:np.ndarray)->tuple:
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
    except:
        print("Warning: Did not find the CPLEX package")
        exit(0)

    A_zipped = zip(A.row.tolist(), A.col.tolist(), A.data)
    m, n = np.shape(A)
    b = list(b.reshape(-1))
    C = C.tolist()[0]

    model = cplex.Cplex()

    model.variables.add(obj=C,lb=[-cplex.infinity]*n,ub=[cplex.infinity]*n)
    model.linear_constraints.add(senses=['L']*m,rhs=b)
    model.linear_constraints.set_coefficients(A_zipped)
    model.objective.set_sense(model.objective.sense.minimize)
    alg = model.parameters.lpmethod.values
    model.parameters.lpmethod.set(alg.barrier)    # uses a barrier method
    model.parameters.solutiontype.set(2)
    #model.parameters.barrier.crossover.set(model.parameters.barrier.crossover.values.none)    # disables crossover (yields a nonbasic solution)

    try:
        model.solve()

        solver_info = {}
        solver_info["name"] = "cplex"
        solver_info["algorithm"] = "barrier"
        status_code = model.solution.get_status()
        solver_info["status"] = status_code

        solution = None
        objective = None
        if status_code == 1 or status_code == 101:
            status = "optimal"
            solution = np.array(model.solution.get_values())
            objective = model.solution.get_objective_value()
        else:
            status = "unknown"
    except RuntimeError as e:
        print(e)
        status = "error"

    return solution, objective, status, solver_info

def solver_scipy(A:coo_matrix,b:np.ndarray,C:np.ndarray)->tuple:
    """
	solver_scipy function: takes as input the matrix A, the vectors b and C. It returns the solution
    of the problem : min C^T x s.t. A x <= b
    found by the scipy linprog solver
    INPUT : A -> coo_matrix of constraints
            b -> np.ndarray of independant terms of each constraint
            C -> np.ndarray of objective vector
    """
    #LINPROG IMPORT
    from scipy.optimize import linprog

    x0_bounds = (None, None)
    result = linprog(C, A_ub=A.toarray(), b_ub=b,bounds = x0_bounds,options={"lstsq":True,"disp": True,"cholesky":False,"sym_pos":False,})

    solver_info = {}
    solver_info["name"] = "linprog"
    solver_info["algorithm"] = "unknown"
    status_flag = result.success
    solver_info["status"] = status_flag

    solution = None
    objective = None
    if status_flag:
        status = "optimal"
        solution = result.x
        objective = result.fun
    else:
        status = "unknown"

    return solution, objective, status, solver_info
