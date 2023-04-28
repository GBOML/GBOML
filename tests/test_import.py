import unittest
from pathlib import Path

from gboml.ast.check import check
from gboml.parsing import parse_file, parse
from gboml.resolve_imports import resolve_imports


class TestImport(unittest.TestCase):
    def test_import_nogen(self):
        tree = parse(
            """
                #TIMEHORIZON
                    T = 8760;
                #NODE A extends B from "instances/imports/b_nogen.gboml";
            """
        )
        print(resolve_imports(tree, Path('.')))

    def test_import_nogen_2(self):
        tree = parse(
            """
                #TIMEHORIZON
                    T = 8760;
                #NODE A extends B from "instances/imports/b_nogen.gboml"
                    #PARAMETERS
                        i = 2;
                    #VARIABLES
                        pass;
            """
        )
        print(resolve_imports(tree, Path('.')))

    def test_import_gen_1(self):
        tree = parse(
            """
                #TIMEHORIZON
                    T = 8760;
                #NODE A extends B[2] from "instances/imports/b_gen.gboml"
                    #PARAMETERS
                        j = 2;
                    #VARIABLES
                        pass;
            """
        )
        print(resolve_imports(tree, Path('.')))

    def test_import_gen_2(self):
        tree = parse(
            """
                #TIMEHORIZON
                    T = 8760;
                #NODE A extends B[2] from "instances/imports/b_gen.gboml"
                    #PARAMETERS
                        i = 2; //this should fail, as i is an index of B
                    #VARIABLES
                        pass;
            """
        )
        print(resolve_imports(tree, Path('.')))

if __name__ == '__main__':
    unittest.main()
