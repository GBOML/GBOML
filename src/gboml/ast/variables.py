from dataclasses import dataclass
from enum import Enum
from typing import Optional

from gboml.ast.base import GBOMLObject
from gboml.ast.path import VarOrParam
from gboml.ast.rvalue import RValue


class VarScope(Enum):
    internal = "internal"
    external = "external"


class VarType(Enum):
    continuous = "continuous"
    integer = "integer"
    binary = "binary"


@dataclass
class Definition(GBOMLObject):
    name: str
    value: RValue


@dataclass
class VariableDefinition(GBOMLObject):
    scope: VarScope
    type: VarType
    name: VarOrParam
    import_from: Optional[VarOrParam]


@dataclass
class ScopeChange(GBOMLObject):
    var: str
    scope: VarScope