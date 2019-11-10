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

from hikari import state_registry
from hikari.core.models import users


@pytest.mark.model
def test_User_when_not_a_bot():
    s = mock.MagicMock(spec_set=state_registry.StateRegistry)
    u = users.User(
        s,
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

    assert u.id == 123456
    assert u.username == "Boris Johnson"
    assert u.discriminator == 6969
    assert u.avatar_hash == "1a2b3c4d"
    assert u.bot is False


@pytest.mark.model
def test_User_when_is_a_bot():
    s = mock.MagicMock(spec_set=state_registry.StateRegistry)
    u = users.User(
        s, {"id": "123456", "username": "Boris Johnson", "discriminator": "6969", "avatar": None, "bot": True}
    )

    assert u.id == 123456
    assert u.username == "Boris Johnson"
    assert u.discriminator == 6969
    assert u.avatar_hash is None
    assert u.bot is True


@pytest.mark.model
def test_BotUser():
    s = mock.MagicMock(spec_set=state_registry.StateRegistry)
    u = users.BotUser(
        s,
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

    assert u.id == 123456
    assert u.username == "Boris Johnson"
    assert u.discriminator == 6969
    assert u.avatar_hash == "1a2b3c4d"
    assert u.bot is False
    assert u.verified is True
    assert u.mfa_enabled is True
