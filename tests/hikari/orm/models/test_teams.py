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
from unittest import mock

import pytest

from hikari.orm import fabric
from hikari.orm.models import teams
from hikari.orm.models import users
from hikari.orm.state import base_registry
from tests.hikari import _helpers


@pytest.fixture()
def member_payload():
    return {
        "membership_state": 2,
        "permissions": ["*"],
        "team_id": "1234321",
        "user": {"avatar": "1a2b3c", "discriminator": 1234, "id": "9876789", "username": "BenDover7"},
    }


@pytest.fixture()
def team_payload(member_payload):
    return {"icon": "1a2b3c", "id": "1234321", "members": [member_payload], "owner_user_id": "9876789"}


@pytest.fixture()
def fabric_obj():
    spec = mock.create_autospec(fabric.Fabric)
    spec.state_registry = mock.create_autospec(base_registry.BaseRegistry)
    return spec


def test_Team(team_payload, fabric_obj, member_payload):
    with mock.patch("hikari.orm.models.teams.TeamMember") as team_member:
        obj = teams.Team(fabric_obj, team_payload)

    assert obj.owner_user_id == 9876789
    assert len(obj.members) == 1
    team_member.assert_called_once_with(fabric_obj, member_payload)
    assert isinstance(obj.members, dict)
    assert obj.id == 1234321
    assert obj.icon == "1a2b3c"


@pytest.mark.model
def test_Team___repr__():
    assert repr(_helpers.mock_model(teams.Team, id=42, owner_user_id=69, __repr__=teams.Team.__repr__))


def test_TeamMember(fabric_obj, member_payload):
    obj = teams.TeamMember(fabric_obj, member_payload)
    assert obj.membership_state == teams.MembershipState.ACCEPTED
    assert obj.permissions == {"*"}
    assert obj.team_id == 1234321
    fabric_obj.state_registry.parse_user.assert_called_once_with(member_payload["user"])


@pytest.mark.model
def test_TeamMember___repr__():
    assert repr(
        _helpers.mock_model(
            teams.TeamMember,
            team_id=42,
            permissions=["*"],
            membership_state=teams.MembershipState.INVITED,
            user=_helpers.mock_model(users.User, id=42, username="foo"),
            __repr__=teams.TeamMember.__repr__,
        )
    )
