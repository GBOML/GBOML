from dataclasses import dataclass, field
from enum import Enum
from typing import Generic, TypeVar, Type, ClassVar

from gboml.ast import *
from gboml.tools.tree_modifier import visit, visit_hier

T = TypeVar('T', bound=NamedGBOMLObject)
U = TypeVar('U', bound=GBOMLObject)

def _create_loopscope_from_attrs(scope: "Scope", element: GBOMLObject, attrs: tuple[str]):
    for attr in attrs:
        for sub_ast in getattr(element, attr):
            visit_hier(sub_ast, {GBOMLObject, Loop}, {Loop: lambda loop,hier: LoopScope(next((hierItem.scope for hierItem in reversed(hier[:-1]) if hasattr(hierItem, 'scope')), scope), loop)})

class OverrideBehavior(Enum):
    ignore = 0
    fail = 1
    overwrite = 2

@dataclass()
class Scope:
    parent: "Scope" = field(repr=False)
    name: str
    path: list[str] = field(init=False)
    content: dict[str, "Scope"] = field(init=False)

    def __post_init__(self):
        self.path = self.parent.path + [self.name]

    def _add_to_scope(self, ast, wrapper=lambda x: x, whenPresent: OverrideBehavior = OverrideBehavior.fail) -> "Scope | None":
        parent = self
        while isinstance(ast, Loop):
            parent = LoopScope(parent, ast)
            ast = ast.child

        if ast.name in self.content:
            if whenPresent == OverrideBehavior.fail:
                raise RuntimeError(f"Identifier {ast.name} is already used")
            elif whenPresent == OverrideBehavior.ignore:
                return None
            else:
                pass

        if ast.name == 'parent':
            raise KeyError(f"Identifier {ast.name} cannot be redefined (reserved keyword)")

        self.content[ast.name] = wrapper(create_scope(ast, parent))
        return self.content[ast.name]

    def _add_all_to_scope(self, l, wrapper=lambda x: x, whenPresent: OverrideBehavior = OverrideBehavior.fail) -> list["Scope"]:
        return [y for x in l for y in [self._add_to_scope(x, wrapper, whenPresent)] if y is not None]

    def __getitem__(self, item):
        if item == 'parent':
            return ParentNodeScope(self.parent)
        try:
            return self.content[item]
        except KeyError as err:  # TODO ask if should delete "as err" or not, can simply use "raise" (instead of "raise err")
            if isinstance(self, GlobalScope):
                raise err

            try:
                scope = self.parent[item]
            except KeyError:
                pass
            else:
                if isinstance(scope, EmptyScope):
                    return scope
                else:
                    raise err

            try:  # note: both 'global' and item can raise KeyError
                scope = self.content['global'].parent.content[item]
            except KeyError:
                pass
            else:
                if getattr(scope, 'canBeCalledWithoutPrefix', False):
                    return scope
            raise err

    def __hash__(self):
        return hash(self.path_to_str())

    def path_to_str(self):
        return '.'.join(self.path)


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

    def __bool__(self):
        return False


@dataclass(eq=False)
class Unresolvable(Scope):  # TODO is this useful ?
    def __getitem__(self, item):
        raise RuntimeError("Not resolved yet")


@dataclass(eq=False)
class NamedAstScope(Scope, Generic[T]):
    name: str = field(init=False)
    ast: T

    def __post_init__(self):
        self.name = self.ast.name
        self.ast.scope = self
        super(NamedAstScope, self).__post_init__()


@dataclass(eq=False)
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
        if not isinstance(out, ScopedDefinition | EmptyScope):
            raise KeyError(f"{item} is not accessible")
        return out


@dataclass(eq=False)
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


@dataclass(eq=False)
class LoopScope(Scope, Generic[U]):
    name: str = field(init=False, default=None)
    ast: U
    varids: list[str] = field(init=False)

    def __post_init__(self):
        self.ast.scope = self
        self.path = self.parent.path
        self.content = self.parent.content

    # needed post_post_init because we need parent's scope fully filled in to update it with keys and check if intersects
    def _finalize_init(self):
        try:
            self.parent[self.ast.varid]
            raise RuntimeError(f"Identifier {self.ast.varid} is already used")
        except KeyError:
            pass

    def __getitem__(self, item):
        return EmptyScope() if item == self.ast.varid else self.parent[item]


