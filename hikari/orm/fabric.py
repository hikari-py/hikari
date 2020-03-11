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
The ORM fabric. This is a reusable dataclass that is passed to all major
components and provides access to the entire object graph for all functional
and data components that are being managed by the application.
"""
from __future__ import annotations

__all__ = ["Fabric"]

import dataclasses
import typing

from hikari.net import gateway as _gateway
from hikari.net import http_client as _http_client
from hikari.orm.gateway import base_chunker as _chunker
from hikari.orm.gateway import base_event_handler as _event_handler
from hikari.orm.http import base_http_adapter as _http_adapter
from hikari.orm.state import base_registry as _state_registry


@dataclasses.dataclass()
class Fabric:
    """
    Wraps all major API components together into one main component that can be passed
    around freely.
    """

    #: The handler for incoming events. This is expected to parse the raw event payloads that
    #: Discord provides.
    event_handler: _event_handler.BaseEventHandler = dataclasses.field(default=NotImplemented)

    #: Application state information. This stores information about any users the application
    #: can see, any guilds it is in, any channels that are available, and the likes.
    state_registry: _state_registry.BaseRegistry = dataclasses.field(default=NotImplemented)

    #: A mapping of shard ID's to gateways that are running.
    gateways: typing.Dict[int, _gateway.GatewayClient] = dataclasses.field(default_factory=dict)

    #: The ammount of shards that are being used overal to connect to Discord
    shard_count: int = 0

    #: The base HTTP client for making HTTP requests.
    http_client: _http_client.HTTPClient = dataclasses.field(default=NotImplemented)

    #: HTTP adapter bridge component to convert raw HTTP call responses to their ORM
    #: representation.
    http_adapter: _http_adapter.BaseHTTPAdapter = dataclasses.field(default=NotImplemented)

    #: Provides a mechanism to handle the guild chunking events.
    chunker: _chunker.BaseChunker = dataclasses.field(default=NotImplemented)
