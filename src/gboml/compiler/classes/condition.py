# Copyright (C) 2020 - 2022
# Bardhyl Miftari, Mathias Berger, Hatim Djelassi, Damien Ernst,
# University of Liege .
# Licensed under the MIT License (see LICENSE file).

from .parent import Type
from .expression import Expression


class Condition(Type):
    """
    Condition object is a tree like structure where:
    - each node is defined by an operator 
    - internal nodes have children of Condition objects
    - leaf nodes have children of Expressions type
    """

    def __init__(self, type_id: str, children: list, line: int = 0) -> None:
    
        assert type(type_id) == str, \
            "Internal error: expected string for condition type"
        assert type_id in \
               ["and", "not", "or", "==", "!=", "<", ">", "<=", ">="], \
               "Internal error: unknown type for condition"
        Type.__init__(self, type_id, line)
        self.type = type_id
        self.children = children
        self.python_ast = None

    def __str__(self) -> str:
    
        string = "["+str(self.type)
        for child in self.children:
            string += ','+str(child)
        string += ']'
    
        return string

    def get_children(self) -> list:
    
        return self.children

    def check(self, definitions: dict) -> bool:
    
        predicate = False
        if type(self.children[0]) == Condition:

            predicate_0 = self.children[0].check(definitions)
            predicate_1 = False
            if len(self.children) == 2:

                predicate_1 = self.children[1].check(definitions)
            if self.type == 'and':

                predicate = (predicate_0 and predicate_1)
            elif self.type == 'or':

                predicate = (predicate_0 or predicate_1)
            elif self.type == "not":

                predicate = (not predicate_0)
                
        elif type(self.children[0]) == Expression:
            value0 = self.children[0].evaluate_expression(definitions)
            value1 = self.children[1].evaluate_expression(definitions)

            if self.type == "==":
                predicate = (value0 == value1)
            elif self.type == "<=":
                predicate = (value0 <= value1)
            elif self.type == ">=":
                predicate = (value0 >= value1)
            elif self.type == ">":
                predicate = (value0 > value1)
            elif self.type == "<":
                predicate = (value0 < value1)
            elif self.type == "!=":
                predicate = (value0 != value1)

        return predicate

    def to_python_ast(self):
        import ast

        condition_type = self.get_type()
        children = self.children
        ast_form = None
        if condition_type == "and":
            ast_form = ast.BinOp(left=children[0].to_python_ast(),
                                 op=ast.BitAnd(),
                                 right=children[1].to_python_ast())
        elif condition_type == "or":
            ast_form = ast.BinOp(left=children[0].to_python_ast(),
                                 op=ast.BitOr(),
                                 right=children[1].to_python_ast())
        elif condition_type == "not":
            ast_form = ast.UnaryOp(op=ast.Not(),
                                   operand=children[0].to_python_ast())
        elif condition_type == "==":
            ast_form = ast.Compare(left=children[0].to_python_ast(),
                                   ops=[ast.Eq()],
                                   comparators=[children[1].to_python_ast()]
                                   )
        elif condition_type == "<=":
            ast_form = ast.Compare(left=children[0].to_python_ast(),
                                   ops=[ast.LtE()],
                                   comparators=[children[1].to_python_ast()]
                                   )
        elif condition_type == ">=":
            ast_form = ast.Compare(left=children[0].to_python_ast(),
                                   ops=[ast.GtE()],
                                   comparators=[children[1].to_python_ast()]
                                   )
        elif condition_type == "<":
            ast_form = ast.Compare(left=children[0].to_python_ast(),
                                   ops=[ast.Lt()],
                                   comparators=[children[1].to_python_ast()]
                                   )
        elif condition_type == ">":
            ast_form = ast.Compare(left=children[0].to_python_ast(),
                                   ops=[ast.Gt()],
                                   comparators=[children[1].to_python_ast()]
                                   )
        elif condition_type == "!=":
            ast_form = ast.Compare(left=children[0].to_python_ast(),
                                   ops=[ast.NotEq()],
                                   comparators=[children[1].to_python_ast()]
                                   )
        return ast_form

    def turn_to_python_expression(self):
        import ast
        condition_ast = self.to_python_ast()
        expr_ast = ast.Expression(condition_ast)
        expr_ast = ast.fix_missing_locations(expr_ast)
        compiled_expr = compile(expr_ast, "", mode="eval")
        self.python_ast = compiled_expr
        return compiled_expr
