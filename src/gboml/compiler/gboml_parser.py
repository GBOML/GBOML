# Copyright (C) 2020 - 2022
# Bardhyl Miftari, Mathias Berger, Hatim Djelassi, Damien Ernst,
# University of Liege .
# Licensed under the MIT License (see LICENSE file).


from .ply import yacc  # type: ignore
from copy import deepcopy
import os

from .gboml_lexer import tokens, lexer
from .utils import check_file_exists, error_, move_to_directory
from .classes import Time, Expression, Variable, Parameter, Program, Objective,\
    Node, Identifier, Constraint, Condition, TimeInterval, Hyperedge

list_opened_files = []
cache_graph = {}

# precedence rules from least to highest priority
# with associativity also specified

precedence = (  # Unary minus operator
    ('left', 'OR'),
    ('left', 'AND'),
    ('right', 'NOT'),
    ('nonassoc', 'EQUAL', 'LEQ', 'BEQ', 'BIGGER', 'LOWER', 'NEQ'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'MULT', 'DIVIDE'),
    ('right', 'UMINUS'),
    ('left', 'POW'),
    )


# Start symbol

def p_start(p):
    """start : time global program"""

    timehorizon = p[1]
    global_parameters = p[2]
    list_node, list_hyperlink = p[3]
    p[0] = Program(list_node, global_param=global_parameters,
                   timescale=timehorizon, links=list_hyperlink)


def p_global(p):
    """global : GLOBAL define_parameters
              | empty"""

    # if global parameters have been defined
    if len(p) == 3:

        global_parameters = p[2]
        p[0] = global_parameters

    # else no global parameters
    else:

        p[0] = []


def p_time(p):
    """time : TIME ID EQUAL expr SEMICOLON
            | empty"""

    # if a timehorizon has been defined
    if len(p) == 6:

        time_identifier = p[2]
        time_expression = p[4]
        p[0] = Time(time_identifier, time_expression, line=p.lineno(2))

    # if no timehorizon definition
    else:

        # force the timehorizon to 1 and emit warning
        expr = Expression('literal', 1, line=p.lineno(1))
        p[0] = Time("T", expr)
        print("WARNING: No timescale was defined ! Default : T = 1")


def p_program(p):
    """program : node program
                | hyperlink program
                | empty"""

    # if input file is empty
    if p[1] is None:

        p[0] = [[], []]

    # elif the first element is a node
    elif type(p[1]) == Node:

        list_node, list_hyperlink = p[2]
        list_node.append(p[1])
        p[0] = [list_node, list_hyperlink]

    # elif the first element is a hyperedge
    elif type(p[1]) == Hyperedge:

        list_node, list_hyperlink = p[2]
        list_hyperlink.append(p[1])
        p[0] = [list_node, list_hyperlink]


def p_hyperlink(p):
    """hyperlink : HYPEREDGE ID parameters expressions_definitions constraints
                 | HYPEREDGE ID EQUAL IMPORT list_of_id FROM FILENAME with_name_parameter_redefinition """

    if len(p) == 6:
        link_identifier = p[2]
        list_parameters = p[3]
        list_expressions = p[4]
        list_constraints = p[5]
        h_link = Hyperedge(link_identifier, list_parameters, list_expressions,
                           list_constraints, line=p.lexer.lineno)
        p[0] = h_link

    elif len(p) == 9:
        # RENAME Hyperedge
        link_identifier = p[2]
        imported_node_identifier = p[5]
        filename = p[7]
        list_parameters_redefinitions, list_name_redefinitions = p[8]
        old_dir, cut_filename = move_to_directory(filename)
        graph_filename = parse_file(cut_filename)
        returned_hyperedge = graph_filename.get(imported_node_identifier)
        returned_hyperedge = deepcopy(returned_hyperedge)
        if returned_hyperedge is None:
            error_("ERROR: In file " + str(filename)
                   + " there is no hyperedge named "
                   + str(imported_node_identifier))
        if type(returned_hyperedge) == Node:
            error_("ERROR: A node is imported as type Hyperedge at line "
                   + str(p.lexer.lineno))
        returned_hyperedge.set_names_changes(list_name_redefinitions)
        returned_hyperedge.set_parameters_changes(list_parameters_redefinitions)
        returned_hyperedge.rename(link_identifier)
        os.chdir(old_dir)
        p[0] = returned_hyperedge


