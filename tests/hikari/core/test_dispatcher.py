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
from unittest import mock

import pytest

from hikari.core import dispatcher
from hikari.core import events
from tests.hikari import _helpers


class TestEvent1(events.HikariEvent):
    ...


class TestEvent2(events.HikariEvent):
    ...


class TestEvent3(events.HikariEvent):
    ...


class TestEventDispatcher:
    EXCEPTION_EVENT = "exception"

    @pytest.fixture
    def delegate(self):
        return _helpers.unslot_class(dispatcher.EventDispatcher)()

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

        ctx = TestEvent1()

        delegate._listeners[TestEvent1] = [mock_coro_fn1, mock_coro_fn2]
        delegate._listeners[TestEvent2] = [mock_coro_fn3]

        with mock.patch("asyncio.gather") as gather:
            delegate.dispatch(ctx)
            gather.assert_called_once_with(delegate._catch(mock_coro_fn1, ctx), delegate._catch(mock_coro_fn2, ctx))

    def test_dispatch_to_non_existant_muxes(self, delegate):
        # Should not throw.
        delegate._waiters = {}
        delegate._listeners = {}
        delegate.dispatch(TestEvent1())
        assert delegate._waiters == {}
        assert delegate._listeners == {}

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
    @_helpers.timeout_after(1)
    async def test_dispatch_invokes_future_waker_if_registered_with_futures(self, delegate, event_loop):
        delegate._waiters[TestEvent1] = {event_loop.create_future(): lambda _: False}

    @pytest.mark.asyncio
    @_helpers.timeout_after(1)
    async def test_dispatch_returns_exception_to_caller(self, delegate, event_loop):
        predicate1 = mock.MagicMock(side_effect=RuntimeError())
        predicate2 = mock.MagicMock(return_value=False)

        future1 = event_loop.create_future()
        future2 = event_loop.create_future()

        ctx = TestEvent3()

        delegate._waiters[TestEvent3] = {}
        delegate._waiters[TestEvent3][future1] = predicate1
        delegate._waiters[TestEvent3][future2] = predicate2

        await delegate.dispatch(ctx)

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
    @_helpers.timeout_after(1)
    async def test_waiter_map_deleted_if_made_empty_during_this_dispatch(self, delegate):
        delegate._waiters[TestEvent1] = {mock.MagicMock(): mock.MagicMock(return_value=True)}
        delegate.dispatch(TestEvent1())
        await asyncio.sleep(0.1)
        assert TestEvent1 not in delegate._waiters

    @pytest.mark.asyncio
    @_helpers.timeout_after(1)
    async def test_waiter_map_not_deleted_if_not_empty(self, delegate):
        delegate._waiters["foobar"] = {mock.MagicMock(): mock.MagicMock(return_value=False)}
        delegate.dispatch("foobar")
        await asyncio.sleep(0.1)
        assert "foobar" in delegate._waiters

    @pytest.mark.asyncio
    @_helpers.timeout_after(2)
    async def test_wait_for_returns_event(self, delegate):
        predicate = mock.MagicMock(return_value=True)
        future = delegate.wait_for(TestEvent1, timeout=5, predicate=predicate)

        ctx = TestEvent1()
        await delegate.dispatch(ctx)

        await asyncio.sleep(0.1)

        assert future.done()
        actual_result = await future
        assert actual_result == ctx
        predicate.assert_called_once_with(ctx)

    @pytest.mark.asyncio
    @_helpers.timeout_after(2)
    async def test_wait_for_returns_matching_event_args_when_invoked_but_no_predicate_match(self, delegate):
        predicate = mock.MagicMock(return_value=False)
        ctx = TestEvent3()
        future = delegate.wait_for(TestEvent3, timeout=5, predicate=predicate)
        await delegate.dispatch(ctx)

        await asyncio.sleep(0.1)

        assert not future.done()
        predicate.assert_called_once_with(ctx)

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
        ctx = TestEvent1()
        future = delegate.wait_for(TestEvent1, timeout=1, predicate=predicate)
        await delegate.dispatch(ctx)
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
        event = TestEvent1()
        delegate.handle_exception = mock.MagicMock()
        await delegate._catch(callback, event)
        callback.assert_awaited_once_with(event)
        delegate.handle_exception.assert_not_called()

    @pytest.mark.asyncio
    async def test_catch_sad_path(self, delegate):
        ex = RuntimeError()
        callback = mock.AsyncMock(side_effect=ex)
        delegate.handle_exception = mock.MagicMock()
        ctx = TestEvent3()
        await delegate._catch(callback, ctx)
        delegate.handle_exception.assert_called_once_with(ex, ctx, callback)

    def test_handle_exception_dispatches_exception_event_with_context(self, delegate):
        delegate.dispatch = mock.MagicMock()

        ex = RuntimeError()
        event = TestEvent1()
        callback = mock.AsyncMock()

        delegate.handle_exception(ex, event, callback)

        expected_ctx = events.ExceptionEvent(ex, event, callback)
        delegate.dispatch.assert_called_once_with(expected_ctx)

    def test_handle_exception_will_not_recursively_invoke_exception_handler_event(self, delegate):
        delegate.dispatch = mock.MagicMock()
        delegate.handle_exception(RuntimeError(), events.ExceptionEvent(..., ..., ...), mock.AsyncMock())
        delegate.dispatch.assert_not_called()
