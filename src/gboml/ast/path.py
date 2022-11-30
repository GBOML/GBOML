import typing
from dataclasses import dataclass, field

from gboml.ast.base import GBOMLObject
from gboml.ast.expressions import ExpressionObj
if typing.TYPE_CHECKING:
    from gboml.ast.rvalue import RValue


@dataclass
class VarOrParamLeaf(GBOMLObject):
    name: str
    indices: list["RValue"] = field(default_factory=list)


@dataclass
class VarOrParam(ExpressionObj):
    path: list[VarOrParamLeaf]