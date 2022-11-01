# Copyright (C) 2020 - 2022
# Bardhyl Miftari, Mathias Berger, Hatim Djelassi, Damien Ernst,
# University of Liege .
# Licensed under the MIT License (see LICENSE file).

from .classes import Program
from .utils import error_, get_only_objects_in_nested_dict_layer

import numpy as np  # type: ignore
from scipy.sparse import coo_matrix  # type: ignore
import multiprocessing as mp


def flatten_definitions_and_get_values(definitions):
    flatten_dict = {}
    for key, value in definitions.items():
        if isinstance(value, dict):
            for sub_key, sub_param in value.items():
                flatten_key = key+"."+sub_key
                if sub_param.get_type() == "expression":
                    flatten_dict[flatten_key] = sub_param.get_value()[0]
                else:
                    flatten_dict[flatten_key] = np.array(sub_param.get_value())
        else:
            if value.get_type() == "expression":
                flatten_dict[key] = value.get_value()[0]
            else:
                flatten_dict[key] = np.array(value.get_value())
    return flatten_dict


def get_flat_nodes_edges_ordered(nodes, hyperedges, without_hyperedges=False):
    all_nodes_edges = []
    for node in nodes:
        all_nodes_edges.append(node)
        sub_nodes = node.get_sub_nodes()
        sub_edges = node.get_sub_hyperedges()
        all_sub_nodes_edges = get_flat_nodes_edges_ordered(sub_nodes,
                                                           sub_edges,
                                                           without_hyperedges)
        all_nodes_edges += all_sub_nodes_edges

    if not without_hyperedges:
        all_nodes_edges += hyperedges

    return all_nodes_edges


def get_flat_nodes_edges_and_definition(nodes, hyperedges,
                                        definitions, accumulator_dict):
    node_definition_tuples = []
    edge_definition_tuples = []
    for node in nodes:
        node_name = node.get_name()
        sub_nodes = node.get_sub_nodes()
        sub_edges = node.get_sub_hyperedges()
        accumulator_dict[node_name] = \
            get_only_objects_in_nested_dict_layer(definitions[node_name])
        node_definition_tuples.append([node, accumulator_dict.copy()])
        sub_node_tuples, sub_edge_tuples = \
            get_flat_nodes_edges_and_definition(sub_nodes, sub_edges,
                                                definitions[node_name],
                                                accumulator_dict)
        node_definition_tuples += sub_node_tuples
        edge_definition_tuples += sub_edge_tuples
        accumulator_dict.pop(node_name)

    for edge in hyperedges:
        edge_name = edge.get_name()
        accumulator_dict[edge_name] = \
            get_only_objects_in_nested_dict_layer(definitions[edge_name])
        edge_definition_tuples.append([edge, accumulator_dict.copy()])
        accumulator_dict.pop(edge_name)

    return node_definition_tuples, edge_definition_tuples


def extend_node_factors_mapping(list_elements_definitions_tuple):
    list_elements, definitions = list_elements_definitions_tuple
    all_triplet_matrix_independent_terms_type = []
    for element in list_elements:
        element.extend(definitions)
        sparse, independent_terms, extension_type = \
            element.sparse, element.independent_terms, element.extension_type

        all_triplet_matrix_independent_terms_type.append([sparse,
                                                          independent_terms,
                                                          extension_type])
    return all_triplet_matrix_independent_terms_type


def extend_factor_on_multiple_processes(root: Program,
                                        definitions,
                                        nb_processes) -> None:
    nodes = root.get_nodes()
    hyperlinks = root.get_links()
    all_tuples = []
    accumulator_dict = {"global": definitions["global"], "T": definitions["T"]}
    node_definition_tuples, edge_definition_tuples = \
        get_flat_nodes_edges_and_definition(nodes, hyperlinks, definitions,
                                            accumulator_dict)
    for node, node_definition in node_definition_tuples:
        flat_node_definitions = flatten_definitions_and_get_values(node_definition)
        obj_fact_list = node.get_objective_factors()
        constr_fact_list = node.get_constraint_factors()
        all_tuples.append([obj_fact_list + constr_fact_list, flat_node_definitions])

    for link, link_definition in edge_definition_tuples:
        flat_link_definitions = flatten_definitions_and_get_values(link_definition)
        constr_fact_list = link.get_constraint_factors()
        all_tuples.append([constr_fact_list, flat_link_definitions])

    with mp.Pool(processes=nb_processes) as pool:
        results = pool.map(extend_node_factors_mapping, all_tuples)
    # pool.close()

    for i, node_factors in enumerate(all_tuples):
        node_results = results[i]
        factor_list, node_dict = node_factors
        for j, factor in enumerate(factor_list):
            sparse, independent_terms, extension_type = node_results[j]
            factor.sparse = sparse
            factor.extension_type = extension_type
            factor.independent_terms = independent_terms


