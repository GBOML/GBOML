from .classes import Program
import numpy as np  # type: ignore
from scipy.sparse import coo_matrix  # type: ignore
import itertools
from .utils import error_


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
	all_rows = []
	all_columns = []
	all_values = []
	all_indep_terms = []
	objective_map = {}

	nb_variables = root.get_nb_var_index()
	total_number_objectives = 0
	nodes = root.get_nodes()

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
			rows = rows + total_number_objectives
			number_node_objectives += number_objectives

			obj_data = dict()
			obj_data["type"] = optimization_type
			obj_data["indexes"] = np.arange(total_number_objectives, total_number_objectives + number_objectives)
			node_objectives[objective_index] = obj_data
			total_number_objectives = total_number_objectives + number_objectives

			if optimization_type == "max":
				values = - values
				independent_terms = - independent_terms
			all_values.append(values)
			all_columns.append(columns)
			all_rows.append(rows)
			all_indep_terms.append(independent_terms)
		objective_map[node_name] = node_objectives
		node.nb_objective_matrix = number_node_objectives
		node.objective_list = None

	if len(all_rows) == 0:
		error_("ERROR: no valid objective defined")

	rows = np.concatenate(all_rows)
	columns = np.concatenate(all_columns)
	values = np.concatenate(all_values)
	indep_terms = np.concatenate(all_indep_terms)
	sparse_matrix = coo_matrix((values, (rows, columns)), shape=(total_number_objectives, nb_variables))
	sparse_matrix.sum_duplicates()

	return sparse_matrix, indep_terms, objective_map


def matrix_generation_a_b(root: Program) -> tuple:
	"""
	matrix_generationAb function: takes as input a program object and returns a tuple 
	composed of a sparse matrix of constraints A and a vector of independent terms b.
	INPUT:  Program object
	OUTPUT: A -> Sparse coo matrix of the constraints
			b -> Np.ndarray of the independent term of each constraint
	"""

	all_rows = []
	all_columns = []
	all_values = []
	all_rhs = []

	nb_variables = root.get_nb_var_index()
	total_number_constraints = 0

	nodes = root.get_nodes()
	hyperlinks = root.get_links()

	for obj in itertools.chain.from_iterable([nodes, hyperlinks]):
		constr_fact_list = obj.get_constraint_factors()
		number_node_constraints = 0

		for constr_fact in constr_fact_list:
			internal_sparse: coo_matrix = constr_fact.sparse
			number_constraints, _ = internal_sparse.shape
			sign = constr_fact.extension_type
			values, rows, columns = internal_sparse.data, internal_sparse.row, internal_sparse.col
			independent_terms = constr_fact.independent_terms
			rows = rows+total_number_constraints
			total_number_constraints = total_number_constraints+number_constraints
			number_node_constraints += number_constraints
			if sign == "==":
				# Do c<=b and -c<=-b
				rows_duplicates = rows+number_constraints
				rows = np.concatenate([rows, rows_duplicates])

				values = np.concatenate([values, -values])
				columns = np.concatenate([columns, columns])

				independent_terms = np.concatenate([independent_terms, -independent_terms])

				total_number_constraints = total_number_constraints+number_constraints
				number_node_constraints += number_constraints
			elif sign == ">=":
				# Do -c<=-b
				values = -values
				independent_terms = - independent_terms

			all_values.append(values)
			all_columns.append(columns)
			all_rows.append(rows)
			all_rhs.append(independent_terms)
		obj.free_factors_constraints()
		obj.c_triplet_list = None
		obj.nb_constraint_matrix = number_node_constraints
	root.link_constraints = None

	if len(all_rows) == 0:
		error_("ERROR: no valid constraint defined")
	elif len(all_rows) == 1:
		all_rows = np.array(all_rows[0])
	else:
		all_rows = np.concatenate(all_rows)

	if len(all_columns) == 1:
		all_columns = np.array(all_columns[0])
	else:
		all_columns = np.concatenate(all_columns)

	if len(all_values) == 1:
		all_values = np.array(all_values[0])
	else:
		all_values = np.concatenate(all_values)

	if len(all_rhs) == 1:
		all_rhs = np.array(all_rhs[0], dtype=float)
	else:
		all_rhs = np.concatenate(all_rhs, dtype=float)

	sparse_matrix = coo_matrix((all_values, (all_rows, all_columns)), shape=(total_number_constraints, nb_variables))
	sparse_matrix.sum_duplicates()
	sparse_matrix.eliminate_zeros()

	return sparse_matrix, all_rhs
