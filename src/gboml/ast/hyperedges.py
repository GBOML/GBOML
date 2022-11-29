from dataclasses import dataclass

from gboml.ast.base import GBOMLObject
from gboml.ast.constraints import Constraint
from gboml.ast.expressions import VarOrParam
from gboml.ast.variables import Definition


@dataclass
class HyperEdge(GBOMLObject):
    pass


@dataclass
class HyperEdgeDefinition(HyperEdge):
    name: str
    parameters: list[Definition]
    constraints: list[Constraint]


@dataclass
class HyperEdgeImport(HyperEdge):
    name: str
    imported_name: VarOrParam
    imported_from: str
    redefinitions: list[Definition]