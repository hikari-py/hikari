# -*- coding: utf-8 -*-
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

import timeit
import typing

from hikari.internal import fast_protocol


@typing.runtime_checkable
class BasicPyProtocol(typing.Protocol):
    def test(self, arg1: str, arg2: bool) -> typing.List[int]:
        raise NotImplementedError

    def test2(self, arg1: str, arg2: bool) -> typing.List[int]:
        raise NotImplementedError

    def test3(self, arg1: str, arg2: bool) -> typing.List[int]:
        raise NotImplementedError

    def test4(self, arg1: str, arg2: bool) -> typing.List[int]:
        raise NotImplementedError

    def test5(self, arg1: str, arg2: bool) -> typing.List[int]:
        raise NotImplementedError

    def test6(self, arg1: str, arg2: bool) -> typing.List[int]:
        raise NotImplementedError

    def test7(self, arg1: str, arg2: bool) -> typing.List[int]:
        raise NotImplementedError

    def test8(self, arg1: str, arg2: bool) -> typing.List[int]:
        raise NotImplementedError

    def test9(self, arg1: str, arg2: bool) -> typing.List[int]:
        raise NotImplementedError

    def test10(self, arg1: str, arg2: bool) -> typing.List[int]:
        raise NotImplementedError


class BasicHikariProtocol(fast_protocol.FastProtocolChecking, typing.Protocol):
    def test(self, arg1: str, arg2: bool) -> typing.List[int]:
        raise NotImplementedError

    def test2(self, arg1: str, arg2: bool) -> typing.List[int]:
        raise NotImplementedError

    def test3(self, arg1: str, arg2: bool) -> typing.List[int]:
        raise NotImplementedError

    def test4(self, arg1: str, arg2: bool) -> typing.List[int]:
        raise NotImplementedError

    def test5(self, arg1: str, arg2: bool) -> typing.List[int]:
        raise NotImplementedError

    def test6(self, arg1: str, arg2: bool) -> typing.List[int]:
        raise NotImplementedError

    def test7(self, arg1: str, arg2: bool) -> typing.List[int]:
        raise NotImplementedError

    def test8(self, arg1: str, arg2: bool) -> typing.List[int]:
        raise NotImplementedError

    def test9(self, arg1: str, arg2: bool) -> typing.List[int]:
        raise NotImplementedError

    def test10(self, arg1: str, arg2: bool) -> typing.List[int]:
        raise NotImplementedError


class Valid:
    def test(self, arg1: str, arg2: bool) -> typing.List[int]: ...

    def test2(self, arg1: str, arg2: bool) -> typing.List[int]: ...

    def test3(self, arg1: str, arg2: bool) -> typing.List[int]: ...

    def test4(self, arg1: str, arg2: bool) -> typing.List[int]: ...

    def test5(self, arg1: str, arg2: bool) -> typing.List[int]: ...

    def test6(self, arg1: str, arg2: bool) -> typing.List[int]: ...

    def test7(self, arg1: str, arg2: bool) -> typing.List[int]: ...

    def test8(self, arg1: str, arg2: bool) -> typing.List[int]: ...

    def test9(self, arg1: str, arg2: bool) -> typing.List[int]: ...

    def test10(self, arg1: str, arg2: bool) -> typing.List[int]: ...


class Invalid: ...


isinstance_long = Valid()
isinstance_failfast = Invalid()

# Dummy work to churn the CPU up.
for i in range(100_000):
    assert sum(i for i in range(10)) > 0

py_protocol_isinstance_long_time = timeit.timeit(
    "isinstance(isinstance_long, BasicPyProtocol)", number=1_000_000, globals=globals()
)
hikari_protocol_isinstance_long_time = timeit.timeit(
    "isinstance(isinstance_long, BasicHikariProtocol)", number=1_000_000, globals=globals()
)
py_protocol_isinstance_failfast_time = timeit.timeit(
    "isinstance(isinstance_failfast, BasicPyProtocol)", number=1_000_000, globals=globals()
)
hikari_protocol_isinstance_failfast_time = timeit.timeit(
    "isinstance(isinstance_failfast, BasicHikariProtocol)", number=1_000_000, globals=globals()
)

py_protocol_issubclass_long_time = timeit.timeit(
    "issubclass(Invalid, BasicPyProtocol)", number=1_000_000, globals=globals()
)
hikari_protocol_issubclass_long_time = timeit.timeit(
    "issubclass(Invalid, BasicHikariProtocol)", number=1_000_000, globals=globals()
)
py_protocol_issubclass_failfast_time = timeit.timeit(
    "issubclass(Valid, BasicPyProtocol)", number=1_000_000, globals=globals()
)
hikari_protocol_issubclass_failfast_time = timeit.timeit(
    "issubclass(Valid, BasicHikariProtocol)", number=1_000_000, globals=globals()
)

print("isinstance(long, BasicPyProtocol)", py_protocol_isinstance_long_time, "µs")
print("isinstance(long, BasicHikariProtocol)", hikari_protocol_isinstance_long_time, "µs")
print("isinstance(failfast, BasicPyProtocol)", py_protocol_isinstance_failfast_time, "µs")
print("isinstance(failfast, BasicHikariProtocol)", hikari_protocol_isinstance_failfast_time, "µs")

print("issubclass(long, BasicPyProtocol)", py_protocol_issubclass_long_time, "µs")
print("issubclass(long, BasicHikariProtocol)", hikari_protocol_issubclass_long_time, "µs")
print("issubclass(failfast, BasicPyProtocol)", py_protocol_issubclass_failfast_time, "µs")
print("issubclass(failfast, BasicHikariProtocol)", hikari_protocol_issubclass_failfast_time, "µs")
