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

import enum

from hikari.core.components import basic_state_registry as _state
from hikari.core.components import event_adapter
from hikari.core.utils import date_utils
from hikari.core.utils import transform


class BasicEvent(enum.Enum):
    """Event names that the basic event adapter can emit to the dispatcher."""

    CONNECT = enum.auto()
    DISCONNECT = enum.auto()
    INVALID_SESSION = enum.auto()
    REQUEST_TO_RECONNECT = enum.auto()
    RESUME = enum.auto()

    DM_CHANNEL_CREATE = enum.auto()
    GUILD_CHANNEL_CREATE = enum.auto()

    DM_CHANNEL_UPDATE = enum.auto()
    GUILD_CHANNEL_UPDATE = enum.auto()

    DM_CHANNEL_DELETE = enum.auto()
    GUILD_CHANNEL_DELETE = enum.auto()

    DM_CHANNEL_PIN_ADDED = enum.auto()
    GUILD_CHANNEL_PIN_ADDED = enum.auto()

    DM_CHANNEL_PIN_REMOVED = enum.auto()
    GUILD_CHANNEL_PIN_REMOVED = enum.auto()

    GUILD_AVAILABLE = enum.auto()
    GUILD_UNAVAILABLE = enum.auto()
    GUILD_JOIN = enum.auto()
    GUILD_UPDATE = enum.auto()
    GUILD_LEAVE = enum.auto()

    GUILD_BAN_ADD = enum.auto()
    GUILD_BAN_REMOVE = enum.auto()

    GUILD_EMOJIS_UPDATE = enum.auto()

    GUILD_INTEGRATIONS_UPDATE = enum.auto()

    GUILD_MEMBER_ADD = enum.auto()
    GUILD_MEMBER_UPDATE = enum.auto()
    GUILD_MEMBER_REMOVE = enum.auto()


