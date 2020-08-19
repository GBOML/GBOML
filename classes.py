
# classes.py
#
# Writer : MIFTARI B
# ------------

class Vector: 
    def __init__(self):
        self.elements = []
        self.n = 0

    def __str__(self):
        string = '['
        for i in range(self.n):
            string = string + ' '+str(self.elements[i])
        string += ']'
        return string

    def add_begin(self,e):
        self.elements.insert(0,e)
        self.n = self.n+1

    def add_element(self,e):
        self.elements.append(e)
        self.n = self.n+1

    def get_elements(self):
        return self.elements

    def get_size(self):
        return self.n

class Program: 
    def __init__(self,vector_n,timescale = None,links = None):
        self.vector_nodes = vector_n
        self.time = timescale
        self.links = links

    def __str__(self):
        string = "["+str(self.vector_nodes)
        if self.time != None:
            string += ' , '+str(self.time)

        if self.links ==None:
            string += ']'
        else:
            string += ' , '+str(self.links)+']'

        return string

    def get_nodes(self):
        return self.vector_nodes

    def get_time(self):
        return self.time

    def get_links(self):
        return self.links

    def set_time(self,timescale):
        self.time = timescale

    def set_vector(self,vector_n):
        self.vector_nodes = vector_n

class Time:
    def __init__(self,time,step):
        self.time = time
        self.step = step
    def __str__(self):
        string = 'time: '+str(self.time)+' step: '+str(self.step)
        return string

class Node: 
    def __init__(self,name,line = 0):
        self.name = name
        self.constraints = Vector()
        self.variables = Vector()
        self.parameters = Vector()
        self.objectives = Vector()
        self.line = line

    def __str__(self):
        string = '['+str(self.name)+' , '
        string += str(self.parameters)+' , '
        string += str(self.variables)+' , '
        string += str(self.constraints)+' , '
        string += str(self.objectives)+']'
        return string

    def set_line(self,line):
        self.line = line

    def get_line(self):
        return self.line

    def set_constraints(self,cons):
        self.constraints = cons

    def set_variables(self,var):
        self.variables = var

    def set_parameters(self,para):
        self.parameters = para

    def set_objectives(self,obj):
        self.objectives = obj

    def get_name(self):
        return self.name

    def get_constraints(self):
        return self.constraints

    def get_variables(self):
        return self.variables

    def get_parameters(self):
        return self.parameters

    def get_objectives(self):
        return self.objectives

class Expression:
    def __init__(self,node_type,name = None,line = 0):
        self.n_type = node_type
        self.children = Vector()
        if name == None:
            self.name = ""
        else :
            self.name = name
        self.line = line

    def __str__(self):
        string = '['+str(self.n_type)
        if self.name !="":
            string += " , "+str(self.name) 
        if self.children.get_size()==0:
            string += ']'
        else:
            string +=  ' , '+str(self.children)+']'
        return string

    def get_children(self):
        return self.children.get_elements()

    def get_nb_children(self):
        return self.children.get_size()

    def add_child(self,child):
        self.children.add_element(child)

    def set_line(self,line):
        self.line = line

    def get_line(self):
        return self.line

    def set_name(self,name):
        self.name = name

    def get_name(self):
        return self.name

    def get_type(self):
        return self.n_type

class Variable: 
    def __init__(self,name,v_type, unity=None,line = 0):
        self.name = name
        self.v_type = v_type
        self.unity = unity
        self.line = line

    def __str__(self):
        string = "["+str(self.name)+' , '+str(self.v_type)
        if self.unity==None:
            string += ']'
        else :
            string += ' , '+ str(self.unity)+']'
        return string

    def set_line(self,line):
        self.line = line

    def get_line(self):
        return self.line

    def get_type(self):
        return self.v_type

    def get_unity(self):
        return self.unity

    def get_name(self):
        return self.name

class Constraint: 
    def __init__(self,c_type,rhs,lhs,line=0):
        self.c_type = c_type
        self.rhs = rhs
        self.lhs = lhs
        self.line = line

    def __str__(self):
        string = "["+str(self.c_type)+' , '+str(self.rhs)
        string += " , "+str(self.lhs)+']'
        return string

    def get_type(self):
        return self.c_type

    def get_rhs(self):
        return self.rhs

    def get_lhs(self):
        return self.lhs

    def set_line(self,line):
        self.line = line

    def get_line(self):
        return self.line


class Parameter: 
    def __init__(self,name,expression,unity=None,line = 0):
        self.name = name
        self.expression = expression
        self.unity = unity
        self.value = None
        self.line = line

    def __str__(self):
        string = "["+str(self.name)+' , '+str(self.expression)
        if self.unity==None:
            string += ']'
        else :
            string += ' , '+ str(self.unity)+']'
        return string

    def set_line(self,line):
        self.line = line

    def get_line(self):
        return self.line

    def set_value(self,value):
        self.value = value

    def get_expression(self):
        return self.expression

    def get_unity(self):
        return self.unity

    def get_name(self):
        return self.name

    def get_value(self):
        return self.value.get_elements()

class Objective:
    def __init__(self,o_type,expression,line = 0):
        self.o_type = o_type
        self.expression = expression
        self.line = line

    def __str__(self):
        string = "["+str(self.o_type)+','+str(self.expression)+']'
        return string

    def set_line(self,line):
        self.line = line

    def get_line(self):
        return self.line

    def get_expression(self):
        return self.expression

class Identifier:
    def __init__(self,type_id,name_id,value_id=None,expression=None,line=0):
        self.type_id = type_id
        self.name_id = name_id
        self.expression = expression
        self.value_id = value_id
        self.line = line

    def __str__(self):
        string = str(self.name_id)
        if self.value_id !=None:
            string += '.'+str(self.value_id)
        if self.expression != None:
            string+="["+str(self.expression)+']'
        return string

    def name_compare(self,identifier_i):
        equal = False
        if type(identifier_i)== type(self):
            if self.name_id == identifier_i.name_id:
                equal = True
        elif type(identifier_i)==str:
            if self.name_id == identifier_i:
                equal = True
        return equal

    def compare(self,identifier_i):
        equal = False
        if type(identifier_i)== type(self) and self.type_id == identifier_i.type_id:
            if (self.name_id == identifier_i.name_id) and (self.value_id ==identifier_i.value_id):
                equal = True

        return equal                

    def get_name(self):
        return self.name_id

    def get_type(self):
        return self.type_id

    def get_expression(self):
        return self.expression

class Attribute:
    def __init__(self,name_node,name_attribute=None):
        self.node = name_node
        self.attribute = name_attribute

    def __str__(self):
        string = str(self.node)
        if self.attribute!=None:
            string+='.'+str(self.attribute)
        return string

class Link: 
    def __init__(self,attribute,vector):
        self.attribute = attribute
        self.vector = vector

    def __str__(self):
        string = '['+str(self.attribute)+' , '+str(self.vector)+']'
        return string
