from utils import error_
import numpy as np
import sys

class Time:
    def __init__(self,time_var,expr,line=None):
        if time_var != "T":
            error_("Semantic error:"+str(line)+": Use \"T\""+\
                " as a symbol for the time horizon. \""+ str(time_var)+\
                "\" is not allowed")
        self.time = time_var
        self.expr = expr
        self.value = expr.evaluate_expression([]) 
        self.line = line

    def __str__(self):
        string = 'time: '+str(self.time)+' expr: '+str(self.expr)
        return string

    def get_value(self):
        return self.value

    def get_expression(self):
        return self.expr

    def check(self):
        time_value = self.value

        if type(time_value) == float and time_value.is_integer()==False:
            time_value = int(round(time_value))
            print("WARNING: the time horizon considered is not an int")
            print("The time horizon was rounded to "+str(time_value))
            
        elif type(time_value) == float:
            time_value = int(time_value) 

        if time_value < 0:
            error_("ERROR: the chosen time horizon is negative.")

        elif time_value == 0:
            print("WARNING: the time horizon considered is 0 no operation to be done")
            exit()
        
        self.value = time_value

class TimeInterval:
    def __init__(self,time_var,begin,end,step,line):
        if time_var != "t":
            error_("Semantic error:"+str(line)+": only \"t\""+\
                " can be looped on. Looping \""+ str(time_var)+\
                "\" is not allowed")
        self.name = time_var
        self.begin = begin

        if type(step) == int:
            self.step = step
        else: 
            self.step = step
        self.end = end
        self.line = line

    
    def get_range(self,definitions):
        begin_value = self.begin.evaluate_expression(definitions)
        end_value = self.end.evaluate_expression(definitions)
        if type(self.step) == int:
            step_value = self.step
        else: 
            step_value = self.step.evaluate_expression(definitions)
        
        time_horizon = sys.maxsize

        time_horizon = definitions["T"][0]

        begin_value, end_value,step_value = self.check(begin_value,end_value,step_value,time_horizon)
        return range(begin_value,end_value,step_value)
        

    def get_interval(self):
        return [self.begin,self.step,self.end]
    
    def check(self,begin_value,end_value,step_value,clip=sys.maxsize):
        begin_value = self.convert_type(begin_value,message='begin')
        end_value = self.convert_type(end_value,message="end")
        step_value = self.convert_type(step_value,message="step")

        if end_value < begin_value:
            error_("ERROR: in for loop, the end_value: "+str(self.end)+\
                " is smaller than the begin value "+str(self.begin) + " at line "+\
                    str(self.line))
        
        if begin_value < 0:
            error_("ERROR: in for loop, the begin value: "+str(self.begin)+\
                " is negative at line "+str(self.line))
        
        if end_value < 1:
            error_("ERROR: in for loop, the end value: "+str(self.end)+\
                " is negative or null at line "+str(self.line))

        if step_value < 1:
            error_("ERROR: in for loop, the step value: "+str(self.step)+\
                " is negative or null at line "+str(self.line))
        
        if end_value > clip:
            print("WARNING: in for loop, end exceeds horizon value "+\
                 " end put back to horizon value T at line "+str(self.line))
            end_value = clip

        return begin_value, end_value,step_value
        
    def convert_type(self,value,message = ""):
        if type(value) == float and value.is_integer()==False:
            value = int(round(value))
            print("WARNING: in for loop, "+message+" value "+\
                " is of type float and was rounded to "+str(value)+\
                " at line "+str(self.line))
        elif type(value) == float:
            value = int(value)
        
        return value 


    

