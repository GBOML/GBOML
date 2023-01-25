# Copyright (C) 2020 - 2022
# Bardhyl Miftari, Mathias Berger, Hatim Djelassi, Damien Ernst,
# University of Liege .
# Licensed under the MIT License (see LICENSE file).


"""Output file, generates the different types of output.

There are two possibilities of output, either json or csv. The two functions
generate_json and generate_pandas generate datastructures that can be written
into respectively a json and csv file.

  Typical usage example:

   json_output = generate_json(program, variable_names, solver_data,
                              status, solution, objective, c_matrix,
                              indep_terms_c,
                              objective_map)
   with open(filename+".json", 'w') as outfile:
        json.dump(dictionary, outfile, indent=4)

"""

import csv
import numpy as np
from gboml.version import __version__


def convert_parameter_dict_to_values(parameter_name_object_dict: dict) -> dict:
    """convert_parameter_dict_to_values

        retrieves the values out of a dictionary of Parameter objects where
        the keys are the parameter names and returns a similar dictionary where
        the keys are the same parameter names with their value replaced by the
        corresponding parameter value

        Args:
            parameter_name_object_dict (dict): dictionary of <parameter name,
            Parameter objects>

        Returns:
            parameter_name_value_dict: dictionary of <parameter name,
            list of values>

    """

    parameter_name_value_dict = {}
    for parameter_name in parameter_name_object_dict.keys():
        parameter_name_value_dict[parameter_name] = \
            parameter_name_object_dict[parameter_name].get_value()
    return parameter_name_value_dict


def get_nodes_and_edges_model_information(nodes, edges):
    """get_nodes_and_edges_model_information

        recursively turning all the information relative to the model
        contained in a list of nodes and hyperedges

        Args:
            nodes (list <Node>) : list of nodes
            edges (list <Hyperedge>) : list of hyperedges

        Returns:
            nodes_information : node model information
            hyperedge_info : hyperedge model information

    """
    nodes_information = {}
    for node in nodes:
        node_data = dict()
        node_data["number_parameters"] = node.get_number_parameters()
        node_data["number_variables"] = node.get_number_variables()
        node_data["number_constraints"] = node.get_number_constraints()
        nb_eq, nb_ineq = node.get_number_expanded_constraints()
        node_data["number_expanded_constraints"] = nb_eq+nb_ineq
        node_data["number_objectives"] = node.get_number_objectives()
        node_data["number_expanded_objectives"] = \
            node.get_number_expanded_objectives()
        node_data["parameters"] = \
            convert_parameter_dict_to_values(node.get_parameter_dict())
        node_data["variables"] = node.get_variable_names()
        sub_nodes = node.get_sub_nodes()
        sub_edges = node.get_sub_hyperedges()
        sub_nodes_info, sub_hyperedge_info = \
            get_nodes_and_edges_model_information(sub_nodes, sub_edges)
        if sub_nodes_info != {}:
            node_data["sub_nodes"] = sub_nodes_info
        if sub_hyperedge_info != {}:
            node_data["sub_hyperedges"] = sub_hyperedge_info
        nodes_information[node.get_name()] = node_data

    hyperedge_info = {}
    for link in edges:
        link_data = dict()
        link_data["number_parameters"] = link.get_number_parameters()
        link_data["number_constraints"] = link.get_number_constraints()
        nb_eq, nb_ineq = link.get_number_expanded_constraints()
        link_data["number_expanded_constraints"] = nb_ineq+nb_eq

        link_data["parameters"] = \
            convert_parameter_dict_to_values(link.get_parameter_dict())
        link_data["variables_used"] = link.get_variables_used()
        hyperedge_info[link.get_name()] = link_data

    return nodes_information, hyperedge_info


