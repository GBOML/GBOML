"""
This step aims at resolving imports and extension of other GBOML models.
At the end of this step, no "Extends" or "import" cls may remain in the resulting graph
"""
import dataclasses
from pathlib import Path
from typing import Optional

from gboml.ast import *
from gboml.parsing import GBOMLParser
from gboml.redundant_definitions import remove_redundant_definitions
from gboml.tools.tree_modifier import modify

# Singleton used in _load_file to detect cyclic imports
WORKING = object()

inheritable_ast = NodeDefinition | NodeGenerator | HyperEdgeDefinition | HyperEdgeGenerator

def _load_file(fpath: Path, parser: GBOMLParser, file_cache: dict[Path, GBOMLGraph]):
    """ Loads a file and resolves its imports. file_cache is used as a cache for already-seen files. """
    fpath = fpath.absolute()
    if fpath not in file_cache:
        file_cache[fpath] = resolve_imports(parser.parse_file(fpath), fpath.parent, file_cache)
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

def _check_indices(child: inheritable_ast,
                   parent: inheritable_ast):
    """ Checks that no indices are overriden """
    child_indices = set()
    if isinstance(child, NodeGenerator) or isinstance(child, HyperEdgeGenerator):
        child_indices = set(child.indices)
    child_parameters = {definition.name for definition in child.parameters}

    if not child_indices.isdisjoint(child_parameters):
        raise RuntimeError(f"The following indices are redefined: " + str(child_indices.intersection(child_parameters)))

    while parent is not None:
        if isinstance(parent, NodeGenerator) or isinstance(parent, HyperEdgeGenerator):
            parent_indices = set(parent.indices)
            if not parent_indices.isdisjoint(child_indices):
                raise RuntimeError(f"{child.name} cannot share indices {parent_indices.intersection(child_indices)} with its parent {parent.name}. Change the name of the indice(s).")
            if not parent_indices.isdisjoint(child_parameters):
                raise RuntimeError(f"{child.name} cannot override indices {parent_indices.intersection(child_parameters)} of its parent {parent.name}.")
        parent_parameters = {definition.name for definition in parent.parameters}
        if not parent_parameters.isdisjoint(child_indices):
            raise RuntimeError(f"{child.name}'s indices {parent_parameters.intersection(child_indices)} override parameters of its parent {parent.name}.")
        parent = parent.import_from



def _find_elem_with_name(l, name):
    """ Finds and returns the element in list `l` that has name `name`"""
    valid_nodes = [x for x in l if x.name == name]
    if len(valid_nodes) == 0:
        raise RuntimeError(f"Node/hyperedge with name '{name}' not found")
    if len(valid_nodes) == 2:
        raise RuntimeError(f"Multiple nodes/hyperedges have the same name '{name}'")
    return valid_nodes[0]

def resolve_imports(tree: GBOMLObject, current_dir: Path, parser: GBOMLParser, file_cache: Optional[dict[Path, GBOMLGraph]] = None) -> GBOMLObject:
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

    def update(ast: inheritable_ast) -> inheritable_ast:
        if ast.import_from is None:
            return ast

        imported_file = _load_file(current_dir / ast.import_from.filename, parser, file_cache)

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
        parent = _find_elem_with_name(cur_ast.nodes if isinstance(ast, Node) else cur_ast.hyperedges,
                                      ast.import_from.name.path[-1].name)

        # pay attention to indices
        parent_indices = []
        if ast.import_from.name.path[-1].indices:
            last_indices = ast.import_from.name.path[-1].indices

            if not isinstance(parent, NodeGenerator | HyperEdgeGenerator):
                raise RuntimeError("This element is not a Node/Hyperedge generator.")
            if len(last_indices) != len(parent.indices):
                raise RuntimeError("Invalid number of indices.")
            for a, b in zip(parent.indices, last_indices):
                parent_indices.append(ExpressionDefinition(a, ExpressionUseGenScope(b)))

        _check_indices(ast, parent)

        return _update_import_from(ast, parent, parent_indices)

    return modify(tree, {Node: update, HyperEdge: update})
