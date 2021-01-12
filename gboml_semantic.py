# -----------------------------------------------------------
# semantic analyzer of GSML language
#
# MIFTARI Bardhyl, Liege, Belgium
# 
# -----------------------------------------------------------

from classes import Time, Expression,Variable,Parameter,Link,\
    Attribute,Program,Objective,Node,Identifier,Constraint
import copy
import numpy as np
from utils import error_,list_to_string
import time as t

def semantic(program):
    """
    Semantic check function : Augments the inputed Program object and checks several errors     
    INPUT:  initialized Program object
    OUTPUT: augmented Program object ready to be transformed to matrix
    """

    #Retrieve time horizon
    time = program.get_time()
    time.check()
    time_value = time.get_value()
    
    #Check if all nodes have different names
    root = program.get_nodes()
    check_names(root)

    #Check if an objective function is defined
    program.check_objective_existance()

    #Inside each node 
    for node in root:
        #Initialize dictionary of defined parameters
        parameter_dictionary = {}
        parameter_dictionary["T"]=[time_value]

        #Retrieve all the parameters'names in set
        all_parameters = node.get_all_parameters_name()

        #Retrieve a dictionary of [name,identifier object] tuple
        all_variables = node.get_dictionary_variables()

        #Check if variables and parameters share names
        match_names(all_parameters,all_variables)

        #Add evaluated parameters to the dictionary of defined paramaters
        parameter_dictionary = parameter_evaluation(node.get_parameters(),parameter_dictionary)

        #Check constraints and objectives expressions
        check_expressions_dependancy(node,all_variables,all_parameters)

        #Augment node with constraintes written in matrix format
        convert_constraints_matrix(node,all_variables,parameter_dictionary)

        #Augment node with objectives written in matrix format
        convert_objectives_matrix(node,all_variables,parameter_dictionary)

    #if the model does not have a proper constraint defined
    if program.get_number_constraints()==0:
        error_("ERROR: no valid constraint was defined making the problem unsolvable")


    #LINKS conversion
    all_input_output_pairs = check_link(program)

    all_input_output_pairs = regroup_by_name(all_input_output_pairs)

    input_output_matrix = convert_links_to_matrix(all_input_output_pairs)

    program.set_link_constraints(input_output_matrix)

    return program


def convert_links_to_matrix(input_output_pairs):
    input_output_matrix = []

    for i in range(len(input_output_pairs)):
        
        input_node = input_output_pairs[i][1]
        output_node = input_output_pairs[i][3]
        for j in range(len(input_output_pairs[i][4])):
            vector_1, vector_2 = get_index_link(input_output_pairs[i][4][j])
            if j==0:
                matrixNodeIn = vector_1
                matrixNodeOut = vector_2
            else:
                matrixNodeIn = np.concatenate((matrixNodeIn,vector_1),axis = 1)
                matrixNodeOut = np.concatenate((matrixNodeOut,vector_2),axis = 1)
        quadruple = [input_node,matrixNodeIn,output_node,matrixNodeOut]
        input_output_matrix.append(quadruple)
    return input_output_matrix

def regroup_by_name(input_output_pairs):
    triplet = []

    for i in range(len(input_output_pairs)):
        link = input_output_pairs[i]
        input_attr = link[0]
        output_attr = link[1]

        name_input = input_attr.node
        node_input = input_attr.get_node_object()
        name_output = output_attr.node
        node_output = output_attr.get_node_object()

        found = False

        for j in range(len(triplet)):
            if triplet[j][0] == name_input and triplet[j][2]==name_output:
                triplet[j][4].append(link)
                found = True
                break

        if not found : 
            triplet.append([name_input,node_input,name_output,node_output,[link]])

    return triplet

