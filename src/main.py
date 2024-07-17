#!/usr/bin/env python3

from gboml.parsing import GBOMLParser
from gboml.redundant_definitions import remove_redundant_definitions
from gboml.resolve_imports import resolve_imports
from gboml.semantic import semantic_check
from gboml.scope import GlobalScope
from gboml.tools.tree_modifier import modify
import dataclasses
import os
from pathlib import Path

tree = GBOMLParser().parse("""
#TIMEHORIZON T = 2*2;
#GLOBAL
    a = 75;
    pi = 314;
    m = {a for i2 in [0:10] where i2 + pi < 6 for i in [1:2] where i2 % i == 0};  // will use pi = 456
    pi = 456 + A.f(a);

#NODE A
    #PARAMETERS
        param = 1;
        subnodes = {P};
        z=4;
        a <- 1;
        a <- a + 1;
        a <- a + 1;
        a <- a + 1;
        f(a) <- global.pi ** iDontExistAndItsFineBecauseFunctionIsRedefinedAfter;
        n(aa,b,cc) <- aa+b+cc;
        q = [1:1];
        u in q;
        o = n(u, q, 2, i for i in [2:0]);
        
        dict = {f(param) * w - 3: P for w in [1:3:2], "je": B};
        f(b) <- global.pi ** b[b].x;
        hello = [0:2];
    #NODE P
        #PARAMETERS
            parentnodes = {A};
        #VARIABLES
            pass;
    

    #NODE GEN[bsasassaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa][j] for i in [0:3] where i == 3 for j in [3:6]
        #PARAMETERS
            x = i * j;
        #VARIABLES
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
                x[t] <= B.param+A.param+param+B.A.param+parent.param+parent.parent.param where t % 2 == 1;
        #VARIABLES
            internal : x[T] <- C.x[T] in [1:3];  // TODO
            internal : baba <- A.param;
    #VARIABLES
        internal : x[T] <- B.x[T];
    #OBJECTIVES
        min : x[t-5] + sum(l for l in hello where l < 2) + len(hello) + f(global.pi) + subnodes[param].a.a + (param > 1).x + (B * 2).param;

""")

for i in reversed(range(29)):
    if i == 25:
        continue  # no test25.txt
    print(f"------------------------------- {i} -------------------------------------")
# parser = GBOMLParser()
# tree = parser.parse_file(f"../tests/instances/ok/test{i}.txt")
# tree = resolve_imports(tree, Path('../tests/instances/ok/'), parser)
tree = remove_redundant_definitions(tree)
print(tree)

# print(tree.meta)
# print(tree.global_defs[0].meta)
globalScope = GlobalScope(tree)
semantic_check(globalScope)
# parse_file("test/test1.txt")
