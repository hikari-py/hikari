# -*- coding: utf-8 -*-
# Copyright (c) 2020 Nekokatt
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
import pytest

from hikari import emojis
from hikari import guilds
from hikari import invites
from hikari import snowflakes
from hikari import traits
from hikari import users
from hikari import voices
from hikari.impl import stateful_cache
from hikari.internal import cache
from hikari.internal import collections
from tests.hikari import hikari_test_helpers


class TestStatefulCacheImpl:
    @pytest.fixture()
    def app_impl(self):
        return mock.Mock(traits.RESTAware)

    @pytest.fixture()
    def cache_impl(self, app_impl) -> stateful_cache.StatefulCacheImpl:
        return hikari_test_helpers.mock_class_namespace(stateful_cache.StatefulCacheImpl, slots_=False)(
            app=app_impl, intents=None
        )

    def test__build_emoji(self, cache_impl):
        emoji_data = cache.KnownCustomEmojiData(
            id=snowflakes.Snowflake(1233534234),
            name="OKOKOKOKOK",
            is_animated=True,
            guild_id=snowflakes.Snowflake(65234123),
            role_ids=(snowflakes.Snowflake(1235123), snowflakes.Snowflake(763245234)),
            user_id=snowflakes.Snowflake(56234232),
            is_colons_required=False,
            is_managed=False,
            is_available=True,
        )
        mock_user = mock.MagicMock(users.User)
        cache_impl._user_entries = collections.FreezableDict(
            {snowflakes.Snowflake(56234232): cache.GenericRefWrapper(object=mock_user)}
        )
        emoji = cache_impl._build_emoji(emoji_data)
        assert emoji.app is cache_impl._app
        assert emoji.id == snowflakes.Snowflake(1233534234)
        assert emoji.name == "OKOKOKOKOK"
        assert emoji.guild_id == snowflakes.Snowflake(65234123)
        assert emoji.user == mock_user
        assert emoji.user is not mock_user
        assert emoji.is_animated is True
        assert emoji.is_colons_required is False
        assert emoji.is_managed is False
        assert emoji.is_available is True

    def test__build_emoji_with_passed_through_users(self, cache_impl):
        emoji_data = cache.KnownCustomEmojiData(
            id=snowflakes.Snowflake(1233534234),
            name="OKOKOKOKOK",
            is_animated=True,
            guild_id=snowflakes.Snowflake(65234123),
            role_ids=(snowflakes.Snowflake(1235123), snowflakes.Snowflake(763245234)),
            user_id=snowflakes.Snowflake(56234232),
            is_colons_required=False,
            is_managed=False,
            is_available=True,
        )
        mock_user = mock.MagicMock(users.User)
        cache_impl._user_entries = collections.FreezableDict({})
        emoji = cache_impl._build_emoji(
            emoji_data,
            cached_users={snowflakes.Snowflake(56234232): cache.GenericRefWrapper(object=mock_user)},
        )
        assert emoji.user == mock_user
        assert emoji.user is not mock_user

    def test__build_emoji_with_no_user(self, cache_impl):
        emoji_data = cache.KnownCustomEmojiData(
            id=snowflakes.Snowflake(1233534234),
            name="OKOKOKOKOK",
            is_animated=True,
            guild_id=snowflakes.Snowflake(65234123),
            role_ids=(snowflakes.Snowflake(1235123), snowflakes.Snowflake(763245234)),
            user_id=None,
            is_colons_required=False,
            is_managed=False,
            is_available=True,
        )
        cache_impl._build_user = mock.Mock()
        emoji = cache_impl._build_emoji(emoji_data)
        cache_impl._build_user.assert_not_called()
        assert emoji.user is None

    def test_clear_emojis(self, cache_impl):
        mock_emoji_data_1 = mock.Mock(cache.KnownCustomEmojiData, user_id=snowflakes.Snowflake(123123), ref_count=0)
        mock_emoji_data_2 = mock.Mock(cache.KnownCustomEmojiData, user_id=snowflakes.Snowflake(123), ref_count=0)
        mock_emoji_data_3 = mock.Mock(cache.KnownCustomEmojiData, user_id=None, ref_count=0)
        mock_emoji_1 = mock.Mock(emojis.Emoji)
        mock_emoji_2 = mock.Mock(emojis.Emoji)
        mock_emoji_3 = mock.Mock(emojis.Emoji)
        mock_wrapped_user_1 = mock.Mock(cache.GenericRefWrapper[users.User])
        mock_wrapped_user_2 = mock.Mock(cache.GenericRefWrapper[users.User])
        cache_impl._emoji_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(43123123): mock_emoji_data_1,
                snowflakes.Snowflake(87643523): mock_emoji_data_2,
                snowflakes.Snowflake(6873451): mock_emoji_data_3,
            }
        )
        cache_impl._user_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(123123): mock_wrapped_user_1,
                snowflakes.Snowflake(123): mock_wrapped_user_2,
                snowflakes.Snowflake(99999): mock.Mock(cache.GenericRefWrapper),
            }
        )
        cache_impl._build_emoji = mock.Mock(side_effect=[mock_emoji_1, mock_emoji_2, mock_emoji_3])
        cache_impl._garbage_collect_user = mock.Mock()
        view = cache_impl.clear_emojis()
        assert view == {
            snowflakes.Snowflake(43123123): mock_emoji_1,
            snowflakes.Snowflake(87643523): mock_emoji_2,
            snowflakes.Snowflake(6873451): mock_emoji_3,
        }
        assert cache_impl._emoji_entries == {}
        cache_impl._garbage_collect_user.assert_has_calls([mock.call(123123, decrement=1), mock.call(123, decrement=1)])
        cache_impl._build_emoji.assert_has_calls(
            [
                mock.call(
                    mock_emoji_data_1,
                    cached_users={
                        snowflakes.Snowflake(123123): mock_wrapped_user_1,
                        snowflakes.Snowflake(123): mock_wrapped_user_2,
                    },
                ),
                mock.call(
                    mock_emoji_data_2,
                    cached_users={
                        snowflakes.Snowflake(123123): mock_wrapped_user_1,
                        snowflakes.Snowflake(123): mock_wrapped_user_2,
                    },
                ),
                mock.call(
                    mock_emoji_data_3,
                    cached_users={
                        snowflakes.Snowflake(123123): mock_wrapped_user_1,
                        snowflakes.Snowflake(123): mock_wrapped_user_2,
                    },
                ),
            ]
        )

    def test_clear_emojis_for_guild(self, cache_impl):
        mock_emoji_data_1 = mock.Mock(cache.KnownCustomEmojiData, user_id=snowflakes.Snowflake(123123), ref_count=0)
        mock_emoji_data_2 = mock.Mock(cache.KnownCustomEmojiData, user_id=snowflakes.Snowflake(123), ref_count=0)
        mock_emoji_data_3 = mock.Mock(cache.KnownCustomEmojiData, user_id=None, ref_count=0)
        mock_other_emoji_data = mock.Mock(cache.KnownCustomEmojiData)
        emoji_ids = collections.SnowflakeSet()
        emoji_ids.add_all(
            [snowflakes.Snowflake(43123123), snowflakes.Snowflake(87643523), snowflakes.Snowflake(6873451)]
        )
        mock_emoji_1 = mock.Mock(emojis.Emoji)
        mock_emoji_2 = mock.Mock(emojis.Emoji)
        mock_emoji_3 = mock.Mock(emojis.Emoji)
        mock_wrapped_user_1 = mock.Mock(cache.GenericRefWrapper[users.User])
        mock_wrapped_user_2 = mock.Mock(cache.GenericRefWrapper[users.User])
        cache_impl._emoji_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(6873451): mock_emoji_data_1,
                snowflakes.Snowflake(43123123): mock_emoji_data_2,
                snowflakes.Snowflake(87643523): mock_emoji_data_3,
                snowflakes.Snowflake(111): mock_other_emoji_data,
            }
        )
        cache_impl._user_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(123123): mock_wrapped_user_1,
                snowflakes.Snowflake(123): mock_wrapped_user_2,
                snowflakes.Snowflake(99999): mock.Mock(cache.GenericRefWrapper),
            }
        )
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(432123123): cache.GuildRecord(emojis=emoji_ids),
                snowflakes.Snowflake(1): mock.Mock(cache.GuildRecord),
            }
        )
        cache_impl._build_emoji = mock.Mock(side_effect=[mock_emoji_1, mock_emoji_2, mock_emoji_3])
        cache_impl._remove_guild_record_if_empty = mock.Mock()
        cache_impl._garbage_collect_user = mock.Mock()
        emoji_mapping = cache_impl.clear_emojis_for_guild(snowflakes.Snowflake(432123123))
        cache_impl._garbage_collect_user.assert_has_calls([mock.call(123123, decrement=1), mock.call(123, decrement=1)])
        cache_impl._remove_guild_record_if_empty.assert_called_once_with(snowflakes.Snowflake(432123123))
        assert emoji_mapping == {
            snowflakes.Snowflake(6873451): mock_emoji_1,
            snowflakes.Snowflake(43123123): mock_emoji_2,
            snowflakes.Snowflake(87643523): mock_emoji_3,
        }
        assert cache_impl._emoji_entries == collections.FreezableDict(
            {snowflakes.Snowflake(111): mock_other_emoji_data}
        )
        assert cache_impl._guild_entries[snowflakes.Snowflake(432123123)].emojis is None
        cache_impl._build_emoji.assert_has_calls(
            [
                mock.call(
                    mock_emoji_data_1,
                    cached_users={
                        snowflakes.Snowflake(123123): mock_wrapped_user_1,
                        snowflakes.Snowflake(123): mock_wrapped_user_2,
                    },
                ),
                mock.call(
                    mock_emoji_data_2,
                    cached_users={
                        snowflakes.Snowflake(123123): mock_wrapped_user_1,
                        snowflakes.Snowflake(123): mock_wrapped_user_2,
                    },
                ),
                mock.call(
                    mock_emoji_data_3,
                    cached_users={
                        snowflakes.Snowflake(123123): mock_wrapped_user_1,
                        snowflakes.Snowflake(123): mock_wrapped_user_2,
                    },
                ),
            ]
        )

    def test_clear_emojis_for_guild_for_unknown_emoji_cache(self, cache_impl):
        cache_impl._emoji_entries = {snowflakes.Snowflake(3123): mock.Mock(cache.KnownCustomEmojiData)}
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(432123123): cache.GuildRecord(),
                snowflakes.Snowflake(1): mock.Mock(cache.GuildRecord),
            }
        )
        cache_impl._build_emoji = mock.Mock()
        cache_impl._remove_guild_record_if_empty = mock.Mock()
        cache_impl._garbage_collect_user = mock.Mock()
        emoji_mapping = cache_impl.clear_emojis_for_guild(snowflakes.Snowflake(432123123))
        cache_impl._garbage_collect_user.assert_not_called()
        cache_impl._remove_guild_record_if_empty.assert_not_called()
        assert emoji_mapping == {}
        cache_impl._build_emoji.assert_not_called()

    def test_clear_emojis_for_guild_for_unknown_record(self, cache_impl):
        cache_impl._emoji_entries = {snowflakes.Snowflake(123124): mock.Mock(cache.KnownCustomEmojiData)}
        cache_impl._guild_entries = collections.FreezableDict({snowflakes.Snowflake(1): mock.Mock(cache.GuildRecord)})
        cache_impl._build_emoji = mock.Mock()
        cache_impl._remove_guild_record_if_empty = mock.Mock()
        cache_impl._garbage_collect_user = mock.Mock()
        emoji_mapping = cache_impl.clear_emojis_for_guild(snowflakes.Snowflake(432123123))
        cache_impl._garbage_collect_user.assert_not_called()
        cache_impl._remove_guild_record_if_empty.assert_not_called()
        assert emoji_mapping == {}
        cache_impl._build_emoji.assert_not_called()

    def test_delete_emoji(self, cache_impl):
        mock_emoji_data = mock.Mock(
            cache.KnownCustomEmojiData,
            user_id=snowflakes.Snowflake(54123),
            guild_id=snowflakes.Snowflake(123333),
            ref_count=0,
        )
        mock_other_emoji_data = mock.Mock(cache.KnownCustomEmojiData)
        mock_emoji = mock.Mock(emojis.KnownCustomEmoji)
        emoji_ids = collections.SnowflakeSet()
        emoji_ids.add_all([snowflakes.Snowflake(12354123), snowflakes.Snowflake(432123)])
        cache_impl._emoji_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(12354123): mock_emoji_data,
                snowflakes.Snowflake(999): mock_other_emoji_data,
            }
        )
        cache_impl._guild_entries = collections.FreezableDict(
            {snowflakes.Snowflake(123333): cache.GuildRecord(emojis=emoji_ids)}
        )
        cache_impl._garbage_collect_user = mock.Mock()
        cache_impl._build_emoji = mock.Mock(return_value=mock_emoji)
        assert cache_impl.delete_emoji(snowflakes.Snowflake(12354123)) is mock_emoji
        assert cache_impl._emoji_entries == {snowflakes.Snowflake(999): mock_other_emoji_data}
        assert cache_impl._guild_entries[snowflakes.Snowflake(123333)].emojis == {snowflakes.Snowflake(432123)}
        cache_impl._build_emoji.assert_called_once_with(mock_emoji_data)
        cache_impl._garbage_collect_user.assert_called_once_with(snowflakes.Snowflake(54123), decrement=1)

    def test_delete_emoji_without_user(self, cache_impl):
        mock_emoji_data = mock.Mock(
            cache.KnownCustomEmojiData,
            ref_count=0,
            user_id=None,
            guild_id=snowflakes.Snowflake(123333),
        )
        mock_other_emoji_data = mock.Mock(cache.KnownCustomEmojiData)
        mock_emoji = mock.Mock(emojis.KnownCustomEmoji)
        emoji_ids = collections.SnowflakeSet()
        emoji_ids.add_all([snowflakes.Snowflake(12354123), snowflakes.Snowflake(432123)])
        cache_impl._emoji_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(12354123): mock_emoji_data,
                snowflakes.Snowflake(999): mock_other_emoji_data,
            }
        )
        cache_impl._guild_entries = collections.FreezableDict(
            {snowflakes.Snowflake(123333): cache.GuildRecord(emojis=emoji_ids)}
        )
        cache_impl._garbage_collect_user = mock.Mock()
        cache_impl._build_emoji = mock.Mock(return_value=mock_emoji)
        assert cache_impl.delete_emoji(snowflakes.Snowflake(12354123)) is mock_emoji
        assert cache_impl._emoji_entries == {snowflakes.Snowflake(999): mock_other_emoji_data}
        assert cache_impl._guild_entries[snowflakes.Snowflake(123333)].emojis == {snowflakes.Snowflake(432123)}
        cache_impl._build_emoji.assert_called_once_with(mock_emoji_data)
        cache_impl._garbage_collect_user.assert_not_called()

    def test_delete_emoji_for_unknown_emoji(self, cache_impl):
        cache_impl._garbage_collect_user = mock.Mock()
        cache_impl._build_emoji = mock.Mock()
        assert cache_impl.delete_emoji(snowflakes.Snowflake(12354123)) is None
        cache_impl._build_emoji.assert_not_called()
        cache_impl._garbage_collect_user.assert_not_called()

    def test_get_emoji(self, cache_impl):
        mock_emoji_data = mock.Mock(cache.KnownCustomEmojiData)
        mock_emoji = mock.Mock(emojis.KnownCustomEmoji)
        cache_impl._build_emoji = mock.Mock(return_value=mock_emoji)
        cache_impl._emoji_entries = collections.FreezableDict({snowflakes.Snowflake(3422123): mock_emoji_data})
        assert cache_impl.get_emoji(snowflakes.Snowflake(3422123)) is mock_emoji
        cache_impl._build_emoji.assert_called_once_with(mock_emoji_data)

    def test_get_emoji_with_unknown_emoji(self, cache_impl):
        cache_impl._build_emoji = mock.Mock()
        assert cache_impl.get_emoji(snowflakes.Snowflake(3422123)) is None
        cache_impl._build_emoji.assert_not_called()

    def test_get_emojis_view(self, cache_impl):
        mock_emoji_data_1 = mock.Mock(cache.KnownCustomEmojiData, user_id=snowflakes.Snowflake(43123))
        mock_emoji_data_2 = mock.Mock(cache.KnownCustomEmojiData, user_id=None)
        mock_emoji_1 = mock.Mock(emojis.KnownCustomEmoji)
        mock_emoji_2 = mock.Mock(emojis.KnownCustomEmoji)
        mock_wrapped_user = mock.Mock(cache.GenericRefWrapper[users.User])
        cache_impl._emoji_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(123123123): mock_emoji_data_1,
                snowflakes.Snowflake(43156234): mock_emoji_data_2,
            }
        )
        cache_impl._user_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(564123): mock.Mock(cache.GenericRefWrapper),
                snowflakes.Snowflake(43123): mock_wrapped_user,
            }
        )
        cache_impl._build_emoji = mock.Mock(side_effect=[mock_emoji_1, mock_emoji_2])
        assert cache_impl.get_emojis_view() == {
            snowflakes.Snowflake(123123123): mock_emoji_1,
            snowflakes.Snowflake(43156234): mock_emoji_2,
        }
        cache_impl._build_emoji.assert_has_calls(
            [
                mock.call(mock_emoji_data_1, cached_users={snowflakes.Snowflake(43123): mock_wrapped_user}),
                mock.call(mock_emoji_data_2, cached_users={snowflakes.Snowflake(43123): mock_wrapped_user}),
            ]
        )

    def test_get_emojis_view_for_guild(self, cache_impl):
        mock_emoji_data_1 = mock.Mock(cache.KnownCustomEmojiData, user_id=snowflakes.Snowflake(32124123))
        mock_emoji_data_2 = mock.Mock(cache.KnownCustomEmojiData, user_id=None)
        mock_emoji_1 = mock.Mock(emojis.KnownCustomEmoji)
        mock_emoji_2 = mock.Mock(emojis.KnownCustomEmoji)
        emoji_ids = collections.SnowflakeSet()
        emoji_ids.add_all([snowflakes.Snowflake(65123), snowflakes.Snowflake(43156234)])
        mock_wrapped_user = mock.Mock(cache.GenericRefWrapper[users.User])
        cache_impl._emoji_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(65123): mock_emoji_data_1,
                snowflakes.Snowflake(942123): mock.Mock(cache.KnownCustomEmojiData),
                snowflakes.Snowflake(43156234): mock_emoji_data_2,
            }
        )
        cache_impl._user_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(564123): mock.Mock(cache.GenericRefWrapper),
                snowflakes.Snowflake(32124123): mock_wrapped_user,
            }
        )
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(99999): mock.Mock(cache.GuildRecord),
                snowflakes.Snowflake(9342123): cache.GuildRecord(emojis=emoji_ids),
            }
        )
        cache_impl._build_emoji = mock.Mock(side_effect=[mock_emoji_1, mock_emoji_2])
        assert cache_impl.get_emojis_view_for_guild(snowflakes.Snowflake(9342123)) == {
            snowflakes.Snowflake(65123): mock_emoji_1,
            snowflakes.Snowflake(43156234): mock_emoji_2,
        }
        cache_impl._build_emoji.assert_has_calls(
            [
                mock.call(mock_emoji_data_1, cached_users={snowflakes.Snowflake(32124123): mock_wrapped_user}),
                mock.call(mock_emoji_data_2, cached_users={snowflakes.Snowflake(32124123): mock_wrapped_user}),
            ]
        )

    def test_get_emojis_view_for_guild_for_unknown_emoji_cache(self, cache_impl):
        cache_impl._emoji_entries = collections.FreezableDict(
            {snowflakes.Snowflake(9999): mock.Mock(cache.KnownCustomEmojiData)}
        )
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(99999): mock.Mock(cache.GuildRecord),
                snowflakes.Snowflake(9342123): cache.GuildRecord(),
            }
        )
        cache_impl._build_emoji = mock.Mock()
        assert cache_impl.get_emojis_view_for_guild(snowflakes.Snowflake(9342123)) == {}
        cache_impl._build_emoji.assert_not_called()

    def test_get_emojis_view_for_guild_for_unknown_record(self, cache_impl):
        cache_impl._emoji_entries = collections.FreezableDict(
            {snowflakes.Snowflake(12354345): mock.Mock(cache.KnownCustomEmojiData)}
        )
        cache_impl._guild_entries = collections.FreezableDict({snowflakes.Snowflake(9342123): cache.GuildRecord()})
        cache_impl._build_emoji = mock.Mock()
        assert cache_impl.get_emojis_view_for_guild(snowflakes.Snowflake(9342123)) == {}
        cache_impl._build_emoji.assert_not_called()

    def test_set_emoji(self, cache_impl):
        mock_user = mock.Mock(users.User, id=snowflakes.Snowflake(654234))
        emoji = emojis.KnownCustomEmoji(
            app=cache_impl._app,
            id=snowflakes.Snowflake(5123123),
            name="A name",
            guild_id=snowflakes.Snowflake(65234),
            role_ids=[snowflakes.Snowflake(213212), snowflakes.Snowflake(6873245)],
            user=mock_user,
            is_animated=False,
            is_colons_required=True,
            is_managed=True,
            is_available=False,
        )
        cache_impl.set_user = mock.Mock()
        cache_impl._increment_user_ref_count = mock.Mock()
        assert cache_impl.set_emoji(emoji) is None
        assert 65234 in cache_impl._guild_entries
        assert cache_impl._guild_entries[snowflakes.Snowflake(65234)].emojis
        assert 5123123 in cache_impl._guild_entries[snowflakes.Snowflake(65234)].emojis
        assert 5123123 in cache_impl._emoji_entries
        emoji_data = cache_impl._emoji_entries[snowflakes.Snowflake(5123123)]
        cache_impl.set_user.assert_called_once_with(mock_user)
        cache_impl._increment_user_ref_count.assert_called_once_with(snowflakes.Snowflake(654234))
        assert emoji_data.id == snowflakes.Snowflake(5123123)
        assert emoji_data.name == "A name"
        assert emoji_data.is_animated is False
        assert emoji_data.guild_id == snowflakes.Snowflake(65234)
        assert emoji_data.role_ids == (snowflakes.Snowflake(213212), snowflakes.Snowflake(6873245))
        assert isinstance(emoji_data.role_ids, tuple)
        assert emoji_data.user_id == snowflakes.Snowflake(654234)
        assert emoji_data.is_colons_required is True
        assert emoji_data.is_managed is True
        assert emoji_data.is_available is False

    def test_set_emoji_with_pre_cached_emoji(self, cache_impl):
        mock_user = mock.Mock(users.User, id=snowflakes.Snowflake(654234))
        emoji = emojis.KnownCustomEmoji(
            app=cache_impl._app,
            id=snowflakes.Snowflake(5123123),
            name="A name",
            guild_id=snowflakes.Snowflake(65234),
            role_ids=[snowflakes.Snowflake(213212), snowflakes.Snowflake(6873245)],
            user=mock_user,
            is_animated=False,
            is_colons_required=True,
            is_managed=True,
            is_available=False,
        )
        cache_impl._emoji_entries = collections.FreezableDict(
            {snowflakes.Snowflake(5123123): mock.Mock(cache.KnownCustomEmojiData)}
        )
        cache_impl.set_user = mock.Mock()
        cache_impl._increment_user_ref_count = mock.Mock()
        assert cache_impl.set_emoji(emoji) is None
        assert 5123123 in cache_impl._emoji_entries
        cache_impl.set_user.assert_called_once_with(mock_user)
        cache_impl._increment_user_ref_count.assert_not_called()

    def test_update_emoji(self, cache_impl):
        mock_cached_emoji_1 = mock.Mock(emojis.KnownCustomEmoji)
        mock_cached_emoji_2 = mock.Mock(emojis.KnownCustomEmoji)
        mock_emoji = mock.Mock(emojis.KnownCustomEmoji, id=snowflakes.Snowflake(54123123))
        cache_impl.get_emoji = mock.Mock(side_effect=[mock_cached_emoji_1, mock_cached_emoji_2])
        cache_impl.set_emoji = mock.Mock()
        assert cache_impl.update_emoji(mock_emoji) == (mock_cached_emoji_1, mock_cached_emoji_2)
        cache_impl.get_emoji.assert_has_calls(
            [mock.call(snowflakes.Snowflake(54123123)), mock.call(snowflakes.Snowflake(54123123))]
        )
        cache_impl.set_emoji.assert_called_once_with(mock_emoji)

    def test_clear_guilds_when_no_guilds_cached(self, cache_impl):
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(423123): cache.GuildRecord(),
                snowflakes.Snowflake(675345): cache.GuildRecord(),
            }
        )
        assert cache_impl.clear_guilds() == {}
        assert cache_impl._guild_entries == {
            snowflakes.Snowflake(423123): cache.GuildRecord(),
            snowflakes.Snowflake(675345): cache.GuildRecord(),
        }

    def test_clear_guilds(self, cache_impl):
        mock_guild_1 = mock.MagicMock(guilds.GatewayGuild)
        mock_guild_2 = mock.MagicMock(guilds.GatewayGuild)
        mock_member = mock.MagicMock(guilds.Member)
        mock_guild_3 = mock.MagicMock(guilds.GatewayGuild)
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(423123): cache.GuildRecord(),
                snowflakes.Snowflake(675345): cache.GuildRecord(guild=mock_guild_1),
                snowflakes.Snowflake(32142): cache.GuildRecord(
                    guild=mock_guild_2,
                    members=collections.FreezableDict({snowflakes.Snowflake(3241123): mock_member}),
                ),
                snowflakes.Snowflake(765345): cache.GuildRecord(guild=mock_guild_3),
                snowflakes.Snowflake(321132): cache.GuildRecord(),
            }
        )
        assert cache_impl.clear_guilds() == {675345: mock_guild_1, 32142: mock_guild_2, 765345: mock_guild_3}
        assert cache_impl._guild_entries == {
            snowflakes.Snowflake(423123): cache.GuildRecord(),
            snowflakes.Snowflake(32142): cache.GuildRecord(members={snowflakes.Snowflake(3241123): mock_member}),
            snowflakes.Snowflake(321132): cache.GuildRecord(),
        }

    def test_delete_guild_for_known_guild(self, cache_impl):
        mock_guild = mock.Mock(guilds.GatewayGuild)
        mock_member = mock.Mock(guilds.Member)
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(354123): cache.GuildRecord(),
                snowflakes.Snowflake(543123): cache.GuildRecord(
                    guild=mock_guild,
                    is_available=True,
                    members=collections.FreezableDict({snowflakes.Snowflake(43123): mock_member}),
                ),
            }
        )
        assert cache_impl.delete_guild(snowflakes.Snowflake(543123)) is mock_guild
        assert cache_impl._guild_entries == {
            snowflakes.Snowflake(354123): cache.GuildRecord(),
            snowflakes.Snowflake(543123): cache.GuildRecord(members={snowflakes.Snowflake(43123): mock_member}),
        }

    def test_delete_guild_for_removes_emptied_record(self, cache_impl):
        mock_guild = mock.Mock(guilds.GatewayGuild)
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(354123): cache.GuildRecord(),
                snowflakes.Snowflake(543123): cache.GuildRecord(guild=mock_guild, is_available=True),
            }
        )
        assert cache_impl.delete_guild(snowflakes.Snowflake(543123)) is mock_guild
        assert cache_impl._guild_entries == {snowflakes.Snowflake(354123): cache.GuildRecord()}

    def test_delete_guild_for_unknown_guild(self, cache_impl):
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(354123): cache.GuildRecord(),
                snowflakes.Snowflake(543123): cache.GuildRecord(),
            }
        )
        assert cache_impl.delete_guild(snowflakes.Snowflake(543123)) is None
        assert cache_impl._guild_entries == {
            snowflakes.Snowflake(354123): cache.GuildRecord(),
            snowflakes.Snowflake(543123): cache.GuildRecord(),
        }

    def test_delete_guild_for_unknown_record(self, cache_impl):
        cache_impl._guild_entries = collections.FreezableDict({snowflakes.Snowflake(354123): cache.GuildRecord()})
        assert cache_impl.delete_guild(snowflakes.Snowflake(543123)) is None
        assert cache_impl._guild_entries == {snowflakes.Snowflake(354123): cache.GuildRecord()}

    def test_get_guild_first_tries_get_available_guilds(self, cache_impl):
        mock_guild = mock.MagicMock(guilds.GatewayGuild)
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(54234123): cache.GuildRecord(),
                snowflakes.Snowflake(543123): cache.GuildRecord(guild=mock_guild, is_available=True),
            }
        )
        cached_guild = cache_impl.get_guild(snowflakes.Snowflake(543123))
        assert cached_guild == mock_guild
        assert cache_impl is not mock_guild

    def test_get_guild_then_tries_get_unavailable_guilds(self, cache_impl):
        mock_guild = mock.MagicMock(guilds.GatewayGuild)
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(543123): cache.GuildRecord(is_available=True),
                snowflakes.Snowflake(54234123): cache.GuildRecord(guild=mock_guild, is_available=False),
            }
        )
        cached_guild = cache_impl.get_guild(snowflakes.Snowflake(54234123))
        assert cached_guild == mock_guild
        assert cache_impl is not mock_guild

    def test_get_available_guild_for_known_guild_when_available(self, cache_impl):
        mock_guild = mock.MagicMock(guilds.GatewayGuild)
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(54234123): cache.GuildRecord(),
                snowflakes.Snowflake(543123): cache.GuildRecord(guild=mock_guild, is_available=True),
            }
        )
        cached_guild = cache_impl.get_available_guild(snowflakes.Snowflake(543123))
        assert cached_guild == mock_guild
        assert cache_impl is not mock_guild

    def test_get_available_guild_for_known_guild_when_unavailable(self, cache_impl):
        mock_guild = mock.Mock(guilds.GatewayGuild)
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(54234123): cache.GuildRecord(),
                snowflakes.Snowflake(543123): cache.GuildRecord(guild=mock_guild, is_available=False),
            }
        )

        result = cache_impl.get_available_guild(snowflakes.Snowflake(543123))

        assert result is None

    def test_get_available_guild_for_unknown_guild(self, cache_impl):
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(54234123): cache.GuildRecord(),
                snowflakes.Snowflake(543123): cache.GuildRecord(),
            }
        )
        assert cache_impl.get_available_guild(snowflakes.Snowflake(543123)) is None

    def test_get_available_guild_for_unknown_guild_record(self, cache_impl):
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(54234123): cache.GuildRecord(),
            }
        )
        assert cache_impl.get_available_guild(snowflakes.Snowflake(543123)) is None

    def test_get_unavailable_guild_for_known_guild_when_unavailable(self, cache_impl):
        mock_guild = mock.MagicMock(guilds.GatewayGuild)
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(54234123): cache.GuildRecord(),
                snowflakes.Snowflake(452131): cache.GuildRecord(guild=mock_guild, is_available=False),
            }
        )
        cached_guild = cache_impl.get_unavailable_guild(snowflakes.Snowflake(452131))
        assert cached_guild == mock_guild
        assert cache_impl is not mock_guild

    def test_get_unavailable_guild_for_known_guild_when_available(self, cache_impl):
        mock_guild = mock.Mock(guilds.GatewayGuild)
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(54234123): cache.GuildRecord(),
                snowflakes.Snowflake(654234): cache.GuildRecord(guild=mock_guild, is_available=True),
            }
        )

        result = cache_impl.get_unavailable_guild(snowflakes.Snowflake(654234))

        assert result is None

    def test_get_unavailable_guild_for_unknown_guild(self, cache_impl):
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(54234123): cache.GuildRecord(),
                snowflakes.Snowflake(543123): cache.GuildRecord(),
            }
        )
        assert cache_impl.get_unavailable_guild(snowflakes.Snowflake(543123)) is None

    def test_get_unavailable_guild_for_unknown_guild_record(self, cache_impl):
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(54234123): cache.GuildRecord(),
            }
        )
        assert cache_impl.get_unavailable_guild(snowflakes.Snowflake(543123)) is None

    def test_get_available_guilds_view(self, cache_impl):
        mock_guild_1 = mock.MagicMock(guilds.GatewayGuild)
        mock_guild_2 = mock.MagicMock(guilds.GatewayGuild)
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(4312312): cache.GuildRecord(guild=mock_guild_1, is_available=True),
                snowflakes.Snowflake(34123): cache.GuildRecord(),
                snowflakes.Snowflake(73453): cache.GuildRecord(guild=mock_guild_2, is_available=True),
                snowflakes.Snowflake(6554234): cache.GuildRecord(guild=object(), is_available=False),
            }
        )
        assert cache_impl.get_available_guilds_view() == {
            snowflakes.Snowflake(4312312): mock_guild_1,
            snowflakes.Snowflake(73453): mock_guild_2,
        }

    def test_get_available_guilds_view_when_no_guilds_cached(self, cache_impl):
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(4312312): cache.GuildRecord(),
                snowflakes.Snowflake(34123): cache.GuildRecord(),
                snowflakes.Snowflake(73453): cache.GuildRecord(),
            }
        )
        assert cache_impl.get_available_guilds_view() == {}

    def test_get_unavailable_guilds_view(self, cache_impl):
        mock_guild_1 = mock.MagicMock(guilds.GatewayGuild)
        mock_guild_2 = mock.MagicMock(guilds.GatewayGuild)
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(4312312): cache.GuildRecord(guild=mock_guild_1, is_available=False),
                snowflakes.Snowflake(34123): cache.GuildRecord(),
                snowflakes.Snowflake(73453): cache.GuildRecord(guild=mock_guild_2, is_available=False),
                snowflakes.Snowflake(6554234): cache.GuildRecord(guild=object(), is_available=True),
            }
        )
        assert cache_impl.get_unavailable_guilds_view() == {
            snowflakes.Snowflake(4312312): mock_guild_1,
            snowflakes.Snowflake(73453): mock_guild_2,
        }

    def test_get_unavailable_guilds_view_when_no_guilds_cached(self, cache_impl):
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(4312312): cache.GuildRecord(),
                snowflakes.Snowflake(34123): cache.GuildRecord(),
                snowflakes.Snowflake(73453): cache.GuildRecord(),
            }
        )
        assert cache_impl.get_unavailable_guilds_view() == {}

    def test_set_guild(self, cache_impl):
        mock_guild = mock.MagicMock(guilds.GatewayGuild, id=snowflakes.Snowflake(5123123))
        assert cache_impl.set_guild(mock_guild) is None
        assert 5123123 in cache_impl._guild_entries
        assert cache_impl._guild_entries[snowflakes.Snowflake(5123123)].guild == mock_guild
        assert cache_impl._guild_entries[snowflakes.Snowflake(5123123)].guild is not mock_guild
        assert cache_impl._guild_entries[snowflakes.Snowflake(5123123)].is_available is True

    def test_set_guild_availability_for_cached_guild(self, cache_impl):
        cache_impl._guild_entries = {snowflakes.Snowflake(43123): cache.GuildRecord(guild=object())}
        assert cache_impl.set_guild_availability(snowflakes.Snowflake(43123), True) is None
        assert cache_impl._guild_entries[snowflakes.Snowflake(43123)].is_available is True

    def test_set_guild_availability_for_uncached_guild(self, cache_impl):
        assert cache_impl.set_guild_availability(snowflakes.Snowflake(452234123), True) is None
        assert 452234123 not in cache_impl._guild_entries

    @pytest.mark.skip(reason="TODO")
    def test_update_guild(self, cache_impl):
        ...

    @pytest.mark.skip(reason="TODO")
    def test_clear_guild_channels(self, cache_impl):
        ...

    @pytest.mark.skip(reason="TODO")
    def test_clear_guild_channels_for_guild(self, cache_impl):
        ...

    @pytest.mark.skip(reason="TODO")
    def test_delete_guild_channel(self, cache_impl):
        ...

    @pytest.mark.skip(reason="TODO")
    def test_get_guild_channel(self, cache_impl):
        ...

    @pytest.mark.skip(reason="TODO")
    def test_get_guild_channels_view(self, cache_impl):
        ...

    @pytest.mark.skip(reason="TODO")
    def test_get_guild_channels_view_for_guild(self, cache_impl):
        ...

    @pytest.mark.skip(reason="TODO")
    def test_set_guild_channel(self, cache_impl):
        ...

    @pytest.mark.skip(reason="TODO")
    def test_update_guild_channel(self, cache_impl):
        ...

    def test__build_invite(self, cache_impl):
        invite_data = cache.InviteData(
            code="okokok",
            guild_id=snowflakes.Snowflake(965234),
            channel_id=snowflakes.Snowflake(87345234),
            inviter_id=snowflakes.Snowflake(123123),
            target_user_id=snowflakes.Snowflake(9543453),
            target_user_type=invites.TargetUserType.STREAM,
            uses=42,
            max_uses=999,
            max_age=datetime.timedelta(days=7),
            is_temporary=True,
            created_at=datetime.datetime(2020, 7, 30, 7, 22, 9, 550233, tzinfo=datetime.timezone.utc),
        )
        mock_inviter = mock.MagicMock(users.User)
        mock_target_user = mock.MagicMock(users.User)
        cache_impl._user_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(123123): cache.GenericRefWrapper(object=mock_inviter),
                snowflakes.Snowflake(9999): mock.Mock(cache.GenericRefWrapper),
                snowflakes.Snowflake(9543453): cache.GenericRefWrapper(object=mock_target_user),
            }
        )
        invite = cache_impl._build_invite(invite_data)
        assert invite.app is cache_impl._app
        assert invite.code == "okokok"
        assert invite.guild is None
        assert invite.guild_id == snowflakes.Snowflake(965234)
        assert invite.channel is None
        assert invite.channel_id == snowflakes.Snowflake(87345234)
        assert invite.inviter == mock_inviter
        assert invite.target_user == mock_target_user
        assert invite.inviter is not mock_inviter
        assert invite.target_user is not mock_target_user
        assert invite.target_user_type is invites.TargetUserType.STREAM
        assert invite.approximate_active_member_count is None
        assert invite.approximate_member_count is None
        assert invite.uses == 42
        assert invite.max_uses == 999
        assert invite.max_age == datetime.timedelta(days=7)
        assert invite.is_temporary is True
        assert invite.created_at == datetime.datetime(2020, 7, 30, 7, 22, 9, 550233, tzinfo=datetime.timezone.utc)

    def test__build_invite_with_passed_through_members(self, cache_impl):
        invite_data = cache.InviteData(
            code="okokok",
            guild_id=snowflakes.Snowflake(965234),
            channel_id=snowflakes.Snowflake(87345234),
            inviter_id=snowflakes.Snowflake(123123),
            target_user_id=snowflakes.Snowflake(9543453),
            target_user_type=invites.TargetUserType.STREAM,
            uses=42,
            max_uses=999,
            max_age=datetime.timedelta(days=7),
            is_temporary=True,
            created_at=datetime.datetime(2020, 7, 30, 7, 22, 9, 550233, tzinfo=datetime.timezone.utc),
        )
        mock_inviter = mock.MagicMock(users.User)
        mock_target_user = mock.MagicMock(users.User)
        invite = cache_impl._build_invite(
            invite_data,
            {
                snowflakes.Snowflake(123123): cache.GenericRefWrapper(object=mock_inviter),
                snowflakes.Snowflake(9543453): cache.GenericRefWrapper(object=mock_target_user),
            },
        )
        assert invite.inviter == mock_inviter
        assert invite.target_user == mock_target_user
        assert invite.inviter is not mock_inviter
        assert invite.target_user is not mock_target_user

    def test_clear_invites(self, cache_impl):
        mock_invite_data_1 = mock.Mock(
            cache.InviteData,
            target_user_id=snowflakes.Snowflake(5341231),
            inviter_id=snowflakes.Snowflake(12354123),
        )
        mock_invite_data_2 = mock.Mock(
            cache.InviteData,
            target_user_id=None,
            inviter_id=None,
        )
        mock_invite_1 = mock.Mock(invites.InviteWithMetadata)
        mock_invite_2 = mock.Mock(invites.InviteWithMetadata)
        mock_wrapped_target_user = mock.Mock(cache.GenericRefWrapper[users.User], ref_count=5)
        mock_wrapped_inviter = mock.Mock(cache.GenericRefWrapper[users.User], ref_count=3)
        cache_impl._invite_entries = collections.FreezableDict(
            {
                "hiBye": mock_invite_data_1,
                "Lblalbla": mock_invite_data_2,
            }
        )
        cache_impl._user_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(5341231): mock_wrapped_target_user,
                snowflakes.Snowflake(12354123): mock_wrapped_inviter,
                snowflakes.Snowflake(65345352): mock.Mock(cache.GenericRefWrapper),
            }
        )
        cache_impl._build_invite = mock.Mock(side_effect=[mock_invite_1, mock_invite_2])
        assert cache_impl.clear_invites() == {
            "hiBye": mock_invite_1,
            "Lblalbla": mock_invite_2,
        }
        assert cache_impl._invite_entries == {}
        cache_impl._build_invite.assert_has_calls(
            [
                mock.call(
                    mock_invite_data_1,
                    cached_users={
                        snowflakes.Snowflake(5341231): mock_wrapped_target_user,
                        snowflakes.Snowflake(12354123): mock_wrapped_inviter,
                    },
                ),
                mock.call(
                    mock_invite_data_2,
                    cached_users={
                        snowflakes.Snowflake(5341231): mock_wrapped_target_user,
                        snowflakes.Snowflake(12354123): mock_wrapped_inviter,
                    },
                ),
            ]
        )

    def test_clear_invites_for_guild(self, cache_impl):
        mock_invite_data_1 = mock.Mock(
            cache.InviteData,
            target_user_id=snowflakes.Snowflake(5341231),
            inviter_id=snowflakes.Snowflake(12354123),
        )
        mock_invite_data_2 = mock.Mock(
            cache.InviteData,
            target_user_id=None,
            inviter_id=None,
        )
        mock_other_invite_data = mock.Mock(cache.InviteData)
        mock_invite_1 = mock.Mock(invites.InviteWithMetadata)
        mock_invite_2 = mock.Mock(invites.InviteWithMetadata)
        mock_wrapped_target_user = mock.Mock(cache.GenericRefWrapper[users.User], ref_count=4)
        mock_wrapped_inviter = mock.Mock(cache.GenericRefWrapper[users.User], ref_count=42)
        cache_impl._invite_entries = collections.FreezableDict(
            {
                "oeoeoeoeooe": mock_invite_data_1,
                "owowowowoowowow": mock_invite_data_2,
                "oeoeoeoeoeoeoe": mock_other_invite_data,
            }
        )
        cache_impl._user_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(5341231): mock_wrapped_target_user,
                snowflakes.Snowflake(12354123): mock_wrapped_inviter,
                snowflakes.Snowflake(65345352): mock.Mock(cache.GenericRefWrapper),
            }
        )
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(54123): mock.Mock(cache.GuildRecord),
                snowflakes.Snowflake(999888777): cache.GuildRecord(invites=["oeoeoeoeooe", "owowowowoowowow"]),
            }
        )
        cache_impl._build_invite = mock.Mock(side_effect=[mock_invite_1, mock_invite_2])
        assert cache_impl.clear_invites_for_guild(snowflakes.Snowflake(999888777)) == {
            "oeoeoeoeooe": mock_invite_1,
            "owowowowoowowow": mock_invite_2,
        }
        assert cache_impl._invite_entries == {"oeoeoeoeoeoeoe": mock_other_invite_data}
        cache_impl._build_invite.assert_has_calls(
            [
                mock.call(
                    mock_invite_data_1,
                    cached_users={
                        snowflakes.Snowflake(5341231): mock_wrapped_target_user,
                        snowflakes.Snowflake(12354123): mock_wrapped_inviter,
                    },
                ),
                mock.call(
                    mock_invite_data_2,
                    cached_users={
                        snowflakes.Snowflake(5341231): mock_wrapped_target_user,
                        snowflakes.Snowflake(12354123): mock_wrapped_inviter,
                    },
                ),
            ]
        )

    def test_clear_invites_for_guild_unknown_invite_cache(self, cache_impl):
        mock_other_invite_data = mock.Mock(cache.InviteData)
        cache_impl._invite_entries = {
            "oeoeoeoeoeoeoe": mock_other_invite_data,
        }
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(54123): mock.Mock(cache.GuildRecord),
                snowflakes.Snowflake(999888777): cache.GuildRecord(invites=None),
            }
        )
        cache_impl._build_invite = mock.Mock()
        assert cache_impl.clear_invites_for_guild(snowflakes.Snowflake(765234123)) == {}
        assert cache_impl._invite_entries == {"oeoeoeoeoeoeoe": mock_other_invite_data}
        cache_impl._build_invite.assert_not_called()

    def test_clear_invites_for_guild_unknown_record(self, cache_impl):
        mock_other_invite_data = mock.Mock(cache.InviteData)
        cache_impl._invite_entries = collections.FreezableDict(
            {
                "oeoeoeoeoeoeoe": mock_other_invite_data,
            }
        )
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(54123): mock.Mock(cache.GuildRecord),
            }
        )
        cache_impl._build_invite = mock.Mock()
        assert cache_impl.clear_invites_for_guild(snowflakes.Snowflake(765234123)) == {}
        assert cache_impl._invite_entries == {"oeoeoeoeoeoeoe": mock_other_invite_data}
        cache_impl._build_invite.assert_not_called()

    def test_clear_invites_for_channel(self, cache_impl):
        mock_invite_data_1 = mock.Mock(
            cache.InviteData,
            target_user_id=snowflakes.Snowflake(5341231),
            inviter_id=snowflakes.Snowflake(12354123),
            channel_id=snowflakes.Snowflake(34123123),
        )
        mock_invite_data_2 = mock.Mock(
            cache.InviteData,
            target_user_id=None,
            inviter_id=None,
            channel_id=snowflakes.Snowflake(34123123),
        )
        mock_other_invite_data = mock.Mock(cache.InviteData, channel_id=snowflakes.Snowflake(9484732))
        mock_other_invite_data_2 = mock.Mock(cache.InviteData)
        mock_invite_1 = mock.Mock(invites.InviteWithMetadata)
        mock_invite_2 = mock.Mock(invites.InviteWithMetadata)
        mock_wrapped_target_user = mock.Mock(cache.GenericRefWrapper[users.User], ref_count=42)
        mock_wrapped_inviter = mock.Mock(cache.GenericRefWrapper[users.User], ref_count=280)
        cache_impl._invite_entries = collections.FreezableDict(
            {
                "oeoeoeoeooe": mock_invite_data_1,
                "owowowowoowowow": mock_invite_data_2,
                "oeoeoeoeoeoeoe": mock_other_invite_data,
                "oeo": mock_other_invite_data_2,
            }
        )
        cache_impl._user_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(5341231): mock_wrapped_target_user,
                snowflakes.Snowflake(12354123): mock_wrapped_inviter,
                snowflakes.Snowflake(65345352): mock.Mock(cache.GenericRefWrapper),
            }
        )
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(54123): mock.Mock(cache.GuildRecord),
                snowflakes.Snowflake(999888777): cache.GuildRecord(
                    invites=["oeoeoeoeooe", "owowowowoowowow", "oeoeoeoeoeoeoe"]
                ),
            }
        )
        cache_impl._build_invite = mock.Mock(side_effect=[mock_invite_1, mock_invite_2])
        assert cache_impl.clear_invites_for_channel(
            snowflakes.Snowflake(999888777), snowflakes.Snowflake(34123123)
        ) == {
            "oeoeoeoeooe": mock_invite_1,
            "owowowowoowowow": mock_invite_2,
        }
        assert cache_impl._guild_entries[snowflakes.Snowflake(999888777)].invites == ["oeoeoeoeoeoeoe"]
        assert cache_impl._invite_entries == {
            "oeoeoeoeoeoeoe": mock_other_invite_data,
            "oeo": mock_other_invite_data_2,
        }

        cache_impl._build_invite.assert_has_calls(
            [
                mock.call(
                    mock_invite_data_1,
                    cached_users={
                        snowflakes.Snowflake(5341231): mock_wrapped_target_user,
                        snowflakes.Snowflake(12354123): mock_wrapped_inviter,
                    },
                ),
                mock.call(
                    mock_invite_data_2,
                    cached_users={
                        snowflakes.Snowflake(5341231): mock_wrapped_target_user,
                        snowflakes.Snowflake(12354123): mock_wrapped_inviter,
                    },
                ),
            ]
        )

    def test_clear_invites_for_channel_unknown_invite_cache(self, cache_impl):
        mock_other_invite_data = mock.Mock(cache.InviteData)
        cache_impl._invite_entries = collections.FreezableDict(
            {
                "oeoeoeoeoeoeoe": mock_other_invite_data,
            }
        )
        cache_impl._user_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(65345352): mock.Mock(cache.GenericRefWrapper),
            }
        )
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(54123): mock.Mock(cache.GuildRecord),
                snowflakes.Snowflake(999888777): cache.GuildRecord(invites=None),
            }
        )
        cache_impl._build_invite = mock.Mock()
        assert (
            cache_impl.clear_invites_for_channel(snowflakes.Snowflake(765234123), snowflakes.Snowflake(12365345)) == {}
        )
        assert cache_impl._invite_entries == {"oeoeoeoeoeoeoe": mock_other_invite_data}
        cache_impl._build_invite.assert_not_called()

    def test_clear_invites_for_channel_unknown_record(self, cache_impl):
        mock_other_invite_data = mock.Mock(cache.InviteData)
        cache_impl._invite_entries = collections.FreezableDict(
            {
                "oeoeoeoeoeoeoe": mock_other_invite_data,
            }
        )
        cache_impl._user_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(65345352): mock.Mock(cache.GenericRefWrapper),
            }
        )
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(54123): mock.Mock(cache.GuildRecord),
            }
        )
        cache_impl._build_invite = mock.Mock()
        assert (
            cache_impl.clear_invites_for_channel(snowflakes.Snowflake(765234123), snowflakes.Snowflake(76234123)) == {}
        )
        assert cache_impl._invite_entries == {"oeoeoeoeoeoeoe": mock_other_invite_data}
        cache_impl._build_invite.assert_not_called()

    def test_delete_invite(self, cache_impl):
        mock_invite_data = mock.Mock(cache.InviteData)
        mock_other_invite_data = mock.Mock(cache.InviteData)
        mock_invite = mock.Mock(
            invites.InviteWithMetadata,
            inviter=mock.Mock(users.User, id=snowflakes.Snowflake(543123)),
            target_user=mock.Mock(users.User, id=snowflakes.Snowflake(9191919)),
            guild_id=snowflakes.Snowflake(999999999),
        )
        cache_impl._invite_entries = collections.FreezableDict(
            {"blamSpat": mock_other_invite_data, "oooooooooooooo": mock_invite_data}
        )
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(1234312): mock.Mock(cache.GuildRecord),
                snowflakes.Snowflake(999999999): cache.GuildRecord(invites=["ok", "blat", "oooooooooooooo"]),
            }
        )
        cache_impl._build_invite = mock.Mock(return_value=mock_invite)
        cache_impl._garbage_collect_user = mock.Mock()
        cache_impl._remove_guild_record_if_empty = mock.Mock()
        assert cache_impl.delete_invite("oooooooooooooo") is mock_invite
        cache_impl._build_invite.assert_called_once_with(mock_invite_data)
        cache_impl._garbage_collect_user.assert_has_calls(
            [
                mock.call(snowflakes.Snowflake(543123), decrement=1),
                mock.call(snowflakes.Snowflake(9191919), decrement=1),
            ]
        )
        assert cache_impl._invite_entries == {
            "blamSpat": mock_other_invite_data,
        }
        assert cache_impl._guild_entries[snowflakes.Snowflake(999999999)].invites == ["ok", "blat"]

    def test_delete_invite_when_guild_id_is_None(self, cache_impl):
        mock_invite_data = mock.Mock(cache.InviteData)
        mock_other_invite_data = mock.Mock(cache.InviteData)
        mock_invite = mock.Mock(invites.InviteWithMetadata, inviter=None, target_user=None, guild_id=None)
        cache_impl._invite_entries = collections.FreezableDict(
            {"blamSpat": mock_other_invite_data, "oooooooooooooo": mock_invite_data}
        )
        cache_impl._build_invite = mock.Mock(return_value=mock_invite)
        cache_impl._garbage_collect_user = mock.Mock()
        cache_impl._remove_guild_record_if_empty = mock.Mock()
        assert cache_impl.delete_invite("oooooooooooooo") is mock_invite
        cache_impl._build_invite.assert_called_once_with(mock_invite_data)
        cache_impl._remove_guild_record_if_empty.assert_not_called()
        assert cache_impl._invite_entries == {"blamSpat": mock_other_invite_data}

    def test_delete_invite_without_users(self, cache_impl):
        mock_invite_data = mock.Mock(cache.InviteData)
        mock_other_invite_data = mock.Mock(cache.InviteData)
        mock_invite = mock.Mock(
            invites.InviteWithMetadata, inviter=None, target_user=None, guild_id=snowflakes.Snowflake(999999999)
        )
        cache_impl._invite_entries = collections.FreezableDict(
            {"blamSpat": mock_other_invite_data, "oooooooooooooo": mock_invite_data}
        )
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(1234312): mock.Mock(cache.GuildRecord),
                snowflakes.Snowflake(999999999): cache.GuildRecord(invites=["ok", "blat", "oooooooooooooo"]),
            }
        )
        cache_impl._build_invite = mock.Mock(return_value=mock_invite)
        cache_impl._garbage_collect_user = mock.Mock()
        cache_impl._remove_guild_record_if_empty = mock.Mock()
        assert cache_impl.delete_invite("oooooooooooooo") is mock_invite
        cache_impl._build_invite.assert_called_once_with(mock_invite_data)
        cache_impl._garbage_collect_user.assert_not_called()
        assert cache_impl._invite_entries == {
            "blamSpat": mock_other_invite_data,
        }
        assert cache_impl._guild_entries[snowflakes.Snowflake(999999999)].invites == ["ok", "blat"]

    def test_delete_invite_for_unknown_invite(self, cache_impl):
        cache_impl._build_invite = mock.Mock()
        cache_impl._garbage_collect_user = mock.Mock()
        cache_impl._remove_guild_record_if_empty = mock.Mock()
        assert cache_impl.delete_invite("oooooooooooooo") is None
        cache_impl._build_invite.assert_not_called()
        cache_impl._garbage_collect_user.assert_not_called()

    def test_get_invite(self, cache_impl):
        mock_invite_data = mock.Mock(cache.InviteData)
        mock_invite = mock.Mock(invites.InviteWithMetadata)
        cache_impl._build_invite = mock.Mock(return_value=mock_invite)
        cache_impl._invite_entries = collections.FreezableDict(
            {"blam": mock.Mock(cache.InviteData), "okokok": mock_invite_data}
        )
        assert cache_impl.get_invite("okokok") is mock_invite
        cache_impl._build_invite.assert_called_once_with(mock_invite_data)

    def test_get_invite_for_unknown_invite(self, cache_impl):
        cache_impl._build_invite = mock.Mock()
        cache_impl._invite_entries = collections.FreezableDict(
            {
                "blam": mock.Mock(cache.InviteData),
            }
        )
        assert cache_impl.get_invite("okokok") is None
        cache_impl._build_invite.assert_not_called()

    def test_get_invites_view(self, cache_impl):
        mock_invite_data_1 = mock.Mock(
            cache.InviteData,
            inviter_id=snowflakes.Snowflake(987),
            target_user_id=snowflakes.Snowflake(34123),
        )
        mock_invite_data_2 = mock.Mock(cache.InviteData, inviter_id=None, target_user_id=None)
        mock_invite_1 = mock.Mock(invites.InviteWithMetadata)
        mock_invite_2 = mock.Mock(invites.InviteWithMetadata)
        mock_wrapped_inviter = mock.Mock(cache.GenericRefWrapper[users.User])
        mock_wrapped_target_user = mock.Mock(cache.GenericRefWrapper[users.User])
        cache_impl._user_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(987): mock_wrapped_inviter,
                snowflakes.Snowflake(34123): mock_wrapped_target_user,
                snowflakes.Snowflake(6599): mock.Mock(cache.GenericRefWrapper),
            }
        )
        cache_impl._invite_entries = collections.FreezableDict(
            {"okok": mock_invite_data_1, "blamblam": mock_invite_data_2}
        )
        cache_impl._build_invite = mock.Mock(side_effect=[mock_invite_1, mock_invite_2])
        assert cache_impl.get_invites_view() == {"okok": mock_invite_1, "blamblam": mock_invite_2}
        cache_impl._build_invite.assert_has_calls(
            [
                mock.call(
                    mock_invite_data_1,
                    cached_users={
                        snowflakes.Snowflake(987): mock_wrapped_inviter,
                        snowflakes.Snowflake(34123): mock_wrapped_target_user,
                    },
                ),
                mock.call(
                    mock_invite_data_2,
                    cached_users={
                        snowflakes.Snowflake(987): mock_wrapped_inviter,
                        snowflakes.Snowflake(34123): mock_wrapped_target_user,
                    },
                ),
            ]
        )

    def test_get_invites_view_for_guild(self, cache_impl):
        mock_invite_data_1 = mock.Mock(
            cache.InviteData,
            inviter_id=snowflakes.Snowflake(987),
            target_user_id=snowflakes.Snowflake(34123),
        )
        mock_invite_data_2 = mock.Mock(cache.InviteData, inviter_id=None, target_user_id=None)
        mock_invite_1 = mock.Mock(invites.InviteWithMetadata)
        mock_invite_2 = mock.Mock(invites.InviteWithMetadata)
        mock_wrapped_inviter = mock.Mock(cache.GenericRefWrapper[users.User])
        mock_wrapped_target_user = mock.Mock(cache.GenericRefWrapper[users.User])
        cache_impl._user_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(987): mock_wrapped_inviter,
                snowflakes.Snowflake(34123): mock_wrapped_target_user,
                snowflakes.Snowflake(6599): mock.Mock(cache.GenericRefWrapper),
            }
        )
        cache_impl._invite_entries = collections.FreezableDict(
            {
                "okok": mock_invite_data_1,
                "dsaytert": mock_invite_data_2,
                "bitsbits ": mock.Mock(cache.InviteData),
            }
        )
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(9544994): mock.Mock(cache.GuildRecord),
                snowflakes.Snowflake(4444444): cache.GuildRecord(invites=["okok", "dsaytert"]),
            }
        )
        cache_impl._build_invite = mock.Mock(side_effect=[mock_invite_1, mock_invite_2])
        assert cache_impl.get_invites_view_for_guild(snowflakes.Snowflake(4444444)) == {
            "okok": mock_invite_1,
            "dsaytert": mock_invite_2,
        }
        cache_impl._build_invite.assert_has_calls(
            [
                mock.call(
                    mock_invite_data_1,
                    cached_users={
                        snowflakes.Snowflake(987): mock_wrapped_inviter,
                        snowflakes.Snowflake(34123): mock_wrapped_target_user,
                    },
                ),
                mock.call(
                    mock_invite_data_2,
                    cached_users={
                        snowflakes.Snowflake(987): mock_wrapped_inviter,
                        snowflakes.Snowflake(34123): mock_wrapped_target_user,
                    },
                ),
            ]
        )

    def test_get_invites_view_for_guild_unknown_emoji_cache(self, cache_impl):
        cache_impl._invite_entries = collections.FreezableDict(
            {
                "okok": mock.Mock(cache.InviteData),
                "dsaytert": mock.Mock(cache.InviteData),
            }
        )
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(9544994): mock.Mock(cache.GuildRecord),
                snowflakes.Snowflake(4444444): cache.GuildRecord(invites=None),
            }
        )
        cache_impl._build_invite = mock.Mock()
        assert cache_impl.get_invites_view_for_guild(snowflakes.Snowflake(4444444)) == {}
        cache_impl._build_invite.assert_not_called()

    def test_get_invites_view_for_guild_unknown_record(self, cache_impl):
        cache_impl._invite_entries = collections.FreezableDict(
            {
                "okok": mock.Mock(cache.InviteData),
                "dsaytert": mock.Mock(cache.InviteData),
            }
        )
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(9544994): mock.Mock(cache.GuildRecord),
            }
        )
        cache_impl._build_invite = mock.Mock()
        assert cache_impl.get_invites_view_for_guild(snowflakes.Snowflake(4444444)) == {}
        cache_impl._build_invite.assert_not_called()

    def test_get_invites_view_for_channel(self, cache_impl):
        mock_invite_data_1 = mock.Mock(
            inviter_id=snowflakes.Snowflake(4312365),
            target_user_id=snowflakes.Snowflake(65643213),
            channel_id=snowflakes.Snowflake(987987),
        )
        mock_invite_data_2 = mock.Mock(inviter_id=None, target_user_id=None, channel_id=snowflakes.Snowflake(987987))
        mock_invite_1 = mock.Mock(invites.InviteWithMetadata)
        mock_invite_2 = mock.Mock(invites.InviteWithMetadata)
        mock_wrapped_inviter = mock.Mock(cache.GenericRefWrapper[users.User])
        mock_wrapped_target_user = mock.Mock(cache.GenericRefWrapper[users.User])
        cache_impl._user_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(4312365): mock_wrapped_inviter,
                snowflakes.Snowflake(65643213): mock_wrapped_target_user,
                snowflakes.Snowflake(999875673): mock.Mock(cache.GenericRefWrapper),
            }
        )
        cache_impl._invite_entries = collections.FreezableDict(
            {
                "blamBang": mock_invite_data_1,
                "bingBong": mock_invite_data_2,
                "Pop": mock.Mock(cache.InviteData, channel_id=snowflakes.Snowflake(94934923)),
                "Fam": mock.Mock(cache.InviteData, channel_id=snowflakes.Snowflake(2123)),
            }
        )
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(31423): mock.Mock(cache.GuildRecord),
                snowflakes.Snowflake(83452134): cache.GuildRecord(invites=["blamBang", "bingBong", "Pop"]),
            }
        )
        cache_impl._build_invite = mock.Mock(side_effect=[mock_invite_1, mock_invite_2])
        assert cache_impl.get_invites_view_for_channel(
            snowflakes.Snowflake(83452134), snowflakes.Snowflake(987987)
        ) == {
            "blamBang": mock_invite_1,
            "bingBong": mock_invite_2,
        }
        cache_impl._build_invite.assert_has_calls(
            [
                mock.call(
                    mock_invite_data_1,
                    cached_users={
                        snowflakes.Snowflake(4312365): mock_wrapped_inviter,
                        snowflakes.Snowflake(65643213): mock_wrapped_target_user,
                    },
                ),
                mock.call(
                    mock_invite_data_2,
                    cached_users={
                        snowflakes.Snowflake(4312365): mock_wrapped_inviter,
                        snowflakes.Snowflake(65643213): mock_wrapped_target_user,
                    },
                ),
            ]
        )

    def test_get_invites_view_for_channel_unknown_emoji_cache(self, cache_impl):
        cache_impl._invite_entries = collections.FreezableDict(
            {
                "okok": mock.Mock(cache.InviteData),
                "dsaytert": mock.Mock(cache.InviteData),
            }
        )
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(9544994): mock.Mock(cache.GuildRecord),
                snowflakes.Snowflake(4444444): cache.GuildRecord(invites=None),
            }
        )
        cache_impl._build_invite = mock.Mock()
        result = cache_impl.get_invites_view_for_channel(snowflakes.Snowflake(4444444), snowflakes.Snowflake(942123))
        assert result == {}
        cache_impl._build_invite.assert_not_called()

    def test_get_invites_view_for_channel_unknown_record(self, cache_impl):
        cache_impl._invite_entries = collections.FreezableDict(
            {
                "okok": mock.Mock(cache.InviteData),
                "dsaytert": mock.Mock(cache.InviteData),
            }
        )
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(9544994): mock.Mock(cache.GuildRecord),
            }
        )
        cache_impl._build_invite = mock.Mock()
        result = cache_impl.get_invites_view_for_channel(snowflakes.Snowflake(4444444), snowflakes.Snowflake(9543123))
        assert result == {}
        cache_impl._build_invite.assert_not_called()

    def test_update_invite(self, cache_impl):
        mock_old_invite = mock.Mock(invites.InviteWithMetadata)
        mock_new_invite = mock.Mock(invites.InviteWithMetadata)
        mock_invite = mock.Mock(invites.InviteWithMetadata, code="biggieSmall")
        cache_impl.get_invite = mock.Mock(side_effect=[mock_old_invite, mock_new_invite])
        cache_impl.set_invite = mock.Mock()
        assert cache_impl.update_invite(mock_invite) == (mock_old_invite, mock_new_invite)
        cache_impl.get_invite.assert_has_calls([mock.call("biggieSmall"), mock.call("biggieSmall")])
        cache_impl.set_invite.assert_called_once_with(mock_invite)

    def test_delete_me_for_known_me(self, cache_impl):
        mock_own_user = mock.Mock(users.OwnUser)
        cache_impl._me = mock_own_user
        assert cache_impl.delete_me() is mock_own_user
        assert cache_impl._me is None

    def test_delete_me_for_unknown_me(self, cache_impl):
        assert cache_impl.delete_me() is None
        assert cache_impl._me is None

    def test_get_me_for_known_me(self, cache_impl):
        mock_own_user = mock.MagicMock(users.OwnUser)
        cache_impl._me = mock_own_user
        cached_me = cache_impl.get_me()
        assert cached_me == mock_own_user
        assert cached_me is not mock_own_user

    def test_get_me_for_unknown_me(self, cache_impl):
        assert cache_impl.get_me() is None

    def test_set_me(self, cache_impl):
        mock_own_user = mock.MagicMock(users.OwnUser)
        assert cache_impl.set_me(mock_own_user) is None
        assert cache_impl._me == mock_own_user
        assert cache_impl._me is not mock_own_user

    def test_update_me_for_cached_me(self, cache_impl):
        mock_cached_own_user = mock.MagicMock(users.OwnUser)
        mock_own_user = mock.MagicMock(users.OwnUser)
        cache_impl._me = mock_cached_own_user
        assert cache_impl.update_me(mock_own_user) == (mock_cached_own_user, mock_own_user)
        assert cache_impl._me == mock_own_user

    def test_update_me_for_uncached_me(self, cache_impl):
        mock_own_user = mock.MagicMock(users.OwnUser)
        assert cache_impl.update_me(mock_own_user) == (None, mock_own_user)
        assert cache_impl._me == mock_own_user

    def test__build_member(self, cache_impl):
        member_data = cache.MemberData(
            id=snowflakes.Snowflake(512312354),
            guild_id=snowflakes.Snowflake(6434435234),
            nickname="NICK",
            role_ids=(snowflakes.Snowflake(65234), snowflakes.Snowflake(654234123)),
            joined_at=datetime.datetime(2020, 7, 9, 13, 11, 18, 384554, tzinfo=datetime.timezone.utc),
            premium_since=datetime.datetime(2020, 7, 17, 13, 11, 18, 384554, tzinfo=datetime.timezone.utc),
            is_deaf=False,
            is_mute=True,
        )
        mock_user = mock.MagicMock(users.User)
        cache_impl._user_entries = collections.FreezableDict(
            {snowflakes.Snowflake(512312354): cache.GenericRefWrapper(object=mock_user)}
        )
        member = cache_impl._build_member(member_data)
        assert member.user == mock_user
        assert member.user is not mock_user
        assert member.guild_id == 6434435234
        assert member.nickname == "NICK"
        assert member.role_ids == (snowflakes.Snowflake(65234), snowflakes.Snowflake(654234123))
        assert member.joined_at == datetime.datetime(2020, 7, 9, 13, 11, 18, 384554, tzinfo=datetime.timezone.utc)
        assert member.premium_since == datetime.datetime(2020, 7, 17, 13, 11, 18, 384554, tzinfo=datetime.timezone.utc)
        assert member.is_deaf is False
        assert member.is_mute is True

    def test__build_member_for_passed_through_user(self, cache_impl):
        member_data = cache.MemberData(
            id=snowflakes.Snowflake(512312354),
            guild_id=snowflakes.Snowflake(6434435234),
            nickname="NICK",
            role_ids=(snowflakes.Snowflake(65234), snowflakes.Snowflake(654234123)),
            joined_at=datetime.datetime(2020, 7, 9, 13, 11, 18, 384554, tzinfo=datetime.timezone.utc),
            premium_since=datetime.datetime(2020, 7, 17, 13, 11, 18, 384554, tzinfo=datetime.timezone.utc),
            is_deaf=False,
            is_mute=True,
        )
        mock_user = mock.MagicMock(users.User)
        cache_impl._user_entries = collections.FreezableDict({})
        member = cache_impl._build_member(
            member_data,
            cached_users={snowflakes.Snowflake(512312354): cache.GenericRefWrapper(object=mock_user)},
        )
        assert member.user == mock_user
        assert member.user is not mock_user

    def test_clear_members(self, cache_impl):
        mock_data_member_1 = mock.Mock(
            cache.MemberData, id=snowflakes.Snowflake(2123123), guild_id=snowflakes.Snowflake(43123123)
        )
        mock_data_member_2 = mock.Mock(
            cache.MemberData,
            id=snowflakes.Snowflake(212314423),
            guild_id=snowflakes.Snowflake(43123123),
        )
        mock_data_member_3 = mock.Mock(
            cache.MemberData, id=snowflakes.Snowflake(2123166623), guild_id=snowflakes.Snowflake(65234)
        )
        mock_data_member_4 = mock.Mock(
            cache.MemberData,
            id=snowflakes.Snowflake(21237777123),
            guild_id=snowflakes.Snowflake(65234),
        )
        mock_data_member_5 = mock.Mock(
            cache.MemberData,
            id=snowflakes.Snowflake(212399999123),
            guild_id=snowflakes.Snowflake(65234),
        )
        mock_member_1 = object()
        mock_member_2 = object()
        mock_member_3 = object()
        mock_member_4 = object()
        mock_member_5 = object()
        mock_wrapped_user_1 = object()
        mock_wrapped_user_2 = object()
        mock_wrapped_user_3 = object()
        mock_wrapped_user_4 = object()
        mock_wrapped_user_5 = object()
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(43123123): cache.GuildRecord(
                    members=collections.FreezableDict(
                        {
                            snowflakes.Snowflake(2123123): mock_data_member_1,
                            snowflakes.Snowflake(212314423): mock_data_member_2,
                        }
                    )
                ),
                snowflakes.Snowflake(35123): cache.GuildRecord(members={}),
                snowflakes.Snowflake(76345123): cache.GuildRecord(members=None),
                snowflakes.Snowflake(65234): cache.GuildRecord(
                    members=collections.FreezableDict(
                        {
                            snowflakes.Snowflake(2123166623): mock_data_member_3,
                            snowflakes.Snowflake(21237777123): mock_data_member_4,
                            snowflakes.Snowflake(212399999123): mock_data_member_5,
                        }
                    )
                ),
            }
        )
        cache_impl._user_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(2123123): mock_wrapped_user_1,
                snowflakes.Snowflake(212314423): mock_wrapped_user_2,
                snowflakes.Snowflake(2123166623): mock_wrapped_user_3,
                snowflakes.Snowflake(21237777123): mock_wrapped_user_4,
                snowflakes.Snowflake(212399999123): mock_wrapped_user_5,
            }
        )
        expected_users = dict(cache_impl._user_entries)
        cache_impl._build_member = mock.Mock(
            side_effect=[mock_member_1, mock_member_2, mock_member_3, mock_member_4, mock_member_5]
        )
        cache_impl._garbage_collect_user = mock.Mock()
        cache_impl._remove_guild_record_if_empty = mock.Mock()

        assert cache_impl.clear_members() == {
            snowflakes.Snowflake(43123123): {
                snowflakes.Snowflake(2123123): mock_member_1,
                snowflakes.Snowflake(212314423): mock_member_2,
            },
            snowflakes.Snowflake(65234): {
                snowflakes.Snowflake(2123166623): mock_member_3,
                snowflakes.Snowflake(21237777123): mock_member_4,
                snowflakes.Snowflake(212399999123): mock_member_5,
            },
        }

        cache_impl._garbage_collect_user.assert_has_calls(
            [
                mock.call(snowflakes.Snowflake(2123123), decrement=1),
                mock.call(snowflakes.Snowflake(212314423), decrement=1),
                mock.call(snowflakes.Snowflake(2123166623), decrement=1),
                mock.call(snowflakes.Snowflake(21237777123), decrement=1),
                mock.call(snowflakes.Snowflake(212399999123), decrement=1),
            ]
        )
        cache_impl._remove_guild_record_if_empty.assert_has_calls(
            [mock.call(snowflakes.Snowflake(43123123)), mock.call(65234)]
        )
        cache_impl._build_member.assert_has_calls(
            [
                mock.call(mock_data_member_1, cached_users=expected_users),
                mock.call(mock_data_member_2, cached_users=expected_users),
                mock.call(mock_data_member_3, cached_users=expected_users),
                mock.call(mock_data_member_4, cached_users=expected_users),
                mock.call(mock_data_member_5, cached_users=expected_users),
            ]
        )

    @pytest.mark.skip(reason="TODO")
    def test_clear_members_for_guild(self, cache_impl):
        ...

    def test_delete_member_for_unknown_guild_record(self, cache_impl):
        assert cache_impl.delete_member(snowflakes.Snowflake(42123), snowflakes.Snowflake(67876)) is None

    def test_delete_member_for_unknown_member_cache(self, cache_impl):
        cache_impl._guild_entries = {snowflakes.Snowflake(42123): cache.GuildRecord()}
        assert cache_impl.delete_member(snowflakes.Snowflake(42123), snowflakes.Snowflake(67876)) is None

    def test_delete_member_for_known_member(self, cache_impl):
        mock_member = mock.Mock(guilds.Member)
        mock_member_data = mock.Mock(
            cache.MemberData, id=snowflakes.Snowflake(67876), guild_id=snowflakes.Snowflake(42123)
        )
        cache_impl._guild_entries = collections.FreezableDict(
            {snowflakes.Snowflake(42123): cache.GuildRecord(members={snowflakes.Snowflake(67876): mock_member_data})}
        )
        cache_impl._user_entries = collections.FreezableDict({snowflakes.Snowflake(67876): object()})
        cache_impl._remove_guild_record_if_empty = mock.Mock()
        cache_impl._garbage_collect_user = mock.Mock()
        cache_impl._build_member = mock.Mock(return_value=mock_member)
        assert cache_impl.delete_member(snowflakes.Snowflake(42123), snowflakes.Snowflake(67876)) is mock_member
        assert cache_impl._guild_entries[snowflakes.Snowflake(42123)].members is None
        cache_impl._build_member.assert_called_once_with(mock_member_data)
        cache_impl._garbage_collect_user.assert_called_once_with(snowflakes.Snowflake(67876), decrement=1)
        cache_impl._remove_guild_record_if_empty.assert_called_once_with(snowflakes.Snowflake(42123))

    def test_delete_member_for_known_hard_referenced_member(self, cache_impl):
        cache_impl._user_entries = collections.FreezableDict(
            {snowflakes.Snowflake(67876): cache.GenericRefWrapper(object=object(), ref_count=4)}
        )
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(42123): cache.GuildRecord(
                    members=collections.FreezableDict(
                        {
                            snowflakes.Snowflake(67876): mock.Mock(
                                cache.MemberData,
                                id=snowflakes.Snowflake(67876),
                                guild_id=snowflakes.Snowflake(42123),
                            )
                        }
                    ),
                    voice_states=collections.FreezableDict({snowflakes.Snowflake(67876): mock.Mock(voices.VoiceState)}),
                )
            }
        )
        assert cache_impl.delete_member(snowflakes.Snowflake(42123), snowflakes.Snowflake(67876)) is None

    def test_get_member_for_unknown_member_cache(self, cache_impl):
        cache_impl._guild_entries = collections.FreezableDict({snowflakes.Snowflake(1234213): cache.GuildRecord()})
        assert cache_impl.get_member(snowflakes.Snowflake(1234213), snowflakes.Snowflake(512312354)) is None

    def test_get_member_for_unknown_member(self, cache_impl):
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(1234213): cache.GuildRecord(
                    members={snowflakes.Snowflake(43123): mock.Mock(cache.MemberData)}
                )
            }
        )
        assert cache_impl.get_member(snowflakes.Snowflake(1234213), snowflakes.Snowflake(512312354)) is None

    def test_get_member_for_unknown_guild_record(self, cache_impl):
        assert cache_impl.get_member(snowflakes.Snowflake(1234213), snowflakes.Snowflake(512312354)) is None

    def test_get_member_for_known_member(self, cache_impl):
        mock_member_data = mock.Mock(cache.MemberData)
        mock_member = mock.Mock(guilds.Member)
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(1234213): cache.GuildRecord(
                    members=collections.FreezableDict(
                        {
                            snowflakes.Snowflake(512312354): mock_member_data,
                            snowflakes.Snowflake(321): mock.Mock(cache.MemberData),
                        }
                    )
                )
            }
        )
        cache_impl._user_entries = collections.FreezableDict({})
        cache_impl._build_member = mock.Mock(return_value=mock_member)
        assert cache_impl.get_member(snowflakes.Snowflake(1234213), snowflakes.Snowflake(512312354)) is mock_member
        cache_impl._build_member.assert_called_once_with(mock_member_data)

    def test_get_members_view(self, cache_impl):
        cache_impl._user_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(345123): object(),
                snowflakes.Snowflake(65345): object(),
                snowflakes.Snowflake(12312): object(),
            }
        )
        expected_users = cache_impl._user_entries.copy()
        mock_member_data_1 = object()
        mock_member_data_2 = object()
        mock_member_data_3 = object()
        mock_member_data_4 = object()
        mock_member_data_5 = object()
        mock_member_1 = object()
        mock_member_2 = object()
        mock_member_3 = object()
        mock_member_4 = object()
        mock_member_5 = object()
        cache_impl._build_member = mock.Mock(
            side_effect=[mock_member_1, mock_member_2, mock_member_3, mock_member_4, mock_member_5]
        )
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(543123): cache.GuildRecord(),
                snowflakes.Snowflake(54123123): cache.GuildRecord(
                    members=collections.FreezableDict(
                        {snowflakes.Snowflake(321): mock_member_data_1, snowflakes.Snowflake(6324): mock_member_data_2}
                    )
                ),
                snowflakes.Snowflake(54234): cache.GuildRecord(members=collections.FreezableDict({})),
                snowflakes.Snowflake(783452): cache.GuildRecord(
                    members=collections.FreezableDict(
                        {
                            snowflakes.Snowflake(54123): mock_member_data_3,
                            snowflakes.Snowflake(786234): mock_member_data_4,
                            snowflakes.Snowflake(86545463): mock_member_data_5,
                        }
                    )
                ),
            }
        )

        assert cache_impl.get_members_view() == {
            snowflakes.Snowflake(54123123): {
                snowflakes.Snowflake(321): mock_member_1,
                snowflakes.Snowflake(6324): mock_member_2,
            },
            snowflakes.Snowflake(783452): {
                snowflakes.Snowflake(54123): mock_member_3,
                snowflakes.Snowflake(786234): mock_member_4,
                snowflakes.Snowflake(86545463): mock_member_5,
            },
        }

        cache_impl._build_member.assert_has_calls(
            [
                mock.call(mock_member_data_1, cached_users=expected_users),
                mock.call(mock_member_data_2, cached_users=expected_users),
                mock.call(mock_member_data_3, cached_users=expected_users),
                mock.call(mock_member_data_4, cached_users=expected_users),
                mock.call(mock_member_data_5, cached_users=expected_users),
            ]
        )

    def test_get_members_view_for_guild_unknown_record(self, cache_impl):
        members_mapping = cache_impl.get_members_view_for_guild(snowflakes.Snowflake(42334))
        assert members_mapping == {}

    def test_get_members_view_for_guild_unknown_member_cache(self, cache_impl):
        cache_impl._guild_entries = collections.FreezableDict({snowflakes.Snowflake(42334): cache.GuildRecord()})
        members_mapping = cache_impl.get_members_view_for_guild(snowflakes.Snowflake(42334))
        assert members_mapping == {}

    def test_get_members_view_for_guild(self, cache_impl):
        mock_member_data_1 = mock.Mock(cache.MemberData, has_been_deleted=False)
        mock_member_data_2 = mock.Mock(cache.MemberData, has_been_deleted=False)
        mock_member_1 = mock.Mock(guilds.Member)
        mock_member_2 = mock.Mock(guilds.Member)
        mock_wrapped_user_1 = mock.Mock(cache.GenericRefWrapper[users.User])
        mock_wrapped_user_2 = mock.Mock(cache.GenericRefWrapper[users.User])
        guild_record = cache.GuildRecord(
            members=collections.FreezableDict(
                {
                    snowflakes.Snowflake(3214321): mock_member_data_1,
                    snowflakes.Snowflake(53224): mock_member_data_2,
                    snowflakes.Snowflake(9000): mock.Mock(cache.MemberData, has_been_deleted=True),
                }
            )
        )
        cache_impl._guild_entries = collections.FreezableDict({snowflakes.Snowflake(42334): guild_record})
        cache_impl._user_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(3214321): mock_wrapped_user_1,
                snowflakes.Snowflake(53224): mock_wrapped_user_2,
                snowflakes.Snowflake(87345): mock.Mock(cache.GenericRefWrapper),
            }
        )
        cache_impl._build_member = mock.Mock(side_effect=[mock_member_1, mock_member_2])
        assert dict(cache_impl.get_members_view_for_guild(snowflakes.Snowflake(42334))) == {
            snowflakes.Snowflake(3214321): mock_member_1,
            snowflakes.Snowflake(53224): mock_member_2,
        }
        cache_impl._build_member.assert_has_calls(
            [
                mock.call(
                    mock_member_data_1,
                    cached_users={
                        snowflakes.Snowflake(3214321): mock_wrapped_user_1,
                        snowflakes.Snowflake(53224): mock_wrapped_user_2,
                    },
                ),
                mock.call(
                    mock_member_data_2,
                    cached_users={
                        snowflakes.Snowflake(3214321): mock_wrapped_user_1,
                        snowflakes.Snowflake(53224): mock_wrapped_user_2,
                    },
                ),
            ]
        )

    def test_set_member(self, cache_impl):
        mock_user = mock.Mock(users.User, id=snowflakes.Snowflake(645234123))
        member_model = guilds.Member(
            guild_id=snowflakes.Snowflake(67345234),
            user=mock_user,
            nickname="A NICK LOL",
            role_ids=[snowflakes.Snowflake(65345234), snowflakes.Snowflake(123123)],
            joined_at=datetime.datetime(2020, 7, 15, 23, 30, 59, 501602, tzinfo=datetime.timezone.utc),
            premium_since=datetime.datetime(2020, 7, 1, 2, 0, 12, 501602, tzinfo=datetime.timezone.utc),
            is_deaf=True,
            is_mute=False,
        )
        cache_impl.set_user = mock.Mock()
        cache_impl._increment_user_ref_count = mock.Mock()
        cache_impl.set_member(member_model)
        cache_impl.set_user.assert_called_once_with(mock_user)
        cache_impl._increment_user_ref_count.assert_called_once_with(snowflakes.Snowflake(645234123))
        assert 67345234 in cache_impl._guild_entries
        assert 645234123 in cache_impl._guild_entries[snowflakes.Snowflake(67345234)].members
        member_entry = cache_impl._guild_entries[snowflakes.Snowflake(67345234)].members[
            snowflakes.Snowflake(645234123)
        ]
        assert member_entry.id == 645234123
        assert member_entry.guild_id == 67345234
        assert member_entry.nickname == "A NICK LOL"
        assert member_entry.role_ids == (65345234, 123123)
        assert member_entry.role_ids is not member_model.role_ids
        assert isinstance(member_entry.role_ids, tuple)
        assert member_entry.joined_at == datetime.datetime(
            2020, 7, 15, 23, 30, 59, 501602, tzinfo=datetime.timezone.utc
        )
        assert member_entry.premium_since == datetime.datetime(
            2020, 7, 1, 2, 0, 12, 501602, tzinfo=datetime.timezone.utc
        )
        assert member_entry.is_deaf is True
        assert member_entry.is_mute is False
        assert not hasattr(member_entry, "user")

    def test_set_member_doesnt_increment_user_ref_count_for_pre_cached_member(self, cache_impl):
        mock_user = mock.Mock(users.User, id=snowflakes.Snowflake(645234123))
        member_model = mock.MagicMock(guilds.Member, user=mock_user, guild_id=snowflakes.Snowflake(67345234))
        cache_impl.set_user = mock.Mock()
        cache_impl._increment_user_ref_count = mock.Mock()
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(67345234): cache.GuildRecord(
                    members=collections.FreezableDict({snowflakes.Snowflake(645234123): mock.Mock(cache.MemberData)})
                )
            }
        )
        cache_impl.set_member(member_model)
        cache_impl.set_user.assert_called_once_with(mock_user)
        cache_impl._increment_user_ref_count.assert_not_called()

    def test_update_member(self, cache_impl):
        mock_old_cached_member = mock.Mock(guilds.Member)
        mock_new_cached_member = mock.Mock(guilds.Member)
        mock_member = mock.Mock(
            guilds.Member,
            guild_id=snowflakes.Snowflake(123123),
            user=mock.Mock(users.User, id=snowflakes.Snowflake(65234123)),
        )
        cache_impl.get_member = mock.Mock(side_effect=[mock_old_cached_member, mock_new_cached_member])
        cache_impl.set_member = mock.Mock()
        assert cache_impl.update_member(mock_member) == (mock_old_cached_member, mock_new_cached_member)
        cache_impl.get_member.assert_has_calls([mock.call(123123, 65234123), mock.call(123123, 65234123)])
        cache_impl.set_member.assert_called_once_with(mock_member)

    @pytest.mark.skip(reason="TODO")
    def test_clear_presences(self, cache_impl):
        ...

    @pytest.mark.skip(reason="TODO")
    def test_clear_presences_for_guild(self, cache_impl):
        ...

    @pytest.mark.skip(reason="TODO")
    def test_delete_presence(self, cache_impl):
        ...

    @pytest.mark.skip(reason="TODO")
    def test_get_presence(self, cache_impl):
        ...

    @pytest.mark.skip(reason="TODO")
    def test_get_presences_view(self, cache_impl):
        ...

    @pytest.mark.skip(reason="TODO")
    def test_get_presences_view_for_guild(self, cache_impl):
        ...

    @pytest.mark.skip(reason="TODO")
    def test_set_presence(self, cache_impl):
        ...

    @pytest.mark.skip(reason="TODO")
    def test_update_presence(self, cache_impl):
        ...

    @pytest.mark.skip(reason="TODO")
    def test_clear_roles(self, cache_impl):
        ...

    @pytest.mark.skip(reason="TODO")
    def test_clear_roles_for_guild(self, cache_impl):
        ...

    @pytest.mark.skip(reason="TODO")
    def test_delete_role(self, cache_impl):
        ...

    @pytest.mark.skip(reason="TODO")
    def test_get_role(self, cache_impl):
        ...

    @pytest.mark.skip(reason="TODO")
    def test_get_roles_view(self, cache_impl):
        ...

    @pytest.mark.skip(reason="TODO")
    def test_get_roles_view_for_guild(self, cache_impl):
        ...

    @pytest.mark.skip(reason="TODO")
    def test_set_role(self, cache_impl):
        ...

    @pytest.mark.skip(reason="TODO")
    def test_update_role(self, cache_impl):
        ...

    def test_clear_users_for_cached_users(self, cache_impl):
        mock_user_1 = mock.MagicMock(users.User)
        mock_user_2 = mock.MagicMock(users.User)
        cache_impl._user_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(53422132): cache.GenericRefWrapper(object=mock_user_1),
                snowflakes.Snowflake(7654433245): cache.GenericRefWrapper(object=mock_user_2),
            }
        )
        assert cache_impl.clear_users() == {
            snowflakes.Snowflake(53422132): mock_user_1,
            snowflakes.Snowflake(7654433245): mock_user_2,
        }
        assert cache_impl._user_entries == {}

    def test_clear_users_ignores_hard_referenced_users(self, cache_impl):
        wrapped_user = cache.GenericRefWrapper(object=mock.Mock(users.User), ref_count=2)
        cache_impl._user_entries = collections.FreezableDict({snowflakes.Snowflake(53422132): wrapped_user})
        assert cache_impl.clear_users() == {}
        assert cache_impl._user_entries == {snowflakes.Snowflake(53422132): wrapped_user}

    def test_clear_users_for_empty_user_cache(self, cache_impl):
        assert cache_impl.clear_users() == {}
        assert cache_impl._user_entries == {}

    def test_delete_user_for_known_unreferenced_user(self, cache_impl):
        mock_user = mock.Mock(users.User)
        mock_wrapped_other_user = cache.GenericRefWrapper(object=mock.Mock(users.User))
        cache_impl._user_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(21231234): cache.GenericRefWrapper(object=mock_user),
                snowflakes.Snowflake(645234): mock_wrapped_other_user,
            }
        )
        assert cache_impl.delete_user(snowflakes.Snowflake(21231234)) is mock_user
        assert cache_impl._user_entries == {snowflakes.Snowflake(645234): mock_wrapped_other_user}

    def test_delete_user_for_referenced_user(self, cache_impl):
        mock_wrapped_user = mock.Mock(cache.GenericRefWrapper, ref_count=2)
        mock_other_wrapped_user = mock.Mock(cache.GenericRefWrapper)
        cache_impl._user_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(21231234): mock_wrapped_user,
                snowflakes.Snowflake(645234): mock_other_wrapped_user,
            }
        )
        assert cache_impl.delete_user(snowflakes.Snowflake(21231234)) is None
        assert cache_impl._user_entries == {
            snowflakes.Snowflake(21231234): mock_wrapped_user,
            snowflakes.Snowflake(645234): mock_other_wrapped_user,
        }

    def test_delete_user_for_unknown_user(self, cache_impl):
        mock_wrapped_user = mock.Mock(cache.GenericRefWrapper)
        cache_impl._user_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(21231234): mock_wrapped_user,
            }
        )
        assert cache_impl.delete_user(snowflakes.Snowflake(75423423)) is None
        assert cache_impl._user_entries == {
            snowflakes.Snowflake(21231234): mock_wrapped_user,
        }

    def test_get_user_for_known_user(self, cache_impl):
        mock_user = mock.MagicMock(users.User)
        cache_impl._user_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(21231234): cache.GenericRefWrapper(object=mock_user),
                snowflakes.Snowflake(645234): mock.Mock(cache.GenericRefWrapper),
            }
        )
        cache_impl._build_user = mock.Mock(return_value=mock_user)
        assert cache_impl.get_user(snowflakes.Snowflake(21231234)) == mock_user

    def test_get_users_view_for_filled_user_cache(self, cache_impl):
        mock_user_1 = mock.MagicMock(users.User)
        mock_user_2 = mock.MagicMock(users.User)
        cache_impl._user_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(54123): cache.GenericRefWrapper(object=mock_user_1),
                snowflakes.Snowflake(76345): cache.GenericRefWrapper(object=mock_user_2),
            }
        )
        assert cache_impl.get_users_view() == {
            snowflakes.Snowflake(54123): mock_user_1,
            snowflakes.Snowflake(76345): mock_user_2,
        }

    def test_get_users_view_for_empty_user_cache(self, cache_impl):
        assert cache_impl.get_users_view() == {}

    def test_set_user(self, cache_impl):
        mock_user = mock.MagicMock(users.User, id=snowflakes.Snowflake(6451234123))
        cache_impl._user_entries = collections.FreezableDict(
            {snowflakes.Snowflake(542143): mock.Mock(cache.GenericRefWrapper)}
        )
        assert cache_impl.set_user(mock_user) is None
        assert 6451234123 in cache_impl._user_entries
        assert cache_impl._user_entries[snowflakes.Snowflake(6451234123)].object == mock_user
        assert cache_impl._user_entries[snowflakes.Snowflake(6451234123)].object is not mock_user
        assert cache_impl._user_entries[snowflakes.Snowflake(6451234123)].ref_count == 0

    def test_set_user_carries_over_ref_count(self, cache_impl):
        mock_user = mock.MagicMock(users.User, id=snowflakes.Snowflake(6451234123))
        cache_impl._user_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(542143): mock.Mock(cache.GenericRefWrapper),
                snowflakes.Snowflake(6451234123): mock.Mock(cache.GenericRefWrapper, ref_count=42),
            }
        )
        assert cache_impl.set_user(mock_user) is None
        assert 6451234123 in cache_impl._user_entries
        assert cache_impl._user_entries[snowflakes.Snowflake(6451234123)].object == mock_user
        assert cache_impl._user_entries[snowflakes.Snowflake(6451234123)].object is not mock_user
        assert cache_impl._user_entries[snowflakes.Snowflake(6451234123)].ref_count == 42

    def test_update_user(self, cache_impl):
        mock_old_cached_user = mock.Mock(users.User)
        mock_new_cached_user = mock.Mock(users.User)
        mock_user = mock.Mock(users.User, id=snowflakes.Snowflake(54123123))
        cache_impl.get_user = mock.Mock(side_effect=(mock_old_cached_user, mock_new_cached_user))
        cache_impl.set_user = mock.Mock()
        assert cache_impl.update_user(mock_user) == (mock_old_cached_user, mock_new_cached_user)
        cache_impl.set_user.assert_called_once_with(mock_user)
        cache_impl.get_user.assert_has_calls([mock.call(54123123), mock.call(54123123)])

    def test__build_voice_state(self, cache_impl):
        voice_state_data = cache.VoiceStateData(
            channel_id=snowflakes.Snowflake(4651234123),
            guild_id=snowflakes.Snowflake(54123123),
            is_guild_deafened=True,
            is_guild_muted=False,
            is_self_deafened=True,
            is_self_muted=True,
            is_streaming=False,
            is_suppressed=False,
            is_video_enabled=False,
            user_id=snowflakes.Snowflake(7512312),
            session_id="lkmdfslkmfdskjlfsdkjlsfdkjldsf",
        )
        mock_member_data = mock.Mock(cache.MemberData)
        mock_member = mock.Mock(guilds.Member)
        record = cache.GuildRecord(
            members=collections.FreezableDict(
                {
                    snowflakes.Snowflake(7512312): mock_member_data,
                    snowflakes.Snowflake(43123123): mock.Mock(cache.MemberData),
                }
            ),
        )
        cache_impl._guild_entries = collections.FreezableDict({snowflakes.Snowflake(54123123): record})
        cache_impl._build_member = mock.Mock(return_value=mock_member)
        current_voice_state = cache_impl._build_voice_state(voice_state_data)
        cache_impl._build_member.assert_called_once_with(mock_member_data, cached_users=None)
        assert current_voice_state.app is cache_impl._app
        assert current_voice_state.channel_id == snowflakes.Snowflake(4651234123)
        assert current_voice_state.guild_id == snowflakes.Snowflake(54123123)
        assert current_voice_state.is_guild_deafened is True
        assert current_voice_state.is_guild_muted is False
        assert current_voice_state.is_self_deafened is True
        assert current_voice_state.is_self_muted is True
        assert current_voice_state.is_streaming is False
        assert current_voice_state.is_video_enabled is False
        assert current_voice_state.user_id == snowflakes.Snowflake(7512312)
        assert current_voice_state.session_id == "lkmdfslkmfdskjlfsdkjlsfdkjldsf"
        assert current_voice_state.member is mock_member

    def test__build_voice_state_with_pass_through_member_and_user_data(self, cache_impl):
        voice_state_data = cache.VoiceStateData(
            channel_id=snowflakes.Snowflake(4651234123),
            guild_id=snowflakes.Snowflake(54123123),
            is_guild_deafened=True,
            is_guild_muted=False,
            is_self_deafened=True,
            is_self_muted=True,
            is_streaming=False,
            is_suppressed=False,
            is_video_enabled=False,
            user_id=snowflakes.Snowflake(7512312),
            session_id="lkmdfslkmfdskjlfsdkjlsfdkjldsf",
        )
        mock_member_data = mock.Mock(cache.MemberData)
        mock_member = mock.Mock(guilds.Member)
        mock_user = mock.Mock(users.User)
        cache_impl._build_member = mock.Mock(return_value=mock_member)
        current_voice_state = cache_impl._build_voice_state(
            voice_state_data,
            cached_members=collections.FreezableDict(
                {
                    snowflakes.Snowflake(7512312): mock_member_data,
                    snowflakes.Snowflake(63123): mock.Mock(cache.MemberData),
                }
            ),
            cached_users=collections.FreezableDict({snowflakes.Snowflake(7512312): mock_user}),
        )
        cache_impl._build_member.assert_called_once_with(
            mock_member_data, cached_users=collections.FreezableDict({snowflakes.Snowflake(7512312): mock_user})
        )
        assert current_voice_state.app is cache_impl._app
        assert current_voice_state.channel_id == snowflakes.Snowflake(4651234123)
        assert current_voice_state.guild_id == snowflakes.Snowflake(54123123)
        assert current_voice_state.is_guild_deafened is True
        assert current_voice_state.is_guild_muted is False
        assert current_voice_state.is_self_deafened is True
        assert current_voice_state.is_self_muted is True
        assert current_voice_state.is_streaming is False
        assert current_voice_state.is_video_enabled is False
        assert current_voice_state.user_id == snowflakes.Snowflake(7512312)
        assert current_voice_state.session_id == "lkmdfslkmfdskjlfsdkjlsfdkjldsf"
        assert current_voice_state.member is mock_member

    @pytest.mark.skip(reason="TODO")
    def test_clear_voice_states(self, cache_impl):
        ...

    @pytest.mark.skip(reason="TODO")
    def test_clear_voice_states_for_channel(self, cache_impl):
        ...

    def test_clear_voice_states_for_guild(self, cache_impl):
        mock_voice_state_data_1 = mock.Mock(cache.VoiceStateData, user_id=snowflakes.Snowflake(7512312))
        mock_voice_state_data_2 = mock.Mock(cache.VoiceStateData, user_id=snowflakes.Snowflake(43123123))
        mock_voice_state_1 = mock.Mock(voices.VoiceState)
        mock_voice_state_2 = mock.Mock(voices.VoiceState)
        mock_member_data_1 = mock.Mock(
            cache.MemberData, guild_id=snowflakes.Snowflake(54123123), id=snowflakes.Snowflake(7512312)
        )
        mock_member_data_2 = mock.Mock(
            cache.MemberData,
            guild_id=snowflakes.Snowflake(54123123),
            id=snowflakes.Snowflake(43123123),
        )
        record = cache.GuildRecord(
            voice_states=collections.FreezableDict(
                {
                    snowflakes.Snowflake(7512312): mock_voice_state_data_1,
                    snowflakes.Snowflake(43123123): mock_voice_state_data_2,
                }
            ),
            members=collections.FreezableDict(
                {
                    snowflakes.Snowflake(7512312): mock_member_data_1,
                    snowflakes.Snowflake(43123123): mock_member_data_2,
                    snowflakes.Snowflake(123): mock.Mock(cache.MemberData),
                }
            ),
        )
        cache_impl._remove_guild_record_if_empty = mock.Mock()
        mock_wrapped_user_1 = mock.Mock(cache.GenericRefWrapper[users.User])
        mock_wrapped_user_2 = mock.Mock(cache.GenericRefWrapper[users.User])
        cache_impl._user_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(7512312): mock_wrapped_user_1,
                snowflakes.Snowflake(43123123): mock_wrapped_user_2,
                snowflakes.Snowflake(56234): mock.Mock(cache.GenericRefWrapper),
            }
        )
        cache_impl._guild_entries = collections.FreezableDict({snowflakes.Snowflake(54123123): record})
        cache_impl._build_voice_state = mock.Mock(side_effect=[mock_voice_state_1, mock_voice_state_2])
        assert cache_impl.clear_voice_states_for_guild(snowflakes.Snowflake(54123123)) == {
            snowflakes.Snowflake(7512312): mock_voice_state_1,
            snowflakes.Snowflake(43123123): mock_voice_state_2,
        }
        cache_impl._remove_guild_record_if_empty.assert_called_once_with(snowflakes.Snowflake(54123123))
        cache_impl._build_voice_state.assert_has_calls(
            [
                mock.call(
                    mock_voice_state_data_1,
                    cached_members={
                        snowflakes.Snowflake(7512312): mock_member_data_1,
                        snowflakes.Snowflake(43123123): mock_member_data_2,
                    },
                    cached_users={
                        snowflakes.Snowflake(7512312): mock_wrapped_user_1,
                        snowflakes.Snowflake(43123123): mock_wrapped_user_2,
                    },
                ),
                mock.call(
                    mock_voice_state_data_2,
                    cached_members={
                        snowflakes.Snowflake(7512312): mock_member_data_1,
                        snowflakes.Snowflake(43123123): mock_member_data_2,
                    },
                    cached_users={
                        snowflakes.Snowflake(7512312): mock_wrapped_user_1,
                        snowflakes.Snowflake(43123123): mock_wrapped_user_2,
                    },
                ),
            ]
        )

    def test_clear_voice_states_for_guild_unknown_voice_state_cache(self, cache_impl):
        cache_impl._guild_entries[snowflakes.Snowflake(24123)] = cache.GuildRecord()
        assert cache_impl.clear_voice_states_for_guild(snowflakes.Snowflake(24123)) == {}

    def test_clear_voice_states_for_guild_unknown_record(self, cache_impl):
        assert cache_impl.clear_voice_states_for_guild(snowflakes.Snowflake(24123)) == {}

    def test_delete_voice_state(self, cache_impl):
        mock_voice_state_data = mock.Mock(cache.VoiceStateData, user_id=snowflakes.Snowflake(12354345))
        mock_other_voice_state_data = mock.Mock(cache.VoiceStateData)
        mock_voice_state = mock.Mock(voices.VoiceState)
        mock_member_data = object()
        cache_impl._build_voice_state = mock.Mock(return_value=mock_voice_state)
        guild_record = cache.GuildRecord(
            voice_states=collections.FreezableDict(
                {
                    snowflakes.Snowflake(12354345): mock_voice_state_data,
                    snowflakes.Snowflake(6541234): mock_other_voice_state_data,
                }
            ),
            members=collections.FreezableDict(
                {snowflakes.Snowflake(12354345): mock_member_data, snowflakes.Snowflake(9955959): object()}
            ),
        )
        cache_impl._user_entries = collections.FreezableDict(
            {snowflakes.Snowflake(12354345): object(), snowflakes.Snowflake(9393): object()}
        )
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(65234): mock.Mock(cache.GuildRecord),
                snowflakes.Snowflake(43123): guild_record,
            }
        )
        cache_impl._remove_guild_record_if_empty = mock.Mock()
        cache_impl._garbage_collect_member = mock.Mock()
        result = cache_impl.delete_voice_state(snowflakes.Snowflake(43123), snowflakes.Snowflake(12354345))
        assert result is mock_voice_state
        cache_impl._garbage_collect_member.assert_called_once_with(guild_record, mock_member_data)
        cache_impl._remove_guild_record_if_empty.assert_called_once_with(snowflakes.Snowflake(43123))
        assert cache_impl._guild_entries[snowflakes.Snowflake(43123)].voice_states == {
            snowflakes.Snowflake(6541234): mock_other_voice_state_data
        }

    def test_delete_voice_state_unknown_state(self, cache_impl):
        mock_other_voice_state_data = mock.Mock(cache.VoiceStateData)
        cache_impl._build_voice_state = mock.Mock()
        guild_record = cache.GuildRecord(
            voice_states=collections.FreezableDict({snowflakes.Snowflake(6541234): mock_other_voice_state_data})
        )
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(65234): mock.Mock(cache.GuildRecord),
                snowflakes.Snowflake(43123): guild_record,
            }
        )
        cache_impl._remove_guild_record_if_empty = mock.Mock()
        assert cache_impl.delete_voice_state(snowflakes.Snowflake(43123), snowflakes.Snowflake(12354345)) is None
        cache_impl._remove_guild_record_if_empty.assert_not_called()
        assert cache_impl._guild_entries[snowflakes.Snowflake(43123)].voice_states == {
            snowflakes.Snowflake(6541234): mock_other_voice_state_data
        }

    def test_delete_voice_state_unknown_state_cache(self, cache_impl):
        cache_impl._build_voice_state = mock.Mock()
        guild_record = cache.GuildRecord(voice_states=None)
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(65234): mock.Mock(cache.GuildRecord),
                snowflakes.Snowflake(43123): guild_record,
            }
        )
        cache_impl._remove_guild_record_if_empty = mock.Mock()
        assert cache_impl.delete_voice_state(snowflakes.Snowflake(43123), snowflakes.Snowflake(12354345)) is None
        cache_impl._remove_guild_record_if_empty.assert_not_called()

    def test_delete_voice_state_unknown_record(self, cache_impl):
        cache_impl._build_voice_state = mock.Mock()
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(65234): mock.Mock(cache.GuildRecord),
            }
        )
        cache_impl._remove_guild_record_if_empty = mock.Mock()
        assert cache_impl.delete_voice_state(snowflakes.Snowflake(43123), snowflakes.Snowflake(12354345)) is None
        cache_impl._remove_guild_record_if_empty.assert_not_called()

    def test_get_voice_state_for_known_voice_state(self, cache_impl):
        mock_voice_state_data = mock.Mock(cache.VoiceStateData)
        mock_voice_state = mock.Mock(voices.VoiceState)
        cache_impl._build_voice_state = mock.Mock(return_value=mock_voice_state)
        guild_record = cache.GuildRecord(voice_states={snowflakes.Snowflake(43124): mock_voice_state_data})
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(1235123): guild_record,
                snowflakes.Snowflake(73245): mock.Mock(cache.GuildRecord),
            }
        )
        result = cache_impl.get_voice_state(snowflakes.Snowflake(1235123), snowflakes.Snowflake(43124))
        assert result is mock_voice_state
        cache_impl._build_voice_state.assert_called_once_with(mock_voice_state_data)

    def test_get_voice_state_for_unknown_voice_state(self, cache_impl):
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(1235123): cache.GuildRecord(
                    voice_states=collections.FreezableDict(
                        {snowflakes.Snowflake(54123): mock.Mock(cache.VoiceStateData)}
                    )
                ),
                snowflakes.Snowflake(73245): mock.Mock(cache.GuildRecord),
            }
        )
        assert cache_impl.get_voice_state(snowflakes.Snowflake(1235123), snowflakes.Snowflake(43124)) is None

    def test_get_voice_state_for_unknown_voice_state_cache(self, cache_impl):
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(1235123): cache.GuildRecord(),
                snowflakes.Snowflake(73245): mock.Mock(cache.GuildRecord),
            }
        )
        assert cache_impl.get_voice_state(snowflakes.Snowflake(1235123), snowflakes.Snowflake(43124)) is None

    def test_get_voice_state_for_unknown_record(self, cache_impl):
        cache_impl._guild_entries = {snowflakes.Snowflake(73245): mock.Mock(cache.GuildRecord)}
        assert cache_impl.get_voice_state(snowflakes.Snowflake(1235123), snowflakes.Snowflake(43124)) is None

    @pytest.mark.skip(reason="TODO")
    def test_get_voice_state_view(self, cache_impl):
        ...

    @pytest.mark.skip(reason="TODO")
    def test_get_voice_states_view_for_channel(self, cache_impl):
        ...

    @pytest.mark.skip(reason="TODO")
    def test_get_voice_states_view_for_guild(self, cache_impl):
        ...

    @pytest.mark.skip(reason="TODO")
    def test_set_voice_state(self, cache_impl):
        ...

    def test_update_voice_state(self, cache_impl):
        mock_old_voice_state = mock.Mock(voices.VoiceState)
        mock_new_voice_state = mock.Mock(voices.VoiceState)
        voice_state = mock.Mock(
            voices.VoiceState, guild_id=snowflakes.Snowflake(43123123), user_id=snowflakes.Snowflake(542134)
        )
        cache_impl.get_voice_state = mock.Mock(side_effect=[mock_old_voice_state, mock_new_voice_state])
        cache_impl.set_voice_state = mock.Mock()
        assert cache_impl.update_voice_state(voice_state) == (mock_old_voice_state, mock_new_voice_state)
        cache_impl.set_voice_state.assert_called_once_with(voice_state)
        cache_impl.get_voice_state.assert_has_calls(
            [
                mock.call(snowflakes.Snowflake(43123123), snowflakes.Snowflake(542134)),
                mock.call(snowflakes.Snowflake(43123123), snowflakes.Snowflake(542134)),
            ]
        )
