from dataclasses import dataclass

from gboml.ast.base import GBOMLObject


@dataclass(frozen=True)
class ImportFile(GBOMLObject):
    filename: str
