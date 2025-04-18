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
from __future__ import annotations

import cProfile
import enum as py_enum
import timeit

from hikari.internal import enums as hikari_enum


class BasicPyEnum(str, py_enum.Enum):
    __slots__ = ()

    a = "0"
    b = "1"
    c = "2"
    d = "3"
    e = "4"
    f = "5"
    g = "6"
    h = "7"
    i = "8"
    j = "9"
    k = "10"
    m = "12"
    n = "13"
    o = "14"
    p = "15"
    q = "16"
    r = "17"
    s = "18"
    t = "19"
    u = "20"
    v = "21"
    w = "22"
    x = "23"
    y = "24"
    z = "25"


class BasicHikariEnum(str, hikari_enum.Enum):
    __slots__ = ()

    a = "0"
    b = "1"
    c = "2"
    d = "3"
    e = "4"
    f = "5"
    g = "6"
    h = "7"
    i = "8"
    j = "9"
    k = "10"
    m = "12"
    n = "13"
    o = "14"
    p = "15"
    q = "16"
    r = "17"
    s = "18"
    t = "19"
    u = "20"
    v = "21"
    w = "22"
    x = "23"
    y = "24"
    z = "25"


# Dummy work to churn the CPU up.
for i in range(100_000):
    assert sum(i for i in range(10)) > 0

py_enum_call_time = timeit.timeit("BasicPyEnum('25')", number=1_000_000, globals=globals())
hikari_enum_call_time = timeit.timeit("BasicHikariEnum('25')", number=1_000_000, globals=globals())
py_enum_delegate_to_map_time = timeit.timeit(
    "BasicPyEnum._value2member_map_['25']", number=1_000_000, globals=globals()
)
hikari_enum_delegate_to_map_time = timeit.timeit(
    "BasicHikariEnum._value_to_member_map_['25']", number=1_000_000, globals=globals()
)
py_enum_getitem_time = timeit.timeit("BasicPyEnum['z']", number=1_000_000, globals=globals())
hikari_enum_getitem_time = timeit.timeit("BasicHikariEnum['z']", number=1_000_000, globals=globals())

print("BasicPyEnum.__call__('25')", py_enum_call_time, "µs")
print("BasicHikariEnum.__call__('25')", hikari_enum_call_time, "µs")
print("BasicPyEnum._value2member_map_['25']", py_enum_delegate_to_map_time, "µs")
print("BasicHikariEnum._value_to_member_map['25']", hikari_enum_delegate_to_map_time, "µs")
print("BasicPyEnum.__getitem__['z']", py_enum_getitem_time, "µs")
print("BasicHikariEnum.__getitem__['z']", hikari_enum_getitem_time, "µs")

print("BasicPyEnum.__call__ profile")
cProfile.runctx("for i in range(1_000_000): BasicPyEnum('25')", globals=globals(), locals=locals())

print("BasicHikariEnum.__call__ profile")
cProfile.runctx("for i in range(1_000_000): BasicHikariEnum('25')", globals=globals(), locals=locals())

print("BasicPyEnum.__getitem__ profile")
cProfile.runctx("for i in range(1_000_000): BasicPyEnum['z']", globals=globals(), locals=locals())

print("BasicHikariEnum.__getitem__ profile")
cProfile.runctx("for i in range(1_000_000): BasicHikariEnum['z']", globals=globals(), locals=locals())
