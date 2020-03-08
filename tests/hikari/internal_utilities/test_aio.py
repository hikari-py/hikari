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

import async_timeout
import cymock as mock
import pytest

from hikari.internal_utilities import aio
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


class TestOptionalAwait:
    @pytest.mark.asyncio
    async def test_optional_await_gets_run_with_await(self):
        coro_fn = CoroutineFunctionStub()

        wrapped_coro_fn = aio.optional_await()(coro_fn)

        with mock.patch("asyncio.create_task", new=mock.AsyncMock()) as create_task:
            await wrapped_coro_fn(9, 18, 27)
            create_task.assert_called_with(coro_fn(9, 18, 27), name=None)

    @pytest.mark.asyncio
    async def test_optional_await_gets_run_without_await(self):
        coro_fn = CoroutineFunctionStub()

        wrapped_coro_fn = aio.optional_await()(coro_fn)

        with mock.patch("asyncio.create_task") as create_task:
            wrapped_coro_fn(9, 18, 27)
            create_task.assert_called_with(coro_fn(9, 18, 27), name=None)

    @pytest.mark.asyncio
    async def test_optional_await_with_description(self):
        coro_fn = CoroutineFunctionStub()

        wrapped_coro_fn = aio.optional_await("foo")(coro_fn)

        with mock.patch("asyncio.create_task", new=mock.AsyncMock()) as create_task:
            await wrapped_coro_fn(9, 18, 27)
            create_task.assert_called_with(coro_fn(9, 18, 27), name="foo")

    @pytest.mark.asyncio
    async def test_optional_await_shielded(self):
        coro_fn = CoroutineFunctionStub()
        wrapped_coro_fn = aio.optional_await(shield=True)(coro_fn)

        shielded_coro = CoroutineStub()

        with mock.patch("asyncio.shield", new=mock.MagicMock(return_value=shielded_coro)) as shield:
            with mock.patch("asyncio.create_task", new=mock.AsyncMock()) as create_task:
                await wrapped_coro_fn(9, 18, 27)
                shield.assert_called_with(coro_fn(9, 18, 27))
                create_task.assert_called_with(shielded_coro, name=None)


