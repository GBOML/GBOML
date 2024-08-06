from dataclasses import dataclass
from gboml.ast.base import GBOMLObject


@dataclass(frozen=True)
class ExpressionObj(GBOMLObject):
    def __eq__(self, obj):
        from gboml.ast.expression_operators import Operator, BoolExpressionComparison
        from gboml.ast.values import Expression
        # first: check type
        if not isinstance(obj, Expression):
            return False
        if self is obj:
            return True
        return BoolExpressionComparison(self, Operator.equal, obj)

@dataclass(frozen=True)
class BoolExpressionObj(GBOMLObject):
    pass
