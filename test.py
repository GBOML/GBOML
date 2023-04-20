# Copyright (C) 2020 - 2022
# Bardhyl Miftari, Mathias Berger, Hatim Djelassi, Damien Ernst,
# University of Liege .
# Licensed under the MIT License (see LICENSE file).

"""GBOML compiler test file

Unittesting of different interfaces to GBOML and the implementation

  Typical usage example:

   $ python test.py
"""

from gboml import GbomlGraph, VariableType
from gboml.compiler.classes import Parameter, Expression, Node, Hyperedge,\
    Time, Program
from gboml.compiler import compile_gboml
from gboml.solver_api import gurobi_solver, cplex_solver, xpress_solver, \
    highs_solver

import unittest
import subprocess
import json
import numpy as np
import os

PATH = os.getcwd()


class CompilerTests(unittest.TestCase):
    """
    CompilerTests

    Tests mainly the gboml/main.py, compile_gboml functions, solver API and
    output types.

    It checks whether a file correctly fails, generates the correct matrices,
    correct solutions and correct output.

    """

    def test_nonexistant_file(self):
        """ test_nonexistant_file

        Tests compiling a file that does not exist.

        """
        process = subprocess.run(['gboml', 'test/nonexistant.txt'],
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
        return_code = process.returncode
        self.assertNotEqual(return_code, 0)

    def test_empty_file(self):
        """ test_empty_file

        Tests a file which is completely empty.

        """
        process = subprocess.run(['gboml', 'test/empty.txt'],
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
        return_code = process.returncode
        self.assertNotEqual(return_code, 0)

    def test_timehorizon_only(self):
        """ test_timehorizon_only

        Tests a file with only a timehorizon defined (no nodes, no hyperedges).

        """

        process = subprocess.run(['gboml', 'test/test1.txt'],
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
        return_code = process.returncode
        self.assertNotEqual(return_code, 0)

    def test_wrong_horizon(self):
        """ test_wrong_horizon

        Tests a file with a wrong name for T the timehorizon.

        """

        process = subprocess.run(['gboml', 'test/test2.txt'],
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
        return_code = process.returncode
        self.assertNotEqual(return_code, 0)

    def test_negative_horizon(self):
        """ test_negative_horizon

        Tests a file with a negative timehorizon

        """

        process = subprocess.run(['gboml', 'test/test3.txt'],
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
        return_code = process.returncode
        self.assertNotEqual(return_code, 0)

    def test_impossible_constraint(self):
        """ test_impossible_constraint

        Tests a file with a constraint that is impossible (0*x==10)

        """

        process = subprocess.run(['gboml', 'test/test4.txt'],
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
        return_code = process.returncode
        self.assertNotEqual(return_code, 0)

    def test_unfeasible_problem_gurobi(self):
        """ test_unfeasible_problem_gurobi

        Tests the gurobi interface for an impossible problem

        """

        process = subprocess.run(['gboml', 'test/test5.txt', "--gurobi"],
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)

    def test_unfeasible_problem_cplex(self):
        """ test_unfeasible_problem_cplex

        Tests the cplex interface for an impossible problem

        """

        process = subprocess.run(['gboml', 'test/test5.txt', "--cplex"],
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)

    def test_unfeasible_problem_clp(self):
        """ test_unfeasible_problem_clp

        Tests the clp-cbc interface for an impossible problem

        """

        process = subprocess.run(['gboml', 'test/test5.txt', "--clp"],
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)

    def test_unfeasible_problem_linprog(self):
        """ test_unfeasible_problem_linprog

        Tests the linprog interface for an impossible problem

        """
        process = subprocess.run(['gboml', 'test/test5.txt', "--linprog"],
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)

    def test_unfeasible_problem_xpress(self):
        """ test_unfeasible_problem_xpress

        Tests the xpress interface for an impossible problem

        """
        process = subprocess.run(['gboml', 'test/test5.txt', "--xpress"],
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)

    def test_positive_solution_gurobi(self):
        """ test_positive_solution_gurobi

        Tests a file having a positive solution with gurobi from the command
        line

        """

        process = subprocess.run(
            ['gboml', 'test/test6.txt', "--gurobi", "--json",
             "--output", "test/test6"],
            stdout=subprocess.PIPE,
            universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)

        with open("test/test6.json", 'r') as j:
            contents = json.loads(j.read())
            self.assertIn("objective", contents["solution"])
            self.assertEqual(contents["solution"]["objective"], 40.0)

    def test_positive_solution_cplex(self):
        """ test_positive_solution_cplex

        Tests a file having a positive solution with cplex from the command line

        """

        process = subprocess.run(
            ['gboml', 'test/test6.txt', "--cplex", "--json", "--output",
             "test/test6"],
            stdout=subprocess.PIPE,
            universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)

        with open("test/test6.json", 'r') as j:
            contents = json.loads(j.read())
            self.assertIn("objective", contents["solution"])
            self.assertEqual(contents["solution"]["objective"], 40.0)

    def test_positive_solution_clp(self):
        """ test_positive_solution_clp

        Tests a file having a positive solution with clp from the command line

        """
        process = subprocess.run(
            ['gboml', 'test/test6.txt', "--clp", "--json", "--output",
             "test/test6"],
            stdout=subprocess.PIPE,
            universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)

        with open("test/test6.json", 'r') as j:
            contents = json.loads(j.read())
            self.assertIn("objective", contents["solution"])
            self.assertEqual(contents["solution"]["objective"], 40.0)

    def test_positive_solution_linprog(self):
        """ test_positive_solution_linprog

        Tests a file having a positive solution with linprog from the command
        line

        """
        process = subprocess.run(
            ['gboml', 'test/test6.txt', "--linprog", "--json",
             "--output", "test/test6"],
            stdout=subprocess.PIPE,
            universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)

        with open("test/test6.json", 'r') as j:
            contents = json.loads(j.read())
            self.assertIn("objective", contents["solution"])
            self.assertEqual(contents["solution"]["objective"], 40.0)

    def test_negative_solution_gurobi(self):
        """ test_negative_solution_gurobi

        Tests a file having a negative solution with gurobi from the command
        line

        """
        process = subprocess.run(
            ['gboml', 'test/test7.txt', "--gurobi", "--json",
             "--output", "test/test7"],
            stdout=subprocess.PIPE,
            universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)

        with open("test/test7.json", 'r') as j:
            contents = json.loads(j.read())
            self.assertIn("objective", contents["solution"])
            self.assertEqual(contents["solution"]["objective"], 4.0)

    def test_negative_solution_cplex(self):
        """ test_negative_solution_cplex

        Tests a file having a negative solution with cplex from the command line

        """
        process = subprocess.run(
            ['gboml', 'test/test7.txt', "--cplex", "--json", "--output",
             "test/test7"],
            stdout=subprocess.PIPE,
            universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)

        with open("test/test7.json", 'r') as j:
            contents = json.loads(j.read())
            self.assertIn("objective", contents["solution"])
            self.assertEqual(contents["solution"]["objective"], 4.0)

    def test_negative_solution_clp(self):
        """ test_negative_solution_clp

        Tests a file having a negative solution with clp from the command line

        """
        process = subprocess.run(
            ['gboml', 'test/test7.txt', "--clp", "--json", "--output",
             "test/test7"],
            stdout=subprocess.PIPE,
            universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)

        with open("test/test7.json", 'r') as j:
            contents = json.loads(j.read())
            self.assertIn("objective", contents["solution"])
            self.assertEqual(contents["solution"]["objective"], 4.0)

    def test_negative_solution_linprog(self):
        """ test_negative_solution_linprog

        Tests a file having a negative solution with linprog from the command
        line

        """
        process = subprocess.run(
            ['gboml', 'test/test7.txt', "--linprog", "--json",
             "--output", "test/test7"],
            stdout=subprocess.PIPE,
            universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)

        with open("test/test7.json", 'r') as j:
            contents = json.loads(j.read())
            self.assertIn("objective", contents["solution"])
            self.assertEqual(contents["solution"]["objective"], 4.0)

    def test_non_linearity(self):
        """ test_non_linearity

        Tests a file containing a non-linearity

        """
        process = subprocess.run(['gboml', 'test/test8.txt'],
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
        return_code = process.returncode
        self.assertNotEqual(return_code, 0)

    def test_non_existant_import(self):
        """ test_non_existant_import

        Tests a file having an import toward a non existing file

        """
        process = subprocess.run(['gboml', 'test/test9.txt'],
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
        return_code = process.returncode
        self.assertNotEqual(return_code, 0)

    def test_non_linear_assignment_division(self):
        """ test_non_linear_assignment_division

        Tests a file with a non linear assignment

        """
        process = subprocess.run(['gboml', 'test/test10.txt'],
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
        return_code = process.returncode
        self.assertNotEqual(return_code, 0)

    def test_normal_file(self):
        """ test_normal_file

        Tests a simple file with a non linear assignment and checks if
        additional prints have been added.

        """
        process = subprocess.run(['gboml', 'test/test11.txt'],
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)
        if process.stdout.count("\n") != 3:
            print("Please remove the additional prints before you push")

    def test_assignment_T(self):
        """ test_normal_file

        Tests a file with one vector variable with only one value fixed.

        """
        process = subprocess.run(
            ['gboml', 'test/test12.txt', "--gurobi", "--json",
             "--output", "test/test12"],
            stdout=subprocess.PIPE,
            universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)

    def test_single_obj_constr(self):
        """ test_single_obj_constr

        Tests the number of constraints and objectives expanded

        """
        with open("test/test12.json", 'r') as j:
            contents = json.loads(j.read())
            solution = contents['model']
            self.assertIn("nodes", solution)
            nodes = solution["nodes"]
            self.assertIn("A", nodes)
            node_a = nodes["A"]
            self.assertIn("number_expanded_constraints", node_a)
            nb_constr_derived = node_a["number_expanded_constraints"]
            self.assertIn("number_expanded_objectives", node_a)
            nb_obj_derived = node_a["number_expanded_objectives"]
            self.assertEqual(nb_constr_derived, 1)
            self.assertEqual(nb_obj_derived, 1)

    def test_precise_where(self):
        """ test_precise_where

        Tests the where keyword for constraints

        """
        process = subprocess.run(['gboml', 'test/test13.txt', "--matrix"],
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
        output_split = process.stdout.split("\n")
        self.assertEqual(output_split[4], 'Matrix A_ineq    (0, 9)\t-1.0')
        self.assertEqual(output_split[5], 'Vector b_ineq  [-0.]')
        self.assertEqual(output_split[6],
                         "Vector C  [[0. 0. 0. 0. 0. 0. 0. 0. 0. 1.]]")
        return_code = process.returncode
        self.assertEqual(return_code, 0)

    # for t in [9:10]
    def test_precise_for(self):
        """ test_precise_for

        Tests a for range for a constraint

        """
        process = subprocess.run(['gboml', 'test/test14.txt', "--matrix"],
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
        output_split = process.stdout.split("\n")
        self.assertEqual(output_split[4], 'Matrix A_ineq    (0, 9)\t-1.0')
        self.assertEqual(output_split[5], 'Vector b_ineq  [-0.]')
        self.assertEqual(output_split[6],
                         "Vector C  [[0. 0. 0. 0. 0. 0. 0. 0. 0. 1.]]")
        return_code = process.returncode
        self.assertEqual(return_code, 0)

    def test_links(self):
        """ test_links

        Tests the linking between two nodes

        """
        process = subprocess.run(
            ['gboml', 'test/test15.txt', "--gurobi", "--json",
             "--output", "test/test15"],
            stdout=subprocess.PIPE,
            universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)
        with open("test/test15.json", 'r') as j:
            contents = json.loads(j.read())
            links = [[["A", "b"], ["R", "f"]],
                     [["A", "b"], ["R", "ff"]],
                     [["R", "h"], ["A", "a"]],
                     [["A", "c"], ["R", "d"]]]
            solution = contents["solution"]
            for [lhs_node, lhs_var], [rhs_node, rhs_var] in links:
                all_nodes = solution["elements"]
                self.assertIn(lhs_node, all_nodes)
                self.assertIn(rhs_node, all_nodes)

                lhs_node_dict = all_nodes[lhs_node]
                rhs_node_dict = all_nodes[rhs_node]

                lhs_node_variables = lhs_node_dict["variables"]
                rhs_node_variables = rhs_node_dict["variables"]

                self.assertIn(lhs_var, lhs_node_variables)
                self.assertIn(rhs_var, rhs_node_variables)

                self.assertTrue(
                    lhs_node_variables[lhs_var] == rhs_node_variables[rhs_var])

    def test_time_dependency_in_obj(self):
        """ test_time_dependancy_in_obj

        Tests the time dependancy of an objective

        """
        process = subprocess.run(['gboml', 'test/test16.txt', "--matrix"],
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
        output_split = process.stdout.split("\n")
        self.assertEqual(output_split[11], "Vector C  [[6. 0. 0. 1. 0. 0.]]")
        return_code = process.returncode
        self.assertEqual(return_code, 0)

    def test_wrong_variable_def(self):
        """ test_wrong_variable_def

        Tests a simple file with a variable wrongly defined

        """
        process = subprocess.run(['gboml', 'test/test17.txt'],
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
        return_code = process.returncode
        self.assertNotEqual(return_code, 0)

    def test_sum_objective(self):
        """ test_sum_objective

        Tests a sum for defining an objective

        """
        process = subprocess.run(['gboml', 'test/test18.txt', "--matrix"],
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
        output_split = process.stdout.split("\n")
        self.assertEqual(output_split[15],
                         "Vector C  [[1. 1. 1. 1. 1. 1. 1. 1. 1. 1. "
                         "0. 0. 0. 0. 0. 0. 0. 0. 0. 0.]]")
        return_code = process.returncode
        self.assertEqual(return_code, 0)

    def test_bigger_variable(self):
        """ test_bigger_Variable

        Tests a variable whose size exceeds the timehorizon

        """
        process = subprocess.run(
            ['gboml', 'test/test19.txt', "--gurobi", "--json",
             "--output", "test/test19"],
            stdout=subprocess.PIPE,
            universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)
        with open("test/test19.json", 'r') as j:
            contents = json.loads(j.read())
            solution = contents["solution"]
            obj = solution["objective"]
            self.assertEqual(obj, 10.0)

    def test_hyperlink(self):
        """ test_hyperlink

        Tests a hyperlink with parameters and that it is correctly converted
        to matrices

        """

        process = subprocess.run(
            ['gboml', 'test/test20.txt', "--gurobi", "--json",
             "--output", "test/test20"],
            stdout=subprocess.PIPE,
            universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)
        with open("test/test20.json", 'r') as j:
            contents = json.loads(j.read())
            solution = contents["solution"]
            nodes = solution["elements"]
            node_a = nodes["A"]
            node_b = nodes['B']
            ax = node_a["variables"]["x"]["values"]
            by = node_b["variables"]["y"]["values"]
            bw = node_b["variables"]["w"]["values"]

            for i in range(6):
                self.assertEqual(ax[i], by[i] + bw[i])

    def test_globalkey(self):
        """ test_globalkey

        Tests that the global parameters are present through-out the file

        """
        process = subprocess.run(['gboml', 'test/test21.txt', "--gurobi",
                                  "--json", "--output", "test/test21"],
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)

        with open("test/test21.json", 'r') as j:
            contents = json.loads(j.read())
            model = contents["model"]
            nodes = model["nodes"]

            node_o = nodes["O"]
            parameters_o = node_o["parameters"]
            p1 = parameters_o["p1"][0]
            p2 = parameters_o["p2"][0]
            self.assertEqual(p1, 2)
            self.assertEqual(p2, 3)

            solution = contents["solution"]
            obj = solution["objective"]
            self.assertEqual(obj, 5.0)

    def test_encapsulation(self):
        """ test_encapsulation

        Tests a node defined inside another node

        """
        global PATH
        os.chdir(PATH)

        _, matrix_eq, vector_b_eq, matrix_ineq, vector_b_ineq, vector_c, indep_terms_c, \
         alone_term_c, time_horizon, name_tuples = compile_gboml("test/test23.txt")
        objective_offset = float(indep_terms_c.sum())
        c_sum = np.asarray(vector_c.sum(axis=0), dtype=float)
        self.assertEqual(objective_offset, 0)
        self.assertTrue(np.allclose(c_sum, np.array([1., 1., 0., 0., 0., 0., 0., 0., 0., 0.])))
        self.assertTrue(np.allclose(vector_b_eq,
                                    np.array([120., 0., 0., 0., 6.9, 6.4])))
        expected_matrix_a = [[1., 0., 0., 0., 0., 0., 0., 0., 0., 0.],
                             [0., 0., -1., 1., -0.75, 0., 1.33333333, 0., 0., 0.],
                             [0., 0., 1., -1., 0., 0., 0., 0., 0., 0.],
                             [-3.14, 1., 0., 0., 0., 0., 0., 0., 0., 0.],
                             [0., 0., 0., 0., 0., 0., 0., 0., 1., 0.],
                             [0., 0., 0., 0., 0., 0., 0., 0., 0., 1.]]
        self.assertTrue(((matrix_eq.todense() - np.array(expected_matrix_a)) <= 0.1).all())
        x, objective, _, _, _, _ = gurobi_solver(matrix_eq, vector_b_eq, matrix_ineq, vector_b_ineq,
                                                 c_sum, objective_offset, name_tuples)
        self.assertTrue((np.array([120., 376.8, 0., 0., 0., 0., 0., 0., 6.9, 6.4]) == x).all())
        self.assertEqual(objective, 496.8)

    def test_encapsulation_with_hyperedge(self):
        """ test_encapsulation_with_hyperedge

        Tests a node defined inside another node with a hyperedge

        """
        global PATH
        os.chdir(PATH)
        _, matrix_eq, vector_b_eq, matrix_ineq, vector_b_ineq, vector_c, indep_terms_c, \
         alone_term_c, time_horizon, name_tuples = compile_gboml("test/test24.txt")
        objective_offset = float(indep_terms_c.sum())
        c_sum = np.asarray(vector_c.sum(axis=0), dtype=float)
        x, objective, _, _, _, _ = gurobi_solver(matrix_eq, vector_b_eq, matrix_ineq, vector_b_ineq, c_sum,
                                                objective_offset, name_tuples)
        self.assertTrue((np.array([120., 1080., 0., 0., 0., 0., 0., 0., 6.9, 6.4, 118]) == x).all())
        self.assertEqual(objective, 1200)

    def test_import_hyperedge(self):
        """ test_import_hyperedge

        Tests a hyperedge import

        """
        global PATH
        os.chdir(PATH)
        _, matrix_eq, vector_b_eq, matrix_ineq, vector_b_ineq, vector_c, indep_terms_c, \
         alone_term_c, time_horizon, name_tuples = compile_gboml("test/test25.txt")
        objective_offset = float(indep_terms_c.sum())+alone_term_c
        c_sum = np.asarray(vector_c.sum(axis=0), dtype=float)
        x, objective, _, _, _, _ = xpress_solver(matrix_eq, vector_b_eq, matrix_ineq, vector_b_ineq,
                                                 c_sum, objective_offset, name_tuples)
        self.assertTrue((np.array([6., 5.]) == x).all())
        self.assertEqual(11, objective)

    def test_nested_nodes_accessing_to_one_variable_and_parent_parameters(self):
        """ test_nested_nodes_accessing_to_one_variable_and_parent_parameters

        Tests a series of nested nodes with only one variable defined

        """
        global PATH
        os.chdir(PATH)
        # program, matrix_eq, vector_b_eq, matrix_ineq, vector_b_ineq, vector_c, indep_terms_c, \
        #            alone_term_c, time_horizon, program.get_tuple_name()
        _, matrix_eq, vector_b_eq, matrix_ineq, vector_b_ineq, vector_c, \
         indep_terms_c, alone_term_c, _, _ = compile_gboml("test/test26.txt")
        objective_offset = float(indep_terms_c.sum())+alone_term_c
        c_sum = np.asarray(vector_c.sum(axis=0), dtype=float)
        self.assertEqual(objective_offset, 1)
        self.assertTrue((np.array([[1.], [-1.]]) == matrix_ineq.todense()).all())
        self.assertEqual(c_sum.all(), np.array([1]))
        self.assertTrue((vector_b_ineq == np.array([6., -1.])).all())

    def test_nested_nodes_accessing_to_array_variable_and_parent_parameters(
            self):
        """ test_nested_nodes_accessing_to_array_variable_and_parent_parameters

        Tests a series of nested nodes with only one variable defined and
        parameters intertwined

        """
        global PATH
        os.chdir(PATH)
        _, matrix_eq, vector_b_eq, matrix_ineq, vector_b_ineq, vector_c, \
         indep_terms_c, alone_term_c, _, name_tuples = compile_gboml("test/test27.txt")
        objective_offset = float(indep_terms_c.sum())
        c_sum = np.asarray(vector_c.sum(axis=0), dtype=float)
        self.assertEqual(objective_offset, 0)
        solution = cplex_solver(matrix_eq, vector_b_eq, matrix_ineq, vector_b_ineq,
                                 c_sum, objective_offset, name_tuples)
        self.assertTrue((solution[0] == np.array([1., 1., 1., 1., 1.])).all())

    def test_nested_nodes_with_hyperedge_and_parent_parameters(self):
        """ test_nested_nodes_with_hyperedge_and_parent_parameters

        Tests a series of nested nodes with two low level nodes and a hyperedge

        """
        global PATH
        os.chdir(PATH)
        _, matrix_a_eq, vector_b_eq, matrix_a_ineq, vector_b_ineq, vector_c, \
        indep_terms_c, alone_term_c, _, name_tuples = compile_gboml("test/test28.txt")
        objective_offset = float(indep_terms_c.sum())
        c_sum = np.asarray(vector_c.sum(axis=0), dtype=float)
        expected_constraint_matrix_eq = np.array([[1, 0, 1, 0], [0, 1, 0, 1]])
        expected_constraint_matrix_ineq = np.array([[0, 0, 1, 0], [0, 0, 0, 1], [-1, 0, 0, 0],
                                                    [0, -1, 0, 0], [0, 0, -1, 0], [0, 0, 0, -1]])

        expected_vector_b_eq = np.array([10, 10])
        expected_vector_b_ineq = np.array([6, 6, -5.5, -5.5, -1, -1])
        expected_vector_c = np.array([[1, 1, 1, 1]])

        self.assertEqual(objective_offset, 0)
        self.assertTrue((expected_vector_c.all() == c_sum).all())
        self.assertTrue((expected_vector_b_eq == vector_b_eq).all())
        self.assertTrue((expected_vector_b_ineq == vector_b_ineq).all())
        self.assertTrue((matrix_a_eq.todense() == expected_constraint_matrix_eq).all())
        self.assertTrue((matrix_a_ineq.todense() == expected_constraint_matrix_ineq).all())

    def test_dual(self):
        """ test_dual

        Tests the dual value of a constraint

        """

        process = subprocess.run(
            ['gboml', 'test/test29_duals.txt', "--gurobi", "--json", "--detailed",
             "--output", "test/test29"],
            stdout=subprocess.PIPE,
            universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)
        with open("test/test29.json", 'r') as j:
            contents = json.loads(j.read())
            solution = contents["solution"]
            nodes = solution["elements"]
            node_system = nodes["system"]
            constraints = node_system["constraints"]
            test_constraint = constraints["test_constraint"]
            dual_value = test_constraint["Pi"]
            self.assertEqual(dual_value[0], 10.0)

    def test_import_five(self):
        """ test_import_five

        Tests import five times the same node and sum in hyperedge

        """

        process = subprocess.run(
            ['gboml', 'test/test30_import5.txt', "--gurobi", "--json",
             "--output", "test/test30"],
            stdout=subprocess.PIPE,
            universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)
        with open("test/test30.json", 'r') as j:
            contents = json.loads(j.read())
            solution = contents["solution"]
            nodes = solution["elements"]
            node_system = nodes["Demande"]
            variables = node_system["variables"]
            tot_score = variables["score_total"]["values"]
            self.assertEqual(tot_score[0], 0.6)

    def test_rename_vector_param(self):
        """ test_rename_vector_param

        Tests redefining a vector parameters

        """
        process = subprocess.run(
            ['gboml', 'test/test31_rename.txt'],
            stdout=subprocess.PIPE,
            universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)

    def test_rename_node(self):
        """ test_rename_node

        Tests redefining several nodes with import

        """
        process = subprocess.run(
            ['gboml', 'test/test_32_rename.txt'],
            stdout=subprocess.PIPE,
            universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)


class GBOMLpyTest(unittest.TestCase):
    """
    GBOMLpyTest

    Tests the GBOML python interface

    It checks whether a file correctly fails, generates the correct matrices,
    correct solutions and correct output.

    """

    def test_horizon_initialization(self):
        """ test_horizon_intialization

        Tests initializing the timehorizon with a value

        """
        timehorizon_considered = 10
        gboml_model = GbomlGraph(timehorizon_considered)
        self.assertEqual(gboml_model.get_timehorizon(), timehorizon_considered)

    def test_horizon_set(self):
        """ test_horizon_set

        Tests setting the timehorizon after object initialization

        """
        gboml_model = GbomlGraph()
        gboml_model.set_timehorizon(12)
        self.assertEqual(gboml_model.get_timehorizon(), 12)

    def test_import_same_name(self):
        """ test_import_same_name

        Tests importing a node without renaming it

        """
        gboml_model = GbomlGraph()
        node_pv = gboml_model.import_node("examples/microgrid/microgrid.txt",
                                          "SOLAR_PV", copy=True)
        self.assertEqual(type(node_pv), Node)
        self.assertEqual(node_pv.get_name(), "SOLAR_PV")

    def test_renaming_in_import(self):
        """ test_renaming_in_import

        Test importing a node and renaming it

        """
        gboml_model = GbomlGraph()
        node_b = gboml_model.import_node("examples/microgrid/microgrid.txt",
                                         "DEMAND", new_node_name="B", copy=True)
        self.assertEqual(node_b.get_name(), "B")
        self.assertEqual(type(node_b), Node)

    def test_redefine_parameters_from_list(self):
        """ test_redefine_parameters_from_list

        Tests importing a node, redefining its parameters and checking changes

        """
        gboml_model = GbomlGraph()
        node_pv = gboml_model.import_node("examples/microgrid/microgrid.txt",
                                          "SOLAR_PV", copy=True)
        all_parameters_names = []
        all_parameters_values = []
        for i, parameter in enumerate(node_pv.get_parameters()):
            all_parameters_names.append(parameter.get_name())
            all_parameters_values.append(i)

        gboml_model.redefine_parameters_from_list(node_pv, all_parameters_names,
                                                  all_parameters_values)
        for i, parameter in enumerate(node_pv.get_parameters_changes()):
            name = parameter.get_name()
            value = parameter.get_expression().get_name()
            self.assertEqual(name, all_parameters_names[i])
            self.assertEqual(value, all_parameters_values[i])

        node_pv_2 = gboml_model.import_node("examples/microgrid/microgrid.txt",
                                            "SOLAR_PV", copy=True)
        self.assertEqual(node_pv_2.get_parameters_changes(), [])

    def test_remove_objective(self):
        """ test_remove_objective

        Tests importing a node and removing its objective

        """
        gboml_model = GbomlGraph()
        node_pv = gboml_model.import_node("examples/microgrid/microgrid.txt",
                                          "SOLAR_PV", copy=True)
        gboml_model.remove_objective_in_node(node_pv, "investment")
        for objective in node_pv.get_objectives():
            self.assertTrue(objective.get_name() != "investment")

    def test_change_type_variable(self):
        """ test_change_type_variable

        Tests importing a node and changing the type of one of its variables

        """
        gboml_model = GbomlGraph()
        node_pv = gboml_model.import_node("examples/microgrid/microgrid.txt",
                                          "SOLAR_PV", copy=True)
        gboml_model.change_type_variable_in_node(node_pv, "investment",
                                                 VariableType.EXTERNAL)
        self.assertEqual(len(node_pv.get_variables_changes()), 1)
        self.assertEqual(node_pv.get_variables_changes(),
                         [["investment", "external", 0]])

    def test_import_everything_and_solve(self):
        """ test_import_everything_and_solve

        Tests to import a full file, renaming its nodes and solve it

        """
        import os
        import sys
        f = open(os.devnull, 'w')
        temp = sys.stdout
        sys.stdout = f

        gboml_model = GbomlGraph()
        gboml_model_with_1 = GbomlGraph()
        nodes, edges, global_params = gboml_model.import_all_nodes_and_edges(
            "examples/microgrid/microgrid.txt")

        old_names = []
        for node in nodes:
            old_names.append(node.get_name())
            gboml_model_with_1.rename(node, node.get_name() + "_1")

        for hyperedge in edges:
            gboml_model_with_1.rename(hyperedge, hyperedge.get_name() + "_1")
            for i, node in enumerate(nodes):
                gboml_model_with_1.change_node_name_in_hyperedge(hyperedge,
                                                                 old_names[i],
                                                                 node.get_name()
                                                                 )

        gboml_model_with_1.add_nodes_in_model(*nodes)
        gboml_model_with_1.add_hyperedges_in_model(*edges)
        gboml_model_with_1.add_global_parameters_objects(global_params)
        gboml_model_with_1.build_model()
        solution_with_1 = gboml_model_with_1.solve_gurobi()
        f.close()
        sys.stdout = temp
        self.assertEqual(solution_with_1[0].all(), np.array(
            [0., 0., 6.9, 0., 0., 0., 0., 6.9, 0., 0., 0.]).all())

    def test_encapsulating(self):
        """ test_encapsulating

        Tests to import the microgrid problem and put everything inside a toy
        node from tests and solve

        """
        import os
        import sys
        f = open(os.devnull, 'w')
        temp = sys.stdout
        sys.stdout = f

        gboml_model = GbomlGraph()
        nodes, edges, global_param = gboml_model.import_all_nodes_and_edges(
            "examples/microgrid/microgrid.txt")
        parent = gboml_model.import_node("test/test6.txt", "H", copy=True)
        for node in nodes:
            gboml_model.add_sub_node(node, parent)

        for edge in edges:
            gboml_model.add_sub_hyperedge(edge, parent)

        gboml_model.add_nodes_in_model(parent)
        gboml_model.add_global_parameters_objects(global_param)
        gboml_model.build_model()
        solution = gboml_model.solve_cplex("src/gboml/solver_api/cplex.opt", False, {"lpmethod": 1})
        f.close()
        sys.stdout = temp
        self.assertEqual(solution[0].all(), np.array(
            [0., 0., 6.9, 0., 0., 0., 0., 6.9, 0., 0., 0., 4.]).all())

    def test_toy_example(self):
        """ test_toy_example

        Tests combining importing, renaming, parameter_redefinition all
        together and solving

        """
        import os
        import sys
        f = open(os.devnull, 'w')
        temp = sys.stdout
        sys.stdout = f
        timehorizon = 3
        gboml_model = GbomlGraph(timehorizon)
        nodes, edges, global_params = gboml_model.import_all_nodes_and_edges(
            "examples/microgrid/microgrid.txt")
        old_names = []
        for node in nodes:
            old_names.append(node.get_name())
            gboml_model.rename(node, "new_" + node.get_name())

        for hyperedge in edges:
            gboml_model.rename(hyperedge, "new_" + hyperedge.get_name())
            for i, node in enumerate(nodes):
                gboml_model.change_node_name_in_hyperedge(hyperedge,
                                                          old_names[i],
                                                          node.get_name())

        parent = gboml_model.import_node("test/test6.txt", "H", copy=True)
        for node in nodes:
            gboml_model.add_sub_node(node, parent)

        for edge in edges:
            gboml_model.add_sub_hyperedge(edge, parent)

        gboml_model.redefine_parameters_from_keywords(parent, b=6)
        gboml_model.add_nodes_in_model(parent)
        gboml_model.add_global_parameters(global_params)
        gboml_model.add_global_parameters([("electricity_price", 0.05)])
        gboml_model.build_model()
        x, objective, status, solver_info = gboml_model.solve_cbc(opt_dict={"gap": [float, 10]})
        f.close()
        sys.stdout = temp
        self.assertTrue(np.allclose(x, np.array(
            [0.345, 0.32, 0., 6.9, 6.4, 0., 6.9, 6.4, 6.1, -0.,
             0., 0., 0., 0., 0., 0., 0., 0., 0., 6.1,
             -0., 0., 0., 0., 0., 6., 6., 6.])))


if __name__ == '__main__':
    """ __main__

    main initializing the unittests. 

    """
    unittest.main()
