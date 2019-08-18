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
Provides gateway integration.
"""
import logging

from hikari.core.state import cache as _cache


class State:
    def __init__(self, cache: _cache.InMemoryCache, dispatch):
        self.logger = logging.getLogger(__name__)
        self.cache = cache
        self.dispatch = dispatch

    async def consume_raw_event(self, event_name, payload):
        try:
            handler = getattr(self, f"on_{event_name.lower()}")
            self.logger.debug(f"Handling %s event", event_name)
            await handler(payload)
        except AttributeError:
            self.logger.warning("No transformation for %s exists, so the event is being ignored", event_name)

    async def on_hello(self, payload):
        self.dispatch("hello", ...)

    async def on_ready(self, payload):
        self.dispatch("ready", ...)

    async def on_resumed(self, payload):
        self.dispatch("resumed", ...)

    async def on_invalid_session(self, payload):
        self.dispatch("invalid_session", ...)

    async def on_channel_create(self, payload):
        self.dispatch("channel_create", ...)

    async def on_channel_update(self, payload):
        self.dispatch("channel_update ", ...)

    async def on_channel_delete(self, payload):
        self.dispatch("channel_delete", ...)

    async def on_channel_pins_update(self, payload):
        self.dispatch("channel_pins_update", ...)

    async def on_guild_create(self, payload):
        self.dispatch("guild_create", ...)

    async def on_guild_update(self, payload):
        self.dispatch("guild_update", ...)

    async def on_guild_delete(self, payload):
        self.dispatch("guild_delete", ...)

    async def on_guild_ban_add(self, payload):
        self.dispatch("guild_ban_add", ...)

    async def on_guild_ban_remove(self, payload):
        self.dispatch("guild_ban_remove", ...)

    async def on_guild_emojis_update(self, payload):
        self.dispatch("guild_emojis_update", ...)

    async def on_guild_integrations_update(self, payload):
        self.dispatch("guild_integrations_update", ...)

    async def on_guild_member_add(self, payload):
        self.dispatch("guild_member_add", ...)

    async def on_guild_member_remove(self, payload):
        self.dispatch("guild_member_remove", ...)

    async def on_guild_member_update(self, payload):
        self.dispatch("guild_member_update", ...)

    async def on_guild_members_chunk(self, payload):
        self.dispatch("guild_members_chunk", ...)

    async def on_guild_role_create(self, payload):
        self.dispatch("guild_role_create", ...)

    async def on_guild_role_update(self, payload):
        self.dispatch("guild_role_update", ...)

    async def on_guild_role_delete(self, payload):
        self.dispatch("guild_role_delete", ...)

    async def on_message_create(self, payload):
        self.dispatch("message_create", ...)

    async def on_message_update(self, payload):
        self.dispatch("message_update", ...)

    async def on_message_delete(self, payload):
        self.dispatch("message_delete", ...)

    async def on_message_delete_bulk(self, payload):
        self.dispatch("message_delete_bulk", ...)

    async def on_message_reaction_add(self, payload):
        self.dispatch("message_reaction_add", ...)

    async def on_message_reaction_remove(self, payload):
        self.dispatch("message_reaction_remove", ...)

    async def on_message_reaction_remove_all(self, payload):
        self.dispatch("message_reaction_remove_all", ...)

    async def on_presence_update(self, payload):
        self.dispatch("presence_update", ...)

    async def on_typing_start(self, payload):
        self.dispatch("typing_start", ...)

    async def on_user_update(self, payload):
        self.dispatch("user_update", ...)

    async def on_voice_state_update(self, payload):
        self.dispatch("voice_state_update", ...)

    async def on_voice_server_update(self, payload):
        self.dispatch("voice_server_update", ...)

    async def on_webhooks_update(self, payload):
        self.dispatch("webhooks_update", ...)
