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
"""Singleton used throughout the library to denote values that are not present."""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = [
    "UNDEFINED",
    "UndefinedNoneOr",
    "UndefinedOr",
    "UndefinedType",
    "count",
]

import enum
import typing

SelfT = typing.TypeVar("SelfT")


class _UndefinedSentinel:
    __slots__: typing.Sequence[str] = ()

    def __bool__(self) -> bool:
        return False

    def __copy__(self: SelfT) -> SelfT:
        # This is meant to be a singleton
        return self

    def __deepcopy__(self: SelfT, memo: typing.MutableMapping[int, typing.Any]) -> SelfT:
        memo[id(self)] = self

        # This is meant to be a singleton
        return self

    def __repr__(self) -> str:
        return "UNDEFINED"

    def __str__(self) -> str:
        return "UNDEFINED"


# Using an enum enables us to use typing.Literal. MyPy has a special case for
# assuming that the number of instances of a specific enum is limited by design,
# whereas using a constant value does not provide that. In short, this allows
# MyPy to determine it can statically cast a value to a different type when
# we do `is` and `is not` checks on values, which removes the need for casts.
@typing.final
class UndefinedType(_UndefinedSentinel, enum.Enum):
    """Wrapper type around the undefined value.

    If you see this in a signature somewhere, it means you can pass a
    value of `UNDEFINED` and it will be valid.

    If you see this as the type of an attribute somewhere, it means that
    the attribute may be `UNDEFINED` in some edge cases.

    This exists to allow static type checkers to dereference this value
    using `typing.Literal`, which aids in static type analysis by treating
    this value as a true singleton. This can only be achieved by using
    an `enum.Enum` of a single value to enforce this.

    For all other purposes, you can treat this as the type of the
    `UNDEFINED` sentinel in this module. You should generally not need to
    use this, however.
    """

    UNDEFINED_VALUE = _UndefinedSentinel()


# Prevent making any more instances as much as possible.
setattr(_UndefinedSentinel, "__new__", lambda _: UNDEFINED)
del _UndefinedSentinel


# noinspection PyTypeChecker
UNDEFINED: typing.Final[typing.Literal[UndefinedType.UNDEFINED_VALUE]] = UndefinedType.UNDEFINED_VALUE
"""Undefined sentinel value.

This will behave as a false value in conditions.
"""


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

- `UNDEFINED` means there is no value present.
- `builtins.None` means the value is present and explicitly empty/null/void.
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
