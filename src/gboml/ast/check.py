import types
import typing
from dataclasses import is_dataclass, fields

from gboml.ast import *


class NotOfType(Exception): pass
class InvalidContent(Exception): pass


def _check_type(value, typ):
    if isinstance(typ, str):
        typ = eval(typ)

    if isinstance(typ, typing.ForwardRef):
        typ = eval(typ.__forward_arg__)

    if isinstance(typ, types.GenericAlias) and typ.__origin__ in [list, set]:
        subtyp = typing.get_args(typ)[0]
        if not isinstance(value, typ.__origin__):
            raise NotOfType(f"{value} is not an instance of {typ}")
        for x in value:
            _check_type(x, subtyp)
        return

    if isinstance(typ, types.UnionType) or ("_name" in typ.__dict__ and typ._name == "Optional"):
        for subtyp in typing.get_args(typ):
            try:
                _check_type(value, subtyp)
                return
            except NotOfType as e:
                pass
        raise NotOfType(f"{value} is not an instance of {typ}")

    if typ == typing.Optional[typing.Any]:
        return

    if typ is typing.Any:
        if typ is not None:
            return
        raise NotOfType(f"{value} is not an instance of {typ}")

    if is_dataclass(typ):
        if not isinstance(value, typ):
            raise NotOfType(f"{value} is not an instance of {typ}")
        check(value)
        return

    if not isinstance(value, typ):
        raise NotOfType(f"{value} is not an instance of {typ}")


def check(t: GBOMLObject):
    """ Check that a GBOMLObject is well-formed"""
    try:
        for f in fields(t):
            value = getattr(t, f.name)
            typ = f.type
            _check_type(value, typ)
    except NotOfType as e:
        raise InvalidContent(str(e) + f" in {t}")
