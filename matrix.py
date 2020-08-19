import numpy as np
from scipy.sparse import dok_matrix
from semantic import evaluate_expression

def check_var(constraints,variables,parameters,t):
    cons = constraints.get_element()
    nb_cons = constraints.get_size()

    for i in range(nb_cons):
        for j in range(len(variables)):
            for k in range(t):
                
                current_parameter = parameters
                tuple_time = ['t',k] 
                current_parameter.append(tuple_time)
                



def variable_in_constraint(constr,variable,constants):
    rhs = constr.get_rhs()
    lhs = constr.get_lhs()

    found1,value1 = variable_factor_in_expression(rhs,variable)  
    found2,value2 = variable_factor_in_expression(lhs,variable)
    
    value = value1 - value2
    return value

def variable_factor_in_expression(expr,variable,constants):
    e_type = expression.get_type()
    nb_child = expression.get_nb_children()
    found = False
    value = 0

    var_id = variable.type_id

    if e_type == 'literal':
        identifier = expression.get_name()

        if type(expression.get_name())!=float or type(expression.get_name())!=int:
            if identifier.compare(variable):
                type_id = identifier.get_type
                if type_id == "complex" or type_id == 'assign':
                    t_expr = identifier.get_expression()
                    t_value = evaluate_expression(t_expr,constants)
                    value = evaluate_expression(variable.get_expression(),constants)
                    if value == t_value:
                        found = True
                else:
                    found = True
    else:
        children = expr.get_children()
        if e_type == 'u-':
            found,value = variable_factor_in_expression(children[0],variable)
            value = - value
        else:
            found1,value1 = variable_factor_in_expression(children[0],variable)
            found2,value2 = variable_factor_in_expression(children[1],variable)
            
            if e_type == '+':
                if found1 or found2:
                    found = True
                    if found1 and found2:
                        value = value1+value2
                    elif found1:
                        value = value1
                    else
                        value = value2
            elif e_type == '-':
                if found1 or found2:
                    found = True
                    if found1 and found2:
                        value = value1-value2
                    elif found1:
                        value = value1
                    else
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
