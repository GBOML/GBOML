from .gboml_lexer import tokenize_file
from .gboml_parser import parse_file
from .gboml_semantic import semantic
from .gboml_matrix_generation import matrix_generationAb,matrix_generationC

import sys,os
import numpy as np # type: ignore


def compile_gboml(input_file:str,log:bool = False,lex:bool = False,parse:bool = False)->tuple:
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