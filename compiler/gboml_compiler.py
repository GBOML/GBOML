from .gboml_lexer import tokenize_file
from .gboml_parser import parse_file
from .gboml_semantic import semantic
from .gboml_matrix_generation import matrix_generationAb,matrix_generationC

import sys,os
import numpy as np # type: ignore


def compile_gboml(input_file:str,log:bool = False,lex:bool = False,parse:bool = False)->tuple:
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
             C_sum -> objective vector
             T -> Timehorizon
             name_tuples -> Mapping to convert the flat x solution to a graph strucure
    """
    if(os.path.isfile(input_file)==False):
        print("No such file as "+str(input_file))
        exit(-1)

    curr_dir = os.getcwd()
    dir_path = os.path.dirname(input_file)
    filename = os.path.basename(input_file)
    os.chdir(dir_path)

    if log == True:
        filename_split = filename.rsplit('.', 1)
        logfile = filename_split[0]
        f = open(logfile+".out", 'w')
        sys.stdout = f

    if lex == True: 
        tokenize_file(filename)

    ast = parse_file(filename)

    if parse == True:
        print(ast.to_string())

    program = semantic(ast)
    A,b,name_tuples = matrix_generationAb(program)
    C = matrix_generationC(program)
    C_sum = np.asarray(C.sum(axis=0))
    T = program.get_time().get_value()
    os.chdir(curr_dir)

    return program,A,b,C_sum,T,name_tuples