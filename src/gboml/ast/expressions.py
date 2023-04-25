from dataclasses import dataclass

from gboml.ast.base import GBOMLObject


@dataclass
class ExpressionObj(GBOMLObject):
    def __eq__(self, obj):
        from gboml.ast.expression_operators import Operator, BoolExpressionComparison
        # first: check type
        if not isinstance(obj, Expression):
            return False
        if self is obj:
            return True
        return BoolExpressionComparison(self, Operator.equal, obj)


Expression = int | float | ExpressionObj

@dataclass
class BoolExpression(GBOMLObject):
    pass
