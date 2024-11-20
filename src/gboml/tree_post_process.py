"""
This step aims to expand the GBOMLGraph just after the parsing.
What is done: import resolution, Activations resolution, redundant definitions removal, LikeLoops to BaseLoops conversion, ImplicitLoops insertion.
We need to resolve the scope in order to insert ImplicitLoops, which is stored in tree.semantic.scope.
No changes to the tree structure are required after this step (with the exception of *possible* changes to attributes specific to AST nodes and leaves).
"""
from gboml.ast import *
from gboml.parsing import GBOMLParser
from gboml.redundant_definitions import remove_redundant_definitions
from gboml.resolve_imports import resolve_imports
from gboml.scope import GlobalScope, HierTypes, get_parent_from_hier, get_scope_after_expr
from gboml.tools.tree_modifier import modify_hier, modify
from itertools import chain, groupby
from pathlib import Path
from typing import Callable, Iterator, Optional
import dataclasses


GenobjsOrGenattrs = GeneratedObjectsType|Array|FunctionConstraint|ExpressionFunctionCall


def _get_obj_below_loops(obj: GBOMLObject) -> GBOMLObject:
    while isinstance(obj, Loop):
        obj = obj.child
    return obj


def _mark_implicit_loops(elem: ExpressionDotCall|PathRoot, hier: list[HierTypes], implicit_loops: dict[GenobjsOrGenattrs|ExpressionObj, set[ImplicitLoop]]) -> ExpressionDotCall|PathRoot:
    """ If an elem references is an IndexingParameterDefinition, mark a new ImplicitLoop in implicit_loops (key=future child of ImplicitLoop, val=ImplicitLoops) """
    if not isinstance(getattr(elem, 'lhs', elem), PathRoot):
        return elem  # if both elem and lhs are not PathRoot, cannot check anything

    if (parent := get_parent_from_hier(hier, GenobjsOrGenattrs|ImplicitLoop)) is not None and isinstance(index_param_def := getattr(get_scope_after_expr(elem), 'ast', None), IndexingParameterDefinition):
        new_loop = ImplicitLoop(None, None, varid=index_param_def.name, on=index_param_def.value, meta=parent.meta)
        # do not add ImplicitLoop if already present in hier (could only be with varid='t' at this time)
        if any(isinstance(hier_item, ImplicitLoop) and hier_item.varid == new_loop.varid == 't' for hier_item in hier):
            return  # TODO throw error if the loop from hier does not have IndexParam as child?

        if parent in implicit_loops:
            implicit_loops[parent].add(new_loop)
        else:
            implicit_loops[parent] = {new_loop}

    return elem

# TODO: reimplement completely implicit loops insertion: they should only be possibly used in Constraints and Objectives
def _add_implicit_loops(elem: GenobjsOrGenattrs|ExpressionObj, hier: list[HierTypes], implicit_loops: dict[GenobjsOrGenattrs|ExpressionObj, set[ImplicitLoop]]) -> GenobjsOrGenattrs|ExpressionObj:
    new_elem = elem
    for loop in implicit_loops.get(elem, []):
        match elem:
            case Array():
                print('arr')  # TODO, array and fcts need to know on which argument the ImplicitLoop(s) are
            case FunctionConstraint() | ExpressionFunctionCall():
                print('fct')
            case _:
                print('default')
        new_elem = dataclasses.replace(loop, child=new_elem)
    return new_elem


