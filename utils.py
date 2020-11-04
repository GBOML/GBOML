
# utils.py
#
# Writer : MIFTARI B
# ------------

class Vector: 
    def __init__(self):
        self.elements = []
        self.n = 0
        self.deleted = []

    def __str__(self):
        string = '['
        for i in range(self.n):
            string = string + ' '+str(self.elements[i])
        string += ']'
        return string

    def __copy__(self):
        v = Vector()
        for i in range(self.n):
            v.add_element(self.elements[i])
        return v

    def add_begin(self,e):
        self.elements.insert(0,e)
        self.n = self.n+1

    def add_element(self,e):
        self.elements.append(e)
        self.n = self.n+1

    def get_elements(self):
        return self.elements

    def get_size(self):
        return self.n

    def delete_last(self):
        element = self.elements.pop()
        self.n = self.n-1
        self.deleted.append(element)