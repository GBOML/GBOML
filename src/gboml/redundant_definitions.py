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
import typing
import warnings

from gboml.ast import *
from gboml.tools.tree_modifier import modify, modify_hier

def _warn_redefinition(old_def: Definition | VariableDefinition, new_def: Definition | VariableDefinition) -> None:
    warnings.warn(f"Removed definition '{old_def.name}' ({old_def.meta}) since it is redefined later ({new_def.meta})", SyntaxWarning, stacklevel=2)


def remove_redundant_definitions(elem: AnyGBOMLObject) -> AnyGBOMLObject:
    if isinstance(elem, GBOMLGraph):
        elem = _merge_attributes(elem, {'global_defs': _merge_definitions, 'nodes': _merge_definitions, 'hyperedges': _merge_definitions})
    return modify(elem, {
        Node: lambda node: _merge_attributes(node, {'parameters': _merge_definitions, 'variables': _merge_node_variables}),
        HyperEdge: lambda hedge: _merge_attributes(hedge, {'parameters': _merge_definitions})
    })


def _merge_attributes(elem: AnyGBOMLObject, attrs_to_mergemethods: dict[str, typing.Callable[[list[GBOMLObject]], list[GBOMLObject] | None]]) -> AnyGBOMLObject:
    todo = {}
    for attr, merge_method in attrs_to_mergemethods.items():
        if (defs := merge_method(getattr(elem, attr))) is not None:
            todo[attr] = defs
    return dataclasses.replace(elem, **todo) if todo else elem


def _name_change(pdef: Definition, old_name: str, new_name: str):
    if isinstance(pdef, FunctionDefinition):
        if old_name in pdef.args:  # ignore if shadowed
            return pdef

    def change_var(p: PathRoot, hier: list[Path]):
        if len(hier) >= 2 and isinstance(hier[-2], ExpressionDotCall) and hier[-2].lhs is not p:
            return
        if p.name == old_name:
            return dataclasses.replace(p, name=new_name)
        return p

    return modify_hier(pdef, {*Path.__args__}, {PathRoot: change_var})


def _merge_definitions(parameters: list[Definition]) -> list[Definition] | None:
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
                _warn_redefinition(params[p.name][-1], p)
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
                    _warn_redefinition(vars[v.name], v)
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
