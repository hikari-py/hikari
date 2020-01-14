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
from hikari.orm.state import base_registry
from hikari.orm.models import channels
from hikari.orm.models import guilds
from hikari.orm.models import invites
from hikari.orm.models import users
from tests.hikari import _helpers


@pytest.fixture()
def mock_state_registry():
    return mock.MagicMock(spec_set=base_registry.BaseRegistry)


@pytest.fixture()
def fabric_obj(mock_state_registry):
    return fabric.Fabric(state_registry=mock_state_registry)

@pytest.mark.model
def test_VanityURL():
    vanity_url_obj = invites.VanityURL({"code": "osososo", "uses": 42})
    assert vanity_url_obj.code == "osososo"
    assert vanity_url_obj.uses == 42


@pytest.fixture
def mock_guild_payload():
    return {"id": "165176875973476352", "name": "CS:GO Fraggers Only", "splash": None, "icon": None}


@pytest.fixture
def mock_channel_payload():
    return {"id": "165176875973476352", "name": "illuminati", "type": 0}


@pytest.fixture
def mock_user_payload():
    return {"id": "165176875973476352", "username": "bob", "avatar": "deadbeef", "discriminator": "#1234"}


@pytest.mark.model
class TestInvite:
    def test_Invite(self, fabric_obj, mock_guild_payload, mock_channel_payload, mock_user_payload):
        inv = invites.Invite(
            fabric_obj,
            {
                "code": "0vCdhLbwjZZTWZLD",
                "guild": mock_guild_payload,
                "channel": mock_channel_payload,
                "inviter": mock_user_payload,
                "target_user": mock_user_payload,
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
        fabric_obj.state_registry.parse_user.assert_has_calls(
            (mock.call(mock_user_payload), mock.call(mock_user_payload))
        )

    @pytest.mark.model
    def test_Invite___repr__(self):
        assert repr(
            _helpers.mock_model(
                invites.Invite,
                code="baz",
                inviter=_helpers.mock_model(users.User, id=42),
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
class TestInviteWithMetadata:
    def test_InviteWithMetadata(self, fabric_obj, mock_guild_payload, mock_channel_payload, mock_user_payload):
        invm = invites.InviteWithMetadata(
            fabric_obj,
            {
                "code": "0vCdhLbwjZZTWZLD",
                "guild": mock_guild_payload,
                "channel": mock_channel_payload,
                "target_user": mock_user_payload,
                "target_user_type": 1,
                "approximate_presence_count": 69,
                "approximate_member_count": 420,
                "inviter": mock_user_payload,
                "uses": 69,
                "max_uses": 420,
                "max_age": 99999,
                "temporary": True,
                "created_at": "2016-03-31T19:15:39.954000+00:00",
                "revoked": True,
            },
        )

        assert invm.code == "0vCdhLbwjZZTWZLD"
        assert invm.guild.id == 165176875973476352
        assert invm.guild.name == "CS:GO Fraggers Only"
        assert invm.guild.splash_hash is None
        assert invm.guild.icon_hash is None
        assert invm.guild.vanity_url_code is None
        assert invm.guild.features == set()
        assert invm.guild.description is None
        assert invm.guild.verification_level is None
        assert invm.guild.banner_hash is None
        assert invm.channel.id == 165176875973476352
        assert invm.channel.name == "illuminati"
        assert invm.channel.type is channels.ChannelType.GUILD_TEXT
        assert invm.target_user_type is invites.InviteTargetUserType.STREAM
        assert invm.approximate_presence_count == 69
        assert invm.approximate_member_count == 420
        assert invm.uses == 69
        assert invm.max_uses == 420
        assert invm.max_age == 99999
        assert invm.is_temporary is True
        assert invm.is_revoked is True
        assert invm.created_at == datetime.datetime(2016, 3, 31, 19, 15, 39, 954000, tzinfo=datetime.timezone.utc)
        fabric_obj.state_registry.parse_user.assert_has_calls(
            (mock.call(mock_user_payload), mock.call(mock_user_payload))
        )


@pytest.mark.model
def test_InviteWithMetadata___str__():
    invite = _helpers.mock_model(
        invites.InviteWithMetadata, code="CAFEDEAD", __str__=invites.InviteWithMetadata.__str__
    )
    assert str(invite) == "CAFEDEAD"


@pytest.mark.parametrize(
    ["invite_payload", "expected_type"],
    [
        (
            {
                "code": "xdfdsa",
                "guild": {
                    "id": "231",
                    "name": "japanese goblin",
                    "splash": None,
                    "banner": None,
                    "description": None,
                    "icon": None,
                    "features": [],
                    "verification_level": 3,
                    "vanity_url_code": None,
                },
                "channel": {"id": "537340989808050216", "name": "general", "type": 0},
            },
            invites.Invite,
        ),
        (
            {
                "code": "xdfdsa",
                "guild": {
                    "id": "231",
                    "name": "japanese goblin",
                    "splash": None,
                    "banner": None,
                    "description": None,
                    "icon": None,
                    "features": [],
                    "verification_level": 3,
                    "vanity_url_code": None,
                },
                "channel": {"id": "537340989808050216", "name": "general", "type": 0},
                "uses": 27,
                "max_uses": 0,
                "max_age": 0,
                "created_at": "2019-04-19T04:02:07.038000+00:00",
            },
            invites.InviteWithMetadata,
        ),
    ],
)
def test_parse_invite(fabric_obj, invite_payload, expected_type):
    assert isinstance(invites.parse_invite(fabric_obj, invite_payload), expected_type)

    @pytest.mark.model
    def test_InviteMetadata___repr__(self):
        assert repr(
            _helpers.mock_model(
                invites.InviteWithMetadata,
                code="baz",
                guild=_helpers.mock_model(guilds.PartialGuild, __repr__=guilds.PartialGuild.__repr__),
                channel=_helpers.mock_model(channels.PartialChannel, __repr__=channels.PartialChannel.__repr__),
                inviter=_helpers.mock_model(users.User, id=42),
                uses=69,
                max_uses=101,
                created_at=datetime.datetime.fromtimestamp(666).replace(tzinfo=datetime.timezone.utc),
                __repr__=invites.InviteWithMetadata.__repr__,
            )
        )
