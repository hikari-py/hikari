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
from __future__ import annotations

import asyncio

from hikari.internal_utilities import meta
from hikari.internal_utilities import unspecified
from hikari.orm.models import audit_logs
from hikari.orm.models import gateway_bot
from . import fabric


class HTTPAdapter:
    """
    Component that bridges the basic HTTP API exposed by :mod:`hikari.net.http_client` and
    wraps it in a unit of processing that can handle parsing API objects into Hikari ORM objects,
    and can handle keeping the state up to date as required.
    """

    def __init__(self, fabric_obj: fabric.Fabric) -> None:
        #: The fabric of this application.
        self.fabric: fabric.Fabric = fabric_obj

        # We are expected to cache this call. We use a future with an immediate callback
        # so that we can await the result without a race condition due to the await context
        # switch.
        self._get_gateway_future = None

    @meta.link_developer_portal(meta.APIResource.GATEWAY)
    async def get_gateway(self) -> str:
        """
        Returns:
            A static URL to use to connect to the gateway with.

        Note:
            This call is cached after the first invocation. This does not require authorization
            to work.
        """
        if self._get_gateway_future is None:
            self._get_gateway_future = asyncio.create_task(self.fabric.http_client.get_gateway())

        return await self._get_gateway_future

    @meta.link_developer_portal(meta.APIResource.GATEWAY)
    async def get_gateway_bot(self) -> gateway_bot.GatewayBot:
        """
        Returns:
            The gateway bot details to use as a recommendation for sharding and bot initialization.

        Note:
            Unlike :meth:`get_gateway`, this requires valid Bot authorization to work.
        """
        gateway_bot_payload = await self.fabric.http_client.get_gateway_bot()
        return gateway_bot.GatewayBot(gateway_bot_payload)

    async def get_guild_audit_log(
        self,
        guild_id: int,
        *,
        user_id: int = unspecified.UNSPECIFIED,
        action_type: audit_logs.AuditLogEvent = unspecified.UNSPECIFIED,
        limit: int = unspecified.UNSPECIFIED,
    ):
        audit_payload = await self.fabric.http_client.get_guild_audit_log(
            guild_id=str(guild_id),
            user_id=str(user_id) if user_id is not unspecified.UNSPECIFIED else user_id,
            action_type=int(action_type) if action_type is not unspecified.UNSPECIFIED else unspecified.UNSPECIFIED,
            limit=limit,
        )
        return audit_logs.AuditLog(self.fabric, audit_payload)
