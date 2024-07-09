from gboml.ast import *
from gboml.scope import *
from gboml.tools.tree_modifier import visit, visit_hier

def _get_scope_from_hier(hier: list[NodeDefinition|NodeGenerator|HyperEdgeDefinition|HyperEdgeGenerator|StdConstraint|SOSConstraint|Objective|DictEntry|GeneratedRValue|VariableDefinition|FunctionDefinition|GeneratedRValue|Loop|VarOrParam]) -> Scope:
    return next(hierItem.scope for hierItem in reversed(hier) if isinstance(hierItem, (*HasLoopInScope.astTypes, NodeDefinition, HyperEdgeDefinition, FunctionDefinition)))

def _check_nodeGen_index(element: NodeGenerator, hier: list[NodeDefinition|NodeGenerator|HyperEdgeDefinition|HyperEdgeGenerator|StdConstraint|SOSConstraint|Objective|DictEntry|GeneratedRValue|VariableDefinition|FunctionDefinition|GeneratedRValue|Loop|VarOrParam] = []) -> None:
    scope = _get_scope_from_hier(hier)
    for index in element.indices:
        try:
            scope[index]
        except KeyError:
            raise KeyError(f"SEMANTIC ERROR: {index} (from {element.name}) can not be used in this scope {element.meta}!")

def _check_fct_in_scope(element: Function, hier: list[NodeDefinition|NodeGenerator|HyperEdgeDefinition|HyperEdgeGenerator|StdConstraint|SOSConstraint|Objective|DictEntry|GeneratedRValue|VariableDefinition|FunctionDefinition|GeneratedRValue|Loop|VarOrParam] = []) -> None:
    scope = _get_scope_from_hier(hier)
    try:
        scope = scope[element.name]
        declaredArgsLen = len(scope.ast.args)
    except KeyError:
        if element.name != 'sum':
            raise KeyError(f"SEMANTIC ERROR: function {element.name} can not be used in this scope {element.meta}!")
        else:
            declaredArgsLen = 1

    if len(element.operands) != declaredArgsLen:
        raise KeyError(f"SEMANTIC ERROR: {element.name}(): expected {declaredArgsLen} arguments but got {len(element.operands)} at {element.meta}!")


def _check_var_in_scope(element: VarOrParam, hier: list[NodeDefinition|NodeGenerator|HyperEdgeDefinition|HyperEdgeGenerator|StdConstraint|SOSConstraint|Objective|DictEntry|GeneratedRValue|VariableDefinition|FunctionDefinition|Loop|VarOrParam] = [], scope: Scope = None) -> None:
    # if there is any parent VarOrParam in hier, return (sub-VarOrParam are handled from the parent)
    if any(isinstance(hierItem, VariableDefinition | VarOrParam) for hierItem in reversed(hier[:-1])):
        return
    if scope is None:  # get the scope of the last node/fct/genrval in hier
        scope = _get_scope_from_hier(hier)
    origScope = scope
    for leaf in element.path[:2]:
        try:
            scope = scope[leaf.name]
            isDeclaredAsArray = isinstance(scope, ScopedVariableDefinition) and bool(scope.ast.indices) or isinstance(scope, ScopedDefinition) and isinstance(scope.ast.value, Array | Range)
        except KeyError:
            # if TIMEHORIZON is set, 'T' and 't' are allowed
            if scope and (leaf.name == 't' or leaf.name == 'T') and origScope['global'].parent.ast.time_horizon is not None:
                isDeclaredAsArray = False  # indices are not allowed
                scope = EmptyScope()  # a following leaf in element.path is not allowed (next leaf.name will raise KeyError)
            else:
                raise KeyError(f"SEMANTIC ERROR: {leaf.name} (from {list(map(lambda e: e.name, element.path))}) can not be used in this scope {leaf.meta}!")

        if isinstance(origScope, HasLoopInScope | ScopedFunctionDefinition) and isinstance(scope, EmptyScope):
            break
        isBeingIteratedOn = leaf is element.path[-1] and isinstance(origScope.ast, Loop) and element is origScope.ast.on
        isUsedAsArray = bool(leaf.indices) or isBeingIteratedOn
        if isUsedAsArray != isDeclaredAsArray:
            raise KeyError(f"SEMANTIC ERROR: {leaf.name} (from {list(map(lambda e: e.name, element.path))}): mixing declaration type and use type (array Vs. scalar) {leaf.meta}!")
        if isDeclaredAsArray:
            break

    # visit all VarOrParam indices at once
    visit(element, {VarOrParam: lambda var: None if var is element else _check_var_in_scope(var, scope = origScope)})

def semantic_check(globalScope: GlobalScope):
    # check if variables are in scope
    visit_hier(globalScope.ast, {NodeDefinition,NodeGenerator,HyperEdgeDefinition,HyperEdgeGenerator,StdConstraint,SOSConstraint,Objective,DictEntry,GeneratedRValue,VariableDefinition,FunctionDefinition,Loop,VarOrParam}, {VarOrParam: _check_var_in_scope, Function: _check_fct_in_scope, NodeGenerator: _check_nodeGen_index})


# TODO SOSConstraints
# TODO Len
# TODO likeloop
# TODO reverse AST during parsing for loops and element that contains these loops


# function decorator ↓ (or separate additionnal argument to all functions)
# TODO define function to raise error; TODO do not stop at first error
# what about attaching error to a new scope.variable? if that var already has an error, don't add another one; at the end simply visit() and raise all errors
