
# semantic.py
#
# Writer : MIFTARI B
# ------------

from classes import Time, Expression,Variable,Parameter,Link,Attribute,Program,Objective,Node,Identifier,Constraint
import copy
import numpy as np
from utils import Vector
import time as t


timevar = []
# To check 
#   if linear                                                   DONE
#   if defined in expression                                    DONE
#   if output match Input                                       DONE
#   if valuable                                                 DONE
#   if at least one objective exists                            DONE
#   if constraints and objective are not meant for parameters   DONE
#   if unity right
#   if output don't have same name as another output            DONE
#   if input - output - internal not defined twice              DONE
#   if rediffined 
#   if a variable has the same name as a parameter              DONE
#   A LHS term shall not be in the RHS
#   OUTPUT MUST HAVE A formula                                  DONE
#   Check that a certain variable is defined in a link
#   if all the elements are zero in matrix constraint 

def semantic(program):
    # WRAPPER that checks all the possible errors that could happen
    global timevar

    #retrieve timevariables if defined
    time = program.get_time()

    if time!=None:
        timevar = ["t","T","step"] 
    
    root = program.get_nodes()
    
    #CHECK If all nodes have different names
    check_names(root)

    #CHECK If an objective function is defined
    find_objective(root)

    n = root.get_size()
    elements = root.get_elements()

    #Inside each node 
    for i in range(n):
        #CHECK if all parameters of a node have different names
        
        all_parameters = check_names(elements[i].get_parameters())
        #print("parameters: "+str(all_parameters))
        #CHECK if all variables of a node have different names
        all_variables = check_names(elements[i].get_variables())
        #print(all_variables)
        
        #CHECK if dont share the same name
        match_names(all_parameters,all_variables)

        #TRY to evaluate the parameters
        vector_parameters = parameter_evaluation(elements[i].get_parameters())

        check_expressions_dependancy(elements[i],all_variables,all_parameters)
        #check_definition_order(elements[i].get_constraints())
        check_var(elements[i],all_variables,vector_parameters,all_parameters,time)

        convert_objectives_matrix(elements[i],all_variables,vector_parameters,time)

    vector_parameters = vector_parameters.get_elements()
    #for i in range(len(vector_parameters)):
    #    print("name: "+str(vector_parameters[i][0])+" value : "+str(vector_parameters[i][1]))
    #print(vector_parameters)
    #check_input_output(root)
    all_input_output_pairs = check_link(program)

    all_input_output_pairs = regroup_by_name(all_input_output_pairs)

    input_output_matrix = convert_links_to_matrix(all_input_output_pairs)

    #print(input_output_matrix)

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

    #print(triplet)
    return triplet

def check_link(program):
    links_vector = program.get_links()
    link_size = links_vector.get_size()
    links = links_vector.get_elements()

    nodes_vector = program.get_nodes()
    node_size = nodes_vector.get_size()
    nodes = nodes_vector.get_elements()

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

        rhs_vector = link_i.vector
        rhs_size = rhs_vector.get_size()
        rhs = rhs_vector.get_elements()

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
            variables_vector = nodes[position].get_variables()
            variable_size = variables_vector.get_size()
            variables = variables_vector.get_elements()
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

                variables_vector = nodes[position].get_variables()
                variable_size = variables_vector.get_size()
                variables = variables_vector.get_elements()
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

    n,m = np.shape(variables_input)
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
    variables_vector = node.get_variables()
    variable_size = variables_vector.get_size()
    variables = variables_vector.get_elements()
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
    nb_cons = constraints.get_size()
    cons = constraints.get_elements()

    for i in range(nb_cons):
        rhs = cons[i].get_rhs()
        lhs = cons[i].get_lhs()

        var_in_right = variables_in_expression(rhs,variables,parameters)
        var_in_left = variables_in_expression(lhs,variables,parameters)

        if var_in_right == False and var_in_left == False:
            error_('No variable in constraint at line '+str(cons[i].get_line()))

        check_linear(rhs,variables,parameters)
        check_linear(lhs,variables,parameters)
        
    objectives = node.get_objectives()
    nb_obj = objectives.get_size()
    obj = objectives.get_elements()

    for i in range(nb_obj):
        expr = obj[i].get_expression()
        contains_var = variables_in_expression(expr,variables,parameters)
        if contains_var == False:
            error_('Objective only depends on constants not on variable at line '+str(expr.get_line()))
        check_linear(expr,variables,parameters)
    

