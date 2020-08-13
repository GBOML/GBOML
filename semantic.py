from classes import *

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
#   WARNING IF NOT USED

def semantic(program):
    # WRAPPER that checks all the possible errors that could happen
    global timevar
    print("timevar "+str(timevar))
    time = program.get_time()
    if time!=None:
        timevar = ["t","T","step"] 
    print("timevar "+str(timevar))
    root = program.get_nodes()
    #CHECK If all nodes have different names
    check_names(root)

    #CHECK If an objective function is defined
    find_objective(root)

    n = root.get_size()
    elements = root.get_elements()
    for i in range(n):
        #CHECK if all parameters of a node have different names
        all_parameters = check_names(elements[i].get_parameters())
        #CHECK if all variables of a node have different names
        all_variables = check_names(elements[i].get_variables())
        #CHECK if dont share the same name
        match_names(all_parameters,all_variables)
        #TRY to evaluate the parameters
        vector_parameters = parameter_evaluation(elements[i].get_parameters())

        check_expressions_dependancy(elements[i],all_variables,all_parameters)

    check_input_output(root)

def check_input_output(root):
    n = root.get_size()
    elements = root.get_elements()
    input_var = []
    output_var = []

    for i in range(n):
        variables_vector = elements[i].get_variables()
        nb_var = variables_vector.get_size()
        variables = variables_vector.get_elements()

        constraints_vector = elements[i].get_constraints()
        nb_cons = constraints_vector.get_size()
        constraints = constraints_vector.get_elements()
        for j in range(nb_var):
            v_type = variables[j].get_type()
            name = variables[j].get_name()
            if v_type == "input": 
                input_var.append(name)
            elif v_type == "output": 
                for k in range(len(output_var)):
                    if name == output_var[k]:
                        error_("Two Nodes output the same variable named : "+str(name)+" rediffined at "+str(elements[i].get_line())+" node "+str(elements[i].get_name()))
                output_var.append(name)

            found = False
            for k in range(nb_cons):
                if name == constraints[i].get_name():
                    found = True

            if found == False:
                if v_type == 'output':
                    error_("Output '"+str(name)+"' does not have a formula associated however defined at line "+str(variables[j].get_line()))

    for i in range(len(input_var)):
        in_var = input_var[i]
        found = False
        for j in range(len(output_var)):
            out_var = output_var[i]
            if in_var == out_var:
                found = True
        if found == False: 
            error_("Input Variable "+str(in_var)+" is not outputted from any node")


def check_expressions_dependancy(node,variables,parameters):
    constraints = node.get_constraints()
    nb_cons = constraints.get_size()
    cons = constraints.get_elements()
    for i in range(nb_cons):
        expr = cons[i].get_expression()
        name = cons[i].get_name()
        found = False
        for j in range(len(variables)):
            if name == variables[i]:
                found = True
                break
        if found == False: 
            error_('Unknown variable "'+str(name)+'" at line '+str(cons[i].get_line()))
        c_type = cons[i].get_type()
        if c_type == "=":
            contains_var = variables_in_expression(expr,variables,parameters)
            if contains_var ==False:
                error_('Variable "'+str(name)+'" at line '+str(cons[i].get_line()) +' only depends on constants should be a parameter not a variable')

    objectives = node.get_objectives()
    nb_obj = objectives.get_size()
    obj = objectives.get_elements()
    for i in range(nb_obj):
        expr = obj[i].get_expression()
        contains_var = variables_in_expression(expr,variables,parameters)
        if contains_var == False:
            error_('Objective only depends on constants not on variable at line '+str(expr.get_line()))

def variables_in_expression(expression,variables,parameters):
    e_type = expression.get_type()
    nb_child = expression.get_nb_children()
    children = expression.get_children()
    is_variable = False
    print(expression)

    if e_type == 'literal':
        if type(expression.get_name())==str:
            for i in range(len(variables)):
                if expression.get_name() == variables[i]:
                    is_variable = True
                    break

            if is_variable == False:
                defined = False
                for i in range(len(parameters)):
                    if expression.get_name() == parameters[i]:
                        defined = True
                        break

                for i in range(len(timevar)):
                    if expression.get_name() == timevar[i]:
                        defined = True
                        break

                print("HERERRE")
                print(expression.get_name())

                if defined == False:
                    print("Undefined name "+str(expression.get_name())+" at line "+str(expression.get_line()))
                    exit(-1)
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

        elif e_type == "*" or e_type == "**" or e_type == "/":
            if term1 == True and term2 == True:
                string = "Operation '"+str(e_type)+"' between two expressions containing variables leading to a non linearity at line "+str(children[0].get_line())+"\n"
                string +="Namely Expression 1 : " + str(children[0])+ "and Expression 2 : "+str(children[1])
                error_(string)

            if term1 == True:
                lin1 = check_linear(children[0],variables,parameters)
                if lin1 == False:
                    error_("Non linearity in expression : "+str(children[0])+" only linear problems are accepted at line "+str(children[0].get_line()))

            if term2 == True:
                lin2 = check_linear(children[1],variables,parameters)
                if lin2 == False: 
                    error_("Non linearity in expression : "+str(children[1])+" only linear problems are accepted  at line "+str(children[0].get_line()))
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
            if name1 == name2:
                error_("A variable and a parameter share the same name '"+str(name1)+"'")

def check_names(root):
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
        all_names.append(name)
    return all_names

def parameter_evaluation(n_parameters):
    n = n_parameters.get_size()
    parameters = n_parameters.get_elements()
    all_values = Vector()
    print("\n\nEvaluations : ")
    for i in range(n):
        e = parameters[i].get_expression()
        name = parameters[i].get_name()
        value = evaluate_expression(e,all_values)
        name_value_tuple = [name,value]
        print(name_value_tuple[0])
        print(name_value_tuple[1])

        all_values.add_element(name_value_tuple)
    print(all_values)

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
            n = definitions.get_size()
            found = False
            defined = definitions.get_elements()
            for i in range(n):
                if defined[i][0]==identifier: 
                    value = defined[i][1]
                    print('value : '+str(value))
                    found = True
            if found == False:
                print(timevar)
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
        else:
            error_("INTERNAL ERROR : unexpected e_type "+str(e_type)+" check internal parser")

    return value
"""
def check_in_brackets(expression,variables,parameters)
    e_type = expression.get_type()
    nb_child = expression.get_nb_children()
    children = expression.get_children()
    if e_type == 'literal':
        if nb_child !=0:
            error_("INTERNAL ERROR : literal expression must have zero child, got "+str(nb_child)+" check internal parser")
    elif e_type == 'u-':
"""     

def error_(message):
    print(message)
    exit(-1)