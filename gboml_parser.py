
# Myparser.py
#
# Writer : MIFTARI B
# ------------

import ply.yacc as yacc
from gboml_lexer import tokens
from classes import Time, Expression, Variable, Parameter, Link, \
    Attribute, Program, Objective, Node, Identifier, Constraint, \
    Condition, TimeInterval

# precendence rules from least to most priority with associativity also specified

precedence = (  # Unary minus operator
    ('left', 'OR'),
    ('left', 'AND'),
    ('right', 'NOT'),
    ('nonassoc','EQUAL','LEQ','BEQ','BIGGER','LOWER','NEQ'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'MULT', 'DIVIDE'),
    ('right', 'UMINUS'),
    ('left', 'POW'),
    )


# Start symbol

def p_start(p):
    '''start : time program links'''

    p[0] = Program(p[2], p[1], p[3])


    # exit()

def p_time(p):
    '''time : TIME ID EQUAL expr
            | empty'''

    if len(p) == 5:
        p[0] = Time(p[2], p[4], line=p.lineno(2))
    else : 
        expr = Expression('literal', 1, line=p.lineno(1))
        p[0] = Time("T", expr)
        print("WARNING: No timescale was defined ! Default : T = 1")


def p_links(p):
    '''links : LINKS link_def link_aux
             | empty'''

    if len(p) > 2:
        p[3].append(p[2])
        p[0] = p[3]
    else:
        p[0] = []


def p_link_def(p):
    '''link_def : ID EQUAL ID more_id
                | ID DOT ID EQUAL ID DOT ID more_id_aux'''

    if len(p) == 5:
        rhs = Attribute(p[1])
        a = Attribute(p[3])
        p[4].append(a)
        p[0] = Link(rhs, p[4])
    else:
        rhs = Attribute(p[1], p[3])
        a = Attribute(p[5], p[7])
        p[8].append(a)
        p[0] = Link(rhs, p[8])


def p_more_id_aux(p):
    '''more_id_aux : COMMA ID DOT ID more_id_aux
                   | empty'''

    if len(p) == 2:
        p[0] = []
    else:
        a = Attribute(p[2], p[4])
        p[5].append(a)
        p[0] = p[5]


def p_more_id(p):
    '''more_id : COMMA ID more_id
               | empty'''

    if len(p) == 2:
        p[0] = []
    else:
        a = Attribute(p[2])
        p[3].append(a)
        p[0] = p[3]


def p_link_aux(p):
    '''link_aux : link_def link_aux
                | empty'''

    if len(p) == 2:
        p[0] = []
    else:
        p[2].append(p[1])
        p[0] = p[2]


def p_program(p):
    '''program : node program
                | empty '''

    if p[1] == None:
        p[0] = []
    else:
        p[2].append(p[1])
        p[0] = p[2]


def p_node(p):
    '''node : NODE ID parameters variables constraints objectives'''

    p[0] = Node(p[2])
    p[0].set_line(p.lexer.lineno)
    p[0].set_parameters(p[3])
    p[0].set_variables(p[4])
    p[0].set_constraints(p[5])
    p[0].set_objectives(p[6])


def p_parameters(p):
    '''parameters : PARAM define_parameters
                  | empty'''

    if len(p) == 2:
        p[0] = []
    else:
        p[0] = p[2]


def p_define_parameters(p):
    '''define_parameters : parameter define_parameters
                         | empty'''

    if len(p) == 2:
        p[0] = []
    else:
        p[2].insert(0, p[1])
        p[0] = p[2]


def p_parameter(p):
    '''parameter : ID EQUAL expr SEMICOLON
                 | ID EQUAL LCBRAC term more_values RCBRAC SEMICOLON
                 | ID EQUAL IMPORT FILENAME SEMICOLON'''

    if len(p) == 5:
        p[0] = Parameter(p[1], p[3], line=p.lineno(1))
    elif len(p) == 8:
        p[0] = Parameter(p[1], None, line=p.lineno(1))
        p[5].insert(0, p[4])
        p[0].set_vector(p[5])
    else:
        p[0] = Parameter(p[1], p[4], line=p.lineno(1))


def p_more_values(p):
    '''more_values : COMMA term more_values
                    | empty'''

    if len(p) == 2:
        p[0] = []
    else:
        p[3].insert(0, p[2])
        p[0] = p[3]


def p_variables(p):
    '''variables : VAR define_variables'''

    p[0] = p[2]


def p_define_variables(p):
    '''define_variables : INTERNAL COLON id var_aux
                        | OUTPUT COLON id var_aux
                        | INPUT COLON id var_aux'''

    var = Variable(p[3], p[1], line=p.lineno(1))
    p[4].insert(0, var)
    p[0] = p[4]


def p_var_aux(p):
    '''var_aux :  define_variables
                | empty'''

    if p[1] == None:
        p[0] = []
    else:
        p[0] = p[1]


