#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekokatt 2019-2020
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
import functools
import typing
import weakref

from hikari.internal_utilities import containers
from hikari.internal_utilities import loggers
from hikari.internal_utilities import transformations
from hikari.orm import fabric
from hikari.orm import state_registry
from hikari.orm.models import applications
from hikari.orm.models import audit_logs
from hikari.orm.models import channels
from hikari.orm.models import connections
from hikari.orm.models import emojis
from hikari.orm.models import gateway_bot
from hikari.orm.models import guilds
from hikari.orm.models import interfaces
from hikari.orm.models import invites
from hikari.orm.models import members
from hikari.orm.models import messages
from hikari.orm.models import presences
from hikari.orm.models import reactions
from hikari.orm.models import roles
from hikari.orm.models import users
from hikari.orm.models import voices
from hikari.orm.models import webhooks


class StateRegistryImpl(state_registry.IStateRegistry):
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
    implementation from :class:`hikari.state_registry.StateRegistry` and implement each
    method as a coroutine function. You will also need to update the models that access the cache, and the event
    adapter that calls this cache, appropriately.
    """

    __slots__ = (
        "fabric",
        "_dm_channels",
        "_emojis",
        "_guilds",
        "_guild_channels",
        "_message_cache",
        "_users",
        "_user",
        "logger",
    )

    def __init__(self, fabric_obj: fabric.Fabric, message_cache_size: int, user_dm_channel_size: int) -> None:
        # Users may be cached while we can see them, or they may be cached as a member. Regardless, we only
        # retain them while they are referenced from elsewhere to keep things tidy.
        self.fabric = fabric_obj
        self._dm_channels: typing.MutableMapping[int, channels.DMChannel] = containers.LRUDict(user_dm_channel_size)
        self._emojis: typing.MutableMapping[int, emojis.GuildEmoji] = weakref.WeakValueDictionary()
        self._guilds: typing.Dict[int, guilds.Guild] = {}
        self._guild_channels: typing.MutableMapping[int, channels.GuildChannel] = weakref.WeakValueDictionary()
        self._users: typing.MutableMapping[int, users.User] = weakref.WeakValueDictionary()
        self._message_cache: typing.MutableMapping[int, messages.Message] = containers.LRUDict(message_cache_size)

        #: The bot user.
        self._user: typing.Optional[users.OAuth2User] = None

        #: Our logger.
        self.logger = loggers.get_named_logger(self)

    def _prepare_unknown_with_callback(self, id, resolver, callback, *resolver_args, **resolver_kwargs):
        obj = interfaces.UnknownObject(id, functools.partial(resolver, *resolver_args, **resolver_kwargs))
        callback is not None and obj.add_done_callback(callback)
        return obj

    @property
    def me(self) -> typing.Optional[users.OAuth2User]:
        return self._user

    @property
    def message_cache(self) -> typing.MutableMapping[int, messages.Message]:
        return self._message_cache

    def increment_reaction_count(self, message_obj: messages.Message, emoji_obj: emojis.Emoji) -> reactions.Reaction:
        # Ensure the reaction is subscribed on the message.
        for reaction_obj in message_obj.reactions:
            if reaction_obj.emoji == emoji_obj:
                # Increment the count.
                reaction_obj.count += 1
                return reaction_obj

        reaction_obj = reactions.Reaction(1, emoji_obj, message_obj)
        message_obj.reactions.append(reaction_obj)
        return reaction_obj

    def decrement_reaction_count(
        self, message_obj: messages.Message, emoji_obj: emojis.Emoji
    ) -> typing.Optional[reactions.Reaction]:
        # Ensure the reaction is subscribed on the message.
        for reaction_obj in message_obj.reactions:
            if reaction_obj.emoji == emoji_obj:
                # Decrement the count.
                reaction_obj.count -= 1

                # If the count is zero, remove it from the message
                if reaction_obj.count == 0:
                    message_obj.reactions.remove(reaction_obj)

                return reaction_obj

        return None

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

    def delete_member(self, member_obj: members.Member) -> None:
        with contextlib.suppress(KeyError):
            del member_obj.guild.members[member_obj.id]

    def delete_reaction(self, message_obj: messages.Message, user_obj: users.User, emoji_obj: emojis.Emoji) -> None:
        # We do not store info about the user, so just ignore that parameter.
        for reaction_obj in message_obj.reactions:
            if reaction_obj.emoji == emoji_obj and reaction_obj.message.id == reaction_obj.message.id:
                message_obj.reactions.remove(reaction_obj)
                # Set this to zero so that if a reference to this object exists elsewhere, it reflects that it has
                # been removed from the message.
                reaction_obj.count = 0
                # This emoji will only be referenced once, so shortcut to save time.
                break

    def delete_all_reactions(self, message_obj: messages.Message) -> None:
        # If the user had any reference to the objects, we should ensure that is now zero to show the reaction
        # is no longer alive.
        for reaction_obj in message_obj.reactions:
            reaction_obj.count = 0

        message_obj.reactions.clear()

    # noinspection PyProtectedMember
    def delete_role(self, role_obj: roles.Role) -> None:
        guild_id = role_obj.guild_id
        with contextlib.suppress(KeyError):
            guild_obj = self._guilds[guild_id]

            del guild_obj.roles[role_obj.id]

            for member in guild_obj.members.values():
                # TODO: make member role references weak, perhaps?
                # Would require me to store the actual roles rather than the IDs though...

                # Protected member access, but much more efficient for this case than resolving every role repeatedly.
                if role_obj in member.roles:
                    member.roles.remove(role_obj)

    def get_channel_by_id(self, channel_id: int) -> typing.Optional[channels.Channel]:
        return self._guild_channels.get(channel_id) or self._dm_channels.get(channel_id)

    def get_mandatory_channel_by_id(  # lgtm [py/similar-function]
        self,
        channel_id: int,
        callback_if_unresolved: typing.Optional[typing.Callable[[channels.Channel], typing.Any]] = None,
    ) -> typing.Union[channels.Channel, interfaces.UnknownObject[channels.Channel]]:
        obj = self.get_channel_by_id(channel_id)
        if obj is not None:
            return obj
        else:
            return self._prepare_unknown_with_callback(
                channel_id, self.fabric.http_adapter.fetch_channel, callback_if_unresolved, channel_id
            )

    def get_guild_emoji_by_id(self, emoji_id: int) -> typing.Optional[emojis.GuildEmoji]:
        return self._emojis.get(emoji_id)

    def get_mandatory_guild_emoji_by_id(  # lgtm [py/similar-function]
        self,
        emoji_id: int,
        guild_id: int,
        callback_if_unresolved: typing.Optional[typing.Callable[[emojis.GuildEmoji], typing.Any]] = None,
    ) -> typing.Union[emojis.GuildEmoji, interfaces.UnknownObject[emojis.GuildEmoji]]:
        obj = self.get_guild_emoji_by_id(emoji_id)
        if obj is not None:
            return obj
        else:
            return self._prepare_unknown_with_callback(
                emoji_id, self.fabric.http_adapter.fetch_guild_emoji, callback_if_unresolved, emoji_id, guild_id
            )

    def get_guild_by_id(self, guild_id: int) -> typing.Optional[guilds.Guild]:
        return self._guilds.get(guild_id)

    def get_mandatory_guild_by_id(  # lgtm [py/similar-function]
        self, guild_id: int, callback_if_unresolved: typing.Optional[typing.Callable[[guilds.Guild], typing.Any]] = None
    ) -> typing.Union[guilds.Guild, interfaces.UnknownObject[guilds.Guild]]:
        obj = self.get_guild_by_id(guild_id)
        if obj is not None:
            return obj
        else:
            return self._prepare_unknown_with_callback(
                guild_id, self.fabric.http_adapter.fetch_guild, callback_if_unresolved, guild_id
            )

    def get_message_by_id(self, message_id: int) -> typing.Optional[messages.Message]:
        return self._message_cache.get(message_id)

    def get_mandatory_message_by_id(  # lgtm [py/similar-function]
        self,
        message_id: int,
        channel_id: int,
        callback_if_unresolved: typing.Optional[typing.Callable[[messages.Message], typing.Any]] = None,
    ) -> typing.Union[messages.Message, interfaces.UnknownObject[messages.Message]]:
        obj = self.get_message_by_id(message_id)
        if obj is not None:
            return obj
        else:
            return self._prepare_unknown_with_callback(
                message_id, self.fabric.http_adapter.fetch_message, callback_if_unresolved, channel_id, message_id
            )

    def get_role_by_id(self, guild_id: int, role_id: int) -> typing.Optional[roles.Role]:
        if guild_id not in self._guilds:
            return None
        return self._guilds[guild_id].roles.get(role_id)

    async def _role_fetcher(self, guild_id, role_id):
        # This isn't a standard endpoint, we have to search for it...
        roles = await self.fabric.http_adapter.fetch_roles(guild_id)
        for role in roles:
            if role.id == role_id:
                return role
        raise ValueError(f"No role could be found for ID {role_id} in guild {guild_id}")

    def get_mandatory_role_by_id(  # lgtm [py/similar-function]
        self,
        guild_id: int,
        role_id: int,
        callback_if_unresolved: typing.Optional[typing.Callable[[roles.Role], typing.Any]] = None,
    ) -> typing.Union[roles.Role, interfaces.UnknownObject[roles.Role]]:
        obj = self.get_role_by_id(guild_id, role_id)
        if obj is not None:
            return obj
        else:
            return self._prepare_unknown_with_callback(
                role_id, self._role_fetcher, callback_if_unresolved, guild_id, role_id
            )

    def get_user_by_id(self, user_id: int) -> typing.Optional[users.User]:
        if self._user is not None and self._user.id == user_id:
            return self._user

        return self._users.get(user_id)

    def get_mandatory_user_by_id(  # lgtm [py/similar-function]
        self, user_id: int, callback_if_unresolved: typing.Optional[typing.Callable[[users.User], typing.Any]] = None
    ) -> typing.Union[users.User, interfaces.UnknownObject[users.User]]:
        obj = self.get_user_by_id(user_id)
        if obj is not None:
            return obj
        else:
            return self._prepare_unknown_with_callback(
                user_id, self.fabric.http_adapter.fetch_user, callback_if_unresolved, user_id
            )

    def get_member_by_id(self, user_id: int, guild_id: int) -> typing.Optional[members.Member]:
        if guild_id not in self._guilds:
            return None
        return self._guilds[guild_id].members.get(user_id)

    def get_mandatory_member_by_id(  # lgtm [py/similar-function]
        self,
        user_id: int,
        guild_id: int,
        callback_if_unresolved: typing.Optional[typing.Callable[[members.Member], typing.Any]] = None,
    ) -> typing.Union[members.MemberLikeT, interfaces.UnknownObject[members.Member]]:
        obj = self.get_member_by_id(user_id, guild_id)
        if obj is not None:
            return obj
        else:
            return self._prepare_unknown_with_callback(
                user_id, self.fabric.http_adapter.fetch_member, callback_if_unresolved, user_id, guild_id
            )

    def parse_application(self, application_payload: containers.DiscordObjectT) -> applications.Application:
        return applications.Application(self.fabric, application_payload)

    def parse_application_user(self, application_user_payload: containers.DiscordObjectT) -> users.OAuth2User:
        if self._user is not None:
            self._user.update_state(application_user_payload)
        else:
            self._user = users.OAuth2User(self.fabric, application_user_payload)

        return self._user

    def parse_audit_log(self, audit_log_payload: containers.DiscordObjectT) -> audit_logs.AuditLog:
        return audit_logs.AuditLog(self.fabric, audit_log_payload)

    def parse_channel(
        self, channel_payload: containers.DiscordObjectT, guild_obj: typing.Optional[guilds.Guild] = None
    ) -> channels.Channel:
        channel_id = int(channel_payload["id"])
        channel_obj = self.get_channel_by_id(channel_id)

        if guild_obj is not None:
            channel_payload["guild_id"] = guild_obj.id

        if channel_obj is not None:
            channel_obj.update_state(channel_payload)
        else:
            channel_obj = channels.parse_channel(self.fabric, channel_payload)
            if channels.is_channel_type_dm(channel_payload["type"]):
                self._dm_channels[channel_id] = channel_obj
            else:
                self._guild_channels[channel_id] = channel_obj
                channel_obj.guild.channels[channel_id] = channel_obj

        return channel_obj

    def parse_connection(self, connection_payload: containers.DiscordObjectT) -> connections.Connection:
        return connections.Connection(self.fabric, connection_payload)

    # These fix typing issues in the update_guild_emojis method.
    @typing.overload
    def parse_emoji(self, emoji_payload: containers.DiscordObjectT, guild_obj: guilds.Guild) -> emojis.GuildEmoji:
        ...

    @typing.overload
    def parse_emoji(self, emoji_payload: containers.DiscordObjectT, guild_obj: None) -> emojis.Emoji:
        ...

    def parse_emoji(self, emoji_payload, guild_obj):
        existing_emoji = None
        # While it is true the API docs state that we always get an ID back, I don't trust discord wont break this
        # in the future, so I am playing it safe.
        emoji_id = transformations.nullable_cast(emoji_payload.get("id"), int)

        if emoji_id is not None:
            existing_emoji = self.get_guild_emoji_by_id(emoji_id)

        if existing_emoji is not None:
            existing_emoji.update_state(emoji_payload)
            return existing_emoji

        new_emoji = emojis.parse_emoji(self.fabric, emoji_payload, guild_obj.id if guild_obj is not None else None)
        if isinstance(new_emoji, emojis.GuildEmoji):
            guild_obj = self.get_mandatory_guild_by_id(guild_obj.id)
            guild_obj.emojis[new_emoji.id] = new_emoji
            self._emojis[new_emoji.id] = new_emoji

        return new_emoji

    def parse_gateway_bot(self, gateway_bot_payload: containers.DiscordObjectT) -> gateway_bot.GatewayBot:
        return gateway_bot.GatewayBot(gateway_bot_payload)

    def parse_guild(self, guild_payload: containers.DiscordObjectT, shard_id: typing.Optional[int]) -> guilds.Guild:
        guild_id = int(guild_payload["id"])
        is_unavailable = guild_payload.get("unavailable", False)

        if guild_id in self._guilds:
            # Always try to update an existing guild first.
            guild_obj = self.get_guild_by_id(guild_id)

            if is_unavailable:
                self.set_guild_unavailability(guild_obj, True)
            else:
                guild_obj.update_state(guild_payload)
        else:
            guild_obj = guilds.Guild(self.fabric, guild_payload, shard_id)
            self._guilds[guild_id] = guild_obj

        return guild_obj

    def parse_invite(self, invite_payload: containers.DiscordObjectT) -> invites.Invite:
        return invites.parse_invite(self.fabric, invite_payload)

    def parse_voice_state(
        self, voice_state_payload: containers.DiscordObjectT, guild_obj: guilds.Guild
    ) -> voices.VoiceState:
        user_id = int(voice_state_payload["user_id"])

        if user_id in guild_obj.voice_states:
            voice_state_obj = guild_obj.voice_states[user_id]
            voice_state_obj.update_state(voice_state_payload)
            return voice_state_obj

        voice_state_obj = voices.VoiceState(self.fabric, guild_obj, voice_state_payload)
        guild_obj.voice_states[user_id] = voice_state_obj
        return voice_state_obj

    def parse_partial_member(
        self,
        partial_member_payload: containers.DiscordObjectT,
        user_payload: containers.DiscordObjectT,
        guild_obj: guilds.Guild,
    ) -> members.Member:
        # Cheap workaround for Discord's inconsistency here.
        partial_member_payload["user"] = user_payload
        return self.parse_member(partial_member_payload, guild_obj)

    def parse_member(self, member_payload: containers.DiscordObjectT, guild_obj: guilds.Guild) -> members.Member:
        member_id = int(member_payload["user"]["id"])

        if member_id in guild_obj.members:
            member_obj = guild_obj.members[member_id]
            role_objs = [
                self.get_mandatory_role_by_id(guild_obj.id, int(role_id)) for role_id in member_payload["roles"]
            ]
            member_obj.update_state(role_objs, member_payload)
            return member_obj

        member_obj = members.Member(self.fabric, guild_obj, member_payload)

        guild_obj.members[member_id] = member_obj
        return member_obj

    def parse_message(self, message_payload: containers.DiscordObjectT) -> messages.Message:
        # Always update the cache with the new message.
        message_id = int(message_payload["id"])

        message_obj = messages.Message(self.fabric, message_payload)
        message_obj.channel.last_message_id = message_id

        self._message_cache[message_id] = message_obj
        return message_obj

    def parse_presence(
        self, member_obj: members.Member, presence_payload: containers.DiscordObjectT
    ) -> presences.Presence:
        presence_obj = presences.Presence(presence_payload)
        member_obj.presence = presence_obj
        return presence_obj

    def parse_reaction(self, reaction_payload: containers.DiscordObjectT) -> reactions.Reaction:
        message_id = int(reaction_payload["message_id"])
        count = int(reaction_payload["count"])
        emoji_obj = self.parse_emoji(reaction_payload["emoji"], None)

        # I hope this message won't ever be unresolved, honestly. Because I have no nice way of getting the info I need
        # to fabricate this damn API call. Thanks Discord.
        message_obj = self.get_message_by_id(message_id)
        new_reaction_obj = reactions.Reaction(count, emoji_obj, message_obj or interfaces.UnknownObject(message_id))

        if message_obj:
            # Prevent attribute-erroring if the message was not cached...
            for existing_reaction_obj in message_obj.reactions:
                if existing_reaction_obj.emoji == new_reaction_obj.emoji:
                    existing_reaction_obj.count = new_reaction_obj.count
                    return existing_reaction_obj

            message_obj.reactions.append(new_reaction_obj)
        return new_reaction_obj

    def parse_role(self, role_payload: containers.DiscordObjectT, guild_obj: guilds.Guild) -> roles.Role:
        role_id = int(role_payload["id"])
        if role_id in guild_obj.roles:
            role = guild_obj.roles[role_id]
            role.update_state(role_payload)
            return role
        else:
            role_payload = roles.Role(self.fabric, role_payload, guild_obj.id)
            guild_obj.roles[role_payload.id] = role_payload
            return role_payload

    def parse_user(self, user_payload: containers.DiscordObjectT) -> users.IUser:
        # If the user already exists, then just return their existing object. We expect discord to tell us if they
        # get updated if they are a member, and for anything else the object will just be disposed of once we are
        # finished with it anyway.
        user_id = int(user_payload["id"])

        if self._user and user_id == self._user.id or "mfa_enabled" in user_payload or "verified" in user_payload:
            return self.parse_application_user(user_payload)

        user_obj = self.get_user_by_id(user_id)

        if user_obj is None:
            user_obj = users.parse_user(self.fabric, user_payload)
            self._users[user_id] = user_obj
            return user_obj

        existing_user = self._users[user_id]
        existing_user.update_state(user_payload)

        return existing_user

    def parse_webhook(self, webhook_payload: containers.DiscordObjectT) -> webhooks.Webhook:
        # Doesn't even need to be a method but I am trying to keep attribute changing code in this class
        # so that it isn't coupling dependent classes of this one to the model implementation as much.
        return webhooks.Webhook(self.fabric, webhook_payload)

    def set_guild_unavailability(self, guild_obj: guilds.Guild, is_unavailable: bool) -> None:
        # Doesn't even need to be a method but I am trying to keep attribute changing code in this class
        # so that it isn't coupling dependent classes of this one to the model implementation as much.
        guild_obj.is_unavailable = is_unavailable

    def set_last_pinned_timestamp(
        self, channel_obj: channels.TextChannel, timestamp: typing.Optional[datetime.datetime]
    ) -> None:
        # We don't persist this information, as it is not overly useful. The user can use the HTTP endpoint if they
        # care what the pins are...
        pass

    def set_roles_for_member(self, role_objs: typing.Sequence[roles.Role], member_obj: members.Member) -> None:
        # Doesn't even need to be a method but I am trying to keep attribute changing code in this class
        # so that it isn't coupling dependent classes of this one to the model implementation as much.
        member_obj.roles = [role for role in role_objs]

    def update_channel(
        self, channel_payload: containers.DiscordObjectT
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
        self, guild_payload: containers.DiscordObjectT
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
        self, emoji_list: typing.List[containers.DiscordObjectT], guild_obj: guilds.Guild
    ) -> typing.Optional[typing.Tuple[typing.FrozenSet[emojis.GuildEmoji], typing.FrozenSet[emojis.GuildEmoji]]]:
        old_emojis = frozenset(guild_obj.emojis.values())
        new_emojis = frozenset(self.parse_emoji(emoji_obj, guild_obj) for emoji_obj in emoji_list)
        guild_obj.emojis = transformations.id_map(new_emojis)
        return old_emojis, new_emojis

    def update_member(
        self, member_obj: members.Member, role_objs: typing.Sequence[roles.Role], payload: containers.DiscordObjectT,
    ) -> typing.Optional[typing.Tuple[members.Member, members.Member]]:
        new_member = member_obj
        old_member = new_member.copy()
        new_member.update_state(role_objs, payload)
        return old_member, new_member

    def update_member_presence(
        self, member_obj: members.Member, presence_payload: containers.DiscordObjectT
    ) -> typing.Optional[typing.Tuple[members.Member, presences.Presence, presences.Presence]]:
        old_presence = member_obj.presence
        new_presence = self.parse_presence(member_obj, presence_payload)
        return member_obj, old_presence, new_presence

    def update_message(
        self, payload: containers.DiscordObjectT
    ) -> typing.Optional[typing.Tuple[messages.Message, messages.Message]]:
        message_id = int(payload["message_id"])
        if message_id in self._message_cache:
            new_message = self._message_cache.get(message_id)
            old_message = new_message.copy()
            new_message.update_state(payload)
            return old_message, new_message
        return None

    def update_role(
        self, guild_obj: guilds.Guild, payload: containers.DiscordObjectT
    ) -> typing.Optional[typing.Tuple[roles.Role, roles.Role]]:
        role_id = int(payload["id"])
        existing_role = guild_obj.roles.get(role_id)

        if existing_role is not None:
            old_role = existing_role.copy()
            new_role = existing_role
            new_role.update_state(payload)
            return old_role, new_role
        return None
