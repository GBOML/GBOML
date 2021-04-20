
# gboml_semantic.py
#
# Part of the GBOML Project
# University of Liege
# Writer : MIFTARI B
# ------------


from .classes import Time, Expression,Variable,Parameter,\
    Attribute,Program,Objective,Node,Identifier,Constraint 
import copy 
import numpy as np # type: ignore
from .utils import error_,list_to_string
import time as t 

def semantic(program:Program)->Program:
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
    node_list = program.get_nodes()
    check_names_repetitions(node_list)

    #Check if an objective function is defined
    program.check_objective_existence()

    definitions = {}
    definitions["T"]=[time_value]

    #GLOBAL 
    global_param = program.get_global_parameters()
    global_dict_object = program.get_dict_global_parameters()

    global_dict = parameter_evaluation(global_param,definitions.copy())
    global_dict.pop("T")
    definitions["global"]= global_dict
    definitions["GLOBAL"]= global_dict

    program_variables = {}
    external_variables = {}

    global_index = 0

    #Inside each node 
    for node in node_list:
        #Initialize dictionary of defined parameters

        parameter_dictionary = definitions.copy()

        #Retrieve all the parameters'names in set
        node_parameters = node.get_dictionary_parameters() 

        name = node.get_name()
        #Retrieve a dictionary of [name,identifier object] tuple
        node_variables = node.get_dictionary_variables()
        program_variables[name] = node_variables

        external_variables[name] = node.get_dictionary_variables("external")

        #Check if variables and parameters share names
        match_dictionaries(node_parameters,node_variables)

        #Add evaluated parameters to the dictionary of defined paramaters
        parameter_dictionary = parameter_evaluation(node.get_parameters(),parameter_dictionary)

        #Set size of different parameters
        global_index = set_size_variables(node_variables,parameter_dictionary,global_index)

        #Keep parameter dictionary
        node.set_parameter_dict(parameter_dictionary)

        node_parameters["global"] = global_dict_object
        node_parameters["GLOBAL"] = global_dict_object
        #Check constraints and objectives expressions
        check_expressions_dependancy(node,node_variables,node_parameters,parameter_dictionary)

        #Augment node with constraintes written in matrix format
        convert_constraints_matrix(node,node_variables,parameter_dictionary)

        #Augment node with objectives written in matrix format
        convert_objectives_matrix(node,node_variables,parameter_dictionary)

    program.set_nb_var_index(global_index)
    program.set_variables_dict(program_variables)

    #if the model does not have a proper constraint defined
    if program.get_number_constraints()==0:
        error_("ERROR: no valid constraint was defined making the problem unsolvable")

    #LINKS conversion
    # TODO: is there a reason that we have the node loop above but the link loops in separate functions?
    # TODO: should we use a copy of definitions (as above)?
    # TODO: could refactor check_expressions_dependancy to
    """
    check_expressions_dependancy function : the dependency of given expression
    INPUT:  expr -> expression
            variables -> dictionary of <name,identifier> objects
            parameters -> dictionary of <name,array> objects 
    OUTPUT: dep (constant, linear, nonlinear, undefined[unknown identifier found])
    """
    # this would encapsulate the common code in check_expressions_dependancy and check_link
    dict_objects = {}
    dict_objects["global"]= global_dict_object
    dict_objects["GLOBAL"]= global_dict_object
    dict_objects["T"] = [time_value]


    check_link(program,external_variables,dict_objects)

    convert_link_matrix(program,external_variables,definitions)

    #program.set_link_constraints(input_output_matrix)

    return program
    
### -------------------------
### NAME RELATED FUNCTIONS
def match_dictionaries(dict1:dict,dict2:dict)->None:
    """
    Match dictionaries find the intersection between the keys of two dictionnaries 
    returns nothing if set is empty and outputs an error otherwise
    INPUT:  dict1 -> dictionary
            dict2 -> dictionary
    OUTPUT: None, or error if fails
    """
    dict1_set = set(dict1)
    dict2_set = set(dict2)

    inter_set = dict1_set.intersection(dict2_set)  
 
    if len(inter_set)!=0:
        error_("ERROR : some variables and parameters share the same name: "+str(inter_set))

