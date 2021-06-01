
# gboml_semantic.py
#
# Part of the GBOML Project
# University of Liege
# Writer : MIFTARI B
# ------------


from .classes import Expression, Attribute, Program, Node, Identifier, Factorize

import numpy as np  # type: ignore
from .utils import error_
import time as t 


def semantic(program: Program) -> Program:
    """
    Semantic check function : Augments the inputed Program object and checks several errors     
    INPUT:  initialized Program object
    OUTPUT: augmented Program object ready to be transformed to matrix
    """

    # Retrieve time horizon and check its validity
    time = program.get_time()
    time.check()
    time_value = time.get_value()
    
    # Check if all nodes have different names
    node_list = program.get_nodes()
    check_names_repetitions(node_list)

    # Check if an objective function is defined
    program.check_objective_existence()

    definitions = dict()
    definitions["T"] = [time_value]

    # GLOBAL Parameters checking
    global_param = program.get_global_parameters()
    global_dict_object = program.get_dict_global_parameters()

    global_dict = parameter_evaluation(global_param, definitions.copy())
    global_dict.pop("T")

    # Either global or GLOBAL as usage keyword
    definitions["global"] = global_dict

    # Variables of the whole program
    program_variables = {}
    external_variables = {}

    global_index = 0

    # Each node checking - factorization and expansion
    for node in node_list:

        name = node.get_name()
        start_time = t.time()

        # Copy dictionary of global parameters

        parameter_dictionary = definitions.copy()

        # Retrieve node parameter dictionary
        node_parameters = node.get_dictionary_parameters() 

        # Retrieve a dictionary of [name,identifier object] tuple of variables

        node_variables = node.get_dictionary_variables()
        program_variables[name] = node_variables
        external_variables[name] = node.get_dictionary_variables("external")

        # Check if variables and parameters share names

        match_dictionaries(node_parameters, node_variables)

        # Add evaluated parameters to the dictionary of defined parameters

        parameter_dictionary = parameter_evaluation(node.get_parameters(), parameter_dictionary)

        # Set size of different parameters

        global_index = set_size_variables(node_variables, parameter_dictionary, global_index)

        # Store parameter dictionary
        node.set_parameter_dict(parameter_dictionary)

        node_parameters["global"] = global_dict_object

        # Check constraints and objectives expressions
        # Retrieve list of factor objects

        list_constraints_factors, list_objectives_factors = check_expressions_dependancy(node, node_variables,
                                                                                         node_parameters,
                                                                                         parameter_dictionary)

        node.set_constraint_factors(list_constraints_factors)
        node.set_objective_factors(list_objectives_factors)

        print("Check variables of node %s : --- %s seconds ---" % (name, t.time() - start_time))

    program.set_nb_var_index(global_index)
    program.set_variables_dict(program_variables)

    # Global dict of objects

    dict_objects = dict()
    dict_objects["global"] = global_dict_object
    dict_objects["T"] = [time_value]

    # LINK checking

    list_links_factors = check_link(program, external_variables, dict_objects, definitions)
    program.set_link_factors(list_links_factors)

    return program

#
# Name checking functions
#


def match_dictionaries(dict1: dict, dict2: dict) -> None:
    """
    Match dictionaries find the intersection between the keys of two dictionaries
    returns nothing if set is empty and outputs an error otherwise
    INPUT:  dict1 -> dictionary
            dict2 -> dictionary
    OUTPUT: None, or error if fails
    """
    dict1_set = set(dict1)
    dict2_set = set(dict2)

    inter_set = dict1_set.intersection(dict2_set)  
 
    if len(inter_set) != 0:
        error_("ERROR : some variables and parameters share the same name: "+str(inter_set))


def check_names_repetitions(elements_list: list) -> None:
    """
    Checks if a node name is present twice in a list of nodes
    INPUT:  elements_list -> list of node objects
    OUTPUT: None, or error if fails
    """

    n = len(elements_list)
    i = 0

    for e in elements_list:
        name = e.get_name()

        if name == "T" or name == "t":
            error_('ERROR: Name "'+str(name)+'" is reserved for time, used at line '+str(elements_list[i].get_line()))

        for k in range(i+1, n):
            if name == elements_list[k].get_name():
                error_('ERROR: Redefinition error: "'+str(name)+'" at line '+str(elements_list[k].get_line()))
        i = i+1


