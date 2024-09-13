import typing
from dataclasses import dataclass
from enum import Enum

from gboml.ast.expressions import ExpressionObj, BoolExpressionObj

if typing.TYPE_CHECKING:
    from gboml.ast.values import Expression, PossiblyGeneratedExpression


class Operator(Enum):
    lesser = "<"
    greater = ">"
    lesser_or_equal = "<="
    greater_or_equal = ">="
    equal = "=="
    not_equal = "!="
    concatenation = "|"
    times = "*"
    divide = "/"
    plus = "+"
    minus = "-"
    exponent = "**"
    unary_minus = "u-"
    modulo = "%"
    b_and = "and"
    b_or = "or"
    b_not = "not"


@dataclass(frozen=True)
class ExpressionOp(ExpressionObj):
    operator: Operator
    operands: tuple["Expression"]


@dataclass(frozen=True)
class BoolExpressionOp(BoolExpressionObj):
    operator: Operator
    operands: tuple["Expression"]


@dataclass(frozen=True)
class BoolExpressionComparison(BoolExpressionObj):
    lhs: "Expression"
    operator: Operator
    rhs: "Expression"

    def __bool__(self):
        """ Checks if lhs and rhs are *exactly* the same tree in an eq relation """
        #TODO improve me
        if self.operator == Operator.equal:
            return self.lhs is self.rhs
        return False


@dataclass(frozen=True)
class ExpressionFunctionCall(ExpressionObj):
    lhs: "Expression"
    operands: tuple["PossiblyGeneratedExpression"]


@dataclass(frozen=True)
class ExpressionDotCall(ExpressionObj):
    lhs: "Expression"
    rhs: str


@dataclass(frozen=True)
class ExpressionArrayCall(ExpressionObj):
    lhs: "Expression"
    rhs: "Expression"
