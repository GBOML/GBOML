from dataclasses import dataclass, field
from typing import Generic, Optional, TypeVar, TYPE_CHECKING

from gboml.ast.arrays import Range
from gboml.ast.base import GBOMLObject
from gboml.ast.path import Path, PathRoot

if TYPE_CHECKING:
    from gboml.ast.values import Expression


T = TypeVar("T")

@dataclass(frozen=True)
class Loop(GBOMLObject):
    child: "GeneratedObjectsType | Loop" = field(compare=False)
    # child: Loop[T] | T


@dataclass(frozen=True)
class BaseLoop(Loop):
    """
     The expression

     expr for a in b

     Creates an object with varid=a, on=b, child=expr
    """
    varid: str
    on: "Expression"
    condition: Optional["Expression"]


@dataclass(frozen=True)
class LikeLoop(Loop):
    varid: str
    on: "Path"
    condition: Optional["Expression"]


@dataclass(frozen=True)
class ImplicitLoop(BaseLoop):
    varid: str = field(default="t", kw_only=True)
    on: "Expression" = field(default=Range(0, PathRoot("T")), kw_only=True)  # fine to *not* use default_factory as Range is immutable/frozen
    condition: "Expression"
