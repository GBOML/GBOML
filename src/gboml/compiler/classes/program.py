# Copyright (C) 2020 - 2022
# Bardhyl Miftari, Mathias Berger, Hatim Djelassi, Damien Ernst,
# University of Liege .
# Licensed under the MIT License (see LICENSE file).

from gboml.compiler.utils import list_to_string, error_, turn_to_dict
from .node import Node


def get_variable_name_size_offset_tuples_from_dict(variables_dict):
    tuple_names = []
    for node_name in variables_dict.keys():

        node_var_dict = variables_dict[node_name]
        all_tuples = []
        for var_name in node_var_dict.keys():
            if type(node_var_dict[var_name]) == dict:
                intermediate_dict = {var_name: node_var_dict[var_name]}
                name_index = \
                    get_variable_name_size_offset_tuples_from_dict(
                        intermediate_dict)

            else:
                variable = node_var_dict[var_name]
                identifier = variable.get_identifier()
                name_index = [identifier.get_index(),
                              var_name, identifier.get_option(),
                              identifier.get_size()]
            all_tuples.append(name_index)
        tuple_names.append([node_name, all_tuples])
    return tuple_names


class Program: 
    """
    Program object is composed of: 
    - a list of nodes
    - a Time object
    - a list of Links
    - a list of link constraint arrays
    """

    def __init__(self, vector_n, global_param=None, timescale=None, links=None):
        
        if global_param is None:

            global_param = []
        self.vector_nodes = vector_n
        self.time = timescale
        self.links = links
        self.global_param = global_param
        self.link_constraints = []
        self.nb_var_index = 0
        self.var_dict = {}
        self.link_list = []
        self.factor_links = []
        self.dict_nodes_links = turn_to_dict(self.vector_nodes+self.links)

    def __str__(self):
        
        string = "["+str(self.vector_nodes)
        if self.time is not None:

            string += ' , '+str(self.time)
        if self.links is None:

            string += ']'
        else:

            string += ' , '+str(self.links)+']'

        return string

    def to_string(self):
        
        string = "Full program\n"
        if self.time is not None:

            string += str(self.time)+"\n"
        string += 'All the defined nodes : \n'
        elements = self.vector_nodes
        for i in range(len(self.vector_nodes)):

            string += '\tName : ' + list_to_string(elements[i].get_name())+'\n'
            string += '\t\tParameters : ' \
                      + list_to_string(elements[i].get_parameters())+'\n'
            string += '\t\tVariables : ' \
                      + list_to_string(elements[i].get_variables())+'\n'
            string += '\t\tConstraints : ' \
                      + list_to_string(elements[i].get_constraints())+'\n'
            string += '\t\tObjectives : ' \
                      + list_to_string(elements[i].get_objectives())+'\n'
        string += '\nLinks predefined are : ' + str(self.links)
        
        return string

    def get(self, list_names):
        if type(list_names) == str:
            name = list_names
            if name not in self.dict_nodes_links:
                return -1
            else:
                return self.dict_nodes_links[name]
        elif (type(list_names) == list and len(list_names) >= 1) \
                or type(list_names) == tuple:
            actual_dict = self.dict_nodes_links
            actual_object = None
            for name in list_names:
                if name not in actual_dict:

                    return None
                else:
                    actual_object = actual_dict[name]
                    if type(actual_object) == Node:
                        actual_dict = actual_object.get_internal_dict()
                    else:
                        actual_dict = {}
            return actual_object

    def set_link_factors(self, factor_list):

        self.factor_links = factor_list

    def free_factors_objectives(self):
        for node in self.vector_nodes:
            node.free_factors_objectives()

    def free_factors_constraints(self):
        for node in self.vector_nodes:
            node.free_factors_constraints()
        self.factor_links = None

    def get_link_factors(self):

        return self.factor_links

    def get_global_parameters(self):

        return self.global_param

    def get_dict_global_parameters(self):

        dict_param = {}
        for param in self.global_param:

            name = param.get_name()
            if name in dict_param:

                error_("Global parameter "+str(name)+" already defined")
            else:

                dict_param[name] = param
        
        return dict_param

    def get_time(self):

        return self.time

    def get_nodes(self):
        
        return self.vector_nodes

    def get_number_nodes(self):

        return len(self.vector_nodes)

    def get_links(self):
        
        return self.links

    def set_time(self, timescale):
        
        self.time = timescale

    def set_vector(self, vector_n):
        
        self.vector_nodes = vector_n

    def set_link_constraints(self, c):
        
        self.link_constraints = c

    def get_link_constraints(self):
        
        return self.link_constraints
    
    def add_link_constraints(self, c):

        self.link_constraints.append(c)

    def get_number_constraints(self):
        
        sum_constraints = 0
        for node in self.vector_nodes:

            sum_constraints += node.get_nb_constraints_matrix()
        
        return sum_constraints 
    
    def check_objective_existence(self):
        
        nodes = self.vector_nodes
        found = False
        for node in nodes:

            objectives = node.get_objectives()
            nb_objectives = len(objectives)

            if nb_objectives != 0:

                found = True
                break
        if found is False:

            error_("ERROR: No objective function was defined")

    def get_nb_var_index(self):

        return self.nb_var_index

    def set_nb_var_index(self, index):

        self.nb_var_index = index

    def set_global_parameters(self, global_param):

        self.global_param = global_param

    def set_variables_dict(self, var_dict):

        self.var_dict = var_dict

    def get_variables_dict(self):

        return self.var_dict

    def get_tuple_name(self):

        return get_variable_name_size_offset_tuples_from_dict(self.var_dict)

    def add_var_link(self, tuple_list):
        link = []

        for element in tuple_list:

            [node_name, _, identifier, _] = element
            link.append([node_name, str(identifier)])
        self.link_list.append(link)

    def get_link_var(self):

        return self.link_list

    def get_first_level_constraints_decomposition(self):
        per_block_constraint_indexes = []
        start_index = 0
        current_index = 0
        nodes = self.vector_nodes
        hyperedges = self.links
        for node in nodes:
            current_index += node.get_number_expanded_constraints(True)
            per_block_constraint_indexes.append([start_index, current_index-1])
            start_index = current_index

        for hyperedge in hyperedges:
            current_index += hyperedge.get_number_expanded_constraints()
        per_block_constraint_indexes.append([start_index, current_index-1])
        return per_block_constraint_indexes
