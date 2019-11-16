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
def test_User_when_not_a_bot(fabric_obj):
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
    assert user_obj.bot is False


@pytest.mark.model
def test_User_when_is_a_bot(fabric_obj):
    user_obj = users.User(
        fabric_obj, {"id": "123456", "username": "Boris Johnson", "discriminator": "6969", "avatar": None, "bot": True}
    )

    assert user_obj.id == 123456
    assert user_obj.username == "Boris Johnson"
    assert user_obj.discriminator == 6969
    assert user_obj.avatar_hash is None
    assert user_obj.bot is True


@pytest.mark.model
def test_BotUser(fabric_obj):
    user_obj = users.BotUser(
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
            "premium_type": 0b1101101,
        },
    )

    assert user_obj.id == 123456
    assert user_obj.username == "Boris Johnson"
    assert user_obj.discriminator == 6969
    assert user_obj.avatar_hash == "1a2b3c4d"
    assert user_obj.bot is False
    assert user_obj.verified is True
    assert user_obj.mfa_enabled is True
