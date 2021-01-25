
# main.py
#
# Writer : MIFTARI B - BERGER M
# ------------

from gboml_lexer import tokenize_file
from gboml_parser import parse_file
from gboml_semantic import semantic
from matrixGeneration import matrix_generationAb,matrix_generationC
import argparse
import time
from scipy.optimize import linprog
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
#from cylp.cy import CyClpSimplex
#from cylp.py.modeling.CyLPModel import CyLPArray
import sys
#from julia.api import Julia
#jpath = "/Applications/Julia-1.5.app/Contents/Resources/julia/bin/julia"
#jl = Julia(runtime=jpath,compiled_modules=False)
from julia import Main
import pandas as pd
import os
import json
import gurobipy as grbp
from gurobipy import GRB
#import cplex


def solver_clp(A,b,C):
    # Initialize return values
    x = None
    flag_solved = False

    # Initialize local time
    start_time = time.time()

    # Compute model info
    nvars = np.shape(C)[1]
    print('\033[93m', "DEBUG: CLP number of variables: %d" % nvars, '\033[0m')

    # Build CLP model
    solver = CyClpSimplex()
    variables = solver.addVariable('variables', nvars)

    solver.addConstraint(A * variables <= b)
    solver.objective = C * variables

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

def solver_gurobi(A, b, c):
    A = A.astype(float)
    _, n = np.shape(A)
    b = b.reshape(-1)
    c = c.reshape(-1)

    model = grbp.Model()
    x = model.addMVar(shape=n, lb=-float('inf'), ub=float('inf'), vtype=GRB.CONTINUOUS, name="x")
    model.addMConstr(A, x, '<', b)
    model.setObjective(c @ x, GRB.MINIMIZE)
    model.setParam('Method',2)          # uses a barrier method
    model.setParam('BarHomogeneous',1)  # uses a barrier variant with better numerical stability
    model.setParam('Crossover',0)       # disables crossover (returns a nonbasic solution)

    try:
        model.optimize()
        if model.getAttr("Status") == 2:
            flag_solved = True
        else:
            flag_solved = False
    except RuntimeError as e:
        print(e)
        flag_solved = False
    return x.X,flag_solved

def solver_cplex(A, b, c):

    A_zipped = zip(A.row.tolist(), A.col.tolist(), A.data)
    m, n = np.shape(A)
    b = list(b.reshape(-1))
    c = c.tolist()[0]

    model = cplex.Cplex()
    model.variables.add(obj=c,lb=[-cplex.infinity]*n,ub=[cplex.infinity]*n)
    model.linear_constraints.add(senses=['L']*m,rhs=b)
    model.linear_constraints.set_coefficients(A_zipped)
    model.objective.set_sense(model.objective.sense.minimize)
    alg = model.parameters.lpmethod.values
    model.parameters.lpmethod.set(alg.barrier)    # uses a barrier method
    model.parameters.barrier.crossover.set(model.parameters.barrier.crossover.values.none)    # disables crossover (yields a nonbasic solution)

    try:
        model.solve()
        if model.solution.get_status()==1 or model.solution.get_status()==101:
            flag_solved = True
        else:
            flag_solved = False
    except RuntimeError as e:
        print(e)
        flag_solved = False
    return model.solution.get_values(),flag_solved

def solver_scipy(A,b,C):
    x0_bounds = (None, None)
    solution = linprog(C_sum, A_ub=A.toarray(), b_ub=b,bounds = x0_bounds,options={"lstsq":True,"disp": True,"cholesky":False,"sym_pos":False,})
    solver_info = {}
    solver_info["name"] = "linprog"
    return solution.x, solution.fun, solution.success, solver_info

def solver_julia_2(A,b,C):
    #number_elements = len(A.row)
    #print(number_elements)
    constraint_matrix = np.array([A.row+1,A.col+1,A.data])
    #constraint_matrix[:,0] = A.row
    #constraint_matrix[:,1] = A.col
    #constraint_matrix[:,2] = A.data

    b = b.reshape((-1,1))
    C = C.reshape((-1,1))
    A = A.astype(float)
    optimal = None
    status = False
    x = None

    Main.include("linear_solver.jl") # load the MyFuncs module
    try :
        x, optimal ,status= Main.lin_solve_sparse(C.astype(float),constraint_matrix.astype(float),b.astype(float))
    except RuntimeError as e:
        print(e)
    return x, optimal ,status

    #print(constraint_matrix)

def convert_dictionary(x,T,name_tuples,optimal,status,program_dict):
    dictionary = program_dict
    dictionary["version"] = "0.0.0"
    dictionary["objective"] = optimal
    dictionary["status"] = status
    dictionary_nodes = dictionary["nodes"]
    for node_name,index_variables in name_tuples:
        dico_node = dictionary_nodes[node_name]
        dico_variables = {}
        for index,variable in index_variables:
            dico_variables[variable] = x[index:(index+T)].flatten().tolist()
        dico_node["variables"] = dico_variables
        dictionary_nodes[node_name]=dico_node

    dictionary["nodes"]= dictionary_nodes
    return dictionary

