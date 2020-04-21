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
__all__ = ["StatelessBot"]

from hikari.clients import bot_base
from hikari.clients import configs
from hikari.clients import rest
from hikari.clients import shards
from hikari.state import dispatchers
from hikari.state import stateless


class StatelessBot(
    bot_base.BotBase[
        shards.ShardClientImpl,
        rest.RESTClient,
        dispatchers.IntentAwareEventDispatcherImpl,
        stateless.StatelessEventManagerImpl,
        configs.BotConfig,
    ]
):
    """Bot client without any state internals.

    This is the most basic type of bot you can create.
    """

    @classmethod
    def _create_shard(
        cls,
        shard_id: int,
        shard_count: int,
        url: str,
        config: configs.BotConfig,
        event_manager: stateless.StatelessEventManagerImpl,
    ) -> shards.ShardClientImpl:
        return shards.ShardClientImpl(
            shard_id=shard_id,
            shard_count=shard_count,
            config=config,
            raw_event_consumer_impl=event_manager,
            url=url,
            dispatcher=event_manager.event_dispatcher,
        )

    @classmethod
    def _create_rest(cls, config: configs.BotConfig) -> rest.RESTClient:
        return rest.RESTClient(config)

    @classmethod
    def _create_event_manager(
        cls, config: configs.BotConfig, dispatcher: dispatchers.IntentAwareEventDispatcherImpl
    ) -> stateless.StatelessEventManagerImpl:
        return stateless.StatelessEventManagerImpl(dispatcher)

    @classmethod
    def _create_event_dispatcher(cls, config: configs.BotConfig) -> dispatchers.IntentAwareEventDispatcherImpl:
        return dispatchers.IntentAwareEventDispatcherImpl(config.intents)
