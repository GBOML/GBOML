import typing
from dataclasses import dataclass, field
from typing import Optional

from gboml.ast.activation import Activation
from gboml.ast.base import GBOMLObject
from gboml.ast.expression_operators import Operator
from gboml.ast.loops import Loop

if typing.TYPE_CHECKING:
    from gboml.ast.values import PossiblyGeneratedExpression, Expression

@dataclass(frozen=True)
class Constraint(GBOMLObject):
    name: Optional[str]


@dataclass(frozen=True)
class StdConstraint(Constraint):
    lhs: "Expression"
    op: Operator
    rhs: "Expression"
    tags: frozenset[str] = field(default=frozenset())

@dataclass(frozen=True)
class FunctionConstraint(Constraint):
    lhs: str
    operands: tuple["PossiblyGeneratedExpression"]
    tags: frozenset[str] = field(default=frozenset())


@dataclass(frozen=True)
class CtrActivation(Activation):
    pass
