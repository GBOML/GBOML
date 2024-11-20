from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from gboml.ast.arrays import Array, Range
from gboml.ast.base import GBOMLObject, NamedGBOMLObject, to_python_ast
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


@dataclass(frozen=True)
class Definition(NamedGBOMLObject):
    name: str

    def _to_python_ast(self):
        return to_python_ast(self.value)

@dataclass(frozen=True)
class ConstantDefinition(Definition):
    value: Expression
    tags: frozenset[str] = field(default=frozenset())

@dataclass(frozen=True)
class ExpressionDefinition(Definition):
    value: Expression
    tags: frozenset[str] = field(default=frozenset())

@dataclass(frozen=True)
class FunctionDefinition(Definition):
    args: tuple[str]
    value: Expression
    tags: frozenset[str] = field(default=frozenset())

@dataclass(frozen=True)
class FunctionConstraintDefinition(Definition):
    args: tuple[str]
    value: Expression
    tags: frozenset[str] = field(default=frozenset())

@dataclass(frozen=True)
class IndexingParameterDefinition(Definition):
    value: Expression


@dataclass(frozen=True)
class VariableDefinition(NamedGBOMLObject):
    name: str
    indices: tuple[Expression]
    scope: VarScope
    type: VarType
    bound_lower: Optional[Expression]
    bound_upper: Optional[Expression]
    import_from: Optional[Path] = None
    tags: frozenset[str] = field(default=frozenset())


@dataclass(frozen=True)
class ScopeChange(GBOMLObject):
    name: str
    scope: VarScope
