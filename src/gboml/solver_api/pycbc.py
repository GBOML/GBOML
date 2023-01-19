from ctypes import cdll, c_void_p, c_int, c_double, c_char_p, POINTER, byref, c_wchar_p, cast
from ctypes.util import find_library

class PyCBC:
    def __init__(self, path=None):
        if path is None:
            path = find_library("cbcSolver")

        self.libCBC = cdll.LoadLibrary(path)

    def Cbc_newModel(self) -> c_void_p:
        """createEnv

        Initializes a C++ CBC environment and returns a ctype pointer
        to the environnement

        Args:

        Returns:
            pointer_to_env (c_void_p) : ctypes pointer to a CBC environment

        """
        self.libCBC.Cbc_newModel.restype = c_void_p
        pointer_to_env = c_void_p(self.libCBC.Cbc_newModel())
        return pointer_to_env

    def Cbc_deleteModel(self, pointer_to_env) -> None:
        """

        Frees a C++ CBC environment

        Args:
            pointer_to_env (c_void_p) : ctypes pointer to a CBC environment

        Returns:

        """
        self.libCBC.Cbc_deleteModel.argtypes = [c_void_p]
        self.libCBC.Cbc_deleteModel(pointer_to_env)

    def Cbc_loadProblem(self, pointer_to_env, numcols, numrows, start_csc, index_csc, value,
                        col_low, col_up, objective, row_lb, row_up) -> None:
        """
        Load a problem (CSC format) in CBC model

        Args:
            pointer_to_env: ctypes pointer to a CBC environment
            numcols: number of columns
            numrows: number of rows
            start_csc: index pointer array in CSC format
            index_csc: index array in CSC format
            value: values of the cofficients in CSC format
            col_low: column lower bound
            col_up: column upper bound
            objective: array of the objective coefficients
            row_lb: array of row lower bound
            row_up: array of row upper bound

        Returns:

        """
        self.libCBC.Cbc_loadProblem.argtypes = [c_void_p, c_int, c_int,
                                                POINTER(c_int),
                                                POINTER(c_int),
                                                POINTER(c_double),
                                                POINTER(c_double),
                                                POINTER(c_double),
                                                POINTER(c_double),
                                                POINTER(c_double),
                                                POINTER(c_double)]
        c_ncols = c_int(numcols)
        c_nrows = c_int(numrows)

        c_start = self.__convert_list_to_c_int(start_csc)
        c_index = self.__convert_list_to_c_int(index_csc)
        c_value = self.__convert_list_to_c_double(value)
        c_clbd = self.__convert_list_to_c_double(col_low)
        c_cubd = self.__convert_list_to_c_double(col_up)
        c_obj = self.__convert_list_to_c_double(objective)
        c_rlbd = self.__convert_list_to_c_double(row_lb)
        c_rubd = self.__convert_list_to_c_double(row_up)

        self.libCBC.Cbc_loadProblem(pointer_to_env, c_ncols, c_nrows,
                                    c_start, c_index, c_value,
                                    c_clbd, c_cubd, c_obj,
                                    c_rlbd, c_rubd)

    def Cbc_setObjSense(self, pointer_to_env, sense: str):
        """
        direction of optimization (1 - minimize, -1 - maximize, 0 - ignore)
        Args:
            pointer_to_env: ctypes pointer to a CBC environment
            sense:  string of either "min" or "max"

        Returns:

        """
        self.libCBC.Cbc_setObjSense.argtypes = [c_void_p, c_double]
        c_value = c_double(0)
        if sense == 'min':
            c_value = c_double(1)
        elif sense == "max":
            c_value = c_double(-1)

        self.libCBC.Cbc_setObjSense(pointer_to_env, c_value)

    def Cbc_getObjSense(self, pointer_to_env) -> str:
        """
        Get sense of current Cbc model

        Args:
            pointer_to_env: ctypes pointer to a CBC environment

        Returns:
            sense <str>: either min max or None
        """
        self.libCBC.Cbc_getObjSense.argtypes = [c_void_p]
        self.libCBC.Cbc_getObjSense.restype = c_double
        c_sense = self.libCBC.Cbc_getObjSense(pointer_to_env)
        if c_sense == 1.0:
            sense = "min"
        elif c_sense == -1.0:
            sense = "max"
        else:
            sense = None
        return sense

    def Cbc_setContinuous(self, pointer_to_env, col: int):
        """
        Sets the column indexed at col in the Cbc model as a continuous
        variable

        Args:
            pointer_to_env: ctypes pointer to a CBC environment
            col: index of column to set as a continuous variable

        Returns:

        """
        self.libCBC.Cbc_setContinuous.argtypes = [c_void_p, c_int]
        c_col = c_int(col)
        self.libCBC.Cbc_setContinuous(pointer_to_env, c_col)

    def Cbc_setInteger(self, pointer_to_env, col: int):
        """
        Sets the column indexed at col in the Cbc model as an integer
        variable

        Args:
            pointer_to_env: ctypes pointer to a CBC environment
            col: index of column to set as an integer variable

        Returns:

        """
        self.libCBC.Cbc_setInteger.argtypes = [c_void_p, c_int]
        c_col = c_int(col)
        self.libCBC.Cbc_setInteger(pointer_to_env, c_col)

    def Cbc_addSOS(self, pointer_to_env, n_rows: int, row_start,
                   col_indices, values, type_v: int):
        """
        Adds SOS constraints to the CBC model

        Args:
            pointer_to_env: ctypes pointer to a CBC environment
            n_rows: number of rows
            row_start: row CSR indices pointer
            col_indices: column indices
            values: coefficients of the variables
            type_v: either type 1 SOS or type 2 SOS

        Returns:

        """
        self.libCBC.Cbc_addSOS.argtypes = [c_void_p,
                                           c_int,
                                           POINTER(c_int),
                                           POINTER(c_int),
                                           POINTER(c_double),
                                           c_int]

        c_n_rows = c_int(n_rows)
        c_nrows = c_int(numrows)
        c_type = c_int(type_v)

        c_start = self.__convert_list_to_c_int(row_start)
        c_index = self.__convert_list_to_c_int(col_indices)
        c_value = self.__convert_list_to_c_double(values)
        self.libCBC.Cbc_addSOS(pointer_to_env, c_n_rows, c_nrows,
                               c_start, c_index, c_value, c_type)

    def Cbc_numberSOS(self, pointer_to_model):
        """
        Returns the number of SOS constraints in the model.

        Args:
            pointer_to_model: ctypes pointer to a CBC environment

        Returns:
            nb_sos <int>: number of SOS constraints

        """
        self.libCBC.Cbc_numberSOS.argtypes = [c_void_p]
        nb_sos = self.libCBC.Cbc_numberSOS(pointer_to_model)
        return nb_sos

    def Cbc_setParameter(self, pointer_to_model, name, value_string):
        """
        Sets a string CBC parameter to a certain string value

        Args:
            pointer_to_model: ctypes pointer to a CBC environment
            name <str>: name of CBC parameter to set
            value_string <str>: value of CBC parameter to set

        Returns:

        """
        self.libCBC.Cbc_setParameter.argtypes = [c_void_p,
                                                 POINTER(c_char),
                                                 POINTER(c_char)]
        c_name = c_wchar_p(name)
        c_value_string = c_wchar_p(value_string)
        self.libCBC.Cbc_setParameter(pointer_to_model, c_name, c_value_string)

    def Cbc_setMaximumSolutions(self, pointer_to_model, nb_solutions: int):
        """
        Sets the maximum number of solutions in CBC solver

        Args:
            pointer_to_model: ctypes pointer to a CBC environment
            nb_solutions <int>: number of solutiosn

        Returns:

        """
        self.libCBC.Cbc_setMaximumSolutions.argtypes = [c_void_p, c_int]
        c_param = c_int(nb_solutions)
        self.libCBC.Cbc_setIntParam(pointer_to_model, c_param)

    def Cbc_setMaximumSeconds(self, pointer_to_model, time: float):
        """
        Sets maximum amount of time taken

        Args:
            pointer_to_model: ctypes pointer to a CBC environment
            time <float>: time in second

        Returns:

        """
        self.libCBC.Cbc_setMaximumSeconds.argtypes = [c_void_p, c_double]
        c_param = c_double(time)
        self.libCBC.Cbc_setMaximumSeconds(pointer_to_model, c_param)

    def Cbc_setAllowableGap(self, pointer_to_model, allowed_gap: float):
        """
        Sets the allowable gap in a CBC model

        Args:
            pointer_to_model: ctypes pointer to a CBC environment
            allowed_gap <float>: value of the gap

        Returns:

        """
        self.libCBC.Cbc_setAllowableGap.argtypes = [c_void_p, c_double]
        c_gap = c_double(allowed_gap)
        self.libCBC.Cbc_setAllowableGap(pointer_to_model, c_gap)

    def Cbc_getAllowableGap(self, pointer_to_model)-> float:
        """
        Get the value of the allowable gap in CBC model

        Args:
            pointer_to_model: ctypes pointer to a CBC environment

        Returns:
            gap_value <float>: value of the allowed gap

        """
        self.libCBC.Cbc_getAllowableGap.argtypes = [c_void_p]
        self.libCBC.Cbc_getAllowableGap.restype = c_double
        gap_value = self.libCBC.Cbc_getAllowableGap(pointer_to_model)
        return gap_value

    def Cbc_setAllowableFractionGap(self, pointer_to_model, allowed_fraction_gap):
        """
        Get the value of the allowable fraction gap in CBC model

        Args:
            pointer_to_model: ctypes pointer to a CBC environment
            allowed_fraction_gap: value of the allowable fraction gap

        Returns:

        """
        self.libCBC.Cbc_setAllowableFractionGap.argtypes = [c_void_p, c_double]
        c_gap = c_double(allowed_fraction_gap)
        self.libCBC.Cbc_setAllowableFractionGap(pointer_to_model, c_gap)

    def Cbc_getAllowableFractionGap(self, pointer_to_model):
        """
        Returns the allowable fraction gap in the model
        Args:
            pointer_to_model: ctypes pointer to a CBC environment

        Returns:
            gap: allowable fraction gap
        """
        self.libCBC.Cbc_getAllowableFractionGap.argtypes = [c_void_p]
        self.libCBC.Cbc_getAllowableFractionGap.restype = c_double
        gap = self.libCBC.Cbc_getAllowableFractionGap(pointer_to_model)
        return gap

    def Cbc_getColSolution(self, pointer_to_model, nb_col):
        """
        Returns the solution of a solved CBC model
        Args:
            pointer_to_model: ctypes pointer to a CBC environment
            nb_col: number of variables in the model

        Returns:
            ouput <list<float>>: array containing the solution
        """
        self.libCBC.Cbc_getColSolution.argtypes = [c_void_p]
        self.libCBC.Cbc_getColSolution.restype = POINTER(c_double)
        output = self.libCBC.Cbc_getColSolution(pointer_to_model)
        output = [output[i] for i in range(nb_col)]
        return output

    def Cbc_printModel(self, pointer_to_model):
        """
        Prints the CBC model
        Args:
            pointer_to_model: ctypes pointer to a CBC environment

        Returns:

        """
        self.libCBC.Cbc_printModel.argtypes = [c_void_p]
        self.libCBC.Cbc_printModel(pointer_to_model)

    def Cbc_solve(self, pointer_to_model):
        """
        Solves the CBC model
        Args:
            pointer_to_model: ctypes pointer to a CBC environment

        Returns:
            status: status code either -1 if stopped before branchAndBound
                                        0 if finished
                                        2 if difficulties were encountered and run abandoned
                                        5 if user event occurred
        """
        self.libCBC.Cbc_solve.argtypes = [c_void_p]
        self.libCBC.Cbc_solve.restype = c_int
        return self.libCBC.Cbc_solve(pointer_to_model)

    def Cbc_getObjValue(self, pointer_to_model):
        """
        Get the objective value of a solved CBC model
        Args:
            pointer_to_model: ctypes pointer to a CBC environment

        Returns:
            value <float>: value of the objective

        """
        self.libCBC.Cbc_getObjValue.argtypes = [c_void_p]
        self.libCBC.Cbc_getObjValue.restype = c_double
        return self.libCBC.Cbc_getObjValue(pointer_to_model)

    def Cbc_status(self, pointer_to_model):
        """
        Get the solver status
        Args:
            pointer_to_model: ctypes pointer to a CBC environment

        Returns:
            status: -1 if stopped before branchAndBound
                     0 if finished
                     2 if difficulties were encountered and run abandoned
                     5 if user event occurred
        """
        self.libCBC.Cbc_status.argtypes = [c_void_p]
        self.libCBC.Cbc_status.restype = c_int
        return self.libCBC.Cbc_status(pointer_to_model)

    def Cbc_isNodeLimitReached(self, pointer_to_model):
        """
        Returns 1 if the node limit was reached
                0 otherwise
        Args:
            pointer_to_model: ctypes pointer to a CBC environment

        Returns:
            status <int>: 1 if true else 0
        """
        self.libCBC.Cbc_isNodeLimitReached.argtypes = [c_void_p]
        self.libCBC.Cbc_isNodeLimitReached.restype = c_int
        return self.libCBC.Cbc_isNodeLimitReached(pointer_to_model)

    def Cbc_isProvenInfeasible(self, pointer_to_model):
        """
        Returns 1 if the problem is infeasible
                0 otherwise
        Args:
            pointer_to_model: ctypes pointer to a CBC environment

        Returns:
            status <int>: 1 if true else 0
        """
        self.libCBC.Cbc_isProvenInfeasible.argtypes = [c_void_p]
        self.libCBC.Cbc_isProvenInfeasible.restype = c_int
        return self.libCBC.Cbc_isProvenInfeasible(pointer_to_model)

    def Cbc_isProvenOptimal(self, pointer_to_model):
        """
        Returns 1 if the problem is proven optimal
                0 otherwise
        Args:
            pointer_to_model: ctypes pointer to a CBC environment

        Returns:
            status <int>: 1 if true else 0
        """
        self.libCBC.Cbc_isProvenOptimal.argtypes = [c_void_p]
        self.libCBC.Cbc_isProvenOptimal.restype = c_int
        return self.libCBC.Cbc_isProvenOptimal(pointer_to_model)

    def Cbc_isSecondsLimitReached(self, pointer_to_model):
        """
        Returns 1 if the seconds limit is reached
                0 otherwise
        Args:
            pointer_to_model: ctypes pointer to a CBC environment

        Returns:
            status <int>: 1 if true else 0
        """
        self.libCBC.Cbc_isSecondsLimitReached.argtypes = [c_void_p]
        self.libCBC.Cbc_isSecondsLimitReached.restype = c_int
        return self.libCBC.Cbc_isSecondsLimitReached(pointer_to_model)

    def Cbc_isSolutionLimitReached(self, pointer_to_model):
        """
        Returns 1 if the solution limit is reached
                0 otherwise
        Args:
            pointer_to_model: ctypes pointer to a CBC environment

        Returns:
            status <int>: 1 if true else 0
        """
        self.libCBC.Cbc_isSolutionLimitReached.argtypes = [c_void_p]
        self.libCBC.Cbc_isSolutionLimitReached.restype = c_int
        return self.libCBC.Cbc_isSolutionLimitReached(pointer_to_model)

    @staticmethod
    def __convert_list_to_c_double(list_doubles: list) -> POINTER(c_double):
        """__convert_list_to_c_double

        Converts a list of floats to a ctypes list of c_double

        Args:
            list_doubles (list) : list of numbers

        Returns:
            c_list_doubles (POINTER(c_double) : list of ctypes c_double

        """
        c_list_doubles = (c_double * len(list_doubles))(*list_doubles)
        return c_list_doubles

    @staticmethod
    def __convert_list_to_c_int(list_ints: list) -> POINTER(c_int):
        """__convert_list_to_c_int

        Converts a list of floats to a ctypes list of c_int

        Args:
            list_ints : list of numbers

        Returns:
            c_list_ints : list of ctypes c_int

        """
        c_list_ints = (c_int * len(list_ints))(*list_ints)
        return c_list_ints

