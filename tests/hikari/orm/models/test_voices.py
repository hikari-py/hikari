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
import cymock as mock
import pytest

from hikari.orm import fabric
from hikari.orm.models import guilds
from hikari.orm.models import voices
from hikari.orm.state import base_registry
from tests.hikari import _helpers


@pytest.fixture
def mock_fabric():
    mock_state = _helpers.create_autospec(base_registry.BaseRegistry)
    return fabric.Fabric(state_registry=mock_state)


@pytest.fixture
def mock_guild():
    return mock.MagicMock(guilds.Guild, id=381870553235193857)


@pytest.mark.model()
def test_VoiceServer(mock_fabric):
    voice_server_obj = voices.VoiceServer(
        mock_fabric, {"token": "awoooooooo", "guild_id": "41771983423143937", "endpoint": "smart.loyal.discord.gg"}
    )
    assert voice_server_obj.token == "awoooooooo"
    assert voice_server_obj.guild_id == 41771983423143937
    assert voice_server_obj.endpoint == "smart.loyal.discord.gg"


@pytest.mark.model
def test_VoiceServer___repr__():
    assert repr(
        _helpers.mock_model(voices.VoiceServer, guild_id=42, endpoint="foo", __repr__=voices.VoiceServer.__repr__)
    )


@pytest.fixture
def mock_member():
    return {
        "user": {
            "id": "123454234",
            "username": "RobinWilliams",
            "discriminator": "3243",
            "avatar": "9c9f4d5f5ee703bc900e7e6c4bbfe44f",
        },
        "joined_at": "2019-03-31T12:10:19.616000",
        "deaf": False,
        "mute": True,
    }


@pytest.mark.model()
@pytest.mark.parametrize("has_member", [True, False])
def test_VoiceState(mock_member, mock_fabric, mock_guild, has_member):
    voice_state_obj = voices.VoiceState(
        mock_fabric,
        mock_guild,
        {
            "guild_id": "381870553235193857",
            "user_id": "115590097100865541",
            "channel_id": "115590097143215541",
            "member": mock_member if has_member else None,
            "session_id": "350a109226bd6f43c81f12c7c08de20a",
            "deaf": False,
            "mute": True,
            "self_deaf": True,
            "self_mute": False,
            "self_stream": True,
            "suppress": False,
        },
    )
    assert voice_state_obj.guild_id == 381870553235193857
    assert voice_state_obj.user_id == 115590097100865541
    assert voice_state_obj.channel_id == 115590097143215541
    assert voice_state_obj.is_deaf is False
    assert voice_state_obj.is_mute is True
    assert voice_state_obj.is_self_deaf is True
    assert voice_state_obj.is_self_mute is False
    assert voice_state_obj.is_self_stream is True
    assert voice_state_obj.is_suppressed is False
    if has_member:
        assert voice_state_obj.member is not None
        mock_fabric.state_registry.parse_member.assert_called_once_with(mock_member, mock_guild)
    else:
        assert voice_state_obj.member is None
        mock_fabric.state_registry.parse_member.assert_not_called()


@pytest.mark.model
def test_VoiceState_update(mock_member, mock_guild, mock_fabric):
    voice_state_obj = voices.VoiceState(
        mock_fabric,
        mock_guild,
        {
            "guild_id": "381870553235193857",
            "user_id": "115590097100865541",
            "channel_id": "115590097143215541",
            "session_id": "350a109226bd6f43c81f12c7c08de20a",
        },
    )
    voice_state_obj.update_state(
        {
            "channel_id": "537340989808050216",
            "deaf": True,
            "mute": True,
            "self_deaf": True,
            "self_mute": True,
            "self_stream": True,
            "suppress": True,
        }
    )
    assert voice_state_obj.channel_id == 537340989808050216
    assert voice_state_obj.is_deaf is True
    assert voice_state_obj.is_mute is True
    assert voice_state_obj.is_self_deaf is True
    assert voice_state_obj.is_self_mute is True
    assert voice_state_obj.is_self_stream is True
    assert voice_state_obj.is_suppressed is True


@pytest.mark.model
def test_VoiceState___repr__():
    assert repr(
        _helpers.mock_model(
            voices.VoiceState,
            user_id=42,
            channel_id=69,
            guild_id=101,
            session_id=666,
            __repr__=voices.VoiceState.__repr__,
        )
    )


@pytest.mark.model
def test_VoiceRegion():
    voice_region_obj = voices.VoiceRegion(
        {"id": "us-west", "name": "US West", "vip": False, "optimal": False, "deprecated": False, "custom": False}
    )
    assert voice_region_obj.id == "us-west"
    assert voice_region_obj.name == "US West"
    assert voice_region_obj.is_vip is False
    assert voice_region_obj.is_optimal is False
    assert voice_region_obj.is_deprecated is False
    assert voice_region_obj.is_custom is False


@pytest.mark.model
def test_VoiceRegion___repr__():
    assert repr(
        _helpers.mock_model(
            voices.VoiceRegion, name="foo", is_vip=True, is_deprecated=False, __repr__=voices.VoiceRegion.__repr__
        )
    )
