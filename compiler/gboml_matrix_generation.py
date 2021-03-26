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
	composed of a sparse matrix of constraints A, a vector of independant terms b and
	a mapping from the flat x vector to the original structure in name_tuples.
    INPUT:  Program object
    OUTPUT: A -> Sparse coo matrix of the constraints
			b -> Np.ndarray of the independant term of each constraint
			name_tuples -> mapping from flat x to graph structure
    """

	nodes = root.get_nodes()
	
	time_root = root.get_time()
	T = time_root.get_value()

	nb_constraints = 0
	index_start = 0

	list_of_b = []

	all_rows = []
	all_values = []
	all_columns = []
	tuples_names = []

	for node in nodes:
		new_index,t_name = set_index(node.get_variable_matrix(),index_start)
		tuples_names.append([node.get_name(),t_name])
		constraints = node.get_constraints_matrix()

		for [values,rows,columns],b,sign in constraints:
			
			columns+=T*rows+index_start
			nb_values = len(values)
			row = np.zeros(nb_values)
			row.fill(nb_constraints)

			if sign =="==":
				#Do c<=b and -c<=-b
				all_values.append(values)
				all_columns.append(columns)
				all_rows.append(row)
				list_of_b.append(b)
				sign = ">="
				nb_constraints = nb_constraints+1
				row = np.zeros(nb_values)
				row.fill(nb_constraints)

			if sign == ">=":
				#Do -c<=-b
				values = -values
				b = -b

			all_values.append(values)
			all_columns.append(columns)
			all_rows.append(row)
			list_of_b.append(b)
			nb_constraints = nb_constraints+1

		#exit()

		index_start = new_index

	links = root.get_link_constraints()
	nb_link_constr = 0

	for nodeIn, matrixIn,nodeOut,matrixOut in links:
		#print(nodeIn.get_name())
		matrixVarIn = nodeIn.get_variable_matrix()
		#print(matrixIn)
		matrixVarOut = nodeOut.get_variable_matrix()

		nonzero_rowIn,nonzero_columnIn = np.nonzero(matrixIn)
		#print(nonzero_rowIn,nonzero_columnIn)
		nonzero_rowOut,nonzero_columnOut = np.nonzero(matrixOut)

		#print(nodeOut.get_name())
		#print(matrixOut)
		#print(nonzero_rowOut,nonzero_columnOut)
		#print("\n\n")

		if len(nonzero_columnIn) != len(nonzero_columnOut):
			error_("Internal error : Non matching column size for matrices")

		for i in range(len(nonzero_columnIn)):
			m = 0
			for l in range(len(nonzero_columnOut)):
				if nonzero_columnOut[l]==nonzero_columnIn[i]:
					m = l

			k = nonzero_rowIn[i]
			#print(k)
			j = nonzero_rowOut[m]
			#print(j)
			indexIn = matrixVarIn[0][k].get_index()
			indexOut = matrixVarOut[0][j].get_index()
			
			columnIn = np.arange(indexIn,indexIn+T)
			columnOut = np.arange(indexOut,indexOut+T)

			column = np.ravel(np.column_stack((columnIn,columnOut)))
			row = np.repeat(np.arange(nb_constraints,nb_constraints+2*T),2)

			nb_constraints = nb_constraints+2*T

			values1 = np.empty((2*T,),int)
			values1[::2] = 1
			values1[1::2] = -1

			values2 = -values1
			
			all_values.append(values1)
			all_values.append(values2)

			all_columns.append(column)
			all_columns.append(column)

			all_rows.append(row)
			
			nb_link_constr += 2*T

	root.nb_variables = index_start

	rows = np.concatenate(all_rows)

	columns = np.concatenate(all_columns)

	values = np.concatenate(all_values)

	b_values = np.array(list_of_b)

	b_links = np.zeros(nb_link_constr)

	b_values = np.append(b_values,b_links)

	sparse_matrix = coo_matrix((values, (rows, columns)),shape=(nb_constraints, index_start))

	#sparse_matrix.sum_duplicates()
	sparse_matrix.eliminate_zeros()

	return sparse_matrix,b_values,tuples_names

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
