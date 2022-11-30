from dataclasses import dataclass

from gboml.ast.arrays import Array, Range
from gboml.ast.base import GBOMLObject
from gboml.ast.loops import Loop
from gboml.ast.expressions import Expression
from gboml.ast.import_file import ImportFile

RValue = Expression | Array | ImportFile | str | Range


@dataclass
class GeneratedRValue(GBOMLObject):
    value: RValue
    loop: Loop


RValueWithGen = RValue | GeneratedRValue
