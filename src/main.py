#!/usr/bin/env python3

from gboml.parsing import GBOMLParser
from gboml.semantic import semantic_check
from gboml.scope import GlobalScope

tree = GBOMLParser().parse("""
#TIMEHORIZON T = 1;

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
                internal : y <- D.x;
            #CONSTRAINTS
                y <= B.b+A.a+c+global.z;
        #VARIABLES
            internal : x <- C.y;
    #VARIABLES
        internal : x <- B.x;
    #OBJECTIVES
        min : x + a;
""")

print(tree)
# print(tree.meta)
# print(tree.global_defs[0].meta)
globalScope = GlobalScope(tree)
semantic_check(globalScope)
# parse_file("test/test1.txt")
