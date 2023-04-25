from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from gboml.ast.functions import Function
from gboml.ast.arrays import Array, Range
from gboml.ast.base import GBOMLObject, NamedGBOMLObject
from gboml.ast.path import VarOrParam
from gboml.ast.rvalue import RValue


class VarScope(Enum):
    internal = "internal"
    external = "external"


class VarType(Enum):
    continuous = "continuous"
    integer = "integer"
    binary = "binary"


class DefinitionType(Enum):
    constant = "="
    expression = "<-"


@dataclass
class Definition(NamedGBOMLObject):
    name: str


@dataclass
class ConstantDefinition(Definition):
    value: RValue
    tags: set[str] = field(default_factory=set)


@dataclass
class ExpressionDefinition(Definition):
    value: RValue
    tags: set[str] = field(default_factory=set)

@dataclass
class FunctionDefinition(Definition):
    args: list[str]
    value: RValue
    tags: set[str] = field(default_factory=set)

@dataclass
class IndexingParameterDefinition(Definition):
    value: Function | Array | Range | VarOrParam

@dataclass
class VariableDefinition(NamedGBOMLObject):
    name: str
    indices: list[str]
    scope: VarScope
    type: VarType
    import_from: Optional[VarOrParam] = None
    tags: set[str] = field(default_factory=set)


@dataclass
class ScopeChange(GBOMLObject):
    name: str
    scope: VarScope