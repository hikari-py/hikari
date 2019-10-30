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

import contextlib
import datetime
import typing
import weakref

from hikari.core.internal import state_registry
from hikari.core.models import channels
from hikari.core.models import emojis
from hikari.core.models import guilds
from hikari.core.models import messages
from hikari.core.models import presences
from hikari.core.models import reactions
from hikari.core.models import roles
from hikari.core.models import users
from hikari.core.models import webhooks
from hikari.core.utils import custom_types
from hikari.core.utils import logging_utils
from hikari.core.utils import transform


class StateRegistryImpl(state_registry.StateRegistry):
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
    implementation from :class:`hikari.core.internal.state_registry.StateRegistry` and implement each
    method as a coroutine function. You will also need to update the models that access the cache, and the event
    adapter that calls this cache, appropriately.
    """

    __slots__ = ("_dm_channels", "_emojis", "_guilds", "_guild_channels", "_message_cache", "_users", "_user", "logger")

    def __init__(self, message_cache_size: int, user_dm_channel_size: int) -> None:
        # Users may be cached while we can see them, or they may be cached as a member. Regardless, we only
        # retain them while they are referenced from elsewhere to keep things tidy.
        self._dm_channels: typing.MutableMapping[int, channels.DMChannel] = custom_types.LRUDict(user_dm_channel_size)
        self._emojis: typing.MutableMapping[int, emojis.GuildEmoji] = weakref.WeakValueDictionary()
        self._guilds: typing.Dict[int, guilds.Guild] = {}
        self._guild_channels: typing.MutableMapping[int, channels.GuildChannel] = weakref.WeakValueDictionary()
        self._users: typing.MutableMapping[int, users.User] = weakref.WeakValueDictionary()
        self._message_cache: typing.MutableMapping[int, messages.Message] = custom_types.LRUDict(message_cache_size)

        #: The bot user.
        self._user: typing.Optional[users.BotUser] = None

        #: Our logger.
        self.logger = logging_utils.get_named_logger(self)

    @property
    def me(self) -> users.BotUser:
        return self._user

    @property
    def message_cache(self) -> typing.MutableMapping[int, messages.Message]:
        return self._message_cache

    def add_reaction(self, message_obj: messages.Message, emoji_obj: emojis.Emoji) -> reactions.Reaction:
        # Ensure the reaction is subscribed on the message.
        for reaction_obj in message_obj.reactions:
            if reaction_obj.emoji == emoji_obj:
                # Increment the count.
                reaction_obj.count += 1
                return reaction_obj
        else:
            reaction_obj = reactions.Reaction(1, emoji_obj, message_obj)
            message_obj.reactions.append(reaction_obj)
            return reaction_obj

    def delete_channel(self, channel_obj: channels.Channel) -> None:
        channel_id = channel_obj.id
        if channel_id in self._guild_channels:
            channel_obj: channels.GuildChannel
            guild_obj = channel_obj.guild
            del guild_obj.channels[channel_id]
            del self._guild_channels[channel_id]
        elif channel_id in self._dm_channels:
            channel_obj: channels.DMChannel
            del self._dm_channels[channel_id]

    def delete_emoji(self, emoji_obj: emojis.GuildEmoji) -> None:
        with contextlib.suppress(KeyError):
            del self._emojis[emoji_obj.id]

        guild_obj = emoji_obj.guild

        with contextlib.suppress(KeyError):
            del guild_obj.emojis[emoji_obj.id]

    def delete_guild(self, guild_obj: guilds.Guild) -> None:
        with contextlib.suppress(KeyError):
            del self._guilds[guild_obj.id]

    def delete_message(self, message_obj: messages.Message) -> None:
        with contextlib.suppress(KeyError):
            message_obj = self._message_cache[message_obj.id]
            del self._message_cache[message_obj.id]

    def delete_member(self, member_obj: users.Member) -> None:
        with contextlib.suppress(KeyError):
            del member_obj.guild.members[member_obj.id]

    def delete_reaction(self, message_obj: messages.Message, user_obj: users.User, emoji_obj: emojis.Emoji) -> None:
        # We do not store info about the user, so just ignore that parameter.
        for reaction_obj in message_obj.reactions:
            if reaction_obj.emoji == emoji_obj and reaction_obj.message.id == reaction_obj.message.id:
                message_obj.reactions.remove(reaction_obj)
                # This emoji will only be referenced once, so shortcut to save time.
                break

    # noinspection PyProtectedMember
    def delete_role(self, role_obj: roles.Role) -> None:
        guild_obj = role_obj.guild
        with contextlib.suppress(KeyError):
            del guild_obj.roles[role_obj.id]

            for member in guild_obj.members.values():
                # TODO: make member role references weak, perhaps?
                # Would require me to store the actual roles rather than the IDs though...

                # Protected member access, but much more efficient for this case than resolving every role repeatedly.
                if role_obj.id in member._role_ids:
                    member._role_ids.remove(role_obj.id)

    def get_channel_by_id(self, channel_id: int) -> typing.Optional[channels.Channel]:
        return self._guild_channels.get(channel_id) or self._dm_channels.get(channel_id)

    def get_emoji_by_id(self, emoji_id: int) -> typing.Optional[emojis.GuildEmoji]:
        return self._emojis.get(emoji_id)

    def get_guild_by_id(self, guild_id: int) -> typing.Optional[guilds.Guild]:
        return self._guilds.get(guild_id)

    def get_member_by_id(self, user_id: int, guild_id: int) -> typing.Optional[users.Member]:
        if guild_id not in self._guilds:
            return None
        return self._guilds[guild_id].members.get(user_id)

    def get_message_by_id(self, message_id: int) -> typing.Optional[messages.Message]:
        return self._message_cache.get(message_id)

    def get_role_by_id(self, guild_id: int, role_id: int) -> typing.Optional[roles.Role]:
        if guild_id not in self._guilds:
            return None
        return self._guilds[guild_id].roles.get(role_id)

    def get_user_by_id(self, user_id: int) -> typing.Optional[users.User]:
        if self._user is not None and self._user.id == user_id:
            return self._user

        return self._users.get(user_id)

    def parse_bot_user(self, bot_user_payload: custom_types.DiscordObject) -> users.BotUser:
        bot_user_payload = users.BotUser(self, bot_user_payload)
        self._user = bot_user_payload
        return bot_user_payload

    def parse_channel(
        self, channel_payload: custom_types.DiscordObject, guild_id: typing.Optional[int]
    ) -> channels.Channel:
        channel_id = int(channel_payload["id"])
        channel_obj = self.get_channel_by_id(channel_id)

        if guild_id is not None:
            channel_obj["guild_id"] = guild_id

        if channel_obj is not None:
            channel_obj.update_state(channel_payload)
        else:
            channel_obj = channels.channel_from_dict(self, channel_payload)
            if channels.is_channel_type_dm(channel_payload["type"]):
                self._dm_channels[channel_id] = channel_obj
            else:
                self._guild_channels[channel_id] = channel_obj
                channel_obj.guild.channels[channel_id] = channel_obj

        return channel_obj

    # These fix typing issues in the update_guild_emojis method.
    @typing.overload
    def parse_emoji(self, emoji_payload: custom_types.DiscordObject, guild_id: int) -> emojis.GuildEmoji:
        ...

    @typing.overload
    def parse_emoji(self, emoji_payload: custom_types.DiscordObject, guild_id: None) -> emojis.Emoji:
        ...

    def parse_emoji(self, emoji_payload, guild_id):
        existing_emoji = None
        emoji_id = int(emoji_payload["id"])

        if emoji_id is not None:
            existing_emoji = self.get_emoji_by_id(emoji_id)

        if existing_emoji is not None:
            existing_emoji.update_state(emoji_payload)
            return existing_emoji

        new_emoji = emojis.emoji_from_dict(self, emoji_payload, guild_id)
        if isinstance(new_emoji, emojis.GuildEmoji):
            guild_obj = self.get_guild_by_id(guild_id)
            if guild_obj is not None:
                guild_obj.emojis[new_emoji.id] = new_emoji

        return new_emoji

    def parse_guild(self, guild_payload: custom_types.DiscordObject):
        guild_id = int(guild_payload["id"])
        unavailable = guild_payload.get("unavailable", False)

        # Always try to update an existing guild first.
        guild_obj = self.get_guild_by_id(guild_id)

        if guild_id in self._guilds:
            if unavailable:
                self.set_guild_unavailability(guild_id, True)
            else:
                guild_obj.update_state(guild_payload)
        else:
            guild_obj = guilds.Guild(self, guild_payload)
            self._guilds[guild_id] = guild_obj

        return guild_obj

    def parse_member(self, member_payload: custom_types.DiscordObject, guild_obj: guilds.Guild):
        member_id = int(member_payload["user"]["id"])

        if member_id in guild_obj.members:
            member_obj = guild_obj.members[member_id]
            nick = member_payload.get("nick")
            role_ids = [int(role_id) for role_id in member_payload.get("roles")]
            member_obj.update_state(role_ids, nick)
            return member_obj

        member_obj = users.Member(self, guild_obj.id, member_payload)

        guild_obj.members[member_id] = member_obj
        return member_obj

    def parse_message(self, message_payload: custom_types.DiscordObject):
        # Always update the cache with the new message.
        message_id = int(message_payload["id"])
        message_obj = messages.Message(self, message_payload)

        channel_obj = message_obj.channel
        if channel_obj is not None:
            message_obj.channel.last_message_id = message_id

            self._message_cache[message_id] = message_obj
            return message_obj
        return None

    def parse_presence(self, member_obj: users.Member, presence_payload: custom_types.DiscordObject):
        presence_obj = presences.Presence(presence_payload)
        member_obj.presence = presence_obj
        return presence_obj

    def parse_reaction(self, reaction_payload: custom_types.DiscordObject):
        message_id = int(reaction_payload["message_id"])
        message_obj = self.get_message_by_id(message_id)
        count = int(reaction_payload["count"])
        emoji_obj = self.parse_emoji(reaction_payload["emoji"], None)

        if message_obj is not None:
            # We might not add this, this is simpler than duplicating code to reparse this payload in two places,
            # though, so we parse it first anyway and then either ditch or store it depending on whether the reaction
            # already exists or not.
            new_reaction_obj = reactions.Reaction(count, emoji_obj, message_obj)

            for existing_reaction_obj in message_obj.reactions:
                if existing_reaction_obj.emoji == new_reaction_obj.emoji:
                    existing_reaction_obj.count = new_reaction_obj.count
                    return existing_reaction_obj
            else:
                message_obj.reactions.append(new_reaction_obj)
                return new_reaction_obj
        else:
            # No message was cached, so just ignore it.
            pass

    def parse_role(self, role_payload: custom_types.DiscordObject, guild_id: int):
        if guild_id in self._guilds:
            guild_obj = self._guilds[guild_id]
            role_payload = roles.Role(self, role_payload, guild_id)
            guild_obj.roles[role_payload.id] = role_payload
            return role_payload
        return None

    def parse_user(self, user_payload: custom_types.DiscordObject):
        # If the user already exists, then just return their existing object. We expect discord to tell us if they
        # get updated if they are a member, and for anything else the object will just be disposed of once we are
        # finished with it anyway.
        user_id = int(user_payload["id"])

        if self._user and user_id == self._user.id or "mfa_enabled" in user_payload or "verified" in user_payload:
            return self.parse_bot_user(user_payload)

        user_obj = self.get_user_by_id(user_id)

        if user_obj is None:
            user_obj = users.User(self, user_payload)
            self._users[user_id] = user_obj
            return user_obj

        existing_user = self._users[user_id]
        existing_user.update_state(user_payload)

        return existing_user

    def parse_webhook(self, webhook_payload: custom_types.DiscordObject):
        return webhooks.Webhook(self, webhook_payload)

    def remove_all_reactions(self, message_obj: messages.Message) -> None:
        for reaction_obj in message_obj.reactions:
            reaction_obj.count = 0

        message_obj.reactions.clear()

    def remove_reaction(self, message_obj: messages.Message, emoji_obj: emojis.Emoji) -> reactions.Reaction:
        for reaction_obj in message_obj.reactions:
            if reaction_obj.emoji == emoji_obj:
                reaction_obj.count -= 1
                if reaction_obj.count <= 0:
                    reaction_obj.count = 0
                    message_obj.reactions.remove(reaction_obj)
                return reaction_obj
        else:
            return reactions.Reaction(0, emoji_obj, message_obj)

    def set_guild_unavailability(self, guild_id: int, unavailability: bool) -> None:
        guild_obj = self.get_guild_by_id(guild_id)
        if guild_obj is not None:
            guild_obj.unavailable = unavailability

    def set_last_pinned_timestamp(self, channel_id: int, timestamp: typing.Optional[datetime.datetime]) -> None:
        # We don't persist this information, as it is not overly useful. The user can use the HTTP endpoint if they
        # care what the pins are...
        pass

    def set_roles_for_member(self, role_objs: typing.Sequence[roles.Role], member_obj: users.Member) -> None:
        member_obj._role_ids = role_objs

    def update_channel(
        self, channel_payload: custom_types.DiscordObject
    ) -> typing.Optional[typing.Tuple[channels.Channel, channels.Channel]]:
        channel_id = int(channel_payload["id"])
        existing_channel = self.get_channel_by_id(channel_id)
        if existing_channel is not None:
            old_channel = existing_channel.copy()
            new_channel = existing_channel
            new_channel.update_state(channel_payload)
            return old_channel, new_channel
        return None

    def update_guild(
        self, guild_payload: custom_types.DiscordObject
    ) -> typing.Optional[typing.Tuple[guilds.Guild, guilds.Guild]]:
        guild_id = int(guild_payload["id"])
        guild_obj = self.get_guild_by_id(guild_id)
        if guild_obj is not None:
            previous_guild = guild_obj.copy()
            new_guild = guild_obj
            new_guild.update_state(guild_payload)
            return previous_guild, new_guild
        return None

    def update_guild_emojis(
        self, emoji_list: typing.List[custom_types.DiscordObject], guild_id: int
    ) -> typing.Optional[typing.Tuple[typing.FrozenSet[emojis.GuildEmoji], typing.FrozenSet[emojis.GuildEmoji]]]:
        guild_obj = self.get_guild_by_id(guild_id)
        if guild_obj is not None:
            old_emojis = frozenset(guild_obj.emojis.values())
            new_emojis = frozenset(self.parse_emoji(emoji_obj, guild_id) for emoji_obj in emoji_list)
            guild_obj.emojis = transform.id_map(new_emojis)
            return old_emojis, new_emojis
        return None

    def update_member(
        self, guild_id: int, role_ids: typing.List[int], nick: typing.Optional[str], user_id: int
    ) -> typing.Optional[typing.Tuple[users.Member, users.Member]]:
        guild_obj = self.get_guild_by_id(guild_id)

        if guild_obj is not None and user_id in guild_obj.members:
            new_member = guild_obj.members[user_id]
            old_member = new_member.copy()
            new_member.update_state(role_ids, nick)
            return old_member, new_member
        return None

    def update_member_presence(
        self, guild_id: int, user_id: int, presence_payload: custom_types.DiscordObject
    ) -> typing.Optional[typing.Tuple[users.Member, presences.Presence, presences.Presence]]:
        guild_obj = self.get_guild_by_id(guild_id)

        if guild_obj is not None and user_id in guild_obj.members:
            member_obj = guild_obj.members[user_id]
            old_presence = member_obj.presence
            new_presence = self.parse_presence(member_obj, presence_payload)
            return member_obj, old_presence, new_presence
        return None

    def update_message(
        self, payload: custom_types.DiscordObject
    ) -> typing.Optional[typing.Tuple[messages.Message, messages.Message]]:
        message_id = int(payload["message_id"])
        existing_message = self._message_cache.get(message_id)
        if existing_message is not None:
            old_message = existing_message.copy()
            new_message = existing_message
            new_message.update_state(payload)
            return old_message, new_message
        return None

    def update_role(
        self, guild_id: int, payload: custom_types.DiscordObject
    ) -> typing.Optional[typing.Tuple[roles.Role, roles.Role]]:
        role_id = int(payload["id"])
        existing_role = self.get_role_by_id(guild_id, role_id)

        if existing_role is not None:
            old_role = existing_role.copy()
            new_role = existing_role
            new_role.update_state(payload)
            return old_role, new_role
        return None

    def __copy__(self):
        """
        We don't allow ourselves to be copied, as this would lead to inconsistent state when the models get
        cloned. Instead, we just return our own reference.

        This is a hack, I should probably remove this and find a different way to implement this eventually.
        """
        return self
