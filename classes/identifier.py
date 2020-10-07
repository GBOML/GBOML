from .parent import Symbol

class Identifier(Symbol):
    def __init__(self,type_id,name_id,expression=None,line=0):
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

    def name_compare(self,identifier_i):
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