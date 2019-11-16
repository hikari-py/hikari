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

from hikari.orm import state_registry
from hikari.orm.models import guilds as _guild
from hikari.orm.models import permissions
from hikari.orm.models import roles


@pytest.fixture
def state():
    return mock.MagicMock(spec_set=state_registry.IStateRegistry)


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
    r = roles.Role(state, payload, 1234)

    assert r.id == 41771983423143936
    assert r.name == "WE DEM BOYZZ!!!!!!"
    assert r.color == 0x3498DB
    assert r.hoist is True
    assert r.position == 1
    assert r.guild_id == 1234
    assert r.permissions == (
        permissions.Permission.USE_VAD
        | permissions.Permission.MOVE_MEMBERS
        | permissions.Permission.DEAFEN_MEMBERS
        | permissions.Permission.MUTE_MEMBERS
        | permissions.Permission.SPEAK
        | permissions.Permission.CONNECT
        | permissions.Permission.MENTION_EVERYONE
        | permissions.Permission.READ_MESSAGE_HISTORY
        | permissions.Permission.ATTACH_FILES
        | permissions.Permission.EMBED_LINKS
        | permissions.Permission.MANAGE_MESSAGES
        | permissions.Permission.SEND_TTS_MESSAGES
        | permissions.Permission.SEND_MESSAGES
        | permissions.Permission.VIEW_CHANNEL
        | permissions.Permission.MANAGE_GUILD
        | permissions.Permission.MANAGE_CHANNELS
        | permissions.Permission.ADMINISTRATOR
        | permissions.Permission.BAN_MEMBERS
        | permissions.Permission.KICK_MEMBERS
        | permissions.Permission.CREATE_INSTANT_INVITE
    )
    assert r.managed is False
    assert r.mentionable is False


@pytest.mark.model
def test_Role_guild(state, payload):
    r = roles.Role(state, payload, 1234)
    guild = mock.MagicMock(spec_set=_guild.Guild)
    state.get_guild_by_id = mock.MagicMock(return_value=guild)
    assert r.guild is guild
    state.get_guild_by_id.assert_called_with(1234)
