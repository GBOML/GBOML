from dataclasses import dataclass, field

from gboml.ast import Loop
from gboml.ast.base import GBOMLObject
from gboml.ast.constraints import Constraint, CtrActivation
from gboml.ast.path import VarOrParam
from gboml.ast.variables import Definition


@dataclass
class HyperEdge(GBOMLObject):
    pass


@dataclass
class HyperEdgeDefinition(HyperEdge):
    name: str
    parameters: list[Definition] = field(default_factory=list)
    constraints: list[Constraint] = field(default_factory=list)
    activations: list[CtrActivation] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass
class HyperEdgeGenerator(HyperEdge):
    name: VarOrParam
    loop: Loop
    parameters: list[Definition] = field(default_factory=list)
    constraints: list[Constraint] = field(default_factory=list)
    activations: list[CtrActivation] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass
class HyperEdgeImport(HyperEdge):
    name: str
    imported_name: VarOrParam
    imported_from: str
    redefinitions: list[Definition]