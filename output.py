import pandas as pd
import numpy as np
from version import __version__

def generate_json(program, variable_names, solver_data, status, solution, objective, C, objective_map):
    data = {}
    # Add global data
    data["version"] = __version__

    # Build and add model data dictionary
    model_data = {}
    horizon = program.time.get_value()
    model_data["horizon"] = horizon
    model_data["number_nodes"] = program.get_number_nodes()
    
    nodes = {}
    for node in program.get_nodes():
        node_data = {}
        node_data["number_parameters"] = node.get_number_parameters()
        node_data["number_variables"] = node.get_number_variables()
        node_data["number_constraints"] = node.get_number_constraints()
        node_data["number_expanded_constraints"] = node.get_number_expanded_constraints()
        node_data["number_objectives"] = node.get_number_objectives()
        node_data["number_expanded_objectives"] = node.get_number_expanded_objectives()
        node_data["parameters"] = node.get_parameter_dict()
        node_data["variables"] = node.get_variable_names()
        nodes[node.get_name()] = node_data

    model_data["nodes"] = nodes

    model_data["links"] = program.get_link_var()

    data["model"] = model_data

    # Add solver data dictionary
    data["solver"] = solver_data

    # Build and add solution data dictionary
    solution_data = {}

    solution_data["status"] = status
    solution_data["objective"] = objective
 
    var_dict = program.get_variables_dict()

    if solution is not None:
        product = C*solution

        nodes = {}
        for node_name, variable_indexes in variable_names:
            inner_node_vars = var_dict[node_name]

            all_obj = []
            
            node_data = {}
            variables = {}
            for index, var_name in variable_indexes:
                var_obj = inner_node_vars[var_name]
                variables[var_name] = solution[index:(index+var_obj.get_size())].flatten().tolist()
            node_data["variables"] = variables
            node_data["objectives"] = all_obj
            nodes[node_name] = node_data

        solution_data["nodes"] = nodes

    data["solution"] = solution_data

    return data

def generate_pandas(x,T,name_tuples):
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

