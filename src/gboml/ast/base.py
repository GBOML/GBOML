from ast import Constant, AST, BinOp, Expression, fix_missing_locations
from dataclasses import dataclass, field
from numpy import arange
from typing import Optional, Any, TypeVar, Callable


def gboml_eval(root: "GBOMLObject|int", local_defs: dict[str, Any]):
    return root if isinstance(root, int) else eval(compile(fix_missing_locations(Expression(to_python_ast(root))), "", mode="eval"), {'$range': arange}, local_defs)

def to_python_ast(expr: 'GBOMLObject|float|str') -> AST:  # TODO see for str
    return expr._to_python_ast() if isinstance(expr, GBOMLObject) else Constant(expr)

def to_balanced_python_ast(operands: tuple['GBOMLObject|float|str'], bin_builder: Callable[[AST, AST], BinOp]) -> BinOp:
    if mid := len(operands) // 2:
        return bin_builder(to_balanced_python_ast(operands[:mid], bin_builder), to_balanced_python_ast(operands[mid:], bin_builder))
    else:
        return to_python_ast(operands[0])

@dataclass
class Meta:
    filename: Optional[str]
    line: Optional[int]
    column: Optional[int]

@dataclass
class Semantic:  # only used in semantic.py; separate class so it is mutable but GBOMLObjects are still frozen
    scope: Optional['Scope'] = field(default=None, kw_only=True)

@dataclass(frozen=True)
class GBOMLObject:
    meta: Optional[Meta] = field(default=None, kw_only=True, repr=False, hash=False, compare=False)
    semantic: Semantic = field(default_factory=Semantic, kw_only=True, repr=False, hash=False, compare=False)

@dataclass(frozen=True)
class NamedGBOMLObject(GBOMLObject):
    name: str


AnyGBOMLObject = TypeVar('AnyGBOMLObject', bound=GBOMLObject)
