from gboml.ast import *
from gboml.scope import *
from gboml.tools.tree_modifier import visit, visit_hier

def _check_var_in_scope(element: VarOrParam, hier: list[NodeDefinition|NodeGenerator|HyperEdgeDefinition|HyperEdgeGenerator|StdConstraint|SOSConstraint|Objective|DictEntry|GeneratedRValue|VariableDefinition|VarOrParam] = [], scope: Scope = None) -> None:
    # if there is any parent VarOrParam in hier, return (sub-VarOrParam are handled at the same time as the parent)
    if any(isinstance(hierItem, VariableDefinition | VarOrParam) for hierItem in reversed(hier[:-1])):
        return
    # print(element, list(map(type, hier)))
    if scope is None:  # get the scope of the last node in hier
        scope = next(hierItem.scope for hierItem in reversed(hier) if isinstance(hierItem, NodeDefinition))
    parentScope = scope
    for leaf in element.path:
        try:
            scope = scope[leaf.name]
        except KeyError:
            # if hier is [] => we are currently looking at a sub-VarOrParam (= in an index) => if TIMEHORIZON is set, 't' is allowed (remember, we aren't in VariableDefinition so no 'T')
            if not hier and scope['global'].parent.ast.time_horizon is not None and leaf.name == 't':
                # TODO only return if no left element.path and no leaf.indices
                return
            else:
                raise KeyError(f"SEMANTIC ERROR: {leaf.name} (from {list(map(lambda e: e.name, element.path))}) not declared in this scope {leaf.meta}!")

        isUsedAsArray = bool(leaf.indices)
        isDeclaredAsArray = isinstance(scope, ScopedVariableDefinition) and bool(scope.ast.indices)
        if isUsedAsArray != isDeclaredAsArray:
            raise KeyError(f"SEMANTIC ERROR: {leaf.name} (from {list(map(lambda e: e.name, element.path))}): mixing declaration type and use type (array Vs. scalar) {leaf.meta}!")
        elif isUsedAsArray:
            visit(element, {VarOrParam: lambda var: None if var is element else _check_var_in_scope(var, scope = parentScope)})

def semantic_check(globalScope: GlobalScope):
    visit_hier(globalScope.ast, {NodeDefinition,NodeGenerator,HyperEdgeDefinition,HyperEdgeGenerator,StdConstraint,SOSConstraint,Objective,DictEntry,GeneratedRValue,VariableDefinition,VarOrParam}, {VarOrParam: _check_var_in_scope})

# TODO if no TIMEHORIZON, we can use T as name of variable
# TODO add expressions to a "dict"

# TODO check with a different function for VariableDefinition
