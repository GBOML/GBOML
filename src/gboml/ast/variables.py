from dataclasses import dataclass
from enum import Enum
from typing import Optional

from gboml.ast.base import GBOMLObject
from gboml.ast.expressions import Expression, Array, VarOrParam


class VarScope(Enum):
    internal = "internal"
    external = "external"


class VarType(Enum):
    continuous = "continuous"
    integer = "integer"
    binary = "binary"


@dataclass
class Import(GBOMLObject):
    filename: str


@dataclass
class Definition(GBOMLObject):
    name: str
    value: Expression | Array | Import | str


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