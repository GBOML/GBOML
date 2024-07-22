"""
This step aims at resolving imports and extension of other GBOML models.
At the end of this step, no "Extends" or "import" cls may remain in the resulting graph
"""
import dataclasses
import pathlib
from typing import Optional

from gboml.ast import *
from gboml.parsing import GBOMLParser
from gboml.redundant_definitions import remove_redundant_definitions
from gboml.tools.tree_modifier import modify_hier, visit

# Singleton used in _load_file to detect cyclic imports
WORKING = object()

inheritable_ast = NodeDefinition | HyperEdgeDefinition

def _load_file(fpath: pathlib.Path, parser: GBOMLParser, file_cache: dict[pathlib.Path, GBOMLGraph]):
    """ Loads a file and resolves its imports. file_cache is used as a cache for already-seen files. """
    fpath = fpath.absolute()
    if fpath not in file_cache:
        file_cache[fpath] = resolve_imports(parser.parse_file(fpath), fpath.parent, parser, file_cache)
    elif file_cache[fpath] is WORKING:
        raise RuntimeError("Cyclic import")
    return file_cache[fpath]


def _update_import_from(child: inheritable_ast, parent: inheritable_ast, parent_indices: list[Definition]) -> inheritable_ast:
    """ Replaces the "Extend" element of child with its true parent, and add the needed parent_indices to its parameters """
    return dataclasses.replace(
        child,
        import_from=parent,
        parameters=parent_indices + parent.parameters
    )


def _find_leaf_with_name(l, name):
    """ Finds and returns the leaf in list `l` (can be under a Loop) that has name `name`"""
    def get_leaf_name(leaf):
        while isinstance(leaf, Loop):
            leaf = leaf.child
        return leaf.name

    valid_nodes = [x for x in l if get_leaf_name(x) == name]
    if not valid_nodes:
        raise RuntimeError(f"Node/hyperedge with name '{name}' not found. Remember to use the full path from the root of the file.")
    if len(valid_nodes) >= 2:
        raise RuntimeError(f"Multiple nodes/hyperedges have the same name '{name}'")
    return valid_nodes[0]


def resolve_imports(tree: GBOMLObject, current_dir: pathlib.Path, parser: GBOMLParser, file_cache: Optional[dict[pathlib.Path, GBOMLGraph]] = None) -> GBOMLObject:
    """
    Resolves imports, transforming all `Extends` entries to Nodes/HyperEdges.

    Args:
        tree:
        current_dir:
        file_cache: dict to be used as a cache. Should initially be empty, and should be reused between calls to
                    resolve_imports.

    Returns:
        A modified tree where Node/HyperEdges with an import_from value that is of type Extends have been
        replaced by a Node/HyperEdge
    """

    if file_cache is None:
        file_cache = {}

    node_cache: set[str] = set()  # paths stored as A.B.C

    def update(ast: inheritable_ast, hier: list[Node | HyperEdge]) -> inheritable_ast:
        if ast.import_from is None:
            return ast

        # TODO forbid if imported path is a parent or child node/hyperedge compared to where it is imported from

        path_i: Path = ast.import_from.name
        imported_node: GBOMLGraph | Node | HyperEdge = tree if ast.import_from.filename is None else _load_file(current_dir / ast.import_from.filename, parser, file_cache)
        stack: list[ExpressionArrayCall | ExpressionDotCall] = []
        constant_defs: ConstantDefinition = []  # used for declaring as params indices (e.g. "import A.B[2*sqrt(64)]" and "A.B[i] for i in [0:99]" => "i = 2*sqrt(64)")
        while not isinstance(path_i, PathRoot):
            stack.append(path_i)
            path_i = path_i.lhs
            if not isinstance(path_i, Path):
                raise RuntimeError(f"{ast.import_from.name.meta} Invalid import node expression. Should only contain attributes (A.B) and/or indices (A[0]).")
        path_str = path_i.name
        imported_node = _find_leaf_with_name(imported_node.nodes, path_str)
        while stack:
            if isinstance(path_i := stack.pop(), ExpressionArrayCall):
                if not isinstance(imported_node, Loop):
                    RuntimeError(f"{ast.import_from.name.meta} Too much indices. Declared here {ast.import_from.filename}:{imported_node.meta}")
                constant_defs.append(ConstantDefinition(imported_node.varid, path_i.rhs, set(), meta=MetaNone))
                imported_node = imported_node.child
            else:
                if isinstance(imported_node, Loop):
                    RuntimeError(f"{ast.import_from.name.meta} Too few indices. Declared here {ast.import_from.filename}:{imported_node.meta}")
                path_str += '.' + path_i.rhs
                imported_node = _find_leaf_with_name(imported_node.nodes if isinstance(ast, Node) else imported_node.hyperedges, path_i.rhs)
        if isinstance(imported_node, Loop):
            RuntimeError(f"{ast.import_from.name.meta} Too few indices. Declared here {ast.import_from.filename}:{imported_node.meta}")
        if imported_node not in hier[:-1]:
            node_cache.clear()
        if path_str in node_cache:
            raise RuntimeError(f"Circular import on {path_str}! Path: {'.'.join(hierItem.name for hierItem in hier)}")
        node_cache.add(path_str)

        new_node = dataclasses.replace(imported_node, name=ast.name, indices=[], parameters=imported_node.parameters + ast.parameters + constant_defs, constraints=imported_node.constraints + ast.constraints, activations=imported_node.activations + ast.activations)
        if isinstance(ast, Node):
            new_node.nodes = new_node.nodes + ast.nodes
            new_node.hyperedges = new_node.hyperedges + ast.hyperedges
            new_node.variables = new_node.variables + ast.variables
            new_node.objectives = new_node.objectives + ast.objectives

        return new_node if new_node.import_from is None else update(new_node, hier + [imported_node])

    return modify_hier(tree, {Node, HyperEdge}, {Node: update, HyperEdge: update})
