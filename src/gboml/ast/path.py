from ast import Load, Name
from dataclasses import dataclass

from gboml.ast.expressions import ExpressionObj
from gboml.ast.expression_operators import ExpressionArrayCall, ExpressionDotCall

@dataclass(frozen=True)
class PathRoot(ExpressionObj):
    name: str

    def _to_python_ast(self):
        return Name(id=self.semantic.scope[self.name].path_to_str(), ctx=Load())


Path = ExpressionArrayCall | ExpressionDotCall | PathRoot
