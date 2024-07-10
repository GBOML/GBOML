from dataclasses import dataclass
from enum import Enum
from typing import Optional

from gboml.ast.values import Expression
from gboml.ast.base import GBOMLObject


class ActivationType(Enum):
    activate = "activate"
    deactivate = "deactivate"


@dataclass
class Activation(GBOMLObject):
    type: ActivationType
    what: list[str]
    condition: Optional[Expression]