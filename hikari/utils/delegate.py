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
Metaclass that allows making a class that delegates fields, properties and methods to named delegate class instances.
This allows making one class implement another without having to subclass it, which enables features such as Member
objects to have several instances that refer to the same object while only physically storing the user once in memory.
"""
from __future__ import annotations

import typing

__all__ = ("DelegatedMeta",)

import asyncio
import functools
import inspect


class DelegatedMeta(type):
    """
    Defines a metaclass for classes that wish to implement one or more other classes via delegation rather than
    inheritance.

    What does this mean...exactly?

    Suppose you have your `User` object. That represents a user floating around in Discord space. Discord introduces
    a second abstraction called a `Member`. This is a specialisation of a `User` which has attributes binding it to
    a specific guild. Seems simple enough.

    Using inheritance, we would need to define our `Member` class as deriving from `User`, and add the extra attributes
    we care about. This is fine for the most part, the only problem is, lets assume we have my User cached already,
    and then we have 15 guilds I share with my bot. Right, that is 15 members that share all the same attributes
    that my User does, so I store stuff like my username and ID 16 times rather than once.

    Delegation works around this by replacing inheritance with a system where the Member simply decorates a User and
    then stores that User as a single field. Each field and method a User has is defined in Member as a property or
    function that simply calls the corresponding item in the User class. Thus, we can implement a User but only
    store it physically once. Because of how Python's GC works, it is perfectly safe to replace the User in the bot's
    state without rebuilding any Members that use it. The User will simply deallocate once all Members that refer to it
    stop existing.

    Example:
        >>> import dataclasses

        >>> @dataclasses.dataclass
        ... class Base:
        ...     a: int
        ...     b: float

        >>> class Delegate(metaclass=DelegatedMeta, deletage_to=(Base, "_base")):
        ...     __slots__ = ("_base", )
        ...
        ...     def __init__(self, base):
        ...         self._base = base

        >>> base = Base(1, 2.3)
        >>> delegate = Delegate(base)
        >>> base.b
        2.3
        >>> delegate.b
        2.3
        >>> base.b = 4.5
        >>> delegate.b
        4.5

    The delegation process is performed on class initialization, meaning once defined once, there is almost zero
    overhead other than one more function call per attribute access; memory overhead is simply one field per instance.

    Note:
        This currently supports slotted elements, delegating by inspecting type annotations, delegating properties,
        delegating methods, coroutine methods, class methods, class coroutine methods, static methods, and static
        coroutine methods.

        Only elements that do not start with an underscore will be delegated.

    Note:
        Subclassing delegate types is experimental currently. You do so at your own risk :-)

    Warning:
        You cannot currently call `isinstance` or `issubclass` on the delegate and the thing it delegates to and
        expect a valid result.
    """
    __delegates__: typing.List[typing.Tuple[DelegatedMeta, str]]

    @classmethod
    def __init_subclass__(mcs, **kwargs):
        """
        Aid usage by preventing explicit subclassing, as we probably never need to do that...
        """
        raise TypeError("This is a delegation metaclass. Perhaps you meant to use `class X(metaclass=DelegatedMeta)`?")

    @classmethod
    def __prepare__(mcs, name, bases, **kwargs):
        """
        Initialize a base namespace for the new class.

        Args:
            name:
                The new class.
            bases:
                The bases of the class
            **kwargs:
                Keyword arguments passed to the initialization of the class.

        Returns:
            A mapping of the base namespace for the class.
        """
        try:
            delegate_to = kwargs.pop("delegate_to")
        except KeyError as e:
            # If this is true, don't worry, we are just subclassing an existing delegate.
            namespaces = {}
            for base in bases:
                if hasattr(base, "__delegates__"):
                    namespaces.update(base.__prepare__(name, [], delegate_to=base.__delegates__))

            if not namespaces:
                raise AttributeError(e) from None
            else:
                return namespaces

        # Ensure it is a list of tuple pairs
        if not isinstance(delegate_to, list) or not all(isinstance(d, tuple) and len(d) == 2 for d in delegate_to):
            if isinstance(delegate_to, tuple) and len(delegate_to) == 2:
                delegate_to = [delegate_to]
            else:
                raise TypeError("The delegate_to argument must be a DelegateTo instance or list of DelegateTo items.")

        namespace = {"__delegates__": []}

        for delegate_to_type, delegate_to_field in delegate_to:
            fields = {}

            # Collect slots first, in case the user forgot to add type hints. We then overwrite them with
            # the type hints we find if they overlap, thus giving more detailed info where possible without adding
            # a concrete constraint on using type hints in slotted classes.
            for slot in getattr(delegate_to_type, '__slots__', []):
                if not slot.startswith('_'):
                    fields[slot] = object

            # Collect type hints, potentially overwriting the slots we found if possible.
            for k, v in getattr(delegate_to_type, '__annotations__', {}).items():
                if not k.startswith('_'):
                    fields[k] = v

            # For each field candidate, delegate it with a property.
            for d_field_name, d_field_type in fields.items():
                delegate = mcs._delegation_attr(delegate_to_field, d_field_name)
                namespace[d_field_name] = delegate

            # For each property candidate, delegate it with a property if it is not private.
            for d_property_name, d_property in inspect.getmembers(delegate_to_type, inspect.isdatadescriptor):
                if not d_property_name.startswith("_"):
                    delegate = mcs._delegation_attr(delegate_to_field, d_property_name)
                    namespace[d_property_name] = delegate

            # For each callable candidate, delegate it with a decorator callable if it is not private
            for d_method_name, d_method in inspect.getmembers(delegate_to_type, mcs._is_method):
                if not d_method_name.startswith("_"):
                    delegate = mcs._delegation_callable(delegate_to_field, d_method_name, d_method)
                    namespace[d_method_name] = delegate

            namespace["__delegates__"].append((delegate_to_type, delegate_to_field))

        return namespace

    @staticmethod
    def __new__(mcs, name, bases, attrs, **kwargs):
        # This is needed to ensure a correct signature, as by default we don't allow passing kwargs about.
        cls: DelegatedMeta = super().__new__(mcs, name, bases, attrs)
        return cls

    @staticmethod
    def _delegation_attr(backing_field: str, target_field: str):
        """
        Creates a delegation property that looks for the given backing_field on the class applied to, and then
        returns the value of the field named target_field on the backing_field found.

        Args:
            backing_field:
                field on delegating type to delegate to.
            target_field:
                the name of the field we are attempting to delegate control to on the backing_field's value.

        Returns:
            A read-only property.
        """
        return property(lambda self: getattr(getattr(self, backing_field), target_field))

    @staticmethod
    def _delegation_callable(backing_field: str, target_method: str, wraps):
        """
        Creates a delegation callable that looks for the given backing_field on the class applied to, and then
        returns the result of calling the field named target_field on the backing_field found.

        Args:
            backing_field:
                field on delegating type to delegate to.
            target_method:
                the method name we are considering.
            wraps:
                the object to wrap.

        Returns:
            A function.
        """
        if asyncio.iscoroutinefunction(wraps):
            async def delegate_method(self, *args, **kwargs):
                # noinspection PyCallingNonCallable
                return await getattr(getattr(self, backing_field), target_method)(*args, **kwargs)
        else:
            def delegate_method(self, *args, **kwargs):
                # noinspection PyCallingNonCallable
                return getattr(getattr(self, backing_field), target_method)(*args, **kwargs)

        return functools.wraps(wraps)(delegate_method)

    @staticmethod
    def _is_method(obj):
        return callable(obj) or inspect.ismethod(obj) or isinstance(obj, (staticmethod, classmethod))
