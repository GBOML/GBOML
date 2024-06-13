# -*- coding: utf-8 -*-
"""
Created on Mon Aug  7 17:19:41 2023

@author: Antoine Larbanois
"""



import json
import os
import argparse
import fct_dico

VECTORS = ["Ammonia", "Methane", "Hydrogen", "Methanol"]

        
def get_the_result_file_with_name(VECTOR, TIME_HORIZON, NAME_NODE, NAME_PARAM, VALUE_PARAM):
    
    if NAME_NODE :
        
        name_file = f"{VECTOR}_Time_Horizon_{TIME_HORIZON}_Modified_Model_{NAME_NODE}_{NAME_PARAM}_{VALUE_PARAM}.json"
        
    else : 
        
        name_file = f"{VECTOR}_Time_Horizon_{TIME_HORIZON}_Originals_Parameters.json"
        
    working_folder_path = os.getcwd()
    intermediate_folder1 = "RESULTS"
    intermediate_folder2 = VECTOR
    full_path = os.path.join(working_folder_path, intermediate_folder1, intermediate_folder2, name_file)
    
    print("selected file : ",name_file)


    if os.path.exists(full_path):
    
        if VECTOR == "Hydrogen" :
            with open(full_path, 'r') as file:
                H2_json = json.load(file)
                d1 = fct_dico.MakeMeReadable(H2_json)
                total_cost_hydrogen = d1.solution.objective
                production_of_hydrogen = sum(d1.solution.elements.LIQUEFIED_HYDROGEN_REGASIFICATION.variables.hydrogen.values)
                cost_per_MWH_hydrogen = (total_cost_hydrogen)/(production_of_hydrogen*0.0394) # HHV
                print(f"Hydrogen model : {(round(cost_per_MWH_hydrogen, 2))} €/MWh (HHV)")
        if VECTOR == "Ammonia" :
            with open(full_path, 'r') as file:
                NH3_json = json.load(file)
                d2 = fct_dico.MakeMeReadable(NH3_json)
                total_cost_ammonia = d2.solution.objective
                production_of_ammonia = sum(d2.solution.elements.LIQUEFIED_NH3_REGASIFICATION.variables.ammonia.values)
                cost_per_MWH_ammonia = (total_cost_ammonia)/(production_of_ammonia*0.00625) #HHV
                print(f"Ammonia model : {(round(cost_per_MWH_ammonia, 2))} €/MWh (HHV)")
        if VECTOR == "Methanol" :
            with open(full_path, 'r') as file:
                MEOH_json = json.load(file)
                d4 = fct_dico.MakeMeReadable(MEOH_json)
                total_cost_methanol = d4.solution.objective
                production_of_methanol = sum(d4.solution.elements.LIQUEFIED_METHANOL_CARRIERS.variables.liquefied_methanol_out.values)
                cost_per_MWH_methanol = (total_cost_methanol)/(production_of_methanol*0.00639) #HHV
                print(f"Methanol model : {(round(cost_per_MWH_methanol, 2))} €/MWh (HHV)")
        if VECTOR == "Methane" :
            with open(full_path, 'r') as file:
                CH4_json = json.load(file)
                d3 = fct_dico.MakeMeReadable(CH4_json)
                total_cost_methane = d3.solution.objective
                production_of_methane = sum(d3.solution.elements.LIQUEFIED_METHANE_REGASIFICATION.variables.methane.values)
                cost_per_MWH_methane = (total_cost_methane)/(production_of_methane*0.0154) #HHV
                print(f"Methane model : {(round(cost_per_MWH_methane, 2))} €/MWh (HHV)")
       
            
    else : 
        
        print("file not found -> incorrect name")
        

    
            
      

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    
    parser.add_argument('-v', '--vector', help="Vector used's name",
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
    
    get_the_result_file_with_name(args.vector, args.Time_Horizon, args.name_node, args.name_param, args.value_param)

    

    

        



    
