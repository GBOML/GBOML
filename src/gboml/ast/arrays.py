import typing
from dataclasses import dataclass

from gboml.ast.base import GBOMLObject
from gboml.ast.expressions import Expression

if typing.TYPE_CHECKING:
    from gboml.ast.rvalue import RValueWithGen, RValue
    from gboml.ast.loops import Loop


@dataclass
class Array(GBOMLObject):
    content: list["RValueWithGen"]


@dataclass
class DictEntry(GBOMLObject):
    key: "RValue"
    value: "RValue"
    loop: typing.Optional["Loop"] = None


@dataclass
class Dictionary(GBOMLObject):
    content: list[DictEntry]


@dataclass
class Range(GBOMLObject):
    start: Expression
    end: Expression
    step: typing.Optional[Expression] = None
