import typing
from dataclasses import dataclass, field
from typing import Optional

from gboml.ast.arrays import Range
from gboml.ast.base import GBOMLObject
from gboml.ast.path import Path, PathRoot

if typing.TYPE_CHECKING:
    from gboml.ast.values import Expression


@dataclass
class Loop(GBOMLObject):
    pass


@dataclass
class BaseLoop(Loop):
    varid: str
    on: "Expression"
    condition: Optional["Expression"]
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


@dataclass
class MultiLoop(Loop):
    sub: list[BaseLoop]
