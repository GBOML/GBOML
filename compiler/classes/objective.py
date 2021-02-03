from compiler.classes.parent import Type
from compiler.classes.expression import Expression

class Objective(Type):
    """
    Objective object is composed of: 
    - a type either min or max
    - an expression
    """


    def __init__(self,o_type,expression,line = 0):
        assert o_type == "min" or o_type == "max", "Internal error: unknown objective type"
        assert type(expression) == Expression, "Internal error: expected expression type expression in objective"

        Type.__init__(self,o_type,line)
        self.expression = expression

    def __str__(self):

        string = "["+str(self.type)+','+str(self.expression)+']'
        
        return string

    def get_expression(self):
        
        return self.expression