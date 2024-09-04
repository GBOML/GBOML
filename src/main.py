#!/usr/bin/env python3

from gboml.parsing import GBOMLParser
from gboml.resolve_imports import resolve_imports
from gboml.semantic import semantic_check
from gboml.tools.tree_modifier import modify
import dataclasses
import os
from pathlib import Path

parser = GBOMLParser()
tree = parser.parse("""
#TIMEHORIZON T = 2*2;
#GLOBAL
    a = 75 + A.param;
    pi = 314;
    m = {a for i2 in [0:10] where i2 + pi < 6 for i in [1:2] where i2 % i == 0};  // will use pi = 456
    pi = 456;

#NODE A
    #PARAMETERS
        param = T-1;
        subnodes = {P} + {P};  // TODO should be forbidden, and next line should still be allowed
        a7 = {1,2,3,4,5} + 1;  // apply +1 on all array elements
        z=4;
        a <- 1;
        a <- a + a[a].a;
        a <- a + 1;
        a <- a + 1;
        f(a) <- global.pi ** iDontExistAndItsFineBecauseFunctionIsRedefinedAfter;
        n(aa,b,cc) <- aa+b+cc;
        q = [3:6];
        v = [1:1];
        u in v;
        o = n(u, q, 2, i for i in [2:0]);
        
        dict = {f(param) * w - 3: P for w in [1:3:2], "je": B};
        f(b) <- global.pi ** b[b].x;
        hello = [0:2];
    #NODE P
        #PARAMETERS
            parentnodes = {A};
        #NODE BLABLA
            pass;
        #VARIABLES
            pass;
        #CONSTRAINTS
            named_constraint: global.pi == 2;

    #NODE P1 extends A.P
        #VARIABLES
            pass;
        #CONSTRAINTS
            deactivate named_constraint;

    #NODE P2 extends A.P
        #PARAMETERS
            parentnodes = {A, A};
            new_param = 12.35;
        #VARIABLES
            pass;
    
    #NODE import = import test[3] from "import_testing.gboml" with
        param = 9;
        var external;

    #NODE GEN;

    #NODE GEN[i][a_man] for i in [0:3] where i == 3 for a_man like u
        #PARAMETERS
            x = i * a_man;
        #VARIABLES
            pass;

    #NODE B
        #PARAMETERS
            param = 2;
        #NODE C[param] where param == 2
            #PARAMETERS
                param = 3;
            #NODE D
                #PARAMETERS
                    param = 4;
                #VARIABLES
                    external : x[T];
                #CONSTRAINTS
                    x[t] >= A.param where t % 365 == 0;

            #NODE E
                #PARAMETERS
                    param = 5.5 + C.A;  // TODO should be forbidden ?
                #VARIABLES
                    external integer : y[T];
                #CONSTRAINTS
                    y[t] >= param;
                #OBJECTIVES
                    min: y[t];

            #HYPEREDGE H
                #PARAMETERS
                    param = A.param + A.n(C.param for i in [1:3]) + A.n(0,1,2)[1];
                #CONSTRAINTS
                    E.y[t]+D.x[t] == param+9;

            #VARIABLES
                internal : x[T] <- D.x[T];
            #CONSTRAINTS
                x[t] <= B.param+A.param+param+B.A.param+parent.param+parent.parent.param where t % 2 == 1;
                SOS1(global.m);
        #VARIABLES
            internal integer : x[T] <- C.x[T];
            internal : baba <- A.param;
            internal binary : baba[T] in [:3];
    #VARIABLES
        internal : x[T] <- B.x[T];
    #OBJECTIVES
        min name : x[t-5] + sum(l for l in hello where l < 2) + sum(1,2) + len(hello) + f(global.pi) + subnodes[param].a.a + (param > 1).x + (B * 2).param + f(x).a;
        max name : x[t];

""")

for i in reversed(range(29)):
    if i == 25:
        continue  # no test25.txt
    print(f"------------------------------- {i} -------------------------------------")
# tree = parser.parse_file(f"../tests/instances/ok/test{i}.txt")
tree = resolve_imports(tree, Path('.'), parser)
tree, global_scope = semantic_check(tree)
print(tree)
