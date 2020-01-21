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
            >>> None  # set this to None explicitly, or...
            >>> ShardOptions([None], 1)    # tell it to use no shards
        Automatically determine how to shard:
            >>> ShardOptions([], 0)
    """

    #: The shards to start. This can be a :class:`range`, a :class:`slice`, or an iterable object
    #: of integer IDs.
    #:
    #: For example, to set all 10 shards up in a 10-shard bot, use:
    #: >>> ShardOptions(range(10), 10)
    #: ...or if you wish to instead use 50 shards and only start shard 20-30, use this:
    #: >>> ShardOptions(slice(20, 30), 10)
    #: ...if you need finer control, you can just specify them directly as well:
    #: >>> ShardOptions([3, 6, 7, 9, 11], 20)
    #:
    #: No sharding is denoted by a one-wide iterable with the value:
    #: >>> ShardOptions([None], 1)
    shards: typing.Union[range, slice, typing.Iterable[type_hints.Nullable[int]]]
    #: The total number of shards that the bot will have up, distributed. This is required to be
    #: consistent across multi-sharded applications that are distributed to ensure that the bot
    #: has the guilds correctly distributed across shards.
    shard_count: int


#: Use an appropriate number of shards for the size of the bot being run.
AUTO_SHARD = ShardOptions((), 0)
#: Use no shards.
NO_SHARDS = ShardOptions([None], 1)

# This is rather long and obnoxious.
_DEFAULT_CHUNK_MODE = dispatching_event_adapter_impl.AutoRequestChunksMode.MEMBERS_AND_PRESENCES


@dataclasses.dataclass()
class ClientOptions:
    """
    Represents customization settings that can be set for a bot.
    """

    allow_redirects: bool = False
    chunk_mode: dispatching_event_adapter_impl.AutoRequestChunksMode = _DEFAULT_CHUNK_MODE
    connector: type_hints.Nullable[aiohttp.BaseConnector] = None
    debug: bool = False
    enable_guild_subscription_events = True
    gateway_intents: type_hints.Nullable[gateway.GatewayIntent] = None
    http_timeout: type_hints.Nullable[float] = None
    large_guild_threshold: int = 250
    max_user_dm_channel_count: int = 100
    max_message_cache_size: int = 100
    presence: type_hints.Nullable[presences.Presence] = presences.Presence()
    proxy_auth: type_hints.Nullable[aiohttp.BasicAuth] = None
    proxy_headers: type_hints.Nullable[aiohttp.typedefs.LooseHeaders] = None
    proxy_url: type_hints.Nullable[str] = None
    shards: type_hints.Nullable[ShardOptions] = AUTO_SHARD
    ssl_context: type_hints.Nullable[ssl.SSLContext] = None
    verify_ssl: bool = True
