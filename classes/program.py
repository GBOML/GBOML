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