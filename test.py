import unittest
import subprocess
import json
from gboml_script import GbomlGraph, VariableType
from compiler.classes import Parameter, Expression, Node, Hyperlink, Time, Program
from compiler import compile_gboml
from solver_api import gurobi_solver, cplex_solver
import numpy as np


class TestErrors(unittest.TestCase):

    # Case where we try to access a nonexistant file
    def test_nonexistant_file(self):
        
        process = subprocess.run(['python', 'main.py', 'test/nonexistant.txt'],
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
        return_code = process.returncode
        self.assertNotEqual(return_code, 0)

    # The file is completely empty
    def test_empty_file(self):
        process = subprocess.run(['python', 'main.py', 'test/empty.txt'],
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
        return_code = process.returncode
        self.assertNotEqual(return_code, 0)

    # Only the horizon is defined
    def test_timehorizon_only(self):
        process = subprocess.run(['python', 'main.py', 'test/test1.txt'],
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
        return_code = process.returncode
        self.assertNotEqual(return_code, 0)

    # The horizon is defined with a wrong name
    def test_wrong_horizon(self):
        process = subprocess.run(['python', 'main.py', 'test/test2.txt'],
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
        return_code = process.returncode
        self.assertNotEqual(return_code, 0)

    # The horizon is negative
    def test_negative_horizon(self):
        process = subprocess.run(['python', 'main.py', 'test/test3.txt'],
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
        return_code = process.returncode
        self.assertNotEqual(return_code, 0)
    
    # A constraint is impossible
    def test_impossible_constraint(self):
        process = subprocess.run(['python', 'main.py', 'test/test4.txt'],
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
        return_code = process.returncode
        self.assertNotEqual(return_code, 0)

    # Gurobi for an impossible problem
    def test_unfeasible_problem_gurobi(self):
        process = subprocess.run(['python', 'main.py', 'test/test5.txt', "--gurobi"],
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)
    
    # Cplex for an impossible problem
    def test_unfeasible_problem_cplex(self):
        process = subprocess.run(['python', 'main.py', 'test/test5.txt', "--cplex"],
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)

    # CLP for an impossible problem
    def test_unfeasible_problem_clp(self):
        process = subprocess.run(['python', 'main.py', 'test/test5.txt', "--clp"],
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)

    # Linprog for an impossible problem
    def test_unfeasible_problem_linprog(self):
        process = subprocess.run(['python', 'main.py', 'test/test5.txt', "--linprog"],
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)

    # Gurobi positive problem resolution
    def test_positive_solution_gurobi(self):
        process = subprocess.run(['python', 'main.py', 'test/test6.txt', "--gurobi", "--json",
                                  "--output", "test/test6"],
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)

        with open("test/test6.json", 'r') as j:
            contents = json.loads(j.read())
            self.assertIn("objective", contents["solution"])
            self.assertEqual(contents["solution"]["objective"], 40.0)

    # Cplex positive problem resolution
    def test_positive_solution_cplex(self):
        process = subprocess.run(['python', 'main.py', 'test/test6.txt', "--cplex", "--json", "--output", "test/test6"],
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)

        with open("test/test6.json", 'r') as j:
            contents = json.loads(j.read())
            self.assertIn("objective", contents["solution"])
            self.assertEqual(contents["solution"]["objective"], 40.0)

    # CLP positive problem resolution
    def test_positive_solution_clp(self):
        process = subprocess.run(['python', 'main.py', 'test/test6.txt', "--clp", "--json", "--output", "test/test6"],
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)

        with open("test/test6.json", 'r') as j:
            contents = json.loads(j.read())
            self.assertIn("objective", contents["solution"])
            self.assertEqual(contents["solution"]["objective"], 40.0)

    # Linprog positive problem resolution
    def test_positive_solution_linprog(self):
        process = subprocess.run(['python', 'main.py', 'test/test6.txt', "--linprog", "--json",
                                  "--output", "test/test6"],
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)

        with open("test/test6.json", 'r') as j:
            contents = json.loads(j.read())
            self.assertIn("objective", contents["solution"])
            self.assertEqual(contents["solution"]["objective"], 40.0)

    # Gurobi negative problem resolution
    def test_negative_solution_gurobi(self):
        process = subprocess.run(['python', 'main.py', 'test/test7.txt', "--gurobi", "--json",
                                  "--output", "test/test7"],
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)

        with open("test/test7.json", 'r') as j:
            contents = json.loads(j.read())
            self.assertIn("objective", contents["solution"])
            self.assertEqual(contents["solution"]["objective"], 4.0)

    # Cplex negative problem resolution
    def test_negative_solution_cplex(self):
        process = subprocess.run(['python', 'main.py', 'test/test7.txt', "--cplex", "--json", "--output", "test/test7"],
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)

        with open("test/test7.json", 'r') as j:
            contents = json.loads(j.read())
            self.assertIn("objective", contents["solution"])
            self.assertEqual(contents["solution"]["objective"], 4.0)

    # CLP negative problem resolution
    def test_negative_solution_clp(self):
        process = subprocess.run(['python', 'main.py', 'test/test7.txt', "--clp", "--json", "--output", "test/test7"],
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)

        with open("test/test7.json", 'r') as j:
            contents = json.loads(j.read())
            self.assertIn("objective", contents["solution"])
            self.assertEqual(contents["solution"]["objective"], 4.0)

    # Linprog negative problem resolution
    def test_negative_solution_linprog(self):
        process = subprocess.run(['python', 'main.py', 'test/test7.txt', "--linprog", "--json",
                                  "--output", "test/test7"],
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)

        with open("test/test7.json", 'r') as j:
            contents = json.loads(j.read())
            self.assertIn("objective", contents["solution"])
            self.assertEqual(contents["solution"]["objective"], 4.0)

    # Non linearity in constraint
    def test_non_linearity(self):
        process = subprocess.run(['python', 'main.py', 'test/test8.txt'],
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
        return_code = process.returncode
        self.assertNotEqual(return_code, 0)

    # import towards non existant file 
    def test_non_existant_import(self):
        process = subprocess.run(['python', 'main.py', 'test/test9.txt'],
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
        return_code = process.returncode
        self.assertNotEqual(return_code, 0)
    
    # non linear assignement
    def test_non_linear_assignment_import(self):
        process = subprocess.run(['python', 'main.py', 'test/test10.txt'],
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
        return_code = process.returncode
        self.assertNotEqual(return_code, 0)

    # normal test file just to check if any print is in there
    def test_normal_file(self):
        process = subprocess.run(['python', 'main.py', 'test/test11.txt'],
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)
        if process.stdout.count("\n") != 3:
            print("Please remove the additional prints before you push")
            
    # test a file with T as assignment of a variable
    def test_assignment_T(self):
        process = subprocess.run(['python', 'main.py', 'test/test12.txt', "--gurobi", "--json",
                                  "--output", "test/test12"],
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)
    
    # nb of constraint and objective derived checked
    def test_single_obj_constr(self):
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

    # where test t == 9
    def test_precise_where(self):
        process = subprocess.run(['python', 'main.py', 'test/test13.txt', "--matrix"],
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
        output_split = process.stdout.split("\n")
        self.assertEqual(output_split[2], 'Matrix A    (0, 9)\t-1.0')
        self.assertEqual(output_split[3], 'Vector b  [-0.]')
        self.assertEqual(output_split[4], "Vector C  [[0. 0. 0. 0. 0. 0. 0. 0. 0. 1.]]")
        return_code = process.returncode
        self.assertEqual(return_code, 0)

    # for t in [9:10]
    def test_precise_for(self):
        process = subprocess.run(['python', 'main.py', 'test/test14.txt', "--matrix"],
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
        output_split = process.stdout.split("\n")
        self.assertEqual(output_split[2], 'Matrix A    (0, 9)\t-1.0')
        self.assertEqual(output_split[3], 'Vector b  [-0.]')
        self.assertEqual(output_split[4], "Vector C  [[0. 0. 0. 0. 0. 0. 0. 0. 0. 1.]]")
        return_code = process.returncode
        self.assertEqual(return_code, 0)
    
    def test_links(self):
        process = subprocess.run(['python', 'main.py', 'test/test15.txt', "--gurobi", "--json",
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

                self.assertTrue(lhs_node_variables[lhs_var] == rhs_node_variables[rhs_var])

    def test_time_dependency_in_obj(self):
        process = subprocess.run(['python', 'main.py', 'test/test16.txt', "--matrix"],
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
        output_split = process.stdout.split("\n")
        self.assertEqual(output_split[9], "Vector C  [[6. 0. 0. 1. 0. 0.]]")
        return_code = process.returncode
        self.assertEqual(return_code, 0)

    def test_wrong_variable_def(self):
        process = subprocess.run(['python', 'main.py', 'test/test17.txt'],
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
        return_code = process.returncode
        self.assertNotEqual(return_code, 0)

    def test_sum_objective(self):
        process = subprocess.run(['python', 'main.py', 'test/test18.txt', "--matrix"],
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
        output_split = process.stdout.split("\n")
        self.assertEqual(output_split[13], "Vector C  [[1. 1. 1. 1. 1. 1. 1. 1. 1. 1. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0.]]")
        return_code = process.returncode
        self.assertEqual(return_code, 0)

    def test_bigger_variable(self):
        process = subprocess.run(['python', 'main.py', 'test/test19.txt', "--gurobi", "--json",
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
        process = subprocess.run(['python', 'main.py', 'test/test20.txt', "--gurobi", "--json",
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
                self.assertEqual(ax[i], by[i]+bw[i])

    def test_globalkey(self):
        process = subprocess.run(['python', 'main.py', 'test/test21.txt', "--cplex",
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
        _, matrix_a, vector_b, vector_c, indep_terms_c, time_horizon, name_tuples = compile_gboml("test/test23.txt")
        objective_offset = float(indep_terms_c.sum())
        c_sum = np.asarray(vector_c.sum(axis=0), dtype=float)
        self.assertEqual(objective_offset, 0)
        self.assertEqual(c_sum.all(), np.array([1., 1., 0., 0., 0., 0.]).all())
        self.assertEqual(vector_b.all(),
                         np.array([120., -120., -0., 1000., 0., 0., 0., 0., 6.9, -6.9, 6.4, -6.4]).all())
        expected_matrix_a = [[1., 0., 0., 0., 0., 0.], [-1., 0., 0., 0., 0., 0.], [-1., 0., 0., 0., 0., 0.],
                             [1., 0., 0., 0., 0., 0.], [0., 0., 1., 0., 0., 0.], [0., 0., 0., 1., 0., 0.],
                             [-3.14, 1., 0., 0., 0., 0.], [3.14, -1., 0., 0., 0., 0.],
                             [0., 0., 0., 0., 1., 0.], [0., 0., 0., 0., -1., 0.], [0., 0., 0., 0., 0., 1.],
                             [0., 0., 0., 0., 0., -1.]]
        self.assertEqual(matrix_a.todense().all(), np.array(expected_matrix_a).all())
        x, objective, _, _, _, _ = gurobi_solver(matrix_a, vector_b, c_sum, objective_offset, name_tuples)
        self.assertEqual(np.array([120., 376.8, 0., 0., 6.9, 6.4]).all(), x.all())
        self.assertEqual(objective, 496.8)
        x, objective, _, _, _, _ = cplex_solver(matrix_a, vector_b, c_sum, objective_offset, name_tuples)
        self.assertEqual(np.array([120., 376.8, 0., 0., 6.9, 6.4]).all(), x.all())
        self.assertLessEqual(abs(objective-496.8), 0.01)

    def test_encapsulation_with_hyperedge(self):
        _, matrix_a, vector_b, vector_c, indep_terms_c, time_horizon, name_tuples = compile_gboml("test/test24.txt")
        objective_offset = float(indep_terms_c.sum())
        c_sum = np.asarray(vector_c.sum(axis=0), dtype=float)
        x, objective, _, _, _, _ = cplex_solver(matrix_a, vector_b, c_sum, objective_offset, name_tuples)
        self.assertEqual(np.array([120., 1080., 0., 0., 6.9, 6.4, 118.]).all(), x.all())
        self.assertEqual(objective, 1200)

    def test_import_hyperedge(self):
        _, matrix_a, vector_b, vector_c, indep_terms_c, time_horizon, name_tuples = compile_gboml("test/test25.txt")
        objective_offset = float(indep_terms_c.sum())
        c_sum = np.asarray(vector_c.sum(axis=0), dtype=float)
        x, objective, _, _, _, _ = cplex_solver(matrix_a, vector_b, c_sum, objective_offset, name_tuples)
        self.assertEqual(np.array([6., 5.]).all(), x.all())
        self.assertEqual(11, objective)

    def test_nested_nodes_accessing_to_one_variable_and_parent_parameters(self):
        _, matrix_a, vector_b, vector_c, indep_terms_c, _, _ = compile_gboml("test/test26.txt")
        objective_offset = float(indep_terms_c.sum())
        c_sum = np.asarray(vector_c.sum(axis=0), dtype=float)
        self.assertEqual(objective_offset, 1)
        self.assertEqual(np.array([[1.], [-1.]]).all(), matrix_a.todense().all())
        self.assertEqual(c_sum.all(), np.array([1]))
        self.assertEqual(vector_b.all(), np.array([6., -1.]).all())


class GBOMLpyTest(unittest.TestCase):

    def test_horizon_initialization(self):
        timehorizon_considered = 10
        gboml_model = GbomlGraph(timehorizon_considered)
        self.assertEqual(gboml_model.get_timehorizon(), timehorizon_considered)

    def test_horizon_set(self):
        gboml_model = GbomlGraph()
        gboml_model.set_timehorizon(12)
        self.assertEqual(gboml_model.get_timehorizon(), 12)

    def test_import_same_name(self):
        gboml_model = GbomlGraph()
        node_pv = gboml_model.import_node("examples/microgrid/microgrid.txt", "SOLAR_PV", copy=True)
        self.assertEqual(type(node_pv), Node)
        self.assertEqual(node_pv.get_name(), "SOLAR_PV")

    def test_renaming_in_import(self):
        gboml_model = GbomlGraph()
        node_b = gboml_model.import_node("examples/microgrid/microgrid.txt", "DEMAND", new_node_name="B", copy=True)
        self.assertEqual(node_b.get_name(), "B")
        self.assertEqual(type(node_b), Node)

    def test_redefine_parameters_from_list(self):
        gboml_model = GbomlGraph()
        node_pv = gboml_model.import_node("examples/microgrid/microgrid.txt", "SOLAR_PV", copy=True)
        all_parameters_names = []
        all_parameters_values = []
        for i, parameter in enumerate(node_pv.get_parameters()):
            all_parameters_names.append(parameter.get_name())
            all_parameters_values.append(i)

        gboml_model.redefine_parameters_from_list(node_pv, all_parameters_names, all_parameters_values)
        for i, parameter in enumerate(node_pv.get_parameters_changes()):
            name = parameter.get_name()
            value = parameter.get_expression().get_name()
            self.assertEqual(name, all_parameters_names[i])
            self.assertEqual(value, all_parameters_values[i])

        node_pv_2 = gboml_model.import_node("examples/microgrid/microgrid.txt", "SOLAR_PV", copy=True)
        self.assertEqual(node_pv_2.get_parameters_changes(), [])

    def test_remove_objective(self):
        gboml_model = GbomlGraph()
        node_pv = gboml_model.import_node("examples/microgrid/microgrid.txt", "SOLAR_PV", copy=True)
        gboml_model.remove_objective_in_node(node_pv, "hi")
        self.assertEqual(node_pv.get_objectives(), [])

    def test_change_type_variable(self):
        gboml_model = GbomlGraph()
        node_pv = gboml_model.import_node("examples/microgrid/microgrid.txt", "SOLAR_PV", copy=True)
        gboml_model.change_type_variable_in_node(node_pv, "investment", VariableType.EXTERNAL)
        self.assertEqual(len(node_pv.get_variables_changes()), 1)
        self.assertEqual(node_pv.get_variables_changes(), [["investment", "external", 0]])

    def test_import_everything_and_solve(self):
        import os
        import sys
        f = open(os.devnull, 'w')
        temp = sys.stdout
        sys.stdout = f

        gboml_model = GbomlGraph()
        gboml_model_with_1 = GbomlGraph()
        nodes, edges = gboml_model.import_all_nodes_and_edges("examples/microgrid/microgrid.txt")

        old_names = []
        for node in nodes:
            old_names.append(node.get_name())
            gboml_model_with_1.rename(node, node.get_name()+"_1")

        for hyperedge in edges:
            gboml_model_with_1.rename(hyperedge, hyperedge.get_name()+"_1")
            for i, node in enumerate(nodes):
                gboml_model_with_1.change_node_name_in_hyperedge(hyperedge, old_names[i], node.get_name())

        gboml_model_with_1.add_nodes_in_model(*nodes)
        gboml_model_with_1.add_hyperedges_in_model(*edges)
        gboml_model_with_1.build_model()
        solution_with_1 = gboml_model_with_1.solve_cplex()
        f.close()
        sys.stdout = temp
        self.assertEqual(solution_with_1[0].all(), np.array([0., 0., 6.9, 0., 0., 0., 0., 6.9, 0., 0., 0.]).all())

    def test_encapsulating(self):
        import os
        import sys
        f = open(os.devnull, 'w')
        temp = sys.stdout
        sys.stdout = f

        gboml_model = GbomlGraph()
        nodes, edges = gboml_model.import_all_nodes_and_edges("examples/microgrid/microgrid.txt")
        parent = gboml_model.import_node("test/test6.txt", "H", copy=True)
        for node in nodes:
            gboml_model.add_sub_node(node, parent)

        for edge in edges:
            gboml_model.add_sub_hyperedge(edge, parent)

        gboml_model.add_nodes_in_model(parent)
        gboml_model.build_model()
        solution = gboml_model.solve_cplex()
        f.close()
        sys.stdout = temp
        self.assertEqual(solution[0].all(), np.array([0., 0., 6.9, 0., 0., 0., 0., 6.9, 0., 0., 0., 4.]).all())

    def test_toy_example(self):
        import os
        import sys
        f = open(os.devnull, 'w')
        temp = sys.stdout
        sys.stdout = f
        timehorizon = 3
        gboml_model = GbomlGraph(timehorizon)
        nodes, edges = gboml_model.import_all_nodes_and_edges("examples/microgrid/microgrid.txt")
        old_names = []
        for node in nodes:
            old_names.append(node.get_name())
            gboml_model.rename(node, "new_" + node.get_name())

        for hyperedge in edges:
            gboml_model.rename(hyperedge, "new_" + hyperedge.get_name())
            for i, node in enumerate(nodes):
                gboml_model.change_node_name_in_hyperedge(hyperedge, old_names[i], node.get_name())

        parent = gboml_model.import_node("test/test6.txt", "H", copy=True)
        for node in nodes:
            gboml_model.add_sub_node(node, parent)

        for edge in edges:
            gboml_model.add_sub_hyperedge(edge, parent)

        gboml_model.redefine_parameters_from_keywords(parent, b=6)
        gboml_model.add_nodes_in_model(parent)
        gboml_model.build_model()
        solution = gboml_model.solve_cplex()
        f.close()
        sys.stdout = temp
        self.assertEqual(solution[0].all(), np.array([0., 0., 0., 0., 0., 0., 6.9, 6.4, 6.1, 0., 0., 0., 0.,
                                                      0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 6.,
                                                      6., 6.]).all())


if __name__ == '__main__':
    unittest.main()
