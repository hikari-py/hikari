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
from hikari.core.components import event_adapter_stub
from hikari.core.model import channel as _channel
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

    GUILD_CREATE = enum.auto()
    GUILD_AVAILABLE = enum.auto()
    GUILD_UNAVAILABLE = enum.auto()
    GUILD_UPDATE = enum.auto()
    GUILD_LEAVE = enum.auto()

    GUILD_BAN_ADD = enum.auto()
    GUILD_BAN_REMOVE = enum.auto()

    GUILD_EMOJIS_UPDATE = enum.auto()

    GUILD_INTEGRATIONS_UPDATE = enum.auto()

    GUILD_MEMBER_ADD = enum.auto()
    GUILD_MEMBER_UPDATE = enum.auto()
    GUILD_MEMBER_REMOVE = enum.auto()


class BasicEventAdapter(event_adapter_stub.EventAdapterStub):
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
        else:
            self.logger.warning(
                "ignoring received channel_create for unknown guild %s channel %s", payload.get("guild_id"), channel.id
            )

    async def handle_channel_update(self, gateway, payload):
        channel_id = int(payload["id"])
        old_channel = self.state_registry.get_channel_by_id(channel_id)

        is_dm = _channel.is_channel_type_dm(payload["type"])

        if old_channel is not None:
            new_channel = self.state_registry.parse_channel(payload)

            if is_dm:
                self.dispatch(BasicEvent.DM_CHANNEL_UPDATE, old_channel, new_channel)
            else:
                self.dispatch(BasicEvent.GUILD_CHANNEL_UPDATE, old_channel, new_channel)
        elif is_dm:
            self.logger.warning("ignoring received CHANNEL_UPDATE for unknown DM channel %s", channel_id)
        else:
            self.state_registry.parse_channel(payload)
            self.logger.warning(
                "ignoring received CHANNEL_UPDATE for unknown guild channel %s - cache amended", channel_id
            )

    async def handle_channel_delete(self, gateway, payload):
        # Update the channel meta data just for this call.
        channel = self.state_registry.parse_channel(payload)

        try:
            channel = self.state_registry.delete_channel(channel.id)
        except KeyError:
            # Inconsistent state gets ignored. This should not happen, I don't think.
            pass
        else:
            event = BasicEvent.DM_CHANNEL_DELETE if channel.is_dm else BasicEvent.GUILD_CHANNEL_DELETE
            self.dispatch(event, channel)

    async def handle_channel_pins_update(self, gateway, payload):
        channel_id = int(payload["channel_id"])
        channel = self.state_registry.get_channel_by_id(channel_id)

        if channel is not None:
            last_pin_timestamp = transform.nullable_cast(
                payload.get("last_pin_timestamp"), date_utils.parse_iso_8601_datetime
            )

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
        else:
            self.logger.warning(
                "ignoring CHANNEL_PINS_UPDATE for %s channel %s which was not previously cached",
                "DM" if _channel.is_channel_type_dm(payload["type"]) else "guild",
                channel_id,
            )

    async def handle_guild_create(self, gateway, payload):
        guild_id = int(payload["id"])
        unavailable = payload.get("unavailable", False)
        was_already_loaded = self.state_registry.get_guild_by_id(guild_id) is not None
        guild = self.state_registry.parse_guild(payload)

        if not was_already_loaded:
            self.dispatch(BasicEvent.GUILD_CREATE, guild)

        if not unavailable:
            self.dispatch(BasicEvent.GUILD_AVAILABLE, guild)

    async def handle_guild_update(self, gateway, payload):
        guild_id = int(payload["id"])
        guild = self.state_registry.get_guild_by_id(guild_id)

        if guild is not None:
            previous_guild = guild.clone()
            new_guild = self.state_registry.parse_guild(payload)
            self.dispatch(BasicEvent.GUILD_UPDATE, previous_guild, new_guild)
        else:
            self.state_registry.parse_guild(payload)
            self.logger.warning(
                "ignoring GUILD_UPDATE for unknown guild %s which was not previously cached - cache amended"
            )

    async def handle_guild_delete(self, gateway, payload):
        # This should always be unspecified if the guild was left,
        # but if discord suddenly send "False" instead, it will still work.
        if payload.get("unavailable", False):
            await self._handle_guild_unavailable(payload)
        else:
            await self._handle_guild_leave(payload)

    async def _handle_guild_unavailable(self, payload):
        # We shouldn't ever need to parse this payload unless we have inconsistent state, but if that happens,
        # lets attempt to fix it.
        guild_id = int(payload["id"])
        guild = self.state_registry.get_guild_by_id(guild_id)

        if guild is None:
            guild = self.state_registry.parse_guild(payload)

        # TODO: move to state registry code, maybe?
        guild.unavailable = True
        self.dispatch(BasicEvent.GUILD_UNAVAILABLE, guild)

    async def _handle_guild_leave(self, payload):
        guild = self.state_registry.parse_guild(payload)
        self.state_registry.delete_guild(guild.id)
        self.dispatch(BasicEvent.GUILD_LEAVE, guild)

    async def handle_guild_ban_add(self, gateway, payload):
        guild_id = int(payload["guild_id"])
        guild = self.state_registry.get_guild_by_id(guild_id)
        user = self.state_registry.parse_user(payload["user"])
        if guild is not None:

            # The user may or may not be cached, if the guild is large. So, we may have to just pass a normal user, or
            # if we can, we can pass a whole member. The member should be assumed to be normal behaviour unless caching
            # of members was disabled, or if Discord is screwing up; regardless, it is probably worth checking this
            # information first. Since they just got banned, we can't even look this information up anymore...
            # Perhaps the audit logs could be checked, but this seems like an overkill, honestly...
            try:
                member = self.state_registry.delete_member_from_guild(user.id, guild_id)
            except KeyError:
                member = user

            self.dispatch(BasicEvent.GUILD_BAN_ADD, guild, member)
        else:
            self.logger.warning("ignoring GUILD_BAN_ADD for user %s in unknown guild %s", user.id, guild_id)

    async def handle_guild_ban_remove(self, gateway, payload):
        guild_id = int(payload["guild_id"])
        guild = self.state_registry.get_guild_by_id(guild_id)
        user = self.state_registry.parse_user(payload["user"])
        if guild is not None:
            self.dispatch(BasicEvent.GUILD_BAN_REMOVE, guild, user)
        else:
            self.logger.warning("ignoring GUILD_BAN_REMOVE for user %s in unknown guild %s", user.id, guild_id)

    async def handle_guild_emojis_update(self, gateway, payload):
        guild_id = int(payload["guild_id"])
        guild = self.state_registry.get_guild_by_id(guild_id)
        if guild is not None:
            old_emojis, new_emojis = self.state_registry.update_guild_emojis(payload, guild_id)
            self.dispatch(BasicEvent.GUILD_EMOJIS_UPDATE, guild, old_emojis, new_emojis)
        else:
            self.logger.warning("ignoring GUILD_EMOJIS_UPDATE for unknown guild %s", guild_id)

    async def handle_guild_integrations_update(self, gateway, payload):
        guild_id = int(payload["guild_id"])
        guild = self.state_registry.get_guild_by_id(guild_id)
        if guild is not None:
            self.dispatch(BasicEvent.GUILD_INTEGRATIONS_UPDATE, guild)
        else:
            self.logger.warning("ignoring GUILD_INTEGRATIONS_UPDATE for unknown guild %s", guild_id)

    async def handle_guild_member_add(self, gateway, payload):
        guild_id = int(payload.pop("guild_id"))
        guild = self.state_registry.get_guild_by_id(guild_id)
        if guild is not None:
            member = self.state_registry.parse_member(payload, guild_id)
            self.dispatch(BasicEvent.GUILD_MEMBER_ADD, member)
        else:
            self.logger.warning("ignoring GUILD_MEMBER_ADD for unknown guild %s", guild_id)

    async def handle_guild_member_update(self, gateway, payload):
        guild_id = int(payload["guild_id"])
        guild = self.state_registry.get_guild_by_id(guild_id)

        if guild is not None:
            user_payload = payload["user"]
            role_ids = payload["roles"]
            nick = payload[""]

        else:
            self.logger.warning("ignoring GUILD_MEMBER_UPDATE for unknown guild %s", guild_id)

    async def handle_guild_member_remove(self, gateway, payload):
        user_id = int(payload["id"])
        guild_id = int(payload["guild_id"])
        member = self.state_registry.delete_member_from_guild(user_id, guild_id)
        self.dispatch(BasicEvent.GUILD_LEAVE, member)

    async def handle_guild_members_chunk(self, gateway, payload):
        # TODO: implement this properly in the future.
        ...

    async def handle_guild_role_create(self, gateway, payload):
        guild_id = int(payload["guild_id"])
        guild = self.state_registry.get_guild_by_id(guild_id)

        if guild is not None:
            role = self.state_registry.parse_role(payload["role"], guild_id)

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
