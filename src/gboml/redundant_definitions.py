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
  is transformed to ect -91999 --mt-deflate -strip 9999x0w.png
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
from typing import Callable, Optional
import warnings

from gboml.ast import *
from gboml.tools.tree_modifier import modify, modify_hier

def _warn_redefinition(old_def: VarOrParamDefinition, new_def: VarOrParamDefinition) -> None:
    warnings.warn(f"Removed definition '{old_def.name}' {old_def.meta} since it is redefined later {new_def.meta}", SyntaxWarning, stacklevel=2)

def _get_obj_below_loops(obj: GBOMLObject) -> GBOMLObject:
    while isinstance(obj, Loop):
        obj = obj.child
    return obj

def _replace_obj_below_loops(possible_loop: GBOMLObject, obj: GBOMLObject) -> GBOMLObject:
    if not isinstance(possible_loop, Loop):
        return obj
    return dataclasses.replace(possible_loop, child=_replace_obj_below_loops(loop.child, obj))


def remove_redundant_definitions(elem: AnyGBOMLObject) -> AnyGBOMLObject:
    if isinstance(elem, GBOMLGraph):
        elem = _merge_attributes(elem, dict.fromkeys(('global_defs', 'nodes', 'hyperedges'), _merge_definitions))
    return modify(elem, {
        NodeDefinition: lambda node: _merge_attributes(node, {'variables': _merge_node_variables} | dict.fromkeys(('parameters', 'nodes', 'hyperedges'), _merge_definitions)),
        HyperEdgeDefinition: lambda hedge: _merge_attributes(hedge, {'parameters': _merge_definitions})
    })  # TODO see
    # constraints: tuple[Constraint] = field(default=tuple())
    # objectives: tuple[Objective] = field(default=tuple())
    # activations: tuple[Activation] = field(default=tuple())


def _merge_attributes(elem: AnyGBOMLObject, attrs_to_mergemethods: dict[str, Callable[[tuple[GBOMLObject]], Optional[tuple[GBOMLObject]]]]) -> AnyGBOMLObject:
    todo = {}
    for attr, merge_method in attrs_to_mergemethods.items():
        if (defs := merge_method(getattr(elem, attr))) is not None:
            todo[attr] = defs
    return dataclasses.replace(elem, **todo) if todo else elem


def _name_change(pdef: Definition, old_name: str, new_name: str):
    if isinstance(pdef, FunctionDefinition):
        if old_name in pdef.args:  # ignore if shadowed
            return pdef

    def change_var(p: PathRoot, hier: list[ExpressionDotCall|ExpressionFunctionCall|ExpressionArrayCall]):
        if p.name != old_name or hier and isinstance(hier[-1], ExpressionDotCall):
            return p
        else:
            return dataclasses.replace(p, name=new_name)

    return modify_hier(pdef, {ExpressionDotCall, ExpressionFunctionCall, ExpressionArrayCall}, {PathRoot: change_var})


def _merge_definitions(parameters: tuple[Definition|NodeDefinition|HyperEdgeDefinition|Loop]) -> Optional[tuple[Definition|NodeDefinition|HyperEdgeDefinition|Loop]]:
    need_update = False
    params: dict[str, list[Definition|NodeDefinition|HyperEdgeDefinition|Loop]] = {}
    for possible_loop in parameters:
        p = _get_obj_below_loops(possible_loop)
        if p.name in params:
            need_update = True
            old_obj = _get_obj_below_loops(params[p.name][-1])
            old_name = old_obj.name
            new_name = f"${old_name}${len(params[p.name])}"
            old_tags = old_obj.tags

            new_p = _name_change(p, old_name, new_name)
            throw_old = new_p is p  # if there is no usage of the old value, we will throw it

            # merge tags
            if old_tags != new_p.tags:
                new_p = dataclasses.replace(new_p, tags=old_tags | new_p.tags)

            if throw_old:
                _warn_redefinition(old_obj, new_p)
                params[p.name] = [possible_loop if new_p is p else _replace_obj_below_loops(possible_loop, new_p)]
            else:
                params[p.name][-1] = _replace_obj_below_loops(params[p.name][-1], dataclasses.replace(old_obj, name=new_name, tags=frozenset()))
                params[p.name].append(_replace_obj_below_loops(possible_loop, new_p))
        else:
            params[p.name] = [possible_loop]

    if need_update:
        return tuple(y for x in params.values() for y in x)
    return None


def _merge_node_variables(variables: tuple[VariableDefinition | ScopeChange]) -> Optional[tuple[VariableDefinition]]:
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
                vars[v.name] = dataclasses.replace(vars[v.name], scope=v.scope)
    if need_update:
        return tuple(vars.values())
    return None