def dict_values_in_nested_dict(nodes, hyperedges, solution,
                               c_matrix_time_solution,
                               constraint_info=None,
                               variables_info=None):
    """dict_values_in_nested_dict

        recursively turning all the information relative to the solution
        contained in a list of nodes and hyperedges

        Args:
            nodes (list <Node>) : list of nodes
            hyperedges (list <Hyperedge>) : list of hyperedges
            solution (numpy array) : array of the solution
            c_matrix_time_solution (numpy array) : array of the
                                                   objective_matrix * solution
                                                   + independent terms
            constraint_info (dict) : eventual additional information
                                     relative to the constraints
            variables_info (dict) : eventual additional information relative

        Returns:
            dict_solution (dict) : dictionary gathering and structuring
                                   all the information

    """
    if variables_info is None:
        variables_info = dict()
    if constraint_info is None:
        constraint_info = dict()
    dict_solution = {}

    for node in nodes:
        dict_node_solution = {}
        dict_variables_solution = {}
        dict_constraints_solution = {}
        node_name = node.get_name()
        variables_dict = node.get_dictionary_variables()

        for var_name, identifier in variables_dict.items():
            all_info_for_variable = {}
            start_index = identifier.get_index()
            size_variable = identifier.get_size()
            values_concerned = solution[start_index:
                                        (start_index + size_variable)]
            if type(values_concerned) != list:
                all_info_for_variable["values"] = values_concerned.flatten().tolist()
            else:
                all_info_for_variable["values"] = values_concerned

            for variable_info_name, variable_info_values \
                    in variables_info.items():
                if len(variable_info_values) > 1 and\
                        type(variable_info_values[0]) == list:
                    list_info = []
                    for value_info in variable_info_values:
                        list_info.append(value_info[start_index:
                                                    (start_index
                                                     + size_variable)])
                    all_info_for_variable[variable_info_name] = list_info
                else:
                    all_info_for_variable[variable_info_name] = \
                        variable_info_values[start_index:
                                             (start_index + size_variable)]
            dict_variables_solution[var_name] = all_info_for_variable

        dict_node_solution["variables"] = dict_variables_solution

        constraints_info_in_node = node.get_constraints_data()

        if constraint_info != {}:
            for constr_by_type, in_node_constr_by_type in constraints_info_in_node.items():
                current_dict = constraint_info[constr_by_type]
                for constraint_name, indexes in in_node_constr_by_type.items():
                    all_info_for_constraint = {}
                    for constraint_info_name, constraint_info_values in \
                            current_dict.items():
                        all_info_for_constraint[constraint_info_name] = \
                            constraint_info_values[indexes]
                    dict_constraints_solution[constraint_name] = \
                        all_info_for_constraint

            if dict_constraints_solution != {}:
                dict_node_solution['constraints'] = dict_constraints_solution

        named_objectives_info = {}
        unnamed_objectives_info = []
        named_and_unnamed_objectives_info = {}
        objectives_data = node.get_objectives_data()
        for i, objective_info in objectives_data.items():
            objective_type = objective_info["type"]

            if objective_type == "min" or objective_type == "max":
                indexes = objective_info["indexes"]
                objective_value = c_matrix_time_solution[indexes].sum()
                if objective_type == "max":
                    objective_value = -objective_value
            else:
                objective_value = objective_info["values"]

            if "name" in objective_info:
                name_objective = objective_info["name"]
                named_objectives_info[name_objective] = objective_value
            else:
                unnamed_objectives_info.append(objective_value)

        if named_objectives_info != {}:
            named_and_unnamed_objectives_info["named"] = named_objectives_info

        if unnamed_objectives_info:
            named_and_unnamed_objectives_info["unnamed"] = \
                unnamed_objectives_info

        if named_and_unnamed_objectives_info != {}:
            dict_node_solution["objectives"] = named_and_unnamed_objectives_info

        sub_nodes = node.get_sub_nodes()
        sub_hyperedges = node.get_sub_hyperedges()

        sub_elements = dict_values_in_nested_dict(sub_nodes,
                                                  sub_hyperedges,
                                                  solution,
                                                  c_matrix_time_solution,
                                                  constraint_info,
                                                  variables_info)
        if sub_elements != {}:
            dict_node_solution["sub_elements"] = sub_elements

        dict_solution[node_name] = dict_node_solution

    if constraint_info != {}:
        for hyperedge in hyperedges:
            hyperedge_name = hyperedge.get_name()
            dict_hyperedge_solution = {}
            dict_hyperedge_constraints_solution = {}
            constraints_info_in_node = hyperedge.get_constraints_data()

            for constr_type, in_node_dict_by_type in constraints_info_in_node.items():
                current_dict = constraint_info[constr_type]
                for constraint_name, indexes in in_node_dict_by_type.items():
                    all_info_for_constraint = {}
                    for constraint_info_name, constraint_info_values in \
                            current_dict.items():
                        all_info_for_constraint[constraint_info_name] = \
                            constraint_info_values[indexes]
                    dict_hyperedge_constraints_solution[constraint_name] = \
                        all_info_for_constraint

            if dict_hyperedge_constraints_solution != {}:
                dict_hyperedge_solution['constraints'] = \
                    dict_hyperedge_constraints_solution
                dict_solution[hyperedge_name] = dict_hyperedge_solution

    return dict_solution


