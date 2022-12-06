from dataclasses import dataclass
from typing import Optional

from gboml.ast.base import GBOMLObject
from gboml.ast.variables import VarOrParam


@dataclass
class Extends(GBOMLObject):
    name: VarOrParam
    filename: Optional[str]
