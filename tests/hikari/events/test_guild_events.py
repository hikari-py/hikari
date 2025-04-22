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

import mock
import pytest

from hikari import guilds
from hikari import presences
from hikari import snowflakes
from hikari import traits
from hikari import users
from hikari.api import shard as shard_api
from hikari.events import guild_events


class TestGuildEvent:
    class MockGuildEvent(guild_events.GuildEvent):
        def __init__(self, app: traits.RESTAware):
            self._app = app
            self._shard = mock.Mock()
            self._guild_id = snowflakes.Snowflake(123)

        @property
        def app(self) -> traits.RESTAware:
            return self._app

        @property
        def shard(self) -> shard_api.GatewayShard:
            return self._shard

        @property
        def guild_id(self) -> snowflakes.Snowflake:
            return self._guild_id

    @pytest.fixture
    def guild_event(self, hikari_app: traits.RESTAware) -> guild_events.GuildEvent:
        return TestGuildEvent.MockGuildEvent(hikari_app)

    def test_get_guild_when_available(self, guild_event: guild_events.GuildEvent):
        with (
            mock.patch.object(guild_event, "_app", mock.Mock(traits.CacheAware)) as patched_app,
            mock.patch.object(patched_app, "cache") as patched_cache,
            mock.patch.object(patched_cache, "get_available_guild") as patched_get_available_guild,
            mock.patch.object(patched_cache, "get_unavailable_guild") as patched_get_unavailable_guild,
        ):
            result = guild_event.get_guild()

            assert result is patched_get_available_guild.return_value
            patched_get_available_guild.assert_called_once_with(123)
            patched_get_unavailable_guild.assert_not_called()

    def test_get_guild_when_unavailable(self, guild_event: guild_events.GuildEvent):
        with (
            mock.patch.object(guild_event, "_app", mock.Mock(traits.CacheAware)) as patched_app,
            mock.patch.object(patched_app, "cache") as patched_cache,
            mock.patch.object(patched_cache, "get_available_guild", return_value=None) as patched_get_available_guild,
            mock.patch.object(patched_cache, "get_unavailable_guild") as patched_get_unavailable_guild,
        ):
            result = guild_event.get_guild()

            assert result is patched_get_unavailable_guild.return_value
            patched_get_unavailable_guild.assert_called_once_with(123)
            patched_get_available_guild.assert_called_once_with(123)

    def test_get_guild_cacheless(self, guild_event: guild_events.GuildEvent):
        with mock.patch.object(guild_event, "_app", None):
            assert guild_event.get_guild() is None

    @pytest.mark.asyncio
    async def test_fetch_guild(self, guild_event: guild_events.GuildEvent):
        with mock.patch.object(guild_event.app.rest, "fetch_guild", mock.AsyncMock()) as patched_fetch_guild:
            result = await guild_event.fetch_guild()

            assert result is patched_fetch_guild.return_value
            patched_fetch_guild.assert_called_once_with(123)

    @pytest.mark.asyncio
    async def test_fetch_guild_preview(self, guild_event: guild_events.GuildEvent):
        with mock.patch.object(
            guild_event.app.rest, "fetch_guild_preview", mock.AsyncMock()
        ) as patched_fetch_guild_preview:
            result = await guild_event.fetch_guild_preview()

            assert result is patched_fetch_guild_preview.return_value
            patched_fetch_guild_preview.assert_called_once_with(123)


class TestGuildAvailableEvent:
    @pytest.fixture
    def event(self) -> guild_events.GuildAvailableEvent:
        return guild_events.GuildAvailableEvent(
            shard=mock.Mock(),
            guild=mock.Mock(guilds.Guild),
            emojis={},
            stickers={},
            roles={},
            channels={},
            members={},
            presences={},
            voice_states={},
            threads={},
        )

    def test_app_property(self, event: guild_events.GuildAvailableEvent):
        assert event.app is event.guild.app

    def test_guild_id_property(self, event: guild_events.GuildAvailableEvent):
        event.guild.id = snowflakes.Snowflake(123)
        assert event.guild_id == 123


