from dataclasses import dataclass

from gboml.ast import GBOMLObject


@dataclass
class ImportFile(GBOMLObject):
    filename: str
