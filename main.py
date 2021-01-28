
# main.py
#
# Writer : MIFTARI B - BERGER M - DJELASSI H
# ------------

#COMPILER IMPORT
from compiler import compile

#GENERAL import
import sys
import pandas as pd
import os
import json
import argparse
import time
import numpy as np

#Solver import
from solver import solver_scipy, solver_clp,\
    solver_cplex,solver_gurobi


def convert_dictionary(x,T,name_tuples,objective,status,program_dict):
    dictionary = program_dict
    dictionary["version"] = "0.0.0"
    dictionary["objective"] = objective
    dictionary["status"] = status
    dictionary_nodes = dictionary["nodes"]
    for node_name,index_variables in name_tuples:
        dico_node = dictionary_nodes[node_name]
        dico_variables = {}
        for index,variable in index_variables:
            dico_variables[variable] = x[index:(index+T)].flatten().tolist()
        dico_node["variables"] = dico_variables
        dictionary_nodes[node_name]=dico_node

    dictionary["nodes"]= dictionary_nodes
    return dictionary

def convert_pandas(x,T,name_tuples):
    ordered_values = []
    columns = []

    for node_name,index_variables in name_tuples:
        for index,variable in index_variables:
            full_name = str(node_name)+"."+str(variable)
            values = x[index:(index+T)].flatten()
            columns.append(full_name)
            ordered_values.append(values)

    df = pd.DataFrame(ordered_values,index=columns)
    return df.T


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Compiler and solver for the generic system model language')
    parser.add_argument( "input_file", type = str)

    parser.add_argument("--lex",help="Prints all tokens found in input file",action='store_const',const=True)
    parser.add_argument("--parse",help="Prints the AST",action='store_const',const=True)
    parser.add_argument("--matrix",help="Prints matrix representation",action='store_const',const=True)

    parser.add_argument("--json", help="Convert results to JSON format",action='store_const',const=True)
    parser.add_argument("--csv", help="Convert results to CSV format",action='store_const',const=True)

    parser.add_argument("--linprog",help = "Scipy linprog solver",action='store_const',const=True)
    parser.add_argument("--gurobi",help = "Gurobi solver",action='store_const',const=True)
    parser.add_argument("--cplex",help = "Cplex solver",action='store_const',const=True)
    parser.add_argument("--clp",help = "CLP solver",action='store_const',const=True)

    parser.add_argument("--log",help="Get log in a file",action="store_const",const=True)

    args = parser.parse_args()

    if args.linprog==False:
        print("The default solver is GUROBI")

    if args.input_file:
        start_time = time.time()
        program,A,b,C_sum,T,name_tuples = compile(args.input_file,args.log,args.lex,args.parse)
        print("All --- %s seconds ---" % (time.time() - start_time))

        if args.matrix:
            print("Matrix A ",A)
            print("Vector b ",b)
            print("Vector C ",C_sum)

        if args.linprog:
            x, objective, status,solver_info = solver_scipy(A,b,C_sum)
        elif args.clp:
            x, objective, status, solver_info = solver_clp(A,b,C_sum)
        elif args.cplex:
            x, objective, status, solver_info = solver_cplex(A,b,C_sum)
        elif args.gurobi:
            x, objective, status, solver_info = solver_gurobi(A,b,C_sum)
        else:
            print("No solver was chosen")
            exit()

        if status == False :
            print("An error occured !")
            exit()
        elif status == "no solution":
            print("The problem is either unsolvable or possesses too many solutions")
            exit()

        filename_split = args.input_file.rsplit('.', 1)
        filename = filename_split[0]

        if args.json:
            dictionary = convert_dictionary(x,T,name_tuples,objective,status,program.to_dict())
            dictionary["solver_info"] = solver_info
            with open(filename+".json", 'w') as outfile:
                json.dump(dictionary, outfile,indent=4)
        if args.csv:
            panda_datastruct = convert_pandas(x,T,name_tuples)
            panda_datastruct.to_csv(filename+".csv")

    else:
        print('ERROR : expected input file')
    print("--- %s seconds ---" % (time.time() - start_time))
