from dataclasses import dataclass
from typing import Optional

from gboml.ast.variables import Definition
from gboml.ast.base import GBOMLObject
from gboml.ast.hyperedges import HyperEdgeDefinition
from gboml.ast.nodes import NodeDefinition


@dataclass(frozen=True)
class GBOMLGraph(GBOMLObject):
    reserved_defs: tuple[Definition]
    time_horizon: Optional[int]
    global_defs: tuple[Definition]
    nodes: tuple[NodeDefinition]
    hyperedges: tuple[HyperEdgeDefinition]
