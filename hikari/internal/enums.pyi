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

# Enums use a lot of internal voodoo that will not type check nicely, so we
# skip that module with MyPy and just accept that "here be dragons".
#
# The caveat to implementing this is that MyPy has to have a special module to
# understand how to use Python's enum types. I really don't want to have to
# ship my own MyPy plugin for this, so just make MyPy think that the types
# we are using are just aliases from the enum types in the standard library.

__all__ = ["Enum", "Flag"]

import enum as __enum
from collections.abc import Iterator as __Iterator
from collections.abc import Sequence as __Sequence
from typing import TypeVar as __TypeVar

from typing_extensions import Self as __Self

from hikari.internal import typing_extensions as __typing_backport

Enum = __enum.Enum

# MyPy started complaining of Flags with no additional flags, so just ignore it here
class Flag(__enum.IntFlag):  # type: ignore[misc]
    def all(self, *flags: __Self) -> bool: ...
    def any(self, *flags: __Self) -> bool: ...
    def difference(self, other: int | __Self) -> __Self: ...
    def intersection(self, other: int | __Self) -> __Self: ...
    def invert(self) -> __Self: ...
    def is_disjoint(self, other: int | __Self) -> bool: ...
    def is_subset(self, other: int | __Self) -> bool: ...
    def is_superset(self, other: int | __Self) -> bool: ...
    def none(self, *flags: __Self) -> bool: ...
    def split(self) -> __Sequence[__Self]: ...
    def symmetric_difference(self, other: int | __Self) -> __Self: ...
    def union(self, other: int | __Self) -> __Self: ...
    def __iter__(self) -> __Iterator[__Self]: ...
    def __len__(self) -> int: ...
    # Aliases
    def isdisjoint(self, other: int | __Self) -> bool: ...  # is_disjoint
    def issuperset(self, other: int | __Self) -> bool: ...  # is_superset
    def symmetricdifference(self, other: int | __Self) -> __Self: ...  # symmetric_difference
    def issubset(self, other: int | __Self) -> bool: ...  # is_subset
    # '__invert__' is explicitly defined as a special case because it is typed as returning 'int' in typeshed
    @__typing_backport.override
    def __invert__(self) -> __Self: ...  # invert

_V = __TypeVar("_V")

def deprecated(value: _V, /, *, removal_version: str) -> _V: ...
