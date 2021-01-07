# -*- coding: utf-8 -*-
# cython: language_level=3
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
"""Singleton used throughout the library to denote values that are not present."""

from __future__ import annotations

__all__: typing.List[str] = [
    "UNDEFINED",
    "UndefinedNoneOr",
    "UndefinedOr",
    "UndefinedType",
    "count",
]

import typing

SelfT = typing.TypeVar("SelfT")


class UndefinedType:
    """The type of the `UNDEFINED` singleton sentinel value."""

    __slots__: typing.Sequence[str] = ()

    def __bool__(self) -> typing.Literal[False]:
        return False

    def __copy__(self: SelfT) -> SelfT:
        # This is meant to be a singleton
        return self

    def __deepcopy__(self: SelfT, memo: typing.MutableMapping[int, typing.Any]) -> SelfT:
        memo[id(self)] = self

        # This is meant to be a singleton
        return self

    def __getstate__(self) -> typing.Any:
        # Returning False tells pickle to not call `__setstate__` on unpickling.
        return False

    def __repr__(self) -> str:
        return "UNDEFINED"

    def __reduce__(self) -> str:
        # Returning a string makes pickle fetch from the module namespace.
        return "UNDEFINED"

    def __str__(self) -> str:
        return "UNDEFINED"


UNDEFINED = UndefinedType()
"""A sentinel singleton that denotes a missing or omitted value."""


def __new__(cls: UndefinedType) -> typing.NoReturn:  # pragma: nocover
    raise TypeError("Cannot initialize multiple instances of singleton UNDEFINED")


UndefinedType.__new__ = __new__
del __new__

T = typing.TypeVar("T", covariant=True)
UndefinedOr = typing.Union[T, UndefinedType]
"""Type hint to mark a type as being semantically optional.

**NOTE THAT THIS IS NOT THE SAME AS `typing.Optional` BY DEFINITION**.

If you see a type with this marker, it may be `UNDEFINED` or the value it wraps.
For example, `UndefinedOr[float]` would mean the value could be a
`builtins.float`, or the literal `UNDEFINED` value.

On the other hand, `typing.Optional[float]` would mean the value could be
a `builtins.float`, or the literal `builtins.None` value.

The reason for using this is in some places, there is a semantic difference
between specifying something as being `builtins.None`, i.e. "no value", and
having a default to specify that the value has just not been mentioned. The
main example of this is in `edit` endpoints where the contents will only be
changed if they are explicitly mentioned in the call. Editing a message content
and setting it to `builtins.None` would be expected to clear the content,
whereas setting it to `UNDEFINED` would be expected to leave the value as it
is without changing it.

Consider `UndefinedOr[T]` semantically equivalent to `undefined` versus
`null` in JavaScript, or `Optional<T>` versus `null` in Java and C#.

If in doubt, remember:

- `UNDEFINED` means there is no value present, or that it has been left to
    the default value.
- `builtins.None` means the value is present and explicitly empty/null/void,
    where this has a deterministic documented behaviour and no differentiation
    is made between a `builtins.None` value, and one that has been omitted.
"""

UndefinedNoneOr = typing.Union[UndefinedOr[T], None]
"""Type hint for a value that may be `undefined.UNDEFINED`, or `builtins.None`.

`UndefinedNoneOr[T]` is simply an alias for
`UndefinedOr[typing.Optional[T]]`, which would expand to
`typing.Union[UndefinedType, T, None]`.
"""


def count(*items: typing.Any) -> int:
    """Count the number of items that are provided that are `UNDEFINED`."""
    return sum(1 for item in items if item is UNDEFINED)