def p_constraints(p):
    '''constraints : CONS constraints_aux
                   | empty'''

    if len(p) == 2:
        p[0] = []
    else:
        p[0] = p[2]


def p_constraints_aux(p):
    '''constraints_aux : define_constraints SEMICOLON constraints_aux
                       | define_constraints SEMICOLON
                       | define_constraints'''

    if len(p) == 2 or len(p) == 3:
        p[0] = []
        p[0].append(p[1])
    else:
        p[3].insert(0, p[1])
        p[0] = p[3]


def p_define_constraints(p):
    '''define_constraints : expr EQUAL expr time_loop condition
                          | expr LEQ expr time_loop condition
                          | expr BEQ expr time_loop condition'''

    p[0] = Constraint(
        p[2],
        p[1],
        p[3],
        time_interval=p[4],
        condition=p[5],
        line=p.lineno(2),
        )


def p_condition(p):
    '''condition : WHERE bool_condition
                 | empty'''

    if len(p) == 3:
        p[0] = p[2]


def p_bool_condition(p):
    '''bool_condition : bool_condition AND bool_condition
                      | NOT bool_condition
                      | bool_condition OR bool_condition
                      | LPAR bool_condition RPAR
                      | expr DOUBLE_EQ expr
                      | expr NEQ expr
                      | expr LOWER expr
                      | expr BIGGER expr
                      | expr LEQ expr 
                      | expr BEQ expr'''

    if len(p) == 4:
        if type(p[2]) == str:
            children = [p[1], p[3]]
            p[0] = Condition(p[2], children, line=p.lineno(2))
        else:
            p[0] = p[2]
    else:
        p[0] = Condition(p[1], [p[2]], line=p.lineno(1))


def p_time_loop(p):
    '''time_loop : FOR ID IN LBRAC expr COLON expr COLON expr RBRAC
                 | FOR ID IN LBRAC expr COLON expr RBRAC
                 | empty'''

    if len(p) == 11:
        p[0] = TimeInterval(p[2], p[5], p[9], p[7], p.lineno(2))
    elif len(p) == 9:
        p[0] = TimeInterval(p[2], p[5], p[7], 1, p.lineno(2))


def p_objectives(p):
    '''objectives : OBJ define_objectives
                  | empty'''

    if p[1] == None:
        p[0] = []
    else:
        p[0] = p[2]


def p_define_objectives(p):
    '''define_objectives : MIN COLON expr obj_aux
                         | MAX COLON expr obj_aux'''

    obj = Objective(p[1], p[3], line=p.lineno(1))
    p[4].append(obj)
    p[0] = p[4]


def p_obj_aux(p):
    '''obj_aux : define_objectives 
               | empty'''

    if p[1] == None:
        p[0] = []
    else:
        p[0] = p[1]


def p_id(p):
    '''id : ID LBRAC expr RBRAC
          | ID'''

    if len(p) == 2:
        p[0] = Identifier('basic', p[1], line=p.lineno(1))
    elif len(p) == 5:
        p[0] = Identifier('assign', p[1], expression=p[3],
                          line=p.lineno(1))


def p_expr(p):
    '''expr : expr PLUS expr %prec PLUS
            | expr MINUS expr %prec MINUS
            | expr MULT expr %prec MULT
            | expr DIVIDE expr %prec DIVIDE
            | MINUS expr %prec UMINUS
            | expr POW expr %prec POW
            | LPAR expr RPAR
            | MOD LPAR expr COMMA expr RPAR
            | term'''

    if len(p) == 4:
        if type(p[2]) == str:
            p[0] = Expression(p[2],line = p.lineno(2))
            p[0].add_child(p[1])
            p[0].add_child(p[3])
        else:
            p[0] = p[2]
    elif len(p) == 3:

        p[0] = Expression('u-',line = p.lineno(1))
        p[0].add_child(p[2])
    elif len(p) == 7:

        p[0] = Expression(p[1],line = p.lineno(1))
        p[0].add_child(p[3])
        p[0].add_child(p[5])
    else:

        p[0] = p[1]


def p_term(p):
    '''term : INT
            | FLOAT
            | id'''

    p[0] = Expression('literal', p[1], line=p.lineno(1))
    if type(p[1]) == Identifier:
        p[0].set_line(p[1].get_line())


def p_empty(p):
    '''empty :'''

    pass


# Error rule for syntax errors

def p_error(p):

    if p != None:
        print('Syntax error:' + str(p.lineno) + ':' \
            + str(find_column(p.lexer.lexdata, p)) \
            + ': Unexpected token ' + str(p.type) + ' namely(' \
            + str(p.value) + ')')
    else:

        print('Syntax error: Expected a certain token got EOF(End Of File)')
    exit(-1)


def find_column(input, p):
    line_start = input.rfind('\n', 0, p.lexpos) + 1
    return p.lexpos - line_start + 1


def parse_file(name):

    # Build the parser

    parser = yacc.yacc()

    with open(name, 'r') as content:
        data = content.read()

    # result = True

    result = parser.parse(data)
    return result
