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
import functools

import async_timeout
import mock
import pytest

from hikari import events
from hikari.events import intent_aware_dispatchers
from tests.hikari import _helpers


def coro(func):
    @functools.wraps(func)
    async def coro_fn(*args, **kwargs):
        return func(*args, **kwargs)

    return coro_fn


class DummyEventType(events.HikariEvent):
    ...


@pytest.fixture()
def intent_aware_dispatcher():
    return intent_aware_dispatchers.IntentAwareEventDispatcherImpl(None)


class TestClose:
    def test_listeners_are_cleared(self, intent_aware_dispatcher):
        intent_aware_dispatcher._listeners = mock.MagicMock()

        intent_aware_dispatcher.close()

        intent_aware_dispatcher._listeners.clear.assert_called_once_with()

    def test_pending_waiters_are_cancelled_and_cleared(self, intent_aware_dispatcher):
        event1_mock_futures = [mock.MagicMock(cancel=mock.MagicMock()) for _ in range(30)]
        event2_mock_futures = [mock.MagicMock(cancel=mock.MagicMock()) for _ in range(30)]
        intent_aware_dispatcher._waiters = {
            "event1": {f: lambda _: False for f in event1_mock_futures},
            "event2": {f: lambda _: False for f in event2_mock_futures},
        }

        intent_aware_dispatcher.close()

        for f in event1_mock_futures + event2_mock_futures:
            f.cancel.assert_called_once_with()
            assert all(f not in fs for fs in intent_aware_dispatcher._waiters.values())

        assert intent_aware_dispatcher._waiters == {}


class TestAddListener:
    @_helpers.assert_raises(type_=TypeError)
    def test_non_HikariEvent_base_raises_TypeError(self, intent_aware_dispatcher):
        async def callback(event):
            pass

        intent_aware_dispatcher.add_listener(object, callback)

    def test_disabled_intents_never_raises_warning(self, intent_aware_dispatcher):
        async def callback(event):
            pass

        intent_aware_dispatcher._enabled_intents = None

        with mock.patch("warnings.warn") as warn:
            intent_aware_dispatcher.add_listener(DummyEventType, callback)

        warn.assert_not_called()

    def test_add_when_no_existing_listeners_exist_for_event_adds_new_list_first(self, intent_aware_dispatcher):
        class NewEventType(events.HikariEvent):
            pass

        dummy_listeners = [...]

        intent_aware_dispatcher._listeners = {DummyEventType: [*dummy_listeners]}

        async def callback(event):
            pass

        intent_aware_dispatcher.add_listener(NewEventType, callback)

        assert DummyEventType in intent_aware_dispatcher._listeners, "wrong event was removed somehow?"
        assert dummy_listeners == intent_aware_dispatcher._listeners[DummyEventType], "wrong event was subscribed to!"

        assert NewEventType in intent_aware_dispatcher._listeners, "event was not subscribed to"
        assert callback in intent_aware_dispatcher._listeners[NewEventType], "callback was not added as a subscriber"
        assert len(intent_aware_dispatcher._listeners[NewEventType]) == 1, "event was not subscribed once"

    def test_add_when_other_listeners_exist_for_event_appends_callback(self, intent_aware_dispatcher):
        class NewEventType(events.HikariEvent):
            pass

        dummy_listeners = [...]
        new_event_listeners = [mock.AsyncMock(), mock.AsyncMock()]

        intent_aware_dispatcher._listeners = {DummyEventType: [*dummy_listeners], NewEventType: [*new_event_listeners]}

        async def callback(event):
            pass

        intent_aware_dispatcher.add_listener(NewEventType, callback)

        assert DummyEventType in intent_aware_dispatcher._listeners, "wrong event was removed somehow?"
        assert dummy_listeners == intent_aware_dispatcher._listeners[DummyEventType], "wrong event was subscribed to!"

        assert NewEventType in intent_aware_dispatcher._listeners, "event was not subscribed to"
        assert callback in intent_aware_dispatcher._listeners[NewEventType], "callback was not added as a subscriber"
        assert intent_aware_dispatcher._listeners[NewEventType] == [
            *new_event_listeners,
            callback,
        ], "callbacks were mangled"


