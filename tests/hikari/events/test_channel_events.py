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
from hikari import snowflakes
from hikari import traits
from hikari.api import shard as shard_api
from hikari.events import channel_events


class TestGuildChannelEvent:
    class MockGuildChannelEvent(channel_events.GuildChannelEvent):
        def __init__(self, app: traits.RESTAware):
            self._app = app
            self._shard = mock.Mock()
            self._channel_id = snowflakes.Snowflake(123)
            self._guild_id = snowflakes.Snowflake(456)

        @property
        def app(self) -> traits.RESTAware:
            return self._app

        @property
        def shard(self) -> shard_api.GatewayShard:
            return self._shard

        @property
        def channel_id(self) -> snowflakes.Snowflake:
            return self._channel_id

        @property
        def guild_id(self) -> snowflakes.Snowflake:
            return self._guild_id

    @pytest.fixture
    def guild_channel_event(self, hikari_app: traits.RESTAware) -> channel_events.GuildChannelEvent:
        return TestGuildChannelEvent.MockGuildChannelEvent(hikari_app)

    def test_get_guild_when_available(self, guild_channel_event: channel_events.GuildChannelEvent):
        with (
            mock.patch.object(guild_channel_event, "_app") as patched_app,
            mock.patch.object(patched_app, "cache") as patched_cache,
            mock.patch.object(patched_cache, "get_available_guild") as patched_get_available_guild,
            mock.patch.object(patched_cache, "get_unavailable_guild") as patched_get_unavailable_guild,
        ):
            result = guild_channel_event.get_guild()

            assert result is patched_get_available_guild.return_value
            patched_get_available_guild.assert_called_once_with(456)
            patched_get_unavailable_guild.assert_not_called()

    def test_get_guild_when_unavailable(self, guild_channel_event: channel_events.GuildChannelEvent):
        with (
            mock.patch.object(guild_channel_event, "_app") as patched_app,
            mock.patch.object(patched_app, "cache") as patched_cache,
            mock.patch.object(patched_cache, "get_available_guild", return_value=None) as patched_get_available_guild,
            mock.patch.object(patched_cache, "get_unavailable_guild") as patched_get_unavailable_guild,
        ):
            result = guild_channel_event.get_guild()

            assert result is patched_get_unavailable_guild.return_value
            patched_get_available_guild.assert_called_once_with(456)
            patched_get_unavailable_guild.assert_called_once_with(456)

    def test_get_guild_without_cache(self, guild_channel_event: channel_events.GuildChannelEvent):
        with mock.patch.object(guild_channel_event, "_app", None):
            assert guild_channel_event.get_guild() is None

    @pytest.mark.asyncio
    async def test_fetch_guild(self, guild_channel_event: channel_events.GuildChannelEvent):
        with mock.patch.object(
            guild_channel_event.app.rest, "fetch_guild", new_callable=mock.AsyncMock
        ) as patched_fetch_guild:
            result = await guild_channel_event.fetch_guild()

            assert result is patched_fetch_guild.return_value
            patched_fetch_guild.assert_awaited_once_with(456)

    def test_get_channel(self, guild_channel_event: channel_events.GuildChannelEvent):
        with (
            mock.patch.object(guild_channel_event, "_app") as patched_app,
            mock.patch.object(patched_app, "cache") as patched_cache,
            mock.patch.object(patched_cache, "get_guild_channel") as patched_get_guild_channel,
        ):
            result = guild_channel_event.get_channel()

            assert result is patched_get_guild_channel.return_value
            patched_get_guild_channel.assert_called_once_with(123)

    def test_get_channel_without_cache(self, guild_channel_event: channel_events.GuildChannelEvent):
        with mock.patch.object(guild_channel_event, "_app", None):
            assert guild_channel_event.get_channel() is None

    @pytest.mark.asyncio
    async def test_fetch_channel(self, guild_channel_event: channel_events.GuildChannelEvent):
        with mock.patch.object(
            guild_channel_event.app.rest,
            "fetch_channel",
            mock.AsyncMock(return_value=mock.MagicMock(spec=channels.GuildChannel)),
        ) as patched_fetch_channel:
            result = await guild_channel_event.fetch_channel()

            assert result is patched_fetch_channel.return_value
            patched_fetch_channel.assert_awaited_once_with(123)


