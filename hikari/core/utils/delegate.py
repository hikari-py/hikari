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
import inspect
import typing

from hikari.core.utils import assertions, custom_types

_DELEGATE_MEMBERS_FIELD = "__delegate_members__"
_DELEGATE_TYPES_FIELD = "__delegate_type_mapping__"
_T = typing.TypeVar("_T")


class DelegatedProperty:
    """
    Delegating property that takes a magic field name and a delegated member name and redirects
    any accession of the property's value to the attribute named "delegated_member_name" that
    belongs to field "magic_field" on the class it is applied to.

    Note:
        This property is read-only, and only works for instance members.
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


def delegate_to(delegate_type: typing.Type, magic_field: str) -> typing.Callable[[typing.Type[_T]], typing.Type[_T]]:
    """
    Make a decorator that wraps a class to make it delegate any inherited fields from `delegate_type` to attributes of
    the same name on a value stored in a field named the `magic_field`.

    Args:
        delegate_type:
            The class that we wish to delegate to.
        magic_field:
            The field that we will store an instance of the delegated type in.

    Returns:
        a decorator for a class.

    The idea behind this is to allow us to derive one class from another and allow initializing one instance
    from another. This is used largely by the `Member` implementation to allow more than one member to refer to
    the same underlying `User` at once.
    """

    def decorator(cls: typing.Type[_T]) -> typing.Type[_T]:
        assertions.assert_subclasses(cls, delegate_type)
        delegated_members = set()
        # Tuple of tuples, each sub tuple is (magic_field, delegate_type)
        delegated_types = getattr(cls, _DELEGATE_TYPES_FIELD, custom_types.EMPTY_SEQUENCE)

        # We have three valid cases: either the attribute is a class member, in which case it is in `__dict__`, the
        # attribute is defined in the class `__slots__`, in which case it is in `__dict__`, or the field is given
        # a type hint, in which case it is in `__annotations__`. Anything else we lack the ability to detect
        # (e.g. fields only defined once we are in the `__init__`, as it is basically monkey patching at this point if
        # we are not slotted).
        dict_fields = {k for k, v in delegate_type.__dict__.items() if not _is_func(v) and not k.startswith("_")}
        annotation_fields = {*getattr(delegate_type, "__annotations__", custom_types.EMPTY_SEQUENCE)}
        targets = dict_fields | annotation_fields
        for name in targets:
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


def _is_func(func):
    return inspect.isfunction(func) or inspect.ismethod(func)


__all__ = ("delegate_to", "DelegatedProperty")
