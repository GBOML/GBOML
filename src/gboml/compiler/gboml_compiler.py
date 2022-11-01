# Copyright (C) 2020 - 2022
# Bardhyl Miftari, Mathias Berger, Hatim Djelassi, Damien Ernst,
# University of Liege .
# Licensed under the MIT License (see LICENSE file).

"""GBOML compiler file

Defines functions to extract the information of a GBOML file,
check and translate it to another structure.

  Typical usage example:

  compile_gboml(gboml_file)
  where:
    gboml_file is the file we want to compile

"""

from .gboml_lexer import tokenize_file
from .gboml_parser import parse_file
from .gboml_semantic import semantic, check_mdp, convert_to_mdp, \
    check_program_linearity, factorize_program
from .gboml_matrix_generation import matrix_generation_a_b, \
    matrix_generation_c, extend_factor, extend_factor_on_multiple_processes
from .utils import move_to_directory

import sys
import os


def compile_gboml(input_file: str, log: bool = False,
                  lex: bool = False, parse: bool = False,
                  nb_processes: int = 1) -> tuple:
    """compile_gboml

        takes as input a filename and converts to the matrix
        representation of the problem and a program object
        (abstract syntax tree)

        Args:
            input_file -> string containing the input file
            log -> boolean predicate of should the output log be saved
                   in the file
            lex -> boolean predicate of printing the different tokens
                   in the file
            parse -> boolean predicate of printing the abstract
                     syntax tree generated from the file
            nb_processes -> number of processes (workers) for
                            the model extension

        Returns:
             program -> program object
             matrix_a -> Constraint sparse matrix
             vector_b -> Vector of independent terms for each constraint
             vector_c -> objective sparse matrix
             indep_terms_c -> vector of independent terms of each row in
                              the objective sparse matrix
             T -> Time horizon
             name_tuples -> Mapping to convert the flat x solution
                            to the original graph structure

    """

    curr_dir, filename = move_to_directory(input_file)

    if log is True:
        filename_split = filename.rsplit('.', 1)
        logfile = filename_split[0]
        f = open(logfile + ".out", 'w')
        sys.stdout = f

    if lex is True:
        tokenize_file(filename)

    ast = parse_file(filename)
    if parse is True:
        print(ast.to_string())

    program, program_variables_dict, definitions = semantic(ast)
    check_program_linearity(program, program_variables_dict, definitions)
    factorize_program(program, program_variables_dict, definitions)

    if nb_processes > 1:
        extend_factor_on_multiple_processes(program, definitions, nb_processes)
    else:
        extend_factor(program, definitions)

    matrix_eq, vector_b_eq, matrix_ineq, vector_b_ineq = matrix_generation_a_b(program)
    vector_c, indep_terms_c, alone_term_c = matrix_generation_c(program)
    program.free_factors_objectives()

    time_horizon = program.get_time().get_value()
    os.chdir(curr_dir)
    return program, matrix_eq, vector_b_eq, matrix_ineq, vector_b_ineq, vector_c, indep_terms_c, \
           alone_term_c, time_horizon, program.get_tuple_name()


def compile_gboml_mdp(input_file: str):
    """compile_gboml_mdp

        takes as input a filename and converts to the mdp
        representation of the problem

        Args:
            input_file -> string containing the input file

        Returns:
             mdp -> MDP object containing the file information

    """

    curr_dir, filename = move_to_directory(input_file)
    ast = parse_file(filename)
    program, program_variables_dict, definitions = semantic(ast)
    check_mdp(program, program_variables_dict, definitions)
    mdp = convert_to_mdp(program, program_variables_dict)
    os.chdir(curr_dir)

    return mdp
