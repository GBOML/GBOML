
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
import sys
from julia import Main 
import pandas as pd


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
    print(constraint_matrix)

    b = b.reshape((-1,1))
    C = C.reshape((-1,1))
    A = A.astype(float)
    flag_solved = False

    Main.include("linear_solver2.jl") # load the MyFuncs module
    #try : 
    x = Main.lin_solve_sparse(C.astype(float),constraint_matrix.astype(float),b.astype(float))
    flag_solved = True
    #except(RuntimeError): 
    #    flag_solved = False
    return x,flag_solved

    #print(constraint_matrix)

def solver_julia(A,b,C):
    b = b.reshape((-1,1))
    C = C.reshape((-1,1))
    A = A.astype(float)
    flag_solved = False

    Main.include("linear_solver.jl") # load the MyFuncs module
    try : 
        x = Main.lin_solve(C.astype(float),A.astype(float),b.astype(float))
        flag_solved = True
    except(RuntimeError): 
        flag_solved = False
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
    
def convert_pandas(x,T,name_tuples):
    ordered_values = []
    columns = []

    for node_name,index_variables in name_tuples:
        for index,variable in index_variables:
            full_name = str(node_name)+"."+str(variable)
            values = x[index:(index+T)].flatten() 
            columns.append(full_name)
            ordered_values.append(values)

    print(ordered_values)
    print(columns)

    df = pd.DataFrame(ordered_values,index=columns)
    return df


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Compiler and solver for the generic system model language')
    parser.add_argument( "input_file", type = str)

    parser.add_argument("--lex",help="Prints all tokens found in input file",action='store_const',const=True)
    parser.add_argument("--parse",help="Prints the AST",action='store_const',const=True)
    parser.add_argument("--matrix",help="Prints matrix representation",action='store_const',const=True)
    
    parser.add_argument("--json", help="Convert results to JSON format",action='store_const',const=True)

    parser.add_argument("--linprog",help = "Scipy linprog solver",action='store_const',const=True)

    parser.add_argument("--gurobi",help = "Gurobi solver with call to Julia",action="store_const",const=True)

    args = parser.parse_args()

    if args.linprog and args.gurobi: 
        print("SOLVER ERROR: you can choose only one solver, not both")
        exit(-1)
    elif not args.linprog and not args.gurobi:
        print("SOLVER ERROR: you must choose one solver")
        exit(-1) 

    if args.input_file:
        if args.lex:
            tokenize_file(args.input_file)
        
        result = parse_file(args.input_file)
        if args.parse:
            print(result.to_string())
        start_time = time.time()

        program = semantic(result)
        print("Semantic --- %s seconds ---" % (time.time() - start_time))
        T = program.get_time().get_value()

        A,b,name_tuples = matrix_generationAb(program)
        
        #solver_julia_2(A,b,1)
        #exit()

        C = matrix_generationC(program)

        C_sum = C.toarray().sum(axis=0)
       
        #np.set_printoptions(threshold=sys.maxsize)

        if args.gurobi:
            #x,flag_solved = solver_julia(A.toarray(),b,C_sum)
            #print(A.toarray())
            x,flag_solved = solver_julia_2(A,b,C_sum)

        elif args.linprog:
            x,flag_solved = solver_scipy(A,b,C_sum)

        if not flag_solved: 
            print("The solver did not find a solution to the problem")
            exit()

        plot_results(x,T,name_tuples)
        panda_datastruct = convert_pandas(x,T,name_tuples)

        filename_split = args.input_file.split(".")
        filename = filename_split[0]

        if args.json: 
            panda_datastruct.to_json(filename+".json")
        else: 
            panda_datastruct.to_csv(filename+".csv")

    else: 
        print('ERROR : expected input file')
    print("--- %s seconds ---" % (time.time() - start_time))