def check_link(program):
    links = program.get_links()
    link_size = len(links)

    nodes = program.get_nodes()
    node_size = len(nodes)
    input_output_pairs = []

    for i in range(link_size):
        link_i = links[i]
        lhs = link_i.attribute
        lhs_name = lhs.node
        lhs_attribute = lhs.attribute

        found = False
        position = 0

        for j in range(node_size):
            node_j = nodes[j]
            node_j_name = node_j.get_name()
            if lhs_name == node_j_name:
                found = True
                lhs.set_node_object(node_j)
                position = j
                break

        if found == False: 
            error_("No Node is named : "+str(lhs_name)+ " in the link")

        rhs = link_i.vector
        rhs_size = len(rhs)

        if lhs_attribute != None :
            if find_variable_and_type(nodes[j],lhs_attribute,internal_v = False,input_v=False)==False:
                error_("The left hand side attribute of the link "+str(link_i)+ " was not found or is of type internal or input")

            for k in range(rhs_size):
                rhs_k = rhs[k]
                rhs_name = rhs_k.node
                rhs_attribute = rhs_k.attribute

                if rhs_name == lhs_name:
                    error_("Using a link inside the same node is not allowed")
                found = False
                position = 0

                for j in range(node_size):
                    node_j = nodes[j]
                    node_j_name = node_j.get_name()
                    if rhs_name == node_j_name:
                        found = True
                        rhs_k.set_node_object(node_j)
                        position = j
                        break

                if found == False: 
                    error_("No Node is named : "+str(rhs_name)+ " in the link "+ str(link_i))

                if find_variable_and_type(nodes[position],rhs_attribute,internal_v = False,output_v=False)==False:
                    error_("The right hand side attribute of the link "+str(link_i)+ " was not found or is of type internal or output")
                
                already_defined = False

                for j in range(len(input_output_pairs)):
                    if rhs_k.compare(input_output_pairs[j][0]):
                        if (not lhs.compare(input_output_pairs[j][1])):
                            error_("An input is assigned twice: first with value "+str(input_output_pairs[j][1])+ " then with value "+str(lhs))
                        else:
                            already_defined = True

                pair_input_output = [rhs_k,lhs]

                if not already_defined:
                    nodes[position].add_link(pair_input_output)
                    input_output_pairs.append(pair_input_output)

        else:
            variables= nodes[position].get_variables()
            variable_size = len(variables)
            found = False
            name = ""

            for j in range(variable_size):
                type_var = variables[j].get_type()
                if type_var == "output":
                    if found == False:
                        found = True 
                        identifier = variables[j].get_identifier()
                        name = identifier.get_name()
                    else : 
                        error_("Can not use linking with only node names if the left-hand side contains more than one outputted variable")
            if found == False:
                error_("The left-hand side node in linking must have an output variable")

            lhs.attribute = name

            for k in range(rhs_size):
                rhs_k = rhs[k]
                rhs_name = rhs_k.node
                
                if rhs_name == lhs_name:
                    error_("Using a link inside the same node is not allowed")
                found = False
                position = 0
                for j in range(node_size):
                    node_j = nodes[j]
                    node_j_name = node_j.get_name()
                    if rhs_name == node_j_name:
                        found = True
                        rhs_k.set_node_object(node_j)
                        position = j
                        break

                if found == False: 
                    error_("No Node is named : "+str(rhs_name)+ " in the link")

                variables = nodes[position].get_variables()
                variable_size = len(variables)
                found = False
                name = ""
                for j in range(variable_size):
                    type_var = variables[j].get_type()
                    if type_var == "input":
                        if found == False:
                            found = True 
                            identifier = variables[j].get_identifier()
                            name = identifier.get_name()
                        else : 
                            error_("Can not use linking with only node names if the right-hand side node contains more than one input variable")
                if found == False:
                    error_("The left-hand side node in linking must have an output variable")

                rhs_k.attribute = name
                already_defined = False

                for j in range(len(input_output_pairs)):
                    if rhs_k.compare(input_output_pairs[j][0]):
                        if (not lhs.compare(input_output_pairs[j][1])):
                            error_("An input is assigned twice: first with value "+str(input_output_pairs[j][1])+ " then with value "+str(lhs))
                        else:
                            already_defined = True

                pair_input_output = [rhs_k,lhs]
                if not already_defined:
                    nodes[position].add_link(pair_input_output)
                    input_output_pairs.append(pair_input_output)
    
    return input_output_pairs

def get_index_link(link):
    input_attr = link[0]
    output_attr = link[1]

    node_input = input_attr.get_node_object()
    node_output = output_attr.get_node_object()

    variables_input = node_input.get_variable_matrix()
    variables_output = node_output.get_variable_matrix()

    _,m = np.shape(variables_input)
    input_vector = np.zeros((m, 1))

    for i in range(m):
        if variables_input[0][i].name_compare(input_attr.attribute):
            input_vector[i]=1

    _,p = np.shape(variables_output)
    output_vector = np.zeros((p, 1))
    for j in range(p):
        if variables_output[0][j].name_compare(output_attr.attribute):
            output_vector[j] =1 

    return input_vector,output_vector



