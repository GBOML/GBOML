
# lexer.py
#
# Writer : MIFTARI B
# ------------

import ply.lex as lex


def tokenize(data):
    """
    Tokenize input data to stdout for testing purposes.
    """
    global lexer 
    lexer.input(data)
    while True:
        tok = lexer.token()
        if not tok:
            break
        print(tok)
    lexer = lex.lex()


def tokenize_file(filepath):
    """
    Tokenize input file to stdout for testing purposes.
    :param fspec: Input file to parse.
    """
    with open(filepath, "r") as content:
        data = content.read()
    return tokenize(data)

def find_column(input,token):
    line_start = input.rfind('\n', 0, token.lexpos) + 1
    return (token.lexpos - line_start) + 1

keywords = {
    'min':'MIN',
    'max':'MAX',
    'input':'INPUT',
    'output':'OUTPUT',
    'internal':'INTERNAL',
    'in':'IN',
    'horizon':'HORIZON',
    'step':'STEP'
}

reserved = {
   '#NODE':'NODE',
   '#PARAMETERS':'PARAM',
   '#CONSTRAINTS':'CONS',
   '#VARIABLES':'VAR',
   '#OBJECTIVES':'OBJ',
   '#TIMESCALE':'TIME',
   '#LINKS':'LINKS'
}

# List of token names.   This is always required
tokens = (
'INT',
'PLUS',
'MINUS',
'POW',
'MULT',
'DIVIDE',
'LPAR',
'RPAR',
'FLOAT',
'ID',
'COMMA',
'LCBRAC',
'RCBRAC',
'LBRAC',
'RBRAC',
'EQUAL',
'LEQ',
'BEQ',
'COLON',
'LOW',
'BIG',
'NAME',
'DOT'
)+tuple(keywords.values())+tuple(reserved.values())

# Regular expression rules for simple tokens
t_PLUS    = r'\+'
t_MINUS   = r'-'
t_COMMA   = r'\,'
t_LCBRAC  = r'\{'
t_RCBRAC  = r'\}'
t_LBRAC   = r'\['
t_RBRAC   = r'\]'
t_POW     = r'\*\*'
t_MULT   = r'\*'
t_DIVIDE  = r'/'
t_LPAR    = r'\('
t_RPAR    = r'\)'
t_EQUAL   = r'\='
t_LEQ     = r'\<\='
t_BEQ     = r'\>\='
t_COLON   = r'\:'
t_LOW     = r'\<'
t_BIG     = r'\>'
t_DOT     = r'\.'

def t_ID(t):
    r'[a-z][a-zA-Z_0-9]*'
    if t.value in keywords:
        t.type =  keywords.get(t.value,'ID') 
    return t

def t_reserved(t):
    r'[#][A-Z]+'
    if t.value in reserved:
        t.type =  reserved.get(t.value,'ID') 
        return t
    else:
        t_error(t)

def t_NAME(t):
    r'[A-Z][a-zA-Z_0-9]*'
    return t

def t_COMMENT(t):
     r'[/][/].*'
     pass
     # No return value. Token discarded

# A regular expression rule with some action code

def t_FLOAT(t):
    r'[0-9]+[\.][0-9]*'
    t.value = float(t.value)    
    return t

def t_INT(t):
    r'[0-9]+'
    t.value = int(t.value)
    return t

# Define a rule so we can track line numbers
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# A string containing ignored characters (spaces and tabs)
t_ignore  = ' \t\r\f'

# Error handling rule
def t_error(t):
    if not p:
        print("End of File!")
        return
    print('Lexing error:'+str(t.lineno)+':'+str(find_column(lexer.lexdata,t))+":Illegal character '%s'" % t.value[0])
    exit(-1)
    
lexer = lex.lex()

#tokenize_file("text.txt")
