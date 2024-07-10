from dataclasses import dataclass

from gboml.ast.base import GBOMLObject


@dataclass
class ImportFile(GBOMLObject):
    filename: str
