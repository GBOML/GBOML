from gboml.ast import *
from gboml.scope import *
from gboml.tools.tree_modifier import visit

def _scope_error(path: list[VarOrParamLeaf], path_item: VarOrParamLeaf):
    raise KeyError(f"SEMANTIC ERROR: {path_item.name} (from {list(map(lambda e: e.name, path))}) not declared in this scope {path_item.meta}!")

def _check_var_in_scope(element: VarOrParam, hier: set[NodeDefinition|NodeGenerator|HyperEdgeDefinition|HyperEdgeGenerator|StdConstraint|SOSConstraint|Objective|DictEntry|GeneratedRValue]) -> None:
    scope = next(hierItem.scope for hierItem in reversed(hier) if isinstance(hierItem, NodeDefinition))
    # print(type(element.path),type(element.path[0]))
    for subElement in element.path:
        try:
            scope = scope[subElement.name]
        except KeyError:
            _scope_error(element.path, subElement)

def semantic_check(globalScope: GlobalScope):
    visit_hier(globalScope.ast, {NodeDefinition,NodeGenerator,HyperEdgeDefinition,HyperEdgeGenerator,StdConstraint,SOSConstraint,Objective,DictEntry,GeneratedRValue}, {VarOrParam: _check_var_in_scope})
