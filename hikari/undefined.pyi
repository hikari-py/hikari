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

import enum as __enum
from typing import Literal as __Literal
from typing import TypeVar as __TypeVar

import typing_extensions

class UndefinedType(__enum.Enum):
    def __bool__(self) -> __Literal[False]: ...
    UNDEFINED = __enum.auto()

UNDEFINED: __Literal[UndefinedType.UNDEFINED] = ...

__T_co = __TypeVar("__T_co", covariant=True)

UndefinedOr: typing_extensions.TypeAlias = __T_co | UndefinedType
UndefinedNoneOr: typing_extensions.TypeAlias = UndefinedOr[__T_co] | None

def all_undefined(*items: object) -> bool: ...
def any_undefined(*items: object) -> bool: ...
def count(*items: object) -> int: ...
