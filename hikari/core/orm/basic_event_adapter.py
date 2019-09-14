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
Handles consumption of gateway events and converting them to the correct data types.
"""
from __future__ import annotations

import copy
import enum
import logging

import typing

from hikari.core.model import channel as _channel
from hikari.core.model import presence as _presence
from hikari.core.orm import basic_state_registry as _state
from hikari.core.utils import dateutils


#: The valid signature for a dispatch function. It must take the event type as the first argument.
from hikari.core.utils import types

DispatchFunctionT = typing.Callable[..., None]


class BasicEvent(str, enum.Enum):
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


class BasicEventAdapter:
    def __init__(self, state_registry: _state.BasicStateRegistry, dispatch: DispatchFunctionT) -> None:
        self.state_registry: _state.BasicStateRegistry = state_registry
        self.dispatch: DispatchFunctionT = dispatch
        self.logger = logging.getLogger(__name__)

    async def consume_raw_event(self, event_name: str, payload: types.DiscordObject) -> None:
        try:
            handler = getattr(self, f"handle_{event_name.lower()}")
        except AttributeError:
            self.logger.warning("No transformation for %s exists, so the event is being ignored", event_name)
            return
        else:
            self.logger.debug(f"Handling %s event", event_name)
            await handler(payload)

    async def handle_hello(self, _):
        self.dispatch(BasicEvent.CONNECTED)

    async def handle_ready(self, payload):
        self.state_registry.parse_bot_user(payload["user"])

        for guild in payload["guilds"]:
            self.state_registry.parse_guild(guild)

        # fixme: We shouldn't dispatch this until later probably.
        self.dispatch(BasicEvent.READY)

    async def handle_resumed(self, _):
        self.dispatch(BasicEvent.RESUMED)

    async def handle_channel_create(self, payload):
        self.dispatch(BasicEvent.CHANNEL_CREATED, self.state_registry.parse_channel(payload))

    async def handle_channel_update(self, payload):
        channel_id = int(payload["id"])
        existing_channel = self.state_registry.get_guild_channel_by_id(
            channel_id
        ) or self.state_registry.get_dm_channel_by_id(channel_id)

        if existing_channel is not None:
            old_channel = copy.deepcopy(existing_channel)
            existing_channel.update_state(payload)
            self.dispatch(BasicEvent.CHANNEL_UPDATED, old_channel, existing_channel)
        else:
            self.logger.debug("Received guild update for unknown channel %s; ignoring", channel_id)

    async def handle_channel_delete(self, payload):
        channel = self.state_registry.parse_channel(payload)
        if isinstance(channel, _channel.GuildChannel):
            del channel.guild.channels[channel.id]
        self.dispatch(BasicEvent.CHANNEL_DELETED, channel)

    async def handle_channel_pins_update(self, payload):
        channel_id = int(payload["channel_id"])
        last_pin_timestamp = payload.get("last_pin_timestamp")

        channel = self.state_registry.get_guild_channel_by_id(channel_id) or self.state_registry.get_dm_channel_by_id(
            channel_id
        )

        # Ignore if we don't have the channel cached yet...
        if channel is not None:
            if last_pin_timestamp is not None:
                channel.last_pin_timestamp = dateutils.parse_iso_8601_datetime(last_pin_timestamp)
                self.dispatch(BasicEvent.CHANNEL_PIN_ADDED, channel)
            else:
                self.dispatch(BasicEvent.CHANNEL_PIN_REMOVED, channel)

    async def handle_guild_create(self, payload):
        guild = self.state_registry.parse_guild(payload)
        self.dispatch(BasicEvent.GUILD_AVAILABLE, guild)

    async def handle_guild_update(self, payload):
        guild_id = int(payload["id"])
        existing_guild = self.state_registry.get_guild_by_id(guild_id)

        if existing_guild is not None:
            old_guild = copy.deepcopy(existing_guild)
            existing_guild.update_state(payload)
            self.dispatch(BasicEvent.GUILD_UPDATED, old_guild, existing_guild)
        else:
            self.logger.debug("Received guild update for unknown guild %s; ignoring", guild_id)

    async def handle_guild_delete(self, payload):
        is_outage = payload.get("unavailable", False)
        guild_id = int(payload["id"])
        # If we have not cached the guild, parse a partial guild instead.
        guild = self.state_registry.get_guild_by_id(guild_id) or self.state_registry.parse_guild(payload)

        if is_outage:
            # We have an outage.
            self.dispatch(BasicEvent.GUILD_UNAVAILABLE, guild)
        else:
            # We were kicked.
            self.dispatch(BasicEvent.GUILD_LEFT, self.state_registry.delete_guild(guild_id))

    async def handle_guild_ban_add(self, payload):
        guild = self.state_registry.get_guild_by_id(int(payload["id"]))
        # We shouldn't expect this to be occurring to add a new user when we are observing them being banned
        # but this ensures that if a ban occurs before we are fully ready that this will still fire correctly, I guess.
        user = self.state_registry.parse_user(payload["user"])
        self.state_registry.delete_member_from_guild(user.id, guild.id)
        self.dispatch(BasicEvent.GUILD_USER_BANNED, guild, user)

    async def handle_guild_ban_remove(self, payload):
        guild = self.state_registry.get_guild_by_id(int(payload["id"]))
        user = self.state_registry.parse_user(payload["user"])
        self.dispatch(BasicEvent.USER_PARDON, guild, user)

    async def handle_guild_emojis_update(self, payload):
        guild = self.state_registry.get_guild_by_id(int(payload["id"]))
        existing_emojis = guild.emojis
        new_emojis = [self.state_registry.parse_emoji(emoji, guild.id) for emoji in payload["emojis"]]
        guild.emojis = {e.id: e for e in new_emojis}
        self.dispatch(BasicEvent.GUILD_EMOJIS_UPDATED, existing_emojis, new_emojis)

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

        guild = self.state_registry.get_guild_by_id(guild_id)

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
                self.dispatch(BasicEvent.PRESENCE_UPDATED, member)

    async def handle_typing_start(self, payload):
        self.dispatch("typing_start", ...)

    async def handle_user_update(self, payload):
        self.dispatch("user_update", ...)

    async def handle_webhooks_update(self, payload):
        self.dispatch("webhooks_update", ...)
