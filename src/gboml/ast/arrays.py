import typing
from dataclasses import dataclass

from gboml.ast.base import GBOMLObject
from gboml.ast.expressions import Expression

if typing.TYPE_CHECKING:
    from gboml.ast.rvalue import RValueWithGen

Array = list["RValueWithGen"]

@dataclass
class Range(GBOMLObject):
    start: Expression
    end: Expression
    step: typing.Optional[Expression] = None
