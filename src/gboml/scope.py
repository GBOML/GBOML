from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Generic, TypeVar, Type, ClassVar, Optional

from gboml.ast import *
from gboml.tools.tree_modifier import visit, visit_hier

T = TypeVar('T', bound=NamedGBOMLObject)
ObjectsWithScope = NodeDefinition|HyperEdgeDefinition|Loop|VarOrParamDefinition|FunctionDefinition
HierTypes = ObjectsWithScope|VarOrParamDefinition|ExpressionFunctionCall|Path

def _obj_below_loops(obj: GBOMLObject) -> GBOMLObject:
    while isinstance(obj, Loop):
        obj = obj.child
    return obj

def _create_loopscope_from_attrs(scope: 'Scope', element: GBOMLObject, attrs: tuple[str]) -> None:
    for attr in attrs:
        for sub_ast in getattr(element, attr):
            visit_hier(sub_ast, {GBOMLObject, Loop}, {Loop: lambda loop,hier: LoopScope(next((hier_item.semantic.scope for hier_item in reversed(hier[:-1]) if hier_item.semantic.scope is not None), scope), loop)})

def _check_dup_names(ctrs: tuple[Constraint], acts: tuple[Activation], objs: tuple[Objective] = tuple()) -> None:
    return
    def check_dups(t):
        seen = set()
        if dups := [x for x in t if x.name in seen or seen.add(x.name)]:
            raise KeyError(f"{list(map(lambda d: d.meta, dups))}: several {type(dups[0]).__name__} with the same name {set(map(lambda d: d.name, dups))}.")
    
    for a in acts:
        pass
    for t in (ctrs, acts, objs):
        if not t:
            continue
        match _obj_below_loops(t[0]): # TODO all can be under loops (does activation make sense)
            case Constraint() | Objective():
                check_dups(filter(lambda e: e.name is not None, t))
            case Activation():
                pass

def _check_redefinition(scope: 'Scope', meta: Meta, item: str) -> None:
    try:
        ans = scope[item]
    except KeyError:
        pass
    else:
        if isinstance(ans, ParentNodeScope|ChildNodeScope):
            ans = ans.parent
        raise KeyError(f"{meta}: Identifier {item} is already used {'' if not ans else ans.ast.meta}.")


def get_scope_from_hier(hier: list[HierTypes]) -> 'Scope':
    return next(hier_item.semantic.scope for hier_item in reversed(hier) if hier_item.semantic.scope is not None)

def get_parent_from_hier(hier: list[HierTypes], _type: type[HierTypes]) -> Optional[HierTypes]:
    return next((hier_item for hier_item in reversed(hier) if isinstance(hier_item, _type)), None)

def get_scope_after_expr(elem: ExpressionDotCall|ExpressionFunctionCall|PathRoot, scope: 'Scope') -> Optional['Scope']:
    """ Returns the scope after looking for expression 'elem' or None if it is impossible to know (e.g. a().x); Raises an error if cannot find the scope. """

    names = []
    if not isinstance(child := elem, PathRoot):
        if isinstance(child, ExpressionDotCall):
            names.append(child.rhs)
        while isinstance(child := child.lhs, ExpressionDotCall):
            names.append(child.rhs)
        if not isinstance(child, PathRoot):
            return None  # cannot check existence

    try:
        scope = scope[child.name]  # child is sure to be PathRoot
        while names:
            if isinstance(scope, VarOrParamDefScope):
                raise KeyError
            scope = scope[names.pop()]
    except KeyError:
        raise RuntimeError(f"{elem} {elem.meta}: cannot be used in this scope")
    return scope


class OverrideBehavior(Enum):
    ignore = 0
    fail = 1
    overwrite = 2