#
# End Name checking functions
#


#
# Link functions
#


def check_link(program: Program, variables: dict, parameters_obj: dict, parameter_val: dict) -> list:
    """
    check_link function : Takes program object and checks its links
    INPUT:  program -> Program object
    OUTPUT: list of input output pairs 
    """

    links = program.get_links()
    list_factor = []
    for link in links:
        index_id = link.get_index_var()
        if index_id in variables or index_id in parameters_obj:
            error_("Redefinition of " + str(index_id) + " at line : " + str(link.get_line()))
        else:
            parameters_obj[index_id] = [0]
        rhs = link.get_rhs()
        lhs = link.get_lhs()

        var_in_right = variables_in_expression(rhs, variables, parameters_obj, check_size=True)
        var_in_left = variables_in_expression(lhs, variables, parameters_obj, check_size=True)

        if var_in_right is False and var_in_left is False:
            error_('No variable in linking constraint at line '+str(link.get_line()))

        check_linear(rhs, variables, parameters_obj)
        check_linear(lhs, variables, parameters_obj)
        factor = Factorize(link)
        factor.factorize_constraint(variables, parameter_val, [])
        list_factor.append(factor)
        parameters_obj.pop(index_id)
    return list_factor

#
# End link functions
#

#
# Node checking functions
#


def set_size_variables(dictionary_var: dict, dictionary_param: dict, index: int) -> int:
    """
    Initializes the index of variable object inside a dictionary
    """
    start_index = index
    for k in dictionary_var.keys():
        identifier = dictionary_var[k]
        identifier.set_size(dictionary_param)
        start_index = identifier.set_index(start_index)
    return start_index


def check_expressions_dependancy(node: Node, variables: dict, parameters_obj: dict, parameter_val: dict) -> tuple:
    """
    check_expressions_dependancy function : checks the expressions inside a node
    INPUT:  node -> Node object
            variables -> dictionary of <name,identifier> objects
            parameters -> dictionary of <name,array> objects 
    OUTPUT: None
    """
    constraints = node.get_constraints()
    list_constraints_factors = []
    for cons in constraints:
        index_id = cons.get_index_var()
        if index_id in variables or index_id in parameters_obj: 
            error_("Redefinition of "+str(index_id)+" at line : "+str(cons.get_line()))
        else: 
            parameters_obj[index_id] = [0]

        rhs = cons.get_rhs()
        lhs = cons.get_lhs()

        var_in_right = variables_in_expression(rhs, variables, parameters_obj, check_size=True)
        var_in_left = variables_in_expression(lhs, variables, parameters_obj, check_size=True)

        if var_in_right is False and var_in_left is False:
            error_('No variable in constraint at line '+str(cons.get_line()))

        check_linear(rhs, variables, parameters_obj)
        check_linear(lhs, variables, parameters_obj)

        parameters_obj.pop(index_id)
        factor = Factorize(cons)
        factor.factorize_constraint(variables, parameter_val, [])
        list_constraints_factors.append(factor)
        
    objectives = node.get_objectives()
    list_objectives_factors = []

    for obj in objectives:
        
        index_id = obj.get_index_var()

        if index_id in variables or index_id in parameters_obj: 
            error_("Redefinition of %s at line %d" % (index_id, obj.get_line))
        else:
            parameters_obj[index_id] = [0]
        
        expr = obj.get_expression()
        
        contains_var = variables_in_expression(expr, variables, parameters_obj, check_size=True)

        if contains_var is False:
            error_('Objective only depends on constants not on variable at line '+str(expr.get_line()))
        check_linear(expr, variables, parameters_obj)

        parameters_obj.pop(index_id)
        factor = Factorize(obj)
        factor.factorize_objective(variables, parameter_val, [])
        list_objectives_factors.append(factor)
    
    return list_constraints_factors, list_objectives_factors


