# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Implementation of parts of Python's `enum` protocol to be fast."""
from __future__ import annotations

__all__: typing.List[str] = ["Enum"]

import sys
import types
import typing

T = typing.TypeVar("T", bound=typing.Hashable)
E = typing.TypeVar("E", bound="_EnumMeta")


class _EnumNamespace(dict):
    def __init__(self, base) -> None:
        super().__init__()
        self.base = base
        self.names_to_values = {}
        self.values_to_names = {}
        self["__doc__"] = "An enumeration."

    def __setitem__(self, name: str, value: typing.Any) -> None:
        if name == "" or name == "mro":
            raise TypeError(f"Invalid enum member name: {name!r}")

        if name.startswith("_"):
            # Dunder/sunder, so skip.
            super().__setitem__(name, value)
            return

        if hasattr(value, "__get__") or hasattr(value, "__set__") or hasattr(value, "__del__"):
            super().__setitem__(name, value)
            return

        if not isinstance(value, self.base):
            raise TypeError(f"Expected member {name} to be of type {self.base.__name__} but was {type(value).__name__}")

        name = sys.intern(name)

        if issubclass(self.base, str):
            value = sys.intern(value)
        else:
            try:
                # This will fail if unhashable.
                hash(value)
            except TypeError:
                raise TypeError(f"Cannot have unhashable values in this enum type ({name}: {value!r})") from None

        if name in self.names_to_values:
            raise TypeError("Cannot define same name twice")
        if name in self.values_to_names:
            raise TypeError("Cannot define same value twice")
        if not isinstance(value, self.base):
            raise TypeError("Enum values must be an instance of the base type of the enum")

        self.names_to_values[name] = value
        self.values_to_names[value] = name


def _make_delegate(name):
    # Do this in a module-global method to skip filling __closure__ with
    # contextual shit we don't want from the metaclass. Lets that crap get
    # garbage collected properly.
    return property(lambda self: getattr(self._value_, name))


# We refer to these from the metaclasses, but obviously this won't work
# until these classes are created, and since they use the metaclasses as
# a base metaclass, we have to give these values for _EnumMeta to not
# flake out when initializing them.
_Enum = NotImplemented


def _make_cast(value2member_map):
    def __cast__(_: E, value: T):
        return value2member_map[value]

    return __cast__


class _EnumMeta(type):
    __objtype__: T
    __enumtype__: E
    _value2member_map_: typing.Mapping[T, E]
    _name2member_map_: typing.Mapping[str, E]
    __members__: types.MappingProxyType[str, T]

    def __init_member__(cls: E):
        return super().__call__()

    def __call__(cls: E, value: T):
        return cls._value2member_map_[value]

    @staticmethod
    def __new__(mcs, name, bases, namespace):
        global _Enum

        if name == "Enum" and _Enum is NotImplemented:
            # noinspection PyRedundantParentheses
            return (_Enum := super().__new__(mcs, name, bases, namespace))

        try:
            base, enum_type = bases
        except ValueError:
            raise TypeError("Expected two base classes for an enum")

        if not issubclass(enum_type, _Enum):
            raise TypeError("second base type for enum must be derived from Enum")

        new_namespace = {
            "__objtype__": base,
            "__enumtype__": enum_type,
            "_name2member_map_": (name2member := {}),
            "_value2member_map_": (value2member := {}),
            "__members__": types.MappingProxyType(namespace.names_to_values),
            **namespace,
        }

        cls = super().__new__(mcs, name, bases, new_namespace)

        for name, value in namespace.names_to_values.items():
            # Patching the member init call is around 100ns faster per call than
            # using the default type.__call__ which would make us do the lookup
            # in cls.__new__. Reason for this is that python will also always
            # invoke cls.__init__ if we do this, so we end up with two function
            # calls.
            member = cls.__init_member__()
            member.name = name
            member.value = value
            name2member[name] = member
            value2member[value] = member

        return cls

    @classmethod
    def __prepare__(mcs, name, bases=()):
        try:
            # Fails if Enum is not defined. We check this in `__new__` properly.
            base, enum_type = bases

            if isinstance(base, _EnumMeta):
                raise TypeError("First base to an enum must be the type to combine with, not _EnumMeta")
            if not isinstance(enum_type, _EnumMeta):
                raise TypeError("Second base to an enum must be the enum type (derived from _EnumMeta) to be used")

            return _EnumNamespace(base)
        except ValueError:
            return _EnumNamespace(object)


class Enum(metaclass=_EnumMeta):
    __objtype__: typing.Type[T]
    __enumtype__: typing.Type[E]
    _value2member_map_: typing.ClassVar[typing.Mapping[T, E]]
    _name2member_map_: typing.ClassVar[typing.Mapping[str, E]]
    __members__: typing.ClassVar[types.MappingProxyType[str, T]]
