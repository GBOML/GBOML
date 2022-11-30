from dataclasses import dataclass
from enum import Enum
from typing import Optional

from gboml.ast.arrays import Array
from gboml.ast.base import GBOMLObject
from gboml.ast.expression_operators import Operator
from gboml.ast.expressions import Expression
from gboml.ast.loops import Loop


class SOSType(Enum):
    SOS1 = "SOS1"
    SOS2 = "SOS2"


@dataclass
class Constraint(GBOMLObject):
    name: Optional[str]


@dataclass
class StdConstraint(Constraint):
    lhs: Expression
    op: Operator
    rhs: Expression
    loop: Optional[Loop]


@dataclass
class SOSConstraint(Constraint):
    type: SOSType
    content: Array
    loop: Optional[Loop]
