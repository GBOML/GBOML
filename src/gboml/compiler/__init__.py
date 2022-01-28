# Copyright (C) 2020 - 2022
# Bardhyl Miftari, Mathias Berger, Hatim Djelassi, Damien Ernst,
# University of Liege .
# Licensed under the MIT License (see LICENSE file).


"""Compiler directory contains each step from the input file to the matrix
generation.

The compiler directory contains :
- The Lexer which converts an input file into a stream of tokens
- The Parser which converts the stream of tokens into a abstract syntax tree
(AST)
- The Semantic Analysis which augments and checks the AST
- The Matrix Generation which converts the AST to a standard optimization form

The file gboml_compiler contains the APIs to compile a full file
The file gboml_lexer contains the APIs to convert a file to a stream of tokens
The file gboml_parser contains the APIs to convert a file to a AST
The file gboml_semantic contains the APIs of the semantic analysis
The file utils contains functions that are used throughout the other files

After running the parser, the PLY package it uses generates two file parser.out
and parsetab.py that are only useful in the parsing step and can be deleted as
they are automatically generated afterwards.
"""


from .gboml_compiler import compile_gboml, compile_gboml_mdp
from .gboml_lexer import tokenize_file
from .gboml_matrix_generation import matrix_generation_a_b, \
    matrix_generation_c, extend_factor, extend_factor_on_multiple_processes
from .gboml_parser import parse_file
from .gboml_semantic import semantic, parameter_evaluation, \
    check_names_repetitions, match_dictionaries, \
    check_mdp, convert_to_mdp, check_program_linearity, factorize_program
