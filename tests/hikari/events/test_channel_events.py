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

import mock
import pytest

from hikari import channels
from hikari import snowflakes
from hikari.events import channel_events
from tests.hikari import hikari_test_helpers


class TestGuildChannelEvent:
    @pytest.fixture
    def event(self):
        cls = hikari_test_helpers.mock_class_namespace(
            channel_events.GuildChannelEvent,
            guild_id=mock.PropertyMock(return_value=snowflakes.Snowflake(929292929)),
            channel_id=mock.PropertyMock(return_value=snowflakes.Snowflake(432432432)),
        )
        return cls()

    def test_get_guild_when_available(self, event):
        result = event.get_guild()

        assert result is event.app.cache.get_available_guild.return_value
        event.app.cache.get_available_guild.assert_called_once_with(929292929)
        event.app.cache.get_unavailable_guild.assert_not_called()

    def test_get_guild_when_unavailable(self, event):
        event.app.cache.get_available_guild.return_value = None
        result = event.get_guild()

        assert result is event.app.cache.get_unavailable_guild.return_value
        event.app.cache.get_available_guild.assert_called_once_with(929292929)
        event.app.cache.get_unavailable_guild.assert_called_once_with(929292929)

    def test_get_guild_without_cache(self):
        event = hikari_test_helpers.mock_class_namespace(channel_events.GuildChannelEvent, app=None)()

        assert event.get_guild() is None

    @pytest.mark.asyncio
    async def test_fetch_guild(self, event):
        event.app.rest.fetch_guild = mock.AsyncMock()
        result = await event.fetch_guild()

        assert result is event.app.rest.fetch_guild.return_value
        event.app.rest.fetch_guild.assert_awaited_once_with(929292929)

    def test_get_channel(self, event):
        result = event.get_channel()

        assert result is event.app.cache.get_guild_channel.return_value
        event.app.cache.get_guild_channel.assert_called_once_with(432432432)

    def test_get_channel_without_cache(self):
        event = hikari_test_helpers.mock_class_namespace(channel_events.GuildChannelEvent, app=None)()

        assert event.get_channel() is None

    @pytest.mark.asyncio
    async def test_fetch_channel(self, event):
        event.app.rest.fetch_channel = mock.AsyncMock(return_value=mock.MagicMock(spec=channels.GuildChannel))
        result = await event.fetch_channel()

        assert result is event.app.rest.fetch_channel.return_value
        event.app.rest.fetch_channel.assert_awaited_once_with(432432432)


class TestGuildChannelCreateEvent:
    @pytest.fixture
    def event(self):
        return channel_events.GuildChannelCreateEvent(channel=mock.Mock(), shard=None)

    def test_app_property(self, event):
        assert event.app is event.channel.app

    def test_channel_id_property(self, event):
        event.channel.id = 123
        assert event.channel_id == 123

    def test_guild_id_property(self, event):
        event.channel.guild_id = 123
        assert event.guild_id == 123


class TestGuildChannelUpdateEvent:
    @pytest.fixture
    def event(self):
        return channel_events.GuildChannelUpdateEvent(channel=mock.Mock(), old_channel=mock.Mock(), shard=None)

    def test_app_property(self, event):
        assert event.app is event.channel.app

    def test_channel_id_property(self, event):
        event.channel.id = 123
        assert event.channel_id == 123

    def test_guild_id_property(self, event):
        event.channel.guild_id = 123
        assert event.guild_id == 123

    def test_old_channel_id_property(self, event):
        event.old_channel.id = 123
        assert event.old_channel.id == 123


class TestGuildChannelDeleteEvent:
    @pytest.fixture
    def event(self):
        return channel_events.GuildChannelDeleteEvent(channel=mock.Mock(), shard=None)

    def test_app_property(self, event):
        assert event.app is event.channel.app

    def test_channel_id_property(self, event):
        event.channel.id = 123
        assert event.channel_id == 123

    def test_guild_id_property(self, event):
        event.channel.guild_id = 123
        assert event.guild_id == 123


class TestGuildPinsUpdateEvent:
    @pytest.fixture
    def event(self):
        return channel_events.GuildPinsUpdateEvent(
            app=mock.Mock(), shard=None, channel_id=12343, guild_id=None, last_pin_timestamp=None
        )

    @pytest.mark.parametrize("result", [mock.Mock(spec=channels.GuildTextChannel), None])
    def test_get_channel(self, event, result):
        event.app.cache.get_guild_channel.return_value = result

        result = event.get_channel()

        assert result is event.app.cache.get_guild_channel.return_value
        event.app.cache.get_guild_channel.assert_called_once_with(event.channel_id)


