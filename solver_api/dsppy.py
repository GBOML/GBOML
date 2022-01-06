"""
    Python class interface for Argonne National Laboratory (USA)'s Decomposition of Structured Programs (DSP)
    implemented by Miftari B and Berger Mathias from Uliege (Belgium).
    This interface provides a basic python mapping for all the deterministic functions present in DspCInterface.h

    example :

        from DSPpy import DSPpy
        dsp = DSPpy()
        pointer_to_env = dsp.createEnv()
        dsp.freeEnv(pointer_to_env)

"""

from ctypes import *
from ctypes.util import find_library


class DSPpy:
    """
    DSPpy is the python class interface with libDSP.so
    Note that : libDSP.so (or mac equivalent) shall be on the library path
    This implementation was not tested on Windows as DSP itself was not tested on windows

    For DSP installation steps, please refer to :
    - https://github.com/Argonne-National-Laboratory/DSP

    """

    def __init__(self):
        """__init__

        Loads the shared DSP library and returns a DSPpy object which contains an interface
        to the different functions defined in DSPCInterface.h

        Args:

        Returns:
            DSPpy object

        """
        self.libDSP = cdll.LoadLibrary(find_library("DSP"))

    def createEnv(self):
        """createEnv

        Initializes a C++ a DSP environment and returns a ctype pointer to the environnement

        Args:

        Returns:
            pointer_to_env (c_void_p) : ctypes pointer to a DSP environment

        """
        self.libDSP.createEnv.restype = c_void_p
        pointer_to_env = c_void_p(self.libDSP.createEnv())
        return pointer_to_env

    def freeEnv(self, pointer_to_env):
        """freeEnv

        Frees a C++ DSP environment

        Args:
            pointer_to_env (c_void_p) : ctypes pointer to a DSP environment

        Returns:

        """
        self.libDSP.freeEnv.argtypes = [c_void_p]
        self.libDSP.freeEnv(byref(pointer_to_env))

    def loadBlockProblem(self, pointer_to_env, id: int, ncols: int, nrows: int, numels: int, start: list, index: list,
                         value: list, clbd: list, cubd: list, coltype: list, obj: list, rlbd: list, rubd: list):
        """loadBlockProblem

        Loads a block in multiple block structured problem. The loaded block is composed of a CSR form constraint
        matrix, an upper and lower bound on rows and columns, columns types and an objective vector.

        Args:
            pointer_to_env (c_void_p) : ctypes pointer to a DSP environment
            id (int) : number that identifies the block (0 is the master block)
            ncols (int) : total number of columns in the constraint matrix
            nrows (int) : number of lines in the loaded block constraint matrix
            numels (int) : number of values in the CSR matrix
            start (list <int>) : CSR format index pointer array of the constraint matrix
            index (list <int>) : CSR format index array of the constraint matrix
            value (list <float>) : CSR format data array of the constraint matrix
            clbd (list <float>) : column lower bound
            cubd (list <float>) : column upper bound
            coltype (list <str>) : list of each columns' type
                                   (respectively "I" for interger, "B" for binary and "C" for continuous)
            obj (list <float>) : objective vector (the objective vector must be
                                 the one of the master problem for the subproblems)
            rlbd (list <float>) : row lower bounds
            rubd (list <float>) : row upper bounds

        Returns:

        """

        self.libDSP.loadBlockProblem.argtypes = [c_void_p, c_int, c_int, c_int, c_int, POINTER(c_int), POINTER(c_int),
                                                 POINTER(c_double), POINTER(c_double), POINTER(c_double),
                                                 POINTER(c_char), POINTER(c_double), POINTER(c_double),
                                                 POINTER(c_double)]
        c_id = c_int(id)
        c_ncols = c_int(ncols)
        c_nrows = c_int(nrows)
        c_numels = c_int(numels)

        c_start = self.__convert_list_to_c_int(start)
        c_index = self.__convert_list_to_c_int(index)
        c_value = self.__convert_list_to_c_double(value)
        c_clbd = self.__convert_list_to_c_double(clbd)
        c_cubd = self.__convert_list_to_c_double(cubd)
        c_coltype = self.__convert_column_type_to_c_char(coltype)
        c_obj = self.__convert_list_to_c_double(obj)
        c_rlbd = self.__convert_list_to_c_double(rlbd)
        c_rubd = self.__convert_list_to_c_double(rubd)

        self.libDSP.loadBlockProblem(pointer_to_env, c_id, c_ncols, c_nrows, c_numels,
                                     c_start, c_index, c_value, c_clbd, c_cubd,
                                     c_coltype, c_obj, c_rlbd, c_rubd)

    def printModel(self, pointer_to_env):
        """printModel

        prints the model contained in the DSP environment pointer

        Args:
            pointer_to_env (c_void_p) : ctypes pointer to a DSP environment

        Returns:

        """
        self.libDSP.printModel.argtypes = [c_void_p]
        self.libDSP.printModel(pointer_to_env)

    def getCpuTime(self, pointer_to_env):
        """getCpuTime

        prints the resolution CPU time

        Args:
            pointer_to_env (c_void_p) : ctypes pointer to a solved DSP environment

        Returns:
            cpu_time (int) : CPU time spend in the solving
        """
        self.libDSP.getCpuTime.argtypes = [c_void_p]
        self.libDSP.getCpuTime.restype = c_double
        cpu_time = self.libDSP.getCpuTime(pointer_to_env)
        return cpu_time

    def getDualBound(self, pointer_to_env):
        """getDualBound

        retrieves the dual bound out of a resolved DSP environment

        Args:
            pointer_to_env (c_void_p) : ctypes pointer to a solved DSP environment

        Returns:
            dual_bound (float) : Dual bound of the solution
        """
        self.libDSP.getDualBound.argtypes = [c_void_p]
        self.libDSP.getDualBound.restype = c_double
        dual_bound = self.libDSP.getDualBound(pointer_to_env)
        return dual_bound

    def getDualSolution(self, pointer_to_env, ncols):
        """getDualSolution

        retrieves the dual solution out of a resolved DSP environment

        Args:
            pointer_to_env (c_void_p) : ctypes pointer to a solved DSP environment
            ncols (int) : number of columns in the optimization problem

        Returns:
            solution (float) : Dual solution
        """
        self.libDSP.getDualSolution.argtypes = [c_void_p, c_int, POINTER(c_double)]
        c_ncols = c_int(ncols)
        c_solution = self.__convert_list_to_c_double([0] * ncols)
        self.libDSP.getDualSolution(pointer_to_env, c_ncols, c_solution)
        solution = self.__convert_to_list(c_solution)
        return solution

    def getPrimalBound(self, pointer_to_env):
        """getPrimalBound

        retrieves the primal bound out of a resolved DSP environment

        Args:
            pointer_to_env (c_void_p) : ctypes pointer to a solved DSP environment

        Returns:
            primal_bound (float) : Primal bound of the solution
        """
        self.libDSP.getPrimalBound.argtypes = [c_void_p]
        self.libDSP.getPrimalBound.restype = c_double
        primal_bound = self.libDSP.getPrimalBound(pointer_to_env)
        return primal_bound

    def getPrimalSolution(self, pointer_to_env, ncols):
        """getPrimalSolution

        retrieves the primal solution out of a resolved DSP environment

        Args:
            pointer_to_env (c_void_p) : ctypes pointer to a solved DSP environment
            ncols (int) : number of columns in the optimization problem

        Returns:
            solution (float) : Primal solution
        """
        self.libDSP.getPrimalSolution.argtypes = [c_void_p, c_int, POINTER(c_double)]
        c_ncols = c_int(ncols)
        c_solution = self.__convert_list_to_c_double([0] * ncols)
        self.libDSP.getPrimalSolution(pointer_to_env, c_ncols, c_solution)
        solution = self.__convert_to_list(c_solution)
        return solution

    def getNumIterations(self, pointer_to_env):
        """getNumIterations

        retrieves the number of iterations needed to solve DSP environment

        Args:
            pointer_to_env (c_void_p) : ctypes pointer to a solved DSP environment

        Returns:
            nb_iteration (int) : Number of iterations taken
        """
        self.libDSP.getNumIterations.argtypes = [c_void_p]
        self.libDSP.getNumIterations.restype = c_int
        nb_iteration = self.libDSP.getNumIterations(pointer_to_env)
        return nb_iteration

    def getStatus(self, pointer_to_env):
        """getStatus

        retrieves the solved DSP environment's status

        Args:
            pointer_to_env (c_void_p) : ctypes pointer to a solved DSP environment

        Returns:
            status (int) : solution status code
        """
        self.libDSP.getStatus.argtypes = [c_void_p]
        self.libDSP.getStatus.restype = c_int
        status = self.libDSP.getStatus(pointer_to_env)
        return status

    def getTotalNumCols(self, pointer_to_env):
        """getTotalNumCols

        retrieves the total number of columns in a DSP environment

        Args:
            pointer_to_env (c_void_p) : ctypes pointer to a solved DSP environment

        Returns:
            nb_col (int) : number of columns in the environment
        """
        self.libDSP.getTotalNumCols.argtypes = [c_void_p]
        self.libDSP.getTotalNumCols.restype = c_int
        nb_col = self.libDSP.getTotalNumCols(pointer_to_env)
        return nb_col

    def getTotalNumRows(self, pointer_to_env):
        """getTotalNumRows

        retrieves the total number of rows in a DSP environment

        Args:
            pointer_to_env (c_void_p) : ctypes pointer to a solved DSP environment

        Returns:
            nb_rows (int) : number of rows in the environment
        """
        self.libDSP.getTotalNumRows.argtypes = [c_void_p]
        self.libDSP.getTotalNumRows.restype = c_int
        nb_rows = self.libDSP.getTotalNumRows(pointer_to_env)
        return nb_rows

    def getWallTime(self, pointer_to_env):
        """getWallTime

        prints the resolution wall time

        Args:
            pointer_to_env (c_void_p) : ctypes pointer to a solved DSP environment

        Returns:
            wall_time (int) : Wall time spend in the solving
        """
        self.libDSP.getWallTime.argtypes = [c_void_p]
        self.libDSP.getWallTime.restype = c_double
        wall_time = self.libDSP.getWallTime(pointer_to_env)
        return wall_time

    def updateBlocks(self, pointer_to_env):
        """updateBlocks

        Once all the blocks loaded, update blocks updates the final fields of a DSP environment
        to make it ready for resolution

        Args:
            pointer_to_env (c_void_p) : ctypes pointer to a loaded DSP environment

        Returns:

        """
        self.libDSP.updateBlocks.argtypes = [c_void_p]
        self.libDSP.updateBlocks(pointer_to_env)

    def solveDe(self, pointer_to_env):
        """solveDe

        Solves a DSP environment using the Extensive Form method

        Args:
            pointer_to_env (c_void_p) : ctypes pointer to a loaded DSP environment

        Returns:

        """
        self.libDSP.solveDe.argtypes = [c_void_p]
        self.libDSP.solveDe(pointer_to_env)

    def solveDw(self, pointer_to_env):
        """solveDw

        Solves a DSP environment using the Dantzig Wolf method

        Args:
            pointer_to_env (c_void_p) : ctypes pointer to a loaded DSP environment

        Returns:

        """
        self.libDSP.solveDw.argtypes = [c_void_p]
        self.libDSP.solveDw(pointer_to_env)

    @staticmethod
    def __convert_to_list(c_list):
        """__convert_to_list

        Converts a list of ctypes elements to a python list of elements

        Args:
            c_list : ctypes list of values

        Returns:
            list_values : python list of values

        """
        list_values = []
        for c_value in c_list:
            list_values.append(c_value)
        return list_values

    @staticmethod
    def __convert_column_type_to_c_char(list_char: list):
        """__convert_column_type_to_c_char

        Converts a list of strings (containing 'B', 'I' and 'C') to ctypes list of char equivalent

        Args:
            list_char : list of characters

        Returns:
            c_list_char : list of ctypes char

        """
        converted_char = []
        for char_i in list_char:
            if char_i == "I":
                converted_char.append(int(73))
            elif char_i == "B":
                converted_char.append(int(66))
            elif char_i == "C":
                converted_char.append(int(67))
            else:
                raise ValueError("Unknown character " + str(char_i))
        c_list_char = (c_char * len(converted_char))(*converted_char)
        return c_list_char

    @staticmethod
    def __convert_list_to_c_double(list_doubles: list):
        """__convert_list_to_c_double

        Converts a list of floats to a ctypes list of c_double

        Args:
            list_doubles : list of numbers

        Returns:
            c_list_doubles : list of ctypes c_double

        """
        print(list_doubles)
        c_list_doubles = (c_double * len(list_doubles))(*list_doubles)
        return c_list_doubles

    @staticmethod
    def __convert_list_to_c_int(list_ints: list):
        """__convert_list_to_c_int

        Converts a list of floats to a ctypes list of c_int

        Args:
            list_ints : list of numbers

        Returns:
            c_list_ints : list of ctypes c_int

        """
        c_list_ints = (c_int * len(list_ints))(*list_ints)
        return c_list_ints
