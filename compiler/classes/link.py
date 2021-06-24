from compiler.utils import error_


class Hyperlink:

    def __init__(self, name, parameters=None, constraints=None, line=0):

        self.name = name
        self.parameters = parameters
        self.constraints = constraints
        self.parameter_dict = None
        self.nb_param = len(parameters)
        self.nb_constraints_expanded = 0
        self.nb_constraints = len(constraints)
        self.constr_factors = []
        self.c_triplet_list = []
        self.variables_used = {}
        self.line = line

    def get_name(self):

        return self.name

    def get_number_parameters(self):

        return self.nb_param

    def get_variables_used(self):

        return self.variables_used

    def add_constraint(self, constr):

        self.constraints.append(constr)

    def set_constraints(self, constraints):

        self.constraints = constraints

    def get_constraints(self):

        return self.constraints

    def set_constraints_matrix(self, list_matrix):

        self.nb_constraints_expanded += len(list_matrix)
        self.c_triplet_list = list_matrix

    def get_constraints_matrix(self):

        return self.c_triplet_list

    def get_number_expanded_constraints(self):

        return self.nb_constraints_expanded

    def get_number_constraints(self):

        return self.nb_constraints

    def add_parameters(self, param):

        self.parameters.append(param)

    def set_parameters(self, parameters):

        self.parameters = parameters

    def get_parameters(self):

        return self.parameters

    def set_parameter_dict(self, param):

        param = param.copy()
        if "global" in param:
            param.pop("global")
        if "GLOBAL" in param:
            param.pop("GLOBAL")
        if "T" in param:
            param.pop("T")
        self.parameter_dict = param

    def get_parameter_dict(self):

        return self.parameter_dict

    def get_dictionary_parameters(self):

        parameters = self.parameters
        all_parameters = dict()
        reserved_names = ["t", "T"]
        for param in parameters:

            name = param.get_name()
            if name in reserved_names:
                error_("Semantic error, variable named " + str(name) +
                       " is not allowed at line " + str(param.get_line()))
            if name not in all_parameters:

                all_parameters[name] = param
            else:

                error_("Semantic error, redefinition of variable " + str(name) + " at line " + str(param.get_line()))

        return all_parameters

    def set_constraint_factors(self, fact_list):

        used_variables = {}
        for constr in fact_list:
            var_list = constr.variables
            nodes_in_constraint = set()
            for node_name, var_name in var_list:
                if node_name not in nodes_in_constraint:
                    nodes_in_constraint.add(node_name)

                if node_name not in used_variables:
                    list_var = [var_name]
                    used_variables[node_name] = list_var
                else:
                    list_var = used_variables[node_name]
                    if var_name not in list_var:
                        list_var.append(var_name)

            if len(nodes_in_constraint) == 1:
                print("Warning : Hyperlink constraint using variables from a single node at line "
                      + str(constr.get_line()))

        self.variables_used = used_variables
        self.constr_factors = fact_list

    def get_constraint_factors(self):

        return self.constr_factors


class Attribute:
    """
    Attribute object is a structure composed of 
    - a node object
    - The node's name 
    - a variable name 
    """

    def __init__(self, name_node: str, name_variable = None, line: int = 0):

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
