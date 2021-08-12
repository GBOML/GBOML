"""GBOML utils file

Defines useful functions that are used throughout the project.

  Typical usage example:

  filename = "/errors/error.txt"
  old_directory, filename = move_to_directory(filename)
  text_file = open(filename, "r")
  error_messages = text_file.read()
  error_(error_messages)

"""
import sys
import os


def move_to_directory(input_file: str):
    """move_to_directory

        takes as input a path to a certain file and moves the directory to the one where the file is.

        Args:
            input_file -> string of a file path

        Returns:
            previous directory -> string of the previous directory
            filename -> string of the filename

    """

    if os.path.isfile(input_file) is False:
        print("No such file as "+str(input_file))
        exit(-1)

    old_directory = os.getcwd()
    directory_path = os.path.dirname(input_file)
    filename = os.path.basename(input_file)

    if directory_path != "":
        os.chdir(directory_path)

    return old_directory, filename


def list_to_string(list_e: list) -> str:
    """list_to_string

        takes as input list of objects and converts them into a string of the concatenation

        Args:
            list_e -> list of objects

        Returns:
            string -> string of the concatenation of the string of all objects

    """
    string: str = ""
    for e in list_e:
        string += str(e)+" "
    return string


def error_(message: str) -> None:
    """error_

        takes as input a string message and exits process after printing that message

        Args:
            message -> string message to print

    """
    print(message)

    exit(-1)
