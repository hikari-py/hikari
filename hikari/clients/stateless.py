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
"""Stateless bot implementation."""

from __future__ import annotations

__all__ = ["StatelessBot"]

import typing

from hikari.clients import bot_base
from hikari.clients import rest
from hikari.clients import shards
from hikari.events import intent_aware_dispatchers
from hikari.state import stateless

if typing.TYPE_CHECKING:
    from hikari.clients import components as _components
    from hikari.clients import configs


class StatelessBot(bot_base.BotBase):
    """Bot client without any state internals.

    This is the most basic type of bot you can create.
    """

    @staticmethod
    def _create_shard(
        components: _components.Components, shard_id: int, shard_count: int, url: str
    ) -> shards.ShardClientImpl:
        return shards.ShardClientImpl(components=components, shard_id=shard_id, shard_count=shard_count, url=url)

    @staticmethod
    def _create_rest(components: _components.Components) -> rest.RESTClient:
        return rest.RESTClient(components)

    @staticmethod
    def _create_event_manager(components: _components.Components) -> stateless.StatelessEventManagerImpl:
        return stateless.StatelessEventManagerImpl(components)

    @staticmethod
    def _create_event_dispatcher(config: configs.BotConfig) -> intent_aware_dispatchers.IntentAwareEventDispatcherImpl:
        return intent_aware_dispatchers.IntentAwareEventDispatcherImpl(config.intents)
