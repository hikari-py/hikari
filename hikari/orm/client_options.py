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
from __future__ import annotations

import dataclasses
import ssl
import typing

import aiohttp.typedefs

from hikari.internal_utilities import type_hints
from hikari.net import gateway
from hikari.orm.gateway import dispatching_event_adapter_impl
from hikari.orm.models import presences


@dataclasses.dataclass(frozen=True)
class ShardOptions:
    """
    Represents allowable shards.

    Special cases:
        No sharding desired:
            >>> ShardOptions([0], 1)
        Automatically determine how to shard:
            >>> ShardOptions([], 0)
    """

    #: The shards to start. This can be a :class:`range`, a :class:`slice`, or an iterable object
    #: of integer IDs.
    #:
    #: For example, to set all 10 shards up in a 10-shard bot, use:
    #: >>> ShardOptions(range(10), 10)
    #: ...or if you wish to instead use 50 shards and only start shard 20-30, use this:
    #: >>> ShardOptions(slice(20, 30), 50)
    #: ...if you need finer control, eg. in a 20 shard bot, you can just specify them directly as well:
    #: >>> ShardOptions([3, 6, 7, 9, 11], 20)
    #:
    #: No sharding is denoted by a one-wide iterable with the value:
    #: >>> ShardOptions([0], 1)
    shards: typing.Union[range, slice, typing.Iterable[int]]
    #: The total number of shards that the bot will have up, distributed. This is required to be
    #: consistent across multi-sharded applications that are distributed to ensure that the bot
    #: has the guilds correctly distributed across shards.
    shard_count: int


#: Use an appropriate number of shards for the size of the bot being run.
AUTO_SHARD = ShardOptions((), 0)
#: Dont use sharding, just shard 0.
NO_SHARDING = ShardOptions([0], 1)

# This is rather long and obnoxious.
_DEFAULT_CHUNK_MODE = dispatching_event_adapter_impl.AutoRequestChunksMode.MEMBERS_AND_PRESENCES


@dataclasses.dataclass()
class ClientOptions:
    """
    Represents customization settings that can be set for a bot.
    """

    #: Whether to allow redirects or not.
    #: This defaults to `False` for security reasons, only modify this if you are receiving multiple
    #: redirection responses causing requests to fail.
    allow_redirects: bool = False
    #: Options for automatically retrieving all guild members in a guild when a READY event is fired.
    chunk_mode: dispatching_event_adapter_impl.AutoRequestChunksMode = _DEFAULT_CHUNK_MODE
    #: The :class:`aiohttp.BaseConnector` to use for the client session. This is used for both the websocket
    #: and any HTTP requests.
    connector: type_hints.Nullable[aiohttp.BaseConnector] = None
    #: Whether to enable debugging or not.
    debug: bool = False
    #: The intents to send to the gateway on IDENTIFY.
    gateway_intents: type_hints.Nullable[gateway.GatewayIntent] = None
    #: The timeout to apply to individual HTTP requests. Any request that takes longer than this time period
    #: will be cancelled with an :class:`asyncio.TimeoutError`
    http_timeout: type_hints.Nullable[float] = None
    #: The total number of members where the gateway will stop sending offline members in the guild member list.
    large_guild_threshold: int = 250
    #: The maximum DM channels stored in the cache.
    max_user_dm_channel_count: int = 100
    #: The maximum messages stored in the cache.
    max_message_cache_size: int = 100
    #: The initial presence to start the bot with.
    presence: type_hints.Nullable[presences.Presence] = dataclasses.field(default_factory=presences.Presence)
    #: The proxy authentication to use.
    proxy_auth: type_hints.Nullable[aiohttp.BasicAuth] = None
    #: The proxy headers to pass.
    proxy_headers: type_hints.Nullable[aiohttp.typedefs.LooseHeaders] = None
    #: The proxy URL to use.
    proxy_url: type_hints.Nullable[str] = None
    #: The shard configuration to use. Check :class:`hikari.client_options.ShardOptions` for more information.
    shards: ShardOptions = AUTO_SHARD
    #: The SSL context to use.
    ssl_context: type_hints.Nullable[ssl.SSLContext] = None
    #: Whether to enable SSL verification or not.
    #: Generally you want this enabled to ensure that the SSL certificate that Discord provides is genuine,
    #: however, some awkward proxies can cause this to not work, in which case you would want to disable this.
    verify_ssl: bool = True
