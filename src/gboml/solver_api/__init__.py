# Copyright (C) 2020 - 2022
# Bardhyl Miftari, Mathias Berger, Hatim Djelassi, Damien Ernst,
# University of Liege .
# Licensed under the MIT License (see LICENSE file).


"""Solver API contains the API and option files from four different solvers.

All the APIs work simiarly, they take the matrix A, the vector b and vector c
as input of the problem
    min : c^T * X s.t. A * X <= b
and passes it to the corresponding solver.

  Args:
    A -> coo_matrix of constraints
    b -> np.ndarray of independent terms of each constraint
    c -> np.ndarray of objective vector
    objective_offset -> float of the objective offset
    name_tuples -> dictionary of <node_name variables> used to get the type

  Returns:
    solution -> np.ndarray of the flat solution
    objective -> float of the objective value
    status -> solution status
    solver_info -> dictionary of solver information

  Typical usage example:

   solution, objective, status, solver_info = api_solver(matrix_a, vector_b,
                                                        vector_c,
                                                        objective_offset,
                                                        name_tuples)
   print("the solution is "+str(solution))
   print("the objective found : "+str(objective))
"""

from .gurobi_solver import gurobi_solver
from .clp_solver import clp_solver
from .cplex_solver import cplex_solver
from .xpress_solver import xpress_solver
from .scipy_solver import scipy_solver
from .dsppy import DSPpy
from .dsp_solver import dsp_solver
from .pyhighs import PyHighs
from .highs_solver import highs_solver
from .cbc_solver import cbc_solver
from .pycbc import PyCBC

__all__ = ["gurobi_solver", "clp_solver", "cplex_solver", "xpress_solver",
           "scipy_solver", "DSPpy", "dsp_solver", "PyHighs", "highs_solver",
           "cbc_solver", "PyCBC"]
