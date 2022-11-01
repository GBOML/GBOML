# Copyright (C) 2020 - 2022
# Bardhyl Miftari, Mathias Berger, Hatim Djelassi, Damien Ernst,
# University of Liege .
# Licensed under the MIT License (see LICENSE file).
import numpy as np

from .parent import Symbol
from gboml.compiler.utils import error_, list_to_string
from .link import Attribute
from .identifier import Identifier
from .error import WrongUsage
import copy


class Expression(Symbol):
    """
    Expression object is a tree like structure : 
    Its internal nodes are made up of 
    - an operator as type 
    - Children nodes of type Expression
    Its leafs are made up of 
    - a fixed type -> "literal"
    - no children nodes
    - a name field -> containing an evaluable unit 
    (number, identifier, etc)
    """

    def __init__(self, node_type: str, name=None, line: int = 0):

        assert type(node_type) == str, \
            "Internal error: expected string for Expression type"
        assert node_type in \
               ["+", "-", "/", "*", "**", "u-", "mod", "literal", "sum"], \
            "Internal error: unknown type for Expression"
        Symbol.__init__(self, name, node_type, line)
        self.parent = None
        self.children: list = []
        self.leafs = None
        self.condition = None
        self.time_interval = None
        self.python_ast = None

    def __str__(self) -> str:

        if self.type != "literal":

            string = '[' + str(self.type)
            if self.name != "":
                string += " , " + str(self.name)
            if len(self.children) == 0:

                string += ']'
            else:

                string += "[" + list_to_string(self.children) + "]]"
        else:

            string = str(self.name)

        return string

    def free(self):

        for child in self.children:
            child.free()
        self.children = []
        if self.time_interval is not None:
            self.time_interval = None
        self.time_interval = None
        self.condition = None
        self.name = None
        self.parent = None
        self.type = None
        self.line = None

    def get_children(self):

        return self.children

    def set_children(self, children):

        self.children = children

    def get_nb_children(self):

        return len(self.children)

    def get_parent(self):

        return self.parent

    def add_parent(self, p):

        self.parent = p

    def add_child(self, child):

        child.add_parent(self)
        self.children.append(child)

    def set_leafs(self, leaves):

        self.leafs = leaves

    def get_leafs(self):

        if self.leafs is None:
            self.leafs = self.find_leafs()

        return self.leafs

    def set_time_interval(self, time_interv):

        self.time_interval = time_interv

    def get_time_interval(self):

        return self.time_interval

    def set_condition(self, cond):

        self.condition = cond

    def get_condition(self):

        return self.condition

    def check_time(self, definitions):

        predicate = True
        if self.condition is not None:
            predicate = self.condition.check(definitions)

        return predicate

    def expanded_leafs(self, definitions):

        expr_type = self.get_type()
        all_leafs = []
        if expr_type == "literal":

            return [self]
        elif expr_type == "sum":

            name_index = self.time_interval.get_index_name()
            range_index = self.time_interval.get_range(definitions)
            expr_list = self.get_children()
            original_expr = expr_list[0]
            if name_index in definitions or name_index == "t":
                error_("Already defined index name : %s" % name_index)

            for k in range_index:

                expr_copy = copy.copy(original_expr)
                new_expr = expr_copy.replace(name_index, k, definitions)
                new_leafs = new_expr.expanded_leafs(definitions)
                for leaf in new_leafs:
                    leaf.add_replacement(name_index, k)
                all_leafs += new_leafs

        else:

            children = self.get_children()
            for child in children:
                leafs = child.expanded_leafs(definitions)
                all_leafs += leafs

        return all_leafs

    def find_leafs(self):

        all_children = []
        if self.type == "literal" or self.type == "sum":

            all_children = [self]
        else:

            children = self.get_children()
            for child in children:
                all_children += child.get_leafs()

        return all_children

    def __copy__(self):

        copy_name = copy.copy(self.get_name())
        copy_type = copy.copy(self.get_type())

        expr_copy = Expression(copy_type, copy_name, self.get_line())
        children = self.get_children()
        new_children = [copy.copy(child) for child in children]
        time_interval = copy.copy(self.time_interval)
        expr_copy.set_children(new_children)
        expr_copy.set_time_interval(time_interval)

        return expr_copy

    def replace_basic_parameters(self, definitions):

        expr_type = self.get_type()
        name = self.get_name()

        if expr_type == "literal":

            if type(name) == Identifier:

                identifier = name
                id_node_name = identifier.get_node_name()
                id_name = identifier.get_name()
                id_type = identifier.get_type()
                parameter_type = ""
                to_replace = False
                value = 0

                if id_type != "basic":
                    WrongUsage("function replace basic parameters can only be "
                               "used for basic parameters")

                if id_node_name == "" and id_name in definitions:
                    parameter = definitions[id_name]
                    parameter_type = parameter.get_type()
                    value = parameter.get_value()
                    to_replace = True

                elif id_node_name in definitions and \
                        id_name in definitions[id_node_name]:
                    parameter = definitions[id_node_name][id_name]
                    parameter_type = parameter.get_type()
                    value = parameter.get_value()
                    to_replace = True

                if to_replace:
                    if parameter_type != 'expression':
                        WrongUsage("function replace basic parameters can "
                                   "only be used for basic parameters")

                    value = value[0]
                    self.name = value

        else:

            children = self.get_children()
            for child in children:
                child.replace_basic_parameters(definitions)

    def replace(self, name_index, value, definitions):

        expr_type = self.get_type()
        name = self.get_name()
        expr = self
        if expr_type == "literal":

            if type(name) == Identifier:

                identifier = name
                id_name = identifier.get_name()
                id_type = identifier.get_type()
                if id_type == "basic" and id_name == name_index:

                    expr = Expression('literal', value, line=self.line)
                elif id_type == "assign":

                    index_expr = identifier.get_expression()
                    index_expr = index_expr.replace(name_index, value,
                                                    definitions)
                    identifier.set_expression(index_expr)
                    self.set_name(identifier)
            elif type(name) == Attribute:

                attr = name
                identifier = attr.get_attribute()
                if identifier == 'assign':
                    index_expr = identifier.get_expression()
                    index_expr = index_expr.replace(name_index, value)
                    identifier.set_expression(index_expr)
                    self.set_name(identifier)
        else:

            children = self.get_children()
            new_children = []
            for child in children:
                new_child = child.replace(name_index, value, definitions)
                new_children.append(new_child)
            self.set_children(new_children)

        return expr

    def evaluate_expression(self, definitions: dict):

        # Get type, children and nb_children
        e_type = self.type
        children = self.get_children()
        nb_child = len(children)
        value = 0

        # if type is literal (leaf without child)
        if e_type == 'literal':

            if nb_child != 0:
                error_("INTERNAL ERROR : literal must have zero child, got "
                       + str(nb_child) + " check internal parser")

            # get identifier can either be a INT FLOAT ID or ID[expr]
            identifier = self.get_name()

            # retrieve value directly if FLOAT or INT
            if type(identifier) == float or type(identifier) == int:

                value = identifier

            else:

                # get id type and set found to false
                identifier_type = identifier.get_type()
                identifier_name = identifier.get_name()
                identifier_expr = identifier.get_expression()
                identifier_node_name = identifier.get_node_name()
                dictionary_definitions = definitions

                if identifier_node_name in definitions:
                    dictionary_definitions = definitions[identifier_node_name]

                if identifier_name not in dictionary_definitions:
                    error_('Identifier "' + str(identifier)
                           + '" used but not previously defined, at line '
                           + str(self.get_line()))

                parameter = dictionary_definitions[identifier_name]
                if isinstance(parameter, list) or isinstance(parameter, int) or isinstance(parameter, float):
                    vector_value = parameter
                else:
                    vector_value = parameter.get_value()

                if isinstance(vector_value, list) or isinstance(vector_value, np.ndarray):
                    nb_values = len(vector_value)
                else:
                    nb_values = 1

                if identifier_type == "basic" and nb_values == 1:
                    if isinstance(vector_value, list):
                        value = vector_value[0]
                    else:
                        value = vector_value
                elif identifier_type == "basic" and isinstance(vector_value, list):
                    value = vector_value

                elif identifier_type == "assign":

                    index = identifier_expr.evaluate_expression(definitions)
                    if type(index) == float:

                        if index.is_integer() is False:
                            error_("Error: an index is a float: "
                                   + str(identifier)
                                   + 'at line ' + str(identifier.get_line()))
                        index = int(round(index))
                    if index >= nb_values or index < 0:
                        error_("Wrong indexing in Identifier '"
                               + str(identifier)
                               + "' at line, " + str(self.get_line()))
                    value = vector_value[index]
                else:

                    error_("Wrong time indexing in Identifier '"
                           + str(identifier) + "' at line, "
                           + str(self.get_line()))
        # if expression type is unary minus
        elif e_type == 'u-':

            if nb_child != 1:
                error_("INTERNAL ERROR : unary minus must have one child, got "
                       + str(nb_child) + " check internal parser")

            # evaluate the children
            term1 = children[0].evaluate_expression(definitions)
            if isinstance(term1, list):
                value = [-x for x in term1]
            else:
                value = -term1

        elif e_type == "sum":
            from .parameter import Parameter
            time_int = self.time_interval.get_range(definitions, default_type="expression")
            time_var = self.time_interval.get_index_name()
            if time_var in definitions:
                error_("ERROR: index " + str(time_var) +
                       " for loop already defined. Redefinition at line "
                       + str(self.line))
            sum_terms = 0
            condition_verified = False
            for i in time_int:

                index_parameter = Parameter(time_var, Expression("literal", i))
                index_parameter.set_value([i])
                definitions[time_var] = index_parameter
                if self.check_time(definitions):
                    condition_verified = True
                    term1 = children[0].evaluate_expression(definitions)
                    sum_terms += term1

            if not condition_verified:
                error_("ERROR: at expression :" + str(self)
                       + " there exists no value in sum range "
                         "that verifies that condition at line " + str(self.line))

            definitions.pop(time_var)
            value = sum_terms

        # MORE THAN one child
        else:

            if nb_child != 2:
                error_("INTERNAL ERROR : binary operators must have"
                       " two children, got "
                       + str(nb_child) + " check internal parser")
            term1 = children[0].evaluate_expression(definitions)
            term2 = children[1].evaluate_expression(definitions)
            if e_type == '+':
                if (isinstance(term1, list) and not isinstance(term2, list)) \
                        or (not isinstance(term1, list) and isinstance(term2, list)):

                    if isinstance(term1, list):
                        list_expression = term1
                        additional_expression = term2
                    else:
                        list_expression = term2
                        additional_expression = term1

                    value = [i + additional_expression for i in list_expression]
                elif isinstance(term1, list) and isinstance(term2, list):
                    if len(term1) != len(term2):
                        error_('Error: Unmatching length for vector + vector at line ' +
                               str(self.get_line()))
                    value = [t1 + t2 for t1, t2 in zip(term1, term2)]

                else:
                    value = term1 + term2
            elif e_type == '*':
                if (isinstance(term1, list) and not isinstance(term2, list)) \
                        or (not isinstance(term1, list) and isinstance(term2, list)):

                    if isinstance(term1, list):
                        list_expression = term1
                        additional_expression = term2
                    else:
                        list_expression = term2
                        additional_expression = term1

                    value = [i * additional_expression for i in list_expression]

                elif isinstance(term1, list) and isinstance(term2, list):
                    error_('Error: multiplying a vector by another one is not allowed ' +
                           str(self.get_line()))
                else:
                    value = term1 * term2
            elif e_type == '/':
                if isinstance(term1, list) and not isinstance(term2, list):
                    list_expression = term1
                    additional_expression = term2

                    value = [i / additional_expression for i in list_expression]
                elif isinstance(term1, list) and isinstance(term2, list):
                    error_('Error: dividing a vector by another one is not allowed ' +
                           str(self.get_line()))
                elif isinstance(term2, list):
                    error_('Error: dividing by a vector is not allowed ' +
                           str(self.get_line()))
                else:
                    value = term1 / term2
            elif e_type == '-':
                if (isinstance(term1, list) and not isinstance(term2, list)) \
                        or (not isinstance(term1, list) and isinstance(term2, list)):

                    if isinstance(term1, list):
                        list_expression = term1
                        additional_expression = term2
                    else:
                        list_expression = term2
                        additional_expression = term1

                    value = [i - additional_expression for i in list_expression]
                elif isinstance(term1, list) and isinstance(term2, list):
                    if len(term1) != len(term2):
                        error_('Error: Unmatching length for vector + vector at line ' +
                               str(self.get_line()))
                    value = [t1 + t2 for t1, t2 in zip(term1, term2)]
                else:
                    value = term1 - term2
            elif e_type == '**':
                if isinstance(term1, list) and not isinstance(term2, list):

                    list_expression = term1
                    additional_expression = term2

                    value = [i ** additional_expression for i in list_expression]
                elif isinstance(term1, list) and isinstance(term2, list):
                    error_('Error: power a vector by another one is not allowed ' +
                           str(self.get_line()))
                elif isinstance(term2, list):
                    error_('Error: power a number by a vector is not allowed ' +
                           str(self.get_line()))
                else:
                    value = term1 ** term2
            elif e_type == "mod":
                if isinstance(term1, list) and not isinstance(term2, list):

                    list_expression = term1
                    additional_expression = term2

                    value = [i % additional_expression for i in list_expression]
                elif isinstance(term1, list) and isinstance(term2, list):
                    error_('Error: modulo a vector by another one is not allowed ' +
                           str(self.get_line()))
                elif isinstance(term2, list):
                    error_('Error: modulo by a vector is not allowed ' +
                           str(self.get_line()))
                else:
                    value = term1 % term2

            else:
                error_("INTERNAL ERROR : unexpected e_type "
                       + str(e_type) + " check internal parser")

        return value

    def evaluate_python_string(self, definitions: dict):
        # Discard precedence information before returning
        prec, value = self.evaluate_python_string_impl(definitions)
        return value

    def evaluate_python_string_impl(self, definitions: dict):
        # Return value is a pair of an int indicating precedence level
        # and a string representing the expression
        # Precedence levels are used to decide when a subexpression
        # must be put in parentheses
        # Parentheses are always required when a subexpression has
        # strictly lower precedence than the current operation
        # Precedence levels:
        # 0 - addition, binary minus
        # 1 - multiplications, division, modulo
        # 2 - unary minus
        # 3 - exponentiation
        # 4 - terminals

        # Get type, children and nb_children
        e_type = self.get_type()
        nb_child = self.get_nb_children()
        children = self.get_children()
        prec = None
        value = None

        # if expression type is unary minus
        if e_type == 'u-':
            if nb_child != 1:
                error_("INTERNAL ERROR : unary minus must have one child, got "
                       + str(nb_child) + " check internal parser")

            # evaluate the children
            prec1, term1 = children[0].evaluate_python_string_impl(definitions)
            if prec1 < 2:
                value = '-(' + term1 + ')'
            else:
                value = '-' + term1
            prec = 2

        # if type is literal (leaf without child)
        elif e_type == 'literal':
            if nb_child != 0:
                error_("INTERNAL ERROR : literal must have zero child, got "
                       + str(nb_child) + " check internal parser")

            # get identifier can either be a INT FLOAT ID or ID[expr]
            identifier = self.get_name()

            # retreive value directly if FLOAT or INT
            if type(identifier) == float or type(identifier) == int:
                value = str(identifier)
                prec = 4

            elif type(identifier) == Attribute:
                key = identifier.get_node_field()
                if key not in definitions:
                    error_("Unknown Identifier " + str(identifier) + " at line "
                           + str(self.get_line()))

                inner_dict = definitions[key]
                inner_identifier = identifier.get_attribute()

                id_type = inner_identifier.get_type()
                id_name = inner_identifier.get_name()
                id_expr = inner_identifier.get_expression()

                if id_name not in inner_dict:
                    error_("Unknown Identifier " + str(identifier)
                           + " at line " + str(self.get_line()))

                if id_type == "basic":
                    value_vect = inner_dict[id_name]
                    if len(value_vect) != 1:
                        error_("INTERNAL error basic type should "
                               "have one value : " + str(identifier)
                               + " at line " + str(self.get_line()))
                    value = str(value_vect[0])
                    prec = 4

                elif id_type == "assign":
                    value_vect = inner_dict[id_name]
                    index = id_expr.evaluate_expression(definitions)
                    if len(value_vect) <= index:
                        error_("Wrong indexing in Identifier '"
                               + str(identifier) + "' at line, "
                               + str(self.get_line()))
                    value = str(value_vect[index])
                    prec = 4

            # else it is either ID or ID[expr]
            else:
                # get id type and set found to false
                id_type = identifier.get_type()
                id_name = identifier.get_name()
                id_expr = identifier.get_expression()

                if not (id_name in definitions):

                    error_('Identifier "' + str(identifier)
                           + '" used but not previously defined, at line '
                           + str(self.get_line()))

                vector_value = definitions[id_name]
                nb_values = len(vector_value)

                if id_type == "basic" and nb_values == 1:
                    value = str(vector_value[0])
                    prec = 4

                elif id_type == "assign":
                    index = id_expr.evaluate_expression(definitions)

                    if type(index) == float:
                        if not index.is_integer():
                            error_("Error: an index is a float: '"
                                   + str(identifier) + "' at line "
                                   + str(identifier.get_line()))
                        index = int(round(index))

                    if index >= nb_values or index < 0:
                        error_("Wrong indexing in Identifier '"
                               + str(identifier) + "' at line, "
                               + str(self.get_line()))

                    value = str(vector_value[index])
                    prec = 4

                else:
                    error_("Wrong time indexing in Identifier '"
                           + str(identifier) + "' at line, "
                           + str(self.get_line()))

        elif e_type == 'sum':
            error_("DEBUG ERROR: Python string conversion for sum "
                   "not implemented")

        # MORE THAN one child
        else:

            if nb_child != 2:
                error_("INTERNAL ERROR : binary operators must have "
                       "two children, got " + str(nb_child)
                       + " check internal parser")

            prec1, term1 = children[0].evaluate_python_string_impl(definitions)
            prec2, term2 = children[1].evaluate_python_string_impl(definitions)
            if e_type == '+':
                if prec1 < 0:
                    value = '(' + term1 + ')'
                else:
                    value = term1
                value = value + '+'
                if prec2 < 0:
                    value = value + '(' + term2 + ')'
                else:
                    value = value + term2
                prec = 0
            elif e_type == '-':
                if prec1 < 0:
                    value = '(' + term1 + ')'
                else:
                    value = term1
                value = value + '-'
                if prec2 < 0:
                    value = value + '(' + term2 + ')'
                else:
                    value = value + term2
                prec = 0
            elif e_type == '*':
                if prec1 < 1:
                    value = '(' + term1 + ')'
                else:
                    value = term1
                value = value + '*'
                if prec2 < 1:
                    value = value + '(' + term2 + ')'
                else:
                    value = value + term2
                prec = 1
            elif e_type == '/':
                if prec1 < 1:
                    value = '(' + term1 + ')'
                else:
                    value = term1
                value = value + '/'
                if prec2 < 1:
                    value = value + '(' + term2 + ')'
                else:
                    value = value + term2
                prec = 1
            elif e_type == "mod":
                if prec1 < 1:
                    value = '(' + term1 + ')'
                else:
                    value = term1
                value = value + '%'
                if prec2 < 1:
                    value = value + '(' + term2 + ')'
                else:
                    value = value + term2
                prec = 1
            elif e_type == '**':
                if prec1 < 3:
                    value = '(' + term1 + ')'
                else:
                    value = term1
                value = value + '**'
                if prec2 < 3:
                    value = value + '(' + term2 + ')'
                else:
                    value = value + term2
                prec = 3
            else:
                error_("INTERNAL ERROR : unexpected e_type "
                       + str(e_type) + " check internal parser")

        return prec, value

    def to_python_ast(self):
        import ast
        e_type = self.get_type()
        nb_child = self.get_nb_children()
        children = self.get_children()
        output = None
        if e_type == 'literal':
            name = self.get_name()
            if type(name) == Identifier:
                output = name.to_python_ast()
            else:
                output = ast.Constant(value=name)
        elif nb_child == 1:
            unique_child = self.children[0]
            if e_type == 'u-':
                output = ast.UnaryOp(op=ast.USub(),
                                     operand=unique_child.to_python_ast())
            else:
                time_interval = self.time_interval
                output = ast.Call(func=ast.Name(id='sum', ctx=ast.Load()),
                                  args=[
                                      ast.GeneratorExp(elt=unique_child.to_python_ast(),
                                                       generators=
                                                       [
                                                           ast.comprehension(
                                                               target=time_interval.turn_name_to_python_expression(),
                                                               iter=ast.Call(func=ast.Name(id='range', ctx=ast.Load()),
                                                                             args=time_interval.get_python_range(),
                                                                             keywords=[]),
                                                               ifs=[],
                                                               is_async=0
                                                           )
                                                       ]
                                                      )
                                       ],
                                  keywords=[]
                                  )

        elif nb_child == 2:
            child_left = children[0]
            child_right = children[1]
            left_ast = child_left.to_python_ast()
            right_ast = child_right.to_python_ast()
            operator = None
            # ["+", "-", "/", "*", "**", "u-", "mod", "literal", "sum"]
            if e_type == '+':
                operator = ast.Add
            elif e_type == "-":
                operator = ast.Sub
            elif e_type == "/":
                operator = ast.Div
            elif e_type == "*":
                operator = ast.Mult
            elif e_type == "**":
                operator = ast.Pow
            elif e_type == "mod":
                operator = ast.Mod
            output = ast.BinOp(left=left_ast, op=operator(), right=right_ast)

        return output

    def turn_to_python_expression(self):
        import ast
        expr_ast = self.to_python_ast()
        expr_ast = ast.Expression(expr_ast)
        expr_ast = ast.fix_missing_locations(expr_ast)
        compiled_expr = compile(expr_ast, "", mode="eval")
        self.python_ast = compiled_expr
        return compiled_expr

    def evaluate_python_ast(self, parameters_dictionary):
        import ast
        if self.python_ast is None:
            self.turn_to_python_expression()

        compiled_expr = self.python_ast
        gl = {"sum": sum, "range": range}
        ndict = dict(gl)
        ndict.update(parameters_dictionary)
        x = eval(compiled_expr, ndict, {})
        return x
