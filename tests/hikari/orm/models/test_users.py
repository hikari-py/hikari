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

from hikari.orm import fabric
from hikari.orm import state_registry
from hikari.orm.models import users


@pytest.fixture()
def mock_state_registry():
    return mock.MagicMock(spec_set=state_registry.IStateRegistry)


@pytest.fixture()
def fabric_obj(mock_state_registry):
    return fabric.Fabric(state_registry=mock_state_registry)


@pytest.mark.model
def test_User_when_not_a_bot_or_system(fabric_obj):
    user_obj = users.User(
        fabric_obj,
        {
            "id": "123456",
            "username": "Boris Johnson",
            "discriminator": "6969",
            "avatar": "1a2b3c4d",
            "locale": "gb",
            "flags": 0b00101101,
            "premium_type": 0b1101101,
        },
    )

    assert user_obj.id == 123456
    assert user_obj.username == "Boris Johnson"
    assert user_obj.discriminator == 6969
    assert user_obj.avatar_hash == "1a2b3c4d"
    assert user_obj.is_bot is False
    assert user_obj.system is False
    user_obj.__repr__()


@pytest.mark.model
def test_User_when_is_a_bot_and_system(fabric_obj):
    user_obj = users.User(
        fabric_obj,
        {
            "id": "123456",
            "username": "Boris Johnson",
            "discriminator": "6969",
            "avatar": None,
            "bot": True,
            "system": True,
        },
    )

    assert user_obj.id == 123456
    assert user_obj.username == "Boris Johnson"
    assert user_obj.discriminator == 6969
    assert user_obj.avatar_hash is None
    assert user_obj.is_bot is True
    assert user_obj.system is True
    user_obj.__repr__()


@pytest.mark.model
def test_OAuth2User(fabric_obj):
    user_obj = users.OAuth2User(
        fabric_obj,
        {
            "id": "123456",
            "username": "Boris Johnson",
            "discriminator": "6969",
            "avatar": "1a2b3c4d",
            "mfa_enabled": True,
            "verified": True,
            "locale": "en-GB",
            "flags": 0b00101101,
            "premium_type": 2,
        },
    )

    assert user_obj.id == 123456
    assert user_obj.username == "Boris Johnson"
    assert user_obj.discriminator == 6969
    assert user_obj.avatar_hash == "1a2b3c4d"
    assert user_obj.is_bot is False
    assert user_obj.system is False
    assert user_obj.verified is True
    assert user_obj.mfa_enabled is True
    assert user_obj.locale == "en-GB"
    user_obj.__repr__()


@pytest.mark.model
@pytest.mark.parametrize(
    ["payload", "expected_type"],
    [
        (
            {
                "id": "123456",
                "username": "Boris Johnson",
                "discriminator": "6969",
                "avatar": "1a2b3c4d",
                "mfa_enabled": True,
                "verified": True,
                "locale": "en-GB",
                "flags": 0b00101101,
                "premium_type": 2,
            },
            users.OAuth2User,
        ),
        (
            {"id": "123456", "username": "Boris Johnson", "discriminator": "6969", "avatar": None, "bot": True},
            users.User,
        ),
    ],
)
def test_parse_user(fabric_obj, payload, expected_type):
    user = users.parse_user(fabric_obj, payload)
    assert isinstance(user, expected_type)
