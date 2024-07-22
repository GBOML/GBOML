from dataclasses import dataclass
from typing import Optional

from gboml.ast.base import GBOMLObject
from gboml.ast.path import Path


@dataclass
class Extends(GBOMLObject):
    name: "Path"
    filename: Optional[str]

@dataclass
class Import(GBOMLObject):
    name: "Path"
    filename: Optional[str]
