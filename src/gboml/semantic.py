from gboml.ast import *
from gboml.scope import *
from gboml.tools.tree_modifier import visit

def _check_var_existence(element: VarOrParam, defNodeScope: DefNodeScope) -> None:
    print()
    for subElement in element.path:
        print(f"SubElement {subElement.name}")
        # if subElement.name == defNodeScope.name:
            # continue
        if subElement.name not in defNodeScope.content and (isinstance(defNodeScope, GlobalScope) or subElement.name not in defNodeScope.content['root'].content): #rootScope.content:
            print(f"SEMANTIC ERROR: {subElement.name} (from {list(map(lambda e: e.name, element.path))}) not declared in this scope {subElement.meta}!")
            print(f"Keys allowed in this scope are {defNodeScope.content.keys()}; this node name is {defNodeScope.name}")
            print(f"Nodes keys {defNodeScope.nodes.keys()} and this node path is {defNodeScope.path}")
            print(f"is it in .nodes.content ? {subElement.name in list(defNodeScope.nodes.values())[0].content}")
            return
        else:
            # print(f"semantic ok: {subElement.name} declared in scope {subElement.meta}")
            defNodeScope = defNodeScope.content['root'].content[subElement.name] if (not isinstance(defNodeScope, GlobalScope) and subElement.name in defNodeScope.content['root'].content) else defNodeScope.content[subElement.name]

def _visit_nodes(nodeDef: NodeDefinition) -> None:
    visit(nodeDef, {VarOrParam: lambda var: _check_var_existence(var, nodeDef.scope)})

def semantic_check(rootScope: RootScope):
    visit(rootScope.ast, {NodeDefinition: _visit_nodes})
