from compiler.classes.node import Node


class Attribute:
    """
    Attribute object is a structure composed of 
    - a node object
    - The node's name 
    - a variable name 
    """

    def __init__(self,name_node:str,name_attribute:str=None):

        assert type(name_node)==str, "Internal error: Attribute node name of unknown type"
        assert type(name_attribute)==str, "Internal error: Attribute name attribute of unknown type"

        self.node = name_node
        self.attribute = name_attribute
        self.node_object = None

    def __str__(self):
        
        string = ""
        if self.node_object != None:
            string += '['
        string += str(self.node)
        if self.attribute!=None:
            string+='.'+str(self.attribute)
        if self.node_object != None:
            string+= ','+str(self.node_object.name)+']'
        
        return string

    def compare(self,attr):
        
        if self.node == attr.node and self.attribute == attr.attribute:
            return True
        
        return False

    def set_node_object(self,n_object):

        self.node_object = n_object

    def get_node_object(self):
        
        return self.node_object


class Link: 
    """
    Link object is a structure composed of 
    - a left handside attribute
    - a vector of right handside attributes
      (one or several)
    """

    def __init__(self,attribute:Attribute,vector:list):

        self.attribute = attribute
        self.vector = vector

    def __str__(self):

        string = '['+str(self.attribute)+' , '+str(self.vector)+']'
        
        return string

    def to_vector(self):

        lhs_attribute = self.attribute
        lhs_node = lhs_attribute.node
        lhs_variables = lhs_attribute.attribute

        lhs = [str(lhs_node),str(lhs_variables)]
        vector = []
        for attr in self.vector:
            rhs_node = attr.node
            rhs_var = attr.attribute
            rhs = [str(rhs_node),str(rhs_var)]
            vector.append([lhs,rhs])
        
        return vector