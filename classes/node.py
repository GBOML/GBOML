from utils import error_

class Node: 
    def __init__(self,name,line = 0):
        self.name = name
        self.constraints = []
        self.variables = []
        self.parameters = []
        self.objectives = []
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

    def get_dictionary_variables(self):
        variables = self.variables
        all_variables = {}
        reserved_names = ["t","T"]
        for var in variables:
            identifier = var.get_name()
            name = identifier.get_name()
            if name in reserved_names:
                error_("Semantic error, variable named "+str(name)+" is not allowed at line "+str(var.get_line()))

            if name not in all_variables:
                all_variables[name]=identifier
            else : 
                error_("Semantic error, redefinition of variable "+str(name)+" at line "+str(var.get_line()))
        return all_variables

    def get_all_parameters_name(self):
        parameters = self.parameters
        all_parameters = set()
        reserved_names = ["t","T"]
        for param in parameters:
            name = param.get_name()
            if name in reserved_names:
                error_("Semantic error, variable named "+str(name)+" is not allowed at line "+str(param.get_line()))

            if name not in all_parameters:
                all_parameters.add(name)
            else : 
                error_("Semantic error, redefinition of variable "+str(name)+" at line "+str(param.get_line()))
        return all_parameters