def generate_json(program, solver_data, status, solution, objective, c_matrix,
                  indep_terms_c, constraint_info=None,
                  variables_info=None) -> dict:
    """generate_json

        Converts all the information contained in the inputs into one dictionary
        that can be dumped in a json file

        Args:
            program (Program): program object containing the augmented abstract
                               syntax tree
            solver_data (dict): dictionary containing the solver data
            status (str): status of the solver
            solution (array): flat array containing the problem's solution
            objective (float): value of the objective
            c_matrix (array): matrix of all the objectives
            indep_terms_c (array): array of all the independent terms of
                                   each objective
            constraint_info (dict): dictionary containing additional
                                    constraints information
            variables_info (dict): dictionary containing additional
                                   variables information

        Returns:
            gathered_data: dictionary containing all the gathered information

    """
    if variables_info is None:
        variables_info = dict()
    if constraint_info is None:
        constraint_info = dict()
    gathered_data = dict()
    gathered_data["version"] = __version__
    model_data = {}
    horizon = program.time.get_value()
    model_data["horizon"] = horizon
    model_data["number_nodes"] = program.get_number_nodes()
    model_data["global_parameters"] = \
        convert_parameter_dict_to_values(program.get_global_parameters())
    nodes, hyperlinks = \
        get_nodes_and_edges_model_information(program.get_nodes(),
                                              program.get_links())

    model_data["nodes"] = nodes
    model_data["hyperedges"] = hyperlinks

    gathered_data["model"] = model_data
    gathered_data["solver"] = solver_data

    solution_data = dict()
    solution_data["status"] = status
    solution_data["objective"] = objective

    if solution is not None:
        product = c_matrix * solution + indep_terms_c

        solution_data["elements"] = \
            dict_values_in_nested_dict(program.get_nodes(),
                                       program.get_links(),
                                       solution,
                                       product,
                                       constraint_info,
                                       variables_info)
    gathered_data["solution"] = solution_data

    return gathered_data


def flat_graph_and_add_node_prefix(nodes, hyperedges, solution, product, constraints_info=None, prefix=""):
    """flat_graph_and_add_node_prefix

        creates a list of the nodes and hyperedges variables & parameters
         and their value. The name of the variable and parameters is
         given as : prefix.parent.parent.

        Args:
            nodes (list<Node>): list of nodes
            hyperedges (list<Hyperedge>): list of hyperedges
            solution (array): flat array containing the problem's solution
            product (ndarray): product of the solution and objective matrix
            constraints_info (dict): dict of constraints information
            prefix (str): prefix to add to the variables and parameters names

        Returns:
            name_tuples: list of tuples <identifier, values>

    """
    solution = np.array(solution)
    name_tuples = []
    for node in nodes:
        variables_dict = node.get_dictionary_variables()
        node_name = prefix+node.get_name()
        for var_name, identifier in variables_dict.items():

            start_index = identifier.get_index()
            size_variable = identifier.get_size()
            identifier_name = node_name+"."+identifier.get_name()
            values = solution[start_index:
                              (start_index + size_variable)].flatten().tolist()
            name_tuples.append([identifier_name, values])

        #parameters = node.get_parameter_dict()
        #for parameter_name, parameter_object in parameters.items():

        #    values = parameter_object.get_value()
        #    parameter_full_name = str(node_name) + "." + str(parameter_name)
        #    name_tuples.append([parameter_full_name, values])

        objectives_data = node.get_objectives_data()
        for i, objective_info in objectives_data.items():
            objective_type = objective_info["type"]
            if "name" in objective_info:
                name_objective = objective_info["name"]

            else:
                name_objective = "unnamed_objective"

            if objective_type == "min" or objective_type == "max":
                indexes = objective_info["indexes"]
                objective_value = product[indexes].sum()
                if objective_type == "max":
                    objective_value = -objective_value
            # ELSE : objective_type is no_variables
            else:
                objective_value = objective_info["values"]
            name_tuples.append([str(node_name) + "." + name_objective, [objective_value]])

        constraints_info_in_node = node.get_constraints_data()
        if constraints_info != {}:
            for constr_type, constr_dict in constraints_info_in_node.items():
                current_constr_dict = constraints_info[constr_type]
                for constraint_name, indexes in constr_dict.items():
                    for constraint_info_name, constraint_info_values in \
                            current_constr_dict.items():
                        name_tuples.append([str(node_name) + "." + constraint_name + "." + constraint_info_name,
                                            constraint_info_values[indexes]])

        sub_nodes = node.get_sub_nodes()
        sub_hyperedges = node.get_sub_hyperedges()
        name_tuples += flat_graph_and_add_node_prefix(sub_nodes,
                                                      sub_hyperedges,
                                                      solution,
                                                      product,
                                                      constraints_info,
                                                      node_name+".")

    for hyperedge in hyperedges:
        hyperedge_name = prefix+hyperedge.get_name()
        parameters = hyperedge.get_parameter_dict()
        #for parameter_name, parameter_object in parameters.items():
        #    values = parameter_object.get_value()
        #    parameter_full_name = str(hyperedge_name) + "." \
        #                          + str(parameter_name)
        #    name_tuples.append([parameter_full_name, values])

        if constraints_info != {}:
            constraints_info_in_hyperedge = hyperedge.get_constraints_data()
            for constr_type, constr_dict in constraints_info_in_hyperedge.items():
                current_constr_dict = constraints_info[constr_type]
                for constraint_name, indexes in constr_dict.items():
                    for constraint_info_name, constraint_info_values in \
                            current_constr_dict.items():
                        name_tuples.append([str(hyperedge_name) + "." + constraint_name + "." + constraint_info_name,
                                            constraint_info_values[indexes]])

    return name_tuples


