

# gboml_parser.py
#
# Part of the GBOML Project
# University of Liege
# Writer : MIFTARI B
# ------------

import ply.yacc as yacc  # type: ignore

from .gboml_lexer import tokens

from .classes import Time, Expression, Variable, Parameter, Program, Objective, Node, Identifier, \
    Constraint, Condition, TimeInterval, Hyperlink

# precedence rules from least to highest priority with associativity also specified

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

    list_node, list_hyperlink = p[3]
    p[0] = Program(list_node, global_param=p[2], timescale=p[1], links=list_hyperlink)


def p_global(p):
    """global : GLOBAL define_parameters
              | empty"""

    if len(p) == 3:

        p[0] = p[2]
    else:

        p[0] = []


def p_time(p):
    """time : TIME ID EQUAL expr SEMICOLON
            | empty"""

    if len(p) == 6:

        p[0] = Time(p[2], p[4], line=p.lineno(2))
    else:

        expr = Expression('literal', 1, line=p.lineno(1))
        p[0] = Time("T", expr)
        print("WARNING: No timescale was defined ! Default : T = 1")


def p_program(p):

    """program : node program
                | hyperlink program
                | empty"""

    if p[1] is None:

        p[0] = [[], []]
    if type(p[1]) == Node:

        list_node, list_hyperlink = p[2]
        list_node.append(p[1])
        p[0] = [list_node, list_hyperlink]
    elif type(p[1]) == Hyperlink:

        list_node, list_hyperlink = p[2]
        list_hyperlink.append(p[1])
        p[0] = [list_node, list_hyperlink]


def p_hyperlink(p):
    """hyperlink : HYPEREDGE ID parameters constraints"""

    h_link = Hyperlink(p[2], p[3], p[4], line=p.lexer.lineno)
    p[0] = h_link


def p_node(p):
    """node : NODE ID parameters variables constraints objectives"""

    p[0] = Node(p[2])
    p[0].set_line(p.lexer.lineno)
    p[0].set_parameters(p[3])
    p[0].set_variables(p[4])
    p[0].set_constraints(p[5])
    p[0].set_objectives(p[6])


def p_parameters(p):
    """parameters : PARAM define_parameters
                  | empty"""

    if len(p) == 2:

        p[0] = []
    else:

        p[0] = p[2]


def p_define_parameters(p):
    """define_parameters : parameter define_parameters
                         | empty"""

    if len(p) == 2:

        p[0] = []
    else:

        p[2].insert(0, p[1])
        p[0] = p[2]


def p_parameter(p):
    """parameter : ID EQUAL expr SEMICOLON
                 | ID EQUAL LCBRAC term more_values RCBRAC SEMICOLON
                 | ID EQUAL IMPORT FILENAME SEMICOLON"""

    if len(p) == 5:

        p[0] = Parameter(p[1], p[3], line=p.lineno(1))
    elif len(p) == 8:

        p[0] = Parameter(p[1], None, line=p.lineno(1))
        p[5].insert(0, p[4])
        p[0].set_vector(p[5])
    else:

        p[0] = Parameter(p[1], p[4], line=p.lineno(1))


def p_more_values(p):
    """more_values : COMMA term more_values
                    | empty"""

    if len(p) == 2:

        p[0] = []
    else:

        p[3].insert(0, p[2])
        p[0] = p[3]


def p_variables(p):
    """variables : VAR define_variables"""

    p[0] = p[2]


def p_define_variables(p):
    """define_variables : INTERNAL type_var option_var COLON id SEMICOLON var_aux
                        | EXTERNAL type_var option_var COLON id SEMICOLON var_aux"""

    p[5].set_option(p[2])
    var = Variable(p[5], p[1], v_option=p[3], line=p.lineno(1))
    p[7].insert(0, var)
    p[0] = p[7]


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

    if p[1] is None:

        p[0] = []
    else:

        p[0] = p[1]


def p_constraints(p):
    """constraints : CONS constraints_aux
                   | empty"""

    if len(p) == 2:

        p[0] = []
    else:

        p[0] = p[2]


def p_constraints_aux(p):
    """constraints_aux : define_constraints SEMICOLON constraints_aux
                       | define_constraints SEMICOLON"""

    if len(p) == 3:

        p[0] = []
        p[0].append(p[1])
    else:

        p[3].insert(0, p[1])
        p[0] = p[3]


def p_define_constraints(p):
    """define_constraints : expr DOUBLE_EQ expr time_loop condition
                          | expr LEQ expr time_loop condition
                          | expr BEQ expr time_loop condition"""

    p[0] = Constraint(p[2], p[1], p[3], time_interval=p[4], condition=p[5], line=p.lineno(2))


def p_condition(p):
    """condition : WHERE bool_condition
                 | empty"""

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

    if len(p) == 4:

        if type(p[2]) == str:

            children = [p[1], p[3]]
            p[0] = Condition(p[2], children, line=p.lineno(2))
        else:

            p[0] = p[2]
    else:

        p[0] = Condition(p[1], [p[2]], line=p.lineno(1))


def p_time_loop(p):
    """time_loop : FOR ID IN LBRAC expr COLON expr COLON expr RBRAC
                 | FOR ID IN LBRAC expr COLON expr RBRAC
                 | empty"""

    if len(p) == 11:

        p[0] = TimeInterval(p[2], p[5], p[9], p[7], p.lineno(2))
    elif len(p) == 9:

        p[0] = TimeInterval(p[2], p[5], p[7], 1, p.lineno(2))


def p_objectives(p):

    """objectives : OBJ define_objectives
                  | empty"""

    if p[1] is None:

        p[0] = []
    else:

        p[0] = p[2]


def p_define_objectives(p):
    """define_objectives : MIN COLON expr time_loop condition SEMICOLON obj_aux
                         | MAX COLON expr time_loop condition SEMICOLON obj_aux"""

    obj = Objective(p[1], p[3], p[4], p[5], line=p.lineno(1))
    p[7].insert(0, obj)
    p[0] = p[7]


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
        p[0] = Identifier('assign', p[3], node_name=p[1], expression=p[5], line=p.lineno(1))


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

        print('Syntax error: %d:%d: Unexpected token %s namely (%s)' % (p.lineno, find_column(p.lexer.lexdata, p),
                                                                        p.type, str(p.value)))
    else:

        print('Syntax error: Expected a certain token got EOF(End Of File)')
    exit(-1)


def find_column(input_string, p):

    line_start = input_string.rfind('\n', 0, p.lexpos) + 1
    return p.lexpos - line_start + 1


def parse_file(name: str) -> Program:

    # Build the parser

    parser = yacc.yacc()

    with open(name, 'r') as content:

        data = content.read()

    # result = True

    result = parser.parse(data)
    return result
