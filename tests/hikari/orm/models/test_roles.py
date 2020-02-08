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

from hikari.orm import fabric
from hikari.orm.models import guilds
from hikari.orm.models import permissions
from hikari.orm.models import roles
from hikari.orm.state import base_registry
from tests.hikari import _helpers


@pytest.fixture
def mock_state_registry():
    return _helpers.create_autospec(base_registry.BaseRegistry)


@pytest.fixture()
def fabric_obj(mock_state_registry):
    return fabric.Fabric(state_registry=mock_state_registry)


@pytest.fixture
def partial_role_payload():
    return {"name": "I am a role", "id": "583692435939524624"}


@pytest.fixture
def role_payload():
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
def test_PartialRole(partial_role_payload):
    partial_role_obj = roles.PartialRole(partial_role_payload)
    assert partial_role_obj.name == "I am a role"
    assert partial_role_obj.id == 583692435939524624


@pytest.mark.model
def test_PartialRole___repr__():
    assert repr(_helpers.mock_model(roles.PartialRole, id=42, name="foo", __repr__=roles.PartialRole.__repr__))


@pytest.mark.model
def test_Role(fabric_obj, role_payload):
    guild_obj = _helpers.mock_model(guilds.Guild, id=6969)
    role_obj = roles.Role(fabric_obj, role_payload, guild_obj.id)
    fabric_obj.state_registry.get_mandatory_guild_by_id.return_value = guild_obj

    assert role_obj.id == 41771983423143936
    assert role_obj.name == "WE DEM BOYZZ!!!!!!"
    assert role_obj.color == 0x3498DB
    assert role_obj.is_hoisted is True
    assert role_obj.position == 1
    assert role_obj.guild_id == guild_obj.id
    assert role_obj.permissions == (
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
    assert role_obj.is_managed is False
    assert role_obj.is_mentionable is False
    assert role_obj.guild is guild_obj
    fabric_obj.state_registry.get_mandatory_guild_by_id.assert_called_once_with(6969)


@pytest.mark.model
def test_Role___repr__():
    assert repr(
        _helpers.mock_model(
            roles.Role,
            id=42,
            name="foo",
            position=69,
            is_managed=True,
            is_mentionable=True,
            is_hoisted=True,
            __repr__=roles.Role.__repr__,
        )
    )
