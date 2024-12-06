import ast
import typing
from dataclasses import dataclass

from gboml.ast.base import GBOMLObject, to_python_ast


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

    def _to_python_ast(self):
        return ast.Call(func=ast.Name(id='$range', ctx=ast.Load()), args=
            [to_python_ast(self.start), ast.BinOp(left=to_python_ast(self.end), op=ast.Add(), right=ast.Constant(1)), ast.Constant(1) if self.step is None else to_python_ast(self.step)]
        )
