from utils import Vector
from .parent import Symbol
from .expression import Expression
from utils import error_,Vector
import os

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
            if(os.path.isfile('./'+expression))==False:
                error_("No such file as "+str(expression))
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