def variables_in_expression(expression: Expression, variables: dict, parameters: dict, check_in: bool = True,
                            check_size=False) -> bool:
    """
    variables_in_expression function : returns true if expression contains variables and false otherwise
    INPUT:  expression -> expression object
            variables -> dictionary of <name,identifier> objects
            parameters -> dictionary of <name,array> objects 
            check_in -> check for errors in identifier 's assigned expression
    OUTPUT: bool -> boolean value if expression contains variable
    """

    leaves = expression.get_leafs()
    is_variable: bool = False
    defined = False

    for expr_id in leaves:
        
        if expr_id.get_type() == 'sum':

            time_int = expr_id.get_time_interval()
            time_var = time_int.get_index_name()
            children_expr = expr_id.get_children()
            if time_var in parameters:

                error_("Redefinition of "+str(time_var)+" at line : "+str(expr_id.get_line()))
            
            parameters[time_var] = None

            for child in children_expr:

                is_child_var = variables_in_expression(child, variables, parameters, check_in, check_size)
                if is_child_var is True:

                    is_variable = True

            parameters.pop(time_var)

        else:

            identifier = expr_id.get_name()
            if type(identifier) == Attribute:

                node_name = identifier.get_node_field()
                attr = identifier.get_attribute()
                if node_name in parameters:

                    # parameter exists
                    attr_name = attr.get_name()
                    attr_type = attr.get_type()
                    inside_dict = parameters[node_name]
                    if attr_name in inside_dict:

                        param_obj = inside_dict[attr_name]
                        if check_size and ((param_obj.get_type() == "expression" and attr_type == "assign") or
                                           (param_obj.get_type() == "table" and attr_type == "basic")):

                            error_("Unmatching type between definition and usage at line : "+str(identifier.get_line())
                                   + " for identifier : " + str(identifier))
                        defined = True

                elif node_name in variables: 

                    attr_name = attr.get_name()
                    inside_dict = variables[node_name]
                    if attr_name in inside_dict:

                        defined = True
                        is_variable = True
                        id_var = inside_dict[attr_name]
                        if check_size and id_var.get_type() != attr.get_type():

                            error_("Unmatching type between definition and usage at line : "+str(identifier.get_line())
                                   + " for identifier : " + str(identifier))
                if defined is False:

                    error_("Undefined name "+str(expression.get_name())+" at line "+str(expression.get_line()))
                if check_in is True:

                    check_in_brackets(attr, variables, parameters)

            elif type(identifier) == Identifier:

                id_name = identifier.get_name() 
                reserved_names = ["T", "t"]
                if id_name in variables:

                    is_variable = True
                    defined = True
                    id_var = variables[id_name]
                    if check_size and id_var.get_type() != identifier.get_type():

                        error_("Unmatching type between definition and usage at line : "+str(identifier.get_line())
                               + " for identifier : " + str(identifier))
                elif id_name in reserved_names:

                    defined = True
                    id_type = identifier.get_type()
                    if id_type == "assign":

                        error_("Error: can not assign time variables : "+str(expression.get_name()) +
                               " at line "+str(expression.get_line()))
                elif id_name in parameters:

                    defined = True
                    id_param = parameters[id_name]
                    if id_param is not None and check_size and \
                            ((id_param.get_type() == "expression" and identifier.get_type() == "assign") or
                             (id_param.get_type() == "table" and identifier.get_type() == "basic")):

                        error_("Unmatching type between definition and usage at line : "+str(identifier.get_line())
                               + " for identifier : " + str(identifier))
                if defined is False:

                    error_("Undefined name "+str(expression.get_name())+" at line "+str(expression.get_line()))
                if check_in is True:

                    check_in_brackets(identifier, variables, parameters)
    return is_variable


