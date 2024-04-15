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

from hikari import guilds
from hikari import presences
from hikari import snowflakes
from hikari.events import guild_events
from tests.hikari import hikari_test_helpers


class TestGuildEvent:
    @pytest.fixture
    def event(self):
        cls = hikari_test_helpers.mock_class_namespace(
            guild_events.GuildEvent, guild_id=mock.PropertyMock(return_value=snowflakes.Snowflake(534123123))
        )
        return cls()

    def test_get_guild_when_available(self, event):
        result = event.get_guild()

        assert result is event.app.cache.get_available_guild.return_value
        event.app.cache.get_available_guild.assert_called_once_with(534123123)
        event.app.cache.get_unavailable_guild.assert_not_called()

    def test_get_guild_when_unavailable(self, event):
        event.app.cache.get_available_guild.return_value = None
        result = event.get_guild()

        assert result is event.app.cache.get_unavailable_guild.return_value
        event.app.cache.get_unavailable_guild.assert_called_once_with(534123123)
        event.app.cache.get_available_guild.assert_called_once_with(534123123)

    def test_get_guild_cacheless(self, event):
        event = hikari_test_helpers.mock_class_namespace(guild_events.GuildEvent, app=object())()

        assert event.get_guild() is None

    @pytest.mark.asyncio
    async def test_fetch_guild(self, event):
        event.app.rest.fetch_guild = mock.AsyncMock()
        result = await event.fetch_guild()

        assert result is event.app.rest.fetch_guild.return_value
        event.app.rest.fetch_guild.assert_called_once_with(534123123)

    @pytest.mark.asyncio
    async def test_fetch_guild_preview(self, event):
        event.app.rest.fetch_guild_preview = mock.AsyncMock()
        result = await event.fetch_guild_preview()

        assert result is event.app.rest.fetch_guild_preview.return_value
        event.app.rest.fetch_guild_preview.assert_called_once_with(534123123)


class TestGuildAvailableEvent:
    @pytest.fixture
    def event(self):
        return guild_events.GuildAvailableEvent(
            shard=object(),
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

    def test_app_property(self, event):
        assert event.app is event.guild.app

    def test_guild_id_property(self, event):
        event.guild.id = 123
        assert event.guild_id == 123


class TestGuildUpdateEvent:
    @pytest.fixture
    def event(self):
        return guild_events.GuildUpdateEvent(
            shard=object(),
            guild=mock.Mock(guilds.Guild),
            old_guild=mock.Mock(guilds.Guild),
            emojis={},
            stickers={},
            roles={},
        )

    def test_app_property(self, event):
        assert event.app is event.guild.app

    def test_guild_id_property(self, event):
        event.guild.id = 123
        assert event.guild_id == 123

    def test_old_guild_id_property(self, event):
        event.old_guild.id = 123
        assert event.old_guild.id == 123


class TestBanEvent:
    @pytest.fixture
    def event(self):
        return hikari_test_helpers.mock_class_namespace(guild_events.BanEvent)()

    def test_app_property(self, event):
        assert event.app is event.user.app


class TestPresenceUpdateEvent:
    @pytest.fixture
    def event(self):
        return guild_events.PresenceUpdateEvent(
            shard=object(),
            presence=mock.Mock(presences.MemberPresence),
            old_presence=mock.Mock(presences.MemberPresence),
            user=mock.Mock(),
        )

    def test_app_property(self, event):
        assert event.app is event.presence.app

    def test_user_id_property(self, event):
        event.presence.user_id = 123
        assert event.user_id == 123

    def test_guild_id_property(self, event):
        event.presence.guild_id = 123
        assert event.guild_id == 123

    def test_old_presence(self, event):
        event.old_presence.id = 123
        event.old_presence.guild_id = 456

        assert event.old_presence.id == 123
        assert event.old_presence.guild_id == 456


class TestGuildStickersUpdateEvent:
    @pytest.fixture
    def event(self):
        return guild_events.StickersUpdateEvent(
            app=mock.Mock(),
            shard=mock.Mock(),
            guild_id=snowflakes.Snowflake(690),
            old_stickers=(mock.Mock(), mock.Mock()),
            stickers=(mock.Mock(), mock.Mock(), mock.Mock()),
        )

    @pytest.mark.asyncio
    async def test_fetch_stickers(self, event):
        event.app.rest.fetch_guild_stickers = mock.AsyncMock()

        assert await event.fetch_stickers() is event.app.rest.fetch_guild_stickers.return_value

        event.app.rest.fetch_guild_stickers.assert_awaited_once_with(event.guild_id)


class TestAuditLogEntryCreateEvent:
    @pytest.fixture
    def event(self):
        return guild_events.AuditLogEntryCreateEvent(shard=mock.Mock(), entry=mock.Mock())

    def test_app_property(self, event):
        assert event.app is event.entry.app

    def test_guild_id_property(self, event):
        assert event.guild_id is event.entry.guild_id
