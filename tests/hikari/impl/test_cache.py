# -*- coding: utf-8 -*-
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
import datetime

import mock
import pytest

from hikari import embeds
from hikari import emojis
from hikari import guilds
from hikari import invites
from hikari import messages
from hikari import snowflakes
from hikari import stickers
from hikari import undefined
from hikari import users
from hikari import voices
from hikari.api import config as config_api
from hikari.impl import cache as cache_impl_
from hikari.impl import config
from hikari.internal import cache as cache_utilities
from hikari.internal import collections
from tests.hikari import hikari_test_helpers


class StubModel(snowflakes.Unique):
    id = None

    def __init__(self, id=0):
        self.id = snowflakes.Snowflake(id)


class TestCacheImpl:
    @pytest.fixture
    def app_impl(self):
        return mock.Mock()

    @pytest.fixture
    def cache_impl(self, app_impl):
        return hikari_test_helpers.mock_class_namespace(cache_impl_.CacheImpl, slots_=False)(
            app=app_impl, settings=config.CacheSettings()
        )

    def test__init___(self, app_impl):
        with mock.patch.object(cache_impl_.CacheImpl, "_create_cache") as create_cache:
            cache_impl_.CacheImpl(app_impl, config.CacheSettings())

        create_cache.assert_called_once_with()

    def test__is_cache_enabled_for(self, cache_impl):
        cache_impl._settings.components = config_api.CacheComponents.MESSAGES | config_api.CacheComponents.GUILDS

        assert cache_impl._is_cache_enabled_for(config_api.CacheComponents.MESSAGES) is True

    def test__increment_ref_count(self, cache_impl):
        mock_obj = mock.Mock(ref_count=10)

        cache_impl._increment_ref_count(mock_obj, 10)

        assert mock_obj.ref_count == 20

    def test_clear(self, cache_impl):
        cache_impl._create_cache = mock.Mock()

        cache_impl.clear()

        cache_impl._create_cache.assert_called_once_with()

    def test_clear_dm_channel_ids(self, cache_impl):
        cache_impl._dm_channel_entries = collections.FreezableDict({123: 5423, 23123: 54123123})

        result = cache_impl.clear_dm_channel_ids()

        assert result == {123: 5423, 23123: 54123123}
        assert cache_impl._dm_channel_entries == {}

    def test_delete_dm_channel_id(self, cache_impl):
        cache_impl._dm_channel_entries = collections.FreezableDict({54123: 2123123, 5434: 1234})

        result = cache_impl.delete_dm_channel_id(54123)

        assert result == 2123123
        assert cache_impl._dm_channel_entries == {5434: 1234}

    def test_delete_dm_channel_id_for_unknown_user(self, cache_impl):
        cache_impl._dm_channel_entries = collections.FreezableDict({54123: 2123123, 5434: 1234})

        result = cache_impl.delete_dm_channel_id(65234123123)

        assert result is None
        assert cache_impl._dm_channel_entries == {54123: 2123123, 5434: 1234}

    def test_get_dm_channel_id(self, cache_impl):
        cache_impl._dm_channel_entries = collections.FreezableDict({24123123: 453123, 5423: 123, 653: 1223})

        assert cache_impl.get_dm_channel_id(5423) == 123

    def test_get_dm_channel_id_for_unknown_user(self, cache_impl):
        cache_impl._dm_channel_entries = collections.FreezableDict({24123123: 453123, 5423: 123, 653: 1223})

        assert cache_impl.get_dm_channel_id(65656565) is None

    def test_get_dm_channel_ids_view(self, cache_impl):
        cache_impl._dm_channel_entries = collections.FreezableDict({222: 333, 643: 213, 54234: 1231321})

        assert cache_impl.get_dm_channel_ids_view() == {222: 333, 643: 213, 54234: 1231321}

    def test_set_dm_channel_id(self, cache_impl):
        cache_impl._user_entries = collections.FreezableDict({43123123: object()})

        cache_impl.set_dm_channel_id(StubModel(43123123), StubModel(12222))

        assert cache_impl._dm_channel_entries == {43123123: 12222}

    def test__build_emoji(self, cache_impl):
        mock_user = mock.MagicMock(users.User)
        emoji_data = cache_utilities.KnownCustomEmojiData(
            id=snowflakes.Snowflake(1233534234),
            name="OKOKOKOKOK",
            is_animated=True,
            guild_id=snowflakes.Snowflake(65234123),
            role_ids=(snowflakes.Snowflake(1235123), snowflakes.Snowflake(763245234)),
            user=cache_utilities.RefCell(mock_user),
            is_colons_required=False,
            is_managed=False,
            is_available=True,
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

    def test__build_emoji_with_no_user(self, cache_impl):
        emoji_data = cache_utilities.KnownCustomEmojiData(
            id=snowflakes.Snowflake(1233534234),
            name="OKOKOKOKOK",
            is_animated=True,
            guild_id=snowflakes.Snowflake(65234123),
            role_ids=(snowflakes.Snowflake(1235123), snowflakes.Snowflake(763245234)),
            user=None,
            is_colons_required=False,
            is_managed=False,
            is_available=True,
        )
        cache_impl._build_user = mock.Mock()

        emoji = cache_impl._build_emoji(emoji_data)

        cache_impl._build_user.assert_not_called()
        assert emoji.user is None

    def test_clear_emojis(self, cache_impl):
        mock_user_1 = mock.Mock(cache_utilities.RefCell[users.User])
        mock_user_2 = mock.Mock(cache_utilities.RefCell[users.User])
        mock_emoji_data_1 = mock.Mock(cache_utilities.KnownCustomEmojiData, user=mock_user_1)
        mock_emoji_data_2 = mock.Mock(cache_utilities.KnownCustomEmojiData, user=mock_user_2)
        mock_emoji_data_3 = mock.Mock(cache_utilities.KnownCustomEmojiData, user=None)
        mock_emoji_1 = mock.Mock(emojis.Emoji)
        mock_emoji_2 = mock.Mock(emojis.Emoji)
        mock_emoji_3 = mock.Mock(emojis.Emoji)
        cache_impl._emoji_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(43123123): mock_emoji_data_1,
                snowflakes.Snowflake(87643523): mock_emoji_data_2,
                snowflakes.Snowflake(6873451): mock_emoji_data_3,
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
        cache_impl._garbage_collect_user.assert_has_calls(
            [mock.call(mock_user_1, decrement=1), mock.call(mock_user_2, decrement=1)]
        )
        cache_impl._build_emoji.assert_has_calls(
            [mock.call(mock_emoji_data_1), mock.call(mock_emoji_data_2), mock.call(mock_emoji_data_3)]
        )

    def test_clear_emojis_for_guild(self, cache_impl):
        mock_user_1 = mock.Mock(cache_utilities.RefCell[users.User])
        mock_user_2 = mock.Mock(cache_utilities.RefCell[users.User])
        mock_emoji_data_1 = mock.Mock(cache_utilities.KnownCustomEmojiData, user=mock_user_1)
        mock_emoji_data_2 = mock.Mock(cache_utilities.KnownCustomEmojiData, user=mock_user_2)
        mock_emoji_data_3 = mock.Mock(cache_utilities.KnownCustomEmojiData, user=None)
        mock_other_emoji_data = mock.Mock(cache_utilities.KnownCustomEmojiData)
        emoji_ids = collections.SnowflakeSet()
        emoji_ids.add_all(
            [snowflakes.Snowflake(43123123), snowflakes.Snowflake(87643523), snowflakes.Snowflake(6873451)]
        )
        mock_emoji_1 = mock.Mock(emojis.Emoji)
        mock_emoji_2 = mock.Mock(emojis.Emoji)
        mock_emoji_3 = mock.Mock(emojis.Emoji)
        cache_impl._emoji_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(6873451): mock_emoji_data_1,
                snowflakes.Snowflake(43123123): mock_emoji_data_2,
                snowflakes.Snowflake(87643523): mock_emoji_data_3,
                snowflakes.Snowflake(111): mock_other_emoji_data,
            }
        )
        guild_record = cache_utilities.GuildRecord(emojis=emoji_ids)
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(432123123): guild_record,
                snowflakes.Snowflake(1): mock.Mock(cache_utilities.GuildRecord),
            }
        )
        cache_impl._build_emoji = mock.Mock(side_effect=[mock_emoji_1, mock_emoji_2, mock_emoji_3])
        cache_impl._remove_guild_record_if_empty = mock.Mock()
        cache_impl._garbage_collect_user = mock.Mock()

        emoji_mapping = cache_impl.clear_emojis_for_guild(StubModel(432123123))

        cache_impl._garbage_collect_user.assert_has_calls(
            [mock.call(mock_user_1, decrement=1), mock.call(mock_user_2, decrement=1)]
        )
        cache_impl._remove_guild_record_if_empty.assert_called_once_with(snowflakes.Snowflake(432123123), guild_record)
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
            [mock.call(mock_emoji_data_1), mock.call(mock_emoji_data_2), mock.call(mock_emoji_data_3)]
        )

    def test_clear_emojis_for_guild_for_unknown_emoji_cache(self, cache_impl):
        cache_impl._emoji_entries = {snowflakes.Snowflake(3123): mock.Mock(cache_utilities.KnownCustomEmojiData)}
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(432123123): cache_utilities.GuildRecord(),
                snowflakes.Snowflake(1): mock.Mock(cache_utilities.GuildRecord),
            }
        )
        cache_impl._build_emoji = mock.Mock()
        cache_impl._remove_guild_record_if_empty = mock.Mock()
        cache_impl._garbage_collect_user = mock.Mock()

        emoji_mapping = cache_impl.clear_emojis_for_guild(StubModel(432123123))

        cache_impl._garbage_collect_user.assert_not_called()
        cache_impl._remove_guild_record_if_empty.assert_not_called()
        assert emoji_mapping == {}
        cache_impl._build_emoji.assert_not_called()

    def test_clear_emojis_for_guild_for_unknown_record(self, cache_impl):
        cache_impl._emoji_entries = {snowflakes.Snowflake(123124): mock.Mock(cache_utilities.KnownCustomEmojiData)}
        cache_impl._guild_entries = collections.FreezableDict(
            {snowflakes.Snowflake(1): mock.Mock(cache_utilities.GuildRecord)}
        )
        cache_impl._build_emoji = mock.Mock()
        cache_impl._remove_guild_record_if_empty = mock.Mock()
        cache_impl._garbage_collect_user = mock.Mock()

        emoji_mapping = cache_impl.clear_emojis_for_guild(StubModel(432123123))

        cache_impl._garbage_collect_user.assert_not_called()
        cache_impl._remove_guild_record_if_empty.assert_not_called()
        assert emoji_mapping == {}
        cache_impl._build_emoji.assert_not_called()

    def test_delete_emoji(self, cache_impl):
        mock_user = object()
        mock_emoji_data = mock.Mock(
            cache_utilities.KnownCustomEmojiData, user=mock_user, guild_id=snowflakes.Snowflake(123333)
        )
        mock_other_emoji_data = mock.Mock(cache_utilities.KnownCustomEmojiData)
        mock_emoji = mock.Mock(emojis.KnownCustomEmoji)
        emoji_ids = collections.SnowflakeSet()
        emoji_ids.add_all([snowflakes.Snowflake(12354123), snowflakes.Snowflake(432123)])
        cache_impl._emoji_entries = collections.FreezableDict(
            {snowflakes.Snowflake(12354123): mock_emoji_data, snowflakes.Snowflake(999): mock_other_emoji_data}
        )
        cache_impl._guild_entries = collections.FreezableDict(
            {snowflakes.Snowflake(123333): cache_utilities.GuildRecord(emojis=emoji_ids)}
        )
        cache_impl._garbage_collect_user = mock.Mock()
        cache_impl._build_emoji = mock.Mock(return_value=mock_emoji)

        result = cache_impl.delete_emoji(StubModel(12354123))

        assert result is mock_emoji
        assert cache_impl._emoji_entries == {snowflakes.Snowflake(999): mock_other_emoji_data}
        assert cache_impl._guild_entries[snowflakes.Snowflake(123333)].emojis == {snowflakes.Snowflake(432123)}
        cache_impl._build_emoji.assert_called_once_with(mock_emoji_data)
        cache_impl._garbage_collect_user.assert_called_once_with(mock_user, decrement=1)

    def test_delete_emoji_without_user(self, cache_impl):
        mock_emoji_data = mock.Mock(
            cache_utilities.KnownCustomEmojiData, user=None, guild_id=snowflakes.Snowflake(123333)
        )
        mock_other_emoji_data = mock.Mock(cache_utilities.KnownCustomEmojiData)
        mock_emoji = mock.Mock(emojis.KnownCustomEmoji)
        emoji_ids = collections.SnowflakeSet()
        emoji_ids.add_all([snowflakes.Snowflake(12354123), snowflakes.Snowflake(432123)])
        cache_impl._emoji_entries = collections.FreezableDict(
            {snowflakes.Snowflake(12354123): mock_emoji_data, snowflakes.Snowflake(999): mock_other_emoji_data}
        )
        cache_impl._guild_entries = collections.FreezableDict(
            {snowflakes.Snowflake(123333): cache_utilities.GuildRecord(emojis=emoji_ids)}
        )
        cache_impl._garbage_collect_user = mock.Mock()
        cache_impl._build_emoji = mock.Mock(return_value=mock_emoji)

        result = cache_impl.delete_emoji(StubModel(12354123))

        assert result is mock_emoji
        assert cache_impl._emoji_entries == {snowflakes.Snowflake(999): mock_other_emoji_data}
        assert cache_impl._guild_entries[snowflakes.Snowflake(123333)].emojis == {snowflakes.Snowflake(432123)}
        cache_impl._build_emoji.assert_called_once_with(mock_emoji_data)
        cache_impl._garbage_collect_user.assert_not_called()

    def test_delete_emoji_for_unknown_emoji(self, cache_impl):
        cache_impl._garbage_collect_user = mock.Mock()
        cache_impl._build_emoji = mock.Mock()

        result = cache_impl.delete_emoji(StubModel(12354123))

        assert result is None
        cache_impl._build_emoji.assert_not_called()
        cache_impl._garbage_collect_user.assert_not_called()

    def test_get_emoji(self, cache_impl):
        mock_emoji_data = mock.Mock(cache_utilities.KnownCustomEmojiData)
        mock_emoji = mock.Mock(emojis.KnownCustomEmoji)
        cache_impl._build_emoji = mock.Mock(return_value=mock_emoji)
        cache_impl._emoji_entries = collections.FreezableDict({snowflakes.Snowflake(3422123): mock_emoji_data})

        result = cache_impl.get_emoji(StubModel(3422123))

        assert result is mock_emoji
        cache_impl._build_emoji.assert_called_once_with(mock_emoji_data)

    def test_get_emoji_with_unknown_emoji(self, cache_impl):
        cache_impl._build_emoji = mock.Mock()

        result = cache_impl.get_emoji(StubModel(3422123))

        assert result is None
        cache_impl._build_emoji.assert_not_called()

    def test_get_emojis_view(self, cache_impl):
        mock_emoji_data_1 = mock.Mock(cache_utilities.KnownCustomEmojiData)
        mock_emoji_data_2 = mock.Mock(cache_utilities.KnownCustomEmojiData)
        mock_emoji_1 = mock.Mock(emojis.KnownCustomEmoji)
        mock_emoji_2 = mock.Mock(emojis.KnownCustomEmoji)
        cache_impl._emoji_entries = collections.FreezableDict(
            {snowflakes.Snowflake(123123123): mock_emoji_data_1, snowflakes.Snowflake(43156234): mock_emoji_data_2}
        )
        cache_impl._build_emoji = mock.Mock(side_effect=[mock_emoji_1, mock_emoji_2])

        result = cache_impl.get_emojis_view()

        assert result == {snowflakes.Snowflake(123123123): mock_emoji_1, snowflakes.Snowflake(43156234): mock_emoji_2}
        cache_impl._build_emoji.assert_has_calls([mock.call(mock_emoji_data_1), mock.call(mock_emoji_data_2)])

    def test_get_emojis_view_for_guild(self, cache_impl):
        mock_emoji_data_1 = mock.Mock(cache_utilities.KnownCustomEmojiData)
        mock_emoji_data_2 = mock.Mock(cache_utilities.KnownCustomEmojiData)
        mock_emoji_1 = mock.Mock(emojis.KnownCustomEmoji)
        mock_emoji_2 = mock.Mock(emojis.KnownCustomEmoji)
        emoji_ids = collections.SnowflakeSet()
        emoji_ids.add_all([snowflakes.Snowflake(65123), snowflakes.Snowflake(43156234)])
        cache_impl._emoji_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(65123): mock_emoji_data_1,
                snowflakes.Snowflake(942123): mock.Mock(cache_utilities.KnownCustomEmojiData),
                snowflakes.Snowflake(43156234): mock_emoji_data_2,
            }
        )
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(99999): mock.Mock(cache_utilities.GuildRecord),
                snowflakes.Snowflake(9342123): cache_utilities.GuildRecord(emojis=emoji_ids),
            }
        )
        cache_impl._build_emoji = mock.Mock(side_effect=[mock_emoji_1, mock_emoji_2])

        result = cache_impl.get_emojis_view_for_guild(StubModel(9342123))

        assert result == {snowflakes.Snowflake(65123): mock_emoji_1, snowflakes.Snowflake(43156234): mock_emoji_2}
        cache_impl._build_emoji.assert_has_calls([mock.call(mock_emoji_data_1), mock.call(mock_emoji_data_2)])

    def test_get_emojis_view_for_guild_for_unknown_emoji_cache(self, cache_impl):
        cache_impl._emoji_entries = collections.FreezableDict(
            {snowflakes.Snowflake(9999): mock.Mock(cache_utilities.KnownCustomEmojiData)}
        )
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(99999): mock.Mock(cache_utilities.GuildRecord),
                snowflakes.Snowflake(9342123): cache_utilities.GuildRecord(),
            }
        )
        cache_impl._build_emoji = mock.Mock()

        result = cache_impl.get_emojis_view_for_guild(StubModel(9342123))

        assert result == {}
        cache_impl._build_emoji.assert_not_called()

    def test_get_emojis_view_for_guild_for_unknown_record(self, cache_impl):
        cache_impl._emoji_entries = collections.FreezableDict(
            {snowflakes.Snowflake(12354345): mock.Mock(cache_utilities.KnownCustomEmojiData)}
        )
        cache_impl._guild_entries = collections.FreezableDict(
            {snowflakes.Snowflake(9342123): cache_utilities.GuildRecord()}
        )
        cache_impl._build_emoji = mock.Mock()

        result = cache_impl.get_emojis_view_for_guild(StubModel(9342123))

        assert result == {}
        cache_impl._build_emoji.assert_not_called()

    def test_set_emoji(self, cache_impl):
        mock_user = mock.Mock(users.User, id=snowflakes.Snowflake(654234))
        mock_reffed_user = cache_utilities.RefCell(mock_user)
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
        cache_impl._set_user = mock.Mock(return_value=mock_reffed_user)
        cache_impl._increment_ref_count = mock.Mock()

        cache_impl.set_emoji(emoji)

        assert 65234 in cache_impl._guild_entries
        assert cache_impl._guild_entries[snowflakes.Snowflake(65234)].emojis
        assert 5123123 in cache_impl._guild_entries[snowflakes.Snowflake(65234)].emojis
        assert 5123123 in cache_impl._emoji_entries
        emoji_data = cache_impl._emoji_entries[snowflakes.Snowflake(5123123)]
        cache_impl._set_user.assert_called_once_with(mock_user)
        cache_impl._increment_ref_count.assert_called_once_with(mock_reffed_user)
        assert emoji_data.id == snowflakes.Snowflake(5123123)
        assert emoji_data.name == "A name"
        assert emoji_data.is_animated is False
        assert emoji_data.guild_id == snowflakes.Snowflake(65234)
        assert emoji_data.role_ids == (snowflakes.Snowflake(213212), snowflakes.Snowflake(6873245))
        assert isinstance(emoji_data.role_ids, tuple)
        assert emoji_data.user is mock_reffed_user
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
            {snowflakes.Snowflake(5123123): mock.Mock(cache_utilities.KnownCustomEmojiData)}
        )
        cache_impl._set_user = mock.Mock()
        cache_impl._increment_user_ref_count = mock.Mock()

        cache_impl.set_emoji(emoji)

        assert 5123123 in cache_impl._emoji_entries
        cache_impl._set_user.assert_called_once_with(mock_user)
        cache_impl._increment_user_ref_count.assert_not_called()

    def test_update_emoji(self, cache_impl):
        mock_cached_emoji_1 = mock.Mock(emojis.KnownCustomEmoji)
        mock_cached_emoji_2 = mock.Mock(emojis.KnownCustomEmoji)
        mock_emoji = mock.Mock(emojis.KnownCustomEmoji, id=snowflakes.Snowflake(54123123))
        cache_impl.get_emoji = mock.Mock(side_effect=[mock_cached_emoji_1, mock_cached_emoji_2])
        cache_impl.set_emoji = mock.Mock()

        result = cache_impl.update_emoji(mock_emoji)

        assert result == (mock_cached_emoji_1, mock_cached_emoji_2)
        cache_impl.get_emoji.assert_has_calls(
            [mock.call(snowflakes.Snowflake(54123123)), mock.call(snowflakes.Snowflake(54123123))]
        )
        cache_impl.set_emoji.assert_called_once_with(mock_emoji)

    def test__build_sticker(self, cache_impl):
        mock_user = mock.MagicMock(users.User)
        sticker_data = cache_utilities.GuildStickerData(
            id=snowflakes.Snowflake(1233534234),
            name="OKOKOKOKOK",
            description="hi",
            guild_id=snowflakes.Snowflake(65234123),
            tag="lol",
            format_type=1,
            user=cache_utilities.RefCell(mock_user),
            is_available=True,
        )

        sticker = cache_impl._build_sticker(sticker_data)

        assert sticker.id == snowflakes.Snowflake(1233534234)
        assert sticker.name == "OKOKOKOKOK"
        assert sticker.guild_id == snowflakes.Snowflake(65234123)
        assert sticker.user == mock_user
        assert sticker.user is not mock_user
        assert sticker.tag == "lol"
        assert sticker.format_type == 1
        assert sticker.is_available is True
        assert sticker.description == "hi"

    def test__build_sticker_with_no_user(self, cache_impl):
        sticker_data = cache_utilities.GuildStickerData(
            id=snowflakes.Snowflake(1233534234),
            name="OKOKOKOKOK",
            description="hi",
            guild_id=snowflakes.Snowflake(65234123),
            tag="lol",
            format_type=1,
            user=None,
            is_available=True,
        )
        cache_impl._build_user = mock.Mock()

        sticker = cache_impl._build_sticker(sticker_data)

        cache_impl._build_user.assert_not_called()
        assert sticker.user is None

    def test_clear_stickers(self, cache_impl):
        mock_user_1 = mock.Mock(cache_utilities.RefCell[users.User])
        mock_user_2 = mock.Mock(cache_utilities.RefCell[users.User])
        mock_sticker_data_1 = mock.Mock(cache_utilities.GuildStickerData, user=mock_user_1)
        mock_sticker_data_2 = mock.Mock(cache_utilities.GuildStickerData, user=mock_user_2)
        mock_sticker_data_3 = mock.Mock(cache_utilities.GuildStickerData, user=None)
        mock_sticker_1 = mock.Mock(stickers.GuildSticker)
        mock_sticker_2 = mock.Mock(stickers.GuildSticker)
        mock_sticker_3 = mock.Mock(stickers.GuildSticker)
        cache_impl._sticker_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(43123123): mock_sticker_data_1,
                snowflakes.Snowflake(87643523): mock_sticker_data_2,
                snowflakes.Snowflake(6873451): mock_sticker_data_3,
            }
        )
        cache_impl._build_sticker = mock.Mock(side_effect=[mock_sticker_1, mock_sticker_2, mock_sticker_3])
        cache_impl._garbage_collect_user = mock.Mock()

        view = cache_impl.clear_stickers()

        assert view == {
            snowflakes.Snowflake(43123123): mock_sticker_1,
            snowflakes.Snowflake(87643523): mock_sticker_2,
            snowflakes.Snowflake(6873451): mock_sticker_3,
        }
        assert cache_impl._sticker_entries == {}
        cache_impl._garbage_collect_user.assert_has_calls(
            [mock.call(mock_user_1, decrement=1), mock.call(mock_user_2, decrement=1)]
        )
        cache_impl._build_sticker.assert_has_calls(
            [mock.call(mock_sticker_data_1), mock.call(mock_sticker_data_2), mock.call(mock_sticker_data_3)]
        )

    def test_clear_stickers_for_guild(self, cache_impl):
        mock_user_1 = mock.Mock(cache_utilities.RefCell[users.User])
        mock_user_2 = mock.Mock(cache_utilities.RefCell[users.User])
        mock_sticker_data_1 = mock.Mock(cache_utilities.GuildStickerData, user=mock_user_1)
        mock_sticker_data_2 = mock.Mock(cache_utilities.GuildStickerData, user=mock_user_2)
        mock_sticker_data_3 = mock.Mock(cache_utilities.GuildStickerData, user=None)
        mock_other_sticker_data = mock.Mock(cache_utilities.GuildStickerData)
        sticker_ids = collections.SnowflakeSet()
        sticker_ids.add_all(
            [snowflakes.Snowflake(43123123), snowflakes.Snowflake(87643523), snowflakes.Snowflake(6873451)]
        )
        mock_sticker_1 = mock.Mock(stickers.GuildSticker)
        mock_sticker_2 = mock.Mock(stickers.GuildSticker)
        mock_sticker_3 = mock.Mock(stickers.GuildSticker)
        cache_impl._sticker_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(6873451): mock_sticker_data_1,
                snowflakes.Snowflake(43123123): mock_sticker_data_2,
                snowflakes.Snowflake(87643523): mock_sticker_data_3,
                snowflakes.Snowflake(111): mock_other_sticker_data,
            }
        )
        guild_record = cache_utilities.GuildRecord(stickers=sticker_ids)
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(432123123): guild_record,
                snowflakes.Snowflake(1): mock.Mock(cache_utilities.GuildRecord),
            }
        )
        cache_impl._build_sticker = mock.Mock(side_effect=[mock_sticker_1, mock_sticker_2, mock_sticker_3])
        cache_impl._remove_guild_record_if_empty = mock.Mock()
        cache_impl._garbage_collect_user = mock.Mock()

        sticker_mapping = cache_impl.clear_stickers_for_guild(StubModel(432123123))

        cache_impl._garbage_collect_user.assert_has_calls(
            [mock.call(mock_user_1, decrement=1), mock.call(mock_user_2, decrement=1)]
        )
        cache_impl._remove_guild_record_if_empty.assert_called_once_with(snowflakes.Snowflake(432123123), guild_record)
        assert sticker_mapping == {
            snowflakes.Snowflake(6873451): mock_sticker_1,
            snowflakes.Snowflake(43123123): mock_sticker_2,
            snowflakes.Snowflake(87643523): mock_sticker_3,
        }
        assert cache_impl._sticker_entries == collections.FreezableDict(
            {snowflakes.Snowflake(111): mock_other_sticker_data}
        )
        assert cache_impl._guild_entries[snowflakes.Snowflake(432123123)].stickers is None
        cache_impl._build_sticker.assert_has_calls(
            [mock.call(mock_sticker_data_1), mock.call(mock_sticker_data_2), mock.call(mock_sticker_data_3)]
        )

    def test_clear_stickers_for_guild_for_unknown_sticker_cache(self, cache_impl):
        cache_impl._sticker_entries = {snowflakes.Snowflake(3123): mock.Mock(cache_utilities.GuildStickerData)}
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(432123123): cache_utilities.GuildRecord(),
                snowflakes.Snowflake(1): mock.Mock(cache_utilities.GuildRecord),
            }
        )
        cache_impl._build_sticker = mock.Mock()
        cache_impl._remove_guild_record_if_empty = mock.Mock()
        cache_impl._garbage_collect_user = mock.Mock()

        sticker_mapping = cache_impl.clear_stickers_for_guild(StubModel(432123123))

        cache_impl._garbage_collect_user.assert_not_called()
        cache_impl._remove_guild_record_if_empty.assert_not_called()
        assert sticker_mapping == {}
        cache_impl._build_sticker.assert_not_called()

    def test_clear_stickers_for_guild_for_unknown_record(self, cache_impl):
        cache_impl._sticker_entries = {snowflakes.Snowflake(123124): mock.Mock(cache_utilities.GuildStickerData)}
        cache_impl._guild_entries = collections.FreezableDict(
            {snowflakes.Snowflake(1): mock.Mock(cache_utilities.GuildRecord)}
        )
        cache_impl._build_sticker = mock.Mock()
        cache_impl._remove_guild_record_if_empty = mock.Mock()
        cache_impl._garbage_collect_user = mock.Mock()

        sticker_mapping = cache_impl.clear_stickers_for_guild(StubModel(432123123))

        cache_impl._garbage_collect_user.assert_not_called()
        cache_impl._remove_guild_record_if_empty.assert_not_called()
        assert sticker_mapping == {}
        cache_impl._build_sticker.assert_not_called()

    def test_delete_sticker(self, cache_impl):
        mock_user = object()
        mock_sticker_data = mock.Mock(
            cache_utilities.GuildStickerData, user=mock_user, guild_id=snowflakes.Snowflake(123333)
        )
        mock_other_sticker_data = mock.Mock(cache_utilities.GuildStickerData)
        mock_sticker = mock.Mock(stickers.GuildSticker)
        sticker_ids = collections.SnowflakeSet()
        sticker_ids.add_all([snowflakes.Snowflake(12354123), snowflakes.Snowflake(432123)])
        cache_impl._sticker_entries = collections.FreezableDict(
            {snowflakes.Snowflake(12354123): mock_sticker_data, snowflakes.Snowflake(999): mock_other_sticker_data}
        )
        cache_impl._guild_entries = collections.FreezableDict(
            {snowflakes.Snowflake(123333): cache_utilities.GuildRecord(stickers=sticker_ids)}
        )
        cache_impl._garbage_collect_user = mock.Mock()
        cache_impl._build_sticker = mock.Mock(return_value=mock_sticker)

        result = cache_impl.delete_sticker(StubModel(12354123))

        assert result is mock_sticker
        assert cache_impl._sticker_entries == {snowflakes.Snowflake(999): mock_other_sticker_data}
        assert cache_impl._guild_entries[snowflakes.Snowflake(123333)].stickers == {snowflakes.Snowflake(432123)}
        cache_impl._build_sticker.assert_called_once_with(mock_sticker_data)
        cache_impl._garbage_collect_user.assert_called_once_with(mock_user, decrement=1)

    def test_delete_sticker_without_user(self, cache_impl):
        mock_sticker_data = mock.Mock(
            cache_utilities.GuildStickerData, user=None, guild_id=snowflakes.Snowflake(123333)
        )
        mock_other_sticker_data = mock.Mock(cache_utilities.GuildStickerData)
        mock_sticker = mock.Mock(stickers.GuildSticker)
        sticker_ids = collections.SnowflakeSet()
        sticker_ids.add_all([snowflakes.Snowflake(12354123), snowflakes.Snowflake(432123)])
        cache_impl._sticker_entries = collections.FreezableDict(
            {snowflakes.Snowflake(12354123): mock_sticker_data, snowflakes.Snowflake(999): mock_other_sticker_data}
        )
        cache_impl._guild_entries = collections.FreezableDict(
            {snowflakes.Snowflake(123333): cache_utilities.GuildRecord(stickers=sticker_ids)}
        )
        cache_impl._garbage_collect_user = mock.Mock()
        cache_impl._build_sticker = mock.Mock(return_value=mock_sticker)

        result = cache_impl.delete_sticker(StubModel(12354123))

        assert result is mock_sticker
        assert cache_impl._sticker_entries == {snowflakes.Snowflake(999): mock_other_sticker_data}
        assert cache_impl._guild_entries[snowflakes.Snowflake(123333)].stickers == {snowflakes.Snowflake(432123)}
        cache_impl._build_sticker.assert_called_once_with(mock_sticker_data)
        cache_impl._garbage_collect_user.assert_not_called()

    def test_delete_sticker_for_unknown_sticker(self, cache_impl):
        cache_impl._garbage_collect_user = mock.Mock()
        cache_impl._build_sticker = mock.Mock()

        result = cache_impl.delete_sticker(StubModel(12354123))

        assert result is None
        cache_impl._build_sticker.assert_not_called()
        cache_impl._garbage_collect_user.assert_not_called()

    def test_get_sticker(self, cache_impl):
        mock_sticker_data = mock.Mock(cache_utilities.GuildStickerData)
        mock_sticker = mock.Mock(emojis.KnownCustomEmoji)
        cache_impl._build_sticker = mock.Mock(return_value=mock_sticker)
        cache_impl._sticker_entries = collections.FreezableDict({snowflakes.Snowflake(3422123): mock_sticker_data})

        result = cache_impl.get_sticker(StubModel(3422123))

        assert result is mock_sticker
        cache_impl._build_sticker.assert_called_once_with(mock_sticker_data)

    def test_get_sticker_with_unknown_sticker(self, cache_impl):
        cache_impl._build_sticker = mock.Mock()

        result = cache_impl.get_sticker(StubModel(3422123))

        assert result is None
        cache_impl._build_sticker.assert_not_called()

    def test_get_stickers_view(self, cache_impl):
        mock_sticker_data_1 = mock.Mock(cache_utilities.GuildStickerData)
        mock_sticker_data_2 = mock.Mock(cache_utilities.GuildStickerData)
        mock_sticker_1 = mock.Mock(stickers.GuildSticker)
        mock_sticker_2 = mock.Mock(stickers.GuildSticker)
        cache_impl._sticker_entries = collections.FreezableDict(
            {snowflakes.Snowflake(123123123): mock_sticker_data_1, snowflakes.Snowflake(43156234): mock_sticker_data_2}
        )
        cache_impl._build_sticker = mock.Mock(side_effect=[mock_sticker_1, mock_sticker_2])

        result = cache_impl.get_stickers_view()

        assert result == {
            snowflakes.Snowflake(123123123): mock_sticker_1,
            snowflakes.Snowflake(43156234): mock_sticker_2,
        }
        cache_impl._build_sticker.assert_has_calls([mock.call(mock_sticker_data_1), mock.call(mock_sticker_data_2)])

    def test_get_stickers_view_for_guild(self, cache_impl):
        mock_sticker_data_1 = mock.Mock(cache_utilities.GuildStickerData)
        mock_sticker_data_2 = mock.Mock(cache_utilities.GuildStickerData)
        mock_sticker_1 = mock.Mock(stickers.GuildSticker)
        mock_sticker_2 = mock.Mock(stickers.GuildSticker)
        sticker_ids = collections.SnowflakeSet()
        sticker_ids.add_all([snowflakes.Snowflake(65123), snowflakes.Snowflake(43156234)])
        cache_impl._sticker_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(65123): mock_sticker_data_1,
                snowflakes.Snowflake(942123): mock.Mock(cache_utilities.GuildStickerData),
                snowflakes.Snowflake(43156234): mock_sticker_data_2,
            }
        )
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(99999): mock.Mock(cache_utilities.GuildRecord),
                snowflakes.Snowflake(9342123): cache_utilities.GuildRecord(stickers=sticker_ids),
            }
        )
        cache_impl._build_sticker = mock.Mock(side_effect=[mock_sticker_1, mock_sticker_2])

        result = cache_impl.get_stickers_view_for_guild(StubModel(9342123))

        assert result == {snowflakes.Snowflake(65123): mock_sticker_1, snowflakes.Snowflake(43156234): mock_sticker_2}
        cache_impl._build_sticker.assert_has_calls([mock.call(mock_sticker_data_1), mock.call(mock_sticker_data_2)])

    def test_get_stickers_view_for_guild_for_unknown_sticker_cache(self, cache_impl):
        cache_impl._sticker_entries = collections.FreezableDict(
            {snowflakes.Snowflake(9999): mock.Mock(cache_utilities.GuildStickerData)}
        )
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(99999): mock.Mock(cache_utilities.GuildRecord),
                snowflakes.Snowflake(9342123): cache_utilities.GuildRecord(),
            }
        )
        cache_impl._build_sticker = mock.Mock()

        result = cache_impl.get_stickers_view_for_guild(StubModel(9342123))

        assert result == {}
        cache_impl._build_sticker.assert_not_called()

    def test_get_stickers_view_for_guild_for_unknown_record(self, cache_impl):
        cache_impl._sticker_entries = collections.FreezableDict(
            {snowflakes.Snowflake(12354345): mock.Mock(cache_utilities.GuildStickerData)}
        )
        cache_impl._guild_entries = collections.FreezableDict(
            {snowflakes.Snowflake(9342123): cache_utilities.GuildRecord()}
        )
        cache_impl._build_sticker = mock.Mock()

        result = cache_impl.get_stickers_view_for_guild(StubModel(9342123))

        assert result == {}
        cache_impl._build_sticker.assert_not_called()

    def test_set_sticker(self, cache_impl):
        mock_user = mock.Mock(users.User, id=snowflakes.Snowflake(654234))
        mock_reffed_user = cache_utilities.RefCell(mock_user)
        sticker = stickers.GuildSticker(
            id=snowflakes.Snowflake(5123123),
            name="A name",
            guild_id=snowflakes.Snowflake(65234),
            user=mock_user,
            description="Jax cute",
            tag="lul",
            format_type=1,
            is_available=False,
        )
        cache_impl._set_user = mock.Mock(return_value=mock_reffed_user)
        cache_impl._increment_ref_count = mock.Mock()

        cache_impl.set_sticker(sticker)

        assert 65234 in cache_impl._guild_entries
        assert cache_impl._guild_entries[snowflakes.Snowflake(65234)].stickers
        assert 5123123 in cache_impl._guild_entries[snowflakes.Snowflake(65234)].stickers
        assert 5123123 in cache_impl._sticker_entries
        sticker_data = cache_impl._sticker_entries[snowflakes.Snowflake(5123123)]
        cache_impl._set_user.assert_called_once_with(mock_user)
        cache_impl._increment_ref_count.assert_called_once_with(mock_reffed_user)
        assert sticker_data.id == snowflakes.Snowflake(5123123)
        assert sticker_data.name == "A name"
        assert sticker_data.guild_id == snowflakes.Snowflake(65234)
        assert sticker_data.user is mock_reffed_user
        assert sticker_data.is_available is False
        assert sticker_data.format_type == 1
        assert sticker_data.tag == "lul"
        assert sticker_data.description == "Jax cute"

    def test_set_sticker_with_pre_cached_sticker(self, cache_impl):
        mock_user = mock.Mock(users.User, id=snowflakes.Snowflake(654234))
        sticker = stickers.GuildSticker(
            id=snowflakes.Snowflake(5123123),
            name="A name",
            guild_id=snowflakes.Snowflake(65234),
            description="OI",
            user=mock_user,
            tag="lul",
            format_type=1,
            is_available=False,
        )
        cache_impl._sticker_entries = collections.FreezableDict(
            {snowflakes.Snowflake(5123123): mock.Mock(cache_utilities.GuildStickerData)}
        )
        cache_impl._set_user = mock.Mock()
        cache_impl._increment_user_ref_count = mock.Mock()

        cache_impl.set_sticker(sticker)

        assert 5123123 in cache_impl._sticker_entries
        cache_impl._set_user.assert_called_once_with(mock_user)
        cache_impl._increment_user_ref_count.assert_not_called()

    def test_clear_guilds_when_no_guilds_cached(self, cache_impl):
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(423123): cache_utilities.GuildRecord(),
                snowflakes.Snowflake(675345): cache_utilities.GuildRecord(),
            }
        )

        result = cache_impl.clear_guilds()

        assert result == {}
        assert cache_impl._guild_entries == {
            snowflakes.Snowflake(423123): cache_utilities.GuildRecord(),
            snowflakes.Snowflake(675345): cache_utilities.GuildRecord(),
        }

    def test_clear_guilds(self, cache_impl):
        mock_guild_1 = mock.MagicMock(guilds.GatewayGuild)
        mock_guild_2 = mock.MagicMock(guilds.GatewayGuild)
        mock_member = mock.MagicMock(guilds.Member)
        mock_guild_3 = mock.MagicMock(guilds.GatewayGuild)
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(423123): cache_utilities.GuildRecord(),
                snowflakes.Snowflake(675345): cache_utilities.GuildRecord(guild=mock_guild_1),
                snowflakes.Snowflake(32142): cache_utilities.GuildRecord(
                    guild=mock_guild_2, members=collections.FreezableDict({snowflakes.Snowflake(3241123): mock_member})
                ),
                snowflakes.Snowflake(765345): cache_utilities.GuildRecord(guild=mock_guild_3),
                snowflakes.Snowflake(321132): cache_utilities.GuildRecord(),
            }
        )

        result = cache_impl.clear_guilds()

        assert result == {675345: mock_guild_1, 32142: mock_guild_2, 765345: mock_guild_3}
        assert cache_impl._guild_entries == {
            snowflakes.Snowflake(423123): cache_utilities.GuildRecord(),
            snowflakes.Snowflake(32142): cache_utilities.GuildRecord(
                members={snowflakes.Snowflake(3241123): mock_member}
            ),
            snowflakes.Snowflake(321132): cache_utilities.GuildRecord(),
        }

    def test_delete_guild_for_known_guild(self, cache_impl):
        mock_guild = mock.Mock(guilds.GatewayGuild)
        mock_member = mock.Mock(guilds.Member)
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(354123): cache_utilities.GuildRecord(),
                snowflakes.Snowflake(543123): cache_utilities.GuildRecord(
                    guild=mock_guild,
                    is_available=True,
                    members=collections.FreezableDict({snowflakes.Snowflake(43123): mock_member}),
                ),
            }
        )

        result = cache_impl.delete_guild(StubModel(543123))

        assert result is mock_guild
        assert cache_impl._guild_entries == {
            snowflakes.Snowflake(354123): cache_utilities.GuildRecord(),
            snowflakes.Snowflake(543123): cache_utilities.GuildRecord(
                members={snowflakes.Snowflake(43123): mock_member}
            ),
        }

    def test_delete_guild_for_removes_emptied_record(self, cache_impl):
        mock_guild = mock.Mock(guilds.GatewayGuild)
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(354123): cache_utilities.GuildRecord(),
                snowflakes.Snowflake(543123): cache_utilities.GuildRecord(guild=mock_guild, is_available=True),
            }
        )

        result = cache_impl.delete_guild(StubModel(543123))

        assert result is mock_guild
        assert cache_impl._guild_entries == {snowflakes.Snowflake(354123): cache_utilities.GuildRecord()}

    def test_delete_guild_for_unknown_guild(self, cache_impl):
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(354123): cache_utilities.GuildRecord(),
                snowflakes.Snowflake(543123): cache_utilities.GuildRecord(),
            }
        )

        result = cache_impl.delete_guild(StubModel(543123))

        assert result is None
        assert cache_impl._guild_entries == {
            snowflakes.Snowflake(354123): cache_utilities.GuildRecord(),
            snowflakes.Snowflake(543123): cache_utilities.GuildRecord(),
        }

    def test_delete_guild_for_unknown_record(self, cache_impl):
        cache_impl._guild_entries = collections.FreezableDict(
            {snowflakes.Snowflake(354123): cache_utilities.GuildRecord()}
        )

        result = cache_impl.delete_guild(StubModel(543123))

        assert result is None
        assert cache_impl._guild_entries == {snowflakes.Snowflake(354123): cache_utilities.GuildRecord()}

    def test_get_guild_first_tries_get_available_guilds(self, cache_impl):
        mock_guild = mock.MagicMock(guilds.GatewayGuild)
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(54234123): cache_utilities.GuildRecord(),
                snowflakes.Snowflake(543123): cache_utilities.GuildRecord(guild=mock_guild, is_available=True),
            }
        )

        cached_guild = cache_impl.get_guild(StubModel(543123))

        assert cached_guild == mock_guild
        assert cache_impl is not mock_guild

    def test_get_guild_then_tries_get_unavailable_guilds(self, cache_impl):
        mock_guild = mock.MagicMock(guilds.GatewayGuild)
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(543123): cache_utilities.GuildRecord(is_available=True),
                snowflakes.Snowflake(54234123): cache_utilities.GuildRecord(guild=mock_guild, is_available=False),
            }
        )

        cached_guild = cache_impl.get_guild(StubModel(54234123))

        assert cached_guild == mock_guild
        assert cache_impl is not mock_guild

    def test_get_available_guild_for_known_guild_when_available(self, cache_impl):
        mock_guild = mock.MagicMock(guilds.GatewayGuild)
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(54234123): cache_utilities.GuildRecord(),
                snowflakes.Snowflake(543123): cache_utilities.GuildRecord(guild=mock_guild, is_available=True),
            }
        )

        cached_guild = cache_impl.get_available_guild(StubModel(543123))

        assert cached_guild == mock_guild
        assert cache_impl is not mock_guild

    def test_get_available_guild_for_known_guild_when_unavailable(self, cache_impl):
        mock_guild = mock.Mock(guilds.GatewayGuild)
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(54234123): cache_utilities.GuildRecord(),
                snowflakes.Snowflake(543123): cache_utilities.GuildRecord(guild=mock_guild, is_available=False),
            }
        )

        result = cache_impl.get_available_guild(StubModel(543123))

        assert result is None

    def test_get_available_guild_for_unknown_guild(self, cache_impl):
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(54234123): cache_utilities.GuildRecord(),
                snowflakes.Snowflake(543123): cache_utilities.GuildRecord(),
            }
        )

        result = cache_impl.get_available_guild(StubModel(543123))

        assert result is None

    def test_get_available_guild_for_unknown_guild_record(self, cache_impl):
        cache_impl._guild_entries = collections.FreezableDict(
            {snowflakes.Snowflake(54234123): cache_utilities.GuildRecord()}
        )

        result = cache_impl.get_available_guild(StubModel(543123))

        assert result is None

    def test_get_unavailable_guild_for_known_guild_when_unavailable(self, cache_impl):
        mock_guild = mock.MagicMock(guilds.GatewayGuild)
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(54234123): cache_utilities.GuildRecord(),
                snowflakes.Snowflake(452131): cache_utilities.GuildRecord(guild=mock_guild, is_available=False),
            }
        )

        cached_guild = cache_impl.get_unavailable_guild(StubModel(452131))

        assert cached_guild == mock_guild
        assert cache_impl is not mock_guild

    def test_get_unavailable_guild_for_known_guild_when_available(self, cache_impl):
        mock_guild = mock.Mock(guilds.GatewayGuild)
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(54234123): cache_utilities.GuildRecord(),
                snowflakes.Snowflake(654234): cache_utilities.GuildRecord(guild=mock_guild, is_available=True),
            }
        )

        result = cache_impl.get_unavailable_guild(StubModel(654234))

        assert result is None

    def test_get_unavailable_guild_for_unknown_guild(self, cache_impl):
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(54234123): cache_utilities.GuildRecord(),
                snowflakes.Snowflake(543123): cache_utilities.GuildRecord(),
            }
        )

        result = cache_impl.get_unavailable_guild(StubModel(543123))

        assert result is None

    def test_get_unavailable_guild_for_unknown_guild_record(self, cache_impl):
        cache_impl._guild_entries = collections.FreezableDict(
            {snowflakes.Snowflake(54234123): cache_utilities.GuildRecord()}
        )

        result = cache_impl.get_unavailable_guild(StubModel(543123))

        assert result is None

    def test_get_guilds_view(self, cache_impl):
        mock_guild_1 = mock.MagicMock(guilds.GatewayGuild)
        mock_guild_2 = mock.MagicMock(guilds.GatewayGuild)
        mock_guild_3 = mock.MagicMock(guilds.GatewayGuild)
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(56132): cache_utilities.GuildRecord(guild=mock_guild_1, is_available=True),
                snowflakes.Snowflake(56234): cache_utilities.GuildRecord(),
                snowflakes.Snowflake(541123): cache_utilities.GuildRecord(guild=mock_guild_2, is_available=False),
                snowflakes.Snowflake(65234): cache_utilities.GuildRecord(guild=mock_guild_3, is_available=False),
            }
        )

        result = cache_impl.get_guilds_view()

        assert result == {
            snowflakes.Snowflake(56132): mock_guild_1,
            snowflakes.Snowflake(541123): mock_guild_2,
            snowflakes.Snowflake(65234): mock_guild_3,
        }

    def test_get_available_guilds_view(self, cache_impl):
        mock_guild_1 = mock.MagicMock(guilds.GatewayGuild)
        mock_guild_2 = mock.MagicMock(guilds.GatewayGuild)
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(4312312): cache_utilities.GuildRecord(guild=mock_guild_1, is_available=True),
                snowflakes.Snowflake(34123): cache_utilities.GuildRecord(),
                snowflakes.Snowflake(73453): cache_utilities.GuildRecord(guild=mock_guild_2, is_available=True),
                snowflakes.Snowflake(6554234): cache_utilities.GuildRecord(guild=object(), is_available=False),
            }
        )

        result = cache_impl.get_available_guilds_view()

        assert result == {snowflakes.Snowflake(4312312): mock_guild_1, snowflakes.Snowflake(73453): mock_guild_2}

    def test_get_available_guilds_view_when_no_guilds_cached(self, cache_impl):
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(4312312): cache_utilities.GuildRecord(),
                snowflakes.Snowflake(34123): cache_utilities.GuildRecord(),
                snowflakes.Snowflake(73453): cache_utilities.GuildRecord(),
            }
        )

        result = cache_impl.get_available_guilds_view()

        assert result == {}

    def test_get_unavailable_guilds_view(self, cache_impl):
        mock_guild_1 = mock.MagicMock(guilds.GatewayGuild)
        mock_guild_2 = mock.MagicMock(guilds.GatewayGuild)
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(4312312): cache_utilities.GuildRecord(guild=mock_guild_1, is_available=False),
                snowflakes.Snowflake(34123): cache_utilities.GuildRecord(),
                snowflakes.Snowflake(73453): cache_utilities.GuildRecord(guild=mock_guild_2, is_available=False),
                snowflakes.Snowflake(6554234): cache_utilities.GuildRecord(guild=object(), is_available=True),
            }
        )

        result = cache_impl.get_unavailable_guilds_view()

        assert result == {snowflakes.Snowflake(4312312): mock_guild_1, snowflakes.Snowflake(73453): mock_guild_2}

    def test_get_unavailable_guilds_view_when_no_guilds_cached(self, cache_impl):
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(4312312): cache_utilities.GuildRecord(),
                snowflakes.Snowflake(34123): cache_utilities.GuildRecord(),
                snowflakes.Snowflake(73453): cache_utilities.GuildRecord(),
            }
        )

        result = cache_impl.get_unavailable_guilds_view()

        assert result == {}

    def test_set_guild(self, cache_impl):
        mock_guild = mock.MagicMock(guilds.GatewayGuild, id=snowflakes.Snowflake(5123123))

        cache_impl.set_guild(mock_guild)

        assert 5123123 in cache_impl._guild_entries
        assert cache_impl._guild_entries[snowflakes.Snowflake(5123123)].guild == mock_guild
        assert cache_impl._guild_entries[snowflakes.Snowflake(5123123)].guild is not mock_guild
        assert cache_impl._guild_entries[snowflakes.Snowflake(5123123)].is_available is True

    def test_set_guild_availability_for_cached_guild(self, cache_impl):
        cache_impl._guild_entries = {snowflakes.Snowflake(43123): cache_utilities.GuildRecord(guild=object())}

        cache_impl.set_guild_availability(StubModel(43123), True)

        assert cache_impl._guild_entries[snowflakes.Snowflake(43123)].is_available is True

    def test_set_guild_availability_for_uncached_guild(self, cache_impl):
        cache_impl.set_guild_availability(StubModel(452234123), True)

        assert 452234123 not in cache_impl._guild_entries

    @pytest.mark.skip(reason="TODO")
    def test_update_guild(self, cache_impl): ...

    @pytest.mark.skip(reason="TODO")
    def test_clear_guild_channels(self, cache_impl): ...

    @pytest.mark.skip(reason="TODO")
    def test_clear_guild_channels_for_guild(self, cache_impl): ...

    @pytest.mark.skip(reason="TODO")
    def test_delete_guild_channel(self, cache_impl): ...

    @pytest.mark.skip(reason="TODO")
    def test_get_guild_channel(self, cache_impl): ...

    @pytest.mark.skip(reason="TODO")
    def test_get_guild_channels_view(self, cache_impl): ...

    @pytest.mark.skip(reason="TODO")
    def test_get_guild_channels_view_for_guild(self, cache_impl): ...

    @pytest.mark.skip(reason="TODO")
    def test_set_guild_channel(self, cache_impl): ...

    @pytest.mark.skip(reason="TODO")
    def test_update_guild_channel(self, cache_impl): ...

    def test__build_invite(self, cache_impl):
        mock_inviter = mock.MagicMock(users.User)
        mock_target_user = mock.MagicMock(users.User)
        mock_application = object()
        invite_data = cache_utilities.InviteData(
            code="okokok",
            guild_id=snowflakes.Snowflake(965234),
            channel_id=snowflakes.Snowflake(87345234),
            inviter=cache_utilities.RefCell(mock_inviter),
            target_type=invites.TargetType.STREAM,
            target_user=cache_utilities.RefCell(mock_target_user),
            target_application=mock_application,
            uses=42,
            max_uses=999,
            max_age=datetime.timedelta(days=7),
            is_temporary=True,
            created_at=datetime.datetime(2020, 7, 30, 7, 22, 9, 550233, tzinfo=datetime.timezone.utc),
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
        assert invite.target_type is invites.TargetType.STREAM
        assert invite.target_application is mock_application
        assert invite.approximate_active_member_count is None
        assert invite.approximate_member_count is None
        assert invite.uses == 42
        assert invite.max_uses == 999
        assert invite.max_age == datetime.timedelta(days=7)
        assert invite.is_temporary is True
        assert invite.created_at == datetime.datetime(2020, 7, 30, 7, 22, 9, 550233, tzinfo=datetime.timezone.utc)

    def test__build_invite_without_users(self, cache_impl):
        invite_data = cache_utilities.InviteData(
            code="okokok",
            guild_id=snowflakes.Snowflake(965234),
            channel_id=snowflakes.Snowflake(87345234),
            inviter=None,
            target_type=invites.TargetType.STREAM,
            target_user=None,
            target_application=None,
            uses=42,
            max_uses=999,
            max_age=datetime.timedelta(days=7),
            is_temporary=True,
            created_at=datetime.datetime(2020, 7, 30, 7, 22, 9, 550233, tzinfo=datetime.timezone.utc),
        )

        invite = cache_impl._build_invite(invite_data)

        assert invite.inviter is None
        assert invite.target_user is None

    def test_clear_invites(self, cache_impl):
        mock_target_user = mock.Mock(cache_utilities.RefCell[users.User], ref_count=5)
        mock_inviter = mock.Mock(cache_utilities.RefCell[users.User], ref_count=3)
        mock_invite_data_1 = mock.Mock(cache_utilities.InviteData, target_user=mock_target_user, inviter=mock_inviter)
        mock_invite_data_2 = mock.Mock(cache_utilities.InviteData, target_user=None, inviter=None)
        mock_invite_1 = mock.Mock(invites.InviteWithMetadata)
        mock_invite_2 = mock.Mock(invites.InviteWithMetadata)
        cache_impl._invite_entries = collections.FreezableDict(
            {"hiBye": mock_invite_data_1, "Lblalbla": mock_invite_data_2}
        )
        cache_impl._build_invite = mock.Mock(side_effect=[mock_invite_1, mock_invite_2])
        cache_impl._garbage_collect_user = mock.Mock()

        result = cache_impl.clear_invites()

        assert result == {"hiBye": mock_invite_1, "Lblalbla": mock_invite_2}
        assert cache_impl._invite_entries == {}
        cache_impl._garbage_collect_user.assert_has_calls(
            [mock.call(mock_target_user, decrement=1), mock.call(mock_inviter, decrement=1)], any_order=True
        )
        cache_impl._build_invite.assert_has_calls([mock.call(mock_invite_data_1), mock.call(mock_invite_data_2)])

    def test_clear_invites_for_guild(self, cache_impl):
        mock_target_user = mock.Mock(cache_utilities.RefCell[users.User], ref_count=4)
        mock_inviter = mock.Mock(cache_utilities.RefCell[users.User], ref_count=42)
        mock_invite_data_1 = mock.Mock(cache_utilities.InviteData, target_user=mock_target_user, inviter=mock_inviter)
        mock_invite_data_2 = mock.Mock(cache_utilities.InviteData, target_user=None, inviter=None)
        mock_other_invite_data = mock.Mock(cache_utilities.InviteData)
        mock_invite_1 = mock.Mock(invites.InviteWithMetadata)
        mock_invite_2 = mock.Mock(invites.InviteWithMetadata)
        cache_impl._invite_entries = collections.FreezableDict(
            {
                "oeoeoeoeooe": mock_invite_data_1,
                "owowowowoowowow": mock_invite_data_2,
                "oeoeoeoeoeoeoe": mock_other_invite_data,
            }
        )
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(54123): mock.Mock(cache_utilities.GuildRecord),
                snowflakes.Snowflake(999888777): cache_utilities.GuildRecord(
                    invites=["oeoeoeoeooe", "owowowowoowowow"]
                ),
            }
        )
        cache_impl._garbage_collect_user = mock.Mock()
        cache_impl._build_invite = mock.Mock(side_effect=[mock_invite_1, mock_invite_2])

        result = cache_impl.clear_invites_for_guild(StubModel(999888777))

        assert result == {"oeoeoeoeooe": mock_invite_1, "owowowowoowowow": mock_invite_2}
        assert cache_impl._invite_entries == {"oeoeoeoeoeoeoe": mock_other_invite_data}
        cache_impl._garbage_collect_user.assert_has_calls(
            [mock.call(mock_target_user, decrement=1), mock.call(mock_inviter, decrement=1)], any_order=True
        )
        cache_impl._build_invite.assert_has_calls([mock.call(mock_invite_data_1), mock.call(mock_invite_data_2)])

    def test_clear_invites_for_guild_unknown_invite_cache(self, cache_impl):
        mock_other_invite_data = mock.Mock(cache_utilities.InviteData)
        cache_impl._invite_entries = {"oeoeoeoeoeoeoe": mock_other_invite_data}
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(54123): mock.Mock(cache_utilities.GuildRecord),
                snowflakes.Snowflake(999888777): cache_utilities.GuildRecord(invites=None),
            }
        )
        cache_impl._build_invite = mock.Mock()

        result = cache_impl.clear_invites_for_guild(StubModel(765234123))

        assert result == {}
        assert cache_impl._invite_entries == {"oeoeoeoeoeoeoe": mock_other_invite_data}
        cache_impl._build_invite.assert_not_called()

    def test_clear_invites_for_guild_unknown_record(self, cache_impl):
        mock_other_invite_data = mock.Mock(cache_utilities.InviteData)
        cache_impl._invite_entries = collections.FreezableDict({"oeoeoeoeoeoeoe": mock_other_invite_data})
        cache_impl._guild_entries = collections.FreezableDict(
            {snowflakes.Snowflake(54123): mock.Mock(cache_utilities.GuildRecord)}
        )
        cache_impl._build_invite = mock.Mock()

        result = cache_impl.clear_invites_for_guild(StubModel(765234123))

        assert result == {}
        assert cache_impl._invite_entries == {"oeoeoeoeoeoeoe": mock_other_invite_data}
        cache_impl._build_invite.assert_not_called()

    def test_clear_invites_for_channel(self, cache_impl):
        mock_target_user = mock.Mock(cache_utilities.RefCell[users.User], ref_count=42)
        mock_inviter = mock.Mock(cache_utilities.RefCell[users.User], ref_count=280)
        mock_invite_data_1 = mock.Mock(
            cache_utilities.InviteData,
            target_user=mock_target_user,
            inviter=mock_inviter,
            channel_id=snowflakes.Snowflake(34123123),
        )
        mock_invite_data_2 = mock.Mock(
            cache_utilities.InviteData, target_user=None, inviter=None, channel_id=snowflakes.Snowflake(34123123)
        )
        mock_other_invite_data = mock.Mock(cache_utilities.InviteData, channel_id=snowflakes.Snowflake(9484732))
        mock_other_invite_data_2 = mock.Mock(cache_utilities.InviteData)
        mock_invite_1 = mock.Mock(invites.InviteWithMetadata)
        mock_invite_2 = mock.Mock(invites.InviteWithMetadata)
        cache_impl._invite_entries = collections.FreezableDict(
            {
                "oeoeoeoeooe": mock_invite_data_1,
                "owowowowoowowow": mock_invite_data_2,
                "oeoeoeoeoeoeoe": mock_other_invite_data,
                "oeo": mock_other_invite_data_2,
            }
        )
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(54123): mock.Mock(cache_utilities.GuildRecord),
                snowflakes.Snowflake(999888777): cache_utilities.GuildRecord(
                    invites=["oeoeoeoeooe", "owowowowoowowow", "oeoeoeoeoeoeoe"]
                ),
            }
        )
        cache_impl._build_invite = mock.Mock(side_effect=[mock_invite_1, mock_invite_2])
        cache_impl._garbage_collect_user = mock.Mock()

        result = cache_impl.clear_invites_for_channel(StubModel(999888777), StubModel(34123123))

        assert result == {"oeoeoeoeooe": mock_invite_1, "owowowowoowowow": mock_invite_2}
        cache_impl._garbage_collect_user.assert_has_calls(
            [mock.call(mock_target_user, decrement=1), mock.call(mock_inviter, decrement=1)], any_order=True
        )
        assert cache_impl._guild_entries[snowflakes.Snowflake(999888777)].invites == ["oeoeoeoeoeoeoe"]
        assert cache_impl._invite_entries == {"oeoeoeoeoeoeoe": mock_other_invite_data, "oeo": mock_other_invite_data_2}

        cache_impl._build_invite.assert_has_calls([mock.call(mock_invite_data_1), mock.call(mock_invite_data_2)])

    def test_clear_invites_for_channel_unknown_invite_cache(self, cache_impl):
        mock_other_invite_data = mock.Mock(cache_utilities.InviteData)
        cache_impl._invite_entries = collections.FreezableDict({"oeoeoeoeoeoeoe": mock_other_invite_data})
        cache_impl._user_entries = collections.FreezableDict(
            {snowflakes.Snowflake(65345352): mock.Mock(cache_utilities.RefCell)}
        )
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(54123): mock.Mock(cache_utilities.GuildRecord),
                snowflakes.Snowflake(999888777): cache_utilities.GuildRecord(invites=None),
            }
        )
        cache_impl._build_invite = mock.Mock()

        result = cache_impl.clear_invites_for_channel(StubModel(765234123), StubModel(12365345))

        assert result == {}
        assert cache_impl._invite_entries == {"oeoeoeoeoeoeoe": mock_other_invite_data}
        cache_impl._build_invite.assert_not_called()

    def test_clear_invites_for_channel_unknown_record(self, cache_impl):
        mock_other_invite_data = mock.Mock(cache_utilities.InviteData)
        cache_impl._invite_entries = collections.FreezableDict({"oeoeoeoeoeoeoe": mock_other_invite_data})
        cache_impl._user_entries = collections.FreezableDict(
            {snowflakes.Snowflake(65345352): mock.Mock(cache_utilities.RefCell)}
        )
        cache_impl._guild_entries = collections.FreezableDict(
            {snowflakes.Snowflake(54123): mock.Mock(cache_utilities.GuildRecord)}
        )
        cache_impl._build_invite = mock.Mock()

        result = cache_impl.clear_invites_for_channel(StubModel(765234123), StubModel(76234123))

        assert result == {}
        assert cache_impl._invite_entries == {"oeoeoeoeoeoeoe": mock_other_invite_data}
        cache_impl._build_invite.assert_not_called()

    def test_delete_invite(self, cache_impl):
        mock_inviter = mock.Mock(users.User, id=snowflakes.Snowflake(543123))
        mock_target_user = mock.Mock(users.User, id=snowflakes.Snowflake(9191919))
        mock_invite_data = mock.Mock(
            cache_utilities.InviteData,
            guild_id=snowflakes.Snowflake(999999999),
            inviter=mock_inviter,
            target_user=mock_target_user,
        )
        mock_other_invite_data = mock.Mock(cache_utilities.InviteData)
        mock_invite = object()
        cache_impl._invite_entries = collections.FreezableDict(
            {"blamSpat": mock_other_invite_data, "oooooooooooooo": mock_invite_data}
        )
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(1234312): mock.Mock(cache_utilities.GuildRecord),
                snowflakes.Snowflake(999999999): cache_utilities.GuildRecord(invites=["ok", "blat", "oooooooooooooo"]),
            }
        )
        cache_impl._build_invite = mock.Mock(return_value=mock_invite)
        cache_impl._garbage_collect_user = mock.Mock()
        # TODO: test when this is called
        cache_impl._remove_guild_record_if_empty = mock.Mock()

        result = cache_impl.delete_invite("oooooooooooooo")

        assert result is mock_invite
        cache_impl._build_invite.assert_called_once_with(mock_invite_data)
        cache_impl._garbage_collect_user.assert_has_calls(
            [mock.call(mock_inviter, decrement=1), mock.call(mock_target_user, decrement=1)]
        )
        assert cache_impl._invite_entries == {"blamSpat": mock_other_invite_data}
        assert cache_impl._guild_entries[snowflakes.Snowflake(999999999)].invites == ["ok", "blat"]

    def test_delete_invite_with_invite_object(self, cache_impl):
        mock_invite_data = mock.Mock(cache_utilities.InviteData)
        mock_other_invite_data = mock.Mock(cache_utilities.InviteData)
        mock_invite = mock.Mock(invites.InviteWithMetadata, inviter=None, target_user=None, guild_id=None)
        cache_impl._invite_entries = collections.FreezableDict(
            {"blamSpat": mock_other_invite_data, "oooooooooooooos": mock_invite_data}
        )
        cache_impl._build_invite = mock.Mock(return_value=mock_invite)
        cache_impl._garbage_collect_user = mock.Mock()

        result = cache_impl.delete_invite(mock.Mock(code="oooooooooooooos"))

        assert result is mock_invite
        cache_impl._build_invite.assert_called_once_with(mock_invite_data)
        assert cache_impl._invite_entries == {"blamSpat": mock_other_invite_data}

    def test_delete_invite_when_guild_id_is_None(self, cache_impl):
        mock_invite_data = mock.Mock(cache_utilities.InviteData)
        mock_other_invite_data = mock.Mock(cache_utilities.InviteData)
        mock_invite = mock.Mock(invites.InviteWithMetadata, inviter=None, target_user=None, guild_id=None)
        cache_impl._invite_entries = collections.FreezableDict(
            {"blamSpat": mock_other_invite_data, "oooooooooooooo": mock_invite_data}
        )
        cache_impl._build_invite = mock.Mock(return_value=mock_invite)
        cache_impl._garbage_collect_user = mock.Mock()
        cache_impl._remove_guild_record_if_empty = mock.Mock()

        result = cache_impl.delete_invite("oooooooooooooo")

        assert result is mock_invite
        cache_impl._build_invite.assert_called_once_with(mock_invite_data)
        cache_impl._remove_guild_record_if_empty.assert_not_called()
        assert cache_impl._invite_entries == {"blamSpat": mock_other_invite_data}

    def test_delete_invite_without_users(self, cache_impl):
        mock_invite_data = mock.Mock(
            cache_utilities.InviteData, inviter=None, target_user=None, guild_id=snowflakes.Snowflake(999999999)
        )
        mock_other_invite_data = mock.Mock(cache_utilities.InviteData)
        mock_invite = object()
        cache_impl._invite_entries = collections.FreezableDict(
            {"blamSpat": mock_other_invite_data, "oooooooooooooo": mock_invite_data}
        )
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(1234312): mock.Mock(cache_utilities.GuildRecord),
                snowflakes.Snowflake(999999999): cache_utilities.GuildRecord(invites=["ok", "blat", "oooooooooooooo"]),
            }
        )
        cache_impl._build_invite = mock.Mock(return_value=mock_invite)
        cache_impl._garbage_collect_user = mock.Mock()
        cache_impl._remove_guild_record_if_empty = mock.Mock()

        result = cache_impl.delete_invite("oooooooooooooo")

        assert result is mock_invite
        cache_impl._build_invite.assert_called_once_with(mock_invite_data)
        cache_impl._garbage_collect_user.assert_not_called()
        assert cache_impl._invite_entries == {"blamSpat": mock_other_invite_data}
        assert cache_impl._guild_entries[snowflakes.Snowflake(999999999)].invites == ["ok", "blat"]

    def test_delete_invite_for_unknown_invite(self, cache_impl):
        cache_impl._build_invite = mock.Mock()
        cache_impl._garbage_collect_user = mock.Mock()
        # TODO: test this is called
        cache_impl._remove_guild_record_if_empty = mock.Mock()

        result = cache_impl.delete_invite("oooooooooooooo")

        assert result is None
        cache_impl._build_invite.assert_not_called()
        cache_impl._garbage_collect_user.assert_not_called()

    def test_get_invite(self, cache_impl):
        mock_invite_data = mock.Mock(cache_utilities.InviteData)
        mock_invite = mock.Mock(invites.InviteWithMetadata)
        cache_impl._build_invite = mock.Mock(return_value=mock_invite)
        cache_impl._invite_entries = collections.FreezableDict(
            {"blam": mock.Mock(cache_utilities.InviteData), "okokok": mock_invite_data}
        )

        result = cache_impl.get_invite("okokok")

        assert result is mock_invite
        cache_impl._build_invite.assert_called_once_with(mock_invite_data)

    def test_get_invite_with_invite_object(self, cache_impl):
        mock_invite_data = mock.Mock(cache_utilities.InviteData)
        mock_invite = mock.Mock(invites.InviteWithMetadata)
        cache_impl._build_invite = mock.Mock(return_value=mock_invite)
        cache_impl._invite_entries = collections.FreezableDict(
            {"blam": mock.Mock(cache_utilities.InviteData), "okokoks": mock_invite_data}
        )

        result = cache_impl.get_invite(mock.Mock(code="okokoks"))

        assert result is mock_invite
        cache_impl._build_invite.assert_called_once_with(mock_invite_data)

    def test_get_invite_for_unknown_invite(self, cache_impl):
        cache_impl._build_invite = mock.Mock()
        cache_impl._invite_entries = collections.FreezableDict({"blam": mock.Mock(cache_utilities.InviteData)})
        assert cache_impl.get_invite("okokok") is None
        cache_impl._build_invite.assert_not_called()

    def test_get_invites_view(self, cache_impl):
        mock_invite_data_1 = mock.Mock(cache_utilities.InviteData)
        mock_invite_data_2 = mock.Mock(cache_utilities.InviteData)
        mock_invite_1 = mock.Mock(invites.InviteWithMetadata)
        mock_invite_2 = mock.Mock(invites.InviteWithMetadata)
        cache_impl._invite_entries = collections.FreezableDict(
            {"okok": mock_invite_data_1, "blamblam": mock_invite_data_2}
        )
        cache_impl._build_invite = mock.Mock(side_effect=[mock_invite_1, mock_invite_2])

        result = cache_impl.get_invites_view()

        assert result == {"okok": mock_invite_1, "blamblam": mock_invite_2}
        cache_impl._build_invite.assert_has_calls([mock.call(mock_invite_data_1), mock.call(mock_invite_data_2)])

    def test_get_invites_view_for_guild(self, cache_impl):
        mock_invite_data_1 = mock.Mock(cache_utilities.InviteData)
        mock_invite_data_2 = mock.Mock(cache_utilities.InviteData)
        mock_invite_1 = mock.Mock(invites.InviteWithMetadata)
        mock_invite_2 = mock.Mock(invites.InviteWithMetadata)
        cache_impl._invite_entries = collections.FreezableDict(
            {
                "okok": mock_invite_data_1,
                "dsaytert": mock_invite_data_2,
                "bitsbits ": mock.Mock(cache_utilities.InviteData),
            }
        )
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(9544994): mock.Mock(cache_utilities.GuildRecord),
                snowflakes.Snowflake(4444444): cache_utilities.GuildRecord(invites=["okok", "dsaytert"]),
            }
        )
        cache_impl._build_invite = mock.Mock(side_effect=[mock_invite_1, mock_invite_2])

        result = cache_impl.get_invites_view_for_guild(StubModel(4444444))

        assert result == {"okok": mock_invite_1, "dsaytert": mock_invite_2}
        cache_impl._build_invite.assert_has_calls([mock.call(mock_invite_data_1), mock.call(mock_invite_data_2)])

    def test_get_invites_view_for_guild_unknown_emoji_cache(self, cache_impl):
        cache_impl._invite_entries = collections.FreezableDict(
            {"okok": mock.Mock(cache_utilities.InviteData), "dsaytert": mock.Mock(cache_utilities.InviteData)}
        )
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(9544994): mock.Mock(cache_utilities.GuildRecord),
                snowflakes.Snowflake(4444444): cache_utilities.GuildRecord(invites=None),
            }
        )
        cache_impl._build_invite = mock.Mock()

        result = cache_impl.get_invites_view_for_guild(StubModel(4444444))

        assert result == {}
        cache_impl._build_invite.assert_not_called()

    def test_get_invites_view_for_guild_unknown_record(self, cache_impl):
        cache_impl._invite_entries = collections.FreezableDict(
            {"okok": mock.Mock(cache_utilities.InviteData), "dsaytert": mock.Mock(cache_utilities.InviteData)}
        )
        cache_impl._guild_entries = collections.FreezableDict(
            {snowflakes.Snowflake(9544994): mock.Mock(cache_utilities.GuildRecord)}
        )
        cache_impl._build_invite = mock.Mock()

        result = cache_impl.get_invites_view_for_guild(StubModel(4444444))

        assert result == {}
        cache_impl._build_invite.assert_not_called()

    def test_get_invites_view_for_channel(self, cache_impl):
        mock_invite_data_1 = mock.Mock(channel_id=snowflakes.Snowflake(987987), code="blamBang")
        mock_invite_data_2 = mock.Mock(channel_id=snowflakes.Snowflake(987987), code="bingBong")
        mock_invite_1 = mock.Mock(invites.InviteWithMetadata)
        mock_invite_2 = mock.Mock(invites.InviteWithMetadata)
        cache_impl._invite_entries = collections.FreezableDict(
            {
                "blamBang": mock_invite_data_1,
                "bingBong": mock_invite_data_2,
                "Pop": mock.Mock(cache_utilities.InviteData, channel_id=snowflakes.Snowflake(94934923)),
                "Fam": mock.Mock(cache_utilities.InviteData, channel_id=snowflakes.Snowflake(2123)),
            }
        )
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(31423): mock.Mock(cache_utilities.GuildRecord),
                snowflakes.Snowflake(83452134): cache_utilities.GuildRecord(invites=["blamBang", "bingBong", "Pop"]),
            }
        )
        cache_impl._build_invite = mock.Mock(side_effect=[mock_invite_1, mock_invite_2])

        result = cache_impl.get_invites_view_for_channel(StubModel(83452134), StubModel(987987))

        assert result == {"blamBang": mock_invite_1, "bingBong": mock_invite_2}
        cache_impl._build_invite.assert_has_calls([mock.call(mock_invite_data_1), mock.call(mock_invite_data_2)])

    def test_get_invites_view_for_channel_unknown_emoji_cache(self, cache_impl):
        cache_impl._invite_entries = collections.FreezableDict(
            {"okok": mock.Mock(cache_utilities.InviteData), "dsaytert": mock.Mock(cache_utilities.InviteData)}
        )
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(9544994): mock.Mock(cache_utilities.GuildRecord),
                snowflakes.Snowflake(4444444): cache_utilities.GuildRecord(invites=None),
            }
        )
        cache_impl._build_invite = mock.Mock()

        result = cache_impl.get_invites_view_for_channel(StubModel(4444444), StubModel(942123))

        assert result == {}
        cache_impl._build_invite.assert_not_called()

    def test_get_invites_view_for_channel_unknown_record(self, cache_impl):
        cache_impl._invite_entries = collections.FreezableDict(
            {"okok": mock.Mock(cache_utilities.InviteData), "dsaytert": mock.Mock(cache_utilities.InviteData)}
        )
        cache_impl._guild_entries = collections.FreezableDict(
            {snowflakes.Snowflake(9544994): mock.Mock(cache_utilities.GuildRecord)}
        )
        cache_impl._build_invite = mock.Mock()

        result = cache_impl.get_invites_view_for_channel(StubModel(4444444), StubModel(9543123))

        assert result == {}
        cache_impl._build_invite.assert_not_called()

    def test_update_invite(self, cache_impl):
        mock_old_invite = mock.Mock(invites.InviteWithMetadata)
        mock_new_invite = mock.Mock(invites.InviteWithMetadata)
        mock_invite = mock.Mock(invites.InviteWithMetadata, code="biggieSmall")
        cache_impl.get_invite = mock.Mock(side_effect=[mock_old_invite, mock_new_invite])
        cache_impl.set_invite = mock.Mock()

        result = cache_impl.update_invite(mock_invite)

        assert result == (mock_old_invite, mock_new_invite)
        cache_impl.get_invite.assert_has_calls([mock.call("biggieSmall"), mock.call("biggieSmall")])
        cache_impl.set_invite.assert_called_once_with(mock_invite)

    def test_delete_me_for_known_me(self, cache_impl):
        mock_own_user = mock.Mock(users.OwnUser)
        cache_impl._me = mock_own_user

        result = cache_impl.delete_me()

        assert result is mock_own_user
        assert cache_impl._me is None

    def test_delete_me_for_unknown_me(self, cache_impl):
        result = cache_impl.delete_me()

        assert result is None
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

        cache_impl.set_me(mock_own_user)

        assert cache_impl._me == mock_own_user
        assert cache_impl._me is not mock_own_user

    def test_set_me_when_not_enabled(self, cache_impl):
        cache_impl._settings.components = 0

        cache_impl.set_me(object())

        assert cache_impl._me is None

    def test_update_me_for_cached_me(self, cache_impl):
        mock_cached_own_user = mock.MagicMock(users.OwnUser)
        mock_own_user = mock.MagicMock(users.OwnUser)
        cache_impl._me = mock_cached_own_user

        result = cache_impl.update_me(mock_own_user)

        assert result == (mock_cached_own_user, mock_own_user)
        assert cache_impl._me == mock_own_user

    def test_update_me_for_uncached_me(self, cache_impl):
        mock_own_user = mock.MagicMock(users.OwnUser)

        result = cache_impl.update_me(mock_own_user)

        assert result == (None, mock_own_user)
        assert cache_impl._me == mock_own_user

    def test_update_me_for_when_not_enabled(self, cache_impl):
        cache_impl._settings.components = 0
        cache_impl.get_me = mock.Mock()
        cache_impl.set_me = mock.Mock()

        result = cache_impl.update_me(object())

        assert result == (None, None)
        cache_impl.get_me.assert_not_called()
        cache_impl.set_me.assert_not_called()

    def test__build_member(self, cache_impl):
        mock_user = mock.MagicMock(users.User)
        member_data = cache_utilities.MemberData(
            user=cache_utilities.RefCell(mock_user),
            guild_id=snowflakes.Snowflake(6434435234),
            nickname="NICK",
            guild_avatar_hash="only slightly gay",
            role_ids=(snowflakes.Snowflake(65234), snowflakes.Snowflake(654234123)),
            joined_at=datetime.datetime(2020, 7, 9, 13, 11, 18, 384554, tzinfo=datetime.timezone.utc),
            premium_since=datetime.datetime(2020, 7, 17, 13, 11, 18, 384554, tzinfo=datetime.timezone.utc),
            is_deaf=False,
            is_mute=True,
            is_pending=False,
            raw_communication_disabled_until=datetime.datetime(
                2021, 10, 18, 13, 11, 18, 384554, tzinfo=datetime.timezone.utc
            ),
        )

        member = cache_impl._build_member(cache_utilities.RefCell(member_data))

        assert member.user == mock_user
        assert member.user is not mock_user
        assert member.guild_id == 6434435234
        assert member.nickname == "NICK"
        assert member.guild_avatar_hash == "only slightly gay"
        assert member.role_ids == (snowflakes.Snowflake(65234), snowflakes.Snowflake(654234123))
        assert member.joined_at == datetime.datetime(2020, 7, 9, 13, 11, 18, 384554, tzinfo=datetime.timezone.utc)
        assert member.premium_since == datetime.datetime(2020, 7, 17, 13, 11, 18, 384554, tzinfo=datetime.timezone.utc)
        assert member.is_deaf is False
        assert member.is_mute is True
        assert member.is_pending is False
        assert member.raw_communication_disabled_until == datetime.datetime(
            2021, 10, 18, 13, 11, 18, 384554, tzinfo=datetime.timezone.utc
        )

    def test_clear_members(self, cache_impl):
        mock_user_1 = cache_utilities.RefCell(mock.Mock(id=snowflakes.Snowflake(2123123)))
        mock_user_2 = cache_utilities.RefCell(mock.Mock(id=snowflakes.Snowflake(212314423)))
        mock_user_3 = cache_utilities.RefCell(mock.Mock(id=snowflakes.Snowflake(2123166623)))
        mock_user_4 = cache_utilities.RefCell(mock.Mock(id=snowflakes.Snowflake(21237777123)))
        mock_user_5 = cache_utilities.RefCell(mock.Mock(id=snowflakes.Snowflake(212399999123)))
        mock_data_member_1 = cache_utilities.RefCell(
            mock.Mock(
                cache_utilities.MemberData,
                user=mock_user_1,
                guild_id=snowflakes.Snowflake(43123123),
                has_been_deleted=False,
            )
        )
        mock_data_member_2 = cache_utilities.RefCell(
            mock.Mock(
                cache_utilities.MemberData,
                user=mock_user_2,
                guild_id=snowflakes.Snowflake(43123123),
                has_been_deleted=False,
            )
        )
        mock_data_member_3 = cache_utilities.RefCell(
            mock.Mock(
                cache_utilities.MemberData,
                user=mock_user_3,
                guild_id=snowflakes.Snowflake(65234),
                has_been_deleted=False,
            )
        )
        mock_data_member_4 = cache_utilities.RefCell(
            mock.Mock(
                cache_utilities.MemberData,
                user=mock_user_4,
                guild_id=snowflakes.Snowflake(65234),
                has_been_deleted=False,
            )
        )
        mock_data_member_5 = cache_utilities.RefCell(
            mock.Mock(
                cache_utilities.MemberData,
                user=mock_user_5,
                guild_id=snowflakes.Snowflake(65234),
                has_been_deleted=False,
            )
        )
        mock_member_1 = object()
        mock_member_2 = object()
        mock_member_3 = object()
        mock_member_4 = object()
        mock_member_5 = object()
        guild_record_1 = cache_utilities.GuildRecord(
            members=collections.FreezableDict(
                {snowflakes.Snowflake(2123123): mock_data_member_1, snowflakes.Snowflake(212314423): mock_data_member_2}
            )
        )
        guild_record_2 = cache_utilities.GuildRecord(
            members=collections.FreezableDict(
                {
                    snowflakes.Snowflake(2123166623): mock_data_member_3,
                    snowflakes.Snowflake(21237777123): mock_data_member_4,
                    snowflakes.Snowflake(212399999123): mock_data_member_5,
                }
            )
        )
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(43123123): guild_record_1,
                snowflakes.Snowflake(35123): cache_utilities.GuildRecord(members=collections.FreezableDict({})),
                snowflakes.Snowflake(76345123): cache_utilities.GuildRecord(members=None),
                snowflakes.Snowflake(65234): guild_record_2,
            }
        )
        cache_impl._build_member = mock.Mock(
            side_effect=[mock_member_1, mock_member_2, mock_member_3, mock_member_4, mock_member_5]
        )
        cache_impl._garbage_collect_user = mock.Mock()
        cache_impl._remove_guild_record_if_empty = mock.Mock()

        result = cache_impl.clear_members()

        assert result == {
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
                mock.call(mock_user_1, decrement=1),
                mock.call(mock_user_2, decrement=1),
                mock.call(mock_user_3, decrement=1),
                mock.call(mock_user_4, decrement=1),
                mock.call(mock_user_5, decrement=1),
            ]
        )
        cache_impl._remove_guild_record_if_empty.assert_has_calls(
            [mock.call(snowflakes.Snowflake(43123123), guild_record_1), mock.call(65234, guild_record_2)],
            any_order=True,
        )
        cache_impl._build_member.assert_has_calls(
            [
                mock.call(mock_data_member_1),
                mock.call(mock_data_member_2),
                mock.call(mock_data_member_3),
                mock.call(mock_data_member_4),
                mock.call(mock_data_member_5),
            ]
        )
        assert guild_record_1.members is None
        assert guild_record_2.members is None

    @pytest.mark.skip(reason="TODO")
    def test_clear_members_for_guild(self, cache_impl): ...

    def test_delete_member_for_unknown_guild_record(self, cache_impl):
        result = cache_impl.delete_member(StubModel(42123), StubModel(67876))

        assert result is None

    def test_delete_member_for_unknown_member_cache(self, cache_impl):
        cache_impl._guild_entries = {snowflakes.Snowflake(42123): cache_utilities.GuildRecord()}

        result = cache_impl.delete_member(StubModel(42123), StubModel(67876))

        assert result is None

    def test_delete_member_for_known_member(self, cache_impl):
        mock_member = mock.Mock(guilds.Member)
        mock_user = cache_utilities.RefCell(mock.Mock(id=snowflakes.Snowflake(67876)))
        mock_member_data = mock.Mock(
            cache_utilities.MemberData, user=mock_user, guild_id=snowflakes.Snowflake(42123), has_been_deleted=False
        )
        mock_reffed_member = cache_utilities.RefCell(mock_member_data)
        guild_record = cache_utilities.GuildRecord(members={snowflakes.Snowflake(67876): mock_reffed_member})
        cache_impl._guild_entries = collections.FreezableDict({snowflakes.Snowflake(42123): guild_record})
        cache_impl._remove_guild_record_if_empty = mock.Mock()
        cache_impl._garbage_collect_user = mock.Mock()
        cache_impl._build_member = mock.Mock(return_value=mock_member)

        result = cache_impl.delete_member(StubModel(42123), StubModel(67876))

        assert result is mock_member
        assert cache_impl._guild_entries[snowflakes.Snowflake(42123)].members is None
        cache_impl._build_member.assert_called_once_with(mock_reffed_member)
        cache_impl._garbage_collect_user.assert_called_once_with(mock_user, decrement=1)
        cache_impl._remove_guild_record_if_empty.assert_called_once_with(snowflakes.Snowflake(42123), guild_record)

    def test_delete_member_for_known_hard_referenced_member(self, cache_impl):
        mock_member = cache_utilities.RefCell(mock.Mock(has_been_deleted=False), ref_count=1)
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(42123): cache_utilities.GuildRecord(
                    members=collections.FreezableDict({snowflakes.Snowflake(67876): mock_member})
                )
            }
        )

        result = cache_impl.delete_member(StubModel(42123), StubModel(67876))

        assert result is None
        assert mock_member.object.has_been_deleted is True

    def test_get_member_for_unknown_member_cache(self, cache_impl):
        cache_impl._guild_entries = collections.FreezableDict(
            {snowflakes.Snowflake(1234213): cache_utilities.GuildRecord()}
        )

        result = cache_impl.get_member(StubModel(1234213), StubModel(512312354))

        assert result is None

    def test_get_member_for_unknown_member(self, cache_impl):
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(1234213): cache_utilities.GuildRecord(
                    members={snowflakes.Snowflake(43123): mock.Mock(cache_utilities.MemberData)}
                )
            }
        )

        result = cache_impl.get_member(StubModel(1234213), StubModel(512312354))

        assert result is None

    def test_get_member_for_unknown_guild_record(self, cache_impl):
        result = cache_impl.get_member(StubModel(1234213), StubModel(512312354))

        assert result is None

    def test_get_member_for_known_member(self, cache_impl):
        mock_member_data = mock.Mock(cache_utilities.MemberData)
        mock_member = mock.Mock(guilds.Member)
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(1234213): cache_utilities.GuildRecord(
                    members=collections.FreezableDict(
                        {
                            snowflakes.Snowflake(512312354): mock_member_data,
                            snowflakes.Snowflake(321): mock.Mock(cache_utilities.MemberData),
                        }
                    )
                )
            }
        )
        cache_impl._user_entries = collections.FreezableDict({})
        cache_impl._build_member = mock.Mock(return_value=mock_member)

        result = cache_impl.get_member(StubModel(1234213), StubModel(512312354))

        assert result is mock_member
        cache_impl._build_member.assert_called_once_with(mock_member_data)

    def test_get_members_view(self, cache_impl):
        mock_member_data_1 = cache_utilities.RefCell(object())
        mock_member_data_2 = cache_utilities.RefCell(object())
        mock_member_data_3 = cache_utilities.RefCell(object())
        mock_member_data_4 = cache_utilities.RefCell(object())
        mock_member_data_5 = cache_utilities.RefCell(object())
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
                snowflakes.Snowflake(543123): cache_utilities.GuildRecord(),
                snowflakes.Snowflake(54123123): cache_utilities.GuildRecord(
                    members=collections.FreezableDict(
                        {snowflakes.Snowflake(321): mock_member_data_1, snowflakes.Snowflake(6324): mock_member_data_2}
                    )
                ),
                snowflakes.Snowflake(54234): cache_utilities.GuildRecord(members=collections.FreezableDict({})),
                snowflakes.Snowflake(783452): cache_utilities.GuildRecord(
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

        result = cache_impl.get_members_view()

        assert result == {
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
                mock.call(mock_member_data_1),
                mock.call(mock_member_data_2),
                mock.call(mock_member_data_3),
                mock.call(mock_member_data_4),
                mock.call(mock_member_data_5),
            ]
        )

    def test_get_members_view_for_guild_unknown_record(self, cache_impl):
        members_mapping = cache_impl.get_members_view_for_guild(StubModel(42334))

        assert members_mapping == {}

    def test_get_members_view_for_guild_unknown_member_cache(self, cache_impl):
        cache_impl._guild_entries = collections.FreezableDict(
            {snowflakes.Snowflake(42334): cache_utilities.GuildRecord()}
        )

        members_mapping = cache_impl.get_members_view_for_guild(StubModel(42334))

        assert members_mapping == {}

    def test_get_members_view_for_guild(self, cache_impl):
        mock_member_data_1 = cache_utilities.RefCell(mock.Mock(cache_utilities.MemberData, has_been_deleted=False))
        mock_member_data_2 = cache_utilities.RefCell(mock.Mock(cache_utilities.MemberData, has_been_deleted=False))
        mock_member_1 = mock.Mock(guilds.Member)
        mock_member_2 = mock.Mock(guilds.Member)
        guild_record = cache_utilities.GuildRecord(
            members=collections.FreezableDict(
                {
                    snowflakes.Snowflake(3214321): mock_member_data_1,
                    snowflakes.Snowflake(53224): mock_member_data_2,
                    snowflakes.Snowflake(9000): cache_utilities.RefCell(
                        mock.Mock(cache_utilities.MemberData, has_been_deleted=True)
                    ),
                }
            )
        )
        cache_impl._guild_entries = collections.FreezableDict({snowflakes.Snowflake(42334): guild_record})
        cache_impl._build_member = mock.Mock(side_effect=[mock_member_1, mock_member_2])

        result = cache_impl.get_members_view_for_guild(StubModel(42334))

        assert result == {snowflakes.Snowflake(3214321): mock_member_1, snowflakes.Snowflake(53224): mock_member_2}
        cache_impl._build_member.assert_has_calls([mock.call(mock_member_data_1), mock.call(mock_member_data_2)])

    def test_set_member(self, cache_impl):
        mock_user = mock.Mock(users.User, id=snowflakes.Snowflake(645234123))
        mock_user_ref = cache_utilities.RefCell(mock_user)
        member_model = guilds.Member(
            guild_id=snowflakes.Snowflake(67345234),
            user=mock_user,
            nickname="A NICK LOL",
            role_ids=[snowflakes.Snowflake(65345234), snowflakes.Snowflake(123123)],
            joined_at=datetime.datetime(2020, 7, 15, 23, 30, 59, 501602, tzinfo=datetime.timezone.utc),
            premium_since=datetime.datetime(2020, 7, 1, 2, 0, 12, 501602, tzinfo=datetime.timezone.utc),
            is_deaf=True,
            guild_avatar_hash="gay",
            is_mute=False,
            is_pending=True,
            raw_communication_disabled_until=datetime.datetime(
                2021, 10, 18, 13, 11, 18, 384554, tzinfo=datetime.timezone.utc
            ),
        )
        cache_impl._set_user = mock.Mock(return_value=mock_user_ref)
        cache_impl._increment_ref_count = mock.Mock()

        cache_impl.set_member(member_model)

        cache_impl._set_user.assert_called_once_with(mock_user)
        cache_impl._increment_ref_count.assert_called_once_with(mock_user_ref)
        assert 67345234 in cache_impl._guild_entries
        assert 645234123 in cache_impl._guild_entries[snowflakes.Snowflake(67345234)].members
        member_entry = cache_impl._guild_entries[snowflakes.Snowflake(67345234)].members[
            snowflakes.Snowflake(645234123)
        ]
        assert member_entry.object.user is mock_user_ref
        assert member_entry.object.guild_id == 67345234
        assert member_entry.object.nickname == "A NICK LOL"
        assert member_entry.object.role_ids == (65345234, 123123)
        assert member_entry.object.role_ids is not member_model.role_ids
        assert member_entry.object.guild_avatar_hash == "gay"
        assert isinstance(member_entry.object.role_ids, tuple)
        assert member_entry.object.joined_at == datetime.datetime(
            2020, 7, 15, 23, 30, 59, 501602, tzinfo=datetime.timezone.utc
        )
        assert member_entry.object.premium_since == datetime.datetime(
            2020, 7, 1, 2, 0, 12, 501602, tzinfo=datetime.timezone.utc
        )
        assert member_entry.object.is_deaf is True
        assert member_entry.object.is_mute is False
        assert member_entry.object.is_pending is True
        assert member_entry.object.raw_communication_disabled_until == datetime.datetime(
            2021, 10, 18, 13, 11, 18, 384554, tzinfo=datetime.timezone.utc
        )

    def test_set_member_doesnt_increment_user_ref_count_for_pre_cached_member(self, cache_impl):
        mock_user = mock.Mock(users.User, id=snowflakes.Snowflake(645234123))
        member_model = mock.MagicMock(guilds.Member, user=mock_user, guild_id=snowflakes.Snowflake(67345234))
        cache_impl._set_user = mock.Mock()
        cache_impl._increment_user_ref_count = mock.Mock()
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(67345234): cache_utilities.GuildRecord(
                    members=collections.FreezableDict(
                        {snowflakes.Snowflake(645234123): mock.Mock(cache_utilities.MemberData)}
                    )
                )
            }
        )

        cache_impl.set_member(member_model)

        cache_impl._set_user.assert_called_once_with(mock_user)
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

        result = cache_impl.update_member(mock_member)

        assert result == (mock_old_cached_member, mock_new_cached_member)
        cache_impl.get_member.assert_has_calls([mock.call(123123, 65234123), mock.call(123123, 65234123)])
        cache_impl.set_member.assert_called_once_with(mock_member)

    @pytest.mark.skip(reason="TODO")
    def test_clear_presences(self, cache_impl): ...

    @pytest.mark.skip(reason="TODO")
    def test_clear_presences_for_guild(self, cache_impl): ...

    @pytest.mark.skip(reason="TODO")
    def test_delete_presence(self, cache_impl): ...

    @pytest.mark.skip(reason="TODO")
    def test_get_presence(self, cache_impl): ...

    @pytest.mark.skip(reason="TODO")
    def test_get_presences_view(self, cache_impl): ...

    @pytest.mark.skip(reason="TODO")
    def test_get_presences_view_for_guild(self, cache_impl): ...

    @pytest.mark.skip(reason="TODO")
    def test_set_presence(self, cache_impl): ...

    @pytest.mark.skip(reason="TODO")
    def test_update_presence(self, cache_impl): ...

    @pytest.mark.skip(reason="TODO")
    def test_clear_roles(self, cache_impl): ...

    @pytest.mark.skip(reason="TODO")
    def test_clear_roles_for_guild(self, cache_impl): ...

    @pytest.mark.skip(reason="TODO")
    def test_delete_role(self, cache_impl): ...

    @pytest.mark.skip(reason="TODO")
    def test_get_role(self, cache_impl): ...

    @pytest.mark.skip(reason="TODO")
    def test_get_roles_view(self, cache_impl): ...

    @pytest.mark.skip(reason="TODO")
    def test_get_roles_view_for_guild(self, cache_impl): ...

    @pytest.mark.skip(reason="TODO")
    def test_set_role(self, cache_impl): ...

    @pytest.mark.skip(reason="TODO")
    def test_update_role(self, cache_impl): ...

    def test__garbage_collect_user_for_known_unreferenced_user(self, cache_impl):
        mock_user = cache_utilities.RefCell(mock.Mock(id=snowflakes.Snowflake(21231234)), ref_count=1)
        mock_other_user = mock.Mock(cache_utilities.RefCell, ref_count=1)
        cache_impl._user_entries = collections.FreezableDict(
            {snowflakes.Snowflake(21231234): mock_user, snowflakes.Snowflake(645234): mock_other_user}
        )

        cache_impl._garbage_collect_user(mock_user, decrement=1)

        assert cache_impl._user_entries == {snowflakes.Snowflake(645234): mock_other_user}

    def test__garbage_collect_user_for_known_unreferenced_user_removes_cached_dm_channelo(self, cache_impl):
        mock_user = cache_utilities.RefCell(mock.Mock(id=snowflakes.Snowflake(21231234)), ref_count=1)
        cache_impl._dm_channel_entries = collections.FreezableDict({21231234: 123123123})
        mock_other_user = mock.Mock(cache_utilities.RefCell, ref_count=1)
        cache_impl._user_entries = collections.FreezableDict(
            {snowflakes.Snowflake(21231234): mock_user, snowflakes.Snowflake(645234): mock_other_user}
        )

        cache_impl._garbage_collect_user(mock_user, decrement=1)

        assert cache_impl._user_entries == {snowflakes.Snowflake(645234): mock_other_user}
        assert cache_impl._dm_channel_entries == {}

    def test_garbage_collect_user_for_referenced_user(self, cache_impl):
        mock_user = cache_utilities.RefCell(mock.Mock(id=snowflakes.Snowflake(21231234)), ref_count=2)
        mock_other_user = mock.Mock(cache_utilities.RefCell)
        cache_impl._user_entries = collections.FreezableDict(
            {snowflakes.Snowflake(21231234): mock_user, snowflakes.Snowflake(645234): mock_other_user}
        )

        cache_impl._garbage_collect_user(mock_user, decrement=1)

        assert cache_impl._user_entries == {
            snowflakes.Snowflake(21231234): mock_user,
            snowflakes.Snowflake(645234): mock_other_user,
        }
        assert mock_user.ref_count == 1

    def test_garbage_collect_user_for_unknown_user(self, cache_impl):
        mock_user = cache_utilities.RefCell(mock.Mock(id=snowflakes.Snowflake(21235432), ref_count=0))
        cache_impl._user_entries = collections.FreezableDict({snowflakes.Snowflake(21231234): mock_user})

        cache_impl._garbage_collect_user(mock_user)

        assert cache_impl._user_entries == {snowflakes.Snowflake(21231234): mock_user}

    def test_get_user_for_known_user(self, cache_impl):
        mock_user = mock.MagicMock(users.User)
        cache_impl._user_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(21231234): cache_utilities.RefCell(mock_user),
                snowflakes.Snowflake(645234): mock.Mock(cache_utilities.RefCell),
            }
        )
        cache_impl._build_user = mock.Mock(return_value=mock_user)

        result = cache_impl.get_user(StubModel(21231234))

        assert result == mock_user

    def test_get_users_view_for_filled_user_cache(self, cache_impl):
        mock_user_1 = mock.MagicMock(users.User)
        mock_user_2 = mock.MagicMock(users.User)
        cache_impl._user_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(54123): cache_utilities.RefCell(mock_user_1),
                snowflakes.Snowflake(76345): cache_utilities.RefCell(mock_user_2),
            }
        )

        result = cache_impl.get_users_view()

        assert result == {snowflakes.Snowflake(54123): mock_user_1, snowflakes.Snowflake(76345): mock_user_2}

    def test_get_users_view_for_empty_user_cache(self, cache_impl):
        assert cache_impl.get_users_view() == {}

    def test__set_user(self, cache_impl):
        mock_user = mock.MagicMock(users.User, id=snowflakes.Snowflake(6451234123))
        cache_impl._user_entries = collections.FreezableDict(
            {snowflakes.Snowflake(542143): mock.Mock(cache_utilities.RefCell)}
        )

        result = cache_impl._set_user(mock_user)

        assert result is cache_impl._user_entries[snowflakes.Snowflake(6451234123)]
        assert 6451234123 in cache_impl._user_entries
        assert cache_impl._user_entries[snowflakes.Snowflake(6451234123)].object == mock_user
        assert cache_impl._user_entries[snowflakes.Snowflake(6451234123)].object is not mock_user

    def test__set_user_carries_over_ref_count(self, cache_impl):
        mock_user = mock.MagicMock(users.User, id=snowflakes.Snowflake(6451234123))
        cache_impl._user_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(542143): mock.Mock(cache_utilities.RefCell),
                snowflakes.Snowflake(6451234123): mock.Mock(cache_utilities.RefCell, ref_count=42),
            }
        )

        result = cache_impl._set_user(mock_user)

        assert result is cache_impl._user_entries[snowflakes.Snowflake(6451234123)]
        assert 6451234123 in cache_impl._user_entries
        assert cache_impl._user_entries[snowflakes.Snowflake(6451234123)].object == mock_user
        assert cache_impl._user_entries[snowflakes.Snowflake(6451234123)].object is not mock_user
        assert cache_impl._user_entries[snowflakes.Snowflake(6451234123)].ref_count == 42

    def test__build_voice_state(self, cache_impl):
        mock_member = mock.Mock(guilds.Member, user=mock.Mock(users.User, id=snowflakes.Snowflake(7512312)))
        mock_member_data = mock.Mock(cache_utilities.MemberData, build_entity=mock.Mock(return_value=mock_member))
        voice_state_data = cache_utilities.VoiceStateData(
            channel_id=snowflakes.Snowflake(4651234123),
            guild_id=snowflakes.Snowflake(54123123),
            is_guild_deafened=True,
            is_guild_muted=False,
            is_self_deafened=True,
            is_self_muted=True,
            is_streaming=False,
            is_suppressed=False,
            is_video_enabled=False,
            member=cache_utilities.RefCell(mock_member_data),
            session_id="lkmdfslkmfdskjlfsdkjlsfdkjldsf",
            requested_to_speak_at=datetime.datetime(2021, 4, 17, 10, 13, 18, 887306, tzinfo=datetime.timezone.utc),
        )

        current_voice_state = cache_impl._build_voice_state(voice_state_data)

        mock_member_data.build_entity.assert_called_once()
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
        assert current_voice_state.requested_to_speak_at == datetime.datetime(
            2021, 4, 17, 10, 13, 18, 887306, tzinfo=datetime.timezone.utc
        )

    @pytest.mark.skip(reason="TODO")
    def test_clear_voice_states(self, cache_impl): ...

    @pytest.mark.skip(reason="TODO")
    def test_clear_voice_states_for_channel(self, cache_impl): ...

    def test_clear_voice_states_for_guild(self, cache_impl):
        mock_member_data_1 = object()
        mock_member_data_2 = object()
        mock_voice_state_data_1 = mock.Mock(cache_utilities.VoiceStateData, member=mock_member_data_1)
        mock_voice_state_data_2 = mock.Mock(cache_utilities.VoiceStateData, member=mock_member_data_2)
        mock_voice_state_1 = mock.Mock(voices.VoiceState)
        mock_voice_state_2 = mock.Mock(voices.VoiceState)
        record = cache_utilities.GuildRecord(
            voice_states=collections.FreezableDict(
                {
                    snowflakes.Snowflake(7512312): mock_voice_state_data_1,
                    snowflakes.Snowflake(43123123): mock_voice_state_data_2,
                }
            )
        )
        cache_impl._remove_guild_record_if_empty = mock.Mock()
        cache_impl._garbage_collect_member = mock.Mock()
        cache_impl._guild_entries = collections.FreezableDict({snowflakes.Snowflake(54123123): record})
        cache_impl._build_voice_state = mock.Mock(side_effect=[mock_voice_state_1, mock_voice_state_2])

        result = cache_impl.clear_voice_states_for_guild(StubModel(54123123))

        assert result == {
            snowflakes.Snowflake(7512312): mock_voice_state_1,
            snowflakes.Snowflake(43123123): mock_voice_state_2,
        }
        cache_impl._garbage_collect_member.assert_has_calls(
            [mock.call(record, mock_member_data_1, decrement=1), mock.call(record, mock_member_data_2, decrement=1)]
        )
        cache_impl._remove_guild_record_if_empty.assert_called_once_with(snowflakes.Snowflake(54123123), record)
        cache_impl._build_voice_state.assert_has_calls(
            [mock.call(mock_voice_state_data_1), mock.call(mock_voice_state_data_2)]
        )

    def test_clear_voice_states_for_guild_unknown_voice_state_cache(self, cache_impl):
        cache_impl._guild_entries[snowflakes.Snowflake(24123)] = cache_utilities.GuildRecord()

        result = cache_impl.clear_voice_states_for_guild(StubModel(24123))

        assert result == {}

    def test_clear_voice_states_for_guild_unknown_record(self, cache_impl):
        result = cache_impl.clear_voice_states_for_guild(StubModel(24123))

        assert result == {}

    def test_delete_voice_state(self, cache_impl):
        mock_member_data = object()
        mock_voice_state_data = mock.Mock(cache_utilities.VoiceStateData, member=mock_member_data)
        mock_other_voice_state_data = mock.Mock(cache_utilities.VoiceStateData)
        mock_voice_state = mock.Mock(voices.VoiceState)
        cache_impl._build_voice_state = mock.Mock(return_value=mock_voice_state)
        guild_record = cache_utilities.GuildRecord(
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
                snowflakes.Snowflake(65234): mock.Mock(cache_utilities.GuildRecord),
                snowflakes.Snowflake(43123): guild_record,
            }
        )
        cache_impl._remove_guild_record_if_empty = mock.Mock()
        cache_impl._garbage_collect_member = mock.Mock()

        result = cache_impl.delete_voice_state(StubModel(43123), StubModel(12354345))

        assert result is mock_voice_state
        cache_impl._garbage_collect_member.assert_called_once_with(guild_record, mock_member_data, decrement=1)
        cache_impl._remove_guild_record_if_empty.assert_called_once_with(snowflakes.Snowflake(43123), guild_record)
        assert cache_impl._guild_entries[snowflakes.Snowflake(43123)].voice_states == {
            snowflakes.Snowflake(6541234): mock_other_voice_state_data
        }

    def test_delete_voice_state_unknown_state(self, cache_impl):
        mock_other_voice_state_data = mock.Mock(cache_utilities.VoiceStateData)
        cache_impl._build_voice_state = mock.Mock()
        guild_record = cache_utilities.GuildRecord(
            voice_states=collections.FreezableDict({snowflakes.Snowflake(6541234): mock_other_voice_state_data})
        )
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(65234): mock.Mock(cache_utilities.GuildRecord),
                snowflakes.Snowflake(43123): guild_record,
            }
        )
        cache_impl._remove_guild_record_if_empty = mock.Mock()

        result = cache_impl.delete_voice_state(StubModel(43123), StubModel(12354345))

        assert result is None
        cache_impl._remove_guild_record_if_empty.assert_not_called()
        assert cache_impl._guild_entries[snowflakes.Snowflake(43123)].voice_states == {
            snowflakes.Snowflake(6541234): mock_other_voice_state_data
        }

    def test_delete_voice_state_unknown_state_cache(self, cache_impl):
        cache_impl._build_voice_state = mock.Mock()
        guild_record = cache_utilities.GuildRecord(voice_states=None)
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(65234): mock.Mock(cache_utilities.GuildRecord),
                snowflakes.Snowflake(43123): guild_record,
            }
        )
        cache_impl._remove_guild_record_if_empty = mock.Mock()

        result = cache_impl.delete_voice_state(StubModel(43123), StubModel(12354345))

        assert result is None
        cache_impl._remove_guild_record_if_empty.assert_not_called()

    def test_delete_voice_state_unknown_record(self, cache_impl):
        cache_impl._build_voice_state = mock.Mock()
        cache_impl._guild_entries = collections.FreezableDict(
            {snowflakes.Snowflake(65234): mock.Mock(cache_utilities.GuildRecord)}
        )
        cache_impl._remove_guild_record_if_empty = mock.Mock()

        result = cache_impl.delete_voice_state(StubModel(43123), StubModel(12354345))

        assert result is None
        cache_impl._remove_guild_record_if_empty.assert_not_called()

    def test_get_voice_state_for_known_voice_state(self, cache_impl):
        mock_voice_state_data = mock.Mock(cache_utilities.VoiceStateData)
        mock_voice_state = mock.Mock(voices.VoiceState)
        cache_impl._build_voice_state = mock.Mock(return_value=mock_voice_state)
        guild_record = cache_utilities.GuildRecord(voice_states={snowflakes.Snowflake(43124): mock_voice_state_data})
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(1235123): guild_record,
                snowflakes.Snowflake(73245): mock.Mock(cache_utilities.GuildRecord),
            }
        )

        result = cache_impl.get_voice_state(StubModel(1235123), StubModel(43124))

        assert result is mock_voice_state
        cache_impl._build_voice_state.assert_called_once_with(mock_voice_state_data)

    def test_get_voice_state_for_unknown_voice_state(self, cache_impl):
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(1235123): cache_utilities.GuildRecord(
                    voice_states=collections.FreezableDict(
                        {snowflakes.Snowflake(54123): mock.Mock(cache_utilities.VoiceStateData)}
                    )
                ),
                snowflakes.Snowflake(73245): mock.Mock(cache_utilities.GuildRecord),
            }
        )

        result = cache_impl.get_voice_state(StubModel(1235123), StubModel(43124))

        assert result is None

    def test_get_voice_state_for_unknown_voice_state_cache(self, cache_impl):
        cache_impl._guild_entries = collections.FreezableDict(
            {
                snowflakes.Snowflake(1235123): cache_utilities.GuildRecord(),
                snowflakes.Snowflake(73245): mock.Mock(cache_utilities.GuildRecord),
            }
        )

        result = cache_impl.get_voice_state(StubModel(1235123), StubModel(43124))

        assert result is None

    def test_get_voice_state_for_unknown_record(self, cache_impl):
        cache_impl._guild_entries = {snowflakes.Snowflake(73245): mock.Mock(cache_utilities.GuildRecord)}

        result = cache_impl.get_voice_state(StubModel(1235123), StubModel(43124))

        assert result is None

    @pytest.mark.skip(reason="TODO")
    def test_get_voice_state_view(self, cache_impl): ...

    @pytest.mark.skip(reason="TODO")
    def test_get_voice_states_view_for_channel(self, cache_impl): ...

    @pytest.mark.skip(reason="TODO")
    def test_get_voice_states_view_for_guild(self, cache_impl): ...

    def test_set_voice_state(self, cache_impl):
        mock_member = object()
        mock_reffed_member = cache_utilities.RefCell(object())
        voice_state = voices.VoiceState(
            app=None,
            channel_id=snowflakes.Snowflake(239211023123),
            guild_id=snowflakes.Snowflake(43123123),
            is_guild_muted=True,
            is_guild_deafened=False,
            is_self_muted=False,
            is_self_deafened=True,
            is_suppressed=False,
            is_video_enabled=True,
            is_streaming=True,
            user_id=snowflakes.Snowflake(4531231),
            member=mock_member,
            session_id="kodfsoijkased9i8uos9i8uawe",
            requested_to_speak_at=datetime.datetime(2021, 4, 17, 10, 13, 56, 939273, tzinfo=datetime.timezone.utc),
        )
        cache_impl._set_member = mock.Mock(return_value=mock_reffed_member)
        cache_impl._increment_ref_count = mock.Mock()

        cache_impl.set_voice_state(voice_state)

        cache_impl._increment_ref_count.assert_called_with(mock_reffed_member)
        cache_impl._set_member.assert_called_once_with(mock_member)
        voice_state_data = cache_impl._guild_entries[43123123].voice_states[4531231]
        assert voice_state_data.channel_id == 239211023123
        assert voice_state_data.guild_id == 43123123
        assert voice_state_data.is_guild_muted is True
        assert voice_state_data.is_guild_deafened is False
        assert voice_state_data.is_self_muted is False
        assert voice_state_data.is_self_deafened is True
        assert voice_state_data.member is mock_reffed_member
        assert voice_state_data.session_id == "kodfsoijkased9i8uos9i8uawe"
        assert voice_state_data.requested_to_speak_at == datetime.datetime(
            2021, 4, 17, 10, 13, 56, 939273, tzinfo=datetime.timezone.utc
        )

    def test_update_voice_state(self, cache_impl):
        mock_old_voice_state = mock.Mock(voices.VoiceState)
        mock_new_voice_state = mock.Mock(voices.VoiceState)
        voice_state = mock.Mock(
            voices.VoiceState, guild_id=snowflakes.Snowflake(43123123), user_id=snowflakes.Snowflake(542134)
        )
        cache_impl.get_voice_state = mock.Mock(side_effect=[mock_old_voice_state, mock_new_voice_state])
        cache_impl.set_voice_state = mock.Mock()

        result = cache_impl.update_voice_state(voice_state)

        assert result == (mock_old_voice_state, mock_new_voice_state)
        cache_impl.set_voice_state.assert_called_once_with(voice_state)
        cache_impl.get_voice_state.assert_has_calls(
            [
                mock.call(snowflakes.Snowflake(43123123), snowflakes.Snowflake(542134)),
                mock.call(snowflakes.Snowflake(43123123), snowflakes.Snowflake(542134)),
            ]
        )

    def test__build_message(self, cache_impl):
        mock_author = mock.MagicMock(users.User)
        mock_member = object()
        member_data = mock.Mock(build_entity=mock.Mock(return_value=mock_member))
        mock_channel = mock.MagicMock()
        mock_mention_user = mock.MagicMock()
        mock_user_mentions = {snowflakes.Snowflake(4231): cache_utilities.RefCell(mock_mention_user)}
        mock_role_mention_ids = (snowflakes.Snowflake(21323123),)
        mock_channel_mentions = {snowflakes.Snowflake(4444): mock_channel}
        mock_attachment = mock.MagicMock(messages.Attachment)
        mock_embed_field = mock.MagicMock(embeds.EmbedField)
        mock_embed = mock.MagicMock(embeds.Embed, fields=(mock_embed_field,))
        mock_sticker = mock.MagicMock(stickers.PartialSticker)
        mock_reaction = mock.MagicMock(messages.Reaction)
        mock_activity = mock.MagicMock(messages.MessageActivity)
        mock_application = mock.MagicMock(messages.MessageApplication)
        mock_reference = mock.MagicMock(messages.MessageReference)
        mock_referenced_message = object()
        mock_component = object()
        mock_referenced_message_data = mock.Mock(
            cache_utilities.MessageData, build_entity=mock.Mock(return_value=mock_referenced_message)
        )
        mock_interaction = mock.Mock()

        message_data = cache_utilities.MessageData(
            id=snowflakes.Snowflake(32123123),
            channel_id=snowflakes.Snowflake(3123123123),
            guild_id=snowflakes.Snowflake(5555555),
            author=cache_utilities.RefCell(mock_author),
            member=cache_utilities.RefCell(member_data),
            content="OKOKOK",
            timestamp=datetime.datetime(2020, 7, 30, 7, 10, 9, 550233, tzinfo=datetime.timezone.utc),
            edited_timestamp=datetime.datetime(2020, 8, 30, 7, 10, 9, 550233, tzinfo=datetime.timezone.utc),
            is_tts=True,
            user_mentions=mock_user_mentions,
            role_mention_ids=mock_role_mention_ids,
            channel_mentions=mock_channel_mentions,
            mentions_everyone=False,
            attachments=(mock_attachment,),
            embeds=(mock_embed,),
            reactions=(mock_reaction,),
            is_pinned=False,
            webhook_id=snowflakes.Snowflake(3123123),
            type=messages.MessageType.REPLY,
            activity=mock_activity,
            application=mock_application,
            message_reference=mock_reference,
            flags=messages.MessageFlag.CROSSPOSTED,
            nonce="aNonce",
            referenced_message=cache_utilities.RefCell(mock_referenced_message_data),
            stickers=(mock_sticker,),
            interaction=mock_interaction,
            application_id=snowflakes.Snowflake(123123123123),
            components=(mock_component,),
        )

        result = cache_impl._build_message(cache_utilities.RefCell(message_data))

        assert result.id == 32123123
        assert result.channel_id == 3123123123
        assert result.guild_id == 5555555
        assert result.author == mock_author
        assert result.author is not mock_author
        assert result.member is mock_member
        assert result.content == "OKOKOK"
        assert result.timestamp == datetime.datetime(2020, 7, 30, 7, 10, 9, 550233, tzinfo=datetime.timezone.utc)
        assert result.edited_timestamp == datetime.datetime(2020, 8, 30, 7, 10, 9, 550233, tzinfo=datetime.timezone.utc)
        assert result.is_tts is True
        assert result.user_mentions == {4231: mock_mention_user}
        assert result.role_mention_ids == (snowflakes.Snowflake(21323123),)
        assert result.channel_mentions == {4444: mock_channel}
        assert result.mentions_everyone is False
        assert result.attachments == (mock_attachment,)

        for field in (
            "title",
            "description",
            "url",
            "color",
            "timestamp",
            "image",
            "thumbnail",
            "video",
            "author",
            "provider",
            "footer",
        ):
            assert getattr(mock_embed, field) == getattr(result.embeds[0], field)

        assert result.embeds[0].fields == [mock_embed_field]
        assert len(result.embeds) == 1

        assert result.reactions == (mock_reaction,)
        assert result.is_pinned is False
        assert result.webhook_id == 3123123
        assert result.type is messages.MessageType.REPLY
        assert result.activity == mock_activity
        assert result.activity is not mock_activity
        assert result.application == mock_application
        assert result.application is not mock_application
        assert result.message_reference == mock_reference
        assert result.message_reference is not mock_reference
        assert result.flags == messages.MessageFlag.CROSSPOSTED
        assert result.stickers == (mock_sticker,)
        assert result.nonce == "aNonce"
        assert result.referenced_message is mock_referenced_message
        assert result.application_id == 123123123123
        assert result.interaction is mock_interaction.build_entity.return_value
        assert result.components == (mock_component,)

    def test__build_message_with_null_fields(self, cache_impl):
        message_data = cache_utilities.MessageData(
            id=snowflakes.Snowflake(32123123),
            channel_id=snowflakes.Snowflake(3123123123),
            guild_id=snowflakes.Snowflake(5555555),
            author=cache_utilities.RefCell(object()),
            member=None,
            content=None,
            timestamp=datetime.datetime(2020, 7, 30, 7, 10, 9, 550233, tzinfo=datetime.timezone.utc),
            edited_timestamp=None,
            is_tts=True,
            user_mentions=undefined.UNDEFINED,
            role_mention_ids=undefined.UNDEFINED,
            channel_mentions=undefined.UNDEFINED,
            mentions_everyone=undefined.UNDEFINED,
            attachments=(),
            embeds=(),
            reactions=(),
            is_pinned=False,
            webhook_id=None,
            type=messages.MessageType.REPLY,
            activity=None,
            application=None,
            message_reference=None,
            flags=messages.MessageFlag.CROSSPOSTED,
            nonce=None,
            referenced_message=None,
            stickers=(),
            interaction=None,
            application_id=None,
            components=(),
        )

        result = cache_impl._build_message(cache_utilities.RefCell(message_data))

        assert result.app is cache_impl._app
        assert result.member is None
        assert result.content is None
        assert result.edited_timestamp is None
        assert result.is_tts is True

        # MentionsData
        assert result.user_mentions is undefined.UNDEFINED
        assert result.role_mention_ids is undefined.UNDEFINED
        assert result.channel_mentions is undefined.UNDEFINED
        assert result.mentions_everyone is undefined.UNDEFINED

        assert result.webhook_id is None
        assert result.activity is None
        assert result.application is None
        assert result.message_reference is None
        assert result.nonce is None
        assert result.referenced_message is None
        assert result.application_id is None
        assert result.interaction is None

    @pytest.mark.skip(reason="TODO")
    def test_clear_messages(self, cache_impl):
        raise NotImplementedError

    @pytest.mark.skip(reason="TODO")
    def test_delete_message(self, cache_impl):
        raise NotImplementedError

    def test_get_message(self, cache_impl):
        mock_message_data = object()
        mock_message = object()
        cache_impl._build_message = mock.Mock(return_value=mock_message)
        cache_impl._message_entries[snowflakes.Snowflake(32332123)] = mock_message_data

        result = cache_impl.get_message(StubModel(32332123))

        assert result is mock_message
        cache_impl._build_message.assert_called_once_with(mock_message_data)

    def test_get_message_reference_only(self, cache_impl):
        mock_message_data = object()
        mock_message = object()
        cache_impl._build_message = mock.Mock(return_value=mock_message)
        cache_impl._referenced_messages[snowflakes.Snowflake(32332123)] = mock_message_data

        result = cache_impl.get_message(StubModel(32332123))

        assert result is mock_message
        cache_impl._build_message.assert_called_once_with(mock_message_data)

    def test_get_message_for_unknown_message(self, cache_impl):
        cache_impl._build_message = mock.Mock()

        result = cache_impl.get_message(StubModel(32332123))

        assert result is None
        cache_impl._build_message.assert_not_called()

    def test_get_messages_view(self, cache_impl):
        mock_message_data_1 = object()
        mock_message_data_2 = object()
        mock_message_data_3 = object()
        mock_message_1 = object()
        mock_message_2 = object()
        mock_message_3 = object()
        cache_impl._build_message = mock.Mock(side_effect=[mock_message_1, mock_message_2, mock_message_3])
        cache_impl._message_entries = collections.FreezableDict(
            {snowflakes.Snowflake(32123): mock_message_data_1, snowflakes.Snowflake(451231): mock_message_data_2}
        )
        cache_impl._referenced_messages = collections.FreezableDict({snowflakes.Snowflake(211111): mock_message_data_3})

        result = cache_impl.get_messages_view()

        assert result == {32123: mock_message_1, 451231: mock_message_2, 211111: mock_message_3}
        cache_impl._build_message.assert_has_calls(
            [mock.call(mock_message_data_1), mock.call(mock_message_data_2), mock.call(mock_message_data_3)]
        )

    @pytest.mark.skip(reason="TODO")
    def test_set_message(self, cache_impl):
        raise NotImplementedError

    def test_update_message_for_full_message(self, cache_impl):
        message = mock.Mock(messages.Message, id=snowflakes.Snowflake(45312312))
        cached_message = object()
        cache_impl.get_message = mock.Mock(side_effect=(None, cached_message))
        cache_impl.set_message = mock.Mock()

        result = cache_impl.update_message(message)

        assert result == (None, cached_message)
        cache_impl.set_message.assert_called_once_with(message)
        cache_impl.get_message.assert_has_calls([mock.call(45312312), mock.call(45312312)])

    @pytest.mark.skip(reason="TODO")
    def test_update_message_for_partial_message(self, cache_impl):
        raise NotImplementedError

    def test_update_message_for_unknown_partial_message(self, cache_impl):
        message = mock.Mock(messages.PartialMessage, id=snowflakes.Snowflake(2123123123))
        cache_impl.get_message = mock.Mock(side_effect=(None, None))
        cache_impl.set_message = mock.Mock()

        result = cache_impl.update_message(message)

        assert result == (None, None)
        cache_impl.set_message.assert_not_called()

    @pytest.mark.parametrize(
        ("name", "component", "expected"),
        [
            ("clear_dm_channel_ids", config_api.CacheComponents.DM_CHANNEL_IDS, cache_utilities.EmptyCacheView()),
            ("clear_emojis", config_api.CacheComponents.EMOJIS, cache_utilities.EmptyCacheView()),
            ("clear_emojis_for_guild", config_api.CacheComponents.EMOJIS, cache_utilities.EmptyCacheView()),
            ("clear_guild_channels", config_api.CacheComponents.GUILD_CHANNELS, cache_utilities.EmptyCacheView()),
            (
                "clear_guild_channels_for_guild",
                config_api.CacheComponents.GUILD_CHANNELS,
                cache_utilities.EmptyCacheView(),
            ),
            ("clear_guilds", config_api.CacheComponents.GUILDS, cache_utilities.EmptyCacheView()),
            ("clear_invites", config_api.CacheComponents.INVITES, cache_utilities.EmptyCacheView()),
            ("clear_invites_for_channel", config_api.CacheComponents.INVITES, cache_utilities.EmptyCacheView()),
            ("clear_invites_for_guild", config_api.CacheComponents.INVITES, cache_utilities.EmptyCacheView()),
            ("clear_members", config_api.CacheComponents.MEMBERS, cache_utilities.EmptyCacheView()),
            ("clear_members_for_guild", config_api.CacheComponents.MEMBERS, cache_utilities.EmptyCacheView()),
            ("clear_messages", config_api.CacheComponents.MESSAGES, cache_utilities.EmptyCacheView()),
            ("clear_presences", config_api.CacheComponents.PRESENCES, cache_utilities.EmptyCacheView()),
            ("clear_presences_for_guild", config_api.CacheComponents.PRESENCES, cache_utilities.EmptyCacheView()),
            ("clear_roles", config_api.CacheComponents.ROLES, cache_utilities.EmptyCacheView()),
            ("clear_roles_for_guild", config_api.CacheComponents.ROLES, cache_utilities.EmptyCacheView()),
            ("clear_stickers", config_api.CacheComponents.GUILD_STICKERS, cache_utilities.EmptyCacheView()),
            ("clear_stickers_for_guild", config_api.CacheComponents.GUILD_STICKERS, cache_utilities.EmptyCacheView()),
            ("clear_threads", config_api.CacheComponents.GUILD_THREADS, cache_utilities.EmptyCacheView()),
            ("clear_threads_for_channel", config_api.CacheComponents.GUILD_THREADS, cache_utilities.EmptyCacheView()),
            ("clear_threads_for_guild", config_api.CacheComponents.GUILD_THREADS, cache_utilities.EmptyCacheView()),
            ("clear_voice_states", config_api.CacheComponents.VOICE_STATES, cache_utilities.EmptyCacheView()),
            (
                "clear_voice_states_for_channel",
                config_api.CacheComponents.VOICE_STATES,
                cache_utilities.EmptyCacheView(),
            ),
            ("clear_voice_states_for_guild", config_api.CacheComponents.VOICE_STATES, cache_utilities.EmptyCacheView()),
            ("delete_dm_channel_id", config_api.CacheComponents.DM_CHANNEL_IDS, None),
            ("delete_emoji", config_api.CacheComponents.EMOJIS, None),
            ("delete_guild", config_api.CacheComponents.GUILDS, None),
            ("delete_guild_channel", config_api.CacheComponents.GUILD_CHANNELS, None),
            ("delete_invite", config_api.CacheComponents.INVITES, None),
            ("delete_member", config_api.CacheComponents.MEMBERS, None),
            ("delete_message", config_api.CacheComponents.MESSAGES, None),
            ("delete_presence", config_api.CacheComponents.PRESENCES, None),
            ("delete_role", config_api.CacheComponents.ROLES, None),
            ("delete_sticker", config_api.CacheComponents.GUILD_STICKERS, None),
            ("delete_thread", config_api.CacheComponents.GUILD_THREADS, None),
            ("delete_voice_state", config_api.CacheComponents.VOICE_STATES, None),
            ("get_available_guild", config_api.CacheComponents.GUILDS, None),
            ("get_available_guilds_view", config_api.CacheComponents.GUILDS, cache_utilities.EmptyCacheView()),
            ("get_dm_channel_id", config_api.CacheComponents.DM_CHANNEL_IDS, None),
            ("get_dm_channel_ids_view", config_api.CacheComponents.DM_CHANNEL_IDS, cache_utilities.EmptyCacheView()),
            ("get_emoji", config_api.CacheComponents.EMOJIS, None),
            ("get_emojis_view", config_api.CacheComponents.EMOJIS, cache_utilities.EmptyCacheView()),
            ("get_emojis_view_for_guild", config_api.CacheComponents.EMOJIS, cache_utilities.EmptyCacheView()),
            ("get_guild", config_api.CacheComponents.GUILDS, None),
            ("get_guild_channel", config_api.CacheComponents.GUILD_CHANNELS, None),
            ("get_guild_channels_view", config_api.CacheComponents.GUILD_CHANNELS, cache_utilities.EmptyCacheView()),
            (
                "get_guild_channels_view_for_guild",
                config_api.CacheComponents.GUILD_CHANNELS,
                cache_utilities.EmptyCacheView(),
            ),
            ("get_invite", config_api.CacheComponents.INVITES, None),
            ("get_invites_view", config_api.CacheComponents.INVITES, cache_utilities.EmptyCacheView()),
            ("get_invites_view_for_channel", config_api.CacheComponents.INVITES, cache_utilities.EmptyCacheView()),
            ("get_invites_view_for_guild", config_api.CacheComponents.INVITES, cache_utilities.EmptyCacheView()),
            ("get_member", config_api.CacheComponents.MEMBERS, None),
            ("get_members_view", config_api.CacheComponents.MEMBERS, cache_utilities.EmptyCacheView()),
            ("get_members_view_for_guild", config_api.CacheComponents.MEMBERS, cache_utilities.EmptyCacheView()),
            ("get_message", config_api.CacheComponents.MESSAGES, None),
            ("get_messages_view", config_api.CacheComponents.MESSAGES, cache_utilities.EmptyCacheView()),
            ("get_presence", config_api.CacheComponents.PRESENCES, None),
            ("get_presences_view", config_api.CacheComponents.PRESENCES, cache_utilities.EmptyCacheView()),
            ("get_presences_view_for_guild", config_api.CacheComponents.PRESENCES, cache_utilities.EmptyCacheView()),
            ("get_role", config_api.CacheComponents.ROLES, None),
            ("get_roles_view", config_api.CacheComponents.ROLES, cache_utilities.EmptyCacheView()),
            ("get_roles_view_for_guild", config_api.CacheComponents.ROLES, cache_utilities.EmptyCacheView()),
            ("get_sticker", config_api.CacheComponents.GUILD_STICKERS, None),
            ("get_stickers_view", config_api.CacheComponents.GUILD_STICKERS, cache_utilities.EmptyCacheView()),
            (
                "get_stickers_view_for_guild",
                config_api.CacheComponents.GUILD_STICKERS,
                cache_utilities.EmptyCacheView(),
            ),
            ("get_thread", config_api.CacheComponents.GUILD_THREADS, None),
            (
                "get_threads_view_for_channel",
                config_api.CacheComponents.GUILD_THREADS,
                cache_utilities.EmptyCacheView(),
            ),
            ("get_threads_view_for_guild", config_api.CacheComponents.GUILD_THREADS, cache_utilities.EmptyCacheView()),
            ("get_unavailable_guild", config_api.CacheComponents.GUILDS, None),
            ("get_unavailable_guilds_view", config_api.CacheComponents.GUILDS, cache_utilities.EmptyCacheView()),
            ("get_voice_state", config_api.CacheComponents.VOICE_STATES, None),
            ("get_voice_states_view", config_api.CacheComponents.VOICE_STATES, cache_utilities.EmptyCacheView()),
            (
                "get_voice_states_view_for_channel",
                config_api.CacheComponents.VOICE_STATES,
                cache_utilities.EmptyCacheView(),
            ),
            (
                "get_voice_states_view_for_guild",
                config_api.CacheComponents.VOICE_STATES,
                cache_utilities.EmptyCacheView(),
            ),
            ("set_dm_channel_id", config_api.CacheComponents.DM_CHANNEL_IDS, None),
            ("set_emoji", config_api.CacheComponents.EMOJIS, None),
            ("set_guild", config_api.CacheComponents.GUILDS, None),
            ("set_guild_availability", config_api.CacheComponents.GUILDS, None),
            ("set_guild_channel", config_api.CacheComponents.GUILD_CHANNELS, None),
            ("set_invite", config_api.CacheComponents.INVITES, None),
            ("set_me", config_api.CacheComponents.ME, None),
            ("set_member", config_api.CacheComponents.MEMBERS, None),
            ("set_message", config_api.CacheComponents.MESSAGES, None),
            ("set_presence", config_api.CacheComponents.PRESENCES, None),
            ("set_role", config_api.CacheComponents.ROLES, None),
            ("set_sticker", config_api.CacheComponents.GUILD_STICKERS, None),
            ("set_thread", config_api.CacheComponents.GUILD_THREADS, None),
            ("set_voice_state", config_api.CacheComponents.VOICE_STATES, None),
            ("update_emoji", config_api.CacheComponents.EMOJIS, (None, None)),
            ("update_guild", config_api.CacheComponents.GUILDS, (None, None)),
            ("update_guild_channel", config_api.CacheComponents.GUILD_CHANNELS, (None, None)),
            ("update_invite", config_api.CacheComponents.INVITES, (None, None)),
            ("update_me", config_api.CacheComponents.ME, (None, None)),
            ("update_member", config_api.CacheComponents.MEMBERS, (None, None)),
            ("update_message", config_api.CacheComponents.MESSAGES, (None, None)),
            ("update_presence", config_api.CacheComponents.PRESENCES, (None, None)),
            ("update_role", config_api.CacheComponents.ROLES, (None, None)),
            ("update_thread", config_api.CacheComponents.GUILD_THREADS, (None, None)),
            ("update_voice_state", config_api.CacheComponents.VOICE_STATES, (None, None)),
        ],
    )
    def test_function_default(self, cache_impl, name, component, expected):
        cache_impl._is_cache_enabled_for = mock.Mock(return_value=False)

        fn = getattr(cache_impl, name)
        n = fn.__code__.co_argcount - 1  # Don't count self as an argument as we don't need to pass it

        assert fn(*(None for _ in range(n))) == expected

        cache_impl._is_cache_enabled_for.assert_called_once_with(component)
