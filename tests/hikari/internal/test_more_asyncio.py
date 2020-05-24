#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekokatt 2019-2020
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
import contextlib

import mock
import pytest

from hikari.internal import more_asyncio
from tests.hikari import _helpers


class CoroutineStub:
    def __init__(self, *args, **kwargs):
        self.awaited = False
        self.args = args
        self.kwargs = kwargs

    def __eq__(self, other):
        return isinstance(other, CoroutineStub) and self.args == other.args and self.kwargs == other.kwargs

    def __await__(self):
        self.awaited = True
        yield from asyncio.sleep(0.01).__await__()

    def __repr__(self):
        args = ", ".join(map(repr, self.args))
        kwargs = ", ".join(map(lambda k, v: f"{k!s}={v!r}", self.kwargs.items()))
        return f"({args}, {kwargs})"


class CoroutineFunctionStub:
    def __call__(self, *args, **kwargs):
        return CoroutineStub(*args, **kwargs)


class TestCoroutineFunctionStubUsedInTests:
    def test_coro_stub_eq(self):
        assert CoroutineStub(9, 18, x=27) == CoroutineStub(9, 18, x=27)

    # POC for the stuff we use in tests
    def test_coro_stub_neq(self):
        assert CoroutineStub(9, 18, x=27) != CoroutineStub(9, 18, x=36)


class TestCompletedFuture:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("args", [(), (12,)])
    async def test_is_awaitable(self, args):
        await more_asyncio.completed_future(*args)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("args", [(), (12,)])
    async def test_is_completed(self, args):
        future = more_asyncio.completed_future(*args)
        assert future.done()

    @pytest.mark.asyncio
    async def test_default_result_is_none(self):
        assert more_asyncio.completed_future().result() is None

    @pytest.mark.asyncio
    async def test_non_default_result(self):
        assert more_asyncio.completed_future(...).result() is ...


class TestIsAsyncIterator:
    def test_on_inst(self):
        class AsyncIterator:
            async def __anext__(self):
                return None

        assert more_asyncio.is_async_iterator(AsyncIterator())

    def test_on_class(self):
        class AsyncIterator:
            async def __anext__(self):
                return ...

        assert more_asyncio.is_async_iterator(AsyncIterator)

    @pytest.mark.asyncio
    async def test_on_genexp(self):
        async def genexp():
            yield ...
            yield ...

        exp = genexp()
        try:
            assert not more_asyncio.is_async_iterator(exp)
        finally:
            await exp.aclose()

    def test_on_iterator(self):
        class Iter:
            def __next__(self):
                return ...

        assert not more_asyncio.is_async_iterator(Iter())

    def test_on_iterator_class(self):
        class Iter:
            def __next__(self):
                return ...

        assert not more_asyncio.is_async_iterator(Iter)

    def test_on_async_iterable(self):
        class AsyncIter:
            def __aiter__(self):
                yield ...

        assert not more_asyncio.is_async_iterator(AsyncIter())

    def test_on_async_iterable_class(self):
        class AsyncIter:
            def __aiter__(self):
                yield ...

        assert not more_asyncio.is_async_iterator(AsyncIter)


class TestIsAsyncIterable:
    def test_on_instance(self):
        class AsyncIter:
            async def __aiter__(self):
                yield ...

        assert more_asyncio.is_async_iterable(AsyncIter())

    def test_on_class(self):
        class AsyncIter:
            async def __aiter__(self):
                yield ...

        assert more_asyncio.is_async_iterable(AsyncIter)

    def test_on_delegate(self):
        class AsyncIterator:
            async def __anext__(self):
                ...

        class AsyncIterable:
            def __aiter__(self):
                return AsyncIterator()

        assert more_asyncio.is_async_iterable(AsyncIterable())

    def test_on_delegate_class(self):
        class AsyncIterator:
            async def __anext__(self):
                ...

        class AsyncIterable:
            def __aiter__(self):
                return AsyncIterator()

        assert more_asyncio.is_async_iterable(AsyncIterable)

    def test_on_inst(self):
        class AsyncIterator:
            async def __anext__(self):
                return None

        assert more_asyncio.is_async_iterator(AsyncIterator())

    def test_on_AsyncIterator(self):
        class AsyncIterator:
            async def __anext__(self):
                return ...

        assert not more_asyncio.is_async_iterable(AsyncIterator())

    def test_on_AsyncIterator_class(self):
        class AsyncIterator:
            async def __anext__(self):
                return ...

        assert not more_asyncio.is_async_iterable(AsyncIterator)
