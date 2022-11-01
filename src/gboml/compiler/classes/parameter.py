# Copyright (C) 2020 - 2022
# Bardhyl Miftari, Mathias Berger, Hatim Djelassi, Damien Ernst,
# University of Liege .
# Licensed under the MIT License (see LICENSE file).

from .parent import Symbol
from gboml.compiler.utils import error_, list_to_string
import os


class Parameter(Symbol): 
    """
    Parameter object is composed of: 
    - a name 
    - a right handside expression or several expression
    """

    def __init__(self, name: str, expression, line=0):

        self.vector = None
        self.read_from_file = False
        self.value = None
        if expression is None:

            type_para = "table"
        elif type(expression) == str:

            type_para = "table"
            self.get_values_from_file(expression)
            expression = None
        else:

            type_para = "expression"
        Symbol.__init__(self, name, type_para, line)
        self.expression = expression

    def __str__(self):
        
        string = "["+str(self.name)+' , '
        if self.expression is None:
            string += list_to_string(self.vector)
        else:
            string += str(self.expression)
        string += str(self.value)
        string += ']'
        
        return string

    def get_value(self):
        return self.value

    def set_value(self, value):
        if len(value) >= 2 and isinstance(value, list):
            self.type = "table"
        self.value = value

    def get_values_from_file(self, expression):
        # from .expression import Expression
        """
        from numpy import genfromtxt, nan
        self.read_from_file = True
        if (os.path.isfile('./' + expression)) is False:
            error_("No such file as " + str(expression))
        value = genfromtxt('./'+expression, delimiter=',;\n ')
        if value[-1] == nan:
            value = value[:-1]

        self.value = value
        self.vector = value

        """
        self.read_from_file = True
        self.vector = []
        if type(expression) is str:

            if(os.path.isfile('./'+expression)) is False:
                error_("No such file as "+str(expression))
            f = open('./'+expression, "r", encoding="ISO-8859-1")
            for line in f:

                line = line.replace("\n", " ")
                line = line.replace(",", " ")
                line = line.replace(";", " ")
                line = line.split(" ")
                for nb in line:

                    if nb == "":

                        continue
                    try:

                        number = float(nb)
                        self.vector.append(number)
                    except ValueError:

                        error_("file "+expression
                               + " contains values that are not numbers "+nb)
            f.close()
            self.value = self.vector


    def get_expression(self):
        
        return self.expression

    def set_vector(self, v):
        
        self.vector = v

    def get_vector(self):
        
        return self.vector

    def get_number_of_values(self):

        if self.type == "expression":
            return 1
        else:
            return len(self.vector)
