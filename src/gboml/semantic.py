from gboml.ast import *
from gboml.scope import *
from gboml.tools.tree_modifier import visit

# NodeDefinition(name='H', import_from=None, parameters=[], nodes=[], hyperedges=[], variables=[VariableDefinition(name='x', indices=[], scope=ScopedVariableDefinition(name='x', path=['H', 'x'], content={'x': ..., 'y': ScopedVariableDefinition(name='y', path=['H', 'y'], content={...}, ast=VariableDefinition(name='y', indices=[], scope=..., type=<VarType.continuous: 'continuous'>, bound_lower=None, bound_upper=None, import_from=None, tags=set())), 'root': ParentNodeScope(name='root', path=[], content={'global': GlobalScope(name='global', path=['global'], content={'b': ScopedDefinition(name='b', path=['global', 'b'], content={...}, ast=ConstantDefinition(name='b', value=4, tags=set()))}), 'H': DefNodeScope(name='H', path=['H'], content={...}, ast=...)})}, ast=...), type=<VarType.continuous: 'continuous'>, bound_lower=None, bound_upper=None, import_from=None, tags=set()), VariableDefinition(name='y', indices=[], scope=ScopedVariableDefinition(name='y', path=['H', 'y'], content={'x': ScopedVariableDefinition(name='x', path=['H', 'x'], content={...}, ast=VariableDefinition(name='x', indices=[], scope=..., type=<VarType.continuous: 'continuous'>, bound_lower=None, bound_upper=None, import_from=None, tags=set())), 'y': ..., 'root': ParentNodeScope(name='root', path=[], content={'global': GlobalScope(name='global', path=['global'], content={'b': ScopedDefinition(name='b', path=['global', 'b'], content={...}, ast=ConstantDefinition(name='b', value=4, tags=set()))}), 'H': DefNodeScope(name='H', path=['H'], content={...}, ast=...)})}, ast=...), type=<VarType.continuous: 'continuous'>, bound_lower=None, bound_upper=None, import_from=None, tags=set())], constraints=[StdConstraint(name=None, lhs=VarOrParam(path=[VarOrParamLeaf(name='x', indices=[])]), op=<Operator.lesser_or_equal: '<='>, rhs=ExpressionOp(operator=<Operator.unary_minus: 'u-'>, operands=[4]), loop=None, tags=set())], objectives=[Objective(type=<ObjType.max: 'max'>, name=None, expression=ExpressionOp(operator=<Operator.plus: '+'>, operands=[VarOrParam(path=[VarOrParamLeaf(name='x', indices=[])]), VarOrParam(path=[VarOrParamLeaf(name='global', indices=[]), VarOrParamLeaf(name='b', indices=[])])]), loop=None, tags=set())], activations=[], tags=set())


def _appendErrors(element: GBOMLObject, defNodeScope: DefNodeScope) -> None:
    
    # if element.path[0].name not in defNodeScope.content and element.path[0].name not in defNodeScope.parent.content:
        # print(f"SEMANTIC ERROR: {element.path[0].name} not declared in this scope {element.meta}!")
        # print(defNodeScope.parent)
    # else:
        # print(f"semantic ok: {element.path[0].name} declared in scope {element.meta}")

    for subElement in element.path:
        print(f"SubElement {subElement.name}")
        # if isinstance(defNodeScope, RootScope):
            # print(defNodeScope)
            # break
        if subElement.name not in defNodeScope.content and subElement.name not in defNodeScope.parent.content:
            print(f"SEMANTIC ERROR: {subElement.name} not declared in this scope {subElement.meta}!")
            print(defNodeScope.parent)
        else:
            print(f"semantic ok: {subElement.name} declared in scope {subElement.meta}")
            # print(defNodeScope.parent)
            if subElement.name in defNodeScope.parent.content:
                defNodeScope = defNodeScope.parent.content[subElement.name]
                print(defNodeScope)

def _visit_nodes(nodeDef: NodeDefinition) -> None:
    visit(nodeDef, {VarOrParam: lambda _: _appendErrors(_, nodeDef.scope)})

def semantic_check(rootScope: RootScope):
    visit(rootScope.ast, {NodeDefinition: _visit_nodes})