class TestGuildUpdateEvent:
    @pytest.fixture
    def event(self) -> guild_events.GuildUpdateEvent:
        return guild_events.GuildUpdateEvent(
            shard=mock.Mock(),
            guild=mock.Mock(guilds.Guild),
            old_guild=mock.Mock(guilds.Guild),
            emojis={},
            stickers={},
            roles={},
        )

    def test_app_property(self, event: guild_events.GuildUpdateEvent):
        assert event.app is event.guild.app

    def test_guild_id_property(self, event: guild_events.GuildUpdateEvent):
        event.guild.id = snowflakes.Snowflake(123)
        assert event.guild_id == 123

    def test_old_guild_id_property(self, event: guild_events.GuildUpdateEvent):
        with mock.patch.object(event.old_guild, "id", snowflakes.Snowflake(123)):
            assert event.old_guild is not None
            assert event.old_guild.id == 123


class TestBanEvent:
    class MockBanEvent(guild_events.BanEvent):
        def __init__(self, app: traits.RESTAware):
            self._app = app
            self._shard = mock.Mock()
            self._guild_id = snowflakes.Snowflake(123)
            self._user = mock.Mock(app=app, id=snowflakes.Snowflake(456))

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
        def user(self) -> users.User:
            return self._user

    @pytest.fixture
    def ban_event(self, hikari_app: traits.RESTAware) -> guild_events.BanEvent:
        return TestBanEvent.MockBanEvent(hikari_app)

    def test_app_property(self, ban_event: guild_events.BanEvent):
        assert ban_event.app is ban_event.user.app


class TestPresenceUpdateEvent:
    @pytest.fixture
    def event(self) -> guild_events.PresenceUpdateEvent:
        return guild_events.PresenceUpdateEvent(
            shard=mock.Mock(),
            presence=mock.Mock(presences.MemberPresence),
            old_presence=mock.Mock(presences.MemberPresence),
            user=mock.Mock(),
        )

    def test_app_property(self, event: guild_events.PresenceUpdateEvent):
        assert event.app is event.presence.app

    def test_user_id_property(self, event: guild_events.PresenceUpdateEvent):
        event.presence.user_id = snowflakes.Snowflake(123)
        assert event.user_id == 123

    def test_guild_id_property(self, event: guild_events.PresenceUpdateEvent):
        event.presence.guild_id = snowflakes.Snowflake(123)
        assert event.guild_id == 123

    def test_old_presence(self, event: guild_events.PresenceUpdateEvent):
        with mock.patch.object(event.old_presence, "guild_id", 456):
            assert event.old_presence is not None
            assert event.old_presence.guild_id == 456


class TestGuildStickersUpdateEvent:
    @pytest.fixture
    def event(self) -> guild_events.StickersUpdateEvent:
        return guild_events.StickersUpdateEvent(
            app=mock.Mock(),
            shard=mock.Mock(),
            guild_id=snowflakes.Snowflake(690),
            old_stickers=(mock.Mock(), mock.Mock()),
            stickers=(mock.Mock(), mock.Mock(), mock.Mock()),
        )

    @pytest.mark.asyncio
    async def test_fetch_stickers(self, event: guild_events.StickersUpdateEvent):
        event.app.rest.fetch_guild_stickers = mock.AsyncMock()

        assert await event.fetch_stickers() is event.app.rest.fetch_guild_stickers.return_value

        event.app.rest.fetch_guild_stickers.assert_awaited_once_with(event.guild_id)


class TestAuditLogEntryCreateEvent:
    @pytest.fixture
    def event(self) -> guild_events.AuditLogEntryCreateEvent:
        return guild_events.AuditLogEntryCreateEvent(shard=mock.Mock(), entry=mock.Mock())

    def test_app_property(self, event: guild_events.AuditLogEntryCreateEvent):
        assert event.app is event.entry.app

    def test_guild_id_property(self, event: guild_events.AuditLogEntryCreateEvent):
        assert event.guild_id is event.entry.guild_id
