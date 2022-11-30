import typing

if typing.TYPE_CHECKING:
    from gboml.ast.rvalue import RValueWithGen

Array = list["RValueWithGen"]
