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

from hikari.model import overwrite, permission


@pytest.mark.model
def test_Overwrite():
    o = overwrite.Overwrite.from_dict(
        {
            "id": "1234567890",
            "type": "role",
            "allow": int(
                permission.Permission.ADD_REACTIONS
                | permission.Permission.BAN_MEMBERS
                | permission.Permission.CREATE_INSTANT_INVITE
            ),
            "deny": int(permission.Permission.MANAGE_MESSAGES | permission.Permission.SEND_TTS_MESSAGES),
        }
    )

    assert o.id == 1234567890
    assert o.type == overwrite.OverwriteEntityType.ROLE
    assert o.allow & permission.Permission.ADD_REACTIONS
    assert o.allow & permission.Permission.BAN_MEMBERS
    assert o.allow & permission.Permission.CREATE_INSTANT_INVITE
    assert o.deny & permission.Permission.MANAGE_MESSAGES
    assert o.deny & permission.Permission.SEND_TTS_MESSAGES
