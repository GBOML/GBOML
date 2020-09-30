
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
        matrix_generationAb(program)
        matrix_generationC(program)
    else: 
        print('ERROR : expected input file')
    print("--- %s seconds ---" % (time.time() - start_time))