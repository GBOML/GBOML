import typing
from dataclasses import dataclass, field
from typing import Optional

from gboml.ast.activation import Activation
from gboml.ast.base import GBOMLObject
from gboml.ast.expression_operators import Operator
from gboml.ast.loops import Loop

if typing.TYPE_CHECKING:
    from gboml.ast.rvalue import PossiblyGeneratedExpression, Expression

@dataclass
class Constraint(GBOMLObject):
    name: Optional[str]


@dataclass
class StdConstraint(Constraint):
    lhs: "Expression"
    op: Operator
    rhs: "Expression"
    loop: Optional[Loop] = None
    tags: set[str] = field(default_factory=set)

@dataclass
class FunctionConstraint(Constraint):
    lhs: "Expression"
    operands: list["PossiblyGeneratedExpression"]
    loop: Optional[Loop] = None
    tags: set[str] = field(default_factory=set)


@dataclass
class CtrActivation(Activation):
    pass
