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
Abstract definition of an event handler.
"""
import abc
import asyncio

from hikari.core.utils import types


class EventAdapter(abc.ABC):
    """
    Abstract definition of an event handler. This automatically implements an underlying handler for every documented
    event that Discord can dispatch to us that performs no operation, so unimplemented events in subclasses go ignored
    silently.

    A couple of additional events are defined that can be produced by the gateway implementation for Hikari.
    """

    async def consume_raw_event(self, gateway, event_name: str, payload: types.DiscordObject) -> None:
        try:
            handler = getattr(self, f"handle_{event_name.lower()}")
        except AttributeError:
            pass
        else:
            asyncio.create_task(handler(gateway, payload))

    async def handle_disconnect(self, gateway, payload):
        ...

    async def handle_request_to_reconnect(self, gateway, payload):
        ...

    async def handle_hello(self, gateway, payload):
        ...

    async def handle_ready(self, gateway, payload):
        ...

    async def handle_resumed(self, gateway, payload):
        ...

    async def handle_invalid_session(self, gateway, payload):
        ...

    async def handle_channel_create(self, gateway, payload):
        ...

    async def handle_channel_update(self, gateway, payload):
        ...

    async def handle_channel_delete(self, gateway, payload):
        ...

    async def handle_channel_pins_update(self, gateway, payload):
        ...

    async def handle_guild_create(self, gateway, payload):
        ...

    async def handle_guild_update(self, gateway, payload):
        ...

    async def handle_guild_delete(self, gateway, payload):
        ...

    async def handle_guild_ban_add(self, gateway, payload):
        ...

    async def handle_guild_ban_remove(self, gateway, payload):
        ...

    async def handle_guild_emojis_update(self, gateway, payload):
        ...

    async def handle_guild_integrations_update(self, gateway, payload):
        ...

    async def handle_guild_member_add(self, gateway, payload):
        ...

    async def handle_guild_member_remove(self, gateway, payload):
        ...

    async def handle_guild_members_chunk(self, gateway, payload):
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