def p_with_name_parameter_redefinition(p):
    """with_name_parameter_redefinition : WITH name_parameter_redefinition
                              | empty"""
    if len(p) == 2:
        p[0] = [[], []]
    elif len(p) == 3:
        p[0] = p[2]


def p_node(p):
    """node : NODE ID parameters program variables expressions_definitions constraints objectives
            | NODE ID EQUAL IMPORT list_of_id FROM FILENAME with_redefine_parameters_variables"""

    if type(p[3]) == list:
        sub_nodes, sub_edges = p[4]
        list_parameters = p[3]
        list_variables = p[5]
        list_expressions = p[6]
        list_constraints = p[7]
        list_objectives = p[8]
        node_identifier = p[2]
        p[0] = Node(node_identifier)
        p[0].set_line(p.lexer.lineno)
        p[0].set_sub_nodes(sub_nodes)
        p[0].set_sub_hyperedges(sub_edges)
        p[0].update_internal_dict()
        p[0].set_parameters(list_parameters)
        p[0].set_variables(list_variables)
        p[0].set_constraints(list_constraints)
        p[0].set_objectives(list_objectives)
        p[0].set_expressions(list_expressions)

    elif type(p[3]) == str:

        node_identifier = p[2]
        imported_node_identifier = p[5]
        filename = p[7]
        list_parameters, list_variables = p[8]
        old_dir, cut_filename = move_to_directory(filename)
        graph_filename = parse_file(cut_filename)
        returned_node = graph_filename.get(imported_node_identifier)
        returned_node = deepcopy(returned_node)
        if returned_node is None:
            error_("ERROR: In file "+str(filename)+" there is no node named "
                   + str(imported_node_identifier) +
                   " at line "+str(p.lexer.lineno))
        if type(returned_node) == Hyperedge:
            error_("ERROR: A hyperedge is imported as type node at line "
                   + str(p.lexer.lineno))
        returned_node.set_parameters_changes(list_parameters)
        returned_node.set_variables_changes(list_variables)
        returned_node.rename(node_identifier)
        os.chdir(old_dir)
        p[0] = returned_node


def p_list_of_id(p):
    """list_of_id : ID DOT list_of_id
                  | ID"""
    identifier_name = p[1]
    if len(p) == 2:
        p[0] = [identifier_name]
    elif len(p) == 4:
        list_id = p[3]
        list_id.insert(0, identifier_name)
        p[0] = list_id


def p_with_redefine_parameters_variables(p):
    """with_redefine_parameters_variables : WITH redefine_parameters_variables
                                          | SEMICOLON"""
    if len(p) == 2:
        p[0] = [[], []]
    else:
        p[0] = p[2]


def p_name_parameter_redefinition(p):
    """name_parameter_redefinition : ID ASSIGN ID SEMICOLON name_parameter_redefinition
                                   | ID ASSIGN ID SEMICOLON
                                   | parameter name_parameter_redefinition
                                   | parameter"""
    if len(p) >= 5:
        lhs_id = p[1]
        rhs_id = p[3]
        redefinition = [lhs_id, rhs_id, p.lineno(1)]
        list_parameters = []
        list_node_name_redefinition = []
        if len(p) == 6:
            list_parameters, list_node_name_redefinition = p[5]
        list_node_name_redefinition.append(redefinition)
        p[0] = [list_parameters, list_node_name_redefinition]

    else:
        parameter = p[1]
        list_parameters = []
        list_node_name_redefinition = []
        if len(p) == 3:
            list_parameters, list_node_name_redefinition = p[2]
        list_parameters.append(parameter)
        p[0] = [list_parameters, list_node_name_redefinition]


def p_redefine_parameters_variables(p):
    """redefine_parameters_variables : parameter redefine_parameters_variables
                                     | ID external_internal SEMICOLON redefine_parameters_variables
                                     | parameter
                                     | ID external_internal SEMICOLON"""

    if len(p) == 2:
        parameter = p[1]
        list_parameters = [parameter]
        list_variables = []
        p[0] = [list_parameters, list_variables]
    elif len(p) == 3:
        parameter = p[1]
        list_parameters, list_variables = p[2]
        list_parameters.append(parameter)
        p[0] = [list_parameters, list_variables]
    elif len(p) == 4:
        variable_name = p[1]
        variable_type = p[2]
        list_parameters = []
        list_variables = [[variable_name, variable_type, p.lineno(1)]]
        p[0] = [list_parameters, list_variables]
    elif len(p) == 5:
        variable_name = p[1]
        variable_type = p[2]
        list_parameters, list_variables = p[2]
        list_variables.append([variable_name, variable_type, p.lineno(1)])
        p[0] = [list_parameters, list_variables]


