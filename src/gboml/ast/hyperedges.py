from dataclasses import dataclass, field
from typing import Optional

from gboml.ast.importable import Extends
from gboml.ast.loops import Loop
from gboml.ast.base import NamedGBOMLObject
from gboml.ast.constraints import Constraint, CtrActivation
from gboml.ast.path import VarOrParam
from gboml.ast.variables import Definition


@dataclass
class HyperEdge(NamedGBOMLObject):
    pass


@dataclass
class HyperEdgeDefinition(HyperEdge):
    name: str
    import_from: Optional[Extends] = None
    parameters: list[Definition] = field(default_factory=list)
    constraints: list[Constraint] = field(default_factory=list)
    activations: list[CtrActivation] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)


@dataclass
class HyperEdgeGenerator(HyperEdge):
    name: str
    indices: list[str]
    loop: Loop
    import_from: Optional[Extends] = None
    parameters: list[Definition] = field(default_factory=list)
    constraints: list[Constraint] = field(default_factory=list)
    activations: list[CtrActivation] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)
