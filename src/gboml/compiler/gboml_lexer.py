# Copyright (C) 2020 - 2022
# Bardhyl Miftari, Mathias Berger, Hatim Djelassi, Damien Ernst,
# University of Liege .
# Licensed under the MIT License (see LICENSE file).

"""GBOML lexer file

Defines the tokens of the GBOML language

  Typical usage example:

  tokenize(gboml_file)
  where:
    gboml_file is the file we want to convert to tokens

"""

from .ply import lex  # type: ignore
import re


def tokenize(data: str) -> None:
    """tokenize

        takes as input a string and prints it as a stream of tokens

        Args:
            data(str) -> string containing the data to be tokenized

        Returns:

    """

    global lexer
    lexer.input(data)
    while True:
        tok = lexer.token()
        if not tok:
            break
        print(tok)
    lexer = lex.lex()


def tokenize_file(filepath: str) -> None:
    """tokenize_file

        takes as input a filename and prints it as a stream of tokens

        Args:
            filepath(str) -> string containing the filename to print as tokens

        Returns:

    """

    with open(filepath, 'r') as content:
        data = content.read()
    return tokenize(data)


def find_column(input_string, token):
    """
    find_column : input a string and a token
                  find the token column in the string
    """

    line_start = input_string.rfind('\n', 0, token.lexpos) + 1
    return token.lexpos - line_start + 1


keywords = {
    'min': 'MIN',
    'max': 'MAX',
    'external': 'EXTERNAL',
    'internal': 'INTERNAL',
    'integer': 'INTEGER',
    'continuous': 'CONTINUOUS',
    'binary': "BINARY",
    'in': 'IN',
    'import': 'IMPORT',
    'mod': 'MOD',
    'for': 'FOR',
    'where': 'WHERE',
    'with': 'WITH',
    'from': 'FROM',
    'and': 'AND',
    'or': 'OR',
    'not': 'NOT',
    "sum": 'SUM',
    "auxiliary": "AUX",
    "action": "ACTION",
    "state": "STATE",
    "sizing": "SIZING"
    }

reserved = {
    '#NODE': 'NODE',
    '#PARAMETERS': 'PARAM',
    '#CONSTRAINTS': 'CONS',
    '#VARIABLES': 'VAR',
    '#OBJECTIVES': 'OBJ',
    '#TIMEHORIZON': 'TIME',
    "#GLOBAL": "GLOBAL",
    "#HYPEREDGE": "HYPEREDGE",
    "#EXPRESSION": "EXPRESSION",
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
    'DOT',
    'FILENAME',
    'SEMICOLON',
    'DOUBLE_EQ',
    'BIGGER',
    'LOWER',
    'NEQ',
    'ASSIGN',
    ) + tuple(keywords.values()) + tuple(reserved.values())

reserved["#LINK"] = "HYPEREDGE"

# Regular expression rules for simple tokens

t_PLUS = r'\+'
t_MINUS = r'-'
t_COMMA = r'\,'
t_LCBRAC = r'\{'
t_RCBRAC = r'\}'
t_LBRAC = r'\['
t_RBRAC = r'\]'
t_POW = r'\*\*'
t_MULT = r'\*'
t_DIVIDE = r'/'
t_LPAR = r'\('
t_RPAR = r'\)'
t_EQUAL = r'\='
t_BIGGER = r'\>'
t_LOWER = r'\<'
t_LEQ = r'\<\='
t_BEQ = r'\>\='
t_COLON = r'\:'
t_SEMICOLON = r'\;'
t_DOT = r'\.'
t_DOUBLE_EQ = r'\=\='
t_NEQ = r'\!\='
t_ASSIGN = r'\<\-'


def t_filename(t):
    r"""\".*\""""

    filename = t.value.replace('"', '')
    legal_characters = r"[a-zA-Z_0-9./:\\]+"
    r = re.compile(legal_characters)

    if re.fullmatch(r, filename):
        t.type = 'FILENAME'
        t.value = filename
        return t
    else:
        t_error(t)


def t_id(t):
    r"""[a-zA-Z_][a-zA-Z_0-9$]*"""

    if t.value in keywords:
        t.type = keywords.get(t.value, 'ID')
    else:
        t.type = "ID"
    return t


def t_reserved(t):
    r"""[#][a-zA-Z_0-9]+"""

    if t.value in reserved:
        t.type = reserved.get(t.value, 'ID')
        return t
    else:
        t_error(t)


def t_comment(t):
    r"""[/][/].*"""

    pass


def t_number(t):
    r"""[0-9]+[\.][0-9]*[e]-[0-9]+|[0-9]+[\.][0-9]*[e][0-9]+|[0-9]+[e][0-9]+|
    [0-9]+[e]-[0-9]+|[0-9]+[\.][0-9]*|[0-9]+|[\.][0-9]+"""

    if "." in t.value or 'e' in t.value:
        t.value = float(t.value)
        t.type = "FLOAT"
    else:
        t.value = int(t.value)
        t.type = "INT"
    return t

# track line number


def t_newline(t):
    r"""\n+"""

    t.lexer.lineno += len(t.value)


# A string containing ignored characters (spaces and tabs)

t_ignore = ' \t\r\f'


# Error handling rule

def t_error(t):

    if lexer.lexdata is not None:
        message = 'Lexing error:' + str(t.lineno) + ':' \
            + str(find_column(lexer.lexdata, t)) + ':'
    else:
        message = 'Lexing error:' + str(t.lineno) + ':'

    if t.type == 'filename':
        message += "Illegal filename '%s'" % t.value
    elif t.type == 'reserved':
        message += "Illegal reserved word '%s'" % t.value
    else:
        message += "Illegal character '%s'" % t.value[0]

    print(message)
    exit(-1)


lexer = lex.lex()
