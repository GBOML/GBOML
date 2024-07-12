from gboml.ast import *
from gboml.scope import *
from gboml.tools.tree_modifier import visit, visit_hier

def _get_scope_from_hier(hier: list[NodeDefinition|NodeGenerator|HyperEdgeDefinition|HyperEdgeGenerator|StdConstraint|FunctionConstraint|Objective|DictEntry|GeneratedExpression|VariableDefinition|FunctionDefinition|ExpressionOp|Loop|Path]) -> Scope:
    return next(hierItem.scope for hierItem in reversed(hier) if isinstance(hierItem, (*GeneratedObjects, NodeDefinition, HyperEdgeDefinition, FunctionDefinition)))

def _check_nodeGen_index(element: NodeGenerator, hier: list[NodeDefinition|NodeGenerator|HyperEdgeDefinition|HyperEdgeGenerator|StdConstraint|FunctionConstraint|Objective|DictEntry|GeneratedExpression|VariableDefinition|FunctionDefinition|ExpressionOp|Loop|Path] = []) -> None:
    scope = _get_scope_from_hier(hier)
    for index in element.indices:
        try:
            scope[index]
        except KeyError:
            raise KeyError(f"SEMANTIC ERROR: {index} (from {element.name}) can not be used in this scope {element.meta}!")

def _check_fct_in_scope(element: ExpressionFunctionCall, hier: list[NodeDefinition|NodeGenerator|HyperEdgeDefinition|HyperEdgeGenerator|StdConstraint|FunctionConstraint|Objective|DictEntry|GeneratedExpression|VariableDefinition|FunctionDefinition|ExpressionOp|Loop|Path] = []) -> None:
    scope = _get_scope_from_hier(hier)
    try:
        scope = scope[element.name]
        declaredArgsLen = len(scope.ast.args)
    except KeyError:
        if element.name not in ('sum', 'len'):
            raise KeyError(f"SEMANTIC ERROR: function {element.name} can not be used in this scope {element.meta}!")
        else:
            declaredArgsLen = 1

    if len(element.operands) != declaredArgsLen:
        raise KeyError(f"SEMANTIC ERROR: {element.name}(): expected {declaredArgsLen} arguments but got {len(element.operands)} at {element.meta}!")


def _check_var_in_scope(element: ExpressionDotCall | ExpressionFunctionCall | PathRoot, hier: list[NodeDefinition|NodeGenerator|HyperEdgeDefinition|HyperEdgeGenerator|StdConstraint|FunctionConstraint|Objective|DictEntry|GeneratedExpression|VariableDefinition|FunctionDefinition|ExpressionOp|Loop|Path] = [], scope: Scope = None) -> None:
    # dotcalls are handled by the parent
    parentExprCall = next((hierItem for hierItem in reversed(hier[:-1]) if isinstance(hierItem, ExpressionArrayCall | ExpressionDotCall)), None)
    if isinstance(parentExprCall, ExpressionDotCall):
        return
    if scope is None:
        scope = _get_scope_from_hier(hier)

    if not isinstance(leftElement := element if isinstance(element, PathRoot) else element.lhs, PathRoot):
        return

    scopeAfterDot = scope[leftElement.name]
    if isinstance(element, ExpressionDotCall):
        scopeAfterDot[element.rhs]




def passyay():
    # if the nearest parent in the AST is a Function, note that its argument can be an array - aka without indices  # TODO
    # checkForArrayDeclarationUse = not isinstance(next((hierItem for hierItem in reversed(hier) if isinstance(hierItem, Function | ExpressionOp)), None), Function)
    for leaf in element.path[:2]:
        try:
            scope = scope[leaf.name]
            isDeclaredAsArray = isinstance(scope, ScopedVariableDefinition) and bool(scope.ast.indices) or isinstance(scope, ScopedDefinition) and isinstance(scope.ast.value, Array | Range)
        except KeyError:
            # if TIMEHORIZON is set, 'T' and 't' are allowed
            if not isinstance(scope, EmptyScope) and (leaf.name == 't' or leaf.name == 'T') and origScope['global'].parent.ast.time_horizon is not None:
                isDeclaredAsArray = False  # indices are not allowed
                scope = EmptyScope()  # a following leaf in element.path is not allowed (next leaf.name will raise KeyError)
            else:
                raise KeyError(f"SEMANTIC ERROR: {leaf.name} (from {list(map(lambda e: e.name, element.path))}) can not be used in this scope {leaf.meta}!")

        if isinstance(origScope, HasLoopInScope | ScopedFunctionDefinition) and isinstance(scope, EmptyScope):
            break
        isBeingIteratedOn = leaf is element.path[-1] and isinstance(origScope.ast, Loop) and element is origScope.ast.on
        isUsedAsArray = bool(leaf.indices) or isBeingIteratedOn
        if checkForArrayDeclarationUse and isUsedAsArray != isDeclaredAsArray:
            raise KeyError(f"SEMANTIC ERROR: {leaf.name} (from {list(map(lambda e: e.name, element.path))}): mixing declaration type and use type (array Vs. scalar) {leaf.meta}!")
        if isDeclaredAsArray:
            break

    # visit all Path indices at once
    visit(element, {ExpressionArrayCall: lambda var: None if var is element else _check_var_in_scope(var, scope = origScope)})

def semantic_check(globalScope: GlobalScope):
    # check if variables are in scope
    visit_hier(globalScope.ast, {NodeDefinition,NodeGenerator,HyperEdgeDefinition,HyperEdgeGenerator,StdConstraint,FunctionConstraint,Objective,DictEntry,GeneratedExpression,VariableDefinition,FunctionDefinition,ExpressionOp,Loop,*Path.__args__}, {ExpressionDotCall: _check_var_in_scope, PathRoot: _check_var_in_scope, ExpressionFunctionCall: _check_var_in_scope})


# TODO likeloop
# TODO reverse AST during parsing for loops and element that contains these loops


# TODO
# scope checking; then Directed Acyclic Graph for deps of variables; then topological sort; then know which one of the nodes of the DAG does not do anything with iterable and mark their types


# function decorator ↓ (or separate additionnal argument to all functions)
# TODO define function to raise error; TODO do not stop at first error
# what about attaching error to a new scope.variable? if that var already has an error, don't add another one; at the end simply visit() and raise all errors
