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
"""Re-implementation of parts of Python's `enum` protocol to be lightweight."""
from __future__ import annotations

__all__: typing.List[str] = ["Enum"]

import inspect
import sys
import types
import typing

if typing.TYPE_CHECKING:
    # Hikari only uses these two types.
    from enum import Enum
else:
    class _EnumNamespace(dict):
        def __init__(self, base) -> None:
            super().__init__()
            self.base = base
            self.names_to_values = {}
            self.values_to_names = {}
            self["__doc__"] = "An enumeration"
            self.descriptors = {}

        def __setitem__(self, name: str, value: typing.Any) -> None:
            name = sys.intern(name)
            if issubclass(self.base, str):
                value = sys.intern(value)
            else:
                try:
                    # This will fail if unhashable.
                    hash(value)
                except TypeError:
                    raise TypeError("Cannot have unhashable values in this enum type") from None

            if name.startswith("_"):
                super().__setitem__(name, value)
                return

            if name == "" or name == "mro":
                raise TypeError(f"Invalid enum member name: {name!r}")

            if hasattr(value, "__get__") or hasattr(value, "__set__") or hasattr(value, "__del__"):
                super().__setitem__(name, value)
                return

            if name in self.names_to_values:
                raise TypeError("Cannot define same name twice")
            if name in self.values_to_names:
                raise TypeError("Cannot define same value twice")
            if not isinstance(value, self.base):
                raise TypeError("Enum values must be an instance of the base type of the enum")

            self.names_to_values[name] = value
            self.values_to_names[value] = name

    def _make_delegate(name):
        return property(lambda self: getattr(self._value_, name))

    def _make_member_type(enum_type_name, base):
        cls = type(f"{enum_type_name}Member", (base,), {"__slots__": ("_name_", "_value_")})

        # Delegate members if possible.
        for name, value in inspect.getmembers(base):
            # __dunder_names__
            if len(name) > 4 and name[:2] == name[-2:] == '__' and name[2] != '_' and name[-3] != '_':
                continue
            elif isinstance(value, staticmethod):
                setattr(cls, name, value)
            elif isinstance(value, classmethod):
                setattr(cls, name, classmethod(value.__func__))
            elif hasattr(value, "__get__") or hasattr(value, "__set__") or hasattr(value, "__delete__"):
                setattr(cls, name, _make_delegate(name))
            else:
                setattr(cls, name, value)

        cls.name = property(lambda self: self._name_)
        cls.value = property(lambda self: self._value_)
        cls.__str__ = lambda self: f"<{enum_type_name}.{self._name_}"
        cls.__repr__ = lambda self: f"<{enum_type_name}.{self._name_}: {self._value_!r}>"
        cls.__getattr__ = lambda self, _name: getattr(self._value_, _name)
        return cls

    # We refer to these from the metaclasses, but obviously this won't work
    # until these classes are created, and since they use the metaclasses as
    # a base metaclass, we have to give these values for _EnumMeta to not
    # flake out when initializing them.
    _Enum = NotImplemented

    class _EnumMeta(type):
        def __call__(cls, value):
            return cls._values_to_names_[value]

        def __init__(cls, name, bases, namespace):
            super().__init__(name, bases, namespace)

        @staticmethod
        def __new__(mcs, name, bases, namespace):
            global _Enum

            if not bases:
                if name == "Enum" and _Enum is NotImplemented:
                    return (_Enum := super().__new__(mcs, name, bases, namespace))
                raise TypeError("Expected two base classes for an enum")

            base, enum_type = bases
            new_namespace = {
                "__objtype__": (member_type := _make_member_type(name, base)),
                "_name2value_map_": (name2value := namespace.names_to_values),
                "_name2member_map_": (name2member := {}),
                "_value2member_map_": (value2member := {}),
                "__members__": types.MappingProxyType(name2value),
                **namespace,
            }

            for name, value in name2value.items():
                member = member_type(_name_=name, _value_=value)
                name2member[name] = member

            return super().__new__(mcs, name, bases, new_namespace)

        @staticmethod
        def __prepare__(mcs, name, bases=()):
            try:
                # Fails if Enum is not defined. We check this in `__new__` properly.
                base, enum_type = bases

                if isinstance(base, _EnumMeta):
                    raise TypeError("First base to an enum must be the type to combine with, not _EnumMeta")
                if not isinstance(enum_type, _EnumMeta):
                    raise TypeError("Second base to an enum must be the enum type (derived from _EnumMeta) to use")

                return _EnumNamespace(base)
            except ValueError:
                return _EnumNamespace(object)

    class Enum(metaclass=_EnumMeta):
        pass

    class DayOfWeek(str, Enum):
        MON = "Monday"
        TUE = "Tuesday"

    print(dir(DayOfWeek), type(DayOfWeek), DayOfWeek.__members__, sep="\n")
