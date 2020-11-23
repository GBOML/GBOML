from .parent import Type

class Constraint(Type): 
    def __init__(self,c_type,rhs,lhs,time_interval = None,condition = None,line=0):
        Type.__init__(self,c_type,line)
        self.rhs = rhs
        self.lhs = lhs
        self.time_interval=time_interval
        self.condition = condition

    def __str__(self):
        string = "["+str(self.type)+' , '+str(self.rhs)
        string += " , "+str(self.lhs)
        if self.condition != None:
            string += " ][ condition : "+str(self.condition)
        if self.time_interval != None:
            string += "][ time : "+str(self.time_interval)
        string+=']'
        return string

    def get_sign(self):
        return self.get_type()

    def get_rhs(self):
        return self.rhs

    def get_lhs(self):
        return self.lhs
    
    def get_leafs(self):
        return self.rhs.get_leafs()+self.lhs.get_leafs()

    def get_time_range(self,definitions):
        range_time = None
        if self.time_interval != None:
            range_time =  self.time_interval.get_range(definitions)
        return range_time

    def check_time(self,definitions):
        cond_predicate = True
        if self.condition != None:
            cond_predicate = self.condition.check(definitions)
        
        return cond_predicate
