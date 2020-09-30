# -*- coding: utf-8 -*-
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
import asyncio

import pytest

from hikari.internal import aio
from tests.hikari import hikari_test_helpers


class CoroutineStub:
    def __init__(self, *args, **kwargs):
        self.awaited = False
        self.args = args
        self.kwargs = kwargs

    def __eq__(self, other):
        return isinstance(other, CoroutineStub) and self.args == other.args and self.kwargs == other.kwargs

    def __await__(self):
        self.awaited = True
        return hikari_test_helpers.idle().__await__()

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
        await aio.completed_future(*args)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("args", [(), (12,)])
    async def test_is_completed(self, args):
        future = aio.completed_future(*args)
        assert future.done()

    @pytest.mark.asyncio
    async def test_default_result_is_none(self):
        assert aio.completed_future().result() is None

    @pytest.mark.asyncio
    async def test_non_default_result(self):
        assert aio.completed_future(...).result() is ...


class TestIsAsyncIterator:
    def test_on_inst(self):
        class AsyncIterator:
            async def __anext__(self):
                return None

        assert aio.is_async_iterator(AsyncIterator())

    def test_on_class(self):
        class AsyncIterator:
            async def __anext__(self):
                return ...

        assert aio.is_async_iterator(AsyncIterator)

    @pytest.mark.asyncio
    async def test_on_genexp(self):
        async def genexp():
            yield ...
            yield ...

        exp = genexp()
        try:
            assert not aio.is_async_iterator(exp)
        finally:
            await exp.aclose()

    def test_on_iterator(self):
        class Iter:
            def __next__(self):
                return ...

        assert not aio.is_async_iterator(Iter())

    def test_on_iterator_class(self):
        class Iter:
            def __next__(self):
                return ...

        assert not aio.is_async_iterator(Iter)

    def test_on_async_iterable(self):
        class AsyncIter:
            def __aiter__(self):
                yield ...

        assert not aio.is_async_iterator(AsyncIter())

    def test_on_async_iterable_class(self):
        class AsyncIter:
            def __aiter__(self):
                yield ...

        assert not aio.is_async_iterator(AsyncIter)


class TestIsAsyncIterable:
    def test_on_instance(self):
        class AsyncIter:
            async def __aiter__(self):
                yield ...

        assert aio.is_async_iterable(AsyncIter())

    def test_on_class(self):
        class AsyncIter:
            async def __aiter__(self):
                yield ...

        assert aio.is_async_iterable(AsyncIter)

    def test_on_delegate(self):
        class AsyncIterator:
            async def __anext__(self):
                ...

        class AsyncIterable:
            def __aiter__(self):
                return AsyncIterator()

        assert aio.is_async_iterable(AsyncIterable())

    def test_on_delegate_class(self):
        class AsyncIterator:
            async def __anext__(self):
                ...

        class AsyncIterable:
            def __aiter__(self):
                return AsyncIterator()

        assert aio.is_async_iterable(AsyncIterable)

    def test_on_inst(self):
        class AsyncIterator:
            async def __anext__(self):
                return None

        assert aio.is_async_iterator(AsyncIterator())

    def test_on_AsyncIterator(self):
        class AsyncIterator:
            async def __anext__(self):
                return ...

        assert not aio.is_async_iterable(AsyncIterator())

    def test_on_AsyncIterator_class(self):
        class AsyncIterator:
            async def __anext__(self):
                return ...

        assert not aio.is_async_iterable(AsyncIterator)