@dataclass(frozen=True)
class Scope:
    parent: "Scope" = field(repr=False)
    name: str
    path: tuple[str] = field(init=False)
    content: dict[str, "Scope"] = field(init=False, hash=False)

    def __post_init__(self):
        print(f"{type(self)} was INITIALIZED")
        object.__setattr__(self, 'path', self.parent.path + (self.name,))  # needs to use __setattr__() to keep class frozen

    def _add_to_scope(self, ast, wrapper=lambda x: x, whenPresent: OverrideBehavior = OverrideBehavior.fail) -> Optional['Scope']:
        parent = self
        while isinstance(ast, Loop):
            parent = LoopScope(parent, ast)
            ast = ast.child

        if ast.name == 'parent':
            raise KeyError(f"{ast.meta}: Identifier {ast.name} cannot be redefined (reserved keyword).")

        try:
            self[ast.name]
        except KeyError:
            pass
        else:
            if whenPresent == OverrideBehavior.fail:
                raise KeyError(f"{ast.meta}: Identifier {ast.name} is already used {scope.parent.ast.meta if isinstance(scope := self.content[ast.name], ParentNodeScope) else scope.ast.meta} GROS CACAA.")
            elif whenPresent == OverrideBehavior.ignore:
                return None

        self.content[ast.name] = wrapper(create_scope(ast, parent))
        return self.content[ast.name]

    def _add_all_to_scope(self, l, wrapper=lambda x: x, whenPresent: OverrideBehavior = OverrideBehavior.fail) -> list["Scope"]:
        return [y for x in l for y in [self._add_to_scope(x, wrapper, whenPresent)] if y is not None]

    def __getitem__(self, item):
        if item == 'parent':
            return ParentNodeScope(self.parent)
        try:
            return self.content[item]
        except KeyError:
            if isinstance(self, GlobalScope):
                raise

            glob = self.content['global'].parent if 'global' in self.content else None
            try:
                scope = self.parent[item]
            except KeyError:
                pass
            else:
                if isinstance(scope, EmptyScope) or glob is not None and not isinstance(scope, ChildNodeScope) and scope.ast in glob.ast.reserved_defs:
                    return scope
                else:
                    raise

            raise

    def path_to_str(self):
        return '.'.join(self.path)


# singleton
class EmptyScope(Scope):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            object.__setattr__(cls._instance, 'parent', None)
            object.__setattr__(cls._instance, 'name', "")
            object.__setattr__(cls._instance, 'path', tuple())
            object.__setattr__(cls._instance, 'content', {})
        return cls._instance

    def __init__(self):
        pass  # Override to do nothing (and no need for constructor args)

    def __bool__(self):
        return False


@dataclass(frozen=True)
class NamedAstScope(Scope, Generic[T]):
    name: str = field(init=False)
    ast: T

    def __post_init__(self):
        object.__setattr__(self, 'name', self.ast.name)
        super().__post_init__()
        self.ast.semantic.scope = self


@dataclass(frozen=True)
class ParentNodeScope(Scope):
    """ A child can only access the parameters of its parents """
    parent: "NodeScope" = field(repr=False)
    name: str = field(init=False)

    def __post_init__(self):
        object.__setattr__(self, 'name', self.parent.name)
        object.__setattr__(self, 'path', self.parent.path)
        object.__setattr__(self, 'content', self.parent.content)

    def __getitem__(self, item):
        out = super().__getitem__(item)
        if not isinstance(out, ParentNodeScope | ScopedDefinition | ScopedFunctionDefinition | EmptyScope):
            raise KeyError(f"{item} is not accessible")
        return out


@dataclass(frozen=True)
class ChildNodeScope(Scope):
    """ A parent can only access the vars of this child (not directly, but at least in child hyperedges) """
    parent: "NodeScope" = field(repr=False)
    name: str = field(init=False)

    def __post_init__(self):
        object.__setattr__(self, 'name', self.parent.name)
        object.__setattr__(self, 'path', self.parent.path)
        object.__setattr__(self, 'content', self.parent.content)

    def __getitem__(self, item):
        out = super().__getitem__(item)
        if not isinstance(out, ScopedVariableDefinition):
            raise KeyError(f"{item} is not accessible")
        return out


@dataclass(frozen=True)
class LoopScope(Scope):
    name: str = field(init=False, default=None)
    ast: Loop

    def __post_init__(self):
        object.__setattr__(self, 'path', self.parent.path)
        object.__setattr__(self, 'content', self.parent.content)
        self.ast.semantic.scope = self
        if not isinstance(self.ast, ImplicitLoop):
            _check_redefinition(self.parent, self.ast.meta, self.ast.varid)

    def __getitem__(self, item):
        return EmptyScope() if item == self.ast.varid else self.parent[item]


