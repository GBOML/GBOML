from compiler.classes.parent import Symbol
from compiler.utils import error_, list_to_string
import os


class Parameter(Symbol): 
    """
    Parameter object is composed of: 
    - a name 
    - a right handside expression or several expression
    """

    def __init__(self, name: str, expression, line=0):

        self.vector = None
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
        self.value = None

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
        self.value = value

    def get_values_from_file(self, expression):
        from compiler.classes.expression import Expression

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
                        expr = Expression('literal', number)
                        self.vector.append(expr)
                    except ValueError:

                        error_("file "+expression+" contains values that are not numbers "+nb)

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
