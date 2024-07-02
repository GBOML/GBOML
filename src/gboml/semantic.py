from gboml.ast import *
from gboml.scope import *
from gboml.tools.tree_modifier import visit, visit_hier

# TODO define function to raise error; TODO do not stop at first error
# what about attaching error to a new scope.variable? if that var already has an error, don't add another one; at the end simply visit() and raise all errors

def _check_fct_in_scope(element: Function, hier: list[NodeDefinition|NodeGenerator|HyperEdgeDefinition|HyperEdgeGenerator|StdConstraint|SOSConstraint|Objective|DictEntry|GeneratedRValue|VariableDefinition|FunctionDefinition|VarOrParam] = []) -> None:
    scope = next(hierItem.scope for hierItem in reversed(hier) if isinstance(hierItem, NodeDefinition))
    try:
        scope = scope[element.name]
        declaredArgsLen = len(scope.ast.args)
    except KeyError:
        raise KeyError(f"SEMANTIC ERROR: function {element.name} can not be used in this scope {element.meta}!")

    if len(element.operands) != declaredArgsLen:
        raise KeyError(f"SEMANTIC ERROR: {element.name}(): expected {declaredArgsLen} arguments but got {len(element.operands)} at {element.meta}!")


def _check_var_in_scope(element: VarOrParam, hier: list[NodeDefinition|NodeGenerator|HyperEdgeDefinition|HyperEdgeGenerator|StdConstraint|SOSConstraint|Objective|DictEntry|GeneratedRValue|VariableDefinition|FunctionDefinition|VarOrParam] = [], scope: Scope = None) -> None:
    # if there is any parent VarOrParam in hier, return (sub-VarOrParam are handled from the parent)
    if any(isinstance(hierItem, VariableDefinition | VarOrParam) for hierItem in reversed(hier[:-1])):
        return
    # print(element, list(map(lambda _: (type(_), isinstance(_, NodeDefinition | FunctionDefinition)), hier)))
    if scope is None:  # get the scope of the last node/fct in hier
        scope = next(hierItem.scope for hierItem in reversed(hier) if isinstance(hierItem, NodeDefinition | FunctionDefinition))
    parentScope = scope
    for leaf in element.path[:2]:
        # print(leaf.name, type(scope), scope.content.keys())
        try:
            scope = scope[leaf.name]
            isDeclaredAsArray = isinstance(scope, ScopedVariableDefinition) and bool(scope.ast.indices)
        except KeyError:
            # if TIMEHORIZON is set, 'T' and 't' are allowed
            if scope and (leaf.name == 't' or leaf.name == 'T') and parentScope['global'].parent.ast.time_horizon is not None:
                isDeclaredAsArray = False  # indices are not allowed
                scope = {}  # a following leaf in element.path is not allowed (next leaf.name will raise KeyError)
            else:
                raise KeyError(f"SEMANTIC ERROR: {leaf.name} (from {list(map(lambda e: e.name, element.path))}) can not be used in this scope {leaf.meta}!")

        isUsedAsArray = bool(leaf.indices)
        if isUsedAsArray != isDeclaredAsArray:
            raise KeyError(f"SEMANTIC ERROR: {leaf.name} (from {list(map(lambda e: e.name, element.path))}): mixing declaration type and use type (array Vs. scalar) {leaf.meta}!")

    # visit all VarOrParam indices at once
    visit(element, {VarOrParam: lambda var: None if var is element else _check_var_in_scope(var, scope = parentScope)})

def semantic_check(globalScope: GlobalScope):
    pass
    # check if variables are in scope
    visit_hier(globalScope.ast, {NodeDefinition,NodeGenerator,HyperEdgeDefinition,HyperEdgeGenerator,StdConstraint,SOSConstraint,Objective,DictEntry,GeneratedRValue,VariableDefinition,FunctionDefinition,VarOrParam}, {VarOrParam: _check_var_in_scope, Function: _check_fct_in_scope})

# TODO add expressions to a "dict"

# TODO check if isDeclaredAsArray is correct for non-x[T] definition
# TODO check for scope in for i ....

# TODO check with a different function for VariableDefinition
