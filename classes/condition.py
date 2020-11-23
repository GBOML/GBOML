from .parent import Type
from .expression import Expression

class Condition:
    def __init__(self,type_id,children,line=0):
        Type.__init__(self,type_id,line)
        self.type = type_id
        self.children = children

    def __str__(self):
        string = "["+str(self.type)
        for child in self.children:
            string += ','+str(child)
        string +=']'
        return string

    def add_child(self,c):
        self.children.append(c)
    
    def get_children(self):
        return self.children
    
    def check(self,definitions):
        predicate = False

        if type(self.children[0])==Condition:
            predicate_0 = self.children[0].check(definitions)
            
            if len(self.children)==2:
                predicate_1 = self.children[1].check(definitions)
        
            if self.type == 'and':
                predicate = (predicate_0 and predicate_1)
            elif self.type == 'or':
                predicate = (predicate_0 or predicate_1)
            elif self.type == "not":
                predicate = (not predicate_0)
                
        elif type(self.children[0])==Expression:
            value0 = self.children[0].evaluate_expression(definitions)
            value1 = self.children[1].evaluate_expression(definitions)

            if self.type == "==":
                predicate = (value0 == value1)
            elif self.type == "<=":
                predicate = (value0 <= value1)
            elif self.type == ">=":
                predicate = (value0 >= value1)
            elif self.type == ">":
                predicate = (value0 > value1)
            elif self.type == "<":
                predicate = (value0 < value1)
            elif self.type == "!=":
                predicate = (value0 != value1)

        return predicate
    
    