def variables_in_expression(expression,variables,parameters):
    e_type = expression.get_type()
    nb_child = expression.get_nb_children()
    children = expression.get_children()
    is_variable = False

    if e_type == 'literal':
        identifier = expression.get_name()

        if type(identifier)!=int and type(identifier)!=float:
            for i in range(len(variables)):
                if identifier.name_compare(variables[i]):
                    is_variable = True
                    break

            if is_variable == False:
                defined = False
                for i in range(len(parameters)):
                    if identifier.name_compare(parameters[i]):
                        defined = True
                        break

                for i in range(len(timevar)):
                    if identifier.name_compare(timevar[i]):
                        defined = True
                        break


                if defined == False:
                    error_("Undefined name "+str(expression.get_name())+" at line "+str(expression.get_line()))

            check_in_brackets(identifier,variables,parameters)
    else:
        value = False
        for i in range(nb_child):
            value = variables_in_expression(children[i],variables,parameters)
            if value == True: 
                is_variable = value
            
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
            if term2 == True & term1 == True:
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


def find_objective(root):
    n = root.get_size()
    elements = root.get_elements()
    found = False
    for i in range(n):
        objectives = elements[i].get_objectives()
        nb_objectives = objectives.get_size()
        if nb_objectives != 0:
            found = True
            break

    if found == False:
        error_("No objective function was defined")


def match_names(list1,list2):
    for i in range(len(list1)):
        name1 = list1[i]
        for j in range(len(list2)):
            name2 = list2[j]
            if name2.name_compare(name1):
                error_("A variable and a parameter share the same name '"+str(name1)+"'")

def check_names(root,add_type = False):
    n = root.get_size()
    elements = root.get_elements()
    all_names = []
    for i in range(n):
        name = elements[i].get_name()

        for k in range(i+1,n):
            if name == elements[k].get_name():
                error_('Redefinition error: "'+str(name)+'" at line '+str(elements[k].get_line()))

        for k in range(len(timevar)):
            if name == timevar[k]:
                error_('Name "'+str(name)+'" is reserved for timescale, used at line '+str(elements[i].get_line()))
        if add_type == True:
            all_names.append(name,elements[i].get_type())
        else:
            all_names.append(name)
    return all_names

def parameter_evaluation(n_parameters):
    n = n_parameters.get_size()
    parameters = n_parameters.get_elements()
    all_values = Vector()
    
    for i in range(n):
        e = parameters[i].get_expression()
        if e != None:
            name = parameters[i].get_name()
            value = evaluate_expression(e,all_values)
            name_value_tuple = [name,value]
            all_values.add_element(name_value_tuple)
        else:
            all_values = evaluate_table(parameters[i],all_values)

    return all_values

def evaluate_table(parameters,definitions):
    name = parameters.get_name()
    values = parameters.get_vector()
    tuple_value_name = []
    for i in range(len(values)):
        value_i = values[i].get_name()
        if type(value_i) != float and type(value_i) !=int:
            type_val = value_i.get_type()
            defined = definitions.get_elements()
            length_def = definitions.get_size()
            found = False
            for j in range(length_def):
                if type_val == "basic":
                    if value_i.get_name() == defined[j][0]:
                        value_i = defined[j][1]
                        found = True
                        break
                elif type_val == "assign":
                    if value_i.name_compare(defined[j][0]) and evaluate_expression(value_i.get_expression(),definitions)==evaluate_expression(defined[j][0].get_expression(),definitions):
                        found = True
                        value_i = defined[j][1]
                        break
            if found == False:
                error_('Undefined parameter : '+str(value_i))
        expr = Expression('literal',i)
        identifier = Identifier('assign',name,expression=expr)
        tuple_value_name = [identifier,value_i]
        definitions.add_element(tuple_value_name)
    return definitions



