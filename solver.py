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

    # Initialize return values
    x = None
    solved = False
    # Initialize local time
    start_time = time.time()

    # Compute model info
    nvars = np.shape(C)[1]
    print(np.shape(C))
    print('\033[93m', "DEBUG: CLP number of variables: %d" % nvars, '\033[0m')

    # Build CLP model
    c = CyLPArray(C)
    solver = CyClpSimplex()
    variables = solver.addVariable('variables', nvars)
    print(type(variables))
    solver.addConstraint(A * variables <= b)

    if nvars == 1:
        solver.objectiveCoefficients = np.array([np.squeeze(C)])
    else:
        solver.objective = c * variables

    print('\033[93m', "DEBUG: CLP translation time: %s seconds" % (time.time() - start_time), '\033[0m')

    # Solve model
    solver.primal()

    # Return solution
    x = solver.primalVariableSolution['variables']
    obj = solver.objectiveValue

    if solver.getStatusCode() == 0:
        solved = True
    print('\033[93m', "DEBUG: CLP solver status: %s" % solver.getStatusString(), '\033[0m')
    print('\033[93m', "DEBUG: CLP return x:", '\033[0m')
    print('\033[93m', x, '\033[0m')
    print('\033[93m', "DEBUG: CLP return obj: %s" % obj, '\033[0m')
    print('\033[93m', "DEBUG: CLP return solved: %s" % solved, '\033[0m')
    print('\033[93m', "DEBUG: CLP total time: %s seconds" % (time.time() - start_time), '\033[0m')
    print('\033[93m', "DEBUG: CLP iteration: %s" % solver.iteration, '\033[0m')

    solver_info = {}
    solver_info["name"] = "clp"
    solver_info["algorithm"] = "primal simplex"
    return x, obj, solved, solver_info

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

    try:
        model.optimize()
        if model.getAttr("Status") == 2:
            flag_solved = True
            solution = x.X
            objective = model.getObjective().getValue()
        else:
            flag_solved = False
    except RuntimeError as e:
        print(e)
        flag_solved = False

    solver_info = {}
    solver_info["name"] = "gurobi"
    solver_info["algorithm"] = "unknown"
    return solution,objective,flag_solved,solver_info

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
    solution = None
    objective = None
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
        if model.solution.get_status()==1 or model.solution.get_status()==101:
            flag_solved = True
            solution = np.array(model.solution.get_values())
            objective = model.solution.get_objective_value()
        else:
            flag_solved = False
    except RuntimeError as e:
        print(e)
        flag_solved = False

    solver_info = {}
    solver_info["name"] = "cplex"
    solver_info["algorithm"] = "unknown"
    return solution, objective, flag_solved,solver_info

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
    solution = linprog(C, A_ub=A.toarray(), b_ub=b,bounds = x0_bounds,options={"lstsq":True,"disp": True,"cholesky":False,"sym_pos":False,})
    solver_info = {}
    solver_info["name"] = "linprog"
    solver_info["algorithm"] = "unknown"
    return solution.x, solution.fun, solution.success, solver_info
