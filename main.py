
# main.py
#
# Writer : MIFTARI B - BERGER M - DJELASSI H
# ------------

# COMPILER import
from compiler import compile_gboml

# SOLVER import
from solver import solver_scipy, solver_clp,\
    solver_cplex, solver_gurobi

# OUTPUT import
from output import generate_json, generate_pandas

# GENERAL import
import json
import sys
import argparse
from time import time, gmtime, strftime
import numpy as np
import scipy

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Compiler and solver for the generic system model language')
    parser.add_argument("input_file", type=str)
    # Compiling info
    parser.add_argument("--lex", help="Prints all tokens found in input file", action='store_const', const=True)
    parser.add_argument("--parse", help="Prints the AST", action='store_const', const=True)
    parser.add_argument("--matrix", help="Prints matrix representation", action='store_const', const=True)
    # Output format
    parser.add_argument("--json", help="Convert results to JSON format", action='store_const', const=True)
    parser.add_argument("--csv", help="Convert results to CSV format", action='store_const', const=True)
    # Solver
    parser.add_argument("--linprog", help="Scipy linprog solver", action='store_const', const=True)
    parser.add_argument("--gurobi", help="Gurobi solver", action='store_const', const=True)
    parser.add_argument("--clp", help="CLP solver", action='store_const', const=True)
    parser.add_argument("--cplex", help="Cplex solver", action='store_const', const=True)
    # Save log
    parser.add_argument("--log", help="Get log in a file", action="store_const", const=True)

    args = parser.parse_args()
    start_time = time()
    if args.input_file:

        program, A, b, C, T, name_tuples, objective_map = compile_gboml(args.input_file, args.log, args.lex, args.parse)
        print("All --- %s seconds ---" % (time() - start_time))
        C_sum = np.asarray(C.sum(axis=0), dtype=float)

        if args.matrix:

            print(len(b))
            print(len(C_sum[0]))
            print(A.shape)

            print("Matrix A ", A)
            print("Vector b ", b)
            print("Vector C ", C_sum)

        if args.linprog:

            x, objective, status, solver_info = solver_scipy(A, b, C_sum, name_tuples)
        elif args.clp:

            x, objective, status, solver_info = solver_clp(A, b, C_sum, name_tuples)
        elif args.cplex:

            x, objective, status, solver_info = solver_cplex(A, b, C_sum, name_tuples)
        elif args.gurobi:

            x, objective, status, solver_info = solver_gurobi(A, b, C_sum, name_tuples)
        else:

            print("No solver was chosen")
            sys.exit()
        assert status in {"unbounded", "optimal", "feasible", "infeasible", "error", "unknown"}
        if status == "unbounded":

            print("Problem is unbounded")
        elif status == "optimal":

            print("Optimal solution found")
        elif status == "feasible":

            print("Feasible solution found")
        elif status == "infeasible":

            print("Problem is infeasible")
        elif status == "error":

            print("An error occurred")
            exit()
        elif status == "unknown":

            print("Solver returned with unknown status")

        filename_split = args.input_file.rsplit('.', 1)
        filename = filename_split[0]
        if args.json:

            dictionary = generate_json(program, name_tuples, solver_info, status, x, objective, C, objective_map)
            with open(filename+".json", 'w') as outfile:

                json.dump(dictionary, outfile, indent=4)
        if args.csv:

            panda_datastruct = generate_pandas(x, T, name_tuples)
            try:

                panda_datastruct.to_csv(filename+".csv")
            except PermissionError:

                time_str = strftime("%Y_%m_%d_%H_%M_%S", gmtime())
                print("WARNING the file "+str(filename)+".csv already exists and is open.")
                try:
                    panda_datastruct.to_csv(filename+time_str+".csv")
                    print("The file was saved as : "+str(filename+time_str+".csv"))
                except PermissionError:

                    print("Unable to save the file")
    else:

        print('ERROR : expected input file')
    print("--- %s seconds ---" % (time() - start_time))