def evaluate_expression(expression,definitions):

    e_type = expression.get_type()
    nb_child = expression.get_nb_children()

    if e_type == 'u-':
        if nb_child != 1:
            error_("INTERNAL ERROR : unary minus must have one child, got "+str(nb_child)+" check internal parser")

        children = expression.get_children()
        term1 = evaluate_expression(children[0],definitions)
        value = -term1

    elif e_type == 'literal':
        if nb_child != 0:
            error_("INTERNAL ERROR : literal must have zero child, got "+str(nb_child)+" check internal parser")

        identifier = expression.get_name()

        if type(expression.get_name())==float or type(expression.get_name())==int:
            value = identifier
        else:
            id_type = identifier.get_type()

            n = definitions.get_size()
            found = False
            defined = definitions.get_elements()
            for i in range(n):
                if (identifier.name_compare(defined[i][0]) and
                    ((id_type == "basic") or
                    ((id_type =="assign") and 
                    (evaluate_expression(identifier.get_expression(),definitions)==evaluate_expression(defined[i][0].get_expression(),definitions))))):
                    value = defined[i][1]
                    found = True
            if found == False:
                
                for i in range(len(timevar)):
                    if identifier == timevar[i]:
                        error_('A Parameter can not depend on time variable :"'+str(timevar[i])+'" at line '+str(expression.get_line()))
                error_('Identifier "'+ str(identifier)+ '" used but not previously defined, at line '+str(expression.get_line()))
    else:
        if nb_child != 2:
            error_("INTERNAL ERROR : binary operators must have two children, got "+str(nb_child)+" check internal parser")

        children = expression.get_children()
        term1 = evaluate_expression(children[0],definitions)
        term2 = evaluate_expression(children[1],definitions)
        if e_type == '+':
            value = term1 + term2
        elif e_type =='*':
            value = term1 * term2
        elif e_type == '/':
            value = term1/term2
        elif e_type == '-':
            value = term1-term2
        elif e_type == '**':
            value = term1**term2
        elif e_type == "mod":
            value = term1%term2
        else:
            error_("INTERNAL ERROR : unexpected e_type "+str(e_type)+" check internal parser")

    return value

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

        if type(expression.get_name())==float or type(expression.get_name())==int:
            value = identifier
        else:
            id_type = identifier.get_type()
            if id_type != 'basic':
                error_('Parameter shall not have this type of structure '+str(identifier))
            identifier = identifier.get_name()

            for i in range(len(parameters)):
                if identifier == parameters[i]:
                    found = True
                    break

            for i in range(len(timevar)):
                if identifier == timevar[i]:
                    is_time_var = True
                    found = True
                    break
            
            for i in range(len(variables)):
                if variables[i].name_compare(identifier):
                    error_('Variable in brackets for assignement ')
            if found == False:
                error_('Identifier "'+ str(identifier)+ '" used but not previously defined, at line '+str(expression.get_line()))

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
        elif e_type =='*' or e_type == '/':
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

def check_var(node,variables,parameters,param_name,time):
    constraints = node.get_constraints()
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
        T = 1

    all_variables = []
    for k in range(T):
        variables_for_time = []
        for i in range(len(variables)):
            var = copy.copy(variables[i])
            expr = Expression('literal',k)
            var.set_expression(expr)

            variables_for_time.append(var)
        all_variables.append(variables_for_time)

    X = np.array(all_variables)
    node.set_variable_matrix(X)

    n,_ = np.shape(X)
    start_time = t.time()
    flag_t_factor = True
    for i in range(nb_cons):
        constr = cons[i]
        constr_leafs = constr.get_leafs()

        variables_used = []

        for leaf in constr_leafs:
            identifier = leaf.get_name()
            if type(identifier)!=int and type(identifier)!=float:
                i = 0
                if identifier.name_compare("t"):
                    flag_t_factor = True

                for variable in variables: 
                    if identifier.name_compare(variable):
                        variables_used.append([i,identifier])
                        break
                    i +=1
    
        nb_variables = len(variables_used)
        
        #print('CONSTRAINT '+str(i+1) + ': '+str(constr))

        if(is_time_dependant_constraint(constr,variables)):
            t_horizon = T
        else:
            t_horizon = 1

        #print("time : "+str(is_time_dependant_constraint(constr,variables)))

        values_computed = False
        for k in range(t_horizon):
            
            tuple_time = ['t',k] 
            parameters.add_element(tuple_time)

            if flag_t_factor == True or values_computed == False:
                new_values = np.zeros(nb_variables)
            else:
                new_values = old_values
            
            rows = np.zeros(nb_variables)
            columns = np.zeros(nb_variables)
            
            l = 0
            for n,identifier in variables_used:
                
                id_type = identifier.get_type()
                
                if id_type == "basic":
                    j = k
                else : 
                    j = evaluate_expression(identifier.get_expression(),parameters)
                    if j >= T:
                        flag_out_of_bounds = True
                        break
                if flag_t_factor == True or values_computed == False:
                    term,flag_out_of_bounds = variable_in_constraint(constr,X[j][n],parameters)
                    new_values[l]=term
                else:
                    new_values = old_values

                rows[l]=n
                columns[l]=j
            
                if flag_out_of_bounds:
                    break
                l+=1
            
            if flag_out_of_bounds==False: 
                if flag_t_factor == True or values_computed == False:
                    constant = constant_in_constraint(constr,variables,parameters,param_name)
                values_computed = True
                
                #print("constant "+str(constant))
                sign = constr.get_sign()
                matrix = [new_values,rows,columns]
                #print(node.get_name())
                #print(matrix)
                node.add_constraints_matrix([matrix,constant,sign])
            
            old_values = new_values
            
            parameters.delete_last()
    #print(matrix)
    print("Check_var --- %s seconds ---" % (t.time() - start_time))


    