def check_names_repetitions(elements_list:list)->None:
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

        for k in range(i+1,n):
            if name == elements_list[k].get_name():
                error_('ERROR: Redefinition error: "'+str(name)+'" at line '+str(elements_list[k].get_line()))
        i = i+1

### END NAME RELATED FUNCTIONS
### -------------------------

### -------------------------
### LINKS RELATED FUNCTIONS

def convert_link_matrix(program:Program,variables:dict,definitions:dict)->None:
    """
    convert_link_matrix function : converts a node's links and variables 
    into constraints and variables matrices of the respective form [value,lign,column]
    and full matrix 
    INPUT:  node, node object treated
            variables, dictionary of variables
            definitions, dictionary with all the parameters and constants
    OUTPUT: None, augments the node object with the corresponding matrices
    """
    constraints = program.get_links()
    
    variables_dict = variables.copy()
    flag_out_of_bounds = False

    if not("T" in definitions):
        error_("INTERNAL ERROR: T not found in list of parameters")
    T = definitions["T"][0]

    for constr in constraints:
        constr_leafs = constr.get_expanded_leafs(definitions)
        variables_used = []

        for leaf in constr_leafs:
            attr = leaf.get_name()
            if type(attr)==Attribute:                
                node_name = attr.get_node_field()
                identifier = attr.get_attribute()
                if node_name in variables: 
                    external_dict = variables_dict[node_name]
                    for variable in external_dict: 
                        if identifier.name_compare(variable):
                            index = external_dict[variable].get_index()
                            size = external_dict[variable].get_size()
                            variables_used.append([node_name,index,identifier,size])
                            break
        program.add_var_link(variables_used)
    
        nb_variables = len(variables_used)

        constr_range = constr.get_time_range(definitions)
        constr_var = constr.get_index_var()
        if (constr_var in definitions) or (constr_var in variables):
            error_("Error loop index used for constraint in line : "+str(constr.get_line())+" name already used : "+str(constr_var))

        if constr_range == None:
            t_horizon = T
            constr_range = range(t_horizon)

        unique_constraint = False
        if(not is_time_dependant_constraint(constr,variables,definitions,constr_var)):
            unique_constraint = True

        add_t:float = 0.0
        for k in constr_range:
            definitions[constr_var]=[k]

            if constr.check_time(definitions)==False:
                continue

            new_values = np.zeros(nb_variables)
            columns = np.zeros(nb_variables)
            
            offset:float = 0.0
            l = 0
            for node_name,n,identifier,id_size in variables_used:
                
                id_type = identifier.get_type()
                id_name = identifier.get_name()

                if id_type == "basic":
                    offset = 0
                else : 
                    offset = identifier.get_expression().evaluate_expression(definitions)
                    if type(offset) == float:
                        if offset.is_integer()==False:
                            error_("Error: an index is a float: "+ str(identifier)+\
                                'at line '+str(identifier.get_line())+"for t = "+str(k))
                        offset = int(round(offset))

                    if offset >= id_size or offset<0:
                        flag_out_of_bounds = True
                        break

                var_dict = variables_dict[node_name]
                var = var_dict[id_name]
                expr = Expression("literal",offset)

                var.set_expression(expr)

                term,flag_out_of_bounds = variable_in_constraint(constr,var,definitions,node_name)
                new_values[l]=term

                columns[l]=n+offset
            
                if flag_out_of_bounds:
                    break
                l+=1
            
            if flag_out_of_bounds==False:

                starting_t = t.time() 
                constant = constant_in_constraint(constr,variables,definitions)
                if not np.any(new_values) and constant != 0:
                    error_("Error constraint "+str(constr)+" is impossible for t="+str(k))

                add_t += t.time()-starting_t
                sign = constr.get_sign()
                matrix = [new_values,columns]
                program.add_link_constraints([matrix,constant,sign])
                if unique_constraint == True:
                    break
            
        definitions.pop(constr_var)


