
# main.py
#
# Writer : MIFTARI B
# ------------

from lexer import tokenize_file
from Myparser import parse_file
from semantic import semantic
from matrixGeneration import matrix_generationAb,matrix_generationC
import argparse
import time
from scipy.optimize import linprog
import matplotlib.pyplot as plt
import numpy as np
from cylp.cy import CyClpSimplex
from cylp.py.modeling.CyLPModel import CyLPArray
import sys
#from julia import Main 
import pandas as pd
import os
import json


def solver_scipy(A,b,C):
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

#    Main.include("linear_solver.jl") # load the MyFuncs module
#    try : 
#        x = Main.lin_solve_sparse(C.astype(float),constraint_matrix.astype(float),b.astype(float))
#        flag_solved = True
#    except(RuntimeError): 
#        flag_solved = False
#    return x,flag_solved

    #print(constraint_matrix)

def solver_julia(A,b,C):
    b = b.reshape((-1,1))
    C = C.reshape((-1,1))
    A = A.astype(float)
    flag_solved = False
    x = None
#    Main.include("linear_solver.jl") # load the MyFuncs module
#    try : 
#        x = Main.lin_solve(C.astype(float),A.astype(float),b.astype(float))
#        flag_solved = True
#    except(RuntimeError): 
#        flag_solved = False
#    return x,flag_solved

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
    if solver.getStatusCode() == 0:
        flag_solved = True
    print('\033[93m', "DEBUG: CLP solver status: %s" % solver.getStatusString(), '\033[0m')
    print('\033[93m', "DEBUG: CLP return x:", '\033[0m')
    print('\033[93m', x, '\033[0m')
    print('\033[93m', "DEBUG: CLP return flag_solved: %s" % flag_solved, '\033[0m')
    print('\033[93m', "DEBUG: CLP total time: %s seconds" % (time.time() - start_time), '\033[0m')
    return x,flag_solved

def plot_results(x,T,name_tuples):
    
    legend = []

    for i in range(0,len(x),T):
        found = False
        for _,index_variables in name_tuples:
            for index, variable in index_variables:
                if index==i:
                    if  variable in ["ppv","pc","pbt"]:
                        legend.append(str(variable))
                        found = True
                    #print(str(variable)+" "+str(x[i]))
        if found :
            plt.plot(x[i:(i+T)])
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

        else:
            x,flag_solved = solver_clp(A,b,C_sum)

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