class TestEventDelegate:
    EXCEPTION_EVENT = "exception"

    @pytest.fixture
    def delegate(self):
        return _helpers.unslot_class(aio.EventDelegate)(self.EXCEPTION_EVENT)

    # noinspection PyTypeChecker
    @_helpers.assert_raises(type_=TypeError)
    def test_add_not_coroutine_function(self, delegate):
        delegate.add("foo", lambda: None)

    def test_add_coroutine_function_when_no_others_with_name(self, delegate):
        async def coro_fn():
            pass

        delegate.add("foo", coro_fn)
        assert coro_fn in delegate._listeners["foo"]

    def test_add_coroutine_function_when_list_exists(self, delegate):
        async def coro_fn1():
            pass

        async def coro_fn2():
            pass

        delegate.add("foo", coro_fn1)
        delegate.add("foo", coro_fn2)
        assert coro_fn1 in delegate._listeners["foo"]
        assert coro_fn2 in delegate._listeners["foo"]

    def test_remove_non_existing_mux_list(self, delegate):
        async def remove_this():
            pass

        # should not raise
        delegate.remove("foo", remove_this)

    def test_remove_non_existing_mux(self, delegate):
        delegate._listeners["foo"] = []

        async def remove_this():
            pass

        # should not raise
        delegate.remove("foo", remove_this)

    def test_remove_when_list_left_empty_removes_key(self, delegate):
        async def remove_this():
            pass

        delegate._listeners["foo"] = [remove_this]

        delegate.remove("foo", remove_this)

        assert "foo" not in delegate._listeners

    def test_remove_when_list_not_left_empty_removes_coroutine_function(self, delegate):
        async def remove_this():
            pass

        delegate._listeners["foo"] = [remove_this, remove_this]

        delegate.remove("foo", remove_this)

        assert delegate._listeners["foo"] == [remove_this]

    def test_dispatch_to_existing_muxes(self, delegate):
        delegate._catch = mock.MagicMock()
        mock_coro_fn1 = mock.MagicMock()
        mock_coro_fn2 = mock.MagicMock()
        mock_coro_fn3 = mock.MagicMock()

        delegate._listeners["foo"] = [mock_coro_fn1, mock_coro_fn2]
        delegate._listeners["bar"] = [mock_coro_fn3]

        args = ("a", "b", "c")

        with mock.patch("asyncio.gather") as gather:
            delegate.dispatch("foo", *args)
            gather.assert_called_once_with(
                delegate._catch(mock_coro_fn1, "foo", args), delegate._catch(mock_coro_fn2, "foo", args)
            )

    def test_dispatch_to_non_existant_muxes(self, delegate):
        # Should not throw.
        delegate.dispatch("foo", "a", "b", "c")

    @pytest.mark.asyncio
    async def test_dispatch_is_awaitable_if_nothing_is_invoked(self, delegate):
        coro_fn = mock.AsyncMock()

        delegate.add("foo", coro_fn)
        await delegate.dispatch("bar")

    @pytest.mark.asyncio
    async def test_dispatch_is_awaitable_if_something_is_invoked(self, delegate):
        coro_fn = mock.AsyncMock()

        delegate.add("foo", coro_fn)
        await delegate.dispatch("foo")

    @pytest.mark.asyncio
    @pytest.mark.parametrize("predicate_return", (True, False))
    @pytest.mark.parametrize(
        ("in_event_args", "expected_result"), [((), None,), ((12,), 12), ((12, 22, 33), (12, 22, 33))]
    )
    @_helpers.timeout_after(1)
    async def test_dispatch_awakens_matching_futures(
        self, delegate, event_loop, predicate_return, in_event_args, expected_result
    ):
        future1 = event_loop.create_future()
        future2 = event_loop.create_future()
        future3 = event_loop.create_future()
        future4 = event_loop.create_future()

        predicate1 = mock.MagicMock(return_value=predicate_return)
        predicate2 = mock.MagicMock(return_value=predicate_return)
        predicate3 = mock.MagicMock(return_value=True)
        predicate4 = mock.MagicMock(return_value=False)

        delegate._waiters["foobar"] = {}
        delegate._waiters["barbaz"] = {future3: predicate3}
        delegate._waiters["foobar"][future1] = predicate1
        delegate._waiters["foobar"][future2] = predicate2
        # Shouldn't be invoked, as the predicate is always false-returning.
        delegate._waiters["foobar"][future4] = predicate4

        await delegate.dispatch("foobar", *in_event_args)

        assert future1.done() is predicate_return
        predicate1.assert_called_once_with(*in_event_args)
        assert future2.done() is predicate_return
        predicate2.assert_called_once_with(*in_event_args)
        assert future3.done() is False
        predicate3.assert_not_called()
        assert future4.done() is False
        predicate4.assert_called_once_with(*in_event_args)

        if predicate_return:
            assert await future1 == expected_result
            assert await future2 == expected_result

    @pytest.mark.asyncio
    @pytest.mark.parametrize("predicate_return", (True, False))
    @pytest.mark.parametrize(
        ("in_event_args", "expected_result"), [((), None,), ((12,), 12), ((12, 22, 33), (12, 22, 33))]
    )
    @_helpers.timeout_after(1)
    async def test_dispatch_removes_awoken_future(
        self, delegate, event_loop, predicate_return, in_event_args, expected_result
    ):
        future = event_loop.create_future()

        predicate = mock.MagicMock()

        delegate._waiters["foobar"] = {}
        delegate._waiters["foobar"][future] = predicate
        # Add a second future that never gets hit so the weakref map is not dropped from being
        # empty.
        delegate._waiters["foobar"][event_loop.create_future()] = lambda *_: False

        await delegate.dispatch("foobar", *in_event_args)
        predicate.assert_called_once_with(*in_event_args)
        predicate.reset_mock()

        await delegate.dispatch("foobar", *in_event_args)
        predicate.assert_not_called()
        assert future not in delegate._waiters["foobar"]

    @pytest.mark.asyncio
    @_helpers.timeout_after(1)
    async def test_dispatch_returns_exception_to_caller(self, delegate, event_loop):
        predicate1 = mock.MagicMock(side_effect=RuntimeError())
        predicate2 = mock.MagicMock(return_value=False)

        future1 = event_loop.create_future()
        future2 = event_loop.create_future()

        delegate._waiters["foobar"] = {}
        delegate._waiters["foobar"][future1] = predicate1
        delegate._waiters["foobar"][future2] = predicate2

        await delegate.dispatch("foobar", object(), object(), object())

        try:
            await future1
            assert False, "No RuntimeError propagated :("
        except RuntimeError:
            pass

        # Isn't done, should raise InvalidStateError.
        try:
            future2.exception()
            assert False, "this future should still be running but isn't!"
        except asyncio.InvalidStateError:
            pass

    @pytest.mark.asyncio
    async def test_waiter_map_deleted_if_already_empty(self, delegate):
        delegate._waiters["foobar"] = {}
        await delegate.dispatch("foobar")
        assert "foobar" not in delegate._waiters

    @pytest.mark.asyncio
    async def test_waiter_map_deleted_if_made_empty_during_this_dispatch(self, delegate):
        delegate._waiters["foobar"] = {mock.MagicMock(): mock.MagicMock(return_value=True)}
        await delegate.dispatch("foobar")
        assert "foobar" not in delegate._waiters

    @pytest.mark.asyncio
    async def test_waiter_map_not_deleted_if_not_empty(self, delegate):
        delegate._waiters["foobar"] = {mock.MagicMock(): mock.MagicMock(return_value=False)}
        await delegate.dispatch("foobar")
        assert "foobar" in delegate._waiters

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("in_event_args", "expected_result"), [((), None,), ((12,), 12), ((12, 22, 33), (12, 22, 33))]
    )
    @_helpers.timeout_after(2)
    async def test_wait_for_returns_matching_event_args_when_invoked(self, delegate, in_event_args, expected_result):
        predicate = mock.MagicMock(return_value=True)
        future = delegate.wait_for("foobar", timeout=5, predicate=predicate)

        await delegate.dispatch("foobar", *in_event_args)

        await asyncio.sleep(0.5)

        assert future.done()
        actual_result = await future
        assert actual_result == expected_result
        predicate.assert_called_once_with(*in_event_args)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("in_event_args", "expected_result"), [((), None,), ((12,), 12), ((12, 22, 33), (12, 22, 33))]
    )
    @_helpers.timeout_after(2)
    async def test_wait_for_returns_matching_event_args_when_invoked_but_no_predicate_match(
        self, delegate, in_event_args, expected_result
    ):
        predicate = mock.MagicMock(return_value=False)
        future = delegate.wait_for("foobar", timeout=5, predicate=predicate)
        await delegate.dispatch("foobar", *in_event_args)

        await asyncio.sleep(0.5)

        assert not future.done()
        predicate.assert_called_once_with(*in_event_args)

    @pytest.mark.asyncio
    @_helpers.assert_raises(type_=asyncio.TimeoutError)
    async def test_wait_for_hits_timeout_and_raises(self, delegate):
        predicate = mock.MagicMock(return_value=False)
        await delegate.wait_for("foobar", timeout=1, predicate=predicate)
        assert False, "event was marked as succeeded when it shouldn't have been"

    @pytest.mark.asyncio
    @_helpers.timeout_after(2)
    @_helpers.assert_raises(type_=RuntimeError)
    async def test_wait_for_raises_predicate_errors(self, delegate):
        predicate = mock.MagicMock(side_effect=RuntimeError)
        future = delegate.wait_for("foobar", timeout=1, predicate=predicate)
        await delegate.dispatch("foobar", object())
        await future

    @pytest.mark.asyncio
    @pytest.mark.parametrize("predicate_side_effect", (True, False, RuntimeError()))
    @_helpers.timeout_after(5)
    @_helpers.assert_raises(type_=asyncio.TimeoutError)
    async def test_other_events_in_same_waiter_event_name_do_not_awaken_us(
        self, delegate, predicate_side_effect, event_loop
    ):
        delegate._waiters["foobar"] = {event_loop.create_future(): mock.MagicMock(side_effect=predicate_side_effect)}

        future = delegate.wait_for("foobar", timeout=1, predicate=mock.MagicMock(return_value=False))

        await asyncio.gather(future, *(delegate.dispatch("foobar") for _ in range(5)))

    @pytest.mark.asyncio
    async def test_catch_happy_path(self, delegate):
        callback = mock.AsyncMock()
        delegate.handle_exception = mock.MagicMock()
        await delegate._catch(callback, "wubalubadubdub", ("blep1", "blep2", "blep3"))
        callback.assert_awaited_once_with("blep1", "blep2", "blep3")
        delegate.handle_exception.assert_not_called()

    @pytest.mark.asyncio
    async def test_catch_sad_path(self, delegate):
        ex = RuntimeError()
        callback = mock.AsyncMock(side_effect=ex)
        delegate.handle_exception = mock.MagicMock()
        await delegate._catch(callback, "wubalubadubdub", ("blep1", "blep2", "blep3"))
        delegate.handle_exception.assert_called_once_with(ex, "wubalubadubdub", ("blep1", "blep2", "blep3"), callback)

    def test_handle_exception_dispatches_exception_event_with_context(self, delegate):
        delegate.dispatch = mock.MagicMock()

        ex = RuntimeError()
        event_name = "foof"
        args = ("aawwwww", "oooo", "ooooooo", "oo.")
        callback = mock.AsyncMock()

        delegate.handle_exception(ex, event_name, args, callback)

        expected_ctx = aio.EventExceptionContext(event_name, callback, args, ex)
        delegate.dispatch.assert_called_once_with(self.EXCEPTION_EVENT, expected_ctx)

    def test_handle_exception_will_not_recursively_invoke_exception_handler_event(self, delegate):
        delegate.dispatch = mock.MagicMock()

        ex = RuntimeError()
        event_name = self.EXCEPTION_EVENT
        args = ("aawwwww", "oooo", "ooooooo", "oo.")
        callback = mock.AsyncMock()

        delegate.handle_exception(ex, event_name, args, callback)
        delegate.dispatch.assert_not_called()


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


class TestMaybeTimeout:
    @pytest.mark.asyncio
    @_helpers.timeout_after(2)
    @pytest.mark.parametrize("wait_for", (0, -1, -1.5, None))
    async def test_never_times_out_if_cannot_wait(self, wait_for):
        try:
            async with async_timeout.timeout(1):
                try:
                    async with aio.maybe_timeout(wait_for):
                        await asyncio.sleep(100)
                    assert False, "asyncio.sleep completed, but it should have hit the test timeout"
                except asyncio.TimeoutError:
                    assert False, "timed out unexpectedly"
            # noinspection PyUnreachableCode
            assert False, "did not time out"
        except asyncio.TimeoutError:
            pass

    @pytest.mark.asyncio
    @_helpers.timeout_after(2)
    @_helpers.assert_raises(type_=asyncio.TimeoutError)
    async def test_times_out(self):
        async with aio.maybe_timeout(1):
            await asyncio.sleep(100)