class BasicEventAdapter(event_adapter.EventAdapter):
    """
    Basic implementation of event management logic.
    """

    def __init__(self, state_registry: _state.BasicStateRegistry, dispatch) -> None:
        super().__init__()
        self.dispatch = dispatch
        self.state_registry: _state.BasicStateRegistry = state_registry
        self._ignored_events = set()

    async def handle_unrecognised_event(self, gateway, event_name, payload):
        if event_name not in self._ignored_events:
            self.logger.warning("Received unrecognised event %s, so will ignore it in the future.", event_name)
            self._ignored_events.add(event_name)

    """
    Connection-related and internally-occurring events.
    """

    async def handle_disconnect(self, gateway, payload):
        """
        Dispatches a :attr:`BasicEvent.DISCONNECT` with the gateway object that triggered it as an argument,
        as well as the integer code given as the closure reason, and the reason string, if there was one.
        """
        self.dispatch(BasicEvent.DISCONNECT, gateway, payload.get("code"), payload.get("reason"))

    async def handle_hello(self, gateway, payload):
        """
        Dispatches a :attr:`BasicEvent.CONNECT` with the gateway object that triggered it as an argument.
        """
        self.dispatch(BasicEvent.CONNECT, gateway)

    async def handle_invalid_session(self, gateway, payload):
        """
        Dispatches a :attr:`BasicEvent.INVALID_SESSION` with the gateway object that triggered it
        and a :class:`bool` indicating if the connection is able to be resumed or not as arguments.
        as an argument.
        """
        self.dispatch(BasicEvent.INVALID_SESSION, gateway, payload)

    async def handle_request_to_reconnect(self, gateway, payload):
        """
        Dispatches a :attr:`BasicEvent.REQUEST_TO_RECONNECT` with the gateway object that triggered it as
        an argument.
        """
        self.dispatch(BasicEvent.REQUEST_TO_RECONNECT, gateway)

    async def handle_resumed(self, gateway, payload):
        """
        Dispatches a :attr:`BasicEvent.RESUME` with the gateway object that triggered it as an argument.
        """
        self.dispatch(BasicEvent.RESUME, gateway)

    """
    API events
    """

    async def handle_channel_create(self, gateway, payload):
        channel = self.state_registry.parse_channel(payload)
        if channel.is_dm:
            self.dispatch(BasicEvent.DM_CHANNEL_CREATE, channel)
        elif channel.guild is not None:
            self.dispatch(BasicEvent.GUILD_CHANNEL_CREATE, channel)
        # ignore if we haven't parsed the guild yet, as discord is just sending bad payloads.

    async def handle_channel_update(self, gateway, payload):
        channel_id = int(payload["id"])
        old_channel = self.state_registry.get_channel_by_id(channel_id)

        if old_channel is not None:
            new_channel = self.state_registry.parse_channel(payload)
            if new_channel.is_dm:
                self.dispatch(BasicEvent.DM_CHANNEL_UPDATE, old_channel, new_channel)
            else:
                self.dispatch(BasicEvent.GUILD_CHANNEL_UPDATE, old_channel, new_channel)

    async def handle_channel_delete(self, gateway, payload):
        channel_id = int(payload["id"])
        channel = self.state_registry.get_channel_by_id(channel_id)

        if channel is not None:
            # Update the channel meta data just for this call.
            channel = self.state_registry.parse_channel(payload)

            try:
                channel = self.state_registry.delete_channel(channel.id)
            except KeyError:
                # Inconsistent state gets ignored.
                pass
            else:
                event = BasicEvent.DM_CHANNEL_DELETE if channel.is_dm else BasicEvent.GUILD_CHANNEL_DELETE
                self.dispatch(event, channel)

    async def handle_channel_pins_update(self, gateway, payload):
        channel_id = int(payload["channel_id"])
        channel = self.state_registry.get_channel_by_id(channel_id)

        last_pin_timestamp = transform.nullable_cast(
            payload.get("last_pin_timestamp"), date_utils.parse_iso_8601_datetime
        )

        if channel is not None:
            if last_pin_timestamp is not None:
                if channel.is_dm:
                    self.dispatch(BasicEvent.DM_CHANNEL_PIN_ADDED, last_pin_timestamp)
                else:
                    self.dispatch(BasicEvent.GUILD_CHANNEL_PIN_ADDED, last_pin_timestamp)
            else:
                if channel.is_dm:
                    self.dispatch(BasicEvent.DM_CHANNEL_PIN_REMOVED)
                else:
                    self.dispatch(BasicEvent.GUILD_CHANNEL_PIN_REMOVED)

    async def handle_guild_create(self, gateway, payload):
        guild_id = int(payload["guild_id"])
        unavailable = payload.get("unavailable", False)
        is_new = self.state_registry.get_guild_by_id(guild_id) is None

        guild = self.state_registry.parse_guild(payload)

        if not unavailable:
            if is_new:
                # We joined the guild. Yay.
                # This relies on the fact that guilds still get internally cached if they are unavailable for any of
                # this to remotely function as expected.
                self.dispatch(BasicEvent.GUILD_JOIN, guild)
            else:
                self.dispatch(BasicEvent.GUILD_AVAILABLE, guild)

    async def handle_guild_update(self, gateway, payload):
        guild_id = int(payload["guild_id"])

        previous_guild = self.state_registry.get_guild_by_id(guild_id)
        now_unavailable = payload.get("unavailable", False)

        if previous_guild is not None and now_unavailable:
            if previous_guild.unavailable and not now_unavailable:
                await self.handle_guild_create(gateway, payload)
            else:
                self.dispatch(BasicEvent.GUILD_UPDATE, previous_guild, self.state_registry.parse_guild(payload))

    async def handle_guild_delete(self, gateway, payload):
        unavailable = payload.get("unavailable", False)
        guild = self.state_registry.parse_guild(payload)
        if not unavailable:
            self.state_registry.delete_guild(guild.id)
            self.dispatch(BasicEvent.GUILD_LEAVE, guild)
        else:
            self.dispatch(BasicEvent.GUILD_UNAVAILABLE, guild)

    async def handle_guild_ban_add(self, gateway, payload):
        guild_id = int(payload["guild_id"])
        guild = self.state_registry.get_guild_by_id(guild_id)
        if guild is not None:
            user = self.state_registry.parse_user(payload["user"])
            self.dispatch(BasicEvent.GUILD_BAN_ADD, guild, user)

    async def handle_guild_ban_remove(self, gateway, payload):
        guild_id = int(payload["guild_id"])
        guild = self.state_registry.get_guild_by_id(guild_id)
        if guild is not None:
            user = self.state_registry.parse_user(payload["user"])
            self.dispatch(BasicEvent.GUILD_BAN_REMOVE, guild, user)

    async def handle_guild_emojis_update(self, gateway, payload):
        guild_id = int(payload["guild_id"])
        guild = self.state_registry.get_guild_by_id(guild_id)
        if guild is not None:
            old_emojis = [*guild.emojis.values()]
            new_emojis = [self.state_registry.parse_emoji(emoji, guild_id) for emoji in payload["emojis"]]
            guild.emojis = transform.snowflake_map(new_emojis)
            self.dispatch(BasicEvent.GUILD_EMOJIS_UPDATE, old_emojis, new_emojis)

    async def handle_guild_integrations_update(self, gateway, payload):
        guild_id = int(payload["guild_id"])
        guild = self.state_registry.get_guild_by_id(guild_id)
        if guild is not None:
            self.dispatch(BasicEvent.GUILD_INTEGRATIONS_UPDATE, guild)

    async def handle_guild_member_add(self, gateway, payload):
        guild_id = int(payload.pop("guild_id"))
        guild = self.state_registry.get_guild_by_id(guild_id)
        if guild is not None:
            member = self.state_registry.parse_member(payload, guild_id)
            self.dispatch(BasicEvent.GUILD_MEMBER_ADD, member)

    async def handle_guild_member_update(self, gateway, payload):
        ...

    async def handle_guild_member_remove(self, gateway, payload):
        ...

    async def handle_guild_members_chunk(self, gateway, payload):
        # TODO: implement this properly.
        ...

    async def handle_guild_role_create(self, gateway, payload):
        ...

    async def handle_guild_role_update(self, gateway, payload):
        ...

    async def handle_guild_role_delete(self, gateway, payload):
        ...

    async def handle_message_create(self, gateway, payload):
        ...

    async def handle_message_update(self, gateway, payload):
        ...

    async def handle_message_delete(self, gateway, payload):
        ...

    async def handle_message_delete_bulk(self, gateway, payload):
        ...

    async def handle_message_reaction_add(self, gateway, payload):
        ...

    async def handle_message_reaction_remove(self, gateway, payload):
        ...

    async def handle_message_reaction_remove_all(self, gateway, payload):
        ...

    async def handle_presence_update(self, gateway, payload):
        ...

    async def handle_typing_start(self, gateway, payload):
        ...

    async def handle_user_update(self, gateway, payload):
        ...

    async def handle_voice_state_update(self, gateway, payload):
        ...

    async def handle_voice_server_update(self, gateway, payload):
        ...

    async def handle_webhooks_update(self, gateway, payload):
        ...
