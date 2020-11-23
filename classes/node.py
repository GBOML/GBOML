from utils import Vector

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
        self.nb_constraint_matrix = 0

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
        self.nb_constraint_matrix += 1
        self.c_triplet_list.append(c_matrix)

    def get_constraints_matrix(self):
        return self.c_triplet_list

    def add_objective_matrix(self,o):
        self.objective_list.append(o)

    def get_objective_list(self):
        return self.objective_list

    def get_nb_constraints_matrix(self):
        return self.nb_constraint_matrix