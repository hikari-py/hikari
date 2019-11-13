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

import typing

from hikari.net import gateway
from hikari.internal_utilities import data_structures
from hikari.internal_utilities import logging_helpers


class BaseEventHandler(abc.ABC):
    """
    An abstract interface for an event handler.

    The purpose of this is to provide a single unified interface that any type and shape of event
    handler can implement and automatically be compatible with the rest of Hikari's infrastructure.

    This library provides a :class:`DispatchingEventAdapter` subinterface that is implemented to
    provide capability for single-process bots, but one may choose to extend this in a different
    way to store event payloads on a message queue such as RabbitMQ, ActiveMQ, IBM MQ, etc. This
    would allow a distributed bot to be designed to the user's specific use case, and allows Hikari
    to become much more expandable and flexible for large bots in the future.
    """

    __slots__ = ()

    @abc.abstractmethod
    def consume_raw_event(self, shard: gateway.GatewayClientV7, event_name: str, payload: typing.Any,) -> None:
        """
        This is invoked by a gateway client instance whenever an event of any type occurs. These are
        defined in :mod:`hikari.events` for convenience and documentation purposes.

        This is a standard method that is expected to handle the given event information in some way.
        How it does this depends on what the implementation is expected to do, but a general pattern
        that will be followed will be to invoke another method elsewhere or schedule an awaitable
        on the running event loop.

        Args:
            shard:
                The gateway client that provided this event.
            event_name:
                The raw event name. See :mod:`hikari.events`.
            payload:
                The raw payload. This will be potentially any form of information and will vary between
                events.
        """


class DispatchingEventAdapter(abc.ABC):
    """
    Stubbed definition of an event handler. This automatically implements an underlying handler for every documented
    event that Discord can dispatch to us that performs no operation, so unimplemented events in subclasses go ignored
    silently.

    A couple of additional events are defined that can be produced by the gateway implementation for Hikari.
    """

    __slots__ = ("logger",)

    @abc.abstractmethod
    def __init__(self) -> None:
        self.logger = logging_helpers.get_named_logger(self)

    async def consume_raw_event(self, shard, event_name: str, payload: typing.Any) -> None:
        try:
            handler = getattr(self, f"handle_{event_name.lower()}")
            await handler(shard, payload)
        except AttributeError:
            await self.drain_unrecognised_event(shard, event_name, payload)

    async def handle_disconnect(self, shard: gateway.GatewayClientV7, payload: data_structures.DiscordObjectT):
        ...

    async def handle_reconnect(self, shard: gateway.GatewayClientV7, payload: data_structures.DiscordObjectT):
        ...

    async def handle_connect(self, shard: gateway.GatewayClientV7, payload: data_structures.DiscordObjectT):
        ...

    async def handle_ready(self, shard: gateway.GatewayClientV7, payload: data_structures.DiscordObjectT):
        ...

    async def handle_resumed(self, shard: gateway.GatewayClientV7, payload: data_structures.DiscordObjectT):
        ...

    async def handle_invalid_session(self, shard: gateway.GatewayClientV7, payload: bool):
        ...

    async def handle_channel_create(self, shard: gateway.GatewayClientV7, payload: data_structures.DiscordObjectT):
        ...

    async def handle_channel_update(self, shard: gateway.GatewayClientV7, payload: data_structures.DiscordObjectT):
        ...

    async def handle_channel_delete(self, shard: gateway.GatewayClientV7, payload: data_structures.DiscordObjectT):
        ...

    async def handle_channel_pins_update(self, shard: gateway.GatewayClientV7, payload: data_structures.DiscordObjectT):
        ...

    async def handle_guild_create(self, shard: gateway.GatewayClientV7, payload: data_structures.DiscordObjectT):
        ...

    async def handle_guild_update(self, shard: gateway.GatewayClientV7, payload: data_structures.DiscordObjectT):
        ...

    async def handle_guild_delete(self, shard: gateway.GatewayClientV7, payload: data_structures.DiscordObjectT):
        ...

    async def handle_guild_ban_add(self, shard: gateway.GatewayClientV7, payload: data_structures.DiscordObjectT):
        ...

    async def handle_guild_ban_remove(self, shard: gateway.GatewayClientV7, payload: data_structures.DiscordObjectT):
        ...

    async def handle_guild_emojis_update(self, shard: gateway.GatewayClientV7, payload: data_structures.DiscordObjectT):
        ...

    async def handle_guild_integrations_update(
        self, shard: gateway.GatewayClientV7, payload: data_structures.DiscordObjectT
    ):
        ...

    async def handle_guild_member_add(self, shard: gateway.GatewayClientV7, payload: data_structures.DiscordObjectT):
        ...

    async def handle_guild_member_update(self, shard: gateway.GatewayClientV7, payload: data_structures.DiscordObjectT):
        ...

    async def handle_guild_member_remove(self, shard: gateway.GatewayClientV7, payload: data_structures.DiscordObjectT):
        ...

    async def handle_guild_members_chunk(self, shard: gateway.GatewayClientV7, payload: data_structures.DiscordObjectT):
        ...

    async def handle_guild_role_create(self, shard: gateway.GatewayClientV7, payload: data_structures.DiscordObjectT):
        ...

    async def handle_guild_role_update(self, shard: gateway.GatewayClientV7, payload: data_structures.DiscordObjectT):
        ...

    async def handle_guild_role_delete(self, shard: gateway.GatewayClientV7, payload: data_structures.DiscordObjectT):
        ...

    async def handle_message_create(self, shard: gateway.GatewayClientV7, payload: data_structures.DiscordObjectT):
        ...

    async def handle_message_update(self, shard: gateway.GatewayClientV7, payload: data_structures.DiscordObjectT):
        ...

    async def handle_message_delete(self, shard: gateway.GatewayClientV7, payload: data_structures.DiscordObjectT):
        ...

    async def handle_message_delete_bulk(self, shard: gateway.GatewayClientV7, payload: data_structures.DiscordObjectT):
        ...

    async def handle_message_reaction_add(
        self, shard: gateway.GatewayClientV7, payload: data_structures.DiscordObjectT
    ):
        ...

    async def handle_message_reaction_remove(
        self, shard: gateway.GatewayClientV7, payload: data_structures.DiscordObjectT
    ):
        ...

    async def handle_message_reaction_remove_all(
        self, shard: gateway.GatewayClientV7, payload: data_structures.DiscordObjectT
    ):
        ...

    async def handle_presence_update(self, shard: gateway.GatewayClientV7, payload: data_structures.DiscordObjectT):
        ...

    async def handle_typing_start(self, shard: gateway.GatewayClientV7, payload: data_structures.DiscordObjectT):
        ...

    async def handle_user_update(self, shard: gateway.GatewayClientV7, payload: data_structures.DiscordObjectT):
        ...

    async def handle_voice_state_update(self, shard: gateway.GatewayClientV7, payload: data_structures.DiscordObjectT):
        ...

    async def handle_voice_server_update(self, shard: gateway.GatewayClientV7, payload: data_structures.DiscordObjectT):
        ...

    async def handle_webhooks_update(self, shard: gateway.GatewayClientV7, payload: data_structures.DiscordObjectT):
        ...

    async def handle_presences_replace(self, shard: gateway.GatewayClientV7, payload: data_structures.DiscordObjectT):
        # This should not be implemented, as it is for users only and is not documented. This exists to allow us to
        # ignore it silently rather than producing spam.
        ...

    async def drain_unrecognised_event(
        self, shard: gateway.GatewayClientV7, event_name: str, payload: data_structures.DiscordObjectT
    ):
        ...
