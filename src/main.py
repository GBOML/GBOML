#!/usr/bin/env python3

from gboml.parsing import GBOMLParser
from gboml.redundant_definitions import remove_redundant_definitions
from gboml.semantic import semantic_check
from gboml.scope import GlobalScope

# ConstantDefinition(name='m', value=Array(content=[GeneratedRValue(value=VarOrParam(path=[VarOrParamLeaf(name='i', indices=[])]),loop=BaseLoop(varid='i', on=Range(start=0, end=10, step=None), condition=None)),
                                                  # GeneratedRValue(value=VarOrParam(path=[VarOrParamLeaf(name='i', indices=[])]),loop=BaseLoop(varid='i', on=Range(start=100, end=120, step=None), condition=None))]), tags=set())

tree = GBOMLParser().parse("""

#TIMEHORIZON T = 2;
#GLOBAL
    pi = 314;

#NODE A
    #PARAMETERS
        param = 1;
        subnodes = {P};
        z=4;
        a <- 1;
        a <- a + 1;
        a <- a + 1;
        a <- a + 1;
        f(a) <- global.pi ** a;
        m = {a for a in [0:10], i for i in [100:120]};
        dict = {f(param) * 2 - 3: P, "je": B};
        f(b) <- global.pi ** b;
    #NODE P
        pass;

    #NODE B
        #PARAMETERS
            param = 2;
        #NODE C
            #PARAMETERS
                param = 3;
            #NODE D
                #PARAMETERS
                    param = 4;
                #VARIABLES
                    external : x[T];
                #CONSTRAINTS
                    x[t] >= A.param;

            #NODE E
                #PARAMETERS
                    param = 5.5;
                #VARIABLES
                    external integer : y[T];
                #CONSTRAINTS
                    y[t] >= param;
                #OBJECTIVES
                    min: y[t];

            #HYPEREDGE H
                #PARAMETERS
                    param = A.param;
                #CONSTRAINTS
                    E.y[t]+D.x[t] == param+9;

            #VARIABLES
                internal : x[T] <- D.x[T];
            #CONSTRAINTS
                x[t] <= B.param+A.param+param;
        #VARIABLES
            internal : x[T] <- C.x[T];
    #VARIABLES
        internal : x[T] <- B.x[T];
    #OBJECTIVES
        min : x[t-5] + f(global.pi) + subnodes[param];
""")

tree = remove_redundant_definitions(tree)
print(tree)
# print(tree.meta)
# print(tree.global_defs[0].meta)
globalScope = GlobalScope(tree)
semantic_check(globalScope)
# parse_file("test/test1.txt")
