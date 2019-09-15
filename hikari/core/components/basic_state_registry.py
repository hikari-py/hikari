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
"""
A basic type of registry that handles storing global state.
"""
from __future__ import annotations

import logging
import typing
import weakref

from hikari.core.model import channel as _channel
from hikari.core.model import emoji as _emoji
from hikari.core.model import guild as _guild
from hikari.core.model import message as _message
from hikari.core.model import model_cache
from hikari.core.model import role as _role
from hikari.core.model import user
from hikari.core.model import user as _user
from hikari.core.model import webhook as _webhook
from hikari.core.utils import types


class BasicStateRegistry(model_cache.AbstractModelCache):
    """
    Registry for global state parsing, querying, and management.
    """

    def __init__(self, message_cache_size: int, user_dm_channel_size: int):
        # Users may be cached while we can see them, or they may be cached as a member. Regardless, we only
        # retain them while they are referenced from elsewhere to keep things tidy.
        self._users: typing.MutableMapping[int, _user.User] = weakref.WeakValueDictionary()
        self._guilds: typing.Dict[int, _guild.Guild] = {}
        self._dm_channels: typing.MutableMapping[int, _channel.DMChannel] = types.LRUDict(user_dm_channel_size)
        self._guild_channels: typing.MutableMapping[int, _channel.GuildChannel] = weakref.WeakValueDictionary()
        self._messages: typing.MutableMapping[int, _message.Message] = types.LRUDict(message_cache_size)
        self._emojis: typing.MutableMapping[int, _emoji.GuildEmoji] = weakref.WeakValueDictionary()

        #: The bot user.
        self.user: typing.Optional[_user.BotUser] = None

        #: Our logger.
        self.logger = logging.getLogger(__name__)

    def get_user_by_id(self, user_id: int):
        return self._users.get(user_id)

    def delete_member_from_guild(self, user_id: int, guild_id: int):
        guild = self._guilds[guild_id]
        member = guild.members[user_id]
        del guild.members[user_id]
        return member

    def get_guild_by_id(self, guild_id: int):
        return self._guilds.get(guild_id)

    def delete_guild(self, guild_id: int):
        guild = self._guilds[guild_id]
        del self._guilds[guild_id]
        return guild

    def delete_dm_channel(self, channel_id: int):
        channel = self._dm_channels[channel_id]
        del self._dm_channels[channel_id]
        return channel

    def delete_guild_channel(self, channel_id: int):
        guild = self._guild_channels[channel_id].guild
        channel = guild.channels[channel_id]
        del guild.channels[channel_id]
        return channel

    def get_message_by_id(self, message_id: int):
        return self._messages.get(message_id)

    def get_dm_channel_by_id(self, dm_channel_id: int):
        return self._dm_channels.get(dm_channel_id)

    def get_guild_channel_by_id(self, guild_channel_id: int):
        return self._guild_channels.get(guild_channel_id)

    def get_emoji_by_id(self, emoji_id: int):
        return self._emojis.get(emoji_id)

    def parse_user(self, user: types.DiscordObject):
        # If the user already exists, then just return their existing object. We expect discord to tell us if they
        # get updated if they are a member, and for anything else the object will just be disposed of once we are
        # finished with it anyway.
        user_id = int(user["id"])
        if user_id not in self._users:
            # DO NOT MAKE THIS INTO A ONE LINER, IT IS A WEAK REF SO WILL BE GARBAGE COLLECTED IMMEDIATELY IF YOU DO.
            user_obj = _user.User(self, user)
            self._users[user_id] = user_obj
        return self._users[user_id]

    def parse_guild(self, guild: types.DiscordObject):
        guild_id = int(guild["id"])
        unavailable = guild.get("unavailable", False)
        if unavailable and guild_id in self._guilds:
            self._guilds[guild_id].unavailable = True
            return self._guilds[guild_id]
        else:
            guild_obj = _guild.Guild(self, guild)
            self._guilds[guild_id] = guild_obj
            return guild_obj

    def parse_member(self, member: types.DiscordObject, guild_id: int):
        # Don't cache members here.
        guild = self.get_guild_by_id(guild_id)
        member_id = int(member["user"]["id"])

        if guild is None:
            self.logger.warning("Member ID %s referencing an unknown guild %s; ignoring", member_id, guild_id)
            return None
        elif member_id in guild.members:
            return guild.members[member_id]
        else:
            member_object = _user.Member(self, guild_id, member)
            guild.members[member_id] = member_object
            return member_object

    def parse_role(self, role: types.DiscordObject):
        # Don't cache roles.
        return _role.Role(role)

    def parse_emoji(self, emoji: types.DiscordObject, guild_id: typing.Optional[int]):
        emoji = _emoji.emoji_from_dict(self, emoji, guild_id)
        if isinstance(emoji, _emoji.GuildEmoji):
            # Only cache guild emojis.
            self._emojis[guild_id] = emoji
        return emoji

    def parse_webhook(self, webhook: types.DiscordObject):
        # Don't cache webhooks.
        return _webhook.Webhook(self, webhook)

    def parse_message(self, message: types.DiscordObject):
        # Always update the cache with the new message.
        message_id = int(message["id"])
        message_obj = _message.Message(self, message)
        self._messages[message_id] = message_obj
        message_obj.channel.last_message_id = message_id
        return message_obj

    def parse_channel(self, channel: types.DiscordObject):
        # Only cache DM channels.
        channel_obj = _channel.channel_from_dict(self, channel)
        if channel_obj.is_dm:
            if channel_obj.id in self._dm_channels:
                return self._dm_channels[channel_obj.id]

            self._dm_channels[channel_obj.id] = channel_obj
        else:
            if channel_obj.guild is not None:
                channel_obj.guild.channels[channel_obj.id] = channel_obj

        return channel_obj

    def parse_bot_user(self, bot_user: types.DiscordObject) -> user.BotUser:
        bot_user = _user.BotUser(self, bot_user)
        self.user = bot_user
        return bot_user
