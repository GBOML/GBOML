from dataclasses import dataclass

from gboml.ast.expressions import ExpressionObj
from gboml.ast.rvalue import RValueWithGen


@dataclass
class Function(ExpressionObj):
    name: str
    operands: list[RValueWithGen]