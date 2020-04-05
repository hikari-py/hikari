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
import asyncio
import datetime
import logging
import typing

from hikari import events
from hikari.clients import configs
from hikari.clients import gateway_manager
from hikari.clients import rest_client
from hikari.clients import runnable
from hikari.clients import shard_client
from hikari.internal import more_asyncio
from hikari.internal import more_logging
from hikari.state import event_dispatchers
from hikari.state import event_managers


class BotBase(runnable.RunnableClient, event_dispatchers.EventDispatcher):
    """An abstract base class for a bot implementation.

    Parameters
    ----------
    config : :obj:`hikari.clients.configs.BotConfig`
        The config object to use.
    event_manager : ``EventManagerT``
        The event manager to use. This must be a subclass of
        :obj:`hikari.state.event_managers.EventManager`
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
    #: :type: :obj:`hikari.clients.gateway_client.GatewayClient`
    gateway: gateway_manager.GatewayManager[shard_client.ShardClient]

    #: The logger to use for this bot.
    #:
    #: :type: :obj:`logging.Logger`
    logger: logging.Logger

    #: The REST HTTP client to use for this bot.
    #:
    #: :type: :obj:`hikari.clients.rest_client.RESTClient`
    rest: rest_client.RESTClient

    @abc.abstractmethod
    def __init__(self, config: configs.BotConfig, event_manager: event_managers.EventManager) -> None:
        super().__init__(more_logging.get_named_logger(self))
        self.config = config
        self.event_manager = event_manager
        self.gateway = NotImplemented
        self.rest = rest_client.RESTClient(self.config)

    async def start(self):
        while (gateway_bot := await self.rest.fetch_gateway_bot()).session_start_limit.remaining <= 0:
            resume_at = datetime.datetime.now() + gateway_bot.session_start_limit.reset_after

            self.logger.critical(
                "You have reached the max identify limit for this time window (%s). "
                "To prevent your token being reset, I will wait for %s (until approx %s) "
                "and then continue signing in. Press CTRL-C to shut down.",
                gateway_bot.session_start_limit.total,
                gateway_bot.session_start_limit.reset_after,
                resume_at,
            )

            await asyncio.sleep(60)
            while (now := datetime.datetime.now()) < resume_at:
                self.logger.info("Still waiting, %s to go...", resume_at - now)
                await asyncio.sleep(60)

        self.logger.info(
            "You have sent an IDENTIFY %s time(s) before now, and have %s remaining. This will reset at %s.",
            gateway_bot.session_start_limit.total - gateway_bot.session_start_limit.remaining,
            gateway_bot.session_start_limit.remaining,
            datetime.datetime.now() + gateway_bot.session_start_limit.reset_after,
        )

        shard_count = self.config.shard_count if self.config.shard_count else gateway_bot.shard_count
        shard_ids = self.config.shard_ids if self.config.shard_ids else [*range(shard_count)]

        self.gateway = gateway_manager.GatewayManager(
            config=self.config,
            url=gateway_bot.url,
            raw_event_consumer_impl=self.event_manager,
            shard_ids=shard_ids,
            shard_count=shard_count,
        )

        await self.gateway.start()

    async def close(self, wait: bool = True):
        await self.gateway.close(wait)
        self.event_manager.event_dispatcher.close()
        await self.rest.close()

    async def join(self) -> None:
        await self.gateway.join()

    def add_listener(
        self, event_type: typing.Type[event_dispatchers.EventT], callback: event_dispatchers.EventCallbackT
    ) -> event_dispatchers.EventCallbackT:
        return self.event_manager.event_dispatcher.remove_listener(event_type, callback)

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
        super().__init__(config, event_managers.StatelessEventManagerImpl())
