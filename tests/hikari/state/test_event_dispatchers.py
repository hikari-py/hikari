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

import mock
import pytest

from hikari import events
from hikari.state import dispatchers
from tests.hikari import _helpers


class StubEvent1(events.HikariEvent):
    ...


class StubEvent2(events.HikariEvent):
    ...


class StubEvent3(events.HikariEvent):
    ...


class TestEventDispatcherImpl:
    @pytest.fixture
    def dispatcher_inst(self):
        return _helpers.unslot_class(dispatchers.IntentAwareEventDispatcherImpl)(None)

    # noinspection PyTypeChecker
    @_helpers.assert_raises(type_=TypeError)
    def test_add_not_coroutine_function(self, dispatcher_inst):
        dispatcher_inst.add_listener("foo", lambda: None)

    def _coro_fn(self, lambda_ex):
        async def wrap(*args, **kwargs):
            return lambda_ex(*args, **kwargs)

        return wrap

    def test_close(self, dispatcher_inst, event_loop):
        futures = []

        def fut():
            futures.append(event_loop.create_future())
            return futures[-1]

        test_event_1_waiters = {
            fut(): lambda _: False,
            fut(): lambda _: False,
            fut(): lambda _: False,
            fut(): lambda _: False,
        }

        test_event_2_waiters = {
            fut(): lambda _: False,
            fut(): lambda _: False,
            fut(): lambda _: False,
            fut(): lambda _: False,
        }

        test_event_1_listeners = [self._coro_fn(lambda xxx: None)]

        test_event_2_listeners = [
            self._coro_fn(lambda xxx: None),
            self._coro_fn(lambda xxx: None),
            self._coro_fn(lambda xxx: None),
            self._coro_fn(lambda xxx: None),
        ]

        dispatcher_inst._waiters = (
            waiters := {StubEvent1: test_event_1_waiters, StubEvent2: test_event_2_waiters,}
        )

        dispatcher_inst._listeners = (
            listeners := {StubEvent1: test_event_1_listeners, StubEvent2: test_event_2_listeners,}
        )

        dispatcher_inst.close()

        assert not waiters
        assert not listeners

        for i, f in enumerate(futures):
            assert f.cancelled(), str(i)

    def test_add_coroutine_function_when_no_others_with_name(self, dispatcher_inst):
        async def coro_fn():
            pass

        dispatcher_inst.add_listener("foo", coro_fn)
        assert coro_fn in dispatcher_inst._listeners["foo"]

    def test_add_coroutine_function_when_list_exists(self, dispatcher_inst):
        async def coro_fn1():
            pass

        async def coro_fn2():
            pass

        dispatcher_inst.add_listener("foo", coro_fn1)
        dispatcher_inst.add_listener("foo", coro_fn2)
        assert coro_fn1 in dispatcher_inst._listeners["foo"]
        assert coro_fn2 in dispatcher_inst._listeners["foo"]

    def test_remove_non_existing_mux_list(self, dispatcher_inst):
        async def remove_this():
            pass

        # should not raise
        dispatcher_inst.remove_listener("foo", remove_this)

    def test_remove_non_existing_mux(self, dispatcher_inst):
        dispatcher_inst._listeners["foo"] = []

        async def remove_this():
            pass

        # should not raise
        dispatcher_inst.remove_listener("foo", remove_this)

    def test_remove_when_list_left_empty_removes_key(self, dispatcher_inst):
        async def remove_this():
            pass

        dispatcher_inst._listeners["foo"] = [remove_this]

        dispatcher_inst.remove_listener("foo", remove_this)

        assert "foo" not in dispatcher_inst._listeners

    def test_remove_when_list_not_left_empty_removes_coroutine_function(self, dispatcher_inst):
        async def remove_this():
            pass

        dispatcher_inst._listeners["foo"] = [remove_this, remove_this]

        dispatcher_inst.remove_listener("foo", remove_this)

        assert dispatcher_inst._listeners["foo"] == [remove_this]

    def test_dispatch_to_existing_muxes(self, dispatcher_inst):
        dispatcher_inst._catch = mock.MagicMock()
        mock_coro_fn1 = mock.MagicMock()
        mock_coro_fn2 = mock.MagicMock()
        mock_coro_fn3 = mock.MagicMock()

        ctx = StubEvent1()

        dispatcher_inst._listeners[StubEvent1] = [mock_coro_fn1, mock_coro_fn2]
        dispatcher_inst._listeners[StubEvent2] = [mock_coro_fn3]

        with mock.patch("asyncio.gather") as gather:
            dispatcher_inst.dispatch_event(ctx)
            gather.assert_called_once_with(
                dispatcher_inst._catch(mock_coro_fn1, ctx), dispatcher_inst._catch(mock_coro_fn2, ctx)
            )

    def test_dispatch_to_non_existant_muxes(self, dispatcher_inst):
        # Should not throw.
        dispatcher_inst._waiters = {}
        dispatcher_inst._listeners = {}
        dispatcher_inst.dispatch_event(StubEvent1())
        assert dispatcher_inst._waiters == {}
        assert dispatcher_inst._listeners == {}

    @pytest.mark.asyncio
    async def test_dispatch_is_awaitable_if_nothing_is_invoked(self, dispatcher_inst):
        coro_fn = mock.AsyncMock()

        dispatcher_inst.add_listener("foo", coro_fn)
        await dispatcher_inst.dispatch_event("bar")

    @pytest.mark.asyncio
    async def test_dispatch_is_awaitable_if_something_is_invoked(self, dispatcher_inst):
        coro_fn = mock.AsyncMock()

        dispatcher_inst.add_listener("foo", coro_fn)
        await dispatcher_inst.dispatch_event("foo")

    @pytest.mark.asyncio
    @_helpers.timeout_after(1)
    async def test_dispatch_invokes_future_waker_if_registered_with_futures(self, dispatcher_inst, event_loop):
        dispatcher_inst._waiters[StubEvent1] = {event_loop.create_future(): lambda _: False}

    @pytest.mark.asyncio
    @_helpers.timeout_after(1)
    async def test_dispatch_returns_exception_to_caller(self, dispatcher_inst, event_loop):
        predicate1 = mock.MagicMock(side_effect=RuntimeError())
        predicate2 = mock.MagicMock(return_value=False)

        future1 = event_loop.create_future()
        future2 = event_loop.create_future()

        ctx = StubEvent3()

        dispatcher_inst._waiters[StubEvent3] = {}
        dispatcher_inst._waiters[StubEvent3][future1] = predicate1
        dispatcher_inst._waiters[StubEvent3][future2] = predicate2

        await dispatcher_inst.dispatch_event(ctx)

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
    async def test_waiter_map_deleted_if_made_empty_during_this_dispatch(self, dispatcher_inst):
        dispatcher_inst._waiters[StubEvent1] = {mock.MagicMock(): mock.MagicMock(return_value=True)}
        dispatcher_inst.dispatch_event(StubEvent1())
        await asyncio.sleep(0.1)
        assert StubEvent1 not in dispatcher_inst._waiters

    @pytest.mark.asyncio
    @_helpers.timeout_after(1)
    async def test_waiter_map_not_deleted_if_not_empty(self, dispatcher_inst):
        dispatcher_inst._waiters[StubEvent1] = {mock.MagicMock(): mock.MagicMock(return_value=False)}
        dispatcher_inst.dispatch_event(StubEvent1())
        await asyncio.sleep(0.1)
        assert StubEvent1 in dispatcher_inst._waiters

    @pytest.mark.asyncio
    @_helpers.timeout_after(2)
    async def test_wait_for_returns_event(self, dispatcher_inst):
        predicate = mock.MagicMock(return_value=True)
        future = dispatcher_inst.wait_for(StubEvent1, timeout=5, predicate=predicate)

        ctx = StubEvent1()
        await dispatcher_inst.dispatch_event(ctx)

        await asyncio.sleep(0.1)

        assert future.done()
        actual_result = await future
        assert actual_result == ctx
        predicate.assert_called_once_with(ctx)

    @pytest.mark.asyncio
    @_helpers.timeout_after(2)
    async def test_wait_for_returns_matching_event_args_when_invoked_but_no_predicate_match(self, dispatcher_inst):
        predicate = mock.MagicMock(return_value=False)
        ctx = StubEvent3()
        future = dispatcher_inst.wait_for(StubEvent3, timeout=5, predicate=predicate)
        await dispatcher_inst.dispatch_event(ctx)

        await asyncio.sleep(0.1)

        assert not future.done()
        predicate.assert_called_once_with(ctx)

    @pytest.mark.asyncio
    @_helpers.assert_raises(type_=asyncio.TimeoutError)
    async def test_wait_for_hits_timeout_and_raises(self, dispatcher_inst):
        predicate = mock.MagicMock(return_value=False)
        await dispatcher_inst.wait_for("foobar", timeout=1, predicate=predicate)
        assert False, "event was marked as succeeded when it shouldn't have been"

    @pytest.mark.asyncio
    @_helpers.timeout_after(2)
    @_helpers.assert_raises(type_=RuntimeError)
    async def test_wait_for_raises_predicate_errors(self, dispatcher_inst):
        predicate = mock.MagicMock(side_effect=RuntimeError)
        ctx = StubEvent1()
        future = dispatcher_inst.wait_for(StubEvent1, timeout=1, predicate=predicate)
        await dispatcher_inst.dispatch_event(ctx)
        await future

    @pytest.mark.asyncio
    @pytest.mark.parametrize("predicate_side_effect", (True, False, RuntimeError()))
    @_helpers.timeout_after(5)
    @_helpers.assert_raises(type_=asyncio.TimeoutError)
    async def test_other_events_in_same_waiter_event_name_do_not_awaken_us(
        self, dispatcher_inst, predicate_side_effect, event_loop
    ):
        dispatcher_inst._waiters["foobar"] = {
            event_loop.create_future(): mock.MagicMock(side_effect=predicate_side_effect)
        }

        future = dispatcher_inst.wait_for("foobar", timeout=1, predicate=mock.MagicMock(return_value=False))

        await asyncio.gather(future, *(dispatcher_inst.dispatch_event("foobar") for _ in range(5)))

    @pytest.mark.asyncio
    async def test_catch_happy_path(self, dispatcher_inst):
        callback = mock.AsyncMock()
        event = StubEvent1()
        dispatcher_inst.handle_exception = mock.MagicMock()
        await dispatcher_inst._catch(callback, event)
        callback.assert_awaited_once_with(event)
        dispatcher_inst.handle_exception.assert_not_called()

    @pytest.mark.asyncio
    async def test_catch_sad_path(self, dispatcher_inst):
        ex = RuntimeError()
        callback = mock.AsyncMock(side_effect=ex)
        dispatcher_inst.handle_exception = mock.MagicMock()
        ctx = StubEvent3()
        await dispatcher_inst._catch(callback, ctx)
        dispatcher_inst.handle_exception.assert_called_once_with(ex, ctx, callback)

    def test_handle_exception_dispatches_exception_event_with_context(self, dispatcher_inst):
        dispatcher_inst.dispatch_event = mock.MagicMock()

        ex = RuntimeError()
        event = StubEvent1()
        callback = mock.AsyncMock()

        dispatcher_inst.handle_exception(ex, event, callback)

        expected_ctx = events.ExceptionEvent(ex, event, callback)
        dispatcher_inst.dispatch_event.assert_called_once_with(expected_ctx)

    def test_handle_exception_will_not_recursively_invoke_exception_handler_event(self, dispatcher_inst):
        dispatcher_inst.dispatch_event = mock.MagicMock()
        dispatcher_inst.handle_exception(RuntimeError(), events.ExceptionEvent(..., ..., ...), mock.AsyncMock())
        dispatcher_inst.dispatch_event.assert_not_called()

    # TODO: test add, on, remove, etc
