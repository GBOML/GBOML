from gboml.ast import *
from gboml.scope import *
from gboml.tools.tree_modifier import visit, visit_hier

from graphlib import TopologicalSorter, CycleError

TYPES = NodeDefinition|HyperEdgeDefinition|StdConstraint|FunctionConstraint|Objective|DictEntry|GeneratedExpression|Definition|VariableDefinition|ExpressionOp|Loop|Path

def _get_scope_from_hier(hier: list[TYPES]) -> Scope:
    return next(hierItem.scope for hierItem in reversed(hier) if hasattr(hierItem, 'scope'))
def _get_parent_definition(hier: list[TYPES]) -> Definition | VariableDefinition | None:
    return next((hierItem for hierItem in reversed(hier) if isinstance(hierItem, Definition | VariableDefinition)), None)
def _add_dep(definition: Definition | VariableDefinition, dep: DefinitionScope) -> None:
    if hasattr(definition, 'deps'):
        definition.deps.add(dep)
    else:
        definition.deps = {dep}

# def _check_nodeGen_index(element: NodeGenerator, hier: list[TYPES] = []) -> None:  # TODO
    # scope = _get_scope_from_hier(hier)
    # for index in element.indices:
        # try:
            # scope[index]
        # except KeyError:
            # raise KeyError(f"SEMANTIC ERROR: {index} (from {element.name}) can not be used in this scope {element.meta}!")

def _check_fct_in_scope(element: ExpressionFunctionCall, hier: list[TYPES] = []) -> None:
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


def _check_var_in_scope(element: ExpressionDotCall | ExpressionFunctionCall | PathRoot, hier: list[TYPES] = [], scope: Scope = None) -> None:
    """ Checks if element is accessible in the current scope (if not, an error is raised), and adds element to its Definition|VariableDefinition parent's dependencies """
    parentExprCall = next((hierItem for hierItem in reversed(hier[:-1]) if isinstance(hierItem, ExpressionArrayCall | ExpressionDotCall)), None)
    if isinstance(parentExprCall, ExpressionDotCall):
        return  # dotcalls are handled by the parent
    if not isinstance(leftElement := element if isinstance(element, PathRoot) else element.lhs, PathRoot):
        return

    if scope is None:
        scope = _get_scope_from_hier(hier)

    scopeAfterDot = scope[leftElement.name]
    if isinstance(element, ExpressionDotCall):
        scopeAfterDot = scopeAfterDot[element.rhs]
    
    if scopeAfterDot and isinstance(parent_def := _get_parent_definition(hier), Definition | VariableDefinition):
        _add_dep(parent_def, scopeAfterDot)
    




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

        if isinstance(origScope, LoopScope | ScopedFunctionDefinition) and isinstance(scope, EmptyScope):
            break
        isBeingIteratedOn = leaf is element.path[-1] and isinstance(origScope.ast, Loop) and element is origScope.ast.on
        isUsedAsArray = bool(leaf.indices) or isBeingIteratedOn
        if checkForArrayDeclarationUse and isUsedAsArray != isDeclaredAsArray:
            raise KeyError(f"SEMANTIC ERROR: {leaf.name} (from {list(map(lambda e: e.name, element.path))}): mixing declaration type and use type (array Vs. scalar) {leaf.meta}!")
        if isDeclaredAsArray:
            break

    # visit all Path indices at once
    visit(element, {ExpressionArrayCall: lambda var: None if var is element else _check_var_in_scope(var, scope = origScope)})


def _topo_sort(globalScope: GlobalScope) -> list[DefinitionScope]:
    """ Performs the topological sort for Definition|VariableDefinition elements (if there's a circular dependency, an error is raised), and return the sorted elements in a map """
    ts = TopologicalSorter()
    add_node = lambda definition: ts.add(definition.scope, *getattr(definition, 'deps', {}))
    visit(globalScope.ast, {Definition: add_node, VariableDefinition: add_node})
    try:
        return list(ts.static_order())
    except CycleError as err:  # default error too long to print
        raise RuntimeError("Circular dependency found!", list(map(lambda dep: (dep.path_to_str(), dep.ast.meta), err.args[1]))) from None


def semantic_check(globalScope: GlobalScope):
    # check if variables are in scope, and store deps
    visit_hier(globalScope.ast, {*TYPES.__args__, *Path.__args__, ExpressionFunctionCall}, dict.fromkeys((ExpressionDotCall, PathRoot, ExpressionFunctionCall), _check_var_in_scope))
    
    _topo_sort(globalScope)    
    


# TODO likeloop
# TODO see what is ScopeChange (used in redundant_def)


# TODO
# know which one of the nodes of the DAG does not do anything with iterable and mark their types

# TODO
# don't allow redefining T nor t. If TIMEHORIZON is None => make it 1
# all T = TIMEHORIZON
# all t = implicit loop

# TODO during scope checking, add ImplicitLoops for Paths referencing a IndexingParameterDefinition

# TODO in parsing, use dataclass.replace

# function decorator ↓ (or separate additionnal argument to all functions)
# TODO define function to raise error; TODO do not stop at first error
# what about attaching error to a new scope.variable? if that var already has an error, don't add another one; at the end simply visit() and raise all errors
