from dataclasses import dataclass
from typing import Optional

from gboml.ast.variables import Definition
from gboml.ast.base import GBOMLObject
from gboml.ast.hyperedges import HyperEdge
from gboml.ast.nodes import Node


@dataclass
class GBOMLGraph(GBOMLObject):
    time_horizon: Optional[int]
    global_defs: list[Definition]
    nodes: list[Node]
    hyperedges: list[HyperEdge]