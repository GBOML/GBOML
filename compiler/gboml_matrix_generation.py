from .classes import Program
import numpy as np  # type: ignore
from scipy.sparse import coo_matrix  # type: ignore
import itertools
from .utils import error_
from multiprocessing import Process
import multiprocessing as mp


def extend_node_factors_mapping(list_elements_definitions_tuple):
	list_elements, definitions = list_elements_definitions_tuple
	all_triplet_matrix_independent_terms_type = []
	for element in list_elements:
		element.extend(definitions)
		sparse, independent_terms, extension_type = element.sparse, element.independent_terms, element.extension_type

		all_triplet_matrix_independent_terms_type.append([sparse, independent_terms, extension_type])
	return all_triplet_matrix_independent_terms_type


def extend_factor_on_multiple_processes(root: Program, definitions, nb_processes) -> None:
	nodes = root.get_nodes()
	all_tuples = []

	for node in nodes:
		node_name = node.get_name()
		obj_fact_list = node.get_objective_factors()
		constr_fact_list = node.get_constraint_factors()
		node_dict = {"global": definitions["global"], "T": definitions["T"], node_name: definitions[node_name]}
		all_tuples.append([obj_fact_list+constr_fact_list, node_dict])

	hyperlinks = root.get_links()
	for link in hyperlinks:
		link_name = link.get_name()
		constr_fact_list = link.get_constraint_factors()
		node_dict = {"global": definitions["global"], "T": definitions["T"], link_name: definitions[link_name]}
		all_tuples.append([constr_fact_list, node_dict])

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

	for node in nodes:
		obj_fact_list = node.get_objective_factors()
		for i, object_fact in enumerate(obj_fact_list):
			object_fact.extend(definitions)
		constr_fact_list = node.get_constraint_factors()
		for constr_fact in constr_fact_list:
			constr_fact.extend(definitions)

	hyperlinks = root.get_links()
	for link in hyperlinks:
		constr_fact_list = link.get_constraint_factors()
		for constr_fact in constr_fact_list:
			constr_fact.extend(definitions)


def matrix_generation_c(root: Program) -> tuple:
	"""
	matrix_generationC function: takes as input a program object and returns a coo_matrix 
	of the different objectives flatten. In other words, returns the different objectives
	as a matrix : min C*x where each line of C corresponds to one objective.
	INPUT:  Program object
	OUTPUT: C -> Sparse coo matrix of the objective function
			objective_map -> Mapping to check which objective relates to which node
	"""

	# TODO: add map (node name -> objective indexes) back in?
	nb_variables = root.get_nb_var_index()
	nodes = root.get_nodes()

	length_values = 0
	length_independent_terms = 0
	number_of_objectives = 0
	for node in nodes:
		objective_factors_list = node.get_objective_factors()
		for objective_index, objective_factor in enumerate(objective_factors_list):
			internal_sparse: coo_matrix = objective_factor.sparse
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
	objective_map = {}

	for node in nodes:
		node_objectives = {}
		number_node_objectives = 0
		objective_factors_list = node.get_objective_factors()
		node_name = node.get_name()

		for objective_index, objective_factor in enumerate(objective_factors_list):

			internal_sparse: coo_matrix = objective_factor.sparse
			number_objectives, _ = internal_sparse.shape
			optimization_type = objective_factor.extension_type
			values, rows, columns = internal_sparse.data, internal_sparse.row, internal_sparse.col
			independent_terms = objective_factor.independent_terms
			rows += objective_offset

			number_of_values = len(values)
			number_of_independent_terms = len(independent_terms)

			obj_data = dict()
			obj_data["type"] = optimization_type
			obj_data["indexes"] = np.arange(objective_offset, objective_offset + number_objectives)
			node_objectives[objective_index] = obj_data

			if optimization_type == "max":
				values = - values
				independent_terms = - independent_terms

			all_values[values_offset:values_offset + number_of_values] = values
			all_columns[values_offset:values_offset + number_of_values] = columns
			all_rows[values_offset:values_offset + number_of_values] = rows
			indep_terms[independent_terms_offset:independent_terms_offset + number_of_independent_terms] = independent_terms
			values_offset += number_of_values
			independent_terms_offset += number_of_independent_terms
			objective_offset += number_objectives
			number_node_objectives += number_objectives

		objective_map[node_name] = node_objectives
		node.nb_objective_matrix = number_node_objectives
		node.objective_list = None

	if len(all_rows) == 0:
		error_("ERROR: no valid objective defined")

	sparse_matrix = coo_matrix((all_values, (all_rows, all_columns)), shape=(number_of_objectives, nb_variables))
	return sparse_matrix, indep_terms, objective_map


