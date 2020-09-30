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
"""Stuff to make working with enum flags a bit easier."""
from __future__ import annotations

__all__: typing.List[str] = ["Flag"]

import enum
import inspect
import math
import typing

FlagT = typing.TypeVar("FlagT", bound="Flag")


class Flag(enum.IntFlag):
    """Base type for an enum integer flag in Hikari.

    Provides a consistent way of producing human-readable strings, extra
    inspection utilities, and injects some boilerplate documentation. This
    should make the concept of using flags a little less daunting to those
    who are not yet used to the idea.

    Example
    -------

    ```py
    >>> class Permission(Flag):
    ...     CREATE = enum.auto()
    ...     READ = enum.auto()
    ...     UPDATE = enum.auto()
    ...     DELETE = enum.auto()

    >>> perms = Permissions.CREATE | Permissions.READ
    >>> print(perms.split())
    [Permissions.CREATE, Permissions.READ]
    ```

    This also provides two operators for clearer semantics of combining and
    removing flag members.

    ```py
    perms = Permissions.CREATE + Permissions.READ
    assert perms  == Permissions.CREATE | Permissions.READ

    perms -= Permissions.CREATE
    assert perms == Permissions.READ
    ```

    Members will be iterable if you wish to inspect each individual flag.

    ```py
    for p in Permissions.CREATE + Permissions.READ:
        print(p)
    ```
    """

    __slots__: typing.Sequence[str] = ()

    def __init_subclass__(cls, **kwargs: typing.Any) -> None:
        doc = inspect.getdoc(cls) or ""

        doc += "\n".join(
            (
                "",
                "",
                "This flag type has several additional operations that can be used",
                "compared to normal enum types. These are applied to instances of",
                "this enum directly, or can be used as a class method by passing the",
                "flag as the first parameter.",
                "",
                f" - `def split() -> typing.Sequence[{cls.__name__}]: ...`<br/>",
                "   Will split the combined flag up into individual atomic flags and",
                "   return them in a `typing.Sequence`.",
                "```py",
                ">>> (FOO | BAR | BAZ).split()",
                "[FOO, BAR, BAZ]",
                "```",
                "",
                f" - `def has_any(*flags: {cls.__name__}) -> bool: ...`<br/>",
                "   Returns `builtins.True` if any of the given flags are present",
                "   in the combined flag this is applied to. Otherwise, returns",
                "   `builtins.False` instead.",
                "",
                f" - `def has_all(*flags: {cls.__name__}) -> bool: ...`<br/>",
                "   Returns `builtins.True` if all of the given flags are present",
                "   in the combined flag this is applied to. Otherwise, returns",
                "   `builtins.False` instead.",
                "",
                f" - `def has_none(*flags: {cls.__name__}) -> bool: ...`<br/>",
                "   Returns `builtins.True` if none of the given flags are present",
                "   in the combined flag this is applied to. Otherwise, returns",
                "   `builtins.False` instead.",
                "",
                "In addition, new operators are overloaded. `+` will combine flags",
                "in the same way `|` would usually, and `-` will remove specific ",
                "flags from this instance. This is equivalent to using the `&` " "operator.",
                "",
                "Finally, combined flag types can be iterated across as if they",
                "were a collection.",
                "```py",
                ">>> for f in FOO | BAR | BAZ:",
                "...     print(f)",
                "FOO",
                "BAR",
                "BAZ",
                "```",
            )
        )
        cls.__doc__ = doc

    def split(self: FlagT) -> typing.Sequence[FlagT]:
        """Return a list of all atomic values for this flag."""
        members: typing.List[FlagT] = []

        for member in type(self).__members__.values():
            # Don't show `NONE` values, it breaks stuff and makes no sense here.
            if not member.value:
                continue

            # If it is not a combined value, and it is contained in the bitfield:
            if math.log2(member.value).is_integer() and member & self:
                members.append(member)

        return sorted(members, key=lambda m: m.name)

    def has_any(self, *flags: FlagT) -> bool:
        return any((flag & self) == flag for flag in flags)

    def has_all(self, *flags: FlagT) -> bool:
        return all((flag & self) == flag for flag in flags)

    def has_none(self, *flags: FlagT) -> bool:
        return not self.has_any(*flags)

    def __add__(self: FlagT, other: typing.Union[int, FlagT]) -> FlagT:
        return type(self)(self | other)

    __radd__ = __add__

    def __sub__(self: FlagT, other: typing.Union[int, FlagT]) -> FlagT:
        return type(self)(self & ~other)

    def __str__(self) -> str:
        if hasattr(self, "name") and self.name is not None:
            return self.name
        return " | ".join(m.name for m in self.split())

    def __iter__(self: FlagT) -> typing.Iterator[FlagT]:
        return iter(self.split())