def check_link(program:Program,variables:dict,parameters:dict)->None:
    """
    check_link function : Takes program object and checks its links
    INPUT:  program -> Program object
    OUTPUT: list of input output pairs 
    """

    links = program.get_links()

    for link in links:
        rhs = link.get_rhs()
        lhs = link.get_lhs()

        var_in_right = variables_in_expression(rhs,variables,parameters,check_size = True)
        var_in_left = variables_in_expression(lhs,variables,parameters,check_size = True)

        if var_in_right == False and var_in_left == False:
            error_('No variable in linking constraint at line '+str(link.get_line()))

        check_linear(rhs,variables,parameters)
        check_linear(lhs,variables,parameters)


### End LINK FUNCTIONS
### -------------------------

def set_size_variables(dictionary_var:dict, dictionary_param:dict, index:int)->int:
    start_index = index
    for k in dictionary_var.keys():
        identifier = dictionary_var[k]
        identifier.set_size(dictionary_param)
        start_index = identifier.set_index(start_index)
    return start_index


### -------------------------
### Expression FUNCTIONS

def check_expressions_dependancy(node:Node,variables:dict,parameters_obj:dict,parameter_val:dict)->None:
    """
    check_expressions_dependancy function : checks the expressions inside a node
    INPUT:  node -> Node object
            variables -> dictionary of <name,identifier> objects
            parameters -> dictionary of <name,array> objects 
    OUTPUT: None
    """
    constraints = node.get_constraints()
    for cons in constraints:
        index_id = cons.get_index_var()
        if index_id in variables or index_id in parameters_obj: 
            error_("Redefinition of "+str(index_id)+" at line : "+str(cons.get_line()))
        else: 
            parameters_obj[index_id]=[0]

        rhs = cons.get_rhs()
        lhs = cons.get_lhs()

        var_in_right = variables_in_expression(rhs,variables,parameters_obj, check_size=True)
        var_in_left = variables_in_expression(lhs,variables,parameters_obj,check_size=True)

        if var_in_right == False and var_in_left == False:
            error_('No variable in constraint at line '+str(cons.get_line()))

        check_linear(rhs,variables,parameters_obj)
        check_linear(lhs,variables,parameters_obj)

        parameters_obj.pop(index_id)
    
    objectives = node.get_objectives()

    for obj in objectives:
        
        index_id = obj.get_index_var()

        if index_id in variables or index_id in parameters_obj: 
            error_("Redefinition of "+str(index_id)+" at line : "+str(cons.get_line()))
        else : 
            parameters_obj[index_id]=[0]
        
        expr = obj.get_expression()
        
        contains_var = variables_in_expression(expr,variables,parameters_obj,check_size=True)
        
        if contains_var == False:
            error_('Objective only depends on constants not on variable at line '+str(expr.get_line()))
        check_linear(expr,variables,parameters_obj)

        parameters_obj.pop(index_id)

