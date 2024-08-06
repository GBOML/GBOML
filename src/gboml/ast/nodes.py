from dataclasses import dataclass, field
from typing import Optional

from gboml.ast.activation import Activation
from gboml.ast.base import NamedGBOMLObject
from gboml.ast.constraints import Constraint
from gboml.ast.importable import Extends
from gboml.ast.hyperedges import HyperEdgeDefinition
from gboml.ast.objectives import Objective
from gboml.ast.variables import Definition, VariableDefinition, ScopeChange


@dataclass(frozen=True)
class NodeDefinition(NamedGBOMLObject):
    name: str
    indices: tuple[str]
    import_from: Optional["Extends | NodeDefinition"] = None
    parameters: tuple[Definition] = field(default=tuple())  # fine to *not* use default_factory as tuple/frozenset are immutable
    nodes: tuple["NodeDefinition"] = field(default=tuple())
    hyperedges: tuple[HyperEdgeDefinition] = field(default=tuple())
    variables: tuple[VariableDefinition | ScopeChange] = field(default=tuple())
    constraints: tuple[Constraint] = field(default=tuple())
    objectives: tuple[Objective] = field(default=tuple())
    activations: tuple[Activation] = field(default=tuple())
    tags: frozenset[str] = field(default=frozenset())
