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

import typing

from hikari.core.model import channel
from hikari.core.model import user as _user
from hikari.core.state import cache as _cache
from hikari.core.utils import delegate


@delegate.delegate_members(_cache.InMemoryCache, "cache")
class State(_cache.InMemoryCache):
    """
    A delegate class to an in-memory cache. This takes on the additional responsibility of orchestrating updates to the
    cache when they are received via websockets or the gateway.

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

    async def handle_hello(self, payload):
        self.dispatch("hello")

    async def handle_ready(self, payload):
        user = payload["user"]
        guilds = payload["guilds"]

        self.user = _user.BotUser.from_dict(self.cache, user)

        for guild in guilds:
            self.cache.parse_guild(guild)

        self.dispatch("ready")

    async def handle_resumed(self, payload):
        self.dispatch("resumed")

    async def handle_channel_create(self, payload):
        self.dispatch("channel_create", self.cache.parse_channel(payload))

    async def handle_channel_update(self, payload):
        new_channel = self.cache.parse_channel(payload)
        self.dispatch("channel_create")

    async def handle_channel_delete(self, payload):
        self.dispatch("channel_delete", ...)

    async def handle_channel_pins_update(self, payload):
        self.dispatch("channel_pins_update", ...)

    async def handle_guild_create(self, payload):
        self.dispatch("guild_create", ...)

    async def handle_guild_update(self, payload):
        self.dispatch("guild_update", ...)

    async def handle_guild_delete(self, payload):
        self.dispatch("guild_delete", ...)

    async def handle_guild_ban_add(self, payload):
        self.dispatch("guild_ban_add", ...)

    async def handle_guild_ban_remove(self, payload):
        self.dispatch("guild_ban_remove", ...)

    async def handle_guild_emojis_update(self, payload):
        self.dispatch("guild_emojis_update", ...)

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

    async def handle_voice_state_update(self, _):
        # self.dispatch("voice_state_update", ...)
        return NotImplemented

    async def handle_voice_server_update(self, _):
        # self.dispatch("voice_server_update", ...)
        return NotImplemented

    async def handle_webhooks_update(self, payload):
        self.dispatch("webhooks_update", ...)
