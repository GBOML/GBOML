from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Meta:
    filename: Optional[str]
    line: Optional[int]
    column: Optional[int]


@dataclass
class GBOMLObject:
    meta: Optional[Meta] = field(default=None, kw_only=True, repr=False)

@dataclass
class NamedGBOMLObject(GBOMLObject):
    name: str