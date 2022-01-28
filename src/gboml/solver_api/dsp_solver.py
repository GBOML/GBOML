# Copyright (C) 2020 - 2022
# Bardhyl Miftari, Mathias Berger, Hatim Djelassi, Damien Ernst,
# University of Liege .
# Licensed under the MIT License (see LICENSE file).


"""DSP Solver file, contains the interface to DSP solver .

Takes the matrix A, the vector b and vector c as input of the problem
    min : c^T * X s.t. A * X <= b
and passes it to the dsp solver.

  Typical usage example:

   solution, objective, status, solver_info = dsp_solver(matrix_a, vector_b,
                                                        vector_c,
                                                        objective_offset,
                                                        name_tuples,
                                                        structure_indexes)
   print("the solution is "+str(solution))
   print("the objective found : "+str(objective))
"""

import numpy as np
from scipy.sparse import coo_matrix, csr_matrix

from gboml.compiler.utils import flat_nested_list_to_two_level
from .dsppy import DSPpy


def dsp_solver(matrix_a: coo_matrix, vector_b: np.ndarray, vector_c: np.ndarray,
               objective_offset: float, name_tuples: dict,
               structure_indexes,
               algorithm="de") -> tuple:
    """dsp_solver

        takes as input the matrix A, the vectors b and c. It returns the
        solution of the problem : min c^T * x s.t. A * x <= b found
        by the dsp solver

        Args:
            matrix_a -> coo_matrix of constraints
            vector_b -> np.ndarray of independent terms of each constraint
            vector_c -> np.ndarray of objective vector
            objective_offset -> float of the objective offset
            name_tuples -> dictionary of <node_name variables> used to get
                           the type
            structure_indexes -> constraint indexes of the different blocks
                                 (last one being the master block)
            algorithm -> solving algorithm to use, either "de" for the extensive
                         form and "dw" for Dantzig-Wolf

        Returns:
            solution -> np.ndarray of the flat solution
            objective -> float of the objective value
            status -> solution status
            solver_info -> dictionary of solver information

    """
    _, nb_cols = np.shape(matrix_a)
    all_constraints_matrix = csr_matrix(matrix_a)

    vector_c = vector_c[-1]

    start_master_constraint, end_master_constraint = structure_indexes[-1]
    master_csr = \
        all_constraints_matrix[start_master_constraint:
                               end_master_constraint + 1, 0:nb_cols]
    master_val, master_row, master_col = master_csr.data, master_csr.indptr,\
                                         master_csr.indices
    master_nb_lines = end_master_constraint + 1 - start_master_constraint
    minus_infinity_col = [-1000] * nb_cols
    plus_infinity_col = [1000] * nb_cols
    master_coltypes = ["C"]*nb_cols
    flat_name_tuples = flat_nested_list_to_two_level(name_tuples)

    for index, _, var_type, var_size in flat_name_tuples:

        if var_type == "integer":

            master_coltypes[index:index+var_size] = ["I"]*var_size
        if var_type == "binary":

            master_coltypes[index:index+var_size] = ["B"]*var_size

    row_lb = [-float("inf")] * master_nb_lines
    row_up = vector_b[start_master_constraint:end_master_constraint + 1]

    dsp = DSPpy()
    pointer_to_model = dsp.createEnv()
    dsp.loadBlockProblem(pointer_to_model, 0, nb_cols, master_nb_lines,
                         len(master_val), master_row, master_col, master_val,
                         minus_infinity_col, plus_infinity_col,
                         master_coltypes,
                         vector_c, row_lb, row_up)

    nb_blocks = len(structure_indexes)
    for b_number in range(nb_blocks-1):
        block_start_constr, block_end_constr = structure_indexes[b_number]
        block_nb_lines = block_end_constr - block_start_constr + 1
        block_csr = \
            all_constraints_matrix[block_start_constr:
                                   block_end_constr + 1, 0:nb_cols]
        block_val, block_row, block_col = block_csr.data, block_csr.indptr, \
                                          block_csr.indices
        row_up = vector_b[block_start_constr:block_end_constr + 1]
        row_lb = [-float("inf")] * block_nb_lines

        dsp.loadBlockProblem(pointer_to_model, b_number + 1, nb_cols,
                             block_nb_lines, len(block_val),
                             block_row, block_col, block_val,
                             minus_infinity_col,
                             plus_infinity_col, master_coltypes,
                             vector_c, row_lb, row_up)

    dsp.updateBlocks(pointer_to_model)
    # Retrieve solver information
    solver_info = {"name": "dsp", "algo": algorithm}
    solution = None
    objective = None

    # Solve the problem
    try:
        if algorithm == "de":
            dsp.solveDe(pointer_to_model)
        elif algorithm == "dw":
            dsp.solveDw(pointer_to_model)
        print("CPU Time : "+str(dsp.getCpuTime(pointer_to_model)))
        print("Wall Time : "+str(dsp.getWallTime(pointer_to_model)))

        status_code = dsp.getStatus(pointer_to_model)
        solver_info["status"] = status_code
        if status_code == 3000:

            status = "optimal"
            solution = dsp.getPrimalSolution(pointer_to_model, nb_cols)
            objective = dsp.getPrimalBound(pointer_to_model) + objective_offset
        else:

            status = "unknown"
    except RuntimeError as e:

        print(e)
        status = "error"
    dsp.freeEnv(pointer_to_model)
    return solution, objective, status, solver_info
