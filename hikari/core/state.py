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
Integrates with the gateway and HTTP components, wrapping an in-memory cache to enable full stateful tracking and
transformation of JSON payloads into Python objects for any service layer that interacts with us. This is what
differentiates the framework from a simple HTTP and websocket wrapper to a full idiomatic pythonic bot framework!
"""
import copy
import enum
import logging
import weakref

import typing

from hikari.core.model import channel as _channel
from hikari.core.model import emoji as _emoji
from hikari.core.model import guild as _guild
from hikari.core.model import message as _message
from hikari.core.model import model_cache
from hikari.core.model import presence as _presence
from hikari.core.model import role as _role
from hikari.core.model import user as _user
from hikari.core.model import webhook as _webhook
from hikari.core.utils import dateutils
from hikari.core.utils import transform
from hikari.core.utils import types


class Event(str, enum.Enum):
    """
    Valid network-based events we can dispatch.
    """

    #: Hello payload was sent, initial connection was made.
    CONNECTED = "connected"
    #: Bot is ready, state has been loaded.
    READY = "ready"
    #: Connection has been resumed.
    RESUMED = "resumed"
    #: A channel was created.
    CHANNEL_CREATED = "channel_created"
    #: A channel was updated.
    CHANNEL_UPDATED = "channel_updated"
    #: A channel was deleted.
    CHANNEL_DELETED = "channel_deleted"
    #: A pin was added to a channel.
    CHANNEL_PIN_ADDED = "channel_pin_added"
    #: A pin was removed from a channel.
    CHANNEL_PIN_REMOVED = "channel_pin_removed"
    #: A guild has just become available. This occurs when we first connect before `ready` is triggered, when resuming
    #: and the guild becomes available again, or when joining a new guild. Also fires once an outage ends.
    GUILD_AVAILABLE = "guild_available"
    #: Info about the guild changed.
    GUILD_UPDATED = "guild_updated"
    #: A guild became unavailable because of an outage.
    GUILD_UNAVAILABLE = "guild_unavailable"
    #: The bot was kicked from the guild.
    GUILD_LEFT = "guild_left"
    #: A guild banned someone.
    GUILD_USER_BANNED = "guild_user_banned"
    #: A guild unbanned someone.
    GUILD_USER_PARDONED = "guild_user_pardoned"
    #: Emojis updated in a guild.
    GUILD_EMOJIS_UPDATED = "guild_emojis_updated"
    #: The presence of a user changed.
    PRESENCE_UPDATED = "presence_updated"


class State(model_cache.AbstractModelCache):
    """
    A mediator for gateway and HTTP components that bridges their interface with the model API and cache API to allow
    everything to interact with each other nicely.

    This defines how events should be processed and what should be dispatched, for example.

    Arguments:
        cache:
            The cache implementation to wrap
        dispatch:
            The dispatch FUNCTION to call. This should not be a co-routine, as it is expected to merely schedule
            future callbacks, not await them.
    """

    def __init__(self, dispatch, message_cache_size: int = 100, user_dm_channel_size: int = 100) -> None:
        # Users may be cached while we can see them, or they may be cached as a member. Regardless, we only
        # retain them while they are referenced from elsewhere to keep things tidy.
        # noinspection PyTypeChecker
        self._users: typing.Dict[int, _user.User] = weakref.WeakValueDictionary()
        self._guilds: typing.Dict[int, _guild.Guild] = {}
        self._dm_channels: typing.Dict[int, _channel.DMChannel] = types.LRUDict(user_dm_channel_size)
        self._guild_channels = weakref.WeakValueDictionary()
        self._messages = types.LRUDict(message_cache_size)
        self._emojis = weakref.WeakValueDictionary()

        self.dispatch = dispatch
        self.user: typing.Optional[_user.BotUser] = None
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
        user_id = int(user["id"])
        if user_id not in self._users:
            self._users[user_id] = _user.User(self, user)
        return self._users[user_id]

    def parse_guild(self, guild: types.DiscordObject):
        guild_id = int(guild.get("id"))
        if guild_id not in self._guilds:
            self._guilds[guild_id] = _guild.Guild(self, guild)
        else:
            guild_obj = self._guilds[guild_id]
            guild_obj.update_state(guild)
            return guild_obj

    def parse_member(self, member: types.DiscordObject, guild_id: int):
        # Don't cache members here.
        guild = self.get_guild_by_id(guild_id)
        member_id = transform.get_cast(member, "id", int)

        if guild is None:
            self.logger.warning("Member ID %s referencing an unknown guild %s; ignoring", member_id, guild_id)
        elif member_id in guild.members:
            return guild.members[member_id]
        else:
            member_object = _user.Member(self, guild_id, member)
            guild.members[member_id] = member_object
            return member_object

    def parse_role(self, role: types.DiscordObject):
        # Don't cache roles.
        return _role.Role(role)

    def parse_emoji(self, emoji: types.DiscordObject, guild_id: int):
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

    async def consume_raw_event(self, event_name, payload):
        try:
            handler = getattr(self, f"handle_{event_name.lower()}")
        except AttributeError:
            self.logger.warning("No transformation for %s exists, so the event is being ignored", event_name)
            return
        else:
            self.logger.debug(f"Handling %s event", event_name)
            await handler(payload)

    async def handle_hello(self, _):
        self.dispatch(Event.CONNECTED)

    async def handle_ready(self, payload):
        user = payload["user"]
        guilds = payload["guilds"]

        self.user = _user.BotUser(self, user)

        for guild in guilds:
            self.parse_guild(guild)

        # fixme: We shouldn't dispatch this until later probably.
        self.dispatch(Event.READY)

    async def handle_resumed(self, _):
        self.dispatch(Event.RESUMED)

    async def handle_channel_create(self, payload):
        self.dispatch(Event.CHANNEL_CREATED, self.parse_channel(payload))

    async def handle_channel_update(self, payload):
        channel_id = int(payload["id"])
        existing_channel = self.get_guild_channel_by_id(channel_id) or self.get_dm_channel_by_id(channel_id)

        if existing_channel is not None:
            old_channel = copy.deepcopy(existing_channel)
            existing_channel.update_state(payload)
            self.dispatch(Event.CHANNEL_UPDATED, old_channel, existing_channel)
        else:
            self.logger.debug("Received guild update for unknown channel %s; ignoring", channel_id)

    async def handle_channel_delete(self, payload):
        channel = self.parse_channel(payload)
        if isinstance(channel, _channel.GuildChannel):
            del channel.guild.channels[channel.id]
        self.dispatch(Event.CHANNEL_DELETED, channel)

    async def handle_channel_pins_update(self, payload):
        channel_id = int(payload["channel_id"])
        last_pin_timestamp = payload.get("last_pin_timestamp")

        channel = self.get_guild_channel_by_id(channel_id) or self.get_dm_channel_by_id(channel_id)

        # Ignore if we don't have the channel cached yet...
        if channel is not None:
            if last_pin_timestamp is not None:
                channel.last_pin_timestamp = dateutils.parse_iso_8601_datetime(last_pin_timestamp)
                self.dispatch(Event.CHANNEL_PIN_ADDED, channel)
            else:
                self.dispatch(Event.CHANNEL_PIN_REMOVED, channel)

    async def handle_guild_create(self, payload):
        guild = self.parse_guild(payload)
        self.dispatch(Event.GUILD_AVAILABLE, guild)

    async def handle_guild_update(self, payload):
        guild_id = int(payload["id"])
        existing_guild = self.get_guild_by_id(guild_id)

        if existing_guild is not None:
            old_guild = copy.deepcopy(existing_guild)
            existing_guild.update_state(payload)
            self.dispatch(Event.GUILD_UPDATED, old_guild, existing_guild)
        else:
            self.logger.debug("Received guild update for unknown guild %s; ignoring", guild_id)

    async def handle_guild_delete(self, payload):
        is_outage = payload.get("unavailable", False)
        guild_id = int(payload["id"])
        # If we have not cached the guild, parse a partial guild instead.
        guild = self.get_guild_by_id(guild_id) or self.parse_guild(payload)

        if is_outage:
            # We have an outage.
            self.dispatch(Event.GUILD_UNAVAILABLE, guild)
        else:
            # We were kicked.
            self.dispatch(Event.GUILD_LEFT, self.delete_guild(guild_id))

    async def handle_guild_ban_add(self, payload):
        guild = self.get_guild_by_id(int(payload["id"]))
        # We shouldn't expect this to be occurring to add a new user when we are observing them being banned
        # but this ensures that if a ban occurs before we are fully ready that this will still fire correctly, I guess.
        user = self.parse_user(payload["user"])
        self.delete_member_from_guild(user.id, guild.id)
        self.dispatch(Event.GUILD_USER_BANNED, guild, user)

    async def handle_guild_ban_remove(self, payload):
        guild = self.get_guild_by_id(int(payload["id"]))
        user = self.parse_user(payload["user"])
        self.dispatch(Event.USER_PARDON, guild, user)

    async def handle_guild_emojis_update(self, payload):
        guild = self.get_guild_by_id(int(payload["id"]))
        existing_emojis = guild.emojis
        new_emojis = transform.get_sequence(payload, "emojis", self.parse_emoji, guild_id=guild.id)
        guild.emojis = {e.id: e for e in new_emojis}
        self.dispatch(Event.GUILD_EMOJIS_UPDATED, existing_emojis, new_emojis)

    async def handle_guild_integrations_update(self, payload):
        self.dispatch("guild_integrations_update", ...)

    async def handle_guild_member_add(self, payload):
        self.dispatch("guild_member_add", ...)

    async def handle_guild_member_remove(self, payload):
        self.dispatch("guild_member_remove", ...)

    async def handle_guild_member_update(self, payload):
        self.dispatch("guild_member_update", ...)

    async def handle_guild_members_chunk(self, payload):
        self.dispatch("guild_members_chunk", ...)

    async def handle_guild_role_create(self, payload):
        self.dispatch("guild_role_create", ...)

    async def handle_guild_role_update(self, payload):
        self.dispatch("guild_role_update", ...)

    async def handle_guild_role_delete(self, payload):
        self.dispatch("guild_role_delete", ...)

    async def handle_message_create(self, payload):
        self.dispatch("message_create", ...)

    async def handle_message_update(self, payload):
        self.dispatch("message_update", ...)

    async def handle_message_delete(self, payload):
        self.dispatch("message_delete", ...)

    async def handle_message_delete_bulk(self, payload):
        self.dispatch("message_delete_bulk", ...)

    async def handle_message_reaction_add(self, payload):
        self.dispatch("message_reaction_add", ...)

    async def handle_message_reaction_remove(self, payload):
        self.dispatch("message_reaction_remove", ...)

    async def handle_message_reaction_remove_all(self, payload):
        self.dispatch("message_reaction_remove_all", ...)

    async def handle_presence_update(self, payload):
        user_id = int(payload["user"]["id"])
        guild_id = int(payload["guild_id"])

        guild = self.get_guild_by_id(guild_id)

        if guild is None:
            self.logger.debug("User ID %s referencing unknown guild %s in presence update; ignoring", user_id, guild_id)
        else:
            member = guild.members.get(user_id)

            if member is None:
                self.logger.debug(
                    "Non existent member %s referred to in guild %s presence update; ignoring", user_id, guild_id
                )
            else:
                member.presence = _presence.Presence(payload)
                self.dispatch(Event.PRESENCE_UPDATED, member)

    async def handle_typing_start(self, payload):
        self.dispatch("typing_start", ...)

    async def handle_user_update(self, payload):
        self.dispatch("user_update", ...)

    async def handle_webhooks_update(self, payload):
        self.dispatch("webhooks_update", ...)
