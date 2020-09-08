import numpy as np
from scipy.sparse import dok_matrix
from semantic import *

def check_var(constraints,variables,parameters,time):
    cons = constraints.get_elements()
    nb_cons = constraints.get_size()

    if time!=None:
        T = time.time
        step = time.step 

        tuple_time = ["T",T]
        parameters.add_element(tuple_time)
        tuple_time = ["step",step]
        parameters.add_element(tuple_time)
    else:
        T = 0

    for i in range(nb_cons):
        constr = cons[i]
        for j in range(len(variables)):
            var = variables[i]
            for k in range(T):
                expr = Expression('literal',k)
                var.set_expression(expr)
                current_parameter = parameters
                tuple_time = ['t',k] 
                current_parameter.add_element(tuple_time)
                print("t : " + str(k))
                term = variable_in_constraint(constr,var,current_parameter)
                print(term)         



def variable_in_constraint(constr,variable,constants):
    rhs = constr.get_rhs()
    lhs = constr.get_lhs()

    found1,value1 = variable_factor_in_expression(rhs,variable,constants)  
    found2,value2 = variable_factor_in_expression(lhs,variable,constants)
    
    value = value1 - value2
    return value

def variable_factor_in_expression(expression,variable,constants):
    e_type = expression.get_type()
    nb_child = expression.get_nb_children()
    found = False
    value = 0

    var_id = variable.type_id

    if e_type == 'literal':
        identifier = expression.get_name()
        print(type(identifier))
        if type(expression.get_name())!=float and type(expression.get_name())!=int:
            if identifier.name_compare(variable):
                type_id = identifier.get_type
                if type_id == 'assign':
                    t_expr = identifier.get_expression()
                    t_value = evaluate_expression(t_expr,constants)
                    value = evaluate_expression(variable.get_expression(),constants)
                    if value == t_value:
                        found = True
                else:
                    found = True
    else:
        children = expression.get_children()
        if e_type == 'u-':
            found,value = variable_factor_in_expression(children[0],variable,constants)
            value = - value
        else:
            found1,value1 = variable_factor_in_expression(children[0],variable,constants)
            found2,value2 = variable_factor_in_expression(children[1],variable,constants)
            
            if e_type == '+':
                if found1 or found2:
                    found = True
                    if found1 and found2:
                        value = value1+value2
                    elif found1:
                        value = value1
                    else:
                        value = value2
            elif e_type == '-':
                if found1 or found2:
                    found = True
                    if found1 and found2:
                        value = value1-value2
                    elif found1:
                        value = value1
                    else:
                        value = -value2
            elif e_type == '*':
                if found1:
                    child = children[1]
                    value = value1
                else:
                    child = children[0]
                    value = value2

                constant = evaluate_expression(child,constants) #MUST BE ALL CONSTANTS AS DEFINITIONS
                value = value*constant
            elif e_type == '/':
                if found1:
                    constant = evaluate_expression(children[1],constants)
                    value = value1/constant
    return found,value


class Matrix: 
    def __init__(self):
        self.matrix = None
        self.name = name
        self.parameters = parameters
        self.variables = variables
        self.constraints = constraints
        self.links = links

    def fill_matrix(self):
        for j in range(len(constraints)):
            const = constraints[i]
            for i in range(len(variables)):
                terms = self.variable_in_constraint(constr,variables[i])
                

'''
import numpy as np
from scipy.sparse import dok_matrix
S = dok_matrix((5, 5), dtype=np.float32)

for i in range(2):
    for j in range(2):
        S[i, j] = i + j  
print(S)
'''