def constant_in_constraint(constr,variables,constants,param_name):
    rhs = constr.get_rhs()
    lhs = constr.get_lhs()

    value1 = constant_factor_in_expression(rhs,variables,constants,param_name)
    
    value2 = constant_factor_in_expression(lhs,variables,constants,param_name)
    
    value = value2 - value1
    return value

def constant_factor_in_expression(expression,variables,constants,param_name):
    e_type = expression.get_type()
    nb_child = expression.get_nb_children()
    children = expression.get_children()
    value = 0

    if variables_in_expression(expression,variables,param_name)==False:
        value = evaluate_expression(expression,constants)
    else:
        if e_type == 'u-':
            is_var = variables_in_expression(children[0],variables,param_name)
            if is_var==False:
                value = evaluate_expression(children[0],constants)
            else: 
                value = constant_factor_in_expression(children[0],variables,constants,param_name)
        elif e_type == "/":
            is_var1 = variables_in_expression(children[0],variables,param_name)
            is_var2 = variables_in_expression(children[1],variables,param_name)

            if is_var1 == False and is_var2 == False:
                value = evaluate_expression(children[0],constants)/evaluate_expression(children[1],constants)
            elif is_var1 == True:
                value = constant_factor_in_expression(children[0],variables,constants,param_name)/evaluate_expression(children[1],constants)
        elif e_type == "*":
            is_var1 = variables_in_expression(children[0],variables,param_name)
            is_var2 = variables_in_expression(children[1],variables,param_name)
            if is_var1 == False and is_var2 == False:
                value = evaluate_expression(children[0],constants)*evaluate_expression(children[1],constants)
            else:
                if is_var1:
                    value1 = constant_factor_in_expression(children[0],variables,constants,param_name)
                else:
                    value1 = evaluate_expression(children[0],constants)
                if is_var2:
                    value2 = constant_factor_in_expression(children[1],variables,constants,param_name)
                else:
                    value2 = evaluate_expression(children[1],constants)

                value = value1*value2
        elif e_type == '+':
            is_var1 = variables_in_expression(children[0],variables,param_name)
            is_var2 = variables_in_expression(children[1],variables,param_name)
            if is_var1 == False and is_var2 == False:
                value = evaluate_expression(children[0],constants)+evaluate_expression(children[1],constants)
            else:
                if is_var1:
                    value1 = constant_factor_in_expression(children[0],variables,constants,param_name)
                else:
                    value1 = evaluate_expression(children[0],constants)
                if is_var2:
                    value2 = constant_factor_in_expression(children[1],variables,constants,param_name)
                else:
                    value2 = evaluate_expression(children[1],constants)

                value = value1+value2
        elif e_type == '-':
            is_var1 = variables_in_expression(children[0],variables,param_name)
            is_var2 = variables_in_expression(children[1],variables,param_name)
            if is_var1 == False and is_var2 == False:
                value = evaluate_expression(children[0],constants)-evaluate_expression(children[1],constants)
            else:
                if is_var1:
                    value1 = constant_factor_in_expression(children[0],variables,constants,param_name)
                else:
                    value1 = evaluate_expression(children[0],constants)
                if is_var2:
                    value2 = constant_factor_in_expression(children[1],variables,constants,param_name)
                else:
                    value2 = evaluate_expression(children[1],constants)

                value = value1-value2
        elif e_type == '**':
            is_var1 = variables_in_expression(children[0],variables,param_name)
            is_var2 = variables_in_expression(children[1],variables,param_name)
            if is_var1 == False and is_var2 == False:
                value = evaluate_expression(children[0],constants)**evaluate_expression(children[1],constants)
            else:
                if is_var1:
                    value1 = constant_factor_in_expression(children[0],variables,constants,param_name)
                else:
                    value1 = evaluate_expression(children[0],constants)
                value2 = evaluate_expression(children[1],constants)

                value = value1**value2
    return value