def generate_list_values_tuple(program, solution, c_matrix, indep_terms_c, constraints_info=None):
    """generate_list_values_tuple

        Converts all the information contained in the inputs into a tuple
        of names and values where values[i] is the list of values
        corresponding to names[i]

        Args:
            program (Program): program object containing the augmented
                               abstract syntax tree
            solution (array): flat array containing the problem's solution
            c_matrix(coo-matrix): matrix of all objectives
            indep_terms_c (array): array of independant terms
            constraints_info(dict): dict of information related to constraints
        Returns:
            names: list of flatten names of all parameters and variables
            values : list of values

    """
    if constraints_info == None:
        constraints_info = dict()
    ordered_values = []
    names = []
    nodes = program.get_nodes()
    hyperedges = program.get_links()

    product = []
    if solution is not None:
        product = c_matrix * solution + indep_terms_c

    global_param: dict = program.get_global_parameters()
    #for param in global_param.keys():
    #    values = global_param[param].get_value()
    #    full_name = "global." + str(param)
    #    names.append(full_name)
    #    ordered_values.append(values)

    name_value_tuples = flat_graph_and_add_node_prefix(nodes,
                                                       hyperedges,
                                                       solution,
                                                       product,
                                                       constraints_info,
                                                       prefix="")

    for name, values in name_value_tuples:
        names.append(name)
        ordered_values.append(values)

    return names, ordered_values


def write_csv(filename, names, values, transpose=False):

    if transpose is True:
        max_length = max([len(i) for i in values])
        column_ordered_values = []
        for i in range(max_length):
            row_i = []
            for value in values:
                if i < len(value):
                    row_i.append(value[i])
                else:
                    row_i.append(None)
            column_ordered_values.append(row_i)
        try:
            with open(filename, 'w', encoding='UTF8', newline="") as f:
                writer = csv.writer(f)
                writer.writerow(names)
                for row_i in column_ordered_values:
                    writer.writerow(row_i)
        except PermissionError:

            print("WARNING the file " + str(filename) +
                  ".csv already exists and is open.")
            print("Was unable to save the file")

    else:
        try:
            with open(filename, 'w', encoding='UTF8', newline="") as f:
                writer = csv.writer(f)

                for name, value in zip(names, values):
                    data = [name]+value
                    writer.writerow(data)
        except PermissionError:

            print("WARNING the file " + str(filename)
                  + ".csv already exists and is open.")
            print("Was unable to save the file")