def find_variable_and_type(node,attribute_name,output_v = True,internal_v = True, input_v=True):
    variables= node.get_variables()
    variable_size = len(variables)
    found = False

    for i in range(variable_size):
        variable_i = variables[i]
        var_name = variable_i.get_name()
        var_type = variable_i.get_type()
        if var_name.name_compare(attribute_name):
        
            if ((var_type == "output" and output_v == True) or
                (var_type == "input" and input_v ==True) or
                (var_type == "internal" and internal_v ==True)):
                found =  True
    return found



def check_expressions_dependancy(node,variables,parameters):
    constraints = node.get_constraints()
    
    for cons in constraints:
        rhs = cons.get_rhs()
        lhs = cons.get_lhs()

        var_in_right = variables_in_expression(rhs,variables,parameters)
        var_in_left = variables_in_expression(lhs,variables,parameters)

        if var_in_right == False and var_in_left == False:
            error_('No variable in constraint at line '+str(cons.get_line()))

        check_linear(rhs,variables,parameters)
        check_linear(lhs,variables,parameters)
        
    objectives = node.get_objectives()

    for obj in objectives:
        expr = obj.get_expression()
        contains_var = variables_in_expression(expr,variables,parameters)
        if contains_var == False:
            error_('Objective only depends on constants not on variable at line '+str(expr.get_line()))
        check_linear(expr,variables,parameters)
    

def variables_in_expression(expression,variables,parameters,check_in = True):
    leafs = expression.get_leafs()
    is_variable = False
    defined = False

    for expr_id in leafs:
        
        identifier = expr_id.get_name()

        if type(identifier)!=int and type(identifier)!=float:
            id_name = identifier.get_name() 
            reserved_names = ["T","t"]
            if id_name in variables:
                is_variable = True
                defined = True
            
            elif id_name in parameters:
                defined = True
            
            elif id_name in reserved_names:
                defined = True 
                id_type = identifier.get_type()
                if id_type == "assign":
                    error_("Error: can not assign time variables : "+str(expression.get_name())+\
                        " at line "+str(expression.get_line()))
            
            if defined == False:
                error_("Undefined name "+str(expression.get_name())+" at line "+str(expression.get_line()))
            
            if check_in == True:
                check_in_brackets(identifier,variables,parameters)
            
    return is_variable

def check_linear(expression,variables,parameters):
    e_type = expression.get_type()
    nb_child = expression.get_nb_children()
    children = expression.get_children()

    if e_type == 'literal':
        if nb_child !=0:
            error_("INTERNAL ERROR : literal expression must have zero child, got "+str(nb_child)+" check internal parser")
    elif e_type == 'u-':
        if nb_child !=1:
            error_("INTERNAL ERROR : unary minus operator must have one child, got "+str(nb_child)+" check internal parser")
        lin1  =  check_linear(children[0],variables,parameters)
        if lin1 == False:
            error_("Non linearity in expression : "+str(children[0])+" only linear problems are accepted at line "+str(children[0].get_line()))
    else : 
        if nb_child != 2:
            error_("INTERNAL ERROR : binary operators must have two children, got "+str(nb_child)+" check internal parser")

        term1 = variables_in_expression(children[0],variables,parameters)
        term2 = variables_in_expression(children[1],variables,parameters)

        if e_type == "-" or e_type == '+':
            if term1 == True:
                lin1 = check_linear(children[0],variables,parameters)
                if lin1 == False:
                    error_("Non linearity in expression : "+str(children[0])+" only linear problems are accepted at line "+str(children[0].get_line()))
            if term2 == True:
                lin2 = check_linear(children[1],variables,parameters)
                if lin2 == False:
                    error_("Non linearity in expression : "+str(children[1])+" only linear problems are accepted at line "+str(children[0].get_line()))

        elif e_type == "*" or e_type == "/":
            if term2 == True and term1 == True:
                string = "Operation '"+str(e_type)+"' between two expressions containing variables leading to a non linearity at line "+str(children[0].get_line())+"\n"
                string +="Namely Expression 1 : " + str(children[0])+ " and Expression 2 : "+str(children[1])
                error_(string)

            if term2 == True and e_type == "/":
                string = "A variable in the denominator of a division leads to a Non linearity at line "+str(children[0].get_line())
                error_(string)

            if term1 == True:
                lin1 = check_linear(children[0],variables,parameters)
                if lin1 == False:
                    error_("Non linearity in expression : "+str(children[0])+" only linear problems are accepted at line "+str(children[0].get_line()))

        elif e_type == "**":
            if term1 == True or term2 == True:
                string = "Operation '"+str(e_type)+"' between one expression containing variables leading to a non linearity at line "+str(children[0].get_line())+"\n"
                string +="Namely Expression 1 : " + str(children[0])+ " and Expression 2 : "+str(children[1])
                error_(string)

        elif e_type == "mod":
            string = "Non linearity, modulo operator is not allowed on variables at line "+str(children[0].get_line())+"\n"
            error_(string)

        else:
            error_("INTERNAL ERROR : unknown type '"+str(e_type)+"' check internal parser")


    return True


