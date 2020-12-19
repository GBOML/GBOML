from classes import Time, Expression,Variable,Parameter,Link,Attribute,Program,Objective,Node,Identifier,Constraint
import numpy as np
from scipy.sparse import coo_matrix
from utils import error_

def matrix_generationC(root):
	nodes = root.get_nodes()
	nb_objectives = 0
	all_rows = []
	all_values = []
	all_columns = []

	nb_variables = root.nb_variables

	time_root = root.get_time()
	T = time_root.get_value()

	for node in nodes:
		objectives = node.get_objective_list()
		var_matrix = node.get_variable_matrix()
		index_start = var_matrix[0][0].get_index()

		for [values,rows,columns],obj_type in objectives:
			columns+=T*rows+index_start
			
			nb_values = len(values)
			row = np.zeros(nb_values)
			row.fill(nb_objectives)

			if obj_type == "max":
				values = - values

			all_values.append(values)
			all_columns.append(columns)
			all_rows.append(row)
			nb_objectives = nb_objectives+1

	rows = np.concatenate(all_rows)

	columns = np.concatenate(all_columns)

	values = np.concatenate(all_values)

	return coo_matrix((values, (rows, columns)),shape=(nb_objectives, nb_variables))

def matrix_generationAb(root):
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

			if sign =="=":
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

		index_start = new_index

	links = root.get_link_constraints()
	nb_link_constr = 0

	for nodeIn, matrixIn,nodeOut,matrixOut in links:
		matrixVarIn = nodeIn.get_variable_matrix()
		matrixVarOut = nodeOut.get_variable_matrix()

		nonzero_rowIn,nonzero_columnIn = np.nonzero(matrixIn)
		nonzero_rowOut,nonzero_columnOut = np.nonzero(matrixOut)

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

	return coo_matrix((values, (rows, columns)),shape=(nb_constraints, index_start)),b_values,tuples_names

def set_index(variable_matrix,start):
	n,m = np.shape(variable_matrix)
	tuple_name = []
	for j in range(m):
		variable_matrix[0][j].set_index(start)
		name = variable_matrix[0][j].get_name()
		tuple_name.append([start,name])
		start = start+n
		
	return start,tuple_name
