"""
This step aims at resolving imports and extension of other GBOML models.
At the end of this step, no "extends" or "import" keyword may remain in the resulting graph
"""
import dataclasses
from pathlib import Path

from gboml.ast import *
from gboml.parsing import parse_file
from gboml.redundant_definitions import remove_redundant_definitions
from gboml.tools.tree_modifier import modify

WORKING = object
file_cache = {}


def load_file(fpath: Path):
    fpath = fpath.absolute()
    if fpath not in file_cache:
        file_cache[fpath] = resolve_imports(parse_file(fpath), fpath.parent)
    elif file_cache[fpath] is WORKING:
        raise RuntimeError("Recursive import")

    return file_cache[fpath]


def _merge(newAst: Node | HyperEdge,
           extends: Node | HyperEdge,
           additionnal_parameters: list[Definition]) -> Node | HyperEdge:
    """ Merges a node/hyperedge and its parent, forming a full node/hyperedge without extension. """
    if isinstance(newAst, Node):
        merge_fields = {"nodes", "hyperedges", "variables", "constraints", "objectives", "activations"}
    else:
        merge_fields = {"constraints", "activations"}

    return remove_redundant_definitions(dataclasses.replace(
        newAst,
        import_from=None,
        tags=newAst.tags | extends.tags,
        parameters=additionnal_parameters + extends.parameters + newAst.parameters,
        **{f: getattr(extends, f) + getattr(newAst, f) for f in merge_fields}
    ))


def _find_elem_with_name(l, name):
    """ Finds and returns the element in list `l` that has name `name`"""
    valid_nodes = [x for x in l if x.name == name]
    if len(valid_nodes) == 0:
        raise RuntimeError(f"Node/hyperedge with name '{name}' not found")
    if len(valid_nodes) == 2:
        raise RuntimeError(f"Multiple nodes/hyperedges have the same name '{name}'")
    return valid_nodes[0]


def resolve_imports(tree: GBOMLObject, current_dir: Path) -> GBOMLObject:
    def update(ast: NodeDefinition | NodeGenerator | HyperEdgeDefinition | HyperEdgeGenerator) \
            -> NodeDefinition | NodeGenerator | HyperEdgeDefinition | HyperEdgeGenerator:
        if ast.import_from is None:
            return ast

        imported_file = load_file(current_dir / ast.import_from.filename)

        # for now, we only resolve "directly-named" nodes in other files.
        # in the future we may resolve nodes referenced inside arrays or parameters, but for now we don't.

        # follow nodes up to the last part of the path
        cur_ast: GBOMLGraph | Node | HyperEdge = imported_file
        for idx, leaf in enumerate(ast.import_from.name.path[0:-1]):
            cur_ast = _find_elem_with_name(cur_ast.nodes, leaf.name)
            if leaf.indices:
                if not isinstance(cur_ast, NodeGenerator | HyperEdgeGenerator):
                    raise RuntimeError("This element is not a Node/Hyperedge generator.")
                if len(leaf.indices) != len(cur_ast.indices):
                    raise RuntimeError("Invalid number of indices.")

        # last element of the path
        cur_ast = _find_elem_with_name(cur_ast.nodes if isinstance(ast, Node) else cur_ast.hyperedges,
                                       ast.import_from.name.path[-1].name)

        # pay attention to indices
        additional_parameters = []
        if ast.import_from.name.path[-1].indices:
            last_indices = ast.import_from.name.path[-1].indices

            if not isinstance(cur_ast, NodeGenerator | HyperEdgeGenerator):
                raise RuntimeError("This element is not a Node/Hyperedge generator.")
            if len(last_indices) != len(cur_ast.indices):
                raise RuntimeError("Invalid number of indices.")
            for a, b in zip(cur_ast.indices, last_indices):
                additional_parameters.append(ExpressionDefinition(a, ExpressionUseGenScope(b)))

        # merge node/hyperedge
        return _merge(ast, cur_ast, additional_parameters)

    return modify(tree, {Node: update, HyperEdge: update})