def match_names(dict,set_compare):
    dictionary_set = set(dict)
 
    inter_set = dictionary_set.intersection(set_compare)  
 
    if len(inter_set)!=0:
        error_("ERROR : some variables and parameters share the same name: "+str(inter_set))

def check_names(elements,add_type = False):
    
    all_names = []
    n = len(elements)
    i = 0

    for e in elements:
        name = e.get_name()

        if name == "T" or name == "t":
            error_('ERROR: Name "'+str(name)+'" is reserved for time, used at line '+str(elements[i].get_line()))

        for k in range(i+1,n):
            if name == elements[k].get_name():
                error_('ERROR: Redefinition error: "'+str(name)+'" at line '+str(elements[k].get_line()))
        
        if add_type == True:
            all_names.append(name,e.get_type())
        else:
            all_names.append(name)

        i = i+1
    return all_names

def parameter_evaluation(n_parameters,definitions):
    
    for parameter in n_parameters:
        e = parameter.get_expression()
        name = parameter.get_name()
        if e != None:
            value = e.evaluate_expression(definitions)
            value = [value]
        else:
            value = evaluate_table(parameter.get_vector(),definitions)
        definitions[name]=value

    return definitions

def evaluate_table(list_values,definitions):
    all_values = []
    for value in list_values:
        value_i = value.get_name()

        if type(value_i) != float and type(value_i) !=int:
            type_val = value_i.get_type()
            id_name = value_i.get_name()

            if not (id_name in definitions):
                error_('Undefined parameter : '+str(value_i))

            values = definitions[id_name]
            if type_val == "basic" and len(values)==1:
                value_i = values[0]

            elif type_val == "basic" and len(values)>1:
                error_('Parameter not properly defined : '+str(value_i))

            elif type_val == "assign":
                inner_expr = value_i.get_expression()
                index = inner_expr.evaluate_expression(definitions)

                if type(index) == float:
                    if index.is_integer()==False:
                        error_("Error: an index is a float: "+ str(value_i))
                    index = int(round(index))

                if index<0 or len(values)<=index:
                    error_('Parameter does not exit at this index : '+str(value_i))

                value_i = values[index]

        all_values.append(value_i)

    return all_values

def check_in_brackets(identifier,variables,parameters):
    id_type = identifier.get_type()
    if id_type == 'assign':
        expr = identifier.get_expression()
        if expr == None:
            error_("INTERNAL ERROR : expected expression for "+str(id_type)+" check internal parser")
        check_expr_in_brackets(expr,variables,parameters)

