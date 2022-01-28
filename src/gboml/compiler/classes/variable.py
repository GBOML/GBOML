# Copyright (C) 2020 - 2022
# Bardhyl Miftari, Mathias Berger, Hatim Djelassi, Damien Ernst,
# University of Liege .
# Licensed under the MIT License (see LICENSE file).

from .parent import Symbol
from .identifier import Identifier
from .error import RedefinitionError


class Variable(Symbol):
    """
    Variable object is composed of: 
    - a type 
    - an Identifier object
    """

    def __init__(self, identifier: Identifier,
                 v_type: str, v_option: str = "",
                 child_variable=None, line=0):
        assert type(v_type) == str, \
            "Internal error: expected string for variable type"
        assert v_type == "internal" or v_type == "external", \
            "Internal error: unknown variable type "+str(v_type)
        assert type(identifier) == Identifier, \
            "Internal error: identifier must be an Identifier object"
        Symbol.__init__(self, identifier, v_type, line)
        self.option = v_option
        self.dependencies = []
        self.lower_constraint = None
        self.upper_constraint = None
        self.initial_constraint = None
        self.dynamics = None
        self.assignment = None
        self.child_variable = child_variable

    def __str__(self):
        string = "[" + str(self.name) + ' , ' + str(self.type)
        string += ']'

        return string

    def get_child_assignment(self):
        return self.child_variable

    def get_lower_constraint(self):
        return self.lower_constraint

    def set_lower_constraint(self, expression):
        if self.lower_constraint is None:
            self.lower_constraint = expression
        else:
            raise RedefinitionError

    def get_upper_constraint(self):
        return self.upper_constraint

    def set_upper_constraint(self, expression):
        if self.upper_constraint is None:
            self.upper_constraint = expression
        else:
            raise RedefinitionError

    def get_dynamic(self):
        return self.dynamics

    def set_dynamic(self, dynamic):
        if self.dynamics is None:
            self.dynamics = dynamic
        else:
            raise RedefinitionError

    def get_assignment(self):
        return self.assignment

    def set_assignment(self, expression):
        if self.assignment is None:
            self.assignment = expression
        else:
            raise RedefinitionError

    def get_initial_constraint(self):
        return self.initial_constraint

    def set_initial_constraint(self, expression):
        if self.initial_constraint is None:
            self.initial_constraint = expression
        else:
            raise RedefinitionError

    def get_dependencies(self):
        return self.dependencies

    def set_dependencies(self, dependencies):
        self.dependencies = dependencies

    def get_option(self):
        return self.option

    def get_size(self):
        return self.name.get_size()

    def get_identifier(self):
        return self.get_name()

    def reset_type(self, vtype):
        assert vtype == "internal" or vtype == "external", \
            "Internal error: unknown variable type"
        self.type = vtype
