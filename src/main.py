#!/usr/bin/env python3

from gboml.ast import gboml_eval
from gboml.matrix_generation import matrix_generation
from gboml.parsing import GBOMLParser
from gboml.semantic import semantic_check
from gboml.tree_post_process import post_process

parser = GBOMLParser()
tree = parser.parse("""
// Working example where x = -256 = y
#TIMEHORIZON T=2;
#NODE H
    #PARAMETERS
        b = -2 - 5/5 * 60 / 60 + 0 * 1331/11/11;
		a = b ** 2 ** 3;
    #VARIABLES
        internal : y[T];  // TODO try y[T][T]
        internal : x;
    #CONSTRAINTS
        -(1 - x + 6 * x / 3 + 1) * 2 <= a - 2 ** 2 - x;
        y[t] >= x - t where t;
        //x - y[t] == 0;
    #OBJECTIVES
        max : x;
        min : y[t];

""")

tree = post_process(tree, parser)
print(tree)


param_defs = {}
for d in semantic_check(tree):
    param_defs[d.semantic.scope.path_to_str()] = gboml_eval(d, param_defs)
print("all params values: ", param_defs)

A_eq, b_eq, A_ineq, b_ineq = matrix_generation(tree, param_defs)
print("equality constraints array:\n", A_eq.toarray(), '\n', b_eq)
print("inequality constraints array:\n", A_ineq.toarray(), '\n', b_ineq)
