from dataclasses import dataclass

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
    parameters: list[Definition]
    nodes: list[Node]
    hyperedges: list[HyperEdge]
    variables: list[VariableDefinition]
    constraints: list[Constraint]
    objectives: list[Objective]


@dataclass
class NodeImport(Node):
    name: str
    imported_name: VarOrParam
    imported_from: str
    scope_changes: list[ScopeChange]
    redefinitions: list[Definition]