def variables_in_expression(expression:Expression,variables:dict,parameters:dict,check_in:bool = True, check_size = False )->bool:
    """
    variables_in_expression function : returns true if expression contains variables and false otherwise
    INPUT:  expression -> expression object
            variables -> dictionary of <name,identifier> objects
            parameters -> dictionary of <name,array> objects 
            check_in -> check for errors in identifier 's assigned expression
    OUTPUT: bool -> boolean value if expression contains variable
    """

    leafs = expression.get_leafs()
    is_variable:bool = False
    defined = False

    for expr_id in leafs:
        
        if expr_id.get_type()=='sum':
            time_int = expr_id.get_time_interval()
            time_var = time_int.get_index_name()
            children_expr = expr_id.get_children()
            if time_var in parameters:
                error_("Redefinition of "+str(time_var)+" at line : "+str(expr_id.get_line()))
            
            parameters[time_var]=None

            for child in children_expr:
                is_child_var = variables_in_expression(child,variables,parameters,check_in,check_size)
                if is_child_var == True:
                    is_variable = True

            parameters.pop(time_var)

        else : 
            identifier = expr_id.get_name()

            if type(identifier)==Attribute:
                node_name = identifier.get_node_field()
                attr = identifier.get_attribute()
                if node_name in parameters :
                    #PARAM EXIST
                    attr_name = attr.get_name()
                    attr_type = attr.get_type()

                    inside_dict = parameters[node_name]
                    if attr_name in inside_dict:
                        param_obj = inside_dict[attr_name]
                        if check_size and ((param_obj.get_type()== "expression" and attr_type=="assign") or \
                        (param_obj.get_type()== "table" and attr_type=="basic")):
                            error_("Unmatching type between definition and usage at line : "+str(identifier.get_line())\
                            +" for identifier : "+ str(identifier)) 

                        defined = True
                        is_variable = False

                elif node_name in variables: 
                    attr_name = attr.get_name()
                    inside_dict = variables[node_name]
                    if attr_name in inside_dict:
                        defined = True
                        is_variable = True
                        id_var = inside_dict[attr_name]
                        if check_size and id_var.get_type()!= attr.get_type():
                            error_("Unmatching type between definition and usage at line : "+str(identifier.get_line())\
                                +" for identifier : "+ str(identifier)) 

                
                if defined == False:
                    error_("Undefined name "+str(expression.get_name())+" at line "+str(expression.get_line()))
                
                if check_in == True:
                    check_in_brackets(attr,variables,parameters)

            elif type(identifier)==Identifier:
                id_name = identifier.get_name() 
                reserved_names = ["T","t"]
                if id_name in variables:
                    is_variable = True
                    defined = True
                    id_var = variables[id_name]
                    if check_size and id_var.get_type()!= identifier.get_type():
                        error_("Unmatching type between definition and usage at line : "+str(identifier.get_line())\
                            +" for identifier : "+ str(identifier)) 

                elif id_name in reserved_names:
                    defined = True 
                    id_type = identifier.get_type()
                    if id_type == "assign":
                        error_("Error: can not assign time variables : "+str(expression.get_name())+\
                            " at line "+str(expression.get_line()))

                elif id_name in parameters:
                    defined = True
                    id_param = parameters[id_name]
                    if check_size and ((id_param.get_type()== "expression" and identifier.get_type()=="assign") or \
                        (id_param.get_type()== "table" and identifier.get_type()=="basic")):
                        error_("Unmatching type between definition and usage at line : "+str(identifier.get_line())\
                            +" for identifier : "+ str(identifier)) 

                if defined == False:
                    error_("Undefined name "+str(expression.get_name())+" at line "+str(expression.get_line()))

                if check_in == True:
                    check_in_brackets(identifier,variables,parameters)


    return is_variable

def check_linear(expression:Expression,variables:dict,parameters:dict)->bool:
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
        if nb_child !=0:
            error_("INTERNAL ERROR : literal expression must have zero child, got "+str(nb_child)+" check internal parser")
    elif e_type == 'u-':
        if nb_child !=1:
            error_("INTERNAL ERROR : unary minus operator must have one child, got "+str(nb_child)+" check internal parser")

        lin1  =  check_linear(children[0],variables,parameters)
        if lin1 == False:
            error_("Non linearity in expression : "+str(children[0])+" only linear problems are accepted at line "+str(children[0].get_line()))

    elif e_type == 'sum':
        if nb_child !=1:
            error_("INTERNAL ERROR : sum operator must have one child, got "+str(nb_child)+" check internal parser")

        time_int = expression.get_time_interval()
        time_var = time_int.get_index_name()
        if time_var in parameters:
            error_("Redefinition of "+str(time_int)+" at line : "+str(expression.get_line()))
            
        parameters[time_var]=None
        
        lin1  =  check_linear(children[0],variables,parameters)
        parameters.pop(time_var)
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


def parameter_evaluation(n_parameters:list,definitions:dict)->dict:
    """
    parameter_evaluation function : evaluates a list of parameter objects
    INPUT:  n_parameters -> list of parameters objects
            definitions -> dictionary of definitions <name,array>
    OUTPUT: definitions -> dictionary of definitions <name,array>
    """

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

def evaluate_table(list_values:list,definitions:dict)->list:
    """
    evaluate_table function : evaluates a list of expression objects
    INPUT:  list_values -> list of expression objects
            definitions -> dictionary of definitions <name,value>
    OUTPUT: list <float>
    """

    all_values:list = []
    for value in list_values:
        value_i = value.get_name()

        if type(value_i) == Identifier:
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

