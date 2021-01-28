import pandas as pd
import numpy as np

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
