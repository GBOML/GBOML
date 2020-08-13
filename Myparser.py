# Yacc example

import ply.yacc as yacc

# Get the token map from the lexer. This is required.
from lexer import tokens
from classes import *

precedence = (
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE'),
    ('right', 'UMINUS'), 
    ('left','POW'),         # Unary minus operator
)

def p_start(p):
    '''start : time program'''
    p[0]=Program(p[2],p[1])

def p_time(p):
    '''time : TIME time_def step_def
            | TIME step_def time_def
            | empty'''
    if len(p)> 2:
        if p[2][0]=="horizon":
            p[0]=Time(p[2][1],p[3][1])
        else:
            p[0]=Time(p[3][1],p[2][1])


def p_time_def(p):
    '''time_def : HORIZON COLON INT'''
    type_value = []
    type_value.append(p[1])
    type_value.append(p[3])
    p[0]=type_value

def p_step_def(p):
    '''step_def : STEP COLON INT'''
    type_value = []
    type_value.append(p[1])
    type_value.append(p[3])
    p[0]=type_value


def p_program(p):
    '''program : node program
                | empty '''
    if p[1]==None:
        p[0]=Vector()
    else:
        p[2].add_element(p[1])
        p[0]=p[2]

def p_node(p):
    '''node : NODE NAME parameters variables constraints objectives'''
    p[0]=Node(p[2])
    print(p.lexpos(2))
    p[0].set_line(p.lexer.lineno)
    p[0].set_parameters(p[3])
    p[0].set_variables(p[4])
    p[0].set_constraints(p[5])
    p[0].set_objectives(p[6])

def p_empty(p):
    'empty :'
    pass

def p_parameters(p):
    '''parameters : PARAM define_parameters'''
    p[0] = p[2]

def p_define_parameters(p):
    '''define_parameters : parameter define_parameters
                         | empty'''
    if len(p)==2:
        p[0]=Vector()
    else : 
        p[2].add_begin(p[1])
        p[0]=p[2]

def p_parameter(p):
    '''parameter : id unity EQUAL expr
                 | id unity EQUAL LCBRAC term more_values RCBRAC'''
    if len(p) == 5:
        p[0]=Parameter(p[1],p[4],p[2],line = p.lexer.lineno)
    else:
        p[0]=Parameter(p[1],None,line = p.lexer.lineno)
        p[6].add_begin(p[5])
        p[0].set_value(p[6])

def p_more_values(p):
    '''more_values : COMMA term more_values
                    | empty'''
    if len(p)==2:
        p[0]=Vector()
    else:
        p[0].add_begin(p[2])

def p_variables(p):
    '''variables : VAR define_variables'''
    p[0]=p[2]

def p_define_variables(p):
    '''define_variables : INTERNAL COLON id unity var_aux
                        | OUTPUT COLON id unity var_aux
                        | INPUT COLON id unity var_aux'''
    var = Variable(p[3],p[1],p[4],line = p.lexer.lineno)
    p[5].add_begin(var)
    p[0]=p[5]

def p_var_aux(p):
    '''var_aux :  define_variables
                | empty'''
    if p[1]==None:
        p[0]=Vector()
    else: 
        p[0]=p[1]

def p_constraints(p):
    '''constraints : CONS define_constraints '''
    p[0]=p[2]

def p_define_constraints(p):
    '''define_constraints : id EQUAL expr cons_aux
                          | id LEQ expr cons_aux
                          | id BEQ expr cons_aux
                          | id LOW expr cons_aux
                          | id BIG expr cons_aux'''
    cons = Constraint(p[2],p[1],p[3],line = p.lexer.lineno)
    p[4].add_begin(cons)
    p[0]=p[4]

def p_cons_aux(p):
    '''cons_aux : define_constraints
                | empty'''
    if p[1]==None:
        p[0]=Vector()
    else:
        p[0]=p[1]

def p_objectives(p):
    '''objectives : OBJ define_objectives
                  | empty'''
    if p[1]==None:
        p[0]=Vector()
    else:
        p[0]=p[2]


def p_define_objectives(p):
    '''define_objectives : MIN COLON expr obj_aux
                         | MAX COLON expr obj_aux'''
    obj = Objective(p[1],p[3],line = p.lexer.lineno)
    p[4].add_begin(obj)
    p[0]=p[4]

def p_obj_aux(p):
    '''obj_aux : define_objectives 
               | empty'''
    if p[1]==None:
        p[0]=Vector()
    else : 
        p[0]=p[1]

def p_id(p):
    '''id : ID LBRAC expr RBRAC
          | ID'''
    p[0] = p[1]

def p_expr(p):
    '''expr : expr PLUS expr %prec PLUS
            | expr MINUS expr %prec MINUS
            | expr TIMES expr %prec TIMES
            | expr DIVIDE expr %prec DIVIDE
            | MINUS expr %prec UMINUS
            | expr POW expr %prec POW
            | LPAR expr RPAR
            | term'''
    if len(p)==4:
        if type(p[2])== str:
            p[0]=Expression(p[2])
            p[0].add_child(p[1])
            p[0].add_child(p[3])
        else:
            p[0]=p[2]
    elif len(p)==3:
        p[0]=Expression('u-')
        p[0].add_child(p[1])
    else:
        p[0]=p[1]

def p_factor(p):
    '''term : INT
            | FLOAT
            | id'''
    p[0]=Expression('literal',p[1],line = p.lexer.lineno)

def p_unity(p):
    '''unity : IN expr
             | empty'''
    if p[1]!=None:
        p[0]=Expression('unity')
        p[0].add_child(p[2])
    else:
        p[0]=None

# Error rule for syntax errors
def p_error(p):
    if p != None:
        token = f"{p.type} namely ({p.value}) on line {p.lineno}"
        print(f"Syntax error: Unexpected token {token}")
    else : 
        print("Expected a certain token got nothing")
    exit(-1)


def parse_file(name):
    # Build the parser
    parser = yacc.yacc()

    with open(name, "r") as content:
        data = content.read()

    #result = True
    result = parser.parse(data)
    return result

#parse_file("text.txt")

"""
parser = yacc.yacc()

with open(name, "r") as content:
    data = content.read()

#result = True
result = parser.parse(data)
print(result)
"""