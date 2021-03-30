from compiler.utils import list_to_string,error_

class Program: 
    """
    Program object is composed of: 
    - a list of nodes
    - a Time object
    - a list of Links
    - a list of link constraint arrays
    """


    def __init__(self,vector_n,global_param = [],timescale = None,links = None):
        
        self.vector_nodes = vector_n
        self.time = timescale
        self.links = links
        self.global_param=global_param
        self.link_constraints = []
        self.nb_var_index = 0
        self.var_dict = {}
        self.link_list = []

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
            string += str(self.time)+"\n"
        string += 'All the defined nodes : \n'
        elements = self.vector_nodes
        for i in range(len(self.vector_nodes)):
            string += '\tName : '+ list_to_string(elements[i].get_name())+'\n'
            string += '\t\tParameters : '+ list_to_string(elements[i].get_parameters())+'\n'
            string += '\t\tVariables : '+ list_to_string(elements[i].get_variables())+'\n'
            string += '\t\tConstraints : '+ list_to_string(elements[i].get_constraints())+'\n'
            string += '\t\tObjectives : '+ list_to_string(elements[i].get_objectives())+'\n'

        string += '\nLinks predefined are : '+ str(self.links)
        
        return string

    def get_global_parameters(self):
        return self.global_param

    def get_dict_global_parameters(self):
        dict_param = {}
        for param in self.global_param:
            name = param.get_name()
            if name in dict_param:
                error_("Global parameter "+str(name)+" already defined")
            else : 
                dict_param[name] = param
        
        return dict_param

    def get_time(self):

        return self.time

    def get_nodes(self):
        
        return self.vector_nodes

    def get_number_nodes(self):

        return len(self.vector_nodes)

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
    
    def add_link_constraints(self,c):

        self.link_constraints.append(c)

    def get_number_constraints(self):
        
        sum_constraints = 0
        for node in self.vector_nodes:
            sum_constraints += node.get_nb_constraints_matrix()
        
        return sum_constraints 
    
    def check_objective_existence(self):
        
        nodes = self.vector_nodes
        found = False
        
        for node in nodes:
            objectives = node.get_objectives()
            nb_objectives = len(objectives)
            if nb_objectives != 0:
                found = True
                break

        if found == False:
            error_("ERROR: No objective function was defined")

    def get_nb_var_index(self):
        return self.nb_var_index

    def set_nb_var_index(self,index):
        self.nb_var_index = index

    def set_variables_dict(self,var_dict):
        self.var_dict = var_dict

    def get_variables_dict(self):
        return self.var_dict

    def get_tuple_name(self):
        tuple_names = []

        for node_name in self.var_dict.keys():
            node_var_dict = self.var_dict[node_name]
            all_tuples = []
            for var_name in node_var_dict.keys():
                name_index = [node_var_dict[var_name].get_index(),var_name]
                all_tuples.append(name_index)
            tuple_names.append([node_name,all_tuples])

        return tuple_names

    def add_var_link(self,tuple_list):
        link = []

        for element in tuple_list:
            [node_name,_,identifier,_] = element
            link.append([node_name,str(identifier)])
        
        self.link_list.append(link)

    def get_link_var(self):
        return self.link_list