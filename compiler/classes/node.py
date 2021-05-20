from compiler.utils import error_

class Node: 
    """
    Node object is composed of: 
    - list of constraints
    - list of parameters
    - list of objectives 
    - list of variables
    - list of links related to the node
    - variable matrix (each column is an identifier of one variables)
    - triplet [array A, sign , b] for constraints
    - list of objective arrays
    - counter for number of constraints
    - all parameters dictionary [name, [values]]
    """

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
        self.param_dict = None
        self.constr_factors = []
        self.obj_factors = []

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

    def set_objective_factors(self,fact_list):
        self.obj_factors = fact_list

    def set_constraint_factors(self,fact_list):
        self.constr_factors = fact_list

    def get_objective_factors(self):
        return self.obj_factors

    def get_constraint_factors(self):
        return self.constr_factors

    def set_parameter_dict(self,param):
        
        param = param.copy()

        if "global" in param: 
            param.pop("global")
        
        if "GLOBAL" in param:
            param.pop("GLOBAL")
        
        if "T" in param:
            param.pop("T")
        
        self.param_dict = param

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

    def get_number_constraints(self):

        return len(self.constraints)

    def get_number_expanded_constraints(self):

        return len(self.c_triplet_list)

    def get_parameter_dict(self):

        return self.param_dict

    def get_variables(self):
        
        return self.variables

    def get_number_variables(self):

        return len(self.variables)

    def get_variable_names(self):

        names = []
        for var in self.variables:
            names.append(var.get_name().get_name())
        return names

    def get_parameters(self):
        
        return self.parameters

    def get_number_parameters(self):

        return len(self.parameters)

    def get_objectives(self):
        
        return self.objectives

    def get_number_objectives(self):

        return len(self.objectives)

    def get_number_expanded_objectives(self):

        return len(self.objective_list)

    def set_variable_matrix(self,X):
        
        self.v_matrix = X

    def get_variable_matrix(self):
        
        return self.v_matrix

    def set_constraints_matrix(self,list_matrix):
        self.nb_constraint_matrix = len(list_matrix) 
        self.c_triplet_list = list_matrix

    def add_constraints_matrix(self,c_matrix):
        
        self.nb_constraint_matrix += 1
        self.c_triplet_list.append(c_matrix)

    def get_constraints_matrix(self):
        
        return self.c_triplet_list

    def set_objective_matrix(self,o):
        self.objective_list = o

    def add_objective_matrix(self,o):
        
        self.objective_list.append(o)

    def get_objective_list(self):
        
        return self.objective_list

    def get_nb_constraints_matrix(self):
        
        return self.nb_constraint_matrix

    def get_dictionary_variables(self,get_type = "all"):
        
        variables = self.variables
        all_variables = {}
        reserved_names = ["t","T"]
        for var in variables:

            v_type = var.get_type()
            if get_type == "external" and v_type =="internal":
                continue
            if get_type == "internal" and v_type == "external":
                continue
            
            identifier = var.get_identifier()
            name = identifier.get_name()
            if name in reserved_names:
                error_("Semantic error, variable named "+str(name)+" is not allowed at line "+str(var.get_line()))

            if name not in all_variables:
                all_variables[name]=identifier
            else : 
                error_("Semantic error, redefinition of variable "+str(name)+" at line "+str(var.get_line()))
        
        return all_variables

    def get_dictionary_parameters(self):
        
        parameters = self.parameters
        all_parameters = dict()
        reserved_names = ["t","T"]
        for param in parameters:
            name = param.get_name()
            if name in reserved_names:
                error_("Semantic error, variable named "+str(name)+" is not allowed at line "+str(param.get_line()))

            if name not in all_parameters:
                all_parameters[name]=param
            else : 
                error_("Semantic error, redefinition of variable "+str(name)+" at line "+str(param.get_line()))
        
        return all_parameters
