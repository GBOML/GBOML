import typing
from dataclasses import dataclass, field
from typing import Optional

from gboml.ast.activation import Activation
from gboml.ast.base import GBOMLObject
from gboml.ast.expression_operators import Operator
from gboml.ast.expressions import Expression
from gboml.ast.loops import Loop

if typing.TYPE_CHECKING:
    from gboml.ast.rvalue import RValueWithGen

@dataclass
class Constraint(GBOMLObject):
    name: Optional[str]


@dataclass
class StdConstraint(Constraint):
    lhs: Expression
    op: Operator
    rhs: Expression
    loop: Optional[Loop] = None
    tags: set[str] = field(default_factory=set)

@dataclass
class FunctionConstraint(Constraint):
    fname: str
    operands: list["RValueWithGen"]
    loop: Optional[Loop] = None
    tags: set[str] = field(default_factory=set)


@dataclass
class CtrActivation(Activation):
    pass
