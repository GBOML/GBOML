from dataclasses import dataclass, field
from enum import Enum
from typing import Generic, TypeVar, Type, ClassVar

from gboml.ast import *
from gboml.tools.tree_modifier import visit, visit_hier

T = TypeVar('T', bound=NamedGBOMLObject)
U = TypeVar('U', bound=GBOMLObject)


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
    canBeCalledWithoutPrefix: bool = field(default=False, kw_only=True, repr=False)

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

        if ast.name in ['T', 't']:
            raise KeyError(f"Identifier {ast.name} cannot be redifined (reserved keyword)")

        self.content[ast.name] = wrapper(create_scope(ast, self))
        return self.content[ast.name]

    def _add_all_to_scope(self, l, wrapper=lambda x: x, whenPresent: OverrideBehavior = OverrideBehavior.fail) -> list["Scope"]:
        return [y for x in l for y in [self._add_to_scope(x, wrapper, whenPresent)] if y is not None]

    def __getitem__(self, item):
        try:
            return self.content[item]
        except KeyError as err:
            content = self.content if isinstance(self, GlobalScope) else self.content['global'].parent.content
            scope = content[item]
            if not scope.canBeCalledWithoutPrefix:
                raise err
            return scope


# singleton
class EmptyScope(Scope):
    _instances = {True: None, False: None}

    def __new__(cls, canBeCalledWithoutPrefix=False):
        if cls._instances[canBeCalledWithoutPrefix] is None:
            instance = super(EmptyScope, cls).__new__(cls)
            instance.parent = None
            instance.name = ""
            instance.path = []
            instance.content = {}
            instance.canBeCalledWithoutPrefix = canBeCalledWithoutPrefix
            cls._instances[canBeCalledWithoutPrefix] = instance
        return cls._instances[canBeCalledWithoutPrefix]

    def __init__(self, canBeCalledWithoutPrefix=False):
        pass  # Override to do nothing (and no need for constructor args)


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
        if item == 'baba':
            print(type(out), out.content.keys())
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
class HasLoopInScope(Scope, Generic[U]):
    name: str = field(init=False, default=None)
    ast: U
    astTypes: ClassVar[set[type[GBOMLObject]]] = {NodeGenerator, HyperEdgeGenerator, GeneratedExpression, DictEntry, StdConstraint, FunctionConstraint, Objective, Loop}
    varids: list[str] = field(init=False)

    def __post_init__(self):
        self.ast.scope = self
        self.path = self.parent.path
        self.content = self.parent.content
        self.varids = []

    # needed post_post_init because we need parent's scope fully filled in to update it with keys and check if intersects
    def _finalize_init(self):
        # only parent loop (of nested loops) should check for already defined variables
        if isinstance(self.ast, Loop) and not isinstance(self.parent.ast, Loop):
            varids = [self.ast.varid]
            i = self.ast
            while (i := i.loop) is not None:
                varids.append(i.varid)

            seen = set()
            duplicates = [varid for varid in varids if varid in seen or seen.add(varid)]
            if duplicates:
                raise RuntimeError(f"Identifier {duplicates} is already used")
            else:
                for varid in self.varids:
                    try:
                        self.parent[varid]
                        raise RuntimeError(f"Identifier {self.ast.loop.varid} is already used")
                    except KeyError:
                        pass
            
            self.varids = varids
            self.parent.varids = varids

    def __getitem__(self, item):
        if isinstance(self.ast, Loop):
            if self.ast.loop is not None:
                scope = self.ast.loop.scope
                while isinstance(scope.ast, Loop):
                    if item == scope.ast.varid:
                        raise KeyError(f"{item} is not accessible")
                    if scope.ast.loop is None:
                        break
                    scope = scope.ast.loop.scope
            elif item == self.ast.varid:
                return EmptyScope()
        elif item in self.varids:
            return EmptyScope()
        
        return self.parent[item]
    

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

        visit_hier(self.ast, {NodeDefinition} | HasLoopInScope.astTypes, dict.fromkeys(HasLoopInScope.astTypes, lambda astObj,hier: HasLoopInScope(hier[-2].scope, astObj)))


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

        visit_hier(self.ast, {HyperEdgeDefinition} | HasLoopInScope.astTypes, dict.fromkeys(HasLoopInScope.astTypes, lambda astObj,hier: HasLoopInScope(hier[-2].scope, astObj)))


@dataclass
class UnresolvedHyperEdgeGeneratorScope(NamedAstScope[NodeGenerator], Unresolvable):
    _parent_nodes: list[NodeScope]

    def __post_init__(self):
        super(UnresolvedHyperEdgeGeneratorScope, self).__post_init__()
        # no resolved yet, nothing is accessible
        self.content = {}


HyperEdgeScope = DefHyperEdgeScope | UnresolvedHyperEdgeGeneratorScope



@dataclass
class DefinitionScope(NamedAstScope[NodeDefinition]):
    def __post_init__(self):
        self.content = self.parent.content
        super(DefinitionScope, self).__post_init__()

@dataclass
class ScopedDefinition(DefinitionScope):
    pass

@dataclass
class ScopedFunctionDefinition(DefinitionScope):
    # needed post_post_init because we need parent's scope fully filled in to check if intersects
    def _finalize_init(self):
        for arg in self.ast.args:
            try:
                self.parent[arg]
                raise RuntimeError(f"Identifier {arg} is already used")
            except KeyError:
                pass

    def __getitem__(self, item):
        return EmptyScope() if item in self.ast.args else self.parent[item]

@dataclass
class ScopedVariableDefinition(DefinitionScope):
    pass


def create_scope(ast_or_scope: NamedGBOMLObject | Scope, parent: Scope) -> Scope:
    match ast_or_scope:
        case NodeDefinition(): return DefNodeScope(parent, ast_or_scope)
        case NodeGenerator(): return UnresolvedNodeGeneratorScope(parent, ast_or_scope)
        case FunctionDefinition(): return ScopedFunctionDefinition(parent, ast_or_scope)
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
        processLoopScope = lambda astObj,hier: HasLoopInScope(hier[-2].scope if len(hier) >= 2 else self, astObj)

        self.content = {}
        self._add_all_to_scope(self.ast.global_defs)
        if self.ast.time_horizon is not None:
            self.content |= dict.fromkeys(('t', 'T', 'len', 'sum'), EmptyScope(canBeCalledWithoutPrefix=True))
        for globdef in self.ast.global_defs:
            visit_hier(globdef, HasLoopInScope.astTypes, dict.fromkeys(HasLoopInScope.astTypes, processLoopScope))
        self.nodes = {x.name: x for x in self._add_all_to_scope(self.ast.nodes)}
        self.hyperedges = {h.name: create_hyperedge_scope(h, self, self.nodes.values()) for h in self.ast.hyperedges}
        visit(self.ast, dict.fromkeys({FunctionDefinition} | HasLoopInScope.astTypes, lambda astObj: astObj.scope._finalize_init()))
