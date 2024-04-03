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

import asyncio
import contextlib
import gc
import sys
import typing
import warnings
import weakref

import mock
import pytest

from hikari import errors
from hikari import intents
from hikari import iterators
from hikari.api import config
from hikari.events import base_events
from hikari.events import member_events
from hikari.events import shard_events
from hikari.impl import event_manager_base
from hikari.internal import reflect
from tests.hikari import hikari_test_helpers


class TestGenerateWeakListener:
    @pytest.mark.asyncio
    async def test__generate_weak_listener_when_method_is_None(self):
        def test():
            return None

        call_weak_method = event_manager_base._generate_weak_listener(test)

        with pytest.raises(
            TypeError,
            match=r"dead weak referenced subscriber method cannot be executed, try actually closing your event streamers",
        ):
            await call_weak_method(None)

    @pytest.mark.asyncio
    async def test__generate_weak_listener(self):
        mock_listener = mock.AsyncMock()
        mock_event = object()

        def test():
            return mock_listener

        call_weak_method = event_manager_base._generate_weak_listener(test)

        await call_weak_method(mock_event)

        mock_listener.assert_awaited_once_with(mock_event)


@pytest.fixture
def mock_app():
    return mock.Mock()


class TestEventStream:
    def test___enter___and___exit__(self):
        stub_stream = hikari_test_helpers.mock_class_namespace(
            event_manager_base.EventStream, open=mock.Mock(), close=mock.Mock()
        )(mock_app, base_events.Event, timeout=None)

        with stub_stream:
            stub_stream.open.assert_called_once_with()
            stub_stream.close.assert_not_called()

        stub_stream.open.assert_called_once_with()
        stub_stream.close.assert_called_once_with()

    @pytest.mark.asyncio
    async def test__listener_when_filter_returns_false(self, mock_app):
        stream = event_manager_base.EventStream(mock_app, base_events.Event, timeout=None)
        stream.filter(lambda _: False)
        mock_event = object()

        assert await stream._listener(mock_event) is None
        assert not stream._queue

    @hikari_test_helpers.timeout()
    @pytest.mark.asyncio
    async def test__listener_when_filter_passes_and_queue_full(self, mock_app):
        stream = event_manager_base.EventStream(mock_app, base_events.Event, timeout=None, limit=2)
        stream._queue.append(object())
        stream._queue.append(object())
        stream.filter(lambda _: True)
        mock_event = object()

        with stream:
            assert await stream._listener(mock_event) is None
            assert await stream.next() is not mock_event
            assert await stream.next() is not mock_event
            assert not stream._queue

    @hikari_test_helpers.timeout()
    @pytest.mark.asyncio
    async def test__listener_when_filter_passes_and_queue_not_full(self, mock_app):
        stream = event_manager_base.EventStream(mock_app, base_events.Event, timeout=None, limit=None)
        stream._queue.append(object())
        stream._queue.append(object())
        stream.filter(lambda _: True)
        mock_event = object()

        with stream:
            assert await stream._listener(mock_event) is None
            assert await stream.next() is not mock_event
            assert await stream.next() is not mock_event
            assert await stream.next() is mock_event

    @pytest.mark.asyncio
    @hikari_test_helpers.timeout()
    async def test___anext___when_stream_closed(self):
        streamer = event_manager_base.EventStream(mock.Mock(), event_type=base_events.Event, timeout=float("inf"))

        # flake8 gets annoyed if we use "with" here so here's a hacky alternative
        with pytest.raises(TypeError):
            await streamer.__anext__()

    @pytest.mark.asyncio
    @hikari_test_helpers.timeout()
    async def test___anext___times_out(self):
        streamer = event_manager_base.EventStream(mock.Mock(), event_type=base_events.Event, timeout=0.001)

        with streamer:
            with pytest.raises(LookupError):
                await streamer.next()

    @pytest.mark.asyncio
    @hikari_test_helpers.timeout()
    async def test___anext___waits_for_next_event(self):
        mock_event = object()
        streamer = event_manager_base.EventStream(mock.Mock(), event_type=base_events.Event, timeout=None)

        async def quickly_run_task(task):
            try:
                await asyncio.wait_for(asyncio.shield(task), timeout=0.01)
            except asyncio.TimeoutError:
                pass

        with streamer:
            next_task = asyncio.create_task(streamer.next())
            await quickly_run_task(next_task)
            assert not next_task.done()
            await streamer._listener(mock_event)
            await quickly_run_task(next_task)
            assert next_task.done()
            assert next_task.result() is mock_event

    @pytest.mark.asyncio
    @hikari_test_helpers.timeout()
    async def test___anext__(self):
        mock_event = object()
        streamer = event_manager_base.EventStream(
            event_manager=mock.Mock(),
            event_type=base_events.Event,
            timeout=hikari_test_helpers.REASONABLE_QUICK_RESPONSE_TIME,
        )
        streamer._queue.append(mock_event)

        with streamer:
            assert await streamer.next() is mock_event

    @pytest.mark.asyncio
    async def test___await__(self):
        mock_event_0 = object()
        mock_event_1 = object()
        mock_event_2 = object()
        streamer = hikari_test_helpers.mock_class_namespace(
            event_manager_base.EventStream,
            close=mock.Mock(),
            open=mock.Mock(),
            init_=False,
            _active=False,
            __anext__=mock.AsyncMock(side_effect=[mock_event_0, mock_event_1, mock_event_2]),
        )()

        assert await streamer == [mock_event_0, mock_event_1, mock_event_2]
        streamer.open.assert_called_once_with()
        streamer.close.assert_called_once_with()

    def test___del___for_active_stream(self):
        mock_coroutine = object()
        close_method = mock.Mock(return_value=mock_coroutine)
        streamer = hikari_test_helpers.mock_class_namespace(
            event_manager_base.EventStream, close=close_method, init_=False
        )()
        streamer._event_type = base_events.Event
        streamer._active = True

        with mock.patch.object(event_manager_base, "_LOGGER") as logger:
            del streamer
            gc.collect()  # Force a GC collection

        logger.warning.assert_called_once_with("active %r streamer fell out of scope before being closed", "Event")
        close_method.assert_called_once_with()

    def test___del___for_inactive_stream(self):
        close_method = mock.Mock()
        streamer = hikari_test_helpers.mock_class_namespace(
            event_manager_base.EventStream, close=close_method, init_=False
        )()
        streamer._event_type = base_events.Event
        streamer._active = False

        del streamer
        close_method.assert_not_called()

    def test_close_for_inactive_stream(self, mock_app):
        stream = event_manager_base.EventStream(mock_app, base_events.Event, timeout=None, limit=None)
        stream.close()
        mock_app.event_manager.unsubscribe.assert_not_called()

    def test_close_for_active_stream(self):
        mock_registered_listener = object()
        mock_manager = mock.Mock()
        stream = hikari_test_helpers.mock_class_namespace(event_manager_base.EventStream)(
            event_manager=mock_manager, event_type=base_events.Event, timeout=float("inf")
        )

        stream.open()
        stream._registered_listener = mock_registered_listener
        stream.close()
        mock_manager.unsubscribe.assert_called_once_with(base_events.Event, mock_registered_listener)
        assert stream._active is False
        assert stream._registered_listener is None

    def test_close_for_active_stream_handles_value_error(self):
        mock_registered_listener = object()
        mock_manager = mock.Mock()
        mock_manager.unsubscribe.side_effect = ValueError
        stream = hikari_test_helpers.mock_class_namespace(event_manager_base.EventStream)(
            event_manager=mock_manager, event_type=base_events.Event, timeout=float("inf")
        )

        stream.open()
        stream._registered_listener = mock_registered_listener
        stream.close()
        mock_manager.unsubscribe.assert_called_once_with(base_events.Event, mock_registered_listener)
        assert stream._active is False
        assert stream._registered_listener is None

    @pytest.mark.asyncio
    async def test_filter(self):
        stream = hikari_test_helpers.mock_class_namespace(event_manager_base.EventStream)(
            event_manager=mock.Mock(), event_type=base_events.Event, timeout=0.001
        )
        stream._filters = iterators.All(())
        first_pass = mock.Mock(attr=True)
        second_pass = mock.Mock(attr=True)
        first_fails = mock.Mock(attr=True)
        second_fail = mock.Mock(attr=False)

        def predicate(obj):
            return obj in (first_pass, second_pass)

        stream.filter(predicate, attr=True)

        await stream._listener(first_pass)
        await stream._listener(first_fails)
        await stream._listener(second_pass)
        await stream._listener(second_fail)

        assert await stream == [first_pass, second_pass]

    @pytest.mark.asyncio
    async def test_filter_handles_calls_while_active(self):
        stream = hikari_test_helpers.mock_class_namespace(event_manager_base.EventStream)(
            event_manager=mock.Mock(), event_type=base_events.Event, timeout=0.001
        )
        stream._filters = iterators.All(())
        first_pass = mock.Mock(attr=True)
        second_pass = mock.Mock(attr=True)
        first_fails = mock.Mock(attr=True)
        second_fail = mock.Mock(attr=False)
        await stream._listener(first_pass)
        await stream._listener(first_fails)
        await stream._listener(second_pass)
        await stream._listener(second_fail)

        def predicate(obj):
            return obj in (first_pass, second_pass)

        with stream:
            stream.filter(predicate, attr=True)

            assert await stream == [first_pass, second_pass]

    def test_open_for_inactive_stream(self):
        mock_listener = object()
        mock_manager = mock.Mock()
        stream = hikari_test_helpers.mock_class_namespace(event_manager_base.EventStream)(
            event_manager=mock_manager, event_type=base_events.Event, timeout=float("inf")
        )

        stream._active = True
        stream._registered_listener = mock_listener

        with mock.patch.object(event_manager_base, "_generate_weak_listener"):
            with mock.patch.object(weakref, "WeakMethod"):
                stream.open()

                weakref.WeakMethod.assert_not_called()
            event_manager_base._generate_weak_listener.assert_not_called()

        mock_manager.subscribe.assert_not_called()
        assert stream._active is True
        assert stream._registered_listener is mock_listener

        # Ensure we don't get a warning or error on del
        stream._active = False

    def test_open_for_active_stream(self):
        mock_manager = mock.Mock()
        stream = hikari_test_helpers.mock_class_namespace(event_manager_base.EventStream)(
            event_manager=mock_manager, event_type=base_events.Event, timeout=float("inf")
        )
        stream._active = False
        mock_listener = object()
        mock_listener_ref = object()

        with mock.patch.object(event_manager_base, "_generate_weak_listener", return_value=mock_listener):
            with mock.patch.object(weakref, "WeakMethod", return_value=mock_listener_ref):
                stream.open()

                weakref.WeakMethod.assert_called_once_with(stream._listener)
            event_manager_base._generate_weak_listener.assert_called_once_with(mock_listener_ref)

        mock_manager.subscribe.assert_called_once_with(base_events.Event, mock_listener)
        assert stream._active is True
        assert stream._registered_listener is mock_listener

        # Ensure we don't get a warning or error on del
        stream._active = False


