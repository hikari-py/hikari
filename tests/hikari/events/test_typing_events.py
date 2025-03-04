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

import typing

import mock
import pytest

from hikari import channels
from hikari.events import typing_events
from tests.hikari import hikari_test_helpers


class TestTypingEvent:
    @pytest.fixture
    def event(self) -> typing_events.TypingEvent:
        cls = hikari_test_helpers.mock_class_namespace(
            typing_events.TypingEvent, channel_id=123, user_id=456, timestamp=mock.Mock(), shard=mock.Mock()
        )

        return cls()

    def test_get_user_when_no_cache(self, event: typing_events.TypingEvent):
        event = hikari_test_helpers.mock_class_namespace(typing_events.TypingEvent, app=None)()

        assert event.get_user() is None

    def test_get_user(self, event: typing_events.TypingEvent):
        assert event.get_user() is event.app.cache.get_user.return_value

    def test_trigger_typing(self, event: typing_events.TypingEvent):
        event.app.rest.trigger_typing = mock.Mock()
        result = event.trigger_typing()
        event.app.rest.trigger_typing.assert_called_once_with(123)
        assert result is event.app.rest.trigger_typing.return_value


class TestGuildTypingEvent:
    @pytest.fixture
    def event(self) -> typing_events.GuildTypingEvent:
        cls = hikari_test_helpers.mock_class_namespace(typing_events.GuildTypingEvent)

        return cls(
            channel_id=123,
            timestamp=mock.Mock(),
            shard=mock.Mock(),
            guild_id=789,
            member=mock.Mock(id=456, app=mock.Mock(rest=mock.AsyncMock())),
        )

    def test_app_property(self, event: typing_events.GuildTypingEvent):
        assert event.app is event.member.app

    def test_get_channel_when_no_cache(self):
        event = hikari_test_helpers.mock_class_namespace(typing_events.GuildTypingEvent, app=None, init_=False)()

        assert event.get_channel() is None

    @pytest.mark.parametrize("guild_channel_impl", [channels.GuildNewsChannel, channels.GuildTextChannel])
    def test_get_channel(
        self,
        event: typing_events.GuildTypingEvent,
        guild_channel_impl: typing.Union[channels.GuildNewsChannel, channels.GuildTextChannel],
    ):
        event.app.cache.get_guild_channel = mock.Mock(return_value=mock.Mock(spec_set=guild_channel_impl))
        result = event.get_channel()

        assert result is event.app.cache.get_guild_channel.return_value
        event.app.cache.get_guild_channel.assert_called_once_with(123)

    @pytest.mark.asyncio
    async def test_get_guild_when_no_cache(self):
        event = hikari_test_helpers.mock_class_namespace(typing_events.GuildTypingEvent, app=None, init_=False)()

        assert event.get_guild() is None

    def test_get_guild_when_available(self, event: typing_events.GuildTypingEvent):
        result = event.get_guild()

        assert result is event.app.cache.get_available_guild.return_value
        event.app.cache.get_available_guild.assert_called_once_with(789)
        event.app.cache.get_unavailable_guild.assert_not_called()

    def test_get_guild_when_unavailable(self, event: typing_events.GuildTypingEvent):
        event.app.cache.get_available_guild.return_value = None
        result = event.get_guild()

        assert result is event.app.cache.get_unavailable_guild.return_value
        event.app.cache.get_unavailable_guild.assert_called_once_with(789)
        event.app.cache.get_available_guild.assert_called_once_with(789)

    def test_user_id(self, event: typing_events.GuildTypingEvent):
        assert event.user_id == event.member.id
        assert event.user_id == 456

    @pytest.mark.asyncio
    @pytest.mark.parametrize("guild_channel_impl", [channels.GuildNewsChannel, channels.GuildTextChannel])
    async def test_fetch_channel(
        self,
        event: typing_events.GuildTypingEvent,
        guild_channel_impl: typing.Union[channels.GuildNewsChannel, channels.GuildTextChannel],
    ):
        event.app.rest.fetch_channel = mock.AsyncMock(return_value=mock.Mock(spec_set=guild_channel_impl))
        await event.fetch_channel()

        event.app.rest.fetch_channel.assert_awaited_once_with(123)

    @pytest.mark.asyncio
    async def test_fetch_guild(self, event: typing_events.GuildTypingEvent):
        await event.fetch_guild()

        event.app.rest.fetch_guild.assert_awaited_once_with(789)

    @pytest.mark.asyncio
    async def test_fetch_guild_preview(self, event: typing_events.GuildTypingEvent):
        await event.fetch_guild_preview()

        event.app.rest.fetch_guild_preview.assert_awaited_once_with(789)

    @pytest.mark.asyncio
    async def test_fetch_member(self, event: typing_events.GuildTypingEvent):
        await event.fetch_member()

        event.app.rest.fetch_member.assert_awaited_once_with(789, 456)


@pytest.mark.asyncio
class TestDMTypingEvent:
    @pytest.fixture
    def event(self) -> typing_events.DMTypingEvent:
        cls = hikari_test_helpers.mock_class_namespace(typing_events.DMTypingEvent)

        return cls(
            channel_id=123, timestamp=mock.Mock(), shard=mock.Mock(), app=mock.Mock(rest=mock.AsyncMock()), user_id=456
        )

    async def test_fetch_channel(self, event: typing_events.DMTypingEvent):
        event.app.rest.fetch_channel = mock.AsyncMock(return_value=mock.Mock(spec_set=channels.DMChannel))
        await event.fetch_channel()

        event.app.rest.fetch_channel.assert_awaited_once_with(123)

    async def test_fetch_user(self, event: typing_events.DMTypingEvent):
        await event.fetch_user()

        event.app.rest.fetch_user.assert_awaited_once_with(456)