def check_in_brackets(identifier:Identifier,variables:dict,parameters:dict)->None:
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
        if expr == None:
            error_("INTERNAL ERROR : expected expression for "+str(id_type)+" check internal parser")
        check_expr_in_brackets(expr,variables,parameters)

def check_expr_in_brackets(expression:Expression,variables:dict,parameters:dict)->bool:
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
    is_time_var:bool = False

    if e_type =='literal':
        if nb_child != 0:
            error_("INTERNAL ERROR : literal must have zero child, got "+str(nb_child)+" check internal parser")
        identifier = expression.get_name()

        if type(identifier)==Identifier:
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

            if found == False:
                
                error_('Identifier "'+ str(identifier)+ '" used but not previously defined, at line '+str(expression.get_line()))
            
            if id_type == "assign":
                is_time_var = check_expr_in_brackets(identifier.get_expression(),variables,parameters)

        elif type(identifier)==Attribute:
            attr = identifier.get_attribute()
            attr_name = attr.get_name()
            node_n = identifier.get_node_field()
            if node_n not in parameters and attr_name not in parameters[node_n]:
                error_('Identifier "'+ str(identifier)+ '" used but not previously defined, at line '+str(expression.get_line()))
            if node_n in variables:
                error_('Variable in brackets for assignement ')

            type_attr = attr.get_type()
            if type_attr=="assign":
                is_time_var = check_expr_in_brackets(attr.get_expression(),variables,parameters)


    elif e_type == 'u-':
        if nb_child != 1:
            error_("INTERNAL ERROR : unary minus must have one child, got "+str(nb_child)+" check internal parser")

        children = expression.get_children()
        is_time_var = check_expr_in_brackets(children[0],variables,parameters)

    elif e_type == "sum":
        if nb_child !=1:
            error_("INTERNAL ERROR : unary minus must have one child, got "+str(nb_child)+" check internal parser")

        children = expression.get_children()
        time_interval = expression.get_time_interval()
        name_index = time_interval.get_index_name()
        #range_index = time_interval.get_range(definitions)
        if name_index in parameters:
            error_("Redefinition of "+name_index+" at line "+expression.get_line())
        parameters[name_index]=None
        is_time_var = check_expr_in_brackets(children[0],variables,parameters)
        parameters.pop(name_index)


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

def convert_constraints_matrix(node:Node,variables:dict,definitions:dict)->None:
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
    
    variables_dict = variables.copy()

    if not("T" in definitions):
        error_("INTERNAL ERROR: T not found in list of parameters")
    T = definitions["T"][0]

    start_time = t.time()

    for constr in constraints:
        constr_leafs = constr.get_expanded_leafs(definitions)
        variables_used = []

        for leaf in constr_leafs:
            l_type = leaf.get_type()

            if l_type == "literal":
                identifier = leaf.get_name() 
                replaced_dict = leaf.get_replacement_dict()
                if type(identifier)==Identifier:
                
                    for variable in variables_dict: 
                        if identifier.name_compare(variable):
                            index = variables_dict[variable].get_index()
                            size = variables_dict[variable].get_size()
                            variables_used.append([index,identifier,size,replaced_dict])
                            break
        nb_variables = len(variables_used)

        constr_range = constr.get_time_range(definitions)
        constr_var = constr.get_index_var()
        if (constr_var in definitions) or (constr_var in variables):
            error_("Error loop index used for constraint in line : "+str(constr.get_line())+" name already used : "+str(constr_var))

        if constr_range == None:
            t_horizon = T
            constr_range = range(t_horizon)

        unique_constraint = False
        if(not is_time_dependant_constraint(constr,variables,definitions,constr_var)):
            unique_constraint = True

        for k in constr_range:
            definitions[constr_var]=[k]

            if constr.check_time(definitions)==False:
                continue

            new_values = np.zeros(nb_variables)
            columns = np.zeros(nb_variables)
            
            offset:float = 0.0
            l = 0
            for n,identifier,id_size,replaced_dict in variables_used:
                
                id_type = identifier.get_type()
                id_name = identifier.get_name()

                if id_type == "basic":
                    offset = 0
                else : 
                    offset = identifier.get_expression().evaluate_expression(definitions)
                    if type(offset) == float:
                        if offset.is_integer()==False:
                            error_("Error: an index is a float: "+ str(identifier)+\
                                'at line '+str(identifier.get_line())+"for t = "+str(k))
                        offset = int(round(offset))

                    if offset >= id_size or offset<0:
                        flag_out_of_bounds = True
                        break

                var = variables_dict[id_name]
                expr = Expression("literal",offset)

                var.set_expression(expr)

                term,flag_out_of_bounds = variable_in_constraint(constr,var,definitions,replaced_dict)
                new_values[l]=term

                columns[l]=n+offset
            
                if flag_out_of_bounds:
                    break
                l+=1
            
            if flag_out_of_bounds==False:

                constant = constant_in_constraint(constr,variables,definitions)
                if not np.any(new_values) and constant != 0:
                    error_("Error constraint "+str(constr)+" is impossible for t="+str(k))

                sign = constr.get_sign()
                matrix = [new_values,columns]
                node.add_constraints_matrix([matrix,constant,sign])
                if unique_constraint == True:
                    break
        definitions.pop(constr_var)
                        
    print("Check variables of node "+ str(node.get_name()) +" : --- %s seconds ---" % (t.time() - start_time))


    