if __name__ == "__main__":
    from scipy.sparse import coo_matrix, csc_matrix
    import numpy as np

    row = np.array([0, 1, 2, 3])
    col = np.array([0, 1, 2, 3])
    data = np.array([1, 2, 1, 1])
    coo_m = coo_matrix((data, (row, col)), shape=(4, 4)).tocsc()
    index, indptr, data = coo_m.indices, coo_m.indptr, coo_m.data
    cbc_lib = PyCBC()
    cbc_model = cbc_lib.Cbc_newModel()
    cbc_lib.Cbc_loadProblem(cbc_model, 4, 4, indptr, index, data,
                            [-1000]*4, [1000]*4, [1]*4, [1]*4, [2]*4)

    cbc_lib.Cbc_setInteger(cbc_model, 1)
    cbc_lib.Cbc_printModel(cbc_model)
    cbc_lib.Cbc_setAllowableGap(cbc_model, 15)
    print(cbc_lib.Cbc_getAllowableGap(cbc_model))

    cbc_lib.Cbc_setObjSense(cbc_model, "min")
    print(cbc_lib.Cbc_getObjSense(cbc_model))
    print(cbc_lib.Cbc_solve(cbc_model))
    print(cbc_lib.Cbc_isProvenOptimal(cbc_model))
    print(cbc_lib.Cbc_getColSolution(cbc_model, 4))
    print(cbc_lib.Cbc_getObjValue(cbc_model))
    cbc_lib.Cbc_deleteModel(cbc_model)