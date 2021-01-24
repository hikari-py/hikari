# -*- coding: utf-8 -*-
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021 davfsa
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
"""Implementation of parts of Python's `typing.Protocol` to be more performant."""

from __future__ import annotations

__all__: typing.List[str] = []

import abc
import typing

if typing.TYPE_CHECKING:
    _T = typing.TypeVar("_T")

_Protocol = NotImplemented
IGNORED_ATTRS = typing.EXCLUDED_ATTRIBUTES + ["__qualname__", "__slots__"]


def _check_if_ignored(name: str) -> bool:
    return name.startswith("_abc_") or name in IGNORED_ATTRS


def _no_init(cls) -> None:
    if type(cls)._is_protocol:
        raise TypeError("Protocols cannot be instantiated")


class _FastProtocol(abc.ABCMeta):
    @staticmethod
    def __new__(
        cls: typing.Type[_T],
        cls_name: str,
        bases: typing.Tuple[typing.Type[typing.Any], ...],
        namespace: typing.Dict[str, typing.Any],
    ) -> _T:
        global _Protocol

        if _Protocol is NotImplemented:
            if cls_name != "Protocol":
                raise TypeError("First instance of _FastProtocol must be Protocol")

            namespace = {"__init__": _no_init, "_is_protocol": True, "_attributes_": (), **namespace}
            # noinspection PyRedundantParentheses
            return (_Protocol := super().__new__(cls, cls_name, bases, namespace))

        if _Protocol not in bases:
            namespace["_is_protocol"] = False

        else:
            attributes = {attr for attr in namespace if not _check_if_ignored(attr)}
            attributes.update(
                annot for annot in namespace.get("__annotations__", {}).keys() if not _check_if_ignored(annot)
            )

            for base in bases:
                # Make sure its a valid Protocol and not a class that mocks the behaviour
                if not (issubclass(base, typing.Generic) and base._is_protocol):
                    raise TypeError(f"Protocols can only inherit from other protocols, got {base!r}")
                attributes.update(base._attributes_)

            namespace = {
                "__init__": _no_init,
                "_is_protocol": True,
                "_attributes_": tuple(attributes),
                **namespace,
            }

        return super().__new__(cls, cls_name, bases, namespace)

    def __instancecheck__(cls: _T, other: typing.Any) -> bool:
        if not cls._is_protocol:
            return super().__instancecheck__(other)

        for i in cls._attributes_:
            if not hasattr(other, i):
                return False

        return True


class Protocol(typing.Generic, metaclass=_FastProtocol):
    """A faster implementation of `typing.Protocol`."""

    __slots__: typing.Sequence[str] = ()

    def __init_subclass__(cls, *args, **kwargs):
        super().__init_subclass__(*args, **kwargs)

        if not cls._is_protocol:
            return

        def _subclass_hook(other: type) -> bool:
            for i in cls._attributes_:
                if not hasattr(other, i):
                    return NotImplemented

            return True

        cls.__subclasshook__ = _subclass_hook
