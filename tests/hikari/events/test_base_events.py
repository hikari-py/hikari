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
import attrs
import mock
import pytest

from hikari import intents
from hikari.api import shard as gateway_shard
from hikari.events import base_events


@base_events.requires_intents(intents.Intents.GUILDS)
@attrs.define(eq=False, hash=False, init=False, kw_only=True)
class DummyGuildEvent(base_events.Event):
    pass


@base_events.no_recursive_throw()
@base_events.requires_intents(intents.Intents.GUILD_PRESENCES)
@attrs.define(eq=False, hash=False, init=False, kw_only=True)
class DummyPresenceEvent(base_events.Event):
    pass


@base_events.no_recursive_throw()
@attrs.define(eq=False, hash=False, init=False, kw_only=True)
class ErrorEvent(base_events.Event):
    pass


@attrs.define(eq=False, hash=False, init=False, kw_only=True)
class DummyGuildDerivedEvent(DummyGuildEvent):
    pass


@attrs.define(eq=False, hash=False, init=False, kw_only=True)
class DummyPresenceDerivedEvent(DummyPresenceEvent):
    pass


def test_is_no_recursive_throw_event_marked():
    assert base_events.is_no_recursive_throw_event(DummyPresenceEvent)
    assert base_events.is_no_recursive_throw_event(ErrorEvent)
    assert not base_events.is_no_recursive_throw_event(DummyGuildEvent)
    assert not base_events.is_no_recursive_throw_event(DummyGuildDerivedEvent)


def test_requires_intents():
    assert list(base_events.get_required_intents_for(DummyGuildEvent)) == [intents.Intents.GUILDS]
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

    @pytest.fixture()
    def event(self, error):
        return base_events.ExceptionEvent(
            exception=error, failed_event=mock.Mock(base_events.Event), failed_callback=mock.AsyncMock()
        )

    def test_app_property(self, event):
        app = mock.Mock()
        event.failed_event.app = app
        assert event.app is app

    @pytest.mark.parametrize("has_shard", [True, False])
    def test_shard_property(self, has_shard, event):
        shard = mock.Mock(spec_set=gateway_shard.GatewayShard)
        if has_shard:
            event.failed_event.shard = shard
            assert event.shard is shard
        else:
            assert event.shard is None

    def test_exc_info_property(self, event, error):
        assert event.exc_info == (type(error), error, error.__traceback__)

    @pytest.mark.asyncio()
    async def test_retry(self, event):
        await event.retry()
        event.failed_callback.assert_awaited_once_with(event.failed_event)