def check_linear(expression: Expression, variables: dict, parameters: dict) -> bool:
    """
    check_linear function : checks if an expression is linear with respect
                            with respect to the variables
    INPUT:  expression -> expression object to check
            variables -> dictionary of <name,identifier> objects
            parameters -> dictionary of <name,array> objects 
    OUTPUT: bool -> boolean value if it depends on a variable
    """

    e_type = expression.get_type()
    nb_child = expression.get_nb_children()
    children = expression.get_children()

    if e_type == 'literal':

        if nb_child != 0:

            error_("INTERNAL ERROR : literal expression must have zero child, got " + str(nb_child) +
                   " check internal parser")
    elif e_type == 'u-':
        if nb_child != 1:

            error_("INTERNAL ERROR : unary minus operator must have one child, got " + str(nb_child) +
                   " check internal parser")
        lin1 = check_linear(children[0], variables, parameters)
        if lin1 is False:

            error_("Non linearity in expression : " + str(children[0])+" only linear problems are accepted at line "
                   + str(children[0].get_line()))
    elif e_type == 'sum':

        if nb_child != 1:

            error_("INTERNAL ERROR : sum operator must have one child, got " + str(nb_child)+" check internal parser")
        time_int = expression.get_time_interval()
        time_var = time_int.get_index_name()
        if time_var in parameters:

            error_("Redefinition of " + str(time_int)+" at line : " + str(expression.get_line()))
        parameters[time_var] = None
        
        lin1 = check_linear(children[0], variables, parameters)
        parameters.pop(time_var)
        if lin1 is False:

            error_("Non linearity in expression : " + str(children[0])+" only linear problems are accepted at line "
                   + str(children[0].get_line()))
    else:

        if nb_child != 2:

            error_("INTERNAL ERROR : binary operators must have two children, got "+str(nb_child) +
                   " check internal parser")
        term1 = variables_in_expression(children[0], variables, parameters)
        term2 = variables_in_expression(children[1], variables, parameters)
        if e_type == "-" or e_type == '+':

            if term1 is True:

                lin1 = check_linear(children[0], variables, parameters)
                if lin1 is False:

                    error_("Non linearity in expression : "+str(children[0]) +
                           " only linear problems are accepted at line "+str(children[0].get_line()))
            if term2 is True:

                lin2 = check_linear(children[1], variables, parameters)
                if lin2 is False:

                    error_("Non linearity in expression : "+str(children[1]) +
                           " only linear problems are accepted at line "+str(children[0].get_line()))
        elif e_type == "*" or e_type == "/":

            if term2 is True and term1 is True:

                string = "Operation '"+str(e_type) +\
                         "' between two expressions containing variables leading to a non linearity at line "\
                         + str(children[0].get_line())+"\n"
                string += "Namely Expression 1 : " + str(children[0]) + " and Expression 2 : "+str(children[1])
                error_(string)
            if term2 is True and e_type == "/":

                string = "A variable in the denominator of a division leads to a Non linearity at line "\
                         + str(children[0].get_line())
                error_(string)
            if term1 is True:

                lin1 = check_linear(children[0], variables, parameters)
                if lin1 is False:

                    error_("Non linearity in expression : "+str(children[0]) +
                           " only linear problems are accepted at line "+str(children[0].get_line()))
        elif e_type == "**":

            if term1 is True or term2 is True:

                string = "Operation '"+str(e_type) +\
                         "' between one expression containing variables leading to a non linearity at line "\
                         + str(children[0].get_line())+"\n"
                string += "Namely Expression 1 : " + str(children[0]) + " and Expression 2 : "+str(children[1])
                error_(string)
        elif e_type == "mod":

            string = "Non linearity, modulo operator is not allowed on variables at line "\
                     + str(children[0].get_line())+"\n"
            error_(string)
        else:

            error_("INTERNAL ERROR : unknown type '"+str(e_type)+"' check internal parser")
    return True


def parameter_evaluation(n_parameters: list, definitions: dict) -> dict:
    """
    parameter_evaluation function : evaluates a list of parameter objects
    INPUT:  n_parameters -> list of parameters objects
            definitions -> dictionary of definitions <name,array>
    OUTPUT: definitions -> dictionary of definitions <name,array>
    """

    for parameter in n_parameters:

        e = parameter.get_expression()
        name = parameter.get_name()
        if e is not None:

            value = e.evaluate_expression(definitions)
            value = [value]
        else:

            value = evaluate_table(parameter.get_vector(), definitions)
        definitions[name] = value
    return definitions


def evaluate_table(list_values: list, definitions: dict) -> list:
    """
    evaluate_table function : evaluates a list of expression objects
    INPUT:  list_values -> list of expression objects
            definitions -> dictionary of definitions <name,value>
    OUTPUT: list <float>
    """

    all_values: list = []
    for value in list_values:

        value_i = value.get_name()
        if type(value_i) == Identifier:

            type_val = value_i.get_type()
            id_name = value_i.get_name()
            if not (id_name in definitions):

                error_('Undefined parameter : '+str(value_i))
            values = definitions[id_name]
            if type_val == "basic" and len(values) == 1:

                value_i = values[0]
            elif type_val == "basic" and len(values) > 1:

                error_('Parameter not properly defined : '+str(value_i))
            elif type_val == "assign":

                inner_expr = value_i.get_expression()
                index = inner_expr.evaluate_expression(definitions)
                if type(index) == float:

                    if index.is_integer() is False:

                        error_("Error: an index is a float: " + str(value_i))
                    index = int(round(index))

                if index < 0 or len(values) <= index:

                    error_('Parameter does not exit at this index : '+str(value_i))
                value_i = values[index]
        all_values.append(value_i)
    return all_values