def convert_pandas(x,T,name_tuples):
    ordered_values = []
    columns = []

    for node_name,index_variables in name_tuples:
        for index,variable in index_variables:
            full_name = str(node_name)+"."+str(variable)
            values = x[index:(index+T)].flatten()
            columns.append(full_name)
            ordered_values.append(values)

    df = pd.DataFrame(ordered_values,index=columns)
    return df.T


def compile_file(directory,file,log=False):
    if log == True:
        filename_split = file.rsplit('.', 1)
        filename = filename_split[0]
        f = open(filename+".out", 'w')
        sys.stdout = f

    path = os.path.join(directory,file)
    result = parse_file(path)
    program = semantic(result)
    A,b,name_tuples = matrix_generationAb(program)
    C = matrix_generationC(program)
    C_sum = C.sum(axis=0)
    x,_ = solver_julia_2(A,b,C_sum)
    T = program.get_time().get_value()
    panda_datastruct = convert_pandas(x,T,name_tuples)

    filename_split = file.split(".")
    filename = filename_split[0]


    panda_datastruct.to_csv(filename+".csv")



if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Compiler and solver for the generic system model language')
    parser.add_argument( "input_file", type = str)

    parser.add_argument("--lex",help="Prints all tokens found in input file",action='store_const',const=True)
    parser.add_argument("--parse",help="Prints the AST",action='store_const',const=True)
    parser.add_argument("--matrix",help="Prints matrix representation",action='store_const',const=True)

    parser.add_argument("--json", help="Convert results to JSON format",action='store_const',const=True)
    parser.add_argument("--csv", help="Convert results to CSV format",action='store_const',const=True)

    parser.add_argument("--linprog",help = "Scipy linprog solver",action='store_const',const=True)

    parser.add_argument("--jump",help = "JuMP + Gurobi solver",action='store_const',const=True)
    parser.add_argument("--gurobi",help = "Gurobi solver",action='store_const',const=True)
    parser.add_argument("--cplex",help = "Cplex solver",action='store_const',const=True)
    parser.add_argument("--clp",help = "CLP solver",action='store_const',const=True)

    parser.add_argument("--log",help="Get log in a file",action="store_const",const=True)

    args = parser.parse_args()

    if args.linprog==False:
        print("The default solver is GUROBI")

    if args.input_file:
        if args.log == True:
            filename_split = args.input_file.rsplit('.', 1)
            filename = filename_split[0]
            f = open(filename+".out", 'w')
            sys.stdout = f

        if(os.path.isfile(args.input_file)==False):
            print("No such file as "+str(args.input_file))
            exit(-1)

        curr_dir = os.getcwd()

        dir_path = os.path.dirname(args.input_file)
        filename = os.path.basename(args.input_file)
        #print(dir_path)
        os.chdir(dir_path)

        if args.lex:
            tokenize_file(filename)


        result = parse_file(filename)

        if args.parse:
            print(result.to_string())
        start_time = time.time()

        program = semantic(result)

        T = program.get_time().get_value()

        A,b,name_tuples = matrix_generationAb(program)

        #solver_julia_2(A,b,1)
        #exit()

        C = matrix_generationC(program)

        C_sum = C.sum(axis=0)

        #gurobi(A,b,C_sum)
        print("All --- %s seconds ---" % (time.time() - start_time))
        #np.set_printoptions(threshold=sys.maxsize)

        if args.matrix:
            print("Matrix A ",A)
            print("Vector b ",b)
            print("Vector C ",C_sum)

        os.chdir(curr_dir)

        if args.linprog:
            x, optimal, status,solver_info = solver_scipy(A,b,C_sum)
        elif args.jump:
            #x,flag_solved = solver_julia(A.toarray(),b,C_sum)
            #print(A.toarray())
            x, optimal ,status = solver_julia_2(A,b,C_sum)
        elif args.clp:
            x, optimal, status, solver_info = solver_clp(A,b,C_sum)
        elif args.cplex:
            x, status = solver_cplex(A,b,C_sum)
        elif args.gurobi:
            x, status = solver_gurobi(A,b,C_sum)
        else:
            print("No solver was chosen")
            exit()

        if status == False :
            print("An error occured !")
            exit()
        elif status == "no solution":
            print("The problem is either unsolvable or possesses too many solutions")
            exit()

        #plot_results(x,T,name_tuples)

        filename_split = args.input_file.rsplit('.', 1)
        filename = filename_split[0]

        if args.json:
            dictionary = convert_dictionary(x,T,name_tuples,optimal,status,program.to_dict())
            dictionary["solver_info"] = solver_info
            with open(filename+".json", 'w') as outfile:
                json.dump(dictionary, outfile,indent=4)
        if args.csv:
            panda_datastruct = convert_pandas(x,T,name_tuples)
            panda_datastruct.to_csv(filename+".csv")

    else:
        print('ERROR : expected input file')
    print("--- %s seconds ---" % (time.time() - start_time))
