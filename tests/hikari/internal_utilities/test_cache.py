#!/usr/bin/env python3
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
import asyncio

import cymock as mock
import pytest

from hikari.internal_utilities import cache


def test_init_CachedFunction_sets_value_to_sentinel():
    def call():
        pass

    cached_call = cache.CachedFunction(call, [], {})
    assert cached_call._value is cached_call._sentinel


def test_call_CachedFunction_first_time_sets_value():
    call = mock.MagicMock(return_value=27)

    cached_call = cache.CachedFunction(call, [9], {"k": 18})

    cached_call()

    call.assert_called_with(9, k=18)

    assert cached_call._value == 27


def test_call_CachedFunction_first_time_returns_value():
    call = mock.MagicMock(return_value=27)

    cached_call = cache.CachedFunction(call, [9], {"k": 18})

    assert cached_call() == 27


def test_call_CachedFunction_second_time_does_not_reset_value():
    call = mock.MagicMock(return_value=27)
    cached_call = cache.CachedFunction(call, [9], {"k": 18})

    cached_call()
    sentinel = object()
    cached_call._value = sentinel
    cached_call()
    call.assert_called_once()


def test_call_CachedFunction_second_time_returns_value():
    call = mock.MagicMock(return_value=27)
    cached_call = cache.CachedFunction(call, [9], {"k": 18})

    cached_call()
    sentinel = object()
    cached_call._value = sentinel
    assert cached_call() is sentinel


@pytest.mark.asyncio
async def test_async_init_CachedFunction_sets_value_for_sentinel():
    async def call():
        pass

    cached_call = cache.CachedFunction(call, [], {})
    assert cached_call._value is cached_call._sentinel


@pytest.mark.asyncio
async def test_async_call_CachedFunction_first_time_sets_value():
    async def call(*args, **kwargs):
        assert len(args) == 1
        assert args[0] == 9
        assert len(kwargs) == 1
        assert kwargs["k"] == 18
        return 27

    cached_call = cache.CachedFunction(call, [9], {"k": 18})

    await cached_call()

    assert await cached_call._value == 27


@pytest.mark.asyncio
async def test_async_call_CachedFunction_first_time_returns_value():
    call = mock.AsyncMock(return_value=27)

    cached_call = cache.CachedFunction(call, [9], {"k": 18})

    assert await cached_call() == 27


@pytest.mark.asyncio
async def test_async_call_CachedFunction_second_time_does_not_reset_value():
    call = mock.AsyncMock(return_value=27)
    cached_call = cache.CachedFunction(call, [9], {"k": 18})

    async def sentinel_test_value():
        return 22

    await cached_call()
    cached_call._value = asyncio.create_task(sentinel_test_value())
    await cached_call()
    call.assert_called_once()


@pytest.mark.asyncio
async def test_async_call_CachedFunction_second_time_returns_value():
    call = mock.AsyncMock(return_value=27)
    cached_call = cache.CachedFunction(call, [9], {"k": 18})

    await cached_call()

    async def sentinel_test_value():
        return 22

    cached_call._value = asyncio.create_task(sentinel_test_value())
    assert await cached_call() == 22


def test_cached_function():
    spy = mock.MagicMock()
    sentinel = object()

    @cache.cached_function(9, 18, 27, name="nekokatt")
    def test(a, b, c, *, name):
        spy(a, b, c, name=name)
        return sentinel

    assert test() is sentinel
    assert test() is sentinel
    spy.assert_called_once_with(9, 18, 27, name="nekokatt")


@pytest.mark.asyncio
async def test_cached_function_coro():
    spy = mock.MagicMock()
    sentinel = object()

    @cache.cached_function(9, 18, 27, name="nekokatt")
    async def test(a, b, c, *, name):
        spy(a, b, c, name=name)
        return sentinel

    assert await test() is sentinel
    assert await test() is sentinel
    spy.assert_called_once_with(9, 18, 27, name="nekokatt")


def test_CachedFunction___qualname__():
    def potato():
        pass

    cached_call = cache.CachedFunction(potato, [], {})

    assert cached_call.__qualname__ == "test_CachedFunction___qualname__.<locals>.potato"


@pytest.fixture
def cached_property_usage():
    class CachedPropertyUsage:
        call_count = 0

        @cache.cached_property()
        def function(self):
            self.call_count += 1
            return self.call_count

    return CachedPropertyUsage()