@pytest.mark.asyncio
class TestInviteEvent:
    @pytest.fixture
    def event(self):
        return hikari_test_helpers.mock_class_namespace(
            channel_events.InviteEvent, slots_=False, code=mock.PropertyMock(return_value="Jx4cNGG")
        )()

    async def test_fetch_invite(self, event):
        event.app.rest.fetch_invite = mock.AsyncMock()

        await event.fetch_invite()

        event.app.rest.fetch_invite.assert_awaited_once_with("Jx4cNGG")


class TestInviteCreateEvent:
    @pytest.fixture
    def event(self):
        return channel_events.InviteCreateEvent(shard=None, invite=mock.Mock())

    def test_app_property(self, event):
        assert event.app is event.invite.app

    @pytest.mark.asyncio
    async def test_channel_id_property(self, event):
        event.invite.channel_id = 123
        assert event.channel_id == 123

    @pytest.mark.asyncio
    async def test_guild_id_property(self, event):
        event.invite.guild_id = 123
        assert event.guild_id == 123

    @pytest.mark.asyncio
    async def test_code_property(self, event):
        event.invite.code = "Jx4cNGG"
        assert event.code == "Jx4cNGG"


@pytest.mark.asyncio
class TestWebhookUpdateEvent:
    @pytest.fixture
    def event(self):
        return channel_events.WebhookUpdateEvent(app=mock.AsyncMock(), shard=mock.Mock(), channel_id=123, guild_id=456)

    async def test_fetch_channel_webhooks(self, event):
        await event.fetch_channel_webhooks()

        event.app.rest.fetch_channel_webhooks.assert_awaited_once_with(123)

    async def test_fetch_guild_webhooks(self, event):
        await event.fetch_guild_webhooks()

        event.app.rest.fetch_guild_webhooks.assert_awaited_once_with(456)


class TestGuildThreadEvent:
    @pytest.mark.asyncio
    async def test_fetch_channel(self):
        mock_app = mock.AsyncMock()
        mock_app.rest.fetch_channel.return_value = mock.Mock(channels.GuildThreadChannel)
        event = hikari_test_helpers.mock_class_namespace(
            channel_events.GuildThreadEvent, app=mock_app, thread_id=123321
        )()

        result = await event.fetch_channel()

        assert result is mock_app.rest.fetch_channel.return_value
        mock_app.rest.fetch_channel.assert_awaited_once_with(123321)


class TestGuildThreadAccessEvent:
    @pytest.fixture
    def event(self) -> channel_events.GuildThreadAccessEvent:
        return channel_events.GuildThreadAccessEvent(shard=mock.Mock(), thread=mock.Mock())

    def test_app_property(self, event: channel_events.GuildThreadAccessEvent):
        assert event.app is event.thread.app

    def test_guild_id(self, event: channel_events.GuildThreadAccessEvent):
        assert event.guild_id is event.thread.guild_id

    def test_thread_id_property(self, event: channel_events.GuildThreadAccessEvent):
        assert event.thread_id is event.thread.id


class TestGuildThreadCreateEvent:
    @pytest.fixture
    def event(self) -> channel_events.GuildThreadCreateEvent:
        return channel_events.GuildThreadCreateEvent(shard=mock.Mock(), thread=mock.Mock())

    def test_app_property(self, event: channel_events.GuildThreadCreateEvent):
        assert event.app is event.thread.app

    def test_guild_id(self, event: channel_events.GuildThreadCreateEvent):
        assert event.guild_id is event.thread.guild_id

    def test_thread_id_property(self, event: channel_events.GuildThreadCreateEvent):
        assert event.thread_id is event.thread.id


class TestGuildThreadUpdateEvent:
    @pytest.fixture
    def event(self) -> channel_events.GuildThreadUpdateEvent:
        return channel_events.GuildThreadUpdateEvent(shard=mock.Mock(), thread=mock.Mock())

    def test_app_property(self, event: channel_events.GuildThreadUpdateEvent):
        assert event.app is event.thread.app

    def test_guild_id(self, event: channel_events.GuildThreadUpdateEvent):
        assert event.guild_id is event.thread.guild_id

    def test_thread_id_property(self, event: channel_events.GuildThreadUpdateEvent):
        assert event.thread_id is event.thread.id