def constant_in_constraint(constr:Constraint,variables:dict,constants:dict)->float:
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
    value:float = 0.0

    value1 = constant_factor_in_expression(rhs,variables,constants)
    
    value2 = constant_factor_in_expression(lhs,variables,constants)
    
    value = value2 - value1
    return value

def constant_factor_in_expression(expression:Expression,variables:dict,constants:dict)->float:
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
    value:float = 0.0

    if variables_in_expression(expression,variables,constants,check_in = False)==False:
        value = expression.evaluate_expression(constants)
    else:
        if e_type == 'u-':
            is_var = variables_in_expression(children[0],variables,constants,check_in = False)
            if is_var==False:
                value = children[0].evaluate_expression(constants)
            else: 
                value = constant_factor_in_expression(children[0],variables,constants)
        elif e_type == "sum":
            time_interv = expression.get_time_interval()
            index_name = time_interv.get_index_name() 
            index_range = time_interv.get_range(constants)
            if index_name in constants:
                error_("INTERNAL ERROR: index already in constants in sum")
            constants[index_name] = 0
            
            is_var = variables_in_expression(children[0],variables,constants,check_in = False)

            value = 0
            for k in index_range:
                constants[index_name]=[k]
                if is_var==False:
                    value_k = children[0].evaluate_expression(constants)
                else: 
                    value_k = constant_factor_in_expression(children[0],variables,constants)

                value += value_k
            constants.pop(index_name)

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

def convert_objectives_matrix(node:Node,variables:dict,definitions:dict)->None:
    """
    convert_objectives_matrix function : converts a node's objectives 
    into objective matrices of the form [value,lign,column]
    INPUT:  node, node object treated
            variables, dictionary of variables
            definitions, dictionary with all the parameters and constants
    OUTPUT: None, augments the node object with the corresponding matrices
    """

    objectives = node.get_objectives()

    if not("T" in definitions):
        error_("INTERNAL ERROR: T not found in list of definitions")

    T = definitions["T"][0]

    variables_dict = variables.copy()

    objective_index = 0

    for obj in objectives:
        obj_type = obj.get_type()
        expr = obj.get_expression()

        expr_leafs = expr.expanded_leafs(definitions)

        variables_used = []

        for leaf in expr_leafs:
            identifier = leaf.get_name()
            if type(identifier)==Identifier:                
                
                for variable in variables_dict: 
                    if identifier.name_compare(variable):
                        index = variables_dict[variable].get_index()
                        size = variables_dict[variable].get_size()
                        variables_used.append([index,identifier,size])
                        break
    
        nb_variables = len(variables_used)

        obj_range = obj.get_time_range(definitions)
        obj_var = obj.get_index_var()
        if (obj_var in definitions) or (obj_var in variables):
            error_("Error loop index used for constraint in line : "+str(obj.get_line())+" name already used : "+str(obj_var))

        if(is_time_dependant_expression(expr,variables,definitions,obj_var)):
            t_horizon = T
        else:
            t_horizon = 1
            obj_range = range(t_horizon)

        if obj_range == None : 
            obj_range = range(t_horizon)

        for k in obj_range:
            definitions[obj_var]=[k]

            values = np.zeros(nb_variables)
            columns = np.zeros(nb_variables)

            l = 0
            offset:float = 0.0
            for n,identifier,id_size in variables_used:

                if obj.check_time(definitions)==False:
                    continue

                id_type = identifier.get_type()
                id_name = identifier.get_name()

                if id_type == "basic":
                    offset = 0
                else : 
                    offset = identifier.get_expression().evaluate_expression(definitions)

                    if type(offset) == float:
                        if offset.is_integer()==False:
                            error_("Error: an index is a float: "+ str(identifier)+\
                                'at line '+str(identifier.get_line())+"for t = "+str(k))
                        offset = int(round(offset))

                    if offset >= id_size or offset<0:
                        flag_out_of_bounds = True
                        break
                
                var = variables_dict[id_name]
                expr_off = Expression("literal",offset)

                var.set_expression(expr_off)

                _,term,flag_out_of_bounds = variable_factor_in_expression(expr,var,definitions)

                values[l] = term
                columns[l] = n + offset

                if flag_out_of_bounds:
                    break
                l += 1
            
            if flag_out_of_bounds == False:
                matrix = [values,columns,objective_index]
                node.add_objective_matrix([matrix,obj_type])
        definitions.pop(obj_var)
        
        objective_index +=1



