# -*- coding: utf-8 -*-
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021 davfsa
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
import contextlib
import logging
import unittest
import warnings
import weakref

import mock
import pytest

from hikari import config
from hikari import errors
from hikari import intents
from hikari import iterators
from hikari import undefined
from hikari.events import base_events
from hikari.events import member_events
from hikari.events import shard_events
from hikari.impl import event_manager_base
from hikari.internal import reflect
from tests.hikari import hikari_test_helpers


class TestGenerateWeakListener:
    @pytest.mark.asyncio()
    async def test__generate_weak_listener_when_method_is_None(self):
        def test():
            return None

        call_weak_method = event_manager_base._generate_weak_listener(test)

        with pytest.raises(
            TypeError,
            match=r"dead weak referenced subscriber method cannot be executed, try actually closing your event streamers",
        ):
            await call_weak_method(None)

    @pytest.mark.asyncio()
    async def test__generate_weak_listener(self):
        mock_listener = mock.AsyncMock()
        mock_event = object()

        def test():
            return mock_listener

        call_weak_method = event_manager_base._generate_weak_listener(test)

        await call_weak_method(mock_event)

        mock_listener.assert_awaited_once_with(mock_event)


@pytest.fixture()
def mock_app():
    return mock.Mock()


class TestEventStream:
    @pytest.mark.asyncio()
    async def test___aenter___and___aexit__(
        self,
    ):
        stub_stream = hikari_test_helpers.mock_class_namespace(
            event_manager_base.EventStream, open=mock.AsyncMock(), close=mock.AsyncMock()
        )(mock_app, base_events.Event, timeout=None)

        async with stub_stream:
            stub_stream.open.assert_awaited_once()
            stub_stream.close.assert_not_called()

        stub_stream.open.assert_awaited_once()
        stub_stream.close.assert_awaited_once()

    def test___enter__(self):
        # flake8 gets annoyed if we use "with" here so here's a hacky alternative
        stub_stream = hikari_test_helpers.mock_class_namespace(event_manager_base.EventStream)(
            mock_app, base_events.Event, timeout=None
        )

        with pytest.raises(TypeError, match=" is async-only, did you mean 'async with'?"):
            stub_stream.__enter__()

    def test___exit__(self):
        stub_stream = hikari_test_helpers.mock_class_namespace(event_manager_base.EventStream)(
            mock_app, base_events.Event, timeout=None
        )

        try:
            stub_stream.__exit__(None, None, None)
        except AttributeError as exc:
            pytest.fail(exc)

    @pytest.mark.asyncio()
    async def test__listener_when_filter_returns_false(self, mock_app):
        stream = event_manager_base.EventStream(mock_app, base_events.Event, timeout=None)
        stream.filter(lambda _: False)
        mock_event = object()

        assert await stream._listener(mock_event) is None
        assert stream._queue.qsize() == 0

    @pytest.mark.asyncio()
    async def test__listener_when_filter_passes_and_queue_full(self, mock_app):
        stream = event_manager_base.EventStream(mock_app, base_events.Event, timeout=None, limit=2)
        stream._queue.put_nowait(object())
        stream._queue.put_nowait(object())
        stream.filter(lambda _: True)
        mock_event = object()

        assert await stream._listener(mock_event) is None
        assert stream._queue.qsize() == 2
        assert stream._queue.get_nowait() is not mock_event
        assert stream._queue.get_nowait() is not mock_event

    @pytest.mark.asyncio()
    async def test__listener_when_filter_passes_and_queue_not_full(self, mock_app):
        stream = event_manager_base.EventStream(mock_app, base_events.Event, timeout=None, limit=None)
        stream._queue.put_nowait(object())
        stream._queue.put_nowait(object())
        stream.filter(lambda _: True)
        mock_event = object()

        assert await stream._listener(mock_event) is None
        assert stream._queue.qsize() == 3
        assert stream._queue.get_nowait() is not mock_event
        assert stream._queue.get_nowait() is not mock_event
        assert stream._queue.get_nowait() is mock_event

    @pytest.mark.asyncio()
    @hikari_test_helpers.timeout()
    async def test___anext___when_stream_closed(self):
        streamer = event_manager_base.EventStream(mock.Mock(), event_type=base_events.Event, timeout=float("inf"))

        # flake8 gets annoyed if we use "with" here so here's a hacky alternative
        with pytest.raises(TypeError):
            await streamer.__anext__()

    @pytest.mark.asyncio()
    @hikari_test_helpers.timeout()
    async def test___anext___times_out(self):
        streamer = event_manager_base.EventStream(
            mock.Mock(), event_type=base_events.Event, timeout=hikari_test_helpers.REASONABLE_QUICK_RESPONSE_TIME
        )

        async with streamer:
            async for _ in streamer:
                pytest.fail("streamer shouldn't have yielded anything")

    @pytest.mark.asyncio()
    @hikari_test_helpers.timeout()
    async def test___anext___waits_for_next_event(self):
        mock_event = object()
        streamer = event_manager_base.EventStream(
            mock.Mock(), event_type=base_events.Event, timeout=hikari_test_helpers.REASONABLE_QUICK_RESPONSE_TIME * 3
        )

        async def add_event():
            await asyncio.sleep(hikari_test_helpers.REASONABLE_SLEEP_TIME)
            streamer._queue.put_nowait(mock_event)

        asyncio.create_task(add_event())

        async with streamer:
            async for event in streamer:
                assert event is mock_event
                return

            pytest.fail("streamer should've yielded something")

    @pytest.mark.asyncio()
    @hikari_test_helpers.timeout()
    async def test___anext__(self):
        mock_event = object()
        streamer = event_manager_base.EventStream(
            event_manager=mock.Mock(),
            event_type=base_events.Event,
            timeout=hikari_test_helpers.REASONABLE_QUICK_RESPONSE_TIME,
        )
        streamer._queue.put_nowait(mock_event)

        async with streamer:
            async for event in streamer:
                assert event is mock_event
                return

        pytest.fail("streamer should've yielded something")

    @pytest.mark.asyncio()
    async def test___await__(self):
        mock_event_0 = object()
        mock_event_1 = object()
        mock_event_2 = object()
        streamer = hikari_test_helpers.mock_class_namespace(
            event_manager_base.EventStream,
            close=mock.AsyncMock(),
            open=mock.AsyncMock(),
            init_=False,
            _active=False,
            __anext__=mock.AsyncMock(side_effect=[mock_event_0, mock_event_1, mock_event_2]),
        )()

        assert await streamer == [mock_event_0, mock_event_1, mock_event_2]
        streamer.open.assert_awaited_once()
        streamer.close.assert_awaited_once()

    def test___del___for_active_stream(self):
        mock_coroutine = object()
        close_method = mock.Mock(return_value=mock_coroutine)
        streamer = hikari_test_helpers.mock_class_namespace(
            event_manager_base.EventStream, close=close_method, init_=False
        )()
        streamer._event_type = base_events.Event
        streamer._active = True

        with mock.patch.object(asyncio, "ensure_future", side_effect=RuntimeError) as ensure_future:
            with unittest.TestCase().assertLogs("hikari.event_manager", level=logging.WARNING) as logging_watcher:
                del streamer

        assert logging_watcher.output == [
            "WARNING:hikari.event_manager:active 'Event' streamer fell out of scope before being closed"
        ]
        ensure_future.assert_called_once_with(mock_coroutine)
        close_method.assert_called_once_with()

    def test___del___for_inactive_stream(self):
        close_method = mock.Mock()
        streamer = hikari_test_helpers.mock_class_namespace(
            event_manager_base.EventStream, close=close_method, init_=False
        )()
        streamer._event_type = base_events.Event
        streamer._active = False

        with mock.patch.object(asyncio, "ensure_future"):
            del streamer
            asyncio.ensure_future.assert_not_called()

        close_method.assert_not_called()

    @pytest.mark.asyncio()
    async def test_close_for_inactive_stream(self, mock_app):
        stream = event_manager_base.EventStream(mock_app, base_events.Event, timeout=None, limit=None)
        await stream.close()
        mock_app.event_manager.unsubscribe.assert_not_called()

    @pytest.mark.asyncio()
    @hikari_test_helpers.timeout()
    async def test_close_for_active_stream(self):
        mock_registered_listener = object()
        mock_manager = mock.Mock()
        stream = hikari_test_helpers.mock_class_namespace(event_manager_base.EventStream)(
            event_manager=mock_manager, event_type=base_events.Event, timeout=float("inf")
        )

        await stream.open()
        stream._registered_listener = mock_registered_listener
        await stream.close()
        mock_manager.unsubscribe.assert_called_once_with(base_events.Event, mock_registered_listener)
        assert stream._active is False
        assert stream._registered_listener is None

    @pytest.mark.asyncio()
    @hikari_test_helpers.timeout()
    async def test_close_for_active_stream_handles_value_error(self):
        mock_registered_listener = object()
        mock_manager = mock.Mock()
        mock_manager.unsubscribe.side_effect = ValueError
        stream = hikari_test_helpers.mock_class_namespace(event_manager_base.EventStream)(
            event_manager=mock_manager, event_type=base_events.Event, timeout=float("inf")
        )

        await stream.open()
        stream._registered_listener = mock_registered_listener
        await stream.close()
        mock_manager.unsubscribe.assert_called_once_with(base_events.Event, mock_registered_listener)
        assert stream._active is False
        assert stream._registered_listener is None

    def test_filter_for_inactive_stream(self):
        stream = hikari_test_helpers.mock_class_namespace(event_manager_base.EventStream)(
            event_manager=mock.Mock(), event_type=base_events.Event, timeout=1
        )
        stream._filters = iterators.All(())
        first_pass = mock.Mock(attr=True)
        second_pass = mock.Mock(attr=True)
        first_fails = mock.Mock(attr=True)
        second_fail = mock.Mock(attr=False)

        def predicate(obj):
            return obj in (first_pass, second_pass)

        stream.filter(predicate, attr=True)

        assert stream._filters(first_pass) is True
        assert stream._filters(first_fails) is False
        assert stream._filters(second_pass) is True
        assert stream._filters(second_fail) is False

    @pytest.mark.asyncio()
    async def test_filter_for_active_stream(self):
        stream = hikari_test_helpers.mock_class_namespace(event_manager_base.EventStream)(
            event_manager=mock.Mock(), event_type=base_events.Event, timeout=float("inf")
        )
        stream._active = True
        mock_wrapping_iterator = object()
        predicate = object()

        with mock.patch.object(iterators.LazyIterator, "filter", return_value=mock_wrapping_iterator):
            assert stream.filter(predicate, name="OK") is mock_wrapping_iterator

            iterators.LazyIterator.filter.assert_called_once_with(predicate, name="OK")

        # Ensure we don't get a warning or error on del
        stream._active = False

    @pytest.mark.asyncio()
    async def test_open_for_inactive_stream(self):
        mock_listener = object()
        mock_manager = mock.Mock()
        stream = hikari_test_helpers.mock_class_namespace(event_manager_base.EventStream)(
            event_manager=mock_manager,
            event_type=base_events.Event,
            timeout=float("inf"),
        )

        stream._active = True
        stream._registered_listener = mock_listener

        with mock.patch.object(event_manager_base, "_generate_weak_listener"):
            with mock.patch.object(weakref, "WeakMethod"):
                await stream.open()

                weakref.WeakMethod.assert_not_called()
            event_manager_base._generate_weak_listener.assert_not_called()

        mock_manager.subscribe.assert_not_called()
        assert stream._active is True
        assert stream._registered_listener is mock_listener

        # Ensure we don't get a warning or error on del
        stream._active = False

    @pytest.mark.asyncio()
    @hikari_test_helpers.timeout()
    async def test_open_for_active_stream(self):
        mock_manager = mock.Mock()
        stream = hikari_test_helpers.mock_class_namespace(event_manager_base.EventStream)(
            event_manager=mock_manager, event_type=base_events.Event, timeout=float("inf")
        )
        stream._active = False
        mock_listener = object()
        mock_listener_ref = object()

        with mock.patch.object(event_manager_base, "_generate_weak_listener", return_value=mock_listener):
            with mock.patch.object(weakref, "WeakMethod", return_value=mock_listener_ref):
                await stream.open()

                weakref.WeakMethod.assert_called_once_with(stream._listener)
            event_manager_base._generate_weak_listener.assert_called_once_with(mock_listener_ref)

        mock_manager.subscribe.assert_called_once_with(base_events.Event, mock_listener)
        assert stream._active is True
        assert stream._registered_listener is mock_listener

        # Ensure we don't get a warning or error on del
        stream._active = False


