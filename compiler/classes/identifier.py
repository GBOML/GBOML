from compiler.classes.parent import Symbol
from compiler.classes.expression import Expression

class Identifier(Symbol):
    """
    Identifier object is a structure composed of 
    - a type id
    - a name
    - an expression 
    - an unitialized index field for knowing its position 
      if it is a variable
    """

    def __init__(self,type_id:str,name_id:str,expression:Expression=None,line:int=0):

        assert type(name_id) == str, "Internal error: expected string for identifier name" 
        assert type_id == "basic" or type_id == "assign", "Internal error: unknown type for identifier"
        assert expression == None or type(expression) == Expression, "Internal error: wrong expression type for identifier"

        Symbol.__init__(self,name_id,type_id,line)
        self.expression = expression
        self.index = 0

    def __str__(self):
        
        string = str(self.name)
        if self.expression != None:
            string+="["+str(self.expression)+']'
        
        return string

    def __copy__(self):
        
        return Identifier(self.type,self.name,expression=None)

    def name_compare(self,identifier_i)->bool:
        
        equal = False
        if type(identifier_i)== type(self):
            if self.name == identifier_i.name:
                equal = True
        elif type(identifier_i)==str:
            if self.name == identifier_i:
                equal = True
        
        return equal

    def set_expression(self,expr):
        
        self.expression = expr

    def get_expression(self):
        
        return self.expression

    def set_index(self,value):
        
        self.index = value
        
    def get_index(self):
        
        return self.index 