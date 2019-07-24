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
import pytest

from hikari.model import permission
from hikari.model import role


@pytest.mark.model
def test_Role_from_dict():
    d = {
        "id": "41771983423143936",
        "name": "WE DEM BOYZZ!!!!!!",
        "color": 3447003,
        "hoist": True,
        "position": 1,
        "permissions": 66321471,
        "managed": False,
        "mentionable": False,
    }

    r = role.Role.from_dict(d)

    assert r.id == 41771983423143936
    assert r.name == "WE DEM BOYZZ!!!!!!"
    assert r.color == 0x3498DB
    assert r.hoist is True
    assert r.position == 1
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
