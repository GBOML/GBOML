# Copyright (C) 2020 - 2022
# Bardhyl Miftari, Mathias Berger, Hatim Djelassi, Damien Ernst,
# University of Liege .
# Licensed under the MIT License (see LICENSE file).

from .parent import Type
from .expression import Expression
from .time_obj import TimeInterval
from .condition import Condition


class Constraint(Type):
    """
    Constraint object is a structure composed of 
    - an operator 
    - a left handside expression 
    - a right handside expression 
    - a TimeInterval object 
    - a condition object
    """

    def __init__(self, c_type: str, lhs: Expression, rhs: Expression,
                 time_interval: TimeInterval = None,
                 condition: Condition = None, line: int = 0):

        assert type(c_type) == str, \
            "Internal error: expected string for Constraint type"
        assert c_type in ["==", "<=", ">="], \
            "Internal error: unknown type for constraint"
        assert type(rhs) == Expression, \
            "Internal error: expected Expression type for " \
            "right hand side in Constraint"
        assert type(rhs) == Expression, "Internal error: expected " \
                                        "Expression type " \
                                        "for left hand side in Constraint"
        assert time_interval is None or type(time_interval) == TimeInterval, \
            "Internal error: expected TimeInterval object in Constraint"
        assert condition is None or type(condition) == Condition, \
            "Internal error: expected Condition object in Constraint"

        Type.__init__(self, c_type, line)
        self.name = None
        self.rhs = rhs
        self.lhs = lhs
        self.time_interval = time_interval
        self.condition = condition

    def __str__(self) -> str:

        string = "[" + str(self.type) + ' , ' + str(self.rhs)
        string += " , " + str(self.lhs)
        if self.condition is not None:
            string += " ][ condition : " + str(self.condition)
        if self.time_interval is not None:
            string += "][ time : " + str(self.time_interval)
        string += ']'

        return string

    def get_name(self):
        return self.name

    def set_name(self, name):
        self.name = name

    def get_time_interval(self):

        return self.time_interval

    def get_condition(self):

        return self.condition

    def get_sign(self) -> str:

        return self.get_type()

    def get_rhs(self) -> Expression:

        return self.rhs

    def get_lhs(self) -> Expression:

        return self.lhs

    def get_leafs(self) -> list:

        return self.rhs.get_leafs() + self.lhs.get_leafs()

    def get_expanded_leafs(self, dictionary: dict) -> list:

        return self.rhs.expanded_leafs(dictionary) + \
               self.lhs.expanded_leafs(dictionary)

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
