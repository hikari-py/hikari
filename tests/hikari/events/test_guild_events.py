# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019-2020
#
# This file is part of Hikari.
#
# Hikari is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hikari is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Hikari. If not, see <https://www.gnu.org/licenses/>.

import mock
import pytest

from hikari.events import guild_events
from hikari.models import guilds
from hikari.models import presences


class TestGuildAvailableEvent:
    @pytest.fixture
    def event(self):
        return guild_events.GuildAvailableEvent(
            shard=object(),
            guild=mock.Mock(guilds.Guild),
            emojis={},
            roles={},
            channels={},
            members={},
            presences={},
            voice_states={},
        )

    def test_guild_id_property(self, event):
        event.guild.id = 123
        assert event.guild_id == 123


class TestGuildUpdateEvent:
    @pytest.fixture
    def event(self):
        return guild_events.GuildUpdateEvent(shard=object(), guild=mock.Mock(guilds.Guild), emojis={}, roles={})

    def test_guild_id_property(self, event):
        event.guild.id = 123
        assert event.guild_id == 123


class TestPresenceUpdateEvent:
    @pytest.fixture
    def event(self):
        return guild_events.PresenceUpdateEvent(
            shard=object(), presence=mock.Mock(presences.MemberPresence), user=mock.Mock()
        )

    def test_user_id_property(self, event):
        event.presence.user_id = 123
        assert event.user_id == 123

    def test_guild_id_property(self, event):
        event.presence.guild_id = 123
        assert event.guild_id == 123