def extend_factor(root: Program, definitions) -> None:
    nodes = root.get_nodes()
    hyperlinks = root.get_links()
    accumulator_dict = {"global": definitions["global"], "T": definitions["T"]}
    node_definition_tuples, edge_definition_tuples = \
        get_flat_nodes_edges_and_definition(nodes, hyperlinks, definitions,
                                            accumulator_dict)
    for node, node_definition in node_definition_tuples:
        flat_node_definitions = flatten_definitions_and_get_values(node_definition)
        obj_fact_list = node.get_objective_factors()
        for i, object_fact in enumerate(obj_fact_list):
            object_fact.extend(flat_node_definitions)
        constr_fact_list = node.get_constraint_factors()
        for constr_fact in constr_fact_list:
            constr_fact.extend(flat_node_definitions)

    for link, link_definition in edge_definition_tuples:
        flat_link_definitions = flatten_definitions_and_get_values(link_definition)
        constr_fact_list = link.get_constraint_factors()
        for constr_fact in constr_fact_list:
            constr_fact.extend(flat_link_definitions)


def matrix_generation_c(root: Program) -> tuple:
    """
    matrix_generationC function: takes as input a program object and returns
    a coo_matrix of the different objectives flatten. In other words, returns
    the different objectives as a matrix : min C*x where each line of C
    corresponds to one objective.
    INPUT:  Program object
    OUTPUT: C -> Sparse coo matrix of the objective function
            objective_map -> Mapping to check which objective relates
                             to which node
    """

    nb_variables = root.get_nb_var_index()
    nodes = root.get_nodes()
    nodes = get_flat_nodes_edges_ordered(nodes, [], without_hyperedges=True)
    length_values = 0
    length_independent_terms = 0
    number_of_objectives = 0
    for node in nodes:
        objective_factors_list = node.get_objective_factors()
        for objective_index, objective_factor in \
                enumerate(objective_factors_list):
            internal_sparse: coo_matrix = objective_factor.sparse
            if internal_sparse is None:
                continue
            number_objective, _ = internal_sparse.shape
            independent_terms = objective_factor.independent_terms
            values = internal_sparse.data

            length_values += len(values)
            number_of_objectives += number_objective
            length_independent_terms += len(independent_terms)

    all_values = np.zeros(length_values)
    all_rows = np.zeros(length_values)
    all_columns = np.zeros(length_values)
    indep_terms = np.zeros(length_independent_terms)
    values_offset = 0
    independent_terms_offset = 0
    objective_offset = 0
    alone_indep_terms = 0

    for node in nodes:
        node_objectives = {}
        number_node_objectives = 0
        objective_factors_list = node.get_objective_factors()

        for objective_index, objective_factor in \
                enumerate(objective_factors_list):

            optimization_type = objective_factor.extension_type
            internal_sparse: coo_matrix = objective_factor.sparse
            name_objective = objective_factor.get_name()
            if internal_sparse is None:
                independent_terms = objective_factor.independent_terms
                if independent_terms and len(independent_terms) != 0:
                    if optimization_type == "max":
                        independent_terms = - independent_terms
                    if isinstance(independent_terms, np.ndarray):
                        alone_indep_terms += independent_terms.sum()
                    else:
                        alone_indep_terms += independent_terms
                obj_data = dict()
                obj_data["type"] = "no_variables"
                obj_data["indexes"] = None
                obj_data["values"] = independent_terms.sum()
                if name_objective is not None:
                    obj_data["name"] = name_objective
                node_objectives[objective_index] = obj_data
                continue
            number_objectives, _ = internal_sparse.shape
            values, rows, columns = \
                internal_sparse.data, internal_sparse.row, internal_sparse.col
            independent_terms = objective_factor.independent_terms
            rows += objective_offset

            number_of_values = len(values)
            number_of_independent_terms = len(independent_terms)

            obj_data = dict()
            obj_data["type"] = optimization_type
            obj_data["indexes"] = np.arange(objective_offset,
                                            objective_offset
                                            + number_objectives)
            if name_objective is not None:
                obj_data["name"] = name_objective
            node_objectives[objective_index] = obj_data

            if optimization_type == "max":
                values = - values
                independent_terms = - independent_terms

            all_values[values_offset:values_offset + number_of_values] = values
            all_columns[values_offset:values_offset + number_of_values] = \
                columns
            all_rows[values_offset:values_offset + number_of_values] = rows
            indep_terms[independent_terms_offset:
                        independent_terms_offset
                        + number_of_independent_terms] = independent_terms
            values_offset += number_of_values
            independent_terms_offset += number_of_independent_terms
            objective_offset += number_objectives
            number_node_objectives += number_objectives

        node.set_objectives_data(node_objectives)
        node.nb_objective_matrix = number_node_objectives
        node.objective_list = None

    if len(all_rows) == 0:
        error_("ERROR: no valid objective defined")

    sparse_matrix = coo_matrix((all_values, (all_rows, all_columns)),
                               shape=(number_of_objectives, nb_variables))
    return sparse_matrix, indep_terms, alone_indep_terms


