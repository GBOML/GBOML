# Copyright (C) 2020 - 2022
# Bardhyl Miftari, Mathias Berger, Hatim Djelassi, Damien Ernst,
# University of Liege .
# Licensed under the MIT License (see LICENSE file).

from gboml.compiler.utils import error_, turn_to_dict


class Node:
    """
    Node object is composed of: 
    - list of constraints
    - list of parameters
    - list of objectives 
    - list of variables
    - list of links related to the node
    - variable matrix (each column is an identifier of one variables)
    - triplet [array A, sign , b] for constraints
    - list of objective arrays
    - counter for number of constraints
    - all parameters dictionary [name, [values]]
    """

    def __init__(self, name, line=0):
        self.filename = ""
        self.name = name
        self.constraints = []
        self.variables = []
        self.parameters = []
        self.objectives = []
        self.line = line
        self.links = []
        self.v_matrix = None
        self.c_triplet_list = []
        self.objective_list = []
        self.nb_eq_constraints = 0
        self.nb_ineq_constraints = 0
        self.nb_constraint_matrix = 0
        self.nb_objective_matrix = 0
        self.param_dict = None
        self.constr_factors = []
        self.obj_factors = []
        self.nodes = []
        self.hyperedges = []
        self.expression = []
        self.parameters_changes = []
        self.variables_changes = []
        self.dict_sub_nodes_edges = {}
        self.objectives_data = {}
        self.constraints_data = {}

    def __str__(self):

        string = '[' + str(self.name) + ' , '
        string += str(self.parameters) + ' , '
        string += str(self.variables) + ' , '
        string += str(self.constraints) + ' , '
        string += str(self.objectives) + ']'

        return string

    def set_line(self, line):

        self.line = line

    def get_line(self):

        return self.line

    def get_sub_nodes(self):
        return self.nodes

    def set_sub_nodes(self, sub_nodes):
        self.nodes = sub_nodes

    def add_sub_node(self, node):
        self.nodes.append(node)

    def get_sub_hyperedges(self):
        return self.hyperedges

    def add_sub_hyperedge(self, hyperedge):
        self.hyperedges.append(hyperedge)

    def set_objectives_data(self, obj_data):
        self.objectives_data = obj_data

    def get_objectives_data(self):
        return self.objectives_data

    def set_constraints_data(self, constr_data, type_constr):
        self.constraints_data[type_constr] = constr_data

    def get_constraints_data(self):
        return self.constraints_data

    def set_sub_hyperedges(self, sub_hyperedges):
        self.hyperedges = sub_hyperedges

    def set_variables_changes(self, changes):
        self.variables_changes = changes

    def add_variable_change(self, change):
        self.variables_changes.append(change)

    def get_variables_changes(self):
        return self.variables_changes

    def set_parameters_changes(self, changes):
        self.parameters_changes = changes

    def add_parameter_change(self, change):
        self.parameters_changes.append(change)

    def get_parameters_changes(self):
        return self.parameters_changes

    def set_objective_factors(self, fact_list):

        self.obj_factors = fact_list

    def set_constraint_factors(self, fact_list):

        self.constr_factors = fact_list

    def set_nb_constraints(self, number, type_constr):
        if type_constr == "eq":
            self.nb_eq_constraints = number
        else:
            self.nb_ineq_constraints = number

    def update_internal_dict(self):

        self.dict_sub_nodes_edges = turn_to_dict(self.get_sub_nodes()
                                                 + self.get_sub_hyperedges())

    def get_internal_dict(self):
        return self.dict_sub_nodes_edges

    def get_objective_factors(self):

        return self.obj_factors

    def free_factors_objectives(self):
        self.obj_factors = None

    def free_factors_constraints(self):
        for factor in self.constr_factors:
            factor.sparse = None
            factor.independent_terms = None
        self.constr_factors = None

    def get_constraint_factors(self):

        return self.constr_factors

    def set_parameter_dict(self, param):

        param = param.copy()
        if "global" in param:
            param.pop("global")
        if "GLOBAL" in param:
            param.pop("GLOBAL")
        if "T" in param:
            param.pop("T")
        self.param_dict = param

    def set_expressions(self, list_expression):
        self.expression = list_expression

    def get_expressions(self):
        return self.expression

    def set_constraints(self, cons):

        self.constraints = cons

    def set_variables(self, var):

        self.variables = var

    def set_parameters(self, para):

        self.parameters = para

    def set_objectives(self, obj):

        self.objectives = obj

    def get_name(self):

        return self.name

    def rename(self, new_name):
        self.name = new_name

    def get_constraints(self):

        return self.constraints

    def remove_constraint(self, constraint):
        self.constraints.remove(constraint)

    def remove_objective(self, objective):
        self.objectives.remove(objective)

    def get_number_constraints(self):

        return len(self.constraints)

    def get_number_expanded_constraints(self, with_sub_nodes_and_edges=False):

        nb_eq_constr = self.nb_eq_constraints
        nb_ineq_constr = self.nb_ineq_constraints

        if with_sub_nodes_and_edges:
            for sub_node in self.get_sub_nodes():
                nb_eq_, nb_ineq_ = \
                    sub_node.get_number_expanded_constraints(True)
                nb_eq_constr += nb_eq_
                nb_ineq_constr += nb_ineq_

            for sub_hyperedge in self.get_sub_hyperedges():
                nb_eq_, nb_ineq_ = \
                    sub_hyperedge.get_number_expanded_constraints()
                nb_eq_constr += nb_eq_
                nb_ineq_constr += nb_ineq_

        return nb_eq_constr, nb_ineq_constr

    def get_parameter_dict(self):

        return self.param_dict

    def get_variables(self):

        return self.variables

    def get_number_variables(self):

        return len(self.variables)

    def get_variable_names(self):

        names = []
        for var in self.variables:
            names.append(var.get_name().get_name())

        return names

    def get_parameters(self):

        return self.parameters

    def get_number_parameters(self):

        return len(self.parameters)

    def get_objectives(self):

        return self.objectives

    def get_number_objectives(self):

        return len(self.objectives)

    def get_number_expanded_objectives(self):

        return self.nb_objective_matrix

    def set_variable_matrix(self, var_matrix):

        self.v_matrix = var_matrix

    def get_variable_matrix(self):

        return self.v_matrix

    def set_constraints_matrix(self, list_matrix):
        self.nb_constraint_matrix += len(list_matrix)
        self.c_triplet_list = list_matrix

    def add_constraints_matrix(self, c_matrix):

        self.nb_constraint_matrix += 1
        self.c_triplet_list.append(c_matrix)

    def get_constraints_matrix(self):

        return self.c_triplet_list

    def set_objective_matrix(self, o):

        length = 0
        for obj_index, tuple_obj in o:
            length += len(tuple_obj)
        self.nb_objective_matrix = length
        self.objective_list = o

    def add_objective_matrix(self, o):

        self.objective_list.append(o)

    def get_objective_list(self):

        return self.objective_list

    def get_nb_constraints_matrix(self):

        return self.nb_constraint_matrix

    def get_dictionary_variables(self, get_type="all", get_id=True):

        variables = self.variables
        all_variables = {}
        reserved_names = ["t", "T"]
        for var in variables:

            v_type = var.get_type()
            if get_type == "external" and v_type == "internal":
                continue
            if get_type == "internal" and v_type == "external":
                continue
            identifier = var.get_identifier()
            name = identifier.get_name()
            if name in reserved_names:
                error_("Semantic error, variable named " + str(name) +
                       " is not allowed at line " + str(var.get_line()))
            if name not in all_variables:

                if get_id:
                    all_variables[name] = identifier
                else:
                    all_variables[name] = var
            else:

                error_("Semantic error, redefinition of variable " + str(name)
                       + " at line " + str(var.get_line()))

        return all_variables

    def get_dictionary_parameters(self):

        parameters = self.parameters
        all_parameters = dict()
        reserved_names = ["t", "T"]
        for param in parameters:

            name = param.get_name()
            if name in reserved_names:
                error_(
                    "Semantic error, variable named " + str(name)
                    + " is not allowed at line " + str(param.get_line()))
            if name not in all_parameters:

                all_parameters[name] = param
            else:

                error_("Semantic error, redefinition of variable " + str(name)
                       + " at line " + str(param.get_line()))

        return all_parameters

    def get_dictionary_expressions(self):

        expressions = self.expression
        all_expressions = dict()
        reserved_names = ["t", "T"]
        for name, expr, line in expressions:

            if name in reserved_names:
                error_("Semantic error, expression named " + str(name) +
                       " is not allowed at line " + str(line))
            if name not in all_expressions:

                all_expressions[name] = expr
            else:

                error_("Semantic error, redefinition of expression "
                       + str(name) + " at line " + str(line))

        return all_expressions
