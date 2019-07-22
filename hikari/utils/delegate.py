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

"""
__all__ = ("delegate_members", "delegate_safe_dataclass")

import asyncio
import dataclasses
import functools
import inspect

from hikari.utils import assertions


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
        delegated_object = getattr(instance if instance is not None else owner, self.magic_field)
        return getattr(delegated_object, self.delegated_member_name)


def delegate_safe_dataclass(**kwargs):
    """
    Dataclass decorator that is compatible with delegate types. This generates a new constructor that
    omits known delegated fields from the signature, thus making it safe to use on delegated classes.

    Warning:
        This decorator must be placed BEFORE the delegate decorators are placed (so, further up the file)
        otherwise it will produce an incorrect constructor.
    """
    kwargs["init"] = False
    dataclass = dataclasses.dataclass(**kwargs)

    def decorator(cls):
        # Slots also prevent using special cases of field for now which would make this exponentially more complex.
        assertions.assert_is_slotted(cls)
        cls = dataclass(cls)
        fields = dataclasses.fields(cls)
        non_delegated_field_names = set(field.name for field in fields) - cls.__delegated_members__

        init_function = (
            "def __init__(self, " +
            ", ".join(name for name in non_delegated_field_names) +
            ") -> None:\n"
        )

        if non_delegated_field_names:
            for name in non_delegated_field_names:
                init_function += f"    self.{name} = {name}\n"
        else:
            init_function += "    pass\n"

        globals_ = {}
        locals_ = {}
        exec(init_function, globals_, locals_)  # nosec
        init = locals_["__init__"]
        cls.__init__ = init
        return cls

    return decorator


def delegate_members(delegate_type, _magic_field):
    """
    Make a decorator that wraps a class to make it delegate any inherited fields or methods from
    `delegate_type` to attributes of the same name on a value stored in a field named the `_magic_field`.
    """
    def decorator(cls):
        assertions.assert_is_slotted(cls)
        assertions.assert_subclasses(cls, delegate_type)
        delegated_members = set()
        for name, value in delegate_type.__dict__.items():
            if name.startswith('_'):
                continue
            if inspect.isfunction(value) or isinstance(value, classmethod):
                if asyncio.iscoroutinefunction(value):
                    async def delegate(self, *args, **kwargs):
                        delegated_to = getattr(self, _magic_field)
                        return await getattr(delegated_to, name)(*args, **kwargs)
                else:
                    def delegate(self, *args, **kwargs):
                        delegated_to = getattr(self, _magic_field)
                        return getattr(delegated_to, name)(*args, **kwargs)

                delegate = functools.wraps(delegate)
            else:
                delegate = DelegatedProperty(_magic_field, name)
                delegate.__doc__ = f"See :attr:`{delegate_type.__name__}.{name}`."

            setattr(cls, name, delegate)
            delegated_members.add(name)

        # Enable repeating the decorator for multiple delegation.
        delegated_members |= getattr(cls, "__delegated_members__", set())
        setattr(cls, "__delegated_members__", frozenset(delegated_members))
        return cls
    return decorator