def check_in_brackets(identifier: Identifier, variables: dict, parameters: dict) -> None:
    """
    check_in_brackets function : checks identifier's expression inside brackets
    INPUT:  identifier -> Identifier object
            variables -> dictionary of variables
            parameters -> dictionary of parameters
    OUTPUT: None
    """
    id_type = identifier.get_type()
    if id_type == 'assign':
        expr = identifier.get_expression()
        if expr is None:
            error_("INTERNAL ERROR : expected expression for "+str(id_type)+" check internal parser")
        check_expr_in_brackets(expr, variables, parameters)


def check_expr_in_brackets(expression: Expression, variables: dict, parameters: dict) -> bool:
    """
    check_expr_in_brackets function : checks if the in-bracket expression of an identifier is correctly defined
    INPUT:  expression -> expression in bracket
            variables -> dictionary of variables
            parameters -> dictionary of parameters
    OUTPUT: is_time_var -> True if it depends on t, False otherwise and an error if check goes wrong
    """

    e_type = expression.get_type()
    nb_child = expression.get_nb_children()
    found = False
    is_time_var: bool = False

    if e_type == 'literal':

        if nb_child != 0:

            error_("INTERNAL ERROR : literal must have zero child, got "+str(nb_child)+" check internal parser")
        identifier = expression.get_name()

        if type(identifier) == Identifier:

            id_name = identifier.get_name()
            id_type = identifier.get_type()
            time_variables = ["t", "T"]
            if id_name in parameters:

                found = True
            elif id_name in time_variables:

                is_time_var = True
                found = True
            elif id_name in variables:

                error_('Variable in brackets for assignement ')
            if found is False:
                
                error_('Identifier "' + str(identifier) +
                       '" used but not previously defined, at line '+str(expression.get_line()))
            
            if id_type == "assign":

                is_time_var = check_expr_in_brackets(identifier.get_expression(), variables, parameters)
        elif type(identifier) == Attribute:

            attr = identifier.get_attribute()
            attr_name = attr.get_name()
            node_n = identifier.get_node_field()
            if node_n not in parameters and attr_name not in parameters[node_n]:

                error_('Identifier "' + str(identifier) + '" used but not previously defined, at line '
                       + str(expression.get_line()))
            if node_n in variables:

                error_('Variable in brackets for assignement ')
            type_attr = attr.get_type()
            if type_attr == "assign":

                is_time_var = check_expr_in_brackets(attr.get_expression(), variables, parameters)
    elif e_type == 'u-':

        if nb_child != 1:

            error_("INTERNAL ERROR : unary minus must have one child, got "+str(nb_child)+" check internal parser")
        children = expression.get_children()
        is_time_var = check_expr_in_brackets(children[0], variables, parameters)
    elif e_type == "sum":

        if nb_child != 1:

            error_("INTERNAL ERROR : unary minus must have one child, got "+str(nb_child)+" check internal parser")
        children = expression.get_children()
        time_interval = expression.get_time_interval()
        name_index = time_interval.get_index_name()
        if name_index in parameters:

            error_("Redefinition of "+name_index+" at line "+expression.get_line())
        parameters[name_index] = None
        is_time_var = check_expr_in_brackets(children[0], variables, parameters)
        parameters.pop(name_index)
    else:

        if nb_child != 2:

            error_("INTERNAL ERROR : binary operators must have two children, got "
                   + str(nb_child)+" check internal parser")
        children = expression.get_children()
        is_time_var1 = check_expr_in_brackets(children[0], variables, parameters)
        is_time_var2 = check_expr_in_brackets(children[1], variables, parameters)
        if e_type == '+' or e_type == '-':

            if is_time_var2 or is_time_var1:

                is_time_var = True
        elif e_type == '*':

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

#
# END Expression FUNCTIONS
#
