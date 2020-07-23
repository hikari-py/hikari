# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019-2020
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
"""Stuff to make working with enum flags a bit easier."""
from __future__ import annotations

__all__: typing.List[str] = ["Flag"]

import enum
import math
import inspect
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

    >>> perms = Permission.CREATE | Permission.READ
    >>> print(perms.split())
    [Permission.CREATE, Permission.READ]
    ```

    This also provides two operators for clearer semantics of combining and
    removing flag members.

    ```py
    perms = Permission.CREATE + Permission.READ
    assert perms  == Permission.CREATE | Permission.READ

    perms -= Permission.CREATE
    assert perms == Permission.READ
    ```

    Members will be iterable if you wish to inspect each individual flag.

    ```py
    for p in Permission.CREATE + Permission.READ:
        print(p)
    ```
    """

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

            # If it isn't a combined value, and it is contained in the bitfield:
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
