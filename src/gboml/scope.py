from dataclasses import dataclass, field
from enum import Enum
from typing import Generic, TypeVar, Type

from gboml.ast import *
from gboml.tools.tree_modifier import visit, visit_hier

T = TypeVar('T', bound=NamedGBOMLObject)


class OverrideBehavior(Enum):
    ignore = 0
    fail = 1
    overwrite = 2


@dataclass
class Scope:
    parent: "Scope" = field(repr=False)
    name: str
    path: list[str] = field(init=False)
    content: dict[str, "Scope"] = field(init=False)

    def __post_init__(self):
        self.path = self.parent.path + [self.name]

    def _add_to_scope(self, ast, wrapper=lambda x: x, whenPresent: OverrideBehavior = OverrideBehavior.fail) -> "Scope | None":
        if ast.name in self.content:
            if whenPresent == OverrideBehavior.fail:
                raise RuntimeError(f"Identifier {ast.name} is already used")
            elif whenPresent == OverrideBehavior.ignore:
                return None
            else:
                pass

        self.content[ast.name] = wrapper(create_scope(ast, self))
        return self.content[ast.name]

    def _add_all_to_scope(self, l, wrapper=lambda x: x, whenPresent: OverrideBehavior = OverrideBehavior.fail) -> list["Scope"]:
        return [y for x in l for y in [self._add_to_scope(x, wrapper, whenPresent)] if y is not None]

    def __getitem__(self, item):
        return self.content[item]


@dataclass
class Unresolvable(Scope):
    def __getitem__(self, item):
        raise RuntimeError("Not resolved yet")


@dataclass
class NamedAstScope(Scope, Generic[T]):
    name: str = field(init=False)
    ast: T

    def __post_init__(self):
        self.name = self.ast.name
        self.ast.scope = self
        super(NamedAstScope, self).__post_init__()


@dataclass
class ParentNodeScope(Scope):
    """ A child can only access the parameters of its parents """
    parent: "NodeScope" = field(repr=False)
    name: str = field(init=False)

    def __post_init__(self):
        self.name = self.parent.name
        self.path = self.parent.path
        self.content = self.parent.content

    def __getitem__(self, item):
        out = super(ParentNodeScope, self).__getitem__(item)
        if not isinstance(out, ScopedDefinition):
            raise KeyError(f"{item} is not accessible")
        return out


@dataclass
class ChildNodeScope(Scope):
    """ A parent can only access the vars of this child (not directly, but at least in child hyperedges) """
    parent: "NodeScope" = field(repr=False)
    name: str = field(init=False)

    def __post_init__(self):
        self.name = self.parent.name
        self.path = self.parent.path
        self.content = self.parent.content

    def __getitem__(self, item):
        out = super(ChildNodeScope, self).__getitem__(item)
        if not isinstance(out, ScopedVariableDefinition):
            raise KeyError(f"{item} is not accessible")
        return out


@dataclass
class DefNodeScope(NamedAstScope[NodeDefinition]):
    nodes: dict[str, "NodeScope"] = field(init=False, repr=False)
    hyperedges: dict[str, "HyperEdgeScope"] = field(init=False, repr=False)

    def __post_init__(self):
        super(DefNodeScope, self).__post_init__()
        self.content = {}
        self._add_all_to_scope(self.ast.parameters)
        node_scopes = self._add_all_to_scope(self.ast.nodes, ChildNodeScope)
        self._add_all_to_scope(self.ast.variables)

        parents = [self.parent]
        while not isinstance(parents[-1], GlobalScope):
            parents.append(parents[-1].parent)
        self._add_all_to_scope(parents, ParentNodeScope, OverrideBehavior.ignore)

        self.nodes = {x.parent.name: x.parent for x in node_scopes}
        self.hyperedges = {h.name: create_hyperedge_scope(h, self, list(self.nodes.values())) for h in self.ast.hyperedges}


