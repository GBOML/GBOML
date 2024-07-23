from gboml.ast import *
from gboml.scope import *
from gboml.tools.tree_modifier import visit, visit_hier

from graphlib import TopologicalSorter, CycleError

TYPES = NodeDefinition|HyperEdgeDefinition|StdConstraint|FunctionConstraint|Objective|DictEntry|GeneratedExpression|VarOrParamDefinition|ExpressionOp|Loop|Path

def _get_scope_from_hier(hier: list[TYPES]) -> Scope:
    return next(hierItem.scope for hierItem in reversed(hier) if hasattr(hierItem, 'scope'))
def _get_parent_varorparam_def(hier: list[TYPES]) -> VarOrParamDefinition | None:
    return next((hierItem for hierItem in reversed(hier) if isinstance(hierItem, VarOrParamDefinition)), None)
def _add_dep(varorparam_def: VarOrParamDefinition, dep: VarOrParamDefScope) -> None:
    if hasattr(varorparam_def, 'deps'):
        varorparam_def.deps.add(dep)
    else:
        varorparam_def.deps = {dep}


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


def _check_var_or_param_scoping(elem: ExpressionDotCall | ExpressionFunctionCall | PathRoot, hier: list[TYPES]) -> None:
    """ Checks if elem is accessible in the current scope (if not, an error is raised), and adds elem to its VarOrParamDefinition parent's dependencies, and add implicit loops if needed """
    parent_expr_call = next((hierItem for hierItem in reversed(hier[:-1]) if isinstance(hierItem, ExpressionArrayCall | ExpressionDotCall | ExpressionFunctionCall)), None)
    if isinstance(parent_expr_call, ExpressionDotCall):
        return  # dotcalls are handled by the parent
    if not isinstance(left_elem := elem if isinstance(elem, PathRoot) else elem.lhs, PathRoot):
        return

    scope = _get_scope_from_hier(hier)
    scope_after_dot = scope[left_elem.name]
    if isinstance(elem, ExpressionDotCall):
        scope_after_dot = scope_after_dot[elem.rhs]

    # check function use/declaration; function to check is elem (or its direct parent if elem is not a function call and elem == parent's lhs)
    fct_call = parent_expr_call if not isinstance(elem, ExpressionFunctionCall) and isinstance(hier[-2], ExpressionFunctionCall) and hier[-2].lhs is elem else elem
    if scope_after_dot and isinstance(scope_after_dot, ScopedFunctionDefinition) != isinstance(fct_call, ExpressionFunctionCall):
        raise RuntimeError(f"{list(map(type, hier))}{fct_call} {fct_call.meta}: used as {'function' if isinstance(fct_call, ExpressionFunctionCall) else 'non-fonction'} "
                            f"but declared as {'function' if isinstance(scope_after_dot, ScopedFunctionDefinition) else 'non-fonction'} {type(scope_after_dot)} {scope_after_dot.ast.meta}!")

    if scope_after_dot and isinstance(parent_def := _get_parent_varorparam_def(hier), VarOrParamDefinition):
        _add_dep(parent_def, scope_after_dot)


def _check_node_or_hyperedge_index(element: NodeDefinition | HyperEdgeDefinition, hier: list[TYPES]) -> None:
    if not element.indices:
        return
    scope = _get_scope_from_hier(hier)
    for index in element.indices:
        try:
            scope[index]
        except KeyError:
            raise KeyError(f"SEMANTIC ERROR: {index} (from {element.name}) can not be used in this scope {element.meta}!")


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
    visit(element, {ExpressionArrayCall: lambda var: None if var is element else _check_var_or_param_scoping(var, scope = origScope)})


def _topo_sort(globalScope: GlobalScope) -> list[VarOrParamDefScope]:
    """ Performs the topological sort for VarOrParamDefinition elements (if there's a circular dependency, an error is raised), and return the sorted elements in a map """
    ts = TopologicalSorter()
    add_node = lambda definition: ts.add(definition.scope, *getattr(definition, 'deps', {}))
    visit(globalScope.ast, {Definition: add_node, VariableDefinition: add_node})
    try:
        return list(ts.static_order())
    except CycleError as err:  # default error too long to print
        raise RuntimeError("Circular dependency found!", list(map(lambda dep: (dep.path_to_str(), dep.ast.meta), err.args[1]))) from None


def semantic_check(globalScope: GlobalScope):
    # check if variables are in scope, and store deps, and add implicit loops
    visit_hier(globalScope.ast, {*TYPES.__args__, *Path.__args__, ExpressionFunctionCall}, dict.fromkeys((ExpressionDotCall, PathRoot, ExpressionFunctionCall), _check_var_or_param_scoping) | dict.fromkeys((NodeDefinition, HyperEdgeDefinition), _check_node_or_hyperedge_index))
    
    _topo_sort(globalScope)


# TODO
# know which one of the nodes of the DAG does not do anything with iterable and mark their types

# TODO during scope checking, add ImplicitLoops for Paths referencing a IndexingParameterDefinition

# function decorator ↓ (or separate additionnal argument to all functions)
# TODO define function to raise error; TODO do not stop at first error
# what about attaching error to a new scope.variable? if that var already has an error, don't add another one; at the end simply visit() and raise all errors