def get_constraints_matrix_and_rhs(graph_elements, type_to_get="eq"):
    length_values = 0
    length_independent_terms = 0
    number_of_constraints = 0

    for obj in graph_elements:
        constr_fact_list = obj.get_constraint_factors()
        for constr_fact in constr_fact_list:
            internal_sparse: coo_matrix = constr_fact.sparse
            if internal_sparse is None:
                continue
            if (type_to_get == "eq" and constr_fact.obj.get_type() == "==") or \
                    (type_to_get != "eq" and constr_fact.obj.get_type() != "=="):
                number_constraints, _ = internal_sparse.shape
                independent_terms = constr_fact.independent_terms
                values = internal_sparse.data

                length_values += len(values)
                number_of_constraints += number_constraints
                length_independent_terms += len(independent_terms)

    all_values = np.zeros(length_values)
    all_rows = np.zeros(length_values)
    all_columns = np.zeros(length_values)
    all_rhs = np.zeros(length_independent_terms)
    values_offset = 0
    independent_terms_offset = 0
    constraint_offset = 0

    for obj in graph_elements:
        constr_fact_list = obj.get_constraint_factors()
        number_node_constraints = 0
        factor_mapping = {}
        for constr_fact in constr_fact_list:
            if (type_to_get == "eq" and constr_fact.obj.get_type() != "==") or \
                    (type_to_get != "eq" and constr_fact.obj.get_type() == "=="):
                continue
            internal_sparse: coo_matrix = constr_fact.sparse
            if internal_sparse is None:
                continue
            number_constraints, _ = internal_sparse.shape
            sign = constr_fact.extension_type
            values, rows, columns = \
                internal_sparse.data, internal_sparse.row, internal_sparse.col
            independent_terms = constr_fact.independent_terms
            rows += constraint_offset
            number_of_values = len(values)
            number_of_independent_terms = len(independent_terms)

            if sign == ">=":
                # Do -c<=-b
                values = -values
                independent_terms = - independent_terms

            all_values[values_offset:values_offset + number_of_values] = values
            all_columns[values_offset:values_offset + number_of_values] = \
                columns
            all_rows[values_offset:values_offset + number_of_values] = rows
            all_rhs[independent_terms_offset:
                    independent_terms_offset
                    + number_of_independent_terms] = independent_terms

            values_offset += number_of_values
            independent_terms_offset += number_of_independent_terms
            constraint_offset += number_constraints
            number_node_constraints += number_constraints

            if constr_fact.get_name():
                factor_mapping[constr_fact.get_name()] \
                    = slice(constraint_offset - number_constraints,
                            constraint_offset)
        if factor_mapping:
            obj.set_constraints_data(factor_mapping, type_to_get)
        obj.set_nb_constraints(number_node_constraints, type_to_get)
    return all_values, all_rows, all_columns, all_rhs, number_of_constraints


def free_factors(graph_elements):
    for obj in graph_elements:
        obj.free_factors_constraints()
        obj.c_triplet_list = None


def matrix_generation_a_b(root: Program) -> tuple:
    """
    matrix_generationAb function: takes as input a program object and
    returns a tuple composed of a sparse matrix of constraints A and
    a vector of independent terms b.
    INPUT:  Program object
    OUTPUT: A -> Sparse coo matrix of the constraints
            b -> Np.ndarray of the independent term of each constraint
    """

    number_of_variables = root.get_nb_var_index()
    nodes = root.get_nodes()
    hyperlinks = root.get_links()
    graph_elements = get_flat_nodes_edges_ordered(nodes, hyperlinks,
                                                  without_hyperedges=False)
    all_values_eq, all_rows_eq, all_columns_eq, all_rhs_eq, number_of_constraints_eq = \
        get_constraints_matrix_and_rhs(graph_elements, type_to_get="eq")
    all_values_ineq, all_rows_ineq, all_columns_ineq, all_rhs_ineq, number_of_constraints_ineq = \
        get_constraints_matrix_and_rhs(graph_elements, type_to_get="ineq")
    root.link_constraints = None
    sparse_matrix_eq = coo_matrix((all_values_eq, (all_rows_eq, all_columns_eq)),
                                  shape=(number_of_constraints_eq,
                                         number_of_variables))

    sparse_matrix_ineq = coo_matrix((all_values_ineq, (all_rows_ineq, all_columns_ineq)),
                                    shape=(number_of_constraints_ineq,
                                           number_of_variables))
    free_factors(graph_elements)
    return sparse_matrix_eq, all_rhs_eq, sparse_matrix_ineq, all_rhs_ineq
