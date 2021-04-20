from compiler.classes.parent import Symbol
from compiler.utils import error_,list_to_string
from compiler.classes.link import Attribute
from compiler.classes.identifier import Identifier
import copy

class Expression(Symbol):
    """
    Expression object is a tree like structure : 
    Its internal nodes are made up of 
    - an operator as type 
    - Children nodes of type Expression
    Its leafs are made up of 
    - a fixed type -> "literal"
    - no children nodes
    - a name field -> containing an evaluable unit 
    (number, identifier, etc)
    """


    def __init__(self,node_type:str,name = None,line:int = 0):
        assert type(node_type) == str, "Internal error: expected string for Expression type" 
        assert node_type in ["+","-","/","*","**","u-","mod","literal","sum"], "Internal error: unknown type for Expression"

        Symbol.__init__(self,name,node_type,line)
        self.children:list = []
        self.leafs = None
        self.time_interval = None
        self.replaced_dict = {}

    def __str__(self)->str:
        
        if self.type != "literal":
            string = '['+str(self.type)
            if self.name !="":
                string += " , "+str(self.name) 
            if len(self.children)==0:
                string += ']'
            else:
                string += "[" + list_to_string(self.children)+ "]]"
        else:
            string = str(self.name)

        return string

    def get_children(self):

        return self.children

    def set_children(self,children):
        self.children = children

    def get_nb_children(self):
        
        return len(self.children)

    def add_child(self,child):
        
        self.children.append(child)
    
    def set_leafs(self,leaves):
        self.leafs = leaves

    def get_leafs(self):
        
        if self.leafs == None:
            self.leafs = self.find_leafs()
        
        return self.leafs
    
    def set_time_interval(self,time_interv):
        self.time_interval = time_interv

    def get_time_interval(self):
        return self.time_interval

    def add_replacement(self,name,value):
        self.replaced_dict[name] =  value

    def get_replacement_dict(self):
        return self.replaced_dict

    def expanded_leafs(self,definitions):
        expr_type = self.get_type()
        if expr_type=="sum":
            name_index = self.time_interval.get_index_name()
            range_index = self.time_interval.get_range(definitions)
            expr_list = self.get_children()
            original_expr = expr_list[0]
            
            if name_index in definitions or name_index == "t":
                error_("Already defined index name : "+str(name_index))
            
            all_leafs = []
            for k in range_index:
                expr_copy = copy.copy(original_expr)
                new_expr = expr_copy.replace(name_index,k,definitions)
                new_leafs = new_expr.expanded_leafs(definitions)
                for leaf in new_leafs:
                    leaf.add_replacement(name_index,k)
                all_leafs += new_leafs

            return all_leafs
        
        elif expr_type == "literal":
            return [self]

        else:
            children = self.get_children()
            all_leafs = []
            for child in children:
                leafs = child.expanded_leafs(definitions)
                all_leafs += leafs
            return all_leafs

    def find_leafs(self):

        all_children = []

        if self.type == "literal" or self.type == "sum":
            all_children = [self]
        
        else: 
            children = self.get_children()
            for child in children:
                all_children += child.get_leafs()
        
        return all_children


    def __copy__(self):
        copy_name = copy.copy(self.get_name())
        copy_type = copy.copy(self.get_type())
        expr_copy = Expression(copy_type,copy_name,self.get_line())
        children = self.get_children()

        new_children = [copy.copy(child) for child in children]
        time_interval = copy.copy(self.time_interval)

        expr_copy.set_children(new_children)
        expr_copy.set_time_interval(time_interval)
        
        return expr_copy


    def replace(self,name_index,value,definitions):

        expr_type = self.get_type()
        name = self.get_name()
        expr = self
        if expr_type == "literal":
            if type(name) == Identifier:
                identifier = name
                id_name = identifier.get_name()
                id_type = identifier.get_type()
                if id_type == "basic" and id_name == name_index:
                    expr = Expression('literal', value, line=self.line)

                elif id_type == "assign":
                    index_expr = identifier.get_expression()
                    index_expr = index_expr.replace(name_index,value,definitions)
                    identifier.set_expression(index_expr)
                    self.set_name(identifier)
            elif type(name) == Attribute:
                attr = name
                identifier = attr.get_attribute()
                if identifier == 'assign':
                    index_expr = identifier.get_expression()
                    index_expr = index_expr.replace(name_index,value)
                    identifier.set_expression(index_expr)
                    self.set_name(identifier)
        else : 

            children = self.get_children()
            new_children = []
            for child in children : 
                new_child = child.replace(name_index,value,definitions)
                new_children.append(new_child)
            self.set_children(new_children)

        return expr



    def evaluate_expression(self,definitions:dict):
        
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
            
            elif type(identifier)==Attribute:
                key = identifier.get_node_field()
                if key not in definitions:
                    error_("Unknown Identifier "+str(identifier)+"at line "+str(self.get_line()))
                
                inner_dict = definitions[key]
                inner_identifier = identifier.get_attribute()

                id_type = inner_identifier.get_type()
                id_name = inner_identifier.get_name()
                id_expr = inner_identifier.get_expression()

                if id_name not in inner_dict:
                    error_("Unknown Identifier "+str(identifier)+" at line "+str(self.get_line()))

                if id_type == "basic" :
                    value_vect = inner_dict[id_name]
                    if len(value_vect)!=1:
                        error_("INTERNAL error basic type should have one value : "+str(identifier)+" at line "+str(self.get_line()))
                    value = value_vect[0]

                elif id_type == "assign" : 
                    value_vect = inner_dict[id_name]
                    index = id_expr.evaluate_expression(definitions)
                    if len(value_vect)<=index:
                        error_("Wrong indexing in Identifier '"+ str(identifier)+ "' at line, "+str(self.get_line()))
                    value = value_vect[index]

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

        elif e_type == "sum":
        
            time_int = self.time_interval.get_range(definitions)
            time_var = self.time_interval.get_index_name()

            if time_var in definitions:
                error_("ERROR: index "+str(time_var)+ " for loop already defined. Redefinition at line "+str(self.line))

            sum_terms = 0
            
            for i in time_int:
                definitions[time_var]=[i]
                term1 = children[0].evaluate_expression(definitions)
                sum_terms+= term1

            definitions.pop(time_var)
            value = sum_terms

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
