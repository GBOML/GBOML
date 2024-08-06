from dataclasses import dataclass, field
from typing import Optional, Any, TypeVar


@dataclass
class Meta:
    filename: Optional[str]
    line: Optional[int]
    column: Optional[int]

@dataclass
class Semantic:  # only used in semantic.py; separate class so it is mutable but GBOMLObjects are still frozen
    scope: Optional['Scope'] = field(default=None, kw_only=True)

@dataclass(frozen=True)
class GBOMLObject:
    meta: Optional[Meta] = field(default=None, kw_only=True, repr=False, hash=False, compare=False)
    semantic: Semantic = field(default_factory=Semantic, kw_only=True, repr=False, hash=False, compare=False)

@dataclass(frozen=True)
class NamedGBOMLObject(GBOMLObject):
    name: str


AnyGBOMLObject = TypeVar('AnyGBOMLObject', bound=GBOMLObject)
