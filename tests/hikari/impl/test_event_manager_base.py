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
import warnings

import mock
import pytest

from hikari import errors
from hikari import intents
from hikari.events import base_events
from hikari.events import member_events
from hikari.impl import event_manager_base


def test__default_predicate_returns_True():
    assert event_manager_base._default_predicate(None) is True


class TestEventManagerBase:
    @pytest.fixture()
    def event_manager(self):
        class EventManagerBaseImpl(event_manager_base.EventManagerBase):
            on_existing_event = None

        return EventManagerBaseImpl(None, None)

    @pytest.mark.asyncio
    async def test_consume_raw_event_when_AttributeError(self, event_manager):
        with mock.patch.object(event_manager_base, "_LOGGER") as logger:
            event_manager.consume_raw_event(None, "UNEXISTING_EVENT", {})

        logger.debug.assert_called_once_with("ignoring unknown event %s", "UNEXISTING_EVENT")

    @pytest.mark.asyncio
    async def test_consume_raw_event_when_found(self, event_manager):
        event_manager._handle_dispatch = mock.Mock()
        event_manager.on_existing_event = mock.Mock()
        shard = object()

        with mock.patch("asyncio.create_task") as create_task:
            event_manager.consume_raw_event(shard, "EXISTING_EVENT", {"berp": "baz"})

        event_manager._handle_dispatch.assert_called_once_with(event_manager.on_existing_event, shard, {"berp": "baz"})
        create_task.assert_called_once_with(
            event_manager._handle_dispatch(event_manager.on_existing_event, shard, {"berp": "baz"}),
            name="dispatch EXISTING_EVENT",
        )

    @pytest.mark.asyncio
    async def test_handle_dispatch_invokes_callback(self, event_manager, event_loop):
        callback = mock.AsyncMock()
        error_handler = mock.MagicMock()
        event_loop.set_exception_handler(error_handler)
        shard = object()
        pl = {"foo": "bar"}

        await event_manager._handle_dispatch(callback, shard, pl)

        callback.assert_awaited_once_with(shard, pl)
        error_handler.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_dispatch_ignores_cancelled_errors(self, event_manager, event_loop):
        callback = mock.AsyncMock(side_effect=asyncio.CancelledError)
        error_handler = mock.MagicMock()
        event_loop.set_exception_handler(error_handler)
        shard = object()
        pl = {"lorem": "ipsum"}

        await event_manager._handle_dispatch(callback, shard, pl)

        error_handler.assert_not_called()

    @pytest.mark.asyncio
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
                "message": "Exception occurred in internal event dispatch conduit",
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
            assert event_manager.subscribe(member_events.MemberCreateEvent, test, _nested=1) == test

        assert event_manager._listeners == {member_events.MemberCreateEvent: [test]}
        check.assert_called_once_with(member_events.MemberCreateEvent, 1)

    def test_subscribe_when_event_type_in_listeners(self, event_manager):
        async def test():
            ...

        async def test2():
            ...

        event_manager._listeners[member_events.MemberCreateEvent] = [test2]

        with mock.patch.object(event_manager_base.EventManagerBase, "_check_intents") as check:
            assert event_manager.subscribe(member_events.MemberCreateEvent, test, _nested=2) == test

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

    def test_get_listeners_polimorphic(self, event_manager):
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

    def test_get_listeners_no_polimorphic_and_no_results(self, event_manager):
        event_manager._listeners = {
            member_events.MemberCreateEvent: ["coroutine1", "coroutine2"],
            member_events.MemberUpdateEvent: ["coroutine3"],
            member_events.MemberDeleteEvent: ["coroutine4", "coroutine5"],
            member_events.MemberDeleteEvent: ["coroutine4", "coroutine5"],
        }

        assert event_manager.get_listeners(member_events.MemberEvent, polymorphic=False) == []

    def test_get_listeners_no_polimorphic_and_results(self, event_manager):
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

    def test_listen_when_more_then_one_param(self, event_manager):
        with pytest.raises(TypeError):

            @event_manager.listen()
            async def test(a, b, c):
                ...

    def test_listen_when_param_not_provided_in_decorator_nor_typehint(self, event_manager):
        with pytest.raises(TypeError):

            @event_manager.listen()
            async def test(event):
                ...

    def test_listen_when_param_provided_in_decorator(self, event_manager):
        with mock.patch.object(event_manager_base.EventManagerBase, "subscribe") as subscribe:

            @event_manager.listen(member_events.MemberCreateEvent)
            async def test(event):
                ...

        subscribe.assert_called_once_with(member_events.MemberCreateEvent, test, _nested=1)

    def test_listen_when_param_provided_in_typehint(self, event_manager):
        with mock.patch.object(event_manager_base.EventManagerBase, "subscribe") as subscribe:

            @event_manager.listen()
            async def test(event: member_events.MemberCreateEvent):
                ...

        subscribe.assert_called_once_with(member_events.MemberCreateEvent, test, _nested=1)
