from .parent import Symbol
from utils import error_

class Expression(Symbol):
    def __init__(self,node_type,name = None,line = 0):
        Symbol.__init__(self,name,node_type,line)
        self.children = []
        self.leafs = None

    def __str__(self):
        if self.type != "literal":
            string = '['+str(self.type)
            if self.name !="":
                string += " , "+str(self.name) 
            if len(self.children)==0:
                string += ']'
            else:
                string +=  ' , '+str(self.children)+']'
        else:
            string = str(self.name)
        return string

    def get_children(self):
        return self.children

    def get_nb_children(self):
        return len(self.children)

    def add_child(self,child):
        self.children.append(child)
    
    def get_leafs(self):
        if self.leafs == None:
            self.leafs = self.find_leafs()
        return self.leafs
    
    def find_leafs(self):
        all_children = []

        if self.type == "literal":
            all_children = [self]
        else: 
            children = self.get_children()
            for child in children:
                all_children += child.find_leafs()
        return all_children

    def evaluate_expression(self,definitions):
        # Get type, children and nb_children
        e_type = self.get_type()
        nb_child = self.get_nb_children()
        children = self.get_children()

        # if expression type is unary minus
        if e_type == 'u-':
            if nb_child != 1:
                error_("INTERNAL ERROR : unary minus must have one child, got "+str(nb_child)+" check internal parser")

            # evaluate the children
            term1 = children[0].evaluate_expression(definitions)
            value = -term1

        # if type is literal (leaf without child)
        elif e_type == 'literal':
            if nb_child != 0:
                error_("INTERNAL ERROR : literal must have zero child, got "+str(nb_child)+" check internal parser")

            # get identifier can either be a INT FLOAT ID or ID[expr]
            identifier = self.get_name()
            
            # retreive value directly if FLOAT or INT
            if type(identifier)==float or type(identifier)==int:
                value = identifier
            
            # else it is either ID or ID[expr]
            else:
                # get id type and set found to false
                id_type = identifier.get_type()
                id_name = identifier.get_name()
                id_expr = identifier.get_expression()

                if not(id_name in definitions):
                    error_('Identifier "'+ str(identifier)+ '" used but not previously defined, at line '+str(self.get_line()))

                vector_value = definitions[id_name]
                nb_values = len(vector_value)

                if id_type == "basic" and nb_values==1:
                    value = vector_value[0]

                elif id_type =="basic" and ("t" in definitions):
                    index = definitions["t"][0]
                    if type(index) == float:
                        if index.is_integer()==False:
                            error_("Error: an index is a float: "+ str(identifier)+\
                                'at line '+str(identifier.get_line()))
                        index = int(round(index))

                    if index >= nb_values or index < 0:
                        error_("Wrong indexing in Identifier '"+ str(identifier)+ "' at line, "+str(self.get_line()))
                    
                    value = vector_value[index]
                
                elif id_type == "assign":
                    index = id_expr.evaluate_expression(definitions)
                    
                    if type(index) == float:
                        if index.is_integer()==False:
                            error_("Error: an index is a float: "+ str(identifier)+\
                                'at line '+str(identifier.get_line()))
                        index = int(round(index))

                    if index >= nb_values or index < 0:
                        error_("Wrong indexing in Identifier '"+ str(identifier)+ "' at line, "+str(self.get_line()))
                    
                    value = vector_value[index]
                
                else:
                    error_("Wrong time indexing in Identifier '"+ str(identifier)+ "' at line, "+str(self.get_line()))

        # MORE THAN one child
        else:
            if nb_child != 2:
                error_("INTERNAL ERROR : binary operators must have two children, got "+str(nb_child)+" check internal parser")

            term1 = children[0].evaluate_expression(definitions)
            term2 = children[1].evaluate_expression(definitions)
            if e_type == '+':
                value = term1 + term2
            elif e_type =='*':
                value = term1 * term2
            elif e_type == '/':
                value = term1/term2
            elif e_type == '-':
                value = term1-term2
            elif e_type == '**':
                value = term1**term2
            elif e_type == "mod":
                value = term1%term2
            else:
                error_("INTERNAL ERROR : unexpected e_type "+str(e_type)+" check internal parser")

        return value