class TestRemoveListener:
    def test_remove_listener_when_present(self, intent_aware_dispatcher):
        async def callback(event):
            pass

        a, b = mock.AsyncMock(), mock.AsyncMock()
        intent_aware_dispatcher._listeners = {DummyEventType: [a, callback, b]}

        intent_aware_dispatcher.remove_listener(DummyEventType, callback)

        assert callback not in intent_aware_dispatcher._listeners[DummyEventType]
        assert intent_aware_dispatcher._listeners[DummyEventType] == [a, b]

    def test_remove_listener_when_present_and_last_listener_of_that_type(self, intent_aware_dispatcher):
        async def callback(event):
            pass

        a, b = mock.AsyncMock(), mock.AsyncMock()
        intent_aware_dispatcher._listeners = {DummyEventType: [callback]}

        intent_aware_dispatcher.remove_listener(DummyEventType, callback)

        assert DummyEventType not in intent_aware_dispatcher._listeners

    def test_remove_listener_when_callback_not_present(self, intent_aware_dispatcher):
        async def callback(event):
            pass

        a, b = mock.AsyncMock(), mock.AsyncMock()
        intent_aware_dispatcher._listeners = {DummyEventType: [a, b]}

        intent_aware_dispatcher.remove_listener(DummyEventType, callback)

    def test_remove_listener_when_event_not_present(self, intent_aware_dispatcher):
        async def callback(event):
            pass

        class DummyEventType2(events.HikariEvent):
            pass

        a, b = mock.AsyncMock(), mock.AsyncMock()
        intent_aware_dispatcher._listeners = {DummyEventType2: [a, b]}

        intent_aware_dispatcher.remove_listener(DummyEventType, callback)


