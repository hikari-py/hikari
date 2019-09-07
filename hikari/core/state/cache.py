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
Implementation of a model cache.
"""
from __future__ import annotations

import logging
import typing
import weakref

from hikari.core.model import channel as _channel
from hikari.core.model import emoji as _emoji
from hikari.core.model import guild as _guild
from hikari.core.model import message as _message
from hikari.core.model import role as _role
from hikari.core.model import user as _user
from hikari.core.model import webhook as _webhook
from hikari.core.model import model_cache
from hikari.core.utils import transform
from hikari.core.utils import types


class InMemoryCache(model_cache.AbstractModelCache):
    """
    Implementation of :class:`model_state.AbstractModelState` which implements the caching logic needed for a shard.

    This is expected to be further extended elsewhere to provide the ability to handle incoming gateway payloads.

    The class itself is designed to be easily overridable should one wish to provide their own implementations.
    """

    def __init__(self, message_cache_size: int = 100, user_dm_channel_size: int = 100) -> None:
        # Users may be cached while we can see them, or they may be cached as a member. Regardless, we only
        # retain them while they are referenced from elsewhere to keep things tidy.
        # noinspection PyTypeChecker
        self._users: typing.Dict[int, _user.User] = weakref.WeakValueDictionary()
        self._guilds: typing.Dict[int, _guild.Guild] = {}
        self._dm_channels: typing.Dict[int, _channel.DMChannel] = types.LRUDict(user_dm_channel_size)
        self._guild_channels = weakref.WeakValueDictionary()
        self._messages = types.LRUDict(message_cache_size)
        self._emojis = weakref.WeakValueDictionary()
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
        user_id = transform.get_cast(user, "id", int)
        if user_id not in self._users:
            self._users[user_id] = _user.User(self, user)
        return self._users[user_id]

    def parse_guild(self, guild: types.DiscordObject):
        guild_id = transform.get_cast(guild, "id", int)
        if guild_id not in self._guilds:
            self._guilds[guild_id] = _guild.Guild(self, guild)
        return self._guilds[guild_id]

    def parse_member(self, member: types.DiscordObject, guild_id: int):
        # Don't cache members here.
        guild = self.get_guild_by_id(guild_id)
        member_id = transform.get_cast(member, "id", int)

        if guild is None:
            self.logger.warning("Member ID %s referencing an unknown guild %s and is discarded", member_id, guild_id)
        elif member_id in guild.members:
            return guild.members[member_id]
        else:
            member_object = _user.Member(self, guild_id, member)
            guild.members[member_id] = member_object
            return member_object

    def parse_role(self, role: types.DiscordObject):
        # Don't cache roles.
        return _role.Role(role)

    def parse_emoji(self, guild_id: int, emoji: types.DiscordObject):
        # Don't cache emojis.
        return _emoji.Emoji(self, emoji, guild_id)

    def parse_webhook(self, webhook: types.DiscordObject):
        # Don't cache webhooks.
        return _webhook.Webhook(self, webhook)

    def parse_message(self, message: types.DiscordObject):
        # Always update the cache with the new message.
        message_id = transform.get_cast(message, "id", int)
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

        return channel_obj


__all__ = ("InMemoryCache",)
