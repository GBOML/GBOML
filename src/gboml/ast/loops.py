from dataclasses import dataclass, field
from typing import Optional

from gboml.ast.base import GBOMLObject
from gboml.ast.expressions import BoolExpression, Expression
from gboml.ast.path import VarOrParam, VarOrParamLeaf


@dataclass
class Loop(GBOMLObject):
    varid: str
    start: Expression
    end: Expression
    step: Optional[Expression]
    condition: Optional[BoolExpression]


@dataclass
class ImplicitLoop(Loop):
    varid: str = field(default="t", init=False)
    start: Expression = field(default=0, init=False)
    end: Expression = field(default_factory=lambda: VarOrParam([VarOrParamLeaf("T")]), init=False)
    step: Optional[Expression] = field(default=None, init=False)
    condition: BoolExpression
