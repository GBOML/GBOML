from ctypes import cdll, c_void_p, c_int, c_double, c_char_p, POINTER, byref
from ctypes.util import find_library

class PyHighs:

   def __init__(self, path=None):
      if path is None:
         self.highslib = cdll.LoadLibrary(find_library("highs"))
      else:
         self.highslib = cdll.LoadLibrary(path)

   def Highs_create(self) -> c_void_p:
      """Highs_create

      Create a HiGHS model and return a ctypes pointer to it. Call
      `Highs_destroy` on the returned pointer to clean up allocated memory.

      Args:

      Returns:
         pointer_to_model (c_void_type): ctypes pointer to HiGHS model

      """
      self.highslib.Highs_create.restype = c_void_p
      pointer_to_model = c_void_p(self.highslib.Highs_create())
      return pointer_to_model

   def Highs_destroy(self, pointer_to_model: c_void_p) -> None:
      """Highs_destroy

      Destroy HiGHS model created by `Highs_create` and free all
      corresponding memory. Future calls using the pointer to HiGHS model are
      not allowed.

      Args:
         pointer_to_model (c_void_type): ctypes pointer to HiGHS model

      Returns:

      """
      self.highslib.Highs_destroy.argtypes = [c_void_p]
      self.highslib.Highs_destroy(pointer_to_model)

   def Highs_passLp(self, pointer_to_model: c_void_p, num_col: int,
                    num_row: int, num_nz:int, a_format: int, sense: int,
                    offset: float, col_cost: list, col_lower: list,
                    col_upper: list, row_lower: list, row_upper: list,
                    a_start:list, a_index: list, a_value: list) -> int:
      """Highs_passLp

      Pass a LP model to HiGHS in a single function call.

      Args:
         pointer_to_model (c_void_type): ctypes pointer to Highs model
         num_col (int): the number of columns in the constraint matrix
         num_row (int): the number of rows in the constraint matrix
         num_nz (int): the number of elements in the constraint matrix
         a_format (int): the format of the constraint matrix (CSC if a_format =
                          1 and CSR if a_format = 2)
         sense (int): the optimization sense
         offset (float): the constant term in the objective function
         col_cost (list <float>): array of length num_col with the objective
                                  coefficients
         col_lower (list <float>): array of length num_col with the lower
                                   column bounds
         col_upper (list <float>): array of length num_col with the upper column
                                   bounds
         row_lower (list <float>): array of length num_row with the upper row
                                   bounds
         row_upper (list <float>): array of length num_row with the upper row
                                   bounds
         a_start (list <int>): the constraint matrix is provided to HiGHS in CSC
                               or CSR format depending on the value of a_format.
                               The sparse matrix consists of three arrays,
                               a_start, a_index and a_value. In CSC format,
                               a_start is a list of length num_col containing
                               the starting index of each column in a_index.
                               In CSR format, a_start is a list of length
                               num_row corresponding to each row.
         a_index (list <int>): list of length num_nz with indices of matrix
                               entries
         a_value (list <float>): list of length num_nz with values of
                                 matrix entries

      Returns:
         status (int): constant indicating whether the call succeeded

      """
      c_num_col = c_int(num_col)
      c_num_row = c_int(num_row)
      c_num_nz = c_int(num_nz)
      c_a_format = c_int(a_format)
      c_sense = c_int(sense)
      c_offset = c_double(offset)
      c_col_cost = (c_double * num_col)(*col_cost)
      c_col_lower = (c_double * num_col)(*col_lower)
      c_col_upper = (c_double * num_col)(*col_upper)
      c_row_lower = (c_double * num_row)(*row_lower)
      c_row_upper = (c_double * num_row)(*row_upper)
      if a_format == 1:
         c_a_start = (c_int * (num_col + 1))(*a_start)
      elif a_format == 2:
         c_a_start = (c_int * (num_row + 1))(*a_start)
      c_a_index = (c_int * num_nz)(*a_index)
      c_a_value = (c_double * num_nz)(*a_value)

      self.highslib.Highs_passLp.argtypes = (c_void_p, c_int, c_int, c_int,
      c_int, c_int, c_double, POINTER(c_double), POINTER(c_double),
      POINTER(c_double), POINTER(c_double), POINTER(c_double), POINTER(c_int),
      POINTER(c_int), POINTER(c_double))
      self.highslib.Highs_passLp.restype = c_int
      status = self.highslib.Highs_passLp(pointer_to_model, c_num_col,
      c_num_row, c_num_nz, c_a_format, c_sense, c_offset, c_col_cost,
      c_col_lower, c_col_upper, c_row_lower, c_row_upper, c_a_start, c_a_index,
      c_a_value)
      return status

   def Highs_passMip(self, pointer_to_model: c_void_p, num_col: int,
                    num_row: int, num_nz:int, a_format: int, sense: int,
                    offset: float, col_cost: list, col_lower: list,
                    col_upper: list, row_lower: list, row_upper: list,
                    a_start:list, a_index: list, a_value: list,
                    integrality: list) -> int:
      """Highs_passMip

      Pass a MILP model to HiGHS in a single function call.

      Args:
         pointer_to_model (c_void_type): ctypes pointer to HiGHS model
         num_col (int): number of columns in constraint matrix
         num_row (int): number of rows in constraint matrix
         num_nz (int): number of elements in constraint matrix
         a_format (int): the format of the constraint matrix (CSC if a_format =
                          1 and CSR if a_format = 2)
         sense (int): optimization sense (1 for min. and -1 for max.)
         offset (float): constant term in objective function
         col_cost (list <float>): list of length num_col with objective
                                  coefficients
         col_lower (list <float>): list of length num_col with lower column
                                   bounds
         col_upper (list <float>): list of length num_col with upper column
                                   bounds
         row_lower (list <float>): list of length num_row with upper row bounds
         row_upper (list <float>): list of length num_row with upper row bounds
         a_start (list <int>): the constraint matrix is provided to HiGHS in CSC
                               or CSR format depending on the value of a_format.
                               The sparse matrix consists of three arrays,
                               a_start, a_index and a_value. In CSC format,
                               a_start is a list of length num_col containing
                               the starting index of each column in a_index.
                               In CSR format, a_start is a list of length
                               num_row corresponding to each row.
         a_index (list <int>): list of length num_nz with indices of matrix
                               entries
         a_value (list <float>): list of length num_nz with values of
                                 matrix entries
         integrality (list <int>): list of length num_col containing a constant
                                   for each column indicating its type (e.g., 0
                                   for continuous and 1 for integer variables)

      Returns:
         status (int): constant indicating whether the call succeeded

      """
      c_num_col = c_int(num_col)
      c_num_row = c_int(num_row)
      c_num_nz = c_int(num_nz)
      c_a_format = c_int(a_format)
      c_sense = c_int(sense)
      c_offset = c_double(offset)
      c_col_cost = (c_double * num_col)(*col_cost)
      c_col_lower = (c_double * num_col)(*col_lower)
      c_col_upper = (c_double * num_col)(*col_upper)
      c_row_lower = (c_double * num_row)(*row_lower)
      c_row_upper = (c_double * num_row)(*row_upper)
      if a_format == 1:
         c_a_start = (c_int * (num_col + 1))(*a_start)
      elif a_format == 2:
         c_a_start = (c_int * (num_row + 1))(*a_start)
      c_a_index = (c_int * num_nz)(*a_index)
      c_a_value = (c_double * num_nz)(*a_value)
      c_integrality = (c_int * num_col)(*integrality)

      self.highslib.Highs_passMip.argtypes = (c_void_p, c_int, c_int, c_int,
      c_int, c_int, c_double, POINTER(c_double), POINTER(c_double),
      POINTER(c_double), POINTER(c_double), POINTER(c_double), POINTER(c_int),
      POINTER(c_int), POINTER(c_double), POINTER(c_int))
      self.highslib.Highs_passMip.restype = c_int
      status = self.highslib.Highs_passMip(pointer_to_model, c_num_col,
      c_num_row, c_num_nz, c_a_format, c_sense, c_offset, c_col_cost,
      c_col_lower, c_col_upper, c_row_lower, c_row_upper, c_a_start, c_a_index,
      c_a_value, c_integrality)
      return status

   def Highs_getObjectiveSense(self, pointer_to_model:c_void_p) -> int:
      """Highs_getObjectiveSense

      Return the objective sense.

      Args:
         pointer_to_model (c_void_type): ctypes pointer to HiGHS model

      Returns:
         sense (int): sense of objective (e.g., 1 for minimisation and -1 for
                      maximisation)

      """
      sense = c_int(0)
      self.highslib.Highs_getObjectiveSense.argtypes = (c_void_p,
      POINTER(c_int))
      self.highslib.Highs_getObjectiveSense.restype = c_int
      status = self.highslib.Highs_getObjectiveSense(pointer_to_model,
      byref(sense))
      return int(sense.value)

   def Highs_getObjectiveOffset(self, pointer_to_model: c_void_p) -> float:
      """Highs_getObjectiveOffset

      Return the objective offset.

      Args:
         pointer_to_model (c_void_type): ctypes pointer to HiGHS model

      Returns:
         offset (float): offset (constant term) of objective

      """
      offset = c_double(0)
      self.highslib.Highs_getObjectiveOffset.argtypes = (c_void_p,
      POINTER(c_double))
      self.highslib.Highs_getObjectiveOffset.restype = c_int
      status = self.highslib.Highs_getObjectiveOffset(pointer_to_model,
      byref(offset))
      return float(offset.value)

   def Highs_getNumCol(self, pointer_to_model: c_void_p) -> int:
      """Highs_getNumCol

      Return the number of columns in the model.

      Args:
         pointer_to_model (c_void_type): ctypes pointer to HiGHS model

      Returns:
         num_col (int): number of columns in model

      """
      self.highslib.Highs_getNumCol.argtypes = [c_void_p]
      self.highslib.Highs_getNumCol.restype = c_int
      num_col = self.highslib.Highs_getNumCol(pointer_to_model)
      return num_col

   def Highs_getNumRow(self, pointer_to_model: c_void_p) -> int:
      """Highs_getNumRow

      Return the number of rows in the model.

      Args:
         pointer_to_model (c_void_type): ctypes pointer to HiGHS model

      Returns:
         num_row (int): number of rows in model

      """
      self.highslib.Highs_getNumRow.argtypes = [c_void_p]
      self.highslib.Highs_getNumRow.restype = c_int
      num_row = self.highslib.Highs_getNumRow(pointer_to_model)
      return num_row

   def Highs_getNumNz(self, pointer_to_model: c_void_p) -> int:
      """Highs_getNumNz

      Return the number of nonzeros in the constraint matrix of the model.

      Args:
         pointer_to_model (c_void_type): ctypes pointer to HiGHS model

      Returns:
         num_nz (int): number of nonzero entries in constraint matrix

      """
      self.highslib.Highs_getNumNz.argtypes = [c_void_p]
      self.highslib.Highs_getNumNz.restype = c_int
      num_nz = self.highslib.Highs_getNumNz(pointer_to_model)
      return num_nz

   def Highs_setBoolOptionValue(self, pointer_to_model: c_void_p, option: str,
                                value: bool) -> int:
      """Highs_setBoolOptionValue

      Set a boolean-valued option.

      Args:
         pointer_to_model (c_void_type): ctypes pointer to HiGHS model
         option (str): name of the option
         value (bool): value of the option

      Returns:
         status (int): constant indicating whether the call succeeded

      """
      b_option = option.encode('utf-8')
      c_value = c_int(int(value))
      self.highslib.Highs_setBoolOptionValue.argtypes = (c_void_p, c_char_p,
      c_int)
      self.highslib.Highs_setBoolOptionValue.restype = c_int
      status = self.highslib.Highs_setBoolOptionValue(pointer_to_model,
      b_option, c_value)
      return status

   def Highs_getBoolOptionValue(self, pointer_to_model: c_void_p, option: str
                                ) -> bool:
       """Highs_getBoolOptionValue

       Return a boolean-valued option.

       Args:
          pointer_to_model (c_void_type): ctypes pointer to HiGHS model
          option (str): name of the option

       Returns:
          value (bool): value of the option

       """
       b_option = option.encode('utf-8')
       option_val = c_int(0)
       self.highslib.Highs_getBoolOptionValue.argtypes = (c_void_p, c_char_p,
       POINTER(c_int))
       self.highslib.Highs_getBoolOptionValue.restype = c_int
       status = self.highslib.Highs_getBoolOptionValue(pointer_to_model,
       b_option, byref(option_val))
       return bool(option_val.value)

   def Highs_setIntOptionValue(self, pointer_to_model: c_void_p, option: str,
                                value: int) -> int:
      """Highs_setIntOptionValue

      Set an int-valued option.

      Args:
         pointer_to_model (c_void_type): ctypes pointer to HiGHS model
         option (str): name of the option
         value (int): value of the option

      Returns:
         status (int): constant indicating whether the call succeeded

      """
      b_option = option.encode('utf-8')
      c_value = c_int(value)
      self.highslib.Highs_setIntOptionValue.argtypes = (c_void_p, c_char_p,
      c_int)
      self.highslib.Highs_setIntOptionValue.restype = c_int
      status = self.highslib.Highs_setIntOptionValue(pointer_to_model, b_option,
      c_value)
      return status

   def Highs_getIntOptionValue(self, pointer_to_model: c_void_p, option: str
                                ) -> int:
       """Highs_getIntOptionValue

       Return an int-valued option.

       Args:
          pointer_to_model (c_void_type): ctypes pointer to HiGHS model
          option (str): name of the option

       Returns:
          value (int): value of the option

       """
       b_option = option.encode('utf-8')
       option_val = c_int(0)
       self.highslib.Highs_getIntOptionValue.argtypes = (c_void_p, c_char_p,
       POINTER(c_int))
       self.highslib.Highs_getIntOptionValue.restype = c_int
       status = self.highslib.Highs_getIntOptionValue(pointer_to_model,
       b_option, byref(option_val))
       return int(option_val.value)

   def Highs_setDoubleOptionValue(self, pointer_to_model: c_void_p, option: str,
                                   value: float) -> int:
      """Highs_setDoubleOptionValue

      Set a float-valued option.

      Args:
         pointer_to_model (c_void_type): ctypes pointer to HiGHS model
         option (str): name of the option
         value (float): value of the option

      Returns:
         status (int): constant indicating whether the call succeeded

      """
      b_option = option.encode('utf-8')
      c_value = c_double(value)
      self.highslib.Highs_setIntOptionValue.argtypes = (c_void_p, c_char_p,
      c_double)
      self.highslib.Highs_setIntOptionValue.restype = c_int
      status = self.highslib.Highs_setDoubleOptionValue(pointer_to_model,
      b_option, c_value)
      return status

   def Highs_getDoubleOptionValue(self, pointer_to_model: c_void_p, option: str
                                  ) -> float:
       """Highs_getDoubleOptionValue

       Return a float-valued option.

       Args:
          pointer_to_model (c_void_type): ctypes pointer to HiGHS model
          option (str): name of the option

       Returns:
          value (float): value of the option

       """
       b_option = option.encode('utf-8')
       option_val = c_double(0)
       self.highslib.Highs_getDoubleOptionValue.argtypes = (c_void_p, c_char_p,
       POINTER(c_double))
       self.highslib.Highs_getDoubleOptionValue.restype = c_int
       status = self.highslib.Highs_getDoubleOptionValue(pointer_to_model,
       b_option, byref(option_val))
       return float(option_val.value)

   def Highs_setStringOptionValue(self, pointer_to_model: c_void_p, option: str,
                                   value: str) -> int:
      """Highs_setStringOptionValue

      Set a string-valued option.

      Args:
         pointer_to_model (c_void_type): ctypes pointer to HiGHS model
         option (str): name of the option
         value (str): value of the option

      Returns:
         status (int): constant indicating whether the call succeeded

      """
      b_option = option.encode('utf-8')
      c_value = value.encode('utf-8')
      self.highslib.Highs_setStringOptionValue.argtypes = (c_void_p, c_char_p,
      c_char_p)
      self.highslib.Highs_setStringOptionValue.restype = c_int
      status = self.highslib.Highs_setStringOptionValue(pointer_to_model,
      b_option, c_value)
      return status

   def Highs_getStringOptionValue(self, pointer_to_model: c_void_p, option: str
                                  ) -> str:
       """Highs_getStringOptionValue

       Return a string-valued option.

       Args:
          pointer_to_model (c_void_type): ctypes pointer to HiGHS model
          option (str): name of the option

       Returns:
          value (str): value of the option

       """
       b_option = option.encode('utf-8')
       option_val = c_char_p('random'.encode('utf-8'))
       self.highslib.Highs_getStringOptionValue.argtypes = (c_void_p, c_char_p,
       c_char_p)
       self.highslib.Highs_getStringOptionValue.restype = c_int
       status = self.highslib.Highs_getStringOptionValue(pointer_to_model,
       b_option, option_val)
       return option_val.value.decode('utf-8')

   def Highs_writeOptions(self, pointer_to_model: c_void_p, path: str) -> int:
      """Highs_writeOptions

      Write current options to file.

      Args:
         pointer_to_model (c_void_type): ctypes pointer to HiGHS model
         path (str): filename to write current options

      Returns:
         status (int): constant indicating whether the call succeeded

      """
      b_path = path.encode('utf-8')
      self.highslib.Highs_writeOptions.argtypes = (c_void_p, c_char_p)
      self.highslib.Highs_writeOptions.restype = c_int
      status = self.highslib.Highs_writeOptions(pointer_to_model, b_path)
      return status

   def Highs_writeOptionsDeviations(self, pointer_to_model: c_void_p,
                                     path: str) -> int:
      """Highs_writeOptionsDeviations

      Write non-default options to file.

      Args:
         pointer_to_model (c_void_type): ctypes pointer to HiGHS model
         path (str): the filename to write the options to

      Returns:
         status (int): constant indicating whether the call succeeded

      """
      b_path = path.encode('utf-8')
      self.highslib.Highs_writeOptionsDeviations.argtypes = (c_void_p, c_char_p)
      self.highslib.Highs_writeOptionsDeviations.restype = c_int
      status = self.highslib.Highs_writeOptionsDeviations(pointer_to_model,
      b_path)
      return status

   def Highs_resetOptions(self, pointer_to_model: c_void_p) -> int:
      """Highs_resetOptions

      Reset all options to their default value.

      Args:
         pointer_to_model (c_void_type): ctypes pointer to HiGHS model

      Returns:
         status (int): constant indicating whether the call succeeded

      """
      self.highslib.Highs_resetOptions.argtypes = [c_void_p]
      self.highslib.Highs_resetOptions.restype = c_int
      status = self.highslib.Highs_resetOptions(pointer_to_model)
      return status

   def Highs_writeModel(self, pointer_to_model: c_void_p, path: str) -> int:
      """Highs_writeModel

       Write a HiGHS model to file.

      Args:
         pointer_to_model (c_void_type): ctypes pointer to HiGHS model
         path (str): the filename to write the model to

      Returns:
         status (int): constant indicating whether the call succeeded

      """
      b_path = path.encode('utf-8')
      self.highslib.Highs_writeModel.argtypes = (c_void_p, c_char_p)
      self.highslib.Highs_writeModel.restype = c_int
      status = self.highslib.Highs_writeModel(pointer_to_model, b_path)
      return status

   def Highs_readModel(self, pointer_to_model: c_void_p, path: str) -> int:
      """Highs_readModel

       Read a HiGHS model from file.

      Args:
         pointer_to_model (c_void_type): ctypes pointer to HiGHS model
         path (str): the filename to read the model from

      Returns:
         status (int): constant indicating whether the call succeeded

      """
      b_path = path.encode('utf-8')
      self.highslib.Highs_readModel.argtypes = (c_void_p, c_char_p)
      self.highslib.Highs_readModel.restype = c_int
      status = self.highslib.Highs_readModel(pointer_to_model, b_path)
      return status

   def Highs_clearModel(self, pointer_to_model: c_void_p) -> int:
      """Highs_clearModel

       Remove all variables and constraints from the HiGHS model, but do not
       invalidate the pointer tomodel. Future calls (for example, adding new
       variables and constraints) are allowed.

      Args:
         pointer_to_model (c_void_type): ctypes pointer to HiGHS model

      Returns:
         status (int): constant indicating whether the call succeeded

      """
      self.highslib.Highs_clearModel.argtype = [c_void_p]
      self.highslib.Highs_clearModel.restype = c_int
      status = self.highslib.Highs_clearModel(pointer_to_model)
      return status

   def Highs_run(self, pointer_to_model: c_void_p) -> int:
      """Highs_run

       Optimize a model. The algorithm used by HiGHS depends on the options that
       have been set.

      Args:
         pointer_to_model (c_void_type): ctypes pointer to HiGHS model

      Returns:
         status (int): constant indicating whether the call succeeded

      """
      self.highslib.Highs_run.argtypes = [c_void_p]
      self.highslib.Highs_run.restype = c_int
      status = self.highslib.Highs_run(pointer_to_model)
      return status

   def Highs_crossover(self, pointer_to_model: c_void_p) -> int:
      """Highs_crossover

       Given a model solved with an interior point method, run crossover to
       compute a basic feasible solution.

      Args:
         pointer_to_model (c_void_type): ctypes pointer to HiGHS model

      Returns:
         status (int): constant indicating whether the call succeeded

      """
      self.highslib.Highs_crossover.argtypes = [c_void_p]
      self.highslib.Highs_crossover.restype = c_int
      status = self.highslib.Highs_crossover(pointer_to_model)
      return status

   def Highs_getModelStatus(self, pointer_to_model: c_void_p) -> int:
      """Highs_getModelStatus

       Return the optimization status of the model.

      Args:
         pointer_to_model (c_void_type): ctypes pointer to HiGHS model

      Returns:
         status (int): the status of the model

      """
      self.highslib.Highs_getModelStatus.argtypes = [c_void_p]
      self.highslib.Highs_getModelStatus.restype = c_int
      status = self.highslib.Highs_getModelStatus(pointer_to_model)
      return status

   def Highs_writeSolution(self, pointer_to_model: c_void_p,
                            path: str) -> int:
      """Highs_writeSolution

       Write the solution information (including dual and basis status, if
       available) to a file.

      Args:
         pointer_to_model (c_void_type): ctypes pointer to HiGHS model
         path (str): the name of the file to write the results to

      Returns:
         status (int): constant indicating whether the call succeeded

      """
      b_path = path.encode('utf-8')
      self.highslib.Highs_writeSolution. argtypes = (c_void_p, c_char_p)
      self.highslib.Highs_writeSolution.restype = c_int
      status = self.highslib.Highs_writeSolution(pointer_to_model, b_path)
      return status

   def Highs_writeSolutionPretty(self, pointer_to_model: c_void_p,
                                 path: str) -> int:
      """Highs_writeSolution

       Write the solution information (including dual and basis status, if
       available) to a file in a human-readable format.

       The method identical to `Highs_writeSolution`, except that the
       printout is in a human-readiable format.

      Args:
         pointer_to_model (c_void_type): ctypes pointer to HiGHS model
         path (str): the name of the file to write the results to

      Returns:
         status (int): constant indicating whether the call succeeded

      """
      b_path = path.encode('utf-8')
      self.highslib.Highs_writeSolutionPretty.argtypes = (c_void_p, c_char_p)
      self.highslib.Highs_writeSolutionPretty.restype = c_int
      status = self.highslib.Highs_writeSolutionPretty(pointer_to_model, b_path)
      return status

   def Highs_getRunTime(self, pointer_to_model: c_void_p) -> float:
      """Highs_getRunTime

      Return the cumulative wall-clock time spent in `Highs_run`.

      Args:
         pointer_to_model (c_void_type): ctypes pointer to HiGHS model

      Returns:
         time (float): the cumulative wall-clock time spent in `Highs_run`

      """
      self.highslib.Highs_getRunTime.argtypes = [c_void_p]
      self.highslib.Highs_getRunTime.restype = c_double
      time = self.highslib.Highs_getRunTime(pointer_to_model)
      return time

   def Highs_getSolution(self, pointer_to_model: c_void_p) -> tuple:
      """Highs_getSolution

      Return the primal and dual solution from an optimized model..

      Args:
         pointer_to_model (c_void_type): ctypes pointer to HiGHS model

      Returns:
         status (int): constant indicating whether the call succeeded
         c_LP_primal (list <float>): list of length num_col filled with primal
                                     column values
         c_LP_dual (list <float>): list of length num_col filled with dual
                                   column values
         c_LP_row_primal (list <float>): list of length num_row filled with
                                         primal row values
         c_LP_row_dual (list <float>): list of length num_row filled with
                                       dual row values

      """
      num_col = self.Highs_getNumCol(pointer_to_model)
      num_row = self.Highs_getNumRow(pointer_to_model)

      c_LP_primal = (c_double * num_col)()
      c_LP_dual = (c_double * num_col)()
      c_LP_row_primal = (c_double * num_row)()
      c_LP_row_dual = (c_double * num_row)()

      self.highslib.Highs_getSolution.argtypes = (c_void_p, POINTER(c_double),
      POINTER(c_double), POINTER(c_double), POINTER(c_double))
      self.highslib.Highs_getSolution.restype = c_int
      status = self.highslib.Highs_getSolution(pointer_to_model, c_LP_primal,
      c_LP_dual, c_LP_row_primal, c_LP_row_dual)
      return (status, list(c_LP_primal), list(c_LP_dual),
             list(c_LP_row_primal), list(c_LP_row_dual))

   def Highs_getBasicVariables(self, pointer_to_model: c_void_p) -> list:
      """Highs_getBasicVariables

      Get the indices of the rows and columns that make up the basis matrix of a
      basic feasible solution.

      Non-negative entries are indices of columns, and negative entries are
      `-row_index - 1`. For example, `{1, -1}` would be the second column and
      first row.

      Args:
         pointer_to_model (c_void_type): ctypes pointer to HiGHS model

      Returns:
         c_bas_var (list <int>): list of length num_rows filled with the
                                   indices of basic variables

      """
      num_row = self.Highs_getNumRow(pointer_to_model)
      c_bas_var = (c_int * num_row)()
      self.highslib.Highs_getBasicVariables.argtypes = (c_void_p,
      POINTER(c_int))
      self.highslib.Highs_getBasicVariables.restype = c_int
      status = self.highslib.Highs_getBasicVariables(pointer_to_model,
      c_bas_var)
      return list(c_bas_var)

   def Highs_getObjectiveValue(self, pointer_to_model: c_void_p) -> float:
      """Highs_getObjectiveValue

      Return the primal objective function value.

      Args:
         pointer_to_model (c_void_type): ctypes pointer to HiGHS model

      Returns:
         obj (float): the primal objective function value

      """
      self.highslib.Highs_getObjectiveValue.argtypes = [c_void_p]
      self.highslib.Highs_getObjectiveValue.restype = c_double
      obj = self.highslib.Highs_getObjectiveValue(pointer_to_model)
      return obj

   def Highs_lpCall(self, num_col: int, num_row: int, num_nz:int, a_format: int,
                    sense: int, offset: float, col_cost: list, col_lower: list,
                    col_upper: list, row_lower: list, row_upper: list,
                    a_start:list, a_index: list, a_value: list) -> tuple:
      """Highs_lpCall

      Formulate and solve a linear program using HiGHS.

      Args:
         pointer_to_model (c_void_type): ctypes pointer to HiGHS model
         num_col (int): the number of columns in the constraint matrix
         num_row (int): the number of rows in the constraint matrix
         num_nz (int): the number of elements in the constraint matrix
         a_format (int): the format of the constraint matrix (CSC if a_format =
                          1 and CSR if a_format = 2)
         sense (int): the optimization sense
         offset (float): the constant term in the objective function
         col_cost (list <float>): array of length num_col with the objective
                                  coefficients
         col_lower (list <float>): array of length num_col with the lower
                                   column bounds
         col_upper (list <float>): array of length num_col with the upper column
                                   bounds
         row_lower (list <float>): array of length num_row with the upper row
                                   bounds
         row_upper (list <float>): array of length num_row with the upper row
                                   bounds
         a_start (list <int>): the constraint matrix is provided to HiGHS in CSC
                               or CSR format depending on the value of a_format.
                               The sparse matrix consists of three arrays,
                               a_start, a_index and a_value. In CSC format,
                               a_start is a list of length num_col containing
                               the starting index of each column in a_index.
                               In CSR format, a_start is a list of length
                               num_row corresponding to each row.
         a_index (list <int>): array of length num_nz with indices of matrix
                               entries
         a_value (list <float>): array of length num_nz with values of
                                 matrix entries

      Returns:
         status (int): constant indicating whether the call succeeded
         model_status (int): termination status of the model after the solve
         c_col_value (list <float>): list of length num_col filled with primal
                                     column values
         c_col_dual (list <float>): list of length num_col filled with dual
                                   column values
         c_row_value (list <float>): list of length num_row filled with
                                         primal row values
         c_row_dual (list <float>): list of length num_row filled with
                                       dual row values
         c_col_basis (list <int>): list of length num_col filled with the basis
                                   status of the columns
         c_row_basis (list <int>): list of length num_rows filled with the basis
                                   status of the rows

      """
      c_num_col = c_int(num_col)
      c_num_row = c_int(num_row)
      c_num_nz = c_int(num_nz)
      c_a_format = c_int(a_format)
      c_sense = c_int(sense)
      c_offset = c_double(offset)
      c_col_cost = (c_double * num_col)(*col_cost)
      c_col_lower = (c_double * num_col)(*col_lower)
      c_col_upper = (c_double * num_col)(*col_upper)
      c_row_lower = (c_double * num_row)(*row_lower)
      c_row_upper = (c_double * num_row)(*row_upper)
      if a_format == 1:
         c_a_start = (c_int * (num_col + 1))(*a_start)
      elif a_format == 2:
         c_a_start = (c_int * (num_row + 1))(*a_start)
      c_a_index = (c_int * num_nz)(*a_index)
      c_a_value = (c_double * num_nz)(*a_value)
      model_status = c_int(0)

      # Pre-allocates C arrays
      c_col_value = (c_double * num_col)()
      c_col_dual = (c_double * num_col)()
      c_row_value = (c_double * num_row)()
      c_row_dual = (c_double * num_row)()
      c_col_basis = (c_int * num_col)()
      c_row_basis = (c_int * num_col)()

      self.highslib.Highs_lpCall.argtypes = (c_int, c_int, c_int, c_int, c_int,
      c_double, POINTER(c_double), POINTER(c_double), POINTER(c_double),
      POINTER(c_double), POINTER(c_double), POINTER(c_int), POINTER(c_int),
      POINTER(c_double), POINTER(c_double), POINTER(c_double),
      POINTER(c_double), POINTER(c_double), POINTER(c_int), POINTER(c_int),
      POINTER(c_int))
      self.highslib.Highs_lpCall.restype = c_int
      status = self.highslib.Highs_lpCall(c_num_col, c_num_row, c_num_nz,
         c_a_format, c_sense, c_offset, c_col_cost, c_col_lower, c_col_upper,
         c_row_lower, c_row_upper, c_a_start, c_a_index, c_a_value, c_col_value,
         c_col_dual, c_row_value, c_row_dual, c_col_basis, c_row_basis,
         byref(model_status))
      return (status, model_status.value, list(c_col_value),
              list(c_col_dual), list(c_row_value), list(c_row_dual),
              list(c_col_basis), list(c_row_basis))

   def Highs_mipCall(self, num_col: int, num_row: int, num_nz:int, a_format: int,
                    sense: int, offset: float, col_cost: list, col_lower: list,
                    col_upper: list, row_lower: list, row_upper: list,
                    a_start:list, a_index: list, a_value: list,
                    integrality: list) -> tuple:
      """Highs_mipCall

      Formulate and solve a mixed-integer linear program using HiGHS.

      Args:
         pointer_to_model (c_void_type): ctypes pointer to HiGHS model
         num_col (int): the number of columns in the constraint matrix
         num_row (int): the number of rows in the constraint matrix
         num_nz (int): the number of elements in the constraint matrix
         a_format (int): the format of the constraint matrix (CSC if a_format =
                          1 and CSR if a_format = 2)
         sense (int): the optimization sense
         offset (float): the constant term in the objective function
         col_cost (list <float>): array of length num_col with the objective
                                  coefficients
         col_lower (list <float>): array of length num_col with the lower
                                   column bounds
         col_upper (list <float>): array of length num_col with the upper column
                                   bounds
         row_lower (list <float>): array of length num_row with the upper row
                                   bounds
         row_upper (list <float>): array of length num_row with the upper row
                                   bounds
         a_start (list <int>): the constraint matrix is provided to HiGHS in CSC
                               or CSR format depending on the value of a_format.
                               The sparse matrix consists of three arrays,
                               a_start, a_index and a_value. In CSC format,
                               a_start is a list of length num_col containing
                               the starting index of each column in a_index.
                               In CSR format, a_start is a list of length
                               num_row corresponding to each row.
         a_index (list <int>): array of length num_nz with indices of matrix
                               entries
         a_value (list <float>): array of length num_nz with values of
                                 matrix entries
         integrality (list <int>): array of length num_col containing a constant
                                   for each column indicating its type (e.g., 0
                                   for continuous and 1 for integer variables)

      Returns:
         status (int): constant indicating whether the call succeeded
         model_status (int): termination status of the model after the solve
         c_col_value (list <float>): list of length num_col filled with primal
                                     column values
         c_row_value (list <float>): list of length num_row filled with
                                         primal row values

      """
      c_num_col = c_int(num_col)
      c_num_row = c_int(num_row)
      c_num_nz = c_int(num_nz)
      c_a_format = c_int(a_format)
      c_sense = c_int(sense)
      c_offset = c_double(offset)
      c_col_cost = (c_double * num_col)(*col_cost)
      c_col_lower = (c_double * num_col)(*col_lower)
      c_col_upper = (c_double * num_col)(*col_upper)
      c_row_lower = (c_double * num_row)(*row_lower)
      c_row_upper = (c_double * num_row)(*row_upper)
      if a_format == 1: # CSC format
         c_a_start = (c_int * (num_col + 1))(*a_start)
      elif a_format == 2: # CSR format
         c_a_start = (c_int * (num_row + 1))(*a_start)
      c_a_index = (c_int * num_nz)(*a_index)
      c_a_value = (c_double * num_nz)(*a_value)
      c_integrality = (c_int * num_col)(*integrality)
      model_status = c_int(0)

      # Pre-allocates C arrays
      c_col_value = (c_double * num_col)()
      c_row_value = (c_double * num_row)()

      self.highslib.Highs_mipCall.argtypes = (c_int, c_int, c_int, c_int, c_int,
      c_double, POINTER(c_double), POINTER(c_double), POINTER(c_double),
      POINTER(c_double), POINTER(c_double), POINTER(c_int), POINTER(c_int),
      POINTER(c_double), POINTER(c_int), POINTER(c_double), POINTER(c_double),
      POINTER(c_int))
      self.highslib.Highs_mipCall.restype = c_int
      status = self.highslib.Highs_mipCall(c_num_col, c_num_row, c_num_nz,
         c_a_format, c_sense, c_offset, c_col_cost, c_col_lower, c_col_upper,
         c_row_lower, c_row_upper, c_a_start, c_a_index, c_a_value,
         c_integrality, c_col_value, c_row_value, byref(model_status))
      return (status, model_status.value, list(c_col_value),
              list(c_row_value))

