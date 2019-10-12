#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019
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
from unittest import mock

import pytest

from hikari.core.components import state_registry
from hikari.core.model import guild as _guild
from hikari.core.model import permission
from hikari.core.model import role


@pytest.fixture
def state():
    return mock.MagicMock(spec_set=state_registry.StateRegistry)


@pytest.fixture
def payload():
    return {
        "id": "41771983423143936",
        "name": "WE DEM BOYZZ!!!!!!",
        "color": 3447003,
        "hoist": True,
        "position": 1,
        "permissions": 66321471,
        "managed": False,
        "mentionable": False,
    }


@pytest.mark.model
def test_Role(state, payload):
    r = role.Role(state, payload, 1234)

    assert r.id == 41771983423143936
    assert r.name == "WE DEM BOYZZ!!!!!!"
    assert r.color == 0x3498DB
    assert r.hoist is True
    assert r.position == 1
    assert r._guild_id == 1234
    assert r.permissions == (
        permission.Permission.USE_VAD
        | permission.Permission.MOVE_MEMBERS
        | permission.Permission.DEAFEN_MEMBERS
        | permission.Permission.MUTE_MEMBERS
        | permission.Permission.SPEAK
        | permission.Permission.CONNECT
        | permission.Permission.MENTION_EVERYONE
        | permission.Permission.READ_MESSAGE_HISTORY
        | permission.Permission.ATTACH_FILES
        | permission.Permission.EMBED_LINKS
        | permission.Permission.MANAGE_MESSAGES
        | permission.Permission.SEND_TTS_MESSAGES
        | permission.Permission.SEND_MESSAGES
        | permission.Permission.VIEW_CHANNEL
        | permission.Permission.MANAGE_GUILD
        | permission.Permission.MANAGE_CHANNELS
        | permission.Permission.ADMINISTRATOR
        | permission.Permission.BAN_MEMBERS
        | permission.Permission.KICK_MEMBERS
        | permission.Permission.CREATE_INSTANT_INVITE
    )
    assert r.managed is False
    assert r.mentionable is False


@pytest.mark.model
def test_Role_guild(state, payload):
    r = role.Role(state, payload, 1234)
    guild = mock.MagicMock(spec_set=_guild.Guild)
    state.get_guild_by_id = mock.MagicMock(return_value=guild)
    assert r.guild is guild
    state.get_guild_by_id.assert_called_with(1234)
