# Copyright (C) 2020 - 2022
# Bardhyl Miftari, Mathias Berger, Hatim Djelassi, Damien Ernst,
# University of Liege .
# Licensed under the MIT License (see LICENSE file).

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

            error_("Semantic error:"+str(line)+": Use \"T\"" +
                   " as a symbol for the time horizon. \"" + str(time_var) +
                   "\" is not allowed")
        self.time = time_var
        self.expr = expr
        self.value = expr.evaluate_expression({}) 
        self.line = line

    def __str__(self) -> str:

        string = 'Time Horizon: '+str(self.time)+'\texpr: '+str(self.expr)

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
            print("The time horizon was rounded to "+str(time_value))
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
                   "and can not be overwritten at line "+str(line))

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
    
    def get_range(self, definitions: dict, clip: int = sys.maxsize) -> range:

        begin_value = self.begin.evaluate_expression(definitions)
        end_value = self.end.evaluate_expression(definitions)
        if type(self.step) == int:

            step_value = self.step
        else:

            step_value = self.step.evaluate_expression(definitions)

        begin_value, end_value, step_value = self.check(begin_value,
                                                        end_value,
                                                        step_value, clip)

        return range(begin_value, end_value+1, step_value)

    def get_interval(self) -> list:

        return [self.begin, self.step, self.end]
    
    def check(self, begin_value, end_value, step_value,
              clip: int = sys.maxsize) -> tuple:

        begin_value = self.convert_type(begin_value, message='begin')
        end_value = self.convert_type(end_value, message="end")
        step_value = self.convert_type(step_value, message="step")
        if end_value < begin_value:

            error_("ERROR: in for loop, the end_value: "+str(self.end) +
                   " is smaller than the begin value "+str(self.begin)
                   + " at line " + str(self.line))

        if step_value < 1:

            error_("ERROR: in for loop, the step value: "+str(self.step)
                   + " is negative or null at line "+str(self.line))
        if end_value+1 > clip:

            print("WARNING: in for loop, end exceeds horizon value " +
                  " end put back to horizon value T at line "+str(self.line))
            end_value = clip

        return begin_value, end_value, step_value
        
    def convert_type(self, value, message: str = "") -> int:
        
        if type(value) == float and value.is_integer() is False:

            value = int(round(value))
            print("WARNING: in for loop, "+message+" value "
                  + " is of type float and was rounded to "+str(value)
                  + " at line "+str(self.line))
        elif type(value) == float:

            value = int(value)
        
        return value
