import typing
from dataclasses import dataclass

from gboml.ast.base import GBOMLObject


if typing.TYPE_CHECKING:
    from gboml.ast.values import Expression, PossiblyGeneratedExpression
    from gboml.ast.loops import Loop


@dataclass(frozen=True)
class Array(GBOMLObject):
    content: tuple["PossiblyGeneratedExpression"]


@dataclass(frozen=True)
class DictEntry(GBOMLObject):
    key: "Expression"
    value: "Expression"


@dataclass(frozen=True)
class Dictionary(GBOMLObject):
    content: tuple[DictEntry]


@dataclass(frozen=True)
class Range(GBOMLObject):
    start: "Expression"
    end: "Expression"
    step: typing.Optional["Expression"] = None