@pytest.mark.asyncio
class TestDispatchEvent:
    async def test_listeners_invoked(self, intent_aware_dispatcher):
        class Event1(events.HikariEvent):
            pass

        class Event2(events.HikariEvent):
            pass

        class Event3(events.HikariEvent):
            pass

        e1_1, e1_2, e1_3 = mock.AsyncMock(), mock.AsyncMock(), mock.AsyncMock()
        e2_1, e2_2, e2_3 = mock.AsyncMock(), mock.AsyncMock(), mock.AsyncMock()
        e3_1, e3_2, e3_3 = mock.AsyncMock(), mock.AsyncMock(), mock.AsyncMock()

        intent_aware_dispatcher._listeners = {
            Event1: [e1_1, e1_2, e1_3],
            Event2: [e2_1, e2_2, e2_3],
            Event3: [e3_1, e3_2, e3_3],
        }

        await intent_aware_dispatcher.dispatch_event(Event2())

        e1_1.assert_not_called()
        e1_2.assert_not_called()
        e1_3.assert_not_called()

        e2_1.assert_awaited_once()
        e2_2.assert_awaited_once()
        e2_3.assert_awaited_once()

        e3_1.assert_not_called()
        e3_2.assert_not_called()
        e3_3.assert_not_called()

    async def test_supertype_events_invoked(self, intent_aware_dispatcher):
        class A(events.HikariEvent):
            pass

        class B(A):
            pass

        class C(B):
            pass

        class D(C):
            pass

        a_callback = mock.AsyncMock()
        b_callback = mock.AsyncMock()
        c_callback = mock.AsyncMock()
        d_callback = mock.AsyncMock()

        intent_aware_dispatcher._listeners = {A: [a_callback], B: [b_callback], C: [c_callback], D: [d_callback]}
        inst = C()

        await intent_aware_dispatcher.dispatch_event(inst)

        a_callback.assert_awaited_once_with(inst)
        b_callback.assert_awaited_once_with(inst)
        c_callback.assert_awaited_once_with(inst)
        d_callback.assert_not_called()

    async def test_waiters_completed(self, intent_aware_dispatcher, event_loop):
        class Event1(events.HikariEvent):
            pass

        class Event2(events.HikariEvent):
            pass

        class Event3(events.HikariEvent):
            pass

        f1_1, f1_2, f1_3 = event_loop.create_future(), event_loop.create_future(), event_loop.create_future()
        f2_1, f2_2, f2_3 = event_loop.create_future(), event_loop.create_future(), event_loop.create_future()
        f3_1, f3_2, f3_3 = event_loop.create_future(), event_loop.create_future(), event_loop.create_future()

        def truthy(event):
            return True

        intent_aware_dispatcher._waiters = {
            Event1: {f1_1: truthy, f1_2: truthy, f1_3: truthy},
            Event2: {f2_1: truthy, f2_2: truthy, f2_3: truthy},
            Event3: {f3_1: truthy, f3_2: truthy, f3_3: truthy},
        }

        inst = Event2()

        await intent_aware_dispatcher.dispatch_event(inst)

        assert not f1_1.done()
        assert not f1_2.done()
        assert not f1_3.done()

        assert f2_1.result() is inst
        assert f2_2.result() is inst
        assert f2_3.result() is inst

        assert not f3_1.done()
        assert not f3_2.done()
        assert not f3_3.done()

    async def test_waiters_subtypes_completed(self, intent_aware_dispatcher, event_loop):
        class A(events.HikariEvent):
            pass

        class B(A):
            pass

        class C(B):
            pass

        class D(C):
            pass

        inst = C()

        a_future = event_loop.create_future()
        b_future = event_loop.create_future()
        c_future = event_loop.create_future()
        d_future = event_loop.create_future()

        def truthy(event):
            return True

        intent_aware_dispatcher._waiters = {
            A: {a_future: truthy},
            B: {b_future: truthy},
            C: {c_future: truthy},
            D: {d_future: truthy},
        }

        await intent_aware_dispatcher.dispatch_event(inst)

        assert a_future.result() is inst
        assert b_future.result() is inst
        assert c_future.result() is inst
        assert not d_future.done()

    @pytest.mark.parametrize(["predicate", "expected_to_awaken"], [(lambda _: True, True), (lambda _: False, False),])
    async def test_waiters_adhere_to_sync_predicate(
        self, intent_aware_dispatcher, predicate, expected_to_awaken, event_loop
    ):
        future = event_loop.create_future()
        intent_aware_dispatcher._waiters = {
            DummyEventType: {future: predicate},
        }

        inst = DummyEventType()

        await intent_aware_dispatcher.dispatch_event(inst)

        assert future.result() is inst if expected_to_awaken else not future.done()

    @pytest.mark.parametrize(
        ["predicate", "expected_to_awaken"], [(coro(lambda _: True), True), (coro(lambda _: False), False),]
    )
    async def test_waiters_adhere_to_async_predicate(
        self, intent_aware_dispatcher, predicate, expected_to_awaken, event_loop
    ):
        future = event_loop.create_future()
        intent_aware_dispatcher._waiters = {
            DummyEventType: {future: predicate},
        }

        inst = DummyEventType()

        await intent_aware_dispatcher.dispatch_event(inst)

        # These get evaluated in the background...
        await asyncio.sleep(0.25)

        assert future.result() is inst if expected_to_awaken else not future.done()

    @_helpers.timeout_after(5)
    @_helpers.assert_raises(type_=LookupError)
    async def test_waiter_sync_exception_is_propagated(self, intent_aware_dispatcher, event_loop):
        def predicate(event):
            raise LookupError("boom")

        future = event_loop.create_future()
        intent_aware_dispatcher._waiters = {
            DummyEventType: {future: predicate},
        }

        inst = DummyEventType()

        await intent_aware_dispatcher.dispatch_event(inst)

        await future

    @_helpers.timeout_after(5)
    @_helpers.assert_raises(type_=LookupError)
    async def test_waiter_async_exception_is_propagated(self, intent_aware_dispatcher, event_loop):
        async def predicate(event):
            raise LookupError("boom")

        future = event_loop.create_future()
        intent_aware_dispatcher._waiters = {
            DummyEventType: {future: predicate},
        }

        inst = DummyEventType()

        await intent_aware_dispatcher.dispatch_event(inst)

        await future

    async def test_no_dispatch_events_is_still_awaitable(self, intent_aware_dispatcher):
        await intent_aware_dispatcher.dispatch_event(DummyEventType())

    async def test_dispatch_event_awaits_async_function(self, intent_aware_dispatcher):
        mock_async_listener = mock.AsyncMock()
        dummy_event = DummyEventType()
        intent_aware_dispatcher._listeners = {DummyEventType: [mock_async_listener]}
        await intent_aware_dispatcher.dispatch_event(dummy_event)
        mock_async_listener.assert_called_once_with(dummy_event)

    async def test_dispatch_event_calls_non_async_function(self, intent_aware_dispatcher):
        mock_listener = mock.MagicMock()
        dummy_event = DummyEventType()
        intent_aware_dispatcher._listeners = {DummyEventType: [mock_listener]}
        await intent_aware_dispatcher.dispatch_event(dummy_event)
        mock_listener.assert_called_once_with(dummy_event)

    async def test_dispatch_event_returns_awaitable_future_if_noop(self, intent_aware_dispatcher):
        try:
            result = intent_aware_dispatcher.dispatch_event(DummyEventType())
            assert isinstance(result, asyncio.Future)
        finally:
            await result

    async def test_dispatch_event_returns_awaitable_future_if_futures_awakened(self, intent_aware_dispatcher):
        try:
            intent_aware_dispatcher._listeners = {DummyEventType: [mock.AsyncMock()]}
            result = intent_aware_dispatcher.dispatch_event(DummyEventType())
            assert isinstance(result, asyncio.Future)
        finally:
            await result

    async def test_dispatch_event_handles_event_exception(self, intent_aware_dispatcher):
        ex = LookupError("boom")
        inst = DummyEventType()

        async def callback(event):
            raise ex

        intent_aware_dispatcher.handle_exception = mock.MagicMock()

        intent_aware_dispatcher._listeners = {DummyEventType: [callback]}
        await intent_aware_dispatcher.dispatch_event(inst)

        intent_aware_dispatcher.handle_exception.assert_called_once_with(ex, inst, callback)

    async def test_dispatch_event_does_not_redispatch_ExceptionEvent_recursively(self, intent_aware_dispatcher):
        ex = LookupError("boom")
        inst = DummyEventType()

        async def callback(event):
            raise ex

        intent_aware_dispatcher.handle_exception = mock.MagicMock(wraps=intent_aware_dispatcher.handle_exception)
        intent_aware_dispatcher._listeners = {DummyEventType: [callback], events.ExceptionEvent: [callback]}
        await intent_aware_dispatcher.dispatch_event(inst)

        await asyncio.sleep(1)

        calls = intent_aware_dispatcher.handle_exception.call_args_list

        assert calls == [mock.call(ex, inst, callback), mock.call(ex, mock.ANY, callback)]


