#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019-2020
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
"""The logic for handling requests to gateway endpoints."""

from __future__ import annotations

__all__ = ["RESTGatewayComponent"]

import abc

from hikari import gateway_entities
from hikari.clients.rest import base


class RESTGatewayComponent(base.BaseRESTComponent, abc.ABC):  # pylint: disable=abstract-method
    """The REST client component for handling requests to gateway endpoints."""

    async def fetch_gateway_url(self) -> str:
        """Get a generic url used for establishing a Discord gateway connection.

        Returns
        -------
        str
            A static URL to use to connect to the gateway with.

        !!! note
            Users are expected to attempt to cache this result.
        """
        # noinspection PyTypeChecker
        return await self._session.get_gateway()

    async def fetch_gateway_bot(self) -> gateway_entities.GatewayBot:
        """Get bot specific gateway information.

        Returns
        -------
        hikari.gateway_entities.GatewayBot
            The bot specific gateway information object.

        !!! note
            Unlike `RESTGatewayComponent.fetch_gateway_url`, this requires a
            valid token to work.
        """
        payload = await self._session.get_gateway_bot()
        return gateway_entities.GatewayBot.deserialize(payload, components=self._components)
