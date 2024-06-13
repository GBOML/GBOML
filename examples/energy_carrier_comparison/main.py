# -*- coding: utf-8 -*-
"""
Created on Wed Jul 12 15:30:38 2023

@author: Antoine Larbanois
"""

import json
import os
from gboml import GbomlGraph
from gboml.compiler.classes import Expression
import argparse


VECTORS = ["Ammonia", "Methane", "Hydrogen", "Methanol"]



def change_param_in_node(ls_nodes, name_node, name_param, value_param):
    # Iterate over every node
    for n in ls_nodes:
        # Get the right node
        if n.name == name_node:
            # Iterate over every paremeter and get the right one
            for param in n.get_parameters():

                if param.name == name_param:
                    print(f"{name_node} , {name_param}, {value_param}")
                    # Change the value of the parameter
                    expr = Expression('literal', value_param)
                    param.expression = expr
                    param.type = "expression"
                    param.vector = None
                        
    return ls_nodes


def load_data_and_solve(VECTOR, TIME_HORIZON, NAME_NODE, NAME_PARAM, VALUE_PARAM):
    
    gboml_model = GbomlGraph(TIME_HORIZON)
    nodes, edges, global_params = gboml_model.import_all_nodes_and_edges(f"GBOML/{VECTOR}.txt")

    if NAME_NODE and NAME_PARAM and VALUE_PARAM :
        
        nodes = change_param_in_node(nodes,args.name_node, args.name_param, args.value_param)
    
    else : 
        print("Originals parameters")


    gboml_model.set_timehorizon(TIME_HORIZON)
    gboml_model.add_nodes_in_model(*nodes)
    gboml_model.add_hyperedges_in_model(*edges)
    gboml_model.add_global_parameters(global_params)
    gboml_model.build_model()
    
    results_dir = "RESULTS"
    os.makedirs(results_dir, exist_ok=True)
    vector_dir = os.path.join(results_dir, VECTOR)
    os.makedirs(vector_dir, exist_ok=True)
    solution = gboml_model.solve_gurobi()
    solution, objective, status, solver_info, constraints_information, variables_information = solution
    print("")
    print("Solved\n")
    dico = gboml_model.turn_solution_to_dictionary(
        solver_info, status, solution, objective, constraints_information, variables_information
    )
    
    print("Json done\n")
    
    if NAME_NODE and NAME_PARAM and VALUE_PARAM :
        
        output_file_path = os.path.join(vector_dir, f"{VECTOR}_Time_Horizon_{TIME_HORIZON}_Modified_Model_{NAME_NODE}_{NAME_PARAM}_{VALUE_PARAM}.json")
        with open(output_file_path, "w") as json_file:
            json_obj = json.dumps(dico)
            json_file.write(json_obj)
    else :
        
        output_file_path = os.path.join(vector_dir, f"{VECTOR}_Time_Horizon_{TIME_HORIZON}_Originals_Parameters.json")
        with open(output_file_path, "w") as json_file:
            json_obj = json.dumps(dico)
            json_file.write(json_obj)


if __name__ == "__main__":
        
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--vector', help='Name of the vector used',
                            type=str, choices=VECTORS,
                            required=True)
    parser.add_argument('-th', '--Time_Horizon', help="Number of hours",
                            type=int, default=8760)
        
    parser.add_argument('-nn', '--name_node', help = 'Specify nodes', 
                            type = str)
        
    parser.add_argument('-np', '--name_param', help = 'Specify parameter', 
                            type = str)
        
    parser.add_argument('-vp', '--value_param', help = 'Specify value parameter', 
                            type = float)
        
    args = parser.parse_args()


    vector = args.vector
    Time_Horizon = args.Time_Horizon
    name_node = args.name_node
    name_param = args.name_param 
    value_param = args.value_param
    
    load_data_and_solve(args.vector, args.Time_Horizon, args.name_node, args.name_param, args.value_param)
    


   
