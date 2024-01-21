# -*- coding: utf-8 -*-
# Copyright (c) 2020 Tomxey
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import datetime

import mock

from hikari import applications
from hikari import guilds
from hikari import snowflakes
from hikari import users


def assert_objects_equal(a, b):
    assert a == b
    assert b == a
    assert not a != b
    assert not b != a
    assert hash(a) == hash(b)


def assert_objects_not_equal(a, b):
    assert a != b
    assert b != a
    assert not a == b
    assert not b == a


def make_user(user_id, username):
    return users.UserImpl(
        app=mock.Mock(),
        id=snowflakes.Snowflake(user_id),
        discriminator="0001",
        username=username,
        global_name=None,
        avatar_hash=None,
        banner_hash=None,
        accent_color=None,
        is_bot=False,
        is_system=False,
        flags=users.UserFlag.NONE,
    )


def make_team_member(user_id, username):
    user = make_user(user_id, username)
    return applications.TeamMember(
        membership_state=applications.TeamMembershipState.ACCEPTED,
        permissions="*",
        team_id=snowflakes.Snowflake(1234),
        user=user,
    )


def make_guild_member(user_id, username):
    user = make_user(user_id, username)
    return guilds.Member(
        user=user,
        guild_id=snowflakes.Snowflake(2233),
        role_ids=[],
        joined_at=datetime.datetime.now(),
        nickname=user.username,
        premium_since=None,
        guild_avatar_hash="no",
        is_deaf=False,
        is_mute=False,
        is_pending=False,
        raw_communication_disabled_until=None,
    )


class TestUsersComparison:
    def test_user_equal_to_team_member(self):
        user = make_user(1, "yasuoop")
        team_member = make_team_member(1, "yasuoop")
        assert_objects_equal(user, team_member)

    def test_user_not_equal_to_team_member(self):
        user = make_user(1, "yasuoop")
        team_member = make_team_member(2, "taricop")
        assert_objects_not_equal(user, team_member)

    def test_user_equal_to_guild_member(self):
        user = make_user(1, "yasuoop")
        guild_member = make_guild_member(1, "yasuoop")
        assert_objects_equal(user, guild_member)

    def test_user_not_equal_to_guild_member(self):
        user = make_user(1, "yasuoop")
        guild_member = make_guild_member(2, "taricop")
        assert_objects_not_equal(user, guild_member)

    def test_team_member_equal_to_guild_member(self):
        team_member = make_team_member(1, "yasuoop")
        guild_member = make_guild_member(1, "yasuoop")
        assert_objects_equal(team_member, guild_member)

    def test_team_member_not_equal_to_guild_member(self):
        team_member = make_team_member(1, "yasuoop")
        guild_member = make_guild_member(2, "taricop")
        assert_objects_not_equal(team_member, guild_member)