@pytest.mark.asyncio
class TestFirstCompleted:
    @hikari_test_helpers.timeout()
    async def test_first_future_completes(self, event_loop):
        f1 = event_loop.create_future()
        f2 = event_loop.create_future()
        f3 = event_loop.create_future()

        f1.set_result(None)
        await aio.first_completed(f1, f2, f3)
        assert f1.done()
        assert f2.cancelled()
        assert f3.cancelled()

    @hikari_test_helpers.timeout()
    async def test_second_future_completes(self, event_loop):
        f1 = event_loop.create_future()
        f2 = event_loop.create_future()
        f3 = event_loop.create_future()

        f2.set_result(None)
        await aio.first_completed(f1, f2, f3)
        assert f1.cancelled()
        assert f2.done()
        assert f3.cancelled()

    @hikari_test_helpers.timeout()
    async def test_timeout_propagates(self, event_loop):
        f1 = event_loop.create_future()
        f2 = event_loop.create_future()
        f3 = event_loop.create_future()

        with pytest.raises(asyncio.TimeoutError):
            await aio.first_completed(f1, f2, f3, timeout=0.01)

        assert f1.cancelled()
        assert f2.cancelled()
        assert f3.cancelled()

    @hikari_test_helpers.timeout()
    async def test_cancelled_propagates(self, event_loop):
        f1 = event_loop.create_future()
        f2 = event_loop.create_future()
        f3 = event_loop.create_future()
        f1.cancel()
        f2.cancel()
        f3.cancel()

        with pytest.raises(asyncio.CancelledError):
            await aio.first_completed(f1, f2, f3)

        assert f1.cancelled()
        assert f2.cancelled()
        assert f3.cancelled()

    @hikari_test_helpers.timeout()
    async def test_single_cancelled_propagates(self, event_loop):
        f1 = event_loop.create_future()
        f2 = event_loop.create_future()
        f3 = event_loop.create_future()
        f1.cancel()

        with pytest.raises(asyncio.CancelledError):
            await aio.first_completed(f1, f2, f3)

        assert f1.cancelled()
        assert f2.cancelled()
        assert f3.cancelled()

    # If the CI runners are slow, this may be flaky.
    @hikari_test_helpers.retry(3)
    @hikari_test_helpers.timeout()
    async def test_result_propagates(self, event_loop):
        f1 = event_loop.create_future()
        f2 = event_loop.create_future()
        f3 = event_loop.create_future()
        f3.set_result(22)

        await aio.first_completed(f1, f2, f3)

        assert f1.cancelled()
        assert f2.cancelled()
        assert f3.done()
        assert not f3.cancelled()

    # If the CI runners are slow, this may be flaky.
    @hikari_test_helpers.retry(3)
    @hikari_test_helpers.timeout()
    async def test_exception_propagates(self, event_loop):
        f1 = event_loop.create_future()
        f2 = event_loop.create_future()
        f3 = event_loop.create_future()

        error = FileExistsError("aaaa")
        f2.set_exception(error)

        with pytest.raises(FileExistsError):
            await aio.first_completed(f1, f2, f3)

        assert f1.cancelled()
        assert f2.done()
        assert f3.cancelled()


@pytest.mark.asyncio
class TestAllOf:
    # If the CI runners are slow, this may be flaky.
    @hikari_test_helpers.retry(3)
    @hikari_test_helpers.timeout()
    async def test_waits_for_all(self, event_loop):
        f1 = event_loop.create_future()
        f2 = event_loop.create_future()
        f3 = event_loop.create_future()

        waiter = event_loop.create_task(aio.all_of(f1, f2, f3))
        await hikari_test_helpers.idle(0.1)
        assert not waiter.cancelled()
        assert not waiter.done()

        f1.set_result(1)
        await hikari_test_helpers.idle(0.1)
        assert not waiter.cancelled()
        assert not waiter.done()

        f2.set_result(2)
        await hikari_test_helpers.idle(0.1)
        assert not waiter.cancelled()
        assert not waiter.done()

        f3.set_result(3)
        await hikari_test_helpers.idle(0.1)
        assert not waiter.cancelled()
        assert waiter.done()

    # If the CI runners are slow, this may be flaky.
    @hikari_test_helpers.retry(3)
    @hikari_test_helpers.timeout()
    async def test_cancels_all_if_one_errors(self, event_loop):
        f1 = event_loop.create_future()
        f2 = event_loop.create_future()
        f3 = event_loop.create_future()

        waiter = event_loop.create_task(aio.all_of(f1, f2, f3))
        # Wait a little bit and ensure asyncio doesn't kill it for some reason
        await asyncio.sleep(0.25)
        assert not waiter.cancelled()
        assert not waiter.done()

        f2.set_exception(FileNotFoundError("boop"))
        with pytest.raises(FileNotFoundError, match="boop"):
            await waiter

        assert f1.cancelled()
        assert f3.cancelled()

    # If the CI runners are slow, this may be flaky.
    @hikari_test_helpers.retry(3)
    @hikari_test_helpers.timeout()
    async def test_cancels_all_if_timeout(self, event_loop):
        f1 = event_loop.create_future()
        f2 = event_loop.create_future()
        f3 = event_loop.create_future()

        waiter = event_loop.create_task(aio.all_of(f1, f2, f3, timeout=0.1))
        with pytest.raises(asyncio.TimeoutError):
            await waiter
        assert not waiter.cancelled(), "future was forcefully cancelled?"
        assert waiter.done(), "asyncio.TimeoutError not raised?"

    # If the CI runners are slow, this may be flaky.
    @hikari_test_helpers.retry(3)
    @hikari_test_helpers.timeout()
    async def test_cancels_all_if_cancelled(self, event_loop):
        f1 = event_loop.create_future()
        f2 = event_loop.create_future()
        f3 = event_loop.create_future()

        waiter = event_loop.create_task(aio.all_of(f1, f2, f3))
        event_loop.call_later(0.01, lambda *_: waiter.cancel())
        with pytest.raises(asyncio.CancelledError):
            await waiter
        assert waiter.cancelled(), "future was forcefully cancelled?"
        assert waiter.done(), "asyncio.CancelledError not raised?"
