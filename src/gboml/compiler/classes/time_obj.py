# Copyright (C) 2020 - 2022
# Bardhyl Miftari, Mathias Berger, Hatim Djelassi, Damien Ernst,
# University of Liege .
# Licensed under the MIT License (see LICENSE file).
import numpy as np

from gboml.compiler.utils import error_
from .expression import Expression
import sys


class Time:
    """
    Time object is a structure composed of 
    - a variable name 
    - a right handside expression
    - a value (evaluation of the right handside)
    """

    def __init__(self, time_var: str, expr: Expression, line: int = None):

        assert type(time_var) == str, \
            "Internal error: expected string for Time identifier"
        assert type(expr) == Expression, \
            "Internal error: unknown type for expression in Time object"
        if time_var != "T":
            error_("Semantic error:" + str(line) + ": Use \"T\"" +
                   " as a symbol for the time horizon. \"" + str(time_var) +
                   "\" is not allowed")
        self.time = time_var
        self.expr = expr
        self.value = expr.evaluate_expression({})
        self.line = line

    def __str__(self) -> str:

        string = 'Time Horizon: ' + str(self.time) + '\texpr: ' + str(self.expr)

        return string

    def get_line(self):
        return self.line

    def get_name(self):

        return self.time

    def set_value(self, value):

        self.value = value

    def get_value(self) -> float:

        return self.value

    def get_expression(self) -> Expression:

        return self.expr

    def check(self) -> None:

        time_value = self.value
        if type(time_value) == float and time_value.is_integer() is False:

            time_value = int(round(time_value))
            print("WARNING: the time horizon considered is not an int")
            print("The time horizon was rounded to " + str(time_value))
        elif type(time_value) == float:

            time_value = int(time_value)
        if time_value < 0:

            error_("ERROR: the chosen time horizon is negative.")
        elif time_value == 0:

            print("WARNING: the time horizon considered is 0")
        self.value = time_value


