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


from hikari.core.components.basic import state_registry as _state
from hikari.core.components import event_adapter
from hikari.core.net import gateway as _gateway
from hikari.core.model import channel
from hikari.core.utils import date_utils
from hikari.core.utils import transform


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
        Dispatches a :attr:`_gateway.Event.DISCONNECT` with the gateway object that triggered it as an argument,
        as well as the integer code given as the closure reason, and the reason string, if there was one.
        """
        self.dispatch(_gateway.Event.DISCONNECT, gateway, payload.get("code"), payload.get("reason"))

    async def handle_connect(self, gateway, payload):
        """
        Dispatches a :attr:`_gateway.Event.CONNECT` with the gateway object that triggered it as an argument.
        """
        self.dispatch(_gateway.Event.CONNECT, gateway)

    async def handle_invalid_session(self, gateway, payload):
        """
        Dispatches a :attr:`hikari.core.net.gateway.Event.INVALID_SESSION` with the gateway object that triggered it
        and a :class:`bool` indicating if the connection is able to be resumed or not as arguments.
        as an argument.
        """
        self.dispatch(_gateway.Event.INVALID_SESSION, gateway, payload)

    async def handle_request_to_reconnect(self, gateway, payload):
        """
        Dispatches a :attr:`hikari.core.net.gateway.Event.REQUEST_TO_RECONNECT` with the gateway object that triggered
        it as an argument.
        """
        self.dispatch(_gateway.Event.REQUEST_TO_RECONNECT, gateway)

    async def handle_resumed(self, gateway, payload):
        """
        Dispatches a :attr:`hikari.core.net.gateway.Event.RESUME` with the gateway object that triggered it as an
        argument.
        """
        self.dispatch(_gateway.Event.RESUMED, gateway)

    """
    API events
    """

    async def handle_channel_create(self, gateway, payload):
        channel = self.state_registry.parse_channel(payload)
        if channel.is_dm:
            self.dispatch(_gateway.Event.DM_CHANNEL_CREATE, channel)
        elif channel.guild is not None:
            self.dispatch(_gateway.Event.GUILD_CHANNEL_CREATE, channel)
        else:
            self.logger.warning(
                "ignoring received channel_create for unknown guild %s channel %s", payload.get("guild_id"), channel.id
            )

    async def handle_channel_update(self, gateway, payload):
        channel_id = int(payload["id"])
        channel_diff = self.state_registry.update_channel(payload)

        if channel_diff is not None:
            is_dm = channel.is_channel_type_dm(payload["type"])
            event = _gateway.Event.DM_CHANNEL_UPDATE if is_dm else _gateway.Event.GUILD_CHANNEL_UPDATE
            self.dispatch(event, *channel_diff)
        else:
            self.logger.warning("ignoring received CHANNEL_UPDATE for unknown channel %s", channel_id)

    async def handle_channel_delete(self, gateway, payload):
        # Update the channel meta data just for this call.
        channel = self.state_registry.parse_channel(payload)

        try:
            channel = self.state_registry.delete_channel(channel.id)
        except KeyError:
            # Inconsistent state gets ignored. This should not happen, I don't think.
            pass
        else:
            event = _gateway.Event.DM_CHANNEL_DELETE if channel.is_dm else _gateway.Event.GUILD_CHANNEL_DELETE
            self.dispatch(event, channel)

    async def handle_channel_pins_update(self, gateway, payload):
        channel_id = int(payload["channel_id"])
        channel_obj = self.state_registry.get_channel_by_id(channel_id)

        if channel_obj is not None:
            last_pin_timestamp = transform.nullable_cast(
                payload.get("last_pin_timestamp"), date_utils.parse_iso_8601_datetime
            )

            if last_pin_timestamp is not None:
                if channel_obj.is_dm:
                    self.dispatch(_gateway.Event.DM_CHANNEL_PIN_ADDED, last_pin_timestamp)
                else:
                    self.dispatch(_gateway.Event.GUILD_CHANNEL_PIN_ADDED, last_pin_timestamp)
            else:
                if channel_obj.is_dm:
                    self.dispatch(_gateway.Event.DM_CHANNEL_PIN_REMOVED)
                else:
                    self.dispatch(_gateway.Event.GUILD_CHANNEL_PIN_REMOVED)
        else:
            self.logger.warning(
                "ignoring CHANNEL_PINS_UPDATE for %s channel %s which was not previously cached",
                "DM" if channel.is_channel_type_dm(payload["type"]) else "guild",
                channel_id,
            )

    async def handle_guild_create(self, gateway, payload):
        guild_id = int(payload["id"])
        unavailable = payload.get("unavailable", False)
        was_already_loaded = self.state_registry.get_guild_by_id(guild_id) is not None
        guild = self.state_registry.parse_guild(payload)

        if not was_already_loaded:
            self.dispatch(_gateway.Event.GUILD_CREATE, guild)

        if not unavailable:
            self.dispatch(_gateway.Event.GUILD_AVAILABLE, guild)

    async def handle_guild_update(self, gateway, payload):
        guild_diff = self.state_registry.update_guild(payload)

        if guild_diff is not None:
            self.dispatch(_gateway.Event.GUILD_UPDATE, *guild_diff)
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

        self.state_registry.set_guild_unavailability(guild_id, True)

        guild_obj = self.state_registry.get_guild_by_id(guild_id)

        if guild_obj is not None:
            self.dispatch(_gateway.Event.GUILD_UNAVAILABLE, guild_obj)
        else:
            # We don't have a guild parsed yet. That shouldn't happen but if it does, we can make a note of this
            # so that we don't fail on other events later, and pre-emptively parse this information now.
            self.state_registry.parse_guild(payload)

    async def _handle_guild_leave(self, payload):
        guild = self.state_registry.parse_guild(payload)
        self.state_registry.delete_guild(guild.id)
        self.dispatch(_gateway.Event.GUILD_LEAVE, guild)

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

            self.dispatch(_gateway.Event.GUILD_BAN_ADD, guild, member)
        else:
            self.logger.warning("ignoring GUILD_BAN_ADD for user %s in unknown guild %s", user.id, guild_id)

    async def handle_guild_ban_remove(self, gateway, payload):
        guild_id = int(payload["guild_id"])
        guild = self.state_registry.get_guild_by_id(guild_id)
        user = self.state_registry.parse_user(payload["user"])
        if guild is not None:
            self.dispatch(_gateway.Event.GUILD_BAN_REMOVE, guild, user)
        else:
            self.logger.warning("ignoring GUILD_BAN_REMOVE for user %s in unknown guild %s", user.id, guild_id)

    async def handle_guild_emojis_update(self, gateway, payload):
        guild_id = int(payload["guild_id"])
        guild = self.state_registry.get_guild_by_id(guild_id)
        if guild is not None:
            old_emojis, new_emojis = self.state_registry.update_guild_emojis(payload, guild_id)
            self.dispatch(_gateway.Event.GUILD_EMOJIS_UPDATE, guild, old_emojis, new_emojis)
        else:
            self.logger.warning("ignoring GUILD_EMOJIS_UPDATE for unknown guild %s", guild_id)

    async def handle_guild_integrations_update(self, gateway, payload):
        guild_id = int(payload["guild_id"])
        guild = self.state_registry.get_guild_by_id(guild_id)
        if guild is not None:
            self.dispatch(_gateway.Event.GUILD_INTEGRATIONS_UPDATE, guild)
        else:
            self.logger.warning("ignoring GUILD_INTEGRATIONS_UPDATE for unknown guild %s", guild_id)

    async def handle_guild_member_add(self, gateway, payload):
        guild_id = int(payload.pop("guild_id"))
        guild = self.state_registry.get_guild_by_id(guild_id)
        if guild is not None:
            member = self.state_registry.parse_member(payload, guild_id)
            self.dispatch(_gateway.Event.GUILD_MEMBER_ADD, member)
        else:
            self.logger.warning("ignoring GUILD_MEMBER_ADD for unknown guild %s", guild_id)

    async def handle_guild_member_update(self, gateway, payload):
        guild_id = int(payload["guild_id"])
        guild = self.state_registry.get_guild_by_id(guild_id)
        user_id = int(payload["user"]["id"])

        if guild is not None and user_id in guild.members:
            role_ids = payload["roles"]
            nick = payload["nick"]

            member_diff = self.state_registry.update_member(guild_id, role_ids, nick, user_id)
            if member_diff is not None:
                self.dispatch(_gateway.Event.GUILD_MEMBER_UPDATE, *member_diff)
            else:
                self.logger.warning(
                    "ignoring GUILD_MEMBER_UPDATE for unknown member %s in guild %s", user_id, guild_id
                )
                self.state_registry.parse_member(payload, guild_id)
        else:
            self.logger.warning("ignoring GUILD_MEMBER_UPDATE for unknown guild %s", guild_id)

    async def handle_guild_member_remove(self, gateway, payload):
        user_id = int(payload["id"])
        guild_id = int(payload["guild_id"])
        member = self.state_registry.delete_member_from_guild(user_id, guild_id)
        self.dispatch(_gateway.Event.GUILD_LEAVE, member)

    async def handle_guild_members_chunk(self, gateway, payload):
        # TODO: implement this feature.
        self.logger.warning("Received GUILD_MEMBERS_CHUNK but that is not implemented yet")

    async def handle_guild_role_create(self, gateway, payload):
        guild_id = int(payload["guild_id"])
        guild = self.state_registry.get_guild_by_id(guild_id)

        if guild is not None:
            role = self.state_registry.parse_role(payload["role"], guild_id)
            self.dispatch(_gateway.Event.GUILD_ROLE_CREATE, role)
        else:
            self.logger.warning("ignoring GUILD_ROLE_CREATE for unknown guild %s", guild_id)

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
