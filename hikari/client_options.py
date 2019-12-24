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
Client options that can be set.
"""
import dataclasses
import functools
import operator
import ssl
import typing

import aiohttp.typedefs

from hikari.net import opcodes
from hikari.orm.gateway import dispatching_event_adapter_impl
from hikari.orm.models import presences


AUTO_SHARD = object()


@dataclasses.dataclass()
class ClientOptions:
    """
    Represents customization settings that can be set for a bot.
    """

    allow_redirects: bool = False
    chunk_mode: dispatching_event_adapter_impl.AutoRequestChunksMode = dispatching_event_adapter_impl.AutoRequestChunksMode.MEMBERS_AND_PRESENCES
    connector: aiohttp.BaseConnector = None
    enable_guild_subscription_events = True
    http_max_retries: int = 5
    http_timeout: float = None
    intents: opcodes.GatewayIntent = functools.reduce(operator.or_, opcodes.GatewayIntent.__iter__())
    large_guild_threshold: int = 250
    max_user_dm_channel_count: int = 100
    max_message_cache_size: int = 100
    max_persistent_gateway_buffer_size: int = 3 * 1024 ** 2
    presence: presences.Presence = presences.Presence()
    proxy_auth: aiohttp.BasicAuth = None
    proxy_headers: aiohttp.typedefs.LooseHeaders = None
    proxy_url: str = None
    shards: typing.Union[None, object, typing.Iterable[int], range, slice] = AUTO_SHARD
    ssl_context: ssl.SSLContext = None
    verify_ssl: bool = True
