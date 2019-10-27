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

import typing

from hikari.core import events
from hikari.core.internal import event_adapter
from hikari.core.internal import state_registry as _state
from hikari.core.models import channel, reaction, presence
from hikari.core.utils import date_utils, custom_types
from hikari.core.utils import transform


class BasicEventAdapter(event_adapter.EventAdapter):
    """
    Basic implementation of event management logic.
    """

    def __init__(self, state_registry: _state.StateRegistry, dispatch) -> None:
        super().__init__()
        self.dispatch = dispatch
        self.state_registry: _state.StateRegistry = state_registry
        self._ignored_events = set()

    async def handle_unrecognised_event(self, gateway, event_name, payload):
        self.dispatch("raw_" + event_name.lower(), payload)
        if event_name not in self._ignored_events:
            self.logger.warning("Received unrecognised event %s, so will ignore it in the future.", event_name)
            self._ignored_events.add(event_name)

    async def handle_disconnect(self, gateway, payload):
        self.dispatch(events.DISCONNECT, gateway, payload.get("code"), payload.get("reason"))

    async def handle_connect(self, gateway, payload):
        self.dispatch(events.CONNECT, gateway)

    async def handle_invalid_session(self, gateway, payload: bool):
        self.dispatch(events.INVALID_SESSION, gateway, payload)

    async def handle_reconnect(self, gateway, payload):
        self.dispatch(events.RECONNECT, gateway)

    async def handle_resumed(self, gateway, payload):
        self.dispatch(events.RESUMED, gateway)

    async def handle_channel_create(self, gateway, payload):
        self.dispatch(events.RAW_CHANNEL_CREATE, payload)

        guild_id = transform.nullable_cast(payload.get("guild_id"), int)
        channel_obj = self.state_registry.parse_channel(payload, guild_id)

        if channel_obj.is_dm:
            self.dispatch(events.DM_CHANNEL_CREATE, channel_obj)
        elif channel_obj.guild is not None:
            self.dispatch(events.GUILD_CHANNEL_CREATE, channel_obj)
        else:
            self.logger.warning(
                "ignoring received channel_create for unknown guild %s channel %s",
                payload.get("guild_id"),
                channel_obj.id,
            )

    async def handle_channel_update(self, gateway, payload):
        self.dispatch(events.RAW_CHANNEL_UPDATE, payload)

        channel_id = int(payload["id"])
        channel_diff = self.state_registry.update_channel(payload)

        if channel_diff is not None:
            is_dm = channel.is_channel_type_dm(payload["type"])
            event = events.DM_CHANNEL_UPDATE if is_dm else events.GUILD_CHANNEL_UPDATE
            self.dispatch(event, *channel_diff)
        else:
            self.logger.warning("ignoring received CHANNEL_UPDATE for unknown channel %s", channel_id)

    async def handle_channel_delete(self, gateway, payload):
        # Update the channel meta data just for this call.
        self.dispatch(events.RAW_CHANNEL_DELETE, payload)

        channel_obj = self.state_registry.parse_channel(payload)

        try:
            channel_obj = self.state_registry.delete_channel(channel_obj.id)
        except KeyError:
            # Inconsistent state gets ignored. This should not happen, I don't think.
            pass
        else:
            event = events.DM_CHANNEL_DELETE if channel_obj.is_dm else events.GUILD_CHANNEL_DELETE
            self.dispatch(event, channel_obj)

    async def handle_channel_pins_update(self, gateway, payload):
        self.dispatch(events.RAW_CHANNEL_PINS_UPDATE, payload)

        channel_id = int(payload["channel_id"])
        channel_obj = self.state_registry.get_channel_by_id(channel_id)

        if channel_obj is not None:
            last_pin_timestamp = transform.nullable_cast(
                payload.get("last_pin_timestamp"), date_utils.parse_iso_8601_ts
            )

            if last_pin_timestamp is not None:
                if channel_obj.is_dm:
                    self.dispatch(events.DM_CHANNEL_PIN_ADDED, last_pin_timestamp)
                else:
                    self.dispatch(events.GUILD_CHANNEL_PIN_ADDED, last_pin_timestamp)
            else:
                if channel_obj.is_dm:
                    self.dispatch(events.DM_CHANNEL_PIN_REMOVED)
                else:
                    self.dispatch(events.GUILD_CHANNEL_PIN_REMOVED)
        else:
            self.logger.warning(
                "ignoring CHANNEL_PINS_UPDATE for %s channel %s which was not previously cached",
                "DM" if channel.is_channel_type_dm(payload["type"]) else "guild",
                channel_id,
            )

    async def handle_guild_create(self, gateway, payload):
        self.dispatch(events.RAW_GUILD_CREATE, payload)

        guild_id = int(payload["id"])
        unavailable = payload.get("unavailable", False)
        was_already_loaded = self.state_registry.get_guild_by_id(guild_id) is not None
        guild = self.state_registry.parse_guild(payload)

        if not was_already_loaded:
            self.dispatch(events.GUILD_CREATE, guild)

        if not unavailable:
            self.dispatch(events.GUILD_AVAILABLE, guild)

    async def handle_guild_update(self, gateway, payload):
        self.dispatch(events.RAW_GUILD_UPDATE, payload)

        guild_diff = self.state_registry.update_guild(payload)

        if guild_diff is not None:
            self.dispatch(events.GUILD_UPDATE, *guild_diff)
        else:
            self.state_registry.parse_guild(payload)
            self.logger.warning(
                "ignoring GUILD_UPDATE for unknown guild %s which was not previously cached - cache amended"
            )

    async def handle_guild_delete(self, gateway, payload):
        self.dispatch(events.RAW_GUILD_DELETE, payload)
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
            self.dispatch(events.GUILD_UNAVAILABLE, guild_obj)
        else:
            # We don't have a guild parsed yet. That shouldn't happen but if it does, we can make a note of this
            # so that we don't fail on other events later, and pre-emptively parse this information now.
            self.state_registry.parse_guild(payload)

    async def _handle_guild_leave(self, payload):
        guild = self.state_registry.parse_guild(payload)
        self.state_registry.delete_guild(guild.id)
        self.dispatch(events.GUILD_LEAVE, guild)

    async def handle_guild_ban_add(self, gateway, payload):
        self.dispatch(events.RAW_GUILD_BAN_ADD, payload)

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

            self.dispatch(events.GUILD_BAN_ADD, guild, member)
        else:
            self.logger.warning("ignoring GUILD_BAN_ADD for user %s in unknown guild %s", user.id, guild_id)

    async def handle_guild_ban_remove(self, gateway, payload):
        self.dispatch(events.RAW_GUILD_BAN_REMOVE, payload)

        guild_id = int(payload["guild_id"])
        guild = self.state_registry.get_guild_by_id(guild_id)
        user = self.state_registry.parse_user(payload["user"])
        if guild is not None:
            self.dispatch(events.GUILD_BAN_REMOVE, guild, user)
        else:
            self.logger.warning("ignoring GUILD_BAN_REMOVE for user %s in unknown guild %s", user.id, guild_id)

    async def handle_guild_emojis_update(self, gateway, payload):
        self.dispatch(events.RAW_GUILD_EMOJIS_UPDATE, payload)

        guild_id = int(payload["guild_id"])
        guild = self.state_registry.get_guild_by_id(guild_id)
        if guild is not None:
            old_emojis, new_emojis = self.state_registry.update_guild_emojis(payload, guild_id)
            self.dispatch(events.GUILD_EMOJIS_UPDATE, guild, old_emojis, new_emojis)
        else:
            self.logger.warning("ignoring GUILD_EMOJIS_UPDATE for unknown guild %s", guild_id)

    async def handle_guild_integrations_update(self, gateway, payload):
        self.dispatch(events.RAW_GUILD_INTEGRATIONS_UPDATE, payload)

        guild_id = int(payload["guild_id"])
        guild = self.state_registry.get_guild_by_id(guild_id)
        if guild is not None:
            self.dispatch(events.GUILD_INTEGRATIONS_UPDATE, guild)
        else:
            self.logger.warning("ignoring GUILD_INTEGRATIONS_UPDATE for unknown guild %s", guild_id)

    async def handle_guild_member_add(self, gateway, payload):
        self.dispatch(events.RAW_GUILD_MEMBER_ADD, payload)

        guild_id = int(payload.pop("guild_id"))
        guild = self.state_registry.get_guild_by_id(guild_id)
        if guild is not None:
            member = self.state_registry.parse_member(payload, guild_id)
            self.dispatch(events.GUILD_MEMBER_ADD, member)
        else:
            self.logger.warning("ignoring GUILD_MEMBER_ADD for unknown guild %s", guild_id)

    async def handle_guild_member_update(self, gateway, payload):
        self.dispatch(events.RAW_GUILD_MEMBER_UPDATE, payload)

        guild_id = int(payload["guild_id"])
        guild = self.state_registry.get_guild_by_id(guild_id)
        user_id = int(payload["user"]["id"])

        if guild is not None and user_id in guild.members:
            role_ids = payload["roles"]
            nick = payload["nick"]

            member_diff = self.state_registry.update_member(guild_id, role_ids, nick, user_id)
            if member_diff is not None:
                self.dispatch(events.GUILD_MEMBER_UPDATE, *member_diff)
            else:
                self.logger.warning("ignoring GUILD_MEMBER_UPDATE for unknown member %s in guild %s", user_id, guild_id)
                self.state_registry.parse_member(payload, guild_id)
        else:
            self.logger.warning("ignoring GUILD_MEMBER_UPDATE for unknown guild %s", guild_id)

    async def handle_guild_member_remove(self, gateway, payload):
        self.dispatch(events.RAW_GUILD_MEMBER_REMOVE, payload)

        user_id = int(payload["id"])
        guild_id = int(payload["guild_id"])
        member = self.state_registry.delete_member_from_guild(user_id, guild_id)
        self.dispatch(events.GUILD_MEMBER_REMOVE, member)

    async def handle_guild_members_chunk(self, gateway, payload):
        self.dispatch(events.RAW_GUILD_MEMBERS_CHUNK, payload)

        # TODO: implement this feature properly.
        self.logger.warning("Received GUILD_MEMBERS_CHUNK but that is not implemented yet")

    async def handle_guild_role_create(self, gateway, payload):
        self.dispatch(events.RAW_GUILD_ROLE_CREATE, payload)

        guild_id = int(payload["guild_id"])
        guild = self.state_registry.get_guild_by_id(guild_id)

        if guild is not None:
            role = self.state_registry.parse_role(payload["role"], guild_id)
            self.dispatch(events.GUILD_ROLE_CREATE, role)
        else:
            self.logger.warning("ignoring GUILD_ROLE_CREATE for unknown guild %s", guild_id)

    async def handle_guild_role_update(self, gateway, payload):
        self.dispatch(events.RAW_GUILD_ROLE_UPDATE, payload)

        guild_id = int(payload["guild_id"])
        guild = self.state_registry.get_guild_by_id(guild_id)

        if guild is not None:
            role_id = int(payload["role"]["id"])
            existing_role = guild.roles.get(role_id)
            if existing_role is not None:
                old_role = existing_role.copy()
                existing_role.update_state(payload["role"])
                new_role = existing_role
                self.dispatch(events.GUILD_ROLE_UPDATE, old_role, new_role)
            else:
                self.logger.warning("ignoring GUILD_ROLE_UPDATE for unknown role %s in guild %s", role_id, guild_id)
        else:
            self.logger.warning("ignoring GUILD_ROLE_UPDATE for unknown guild %s", guild_id)

    async def handle_guild_role_delete(self, gateway, payload):
        self.dispatch(events.RAW_GUILD_ROLE_DELETE, payload)

        guild_id = int(payload["guild_id"])
        role_id = int(payload["role_id"])
        guild = self.state_registry.get_guild_by_id(guild_id)

        if guild is not None:
            if role_id in guild.roles:
                role = self.state_registry.delete_role(guild_id, role_id)
                self.dispatch(events.GUILD_ROLE_DELETE, role)
            else:
                self.logger.warning("ignoring GUILD_ROLE_DELETE for unknown role %s in guild %s", role_id, guild_id)
        else:
            self.logger.warning("ignoring GUILD_ROLE_DELETE for role %s in unknown guild %s", role_id, guild_id)

    async def handle_message_create(self, gateway, payload):
        self.dispatch(events.RAW_MESSAGE_CREATE, payload)
        message = self.state_registry.parse_message(payload)
        if message.channel is not None:
            self.dispatch(events.MESSAGE_CREATE, message)
        else:
            channel_id = int(payload["channel_id"])
            self.logger.warning("ignoring MESSAGE_CREATE for message %s in unknown channel %s", message.id, channel_id)

    async def handle_message_update(self, gateway, payload):
        self.dispatch(events.RAW_MESSAGE_UPDATE, payload)
        diff = self.state_registry.update_message(payload)

        # Don't bother logging this, it will probably happen a lot, as this state occurs whenever a message not cached
        # gets edited. It is perfectly normal.
        if diff is not None:
            self.dispatch(events.MESSAGE_UPDATE, *diff)

    async def handle_message_delete(self, gateway, payload):
        self.dispatch(events.RAW_MESSAGE_DELETE, payload)

        try:
            message = self.state_registry.delete_message(int(payload["id"]))
            self.dispatch(events.MESSAGE_DELETE, message)
        except KeyError:
            # Will occur if the message was deleted without being in the cache. This is fine.
            pass

    async def handle_message_delete_bulk(self, gateway, payload):
        self.dispatch(events.RAW_MESSAGE_DELETE_BULK, payload)

        channel_id = int(payload["channel_id"])
        messages = (int(message_id) for message_id in payload["ids"])
        messages = {
            message_id: transform.try_cast(message_id, self.state_registry.delete_message, None)
            for message_id in messages
        }

        channel_obj = self.state_registry.get_channel_by_id(channel_id)
        if channel_obj is not None:
            self.dispatch(events.MESSAGE_DELETE_BULK, channel_obj, messages)
        else:
            self.logger.warning("ignoring MESSAGE_DELETE_BULK for unknown channel %s", channel_id)

    # This is a headache to do as it has a completely different layout to reactions elsewhere...
    async def handle_message_reaction_add(self, gateway, payload):
        self.dispatch(events.RAW_MESSAGE_REACTION_ADD, payload)
        guild_id = transform.nullable_cast(payload.get("guild_id"), int)
        message_id = int(payload["message_id"])
        user_id = int(payload["user_id"])
        message_obj = self.state_registry.get_message_by_id(message_id)

        if message_obj is None:
            # Message was not cached, so ignore
            return

        emoji_obj = self.state_registry.parse_emoji(payload["emoji"], None)

        reaction_obj = self.state_registry.add_reaction(message_obj, emoji_obj)

        if guild_id is not None:
            user_obj = self.state_registry.get_member_by_id(user_id, guild_id)
        else:
            user_obj = self.state_registry.get_user_by_id(user_id)

        if user_obj is not None:
            self.dispatch(events.MESSAGE_REACTION_ADD, reaction_obj, user_obj)

        else:
            self.logger.warning(
                "ignoring MESSAGE_REACTION_ADD for unknown %s %s",
                "user" if user_id is None else f"guild {guild_id} and member",
                user_id,
            )

    async def handle_message_reaction_remove(self, gateway, payload):
        self.dispatch(events.RAW_MESSAGE_REACTION_REMOVE, payload)
        guild_id = transform.nullable_cast(payload.get("guild_id"), int)
        message_id = int(payload["message_id"])
        user_id = int(payload["user_id"])
        message_obj = self.state_registry.get_message_by_id(message_id)

        if message_obj is None:
            # Message was not cached, so ignore
            return

        emoji_obj = self.state_registry.parse_emoji(payload["emoji"], None)

        reaction_obj = self.state_registry.remove_reaction(message_obj, emoji_obj)

        if guild_id is not None:
            user_obj = self.state_registry.get_member_by_id(user_id, guild_id)
        else:
            user_obj = self.state_registry.get_user_by_id(user_id)

        if user_obj is not None:
            self.dispatch(events.MESSAGE_REACTION_REMOVE, reaction_obj, user_obj)

        else:
            self.logger.warning(
                "ignoring MESSAGE_REACTION_REMOVE for unknown %s %s",
                "user" if user_id is None else f"guild {guild_id} and member",
                user_id,
            )

    async def handle_message_reaction_remove_all(self, gateway, payload):
        self.dispatch(events.RAW_MESSAGE_REACTION_REMOVE_ALL, payload)
        message_id = int(payload["message_id"])

        message_obj = self.state_registry.get_message_by_id(message_id)

        if message_obj is None:
            # Not cached, so ignore.
            return

        self.state_registry.remove_all_reactions(message_obj)
        self.dispatch(events.MESSAGE_REACTION_REMOVE_ALL, message_obj)

    async def handle_presence_update(self, gateway, payload):
        self.dispatch(events.RAW_MEMBER_PRESENCE_UPDATE, payload)

        guild_id = int(payload["guild_id"])
        guild = self.state_registry.get_guild_by_id(guild_id)

        if guild is None:
            self.logger.warning("ignoring PRESENCE_UPDATE for unknown guild %s", guild_id)
            return

        user_id = int(payload["user"]["id"])
        user = self.state_registry.get_user_by_id(user_id)
        if user is None:
            self.logger.warning("ignoring PRESENCE_UPDATE for unknown user %s in guild %s", user_id, guild_id)
            return

        member = self.state_registry.get_member_by_id(user_id, guild_id)
        if member is None:
            self.logger.warning("ignoring PRESENCE_UPDATE for unknown member %s in guild %s", user_id, guild_id)
            return

        presence_obj = self.state_registry.parse_presence(guild_id, user_id, payload)

        role_ids = (int(role_id) for role_id in payload["roles"])
        roles = []
        for role_id in role_ids:
            next_role = self.state_registry.get_role_by_id(guild_id, role_id)
            if next_role is None:
                self.logger.warning(
                    "ignoring unknown role %s being added to user %s in guild %s silently",
                    role_id,
                    user_id,
                    guild_id
                )
            else:
                roles.append(role_id)

        self.state_registry.update

        self.dispatch(events.MEMBER_PRESENCE_UPDATE, presence_obj)

    async def handle_typing_start(self, gateway, payload):
        self.dispatch(events.RAW_TYPING_START, payload)
        channel_id = int(payload["channel_id"])
        user_id = int(payload["user_id"])
        channel_obj = self.state_registry.get_channel_by_id(channel_id)

        if channel_obj is None:
            self.logger.warning("ignoring TYPING_START by user %s in unknown channel %s", user_id, channel_id)
            return

        user_obj = self.state_registry.get_user_by_id(user_id)
        if user_obj is None:
            self.logger.warning("ignoring TYPING_START by unknown user %s in channel %s", user_id, channel_id)

        self.dispatch(events.TYPING_START, user_obj, channel_obj)

    async def handle_user_update(self, gateway, payload):
        self.dispatch(events.RAW_USER_UPDATE, payload)
        user_obj = self.state_registry.parse_user(payload)
        self.dispatch(events.USER_UPDATE, user_obj)

    async def handle_voice_state_update(self, gateway, payload):
        self.dispatch(events.RAW_VOICE_STATE_UPDATE, payload)
        # Todo: implement voice.

    async def handle_voice_server_update(self, gateway, payload):
        self.dispatch(events.RAW_VOICE_SERVER_UPDATE, payload)
        # Todo: implement voice.

    async def handle_webhooks_update(self, gateway, payload):
        self.dispatch(events.RAW_WEBHOOKS_UPDATE, payload)
        channel_id = int(payload["channel_id"])

        channel_obj = self.state_registry.get_channel_by_id(channel_id)

        if channel_obj is None:
            self.logger.warning("ignoring WEBHOOKS_UPDATE in unknown channel %s", channel_id)
        else:
            self.dispatch(events.WEBHOOKS_UPDATE, channel_obj)
