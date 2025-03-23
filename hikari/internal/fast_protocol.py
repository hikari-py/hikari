# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021-present davfsa
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
"""A utility for faster [`typing.Protocol`][] instance checks."""

from __future__ import annotations

__all__: typing.Sequence[str] = ("FastProtocolChecking",)

import abc
import typing

if typing.TYPE_CHECKING:
    from typing_extensions import Self

_Protocol: type[FastProtocolChecking] = NotImplemented
_IGNORED_ATTRS = frozenset(typing.EXCLUDED_ATTRIBUTES) | {"__qualname__", "__slots__"}
_abc_instancecheck = abc.ABCMeta.__instancecheck__
_abc_subclasscheck = abc.ABCMeta.__subclasscheck__


def _check_if_ignored(name: str) -> bool:
    return name.startswith("_abc_") or name in _IGNORED_ATTRS


# This metaclass needs to subclass the same type as `typing.Protocol` to be
# able to overwrite it
class _FastProtocolChecking(type(typing.Protocol)):
    _attributes_: tuple[str, ...]

    def __new__(cls, cls_name: str, bases: tuple[type, ...], namespace: dict[str, typing.Any]) -> Self:
        global _Protocol

        if _Protocol is NotImplemented:
            if cls_name != "FastProtocolChecking":
                msg = "First instance of _FastProtocolChecking must be FastProtocolChecking"
                raise TypeError(msg)

            namespace["_attributes_"] = ()
            # noinspection PyRedundantParentheses
            return (_Protocol := super().__new__(cls, cls_name, bases, namespace))

        if _Protocol in bases:
            in_bases = True
            attributes = {attr for attr in namespace if not _check_if_ignored(attr)}
            attributes.update(annot for annot in namespace.get("__annotations__", {}) if not _check_if_ignored(annot))

            for base in bases:
                if base in (typing.Protocol, _Protocol):
                    continue

                if _Protocol not in base.__bases__:
                    msg = f"FastProtocolChecking can only inherit from other fast checking protocols, got {base!r}"
                    raise TypeError(msg)

                attributes.update(base._attributes_)

            namespace["_attributes_"] = tuple(attributes)

        else:
            in_bases = False

        obj = super().__new__(cls, cls_name, bases, namespace)

        if in_bases and not obj._is_protocol:
            msg = "FastProtocolChecking can only be used with protocols"
            raise TypeError(msg)

        return obj

    def __subclasscheck__(cls, other: type) -> bool:
        return _abc_subclasscheck(cls, other)

    def __instancecheck__(cls, other: object) -> bool:
        if not cls._is_protocol:
            return super().__instancecheck__(other)

        if _abc_instancecheck(cls, other):
            return True

        for i in cls._attributes_:
            if not hasattr(other, i):
                return False

        return True


@typing.runtime_checkable
class FastProtocolChecking(typing.Protocol, metaclass=_FastProtocolChecking):
    """An extension to make protocols with faster instance checks.

    !!! note
        All protocols that subclass this class must be decorated with
        [@typing.runtime_checkable][] to keep mypy happy.
    """

    __slots__: typing.Sequence[str] = ()

    __subclasshook__: typing.Callable[[type[typing.Any]], bool]

    def __init_subclass__(cls, *args: object, **kwargs: object) -> None:
        # typing sets their own subclasshook if its not there. We want to
        # overwrite that one, but not any that was already defined, so we check
        # this before typing does anything to it.
        should_overwrite = "__subclasshook__" not in cls.__dict__

        super().__init_subclass__(*args, **kwargs)

        if not should_overwrite:
            return

        def _subclass_hook(other: type[typing.Any]) -> bool:
            for i in cls._attributes_:
                if i not in other.__dict__:
                    return NotImplemented

            return True

        cls.__subclasshook__ = _subclass_hook