class TestConsumer:
    @pytest.mark.parametrize(
        ("is_caching", "listener_group_count", "waiter_group_count", "expected_result"),
        [(True, -10000, -10000, True), (False, 0, 1, True), (False, 1, 0, True), (False, 0, 0, False)],
    )
    def test_is_enabled(self, is_caching, listener_group_count, waiter_group_count, expected_result):
        consumer = event_manager_base._Consumer(object(), 123, is_caching)
        consumer.listener_group_count = listener_group_count
        consumer.waiter_group_count = waiter_group_count

        assert consumer.is_enabled is expected_result


class TestEventManagerBase:
    @pytest.fixture
    def event_manager(self):
        class EventManagerBaseImpl(event_manager_base.EventManagerBase):
            on_existing_event = None

        return EventManagerBaseImpl(mock.Mock(), mock.Mock())

    def test___init___loads_consumers(self):
        class StubManager(event_manager_base.EventManagerBase):
            @event_manager_base.filtered(shard_events.ShardEvent, config.CacheComponents.MEMBERS)
            async def on_foo(self, event):
                raise NotImplementedError

            @event_manager_base.filtered((shard_events.ShardStateEvent, shard_events.ShardPayloadEvent))
            async def on_bar(self, event):
                raise NotImplementedError

            @event_manager_base.filtered(shard_events.MemberChunkEvent, config.CacheComponents.MESSAGES)
            async def on_bat(self, event):
                raise NotImplementedError

            async def on_not_decorated(self, event):
                raise NotImplementedError

            async def not_a_listener(self):
                raise NotImplementedError

        manager = StubManager(
            mock.Mock(), 0, cache_components=config.CacheComponents.MEMBERS | config.CacheComponents.GUILD_CHANNELS
        )
        assert manager._consumers == {
            "foo": event_manager_base._Consumer(manager.on_foo, 9, True),
            "bar": event_manager_base._Consumer(manager.on_bar, 105, False),
            "bat": event_manager_base._Consumer(manager.on_bat, 65545, False),
            "not_decorated": event_manager_base._Consumer(manager.on_not_decorated, -1, True),
        }

    def test___init___loads_consumers_when_cacheless(self):
        class StubManager(event_manager_base.EventManagerBase):
            @event_manager_base.filtered(shard_events.ShardEvent, config.CacheComponents.MEMBERS)
            async def on_foo(self, event):
                raise NotImplementedError

            @event_manager_base.filtered((shard_events.ShardStateEvent, shard_events.ShardPayloadEvent))
            async def on_bar(self, event):
                raise NotImplementedError

            @event_manager_base.filtered(shard_events.MemberChunkEvent, config.CacheComponents.MESSAGES)
            async def on_bat(self, event):
                raise NotImplementedError

            async def on_not_decorated(self, event):
                raise NotImplementedError

            async def not_a_listener(self):
                raise NotImplementedError

        manager = StubManager(mock.Mock(), 0, cache_components=config.CacheComponents.NONE)
        assert manager._consumers == {
            "foo": event_manager_base._Consumer(manager.on_foo, 9, False),
            "bar": event_manager_base._Consumer(manager.on_bar, 105, False),
            "bat": event_manager_base._Consumer(manager.on_bat, 65545, False),
            "not_decorated": event_manager_base._Consumer(manager.on_not_decorated, -1, False),
        }

    def test__increment_listener_group_count(self, event_manager):
        on_foo_consumer = event_manager_base._Consumer(None, 9, False)
        on_bar_consumer = event_manager_base._Consumer(None, 105, False)
        on_bat_consumer = event_manager_base._Consumer(None, 1, False)
        event_manager._consumers = {"foo": on_foo_consumer, "bar": on_bar_consumer, "bat": on_bat_consumer}

        event_manager._increment_listener_group_count(shard_events.ShardEvent, 1)

        assert on_foo_consumer.listener_group_count == 1
        assert on_bar_consumer.listener_group_count == 1
        assert on_bat_consumer.listener_group_count == 0

    def test__increment_waiter_group_count(self, event_manager):
        on_foo_consumer = event_manager_base._Consumer(None, 9, False)
        on_bar_consumer = event_manager_base._Consumer(None, 105, False)
        on_bat_consumer = event_manager_base._Consumer(None, 1, False)
        event_manager._consumers = {"foo": on_foo_consumer, "bar": on_bar_consumer, "bat": on_bat_consumer}

        event_manager._increment_waiter_group_count(shard_events.ShardEvent, 1)

        assert on_foo_consumer.waiter_group_count == 1
        assert on_bar_consumer.waiter_group_count == 1
        assert on_bat_consumer.waiter_group_count == 0

    def test__enabled_for_event_when_listener_registered(self, event_manager):
        event_manager._listeners = {shard_events.ShardStateEvent: [], shard_events.MemberChunkEvent: []}
        event_manager._waiters = {}

        assert event_manager._enabled_for_event(shard_events.ShardStateEvent) is True

    def test__enabled_for_event_when_waiter_registered(self, event_manager):
        event_manager._listeners = {}
        event_manager._waiters = {shard_events.ShardStateEvent: [], shard_events.MemberChunkEvent: []}

        assert event_manager._enabled_for_event(shard_events.ShardStateEvent) is True

    def test__enabled_for_event_when_not_registered(self, event_manager):
        event_manager._listeners = {shard_events.ShardPayloadEvent: [], shard_events.MemberChunkEvent: []}
        event_manager._waiters = {shard_events.ShardPayloadEvent: [], shard_events.MemberChunkEvent: []}

        assert event_manager._enabled_for_event(shard_events.ShardStateEvent) is False

    @pytest.mark.asyncio
    async def test_consume_raw_event_when_KeyError(self, event_manager):
        event_manager._enabled_for_event = mock.Mock(return_value=True)
        mock_payload = {"id": "3123123123"}
        mock_shard = mock.Mock(id=123)
        event_manager._handle_dispatch = mock.Mock()
        event_manager.dispatch = mock.Mock()

        with pytest.raises(LookupError):
            event_manager.consume_raw_event("UNEXISTING_EVENT", mock_shard, mock_payload)

        event_manager._handle_dispatch.assert_not_called()
        event_manager.dispatch.assert_called_once_with(
            event_manager._event_factory.deserialize_shard_payload_event.return_value
        )
        event_manager._event_factory.deserialize_shard_payload_event.assert_called_once_with(
            mock_shard, mock_payload, name="UNEXISTING_EVENT"
        )
        event_manager._enabled_for_event.assert_called_once_with(shard_events.ShardPayloadEvent)

    @pytest.mark.asyncio
    async def test_consume_raw_event_when_found(self, event_manager):
        event_manager._enabled_for_event = mock.Mock(return_value=True)
        event_manager._handle_dispatch = mock.Mock()
        event_manager.dispatch = mock.Mock()
        on_existing_event = object()
        event_manager._consumers = {"existing_event": on_existing_event}
        shard = object()
        payload = {"berp": "baz"}

        with mock.patch("asyncio.create_task") as create_task:
            event_manager.consume_raw_event("EXISTING_EVENT", shard, payload)

        event_manager._handle_dispatch.assert_called_once_with(on_existing_event, shard, {"berp": "baz"})
        create_task.assert_called_once_with(
            event_manager._handle_dispatch(on_existing_event, shard, {"berp": "baz"}), name="dispatch EXISTING_EVENT"
        )
        event_manager.dispatch.assert_called_once_with(
            event_manager._event_factory.deserialize_shard_payload_event.return_value
        )
        event_manager._event_factory.deserialize_shard_payload_event.assert_called_once_with(
            shard, payload, name="EXISTING_EVENT"
        )
        event_manager._enabled_for_event.assert_called_once_with(shard_events.ShardPayloadEvent)

    @pytest.mark.asyncio
    async def test_consume_raw_event_skips_raw_dispatch_when_not_enabled(self, event_manager):
        event_manager._enabled_for_event = mock.Mock(return_value=False)
        event_manager._handle_dispatch = mock.Mock()
        event_manager.dispatch = mock.Mock()
        on_existing_event = object()
        event_manager._consumers = {"existing_event": on_existing_event}
        shard = object()
        payload = {"berp": "baz"}

        with mock.patch("asyncio.create_task") as create_task:
            event_manager.consume_raw_event("EXISTING_EVENT", shard, payload)

        event_manager._handle_dispatch.assert_called_once_with(on_existing_event, shard, {"berp": "baz"})
        create_task.assert_called_once_with(
            event_manager._handle_dispatch(on_existing_event, shard, {"berp": "baz"}), name="dispatch EXISTING_EVENT"
        )
        event_manager.dispatch.assert_not_called()
        event_manager._event_factory.deserialize_shard_payload_event.vassert_not_called()
        event_manager._enabled_for_event.assert_called_once_with(shard_events.ShardPayloadEvent)

    @pytest.mark.asyncio
    async def test_handle_dispatch_invokes_callback(self, event_manager):
        event_manager._enabled_for_consumer = mock.Mock(return_value=True)
        consumer = mock.AsyncMock()
        error_handler = mock.MagicMock()
        event_loop = asyncio.get_running_loop()
        event_loop.set_exception_handler(error_handler)
        shard = object()
        pl = {"foo": "bar"}

        await event_manager._handle_dispatch(consumer, shard, pl)

        consumer.callback.assert_awaited_once_with(shard, pl)
        error_handler.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_dispatch_ignores_cancelled_errors(self, event_manager):
        event_manager._enabled_for_consumer = mock.Mock(return_value=True)
        consumer = mock.AsyncMock(side_effect=asyncio.CancelledError)
        error_handler = mock.MagicMock()
        event_loop = asyncio.get_running_loop()
        event_loop.set_exception_handler(error_handler)
        shard = object()
        pl = {"lorem": "ipsum"}

        await event_manager._handle_dispatch(consumer, shard, pl)

        error_handler.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_dispatch_handles_exceptions(self, event_manager):
        mock_task = mock.Mock()
        # On Python 3.12+ Asyncio uses this to get the task's context if set to call the
        # error handler in. We want to avoid for this test for simplicity.
        mock_task.get_context.return_value = None
        event_manager._enabled_for_consumer = mock.Mock(return_value=True)
        exc = Exception("aaaa!")
        consumer = mock.Mock(callback=mock.AsyncMock(side_effect=exc))
        error_handler = mock.MagicMock()
        event_loop = asyncio.get_running_loop()
        event_loop.set_exception_handler(error_handler)
        shard = object()
        pl = {"i like": "cats"}

        with mock.patch.object(asyncio, "current_task", return_value=mock_task):
            await event_manager._handle_dispatch(consumer, shard, pl)

        error_handler.assert_called_once_with(
            event_loop,
            {"exception": exc, "message": "Exception occurred in raw event dispatch conduit", "task": mock_task},
        )

    @pytest.mark.asyncio
    async def test_handle_dispatch_invokes_when_consumer_not_enabled(self, event_manager):
        consumer = mock.Mock(callback=mock.AsyncMock(__name__="ok"), is_enabled=False)
        error_handler = mock.MagicMock()
        event_loop = asyncio.get_running_loop()
        event_loop.set_exception_handler(error_handler)
        shard = object()
        pl = {"foo": "bar"}

        await event_manager._handle_dispatch(consumer, shard, pl)

        consumer.callback.assert_not_called()
        error_handler.assert_not_called()

    def test_subscribe_when_class_call(self, event_manager):
        class Foo:
            async def __call__(self) -> None: ...

        foo = Foo()
        event_manager._check_event = mock.Mock()

        event_manager.subscribe(member_events.MemberCreateEvent, foo)

        assert event_manager._listeners[member_events.MemberCreateEvent] == [foo]

    def test_subscribe_when_callback_is_not_coroutine(self, event_manager):
        def test(): ...

        with pytest.raises(TypeError, match=r"Cannot subscribe a non-coroutine function callback"):
            event_manager.subscribe(member_events.MemberCreateEvent, test)

    def test_subscribe_when_event_type_not_in_listeners(self, event_manager):
        async def test(): ...

        event_manager._increment_listener_group_count = mock.Mock()
        event_manager._check_event = mock.Mock()

        event_manager.subscribe(member_events.MemberCreateEvent, test, _nested=1)

        assert event_manager._listeners == {member_events.MemberCreateEvent: [test]}
        event_manager._check_event.assert_called_once_with(member_events.MemberCreateEvent, 1)
        event_manager._increment_listener_group_count.assert_called_once_with(member_events.MemberCreateEvent, 1)

    def test_subscribe_when_event_type_in_listeners(self, event_manager):
        async def test(): ...

        async def test2(): ...

        event_manager._increment_listener_group_count = mock.Mock()
        event_manager._listeners[member_events.MemberCreateEvent] = [test2]
        event_manager._check_event = mock.Mock()

        event_manager.subscribe(member_events.MemberCreateEvent, test, _nested=2)

        assert event_manager._listeners == {member_events.MemberCreateEvent: [test2, test]}
        event_manager._check_event.assert_called_once_with(member_events.MemberCreateEvent, 2)
        event_manager._increment_listener_group_count.assert_not_called()

    @pytest.mark.parametrize("obj", ["test", event_manager_base.EventManagerBase])
    def test__check_event_when_event_type_does_not_subclass_Event(self, event_manager, obj):
        with pytest.raises(TypeError, match=r"'event_type' is a non-Event type"):
            event_manager._check_event(obj, 0)

    def test__check_event_when_no_intents_required(self, event_manager):
        event_manager._intents = intents.Intents.ALL

        with mock.patch.object(base_events, "get_required_intents_for", return_value=None) as get_intents:
            with mock.patch.object(warnings, "warn") as warn:
                event_manager._check_event(member_events.MemberCreateEvent, 0)

        get_intents.assert_called_once_with(member_events.MemberCreateEvent)
        warn.assert_not_called()

    def test__check_event_when_generic_event(self, event_manager):
        T = typing.TypeVar("T")

        class GenericEvent(typing.Generic[T], base_events.Event): ...

        event_manager._intents = intents.Intents.GUILD_MEMBERS

        with mock.patch.object(
            base_events, "get_required_intents_for", return_value=intents.Intents.GUILD_MEMBERS
        ) as get_intents:
            with mock.patch.object(warnings, "warn") as warn:
                event_manager._check_event(GenericEvent[int], 0)

        get_intents.assert_called_once_with(GenericEvent)
        warn.assert_not_called()

    def test__check_event_when_intents_correct(self, event_manager):
        event_manager._intents = intents.Intents.GUILD_EMOJIS | intents.Intents.GUILD_MEMBERS

        with mock.patch.object(
            base_events, "get_required_intents_for", return_value=intents.Intents.GUILD_MEMBERS
        ) as get_intents:
            with mock.patch.object(warnings, "warn") as warn:
                event_manager._check_event(member_events.MemberCreateEvent, 0)

        get_intents.assert_called_once_with(member_events.MemberCreateEvent)
        warn.assert_not_called()

    def test__check_event_when_intents_incorrect(self, event_manager):
        event_manager._intents = intents.Intents.GUILD_EMOJIS

        with mock.patch.object(
            base_events, "get_required_intents_for", return_value=intents.Intents.GUILD_MEMBERS
        ) as get_intents:
            with mock.patch.object(warnings, "warn") as warn:
                event_manager._check_event(member_events.MemberCreateEvent, 0)

        get_intents.assert_called_once_with(member_events.MemberCreateEvent)
        warn.assert_called_once_with(
            "You have tried to listen to MemberCreateEvent, but this will only ever be triggered if "
            "you enable one of the following intents: GUILD_MEMBERS.",
            category=errors.MissingIntentWarning,
            stacklevel=3,
        )

    def test_get_listeners_when_not_event(self, event_manager):
        event_manager._listeners = {}

        assert event_manager.get_listeners(base_events.Event) == []

    def test_get_listeners_polymorphic(self, event_manager):
        event_manager._listeners = {
            base_events.Event: ["coroutine0"],
            member_events.MemberEvent: ["coroutine1"],
            member_events.MemberCreateEvent: ["hi", "i am"],
            member_events.MemberUpdateEvent: ["hidden"],
            base_events.ExceptionEvent: ["so you won't see me"],
        }

        assert event_manager.get_listeners(member_events.MemberEvent) == ["coroutine1", "coroutine0"]

    def test_get_listeners_monomorphic_and_no_results(self, event_manager):
        event_manager._listeners = {
            member_events.MemberCreateEvent: ["coroutine1", "coroutine2"],
            member_events.MemberUpdateEvent: ["coroutine3"],
            member_events.MemberDeleteEvent: ["coroutine4", "coroutine5"],
        }

        assert event_manager.get_listeners(member_events.MemberEvent, polymorphic=False) == ()

    def test_get_listeners_monomorphic_and_results(self, event_manager):
        event_manager._listeners = {
            member_events.MemberEvent: ["coroutine0"],
            member_events.MemberCreateEvent: ["coroutine1", "coroutine2"],
            member_events.MemberUpdateEvent: ["coroutine3"],
            member_events.MemberDeleteEvent: ["coroutine4", "coroutine5"],
        }

        assert event_manager.get_listeners(member_events.MemberEvent, polymorphic=False) == ["coroutine0"]

    def test_unsubscribe_when_event_type_not_in_listeners(self, event_manager):
        async def test(): ...

        event_manager._increment_listener_group_count = mock.Mock()
        event_manager._listeners = {}

        event_manager.unsubscribe(member_events.MemberCreateEvent, test)

        assert event_manager._listeners == {}
        event_manager._increment_listener_group_count.assert_not_called()

    def test_unsubscribe_when_event_type_when_list_not_empty_after_delete(self, event_manager):
        async def test(): ...

        async def test2(): ...

        event_manager._increment_listener_group_count = mock.Mock()
        event_manager._listeners = {
            member_events.MemberCreateEvent: [test, test2],
            member_events.MemberDeleteEvent: [test],
        }

        event_manager.unsubscribe(member_events.MemberCreateEvent, test)

        assert event_manager._listeners == {
            member_events.MemberCreateEvent: [test2],
            member_events.MemberDeleteEvent: [test],
        }
        event_manager._increment_listener_group_count.assert_not_called()

    def test_unsubscribe_when_event_type_when_list_empty_after_delete(self, event_manager):
        async def test(): ...

        event_manager._increment_listener_group_count = mock.Mock()
        event_manager._listeners = {member_events.MemberCreateEvent: [test], member_events.MemberDeleteEvent: [test]}

        event_manager.unsubscribe(member_events.MemberCreateEvent, test)

        assert event_manager._listeners == {member_events.MemberDeleteEvent: [test]}
        event_manager._increment_listener_group_count.assert_called_once_with(member_events.MemberCreateEvent, -1)

    def test_listen_when_no_params(self, event_manager):
        with pytest.raises(TypeError):

            @event_manager.listen()
            async def test(): ...

    def test_listen_when_more_then_one_param_when_provided_in_typehint(self, event_manager):
        with pytest.raises(TypeError):

            @event_manager.listen()
            async def test(a, b, c): ...

    def test_listen_when_more_then_one_param_when_provided_in_decorator(self, event_manager):
        with pytest.raises(TypeError):

            @event_manager.listen(object)
            async def test(a, b, c): ...

    def test_listen_when_param_not_provided_in_decorator_nor_typehint(self, event_manager):
        with pytest.raises(TypeError):

            @event_manager.listen()
            async def test(event): ...

    def test_listen_when_param_provided_in_decorator(self, event_manager):
        stack = contextlib.ExitStack()

        subscribe = stack.enter_context(mock.patch.object(event_manager_base.EventManagerBase, "subscribe"))
        resolve_signature = stack.enter_context(mock.patch.object(reflect, "resolve_signature"))

        with stack:

            @event_manager.listen(member_events.MemberCreateEvent)
            async def test(event): ...

        resolve_signature.assert_not_called()
        subscribe.assert_called_once_with(member_events.MemberCreateEvent, test, _nested=1)

    def test_listen_when_multiple_params_provided_in_decorator(self, event_manager):
        stack = contextlib.ExitStack()

        subscribe = stack.enter_context(mock.patch.object(event_manager_base.EventManagerBase, "subscribe"))
        resolve_signature = stack.enter_context(mock.patch.object(reflect, "resolve_signature"))

        with stack:

            @event_manager.listen(member_events.MemberCreateEvent, member_events.MemberDeleteEvent)
            async def test(event): ...

        assert subscribe.call_count == 2
        resolve_signature.assert_not_called()
        subscribe.assert_has_calls(
            [
                mock.call(member_events.MemberCreateEvent, test, _nested=1),
                mock.call(member_events.MemberDeleteEvent, test, _nested=1),
            ]
        )

    def test_listen_when_param_provided_in_typehint(self, event_manager):
        with mock.patch.object(event_manager_base.EventManagerBase, "subscribe") as subscribe:

            @event_manager.listen()
            async def test(event: member_events.MemberCreateEvent): ...

        subscribe.assert_called_once_with(member_events.MemberCreateEvent, test, _nested=1)

    def test_listen_when_multiple_params_provided_as_typing_union_in_typehint(self, event_manager):
        with mock.patch.object(event_manager_base.EventManagerBase, "subscribe") as subscribe:

            @event_manager.listen()
            async def test(event: typing.Union[member_events.MemberCreateEvent, member_events.MemberDeleteEvent]): ...

        assert subscribe.call_count == 2
        subscribe.assert_has_calls(
            [
                mock.call(member_events.MemberCreateEvent, test, _nested=1),
                mock.call(member_events.MemberDeleteEvent, test, _nested=1),
            ]
        )

    @pytest.mark.skipif(sys.version_info < (3, 10), reason="Bitwise union only available on 3.10+")
    def test_listen_when_multiple_params_provided_as_bitwise_union_in_typehint(self, event_manager):
        with mock.patch.object(event_manager_base.EventManagerBase, "subscribe") as subscribe:

            @event_manager.listen()
            async def test(event: member_events.MemberCreateEvent | member_events.MemberDeleteEvent): ...

        assert subscribe.call_count == 2
        subscribe.assert_has_calls(
            [
                mock.call(member_events.MemberCreateEvent, test, _nested=1),
                mock.call(member_events.MemberDeleteEvent, test, _nested=1),
            ]
        )

    def test_listen_when_incorrect_type_in_typehint(self, event_manager):
        with pytest.raises(TypeError):

            @event_manager.listen()
            async def test(event: list[member_events.MemberUpdateEvent]): ...
