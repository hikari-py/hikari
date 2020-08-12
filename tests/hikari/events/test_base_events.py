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
import attr
import mock
import pytest

from hikari.events import base_events
from hikari.models import intents


@base_events.requires_intents(intents.Intents.GUILDS)
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class DummyGuildEVent(base_events.Event):
    pass


@base_events.no_recursive_throw()
@base_events.requires_intents(intents.Intents.GUILD_PRESENCES)
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class DummyPresenceEvent(base_events.Event):
    pass


@base_events.no_recursive_throw()
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class ErrorEvent(base_events.Event):
    pass


@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class DummyGuildDerivedEvent(DummyGuildEVent):
    pass


@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class DummyPresenceDerivedEvent(DummyPresenceEvent):
    pass


def test_is_no_recursive_throw_event_marked():
    assert base_events.is_no_recursive_throw_event(DummyPresenceEvent)
    assert base_events.is_no_recursive_throw_event(ErrorEvent)
    assert not base_events.is_no_recursive_throw_event(DummyGuildEVent)
    assert not base_events.is_no_recursive_throw_event(DummyGuildDerivedEvent)


def test_requires_intents():
    assert list(base_events.get_required_intents_for(DummyGuildEVent)) == [intents.Intents.GUILDS]
    assert list(base_events.get_required_intents_for(DummyPresenceEvent)) == [intents.Intents.GUILD_PRESENCES]
    assert list(base_events.get_required_intents_for(ErrorEvent)) == []


def test_inherited_requires_intents():
    assert list(base_events.get_required_intents_for(DummyPresenceDerivedEvent)) == [intents.Intents.GUILD_PRESENCES]
    assert list(base_events.get_required_intents_for(DummyGuildDerivedEvent)) == [intents.Intents.GUILDS]


def test_inherited_is_no_recursive_throw_event():
    assert base_events.is_no_recursive_throw_event(DummyPresenceDerivedEvent)
    assert not base_events.is_no_recursive_throw_event(DummyGuildDerivedEvent)


class TestExceptionEvent:
    @pytest.fixture(scope="class")  # we don't modify this so make it once.
    def error(self):
        # Raise and catch to fill in the traceback attribute.
        try:
            raise RuntimeError("blah")
        except RuntimeError as ex:
            return ex

    @pytest.fixture
    def event(self, error):
        return base_events.ExceptionEvent(
            app=object(),
            shard=object(),
            exception=error,
            failed_event=mock.Mock(base_events.Event),
            failed_callback=mock.AsyncMock(),
        )

    def test_failed_callback_property(self, event):
        stub_callback = object()
        event._failed_callback = stub_callback
        assert event.failed_callback is stub_callback

    def test_exc_info_property(self, event, error):
        assert event.exc_info == (type(error), error, error.__traceback__)

    @pytest.mark.asyncio
    async def test_retry(self, event):
        await event.retry()
        event._failed_callback.assert_awaited_once_with(event.failed_event)
