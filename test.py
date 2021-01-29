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
            self.assertIn("objective", contents)
            self.assertEqual(contents["objective"],40.0)

    # Cplex positive problem resolution
    def test_positive_solution_cplex(self):
        process = subprocess.run(['python', 'main.py', 'test/test6.txt',"--cplex","--json"], 
                           stdout=subprocess.PIPE,
                           universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)

        with open("test/test6.json", 'r') as j:
            contents = json.loads(j.read())
            self.assertIn("objective", contents)
            self.assertEqual(contents["objective"],40.0)

    # CLP positive problem resolution
    def test_positive_solution_clp(self):
        process = subprocess.run(['python', 'main.py', 'test/test6.txt',"--clp","--json"], 
                           stdout=subprocess.PIPE,
                           universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)

        with open("test/test6.json", 'r') as j:
            contents = json.loads(j.read())
            self.assertIn("objective", contents)
            self.assertEqual(contents["objective"],40.0)

    # Linprog positive problem resolution
    def test_positive_solution_linprog(self):
        process = subprocess.run(['python', 'main.py', 'test/test6.txt',"--linprog","--json"], 
                           stdout=subprocess.PIPE,
                           universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)

        with open("test/test6.json", 'r') as j:
            contents = json.loads(j.read())
            self.assertIn("objective", contents)
            self.assertEqual(contents["objective"],40.0)

    # Gurobi negative problem resolution
    def test_negative_solution_gurobi(self):
        process = subprocess.run(['python', 'main.py', 'test/test7.txt',"--gurobi","--json"], 
                           stdout=subprocess.PIPE,
                           universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)

        with open("test/test7.json", 'r') as j:
            contents = json.loads(j.read())
            self.assertIn("objective", contents)
            self.assertEqual(contents["objective"],4.0)

    # Cplex negative problem resolution
    def test_negative_solution_cplex(self):
        process = subprocess.run(['python', 'main.py', 'test/test7.txt',"--cplex","--json"], 
                           stdout=subprocess.PIPE,
                           universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)

        with open("test/test7.json", 'r') as j:
            contents = json.loads(j.read())
            self.assertIn("objective", contents)
            self.assertEqual(contents["objective"],4.0)

    # CLP negative problem resolution
    def test_negative_solution_clp(self):
        process = subprocess.run(['python', 'main.py', 'test/test7.txt',"--clp","--json"], 
                           stdout=subprocess.PIPE,
                           universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)

        with open("test/test7.json", 'r') as j:
            contents = json.loads(j.read())
            self.assertIn("objective", contents)
            self.assertEqual(contents["objective"],4.0)

    # Linprog negative problem resolution
    def test_negative_solution_linprog(self):
        process = subprocess.run(['python', 'main.py', 'test/test7.txt',"--linprog","--json"], 
                           stdout=subprocess.PIPE,
                           universal_newlines=True)
        return_code = process.returncode
        self.assertEqual(return_code, 0)

        with open("test/test7.json", 'r') as j:
            contents = json.loads(j.read())
            self.assertIn("objective", contents)
            self.assertEqual(contents["objective"],4.0)

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

if __name__ == '__main__':
    unittest.main()