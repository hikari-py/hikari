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
import datetime
import pytest

import mock

from hikari.api.rest import app as rest_app
from hikari.impl import stateful_cache
from hikari.models import guilds
from hikari.models import users
from hikari.utilities import snowflake
from tests.hikari import hikari_test_helpers


class TestStatefulCacheComponentImpl:
    @pytest.fixture()
    def app_impl(self):
        return mock.Mock(rest_app.IApp)

    @pytest.fixture()
    def cache_impl(self, app_impl) -> stateful_cache.StatefulCacheComponentImpl:
        return hikari_test_helpers.unslot_class(stateful_cache.StatefulCacheComponentImpl)(app=app_impl, intents=None)

    def test_clear_members_for_known_member_cache(self, cache_impl):
        ...

    def test_delete_member_for_unknown_guild_record(self, cache_impl):
        assert cache_impl.delete_member(snowflake.Snowflake(42123), snowflake.Snowflake(67876)) is None

    def test_delete_member_for_unknown_member_cache(self, cache_impl):
        cache_impl._guild_entries = {snowflake.Snowflake(42123): stateful_cache._GuildRecord()}
        assert cache_impl.delete_member(snowflake.Snowflake(42123), snowflake.Snowflake(67876)) is None

    def test_delete_member_for_known_member(self, cache_impl):
        mock_member = mock.MagicMock(guilds.Member)
        mock_member_data = mock.MagicMock(stateful_cache._MemberData)
        cache_impl._guild_entries = {
            snowflake.Snowflake(42123): stateful_cache._GuildRecord(
                members={snowflake.Snowflake(67876): mock_member_data}
            )
        }
        cache_impl._build_member = mock.MagicMock(return_value=mock_member)
        assert cache_impl.delete_member(snowflake.Snowflake(42123), snowflake.Snowflake(67876)) is mock_member
        cache_impl._build_member.assert_called_once_with(mock_member_data)

    def test_get_member_for_unknown_member_cache(self, cache_impl):
        cache_impl._guild_entries = {snowflake.Snowflake(1234213): stateful_cache._GuildRecord()}
        assert cache_impl.get_member(snowflake.Snowflake(1234213), snowflake.Snowflake(512312354)) is None

    def test_get_member_for_unknown_guild_record(self, cache_impl):
        assert cache_impl.get_member(snowflake.Snowflake(1234213), snowflake.Snowflake(512312354)) is None

    def test_get_member_for_known_member(self, cache_impl):
        mock_user = mock.MagicMock(users.User)
        role_ids = stateful_cache._IDTable()
        role_ids.add_all((snowflake.Snowflake(65234), snowflake.Snowflake(654234123)))
        member_data = stateful_cache._MemberData(
            id=snowflake.Snowflake(512312354),
            guild_id=snowflake.Snowflake(6434435234),
            nickname="NICK",
            role_ids=role_ids,
            joined_at=datetime.datetime(2020, 7, 9, 13, 11, 18, 384554, tzinfo=datetime.timezone.utc),
            premium_since=datetime.datetime(2020, 7, 17, 13, 11, 18, 384554, tzinfo=datetime.timezone.utc),
            is_deaf=False,
            is_mute=True,
        )
        cache_impl._guild_entries = {
            snowflake.Snowflake(1234213): stateful_cache._GuildRecord(
                members={snowflake.Snowflake(512312354): member_data}
            )
        }
        cache_impl._user_entries = {snowflake.Snowflake(512312354): mock_user}
        member = cache_impl.get_member(snowflake.Snowflake(1234213), snowflake.Snowflake(512312354))
        assert member.user == mock_user
        assert member.guild_id == 6434435234
        assert member.nickname == "NICK"
        assert list(member.role_ids) == [654234123, 65234]  # TODO: is order guaranteed here or should i use sets?
        assert member.joined_at == datetime.datetime(2020, 7, 9, 13, 11, 18, 384554, tzinfo=datetime.timezone.utc)
        assert member.premium_since == datetime.datetime(2020, 7, 17, 13, 11, 18, 384554, tzinfo=datetime.timezone.utc)
        assert member.is_deaf is False
        assert member.is_mute is True

    @pytest.mark.asyncio
    async def test_get_members_view_for_unknown_guild_record(self, cache_impl):
        members_iterator = cache_impl.get_members_view(snowflake.Snowflake(42334))
        assert await members_iterator.iterator() == []

    @pytest.mark.asyncio
    async def test_get_members_view_for_unknown_member_cache(self, cache_impl):
        cache_impl._guild_entries = {snowflake.Snowflake(42334): stateful_cache._GuildRecord()}
        members_iterator = cache_impl.get_members_view(snowflake.Snowflake(42334))
        assert await members_iterator.iterator() == []

    @pytest.mark.asyncio
    async def test_get_members_view_for_known_guild(self, cache_impl):
        mock_member_1 = mock.MagicMock(guilds.Member)
        mock_member_2 = mock.MagicMock(guilds.Member)
        mock_user_1 = mock.MagicMock(users.User)
        mock_user_2 = mock.MagicMock(users.User)
        guild_record = stateful_cache._GuildRecord(
            members={
                snowflake.Snowflake(3214321): mock.MagicMock(
                    stateful_cache._GuildRecord,
                    id=snowflake.Snowflake(3214321),
                    build_entity=mock.MagicMock(return_value=mock_member_1),
                ),
                snowflake.Snowflake(53224): mock.MagicMock(
                    stateful_cache._GuildRecord,
                    id=snowflake.Snowflake(53224),
                    build_entity=mock.MagicMock(return_value=mock_member_2),
                ),
            },
        )
        cache_impl._guild_entries = {snowflake.Snowflake(42334): guild_record}
        cache_impl._user_entries = {snowflake.Snowflake(3214321): mock_user_1, snowflake.Snowflake(53224): mock_user_2}
        members_iterator = cache_impl.get_members_view(snowflake.Snowflake(42334))
        assert members_iterator == {
            snowflake.Snowflake(3214321): mock_member_1,
            snowflake.Snowflake(53224): mock_member_2,
        }
        assert members_iterator[snowflake.Snowflake(3214321)].user == mock_user_1
        assert members_iterator[snowflake.Snowflake(53224)].user == mock_user_2

    def test_set_member(self, cache_impl):
        mock_user = mock.Mock(users.User, id=snowflake.Snowflake(645234123))
        member_model = guilds.Member()
        member_model.guild_id = snowflake.Snowflake(67345234)
        member_model.user = mock_user
        member_model.nickname = "A NICK LOL"
        member_model.role_ids = {snowflake.Snowflake(65345234), snowflake.Snowflake(123123)}
        member_model.joined_at = datetime.datetime(2020, 7, 15, 23, 30, 59, 501602, tzinfo=datetime.timezone.utc)
        member_model.premium_since = datetime.datetime(2020, 7, 1, 2, 0, 12, 501602, tzinfo=datetime.timezone.utc)
        member_model.is_deaf = True
        member_model.is_mute = False
        cache_impl.set_member(member_model)
        assert 67345234 in cache_impl._guild_entries
        assert 645234123 in cache_impl._guild_entries[snowflake.Snowflake(67345234)].members
        member_entry = cache_impl._guild_entries[snowflake.Snowflake(67345234)].members.get(
            snowflake.Snowflake(645234123), ...
        )
        assert member_entry is not ...
        assert member_entry.id == 645234123
        assert member_entry.guild_id == 67345234
        assert member_entry.nickname == "A NICK LOL"
        assert member_entry.role_ids == {65345234, 123123}
        assert member_entry.joined_at == datetime.datetime(
            2020, 7, 15, 23, 30, 59, 501602, tzinfo=datetime.timezone.utc
        )
        assert member_entry.premium_since == datetime.datetime(
            2020, 7, 1, 2, 0, 12, 501602, tzinfo=datetime.timezone.utc
        )
        assert member_entry.is_deaf is True
        assert member_entry.is_mute is False
        assert not hasattr(member_entry, "user")

    def test_update_member(self, cache_impl):
        ...

    def test_clear_users_for_cached_users(self, cache_impl):
        mock_user_1 = mock.MagicMock(users.User)
        mock_user_2 = mock.MagicMock(users.User)
        cache_impl._user_entries = {
            snowflake.Snowflake(5432123): mock_user_1,
            snowflake.Snowflake(7654433245): mock_user_2,
        }
        users_iterator = cache_impl.clear_users()
        assert users_iterator == {
            snowflake.Snowflake(5432123): mock_user_1,
            snowflake.Snowflake(7654433245): mock_user_2,
        }
        assert cache_impl._user_entries == {}

    def test_clear_users_for_empty_user_cache(self, cache_impl):
        assert cache_impl.clear_users() == {}
        assert cache_impl._user_entries == {}

    def test_delete_user_for_known_user(self, cache_impl):
        mock_user = mock.MagicMock(users.User)
        mock_other_user = mock.MagicMock(users.User)
        cache_impl._user_entries = {
            snowflake.Snowflake(21231234): mock_user,
            snowflake.Snowflake(645234): mock_other_user,
        }
        assert cache_impl.delete_user(snowflake.Snowflake(21231234)) is mock_user
        assert cache_impl._user_entries == {snowflake.Snowflake(645234): mock_other_user}

    def test_delete_user_for_unknown_user(self, cache_impl):
        mock_user = mock.MagicMock(users.User)
        mock_other_user = mock.MagicMock(users.User)
        cache_impl._user_entries = {
            snowflake.Snowflake(21231234): mock_user,
            snowflake.Snowflake(645234): mock_other_user,
        }
        assert cache_impl.delete_user(snowflake.Snowflake(75423423)) is None
        assert cache_impl._user_entries == {
            snowflake.Snowflake(21231234): mock_user,
            snowflake.Snowflake(645234): mock_other_user,
        }

    def test_get_user_for_known_user(self, cache_impl):
        mock_user = mock.MagicMock(users.User)
        cache_impl._user_entries = {
            snowflake.Snowflake(21231234): mock_user,
            snowflake.Snowflake(645234): mock.MagicMock(users.User),
        }
        assert cache_impl.get_user(snowflake.Snowflake(21231234)) == mock_user

    def test_get_users_view_for_filled_user_cache(self, cache_impl):
        mock_user_1 = mock.MagicMock(users.User)
        mock_user_2 = mock.MagicMock(users.User)
        cache_impl._user_entries = {snowflake.Snowflake(54123): mock_user_1, snowflake.Snowflake(76345): mock_user_2}
        assert cache_impl.get_users_view() == {
            snowflake.Snowflake(54123): mock_user_1,
            snowflake.Snowflake(76345): mock_user_2,
        }

    def test_get_users_view_for_empty_user_cache(self, cache_impl):
        assert cache_impl.get_users_view() == {}

    def test_set_user(self, cache_impl):
        mock_user = mock.MagicMock(users.User, id=snowflake.Snowflake(6451234123))
        mock_cached_user = mock.MagicMock(users.User)
        cache_impl._user_entries = {snowflake.Snowflake(542143): mock_cached_user}
        assert cache_impl.set_user(mock_user) is None
        assert cache_impl._user_entries == {
            snowflake.Snowflake(542143): mock_cached_user,
            snowflake.Snowflake(6451234123): mock_user,
        }

    def test_update_user(self, cache_impl):
        mock_old_cached_user = mock.MagicMock(users.User)
        mock_new_cached_user = mock.MagicMock(users.User)
        mock_user = mock.MagicMock(users.User, id=snowflake.Snowflake(54123123))
        cache_impl.get_user = mock.MagicMock(side_effect=(mock_old_cached_user, mock_new_cached_user))
        cache_impl.set_user = mock.MagicMock()
        assert cache_impl.update_user(mock_user) == (mock_old_cached_user, mock_new_cached_user)
        cache_impl.set_user.assert_called_once_with(mock_user)
        cache_impl.get_user.assert_has_calls([mock.call(54123123), mock.call(54123123)])
