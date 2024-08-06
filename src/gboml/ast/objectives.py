from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from gboml.ast.values import Expression
from gboml.ast.activation import Activation
from gboml.ast.base import GBOMLObject
from gboml.ast.loops import Loop


class ObjType(Enum):
    min = "min"
    max = "max"


@dataclass(frozen=True)
class Objective(GBOMLObject):
    type: ObjType
    name: Optional[str]
    expression: Expression
    tags: frozenset[str] = field(default=frozenset())

@dataclass(frozen=True)
class ObjActivation(Activation):
    pass