def convert_objectives_matrix(node,variables,parameters,time):
    matrixVar = node.get_variable_matrix()
    n,_ = np.shape(matrixVar)

    objectives_vector = node.get_objectives()
    objectives = objectives_vector.get_elements()
    obj_size = objectives_vector.get_size()

    if time!=None:
        T = time.time        
    else:
        T = 1

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

        if(is_time_dependant_expression(expr,variables)):
            t_horizon = T
        else:
            t_horizon = 1

        for k in range(t_horizon):
        
            tuple_time = ['t',k] 
            parameters.add_element(tuple_time)

            values = np.zeros(nb_variables)
            rows = np.zeros(nb_variables)
            columns = np.zeros(nb_variables)

            l = 0
            for n,identifier in variables_used:
                id_type = identifier.get_type()

                if id_type == "basic":
                    j = k
                else : 
                    j = evaluate_expression(identifier.get_expression(),parameters)
                    if j >= T:
                        flag_out_of_bounds = True
                        break
                _,term,flag_out_of_bounds = variable_factor_in_expression(expr,matrixVar[j][n],parameters)

                values[l] = term
                rows[l] = n
                columns[l] = j

                if flag_out_of_bounds:
                    break
                l += 1
            
            if flag_out_of_bounds == False:
                matrix = [values,rows,columns]
                node.add_objective_matrix([matrix,obj_type])

            parameters.delete_last()


def variable_in_constraint(constr,variable,constants):
    rhs = constr.get_rhs()
    lhs = constr.get_lhs()
    flag_out_of_bounds = False

    _,value1,flag_out_of_bounds1 = variable_factor_in_expression(rhs,variable,constants)
    _,value2,flag_out_of_bounds2 = variable_factor_in_expression(lhs,variable,constants)
    value = value1 - value2
    if flag_out_of_bounds1 or flag_out_of_bounds2:
        flag_out_of_bounds = True
    return value,flag_out_of_bounds

def variable_factor_in_expression(expression,variable,constants):
    e_type = expression.get_type()
    nb_child = expression.get_nb_children()
    found = False
    value = 0
    flag_out_of_bounds = False

    var_id = variable.get_type()

    if e_type == 'literal':
        identifier = expression.get_name()
        if type(expression.get_name())!=float and type(expression.get_name())!=int:
            if identifier.name_compare(variable):
                type_id = identifier.get_type()
                if type_id == 'assign':
                    t_expr = identifier.get_expression()
                    t_value = evaluate_expression(t_expr,constants)

                    const = constants.get_elements()
                    for i in range(constants.get_size()):
                        if const[constants.get_size()-i-1][0]=='T':
                            T = const[constants.get_size()-i-1][1]

                    if t_value<0 or t_value >=T:
                        flag_out_of_bounds = True
                    value1 = evaluate_expression(variable.get_expression(),constants)
                    if value1 == t_value:
                        found = True
                        value = 1
                else:
                    value1 = evaluate_expression(variable.get_expression(),constants)
                    const = constants.get_elements()
                    for i in range(constants.get_size()):
                        if const[i][0]=='t':
                            t = const[i][1]
                    if t == value1:
                        found = True
                        value = 1
    else:
        children = expression.get_children()
        if e_type == 'u-':
            found,value,flag_out_of_bounds = variable_factor_in_expression(children[0],variable,constants)
            if flag_out_of_bounds:
                return found,value,flag_out_of_bounds
            value = - value
        else:
            found1,value1,flag_out_of_bounds = variable_factor_in_expression(children[0],variable,constants)
            if flag_out_of_bounds:
                return found,value,flag_out_of_bounds
            found2,value2,flag_out_of_bounds = variable_factor_in_expression(children[1],variable,constants)
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
                constant = evaluate_expression(child,constants) #MUST BE ALL CONSTANTS AS DEFINITIONS
                value = value*constant
            elif e_type == '/':
                if found1:
                    constant = evaluate_expression(children[1],constants)
                    value = value1/constant
                    found = True
                    
    return found,value,flag_out_of_bounds

