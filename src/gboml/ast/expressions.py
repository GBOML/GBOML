from dataclasses import dataclass, field

from gboml.ast.base import GBOMLObject


@dataclass
class ExpressionObj(GBOMLObject):
    pass


Expression = int | float | ExpressionObj
Array = list["GeneratedExpression | Expression | Array | str"]


@dataclass
class BoolExpression(GBOMLObject):
    pass


@dataclass
class VarOrParamLeaf(GBOMLObject):
    name: str
    indices: list[Expression] = field(default_factory=list)

@dataclass
class VarOrParam(ExpressionObj):
    path: list[VarOrParamLeaf]
