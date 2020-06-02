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
"""Basic implementation the components for a single-process bot."""

from __future__ import annotations

__all__ = ["BotImpl"]

import logging
import typing
from concurrent import futures

from hikari.api import app
from hikari.impl import cache as cache_impl
from hikari.impl import entity_factory as entity_factory_impl
from hikari.impl import event_manager
from hikari.impl import gateway_zookeeper
from hikari.models import presences
from hikari.net import rest
from hikari.utilities import klass
from hikari.utilities import undefined

if typing.TYPE_CHECKING:
    import datetime

    from hikari.api import cache as cache_
    from hikari.api import entity_factory as entity_factory_
    from hikari.api import event_consumer as event_consumer_
    from hikari import http_settings as http_settings_
    from hikari.api import event_dispatcher
    from hikari.models import gateway as gateway_models
    from hikari.models import intents as intents_


class BotImpl(gateway_zookeeper.AbstractGatewayZookeeper, app.IBot):
    def __init__(
        self,
        *,
        config: http_settings_.HTTPSettings,
        debug: bool = False,
        gateway_version: int = 6,
        initial_activity: typing.Optional[presences.OwnActivity] = None,
        initial_idle_since: typing.Optional[datetime.datetime] = None,
        initial_is_afk: bool = False,
        initial_status: presences.PresenceStatus = presences.PresenceStatus.ONLINE,
        intents: typing.Optional[intents_.Intent] = None,
        large_threshold: int = 250,
        rest_version: int = 6,
        rest_url: typing.Union[undefined.Undefined, str] = undefined.Undefined(),
        shard_ids: typing.Optional[typing.Set[int]],
        shard_count: typing.Optional[int],
        token: str,
        use_compression: bool = True,
    ):
        self._logger = klass.get_logger(self)

        self._cache = cache_impl.CacheImpl(app=self)
        self._config = config
        self._event_manager = event_manager.EventManagerImpl(app=self)
        self._entity_factory = entity_factory_impl.EntityFactoryImpl(app=self)

        self._rest = rest.REST(  # nosec
            app=self,
            config=config,
            debug=debug,
            token=token,
            token_type="Bot",
            rest_url=rest_url,
            version=rest_version,
        )

        super().__init__(
            config=config,
            debug=debug,
            initial_activity=initial_activity,
            initial_idle_since=initial_idle_since,
            initial_is_afk=initial_is_afk,
            initial_status=initial_status,
            intents=intents,
            large_threshold=large_threshold,
            shard_ids=shard_ids,
            shard_count=shard_count,
            token=token,
            use_compression=use_compression,
            version=gateway_version,
        )

    @property
    def event_dispatcher(self) -> event_dispatcher.IEventDispatcher:
        return self._event_manager

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @property
    def cache(self) -> cache_.ICache:
        return self._cache

    @property
    def entity_factory(self) -> entity_factory_.IEntityFactory:
        return self._entity_factory

    @property
    def thread_pool(self) -> typing.Optional[futures.ThreadPoolExecutor]:
        # XXX: fixme
        return None

    @property
    def rest(self) -> rest.REST:
        return self._rest

    @property
    def event_consumer(self) -> event_consumer_.IEventConsumer:
        return self._event_manager

    @property
    def http_settings(self) -> http_settings_.HTTPSettings:
        return self._config

    def listen(self, event_type=undefined.Undefined()):
        return self.event_dispatcher.listen(event_type)

    def subscribe(self, event_type, callback):
        return self.event_dispatcher.subscribe(event_type, callback)

    def unsubscribe(self, event_type, callback):
        return self.event_dispatcher.unsubscribe(event_type, callback)

    async def wait_for(self, event_type, predicate, timeout):
        return await self.event_dispatcher.wait_for(event_type, predicate, timeout)

    def dispatch(self, event):
        return self.event_dispatcher.dispatch(event)

    async def close(self) -> None:
        await super().close()
        await self._rest.close()

    async def _fetch_gateway_recommendations(self) -> gateway_models.GatewayBot:
        return await self.rest.fetch_gateway_bot()
