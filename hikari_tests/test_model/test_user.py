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

from hikari.model import guild, user


def test_User_from_dict_when_not_a_bot():
    u = user.User.from_dict(
        {
            "id": "123456",
            "username": "Boris Johnson",
            "discriminator": "6969",
            "avatar": "1a2b3c4d",
            "mfa_enabled": True,
            "locale": "gb",
            "flags": 0b00101101,
            "premium_type": 0b1101101,
        }
    )

    assert u.id == 123456
    assert u.username == "Boris Johnson"
    assert u.discriminator == 6969
    assert u.avatar_hash == "1a2b3c4d"
    assert u.bot is False


def test_User_from_dict_when_is_a_bot():
    u = user.User.from_dict(
        {"id": "123456", "username": "Boris Johnson", "discriminator": "6969", "avatar": None, "bot": True}
    )

    assert u.id == 123456
    assert u.username == "Boris Johnson"
    assert u.discriminator == 6969
    assert u.avatar_hash is None
    assert u.bot is True


def test_Member_from_dict_with_filled_fields():
    u = user.User(12345, "foobar", 1234, "1a2b3c4d", False)
    g = guild.Guild()
    m = user.Member.from_dict(
        {
            "nick": "foobarbaz",
            "roles": ["11111", "22222", "33333", "44444"],
            "joined_at": "2015-04-26T06:26:56.936000+00:00",
            "premium_since": "2019-05-17T06:26:56.936000+00:00",
            # These should be completely ignored.
            "deaf": False,
            "mute": True,
            "user": {
                "id": "123456",
                "username": "Boris Johnson",
                "discriminator": "6969",
                "avatar": "1a2b3c4d",
                "mfa_enabled": True,
                "locale": "gb",
                "flags": 0b00101101,
                "premium_type": 0b1101101,
            },
        },
        u,
        g,
    )

    assert m.id == 12345
    assert m.username == "foobar"
    assert m.nick == "foobarbaz"
    assert m.joined_at == datetime.datetime(2015, 4, 26, 6, 26, 56, 936000, datetime.timezone.utc)
    assert m.nitro_boosted_at == datetime.datetime(2019, 5, 17, 6, 26, 56, 936000, datetime.timezone.utc)


def test_Member_from_dict_with_no_optional_fields():
    u = user.User(12345, "foobar", 1234, "1a2b3c4d", False)
    g = guild.Guild()
    m = user.Member.from_dict(
        {
            "roles": ["11111", "22222", "33333", "44444"],
            "joined_at": "2015-04-26T06:26:56.936000+00:00",
            # These should be completely ignored.
            "user": {"id": "123456", "username": "Boris Johnson", "discriminator": "6969", "avatar": "1a2b3c4d"},
        },
        u,
        g,
    )

    assert m.id == 12345
    assert m.username == "foobar"
    assert m.nick is None
    assert m.joined_at == datetime.datetime(2015, 4, 26, 6, 26, 56, 936000, datetime.timezone.utc)
    assert m.nitro_boosted_at is None