def check_expr_in_brackets(expression,variables,parameters):
    e_type = expression.get_type()
    nb_child = expression.get_nb_children()
    found = False
    is_time_var = False

    if e_type =='literal':
        if nb_child != 0:
            error_("INTERNAL ERROR : literal must have zero child, got "+str(nb_child)+" check internal parser")
        identifier = expression.get_name()

        if type(identifier)!=float and type(identifier)!=int:
            id_name = identifier.get_name()
            id_type = identifier.get_type()
            
            time_variables = ["t","T"]
            if id_name in parameters:
                found = True
                    
            elif id_name in time_variables:
                is_time_var = True
                found = True
            
            elif id_name in variables:
                error_('Variable in brackets for assignement ')

            #if id_type != 'basic':
            #    error_('Parameter shall not have this type of structure '+str(identifier))
            #identifier = identifier.get_name()

            if found == False:
                error_('Identifier "'+ str(identifier)+ '" used but not previously defined, at line '+str(expression.get_line()))
            
            if id_type == "assign":
                is_time_var = check_expr_in_brackets(identifier.get_expression(),variables,parameters)

    elif e_type == 'u-':
        if nb_child != 1:
            error_("INTERNAL ERROR : unary minus must have one child, got "+str(nb_child)+" check internal parser")

        children = expression.get_children()
        is_time_var = check_expr_in_brackets(children[0],variables,parameters)
    else:
        if nb_child != 2:
            error_("INTERNAL ERROR : binary operators must have two children, got "+str(nb_child)+" check internal parser")

        children = expression.get_children()
        is_time_var1 = check_expr_in_brackets(children[0],variables,parameters)
        is_time_var2 = check_expr_in_brackets(children[1],variables,parameters)

        if e_type == '+' or e_type == '-':
            if is_time_var2 or is_time_var1:
                is_time_var = True       
        elif e_type =='*':
            if is_time_var2 and is_time_var1:
                error_("Non linearity in assignement")
            elif is_time_var2 or is_time_var1:
                is_time_var = True
        elif e_type == '/':
            if is_time_var2:
                error_("Non linearity in assignement")
            if is_time_var1:
                is_time_var = True
        elif e_type == '**':
            if is_time_var2 or is_time_var1:
                error_("Non linearity in assignement")
        elif e_type == "mod":
            if is_time_var2 or is_time_var1:
                is_time_var = True
        else:
            error_("INTERNAL ERROR : unexpected e_type "+str(e_type)+" check internal parser")

    return is_time_var

def convert_constraints_matrix(node,variables,definitions):
    """
    convert_constraints_matrix function : converts a node's constraints and variables 
    into constraint and variables matrices of the respective form [value,lign,column]
    and full matrix 
    INPUT:  node, node object treated
            variables, dictionary of variables
            definitions, dictionary with all the parameters and constants
    OUTPUT: None, augments the node object with the corresponding matrices
    """
    constraints = node.get_constraints()
    
    if not("T" in definitions):
        error_("INTERNAL ERROR: T not found in list of parameters")
    T = definitions["T"][0]

    start_time = t.time()
    all_variables = []

    for k in range(T):
        variables_for_time = []
        var_identifiers = list(variables.values())

        for variable in var_identifiers:
            var = copy.copy(variable)
            expr = Expression('literal',k)
            var.set_expression(expr)

            variables_for_time.append(var)
        all_variables.append(variables_for_time)


    X = np.array(all_variables)
    node.set_variable_matrix(X)
 
    n,_ = np.shape(X)
    start_time = t.time()

    for constr in constraints:
        constr_leafs = constr.get_leafs()
        variables_used = []

        for leaf in constr_leafs:
            identifier = leaf.get_name()
            if type(identifier)!=int and type(identifier)!=float:
                i=0
                for variable in variables: 
                    if identifier.name_compare(variable):
                        variables_used.append([i,identifier])
                        break
                    i +=1
    
        nb_variables = len(variables_used)
        
        #print('CONSTRAINT '+str(i+1) + ': '+str(constr))

        constr_range = constr.get_time_range(definitions)
        if constr_range == None:
            t_horizon = T
            constr_range = range(t_horizon)

        unique_constraint = False
        if(not is_time_dependant_constraint(constr,variables,definitions)):
            unique_constraint = True

        #print("time : "+str(is_time_dependant_constraint(constr,variables)))
        #print(constr)
        #print("t horizon" + str(t_horizon))
        add_t = 0
        for k in constr_range:
            definitions['t']=[k]

            if constr.check_time(definitions)==False:
                continue

            new_values = np.zeros(nb_variables)
            
            rows = np.zeros(nb_variables)
            columns = np.zeros(nb_variables)
            
            l = 0
            for n,identifier in variables_used:
                
                id_type = identifier.get_type()
                
                if id_type == "basic":
                    j = k
                else : 
                    j = identifier.get_expression().evaluate_expression(definitions)
                    if type(j) == float:
                        if j.is_integer()==False:
                            error_("Error: an index is a float: "+ str(identifier)+\
                                'at line '+str(identifier.get_line())+"for t = "+str(k))
                        j = int(round(j))

                    if j >= T or j<0:
                        flag_out_of_bounds = True
                        break
                    

                term,flag_out_of_bounds = variable_in_constraint(constr,X[j][n],definitions)
                new_values[l]=term

                rows[l]=n
                columns[l]=j
            
                if flag_out_of_bounds:
                    break
                l+=1
            
            if flag_out_of_bounds==False:
                starting_t = t.time() 
                constant = constant_in_constraint(constr,variables,definitions)
                add_t += t.time()-starting_t
                sign = constr.get_sign()
                matrix = [new_values,rows,columns]
                #print(constr)
                #print([matrix,constant,sign])

                node.add_constraints_matrix([matrix,constant,sign])
                if unique_constraint == True:
                    break
                        
        #print("add_time --- %s seconds ---" % (add_t))
    print("Check_var --- %s seconds ---" % (t.time() - start_time))


    
