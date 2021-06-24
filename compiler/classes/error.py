
class RedefinitionError(Exception):
    """Redefinition of protected element"""
    def __init__(self):
        self.message = "Attempt at overwriting a protected field"
        super().__init__(self.message)
