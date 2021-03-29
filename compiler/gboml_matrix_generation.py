from .classes import Time, Expression,Variable,Parameter,Attribute,Program,\
	Objective,Node,Identifier,Constraint
import numpy as np # type: ignore
from scipy.sparse import coo_matrix # type: ignore
from .utils import error_

def matrix_generationC(root:Program)-> coo_matrix:
	"""
	matrix_generationC function: takes as input a program object and returns a coo_matrix 
	of the different objectives flatten. In other words, returns the different objectives
	as a matrix : min C*x where each line of C corresponds to one objective.
    INPUT:  Program object
    OUTPUT: C -> Sparse coo matrix of the objective function
			objective_map -> Mapping to check which objectif relates to which node
    """

	nodes = root.get_nodes()
	nb_objectives = 0
	all_rows = []
	all_values = []
	all_columns = []

	nb_variables = root.nb_variables

	time_root = root.get_time()
	T = time_root.get_value()

	objective_map = {}

	for node in nodes:
		node_objectives = {}
		same_objective_index = []

		objectives = node.get_objective_list()
		var_matrix = node.get_variable_matrix()
		index_start = var_matrix[0][0].get_index()

		old_obj = 0

		for [values,rows,columns,objective_index],obj_type in objectives:
			#print(node.get_name())
			columns+=T*rows+index_start
			
			nb_values = len(values)
			row = np.zeros(nb_values)
			row.fill(nb_objectives)

			if obj_type == "max":
				values = - values

			if old_obj == objective_index:
				same_objective_index.append(nb_objectives)

			else: 
				objective_dict = {}
				objective_dict["indexes"] = same_objective_index
				objective_dict["type"] = obj_type
				node_objectives[str(old_obj)] = objective_dict
				old_obj = objective_index
				same_objective_index = [nb_objectives]

			all_values.append(values)
			all_columns.append(columns)
			all_rows.append(row)
			
			nb_objectives = nb_objectives+1
		
		if same_objective_index != []:
			objective_dict = {}
			objective_dict["indexes"] = same_objective_index
			objective_dict["type"] = obj_type
			node_objectives[str(old_obj)] = objective_dict

			objective_map[node.get_name()] = node_objectives


	rows = np.concatenate(all_rows)

	columns = np.concatenate(all_columns)

	values = np.concatenate(all_values)

	return coo_matrix((values, (rows, columns)),shape=(nb_objectives, nb_variables)), objective_map

def matrix_generationAb(root:Program)->tuple:
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
    for node in nodes:

        constraints = node.get_constraints_matrix()
        for [values,col_indexes],rhs,sign in constraints:

            if sign == "==":
                #Do c<=b and -c<=-b
                row_indexes = np.zeros(len(values))
                row_indexes.fill(nb_constraints)
                all_values.append(values)
                all_columns.append(col_indexes)
                all_rows.append(row_indexes)
                all_rhs.append(rhs)
                nb_constraints = nb_constraints + 1
                sign = ">="

            if sign == ">=":
                #Do -c<=-b
                values = - values
                rhs = - rhs

            row_indexes = np.zeros(len(values))
            row_indexes.fill(nb_constraints)
            all_values.append(values)
            all_columns.append(col_indexes)
            all_rows.append(row_indexes)
            all_rhs.append(rhs)
            nb_constraints = nb_constraints + 1

    # TODO: add link constraints

    rows = np.concatenate(all_rows)
    columns = np.concatenate(all_columns)
    values = np.concatenate(all_values)
    rhs_vector = np.array(all_rhs)
    sparse_matrix = coo_matrix((values, (rows, columns)),shape=(nb_constraints, nb_variables))

    #sparse_matrix.sum_duplicates()
    sparse_matrix.eliminate_zeros()

    return sparse_matrix,rhs_vector

def set_index(variable_matrix:np.ndarray,start:int)->tuple:
	"""
	set_index function: takes as input a matrix of variables with the first element
	of each column being the timestep [0] of a new variable. It sets the index of that
	variable to its place in the flat X vector and returns a tuple of the next starting value
	and pairs starting index and variable name.
    INPUT: variable_matrix -> np.ndarray of identifier objects 
		   start -> the first starting index of a node in the flat vector X
	OUTPUT: start -> Next starting index of next node
			tuple_name -> list of starting index and variable name pairs
    """

	n,m = np.shape(variable_matrix)
	tuple_name = []
	for j in range(m):
		variable_matrix[0][j].set_index(start)
		name = variable_matrix[0][j].get_name()
		tuple_name.append([start,name])
		start = start+n
		
	return start,tuple_name