def constant_in_constraint(constr,variables,constants):
    """
    constant_in_constraint function : computes the constant factor 
    in an constraint
    INPUT:  constr, considered constraint
            variables, dictionary of variables
            constants, dictionary with all the parameters and constants
    OUTPUT: value, value of the constant in the constraint
    """
    rhs = constr.get_rhs()
    lhs = constr.get_lhs()

    value1 = constant_factor_in_expression(rhs,variables,constants)
    
    value2 = constant_factor_in_expression(lhs,variables,constants)
    
    value = value2 - value1
    return value

def constant_factor_in_expression(expression,variables,constants):
    """
    constant_factor_in_expression function : computes the constant factor 
    in an expression
    INPUT:  expression, considered expression
            variables, dictionary of variables
            constants, dictionary with all the parameters and constants
    OUTPUT: value, value of the constant in the expression
    """
    e_type = expression.get_type()
    children = expression.get_children()
    value = 0

    if variables_in_expression(expression,variables,constants,check_in = False)==False:
        value = expression.evaluate_expression(constants)
    else:
        if e_type == 'u-':
            is_var = variables_in_expression(children[0],variables,constants,check_in = False)
            if is_var==False:
                value = children[0].evaluate_expression(constants)
            else: 
                value = constant_factor_in_expression(children[0],variables,constants)
        elif e_type == "/":
            is_var1 = variables_in_expression(children[0],variables,constants,check_in = False)
            is_var2 = variables_in_expression(children[1],variables,constants,check_in = False)

            if is_var1 == False and is_var2 == False:
                value = children[0].evaluate_expression(constants)/children[1].evaluate_expression(constants)
            elif is_var1 == True:
                value = constant_factor_in_expression(children[0],variables,constants)/children[1].evaluate_expression(constants)
        elif e_type == "*":
            is_var1 = variables_in_expression(children[0],variables,constants,check_in = False)
            is_var2 = variables_in_expression(children[1],variables,constants,check_in = False)
            if is_var1 == False and is_var2 == False:
                value = children[0].evaluate_expression(constants)*children[1].evaluate_expression(constants)
            else:
                if is_var1:
                    value1 = constant_factor_in_expression(children[0],variables,constants)
                else:
                    value1 = children[0].evaluate_expression(constants)
                if is_var2:
                    value2 = constant_factor_in_expression(children[1],variables,constants)
                else:
                    value2 = children[1].evaluate_expression(constants)

                value = value1*value2
        elif e_type == '+':
            is_var1 = variables_in_expression(children[0],variables,constants,check_in = False)
            is_var2 = variables_in_expression(children[1],variables,constants,check_in = False)
            if is_var1 == False and is_var2 == False:
                value = children[0].evaluate_expression(constants)+children[1].evaluate_expression(constants)
            else:
                if is_var1:
                    value1 = constant_factor_in_expression(children[0],variables,constants)
                else:
                    value1 = children[0].evaluate_expression(constants)
                if is_var2:
                    value2 = constant_factor_in_expression(children[1],variables,constants)
                else:
                    value2 = children[1].evaluate_expression(constants)

                value = value1+value2
        elif e_type == '-':
            is_var1 = variables_in_expression(children[0],variables,constants,check_in = False)
            is_var2 = variables_in_expression(children[1],variables,constants,check_in = False)
            if is_var1 == False and is_var2 == False:
                value = children[0].evaluate_expression(constants)-children[1].evaluate_expression(constants)
            else:
                if is_var1:
                    value1 = constant_factor_in_expression(children[0],variables,constants)
                else:
                    value1 = children[0].evaluate_expression(constants)
                if is_var2:
                    value2 = constant_factor_in_expression(children[1],variables,constants)
                else:
                    value2 = children[1].evaluate_expression(constants)

                value = value1-value2
        elif e_type == '**':
            is_var1 = variables_in_expression(children[0],variables,constants,check_in = False)
            is_var2 = variables_in_expression(children[1],variables,constants,check_in = False)
            if is_var1 == False and is_var2 == False:
                value = children[0].evaluate_expression(constants)**children[1].evaluate_expression(constants)
            else:
                if is_var1:
                    value1 = constant_factor_in_expression(children[0],variables,constants)
                else:
                    value1 = children[0].evaluate_expression(constants)
                value2 = children[1].evaluate_expression(constants)

                value = value1**value2
    return value