@dataclass(eq=False)
class NodeScope(NamedAstScope[NodeDefinition]):
    nodes: dict[str, "NodeScope"] = field(init=False, repr=False)
    hyperedges: dict[str, "HyperEdgeScope"] = field(init=False, repr=False)

    def __post_init__(self):
        super(NodeScope, self).__post_init__()
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

        _create_loopscope_from_attrs(self, self.ast, ('constraints', 'objectives', 'parameters'))


@dataclass(eq=False)
class HyperEdgeScope(NamedAstScope[HyperEdgeDefinition]):
    _parent_nodes: list[NodeScope]

    def __post_init__(self):
        super(HyperEdgeScope, self).__post_init__()
        self.content = {}
        self._add_all_to_scope(self.ast.parameters)
        self._add_all_to_scope(self._parent_nodes)

        parents = [self.parent]
        while not isinstance(parents[-1], GlobalScope):
            parents.append(parents[-1].parent)
        self._add_all_to_scope(parents, ParentNodeScope, OverrideBehavior.ignore)

        _create_loopscope_from_attrs(self, self.ast, ('constraints', 'parameters'))


@dataclass(eq=False)
class DefinitionScope(NamedAstScope[Definition]):
    def __post_init__(self):
        self.content = self.parent.content
        super(DefinitionScope, self).__post_init__()

@dataclass(eq=False)
class ScopedDefinition(DefinitionScope):
    pass

@dataclass(eq=False)
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

@dataclass(eq=False)
class ScopedVariableDefinition(DefinitionScope):
    pass


def create_scope(ast_or_scope: NamedGBOMLObject | Scope, parent: Scope) -> Scope:
    match ast_or_scope:
        case NodeDefinition(): return NodeScope(parent, ast_or_scope)
        case FunctionDefinition(): return ScopedFunctionDefinition(parent, ast_or_scope)
        case Definition(): return ScopedDefinition(parent, ast_or_scope)
        case VariableDefinition(): return ScopedVariableDefinition(parent, ast_or_scope)
        case Scope(): return ast_or_scope
        case _: raise RuntimeError(f"Unknown Type {ast_or_scope.__class__}")

def create_hyperedge_scope(ast: HyperEdge, parent: Scope, nodes_in_parent: list[NodeScope]) -> Scope:
    match ast:
        case HyperEdgeDefinition(): return HyperEdgeScope(parent, ast, nodes_in_parent)
        case HyperEdgeGenerator(): return UnresolvedHyperEdgeGeneratorScope(parent, ast, nodes_in_parent)

@dataclass(eq=False)
class GlobalScope(Scope):
    name: str = field(init=False, default="global")
    path: list[str] = field(init=False, default_factory=list)
    parent: Scope = field(init=False, default=None)
    ast: GBOMLGraph = field(repr=False)
    nodes: dict[str, NodeScope] = field(init=False, repr=False)
    hyperedges: dict[str, HyperEdgeScope] = field(init=False, repr=False)

    def __post_init__(self):
        # processLoopScope = lambda astObj,hier: LoopScope(hier[-2].scope if len(hier) >= 2 else self, astObj)

        self.content = {}
        self._add_all_to_scope(self.ast.global_defs)
        self.content |= dict.fromkeys(('len', 'sum') if self.ast.time_horizon is None else ('t', 'T', 'len', 'sum'), EmptyScope(canBeCalledWithoutPrefix=True))
        _create_loopscope_from_attrs(self, self.ast, ('global_defs',))
        # for globdef in self.ast.global_defs:
            # visit_hier(globdef, {Loop}, dict.fromkeys(GeneratedObjects, processLoopScope))
        self.nodes = {x.name: x for x in self._add_all_to_scope(self.ast.nodes)}
        self.hyperedges = {h.name: create_hyperedge_scope(h, self, self.nodes.values()) for h in self.ast.hyperedges}
        visit(self.ast, dict.fromkeys({FunctionDefinition, Loop}, lambda astObj: astObj.scope._finalize_init()))
