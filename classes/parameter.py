from .parent import Symbol
from .expression import Expression
from utils import error_,list_to_string
import os

class Parameter(Symbol): 
    def __init__(self,name,expression,line = 0):
        self.vector = None
        if expression == None:
            type_para = "table"
        elif type(expression) == str:
            type_para = "table"
            self.get_values_from_file(expression)
            expression = None
        else:
            type_para = "expression"

        Symbol.__init__(self,name,type_para,line)
        self.expression = expression

    def __str__(self):
        string = "["+str(self.name)+' , '
        if self.expression == None:
            string+= list_to_string(self.vector)
        else:
            string+=str(self.expression)
        string += ']'
        
        return string

    def get_values_from_file(self,expression):
        self.vector = []
        if type(expression)==str:

            if(os.path.isfile('./'+expression))==False:
                error_("No such file as "+str(expression))
            f = open('./'+expression, "r")
            for line in f: 
                line = line.replace("\n"," ")
                line = line.replace(","," ")
                line = line.replace(";"," ")
                line = line.split(" ")
                for nb in line:
                    if nb == "":
                        continue
                    try:
                        number = float(nb)
                    except:
                        error_("file "+expression+" contains values that are not numbers "+nb)
                    expr = Expression('literal',number)
                    self.vector.append(expr)

    def get_expression(self):
        return self.expression

    def set_vector(self,v):
        self.vector = v

    def get_vector(self):
        return self.vector
