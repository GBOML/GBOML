from dataclasses import dataclass, field

from gboml.ast import Loop
from gboml.ast.base import GBOMLObject
from gboml.ast.constraints import Constraint
from gboml.ast.path import VarOrParam
from gboml.ast.hyperedges import HyperEdge
from gboml.ast.objectives import Objective
from gboml.ast.variables import Definition, VariableDefinition, ScopeChange


@dataclass
class Node(GBOMLObject):
    pass


@dataclass
class NodeDefinition(Node):
    name: str
    parameters: list[Definition] = field(default_factory=list)
    nodes: list[Node] = field(default_factory=list)
    hyperedges: list[HyperEdge] = field(default_factory=list)
    variables: list[VariableDefinition] = field(default_factory=list)
    constraints: list[Constraint] = field(default_factory=list)
    objectives: list[Objective] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass
class NodeGenerator(Node):
    name: VarOrParam
    loop: Loop
    parameters: list[Definition] = field(default_factory=list)
    nodes: list[Node] = field(default_factory=list)
    hyperedges: list[HyperEdge] = field(default_factory=list)
    variables: list[VariableDefinition] = field(default_factory=list)
    constraints: list[Constraint] = field(default_factory=list)
    objectives: list[Objective] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass
class NodeImport(Node):
    name: str
    imported_name: VarOrParam
    imported_from: str
    scope_changes: list[ScopeChange] = field(default_factory=list)
    redefinitions: list[Definition] = field(default_factory=list)