def convert_objectives_matrix(node,variables,definitions):
    """
    convert_objectives_matrix function : converts a node's objectives 
    into objective matrices of the form [value,lign,column]
    INPUT:  node, node object treated
            variables, dictionary of variables
            definitions, dictionary with all the parameters and constants
    OUTPUT: None, augments the node object with the corresponding matrices
    """
    matrixVar = node.get_variable_matrix()
    n,_ = np.shape(matrixVar)

    objectives = node.get_objectives()
    obj_size = len(objectives)

    if not("T" in definitions):
        error_("INTERNAL ERROR: T not found in list of definitions")

    T = definitions["T"][0]

    for i in range(obj_size):
        obj = objectives[i]
        obj_type = obj.get_type()
        expr = obj.get_expression()

        expr_leafs = expr.get_leafs()

        variables_used = []

        for leaf in expr_leafs:
            identifier = leaf.get_name()
            if type(identifier)!=int and type(identifier)!=float:
                i = 0
                for variable in variables: 
                    if identifier.name_compare(variable):
                        variables_used.append([i,identifier])
                        break
                    i +=1
    
        nb_variables = len(variables_used)

        if(is_time_dependant_expression(expr,variables,definitions)):
            t_horizon = T
        else:
            t_horizon = 1

        for k in range(t_horizon):
            definitions["t"]=[k]

            values = np.zeros(nb_variables)
            rows = np.zeros(nb_variables)
            columns = np.zeros(nb_variables)

            l = 0
            for n,identifier in variables_used:
                id_type = identifier.get_type()

                if id_type == "basic":
                    j = k
                else : 
                    j = identifier.get_expression().evaluate_expression(definitions)

                    if type(j) == float:
                        if j.is_integer()==False:
                            error_("Error: an index is a float: "+ str(identifier)+\
                                'at line '+str(identifier.get_line())+"for t = "+str(k))
                        j = int(round(j))

                    if j >= T or j<0:
                        flag_out_of_bounds = True
                        break
                    
                _,term,flag_out_of_bounds = variable_factor_in_expression(expr,matrixVar[j][n],definitions)

                values[l] = term
                rows[l] = n
                columns[l] = j

                if flag_out_of_bounds:
                    break
                l += 1
            
            if flag_out_of_bounds == False:
                matrix = [values,rows,columns]
                node.add_objective_matrix([matrix,obj_type])


def variable_in_constraint(constr,variable,constants):
    """
    variable_in_constraint function : computes the constant term
    multiplying a variable in a constraint
    INPUT:  constr, constraint considered
            variable, identifier object containing a variable
            constants, dictionary with all the parameters and constants
    OUTPUT: value, value that multiplies the variable in the expression
            flag_out_of_bound, predicate if the variable is out of bounds
    """
    rhs = constr.get_rhs()
    lhs = constr.get_lhs()
    flag_out_of_bounds = False

    _,value1,flag_out_of_bounds1 = variable_factor_in_expression(rhs,variable,constants)
    _,value2,flag_out_of_bounds2 = variable_factor_in_expression(lhs,variable,constants)
    value = value1 - value2
    if flag_out_of_bounds1 or flag_out_of_bounds2:
        flag_out_of_bounds = True
    return value,flag_out_of_bounds