class TestGuildChannelCreateEvent:
    @pytest.fixture
    def event(self) -> channel_events.GuildChannelCreateEvent:
        return channel_events.GuildChannelCreateEvent(channel=mock.Mock(), shard=mock.Mock())

    def test_app_property(self, event: channel_events.GuildChannelCreateEvent):
        assert event.app is event.channel.app

    def test_channel_id_property(self, event: channel_events.GuildChannelCreateEvent):
        event.channel.id = snowflakes.Snowflake(123)
        assert event.channel_id == 123

    def test_guild_id_property(self, event: channel_events.GuildChannelCreateEvent):
        event.channel.guild_id = snowflakes.Snowflake(123)
        assert event.guild_id == 123


class TestGuildChannelUpdateEvent:
    @pytest.fixture
    def event(self) -> channel_events.GuildChannelUpdateEvent:
        return channel_events.GuildChannelUpdateEvent(channel=mock.Mock(), old_channel=mock.Mock(), shard=mock.Mock())

    def test_app_property(self, event: channel_events.GuildChannelUpdateEvent):
        assert event.app is event.channel.app

    def test_channel_id_property(self, event: channel_events.GuildChannelUpdateEvent):
        event.channel.id = snowflakes.Snowflake(123)
        assert event.channel_id == 123

    def test_guild_id_property(self, event: channel_events.GuildChannelUpdateEvent):
        event.channel.guild_id = snowflakes.Snowflake(123)
        assert event.guild_id == 123

    def test_old_channel_id_property(self, event: channel_events.GuildChannelUpdateEvent):
        assert event.old_channel
        event.old_channel.id = snowflakes.Snowflake(123)
        assert event.old_channel.id == 123


class TestGuildChannelDeleteEvent:
    @pytest.fixture
    def event(self) -> channel_events.GuildChannelDeleteEvent:
        return channel_events.GuildChannelDeleteEvent(channel=mock.Mock(), shard=mock.Mock())

    def test_app_property(self, event: channel_events.GuildChannelDeleteEvent):
        assert event.app is event.channel.app

    def test_channel_id_property(self, event: channel_events.GuildChannelDeleteEvent):
        event.channel.id = snowflakes.Snowflake(123)
        assert event.channel_id == 123

    def test_guild_id_property(self, event: channel_events.GuildChannelDeleteEvent):
        event.channel.guild_id = snowflakes.Snowflake(123)
        assert event.guild_id == 123


class TestGuildPinsUpdateEvent:
    @pytest.fixture
    def event(self) -> channel_events.GuildPinsUpdateEvent:
        return channel_events.GuildPinsUpdateEvent(
            app=mock.Mock(),
            shard=mock.Mock(),
            channel_id=snowflakes.Snowflake(12343),
            guild_id=snowflakes.Snowflake(45676),
            last_pin_timestamp=None,
        )

    @pytest.mark.parametrize("result", [mock.Mock(spec=channels.GuildTextChannel), None])
    def test_get_channel(
        self, event: channel_events.GuildPinsUpdateEvent, result: typing.Optional[channels.GuildTextChannel]
    ):
        with (
            mock.patch.object(event, "app") as patched_app,
            mock.patch.object(patched_app, "cache") as patched_cache,
            mock.patch.object(patched_cache, "get_guild_channel", return_value=result) as patched_get_guild_channel,
        ):
            channel = event.get_channel()

            assert channel is patched_get_guild_channel.return_value
            patched_get_guild_channel.assert_called_once_with(event.channel_id)


@pytest.mark.asyncio
class TestInviteEvent:
    class MockInviteEvent(channel_events.InviteEvent):
        def __init__(self, app: traits.RESTAware):
            self._app = app
            self._shard = mock.Mock()
            self._channel_id = snowflakes.Snowflake(123)
            self._guild_id = snowflakes.Snowflake(456)
            self._code = "code"

        @property
        def app(self) -> traits.RESTAware:
            return self._app

        @property
        def shard(self) -> shard_api.GatewayShard:
            return self._shard

        @property
        def channel_id(self) -> snowflakes.Snowflake:
            return self._channel_id

        @property
        def guild_id(self) -> snowflakes.Snowflake:
            return self._guild_id

        @property
        def code(self) -> str:
            return self._code

    @pytest.fixture
    def invite_event(self, hikari_app: traits.RESTAware) -> channel_events.InviteEvent:
        return TestInviteEvent.MockInviteEvent(hikari_app)

    async def test_fetch_invite(self, invite_event: channel_events.InviteEvent):
        invite_event.app.rest.fetch_invite = mock.AsyncMock()

        with mock.patch.object(invite_event.app.rest, "fetch_invite", mock.AsyncMock()) as patched_fetch_invite:
            await invite_event.fetch_invite()

            patched_fetch_invite.assert_awaited_once_with("code")


