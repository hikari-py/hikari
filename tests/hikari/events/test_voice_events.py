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

from hikari.events import voice_events
from hikari.models import voices


class TestVoiceStateUpdateEvent:
    @pytest.fixture
    def event(self):
        return voice_events.VoiceStateUpdateEvent(shard=object(), state=mock.Mock(voices.VoiceState))

    def test_guild_id_property(self, event):
        event.state.guild_id = 123
        assert event.guild_id == 123


class TestVoiceServerUpdateEvent:
    @pytest.fixture
    def event(self):
        return voice_events.VoiceServerUpdateEvent(
            shard=object(), guild_id=123, token="token", raw_endpoint="voice.discord.com:123"
        )

    def test_endpoint_property(self, event):
        assert event.endpoint == "wss://voice.discord.com:443"
