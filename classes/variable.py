from .parent import Symbol

class Variable(Symbol): 
    def __init__(self,name,v_type, line = 0):
        Symbol.__init__(self,name,v_type,line)

    def __str__(self):
        string = "["+str(self.name)+' , '+str(self.type)
        string += ']'
        return string

    def get_identifier(self):
        return self.get_name()
