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
import asyncio

from hikari.core.utils import custom_types
from hikari.core.utils import logging_utils


class EventAdapter:
    """
    Stubbed definition of an event handler. This automatically implements an underlying handler for every documented
    event that Discord can dispatch to us that performs no operation, so unimplemented events in subclasses go ignored
    silently.

    A couple of additional events are defined that can be produced by the gateway implementation for Hikari.
    """

    def __init__(self):
        self.logger = logging_utils.get_named_logger(self)

    async def consume_raw_event(self, gateway, event_name: str, payload: custom_types.DiscordObject) -> None:
        try:
            handler = getattr(self, f"handle_{event_name.lower()}")
            asyncio.create_task(handler(gateway, payload))
        except AttributeError:
            asyncio.create_task(self.handle_unrecognised_event(gateway, event_name, payload))

    async def handle_disconnect(self, gateway, payload):
        ...

    async def handle_request_to_reconnect(self, gateway, payload):
        ...

    async def handle_connect(self, gateway, payload):
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

    async def handle_guild_member_update(self, gateway, payload):
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

    async def handle_presences_replace(self, gateway, payload):
        # This should not be implemented, as it is for users only and is not documented. This exists to allow us to
        # ignore it silently rather than producing spam.
        ...

    async def handle_unrecognised_event(self, gateway, event_name, payload):
        ...