def p_parameters(p):
    """parameters : PARAM define_parameters
                  | empty"""

    # if no parameter has been defined
    if len(p) == 2:

        p[0] = []

    # else parameters have been defined
    else:

        list_parameters = p[2]
        p[0] = list_parameters


def p_define_parameters(p):
    """define_parameters : parameter define_parameters
                         | empty"""

    # if no parameter has been defined
    if len(p) == 2:

        p[0] = []

    # else parameters have been defined
    else:

        p[2].insert(0, p[1])
        p[0] = p[2]


def p_parameter(p):
    """parameter : ID EQUAL expr SEMICOLON
                 | ID EQUAL LCBRAC expr more_values RCBRAC SEMICOLON
                 | ID EQUAL IMPORT FILENAME SEMICOLON"""

    parameter_id = p[1]

    # parameter defined by an expression
    if len(p) == 5:

        parameter_expression = p[3]
        p[0] = Parameter(parameter_id, parameter_expression, line=p.lineno(1))

    # parameter defined as a table
    elif len(p) == 8:

        list_values = p[5]
        last_value = p[4]
        p[0] = Parameter(parameter_id, None, line=p.lineno(1))
        list_values.insert(0, last_value)
        p[0].set_vector(list_values)

    # parameter defined via an import
    else:

        filename = p[4]
        p[0] = Parameter(parameter_id, filename, line=p.lineno(1))


def p_more_values(p):
    """more_values : COMMA expr more_values
                    | empty"""

    # if no more values are used
    if len(p) == 2:

        p[0] = []

    # add additional value
    else:
        list_values = p[3]
        additional_value = p[2]
        list_values.insert(0, additional_value)
        p[0] = list_values


def p_variables(p):
    """variables : VAR define_variables"""

    p[0] = p[2]


def p_define_variables(p):
    """define_variables : external_internal type_var option_var COLON id SEMICOLON var_aux
                        | external_internal type_var option_var COLON id ASSIGN id SEMICOLON var_aux"""

    identifier_option = p[2]
    var_identifier = p[5]
    var_type = p[3]
    internal_external_keyword = p[1]

    # variable definition without assignment
    if len(p) == 8:
        list_variables = p[7]
        var_identifier.set_option(identifier_option)
        var = Variable(var_identifier, internal_external_keyword,
                       v_option=var_type, line=p.lineno(1))
        list_variables.insert(0, var)
        p[0] = list_variables

    # variable definition with assignment
    elif len(p) == 10:
        list_variables = p[9]
        child_variable = p[7]
        var_identifier.set_option(identifier_option)
        var = Variable(var_identifier, internal_external_keyword,
                       v_option=var_type, child_variable=child_variable,
                       line=p.lineno(1))
        list_variables.insert(0, var)
        p[0] = list_variables


def p_external_internal(p):
    """external_internal : INTERNAL
                         | EXTERNAL"""
    p[0] = p[1]


def p_type_var(p):
    """type_var : BINARY
                | CONTINUOUS
                | INTEGER
                | empty"""

    if p[1] is None:

        p[1] = "continuous"
    p[0] = p[1]


def p_option_var(p):
    """option_var : AUX
                  | ACTION
                  | SIZING
                  | STATE
                  | empty"""
    if p[1] is None:

        p[1] = "auxiliary"
    p[0] = p[1]


def p_var_aux(p):
    """var_aux :  define_variables
                | empty"""

    # case empty
    if p[1] is None:

        p[0] = []

    # case where more variables are defined
    else:

        p[0] = p[1]


def p_expressions_definition(p):
    """expressions_definitions : EXPRESSION expression_declaration expression_declaration_aux
                                | empty"""

    # empty case
    if len(p) == 2:
        p[0] = []

    # definition case
    else:
        list_expressions = p[3]
        additional_expression = p[2]
        list_expressions.insert(0, additional_expression)
        p[0] = list_expressions


