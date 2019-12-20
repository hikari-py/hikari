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
import datetime
from unittest import mock

import pytest

from hikari.orm import fabric
from hikari.orm import state_registry
from hikari.orm.models import channels
from hikari.orm.models import guilds
from hikari.orm.models import invites
from hikari.orm.models import users
from tests.hikari import _helpers


@pytest.fixture()
def mock_state_registry():
    return mock.MagicMock(spec_set=state_registry.IStateRegistry)


@pytest.fixture()
def fabric_obj(mock_state_registry):
    return fabric.Fabric(state_registry=mock_state_registry)


@pytest.mark.model
class TestInvite:
    def test_Invite(self, fabric_obj):
        guild_dict = {"id": "165176875973476352", "name": "CS:GO Fraggers Only", "splash": None, "icon": None}
        channel_dict = {"id": "165176875973476352", "name": "illuminati", "type": 0}
        user_dict = {"id": "165176875973476352", "username": "bob", "avatar": "deadbeef", "discriminator": "#1234"}

        inv = invites.Invite(
            fabric_obj,
            {
                "code": "0vCdhLbwjZZTWZLD",
                "guild": guild_dict,
                "channel": channel_dict,
                "target_user": user_dict,
                "target_user_type": 1,
                "approximate_presence_count": 69,
                "approximate_member_count": 420,
            },
        )

        assert inv.code == "0vCdhLbwjZZTWZLD"
        assert inv.target_user_type is invites.InviteTargetUserType.STREAM
        assert inv.approximate_presence_count == 69
        assert inv.approximate_member_count == 420
        assert inv.channel.id == 165176875973476352
        assert inv.channel.name == "illuminati"
        assert inv.channel.type is channels.ChannelType.GUILD_TEXT
        assert inv.guild.id == 165176875973476352
        assert inv.guild.name == "CS:GO Fraggers Only"
        assert inv.guild.splash_hash is None
        assert inv.guild.icon_hash is None
        assert inv.guild.vanity_url_code is None
        assert inv.guild.features == set()
        assert inv.guild.description is None
        assert inv.guild.verification_level is None
        assert inv.guild.banner_hash is None
        fabric_obj.state_registry.parse_user.assert_called_with(user_dict)

    @pytest.mark.model
    def test_Invite___repr__(self):
        assert repr(
            _helpers.mock_model(
                invites.Invite,
                code="baz",
                guild=_helpers.mock_model(guilds.PartialGuild, __repr__=guilds.PartialGuild.__repr__),
                channel=_helpers.mock_model(channels.PartialChannel, __repr__=channels.PartialChannel.__repr__),
                __repr__=invites.Invite.__repr__,
            )
        )

    @pytest.mark.model
    def test_Invite___str__(self):
        invite = _helpers.mock_model(invites.Invite, code="CAFEDEAD", __str__=invites.Invite.__str__)
        assert str(invite) == "CAFEDEAD"


@pytest.mark.model
class TestInviteMetadata:
    def test_InviteMetadata(self, fabric_obj):
        user_dict = {
            "id": "80351110224678912",
            "username": "Nelly",
            "discriminator": "1337",
            "avatar": "8342729096ea3675442027381ff50dfe",
            "verified": True,
            "email": "nelly@discordapp.com",
            "flags": 64,
            "premium_type": 1,
        }

        invm = invites.InviteMetadata(
            fabric_obj,
            {
                "inviter": user_dict,
                "uses": 69,
                "max_uses": 420,
                "max_age": 99999,
                "temporary": True,
                "created_at": "2016-03-31T19:15:39.954000+00:00",
                "revoked": True,
            },
        )

        assert invm.uses == 69
        assert invm.max_uses == 420
        assert invm.max_age == 99999
        assert invm.is_temporary is True
        assert invm.is_revoked is True
        assert invm.created_at == datetime.datetime(2016, 3, 31, 19, 15, 39, 954000, tzinfo=datetime.timezone.utc)
        fabric_obj.state_registry.parse_user.assert_called_with(user_dict)

    @pytest.mark.model
    def test_InviteMetadata___repr__(self):
        assert repr(
            _helpers.mock_model(
                invites.InviteMetadata,
                inviter=_helpers.mock_model(users.User, id=42),
                uses=69,
                max_uses=101,
                created_at=datetime.datetime.fromtimestamp(666).replace(tzinfo=datetime.timezone.utc),
                __repr__=invites.InviteMetadata.__repr__,
            )
        )
