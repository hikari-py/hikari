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

from hikari.events import reaction_events
from hikari.models import guilds


class TestGuildReactionAddEvent:
    @pytest.fixture
    def event(self):
        return reaction_events.GuildReactionAddEvent(
            shard=object(), member=mock.MagicMock(guilds.Member), channel_id=123, message_id=456, emoji="👌"
        )

    def test_guild_id_property(self, event):
        event.member.guild_id = 123
        assert event.guild_id == 123

    def test_user_id_property(self, event):
        event.member.user.id = 123
        assert event.user_id == 123
