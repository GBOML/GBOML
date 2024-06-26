import unittest
from pathlib import Path

from lark.exceptions import UnexpectedCharacters, UnexpectedToken

from gboml.ast.check import check
from gboml.parsing import GBOMLParser

instance_dir = Path(__file__).parent / "instances"

should_pass = [x
               for ok_dir in [
                   instance_dir / "ok",
                   instance_dir
               ]
               for x in ok_dir.iterdir()
               if str(x).endswith(".txt")]

should_not_pass = [x
                   for ko_dir in [instance_dir / "ko_parsing"]
                   for x in ko_dir.iterdir()
                   if str(x).endswith(".txt")]


parser = GBOMLParser()

class TestParsing(unittest.TestCase):
    def test_parse(self):
        """ Checks if the file (doesn't) parses """
        for filename in should_pass:
            with self.subTest(filename=filename):
                out = parser.parse_file(str(filename))
                check(out)

    def test_not_parse(self):
        for filename in should_not_pass:
            with self.subTest(filename=filename):
                try:
                    out = parser.parse_file(str(filename))
                    check(out)
                except:
                    continue
                raise Exception("Shouldn't success")


if __name__ == '__main__':
    unittest.main()