from dataclasses import dataclass

from gboml.ast.expressions import ExpressionObj
from gboml.ast.expression_operators import ExpressionArrayCall, ExpressionDotCall

@dataclass
class PathRoot(ExpressionObj):
    name: str


Path = ExpressionArrayCall | ExpressionDotCall | PathRoot