def _process_activations(tree: GBOMLGraph) -> GBOMLGraph:
    """
    Checks for duplicate named Objectives, named Constraints, Activations; and for (de)Activations not refering to any known Obj/Constr.
    If Activation is not conditional and is "deactivate", remove Obj/Constr from tree. Activation is removed when possible.
    """
    def check_dups(t, get_name=lambda x: _get_obj_below_loops(x).name):
        seen = set()
        if dups := [x for x in t if (name := get_name(x)) is not None and name in seen or seen.add(name)]:
            raise KeyError(f"{list(d.meta for d in dups)}: several {type(dups[0]).__name__} with the same name {set(get_name(d) for d in dups)}.")

    def modify_ctrs_objs(ctrs_objs: tuple[Constraint, ...]|tuple[Objective, ...], acts: Iterator[CtrActivation]|Iterator[ObjActivation], meta: Meta) -> Optional[tuple[Constraint, ...]|tuple[Objective, ...]]:
        """ Gets elem.contraints OR elem.objectives (corresponding *respectively* to CtrAct|ObjAct), remove some of them using elem.activations, returns updated ctrs OR objs (or None if no update needed). """
        check_dups(ctrs_objs)
        acts_names = set(chain.from_iterable(act.what for act in acts))
        check_dups(acts_names, lambda x: x)
        if undefineds := acts_names.difference(_get_obj_below_loops(co).name for co in ctrs_objs):
            raise KeyError(f"{meta}: (de)activation '{undefineds}' does not refer to any known Constraint/Objective.")
        if names_to_remove := set(chain.from_iterable(act.what for act in acts if act.condition is None and act.type == ActivationType.deactivate)):
            return tuple(co for co in ctrs_objs if _get_obj_below_loops(co).name not in names_to_remove)
        return None

    def node_acts(elem: NodeDefinition) -> NodeDefinition:
        new_ctrs = modify_ctrs_objs(elem.constraints, (acts for acts in elem.activations if isinstance(acts, CtrActivation)), elem.meta)
        new_objs = modify_ctrs_objs(elem.objectives, (acts for acts in elem.activations if isinstance(acts, ObjActivation)), elem.meta)
        return elem if new_ctrs is None and new_objs is None else dataclasses.replace(elem, activations=tuple(act for act in elem.acts if act.condition is not None), constraints=new_ctrs, objectives=new_objs)

    def hyperedge_acts(elem: HyperEdgeDefinition) -> HyperEdgeDefinition:
        new_ctrs = modify_ctrs_objs(elem.constraints, elem.activations, elem.meta)
        return elem if new_ctrs is None else dataclasses.replace(elem, activations=tuple(act for act in elem.acts if act.condition is not None), constraints=new_ctrs)

    return modify(tree, {NodeDefinition: node_acts, HyperEdgeDefinition: hyperedge_acts})


# TODO should check if all elements in activation condition are actually params (not vars)

def _process_loops(tree: GBOMLGraph) -> GBOMLGraph:
    """ Adds ImplicitLoops and convert LikeLoops to BaseLoops """
    def likeloop_to_baseloop(elem: LikeLoop, hier: list[HierTypes]) -> BaseLoop:
        if not isinstance(index_param_def := getattr(get_scope_after_expr(elem.on), 'ast', None), IndexingParameterDefinition):
            raise RuntimeError(f"{elem} {elem.meta}: {elem.on} is not an IndexingParameterDefinition")
        return BaseLoop(elem.child, elem.varid, index_param_def.value, elem.condition, meta=elem.meta, semantic=elem.semantic)

    tree = modify_hier(tree, set(HierTypes.__args__), {LikeLoop: likeloop_to_baseloop})
    implicit_loops: dict[GenobjsOrGenattrs|ExpressionObj, set[ImplicitLoop]] = {}
    tree = modify_hier(tree, GeneratedObjects | {*HierTypes.__args__, ImplicitLoop, Array, FunctionConstraint, ExpressionFunctionCall},
                by_before=dict.fromkeys((ExpressionDotCall, PathRoot), lambda elem,hier: _mark_implicit_loops(elem, hier, implicit_loops)),
                by_after=dict.fromkeys(GenobjsOrGenattrs.__args__ + (ExpressionObj,), lambda elem,hier: _add_implicit_loops(elem, hier, implicit_loops)))
    print("⸻⸻⸻⸻⸻⸻⸻⸻⸻⸻⸻⸻⸻⸻⸻⸻⸻⸻TODO: this reconstructs the WHOLE Scope (children's init and post_init are called too)⸻⸻⸻⸻⸻⸻⸻⸻⸻⸻", hash(tree.semantic.scope))
    tree.semantic.scope = dataclasses.replace(tree.semantic.scope, ast=tree)  # TODO: this reconstructs the WHOLE Scope (children's init and post_init are called too)
    print("⸻⸻⸻⸻⸻⸻⸻⸻⸻⸻⸻⸻⸻⸻⸻⸻⸻⸻TODO: this reconstructs the WHOLE Scope (children's init and post_init are called too)⸻⸻⸻⸻⸻⸻⸻⸻⸻⸻", hash(tree.semantic.scope))
    return tree


def post_process(tree: GBOMLGraph, parser: GBOMLParser) -> GBOMLGraph:
    tree = resolve_imports(tree, Path('.'), parser)
    tree = remove_redundant_definitions(tree)
    tree = _process_activations(tree)
    tree.semantic.scope = GlobalScope(tree)
    return _process_loops(tree)
