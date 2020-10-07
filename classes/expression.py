from .parent import Symbol
from utils import Vector

class Expression(Symbol):
    def __init__(self,node_type,name = None,line = 0):
        Symbol.__init__(self,name,node_type,line)
        self.children = Vector()

    def __str__(self):
        if self.type != "literal":
            string = '['+str(self.type)
            if self.name !="":
                string += " , "+str(self.name) 
            if self.children.get_size()==0:
                string += ']'
            else:
                string +=  ' , '+str(self.children)+']'
        else:
            string = str(self.name)
        return string

    def get_children(self):
        return self.children.get_elements()

    def get_nb_children(self):
        return self.children.get_size()

    def add_child(self,child):
        self.children.add_element(child)