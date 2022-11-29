from dataclasses import dataclass
from enum import Enum

from gboml.ast.expressions import ExpressionObj, Expression, Array, BoolExpression
from gboml.ast.loops import GeneratedExpression


class Operator(Enum):
    lesser = "<"
    greater = ">"
    lesser_or_equal = "<="
    greater_or_equal = ">="
    equal = "=="
    not_equal = "!="
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


@dataclass
class ExpressionOp(ExpressionObj):
    operator: Operator
    operands: list[Expression]

@dataclass
class Function(ExpressionObj):
    name: str
    operands: list[GeneratedExpression | Expression | Array | str]

@dataclass
class BoolExpressionOp(BoolExpression):
    operator: Operator
    operands: list[BoolExpression]

@dataclass
class BoolExpressionComparison(BoolExpression):
    lhs: Expression
    operator: Operator
    rhs: Expression
