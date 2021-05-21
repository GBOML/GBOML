

class Attribute:
    """
    Attribute object is a structure composed of 
    - a node object
    - The node's name 
    - a variable name 
    """

    def __init__(self, name_node: str, name_variable: str = None, line: int = 0):

        assert type(name_node) == str, "Internal error: Attribute node name of unknown type"
        self.node = name_node
        self.attribute = name_variable
        self.node_object = None  # POINTER to corresponding node object
        self.line = line

    def get_attribute(self):

        return self.attribute

    def get_node_field(self):

        return self.node

    def get_line(self):

        return self.line

    def __str__(self):
        
        string = ""
        if self.node_object is not None:

            string += '['
        string += str(self.node)
        if self.attribute is not None:

            string += '.'+str(self.attribute)
        if self.node_object is not None:

            string += ','+str(self.node_object.name)+']'
        
        return string

    def compare(self, attr):
        
        if self.node == attr.node and self.attribute == attr.attribute:

            return True
        
        return False

    def set_node_object(self, n_object):

        self.node_object = n_object

    def get_node_object(self):
        
        return self.node_object
