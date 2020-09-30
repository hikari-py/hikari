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
"""Implementation of parts of Python's `enum` protocol to be faster."""
from __future__ import annotations

__all__: typing.List[str] = ["Enum"]

import os
import sys
import types
import typing

_T = typing.TypeVar("_T")


class _EnumNamespace(typing.Dict[str, typing.Any]):
    __slots__: typing.Sequence[str] = ("base", "names_to_values", "values_to_names")

    def __init__(self, base: typing.Type[typing.Any]) -> None:
        super().__init__()
        self.base = base
        self.names_to_values: typing.Dict[str, typing.Any] = {}
        self.values_to_names: typing.Dict[str, typing.Any] = {}
        self["__doc__"] = "An enumeration."

    def __contains__(self, item: typing.Any) -> bool:
        try:
            _ = self[item]
            return True
        except KeyError:
            return False

    def __getitem__(self, name: str) -> typing.Any:
        try:
            return super().__getitem__(name)
        except KeyError:
            try:
                return self.names_to_values[name]
            except KeyError:
                raise KeyError(name) from None

    def __iter__(self) -> typing.Iterator[str]:
        yield from super().__iter__()
        yield self.names_to_values

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
        if value in self.values_to_names:
            # We must have defined some alias, so just register the name
            self.names_to_values[name] = value
            return
        if not isinstance(value, self.base):
            raise TypeError("Enum values must be an instance of the base type of the enum")

        self.names_to_values[name] = value
        self.values_to_names[value] = name


# We refer to these from the metaclasses, but obviously this won't work
# until these classes are created, and since they use the metaclasses as
# a base metaclass, we have to give these values for _EnumMeta to not
# flake out when initializing them.
_Enum = NotImplemented


def _attr_mutator(self, *_: typing.Any) -> typing.NoReturn:
    raise TypeError("Cannot mutate enum members")


class _EnumMeta(type):
    def __call__(cls, value: typing.Any) -> typing.Any:
        try:
            return cls._value2member_map_[value]
        except KeyError:
            # If we cant find the value, just return what got casted in
            return value

    def __dir__(cls) -> typing.List[str]:
        members = ["__class__", "__doc__", "__members__", "__module__"]
        try:
            members += list(cls._name2member_map_)
        finally:
            return members

    def __getattr__(cls, name: str) -> typing.Any:
        if name.startswith("_") and name.endswith("_"):
            # Stop recursion errors by trying to look up _name2member_map_
            # recursively.
            raise AttributeError(name)
        try:
            return cls._name2member_map_[name]
        except KeyError:
            try:
                return super().__getattribute__(name)
            except AttributeError:
                raise AttributeError(name) from None

    def __getitem__(cls, name: str) -> typing.Any:
        return cls._name2member_map_[name]

    def __iter__(cls) -> typing.Iterator[str]:
        yield cls._name2member_map_

    @staticmethod
    def __new__(
        mcs: typing.Type[_T],
        name: str,
        bases: typing.Tuple[typing.Type[typing.Any], ...],
        namespace: _EnumNamespace,
    ) -> _T:
        global _Enum

        if name == "Enum" and _Enum is NotImplemented:
            # noinspection PyRedundantParentheses
            return (_Enum := super().__new__(mcs, name, bases, namespace))

        try:
            base, enum_type = bases
        except ValueError:
            raise TypeError("Expected two base classes for an enum") from None

        if not issubclass(enum_type, _Enum):
            raise TypeError("second base type for enum must be derived from Enum")

        new_namespace = {
            "__objtype__": base,
            "__enumtype__": enum_type,
            "_name2member_map_": (name2member := {}),
            "_value2member_map_": (value2member := {}),
            # Required to be immutable by enum API itself.
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
            member = cls.__new__(cls, value)
            member.name = name
            member.value = value
            name2member[name] = member
            value2member[value] = member

        cls.__setattr__ = _attr_mutator
        cls.__delattr__ = _attr_mutator

        return cls

    @classmethod
    def __prepare__(mcs, name: str, bases: typing.Tuple[typing.Type[typing.Any], ...] = ()) -> _EnumNamespace:
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

    def __repr__(cls) -> str:
        return f"<enum {cls.__name__}>"

    __str__ = __repr__


class Enum(metaclass=_EnumMeta):
    """Re-implementation of parts of Python's `enum` to be faster."""

    def __getattr__(self, name: str) -> typing.Any:
        return getattr(self.value, name)

    def __repr__(self) -> str:
        return f"<{type(self).__name__}.{self.name}: {self.value!r}>"

    def __str__(self) -> str:
        return f"{type(self).__name__}.{self.name}"


# We have to use this fallback, or Pdoc will fail to document some stuff correctly...
if os.getenv("PDOC3_GENERATING") == "1":  # pragma: no cover
    from enum import Enum  # noqa: F811 - Redefinition intended
