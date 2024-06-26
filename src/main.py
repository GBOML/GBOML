#!/usr/bin/env python3

from gboml.parsing import GBOMLParser
from gboml.semantic import semantic_check
from gboml.scope import RootScope

tree = GBOMLParser().parse("""
#TIMEHORIZON T = 1;
#GLOBAL
    b = 4;

#NODE A
    #PARAMETERS
        a = 1;
    #NODE B
        #PARAMETERS
            b = 2;
        #NODE C
            #PARAMETERS
                c = 3;
            #NODE D
                #PARAMETERS
                    d = 4;
                #VARIABLES
                    internal : x;
                #CONSTRAINTS
                    x >= A.a;
            #VARIABLES
                internal : x <- D.x;
            #CONSTRAINTS
                x <= B.b+A.a+c+global.b;
        #VARIABLES
            internal : x <- C.x;
    #VARIABLES
        internal : x <- B.x;
    #OBJECTIVES
        min : x + a;
""")


['B', 'b']
['A', 'a']
['c']
['global', 'b']
['x']
['A', 'a']
['x']
['D', 'x']
['C', 'x']
['x']
['a']
['B', 'x']
['B', 'b']
['A', 'a']
['c']
['global', 'b']
['x']
['A', 'a']
['x']
['D', 'x']
['C', 'x']
['B', 'b']
['A', 'a']
['c']
['global', 'b']
['x']
['A', 'a']
['x']
['D', 'x']
['A', 'a']
['x']

print(tree)
# print(tree.meta)
# print(tree.global_defs[0].meta)
rootScope = RootScope(tree)
semantic_check(rootScope)
#parse_file("test/test1.txt")
