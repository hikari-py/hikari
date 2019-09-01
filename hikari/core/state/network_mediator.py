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
import logging
import enum
import typing

from hikari.core.model import channel as _channel
from hikari.core.model import user as _user
from hikari.core.state import cache as _cache
from hikari.core.utils import dateutils
from hikari.core.utils import transform


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


class BasicNetworkMediator:
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

    # noinspection PyMissingConstructor
    def __init__(self, cache: _cache.InMemoryCache, dispatch):
        self.logger = logging.getLogger(__name__)
        self.cache = cache
        self.dispatch = dispatch
        self.user: typing.Optional[_user.BotUser] = None

    async def consume_raw_event(self, event_name, payload):
        try:
            handler = getattr(self, f"handle_{event_name.lower()}")
            self.logger.debug(f"Handling %s event", event_name)
            await handler(payload)
        except AttributeError:
            self.logger.warning("No transformation for %s exists, so the event is being ignored", event_name)

    async def handle_hello(self, _):
        self.dispatch(Event.CONNECTED)

    async def handle_ready(self, payload):
        user = payload["user"]
        guilds = payload["guilds"]

        self.user = _user.BotUser.from_dict(self.cache, user)

        for guild in guilds:
            self.cache.parse_guild(guild)

        # fixme: We shouldn't dispatch this until later probably.
        self.dispatch(Event.READY)

    async def handle_resumed(self, _):
        self.dispatch(Event.RESUMED)

    async def handle_channel_create(self, payload):
        self.dispatch(Event.CHANNEL_CREATED, self.cache.parse_channel(payload))

    async def handle_channel_update(self, payload):
        channel_id = int(payload["id"])
        old_channel = self.cache.get_guild_channel_by_id(channel_id) or self.cache.get_dm_channel_by_id(channel_id)
        new_channel = self.cache.parse_channel(payload)

        if old_channel is not None:
            transform.update_volatile_fields(old_channel, new_channel)
            self.dispatch(Event.CHANNEL_UPDATED, old_channel, new_channel)
        else:
            await self.handle_channel_create(payload)

    async def handle_channel_delete(self, payload):
        channel = self.cache.parse_channel(payload)
        if isinstance(channel, _channel.GuildChannel):
            del channel.guild.channels[channel.id]
        self.dispatch(Event.CHANNEL_DELETED, channel)

    async def handle_channel_pins_update(self, payload):
        channel_id = int(payload["channel_id"])
        last_pin_timestamp = payload.get("last_pin_timestamp")

        channel = self.cache.get_guild_channel_by_id(channel_id) or self.cache.get_dm_channel_by_id(channel_id)

        # Ignore if we don't have the channel cached yet...
        if channel is not None:
            if last_pin_timestamp is not None:
                channel.last_pin_timestamp = dateutils.parse_iso_8601_datetime(last_pin_timestamp)
                self.dispatch(Event.CHANNEL_PIN_ADDED, channel)
            else:
                self.dispatch(Event.CHANNEL_PIN_REMOVED, channel)

    async def handle_guild_create(self, payload):
        self.dispatch(Event.GUILD_AVAILABLE, self.cache.parse_guild(payload))

    async def handle_guild_update(self, payload):
        guild_id = int(payload["id"])
        old_guild = self.cache.get_guild_by_id(guild_id)
        new_guild = self.cache.parse_guild(payload)
        if old_guild is not None:
            transform.update_volatile_fields(old_guild, new_guild)
            self.dispatch(Event.GUILD_UPDATED, old_guild, new_guild)
        else:
            await self.handle_guild_create(payload)

    async def handle_guild_delete(self, payload):
        is_outage = payload.get("unavailable", False)
        guild_id = int(payload["id"])
        # If we have not cached the guild, parse a partial guild instead.
        guild = self.cache.get_guild_by_id(guild_id) or self.cache.parse_guild(payload)

        if is_outage:
            self.dispatch(Event.GUILD_UNAVAILABLE, guild)
        else:
            # We were kicked.
            self.dispatch(Event.GUILD_LEFT, self.cache.delete_guild(guild_id))

    async def handle_guild_ban_add(self, payload):
        guild = self.cache.get_guild_by_id(int(payload["id"]))
        # We shouldn't expect this to be occurring to add a new user when we are observing them being banned
        # but this ensures that if a ban occurs before we are fully ready that this will still fire correctly, I guess.
        user = self.cache.parse_user(payload["user"])
        self.cache.delete_member_from_guild(user.id, guild.id)
        self.dispatch(Event.GUILD_USER_BANNED, guild, user)

    async def handle_guild_ban_remove(self, payload):
        guild = self.cache.get_guild_by_id(int(payload["id"]))
        user = self.cache.parse_user(payload["user"])
        self.dispatch(Event.USER_PARDON, guild, user)

    async def handle_guild_emojis_update(self, payload):
        guild = self.cache.get_guild_by_id(int(payload["id"]))
        existing_emojis = guild.emojis
        new_emojis = transform.get_sequence(payload, "emojis", self.cache.parse_emoji, guild_id=guild.id)
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
        self.dispatch("presence_update", ...)

    async def handle_typing_start(self, payload):
        self.dispatch("typing_start", ...)

    async def handle_user_update(self, payload):
        self.dispatch("user_update", ...)

    async def handle_webhooks_update(self, payload):
        self.dispatch("webhooks_update", ...)
