# Copyright (C) 2020 - 2022
# Bardhyl Miftari, Mathias Berger, Hatim Djelassi, Damien Ernst,
# University of Liege .
# Licensed under the MIT License (see LICENSE file).

from .parent import Type
from .expression import Expression


class Objective(Type):
    """
    Objective object is composed of: 
    - a type either min or max
    - an expression
    """

    def __init__(self, o_type, expression, time_interval=None,
                 condition=None, name=None, line=0):

        assert o_type == "min" or o_type == "max", \
            "Internal error: unknown objective type"
        assert type(expression) == Expression, \
            "Internal error: expected expression type expression in objective"
        Type.__init__(self, o_type, line)
        self.expression = expression
        self.time_interval = time_interval
        self.condition = condition
        self.name = name

    def __str__(self):

        string = "["+str(self.type)+','+str(self.expression)+']'
        
        return string

    def get_name(self):
        return self.name

    def get_expression(self):
        
        return self.expression

    def get_index_var(self):

        var_name = "t"
        if self.time_interval is not None:

            var_name = self.time_interval.get_index_name()
        
        return var_name

    def get_time_range(self, definitions):
        
        range_time = None
        if self.time_interval is not None:

            range_time = self.time_interval.get_range(definitions)
        
        return range_time

    def check_time(self, definitions):
        
        predicate = True
        if self.condition is not None:
            predicate = self.condition.check(definitions)
        
        return predicate

    def get_condition(self):

        return self.condition

    def get_time_interval(self):

        return self.time_interval