class TimeInterval:
    """
    Time Interval object is a structure composed of 
    - a variable name 
    - a begin expression
    - an end expression 
    - a step expression or int if not defined
    """

    def __init__(self, time_var: str, begin: Expression,
                 end: Expression, step, line: int):

        assert type(time_var) == str, \
            "Internal error: expected string for TimeInterval identifier"
        assert type(begin) == Expression, \
            "Internal error: unknown type for begin in TimeInterval object"
        assert type(end) == Expression, \
            "Internal error: unknown type for end in TimeInterval object"
        assert type(step) == Expression or type(step) == int, \
            "Internal error: unknown type for step in TimeInterval object"
        self.name = time_var
        if time_var == "t":
            error_("ERROR: t is a reserved keyword "
                   "and can not be overwritten at line " + str(line))

        self.begin = begin
        if type(step) == int:

            self.step = step
        else:

            self.step = step
        self.end = end
        self.line = line

    def __copy__(self):

        time_int = TimeInterval(self.name, self.begin,
                                self.end, self.step, self.line)

        return time_int

    def get_begin(self):

        return self.begin

    def get_step(self):

        return self.step

    def get_end(self):

        return self.end

    def get_index_name(self):

        return self.name

    def get_range(self, definitions: dict, clip: int = sys.maxsize,
                  default_type="ast", list_indexes=None) -> range:

        if list_indexes is None:
            list_indexes = []

        if default_type != "ast":
            begin_value = self.begin.evaluate_expression(definitions)
            end_value = self.end.evaluate_expression(definitions)
            if type(self.step) == int:

                step_value = self.step
            else:

                step_value = self.step.evaluate_expression(definitions)

            begin_value, end_value, step_value = self.check_sizes(begin_value,
                                                                  end_value,
                                                                  step_value,
                                                                  clip=clip)

            return range(begin_value, end_value + 1, step_value)
        else:
            begin_value = eval(self.begin.turn_to_python_expression(),
                               definitions, {})
            end_value = eval(self.end.turn_to_python_expression(),
                             definitions, {})
            if type(self.step) == int:

                step_value = self.step
            else:

                step_value = eval(self.step.turn_to_python_expression(),
                                  definitions, {})

            begin_value, end_value, step_value = self.check_sizes(begin_value,
                                                                  end_value,
                                                                  step_value,
                                                                  clip=clip)

            if isinstance(begin_value, np.ndarray):
                all_range = []
                max_length = 0
                number_of_repeats = len(definitions[list_indexes[0]])
                for begin, end, step in zip(begin_value, end_value, step_value):
                    current_array = np.arange(begin, end+1, step)
                    max_length = max(max_length, len(current_array))
                    all_range.append(current_array)
                returned_range = np.full((number_of_repeats, max_length), np.nan)
                for i in range(number_of_repeats):
                    returned_range[i][:len(all_range[i])] = all_range[i]

            elif list_indexes:
                number_of_repeats = len(definitions[list_indexes[0]])
                all_range = np.arange(begin_value, end_value + 1, step_value)
                returned_range = all_range + np.zeros((number_of_repeats, 1))
            else:
                returned_range = range(begin_value, end_value + 1, step_value)

            return returned_range

    def get_interval(self) -> list:

        return [self.begin, self.step, self.end]

    def check_sizes(self, begin_value, end_value, step_value, clip: int = sys.maxsize):

        begin_value = self.convert_type(begin_value, message='begin')
        end_value = self.convert_type(end_value, message="end")
        step_value = self.convert_type(step_value, message="step")
        nb_iterations = 1
        if isinstance(begin_value, np.ndarray) or isinstance(end_value, np.ndarray) or \
                isinstance(step_value, np.ndarray):

            size_begin = 1
            size_end = 1
            size_step = 1
            if isinstance(begin_value, np.ndarray):
                size_begin = len(begin_value)
                if size_begin == 1:
                    begin_value = begin_value[0]
            if isinstance(end_value, np.ndarray):
                size_end = len(end_value)
                if size_end == 1:
                    end_value = end_value[0]
            if isinstance(step_value, np.ndarray):
                size_step = len(step_value)
                if size_step == 1:
                    step_value = step_value[0]
            nb_iterations = max(nb_iterations, size_end, size_step, size_begin)

            if size_begin == 1:
                temp_array = np.zeros(nb_iterations, dtype=int)
                temp_array.fill(begin_value)
                begin_value = temp_array
            if size_end == 1:
                temp_array = np.zeros(nb_iterations, dtype=int)
                temp_array.fill(end_value)
                end_value = temp_array
            if size_step == 1:
                temp_array = np.zeros(nb_iterations, dtype=int)
                temp_array.fill(step_value)
                step_value = temp_array
            begin_value, end_value, step_value = self.check_triplet_array(begin_value, end_value, step_value)
        else:
            begin_value, end_value, step_value = self.check_triplet(begin_value, end_value, step_value, clip)
        return begin_value, end_value, step_value

    def check_triplet(self, begin_value, end_value, step_value,
              clip: int = sys.maxsize) -> tuple:

        if end_value < begin_value:
            error_("ERROR: in for loop, the end_value: " + str(self.end) +
                   " is smaller than the begin value " + str(self.begin)
                   + " at line " + str(self.line))

        if step_value < 1:
            error_("ERROR: in for loop, the step value: " + str(self.step)
                   + " is negative or null at line " + str(self.line))
        if end_value + 1 > clip:
            print("WARNING: in for loop, end exceeds horizon value " +
                  " end put back to horizon value T at line " + str(self.line))
            end_value = clip

        return begin_value, end_value, step_value

    def check_triplet_array(self, begin_value: np.ndarray, end_value:np.ndarray, step_value: np.ndarray,
              clip: int = sys.maxsize) -> tuple:

        if (end_value < begin_value).any():
            error_("ERROR: in for loop, the end_value: " + str(self.end) +
                   " is smaller than the begin value " + str(self.begin)
                   + " at line " + str(self.line))

        if (step_value < 1).any():
            error_("ERROR: in for loop, the step value: " + str(self.step)
                   + " is negative or null at line " + str(self.line))
        if (end_value + 1 > clip).any():
            print("WARNING: in for loop, end exceeds horizon value " +
                  " end put back to horizon value T at line " + str(self.line))
            end_value = np.clip(end_value, a_max=clip)

        return begin_value, end_value, step_value

    def convert_type(self, value, message: str = "") -> int:

        if type(value) == float and value.is_integer() is False:

            value = int(round(value))
            print("WARNING: in for loop, " + message + " value "
                  + " is of type float and was rounded to " + str(value)
                  + " at line " + str(self.line))
        elif type(value) == float:

            value = int(value)

        #elif isinstance(value, np.ndarray):
        #    value = np.array(value, dtype=np.int64)

        return value

    def turn_name_to_python_expression(self):
        import ast
        name = ast.Name(id=self.name, ctx=ast.Store())
        return name

    def get_python_range(self):
        import ast
        arguments = [self.begin.to_python_ast()]
        new_end = Expression("+")
        new_end.add_child(self.end)
        new_end.add_child(Expression('literal', 1))
        arguments.append(new_end.to_python_ast())
        if self.step is not None and type(self.step) == Expression:
            arguments.append(self.step.to_python_ast())
        elif self.step is not None and type(self.step) == int:
            arguments.append(ast.Constant(value=self.step, kind=None))
        return arguments
