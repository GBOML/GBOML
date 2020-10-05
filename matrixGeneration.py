from classes import *
import numpy as np
from scipy.sparse import coo_matrix

def matrix_generationC(root):
	node_vector = root.get_nodes()
	nodes = node_vector.get_elements()
	node_size = node_vector.get_size()

	nb_objectives = 0
	all_rows = []
	all_values = []
	all_columns = []

	nb_variables = root.nb_variables

	index_start = 0
	time_root = root.get_time()
	T = time_root.time

	for node in nodes:
		objectives = node.get_objective_list()
		var_matrix = node.get_variable_matrix()
		index_start = var_matrix[0][0].get_index()
		for obj_matrix,obj_type in objectives:
			flat_matrix = obj_matrix.flatten()

			nonzero_index = np.nonzero(flat_matrix)
			nonzero_matrix = flat_matrix[nonzero_index]
			
			size_flat = flat_matrix.size
			size_nonzero = nonzero_matrix.size

			row = np.zeros(size_nonzero)
			row.fill(nb_objectives)

			column_interval = np.arange(index_start,index_start+size_flat)
			column = column_interval[nonzero_index]

			if obj_type == "max":
				nonzero_matrix = - nonzero_matrix

			all_values.append(nonzero_matrix)
			all_columns.append(column)
			all_rows.append(row)
			nb_objectives = nb_objectives+1

	rows = np.concatenate(all_rows)
	print("row "+str(rows))

	columns = np.concatenate(all_columns)
	print("columns "+str(columns))

	values = np.concatenate(all_values)
	print("values "+str(values))

	print(coo_matrix((values, (rows, columns)),shape=(nb_objectives, nb_variables)))
	return coo_matrix((values, (rows, columns)),shape=(nb_objectives, nb_variables))

def matrix_generationAb(root):
	node_vector = root.get_nodes()
	nodes = node_vector.get_elements()
	node_size = node_vector.get_size()

	time_root = root.get_time()
	T = time_root.time

	nb_constraints = 0
	index_start = 0

	list_of_b = []

	all_rows = []
	all_values = []
	all_columns = []

	nb_objectives = []

	for node in nodes:
		new_index = set_index(node.get_variable_matrix(),index_start)
		objectives = node.get_objective_list()
		constraints = node.get_constraints_matrix()
		print("constraints : "+str(constraints))

		for c_matrix,b,sign in constraints:
			print("c_matrix: "+str(c_matrix))
			flat_matrix = c_matrix.flatten('F')
			nonzero_index = np.nonzero(flat_matrix)
			nonzero_matrix = flat_matrix[nonzero_index]

			size_flat = flat_matrix.size
			size_nonzero = nonzero_matrix.size
			print(flat_matrix)
			
			row = np.zeros(size_nonzero)
			row.fill(nb_constraints)

			column_interval = np.arange(index_start,index_start+size_flat)
			column = column_interval[nonzero_index]

			if sign =="=":
				#Do c<=b and -c<=-b
				all_values.append(nonzero_matrix)
				all_columns.append(column)
				all_rows.append(row)
				list_of_b.append(b)
				sign = ">="
				nb_constraints = nb_constraints+1
				row = np.zeros(size_nonzero)
				row.fill(nb_constraints)

			if sign == ">=":
				#Do -c<=-b
				nonzero_matrix = -nonzero_matrix
				b = -b

			all_values.append(nonzero_matrix)
			all_columns.append(column)
			all_rows.append(row)
			list_of_b.append(b)
			nb_constraints = nb_constraints+1

		index_start = new_index

	links = root.get_link_constraints()

	for nodeIn, matrixIn,nodeOut,matrixOut in links:
		matrixVarIn = nodeIn.get_variable_matrix()
		matrixVarOut = nodeOut.get_variable_matrix()

		nonzero_rowIn,nonzero_columnIn = np.nonzero(matrixIn)
		nonzero_rowOut,nonzero_columnOut = np.nonzero(matrixOut)
		print("nonzero_lin "+str(nonzero_rowIn)+" nonzero_column "+str(nonzero_columnIn))

		if len(nonzero_columnIn) != len(nonzero_columnOut):
			error_("Internal error : Non matching column size for matrices")

		for i in range(len(nonzero_columnIn)):
			k = nonzero_rowIn[i]
			j = nonzero_rowOut[i]

			indexIn = matrixVarIn[0][k].get_index()
			indexOut = matrixVarOut[0][j].get_index()
			
			columnIn = np.arange(indexIn,indexIn+T)
			columnOut = np.arange(indexOut,indexOut+T)

			column = np.ravel(np.column_stack((columnIn,columnOut)))
			row = np.repeat(np.arange(nb_constraints,nb_constraints+T),2)

			nb_constraints = nb_constraints+T

			values = np.empty((2*T,),int)
			values[::2] = 1
			values[1::2] = -1

			all_values.append(values)
			all_columns.append(column)
			all_rows.append(row)
			for l in range(T):
				list_of_b.append(0)

		for i in range(len(nonzero_columnIn)):
			k = nonzero_rowIn[i]
			j = nonzero_rowOut[i]

			indexIn = matrixVarIn[0][k].get_index()
			indexOut = matrixVarOut[0][j].get_index()
			
			columnIn = np.arange(indexIn,indexIn+T)
			columnOut = np.arange(indexOut,indexOut+T)

			column = np.ravel(np.column_stack((columnIn,columnOut)))
			row = np.repeat(np.arange(nb_constraints,nb_constraints+T),2)

			nb_constraints = nb_constraints+T

			values = np.empty((2*T,),int)
			values[::2] = -1
			values[1::2] = 1

			all_values.append(values)
			all_columns.append(column)
			all_rows.append(row)
			for l in range(T):
				list_of_b.append(0)

	root.nb_variables = index_start

	rows = np.concatenate(all_rows)
	print(rows.size)

	columns = np.concatenate(all_columns)
	print(columns.size)

	values = np.concatenate(all_values)
	print(values.size)

	b_values = np.array(list_of_b)
	print(b_values)

	print(coo_matrix((values, (rows, columns)),shape=(nb_constraints, index_start)))
	return coo_matrix((values, (rows, columns)),shape=(nb_constraints, index_start)),b_values

def set_index(variable_matrix,start):
	n,m = np.shape(variable_matrix)
	for j in range(m):
		variable_matrix[0][j].set_index(start)
		start = start+n
	return start

def error_(string):
	print(string)
	exit(-1)