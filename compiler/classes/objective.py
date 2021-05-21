from compiler.classes.parent import Type
from compiler.classes.expression import Expression


class Objective(Type):
    """
    Objective object is composed of: 
    - a type either min or max
    - an expression
    """

    def __init__(self, o_type, expression, time_interval=None, condition=None, line=0):

        assert o_type == "min" or o_type == "max", "Internal error: unknown objective type"
        assert type(expression) == Expression, "Internal error: expected expression type expression in objective"
        Type.__init__(self, o_type, line)
        self.expression = expression
        self.time_interval = time_interval
        self.condition = condition

    def __str__(self):

        string = "["+str(self.type)+','+str(self.expression)+']'
        
        return string

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
