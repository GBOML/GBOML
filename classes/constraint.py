from .parent import Type

class Constraint(Type): 
    def __init__(self,c_type,rhs,lhs,line=0):
        Type.__init__(self,c_type,line)
        self.rhs = rhs
        self.lhs = lhs

    def __str__(self):
        string = "["+str(self.type)+' , '+str(self.rhs)
        string += " , "+str(self.lhs)+']'
        return string

    def get_sign(self):
        return self.get_type()

    def get_rhs(self):
        return self.rhs

    def get_lhs(self):
        return self.lhs
    
    def get_leafs(self):
        return self.rhs.get_leafs()+self.lhs.get_leafs()