def variable_in_constraint(constr:Constraint,variable:Identifier,constants:dict,replaced_dict= {},node_name = "")->tuple:
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

    _,value1,flag_out_of_bounds1 = variable_factor_in_expression(rhs,variable,constants,replaced_dict,node_name)
    _,value2,flag_out_of_bounds2 = variable_factor_in_expression(lhs,variable,constants,replaced_dict,node_name)
    value = value1 - value2
    if flag_out_of_bounds1 or flag_out_of_bounds2:
        flag_out_of_bounds = True
    return value,flag_out_of_bounds

def variable_factor_in_expression(expression:Expression,variable:Identifier,definitions:dict,replaced_dict:dict={},node_name = "")->tuple:
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
    value:float = 0.0
    flag_out_of_bounds = False

    if e_type == 'literal':
        identifier = expression.get_name()
        var_size = variable.get_size()
        if type(expression.get_name())==Identifier:
            if identifier.name_compare(variable):
                type_id = identifier.get_type()
                if type_id == 'assign':
                    t_expr = identifier.get_expression()

                    t_value = t_expr.evaluate_expression(definitions)

                    if not('T' in definitions):
                        error_("INTERNAL ERROR: T not found")
                    
                    values_T = definitions['T']
                    T = values_T[0]

                    if t_value < 0 and t_value >= var_size :
                        flag_out_of_bounds = True

                    value1 = variable.get_expression().evaluate_expression(definitions)
                    
                    if value1 == t_value:
                        found = True
                        value = 1
                else:
                    value1 = variable.get_expression().evaluate_expression(definitions)

                    if 0 == value1:
                        found = True
                        value = 1
    
        if type(expression.get_name())==Attribute:
            attribute = identifier
            attr_node = attribute.get_node_field()
            attr_id = attribute.get_attribute()
            if attr_node == node_name and attr_id.name_compare(variable):
                type_id = attr_id.get_type()
                if type_id == 'assign':
                    t_expr = attr_id.get_expression()
                    if not('T' in definitions):
                        error_("INTERNAL ERROR: T not found")
                    t_value = t_expr.evaluate_expression(definitions)
                    values_T = definitions['T']
                    T = values_T[0]
                    if t_value < 0 or t_value >= var_size:
                        flag_out_of_bounds = True
                    value1 = variable.get_expression().evaluate_expression(definitions)
                    if value1 == t_value:
                        found = True
                        value = 1
                else:
                    value1 = variable.get_expression().evaluate_expression(definitions)

                    if 0 == value1:
                        found = True
                        value = 1
    else:
        children = expression.get_children()
        if e_type == 'u-':
            found,value,flag_out_of_bounds = variable_factor_in_expression(children[0],variable,definitions,node_name)
            if flag_out_of_bounds:
                return found,value,flag_out_of_bounds
            value = - value

        elif e_type == "sum":
            time_interval = expression.get_time_interval()
            name_index = time_interval.get_index_name()
            range_index = time_interval.get_range(definitions)
            value = 0
            if is_in_sum(variable,expression):
                #index_val = replaced_dict[name_index]
                
                #definitions[name_index]=[index_val]
                for name_index in range_index:
                    found_interim, value_interm, flag_out_of_bounds_interm = variable_factor_in_expression(children[0],variable,definitions,node_name)
                    if flag_out_of_bounds_interm:
                        flag_out_of_bounds = True
                        return found, value, flag_out_of_bounds
                        
                    if found_interim == True:
                        found = True
                        value += value_interm
                definitions.pop(name_index)

        else:
            found1,value1,flag_out_of_bounds = variable_factor_in_expression(children[0],variable,definitions,node_name)
            
            if flag_out_of_bounds:
                return found,value,flag_out_of_bounds
            found2,value2,flag_out_of_bounds = variable_factor_in_expression(children[1],variable,definitions,node_name)
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

