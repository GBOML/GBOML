
# utils.py
#
# Writer : MIFTARI B
# ------------

def list_to_string(list_e: list) -> str:
    """
    list_to_string function: transforms a list to a string
    INPUT : list_e -> list object
    OUTPUT : string -> str of the concatenation of all the elements of the list
    """
    string: str = ""
    for e in list_e:
        string += str(e)+" "
    return string


def error_(message: str) -> None:
    """
    error_ function: Standard error handling. Prints the error message and returns -1
    INPUT : message -> error message
    """
    print(message)
    exit(-1)
