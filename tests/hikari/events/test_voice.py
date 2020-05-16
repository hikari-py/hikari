#!/usr/bin/env python3
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
import pytest

from hikari.events import voice


class TestVoiceServerUpdateEvent:
    @pytest.fixture()
    def test_voice_server_update_payload(self):
        return {"token": "a_token", "guild_id": "303030300303", "endpoint": "smart.loyal.discord.gg"}

    def test_deserialize(self, test_voice_server_update_payload):
        voice_server_update_obj = voice.VoiceServerUpdateEvent.deserialize(test_voice_server_update_payload)
        assert voice_server_update_obj.token == "a_token"
        assert voice_server_update_obj.guild_id == 303030300303
        assert voice_server_update_obj.endpoint == "smart.loyal.discord.gg"
