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
import collections
import weakref

from hikari.core.model import guild as _guild
from hikari.core.model import message as _message
from hikari.core.model import channel as _channel
from hikari.core.model import role as _role
from hikari.core.model import user as _user
from hikari.core.model import model_state
from hikari.core.utils import assertions
from hikari.core.utils import transform
from hikari.core.utils import types


class LRUDict(collections.MutableMapping):
    """
    A dict that stores a maximum number of items before the oldest is purged.

    Warning:
        This will not function correctly on non-CPython implementations of Python3.6, and any implementation of
        Python3.5 or older, as it makes the assumption that all dictionaries are ordered by default.
    """
    __slots__ = ("_lru_size", "_data")

    def __init__(self, lru_size: int, dict_factory=dict) -> None:
        assertions.assert_natural(lru_size)
        self._data = dict_factory()
        self._lru_size = lru_size

    def __getitem__(self, item):
        return self._data[item]

    def __setitem__(self, key, value):
        while len(self._data) >= self._lru_size:
            self._data.popitem()
        self._data[key] = value

    def __delitem__(self, key):
        del self._data[key]

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        yield from self._data


class Cache(model_state.AbstractModelState):
    """
    Implementation of :class:`model_state.AbstractModelState` which implements the caching logic needed for a shard.

    This is expected to be further extended elsewhere to provide the ability to handle incoming gateway payloads.

    The class itself is designed to be easily overridable should one wish to provide their own implementations.
    """
    def __init__(
        self,
        message_cache_size: int = 100,
        user_dm_channel_size: int = 100,
    ) -> None:
        # Users may be cached while we can see them, or they may be cached as a member. Regardless, we only
        # retain them while they are referenced from elsewhere to keep things tidy.
        self._users = weakref.WeakValueDictionary()
        self._guilds = {}
        self._dm_channels = LRUDict(user_dm_channel_size)
        self._messages = LRUDict(message_cache_size)
        # These members may only be referred to in the guild they are from, after that they are disposed of.
        self._members = weakref.WeakValueDictionary()

    def get_user_by_id(self, user_id: int):
        return self._users.get(user_id)

    def get_guild_by_id(self, guild_id: int):
        return self._guilds.get(guild_id)

    def get_message_by_id(self, message_id: int):
        return self._messages.get(message_id)

    def parse_user(self, user: types.DiscordObject):
        # If the user already exists, then just return their existing object. We expect discord to tell us if they
        # get updated if they are a member, and for anything else the object will just be disposed of once we are
        # finished with it anyway.
        user_id = transform.get_cast(user, 'id', int)
        if user_id not in self._users:
            self._users[user_id] = _user.User.from_dict(self, user)
        return self._users[user_id]

    def parse_guild(self, guild: types.DiscordObject):
        guild_id = transform.get_cast(guild, 'id', int)
        if guild_id not in self._guilds:
            self._guilds[guild_id] = _guild.Guild.from_dict(self, guild)
        return self._guilds[guild_id]

    def parse_member(self, member: types.DiscordObject, guild_id: int):
        user_id = transform.get_cast(member.get("user"), 'id', int)
        if user_id not in self._members:
            self._members[user_id] = _user.Member.from_dict(self, guild_id, member)
        return self._members[user_id]

    def parse_role(self, role: types.DiscordObject):
        # Don't cache roles here.
        return _role.Role.from_dict(role)

    def parse_emoji(self, emoji: types.DiscordObject):
        # TODO: cache emoji
        # TODO: parse emoji
        return NotImplemented

    def parse_message(self, message: types.DiscordObject):
        message_id = transform.get_cast(message, 'id', int)
        message_obj = _message.Message.from_dict(self, message)
        self._messages[message_id] = message_obj
        return message_obj

    def parse_channel(self, channel: types.DiscordObject):
        channel = _channel.channel_from_dict(self, channel)
        if channel.is_dm:
            self._dm_channels[channel.id] = channel
        return channel

    def parse_webhook(self, webhook: types.DiscordObject):
        # Don't cache webhooks here.
        # TODO: parse webhook
        return NotImplemented
