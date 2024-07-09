import typing
from dataclasses import dataclass

from gboml.ast.expressions import ExpressionObj

if typing.TYPE_CHECKING:
    from gboml.ast.rvalue import PossiblyGeneratedExpression


@dataclass
class Function(ExpressionObj):
    name: str
    operands: list["PossiblyGeneratedExpression"]