def test__default_predicate_returns_True():
    assert event_manager_base._default_predicate(None) is True


class TestEventManagerBase:
    @pytest.fixture()
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

            async def on_not_decorated(self, event):
                raise NotImplementedError

            async def not_a_listener(self):
                raise NotImplementedError

        expected_foo_events = (shard_events.ShardEvent, base_events.Event)
        expected_bar_events = (
            shard_events.ShardStateEvent,
            shard_events.ShardEvent,
            base_events.Event,
            shard_events.ShardPayloadEvent,
        )
        manager = StubManager(mock.Mock(), mock.Mock(intents=42))
        assert manager._consumers == {
            "foo": event_manager_base._Consumer(manager.on_foo, config.CacheComponents.MEMBERS, expected_foo_events),
            "bar": event_manager_base._Consumer(manager.on_bar, config.CacheComponents.NONE, expected_bar_events),
            "not_decorated": event_manager_base._Consumer(
                manager.on_not_decorated, undefined.UNDEFINED, undefined.UNDEFINED
            ),
        }

    @pytest.mark.asyncio()
    async def test_consume_raw_event_when_KeyError(self, event_manager):
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

    @pytest.mark.asyncio()
    async def test_consume_raw_event_when_found(self, event_manager):
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
            event_manager._handle_dispatch(on_existing_event, shard, {"berp": "baz"}),
            name="dispatch EXISTING_EVENT",
        )
        event_manager.dispatch.assert_called_once_with(
            event_manager._event_factory.deserialize_shard_payload_event.return_value
        )
        event_manager._event_factory.deserialize_shard_payload_event.assert_called_once_with(
            shard, payload, name="EXISTING_EVENT"
        )

    @pytest.mark.asyncio()
    async def test_handle_dispatch_invokes_callback(self, event_manager, event_loop):
        callback = mock.AsyncMock()
        error_handler = mock.MagicMock()
        event_loop.set_exception_handler(error_handler)
        shard = object()
        pl = {"foo": "bar"}

        await event_manager._handle_dispatch(callback, shard, pl)

        callback.assert_awaited_once_with(shard, pl)
        error_handler.assert_not_called()

    @pytest.mark.asyncio()
    async def test_handle_dispatch_ignores_cancelled_errors(self, event_manager, event_loop):
        callback = mock.AsyncMock(side_effect=asyncio.CancelledError)
        error_handler = mock.MagicMock()
        event_loop.set_exception_handler(error_handler)
        shard = object()
        pl = {"lorem": "ipsum"}

        await event_manager._handle_dispatch(callback, shard, pl)

        error_handler.assert_not_called()

    @pytest.mark.asyncio()
    async def test_handle_dispatch_handles_exceptions(self, event_manager, event_loop):
        exc = Exception("aaaa!")
        callback = mock.AsyncMock(side_effect=exc)
        error_handler = mock.MagicMock()
        event_loop.set_exception_handler(error_handler)
        shard = object()
        pl = {"i like": "cats"}

        with mock.patch.object(asyncio, "current_task") as current_task:
            await event_manager._handle_dispatch(callback, shard, pl)

        error_handler.assert_called_once_with(
            event_loop,
            {
                "exception": exc,
                "message": "Exception occurred in raw event dispatch conduit",
                "task": current_task(),
            },
        )

    def test_subscribe_when_callback_is_not_coroutine(self, event_manager):
        def test():
            ...

        with pytest.raises(TypeError):
            event_manager.subscribe(member_events.MemberCreateEvent, test)

    def test_subscribe_when_event_type_does_not_subclass_Event(self, event_manager):
        async def test():
            ...

        with pytest.raises(TypeError):
            event_manager.subscribe("test", test)

    def test_subscribe_when_event_type_not_in_listeners(self, event_manager):
        async def test():
            ...

        with mock.patch.object(event_manager_base.EventManagerBase, "_check_intents") as check:
            event_manager.subscribe(member_events.MemberCreateEvent, test, _nested=1)

        assert event_manager._listeners == {member_events.MemberCreateEvent: [test]}
        check.assert_called_once_with(member_events.MemberCreateEvent, 1)

    def test_subscribe_when_event_type_in_listeners(self, event_manager):
        async def test():
            ...

        async def test2():
            ...

        event_manager._listeners[member_events.MemberCreateEvent] = [test2]

        with mock.patch.object(event_manager_base.EventManagerBase, "_check_intents") as check:
            event_manager.subscribe(member_events.MemberCreateEvent, test, _nested=2)

        assert event_manager._listeners == {member_events.MemberCreateEvent: [test2, test]}
        check.assert_called_once_with(member_events.MemberCreateEvent, 2)

    def test__check_intents_when_no_intents_required(self, event_manager):
        event_manager._intents = intents.Intents.ALL

        with mock.patch.object(base_events, "get_required_intents_for", return_value=None) as get_intents:
            with mock.patch.object(warnings, "warn") as warn:
                event_manager._check_intents(member_events.MemberCreateEvent, 0)

        get_intents.assert_called_once_with(member_events.MemberCreateEvent)
        warn.assert_not_called()

    def test__check_intents_when_intents_correct(self, event_manager):
        event_manager._intents = intents.Intents.GUILD_EMOJIS | intents.Intents.GUILD_MEMBERS

        with mock.patch.object(
            base_events, "get_required_intents_for", return_value=intents.Intents.GUILD_MEMBERS
        ) as get_intents:
            with mock.patch.object(warnings, "warn") as warn:
                event_manager._check_intents(member_events.MemberCreateEvent, 0)

        get_intents.assert_called_once_with(member_events.MemberCreateEvent)
        warn.assert_not_called()

    def test__check_intents_when_intents_incorrect(self, event_manager):
        event_manager._intents = intents.Intents.GUILD_EMOJIS

        with mock.patch.object(
            base_events, "get_required_intents_for", return_value=intents.Intents.GUILD_MEMBERS
        ) as get_intents:
            with mock.patch.object(warnings, "warn") as warn:
                event_manager._check_intents(member_events.MemberCreateEvent, 0)

        get_intents.assert_called_once_with(member_events.MemberCreateEvent)
        warn.assert_called_once_with(
            "You have tried to listen to MemberCreateEvent, but this will only ever be triggered if "
            "you enable one of the following intents: GUILD_MEMBERS.",
            category=errors.MissingIntentWarning,
            stacklevel=3,
        )

    def test_get_listeners_when_not_event(self, event_manager):
        assert len(event_manager.get_listeners("test")) == 0

    def test_get_listeners_polymorphic(self, event_manager):
        event_manager._listeners = {
            base_events.Event: ["this will never appear"],
            member_events.MemberEvent: ["coroutine0"],
            member_events.MemberCreateEvent: ["coroutine1", "coroutine2"],
            member_events.MemberUpdateEvent: ["coroutine3"],
            member_events.MemberDeleteEvent: ["coroutine4", "coroutine5"],
        }

        assert event_manager.get_listeners(member_events.MemberEvent) == [
            "coroutine0",
            "coroutine1",
            "coroutine2",
            "coroutine3",
            "coroutine4",
            "coroutine5",
        ]

    def test_get_listeners_monomorphic_and_no_results(self, event_manager):
        event_manager._listeners = {
            member_events.MemberCreateEvent: ["coroutine1", "coroutine2"],
            member_events.MemberUpdateEvent: ["coroutine3"],
            member_events.MemberDeleteEvent: ["coroutine4", "coroutine5"],
        }

        assert event_manager.get_listeners(member_events.MemberEvent, polymorphic=False) == []

    def test_get_listeners_monomorphic_and_results(self, event_manager):
        event_manager._listeners = {
            member_events.MemberEvent: ["coroutine0"],
            member_events.MemberCreateEvent: ["coroutine1", "coroutine2"],
            member_events.MemberUpdateEvent: ["coroutine3"],
            member_events.MemberDeleteEvent: ["coroutine4", "coroutine5"],
        }

        assert event_manager.get_listeners(member_events.MemberEvent, polymorphic=False) == ["coroutine0"]

    def test_unsubscribe_when_event_type_not_in_listeners(self, event_manager):
        async def test():
            ...

        event_manager._listeners = {}

        event_manager.unsubscribe(member_events.MemberCreateEvent, test)

        assert event_manager._listeners == {}

    def test_unsubscribe_when_event_type_when_list_not_empty_after_delete(self, event_manager):
        async def test():
            ...

        async def test2():
            ...

        event_manager._listeners = {
            member_events.MemberCreateEvent: [test, test2],
            member_events.MemberDeleteEvent: [test],
        }

        event_manager.unsubscribe(member_events.MemberCreateEvent, test)

        assert event_manager._listeners == {
            member_events.MemberCreateEvent: [test2],
            member_events.MemberDeleteEvent: [test],
        }

    def test_unsubscribe_when_event_type_when_list_empty_after_delete(self, event_manager):
        async def test():
            ...

        event_manager._listeners = {member_events.MemberCreateEvent: [test], member_events.MemberDeleteEvent: [test]}

        event_manager.unsubscribe(member_events.MemberCreateEvent, test)

        assert event_manager._listeners == {member_events.MemberDeleteEvent: [test]}

    def test_listen_when_no_params(self, event_manager):
        with pytest.raises(TypeError):

            @event_manager.listen()
            async def test():
                ...

    def test_listen_when_more_then_one_param_when_provided_in_typehint(self, event_manager):
        with pytest.raises(TypeError):

            @event_manager.listen()
            async def test(a, b, c):
                ...

    def test_listen_when_more_then_one_param_when_provided_in_decorator(self, event_manager):
        with pytest.raises(TypeError):

            @event_manager.listen(object)
            async def test(a, b, c):
                ...

    def test_listen_when_param_not_provided_in_decorator_nor_typehint(self, event_manager):
        with pytest.raises(TypeError):

            @event_manager.listen()
            async def test(event):
                ...

    def test_listen_when_param_provided_in_decorator(self, event_manager):
        stack = contextlib.ExitStack()

        subscribe = stack.enter_context(mock.patch.object(event_manager_base.EventManagerBase, "subscribe"))
        resolve_signature = stack.enter_context(mock.patch.object(reflect, "resolve_signature"))

        with stack:

            @event_manager.listen(member_events.MemberCreateEvent)
            async def test(event):
                ...

        resolve_signature.assert_not_called()
        subscribe.assert_called_once_with(member_events.MemberCreateEvent, test, _nested=1)

    def test_listen_when_param_provided_in_typehint(self, event_manager):
        with mock.patch.object(event_manager_base.EventManagerBase, "subscribe") as subscribe:

            @event_manager.listen()
            async def test(event: member_events.MemberCreateEvent):
                ...

        subscribe.assert_called_once_with(member_events.MemberCreateEvent, test, _nested=1)
