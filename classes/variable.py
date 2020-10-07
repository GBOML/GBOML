from .parent import Symbol

class Variable(Symbol): 
    def __init__(self,name,v_type, unity=None,line = 0):
        Symbol.__init__(self,name,v_type,line)
        self.unity = unity

    def __str__(self):
        string = "["+str(self.name)+' , '+str(self.type)
        if self.unity==None:
            string += ']'
        else :
            string += ' , '+ str(self.unity)+']'
        return string

    def get_identifier(self):
        return self.get_name()

    def get_unity(self):
        return self.unity