def p_expression_declaration(p):
    """expression_declaration : ID EQUAL expr SEMICOLON"""
    p[0] = [p[1], p[3], p.lineno(1)]


def p_expression_declaration_aux(p):
    """expression_declaration_aux : expression_declaration expression_declaration_aux
                                  | empty"""
    if len(p) == 2:
        p[0] = []

    elif len(p) == 3:
        list_expressions = p[2]
        additional_expression = p[1]
        list_expressions.insert(0, additional_expression)
        p[0] = list_expressions


def p_constraints(p):
    """constraints : CONS constraints_aux
                   | empty"""
    # empty case
    if len(p) == 2:

        p[0] = []

    # definition case
    else:

        p[0] = p[2]


def p_constraints_aux(p):
    """constraints_aux : ID COLON define_constraints SEMICOLON constraints_aux
                       | ID COLON define_constraints SEMICOLON
                       | define_constraints SEMICOLON constraints_aux
                       | define_constraints SEMICOLON"""

    # last unnamed constraint definition
    if len(p) == 3:

        p[0] = []
        p[0].append(p[1])

    # add one unnamed constraint
    elif len(p) == 4:

        p[3].insert(0, p[1])
        p[0] = p[3]

    # last named constraint
    elif len(p) == 5:
        p[3].set_name(p[1])
        p[0] = []
        p[0].append(p[3])

    # add named constraint
    elif len(p) == 6:
        p[3].set_name(p[1])
        p[5].insert(0, p[3])
        p[0] = p[5]


def p_define_constraints(p):
    """define_constraints : expr DOUBLE_EQ expr time_loop condition
                          | expr LEQ expr time_loop condition
                          | expr BEQ expr time_loop condition"""

    # define a general constraint
    p[0] = Constraint(p[2], p[1], p[3], time_interval=p[4],
                      condition=p[5], line=p.lineno(2))


def p_condition(p):
    """condition : WHERE bool_condition
                 | empty"""

    # not empty case
    if len(p) == 3:

        p[0] = p[2]


def p_bool_condition(p):
    """bool_condition : bool_condition AND bool_condition
                      | NOT bool_condition
                      | bool_condition OR bool_condition
                      | LPAR bool_condition RPAR
                      | expr DOUBLE_EQ expr
                      | expr NEQ expr
                      | expr LOWER expr
                      | expr BIGGER expr
                      | expr LEQ expr 
                      | expr BEQ expr"""

    # AND OR PAR DOUBLE_EQ NEQ LOWER BIGGER LEQ BEQ cases
    if len(p) == 4:
        # AND OR DOUBLE_EQ NEQ LOWER BIGGER LEQ BEQ cases
        if type(p[2]) == str:

            children = [p[1], p[3]]
            p[0] = Condition(p[2], children, line=p.lineno(2))
        # PAR case
        else:

            p[0] = p[2]

    # NOT case
    else:

        p[0] = Condition(p[1], [p[2]], line=p.lineno(1))


def p_time_loop(p):
    """time_loop : FOR ID IN LBRAC expr COLON expr COLON expr RBRAC
                 | FOR ID IN LBRAC expr COLON expr RBRAC
                 | empty"""

    if len(p) == 11:

        p[0] = TimeInterval(p[2], p[5], p[9], p[7], p.lineno(2))
    elif len(p) == 9:
        step = Expression('literal', 1)
        p[0] = TimeInterval(p[2], p[5], p[7], step, p.lineno(2))


def p_objectives(p):

    """objectives : OBJ define_objectives
                  | empty"""

    if p[1] is None:

        p[0] = []
    else:

        p[0] = p[2]


def p_define_objectives(p):
    """define_objectives : MIN ID COLON expr time_loop condition SEMICOLON obj_aux
                         | MAX ID COLON expr time_loop condition SEMICOLON obj_aux
                         | MIN COLON expr time_loop condition SEMICOLON obj_aux
                         | MAX COLON expr time_loop condition SEMICOLON obj_aux"""

    if len(p) == 8:
        obj = Objective(p[1], p[3], p[4], p[5], line=p.lineno(1), name=None)
        p[7].insert(0, obj)
        p[0] = p[7]
    elif len(p) == 9:
        obj = Objective(p[1], p[4], p[5], p[6], line=p.lineno(1), name=p[2])
        p[8].insert(0, obj)
        p[0] = p[8]


