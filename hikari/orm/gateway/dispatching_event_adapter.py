#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekokatt 2019-2020
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
Core event adapter implementation for dispatching events.

The purpose of this is to provide a base for an implementation to define how
to handle events.
"""
from __future__ import annotations

import abc
import logging
import typing

from hikari.internal_utilities import containers
from hikari.internal_utilities import loggers
from hikari.net import gateway
from hikari.orm import fabric as _fabric
from hikari.orm.gateway import base_event_handler


class BaseDispatchingEventAdapter(base_event_handler.BaseEventHandler):
    """
    Stubbed definition of an event handler. This automatically implements an underlying handler for every documented
    event that Discord can dispatch to us that performs no operation, so unimplemented events in subclasses go ignored
    silently.

    A couple of additional events are defined that can be produced by the gateway implementation for Hikari.
    """

    __slots__ = ("logger", "fabric")

    #: The logger used for this event adapter.
    logger: logging.Logger

    #: The application fabric.
    fabric: _fabric.Fabric

    @abc.abstractmethod
    def __init__(self, fabric_obj: _fabric.Fabric) -> None:
        self.logger = loggers.get_named_logger(self)
        self.fabric = fabric_obj

    async def consume_raw_event(self, shard, event_name: str, payload: typing.Any) -> None:
        try:
            try:
                handler = getattr(self, f"handle_{event_name.lower()}")
            except AttributeError:
                await self.drain_unrecognised_event(shard, event_name, payload)
            else:
                await handler(shard, payload)
        except Exception as ex:
            self.logger.exception("An exception was discarded", exc_info=ex)

    ###################
    # Internal events #
    ###################

    async def handle_disconnect(self, shard: gateway.GatewayClient, payload: containers.JSONObject):
        ...

    async def handle_connect(self, shard: gateway.GatewayClient, payload: containers.JSONObject):
        ...

    async def handle_manual_shutdown(self, shard: gateway.GatewayClient, payload: containers.JSONObject):
        ...

    ##################
    # Gateway events #
    ##################

    async def handle_hello(self, shard: gateway.GatewayClient, payload: containers.JSONObject):
        ...

    async def handle_reconnect(self, shard: gateway.GatewayClient, payload: containers.JSONObject):
        ...

    async def handle_invalid_session(self, shard: gateway.GatewayClient, payload: containers.JSONObject):
        ...

    async def handle_ready(self, shard: gateway.GatewayClient, payload: containers.JSONObject):
        ...

    async def handle_resumed(self, shard: gateway.GatewayClient, payload: containers.JSONObject):
        ...

    async def handle_channel_create(self, shard: gateway.GatewayClient, payload: containers.JSONObject):
        ...

    async def handle_channel_update(self, shard: gateway.GatewayClient, payload: containers.JSONObject):
        ...

    async def handle_channel_delete(self, shard: gateway.GatewayClient, payload: containers.JSONObject):
        ...

    async def handle_channel_pins_update(self, shard: gateway.GatewayClient, payload: containers.JSONObject):
        ...

    async def handle_guild_create(self, shard: gateway.GatewayClient, payload: containers.JSONObject):
        ...

    async def handle_guild_update(self, shard: gateway.GatewayClient, payload: containers.JSONObject):
        ...

    async def handle_guild_delete(self, shard: gateway.GatewayClient, payload: containers.JSONObject):
        ...

    async def handle_guild_ban_add(self, shard: gateway.GatewayClient, payload: containers.JSONObject):
        ...

    async def handle_guild_ban_remove(self, shard: gateway.GatewayClient, payload: containers.JSONObject):
        ...

    async def handle_guild_emojis_update(self, shard: gateway.GatewayClient, payload: containers.JSONObject):
        ...

    async def handle_guild_integrations_update(self, shard: gateway.GatewayClient, payload: containers.JSONObject):
        ...

    async def handle_guild_member_add(self, shard: gateway.GatewayClient, payload: containers.JSONObject):
        ...

    async def handle_guild_member_update(self, shard: gateway.GatewayClient, payload: containers.JSONObject):
        ...

    async def handle_guild_member_remove(self, shard: gateway.GatewayClient, payload: containers.JSONObject):
        ...

    async def handle_guild_members_chunk(self, shard: gateway.GatewayClient, payload: containers.JSONObject):
        ...

    async def handle_guild_role_create(self, shard: gateway.GatewayClient, payload: containers.JSONObject):
        ...

    async def handle_guild_role_update(self, shard: gateway.GatewayClient, payload: containers.JSONObject):
        ...

    async def handle_guild_role_delete(self, shard: gateway.GatewayClient, payload: containers.JSONObject):
        ...

    async def handle_message_create(self, shard: gateway.GatewayClient, payload: containers.JSONObject):
        ...

    async def handle_message_update(self, shard: gateway.GatewayClient, payload: containers.JSONObject):
        ...

    async def handle_message_delete(self, shard: gateway.GatewayClient, payload: containers.JSONObject):
        ...

    async def handle_message_delete_bulk(self, shard: gateway.GatewayClient, payload: containers.JSONObject):
        ...

    async def handle_message_reaction_add(self, shard: gateway.GatewayClient, payload: containers.JSONObject):
        ...

    async def handle_message_reaction_remove(self, shard: gateway.GatewayClient, payload: containers.JSONObject):
        ...

    async def handle_message_reaction_remove_all(self, shard: gateway.GatewayClient, payload: containers.JSONObject):
        ...

    async def handle_presence_update(self, shard: gateway.GatewayClient, payload: containers.JSONObject):
        ...

    async def handle_typing_start(self, shard: gateway.GatewayClient, payload: containers.JSONObject):
        ...

    async def handle_user_update(self, shard: gateway.GatewayClient, payload: containers.JSONObject):
        ...

    async def handle_voice_state_update(self, shard: gateway.GatewayClient, payload: containers.JSONObject):
        ...

    async def handle_voice_server_update(self, shard: gateway.GatewayClient, payload: containers.JSONObject):
        ...

    async def handle_webhooks_update(self, shard: gateway.GatewayClient, payload: containers.JSONObject):
        ...

    async def handle_presences_replace(self, shard: gateway.GatewayClient, payload: containers.JSONObject):
        # This should not be implemented, as it is for users only and is not documented. This exists to allow us to
        # ignore it silently rather than producing spam.
        ...

    async def drain_unrecognised_event(
        self, shard: gateway.GatewayClient, event_name: str, payload: containers.JSONObject
    ):
        ...