def variable_factor_in_expression(expression,variable,definitions):
    """
    variable_factor_in_expression function : computes the constant term
    multiplying a variable in an expression
    INPUT:  expression, expression considered
            variable, identifier object containing a variable
            definitions, dictionary with all the parameters and constants
    OUTPUT: found, is variable in expression predicate
            value, value that multiplies the variable in the expression
            flag_out_of_bounds, if the valuation of the variable out of bounds 
    """
    e_type = expression.get_type()
    found = False
    value = 0
    flag_out_of_bounds = False

    if e_type == 'literal':
        identifier = expression.get_name()
        if type(expression.get_name())!=float and type(expression.get_name())!=int:
            if identifier.name_compare(variable):
                type_id = identifier.get_type()
                if type_id == 'assign':
                    t_expr = identifier.get_expression()
                    t_value = t_expr.evaluate_expression(definitions)

                    if not('T' in definitions):
                        error_("INTERNAL ERROR: T not found")
                    
                    values_T = definitions['T']
                    T = values_T[0]

                    if t_value < 0 or t_value >= T:
                        flag_out_of_bounds = True

                    value1 = variable.get_expression().evaluate_expression(definitions)
                    if value1 == t_value:
                        found = True
                        value = 1
                else:
                    value1 = variable.get_expression().evaluate_expression(definitions)
                    
                    if not('t' in definitions):
                        error_("INTERNAL ERROR: t not found")

                    values_t = definitions['t']
                    t = values_t[0]
                    
                    if t == value1:
                        found = True
                        value = 1
    else:
        children = expression.get_children()
        if e_type == 'u-':
            found,value,flag_out_of_bounds = variable_factor_in_expression(children[0],variable,definitions)
            if flag_out_of_bounds:
                return found,value,flag_out_of_bounds
            value = - value
        else:
            found1,value1,flag_out_of_bounds = variable_factor_in_expression(children[0],variable,definitions)
            if flag_out_of_bounds:
                return found,value,flag_out_of_bounds
            found2,value2,flag_out_of_bounds = variable_factor_in_expression(children[1],variable,definitions)
            if flag_out_of_bounds:
                return found,value,flag_out_of_bounds

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
            elif e_type == '*' and (found1 or found2):
                if found1:
                    child = children[1]
                    value = value1
                else:
                    child = children[0]
                    value = value2
                found = True
                constant = child.evaluate_expression(definitions) #MUST BE ALL CONSTANTS AS DEFINITIONS
                value = value*constant
            elif e_type == '/':
                if found1:
                    constant = children[1].evaluate_expression(definitions)
                    value = value1/constant
                    found = True
                    
    return found,value,flag_out_of_bounds

def is_time_dependant_constraint(constraint,variables_dictionary,parameter_dictionary):
    """
    is_time_dependant_constraint predicate : checks if constraint is time dependant
    A constraint is time dependant if its right hand side or left depend on "t"
    INPUT:  constraint, constraint to check
            variables_dictionary, dictionary with all the variables
            parameter_dictionary, dictionary with all the parameters and constants
    OUTPUT: predicate, the boolean corresponding to the predicate
    """
    rhs = constraint.get_rhs()
    time_dep = is_time_dependant_expression(rhs,variables_dictionary,parameter_dictionary)
    lhs = constraint.get_lhs()
    if time_dep == False:
        time_dep = is_time_dependant_expression(lhs,variables_dictionary,parameter_dictionary)
    return time_dep

def is_time_dependant_expression(expression,variables_dictionary,parameter_dictionary):
    """
    is_time_dependant_expression predicate : checks if expression is time dependant
    An expression is time dependant if it depends on "t"
    INPUT:  expression, expression to check
            variables_dictionary, dictionary with all the variables
            parameter_dictionary, dictionary with all the parameters and constants
    OUTPUT: predicate, the boolean corresponding to the predicate
    """
    e_type = expression.get_type()
    nb_child = expression.get_nb_children()
    children = expression.get_children()
    predicate = False

    if e_type == 'literal':
        identifier = expression.get_name()
        if type(expression.get_name())!=float and type(expression.get_name())!=int:
            id_type = identifier.get_type()
            id_name = identifier.get_name()
            
            if id_name == "t":
                predicate = True
            elif id_name == "T":
                predicate = False
            else:
                if id_name in variables_dictionary:
                    if id_type =="assign":
                        predicate = is_time_dependant_expression(identifier.get_expression(),\
                            variables_dictionary,parameter_dictionary)
                    else: 
                        predicate = True
                elif id_name in parameter_dictionary:
                    if id_type =="assign":
                        predicate = is_time_dependant_expression(identifier.get_expression(),\
                            variables_dictionary,parameter_dictionary)
                    else:
                        vector = parameter_dictionary[id_name]
                        if len(vector)>1:
                            predicate = True
    else:
        for i in range(nb_child):
            predicate_i = is_time_dependant_expression(children[i],variables_dictionary,parameter_dictionary)
            if predicate_i:
                predicate = predicate_i
                break

    return predicate
