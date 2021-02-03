
# main.py
#
# Writer : MIFTARI B - BERGER M - DJELASSI H
# ------------

#COMPILER import
from compiler import compile_gboml

#SOLVER import
from solver import solver_scipy, solver_clp,\
    solver_cplex,solver_gurobi

#OUTPUT import
from output import generate_json, generate_pandas

#GENERAL import
import json
import argparse
import time

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Compiler and solver for the generic system model language')
    parser.add_argument( "input_file", type = str)

    parser.add_argument("--lex",help="Prints all tokens found in input file",action='store_const',const=True)
    parser.add_argument("--parse",help="Prints the AST",action='store_const',const=True)
    parser.add_argument("--matrix",help="Prints matrix representation",action='store_const',const=True)

    parser.add_argument("--json", help="Convert results to JSON format",action='store_const',const=True)
    parser.add_argument("--csv", help="Convert results to CSV format",action='store_const',const=True)

    parser.add_argument("--linprog",help = "Scipy linprog solver",action='store_const',const=True)
    parser.add_argument("--gurobi",help = "Gurobi solver",action='store_const',const=True)
    parser.add_argument("--cplex",help = "Cplex solver",action='store_const',const=True)
    parser.add_argument("--clp",help = "CLP solver",action='store_const',const=True)

    parser.add_argument("--log",help="Get log in a file",action="store_const",const=True)

    args = parser.parse_args()

    if args.input_file:
        start_time = time.time()
        program,A,b,C_sum,T,name_tuples = compile_gboml(args.input_file,args.log,args.lex,args.parse)
        print("All --- %s seconds ---" % (time.time() - start_time))

        if args.matrix:
            print("Matrix A ",A)
            print("Vector b ",b)
            print("Vector C ",C_sum)

        if args.linprog:
            x, objective, status,solver_info = solver_scipy(A,b,C_sum)
        elif args.clp:
            x, objective, status, solver_info = solver_clp(A,b,C_sum)
        elif args.cplex:
            x, objective, status, solver_info = solver_cplex(A,b,C_sum)
        elif args.gurobi:
            x, objective, status, solver_info = solver_gurobi(A,b,C_sum)
        else:
            print("No solver was chosen")
            exit()

        if status == False :
            print("An error occured !")
            exit()
        elif status == "no solution":
            print("The problem is either unsolvable or possesses too many solutions")
            exit()

        filename_split = args.input_file.rsplit('.', 1)
        filename = filename_split[0]

        if args.json:
            dictionary = generate_json(program, name_tuples, solver_info, status, x, objective)
            with open(filename+".json", 'w') as outfile:
                json.dump(dictionary, outfile,indent=4)

        if args.csv:
            panda_datastruct = generate_pandas(x,T,name_tuples)
            panda_datastruct.to_csv(filename+".csv")

    else:
        print('ERROR : expected input file')
    print("--- %s seconds ---" % (time.time() - start_time))
