"""
This step aims to remove redundant definitions, in the form of parameters or variables being
redefined. This includes:

- Parameter extension:
      #PARAMETERS
         a <- 1
         a <- a + 1
         a <- a + 1
         a <- a + 1
  is transformed to
      #PARAMETERS
         $a$2 <- 1
         $a$1 <- $a$2 + 1
         $a$0 <- $a$1 + 1
         a <- $a$0 + 1
- Parameter overriding:
      #PARAMETERS
         a <- 1
         a <- 2
  is transformed to
      #PARAMETERS
         a <- 2
- Variable overriding. Only the last definition of a variable is kept.
- Variable scope change.
- Tag merging. Tag are merged inside the "true representative"
      #PARAMETERS
         a <- 1 @tag1
         a <- a + 1 @tag2
         b <- 1 @tag3
         b <- 2 @tag4
      #VARIABLES
         internal: a @tag5;
         internal: a @tag6;
  is transformed to
      #PARAMETERS
         $a$0 <- 1
         a <- $a$0 + 1 @tag1 @tag2
         b <- 2 @tag3 @tag4
      #VARIABLES
         internal: a @tag5 @tag6
"""
import dataclasses

from gboml.ast import *
from gboml.tools.tree_modifier import modify


def remove_redundant_definitions(elem: AnyGBOMLObject) -> AnyGBOMLObject:
    return modify(elem, {Node: _modify_node, HyperEdge: _modify_hyperedge})


def _name_change(pdef: Definition, old_name: str, new_name: str):
    if isinstance(pdef, FunctionDefinition):
        if old_name in pdef.args:  # ignore if shadowed
            return pdef

    def change_var(v: VarOrParam):
        if v.path[0].name == old_name:
            return dataclasses.replace(v, path=[dataclasses.replace(v.path[0], name=new_name)] + v.path[1:])
        return v

    return modify(pdef, {VarOrParam: change_var})


def _merge_parameters(parameters: list[Definition]) -> list[Definition] | None:
    need_update = False
    params: dict[str, list[Definition]] = {}
    for p in parameters:
        if p.name in params:
            need_update = True
            old_name = params[p.name][-1].name
            new_name = f"${old_name}${len(params[p.name])}"
            old_tags = params[p.name][-1].tags

            new_p = _name_change(p, old_name, new_name)
            throw_old = new_p is p  # if there is no usage of the old value, we will throw it

            # merge tags
            if old_tags != new_p.tags:
                new_p = dataclasses.replace(new_p, tags=old_tags | new_p.tags)

            if throw_old:
                params[p.name] = [new_p]
            else:
                params[p.name][-1] = dataclasses.replace(params[p.name][-1], name=new_name, tags=set())
                params[p.name].append(new_p)
        else:
            params[p.name] = [p]

    if need_update:
        return [y for x in params.values() for y in x]
    return None


def _merge_node_variables(variables: list[VariableDefinition | ScopeChange]) -> list[VariableDefinition] | None:
    need_update = False
    vars: dict[str, VariableDefinition] = {}
    for v in variables:
        match v:
            case VariableDefinition():
                if v.name not in vars:
                    vars[v.name] = v
                else:
                    vars[v.name] = dataclasses.replace(v, tags=vars[v.name].tags | v.tags) if vars[v.name].tags != v.tags else v
                    need_update = True
            case ScopeChange():
                if v.name not in vars:
                    raise RuntimeError(f"No variable named {v.name}")
                need_update = True
                vars[v.name].scope = v.scope
    if need_update:
        return list(vars.values())
    return None


def _modify_node(node: NodeDefinition | NodeGenerator) -> NodeDefinition | NodeGenerator:
    todo = {}

    params = _merge_parameters(node.parameters)
    if params is not None:
        todo["parameters"] = params

    vars = _merge_node_variables(node.variables)
    if vars is not None:
        todo["vars"] = vars

    if len(todo):
        return dataclasses.replace(node, **todo)
    return node


def _modify_hyperedge(hyperedge: HyperEdgeDefinition | HyperEdgeGenerator) -> HyperEdgeDefinition | HyperEdgeGenerator:
    params = _merge_parameters(hyperedge.parameters)
    if params is not None:
        return dataclasses.replace(hyperedge, parameters=params)
    return hyperedge


if __name__ == '__main__':
    print(remove_redundant_definitions(NodeDefinition(name="lol", parameters=[
        ConstantDefinition("a", 1, tags={"@t", "@t2"}),
        ConstantDefinition("a", ExpressionOp(Operator.plus, [1, VarOrParam([VarOrParamLeaf("a")])]), tags={"@t2", "@t3"}),
        ConstantDefinition("b", 1, tags={"@a"}),
        ConstantDefinition("b", 2),
    ])))
