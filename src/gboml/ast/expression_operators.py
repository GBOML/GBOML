from dataclasses import dataclass
from enum import Enum

from gboml.ast.expressions import ExpressionObj, Expression, BoolExpression


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
class BoolExpressionOp(BoolExpression):
    operator: Operator
    operands: list[BoolExpression]


@dataclass
class BoolExpressionComparison(BoolExpression):
    lhs: Expression
    operator: Operator
    rhs: Expression

    def __bool__(self):
        """ Checks if lhs and rhs are *exactly* the same tree in an eq relation """
        #TODO improve me
        if self.operator == Operator.equal:
            return self.lhs is self.rhs
        return False


@dataclass
class ExpressionUseGenScope(ExpressionObj):
    """ This reserved expression indicates that the child must be evaluated using the scope of the
        generator (in a node/edge generator), that is the scope of the parent + the loop of the generator.
    """
    child: Expression
