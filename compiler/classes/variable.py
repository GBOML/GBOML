from compiler.classes.parent import Symbol
from compiler.classes.identifier import Identifier
from compiler.utils import error_

class Variable(Symbol): 
    """
    Variable object is composed of: 
    - a type 
    - an Identifier object
    """

    def __init__(self,identifier:Identifier,v_type:str, line = 0):

        assert type(v_type) == str, "Internal error: expected string for variable type"
        assert v_type == "internal" or v_type == "output" or v_type == "input", "Internal error: unknown variable type"
        assert type(identifier) == Identifier, "Internal error: identifier must be an Identifier object"

        Symbol.__init__(self,identifier,v_type,line)

    def __str__(self):

        string = "["+str(self.name)+' , '+str(self.type)
        string += ']'
        
        return string

    def get_identifier(self):
        
        return self.get_name()