def matrix_generation_a_b(root: Program) -> tuple:
	"""
	matrix_generationAb function: takes as input a program object and returns a tuple 
	composed of a sparse matrix of constraints A and a vector of independent terms b.
	INPUT:  Program object
	OUTPUT: A -> Sparse coo matrix of the constraints
			b -> Np.ndarray of the independent term of each constraint
	"""

	number_of_variables = root.get_nb_var_index()
	nodes = root.get_nodes()
	hyperlinks = root.get_links()
	length_values = 0
	length_independent_terms = 0
	number_of_constraints = 0

	for obj in itertools.chain.from_iterable([nodes, hyperlinks]):
		constr_fact_list = obj.get_constraint_factors()
		for constr_fact in constr_fact_list:
			internal_sparse: coo_matrix = constr_fact.sparse
			number_constraints, _ = internal_sparse.shape
			independent_terms = constr_fact.independent_terms
			sign = constr_fact.extension_type
			values = internal_sparse.data
			"""
			if sign == "==":
				length_values += 2*len(values)
				number_of_constraints += 2*number_constraints
				length_independent_terms += 2*len(independent_terms)
			else:
			"""
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
	constraints_mapping = {}

	for obj in itertools.chain.from_iterable([nodes, hyperlinks]):
		constr_fact_list = obj.get_constraint_factors()
		number_node_constraints = 0
		factor_mapping = {}
		object_name = obj.get_name()
		print(object_name)
		for constr_fact in constr_fact_list:

			internal_sparse: coo_matrix = constr_fact.sparse
			number_constraints, _ = internal_sparse.shape
			sign = constr_fact.extension_type
			values, rows, columns = internal_sparse.data, internal_sparse.row, internal_sparse.col
			independent_terms = constr_fact.independent_terms
			rows += constraint_offset
			number_of_values = len(values)
			number_of_independent_terms = len(independent_terms)

			if sign == ">=":
				# Do -c<=-b
				values = -values
				independent_terms = - independent_terms

			all_values[values_offset:values_offset+number_of_values] = values
			all_columns[values_offset:values_offset+number_of_values] = columns
			all_rows[values_offset:values_offset+number_of_values] = rows
			all_rhs[independent_terms_offset:independent_terms_offset+number_of_independent_terms] = independent_terms

			values_offset += number_of_values
			independent_terms_offset += number_of_independent_terms
			constraint_offset += number_constraints
			number_node_constraints += number_constraints
			"""
			if sign == "==":
				# Add also -c<=-b
				rows = rows+number_constraints
				values = -values
				independent_terms = -independent_terms

				all_values[values_offset:values_offset + number_of_values] = values
				all_columns[values_offset:values_offset + number_of_values] = columns
				all_rows[values_offset:values_offset + number_of_values] = rows
				all_rhs[independent_terms_offset:independent_terms_offset + number_of_independent_terms] = independent_terms

				values_offset += number_of_values
				independent_terms_offset += number_of_independent_terms
				constraint_offset += number_constraints
				number_node_constraints += number_constraints
				number_constraints = 2*number_constraints
			"""
			if constr_fact.get_name():
				factor_mapping[constr_fact.get_name()] = slice(constraint_offset-number_constraints, constraint_offset)
		if factor_mapping:
			constraints_mapping[object_name] = factor_mapping
		obj.free_factors_constraints()
		obj.c_triplet_list = None
		obj.nb_constraint_matrix = number_node_constraints
	root.link_constraints = None
	sparse_matrix = coo_matrix((all_values, (all_rows, all_columns)), shape=(number_of_constraints, number_of_variables))

	return sparse_matrix, all_rhs, constraints_mapping
