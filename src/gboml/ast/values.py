from dataclasses import dataclass

from gboml.ast.arrays import Array, Range, Dictionary
from gboml.ast.base import GBOMLObject
from gboml.ast.loops import Loop
from gboml.ast.expressions import BoolExpressionObj, ExpressionObj
from gboml.ast.import_file import ImportFile


LeafValue = Array | ImportFile | str | Range | Dictionary | int | float
Expression = BoolExpressionObj | ExpressionObj | LeafValue

@dataclass
class GeneratedExpression(GBOMLObject):
    value: Expression
    loop: Loop


PossiblyGeneratedExpression = Expression | GeneratedExpression
