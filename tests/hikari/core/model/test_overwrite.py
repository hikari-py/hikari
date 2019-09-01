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

from hikari.core.model import overwrite
from hikari.core.model import permission
from hikari.core.model import user


@pytest.mark.model
class TestOverwrite:
    def test_Overwrite(self):
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

        expected_inverse = (
            permission.Permission.NONE
            | permission.Permission.KICK_MEMBERS
            | permission.Permission.ADMINISTRATOR
            | permission.Permission.MANAGE_CHANNELS
            | permission.Permission.MANAGE_GUILD
            | permission.Permission.VIEW_AUDIT_LOG
            | permission.Permission.PRIORITY_SPEAKER
            | permission.Permission.VIEW_CHANNEL
            | permission.Permission.SEND_MESSAGES
            | permission.Permission.EMBED_LINKS
            | permission.Permission.ATTACH_FILES
            | permission.Permission.READ_MESSAGE_HISTORY
            | permission.Permission.MENTION_EVERYONE
            | permission.Permission.USE_EXTERNAL_EMOJIS
            | permission.Permission.CONNECT
            | permission.Permission.SPEAK
            | permission.Permission.MUTE_MEMBERS
            | permission.Permission.DEAFEN_MEMBERS
            | permission.Permission.MOVE_MEMBERS
            | permission.Permission.USE_VAD
            | permission.Permission.MANAGE_ROLES
            | permission.Permission.MANAGE_WEBHOOKS
            | permission.Permission.MANAGE_EMOJIS
        )

        assert bin(o.default) == bin(expected_inverse)


@pytest.mark.model
class TestOverwriteEntityType:
    def test_OverwriteEntityType_instancecheck(self):
        m = mock.MagicMock(spec=user.Member)

        # I wasn't sure of this, so this is just to be safe that my assumption was correct that the mocks
        # implement instancecheck and subclass check correctly.
        assert isinstance(m, user.Member)
        assert type(m) is not user.Member

        assert isinstance(m, overwrite.OverwriteEntityType.MEMBER.value)  # always should be right
        assert isinstance(m, overwrite.OverwriteEntityType.MEMBER)  # this is what i am concerned about

    def test_OverwriteEntityType_subclasscheck(self):
        assert issubclass(user.Member, overwrite.OverwriteEntityType.MEMBER.value)  # always should be right
        assert issubclass(user.Member, overwrite.OverwriteEntityType.MEMBER)  # actual thing to test
