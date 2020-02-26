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

import hikari.orm.models.members
from hikari.orm.models import overwrites
from hikari.orm.models import permissions
from tests.hikari import _helpers


@pytest.mark.model
class TestOverwrite:
    def test_Overwrite(self):
        o = overwrites.Overwrite(
            id="1234567890",
            type="role",
            allow=int(
                permissions.Permission.ADD_REACTIONS
                | permissions.Permission.BAN_MEMBERS
                | permissions.Permission.CREATE_INSTANT_INVITE
            ),
            deny=int(permissions.Permission.MANAGE_MESSAGES | permissions.Permission.SEND_TTS_MESSAGES),
        )

        assert o.id == 1234567890
        assert o.type == overwrites.OverwriteEntityType.ROLE
        assert o.allow & permissions.Permission.ADD_REACTIONS
        assert o.allow & permissions.Permission.BAN_MEMBERS
        assert o.allow & permissions.Permission.CREATE_INSTANT_INVITE
        assert o.deny & permissions.Permission.MANAGE_MESSAGES
        assert o.deny & permissions.Permission.SEND_TTS_MESSAGES

        expected_inverse = ~permissions.Permission.NONE
        expected_inverse ^= permissions.Permission.MANAGE_MESSAGES
        expected_inverse ^= permissions.Permission.SEND_TTS_MESSAGES
        expected_inverse ^= permissions.Permission.CREATE_INSTANT_INVITE
        expected_inverse ^= permissions.Permission.BAN_MEMBERS
        expected_inverse ^= permissions.Permission.ADD_REACTIONS

        assert bin(o.default) == bin(expected_inverse)

    def test_Overwrite_to_dict(self):
        o = overwrites.Overwrite(
            id="1234567890",
            type="role",
            allow=int(
                permissions.Permission.ADD_REACTIONS
                | permissions.Permission.BAN_MEMBERS
                | permissions.Permission.CREATE_INSTANT_INVITE
            ),
            deny=int(permissions.Permission.MANAGE_MESSAGES | permissions.Permission.SEND_TTS_MESSAGES),
        )
        assert o.to_dict() == {"id": 1234567890, "type": "role", "allow": 69, "deny": 12288}

    @pytest.mark.model
    def test_Overwrite___repr__(self):
        assert repr(
            _helpers.mock_model(
                overwrites.Overwrite,
                id=42,
                type=overwrites.OverwriteEntityType.ROLE,
                allow=permissions.NONE,
                deny=permissions.CONNECT,
                __repr__=overwrites.Overwrite.__repr__,
            )
        )


@pytest.mark.model
class TestOverwriteEntityType:
    def test_OverwriteEntityType_instancecheck(self):
        m = mock.MagicMock(spec=hikari.orm.models.members.Member)

        # I wasn't sure of this, so this is just to be safe that my assumption was correct that the mocks
        # implement instancecheck and subclass check correctly.
        assert isinstance(m, hikari.orm.models.members.Member)
        assert type(m) is not hikari.orm.models.members.Member

        assert isinstance(m, overwrites.OverwriteEntityType.MEMBER.value)  # always should be right
        assert isinstance(m, overwrites.OverwriteEntityType.MEMBER)  # this is what i am concerned about

    def test_OverwriteEntityType_subclasscheck(self):
        assert issubclass(
            hikari.orm.models.members.Member, overwrites.OverwriteEntityType.MEMBER.value
        )  # always should be right
        assert issubclass(
            hikari.orm.models.members.Member, overwrites.OverwriteEntityType.MEMBER
        )  # actual thing to test
