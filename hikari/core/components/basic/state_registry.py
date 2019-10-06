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

from hikari.core.model import abstract_state_registry
from hikari.core.model import channel
from hikari.core.model import emoji
from hikari.core.model import guild
from hikari.core.model import presence
from hikari.core.model import message
from hikari.core.model import role
from hikari.core.model import user
from hikari.core.model import webhook
from hikari.core.utils import logging_utils
from hikari.core.utils import transform
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
        self._dm_channels: typing.MutableMapping[int, channel.DMChannel] = types.LRUDict(user_dm_channel_size)
        self._emojis: typing.MutableMapping[int, emoji.GuildEmoji] = weakref.WeakValueDictionary()
        self._guilds: typing.Dict[int, guild.Guild] = {}
        self._guild_channels: typing.MutableMapping[int, channel.GuildChannel] = weakref.WeakValueDictionary()
        self._messages: typing.MutableMapping[int, message.Message] = types.LRUDict(message_cache_size)
        self._roles: typing.MutableMapping[int, role.Role] = weakref.WeakValueDictionary()
        self._users: typing.MutableMapping[int, user.User] = weakref.WeakValueDictionary()

        #: The bot user.
        self.user: typing.Optional[user.BotUser] = None

        #: Our logger.
        self.logger = logging_utils.get_named_logger(self)

    def delete_channel(self, channel_id: int) -> channel.Channel:
        if channel_id in self._guild_channels:
            guild_obj = self._guild_channels[channel_id].guild
            channel_obj = guild_obj.channels[channel_id]
            del guild_obj.channels[channel_id]
            del self._guild_channels[channel_id]
        elif channel_id in self._dm_channels:
            channel_obj = self._dm_channels[channel_id]
            del self._dm_channels[channel_id]
        else:
            raise KeyError(str(channel_id))

        return channel_obj

    def delete_emoji(self, emoji_id: int) -> emoji.GuildEmoji:
        emoji_obj = self._emojis[emoji_id]
        guild_obj = emoji_obj.guild
        del guild_obj.emojis[emoji_id]
        del self._emojis[emoji_id]
        return emoji_obj

    def delete_guild(self, guild_id: int) -> guild.Guild:
        guild_obj = self._guilds[guild_id]
        del self._guilds[guild_id]
        return guild_obj

    def delete_member_from_guild(self, user_id: int, guild_id: int) -> user.Member:
        guild_obj = self._guilds[guild_id]
        member_obj = guild_obj.members[user_id]
        del guild_obj.members[user_id]
        return member_obj

    # noinspection PyProtectedMember
    def delete_role(self, guild_id: int, role_id: int) -> role.Role:
        guild_obj = self._guilds[guild_id]
        role_obj = guild_obj.roles[role_id]
        del guild_obj.roles[role_id]
        for member in guild_obj.members.values():
            if role_id in member._role_ids:
                member._role_ids.remove(role_id)

        return role_obj

    def get_channel_by_id(self, channel_id: int) -> typing.Optional[channel.Channel]:
        return self._guild_channels.get(channel_id) or self._dm_channels.get(channel_id)

    def get_emoji_by_id(self, emoji_id: int):
        return self._emojis.get(emoji_id)

    def get_guild_by_id(self, guild_id: int):
        return self._guilds.get(guild_id)

    def get_guild_channel_by_id(self, guild_channel_id: int):
        return self._guild_channels.get(guild_channel_id)

    def get_message_by_id(self, message_id: int):
        return self._messages.get(message_id)

    def get_role_by_id(self, guild_id: int, role_id: int) -> typing.Optional[role.Role]:
        self._

    def get_user_by_id(self, user_id: int):
        return self._users.get(user_id)

    def parse_bot_user(self, bot_user_payload: types.DiscordObject) -> user.BotUser:
        bot_user_payload = user.BotUser(self, bot_user_payload)
        self.user = bot_user_payload
        return bot_user_payload

    def parse_channel(self, channel_payload: types.DiscordObject) -> channel.Channel:
        channel_id = int(channel_payload["id"])
        channel_obj = self.get_channel_by_id(channel_id)
        if channel_obj is not None:
            channel_obj.update_state(channel_payload)
        else:
            channel_obj = channel.channel_from_dict(self, channel_payload)
            if channel.is_channel_type_dm(channel_payload["type"]):
                self._dm_channels[channel_id] = channel_obj
            else:
                self._guild_channels[channel_id] = channel_obj
                channel_obj.guild.channels[channel_id] = channel_obj

        return channel_obj

    # These fix typing issues in the update_guild_emojis method.
    @typing.overload
    def parse_emoji(self, emoji_payload: types.DiscordObject, guild_id: int) -> emoji.GuildEmoji:
        ...

    @typing.overload
    def parse_emoji(self, emoji_payload: types.DiscordObject, guild_id: None) -> emoji.AbstractEmoji:
        ...

    def parse_emoji(self, emoji_payload, guild_id):
        existing_emoji = None
        if guild_id is not None and emoji.is_payload_guild_emoji_candidate(emoji_payload):
            emoji_id = int(emoji_payload["id"])
            existing_emoji = self.get_emoji_by_id(emoji_id)

        if existing_emoji is not None:
            existing_emoji.update_state(emoji_payload)
            return existing_emoji

        return emoji.emoji_from_dict(self, emoji_payload, guild_id)

    def parse_guild(self, guild_payload: types.DiscordObject):
        guild_id = int(guild_payload["id"])
        unavailable = guild_payload.get("unavailable", False)
        if guild_id in self._guilds:
            guild_obj = self._guilds[guild_id]
            if unavailable:
                guild_obj.unavailable = True
            else:
                guild_obj.update_state(guild_payload)
        else:
            guild_obj = guild.Guild(self, guild_payload)
            self._guilds[guild_id] = guild_obj

        return guild_obj

    def parse_member(self, member_payload: types.DiscordObject, guild_id: int):
        # Don't cache members here.
        guild_obj = self.get_guild_by_id(guild_id)
        member_id = int(member_payload["user"]["id"])

        if guild is not None and member_id in guild_obj.members:
            return guild_obj.members[member_id]
        else:
            member_obj = user.Member(self, guild_id, member_payload)

            # Guild may be none when we receive this member for the first time in a GUILD_CREATE payload.
            if guild is not None:
                guild_obj.members[member_id] = member_obj
            return member_obj

    def parse_message(self, message_payload: types.DiscordObject):
        # Always update the cache with the new message.
        message_id = int(message_payload["id"])
        message_obj = message.Message(self, message_payload)
        self._messages[message_id] = message_obj
        message_obj.channel.last_message_id = message_id
        return message_obj

    def parse_presence(self, guild_id: int, user_id: int, presence_payload: types.DiscordObject):
        presence_obj = presence.Presence(presence_payload)
        guild_obj = self.get_guild_by_id(guild_id)
        if guild is not None and user_id in guild_obj.members:
            guild_obj.members[user_id].presence = presence_obj
        return presence_obj

    def parse_role(self, role_payload: types.DiscordObject, guild_id: int):
        role_payload = role.Role(self, role_payload, guild_id)
        self._roles[role_payload.id] = role_payload
        return role_payload

    def parse_user(self, user_payload: types.DiscordObject):
        # If the user already exists, then just return their existing object. We expect discord to tell us if they
        # get updated if they are a member, and for anything else the object will just be disposed of once we are
        # finished with it anyway.
        user_id = int(user_payload["id"])
        if user_id not in self._users:
            user_obj = user.User(self, user_payload)
            self._users[user_id] = user_obj
            return user_obj
        else:
            existing_user = self._users[user_id]
            existing_user.update_state(user_payload)
            return existing_user

    def parse_webhook(self, webhook_payload: types.DiscordObject):
        # Don't cache webhooks.
        return webhook.Webhook(self, webhook_payload)

    def set_guild_unavailability(self, guild_id: int, unavailability: bool) -> None:
        guild_obj = self.get_guild_by_id(guild_id)
        if guild_obj is not None:
            guild_obj.unavailable = unavailability

    def update_channel(
        self, channel_payload: types.DiscordObject
    ) -> typing.Optional[typing.Tuple[channel.Channel, channel.Channel]]:
        channel_id = int(channel_payload["id"])
        existing_channel = self.get_channel_by_id(channel_id)
        if existing_channel is not None:
            old_channel = existing_channel.clone()
            new_channel = existing_channel
            new_channel.update_state(channel_payload)
            return old_channel, new_channel
        else:
            return None

    def update_guild(
        self, guild_payload: types.DiscordObject
    ) -> typing.Optional[typing.Tuple[guild.Guild, guild.Guild]]:
        guild_id = int(guild_payload["id"])
        guild_obj = self.get_guild_by_id(guild_id)
        if guild_obj is not None:
            previous_guild = guild_obj.clone()
            new_guild = guild_obj
            new_guild.update_state(guild_payload)
            return previous_guild, new_guild
        else:
            return None

    def update_guild_emojis(
        self, emoji_list: typing.List[types.DiscordObject], guild_id: int
    ) -> typing.Optional[typing.Tuple[typing.FrozenSet[emoji.GuildEmoji], typing.FrozenSet[emoji.GuildEmoji]]]:
        guild_obj = self.get_guild_by_id(guild_id)
        if guild_obj is not None:
            old_emojis = frozenset(guild_obj.emojis.values())
            new_emojis = frozenset(self.parse_emoji(emoji, guild_id) for emoji in emoji_list)
            guild_obj.emojis = transform.snowflake_map(new_emojis)
            return old_emojis, new_emojis
        else:
            return None

    def update_last_pinned_timestamp(self, channel_id: int, timestamp: typing.Optional[datetime.datetime]) -> None:
        # We don't persist this information, as it is not overly useful. The user can use the HTTP endpoint if they
        # care what the pins are...
        pass

    def update_member(
        self, guild_id: int, role_ids: typing.List[int], nick: typing.Optional[str], user_id: int
    ) -> typing.Optional[typing.Tuple[user.Member, user.Member]]:
        guild_obj = self.get_guild_by_id(guild_id)

        if guild is not None and user_id in guild_obj.members:
            new_member = guild_obj.members[user_id]
            old_member = new_member.clone()
            new_member.update_state(role_ids, nick)
            return old_member, new_member
        else:
            return None

    def update_member_presence(
        self, guild_id: int, user_id: int, presence_payload: types.DiscordObject
    ) -> typing.Optional[typing.Tuple[user.Member, presence.Presence, presence.Presence]]:
        guild_obj = self.get_guild_by_id(guild_id)

        if guild is not None and user_id in guild_obj.members:
            member_obj = guild_obj.members[user_id]
            old_presence = member_obj.presence
            new_presence = self.parse_presence(guild_id, user_id, presence_payload)
            return member_obj, old_presence, new_presence
        else:
            return None
