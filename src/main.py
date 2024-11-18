#!/usr/bin/env python3

from gboml.parsing import GBOMLParser
from gboml.semantic import semantic_check
from gboml.tree_post_process import post_process

parser = GBOMLParser()
tree = parser.parse("""
// Working example where x = -256
#NODE H
    #PARAMETERS
        a = b ** 2 ** 3;
        b = -2 - 5/5 * 60 % 5 + 0 * 1331/11/11 + c;
        c = 2 ** -1 - .5 + d;
        d = 2 - 3 + 1 + e;
        e = -2 ** 2 + 4 + f;
        f = 4 + -2 ** 2 + g;
        g = 2 ** -2 ** 2 - .0625;
    #VARIABLES
        internal : x;
    #CONSTRAINTS
        -(1 - x + 6 * x / 3 + 9 % 8) * 2 <= a - 2 ** 2 - x;
    #OBJECTIVES
        max : x;

""")

tree = post_process(tree, parser)
print(tree)
semantic_check(tree)
