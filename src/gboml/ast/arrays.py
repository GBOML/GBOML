import typing
from dataclasses import dataclass

from gboml.ast.base import GBOMLObject


if typing.TYPE_CHECKING:
    from gboml.ast.rvalue import Expression, PossiblyGeneratedExpression
    from gboml.ast.loops import Loop


@dataclass
class Array(GBOMLObject):
    content: list["PossiblyGeneratedExpression"]


@dataclass
class DictEntry(GBOMLObject):
    key: "Expression"
    value: "Expression"
    loop: typing.Optional["Loop"] = None


@dataclass
class Dictionary(GBOMLObject):
    content: list[DictEntry]


@dataclass
class Range(GBOMLObject):
    start: "Expression"
    end: "Expression"
    step: typing.Optional["Expression"] = None
