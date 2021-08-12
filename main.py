"""GBOML compiler main file, compiles input file given in command line.

GBOML is an algebraic modelling language developed at the UNIVERSITY OF LIEGE.
This compiler takes GBOML input files and converts them into matrices to send
to solvers. Furthermore, once the problem solved, it outputs the results in an
understandable formalism similar to the input file.

  Typical usage example:

   $ python main.py gboml_file.txt --solver --output_type
  where:
    gboml_file is the file we want to compile
    --solver can either be linprog, cplex, clp/cbc, gurobi, xpress
    --output_type can either be csv or json

Several other options exists and can be retrieved by writing :
  python main.py -h
"""


from compiler import compile_gboml, compile_gboml_mdp
from output import generate_json, generate_pandas
from solver_api import scipy_solver, clp_solver,\
    cplex_solver, gurobi_solver, xpress_solver

import argparse
import json
import numpy as np
import sys
from time import gmtime, strftime, sleep, time

if __name__ == '__main__':

    parser = argparse.ArgumentParser(allow_abbrev=False,
                                     description='Compiler and solver for the generic system model language')
    parser.add_argument("input_file", type=str)

    # Compiling info
    parser.add_argument("--lex", help="Prints all tokens found in input file", action='store_const', const=True)
    parser.add_argument("--parse", help="Prints the AST", action='store_const', const=True)
    parser.add_argument("--matrix", help="Prints matrix representation", action='store_const', const=True)

    # Solver
    parser.add_argument("--clp", help="CLP solver", action='store_const', const=True)
    parser.add_argument("--cplex", help="Cplex solver", action='store_const', const=True)
    parser.add_argument("--convert", help="convert to mdp", action="store_const", const=True)
    parser.add_argument("--linprog", help="Scipy linprog solver", action='store_const', const=True)
    parser.add_argument("--gurobi", help="Gurobi solver", action='store_const', const=True)
    parser.add_argument("--xpress", help="Xpress solver", action='store_const', const=True)

    # Output
    parser.add_argument("--csv", help="Convert results to CSV format", action='store_const', const=True)
    parser.add_argument("--json", help="Convert results to JSON format", action='store_const', const=True)
    parser.add_argument("--log", help="Get log in a file", action="store_const", const=True)
    parser.add_argument("--output", help="Output filename", type=str)

    args = parser.parse_args()
    start_time = time()

    if args.input_file:

        program, A, b, C, indep_terms_c, T, name_tuples, objective_map = compile_gboml(args.input_file, args.log,
                                                                                       args.lex, args.parse)
        print("All --- %s seconds ---" % (time() - start_time))
        C_sum = np.asarray(C.sum(axis=0), dtype=float)

        if args.matrix:

            print("Matrix A ", A)
            print("Vector b ", b)
            print("Vector C ", C_sum)

        objective_offset = float(indep_terms_c.sum())
        status = None

        if args.linprog:

            x, objective, status, solver_info = scipy_solver(A, b, C_sum, objective_offset, name_tuples)
        elif args.clp:

            x, objective, status, solver_info = clp_solver(A, b, C_sum, objective_offset, name_tuples)
        elif args.cplex:

            x, objective, status, solver_info = cplex_solver(A, b, C_sum, objective_offset, name_tuples)
        elif args.gurobi:

            x, objective, status, solver_info = gurobi_solver(A, b, C_sum, objective_offset, name_tuples)
        elif args.xpress:

            x, objective, status, solver_info = xpress_solver(A, b, C_sum, objective_offset, name_tuples)
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
        if args.output:

            filename = args.output
        else:

            filename_split = args.input_file.rsplit('.', 1)
            filename = filename_split[0]
            time_str = strftime("%Y_%m_%d_%H_%M_%S", gmtime())
            filename = filename + "_"+time_str

        if args.json:
            dictionary = generate_json(program, name_tuples, solver_info, status, x, objective, C,
                                       indep_terms_c, objective_map)
            try:
                with open(filename+".json", 'w') as outfile:

                    json.dump(dictionary, outfile, indent=4)

                print("File saved: " + filename+".json")
            except PermissionError:

                print("WARNING the file "+str(filename)+".json already exists and is open.")
                print("Was unable to save the file")
        if args.csv:

            panda_datastructure = generate_pandas(program, x, name_tuples)
            try:

                panda_datastructure.to_csv(filename+".csv")
                print("File saved: " + filename+".csv")
            except PermissionError:

                print("WARNING the file "+str(filename)+".csv already exists and is open.")
                print("Was unable to save the file")
    else:

        print('ERROR : expected input file')
    print("--- %s seconds ---" % (time() - start_time))
