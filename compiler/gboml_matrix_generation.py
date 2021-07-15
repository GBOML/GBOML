from .classes import Program
import numpy as np  # type: ignore
from scipy.sparse import coo_matrix  # type: ignore
import itertools
from .utils import error_


def extend_factor(root: Program, definitions) -> None:
	nodes = root.get_nodes()
	for node in nodes:

		obj_fact_list = node.get_objective_factors()
		obj_acc = []
		for i, object_fact in enumerate(obj_fact_list):
			object_fact.extend(definitions)
			obj_matrix = object_fact.get_extension()
			obj_acc.append([i, obj_matrix])

		node.set_objective_matrix(obj_acc)
		constr_fact_list = node.get_constraint_factors()
		constr_acc = []
		for constr_fact in constr_fact_list:
			constr_fact.extend(definitions)
			constr_matrix = constr_fact.get_extension()
			constr_acc += constr_matrix
		node.set_constraints_matrix(constr_acc)
		node.constr_factors = None

	hyperlinks = root.get_links()
	for link in hyperlinks:

		constr_fact_list = link.get_constraint_factors()
		constr_acc = []
		for constr_fact in constr_fact_list:
			constr_fact.extend(definitions)
			constr_matrix = constr_fact.get_extension()
			constr_acc += constr_matrix
		link.set_constraints_matrix(constr_acc)
		link.constr_factors = None


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
	nb_objectives = 0

	nodes = root.get_nodes()

	for node in nodes:
		node_objectives = {}

		# TODO: Generation of the objective map currently assumes the following:
		# 1: the first obj_index will be 0 (if not, we generate an empty entry in the first loop iteration)
		# 2: objective with the same obj_index come in groups (we close an entry of node_objectives
		# once we get a new obj_index)
		# This could be avoided by having node.get_objective_list return a container that is structured by obj_indexes
		current_row_indexes = []
		objectives = node.get_objective_list()
		node_name = node.get_name()

		for obj_index, tuple_obj in objectives:
			_, _, sign = tuple_obj[0]
			obj_data = dict()
			obj_data["type"] = sign	
			obj_data["indexes"] = np.arange(nb_objectives, nb_objectives+len(tuple_obj))
			node_objectives[obj_index] = obj_data

			for [values, col_indexes], constant, sign in tuple_obj:

				current_row_indexes.append(nb_objectives)

				if sign == "max":
					values = - values
					constant = - constant

				row_indexes = np.zeros(len(values))
				row_indexes.fill(nb_objectives)
				all_values.append(values)
				all_columns.append(col_indexes)
				all_rows.append(row_indexes)
				all_indep_terms.append(constant)
				nb_objectives = nb_objectives + 1

		objective_map[node_name] = node_objectives
		node.objective_list = None
	rows = np.concatenate(all_rows)
	columns = np.concatenate(all_columns)
	values = np.concatenate(all_values)
	indep_terms = np.array(all_indep_terms)

	sparse_matrix = coo_matrix((values, (rows, columns)), shape=(nb_objectives, nb_variables))
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
	nb_constraints = 0

	nodes = root.get_nodes()
	hyperlinks = root.get_links()

	for obj in itertools.chain.from_iterable([nodes, hyperlinks]):

		constraints = obj.get_constraints_matrix()
		for [values, col_indexes], rhs, sign in constraints:

			if sign == "==":
				# Do c<=b and -c<=-b
				row_indexes = np.zeros(len(values))
				row_indexes.fill(nb_constraints)
				all_values.append(values)
				all_columns.append(col_indexes)
				all_rows.append(row_indexes)
				all_rhs.append(rhs)
				nb_constraints = nb_constraints + 1
				sign = ">="

			if sign == ">=":
				# Do -c<=-b
				values = - values
				rhs = - rhs

			row_indexes = np.zeros(len(values))
			row_indexes.fill(nb_constraints)
			all_values.append(values)
			all_columns.append(col_indexes)
			all_rows.append(row_indexes)
			all_rhs.append(rhs)
			nb_constraints = nb_constraints + 1
		obj.c_triplet_list = None
	root.link_constraints = None

	if len(all_rows) == 0:
		error_("ERROR: no valid constraint defined")
	elif len(all_rows) == 1:
		rows = np.array(all_rows[0])
	else:
		rows = np.concatenate(all_rows)

	if len(all_rows) == 1:
		columns = np.array(all_columns[0])
	else:
		columns = np.concatenate(all_columns)

	if len(all_values) == 1:
		values = np.array(all_values[0])
	else:
		values = np.concatenate(all_values)

	rhs_vector = np.array(all_rhs, dtype=float)
	sparse_matrix = coo_matrix((values, (rows, columns)), shape=(nb_constraints, nb_variables))
	sparse_matrix.sum_duplicates()
	sparse_matrix.eliminate_zeros()

	return sparse_matrix, rhs_vector
