from dataclasses import dataclass

from gboml.ast.base import GBOMLObject


@dataclass
class ExpressionObj(GBOMLObject):
    pass


Expression = int | float | ExpressionObj

@dataclass
class BoolExpression(GBOMLObject):
    pass



