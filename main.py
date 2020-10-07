
# main.py
#
# Writer : MIFTARI B
# ------------

from lexer import *
from Myparser import parse_file
from semantic import semantic
from matrixGeneration import matrix_generationAb,matrix_generationC
import argparse
import time
from scipy.optimize import linprog
from julia import Main 

def solver_scipy(A,b,C):
    x0_bounds = (None, None)
    res = linprog(C_sum, A_ub=A.toarray(), b_ub=b,bounds = (None, None),options={"lstsq":True,"disp": True,"cholesky":False,"sym_pos":False,})
    print(res)

def solver_julia(A,b,C):
    b = b.reshape((-1,1))
    C = C.reshape((-1,1))
    print(type(b.astype(float)))
    print(type(A.astype(float)))
    A = A.astype(float)
    print(type(C.astype(float)))
    print(Main.print(type(A)))

    Main.include("linear_solver.jl") # load the MyFuncs module
    
    print(Main.lin_solve(C.astype(float),A.astype(float),b.astype(float)))

if __name__ == '__main__':
    start_time = time.time()


    parser = argparse.ArgumentParser(description='Compiler converting txt file to python matrix')
    parser.add_argument( "input_file", type = str)

    parser.add_argument("--lex",help="Prints all tokens found in input file",action='store_const',const=True)
    parser.add_argument("--parse",help="Prints the AST",action='store_const',const=True)
    parser.add_argument("--matrix",help="Prints matrix representation",action='store_const',const=True)
    
    args = parser.parse_args()

    if args.input_file:
        if args.lex:
            tokenize_file(args.input_file)
        
        result = parse_file(args.input_file)
        if args.parse:
            print(result)
        program = semantic(result)
        A,b = matrix_generationAb(program)
        C = matrix_generationC(program)

        C_sum = C.toarray().sum(axis=0)

        print("b = "+str(b))
        print(A.toarray().dtype)
        
        solver_julia(A.toarray(),b,C_sum)
        #solver_scipy(A,b,C_sum)
    else: 
        print('ERROR : expected input file')
    print("--- %s seconds ---" % (time.time() - start_time))