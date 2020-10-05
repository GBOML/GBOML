
# classes.py
#
# Writer : MIFTARI B
# ------------

from utils import Vector
import os

def error_(string):
    print(string)
    exit(-1)

class Type:
    def __init__(self,type_id,line):
        self.type = type_id
        self.line = line

    def set_line(self,line):
        self.line = line

    def get_line(self):
        return self.line

    def get_type(self):
        return self.type

    def set_type(self,type_id):
        self.type = type_id

class Symbol(Type):
    def __init__(self,name,type_id,line):
        Type.__init__(self, type_id, line)
        if name == None:
            self.name = ""
        else:
            self.name = name

    def get_name(self):
        return self.name

    def set_name(self,name):
        self.name = name


class Program: 
    def __init__(self,vector_n,timescale = None,links = None):
        self.vector_nodes = vector_n
        self.time = timescale
        self.links = links
        self.link_constraints = []
        self.nb_variables = 0

    def __str__(self):
        string = "["+str(self.vector_nodes)
        if self.time != None:
            string += ' , '+str(self.time)

        if self.links ==None:
            string += ']'
        else:
            string += ' , '+str(self.links)+']'

        return string

    def to_string(self):
        string = "Full program\n"
        if self.time != None:
            string += "Time horizon : "+str(self.time.time)+"\n"
            string += "Time step : "+str(self.time.step)+"\n"
        string += 'All the defined nodes : \n'
        elements = self.vector_nodes.get_elements()
        for i in range(self.vector_nodes.get_size()):
            string += '\tName : '+ str(elements[i].get_name())+'\n'
            string += '\t\tParameters : '+ str(elements[i].get_parameters())+'\n'
            string += '\t\tVariables : '+ str(elements[i].get_variables())+'\n'
            string += '\t\tConstraints : '+ str(elements[i].get_constraints())+'\n'
            string += '\t\tObjectives : '+ str(elements[i].get_objectives())+'\n'

        string += '\nLinks predefined are : '+ str(self.links)
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

    def set_link_constraints(self,c):
        self.link_constraints = c

    def get_link_constraints(self):
        return self.link_constraints

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
        self.links = []
        self.v_matrix = None
        self.c_triplet_list = []
        self.objective_list = []

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

    def add_link(self,link):
        self.links.append(link)

    def get_links(self):
        return self.links

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

    def set_variable_matrix(self,X):
        self.v_matrix = X

    def get_variable_matrix(self):
        return self.v_matrix

    def add_constraints_matrix(self,c_matrix):
        self.c_triplet_list.append(c_matrix)

    def get_constraints_matrix(self):
        return self.c_triplet_list

    def add_objective_matrix(self,o):
        self.objective_list.append(o)

    def get_objective_list(self):
        return self.objective_list

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

class Parameter(Symbol): 
    def __init__(self,name,expression,unity=None,line = 0):
        self.vector = None
        if expression == None:
            type_para = "table"
        elif type(expression) == str:
            type_para = "table"
            self.get_values_from_file(expression)
            print(self.vector)
            expression = None
        else:
            type_para = "expression"

        Symbol.__init__(self,name,type_para,line)
        self.expression = expression
        self.unity = unity

    def __str__(self):
        string = "["+str(self.name)+' , '+str(self.expression)
        if self.unity==None:
            string += ']'
        else :
            string += ' , '+ str(self.unity)+']'
        return string

    def get_values_from_file(self,expression):
        self.vector = Vector()
        if type(expression)==str:
            print(os.path.isfile('./'+expression))
            f = open(expression, "r")
            for line in f: 
                line = line.replace("\n","")
                line = line.replace(";","")
                line = line.split(" ")
                print(line)
                for nb in line:
                    print(nb)
                    if nb == "":
                        continue
                    try:
                        number = float(nb)
                    except:
                        error_("file "+expression+" contains values that are not numbers "+nb)
                    expr = Expression('literal',number)
                    self.vector.add_element(expr)

    def get_expression(self):
        return self.expression

    def get_unity(self):
        return self.unity

    def set_vector(self,v):
        self.vector = v

    def get_vector(self):
        return self.vector.get_elements()

class Objective(Type):
    def __init__(self,o_type,expression,line = 0):
        Type.__init__(self,o_type,line)
        self.expression = expression

    def __str__(self):
        string = "["+str(self.type)+','+str(self.expression)+']'
        return string

    def get_expression(self):
        return self.expression

class Identifier(Symbol):
    def __init__(self,type_id,name_id,expression=None,line=0):
        Symbol.__init__(self,name_id,type_id,line)
        self.expression = expression
        self.index = 0

    def __str__(self):
        string = str(self.name)
        if self.expression != None:
            string+="["+str(self.expression)+']'
        return string

    def __copy__(self):
        return Identifier(self.type,self.name,expression=None)

    def name_compare(self,identifier_i):
        equal = False
        if type(identifier_i)== type(self):
            if self.name == identifier_i.name:
                equal = True
        elif type(identifier_i)==str:
            if self.name == identifier_i:
                equal = True
        return equal

    def set_expression(self,expr):
        self.expression = expr

    def get_expression(self):
        return self.expression

    def set_index(self,value):
        self.index = value
        
    def get_index(self):
        return self.index 

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
