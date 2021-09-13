"""Output file, generates the different types of output.

There are two possibilities of output, either json or csv. The two functions
generate_json and generate_pandas generate datastructures that can be written
into respectively a json and csv file.

  Typical usage example:

   json_output = generate_json(program, variable_names, solver_data,
                              status, solution, objective, c_matrix, indep_terms_c,
                              objective_map)
   with open(filename+".json", 'w') as outfile:
        json.dump(dictionary, outfile, indent=4)

"""


import pandas as pd
from version import __version__


def convert_parameter_dict_to_values(parameter_name_object_dict: dict) -> dict:
    """convert_parameter_dict_to_values

        retrieves the values out of a dictionary of Parameter objects where
        the keys are the parameter names and returns a similar dictionary where
        the keys are the same parameter names with their value replaced by the
        corresponding parameter value

        Args:
            parameter_name_object_dict (dict): dictionary of <parameter name, Parameter objects>

        Returns:
            parameter_name_value_dict: dictionary of <parameter name, list of values>

    """

    parameter_name_value_dict = {}
    for parameter_name in parameter_name_object_dict.keys():
        parameter_name_value_dict[parameter_name] = parameter_name_object_dict[parameter_name].get_value()
    return parameter_name_value_dict


def generate_json(program, variable_names, solver_data, status, solution, objective, c_matrix, indep_terms_c,
                  objective_map, constraint_info=dict(), variables_info=dict()) -> dict:
    """generate_json

        Converts all the information contained in the inputs into one dictionary
        that can be dumped in a json file

        Args:
            program (Program): program object containing the augmented abstract syntax tree
            variable_names (dict): dictionary of <node_name, list of variables>
            solver_data (dict): dictionary containing the solver data
            status (str): status of the solver
            solution (array): flat array containing the problem's solution
            objective (float): value of the objective
            c_matrix (array): matrix of all the objectives
            indep_terms_c (array): array of all the independent terms of each objective
            objective_map (dict): dictionary of the mapping between node, objective and index in matrix

        Returns:
            gathered_data: dictionary containing all the gathered information

    """
    gathered_data = dict()
    gathered_data["version"] = __version__
    model_data = {}
    horizon = program.time.get_value()
    model_data["horizon"] = horizon
    model_data["number_nodes"] = program.get_number_nodes()
    model_data["global_parameters"] = convert_parameter_dict_to_values(program.get_global_parameters())
    nodes = {}
    for node in program.get_nodes():

        node_data = dict()
        node_data["number_parameters"] = node.get_number_parameters()
        node_data["number_variables"] = node.get_number_variables()
        node_data["number_constraints"] = node.get_number_constraints()
        node_data["number_expanded_constraints"] = node.get_number_expanded_constraints()
        node_data["number_objectives"] = node.get_number_objectives()
        node_data["number_expanded_objectives"] = node.get_number_expanded_objectives()
        node_data["parameters"] = convert_parameter_dict_to_values(node.get_parameter_dict())
        node_data["variables"] = node.get_variable_names()
        nodes[node.get_name()] = node_data

    model_data["nodes"] = nodes

    hyperlinks = {}
    for link in program.get_links():
        link_data = dict()
        link_data["number_parameters"] = link.get_number_parameters()
        link_data["number_constraints"] = link.get_number_constraints()
        link_data["number_expanded_constraints"] = link.get_number_expanded_constraints()
        link_data["parameters"] = convert_parameter_dict_to_values(link.get_parameter_dict())
        link_data["variables_used"] = link.get_variables_used()
        hyperlinks[link.get_name()] = link_data

    model_data["hyperedges"] = hyperlinks

    gathered_data["model"] = model_data
    gathered_data["solver"] = solver_data

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
    gathered_data["solution"] = solution_data

    return gathered_data


def generate_pandas(program, solution, name_tuples) -> pd.DataFrame:
    """generate_pandas

        Converts all the information contained in the inputs into one pandas dataframe
        that can be dumped in a csv file

        Args:
            program (Program): program object containing the augmented abstract syntax tree
            solution (array): flat array containing the problem's solution
            name_tuples (dict): dictionary of <node_name, list of variables>

        Returns:
            df: pandas dataframe containing all the gathered information

    """
    ordered_values = []
    columns = []
    nodes = program.get_nodes()
    dict_name_tuple = {}
    for node_name, variables_info in name_tuples:
        dict_name_tuple[node_name] = variables_info

    global_param: dict = program.get_global_parameters()
    for param in global_param.keys():
        values = global_param[param].get_value()
        full_name = "global." + str(param)
        columns.append(full_name)
        ordered_values.append(values)

    for node in nodes:
        node_name = node.get_name()
        parameters = node.get_parameter_dict()
        variable_indexes = dict_name_tuple[node_name]

        for param in parameters.keys():
            values = parameters[param].get_value()
            full_name = str(node_name)+"."+str(param)
            columns.append(full_name)
            ordered_values.append(values)

        for index, var_name, _, var_size in variable_indexes:

            full_name = str(node_name)+"."+str(var_name)
            values = solution[index:(index+var_size)].flatten()
            columns.append(full_name)
            ordered_values.append(values)

    df = pd.DataFrame(ordered_values, index=columns)
    return df.T