def is_in_sum(variable:Identifier,expr:Expression)->bool:
    expr_type = expr.get_type()
    is_in = False
    if expr_type == "sum":
        children = expr.get_children()
        child = children[0]
        child_leaves = child.get_leafs()
        for leaf in child_leaves:
            l_type = leaf.get_type()
            if l_type == "literal":
                identifier = leaf.get_name()
                if variable.name_compare(identifier):
                    is_in = True
                    break
            elif l_type == "sum":
                is_in = is_in_sum(variable,expr)
                if is_in:
                    break
    return is_in


def is_time_dependant_constraint(constraint:Constraint,variables_dictionary:dict,parameter_dictionary:dict,index_id:str = "t")->bool:
    """
    is_time_dependant_constraint predicate : checks if constraint is time dependant
    A constraint is time dependant if its right hand side or left depend on "t"
    INPUT:  constraint, constraint to check
            variables_dictionary, dictionary with all the variables
            parameter_dictionary, dictionary with all the parameters and constants
    OUTPUT: predicate, the boolean corresponding to the predicate
    """
    rhs = constraint.get_rhs()
    time_dep:bool = is_time_dependant_expression(rhs,variables_dictionary,parameter_dictionary,index_id)
    lhs = constraint.get_lhs()
    if time_dep == False:
        time_dep = is_time_dependant_expression(lhs,variables_dictionary,parameter_dictionary,index_id)
    return time_dep

def is_time_dependant_expression(expression:Expression,variables_dictionary:dict,parameter_dictionary:dict,index_id:str="t")->bool:
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
    predicate:bool = False

    if e_type == 'literal':
        identifier = expression.get_name()
        if type(expression.get_name())==Identifier:
            id_type = identifier.get_type()
            id_name = identifier.get_name()

            if id_name == index_id:
                predicate = True
            elif id_name == "T":
                predicate = False
            else:
                if id_name in variables_dictionary:
                    if id_type =="assign":

                        predicate = is_time_dependant_expression(identifier.get_expression(),\
                            variables_dictionary,parameter_dictionary,index_id)
                    else: 
                        predicate = False
                elif id_name in parameter_dictionary:
                    if id_type =="assign":
                        predicate = is_time_dependant_expression(identifier.get_expression(),\
                            variables_dictionary,parameter_dictionary,index_id)
                    else:
                        vector = parameter_dictionary[id_name]
                        if len(vector)>1:
                            predicate = False
    
        if type(expression.get_name())==Attribute: 
            attr = expression.get_name()
            identifier = attr.get_attribute()
            if identifier.get_type() == "assign":
                predicate = is_time_dependant_expression(identifier.get_expression(),variables_dictionary,parameter_dictionary,index_id)

    else:
        for i in range(nb_child):
            predicate_i = is_time_dependant_expression(children[i],variables_dictionary,parameter_dictionary,index_id)
            if predicate_i:
                predicate = predicate_i
                break

    return predicate

### END Expression FUNCTIONS
### -------------------------