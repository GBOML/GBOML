from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from gboml.ast.arrays import Array, Range
from gboml.ast.base import GBOMLObject, NamedGBOMLObject
from gboml.ast.values import Expression
from gboml.ast.path import Path

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
    value: Expression
    tags: set[str] = field(default_factory=set)


@dataclass
class ExpressionDefinition(Definition):
    value: Expression
    tags: set[str] = field(default_factory=set)

@dataclass
class FunctionDefinition(Definition):
    args: list[str]
    value: Expression
    tags: set[str] = field(default_factory=set)

@dataclass
class IndexingParameterDefinition(Definition):
    value: Array | Range | Path

@dataclass
class VariableDefinition(NamedGBOMLObject):
    name: str
    indices: list[Expression]
    scope: VarScope
    type: VarType
    bound_lower: Optional[Expression]
    bound_upper: Optional[Expression]
    import_from: Optional[Path] = None
    tags: set[str] = field(default_factory=set)


@dataclass
class ScopeChange(GBOMLObject):
    name: str
    scope: VarScope