if __name__ == "__main__":

   ## Dummy input data
   # Python data

   num_row = 4 # number of rows in coeff matrix
   num_col = 4 # number of columns in coeff matrix
   num_nz = 4 # number of nonzero entries in coeff matrix

   col_cost = [1, 2, 3, 4] # objective coefficients

   a_start = [0, 1, 2, 3, 4] # row index for CSR representation of coeff matrix
   a_index = [0, 1, 2, 3] # column index for CSR representation of coeff matrix
   a_value = [1, 2, 3, 4] # nonzero values in coeff matrix

   col_lower = [1, 2, 3, 4] # lower bounds on primal variables
   col_upper = [10, 10, 10, 10] # upper bounds on primal variables

   row_lower = [1, 1, 1, 1] # lower bound on each row
   row_upper = [100, 100, 100, 100] # upper bound on each row

   a_format = 2 # flag for coeff matrix in CSR format (set to 1 for CSC)
   sense = 1 # flag for minimisation (set to -1 for maximisation)
   offset = 0 # constant term in the objective

   integrality = [0, 0, 1, 1] # 0 for continuous and 1 for integer variables
   ## Conversion to C data
   c_num_col = c_int(num_col)
   c_num_row = c_int(num_row)
   c_num_nz = c_int(num_nz)
   c_a_format = c_int(a_format)
   c_sense = c_int(sense)
   c_offset = c_double(offset)

   c_col_cost = (c_double * num_col)(*col_cost)
   c_col_lower = (c_double * num_col)(*col_lower)
   c_col_upper = (c_double * num_col)(*col_upper)
   c_row_lower = (c_double * num_row)(*row_lower)
   c_row_upper = (c_double * num_row)(*row_upper)
   c_a_start = (c_int * (num_row + 1))(*a_start)
   c_a_index = (c_int * num_nz)(*a_index)
   c_a_value = (c_double * num_nz)(*a_value)

   c_col_value = (c_double * num_col)()
   c_col_dual = (c_double * num_col)()
   c_row_value = (c_double * num_row)()
   c_row_dual = (c_double * num_row)()
   c_col_basis = (c_int * num_col)()
   c_row_basis = (c_int * num_col)()

   c_integrality = (c_int * num_col)(*integrality)

   model_status = c_int(0)

   ### HiGHS library
   print(find_library("highs"))
   highslib = cdll.LoadLibrary(find_library("highs"))
   ## Create LP and MILP models

   highslib.Highs_create.restype = c_void_p
   pointer_to_LP_model = c_void_p(highslib.Highs_create())
   pointer_to_MILP_model = c_void_p(highslib.Highs_create())

   ## Instantiate LP model

   highslib.Highs_passLp.argtypes = (c_void_p, c_int, c_int, c_int, c_int, c_int,
   c_double, POINTER(c_double), POINTER(c_double), POINTER(c_double),
   POINTER(c_double), POINTER(c_double), POINTER(c_int), POINTER(c_int),
   POINTER(c_double))
   highslib.Highs_passLp.restype = c_int
   print("hi")
   pass_LP_status = highslib.Highs_passLp(pointer_to_LP_model, c_num_col, c_num_row,
   c_num_nz, c_a_format, c_sense, c_offset, c_col_cost, c_col_lower, c_col_upper,
   c_row_lower, c_row_upper, c_a_start, c_a_index, c_a_value)

   ## Instantiate MILP model

   highslib.Highs_passMip.argtypes = (c_void_p, c_int, c_int, c_int, c_int, c_int,
   c_double, POINTER(c_double), POINTER(c_double), POINTER(c_double),
   POINTER(c_double), POINTER(c_double), POINTER(c_int), POINTER(c_int),
   POINTER(c_double), POINTER(c_int))
   highslib.Highs_passMip.restype = c_int

   pass_MILP_status = highslib.Highs_passMip(pointer_to_MILP_model, c_num_col,
   c_num_row, c_num_nz, c_a_format, c_sense, c_offset, c_col_cost, c_col_lower,
   c_col_upper, c_row_lower, c_row_upper, c_a_start, c_a_index, c_a_value,
   c_integrality)
   ## Print LP model to file

   highslib.Highs_writeModel.argtypes = (c_void_p, c_char_p)
   highslib.Highs_writeModel.restype = c_int

   lp_path = '/Users/bmiftari/Documents/inge21-22/HIGHS/HiGHS/build/lib/test.lp'
   b_lp_path = lp_path.encode('utf-8')

   lp_print_status = highslib.Highs_writeModel(pointer_to_LP_model, b_lp_path)

   ## Run model

   highslib.Highs_run.argtypes = [c_void_p]
   highslib.Highs_run.restype = c_int

   run_LP_status = highslib.Highs_run(pointer_to_LP_model)
   run_MILP_status = highslib.Highs_run(pointer_to_MILP_model)

   ## Print solution to file

   sol_path = '/Users/bmiftari/Documents/inge21-22/HIGHS/HiGHS/build/lib/test.sol'
   b_sol_path = sol_path.encode('utf-8')

   highslib.Highs_writeSolutionPretty.argtypes = (c_void_p, c_char_p)
   highslib.Highs_writeSolutionPretty.restype = c_int

   sol_print_status = highslib.Highs_writeSolutionPretty(pointer_to_LP_model, b_sol_path)

   ## Retrieve solution

   highslib.Highs_getSolution.argtypes = (c_void_p, POINTER(c_double),
   POINTER(c_double), POINTER(c_double), POINTER(c_double))
   highslib.Highs_getSolution.restype = c_int

   c_LP_primal = (c_double * num_col)()
   c_LP_dual = (c_double * num_col)()
   c_LP_row_primal = (c_double * num_row)()
   c_LP_row_dual = (c_double * num_row)()

   retrieve_status = highslib.Highs_getSolution(pointer_to_LP_model, c_LP_primal,
   c_LP_dual, c_LP_row_primal, c_LP_row_dual)

   print(list(c_LP_primal))
   print(list(c_LP_dual))
   print(list(c_LP_row_primal))
   print(list(c_LP_row_dual))

   ## Free memory

   highslib.Highs_destroy.argtypes = [c_void_p]

   highslib.Highs_destroy(pointer_to_LP_model)
   highslib.Highs_destroy(pointer_to_MILP_model)

   ## LP Call

   # Argument and return types definitions
   highslib.Highs_lpCall.argtypes = (c_int, c_int, c_int, c_int, c_int, c_double,
   POINTER(c_double), POINTER(c_double), POINTER(c_double), POINTER(c_double),
   POINTER(c_double), POINTER(c_int), POINTER(c_int), POINTER(c_double),
   POINTER(c_double), POINTER(c_double), POINTER(c_double), POINTER(c_double),
   POINTER(c_int), POINTER(c_int), POINTER(c_int))
   highslib.Highs_lpCall.restype = c_int

   # Library call
   return_status = highslib.Highs_lpCall(c_num_col, c_num_row, c_num_nz,
      c_a_format, c_sense, c_offset, c_col_cost, c_col_lower, c_col_upper,
      c_row_lower, c_row_upper, c_a_start, c_a_index, c_a_value, c_col_value,
      c_col_dual, c_row_value, c_row_dual, c_col_basis, c_row_basis,
      byref(model_status))

   # Print solution
   print(return_status)
   print(model_status.value)
   print(list(c_col_value))
   print(list(c_col_dual))
   print(list(c_row_value))
   print(list(c_row_dual))
   print(list(c_col_basis))
   print(list(c_row_basis))

   ## MIP Call

   # Argument and return types definitions
   highslib.Highs_mipCall.argtypes = (c_int, c_int, c_int, c_int, c_int, c_double,
   POINTER(c_double), POINTER(c_double), POINTER(c_double), POINTER(c_double),
   POINTER(c_double), POINTER(c_int), POINTER(c_int), POINTER(c_double),
   POINTER(c_int), POINTER(c_double), POINTER(c_double), POINTER(c_int))
   highslib.Highs_mipCall.restype = c_int

   # Library call
   return_status = highslib.Highs_mipCall(c_num_col, c_num_row, c_num_nz,
      c_a_format, c_sense, c_offset, c_col_cost, c_col_lower, c_col_upper,
      c_row_lower, c_row_upper, c_a_start, c_a_index, c_a_value, c_integrality,
      c_col_value, c_row_value, byref(model_status))

   # Print solution
   print(return_status)
   print(model_status.value)
   print(list(c_col_value))
   print(list(c_row_value))