def p_obj_aux(p):
    """obj_aux : define_objectives
               | empty"""

    if p[1] is None:

        p[0] = []
    else:

        p[0] = p[1]


def p_id(p):
    """id : ID
          | ID DOT ID
          | ID LBRAC expr RBRAC
          | ID DOT ID LBRAC expr RBRAC"""

    if len(p) == 2:
        # Rule ID
        p[0] = Identifier('basic', p[1], line=p.lineno(1))

    elif len(p) == 4:

        # Rule ID DOT ID
        p[0] = Identifier('basic', p[3], node_name=p[1], line=p.lineno(1))

    elif len(p) == 5:

        # Rule ID LBRAC expr RBRAC
        p[0] = Identifier('assign', p[1], expression=p[3], line=p.lineno(1))

    elif len(p) == 7:

        # Rule ID DOT ID LBRAC expr RBRAC
        p[0] = Identifier('assign', p[3], node_name=p[1], expression=p[5],
                          line=p.lineno(1))


def p_expr(p):
    """expr : expr PLUS expr %prec PLUS
            | expr MINUS expr %prec MINUS
            | expr MULT expr %prec MULT
            | expr DIVIDE expr %prec DIVIDE
            | MINUS expr %prec UMINUS
            | expr POW expr %prec POW
            | LPAR expr RPAR
            | MOD LPAR expr COMMA expr RPAR
            | SUM LPAR expr time_loop condition RPAR
            | term"""

    if len(p) == 4:
        
        # CASES + - * / ^ ()
        if type(p[2]) == str:

            p[0] = Expression(p[2], line=p.lineno(2))
            p[0].add_child(p[1])
            p[0].add_child(p[3])
        else:

            # ()
            p[0] = p[2]
    
    elif len(p) == 3:

        # CASE u-
        p[0] = Expression('u-', line=p.lineno(1))
        p[0].add_child(p[2])
    
    elif len(p) == 7:
        
        # CASE MODULO
        if p[1] == "mod":
            p[0] = Expression(p[1], line=p.lineno(1))
            p[0].add_child(p[3])
            p[0].add_child(p[5])

        if p[1] == "sum":
            # CASE SUM
            p[0] = Expression('sum', line=p.lineno(1))
            p[0].add_child(p[3])
            p[0].set_time_interval(p[4])
            p[0].set_condition(p[5])
    
    elif len(p) == 2:

        # CASE term
        p[0] = p[1]
    

def p_term(p):
    """term : INT
            | FLOAT
            | id"""

    p[0] = Expression('literal', p[1], line=p.lineno(1))
    if type(p[1]) == Identifier:
        p[0].set_line(p[1].get_line())


def p_empty(p):
    """empty :"""

    pass


# Error rule for syntax errors

def p_error(p):

    if p is not None:

        print('Syntax error: %d:%d: Unexpected token %s namely (%s)'
              % (p.lineno, find_column(p.lexer.lexdata, p),
                 p.type, str(p.value)))
    else:
        print('Syntax error: Expected a certain token got EOF(End Of File)')
    exit(-1)


def find_column(input_string, p):

    line_start = input_string.rfind('\n', 0, p.lexpos) + 1
    return p.lexpos - line_start + 1


def parse_file(name: str, cache=True) -> Program:
    """ parse_file

        takes as input a filename and converts it into a Program structure
        containing all the information

        Args:
            name (str) -> filename
            cache (bool) -> predicate whether to cache the imported nodes or not

        Returns:
            program -> program object containing all the information of the file

        Notes:
            When caching as only the filename is mapped to a program, conflicts
            can arise if a same filename is shared
            between two different files (on different paths typically)

    """
    # Build the parser
    global list_opened_files
    global cache_graph

    parser = yacc.yacc()
    check_file_exists(name)

    with open(name, 'r') as content:

        data = content.read()

    if name in list_opened_files:
        error_("ERROR: File "+str(name)
               + " has already been visited, there are loops in the import \n"
               + str(list_opened_files))

    if name in cache_graph and cache:
        return cache_graph[name]
    else:
        list_opened_files.append(name)
    # result = True

    result = parser.parse(data, lexer=lexer.clone())

    list_opened_files.pop(-1)

    cache_graph[name] = result

    return result