@dataclass(frozen=True)
class NodeScope(NamedAstScope[NodeDefinition]):
    nodes: dict[str, "NodeScope"] = field(init=False, repr=False, hash=False)
    hyperedges: dict[str, "HyperEdgeScope"] = field(init=False, repr=False, hash=False)

    def __post_init__(self):
        object.__setattr__(self, 'content', {})
        super().__post_init__()
        
        parents = [self.parent]
        while not isinstance(parents[-1], GlobalScope):
            parents.append(parents[-1].parent)
        self._add_all_to_scope(parents, ParentNodeScope, OverrideBehavior.ignore)

        self._add_all_to_scope(self.ast.parameters)
        node_scopes = self._add_all_to_scope(self.ast.nodes, ChildNodeScope)
        self._add_all_to_scope(self.ast.variables)

        object.__setattr__(self, 'nodes', {x.parent.name: x.parent for x in node_scopes})
        object.__setattr__(self, 'hyperedges', {h.name: HyperEdgeScope(self, h, list(self.nodes.values())) for h in self.ast.hyperedges})

        _create_loopscope_from_attrs(self, self.ast, ('constraints', 'objectives', 'parameters'))
        _check_dup_names(self.ast.constraints, self.ast.activations, self.ast.objectives)
        _check_redefinition(self, self.ast.meta, self.ast.name)


@dataclass(frozen=True)
class HyperEdgeScope(NamedAstScope[HyperEdgeDefinition]):
    _parent_nodes: tuple[NodeScope]

    def __post_init__(self):
        object.__setattr__(self, 'content', {})
        super().__post_init__()
        self._add_all_to_scope(self.ast.parameters)
        self._add_all_to_scope(self._parent_nodes)

        parents = [self.parent]
        while not isinstance(parents[-1], GlobalScope):
            parents.append(parents[-1].parent)
        self._add_all_to_scope(parents, ParentNodeScope, OverrideBehavior.ignore)

        _create_loopscope_from_attrs(self, self.ast, ('constraints', 'parameters'))
        _check_dup_names(self.ast.constraints, self.ast.activations)
        _check_redefinition(self, self.ast.meta, self.ast.name)


@dataclass(frozen=True)
class VarOrParamDefScope(NamedAstScope[Definition]):
    def __post_init__(self):
        object.__setattr__(self, 'content', self.parent.content)
        super().__post_init__()
        _check_redefinition(self, self.ast.meta, self.ast.name)

@dataclass(frozen=True)
class ScopedDefinition(VarOrParamDefScope):
    pass

@dataclass(frozen=True)
class ScopedFunctionDefinition(VarOrParamDefScope):
    def __post_init__(self):
        super().__post_init__()
        for arg in self.ast.args:
            _check_redefinition(self.parent, self.ast.meta, arg)

    def __getitem__(self, item):
        return EmptyScope() if item in self.ast.args else self.parent[item]

@dataclass(frozen=True)
class ScopedVariableDefinition(VarOrParamDefScope):
    pass


def create_scope(ast_or_scope: NamedGBOMLObject | Scope, parent: Scope) -> Scope:
    match ast_or_scope:
        case NodeDefinition(): return NodeScope(parent, ast_or_scope)
        case FunctionDefinition(): return ScopedFunctionDefinition(parent, ast_or_scope)
        case Definition(): return ScopedDefinition(parent, ast_or_scope)
        case VariableDefinition(): return ScopedVariableDefinition(parent, ast_or_scope)
        case Scope(): return ast_or_scope
        case _: raise RuntimeError(f"Unknown Type {ast_or_scope.__class__}")


@dataclass(frozen=True)
class GlobalScope(Scope):
    name: str = field(init=False, default="global")
    path: tuple[str] = field(init=False, default_factory=tuple)
    parent: Scope = field(init=False, default=None)
    ast: GBOMLGraph = field(repr=False)
    nodes: dict[str, NodeScope] = field(init=False, repr=False, hash=False)
    hyperedges: dict[str, HyperEdgeScope] = field(init=False, repr=False, hash=False)

    def __post_init__(self):
        object.__setattr__(self, 'content', {})
        self._add_all_to_scope(self.ast.global_defs)
        self._add_all_to_scope(self.ast.reserved_defs)
        _create_loopscope_from_attrs(self, self.ast, ('global_defs',))
        object.__setattr__(self, 'nodes', {x.name: x for x in self._add_all_to_scope(self.ast.nodes)})
        object.__setattr__(self, 'hyperedges', {h.name: HyperEdgeScope(self, h, tuple(self.nodes.values())) for h in self.ast.hyperedges})
        self.ast.semantic.scope = self
