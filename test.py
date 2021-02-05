import unittest
import subprocess
import json

class TestErrors(unittest.TestCase):

    #Case where we try to access a nonexistant file 
    def test_nonexistant_file(self):
        process = subprocess.run(['python', 'main.py', 'test/nonexistant.txt'], 
                           stdout=subprocess.PIPE,
                           universal_newlines=True)
        return_code = process.returncode
        self.assertNotEqual(return_code, 0)

    #The file is completely empty
    def test_empty_file(self):
        process = subprocess.run(['python', 'main.py', 'test/empty.txt'], 
                           stdout=subprocess.PIPE,
                           universal_newlines=True)
        return_code = process.returncode
        self.assertNotEqual(return_code, 0)

    #Only the horizon is defined
    def test_timehorizon_only(self):
        process = subprocess.run(['python', 'main.py', 'test/test1.txt'], 
                           stdout=subprocess.PIPE,
                           universal_newlines=True)
        return_code = process.returncode
        self.assertNotEqual(return_code, 0)

    #The horizon is defined with a wrong name
    def test_wrong_horizon(self):
        process = subprocess.run(['python', 'main.py', 'test/test2.txt'], 
                           stdout=subprocess.PIPE,
                           universal_newlines=True)
        return_code = process.returncode
        self.assertNotEqual(return_code, 0)

    #The horizon is negative
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
        process = subprocess.run(['python', 'main.py', 'test/test5.txt',"--gurobi"], 
                           stdout=subprocess.PIPE,
                           universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)
    
    # Cplex for an impossible problem
    def test_unfeasible_problem_cplex(self):
        process = subprocess.run(['python', 'main.py', 'test/test5.txt',"--cplex"], 
                           stdout=subprocess.PIPE,
                           universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)

    # CLP for an impossible problem
    def test_unfeasible_problem_clp(self):
        process = subprocess.run(['python', 'main.py', 'test/test5.txt',"--clp"], 
                           stdout=subprocess.PIPE,
                           universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)

    # Linprog for an impossible problem
    def test_unfeasible_problem_linprog(self):
        process = subprocess.run(['python', 'main.py', 'test/test5.txt',"--linprog"], 
                           stdout=subprocess.PIPE,
                           universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)

    # Gurobi positive problem resolution
    def test_positive_solution_gurobi(self):
        process = subprocess.run(['python', 'main.py', 'test/test6.txt',"--gurobi","--json"], 
                           stdout=subprocess.PIPE,
                           universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)

        with open("test/test6.json", 'r') as j:
            contents = json.loads(j.read())
            self.assertIn("objective", contents["solution"])
            self.assertEqual(contents["solution"]["objective"],40.0)

    # Cplex positive problem resolution
    def test_positive_solution_cplex(self):
        process = subprocess.run(['python', 'main.py', 'test/test6.txt',"--cplex","--json"], 
                           stdout=subprocess.PIPE,
                           universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)

        with open("test/test6.json", 'r') as j:
            contents = json.loads(j.read())
            self.assertIn("objective", contents["solution"])
            self.assertEqual(contents["solution"]["objective"],40.0)

    # CLP positive problem resolution
    def test_positive_solution_clp(self):
        process = subprocess.run(['python', 'main.py', 'test/test6.txt',"--clp","--json"], 
                           stdout=subprocess.PIPE,
                           universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)

        with open("test/test6.json", 'r') as j:
            contents = json.loads(j.read())
            self.assertIn("objective", contents["solution"])
            self.assertEqual(contents["solution"]["objective"],40.0)

    # Linprog positive problem resolution
    def test_positive_solution_linprog(self):
        process = subprocess.run(['python', 'main.py', 'test/test6.txt',"--linprog","--json"], 
                           stdout=subprocess.PIPE,
                           universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)

        with open("test/test6.json", 'r') as j:
            contents = json.loads(j.read())
            self.assertIn("objective", contents["solution"])
            self.assertEqual(contents["solution"]["objective"],40.0)

    # Gurobi negative problem resolution
    def test_negative_solution_gurobi(self):
        process = subprocess.run(['python', 'main.py', 'test/test7.txt',"--gurobi","--json"], 
                           stdout=subprocess.PIPE,
                           universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)

        with open("test/test7.json", 'r') as j:
            contents = json.loads(j.read())
            self.assertIn("objective", contents["solution"])
            self.assertEqual(contents["solution"]["objective"],4.0)

    # Cplex negative problem resolution
    def test_negative_solution_cplex(self):
        process = subprocess.run(['python', 'main.py', 'test/test7.txt',"--cplex","--json"], 
                           stdout=subprocess.PIPE,
                           universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)

        with open("test/test7.json", 'r') as j:
            contents = json.loads(j.read())
            self.assertIn("objective", contents["solution"])
            self.assertEqual(contents["solution"]["objective"],4.0)

    # CLP negative problem resolution
    def test_negative_solution_clp(self):
        process = subprocess.run(['python', 'main.py', 'test/test7.txt',"--clp","--json"], 
                           stdout=subprocess.PIPE,
                           universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)

        with open("test/test7.json", 'r') as j:
            contents = json.loads(j.read())
            self.assertIn("objective", contents["solution"])
            self.assertEqual(contents["solution"]["objective"],4.0)

    # Linprog negative problem resolution
    def test_negative_solution_linprog(self):
        process = subprocess.run(['python', 'main.py', 'test/test7.txt',"--linprog","--json"], 
                           stdout=subprocess.PIPE,
                           universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)

        with open("test/test7.json", 'r') as j:
            contents = json.loads(j.read())
            self.assertIn("objective", contents["solution"])
            self.assertEqual(contents["solution"]["objective"],4.0)

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
        if process.stdout.count("\n")!=3:
            print("Please remove the additional prints before you push")
            
    # test a file with T as assignment of a variable
    def test_assignment_T(self):
        process = subprocess.run(['python', 'main.py', 'test/test12.txt',"--gurobi","--json"], 
                           stdout=subprocess.PIPE,
                           universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)
    
    # nb of constraint and objective derived checked
    def test_single_obj_constr(self):
        with open("test/test12.json", 'r') as j:
            contents = json.loads(j.read())
            self.assertIn("nodes", contents)
            nodes = contents["nodes"]
            self.assertIn("A", nodes)
            nodeA = nodes["A"]
            self.assertIn("number_of_constraints_derived", nodeA)
            nb_constr_derived = nodeA["number_of_constraints_derived"]
            self.assertIn("number_of_objectives_derived", nodeA)
            nb_obj_derived = nodeA["number_of_objectives_derived"]
            self.assertEqual(nb_constr_derived, 1)
            self.assertEqual(nb_obj_derived,1)

    # where test t == 9
    def test_precise_where(self):
        process = subprocess.run(['python', 'main.py', 'test/test13.txt',"--matrix"], 
                           stdout=subprocess.PIPE,
                           universal_newlines=True)
        output_split = process.stdout.split("\n")
        self.assertEqual(output_split[2],'Matrix A    (0, 9)\t-1.0')
        self.assertEqual(output_split[3],'Vector b  [-0.]')
        self.assertEqual(output_split[4],"Vector C  [[0. 0. 0. 0. 0. 0. 0. 0. 0. 1.]]")
        return_code = process.returncode
        self.assertEqual(return_code, 0)

    # for t in [9:10]
    def test_precise_for(self):
        process = subprocess.run(['python', 'main.py', 'test/test14.txt',"--matrix"], 
                           stdout=subprocess.PIPE,
                           universal_newlines=True)
        output_split = process.stdout.split("\n")
        self.assertEqual(output_split[2],'Matrix A    (0, 9)\t-1.0')
        self.assertEqual(output_split[3],'Vector b  [-0.]')
        self.assertEqual(output_split[4],"Vector C  [[0. 0. 0. 0. 0. 0. 0. 0. 0. 1.]]")
        return_code = process.returncode
        self.assertEqual(return_code, 0)
    
    def test_links(self):
        process = subprocess.run(['python', 'main.py', 'test/test15.txt',"--gurobi","--json"], 
                           stdout=subprocess.PIPE,
                           universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)
        with open("test/test15.json", 'r') as j:
            contents = json.loads(j.read())
            links = contents["links"]
            for l in links:
                l=l.replace("["," ")
                l=l.replace(']'," ")
                l=l.replace('.'," ")
                l=l.replace(","," ")
                l=l.split()
                all_nodes = contents["nodes"]
                node_name1 = l[0]
                variable_name1 = l[1]
                node_name2 = l[4]
                variable_name2 = l[5]
                self.assertIn(node_name1,all_nodes)
                self.assertIn(node_name2,all_nodes)
                node1 = all_nodes[node_name1]
                node2 = all_nodes[node_name2]
                variables1 = node1["variables"]
                variables2 = node2["variables"]
                self.assertIn(variable_name1,variables1)
                self.assertIn(variable_name2,variables2)
                self.assertTrue(variables1[variable_name1]==variables2[variable_name2])
    
    def test_time_dependency_in_obj(self):
        process = subprocess.run(['python', 'main.py', 'test/test16.txt',"--matrix"], 
                           stdout=subprocess.PIPE,
                           universal_newlines=True)
        output_split = process.stdout.split("\n")
        self.assertEqual(output_split[9],"Vector C  [[6. 0. 0. 1. 0. 0.]]")
        return_code = process.returncode
        self.assertEqual(return_code, 0)


if __name__ == '__main__':
    unittest.main()