class TestInviteCreateEvent:
    @pytest.fixture
    def event(self) -> channel_events.InviteCreateEvent:
        return channel_events.InviteCreateEvent(shard=mock.Mock(), invite=mock.Mock())

    def test_app_property(self, event: channel_events.InviteCreateEvent):
        assert event.app is event.invite.app

    @pytest.mark.asyncio
    async def test_channel_id_property(self, event: channel_events.InviteCreateEvent):
        event.invite.channel_id = snowflakes.Snowflake(123)
        assert event.channel_id == 123

    @pytest.mark.asyncio
    async def test_guild_id_property(self, event: channel_events.InviteCreateEvent):
        event.invite.guild_id = snowflakes.Snowflake(123)
        assert event.guild_id == 123

    @pytest.mark.asyncio
    async def test_code_property(self, event: channel_events.InviteCreateEvent):
        event.invite.code = "Jx4cNGG"
        assert event.code == "Jx4cNGG"


@pytest.mark.asyncio
class TestWebhookUpdateEvent:
    @pytest.fixture
    def event(self) -> channel_events.WebhookUpdateEvent:
        return channel_events.WebhookUpdateEvent(
            app=mock.AsyncMock(),
            shard=mock.Mock(),
            channel_id=snowflakes.Snowflake(123),
            guild_id=snowflakes.Snowflake(456),
        )

    async def test_fetch_channel_webhooks(self, event: channel_events.WebhookUpdateEvent):
        with mock.patch.object(event.app.rest, "fetch_channel_webhooks") as patched_fetch_channel_webhooks:
            await event.fetch_channel_webhooks()
            patched_fetch_channel_webhooks.assert_awaited_once_with(123)

    async def test_fetch_guild_webhooks(self, event: channel_events.WebhookUpdateEvent):
        with mock.patch.object(event.app.rest, "fetch_guild_webhooks") as patched_fetch_guild_webhooks:
            await event.fetch_guild_webhooks()
            patched_fetch_guild_webhooks.assert_awaited_once_with(456)


class TestGuildThreadEvent:
    class MockGuildThreadEvent(channel_events.GuildThreadEvent):
        def __init__(self, app: traits.RESTAware):
            self._app = app
            self._shard = mock.Mock()
            self._thread_id = snowflakes.Snowflake(123)
            self._guild_id = snowflakes.Snowflake(456)
            self._code = "code"

        @property
        def app(self) -> traits.RESTAware:
            return self._app

        @property
        def shard(self) -> shard_api.GatewayShard:
            return self._shard

        @property
        def guild_id(self) -> snowflakes.Snowflake:
            return self._guild_id

        @property
        def thread_id(self) -> snowflakes.Snowflake:
            return self._thread_id

    @pytest.mark.asyncio
    async def test_fetch_channel(self, hikari_app: traits.RESTAware):
        with mock.patch.object(
            hikari_app.rest,
            "fetch_channel",
            new_callable=mock.AsyncMock,
            return_value=mock.Mock(channels.GuildThreadChannel),
        ) as patched_fetch_channel:
            event = TestGuildThreadEvent.MockGuildThreadEvent(hikari_app)

            result = await event.fetch_channel()

            assert result is patched_fetch_channel.return_value
            patched_fetch_channel.assert_awaited_once_with(123)


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
        return channel_events.GuildThreadUpdateEvent(shard=mock.Mock(), thread=mock.Mock(), old_thread=mock.Mock())

    def test_app_property(self, event: channel_events.GuildThreadUpdateEvent):
        assert event.app is event.thread.app

    def test_guild_id(self, event: channel_events.GuildThreadUpdateEvent):
        assert event.guild_id is event.thread.guild_id

    def test_thread_id_property(self, event: channel_events.GuildThreadUpdateEvent):
        assert event.thread_id is event.thread.id