@pytest.fixture
def async_cached_property_usage():
    class CachedPropertyUsage:
        call_count = 0

        @cache.cached_property()
        async def function(self):
            self.call_count += 1
            return self.call_count

    return CachedPropertyUsage()


def test_cached_property_makes_property_that_caches_result(cached_property_usage):
    assert cached_property_usage.function == 1
    assert cached_property_usage.function == 1
    assert cached_property_usage.function == 1
    assert cached_property_usage.call_count == 1
    cached_property_usage.call_count = 2
    assert cached_property_usage.function == 1


def test_cached_property_makes_property_that_can_have_cache_cleared(cached_property_usage):
    _ = cached_property_usage.function
    del cached_property_usage.function
    assert cached_property_usage.function == 2
    assert cached_property_usage.function == 2
    del cached_property_usage.function
    del cached_property_usage.function
    assert cached_property_usage.function == 3


@pytest.mark.asyncio
async def test_async_cached_property_makes_property_that_caches_result(async_cached_property_usage):
    assert await async_cached_property_usage.function == 1
    assert await async_cached_property_usage.function == 1
    assert await async_cached_property_usage.function == 1
    assert async_cached_property_usage.call_count == 1
    async_cached_property_usage.call_count = 2
    assert await async_cached_property_usage.function == 1


@pytest.mark.asyncio
async def test_async_cached_property_reuses_future(async_cached_property_usage):
    f1 = async_cached_property_usage.function
    assert isinstance(f1, asyncio.Future)
    f2 = async_cached_property_usage.function
    assert f1 is f2
    await f1
    f3 = async_cached_property_usage.function
    assert f3 is f1
    assert await f1 == await f3


@pytest.mark.asyncio
async def test_async_cached_property_makes_property_that_can_have_cache_cleared(async_cached_property_usage):
    _ = await async_cached_property_usage.function
    del async_cached_property_usage.function
    assert await async_cached_property_usage.function == 2
    assert await async_cached_property_usage.function == 2
    del async_cached_property_usage.function
    del async_cached_property_usage.function
    assert await async_cached_property_usage.function == 3


def test_cached_property_on_class_returns_self():
    class Class:
        @cache.cached_property()
        def foo(self):
            return 123

    # noinspection PyTypeHints
    assert isinstance(Class.foo, cache.CachedProperty)


def test_async_cached_property_on_class_returns_self():
    class Class:
        @cache.cached_property()
        async def foo(self):
            return 123

    # noinspection PyTypeHints
    assert isinstance(Class.foo, cache.CachedProperty)


def test_cached_property_works_on_slots_for_call():
    value = 0

    class Slotted:
        __slots__ = ("_cp_foo",)

        @cache.cached_property()
        def foo(self):
            nonlocal value
            value += 1
            return value

    s = Slotted()
    assert value == 0
    assert s.foo == 1
    assert value == 1
    assert s.foo == 1
    assert s.foo == 1
    assert value == 1


@pytest.mark.asyncio
async def test_async_cached_property_works_on_slots_for_call():
    value = 0

    class Slotted:
        __slots__ = ("_cp_foo",)

        @cache.cached_property()
        async def foo(self):
            nonlocal value
            value += 1
            return value

    s = Slotted()
    assert value == 0
    assert await s.foo == 1
    assert value == 1
    assert await s.foo == 1
    assert await s.foo == 1
    assert value == 1


def test_cached_property_works_on_slots_for_del():
    value = 0

    class Slotted:
        __slots__ = ("_cp_foo",)

        @cache.cached_property()
        def foo(self):
            nonlocal value
            value += 1
            return value

    s = Slotted()
    _ = s.foo
    del s.foo
    assert s.foo == 2
    assert s.foo == 2
    assert value == 2
    del s.foo
    del s.foo
    assert s.foo == 3
    assert value == 3


@pytest.mark.asyncio
async def test_async_cached_property_works_on_slots_for_del():
    value = 0

    class Slotted:
        __slots__ = ("_cp_foo",)

        @cache.cached_property()
        async def foo(self):
            nonlocal value
            value += 1
            return value

    s = Slotted()
    _ = await s.foo
    del s.foo
    assert await s.foo == 2
    assert await s.foo == 2
    assert value == 2
    del s.foo
    del s.foo
    assert await s.foo == 3
    assert value == 3
