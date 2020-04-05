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
"""May contain nuts."""
__all__ = ["RESTClient"]

import datetime

from hikari import gateway_entities
from hikari.clients import configs


class RESTClient:
    """Stuff will go here when this is implemented..."""

    # TODO: FasterSpeeding: update this.
    def __init__(self, _: configs.RESTConfig) -> None:
        ...

    async def close(self):
        ...

    async def fetch_gateway_bot(self) -> gateway_entities.GatewayBot:
        # Stubbed placeholder.
        # TODO: replace with actual implementation.
        return gateway_entities.GatewayBot(
            url="wss://gateway.discord.gg",
            shard_count=1,
            session_start_limit=gateway_entities.SessionStartLimit(
                total=1000, remaining=999, reset_after=datetime.timedelta(days=0.9)
            ),
        )
