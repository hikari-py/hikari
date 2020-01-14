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
import contextlib
import datetime
import inspect
import signal
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

    _SHUTDOWN_SIGNALS = (signal.SIGINT, signal.SIGTERM)

    def __init__(self, token: str, options: typing.Optional[client_options.ClientOptions] = None) -> None:
        self._client_options = options or client_options.ClientOptions()
        self._event_dispatcher = aio.MuxMap()
        self._fabric: typing.Optional[fabric.Fabric] = None
        self.logger = loggers.get_named_logger(self)
        self.token = token
        self._shard_tasks = None

    async def _init_new_application_fabric(self):
        self._fabric = fabric.Fabric()

        try:
            self._fabric.state_registry = await self._new_state_registry()
            self._fabric.event_handler = await self._new_event_handler()
            self._fabric.http_api = await self._new_http_api()
            self._fabric.http_adapter = await self._new_http_adapter()
            self._fabric.gateways = await self._new_shard_map()
            self._fabric.chunker = await self._new_chunker()
        except Exception as ex:
            self.logger.exception("failed to start a new client", exc_info=ex)
            await self.close()
            self._fabric = None
            raise RuntimeError("failed to initialize application fabric fully")

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

        # Use comparison rather than identify, this lets the user unmarshal a JSON file using lib X if they wish
        # to load config from file directly into the bot.
        if self._client_options.shards == client_options.AUTO_SHARD:
            gateway_bot = await self._fabric.http_adapter.fetch_gateway_bot()
            self.logger.info("The gateway has recommended %s shards for this bot", gateway_bot.shards)

            # Hope this cannot go below zero, but who knows with Discord.
            if gateway_bot.session_start_limit.remaining <= 0:
                raise RuntimeError(
                    "You have hit your IDENTIFY limit. I won't proceed to log in as your token will "
                    "be reset if I do this. Please rectify the issue manually and try again."
                )

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
                http_timeout=self._client_options.http_timeout,
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

    def run(self) -> None:
        """
        Executes the bot on the current event loop and blocks until it is complete.
        Also registers several operating system signal handlers internally to handle shutting the bot
        down cleanly on interrupts.

        Warning:
            This will not close the event loop being run on, and will take over consuming various
            low-level system interrupt signals until the client shuts down.

        Note:
            If you instead wish to start the bot from within a coroutine, you
            should await :meth:`run_async` instead. This is more useful if you have other resources
            you wish to handle the shutdown of, such as database connection pools.
        """
        asyncio.get_event_loop().run_until_complete(self.run_async())

    def _signal_handler(self, triggered_signal_id, loop):
        self.logger.critical(
            "%s signal received. Will shut client down now.", compat.signal.strsignal(triggered_signal_id)
        )
        asyncio.run_coroutine_threadsafe(self.close(), loop)

    async def run_async(self) -> None:
        """
        Equivalent to running :meth:`start` and :meth:`join`, but also manages registering
        signal handlers to detect interrupts if invoked on the main thread.

        For example, an `asyncpg` connection pool could be managed like so:

        .. code-block:: python

            bot = client.Client(...)

            async def main():
                async with asyncpg.create_pool(...) as bot.db:
                    await bot.run_async()

            asyncio.run(main())

        ...this example would ensure the database is shut down cleanly on any interrupt occurring, or any
        persistent connection issue occurring.

        Warning:
            As per the implementation of :meth:`asyncio.AbstractEventLoop.add_signal_handler`, the signal
            handlers may only be registered if the loop is bound and running to the main thread. If this
            is not true, then the signal is just not registered.

            If you are running this client on a child thread for this application, you must manage
            consuming interrupts and safely closing this client manually.
        """
        loop = asyncio.get_event_loop()

        registered_signals = set()
        for signal_id in self._SHUTDOWN_SIGNALS:
            # This may occur in several situations! We might not have the signal on our system, or we might not
            # be on the main thread, in which case, we can't do much more about this.
            with contextlib.suppress(Exception):
                loop.add_signal_handler(signal_id, self._signal_handler, signal_id, loop)
                registered_signals.add(signal_id)

        try:
            await self.start()
            await self.join()
        except KeyboardInterrupt:
            self._signal_handler(signal.SIGINT, loop)
        finally:
            # Clear signal handlers if we can...
            for signal_id in registered_signals:
                with contextlib.suppress(Exception):
                    loop.remove_signal_handler(signal_id)

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

    async def join(self) -> None:
        """
        Waits for the client to shut down. This can be used to keep the event loop running after calling
        :func:`start` and initializing any other resources you need.

        Raises:
            The exception that the first shard to shut down provided us. If no exceptions were provided, then
            this is ignored.

        All other shards will be disconnected.
        """
        assertions.assert_that(self._shard_tasks is not None, "client is not started", RuntimeError)
        dead_tasks, pending_tasks = await asyncio.wait(self._shard_tasks.values(), return_when=asyncio.FIRST_COMPLETED)

        first_ex = None
        for dead_task in dead_tasks:
            shard, result = dead_task.result()
            if isinstance(result, Exception):
                self.logger.exception("shard %s raised a fatal exception", shard.shard_id, exc_info=result)
                if first_ex is None and isinstance(result, Exception):
                    first_ex = result
            else:
                self.logger.warning("shard %s shut down permanently with result %s", shard.shard_id, result)

        await self.close()

        # Ignore any further errors.
        await asyncio.gather(*pending_tasks, return_exceptions=True)

        if first_ex is not None:
            raise first_ex

    async def close(self):
        """
        Shuts the client down. This closes the HTTP client session and kills every running shard
        before returning once everything has shut down.
        """
        await self._fabric.http_api.close()
        gateway_tasks = []
        for shard_id, shard in self._fabric.gateways.items():
            if shard.is_running:
                self.logger.info("shutting down shard %s", shard_id)
                shutdown_task = compat.asyncio.create_task(shard.close(), name=f"waiting for shard {shard_id} to close")
                gateway_tasks.append(shutdown_task)

        if gateway_tasks:
            await asyncio.wait(gateway_tasks, return_when=asyncio.ALL_COMPLETED)

        # Make all remaining tasks cancel if they hung or refused to shut down...
        # Check the shard tasks map is populated first to make sure we don't just try closing it when it isn't
        # yet populated (e.g. if we fail to make a fabric because of a connection error during
        # _init_new_application_fabric, as we still rely on this call to ensure the HTTP API is closed.
        #
        # This also prevents strange errors hitting the user if they misuse close, as managing multiple shards
        # safely is pretty unforgiving...
        if self._shard_tasks is not None:
            for task in self._shard_tasks.values():
                task.cancel()

    def dispatch(self, event: str, *args) -> None:
        """
        Dispatches an event to any listeners.

        Args:
            event:
                The event name to dispatch.
            *args:
                Any arguments to pass to the event.

        Note:
            Any event is dispatched as a future asynchronously. This will not wait for that to occur.
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
                function itself is used, minus the word **on_** if present at the start.

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
            RuntimeError,
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
        if self._fabric and len(self._fabric.gateways) == 0:
            # Bot has not yet started.
            return float("nan")
        return sum(shard.heartbeat_latency for shard in self._fabric.gateways.values()) / len(self._fabric.gateways)

    @property
    def heartbeat_latencies(self) -> typing.Mapping[typing.Optional[int], float]:
        """
        Creates a mapping of each shard ID to the latest heartbeat latency for that shard.
        """
        if self._fabric:
            return {shard.shard_id: shard.heartbeat_latency for shard in self._fabric.gateways.values()}
        return {}
