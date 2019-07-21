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
__all__ = ("DelegatedMeta",)

import asyncio
import functools
import inspect


class DelegatedMeta(type):
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
            raise AttributeError(e) from None

        # Ensure it is a list of tuple pairs
        if not isinstance(delegate_to, list) or not all(isinstance(d, tuple) and len(d) == 2 for d in delegate_to):
            if isinstance(delegate_to, tuple) and len(delegate_to) == 2:
                delegate_to = [delegate_to]
            else:
                raise TypeError("The delegate_to argument must be a DelegateTo instance or list of DelegateTo items.")

        type_annotations = {}
        namespace = {"__annotations__": type_annotations}

        for delegate_to_type, delegate_to_field in delegate_to:
            # Add type hint.
            type_annotations[delegate_to_field] = delegate_to_type
            private_prefix = f'_{delegate_to_type.__name__}__'

            fields = {}

            # Collect slots first, in case the user forgot to add type hints. We then overwrite them with
            # the type hints we find if they overlap, thus giving more detailed info where possible without adding
            # a concrete constraint on using type hints in slotted classes.
            for slot in getattr(delegate_to_type, '__slots__', []):
                if not slot.startswith('__'):
                    fields[slot] = object

            # Collect type hints, potentially overwriting the slots we found if possible.
            for k, v in getattr(delegate_to_type, '__annotations__', {}).items():
                fields[k] = v

            # For each field candidate, delegate it with a property.
            for d_field_name, d_field_type in fields.items():
                type_annotations[d_field_name] = d_field_type
                delegate = mcs._delegation_attr(delegate_to_field, d_field_name)
                namespace[d_field_name] = delegate

            # For each property candidate, delegate it with a property if it is not private.
            for d_property_name, d_property in inspect.getmembers(delegate_to_type, inspect.isdatadescriptor):
                if not d_property_name.startswith(private_prefix):
                    type_annotations[d_property_name] = d_property
                    delegate = mcs._delegation_attr(delegate_to_field, d_property_name)
                    namespace[d_property_name] = delegate

            # For each callable candidate, delegate it with a decorator callable if it is not private
            for d_method_name, d_method in inspect.getmembers(delegate_to_type, mcs._is_method):
                if not d_method_name.startswith(private_prefix):
                    delegate = mcs._delegation_callable(delegate_to_field, d_method_name, d_method)
                    namespace[d_method_name] = delegate

        return namespace

    @staticmethod
    def __new__(mcs, name, bases, attrs, **kwargs):
        # This is needed to ensure a correct signature, as by default we don't allow passing kwargs about.
        return super().__new__(mcs, name, bases, attrs)

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