def is_time_dependant_constraint(constraint,variables):
    rhs = constraint.get_rhs()
    time_dep = is_time_dependant_expression(rhs,variables)
    lhs = constraint.get_lhs()
    if time_dep == False:
        time_dep = is_time_dependant_expression(lhs,variables)
    return time_dep

def is_time_dependant_expression(expression,variables):
    e_type = expression.get_type()
    nb_child = expression.get_nb_children()
    children = expression.get_children()
    found = False

    if e_type == 'literal':
        identifier = expression.get_name()
        if type(expression.get_name())!=float and type(expression.get_name())!=int:
            id_type = identifier.get_type()
            if identifier.name_compare("t"):
                if id_type != "basic":
                    error_("Identifier t is used with [expression] at line "+identifier.get_line())
                found = True
            else:
                if id_type == 'assign':
                    found = is_time_dependant_expression(identifier.get_expression(),variables)
                else:
                    for variable in variables:
                        if variable.name_compare(expression.get_name()):
                            found = True
    else:
        for i in range(nb_child):
            found1 = is_time_dependant_expression(children[i],variables)
            if found1:
                found = found1

    return found

#def check_definition_order(constraints,variables):
#    nb_cons = constraints.get_size()
#    cons = constraints.get_elements()
#    for i in range(nb_cons):
#        variable_list = get_variables_constraint(cons[i],variables,[])

def get_variables_constraint(constraint,variables):
    rhs = constraint.get_rhs()
    lhs = constraint.get_lhs()

    rhs_list = get_variables_expression(rhs,variables)
    lhs_list = get_variables_expression(lhs,variables)

    full_list = rhs_list + lhs_list

def get_variables_expression(expression,variables):
    e_type = expression.get_type()
    nb_child = expression.get_nb_children()
    children = expression.get_children()
    variable_list = []

    if e_type == "literal":
        identifier = expression.get_name()
        if type(identifier) != int and type(identifier) != float:
            for i in range(len(variables)):
                if identifier.name_compare(variables[i]):
                    variable_list.append(identifier)
                    break
    else: 
        for i in range(nb_child):
            curr_var = get_variables_expression(children[i],variables)
            variable_list = curr_var + variable_list  
    return variable_list

def error_(message):
    print(message)
    exit(-1)

# def check_input_output(root):
#     n = root.get_size()
#     elements = root.get_elements()
#     input_var = []
#     output_var = []

#     for i in range(n):
#         variables_vector = elements[i].get_variables()
#         nb_var = variables_vector.get_size()
#         variables = variables_vector.get_elements()

#         constraints_vector = elements[i].get_constraints()
#         nb_cons = constraints_vector.get_size()
#         constraints = constraints_vector.get_elements()
#         for j in range(nb_var):
#             v_type = variables[j].get_type()
#             name = variables[j].get_name()
#             if v_type == "input": 
#                 input_var.append(name)
#             elif v_type == "output": 
#                 for k in range(len(output_var)):
#                     if name == output_var[k]:
#                         error_("Two Nodes output the same variable named : "+str(name)+" rediffined at "+str(elements[i].get_line())+" node "+str(elements[i].get_name()))
#                 output_var.append(name)

#             found = False
#             for k in range(nb_cons):
#                 if name == constraints[i].get_name():
#                     found = True

#             if found == False:
#                 if v_type == 'output':
#                     error_("Output '"+str(name)+"' does not have a formula associated however defined at line "+str(variables[j].get_line()))

#     for i in range(len(input_var)):
#         in_var = input_var[i]
#         found = False
#         for j in range(len(output_var)):
#             out_var = output_var[i]
#             if in_var == out_var:
#                 found = True
#         if found == False: 
#             error_("Input Variable "+str(in_var)+" is not outputted from any node")