@pytest.mark.asyncio
class TestIntentAwareDispatcherImplIT:
    async def test_dispatch_event_when_invoked_event_integration_test(self, intent_aware_dispatcher):
        dummy_event_invoked = 0
        event_obj = DummyEventType()

        @intent_aware_dispatcher.event(DummyEventType)
        async def on_dummy_event(actual_event_obj):
            nonlocal dummy_event_invoked
            dummy_event_invoked += 1
            assert actual_event_obj is event_obj

        await intent_aware_dispatcher.dispatch_event(event_obj)

        assert dummy_event_invoked == 1

    async def test_dispatch_event_when_not_invoked_event_integration_test(self, intent_aware_dispatcher):
        dummy_event_invoked = 0

        @intent_aware_dispatcher.event(DummyEventType)
        async def on_dummy_event(actual_event_obj):
            nonlocal dummy_event_invoked
            dummy_event_invoked += 1

        await intent_aware_dispatcher.dispatch_event(mock.MagicMock())

        assert dummy_event_invoked == 0

    async def test_dispatch_event_when_event_invoked_errors_integration_test(self, intent_aware_dispatcher):
        dummy_event_invoked = 0
        exception_event_invoked = 0
        event_obj = DummyEventType()

        @intent_aware_dispatcher.event(DummyEventType)
        async def on_dummy_event(actual_event_obj):
            nonlocal dummy_event_invoked
            dummy_event_invoked += 1
            assert actual_event_obj is event_obj
            raise RuntimeError("BANG")

        @intent_aware_dispatcher.event()
        async def on_exception(actual_exception_event: events.ExceptionEvent):
            nonlocal exception_event_invoked
            assert isinstance(actual_exception_event, events.ExceptionEvent)
            exception_event_invoked += 1

        await intent_aware_dispatcher.dispatch_event(event_obj)

        # Just in case it isn't immediately scheduled to handle the exception.
        await asyncio.sleep(0.25)

        assert dummy_event_invoked == 1
        assert exception_event_invoked == 1


