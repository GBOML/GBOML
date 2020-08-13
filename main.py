from lexer import *
from Myparser import parse_file
from semantic import semantic
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Compiler converting txt file to python matrix')
    parser.add_argument( "input_file", type = str)

    parser.add_argument("--lex",help="Prints all tokens found in input file",action='store_const',const=True)
    parser.add_argument("--parse",help="Prints the AST",action='store_const',const=True)
    parser.add_argument("--graph",help="Prints graph representation",action='store_const',const=True)
    
    args = parser.parse_args()

    if args.input_file:
        if args.lex:
            tokenize_file(args.input_file)
        result = parse_file(args.input_file)
        if args.parse:
            print(result)
        semantic(result)

    else: 
        print('ERROR : expected input file')