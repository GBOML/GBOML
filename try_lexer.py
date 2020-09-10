from lexer import tokenize_file
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Compiler converting txt file to python matrix')
    parser.add_argument( "input_file", type = str)

    args = parser.parse_args()

    tokenize_file(args.input_file)