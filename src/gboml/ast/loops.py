import typing
from dataclasses import dataclass, field
from typing import Optional

from gboml.ast.arrays import Range
from gboml.ast.base import GBOMLObject
from gboml.ast.path import Path, PathRoot

if typing.TYPE_CHECKING:
    from gboml.ast.values import Expression


T = typing.TypeVar("T")

@dataclass
class Loop(GBOMLObject, typing.Generic[T]):
    pass


@dataclass
class BaseLoop(Loop):
    """
     The expression

     expr for a in b

     Creates an object with varid=a, on=b, child=expr
    """
    varid: str
    on: "Expression"
    condition: Optional["Expression"]
    child: Loop[T] | T
    loop: Optional[Loop] = field(default=None)  # for nested loops  # TODO, change type


@dataclass
class LikeLoop(Loop):
    varid: str
    on: "Path"
    condition: Optional["Expression"]


@dataclass
class ImplicitLoop(BaseLoop):
    varid: str = field(default="t", init=False)
    on: "Expression" = field(default_factory=lambda: Range(0, PathRoot("T")), init=False)
    condition: "Expression"
