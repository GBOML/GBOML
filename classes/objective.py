from .parent import Type

class Objective(Type):
    def __init__(self,o_type,expression,line = 0):
        Type.__init__(self,o_type,line)
        self.expression = expression

    def __str__(self):
        string = "["+str(self.type)+','+str(self.expression)+']'
        return string

    def get_expression(self):
        return self.expression