# Copyright (C) 2020 - 2022
# Bardhyl Miftari, Mathias Berger, Hatim Djelassi, Damien Ernst,
# University of Liege .
# Licensed under the MIT License (see LICENSE file).

class Type:

    def __init__(self, type_id, line):
    
        self.type = type_id
        self.line = line

    def set_line(self, line):
    
        self.line = line

    def get_line(self):
    
        return self.line

    def get_type(self):
    
        return self.type

    def set_type(self, type_id):
    
        self.type = type_id


class Symbol(Type):
    
    def __init__(self, name, type_id, line):
    
        Type.__init__(self, type_id, line)
        if name is None:

            self.name = ""
        else:

            self.name = name

    def get_name(self):
    
        return self.name

    def set_name(self, name):
    
        self.name = name
