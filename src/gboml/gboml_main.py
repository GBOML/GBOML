# Copyright (C) 2020 - 2022
# Bardhyl Miftari, Mathias Berger, Hatim Djelassi, Damien Ernst,
# University of Liege .
# Licensed under the MIT License (see LICENSE file).

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

from .compiler import compile_gboml
from .solver_api import scipy_solver, clp_solver, cplex_solver, \
    gurobi_solver, xpress_solver, dsp_solver, highs_solver, cbc_solver
from .output import generate_json, generate_list_values_tuple, write_csv

import argparse
import json
import numpy as np
import sys
from time import gmtime, strftime, time


def main():
    parser = argparse.ArgumentParser(allow_abbrev=False,
                                     description='Compiler and solver for the '
                                                 'generic system model language'
                                     )
    parser.add_argument("input_file", type=str)

    # Compiling info
    parser.add_argument("--lex", help="Prints all tokens found in input file",
                        action='store_const', const=True)
    parser.add_argument("--parse", help="Prints the AST", action='store_const',
                        const=True)
    parser.add_argument("--matrix", help="Prints matrix representation",
                        action='store_const', const=True)
    parser.add_argument("--nb_processes", help="Number of processes to use",
                        type=int)

    # Solver
    parser.add_argument("--clp", help="CLP solver", action='store_const',
                        const=True)
    parser.add_argument("--cbc", help="CBC solver", action='store_const',
                        const=True)
    parser.add_argument("--cplex", help="Cplex solver", action='store_const',
                        const=True)
    parser.add_argument("--linprog", help="Scipy linprog solver",
                        action='store_const', const=True)
    parser.add_argument("--gurobi", help="Gurobi solver",
                        action='store_const', const=True)
    parser.add_argument("--xpress", help="Xpress solver",
                        action='store_const', const=True)
    parser.add_argument("--dsp_de", help="DSP Extensive Form algorithm",
                        action='store_const', const=True)
    parser.add_argument("--dsp_dw", help="DSP Dantzig-Wolf algorithm",
                        action="store_const", const=True)
    parser.add_argument("--highs", help="Highs Solver",
                        action="store_const", const=True)

    # Output
    parser.add_argument("--row_csv", help="Convert results to row wise CSV format",
                        action='store_const', const=True)
    parser.add_argument("--col_csv",
                        help="Convert results to column wise CSV format",
                        action='store_const', const=True)

    parser.add_argument("--json", help="Convert results to JSON format",
                        action='store_const', const=True)
    parser.add_argument("--detailed",
                        help="get detailed version of the output",
                        nargs="?",
                        type=str, default="")
    parser.add_argument("--log", help="Get log in a file",
                        action="store_const", const=True)
    parser.add_argument("--output", help="Output filename", type=str)
    parser.add_argument("--opt", help="Optimization options filename", type=str)

    args = parser.parse_args()
    start_time = time()
    if args.detailed is None:
        args.detailed = True
    elif args.detailed == "":
        args.detailed = False

    if args.input_file:
        if args.nb_processes is None:
            args.nb_processes = 1
        elif args.nb_processes <= 0:
            print("The number of processes must be strictly positive")
            exit()

        program, A_eq, b_eq, A_ineq, b_ineq, C, indep_terms_c, alone_term_c, T, name_tuples = \
            compile_gboml(args.input_file, args.log, args.lex,
                          args.parse, args.nb_processes)

        print("All --- %s seconds ---" % (time() - start_time))
        C_sum = np.asarray(C.sum(axis=0), dtype=float)

        if args.matrix:
            print("Matrix A_eq ", A_eq)
            print("Vector b_eq ", b_eq)
            print("Matrix A_ineq ", A_ineq)
            print("Vector b_ineq ", b_ineq)
            print("Vector C ", C_sum)
            print("Offset", indep_terms_c)

        objective_offset = float(indep_terms_c.sum() + alone_term_c)
        status = None

        constraints_additional_information = dict()
        variables_additional_information = dict()

        if args.linprog:

            x, objective, status, solver_info = \
                scipy_solver(A_eq, b_eq, A_ineq, b_ineq, C_sum, objective_offset, name_tuples)
        elif args.clp:

            x, objective, status, solver_info = \
                clp_solver(A_eq, b_eq, A_ineq, b_ineq, C_sum, objective_offset, name_tuples)
        elif args.cbc:

            x, objective, status, solver_info = \
                cbc_solver(A_eq, b_eq, A_ineq, b_ineq, C_sum, objective_offset, name_tuples)
        elif args.cplex:
            x, objective, status, solver_info, \
             constraints_additional_information, \
             variables_additional_information = \
             cplex_solver(A_eq, b_eq, A_ineq, b_ineq, C_sum, objective_offset, name_tuples,
                          args.opt, details=args.detailed)

        elif args.gurobi:

            x, objective, status, solver_info, \
             constraints_additional_information, \
             variables_additional_information = \
             gurobi_solver(A_eq, b_eq, A_ineq, b_ineq, C_sum, objective_offset, name_tuples,
                           args.opt, args.detailed)
            print(x)

        elif args.xpress:

            x, objective, status, solver_info, \
             constraints_additional_information, \
             variables_additional_information = \
             xpress_solver(A_eq, b_eq, A_ineq, b_ineq, C_sum, objective_offset, name_tuples,
                           args.opt, args.detailed)

        elif args.dsp_dw:
            struct_eq, struct_ineq = program.get_first_level_constraints_decomposition()
            x, objective, status, solver_info = \
                dsp_solver(A_eq, b_eq, A_ineq, b_ineq, C_sum, objective_offset, name_tuples,
                           struct_eq, struct_ineq, algorithm="dw")

        elif args.dsp_de:
            struct_eq, struct_ineq = program.get_first_level_constraints_decomposition()
            x, objective, status, solver_info = \
                dsp_solver(A_eq, b_eq, A_ineq, b_ineq, C_sum, objective_offset, name_tuples,
                           struct_eq, struct_ineq, algorithm="de")

        elif args.highs:
            x, objective, status, solver_info = \
                highs_solver(A_eq, b_eq, A_ineq, b_ineq, C_sum, objective_offset, name_tuples,
                             args.opt)
        else:

            print("No solver was chosen")
            sys.exit()

        assert status in {"unbounded", "optimal", "feasible", "infeasible",
                          "error", "unknown", "sub-optimal stopped"}

        if status == "unbounded":

            print("Problem is unbounded")
            exit()
        elif status == "optimal":

            print("Optimal solution found")

        elif status == "sub-optimal stopped":
            print("Sub-optimal solution as solver was stopped")

        elif status == "feasible":

            print("Feasible solution found")
        elif status == "infeasible":

            print("Problem is infeasible")
            exit()
        elif status == "error":

            print("An error occurred")
            exit()
        elif status == "unknown":

            print("Solver returned with unknown status")
            exit()
        if args.output:

            filename = args.output
        else:

            filename_split = args.input_file.rsplit('.', 1)
            filename = filename_split[0]
            time_str = strftime("%Y_%m_%d_%H_%M_%S", gmtime())
            filename = filename + "_" + time_str

        if args.json:
            dictionary = generate_json(program, solver_info, status, x,
                                       objective, C,
                                       indep_terms_c,
                                       constraints_additional_information,
                                       variables_additional_information)
            try:
                with open(filename + ".json", 'w') as outfile:

                    json.dump(dictionary, outfile, indent=4)

                print("File saved: " + filename + ".json")
            except PermissionError:

                print("WARNING the file " + str(filename)
                      + ".json already exists and is open.")
                print("Was unable to save the file")
        if args.row_csv or args.col_csv:
            names_var_and_param, values_var_and_param = \
                generate_list_values_tuple(program, x, C, indep_terms_c,
                                           constraints_info=constraints_additional_information)
            write_csv(filename + ".csv", names_var_and_param,
                      values_var_and_param, transpose=args.col_csv)
    else:

        print('ERROR : expected input file')
    print("--- %s seconds ---" % (time() - start_time))
