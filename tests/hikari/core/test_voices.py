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
# along ith Hikari. If not, see <https://www.gnu.org/licenses/>.
import pytest

from hikari.core import voices


@pytest.fixture()
def voice_state_payload():
    return {
        "guild_id": "929292929292992",
        "channel_id": "157733188964188161",
        "user_id": "80351110224678912",
        "session_id": "90326bd25d71d39b9ef95b299e3872ff",
        "deaf": True,
        "mute": True,
        "self_deaf": False,
        "self_mute": True,
        "suppress": False,
    }


@pytest.fixture()
def voice_region_payload():
    return {"id": "london", "name": "LONDON", "vip": True, "optimal": False, "deprecated": True, "custom": False}


class TestVoiceState:
    def test_deserialize(self, voice_state_payload):
        voice_state_obj = voices.VoiceState.deserialize(voice_state_payload)
        assert voice_state_obj.guild_id == 929292929292992
        assert voice_state_obj.channel_id == 157733188964188161
        assert voice_state_obj.user_id == 80351110224678912
        assert voice_state_obj.session_id == "90326bd25d71d39b9ef95b299e3872ff"
        assert voice_state_obj.is_guild_deafened is True
        assert voice_state_obj.is_guild_muted is True
        assert voice_state_obj.is_self_deafened is False
        assert voice_state_obj.is_self_muted is True
        assert voice_state_obj.is_suppressed is False


class TestVoiceRegion:
    def test_deserialize(self, voice_region_payload):
        voice_region_obj = voices.VoiceRegion.deserialize(voice_region_payload)
        assert voice_region_obj.id == "london"
        assert voice_region_obj.name == "LONDON"
        assert voice_region_obj.is_vip is True
        assert voice_region_obj.is_optimal_location is False
        assert voice_region_obj.is_deprecated is True
        assert voice_region_obj.is_custom is False
