from dataclasses import dataclass, field
from typing import Optional

from gboml.ast.functions import Function
from gboml.ast.arrays import Array, Range
from gboml.ast.base import GBOMLObject
from gboml.ast.expressions import BoolExpression
from gboml.ast.path import VarOrParam, VarOrParamLeaf

Iterable = Function | Array | Range | VarOrParam

@dataclass
class Loop(GBOMLObject):
    pass


@dataclass
class BaseLoop(Loop):
    varid: str
    on: Iterable
    condition: Optional[BoolExpression]


@dataclass
class ImplicitLoop(BaseLoop):
    varid: str = field(default="t", init=False)
    on: Iterable = field(default_factory=lambda: Range(0, VarOrParam([VarOrParamLeaf("T")])), init=False)
    condition: BoolExpression


@dataclass
class MultiLoop(Loop):
    sub: list[BaseLoop]
