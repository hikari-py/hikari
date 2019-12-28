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
from __future__ import annotations

import asyncio
import datetime
import inspect
import types
import typing

from hikari import client_options
from hikari.internal_utilities import aio
from hikari.internal_utilities import assertions
from hikari.internal_utilities import compat
from hikari.internal_utilities import loggers
from hikari.net import gateway
from hikari.net import http_api
from hikari.orm import fabric
from hikari.orm.gateway import basic_chunker_impl
from hikari.orm.gateway import dispatching_event_adapter_impl
from hikari.orm.http import http_adapter_impl
from hikari.orm.state import state_registry_impl


class Client:
    """
    A basic implementation of a client for running a Discord bot.
    
    Args:
        token:
            The bot token to sign in with.
        options:
            Other :class:`hikari.client_options.ClientOptions` to set. If not provided, sensible
            defaults are used instead.
    
    >>> client = Client("token_here")
    >>> @client.event()
    ... async def on_ready(shard):
    ...     print("Shard", shard.shard_id, "is ready!")
    >>> asyncio.run(client.run())
    """

    def __init__(self, token: str, options: typing.Optional[client_options.ClientOptions] = None) -> None:
        self._client_options = options or client_options.ClientOptions()
        self._event_dispatcher = aio.MuxMap()
        self._fabric: typing.Optional[fabric.Fabric] = None
        self._quieting_down = False
        self.logger = loggers.get_named_logger(self)
        self.token = token
        self._shard_tasks = None

    async def _init_new_application_fabric(self):
        self._fabric = fabric.Fabric()
        self._fabric.state_registry = await self._new_state_registry()
        self._fabric.event_handler = await self._new_event_handler()
        self._fabric.http_api = await self._new_http_api()
        self._fabric.http_adapter = await self._new_http_adapter()
        self._fabric.gateways = await self._new_shard_map()
        self._fabric.chunker = await self._new_chunker()

    async def _new_state_registry(self):
        return state_registry_impl.StateRegistryImpl(
            self._fabric, self._client_options.max_message_cache_size, self._client_options.max_user_dm_channel_count,
        )

    async def _new_event_handler(self):
        return dispatching_event_adapter_impl.DispatchingEventAdapterImpl(
            self._fabric, self.dispatch, request_chunks_mode=self._client_options.chunk_mode,
        )

    async def _new_http_api(self):
        return http_api.HTTPAPIImpl(
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

    async def _new_http_adapter(self):
        return http_adapter_impl.HTTPAdapterImpl(self._fabric)

    async def _new_shard_map(self):
        shard_ids = self._client_options.shards

        if not isinstance(shard_ids, client_options.ShardOptions) and shard_ids is not None:
            raise RuntimeError(
                "shard_ids in client options was not a valid type or value.\n"
                "\n"
                "When specifying the shards you wish to use in this setting, you have a few options for what you can \n"
                "set it to:\n",
                "   1. Do not specify anything for it. This will default it to `hikari.client_options.AUTO_SHARD` \n"
                "      which will ask the gateway for the most appropriate settings for your bot on start up.\n"
                "   2. Set it to `None`. This will turn sharding off and use a single gateway for your bot.\n"
                "   3. Set it to a `hikari.client_options.ShardOptions` object. The first value\n"
                "      can be either a collection of `int`s, a `slice`, or a `range`, and represents any shard IDs\n"
                "      to spin up. The second value is the total number of shards that are running for the entire bot\n"
                "      (you may only want to run three specific shards from a 50-shard bot here, perhaps.\n"
                "\n"
                "Setting any other type of value is invalid.",
            )

        if shard_ids is client_options.AUTO_SHARD:
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
            shard_ids = range(gateway_bot.shards) if gateway_bot.shards != 1 else [None]
            shard_count = gateway_bot.shards
        else:
            url = await self._fabric.http_adapter.gateway_url

            if isinstance(shard_ids, client_options.ShardOptions):
                if isinstance(shard_ids.shards, slice):
                    shard_count = shard_ids.shard_count
                    shard_ids = [i for i in range(shard_ids.shards.start, shard_ids.shards.stop, shard_ids.shards.step)]
                else:
                    shard_ids, shard_count = list(shard_ids.shards), shard_ids.shard_count
            else:
                shard_count = 1
                shard_ids = [None]

        shard_map = {}
        for shard_id in shard_ids:
            shard_map[shard_id] = gateway.GatewayClient(
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
                shard_count=shard_count,
                gateway_event_dispatcher=self._fabric.event_handler.consume_raw_event,
                internal_event_dispatcher=self._fabric.event_handler.consume_raw_event,
            )

        return shard_map

    async def _new_chunker(self):
        return basic_chunker_impl.BasicChunkerImpl(self._fabric)

    async def _run_shard(
        self, shard: gateway.GatewayClient
    ) -> typing.Tuple[gateway.GatewayClient, typing.Union[Exception, typing.Any]]:
        """
        Start a shard and wait for it to stop running.

        Args:
            shard:
                the gateway client to run.

        Returns:
            A tuple of the shard input and the exception it raised or result it returned when it stopped.
        """
        try:
            self.logger.info("launching shard %s", shard.shard_id)
            return shard, await shard.run()
        except Exception as ex:
            return shard, ex

    async def _start_shard_and_wait_ready(
        self, shard: gateway.GatewayClient,
    ) -> typing.Tuple[gateway.GatewayClient, asyncio.Task]:
        """
        Start a shard and wait for it to be READY, letting it continue to run in the background.

        Args:
            shard:
                The gateway client to launch.

        Returns:
            The shard that was ready and the task to await for the shard to shut down eventually.

        Raises:
            RuntimeException:
                If the shard shuts down before it was READY.
        """
        run_task = compat.asyncio.create_task(self._run_shard(shard), name=f"poll shard {shard.shard_id} for events")
        ready_task = compat.asyncio.create_task(
            shard.ready_event.wait(), name=f"wait for shard {shard.shard_id} to be READY"
        )

        _, pending_tasks = await asyncio.wait([run_task, ready_task], return_when=asyncio.FIRST_COMPLETED)

        if run_task.done() and not ready_task.done():
            ready_task.cancel()
            _, reason = await run_task
            ex = reason if isinstance(reason, Exception) else None
            raise RuntimeError(f"Shard {shard.shard_id} did not manage to become ready") from ex

        return shard, run_task

    async def start(self) -> typing.Mapping[typing.Optional[int], asyncio.Task]:
        """
        Starts the client. This will initialize any shards, and wait for them to become READY. Once
        that has occurred, this coroutine will return, allowing you to run other coroutines in the
        background.

        All shards are started concurrently at the same time to reduce startup waiting times.

        Returns:
            An immutable mapping of shard IDs to their respective tasks that they are running within. The tasks will,
            when awaited, wait for the corresponding shard to be READY.
        """
        assertions.assert_that(self._shard_tasks is None, "client is already started", RuntimeError)
        await self._init_new_application_fabric()
        waiters = (self._start_shard_and_wait_ready(shard) for shard in self._fabric.gateways.values())
        shard_tasks = await asyncio.gather(*waiters)
        self._shard_tasks = {shard.shard_id: task for shard, task in shard_tasks}
        return types.MappingProxyType(self._shard_tasks)

    async def join(self):
        """
        Waits for the client to shut down. This can be used to keep the event loop running after calling
        :func:`start` and initializing any other resources you need.
        """
        assertions.assert_that(self._shard_tasks is not None, "client is not started", RuntimeError)
        dead_tasks, pending_tasks = await asyncio.wait(self._shard_tasks.values(), return_when=asyncio.FIRST_EXCEPTION)
        for failure in dead_tasks:
            shard_id, reason = failure.result()
            self.logger.exception("shard %s has shut down", shard_id, exc_info=reason)

            reason = reason if isinstance(reason, BaseException) else None
            if not self._quieting_down:
                raise RuntimeError(f"shard {shard_id} has shut down") from reason

    async def run(self):
        """
        An alias for :func:`start` and then :func:`join`. Runs the client and waits for it to finish.
        """
        await self.start()
        await self.join()

    async def close(self):
        """
        Shuts the client down. This closes the HTTP client session and kills every running shard
        before returning.
        """
        assertions.assert_that(self._shard_tasks is not None, "client is not started")
        self._quieting_down = True
        await self._fabric.http_api.close()
        gateway_tasks = []
        for shard_id, shard in self._fabric.gateways.items():
            self.logger.info("shutting down shard %s", shard_id)
            shutdown_task = compat.asyncio.create_task(shard.close(), name=f"waiting for shard {shard_id} to close")
            gateway_tasks.append(shutdown_task)
        await asyncio.wait(gateway_tasks, return_when=asyncio.ALL_COMPLETED)

    def dispatch(self, event: str, *args) -> None:
        """
        Dispatches an event to any listeners.

        Args:
            event:
                The event name to dispatch.
            *args:
                Any arguments to pass to the event.

        Note:
            any event is dispatched as a future asynchronously. This will not wait for that to occur.
        """
        self._event_dispatcher.dispatch(event, *args)

    def add_event(self, event_name: str, coroutine_function: aio.CoroutineFunctionT) -> None:
        """
        Subscribes the given event coroutine function to the given event name.

        Args:
            event_name:
                The event to add to.
            coroutine_function:
                The coroutine function callback to add.
        """
        self.logger.debug(
            "subscribing %s%s to %s event",
            coroutine_function.__name__,
            inspect.signature(coroutine_function),
            event_name,
        )
        self._event_dispatcher.add(event_name, coroutine_function)

    def remove_event(self, event_name: str, coroutine_function: aio.CoroutineFunctionT) -> None:
        """
        Unsubscribes the given event coroutine function from the given event name, if it is there.

        Args:
            event_name:
                The event to remove from.
            coroutine_function:
                The coroutine function callback to remove.
        """
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

        >>> @client.event()
        ... async def on_message_create(message):
        ...     if not message.author.is_bot and message.content == "!ping":
        ...         await message.channel.send("pong!")

        >>> @client.event("message_create")
        ... async def ping_pong(message):
        ...     if not message.author.is_bot and message.content == "!ping":
        ...         await message.channel.send("pong!")
        """
        assertions.assert_that(
            isinstance(name, str) or name is None,
            "Invalid use of @client.event() decorator.\n"
            "\n"
            "  Valid usage of this decorator is as follows:\n"
            "\n"
            "    @client.event()\n"
            "    async def on_message_create(message):\n"
            "        ...\n"
            "\n"
            "  ...or...\n"
            "\n"
            "    @client.event('message_create')\n"
            "    async def some_name_here(message):\n"
            "        ...\n",
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
        """
        The average heartbeat latency across all gateway shard connections. If any are not running, you will receive
        a :class:`float` with the value of `NaN` instead.
        """
        if len(self._fabric.gateways) == 0:
            # Bot has not yet started.
            return float("nan")
        return sum(shard.heartbeat_latency for shard in self._fabric.gateways.values()) / len(self._fabric.gateways)

    @property
    def heartbeat_latencies(self) -> typing.Mapping[typing.Optional[int], float]:
        """
        Creates a mapping of each shard ID to the latest heartbeat latency for that shard.
        """
        return {shard.shard_id: shard.heartbeat_latency for shard in self._fabric.gateways.values()}
