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
The primary client for writing a bot with Hikari.
"""
import asyncio
import datetime
import inspect
import typing

from hikari import client_options
from hikari.internal_utilities import compat
from hikari.internal_utilities import loggers
from hikari.net import gateway
from hikari.net import http_api
from hikari.orm import fabric
from hikari.orm.gateway import basic_chunker_impl
from hikari.orm.gateway import dispatching_event_adapter_impl
from hikari.orm.http import http_adapter_impl
from hikari.orm.state import state_registry_impl
from hikari.internal_utilities import aio
from hikari.internal_utilities import assertions


class Client:
    def __init__(self, token: str, options: typing.Optional[client_options.ClientOptions] = None) -> None:
        self._client_options = options or client_options.ClientOptions()
        self._event_dispatcher = aio.MuxMap()
        self._fabric: typing.Optional[fabric.Fabric] = None
        self._quieting_down = False
        self.logger = loggers.get_named_logger(self)
        self.token = token

    async def _new_application_fabric(self):
        self._fabric = fabric.Fabric()
        self._fabric.state_registry = state_registry_impl.StateRegistryImpl(
            self._fabric, self._client_options.max_message_cache_size, self._client_options.max_user_dm_channel_count,
        )
        self._fabric.event_handler = dispatching_event_adapter_impl.DispatchingEventAdapterImpl(
            self._fabric, self.dispatch, request_chunks_mode=self._client_options.chunk_mode,
        )
        self._fabric.http_api = http_api.HTTPAPIImpl(
            allow_redirects=self._client_options.allow_redirects,
            max_retries=self._client_options.http_max_retries,
            token=self.token,
            connector=self._client_options.connector,
            proxy_headers=self._client_options.proxy_headers,
            proxy_auth=self._client_options.proxy_auth,
            proxy_url=self._client_options.proxy_url,
            ssl_context=self._client_options.ssl_context,
            verify_ssl=self._client_options.verify_ssl,
            timeout=self._client_options.http_timeout,
        )
        self._fabric.http_adapter = http_adapter_impl.HTTPAdapterImpl(self._fabric)
        self._fabric.gateways = {new_shard.shard_id: new_shard for new_shard in await self._build_gateways()}
        self._fabric.chunker = basic_chunker_impl.BasicChunkerImpl(self._fabric)

    async def _build_gateways(self):
        shards_ids = self._client_options.shards

        if shards_ids is client_options.AUTO_SHARD:
            gateway_bot = await self._fabric.http_adapter.fetch_gateway_bot()
            self.logger.info("The gateway has recommended %s shards for this bot", gateway_bot.shards)

            self.logger.info(
                "You have performed an IDENTIFY %s times recently. You may IDENTIFY %s more times before your "
                "token gets reset by Discord. This limit resets at %s (%s from now)",
                gateway_bot.session_start_limit.used,
                gateway_bot.session_start_limit.remaining,
                gateway_bot.session_start_limit.reset_at,
                gateway_bot.session_start_limit.reset_at - datetime.datetime.now(tz=datetime.timezone.utc),
            )

            url = gateway_bot.url

            # We can send one shard, but that triggers the shard logger format pattern, and is a little inconsistent
            # with the other functionality in this method, so lets keep this consistent.
            shards_ids = range(gateway_bot.shards) if gateway_bot.shards != 1 else [None]
        else:
            url = await self._fabric.http_adapter.gateway_url

            if shards_ids is None:
                shards_ids = [None]
            elif isinstance(shards_ids, slice):
                shards_ids = [i for i in range(shards_ids.start, shards_ids.stop, shards_ids.step)]
            else:
                shards_ids = list(shards_ids)

        shard_instances = []
        for shard_id in shards_ids:
            shard_instances.append(
                gateway.GatewayClient(
                    token=self.token,
                    uri=url,
                    connector=self._client_options.connector,
                    proxy_headers=self._client_options.proxy_headers,
                    proxy_auth=self._client_options.proxy_auth,
                    proxy_url=self._client_options.proxy_url,
                    ssl_context=self._client_options.ssl_context,
                    verify_ssl=self._client_options.verify_ssl,
                    timeout=self._client_options.http_timeout,
                    max_persistent_buffer_size=self._client_options.max_persistent_gateway_buffer_size,
                    large_threshold=self._client_options.large_guild_threshold,
                    enable_guild_subscription_events=self._client_options.enable_guild_subscription_events,
                    intents=self._client_options.intents,
                    initial_presence=self._client_options.presence.to_dict(),
                    shard_id=shard_id,
                    shard_count=len(shards_ids),
                    gateway_event_dispatcher=self._fabric.event_handler.consume_raw_event,
                    internal_event_dispatcher=self._fabric.event_handler.consume_raw_event,
                )
            )

        return shard_instances

    @staticmethod
    async def _run_shard(shard):
        try:
            return shard, await shard.run()
        except BaseException as ex:
            return shard, ex

    async def _launch_shard(self, shard):
        self.logger.info("launching shard %s", shard.shard_id)
        task = compat.asyncio.create_task(self._run_shard(shard), name=f"poll shard {shard.shard_id} for events",)
        return shard.shard_id, task

    async def run(self):
        shard_tasks = await self.start()
        failures, _ = await asyncio.wait(shard_tasks.values(), return_when=asyncio.FIRST_EXCEPTION)
        for failure in failures:
            shard_id, reason = failure.result()
            self.logger.exception("shard %s has shut down", shard_id, exc_info=reason)

            reason = reason if isinstance(reason, BaseException) else None
            if not self._quieting_down:
                raise RuntimeError(f"shard {shard_id} has shut down") from reason

    async def start(self):
        await self._new_application_fabric()
        shard_tasks = await asyncio.gather(*(self._launch_shard(shard) for shard in self._fabric.gateways.values()))
        return {shard_id: task for shard_id, task in shard_tasks}

    async def close(self):
        self._quieting_down = True
        await self._fabric.http_api.close()
        gateway_tasks = []
        for shard_id, shard in self._fabric.gateways.items():
            self.logger.info("shutting down shard %s", shard_id)
            shutdown_task = compat.asyncio.create_task(shard.close(), name=f"waiting for shard {shard_id} to close")
            gateway_tasks.append(shutdown_task)
        await asyncio.wait(gateway_tasks, return_when=asyncio.ALL_COMPLETED)

    def dispatch(self, event: str, *args) -> None:
        self._event_dispatcher.dispatch(event, *args)

    def add_event(self, event_name: str, coroutine_function: aio.CoroutineFunctionT) -> None:
        self.logger.debug(
            "subscribing %s%s to %s event",
            coroutine_function.__name__,
            inspect.signature(coroutine_function),
            event_name,
        )
        self._event_dispatcher.add(event_name, coroutine_function)

    def remove_event(self, event_name: str, coroutine_function: aio.CoroutineFunctionT) -> None:
        self.logger.debug(
            "unsubscribing %s%s from %s event",
            coroutine_function.__name__,
            inspect.signature(coroutine_function),
            event_name,
        )
        self._event_dispatcher.remove(event_name, coroutine_function)

    def event(
        self, name: typing.Optional[str] = None
    ) -> typing.Callable[[aio.CoroutineFunctionT], aio.CoroutineFunctionT]:
        """
        Generates a decorator for a coroutine function in order to subscribe it as an event listener.

        Args:
            name:
                The name of the event to subscribe to. If you do not supply this, then the name of the coroutine
                function itself is used, minus the word "on_" if present at the start.

        Returns:
            A decorator that decorates a coroutine function and returns the coroutine function passed to it.
        """
        assertions.assert_that(
            isinstance(name, str) or name is None,
            "Invalid use of @client.event() decorator.\nValid usage of this decorator is as follows:\n"
            "@client.event()\n"
            "async def on_message_create(message):\n"
            "    ...\n"
            "# or\n"
            "@client.event('message_create')\n"
            "async def some_name_here(message):\n"
            "    ...\n",
        )

        def decorator(coroutine_function: aio.CoroutineFunctionT) -> aio.CoroutineFunctionT:
            if name is None:
                if coroutine_function.__name__.startswith("on_"):
                    event_name = coroutine_function.__name__[3:]
                else:
                    event_name = coroutine_function.__name__
            else:
                event_name = name
            self.add_event(event_name, coroutine_function)
            return coroutine_function

        return decorator

    @property
    def heartbeat_latency(self) -> float:
        if len(self._fabric.gateways) == 0:
            # Bot has not yet started.
            return float("nan")
        return sum(shard.heartbeat_latency for shard in self._fabric.gateways.values()) / len(self._fabric.gateways)

    @property
    def heartbeat_latencies(self) -> typing.Mapping[typing.Optional[int], float]:
        return {shard.shard_id: shard.heartbeat_latency for shard in self._fabric.gateways.values()}
