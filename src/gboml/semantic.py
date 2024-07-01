from gboml.ast import *
from gboml.scope import *
from gboml.tools.tree_modifier import visit, visit_hier

def _check_var_in_scope(element: VarOrParam, hier: list[NodeDefinition|NodeGenerator|HyperEdgeDefinition|HyperEdgeGenerator|StdConstraint|SOSConstraint|Objective|DictEntry|GeneratedRValue|VariableDefinition|FunctionDefinition|VarOrParam] = [], scope: Scope = None) -> None:
    # if there is any parent VarOrParam in hier, return (sub-VarOrParam are handled at the same time as the parent)
    if any(isinstance(hierItem, VariableDefinition | VarOrParam) for hierItem in reversed(hier[:-1])):
        return
    print(element, list(map(lambda _: (type(_), isinstance(_, NodeDefinition | FunctionDefinition)), hier)))
    if scope is None:  # get the scope of the last node in hier
        scope = next(hierItem.scope for hierItem in reversed(hier) if isinstance(hierItem, NodeDefinition | FunctionDefinition))
    parentScope = scope
    for leaf in element.path:
        # TODO from the 2nd iteration, check that previous leaf was a list of nodes
        print(type(scope), scope.parent.content.keys())
        try:
            scope = scope[leaf.name]
            isDeclaredAsArray = isinstance(scope, ScopedVariableDefinition) and bool(scope.ast.indices)
        except KeyError as err:
            # if TIMEHORIZON is set, 'T' and 't' are allowed
            if scope and scope['global'].parent.ast.time_horizon is not None and (leaf.name == 't' or leaf.name == 'T'):
                isDeclaredAsArray = False  # indices are not allowed
                scope = {}  # a following leaf in element.path is not allowed (next leaf.name will raise KeyError)
            else:
                raise KeyError(f"SEMANTIC ERROR: {leaf.name} (from {list(map(lambda e: e.name, element.path))}) can not be used in this scope {leaf.meta}!")

        isUsedAsArray = bool(leaf.indices)
        if isUsedAsArray != isDeclaredAsArray:
            raise KeyError(f"SEMANTIC ERROR: {leaf.name} (from {list(map(lambda e: e.name, element.path))}): mixing declaration type and use type (array Vs. scalar) {leaf.meta}!")
        elif isUsedAsArray:  # check scope of all sub-VarOrParam
            visit(element, {VarOrParam: lambda var: None if var is element else _check_var_in_scope(var, scope = parentScope)})

def semantic_check(globalScope: GlobalScope):
    # check variables shadowing TODO (parts already done in scope.py._add_to_scope(), but not T/t)
    pass
    # check if variables are in scope
    visit_hier(globalScope.ast, {NodeDefinition,NodeGenerator,HyperEdgeDefinition,HyperEdgeGenerator,StdConstraint,SOSConstraint,Objective,DictEntry,GeneratedRValue,VariableDefinition,FunctionDefinition,VarOrParam}, {VarOrParam: _check_var_in_scope})

# TODO if no TIMEHORIZON, we can use T as name of variable
# TODO add expressions to a "dict"

# TODO check for scope in FunctionDefinition (args of fct are done, but check for the overall fct usage - if it is detected correctly)
# TODO check for scope in for i ....

# TODO check with a different function for VariableDefinition
