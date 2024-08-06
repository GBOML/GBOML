from dataclasses import dataclass, field
from typing import Optional

from gboml.ast.importable import Extends
from gboml.ast.base import NamedGBOMLObject
from gboml.ast.constraints import Constraint, CtrActivation
from gboml.ast.variables import Definition



@dataclass(frozen=True)
class HyperEdgeDefinition(NamedGBOMLObject):
    name: str
    indices: tuple[str]
    import_from: Optional["Extends | HyperEdgeDefinition"] = None
    parameters: tuple[Definition] = field(default=tuple())  # fine to *not* use default_factory as tuple/frozenset are immutable
    constraints: tuple[Constraint] = field(default=tuple())
    activations: tuple[CtrActivation] = field(default=tuple())
    tags: frozenset[str] = field(default=frozenset())