@pytest.mark.asyncio
class TestWaitForIntegrationTest:
    @_helpers.timeout_after(5)
    async def test_truthy_sync_predicate(self, intent_aware_dispatcher):
        event = DummyEventType()

        def predicate(actual_event):
            assert actual_event is event
            return True

        task = intent_aware_dispatcher.wait_for(DummyEventType, predicate=predicate, timeout=None)
        await intent_aware_dispatcher.dispatch_event(event)

        await task

    @_helpers.timeout_after(5)
    async def test_truthy_async_predicate(self, intent_aware_dispatcher):
        event = DummyEventType()

        async def predicate(actual_event):
            assert actual_event is event
            return True

        task = intent_aware_dispatcher.wait_for(DummyEventType, predicate=predicate, timeout=None)
        await intent_aware_dispatcher.dispatch_event(event)

        await task

    @_helpers.timeout_after(5)
    async def test_second_truthy_sync_predicate(self, intent_aware_dispatcher):
        event = DummyEventType()

        def predicate(actual_event):
            assert actual_event is event
            return True

        dead_task = intent_aware_dispatcher.wait_for(DummyEventType, predicate=lambda _: False, timeout=None)
        task = intent_aware_dispatcher.wait_for(DummyEventType, predicate=predicate, timeout=None)
        await intent_aware_dispatcher.dispatch_event(event)

        await task
        dead_task.cancel()

    @_helpers.timeout_after(5)
    async def test_second_truthy_async_predicate(self, intent_aware_dispatcher):
        event = DummyEventType()

        async def predicate(actual_event):
            assert actual_event is event
            return True

        dead_task = intent_aware_dispatcher.wait_for(DummyEventType, predicate=lambda _: False, timeout=None)
        task = intent_aware_dispatcher.wait_for(DummyEventType, predicate=predicate, timeout=None)
        await intent_aware_dispatcher.dispatch_event(event)

        await task
        dead_task.cancel()

    async def test_falsy_sync_predicate(self, intent_aware_dispatcher):
        event = DummyEventType()

        def predicate(actual_event):
            assert actual_event is event
            return False

        task = intent_aware_dispatcher.wait_for(DummyEventType, predicate=predicate, timeout=100)
        await intent_aware_dispatcher.dispatch_event(event)

        try:
            with async_timeout.timeout(1):
                await task
            assert False
        except asyncio.TimeoutError:
            pass

    async def test_falsy_async_predicate(self, intent_aware_dispatcher):
        event = DummyEventType()

        async def predicate(actual_event):
            assert actual_event is event
            return False

        task = intent_aware_dispatcher.wait_for(DummyEventType, predicate=predicate, timeout=100)
        await intent_aware_dispatcher.dispatch_event(event)

        try:
            with async_timeout.timeout(1):
                await task
            assert False
        except asyncio.TimeoutError:
            pass

    @pytest.mark.parametrize("failed_attempts", [0, 1, 2])
    @_helpers.timeout_after(5)
    async def test_wait_for_timeout(self, intent_aware_dispatcher, failed_attempts):
        event = DummyEventType()

        async def predicate(actual_event):
            assert actual_event is event
            return False

        task = intent_aware_dispatcher.wait_for(DummyEventType, predicate=predicate, timeout=0.1)

        for i in range(failed_attempts):
            await intent_aware_dispatcher.dispatch_event(event)

        try:
            await task
            assert False
        except asyncio.TimeoutError:
            pass
