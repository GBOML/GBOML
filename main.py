# main.py
#
# Writer : MIFTARI B
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
import sys
from julia.api import Julia
jpath = "/Applications/Julia-1.5.app/Contents/Resources/julia/bin/julia"
jl = Julia(runtime=jpath,compiled_modules=False)
from julia import Main
import pandas as pd
import os
import json
import gurobipy as grbp
from gurobipy import GRB
import cplex

def solver_gurobi(A, b, c):

    A = A.astype(float)
    m, n = np.shape(A)
    b = b.reshape(-1)
    c = c.reshape(-1)

    model = grbp.Model()
    x = model.addMVar(shape=n, lb=-float('inf'), ub=float('inf'), vtype=GRB.CONTINUOUS, name="x")
    model.addMConstr(A, x, '<', b)
    model.setObjective(c @ x, GRB.MINIMIZE)
    model.setParam('Method',2)
    model.setParam('BarHomogeneous',1)
    model.setParam('Crossover',0)

    try:
        model.optimize()
        if model.getAttr("Status") == 2:
            flag_solved = True
        else:
            flag_solver = False
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
    model.variables.add(obj=c,lb=[-cplex.infinity]*n,ub=[cplex.infinity]*n,types=['C']*n)
    model.linear_constraints.add(senses=['L']*m,rhs=b)
    model.linear_constraints.set_coefficients(A_zipped)
    model.objective.set_sense(model.objective.sense.minimize)
    alg = model.parameters.lpmethod.values
    model.parameters.lpmethod.set(alg.barrier)
    model.parameters.barrier.crossover.set(model.parameters.barrier.crossover.values.none)

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
    print(A,b,C)
    x0_bounds = (None, None)
    solution = linprog(C_sum, A_ub=A.toarray(), b_ub=b,bounds = x0_bounds,options={"lstsq":True,"disp": True,"cholesky":False,"sym_pos":False,})
    return solution.x,solution.success

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
    flag_solved = False
    x = None

    Main.include("linear_solver.jl") # load the MyFuncs module
    try :
        x = Main.lin_solve_sparse(C.astype(float),constraint_matrix.astype(float),b.astype(float))
        flag_solved = True
    except RuntimeError as e:
        print(e)
        flag_solved = False
    return x,flag_solved

    #print(constraint_matrix)

def solver_julia(A,b,C):
    b = b.reshape((-1,1))
    C = C.reshape((-1,1))
    A = A.astype(float)
    flag_solved = False
    x = None
    Main.include("linear_solver.jl") # load the MyFuncs module
    try :
        x = Main.lin_solve(C.astype(float),A.astype(float),b.astype(float))
        flag_solved = True
    except(RuntimeError):
        flag_solved = False
    return x,flag_solved

def plot_results(x,T,name_tuples):

    legend = []
    font = {'size'   : 15}

    matplotlib.rc('font', **font)
    for i in range(0,len(x),T):
        found = False
        for node,index_variables in name_tuples:
            if node == "OPERATION_COST":
                for index, variable in index_variables:
                    if index==i:
                        if  variable in ["pv_production","battery","consumption","shed"]:
                            legend.append(str(variable))
                            found = True
                        #print(str(variable)+" "+str(x[i]))
        if found :
            plt.plot(x[i:(i+T)])
    plt.ylabel('Power[watt]', size = 20)
    plt.xlabel('Time[hour]', size = 20)
    plt.legend(legend)
    plt.show()

def convert_dictionary(x,T,name_tuples):
    dictionary = {}

    for node_name,index_variables in name_tuples:
        dico_node = {}
        for index,variable in index_variables:
            dico_node[variable] = x[index:(index+T)].flatten().tolist()
        dictionary[node_name] = dico_node

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

    #print(ordered_values)
    #print(columns)

    df = pd.DataFrame(ordered_values,index=columns)
    return df.T


def compile_file(directory,file):
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

    args = parser.parse_args()

    if args.linprog==False:
        print("The default solver is GUROBI")

    if args.input_file:
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
        #print(C)
        C_sum = C.sum(axis=0)
        print("All --- %s seconds ---" % (time.time() - start_time))
        #np.set_printoptions(threshold=sys.maxsize)

        if args.matrix:
            print("Matrix A ",A)
            print("Vector b ",b)
            print("Vector C ",C_sum)

        os.chdir(curr_dir)

        if args.linprog:
            x,flag_solved = solver_scipy(A,b,C_sum)

        elif args.jump:
            #x,flag_solved = solver_julia(A.toarray(),b,C_sum)
            #print(A.toarray())
            x,flag_solved = solver_julia_2(A,b,C_sum)

        elif args.gurobi:
            x, flag_solved = solver_gurobi(A,b,C_sum)

        elif args.cplex:
            x, flag_solved = solver_cplex(A,b,C_sum)

        if not flag_solved:
            print("The solver did not find a solution to the problem")
            exit()

        #plot_results(x,T,name_tuples)

        filename_split = args.input_file.rsplit('.', 1)
        filename = filename_split[0]

        if args.json:
            dictionary = convert_dictionary(x,T,name_tuples)
            with open(filename+".json", 'w') as outfile:
                json.dump(dictionary, outfile,indent=4)
        if args.csv:
            panda_datastruct = convert_pandas(x,T,name_tuples)
            panda_datastruct.to_csv(filename+".csv")

    else:
        print('ERROR : expected input file')
    print("--- %s seconds ---" % (time.time() - start_time))
