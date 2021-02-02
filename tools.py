from pandas import DataFrame
import numpy as np

def convert_dictionary(x:np.ndarray,T:int,name_tuples:list,objective:float,status:dict,program_dict:dict)->dict:
    """
	convert_dictionary function: converts all the gathered information in one big dictionary
    INPUT : x -> Vector of the solved problem
            T -> Time horizon
            name_tuples -> mapping to convert the flat x vector to the original structure
            objective -> value of objective function
            status -> dictionary containing the solution status
            program_dict -> general dictionary of all infos related to the program
    OUTPUT : dictionary -> dictionary of all the gathered info
    """
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

def convert_pandas(x:np.ndarray,T:int,name_tuples:list)->DataFrame:
    """
	convert_pandas function: converts the flat X vector to a pandas object containing the
    initial graph strucure
    INPUT : x -> Vector of the solved problem
            T -> Time horizon
            name_tuples -> mapping to convert the flat x vector to the original structure
    OUTPUT : df.T -> pandas object of the solution with the graph strucuture
    """
    ordered_values = []
    columns = []

    for node_name,index_variables in name_tuples:
        for index,variable in index_variables:
            full_name = str(node_name)+"."+str(variable)
            values = x[index:(index+T)].flatten()
            columns.append(full_name)
            ordered_values.append(values)

    df = DataFrame(ordered_values,index=columns)
    return df.T
