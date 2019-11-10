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
import datetime
from unittest import mock

import pytest

from hikari import state_registry
from hikari.core.models import guilds
from hikari.core.models import members
from hikari.core.models import roles
from hikari.core.models import users
from tests.hikari import _helpers


@pytest.mark.model
def test_Member_with_filled_fields():
    s = mock.MagicMock(spec_set=state_registry.StateRegistry)
    user_dict = {
        "id": "123456",
        "username": "Boris Johnson",
        "discriminator": "6969",
        "avatar": "1a2b3c4d",
        "locale": "gb",
        "flags": 0b00101101,
        "premium_type": 0b1101101,
    }
    guild_obj = _helpers.mock_model(guilds.Guild, id=12345)
    m = members.Member(
        s,
        guild_obj,
        {
            "nick": "foobarbaz",
            "roles": ["11111", "22222", "33333", "44444"],
            "joined_at": "2015-04-26T06:26:56.936000+00:00",
            "premium_since": "2019-05-17T06:26:56.936000+00:00",
            # These should be completely ignored.
            "deaf": False,
            "mute": True,
            "user": user_dict,
        },
    )

    assert m.nick == "foobarbaz"
    assert m.joined_at == datetime.datetime(2015, 4, 26, 6, 26, 56, 936000, datetime.timezone.utc)
    assert m.premium_since == datetime.datetime(2019, 5, 17, 6, 26, 56, 936000, datetime.timezone.utc)
    assert m.guild is guild_obj
    s.parse_user.assert_called_with(user_dict)


@pytest.mark.model
def test_Member_with_no_optional_fields():
    s = mock.MagicMock(spec_set=state_registry.StateRegistry)
    user_dict = {"id": "123456", "username": "Boris Johnson", "discriminator": "6969", "avatar": "1a2b3c4d"}
    guild_obj = _helpers.mock_model(guilds.Guild, id=12345)
    m = members.Member(
        s,
        guild_obj,
        {
            "roles": ["11111", "22222", "33333", "44444"],
            "joined_at": "2015-04-26T06:26:56.936000+00:00",
            "user": user_dict,
        },
    )

    assert m.nick is None
    assert m.joined_at == datetime.datetime(2015, 4, 26, 6, 26, 56, 936000, datetime.timezone.utc)
    assert m.premium_since is None
    assert m.guild is guild_obj
    s.parse_user.assert_called_with(user_dict)


@pytest.mark.model
def test_Member_update_state():
    # We have faff mocking the delegate neatly, so whatever. Hacks also work.
    role_one = _helpers.mock_model(roles.Role)
    role_two = _helpers.mock_model(roles.Role)
    role_three = _helpers.mock_model(roles.Role)

    role_objs = [role_one, role_two, role_three]

    class MockMember:
        _state = mock.MagicMock(side_effects=[role_one, role_two, role_three])
        _user = mock.MagicMock()

    m = mock.MagicMock(wraps=MockMember())
    members.Member.update_state(m, role_objs, "potato")
    assert m.nick == "potato"
    assert m.roles == role_objs


@pytest.mark.model
def test_Member_user_accessor():
    u = mock.MagicMock(spec=users.User)
    g = mock.MagicMock(spec=guilds.Guild)
    s = mock.MagicMock(spec_set=state_registry.StateRegistry)
    # Member's state is delegated to the inner user.
    u._state = s
    s.parse_user = mock.MagicMock(return_value=u)
    s.get_guild_by_id = mock.MagicMock(return_value=g)
    m = members.Member(s, 1234, {"joined_at": "2019-05-17T06:26:56.936000+00:00", "user": u})
    assert m.user is u


@pytest.mark.model
def test_Member_guild_accessor():
    u = mock.MagicMock(spec=users.User)
    g = mock.MagicMock(spec=guilds.Guild)
    s = mock.MagicMock(spec_set=state_registry.StateRegistry)
    # Member's state is delegated to the inner user.
    u._state = s
    s.parse_user = mock.MagicMock(return_value=u)
    m = members.Member(s, g, {"joined_at": "2019-05-17T06:26:56.936000+00:00", "user": u, "guild_id": 1234})
    assert m.guild is g
