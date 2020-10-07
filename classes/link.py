
class Attribute:
    def __init__(self,name_node,name_attribute=None):
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
    def __init__(self,attribute,vector):
        self.attribute = attribute
        self.vector = vector

    def __str__(self):
        string = '['+str(self.attribute)+' , '+str(self.vector)+']'
        return string