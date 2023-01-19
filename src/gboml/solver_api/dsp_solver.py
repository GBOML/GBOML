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


def dsp_solver(matrix_a_eq: coo_matrix, vector_b_eq: np.ndarray,
               matrix_a_ineq: coo_matrix, vector_b_ineq: np.ndarray,
               vector_c: np.ndarray,
               objective_offset: float, name_tuples: dict,
               structure_indexes_eq,
               structure_indexes_ineq,
               algorithm="de") -> tuple:
    """dsp_solver

        takes as input the matrix A, the vectors b and c. It returns the
        solution of the problem : min c^T * x s.t. A * x <= b found
        by the dsp solver

        Args:
            matrix_a_eq -> coo_matrix of equality constraints
            vector_b_eq -> np.ndarray of independent terms of each equality constraint
            matrix_a_ineq -> coo_matrix of inequality constraints
            vector_b_eq -> np.ndarray of independent terms of each inequality constraint
            vector_c -> np.ndarray of objective vector
            objective_offset -> float of the objective offset
            name_tuples -> dictionary of <node_name variables> used to get
                           the type
            structure_indexes_eq -> constraint indexes for equality matrix of the different blocks
                                    (last one being the master block)
            structure_indexes_ineq -> constraint indexes for inequality matrix of the different blocks
                                    (last one being the master block)
            algorithm -> solving algorithm to use, either "de" for the extensive
                         form and "dw" for Dantzig-Wolf

        Returns:
            solution -> np.ndarray of the flat solution
            objective -> float of the objective value
            status -> solution status
            solver_info -> dictionary of solver information

    """
    _, nb_cols = vector_c.shape
    csr_constraints_matrix_eq = csr_matrix(matrix_a_eq)
    vector_c = vector_c[-1]

    master_constr_slice_eq = structure_indexes_eq[-1]
    master_csr_eq = \
        csr_constraints_matrix_eq[master_constr_slice_eq, 0:nb_cols]

    master_val_eq, master_row_eq, master_col_eq = master_csr_eq.data, master_csr_eq.indptr,\
                                                  master_csr_eq.indices

    csr_constraints_matrix_ineq = csr_matrix(matrix_a_ineq)

    master_constr_slice_ineq = structure_indexes_ineq[-1]
    master_csr_ineq = \
        csr_constraints_matrix_ineq[master_constr_slice_ineq, 0:nb_cols]

    master_val_ineq, master_row_ineq, master_col_ineq = master_csr_ineq.data, master_csr_ineq.indptr, \
                                                        master_csr_ineq.indices

    master_nb_lines_eq = master_constr_slice_eq.stop-master_constr_slice_eq.start
    master_nb_lines_ineq = master_constr_slice_ineq.stop-master_constr_slice_ineq.start
    minus_infinity_col = [-1000] * nb_cols
    plus_infinity_col = [1000] * nb_cols
    master_coltypes = ["C"]*nb_cols
    flat_name_tuples = flat_nested_list_to_two_level(name_tuples)

    for index, _, var_type, var_size in flat_name_tuples:

        if var_type == "integer":

            master_coltypes[index:index+var_size] = ["I"]*var_size
        if var_type == "binary":

            master_coltypes[index:index+var_size] = ["B"]*var_size

    vector_master_eq = vector_b_eq[master_constr_slice_eq].tolist()

    row_lb = [-float("inf")] * master_nb_lines_ineq+vector_master_eq

    row_up = vector_b_ineq[master_constr_slice_ineq].tolist()+vector_master_eq

    dsp = DSPpy()
    pointer_to_model = dsp.createEnv()
    master_val = np.concatenate((master_val_ineq, master_val_eq))
    master_col = np.concatenate((master_col_ineq, master_col_eq))
    master_row = np.concatenate((master_row_ineq[:-1], master_row_eq+len(master_val_ineq)))

    dsp.loadBlockProblem(pointer_to_model, 0, nb_cols, master_nb_lines_ineq+master_nb_lines_eq,
                         len(master_val), master_row, master_col, master_val,
                         minus_infinity_col, plus_infinity_col,
                         master_coltypes,
                         vector_c, row_lb, row_up)

    nb_blocks = len(structure_indexes_eq)
    for b_number in range(nb_blocks-1):
        block_slice_eq = structure_indexes_eq[b_number]
        block_slice_ineq = structure_indexes_ineq[b_number]

        block_nb_lines_eq = block_slice_eq.stop - block_slice_eq.start
        block_nb_lines_ineq = block_slice_ineq.stop - block_slice_ineq.start

        block_csr_eq = csr_constraints_matrix_eq[block_slice_eq, 0:nb_cols]
        block_csr_ineq = csr_constraints_matrix_ineq[block_slice_ineq, 0:nb_cols]

        block_eq_val, bloc_eq_row, block_eq_col = block_csr_eq.data, block_csr_eq.indptr, \
                                                  block_csr_eq.indices

        block_ineq_val, bloc_ineq_row, block_ineq_col = block_csr_ineq.data, block_csr_ineq.indptr, \
                                                        block_csr_ineq.indices
        vector_block_eq = vector_b_eq[block_slice_eq].tolist()
        row_up = vector_b_ineq[block_slice_ineq].tolist()+vector_block_eq

        row_lb = [-float("inf")] * block_nb_lines_ineq + vector_block_eq

        block_val = np.concatenate((block_ineq_val, block_eq_val))
        block_col = np.concatenate((block_ineq_col, block_eq_col))
        block_row = np.concatenate((bloc_ineq_row[:-1], bloc_eq_row + len(block_ineq_val)))

        dsp.loadBlockProblem(pointer_to_model, b_number + 1, nb_cols,
                             block_nb_lines_ineq+block_nb_lines_eq, len(block_val),
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
            print("STARTED SOLVING")
            dsp.setIntParam(pointer_to_model, "DW/MASTER/SOLVER", 0)
            dsp.setIntParam(pointer_to_model, "DW/SUB/SOLVER", 0)
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
