import dataclasses
import inspect
import types
import typing
from enum import Enum
from functools import partial

from gboml.ast import *


def _recursive_class_list_children(cls):
    yield cls
    for cls2 in cls.__subclasses__():
        yield from _recursive_class_list_children(cls2)

def _recursive_class_list_parents(cls):
    out = [cls]
    while True:
        assert len(out[-1].__bases__) == 1  # otherwise we might need a toposort...
        if out[-1].__bases__[0] == object:
            break
        out.append(out[-1].__bases__[0])
    return out


excluded_types = {
    typing.Optional[Meta],
    str, int, float,
    list[str],
    typing.Optional[str],
    types.NoneType
}


def _effective_types(typ):
    """
        Lists GBOMLObject-subclasses "inside" other types, such as Optional, Union or list.
    """
    if isinstance(typ, str):
        typ = eval(typ)
    if isinstance(typ, typing.ForwardRef):
        typ = eval(typ.__forward_arg__)
    if typ in excluded_types or (inspect.isclass(typ) and issubclass(typ, Enum)):
        return
    if isinstance(typ, types.GenericAlias) and typ.__origin__ in [list, set]:
        yield from _effective_types(typing.get_args(typ)[0])
        return
    if typing.get_origin(typ) == typing.Union or isinstance(typ, types.UnionType) or ("_name" in typ.__dict__ and typ._name == "Optional"):
        for subtyp in typing.get_args(typ):
            yield from _effective_types(subtyp)
        return
    yield typ


def _compute_types_inside():
    """ GBOMLObject-subclasses used by given GBOMLObject-subclasses, recursively """
    types_inside = {x: set() for x in all_gbomlobjects}
    for cls in all_gbomlobjects:
        for field in dataclasses.fields(cls):
            for typ in _effective_types(field.type):
                types_inside[cls].add(typ)
        for cls2 in cls.__bases__:
            if cls2 in types_inside:
                types_inside[cls2] |= types_inside[cls]
                types_inside[cls2].add(cls)

    modified = True
    while modified:
        modified = False
        for cls in types_inside:
            for cls2 in list(types_inside[cls]):
                for cls3 in types_inside[cls2]:
                    if cls3 not in types_inside[cls]:
                        types_inside[cls] |= {cls3}
                        types_inside[cls] |= types_inside[cls3]
                        modified = True
    return types_inside


def _compute_paths_to():
    """ path_to[x][y] gives the set of fields in class y that can lead to a subclass x """
    paths_to = {x: {y: set() for y in all_gbomlobjects} for x in all_gbomlobjects}
    for cls in leaf_gbomlobjects:
        for field in dataclasses.fields(cls):
            in_types = {a for b in _effective_types(field.type) for a in types_inside[b]} | set(_effective_types(field.type))
            for cls2 in in_types:
                paths_to[cls2][cls].add(field.name)
    return paths_to


""" All descendants of GBOMLObject"""
all_gbomlobjects: set[typing.Type[GBOMLObject]] = set(_recursive_class_list_children(GBOMLObject))
""" Classes that have no children (i.e. the ones that are actually used)"""
leaf_gbomlobjects: set[typing.Type[GBOMLObject]] = {cls for cls in all_gbomlobjects if len(cls.__subclasses__()) == 0}
""" GBOMLObject-subclasses used by given GBOMLObject-subclasses, recursively """
types_inside = _compute_types_inside()
""" path_to[x][y] gives the set of fields in class y that can lead to a subclass x """
paths_to = _compute_paths_to()
""" all parents of class cls, including itself, from child to parent """
family_list = {x: _recursive_class_list_parents(x) for x in all_gbomlobjects}

# note: this whole thing above runs each time GBOML is loaded in memory,
#       and it takes ~20ms. We probably shouldn't care.


def _modify_list(l, by):
    # we do not copy l if it is not modified
    copied = False

    for i in range(len(l)):
        cur = l[i]
        out = modify(l[i], by)
        if out is not cur:
            # first copy l if we need to modify it
            if copied is False:
                l = list(l)
                copied = True
            l[i] = out

    return l


def _modify_gbomlobject(obj, by):
    # if we now what to do with the current object, let's do it
    for x in family_list[obj.__class__]:
        if x in by:
            return by[x](obj)

    # and now the hard part
    interesting_fields = set()
    for by_type in by:
        interesting_fields |= paths_to[by_type][obj.__class__]
    modified = {}
    for field_name in interesting_fields:
        cur = getattr(obj, field_name)
        out = modify(cur, by)
        if out is not cur:
            modified[field_name] = out
    if len(modified):
        return dataclasses.replace(obj, **modified)
    return obj


def modify(element: typing.Any, by: dict[typing.Type[GBOMLObject], typing.Callable[[GBOMLObject], GBOMLObject]]):
    """
        Recursively modifies a GBOMLGraph tree (or any part of it) according to rules set in the dict `by`.
        `by` entries should be in the form `(cls: fun)`, where cls is a class derivating from GBOMLObject and
        fun a callable function that takes as input the object to modify and returns its new value. `fun` will
        be called on all elements that derivates from class `fun`. If multiple `cls` are valid, the class
        that is the nearest from the object is chosen.
    """
    match element:
        case GBOMLObject(): return _modify_gbomlobject(element, by)
        case list(): return _modify_list(element, by)
        case int() | str() | None: return element
        case other: raise RuntimeError(f"Unknown type {other.__class__}")


def visit(element: typing.Any, call: dict[typing.Type[GBOMLObject], typing.Callable[[GBOMLObject], None]]):
    """
        Recursively visit a GBOMLGraph tree (or any part of it), calling functions in the dict `call` each time it
        sees an object of the right type.
        `call` entries should be in the form `(cls: fun)`, where `cls` is a class derivating from GBOMLObject and
        `fun` a callable function that takes as input the object being visited that is an instance of class `cls`.
        If multiple `cls` are valid, the class that is the nearest from the object is chosen.
    """
    def _(f, v):
        f(v)
        return v
    return modify(element, {x: partial(_, y) for x, y in call.items()})