@dataclass
class UnresolvedNodeGeneratorScope(NamedAstScope[NodeGenerator], Unresolvable):
    def __post_init__(self):
        super(UnresolvedNodeGeneratorScope, self).__post_init__()
        # no resolved yet, nothing is accessible
        self.content = {}


NodeScope = DefNodeScope | UnresolvedNodeGeneratorScope


@dataclass
class DefHyperEdgeScope(NamedAstScope[HyperEdgeDefinition]):
    _parent_nodes: list[NodeScope]

    def __post_init__(self):
        super(DefHyperEdgeScope, self).__post_init__()
        self.content = {}
        self._add_all_to_scope(self.ast.parameters)
        self._add_all_to_scope(self._parent_nodes)

        parents = [self.parent]
        while not isinstance(parents[-1], GlobalScope):
            parents.append(parents[-1].parent)
        self._add_all_to_scope(parents, ParentNodeScope, OverrideBehavior.ignore)


@dataclass
class UnresolvedHyperEdgeGeneratorScope(NamedAstScope[NodeGenerator], Unresolvable):
    _parent_nodes: list[NodeScope]

    def __post_init__(self):
        super(UnresolvedHyperEdgeGeneratorScope, self).__post_init__()
        # no resolved yet, nothing is accessible
        self.content = {}


HyperEdgeScope = DefHyperEdgeScope | UnresolvedHyperEdgeGeneratorScope

def _add_scope_to_varOrParam(var: VarOrParam, scope: Scope):
    print("HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH", scope.path)
    print(list(map(lambda var: var.name, var.path)))
    var.scope = scope

@dataclass
class ScopedDefinition(NamedAstScope[NodeDefinition]):
    def __post_init__(self):
        super(ScopedDefinition, self).__post_init__()
        self.content = self.parent.content
        visit(self.ast, {VarOrParam: lambda var: _add_scope_to_varOrParam(var, self)})

@dataclass
class ScopedVariableDefinition(NamedAstScope[NodeDefinition]):
    def __post_init__(self):
        super(ScopedVariableDefinition, self).__post_init__()
        self.content = self.parent.content
        visit(self.ast, {VarOrParam: lambda var: _add_scope_to_varOrParam(var, self)})


def create_scope(ast_or_scope: NamedGBOMLObject | Scope, parent: Scope) -> Scope:
    match ast_or_scope:
        case NodeDefinition(): return DefNodeScope(parent, ast_or_scope)
        case NodeGenerator(): return UnresolvedNodeGeneratorScope(parent, ast_or_scope)
        case Definition(): return ScopedDefinition(parent, ast_or_scope)
        case VariableDefinition(): return ScopedVariableDefinition(parent, ast_or_scope)
        case Scope(): return ast_or_scope
        case _: raise RuntimeError(f"Unknown Type {ast_or_scope.__class__}")

def create_hyperedge_scope(ast: HyperEdge, parent: Scope, nodes_in_parent: list[NodeScope]) -> Scope:
    match ast:
        case HyperEdgeDefinition(): return DefHyperEdgeScope(parent, ast, nodes_in_parent)
        case HyperEdgeGenerator(): return UnresolvedHyperEdgeGeneratorScope(parent, ast, nodes_in_parent)

@dataclass
class GlobalScope(Scope):
    name: str = field(init=False, default="global")
    path: list[str] = field(init=False, default_factory=lambda: [])
    parent: Scope = field(init=False, default=None)
    ast: GBOMLGraph = field(repr=False)
    nodes: dict[str, NodeScope] = field(init=False, repr=False)
    hyperedges: dict[str, HyperEdgeScope] = field(init=False, repr=False)

    def __post_init__(self):
        self.content = {}
        self._add_all_to_scope(self.ast.global_defs)
        self.nodes = {x.name: x for x in self._add_all_to_scope(self.ast.nodes)}
        self.hyperedges = {h.name: create_hyperedge_scope(h, self, self.nodes.values()) for h in self.ast.hyperedges}
