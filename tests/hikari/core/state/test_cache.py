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

from hikari.core.model import channel as _channel
from hikari.core.model import emoji as _emoji
from hikari.core.model import guild as _guild
from hikari.core.model import message as _message
from hikari.core.model import role as _role
from hikari.core.model import user as _user
from hikari.core.model import webhook as _webhook
from hikari.core.state import cache


@pytest.mark.state
class TestInMemoryCache:
    @pytest.fixture()
    def in_memory_cache(self):
        return cache.InMemoryCache()

    def test_get_user_by_id_calls_get(self, in_memory_cache):
        in_memory_cache._users = mock.MagicMock(spec_set=dict)
        in_memory_cache.get_user_by_id(123)
        in_memory_cache._users.get.assert_called_once_with(123)

    def test_get_guild_by_id_calls_get(self, in_memory_cache):
        in_memory_cache._guilds = mock.MagicMock(spec_set=dict)
        in_memory_cache.get_guild_by_id(123)
        in_memory_cache._guilds.get.assert_called_once_with(123)

    def test_get_guild_channel_by_id_calls_get(self, in_memory_cache):
        in_memory_cache._guild_channels = mock.MagicMock(spec_set=dict)
        in_memory_cache.get_guild_channel_by_id(123)
        in_memory_cache._guild_channels.get.assert_called_once_with(123)

    def test_get_dm_channel_by_id_calls_get(self, in_memory_cache):
        in_memory_cache._dm_channels = mock.MagicMock(spec_set=dict)
        in_memory_cache.get_dm_channel_by_id(123)
        in_memory_cache._dm_channels.get.assert_called_once_with(123)

    def test_get_message_by_id_calls_get(self, in_memory_cache):
        in_memory_cache._messages = mock.MagicMock(spec_set=dict)
        in_memory_cache.get_message_by_id(123)
        in_memory_cache._messages.get.assert_called_once_with(123)

    def test_get_emoji_by_id_calls_get(self, in_memory_cache):
        in_memory_cache._emojis = mock.MagicMock(spec_set=dict)
        in_memory_cache.get_emoji_by_id(123)
        in_memory_cache._emojis.get.assert_called_once_with(123)

    def test_parse_existing_user(self, in_memory_cache):
        payload = {"id": "1234"}
        existing_user = mock.MagicMock(spec_set=_user.User)
        in_memory_cache._users = {1234: existing_user}
        with mock.patch.object(_user.User, "__new__", return_value=...) as __new__:
            user = in_memory_cache.parse_user(payload)
            __new__.assert_not_called()
            assert user is existing_user
        assert in_memory_cache._users == {1234: existing_user}

    def test_parse_new_user(self, in_memory_cache):
        payload = {"id": "1234"}
        in_memory_cache._users = {}
        new_user = mock.MagicMock(spec_set=_user.User)
        with mock.patch.object(_user.User, "__new__", return_value=new_user) as __new__:
            user = in_memory_cache.parse_user(payload)
            __new__.assert_called_once_with(_user.User, in_memory_cache, payload)
            assert user is new_user

    def test_parse_existing_guild(self, in_memory_cache):
        payload = {"id": "1234"}
        existing_guild = mock.MagicMock(spec_set=_guild.Guild)
        in_memory_cache._guilds = {1234: existing_guild}
        with mock.patch.object(_guild.Guild, "__new__") as __new__:
            guild = in_memory_cache.parse_guild(payload)
            __new__.assert_not_called()
            assert guild is existing_guild
        assert in_memory_cache._guilds == {1234: existing_guild}

    def test_parse_new_guild(self, in_memory_cache):
        payload = {"id": "1234"}
        in_memory_cache._guilds = {}
        new_guild = mock.MagicMock(spec_set=_guild.Guild)
        with mock.patch.object(_guild.Guild, "__new__", return_value=new_guild) as __new__:
            guild = in_memory_cache.parse_guild(payload)
            __new__.assert_called_once_with(_guild.Guild, in_memory_cache, payload)
            assert guild is new_guild

    def test_parse_existing_emoji(self, in_memory_cache):
        # We aren't caching emojis for now...
        payload = {"id": "1234"}
        in_memory_cache._emojis = {}
        new_emoji = mock.MagicMock(spec_set=_emoji.Emoji)
        with mock.patch.object(_emoji.Emoji, "__new__", return_value=new_emoji) as __new__:
            emoji = in_memory_cache.parse_emoji(1234, payload)
            __new__.assert_called_once_with(_emoji.Emoji, in_memory_cache, payload, 1234)
            assert emoji is new_emoji

    def test_parse_new_emoji(self, in_memory_cache):
        payload = {"id": "1234"}
        in_memory_cache._emojis = {}
        new_emoji = mock.MagicMock(spec_set=_emoji.Emoji)
        with mock.patch.object(_emoji.Emoji, "__new__", return_value=new_emoji) as __new__:
            emoji = in_memory_cache.parse_emoji(1234, payload)
            __new__.assert_called_once_with(_emoji.Emoji, in_memory_cache, payload, 1234)
            assert emoji is new_emoji

    def test_parse_existing_message(self, in_memory_cache):
        payload = {"id": "1234"}
        existing_message = mock.MagicMock(spec_set=_message.Message)
        in_memory_cache._messages = {1234: existing_message}
        new_message = mock.MagicMock(spec_set=_message.Message)

        assert existing_message in in_memory_cache._messages.values()
        assert new_message not in in_memory_cache._messages.values()

        with mock.patch.object(_message.Message, "__new__", return_value=new_message) as __new__:
            message = in_memory_cache.parse_message(payload)
            __new__.assert_called_once_with(_message.Message, in_memory_cache, payload)
            assert message is new_message

        assert existing_message not in in_memory_cache._messages.values()
        assert new_message in in_memory_cache._messages.values()

    def test_parse_new_message(self, in_memory_cache):
        payload = {"id": "1234"}
        in_memory_cache._messages = {}
        new_message = mock.MagicMock(spec_set=_message.Message)
        new_message.id = 1234

        assert new_message not in in_memory_cache._messages.values()

        with mock.patch.object(_message.Message, "__new__", return_value=new_message) as __new__:
            message = in_memory_cache.parse_message(payload)
            __new__.assert_called_once_with(_message.Message, in_memory_cache, payload)
            assert message is new_message

        assert new_message in in_memory_cache._messages.values()

    @pytest.mark.parametrize(
        ["impl", "is_dm"],
        [
            (_channel.DMChannel, True),
            (_channel.GroupDMChannel, True),
            (_channel.GuildCategory, False),
            (_channel.GuildNewsChannel, False),
            (_channel.GuildStoreChannel, False),
            (_channel.GuildTextChannel, False),
            (_channel.GuildVoiceChannel, False),
        ],
    )
    def test_maybe_parse_existing_channel(self, in_memory_cache, impl, is_dm):
        type_id = [key for key, value in _channel._channel_type_to_class.items()][0]
        payload = {"id": "1234", "type": type_id}
        existing_channel = mock.MagicMock(spec_set=_channel.Channel)
        in_memory_cache._dm_channels = {1234: existing_channel}

        new_channel = mock.MagicMock(spec_set=_channel.Channel)
        new_channel.id = 1234
        setattr(new_channel, "is_dm", is_dm)

        with mock.patch.object(_channel, "channel_from_dict", return_value=new_channel) as __new__:
            channel = in_memory_cache.parse_channel(payload)
            __new__.assert_called_once_with(in_memory_cache, payload)

            if is_dm:
                # DM channels that exist should not be parsed, the cached channel should be used.
                assert in_memory_cache._dm_channels == {1234: existing_channel}
                assert channel is existing_channel
            else:
                # Non dm channels should always be parsed, as we don't cache them.
                assert in_memory_cache._dm_channels == {1234: existing_channel}

    @pytest.mark.parametrize(
        ["impl", "is_dm"],
        [
            (_channel.DMChannel, True),
            (_channel.GroupDMChannel, True),
            (_channel.GuildCategory, False),
            (_channel.GuildNewsChannel, False),
            (_channel.GuildStoreChannel, False),
            (_channel.GuildTextChannel, False),
            (_channel.GuildVoiceChannel, False),
        ],
    )
    def test_maybe_parse_new_channel(self, in_memory_cache, impl, is_dm):
        type_id = [key for key, value in _channel._channel_type_to_class.items()][0]
        payload = {"id": "12345", "type": type_id}
        existing_channel = mock.MagicMock(spec_set=_channel.Channel)
        in_memory_cache._dm_channels = {1234: existing_channel}
        new_channel = mock.MagicMock(spec_set=_channel.Channel)
        new_channel.id = 12345
        setattr(new_channel, "is_dm", is_dm)

        with mock.patch.object(_channel, "channel_from_dict", return_value=new_channel) as __new__:
            channel = in_memory_cache.parse_channel(payload)

            # DM channels that don't yet exist must be parsed. We parse other channels regardless.
            __new__.assert_called_once_with(in_memory_cache, payload)

            if is_dm:
                assert channel is new_channel
                assert in_memory_cache._dm_channels == {1234: existing_channel, 12345: new_channel}
            else:
                assert in_memory_cache._dm_channels == {1234: existing_channel}

            assert channel is new_channel

    def test_parse_webhook(self, in_memory_cache):
        payload = {"id": "1234"}
        webhook = mock.MagicMock(spec_set=_webhook.Webhook)
        with mock.patch.object(_webhook.Webhook, "__new__", return_value=webhook) as __new__:
            assert in_memory_cache.parse_webhook(payload) is webhook
            __new__.assert_called_once_with(_webhook.Webhook, in_memory_cache, payload)

    def test_parse_member_in_nonexistent_guild(self, in_memory_cache):
        in_memory_cache._guilds = {}
        payload = {"id": "1234"}
        member = mock.MagicMock(spec_set=_user.Member)
        with mock.patch.object(_user.Member, "__new__", return_value=member) as __new__:
            in_memory_cache.logger = mock.MagicMock()
            assert in_memory_cache.parse_member(payload, 9876) is None
            in_memory_cache.logger.warning.assert_called_once()

    def test_parse_new_member_in_existent_guild(self, in_memory_cache):
        guild = mock.MagicMock(spec_set=_guild.Guild)
        guild.members = {}

        in_memory_cache._guilds = {9876: guild}

        payload = {"id": "1234"}

        member = mock.MagicMock(spec_set=_user.Member)
        with mock.patch.object(_user.Member, "__new__", return_value=member) as __new__:
            assert in_memory_cache.parse_member(payload, 9876) is member
            __new__.assert_called_once_with(_user.Member, in_memory_cache, 9876, payload)
            assert guild.members == {1234: member}

    def test_parse_existing_member_in_existent_guild(self, in_memory_cache):
        guild = mock.MagicMock(spec_set=_guild.Guild)
        existing_member = mock.MagicMock(spec_set=_user.Member)
        guild.members = {1234: existing_member}

        in_memory_cache._guilds = {9876: guild}

        payload = {"id": "1234"}

        new_member = mock.MagicMock(spec_set=_user.Member)
        with mock.patch.object(_user.Member, "__new__", return_value=new_member) as __new__:
            assert in_memory_cache.parse_member(payload, 9876) is existing_member
            __new__.assert_not_called()
            assert guild.members == {1234: existing_member}

    def test_parse_role(self, in_memory_cache):
        payload = {"id": "1234"}
        role = mock.MagicMock(spec_set=_role.Role)
        with mock.patch.object(_role.Role, "__new__", return_value=role) as __new__:
            assert in_memory_cache.parse_role(payload) is role
            __new__.assert_called_once_with(_role.Role, payload)
