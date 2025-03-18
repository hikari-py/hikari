# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021-present davfsa
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

import mock
import pytest

from hikari import guilds
from hikari import snowflakes
from hikari import traits
from hikari import users
from hikari.api import shard as shard_api
from hikari.events import member_events


class TestMemberEvent:
    class MockMemberEvent(member_events.MemberEvent):
        def __init__(self, app: traits.RESTAware):
            self._app = app
            self._shard = mock.Mock()
            self._guild_id = snowflakes.Snowflake(123)
            self._user = mock.Mock(app=app, id=snowflakes.Snowflake(456))

        @property
        def app(self) -> traits.RESTAware:
            return self._app

        @property
        def shard(self) -> shard_api.GatewayShard:
            return self._shard

        @property
        def guild_id(self) -> snowflakes.Snowflake:
            return self._guild_id

        @property
        def user(self) -> users.User:
            return self._user

    @pytest.fixture
    def member_event(self, hikari_app: traits.RESTAware) -> member_events.MemberEvent:
        return TestMemberEvent.MockMemberEvent(hikari_app)

    def test_app_property(self, member_event: member_events.MemberEvent):
        assert member_event.app is member_event.user.app

    def test_user_id_property(self, member_event: member_events.MemberEvent):
        assert member_event.user_id == 456

    def test_guild_when_no_cache_trait(self, member_event: member_events.MemberEvent):
        with mock.patch.object(member_event, "_app", None):
            assert member_event.get_guild() is None

    def test_get_guild_when_available(self, member_event: member_events.MemberEvent):
        with (
            mock.patch.object(member_event, "_app", mock.Mock(traits.CacheAware)) as patched_app,
            mock.patch.object(patched_app, "cache") as patched_cache,
            mock.patch.object(patched_cache, "get_available_guild") as patched_get_available_guild,
            mock.patch.object(patched_cache, "get_unavailable_guild") as patched_get_unavailable_guild,
        ):
            result = member_event.get_guild()

            assert result is patched_get_available_guild.return_value
            patched_get_available_guild.assert_called_once_with(123)
            patched_get_unavailable_guild.assert_not_called()

    def test_guild_when_unavailable(self, member_event: member_events.MemberEvent):
        with (
            mock.patch.object(member_event, "_app", mock.Mock(traits.CacheAware)) as patched_app,
            mock.patch.object(patched_app, "cache") as patched_cache,
            mock.patch.object(patched_cache, "get_available_guild", return_value=None) as patched_get_available_guild,
            mock.patch.object(patched_cache, "get_unavailable_guild") as patched_get_unavailable_guild,
        ):
            result = member_event.get_guild()

            assert result is patched_get_unavailable_guild.return_value
            patched_get_unavailable_guild.assert_called_once_with(123)
            patched_get_available_guild.assert_called_once_with(123)


class TestMemberCreateEvent:
    @pytest.fixture
    def event(self) -> member_events.MemberCreateEvent:
        return member_events.MemberCreateEvent(shard=mock.Mock(), member=mock.Mock())

    def test_guild_property(self, event: member_events.MemberCreateEvent):
        with mock.patch.object(event.member, "guild_id", snowflakes.Snowflake(123)):
            assert event.guild_id == 123

    def test_user_property(self, event: member_events.MemberCreateEvent):
        user = mock.Mock()
        with mock.patch.object(event.member, "user", user):
            assert event.user == user


class TestMemberUpdateEvent:
    @pytest.fixture
    def event(self) -> member_events.MemberUpdateEvent:
        return member_events.MemberUpdateEvent(
            shard=mock.Mock(), member=mock.Mock(), old_member=mock.Mock(guilds.Member)
        )

    def test_guild_property(self, event: member_events.MemberUpdateEvent):
        with mock.patch.object(event.member, "guild_id", snowflakes.Snowflake(123)):
            assert event.guild_id == 123

    def test_user_property(self, event: member_events.MemberUpdateEvent):
        user = mock.Mock()
        with mock.patch.object(event.member, "user", user):
            assert event.user == user

    def test_old_user_property(self, event: member_events.MemberUpdateEvent):
        with (
            mock.patch.object(event.member, "guild_id", snowflakes.Snowflake(123)),
            mock.patch.object(event.member, "id", 456),
        ):
            assert event.member.guild_id == 123
            assert event.member.id == 456
