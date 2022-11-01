# Copyright (C) 2020 - 2022
# Bardhyl Miftari, Mathias Berger, Hatim Djelassi, Damien Ernst,
# University of Liege .
# Licensed under the MIT License (see LICENSE file).

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
import numpy as np
import os


def check_file_exists(input_file: str):
    if os.path.isfile(input_file) is False:
        print("No such file as "+str(input_file))
        exit(-1)


def move_to_directory(input_file: str):
    """move_to_directory

        takes as input a path to a certain file and moves
        the directory to the one where the file is.

        Args:
            input_file -> string of a file path

        Returns:
            previous directory -> string of the previous directory
            filename -> string of the filename

    """

    check_file_exists(input_file)
    old_directory = os.getcwd()
    directory_path = os.path.dirname(input_file)
    filename = os.path.basename(input_file)

    if directory_path != "":
        os.chdir(directory_path)

    return old_directory, filename


def turn_to_dict(list_nodes: list) -> dict:
    dict_nodes = {}
    for node in list_nodes:
        name = node.get_name()
        if name in dict_nodes:
            error_("The name : "+str(name)
                   + " has already been used at line "
                   + str(dict_nodes[name].get_line())
                   + " redefinition at line "+str(node.get_line()))
        else:
            dict_nodes[name] = node
    return dict_nodes


def flat_nested_list_to_two_level(nested_list_elements):
    all_elements_flat = []
    for node_name, elements in nested_list_elements:
        for element in elements:
            if len(element) != 4 and type(element[0]) != int:
                all_elements_flat += flat_nested_list_to_two_level(element)
            else:
                all_elements_flat.append(element)
    return all_elements_flat


def list_to_string(list_e: list) -> str:
    """list_to_string

        takes as input list of objects and converts them into
        a string of the concatenation

        Args:
            list_e -> list of objects

        Returns:
            string -> string of the concatenation of the string of all objects

    """
    string: str = ""
    for e in list_e:
        string += str(e)+" "
    return string


def update_branch_in_nested_dict(to_update_dict, list_keys,
                                 new_key, to_add_dict):
    if not list_keys:
        to_update_dict[new_key] = to_add_dict
        return [0, to_update_dict]
    else:
        first_key = list_keys.pop(0)
        if first_key in to_update_dict:
            next_level_dict = to_update_dict[first_key]
            code, updated_branch = update_branch_in_nested_dict(next_level_dict,
                                                                list_keys,
                                                                new_key,
                                                                to_add_dict)
            if code == -1:
                return [-1, to_update_dict]

            to_update_dict[first_key] = updated_branch
            return [0, to_update_dict]
        else:
            return [-1, to_update_dict]


def get_branch_in_nested_dict(dictionary, list_keys, not_lower=False):
    accumulator_dict = {}
    level_dict = dictionary
    for key in list_keys:
        if key not in level_dict:
            return [-1, accumulator_dict]

        if key != list_keys[-1] or not not_lower:

            accumulator_dict[key] = level_dict[key]
            level_dict = level_dict[key]
        else:

            nested_dict = level_dict[key]
            intermediate_stopped_dict = dict()
            for nested_key in nested_dict.keys():
                if type(nested_dict[nested_key]) != dict:
                    intermediate_stopped_dict[nested_key] = \
                        nested_dict[nested_key]
            accumulator_dict[key] = intermediate_stopped_dict

    return [0, accumulator_dict]


def get_layer_in_nested_dict(dictionary, list_keys, only_dict=False):
    level_dict = dictionary
    for key in list_keys:
        if key not in level_dict:
            return [-1, level_dict]
        level_dict = level_dict[key]

    if only_dict:
        level_dict_with_only_nested_dicts = {}
        for key in level_dict.keys():
            if type(level_dict[key]) == dict:
                level_dict_with_only_nested_dicts[key] = level_dict[key]
        level_dict = level_dict_with_only_nested_dicts
    return [0, level_dict]


def get_only_objects_in_nested_dict_layer(dictionary):
    only_object_dict = {}
    for key in dictionary.keys():
        if type(dictionary[key]) != dict:
            only_object_dict[key] = dictionary[key]
    return only_object_dict


def read_attributes_in_file(filename):
    with open(filename) as f:
        file_content = f.readlines()
    attributes = []
    for line in file_content:
        line = line.replace("\n", " ")
        line = line.replace(",", " ")
        line = line.replace(";", " ")
        line = line.split()
        attributes += line
    return attributes


def error_(message: str) -> None:
    """error_

        takes as input a string message and exits process
        after printing that message

        Args:
            message -> string message to print

    """
    print(message)

    exit(-1)
