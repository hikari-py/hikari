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
from __future__ import annotations

import datetime

import mock
import pytest

from hikari import applications
from hikari import emojis
from hikari import guilds
from hikari import snowflakes
from hikari import users


def make_user(user_id):
    return users.UserImpl(
        app=mock.Mock(),
        id=snowflakes.Snowflake(user_id),
        discriminator="0001",
        username="testing",
        global_name=None,
        avatar_decoration=None,
        avatar_hash=None,
        banner_hash=None,
        accent_color=None,
        is_bot=False,
        is_system=False,
        flags=users.UserFlag.NONE,
    )


def make_team_member(user_id):
    user = make_user(user_id)
    return applications.TeamMember(
        membership_state=applications.TeamMembershipState.ACCEPTED,
        permissions="*",
        team_id=snowflakes.Snowflake(1234),
        user=user,
    )


def make_guild_member(user_id):
    user = make_user(user_id)
    return guilds.Member(
        user=user,
        guild_id=snowflakes.Snowflake(2233),
        role_ids=[],
        joined_at=datetime.datetime.now(),
        nickname=user.username,
        premium_since=None,
        guild_avatar_decoration=None,
        guild_avatar_hash="no",
        guild_banner_hash="yes",
        is_deaf=False,
        is_mute=False,
        is_pending=False,
        raw_communication_disabled_until=None,
        guild_flags=guilds.GuildMemberFlags.NONE,
    )


def make_unicode_emoji():
    return emojis.UnicodeEmoji("\N{OK HAND SIGN}")


def make_custom_emoji(emoji_id):
    return emojis.CustomEmoji(id=emoji_id, name="testing", is_animated=False)


def make_known_custom_emoji(emoji_id):
    return emojis.KnownCustomEmoji(
        app=mock.Mock(),
        id=emoji_id,
        name="testing",
        is_animated=False,
        guild_id=snowflakes.Snowflake(123),
        role_ids=[],
        user=None,
        is_colons_required=False,
        is_managed=True,
        is_available=False,
    )


@pytest.mark.parametrize(
    ("a", "b", "eq"),
    [
        (make_user(1), make_team_member(1), True),
        (make_user(1), make_team_member(2), False),
        (make_user(1), make_guild_member(1), True),
        (make_user(1), make_guild_member(2), False),
        (make_team_member(1), make_guild_member(1), True),
        (make_team_member(1), make_guild_member(2), False),
        (make_custom_emoji(1), make_known_custom_emoji(1), True),
        (make_custom_emoji(1), make_known_custom_emoji(2), False),
        (make_unicode_emoji(), make_custom_emoji(1), False),
        (make_unicode_emoji(), make_known_custom_emoji(2), False),
    ],
    ids=[
        "User == Team Member",
        "User != Team Member",
        "User == Guild Member",
        "User != Guild Member",
        "Team Member == Guild Member",
        "Team Member != Guild Member",
        "Custom Emoji == Known Custom Emoji",
        "Custom Emoji != Known Custom Emoji",
        "Unicode Emoji != Custom Emoji",
        "Unicode Emoji != Known Custom Emoji",
    ],
)
def test_comparison(a: object, b: object, eq: bool) -> None:
    if eq:
        assert a == b
        assert b == a
        assert not a != b
        assert not b != a

    else:
        assert a != b
        assert b != a
        assert not a == b
        assert not b == a
