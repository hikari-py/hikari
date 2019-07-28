#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019
#
# This file is part of Hikari.
#
# Hikari is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hikari is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Hikari. If not, see <https://www.gnu.org/licenses/>.
"""
Implements a basic type delegation system that piggybacks off of the standard 
inheritance system in Python and boasts full dataclass compatibility in the 
process.
"""
import dataclasses
import inspect

from hikari.core.utils import assertions

__all__ = ("delegate_members", "delegate_safe_dataclass")


_DELEGATE_MEMBERS_FIELD = "__delegate_members__"
_DELEGATE_TYPES_FIELD = "__delegate_type_mapping__"


class DelegatedProperty:
    """
    Delegating property that takes a magic field name and a delegated member name and redirects
    any accession of the property's value to the attribute named "delegated_member_name" that
    belongs to field "magic_field" on the class it is applied to.
    """

    def __init__(self, magic_field, delegated_member_name) -> None:
        self.magic_field = magic_field
        self.delegated_member_name = delegated_member_name

    def __get__(self, instance, owner):
        if instance is not None:
            delegated_object = getattr(instance, self.magic_field)
            return getattr(delegated_object, self.delegated_member_name)
        else:
            return self


def delegate_safe_dataclass(decorator=dataclasses.dataclass, **kwargs):
    """
    Dataclass decorator that is compatible with delegate types. This generates a new constructor that
    omits known delegated fields from the signature, thus making it safe to use on delegated classes.

    Args:
        decorator:
            The decorator to apply to the dataclass to initialize it as a dataclass.

    Warning:
        This decorator must be placed AFTER the delegate decorators are placed (so, further down the file)
        otherwise it will produce an incorrect constructor. This is checked when using the decorator.
    """

    def actual_decorator(cls):
        if hasattr(cls, _DELEGATE_MEMBERS_FIELD):
            raise TypeError("This class has already had delegates defined on it. Cannot make a dataclass now.")

        # We don't have an `__annotations__` element if no fields exist, annoyingly.
        annotations = getattr(cls, "__annotations__", ())
        fields = ", ".join(field for field in annotations)
        init = "\n".join(
            [
                f"def __init__(self, {fields}) -> None:",
                *[f"    self.{field} = {field}" for field in annotations],
                # Sue me, who cares if this always ends in pass, it is the simplest way to ensure a body if no fields
                # exist in the class.
                "    pass",
            ]
        )
        locals_ = {}
        exec(init, {}, locals_)  # nosec
        cls.__init__ = locals_["__init__"]
        kwargs["init"] = False
        return decorator(**kwargs)(cls)

    return actual_decorator


def delegate_members(delegate_type, magic_field):
    """
    Make a decorator that wraps a class to make it delegate any inherited fields from `delegate_type` to attributes of
    the same name on a value stored in a field named the `magic_field`.

    Args:
        delegate_type:
            The class that we wish to delegate to.
        magic_field:
            The field that we will store an instance of the delegated type in.

    The idea behind this is to allow us to derive one class from another and allow initializing one instance
    from another. This is used largely by the `Member` implementation to allow more than one member to refer to
    the same underlying `User` at once.

    Warning:
        If making the outer class a dataclass, you must use the :attr:`delegate_safe_dataclass`
        decorator rather than the vanilla :func:`dataclasses.dataclass` one, otherwise it will
        produce an incompatible signature.

        If you are instead initializing the class yourself, it is vital that you do not call `super().__init__`
        and that you define your own constructor that consumes the delegate types. It is recommended to use the
        :attr:`delegate_safe_dataclass` for complex data classes to automate this correctly.
    """

    def decorator(cls):
        assertions.assert_subclasses(cls, delegate_type)
        delegated_members = set()
        # Tuple of tuples, each sub tuple is (magic_field, delegate_type)
        delegated_types = getattr(cls, _DELEGATE_TYPES_FIELD, ())

        # We have three valid cases: either the attribute is a class member, in which case it is in `__dict__`, the
        # attribute is defined in the class `__slots__`, in which case it is in `__dict__`, or the field is given
        # a type hint, in which case it is in `__annotations__`. Anything else we lack the ability to detect
        # (e.g. fields only defined once we are in the `__init__`, as it is basically monkey patching at this point if
        # we are not slotted).
        dict_fields = {k for k, v in delegate_type.__dict__.items()}
        annotation_fields = {*getattr(delegate_type, "__annotations__", ())}
        for name in dict_fields | annotation_fields:
            if name.startswith("_") or _is_func(cls, name):
                continue

            delegate = DelegatedProperty(magic_field, name)
            delegate.__doc__ = f"See :attr:`{delegate_type.__name__}.{name}`."

            setattr(cls, name, delegate)
            delegated_members.add(name)

        # Enable repeating the decorator for multiple delegation.
        delegated_members |= getattr(cls, _DELEGATE_MEMBERS_FIELD, set())
        setattr(cls, _DELEGATE_MEMBERS_FIELD, frozenset(delegated_members))
        setattr(cls, _DELEGATE_TYPES_FIELD, (*delegated_types, (magic_field, delegate_type)))
        return cls

    return decorator


def _is_func(cls, name):
    func = getattr(cls, name, None)
    return inspect.isfunction(func) or inspect.ismethod(func)
