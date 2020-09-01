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

import mock
import pytest

from hikari import guilds
from hikari import presences
from hikari.events import guild_events


class TestGuildAvailableEvent:
    @pytest.fixture()
    def event(self):
        return guild_events.GuildAvailableEvent(
            app=None,
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
    @pytest.fixture()
    def event(self):
        return guild_events.GuildUpdateEvent(
            app=None, shard=object(), guild=mock.Mock(guilds.Guild), emojis={}, roles={}
        )

    def test_guild_id_property(self, event):
        event.guild.id = 123
        assert event.guild_id == 123


class TestPresenceUpdateEvent:
    @pytest.fixture()
    def event(self):
        return guild_events.PresenceUpdateEvent(
            app=None, shard=object(), presence=mock.Mock(presences.MemberPresence), user=mock.Mock()
        )

    def test_user_id_property(self, event):
        event.presence.user_id = 123
        assert event.user_id == 123

    def test_guild_id_property(self, event):
        event.presence.guild_id = 123
        assert event.guild_id == 123
