# Copyright (C) 2020 - 2022
# Bardhyl Miftari, Mathias Berger, Hatim Djelassi, Damien Ernst,
# University of Liege .
# Licensed under the MIT License (see LICENSE file).

class RedefinitionError(Exception):
    """Redefinition of protected element"""
    def __init__(self):
        self.message = "Attempt at overwriting a protected field"
        super().__init__(self.message)


class UndefinedIdentifier(Exception):
    """Undefined identifier used"""
    def __init__(self):
        self.message = "Identifier used but not defined"
        super().__init__(self.message)


class OutOfBoundIdentifier(Exception):
    """Trying to access an identifier """
    def __init__(self):
        self.message = "Out of bounds identifier assignment"
        super().__init__(self.message)


class WrongUsage(Exception):
    """Misusage of a function"""
    def __init__(self, message):
        super().__init__(message)
