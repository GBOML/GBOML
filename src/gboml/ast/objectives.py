from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from gboml.ast.activation import Activation
from gboml.ast.base import GBOMLObject
from gboml.ast.expressions import Expression
from gboml.ast.loops import Loop


class ObjType(Enum):
    min = "min"
    max = "max"


@dataclass
class Objective(GBOMLObject):
    type: ObjType
    name: Optional[str]
    expression: Expression
    loop: Optional[Loop] = None
    tags: list[str] = field(default_factory=list)

@dataclass
class ObjActivation(Activation):
    pass