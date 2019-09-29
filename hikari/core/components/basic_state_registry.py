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

import datetime
import typing
import weakref

from hikari.core.model import channel as _channel
from hikari.core.model import emoji as _emoji
from hikari.core.model import guild as _guild
from hikari.core.model import message as _message
from hikari.core.model import abstract_state_registry
from hikari.core.model import role as _role
from hikari.core.model import user as _user
from hikari.core.model import webhook as _webhook
from hikari.core.utils import assertions
from hikari.core.utils import logging_utils
from hikari.core.utils import types


class BasicStateRegistry(abstract_state_registry.AbstractStateRegistry):
    """
    Registry for global state parsing, querying, and management.

    This implementation uses a set of mappings in memory to handle lookups in an average-case time of O(k) and a
    worst case time of O(n). For objects that have ownership in other objects (e.g. roles that are owned by a guild),
    we provide internally weak mappings to look up these values quickly. This enables operations such as role deletion
    to run in O(k) average time, and worst case time of O(n) rather than average time of O(n) and worst case time of
    O(mn) (where M denotes the number of guilds in the cache, and N denotes the number of roles on average in each
    guild).

    Weak references are used internally to enable atomic destruction of transitively owned objects when references
    elsewhere are dropped.

    Cache accesses are not asynchronous. This means that this implementation is not suitable for interfacing with a
    distributed cache (e.g. Redis). If you wish to instead use that sort of implementation, you should create an
    implementation from :class:`hikari.core.mode.abstract_state_registry.AbstractStateRegistry` and implement each
    method as a coroutine function. You will also need to update the models that access the cache, and the event
    adapter that calls this cache, appropriately.
    """

    __slots__ = (
        "_dm_channels",
        "_emojis",
        "_guilds",
        "_guild_channels",
        "_messages",
        "_roles",
        "_users",
        "user",
        "logger",
    )

    def __init__(self, message_cache_size: int, user_dm_channel_size: int) -> None:
        # Users may be cached while we can see them, or they may be cached as a member. Regardless, we only
        # retain them while they are referenced from elsewhere to keep things tidy.
        self._dm_channels: typing.MutableMapping[int, _channel.DMChannel] = types.LRUDict(user_dm_channel_size)
        self._emojis: typing.MutableMapping[int, _emoji.GuildEmoji] = weakref.WeakValueDictionary()
        self._guilds: typing.Dict[int, _guild.Guild] = {}
        self._guild_channels: typing.MutableMapping[int, _channel.GuildChannel] = weakref.WeakValueDictionary()
        self._messages: typing.MutableMapping[int, _message.Message] = types.LRUDict(message_cache_size)
        self._roles: typing.MutableMapping[int, _role.Role] = weakref.WeakValueDictionary()
        self._users: typing.MutableMapping[int, _user.User] = weakref.WeakValueDictionary()

        #: The bot user.
        self.user: typing.Optional[_user.BotUser] = None

        #: Our logger.
        self.logger = logging_utils.get_named_logger(self)

    def delete_channel(self, channel_id: int) -> _channel.Channel:
        if channel_id in self._guild_channels:
            guild = self._guild_channels[channel_id].guild
            channel = guild.channels[channel_id]
            del guild.channels[channel_id]
            del self._guild_channels[channel_id]
            return channel
        elif channel_id in self._dm_channels:
            channel = self._dm_channels[channel_id]
            del self._dm_channels[channel_id]
            return channel
        else:
            raise KeyError(str(channel_id))

    def delete_emoji(self, emoji_id: int) -> _emoji.GuildEmoji:
        emoji = self._emojis[emoji_id]
        guild = emoji.guild
        del guild.emojis[emoji_id]
        del self._emojis[emoji_id]
        return emoji

    def delete_guild(self, guild_id: int) -> _guild.Guild:
        guild = self._guilds[guild_id]
        del self._guilds[guild_id]
        return guild

    def delete_member_from_guild(self, user_id: int, guild_id: int) -> _user.Member:
        guild = self._guilds[guild_id]
        member = guild.members[user_id]
        del guild.members[user_id]
        return member

    def delete_role(self, role_id: int) -> _role.Role:
        role = self._roles[role_id]
        guild = role.guild
        del guild.roles[role_id]
        del self._roles[role_id]
        return role

    def get_channel_by_id(self, channel_id: int) -> typing.Optional[_channel.Channel]:
        return self._guild_channels.get(channel_id) or self._dm_channels.get(channel_id)

    def get_emoji_by_id(self, emoji_id: int):
        return self._emojis.get(emoji_id)

    def get_guild_by_id(self, guild_id: int):
        return self._guilds.get(guild_id)

    def get_guild_channel_by_id(self, guild_channel_id: int):
        return self._guild_channels.get(guild_channel_id)

    def get_message_by_id(self, message_id: int):
        return self._messages.get(message_id)

    def get_role_by_id(self, role_id: int) -> typing.Optional[_role.Role]:
        pass

    def get_user_by_id(self, user_id: int):
        return self._users.get(user_id)

    def parse_bot_user(self, bot_user: types.DiscordObject) -> _user.BotUser:
        bot_user = _user.BotUser(self, bot_user)
        self.user = bot_user
        return bot_user

    def parse_channel(self, channel: types.DiscordObject):
        # Only cache DM channels directly
        channel_obj = _channel.channel_from_dict(self, channel)
        if channel_obj.is_dm:
            if channel_obj.id in self._dm_channels:
                return self._dm_channels[channel_obj.id]

            self._dm_channels[channel_obj.id] = channel_obj
        else:
            if channel_obj.guild is not None:
                channel_obj.guild.channels[channel_obj.id] = channel_obj

        return channel_obj

    # These fix typing issues in the update_guild_emojis method.
    @typing.overload
    def parse_emoji(self, emoji: types.DiscordObject, guild_id: int) -> _emoji.GuildEmoji:
        ...

    @typing.overload
    def parse_emoji(self, emoji: types.DiscordObject, guild_id: None) -> _emoji.AbstractEmoji:
        ...

    def parse_emoji(self, emoji, guild_id):
        existing_emoji = None
        if guild_id is not None and _emoji.is_payload_guild_emoji_candidate(emoji):
            emoji_id = int(emoji["id"])
            existing_emoji = self.get_emoji_by_id(emoji_id)

        if existing_emoji is not None:
            existing_emoji.update_state(emoji)
            return existing_emoji

        return _emoji.emoji_from_dict(self, emoji, guild_id)

    def parse_guild(self, guild: types.DiscordObject):
        guild_id = int(guild["id"])
        unavailable = guild.get("unavailable", False)
        if guild_id in self._guilds:
            if unavailable:
                self._guilds[guild_id].unavailable = True
                return self._guilds[guild_id]
            else:
                self._guilds[guild_id].update_state(guild)
        else:
            guild_obj = _guild.Guild(self, guild)
            self._guilds[guild_id] = guild_obj
            return guild_obj

    def parse_member(self, member: types.DiscordObject, guild_id: int):
        # Don't cache members here.
        guild = self.get_guild_by_id(guild_id)
        member_id = int(member["user"]["id"])

        if guild is not None and member_id in guild.members:
            return guild.members[member_id]
        else:
            member_object = _user.Member(self, guild_id, member)

            # Guild may be none when we receive this member for the first time in a GUILD_CREATE payload.
            if guild is not None:
                guild.members[member_id] = member_object
            return member_object

    def parse_message(self, message: types.DiscordObject):
        # Always update the cache with the new message.
        message_id = int(message["id"])
        message_obj = _message.Message(self, message)
        self._messages[message_id] = message_obj
        message_obj.channel.last_message_id = message_id
        return message_obj

    def parse_role(self, role: types.DiscordObject, guild_id: int):
        role = _role.Role(self, role, guild_id)
        self._roles[role.id] = role
        return role

    def parse_user(self, user: types.DiscordObject):
        # If the user already exists, then just return their existing object. We expect discord to tell us if they
        # get updated if they are a member, and for anything else the object will just be disposed of once we are
        # finished with it anyway.
        user_id = int(user["id"])
        if user_id not in self._users:
            user_obj = _user.User(self, user)
            self._users[user_id] = user_obj
            return user_obj
        else:
            existing_user = self._users[user_id]
            existing_user.update_state(user)
            return existing_user

    def parse_webhook(self, webhook: types.DiscordObject):
        # Don't cache webhooks.
        return _webhook.Webhook(self, webhook)

    def update_last_pinned_timestamp(self, channel_id: int, timestamp: typing.Optional[datetime.datetime]) -> None:
        # We don't persist this information, as it is not overly useful. The user can use the HTTP endpoint if they
        # care what the pins are...
        pass

    def update_guild_emojis(
        self, emoji_list: typing.List[types.DiscordObject], guild_id: int
    ) -> typing.Tuple[typing.FrozenSet[_emoji.GuildEmoji], typing.FrozenSet[_emoji.GuildEmoji]]:
        guild = assertions.assert_not_none(self.get_guild_by_id(guild_id), f"guild {guild_id} was not cached")
        old_emojis = frozenset(guild.emojis.values())
        new_emojis = frozenset(self.parse_emoji(emoji, guild_id) for emoji in emoji_list)
        return old_emojis, new_emojis
