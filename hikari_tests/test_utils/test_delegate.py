#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019
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
import textwrap

import dataclasses
import pytest

from hikari.utils import delegate


def test_delegation_attr_delegates_as_expected():
    class Inner:
        def __init__(self):
            self.value = 12345

    class Outer:
        value = delegate.DelegatedMeta._delegation_attr("_inner", "value")

        def __init__(self, inner):
            self._inner = inner

    inner = Inner()
    outer = Outer(inner)
    assert outer.value == 12345


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "inner_method",
    [
        """
        def test(self, a, b):
            return str(a) + str(b)\n
        """,
        """
        async def test(self, a, b):
            return str(a) + str(b)\n
        """,
        """
        @classmethod
        def test(cls, a, b):
            return str(a) + str(b)\n
        """,
        """
        @classmethod
        async def test(cls, a, b):
            return str(a) + str(b)\n
        """,
        """
        @staticmethod
        def test(a, b):
            return str(a) + str(b)\n
        """,
        """
        @staticmethod
        async def test(a, b):
            return str(a) + str(b)\n
        """,
        """
        class TestCallable:
            def __call__(self, a, b):
                return str(a) + str(b)

        test = TestCallable()
        """,
        """
        class TestCallable:
            async def __call__(self, a, b):
                return str(a) + str(b)

        test = TestCallable()
        """
    ])
async def test_delegation_callable_delegates_as_expected(inner_method):
    async def _maybe_await(func, *args, **kwargs):
        result = func(*args, **kwargs)
        if hasattr(result, '__await__'):
            return await result
        else:
            return result

    class Inner:
        exec(textwrap.dedent(inner_method))

    class Outer:
        test = delegate.DelegatedMeta._delegation_callable("_inner", "test", Inner.test)

        def __init__(self, inner):
            self._inner = inner

    inner = Inner()
    outer = Outer(inner)

    assert await _maybe_await(outer.test, 9, 18) == await _maybe_await(inner.test, 9, 18) == "918"


def test_delegate_slotting():
    class Base:
        __slots__ = ("a", "_b")

        def __init__(self, a, b):
            self.a = a
            self._b = b


    @dataclasses.dataclass
    class Delegate(metaclass=delegate.DelegatedMeta, delegate_to=(Base, "_base")):
        _base: Base

    b = Base(1, 2.3)
    d = Delegate(b)
    assert d.a == b.a == 1
    assert not hasattr(d, "_b")


def test_delegate_by_annotations():
    @dataclasses.dataclass()
    class Base:
        a: int
        _b: float

    @dataclasses.dataclass
    class Delegate(metaclass=delegate.DelegatedMeta, delegate_to=(Base, "_base")):
        _base: Base

    b = Base(1, 2.3)
    d = Delegate(b)
    assert d.a == b.a == 1
    assert not hasattr(d, "_b")


def test_DelegatedMeta_fails_if_subclassed():
    try:
        class Delegation(delegate.DelegatedMeta):
            pass

        assert False
    except TypeError:
        pass


def test_DelegatedMeta_fails_if_no_delegate_to_keyword_is_provided():
    try:
        class Delegation(metaclass=delegate.DelegatedMeta):
            pass

        assert False
    except AttributeError:
        pass


def test_DelegatedMeta_fails_if_delegate_to_keyword_is_provided_but_is_not_a_valid_type():
    try:
        class Delegation(metaclass=delegate.DelegatedMeta, delegate_to=69):
            pass

        assert False
    except TypeError:
        pass


def test_DelegatedMeta_allows_single_delegation_field():
    class Backing:
        test0: int

        def test1(self, a, b, c):
            pass

        async def test2(self, a, b, c):
            pass

        @classmethod
        def test3(self, a, b, c):
            pass

        @classmethod
        async def test4(self, a, b, c):
            pass

        @staticmethod
        def test5(self, a, b, c):
            pass

        @staticmethod
        async def test6(self, a, b, c):
            pass7

        @property
        def test7(self):
            return NotImplemented

        @property
        async def test8(self):
            return NotImplemented

        def __private_function(self):
            pass

        async def __private_coroutine(self):
            pass

        @property
        def __private_function_property(self):
            pass

        @property
        async def __private_coroutine_property(self):
            pass

    class Delegation(metaclass=delegate.DelegatedMeta, delegate_to=(Backing, "_backing")):
        pass

    assert not any("private_function" in attr for attr in dir(Delegation))
    assert not any("private_coroutine_function" in attr for attr in dir(Delegation))
    assert not any("private_function_property" in attr for attr in dir(Delegation))
    assert not any("private_coroutine_property" in attr for attr in dir(Delegation))

    for i in range(0, 9):
        assert hasattr(Delegation, f"test{i}")


def test_DelegatedMeta_with_multiple_delegations():
    import abc

    @dataclasses.dataclass
    class SomeModel:
        a: int
        b: float

    class CallableABC(metaclass=abc.ABCMeta):
        @abc.abstractmethod
        def __call__(self, *args, **kwargs):
            ...

    class CallableImpl(CallableABC):
        def __call__(self, *args, **kwargs):
            return 18

    class SomethingWithSlots:
        __slots__ = ("c", "d")

        def __init__(self, c, d):
            self.c = c
            self.d = d

    class SomethingElse:
        @staticmethod
        def foo():
            return "bar"

        def foo_again(self):
            return self.foo() + "... again"

    @dataclasses.dataclass()
    class Delegate(
        metaclass=delegate.DelegatedMeta,
        delegate_to=[
            (SomeModel, "_some_model"),
            (CallableImpl, "_callable"),
            (SomethingWithSlots, "_slotted_thingy"),
            (SomethingElse, "_that")
        ]
    ):
        _some_model: SomeModel
        _callable: CallableImpl
        _slotted_thingy: SomethingWithSlots
        _that: SomethingElse

    model = SomeModel(1, 2.4)
    callable = CallableImpl()
    slotted = SomethingWithSlots(9, 18)
    that = SomethingElse()
    Delegate(model, callable, slotted, that)


def test_delegate_subclass_check_normal_case():
    @dataclasses.dataclass()
    class Base:
        a: int
        _b: float

    @dataclasses.dataclass
    class Delegate(metaclass=delegate.DelegatedMeta, delegate_to=(Base, "_base")):
        _base: Base

    class DerivedDelegate(Delegate):
        pass

    assert issubclass(DerivedDelegate, Delegate)


def test_delegate_subclassing_subclasscheck():
    class Inner:
        value: int

        def __init__(self):
            self.value = 12345

    @dataclasses.dataclass()
    class Outer(metaclass=delegate.DelegatedMeta, delegate_to=(Inner, "_base")):
        _base: Inner

    class SomeOtherBase:
        pass

    class SubOuter(Outer, SomeOtherBase):
        pass

    inner = Inner()
    sub_outer = SubOuter(inner)
    assert sub_outer.value == 12345
    assert isinstance(sub_outer, Outer)
