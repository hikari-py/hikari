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

from hikari.internal_utilities import date_helpers
from hikari.internal_utilities import transformations
from hikari.orm import dispatching_event_adapter
from hikari.orm import events
from hikari.orm import fabric as _fabric
from hikari.orm.models import channels


class DispatchingEventAdapterImpl(dispatching_event_adapter.DispatchingEventAdapter):
    """
    Basic implementation of event management logic for single-application bots.

    This handles parsing incoming events from Discord and translating the JSON objects
    and arrays provided into meaningful objects with respect to this ORM. Events as
    defined in the :mod:`hikari.orm.events` module are then dispatched to the given
    dispatcher function.

    Args:
        fabric_obj:
            The ORM fabric to use.
        dispatch:
            The callable to dispatch every event to once adapted to an object in the object
            graph.
    """

    __slots__ = ("dispatch", "_ignored_events")

    def __init__(self, fabric_obj: _fabric.Fabric, dispatch: typing.Callable[..., None]) -> None:
        super().__init__(fabric_obj)
        self.dispatch = dispatch
        self._ignored_events = set()

    async def drain_unrecognised_event(self, _, event_name, payload):
        self.dispatch("raw_" + event_name.lower(), payload)
        if event_name not in self._ignored_events:
            self.logger.warning("Received unrecognised event %s, so will ignore it in the future.", event_name)
            self._ignored_events.add(event_name)

    async def handle_disconnect(self, gateway, payload):
        self.dispatch(events.DISCONNECT, gateway, payload.get("code"), payload.get("reason"))

    async def handle_connect(self, gateway, _):
        self.dispatch(events.CONNECT, gateway)

    async def handle_invalid_session(self, gateway, payload: bool):
        self.dispatch(events.INVALID_SESSION, gateway, payload)

    async def handle_reconnect(self, gateway, _):
        self.dispatch(events.RECONNECT, gateway)

    async def handle_resumed(self, gateway, _):
        self.dispatch(events.RESUMED, gateway)

    async def handle_channel_create(self, _, payload):
        self.dispatch(events.RAW_CHANNEL_CREATE, payload)

        guild_id = transformations.nullable_cast(payload.get("guild_id"), int)
        if guild_id is not None:
            guild_obj = self.fabric.state_registry.get_guild_by_id(guild_id)
            if guild_obj is None:
                self.logger.warning("ignoring received CHANNEL_CREATE for channel in unknown guild %s", guild_id)
                return
        else:
            guild_obj = None

        channel_obj = self.fabric.state_registry.parse_channel(payload, guild_obj)

        if channel_obj.is_dm:
            self.dispatch(events.DM_CHANNEL_CREATE, channel_obj)
        else:
            self.dispatch(events.GUILD_CHANNEL_CREATE, channel_obj)

    async def handle_channel_update(self, _, payload):
        self.dispatch(events.RAW_CHANNEL_UPDATE, payload)

        channel_id = int(payload["id"])
        channel_diff = self.fabric.state_registry.update_channel(payload)

        if channel_diff is not None:
            is_dm = channels.is_channel_type_dm(payload["type"])
            event = events.DM_CHANNEL_UPDATE if is_dm else events.GUILD_CHANNEL_UPDATE
            self.dispatch(event, *channel_diff)
        else:
            self.logger.warning("ignoring received CHANNEL_UPDATE for unknown channel %s", channel_id)

    async def handle_channel_delete(self, _, payload):
        # Update the channel meta data just for this call.
        self.dispatch(events.RAW_CHANNEL_DELETE, payload)

        guild_id = transformations.nullable_cast(payload.get("guild_id"), int)
        if guild_id is not None:
            guild_obj = self.fabric.state_registry.get_guild_by_id(guild_id)
            if guild_obj is None:
                self.logger.warning("ignoring received CHANNEL_DELETE for channel in unknown guild %s", guild_id)
                return
        else:
            guild_obj = None

        channel_obj = self.fabric.state_registry.parse_channel(payload, guild_obj)
        event = events.DM_CHANNEL_DELETE if channel_obj.is_dm else events.GUILD_CHANNEL_DELETE
        self.dispatch(event, channel_obj)

    async def handle_channel_pins_update(self, _, payload):
        self.dispatch(events.RAW_CHANNEL_PINS_UPDATE, payload)

        channel_id = int(payload["channel_id"])
        channel_obj: typing.Optional[channels.Channel] = self.fabric.state_registry.get_channel_by_id(channel_id)

        if channel_obj is not None:
            channel_obj: channels.TextChannel

            last_pin_timestamp = transformations.nullable_cast(
                payload.get("last_pin_timestamp"), date_helpers.parse_iso_8601_ts
            )

            self.fabric.state_registry.set_last_pinned_timestamp(channel_obj, last_pin_timestamp)

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
                "DM" if channels.is_channel_type_dm(payload["type"]) else "guild",
                channel_id,
            )

    async def handle_guild_create(self, _, payload):
        self.dispatch(events.RAW_GUILD_CREATE, payload)

        guild_id = int(payload["id"])
        unavailable = payload.get("unavailable", False)
        was_already_loaded = self.fabric.state_registry.get_guild_by_id(guild_id) is not None
        guild = self.fabric.state_registry.parse_guild(payload)

        if not was_already_loaded:
            self.dispatch(events.GUILD_CREATE, guild)

        if not unavailable:
            self.dispatch(events.GUILD_AVAILABLE, guild)

    async def handle_guild_update(self, _, payload):
        self.dispatch(events.RAW_GUILD_UPDATE, payload)

        guild_diff = self.fabric.state_registry.update_guild(payload)

        if guild_diff is not None:
            self.dispatch(events.GUILD_UPDATE, *guild_diff)
        else:
            self.logger.warning("ignoring GUILD_UPDATE for unknown guild %s which was not previously cached")

    async def handle_guild_delete(self, _, payload):
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
        guild_obj = self.fabric.state_registry.get_guild_by_id(guild_id)

        if guild_obj is not None:
            self.fabric.state_registry.set_guild_unavailability(guild_obj, True)
            self.dispatch(events.GUILD_UNAVAILABLE, guild_obj)
        else:
            # We don't have a guild parsed yet. That shouldn't happen but if it does, we can make a note of this
            # so that we don't fail on other events later, and pre-emptively parse this information now.
            self.fabric.state_registry.parse_guild(payload)

    async def _handle_guild_leave(self, payload):
        guild = self.fabric.state_registry.parse_guild(payload)
        self.fabric.state_registry.delete_guild(guild)
        self.dispatch(events.GUILD_LEAVE, guild)

    async def handle_guild_ban_add(self, _, payload):
        self.dispatch(events.RAW_GUILD_BAN_ADD, payload)

        guild_id = int(payload["guild_id"])
        guild = self.fabric.state_registry.get_guild_by_id(guild_id)
        user = self.fabric.state_registry.parse_user(payload["user"])
        if guild is not None:

            # The user may or may not be cached, if the guild is large. So, we may have to just pass a normal user, or
            # if we can, we can pass a whole member. The member should be assumed to be normal behaviour unless caching
            # of members was disabled, or if Discord is screwing up; regardless, it is probably worth checking this
            # information first. Since they just got banned, we can't even look this information up anymore...
            # Perhaps the audit logs could be checked, but this seems like an overkill, honestly...
            if user.id in guild.members:
                user = guild.members[user.id]
            self.dispatch(events.GUILD_BAN_ADD, guild, user)
        else:
            self.logger.warning("ignoring GUILD_BAN_ADD for user %s in unknown guild %s", user.id, guild_id)

    async def handle_guild_ban_remove(self, _, payload):
        self.dispatch(events.RAW_GUILD_BAN_REMOVE, payload)

        guild_id = int(payload["guild_id"])
        guild = self.fabric.state_registry.get_guild_by_id(guild_id)
        user = self.fabric.state_registry.parse_user(payload["user"])
        if guild is not None:
            self.dispatch(events.GUILD_BAN_REMOVE, guild, user)
        else:
            self.logger.warning("ignoring GUILD_BAN_REMOVE for user %s in unknown guild %s", user.id, guild_id)

    async def handle_guild_emojis_update(self, _, payload):
        self.dispatch(events.RAW_GUILD_EMOJIS_UPDATE, payload)

        guild_id = int(payload["guild_id"])
        guild_obj = self.fabric.state_registry.get_guild_by_id(guild_id)
        if guild_obj is not None:
            diff = self.fabric.state_registry.update_guild_emojis(payload["emojis"], guild_obj)
            self.dispatch(events.GUILD_EMOJIS_UPDATE, guild_obj, *diff)
        else:
            self.logger.warning("ignoring GUILD_EMOJIS_UPDATE for unknown guild %s", guild_id)

    async def handle_guild_integrations_update(self, _, payload):
        self.dispatch(events.RAW_GUILD_INTEGRATIONS_UPDATE, payload)

        guild_id = int(payload["guild_id"])
        guild = self.fabric.state_registry.get_guild_by_id(guild_id)
        if guild is not None:
            self.dispatch(events.GUILD_INTEGRATIONS_UPDATE, guild)
        else:
            self.logger.warning("ignoring GUILD_INTEGRATIONS_UPDATE for unknown guild %s", guild_id)

    async def handle_guild_member_add(self, _, payload):
        self.dispatch(events.RAW_GUILD_MEMBER_ADD, payload)

        guild_id = int(payload.pop("guild_id"))
        guild_obj = self.fabric.state_registry.get_guild_by_id(guild_id)
        if guild_obj is not None:
            member = self.fabric.state_registry.parse_member(payload, guild_obj)
            self.dispatch(events.GUILD_MEMBER_ADD, member)
        else:
            self.logger.warning("ignoring GUILD_MEMBER_ADD for unknown guild %s", guild_id)

    async def handle_guild_member_update(self, gateway, payload):
        self.dispatch(events.RAW_GUILD_MEMBER_UPDATE, payload)

        guild_id = int(payload["guild_id"])
        guild_obj = self.fabric.state_registry.get_guild_by_id(guild_id)
        user_id = int(payload["user"]["id"])

        if guild_obj is not None and user_id in guild_obj.members:
            member_obj = guild_obj.members[user_id]

            role_ids = payload["roles"]
            role_objs = []

            for role_id in role_ids:
                role_obj = self.fabric.state_registry.get_role_by_id(guild_id, role_id)
                if role_obj is not None:
                    role_objs.append(role_obj)
                else:
                    self.logger.warning(
                        "ignoring unknown role %s in GUILD_MEMBER_UPDATE for member %s in guild %s",
                        role_id,
                        user_id,
                        guild_id,
                    )

            nick = payload["nick"]
            member_diff = self.fabric.state_registry.update_member(member_obj, role_objs, nick)
            self.dispatch(events.GUILD_MEMBER_UPDATE, *member_diff)
        else:
            self.logger.warning("ignoring GUILD_MEMBER_UPDATE for unknown guild %s", guild_id)

    async def handle_guild_member_remove(self, gateway, payload):
        self.dispatch(events.RAW_GUILD_MEMBER_REMOVE, payload)

        user_id = int(payload["user"]["id"])
        guild_id = int(payload["guild_id"])
        member_obj = self.fabric.state_registry.get_member_by_id(user_id, guild_id)

        if member_obj is not None:
            self.fabric.state_registry.delete_member(member_obj)
            self.dispatch(events.GUILD_MEMBER_REMOVE, member_obj)
        else:
            self.logger.warning("ignoring GUILD_MEMBER_REMOVE for unknown member %s in guild %s", user_id, guild_id)

    async def handle_guild_members_chunk(self, gateway, payload):
        self.dispatch(events.RAW_GUILD_MEMBERS_CHUNK, payload)

        # TODO: implement this feature properly.
        self.logger.warning("received GUILD_MEMBERS_CHUNK but that is not implemented yet")

    async def handle_guild_role_create(self, gateway, payload):
        self.dispatch(events.RAW_GUILD_ROLE_CREATE, payload)

        guild_id = int(payload["guild_id"])
        guild_obj = self.fabric.state_registry.get_guild_by_id(guild_id)

        if guild_obj is not None:
            role = self.fabric.state_registry.parse_role(payload["role"], guild_obj)
            self.dispatch(events.GUILD_ROLE_CREATE, role)
        else:
            self.logger.warning("ignoring GUILD_ROLE_CREATE for unknown guild %s", guild_id)

    async def handle_guild_role_update(self, gateway, payload):
        self.dispatch(events.RAW_GUILD_ROLE_UPDATE, payload)

        guild_id = int(payload["guild_id"])
        guild_obj = self.fabric.state_registry.get_guild_by_id(guild_id)

        if guild_obj is not None:
            diff = self.fabric.state_registry.update_role(guild_obj, payload["role"])

            if diff is not None:
                self.dispatch(events.GUILD_ROLE_UPDATE, *diff)
            else:
                role_id = int(payload["role"]["id"])
                self.logger.warning("ignoring GUILD_ROLE_UPDATE for unknown role %s in guild %s", role_id, guild_id)
        else:
            self.logger.warning("ignoring GUILD_ROLE_UPDATE for unknown guild %s", guild_id)

    async def handle_guild_role_delete(self, gateway, payload):
        self.dispatch(events.RAW_GUILD_ROLE_DELETE, payload)

        guild_id = int(payload["guild_id"])
        role_id = int(payload["role_id"])
        guild = self.fabric.state_registry.get_guild_by_id(guild_id)

        if guild is not None:
            if role_id in guild.roles:
                role_obj = guild.roles[role_id]
                self.fabric.state_registry.delete_role(role_obj)
                self.dispatch(events.GUILD_ROLE_DELETE, role_obj)
            else:
                self.logger.warning("ignoring GUILD_ROLE_DELETE for unknown role %s in guild %s", role_id, guild_id)
        else:
            self.logger.warning("ignoring GUILD_ROLE_DELETE for role %s in unknown guild %s", role_id, guild_id)

    async def handle_message_create(self, gateway, payload):
        self.dispatch(events.RAW_MESSAGE_CREATE, payload)
        message = self.fabric.state_registry.parse_message(payload)
        if message is not None:
            self.dispatch(events.MESSAGE_CREATE, message)
        else:
            message_id = int(payload["id"])
            channel_id = int(payload["channel_id"])
            self.logger.warning("ignoring MESSAGE_CREATE for message %s in unknown channel %s", message_id, channel_id)

    async def handle_message_update(self, gateway, payload):
        self.dispatch(events.RAW_MESSAGE_UPDATE, payload)
        diff = self.fabric.state_registry.update_message(payload)

        # Don't bother logging this, it will probably happen a lot, as this state occurs whenever a message not cached
        # gets edited. It is perfectly normal.
        if diff is not None:
            self.dispatch(events.MESSAGE_UPDATE, *diff)

    async def handle_message_delete(self, gateway, payload):
        self.dispatch(events.RAW_MESSAGE_DELETE, payload)

        message_id = int(payload["id"])
        message_obj = self.fabric.state_registry.get_message_by_id(message_id)

        if message_obj is not None:
            self.fabric.state_registry.delete_message(message_obj)
            self.dispatch(events.MESSAGE_DELETE, message_obj)
        # If this does not fire, we can just ignore it, as it just means the message is no longer cached.

    async def handle_message_delete_bulk(self, gateway, payload):
        self.dispatch(events.RAW_MESSAGE_DELETE_BULK, payload)

        channel_id = int(payload["channel_id"])
        messages = (int(message_id) for message_id in payload["ids"])
        messages = {
            message_id: transformations.try_cast(message_id, self.fabric.state_registry.delete_message, None)
            for message_id in messages
        }

        channel_obj = self.fabric.state_registry.get_channel_by_id(channel_id)
        if channel_obj is not None:
            self.dispatch(events.MESSAGE_DELETE_BULK, channel_obj, messages)
        else:
            self.logger.warning("ignoring MESSAGE_DELETE_BULK for unknown channel %s", channel_id)

    # This is a headache to do as it has a completely different layout to reactions elsewhere...
    async def handle_message_reaction_add(self, gateway, payload):
        self.dispatch(events.RAW_MESSAGE_REACTION_ADD, payload)
        guild_id = transformations.nullable_cast(payload.get("guild_id"), int)
        message_id = int(payload["message_id"])
        user_id = int(payload["user_id"])
        message_obj = self.fabric.state_registry.get_message_by_id(message_id)
        guild_obj = self.fabric.state_registry.get_guild_by_id(guild_id)

        if message_obj is None:
            # Message was not cached, so ignore
            return

        emoji_obj = self.fabric.state_registry.parse_emoji(payload["emoji"], guild_obj)
        reaction_obj = self.fabric.state_registry.increment_reaction_count(message_obj, emoji_obj)

        if guild_id is not None:
            user_obj = self.fabric.state_registry.get_member_by_id(user_id, guild_id)
        else:
            user_obj = self.fabric.state_registry.get_user_by_id(user_id)

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
        guild_id = transformations.nullable_cast(payload.get("guild_id"), int)
        message_id = int(payload["message_id"])
        user_id = int(payload["user_id"])
        message_obj = self.fabric.state_registry.get_message_by_id(message_id)

        if message_obj is None:
            # Message was not cached, so ignore
            return

        if guild_id is not None:
            user_obj = self.fabric.state_registry.get_member_by_id(user_id, guild_id)
        else:
            user_obj = self.fabric.state_registry.get_user_by_id(user_id)

        emoji_obj = self.fabric.state_registry.parse_emoji(payload["emoji"], None)
        reaction_obj = self.fabric.state_registry.decrement_reaction_count(message_obj, emoji_obj)

        if reaction_obj is None:
            self.logger.warning(
                "ignoring MESSAGE_REACTION_REMOVE for non existent reaction %s on message %s by %s %s",
                reaction_obj,
                message_id,
                "user" if user_id is None else f"guild {guild_id} and member",
                user_id,
            )
            return

        if user_obj is None:
            self.logger.warning(
                "ignoring MESSAGE_REACTION_REMOVE for reaction %s on message %s for unknown %s %s",
                reaction_obj,
                message_id,
                "user" if user_id is None else f"guild {guild_id} and member",
                user_id,
            )

        self.dispatch(events.MESSAGE_REACTION_REMOVE, reaction_obj, user_obj)

    async def handle_message_reaction_remove_all(self, gateway, payload):
        self.dispatch(events.RAW_MESSAGE_REACTION_REMOVE_ALL, payload)
        message_id = int(payload["message_id"])

        message_obj = self.fabric.state_registry.get_message_by_id(message_id)

        if message_obj is None:
            # Not cached, so ignore.
            return

        self.fabric.state_registry.delete_all_reactions(message_obj)
        self.dispatch(events.MESSAGE_REACTION_REMOVE_ALL, message_obj)

    async def handle_presence_update(self, gateway, payload):
        self.dispatch(events.RAW_PRESENCE_UPDATE, payload)

        guild_id = int(payload["guild_id"])
        guild_obj = self.fabric.state_registry.get_guild_by_id(guild_id)

        if guild_obj is None:
            self.logger.warning("ignoring PRESENCE_UPDATE for unknown guild %s", guild_id)
            return

        user_id = int(payload["user"]["id"])
        user_obj = self.fabric.state_registry.get_user_by_id(user_id)
        if user_obj is None:
            self.logger.warning("ignoring PRESENCE_UPDATE for unknown user %s in guild %s", user_id, guild_id)
            return

        member_obj = self.fabric.state_registry.get_member_by_id(user_id, guild_id)
        if member_obj is None:
            self.logger.warning("ignoring PRESENCE_UPDATE for unknown member %s in guild %s", user_id, guild_id)
            return

        presence_diff = self.fabric.state_registry.update_member_presence(member_obj, payload)

        role_ids = (int(role_id) for role_id in payload["roles"])
        role_objs = []
        for role_id in role_ids:
            next_role = self.fabric.state_registry.get_role_by_id(guild_id, role_id)
            if next_role is None:
                self.logger.warning(
                    "ignoring unknown role %s being added to user %s in guild %s silently", role_id, user_id, guild_id
                )
            else:
                role_objs.append(next_role)

        self.fabric.state_registry.set_roles_for_member(role_objs, member_obj)

        self.dispatch(events.PRESENCE_UPDATE, *presence_diff)

    async def handle_typing_start(self, gateway, payload):
        self.dispatch(events.RAW_TYPING_START, payload)
        channel_id = int(payload["channel_id"])
        user_id = int(payload["user_id"])
        channel_obj = self.fabric.state_registry.get_channel_by_id(channel_id)

        if channel_obj is None:
            self.logger.warning("ignoring TYPING_START by user %s in unknown channel %s", user_id, channel_id)
            return

        if channel_obj.is_dm:
            user_obj = self.fabric.state_registry.get_user_by_id(user_id)
        else:
            user_obj = channel_obj.guild.members.get(user_id)

        if user_obj is None:
            self.logger.warning("ignoring TYPING_START by unknown user %s in channel %s", user_id, channel_id)

        self.dispatch(events.TYPING_START, user_obj, channel_obj)

    async def handle_user_update(self, gateway, payload):
        self.dispatch(events.RAW_USER_UPDATE, payload)
        user_obj = self.fabric.state_registry.parse_user(payload)
        self.dispatch(events.USER_UPDATE, user_obj)

    async def handle_voice_state_update(self, gateway, payload):
        self.dispatch(events.RAW_VOICE_STATE_UPDATE, payload)
        # TODO: implement voice.
        self.logger.warning("received VOICE_STATE_UPDATE but that is not implemented yet")

    async def handle_voice_server_update(self, gateway, payload):
        self.dispatch(events.RAW_VOICE_SERVER_UPDATE, payload)
        # TODO: implement voice.
        self.logger.warning("received VOICE_SERVER_UPDATE but that is not implemented yet")

    async def handle_webhooks_update(self, gateway, payload):
        self.dispatch(events.RAW_WEBHOOKS_UPDATE, payload)
        channel_id = int(payload["channel_id"])

        channel_obj = self.fabric.state_registry.get_channel_by_id(channel_id)

        if channel_obj is None:
            self.logger.warning("ignoring WEBHOOKS_UPDATE in unknown channel %s", channel_id)
        else:
            self.dispatch(events.WEBHOOKS_UPDATE, channel_obj)
