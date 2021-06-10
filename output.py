import pandas as pd
from version import __version__


def generate_json(program, variable_names, solver_data, status, solution, objective, c_matrix, indep_terms_c,
                  objective_map):

    data = dict()
    # Add global data
    data["version"] = __version__
    # Build and add model data dictionary
    model_data = {}
    horizon = program.time.get_value()
    model_data["horizon"] = horizon
    model_data["number_nodes"] = program.get_number_nodes()
    model_data["global_parameters"] = program.get_global_parameters()
    nodes = {}
    for node in program.get_nodes():

        node_data = dict()
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

    hyperlinks = {}
    for link in program.get_links():
        link_data = dict()
        link_data["number_parameters"] = link.get_number_parameters()
        link_data["number_constraints"] = link.get_number_constraints()
        link_data["number_expanded_constraints"] = link.get_number_expanded_constraints()
        link_data["parameters"] = link.get_parameter_dict()
        link_data["variables_used"] = link.get_variables_used()
        hyperlinks[link.get_name()] = link_data

    model_data["hyperedges"] = hyperlinks

    data["model"] = model_data
    # Add solver data dictionary
    data["solver"] = solver_data
    # Build and add solution data dictionary
    solution_data = dict()
    solution_data["status"] = status
    solution_data["objective"] = objective
    var_dict = program.get_variables_dict()

    if solution is not None:
        product = c_matrix*solution+indep_terms_c
        nodes = {}
        for node_name, variable_indexes in variable_names:

            inner_node_vars = var_dict[node_name]
            all_obj = []
            node_data = {}
            variables = {}
            for index, var_name, _, _ in variable_indexes:

                var_obj = inner_node_vars[var_name]
                variables[var_name] = solution[index:(index+var_obj.get_size())].flatten().tolist()
            if node_name in objective_map:

                objective_dict = objective_map[node_name]
                for i in objective_dict.keys():

                    obj = objective_dict[i]
                    obj_type = obj["type"]
                    obj_indexes = obj["indexes"]
                    value = product[obj_indexes].sum()
                    if obj_type == "max":

                        value = -value
                    all_obj.append(value)
            node_data["variables"] = variables
            node_data["objectives"] = all_obj
            nodes[node_name] = node_data
        solution_data["nodes"] = nodes
    data["solution"] = solution_data

    return data


def generate_pandas(x, horizon, name_tuples):

    ordered_values = []
    columns = []
    for node_name, variable_indexes in name_tuples:

        for index, var_name, _, var_size in variable_indexes:

            full_name = str(node_name)+"."+str(var_name)
            values = x[index:(index+var_size)].flatten()
            columns.append(full_name)
            ordered_values.append(values)
    df = pd.DataFrame(ordered_values, index=columns)

    return df.T
