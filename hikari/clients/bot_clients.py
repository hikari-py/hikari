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
"""A bot client might go here... eventually..."""
__all__ = ["BotBase", "StatelessBot"]

import abc
import datetime
import logging
import typing

from hikari import events
from hikari.clients import configs
from hikari.clients import gateway_managers
from hikari.clients import rest_clients
from hikari.clients import runnable
from hikari.clients import shard_clients
from hikari.internal import more_asyncio
from hikari.internal import more_logging
from hikari.state import event_dispatchers
from hikari.state import event_managers
from hikari.state import stateless_event_managers


class BotBase(runnable.RunnableClient, event_dispatchers.EventDispatcher):
    """An abstract base class for a bot implementation.

    Parameters
    ----------
    config : :obj:`hikari.clients.configs.BotConfig`
        The config object to use.
    event_manager : ``hikari.state.event_managers.EventManager``
        The event manager to use.
    """

    #: The config for this bot.
    #:
    #: :type: :obj:`hikari.clients.configs.BotConfig`
    config: configs.BotConfig

    #: The event manager for this bot.
    #:
    #: :type: a subclass of :obj:`hikari.state.event_managers.EventManager`
    event_manager: event_managers.EventManager

    #: The gateway for this bot.
    #:
    #: :type: :obj:`hikari.clients.gateway_managers.GatewayManager` [ :obj:`hikari.clients.shard_clients.ShardClient` ]
    gateway: gateway_managers.GatewayManager[shard_clients.ShardClient]

    #: The logger to use for this bot.
    #:
    #: :type: :obj:`logging.Logger`
    logger: logging.Logger

    #: The REST HTTP client to use for this bot.
    #:
    #: :type: :obj:`hikari.clients.rest_clients.RESTClient`
    rest: rest_clients.RESTClient

    @abc.abstractmethod
    def __init__(self, config: configs.BotConfig, event_manager: event_managers.EventManager) -> None:
        super().__init__(more_logging.get_named_logger(self))
        self.config = config
        self.event_manager = event_manager
        self.gateway = NotImplemented
        self.rest = NotImplemented

    async def start(self):
        self.rest = rest_clients.RESTClient(self.config)
        gateway_bot = await self.rest.fetch_gateway_bot()

        self.logger.info(
            "You have sent an IDENTIFY %s time(s) before now, and have %s remaining. This will reset at %s.",
            gateway_bot.session_start_limit.total - gateway_bot.session_start_limit.remaining,
            gateway_bot.session_start_limit.remaining,
            datetime.datetime.now() + gateway_bot.session_start_limit.reset_after,
        )

        shard_count = self.config.shard_count if self.config.shard_count else gateway_bot.shard_count
        shard_ids = self.config.shard_ids if self.config.shard_ids else [*range(shard_count)]

        self.gateway = gateway_managers.GatewayManager(
            config=self.config,
            url=gateway_bot.url,
            raw_event_consumer_impl=self.event_manager,
            shard_ids=shard_ids,
            shard_count=shard_count,
            dispatcher=self.event_manager.event_dispatcher,
        )

        await self.gateway.start()

    async def close(self):
        await self.gateway.close()
        self.event_manager.event_dispatcher.close()
        await self.rest.close()

    async def join(self) -> None:
        await self.gateway.join()

    def add_listener(
        self, event_type: typing.Type[event_dispatchers.EventT], callback: event_dispatchers.EventCallbackT
    ) -> event_dispatchers.EventCallbackT:
        return self.event_manager.event_dispatcher.add_listener(event_type, callback)

    def remove_listener(
        self, event_type: typing.Type[event_dispatchers.EventT], callback: event_dispatchers.EventCallbackT
    ) -> event_dispatchers.EventCallbackT:
        return self.event_manager.event_dispatcher.remove_listener(event_type, callback)

    def wait_for(
        self,
        event_type: typing.Type[event_dispatchers.EventT],
        *,
        timeout: typing.Optional[float],
        predicate: event_dispatchers.PredicateT,
    ) -> more_asyncio.Future:
        return self.event_manager.event_dispatcher.wait_for(event_type, timeout=timeout, predicate=predicate)

    def dispatch_event(self, event: events.HikariEvent) -> more_asyncio.Future[typing.Any]:
        return self.event_manager.event_dispatcher.dispatch_event(event)


class StatelessBot(BotBase):
    """Bot client without any state internals.

    Parameters
    ----------
    config : :obj:`hikari.clients.configs.BotConfig`
        The config object to use.
    """

    def __init__(self, config: configs.BotConfig) -> None:
        super().__init__(config, stateless_event_managers.StatelessEventManagerImpl())
