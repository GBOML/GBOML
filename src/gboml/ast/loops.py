from dataclasses import dataclass
from typing import Optional

from gboml.ast.base import GBOMLObject
from gboml.ast.expressions import BoolExpression, Expression


@dataclass
class Loop(GBOMLObject):
    varid: str
    start: int
    end: int
    step: Optional[int]
    condition: Optional[BoolExpression]


@dataclass
class GeneratedExpression(GBOMLObject):
    expression: Expression
    loop: Loop
