#!/usr/bin/env python3

from gboml.parsing import GBOMLParser
from gboml.redundant_definitions import remove_redundant_definitions
from gboml.resolve_imports import resolve_imports
from gboml.semantic import semantic_check
from gboml.scope import GlobalScope
from gboml.ast import BaseLoop, MultiLoop
from gboml.tools.tree_modifier import modify
import dataclasses
import os
from pathlib import Path

# TODO works really well, but then MultiLoop isn't useful anymore. Could remove at the AST creation ?
def _extend_multiloop(mloop: MultiLoop) -> BaseLoop:
    prevloop = mloop.sub[-1]
    for subloop in reversed(mloop.sub[:-1]):
        subloop = dataclasses.replace(subloop, loop=prevloop)
        prevloop = subloop
    return prevloop


# FunctionDefinition(name='f', args=['b'], value=ExpressionOp(operator=<Operator.exponent: '**'>, operands=[VarOrParam(path=[VarOrParamLeaf(name='global', indices=[]), VarOrParamLeaf(name='pi', indices=[])]), VarOrParam(path=[VarOrParamLeaf(name='b', indices=[VarOrParam(path=[VarOrParamLeaf(name='b', indices=[])])]), VarOrParamLeaf(name='x', indices=[])])]), tags=set()), ConstantDefinition(name='dict', value=Dictionary(content=[DictEntry(key=ExpressionOp(operator=<Operator.minus: '-'>, operands=[ExpressionOp(operator=<Operator.times: '*'>, operands=[Function(name='f', operands=[VarOrParam(path=[VarOrParamLeaf(name='param', indices=[])])]), VarOrParam(path=[VarOrParamLeaf(name='w', indices=[])])]), 3]), value=VarOrParam(path=[VarOrParamLeaf(name='P', indices=[])]), loop=BaseLoop(varid='w', on=Range(start=1, end=3, step=2), condition=None, loop=None)), DictEntry(key='je', value=VarOrParam(path=[VarOrParamLeaf(name='B', indices=[])]), loop=None)]), tags=set()), ConstantDefinition(name='hello', value=Range(start=0, end=2, step=None), tags=set())], nodes=[NodeDefinition(name='P', import_from=None, parameters=[], nodes=[], hyperedges=[], variables=[], constraints=[], objectives=[], activations=[], tags=set()), NodeGenerator(name='GEN', indices=['i', 'j'], loop=BaseLoop(varid='i', on=Range(start=0, end=3, step=None), condition=BoolExpressionComparison(lhs=VarOrParam(path=[VarOrParamLeaf(name='i', indices=[])]), operator=<Operator.equal: '=='>, rhs=3), loop=BaseLoop(varid='j', on=Range(start=3, end=6, step=None), condition=None, loop=None)), import_from=None, parameters=[ConstantDefinition(name='x', value=ExpressionOp(operator=<Operator.times: '*'>, operands=[VarOrParam(path=[VarOrParamLeaf(name='i', indices=[])]), VarOrParam(path=[VarOrParamLeaf(name='j', indices=[])])]), tags=set())], nodes=[], hyperedges=[], variables=[], constraints=[], objectives=[], activations=[], tags=set()), NodeDefinition(name='B', import_from=None, parameters=[ConstantDefinition(name='param', value=2, tags=set())], nodes=[NodeDefinition(name='C', import_from=None, parameters=[ConstantDefinition(name='param', value=3, tags=set())], nodes=[NodeDefinition(name='D', import_from=None, parameters=[ConstantDefinition(name='param', value=4, tags=set())], nodes=[], hyperedges=[], variables=[VariableDefinition(name='x', indices=[VarOrParam(path=[VarOrParamLeaf(name='T', indices=[])])], scope=<VarScope.external: 'external'>, type=<VarType.continuous: 'continuous'>, bound_lower=None, bound_upper=None, import_from=None, tags=set())], constraints=[StdConstraint(name=None, lhs=VarOrParam(path=[VarOrParamLeaf(name='x', indices=[VarOrParam(path=[VarOrParamLeaf(name='t', indices=[])])])]), op=<Operator.greater_or_equal: '>='>, rhs=VarOrParam(path=[VarOrParamLeaf(name='A', indices=[]), VarOrParamLeaf(name='param', indices=[])]), loop=None, tags=set())], objectives=[], activations=[], tags=set()), NodeDefinition(name='E', import_from=None, parameters=[ConstantDefinition(name='param', value=5.5, tags=set())], nodes=[], hyperedges=[], variables=[VariableDefinition(name='y', indices=[VarOrParam(path=[VarOrParamLeaf(name='T', indices=[])])], scope=<VarScope.external: 'external'>, type=<VarType.integer: 'integer'>, bound_lower=None, bound_upper=None, import_from

tree = GBOMLParser().parse("""
#TIMEHORIZON T = 2*2;
#GLOBAL
    a = 75;
    pi = 314;
    m = {a for i2 in [0:10] where i2 + a < 6 for i in [1:2] where i2 % i == 0};
    pi = 456;

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
        
        dict = {f(param) * w - 3: P for w in [1:3:2], "je": B};
        f(b) <- global.pi ** b[b].x;
        hello = [0:2];
    #NODE P
        pass;

    #NODE GEN[i][j] for i in [0:3] where i == 3 for j in [3:6]
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
                x[t] <= B.param+A.param+param;
        #VARIABLES
            internal : x[T] <- C.x[T];
            internal : baba;
    #VARIABLES
        internal : x[T] <- B.x[T];
    #OBJECTIVES
        min : x[t-5] + sum(l for l in hello where l < 2) + len(hello) + f(global.pi) + subnodes[param];

""")

for i in reversed(range(29)):
    if i == 25:
        continue  # no test25.txt
    print(f"------------------------------- {i} -------------------------------------")
# parser = GBOMLParser()
# tree = parser.parse_file(f"../tests/instances/ok/test{i}.txt")
# tree = resolve_imports(tree, Path('../tests/instances/ok/'), parser)
tree = remove_redundant_definitions(tree)
tree = modify(tree, {MultiLoop: _extend_multiloop})
print(tree)

# print(tree.meta)
# print(tree.global_defs[0].meta)
globalScope = GlobalScope(tree)
semantic_check(globalScope)
# parse_file("test/test1.txt")
