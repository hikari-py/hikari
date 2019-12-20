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
from hikari.orm import state_registry
from hikari.orm.models import applications
from tests.hikari import _helpers


@pytest.fixture
def fabric_obj():
    mock_state_registry = mock.MagicMock(spec_set=state_registry.IStateRegistry)
    return fabric.Fabric(state_registry=mock_state_registry)


@pytest.mark.model()
def test_applications(fabric_obj):
    mock_team_user = {
        "id": "577152550839648258",
        "username": "team577152550839648258",
        "avatar": None,
        "discriminator": "0000",
        "flags": 1024,
    }
    mock_user = {
        "id": "115590097100865541",
        "username": "Neko Nyaster",
        "avatar": None,
        "discriminator": 2424,
    }
    application_obj = applications.Application(
        fabric_obj,
        {
            "bot_public": True,
            "bot_require_code_grant": False,
            "cover_image": "sdaok2109aposi921ie",
            "description": "A place for nekos and humans alike.",
            "guild_id": "115590097100865541",
            "icon": None,
            "id": "175590097100863321",
            "name": "Cat Haven",
            "owner": mock_team_user,
            "primary_sku_id": "199590097100863321",
            "slug": "test",
            "summary": "Only the few will understand.",
            "team": {
                "icon": "s129kjfd9lk10saok289h",
                "id": "229590097100863321",
                "owner_user_id": "175590097100863321",
                "members": [
                    {"membership_state": 2, "permissions": ["*"], "team_id": "175590097100863321", "user": mock_user}
                ],
            },
            "verify_key": "39lds9204odsa092034ko2",
        },
    )
    assert application_obj.is_bot_public is True
    assert application_obj.is_bot_code_grant_required is False
    assert application_obj.cover_image_hash == "sdaok2109aposi921ie"
    assert application_obj.description == "A place for nekos and humans alike."
    assert application_obj.guild_id == 115590097100865541
    assert application_obj.icon_hash is None
    assert application_obj.id == 175590097100863321
    assert application_obj.name == "Cat Haven"
    assert application_obj.primary_sku_id == 199590097100863321
    assert application_obj.slug_url == "test"
    assert application_obj.summary == "Only the few will understand."
    assert application_obj.team.icon == "s129kjfd9lk10saok289h"
    assert application_obj.team.id == 229590097100863321
    assert application_obj.team.owner_user_id == 175590097100863321
    assert application_obj.verify_key == "39lds9204odsa092034ko2"
    fabric_obj.state_registry.parse_user.assert_any_call(mock_user)
    fabric_obj.state_registry.parse_user.assert_any_call(mock_team_user)
    assert fabric_obj.state_registry.parse_user.call_count == 2


@pytest.mark.model
def test_Application___repr__():
    assert repr(
        _helpers.mock_model(
            applications.Application,
            id=42,
            name="foobar",
            description="asdf movies are great",
            __repr__=applications.Application.__repr__,
        )
    )
