from .gboml_lexer import tokenize_file
from .gboml_parser import parse_file
from .gboml_semantic import new_semantic
from .gboml_matrix_generation import matrix_generation_a_b,\
    matrix_generation_c, extend_factor

import sys
import os


def compile_gboml(input_file: str, log: bool = False, lex: bool = False, parse: bool = False) -> tuple:

    """
    compile_gboml function: takes as input a gboml file and converts it in a program object and
    three matrices, min : C^T * X s.t. A*x <= b
    INPUT : input file -> str of the path towards the input file
            log -> boolean to retrieve terminal log in a .log file
            lex -> boolean to print the file's token
            parse -> print the program object
    OUTPUT : program -> program object
             A -> Constraint sparse matrix 
             b -> Vector of independant terms for each constraint
             C -> objective sparse matrix
             T -> Timehorizon
             name_tuples -> Mapping to convert the flat x solution to a graph strucure
             objective_belonging -> Mapping to check which objectif relates to which node
    """

    if os.path.isfile(input_file) is False:
        print("No such file as "+str(input_file))
        exit(-1)

    curr_dir = os.getcwd()
    dir_path = os.path.dirname(input_file)
    filename = os.path.basename(input_file)
    if dir_path != "":
        os.chdir(dir_path)

    if log is True:
        filename_split = filename.rsplit('.', 1)
        logfile = filename_split[0]
        f = open(logfile+".out", 'w')
        sys.stdout = f

    if lex is True:
        tokenize_file(filename)

    ast = parse_file(filename)

    if parse is True:
        print(ast.to_string())

    program = new_semantic(ast)
    
    extend_factor(program)
    
    matrix_a, vector_b = matrix_generation_a_b(program)
    vector_c, indep_terms_c, objective_map = matrix_generation_c(program)

    time_horizon = program.get_time().get_value()
    os.chdir(curr_dir)

    return program, matrix_a, vector_b, vector_c, indep_terms_c, time_horizon, program.get_tuple_name(), objective_map
