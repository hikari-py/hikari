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
import time
import typing

import aiohttp

from hikari.internal_utilities import aio
from hikari.internal_utilities import assertions
from hikari.internal_utilities import containers
from hikari.internal_utilities import loggers
from hikari.net import errors
from hikari.net import gateway
from hikari.net import http_client
from hikari.net import ratelimits
from hikari.orm import fabric, client_options
from hikari.orm.gateway import basic_chunker_impl
from hikari.orm.gateway import dispatching_event_adapter_impl
from hikari.orm.gateway import event_types
from hikari.orm.http import http_adapter_impl
from hikari.orm.state import state_registry_impl

if typing.TYPE_CHECKING:
    from hikari.internal_utilities import type_hints


class Client:
    """
    A highly configurable implementation of a client for running a Discord bot. This contains logic wrapped around
    orchestrating all of the internal components to work together correctly, autosharding where appropriate,
    initializing all internal components, as well as registering and dispatching events.

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
    >>> client.run()
    """

    _SHARD_IDENTIFY_WAIT = 5.0
    _SHUTDOWN_SIGNALS = (signal.SIGINT, signal.SIGTERM)

    def __init__(
        self,
        token: str,
        loop: type_hints.Nullable[asyncio.AbstractEventLoop] = None,
        options: type_hints.Nullable[client_options.ClientOptions] = None,
    ) -> None:
        self._client_options = options or client_options.ClientOptions()
        self._event_dispatcher = aio.EventDelegate()
        self._fabric: type_hints.Nullable[fabric.Fabric] = None
        self._shard_keepalive_tasks: typing.Dict[gateway.GatewayClient, asyncio.Task] = {}
        self.logger = loggers.get_named_logger(self)
        self.token = token
        self.is_closed = False

        try:
            self.loop = loop or asyncio.get_event_loop()
        except RuntimeError:
            # No event loop is on this thread yet.
            raise RuntimeError("No event loop is running on this thread. Please make one and set it explicitly.")

    async def _init_new_application_fabric(self):
        self._fabric = fabric.Fabric()

        try:
            self._fabric.state_registry = await self._new_state_registry()
            self._fabric.event_handler = await self._new_event_handler()
            self._fabric.http_client = await self._new_http_client()
            self._fabric.http_adapter = await self._new_http_adapter()
            self._fabric.gateways, self._fabric.shard_count = await self._new_shard_map()
            self._fabric.chunker = await self._new_chunker()
        except Exception as ex:
            self.logger.exception("failed to start a new client", exc_info=ex)
            self._fabric = None

            # Again, something is already going wrong
            try:
                await self.shutdown()
            finally:
                raise RuntimeError("failed to initialize application fabric fully")

    async def _new_state_registry(self):
        return state_registry_impl.StateRegistryImpl(
            self._fabric, self._client_options.max_message_cache_size, self._client_options.max_user_dm_channel_count,
        )

    async def _new_event_handler(self):
        return dispatching_event_adapter_impl.DispatchingEventAdapterImpl(
            self._fabric, self.dispatch, request_chunks_mode=self._client_options.chunk_mode,
        )

    async def _new_http_client(self):
        return http_client.HTTPClient(
            allow_redirects=self._client_options.allow_redirects,
            token=f"Bot {self.token}",
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

        if not isinstance(shard_ids, client_options.ShardOptions):
            raise RuntimeError(
                "shard_ids in client options was not a valid type or value.\n"
                "\n"
                "When specifying the shards you wish to use in this setting, you have a few options for what you can \n"
                "set it to:\n",
                "   1. Do not specify anything for it. This will default it to `hikari.client_options.AUTO_SHARD` \n"
                "      which will ask the gateway for the most appropriate settings for your bot on start up.\n"
                "   2. Set it to `hikari.client_options.NO_SHARDING`. This will turn sharding off and use a single \n"
                "      gateway for your bot.\n"
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
            self.logger.info("the gateway has recommended %s shard(s) for this bot", gateway_bot.shards)

            # Hope this cannot go below zero, but who knows with Discord.
            if gateway_bot.session_start_limit.remaining <= 0:
                raise RuntimeError(
                    "you have hit your IDENTIFY limit. I won't proceed to log in as your token will "
                    "be reset if I do this. Please rectify the issue manually and try again."
                )

            self.logger.info(
                "you have performed an IDENTIFY %s times recently. You may IDENTIFY %s more times before your "
                "token gets reset by Discord. This limit resets at %s (%s from now)",
                gateway_bot.session_start_limit.used,
                gateway_bot.session_start_limit.remaining,
                gateway_bot.session_start_limit.reset_at,
                gateway_bot.session_start_limit.reset_at - datetime.datetime.now(tz=datetime.timezone.utc),
            )

            url = gateway_bot.url

            shard_ids = range(gateway_bot.shards)
            shard_count = gateway_bot.shards
        else:
            url = await self._fabric.http_adapter.gateway_url

            if isinstance(shard_ids.shards, slice):
                shard_count = shard_ids.shard_count
                shard_ids = [
                    i
                    for i in range(
                        shard_ids.shards.start if shard_ids.shards.start else 0,
                        shard_ids.shards.stop,
                        shard_ids.shards.step if shard_ids.shards.step else 1,
                    )
                ]
            else:
                shard_ids, shard_count = list(shard_ids.shards), shard_ids.shard_count

        shard_map = {}
        for shard_id in shard_ids:
            shard_map[shard_id] = gateway.GatewayClient(
                dispatch=self._fabric.event_handler.consume_raw_event,
                debug=self._client_options.debug,
                intents=self._client_options.gateway_intents,
                token=self.token,
                url=url,
                connector=self._client_options.connector,
                proxy_headers=self._client_options.proxy_headers,
                proxy_auth=self._client_options.proxy_auth,
                proxy_url=self._client_options.proxy_url,
                ssl_context=self._client_options.ssl_context,
                verify_ssl=self._client_options.verify_ssl,
                large_threshold=self._client_options.large_guild_threshold,
                initial_presence=self._client_options.presence.to_dict(),
                shard_id=shard_id,
                shard_count=shard_count,
            )

        return shard_map, shard_count

    async def _new_chunker(self):
        return basic_chunker_impl.BasicChunkerImpl(self._fabric)

    async def _shard_keep_alive(self, shard: gateway.GatewayClient) -> None:
        self.logger.debug("starting keepalive task for shard %s", shard.shard_id)

        backoff = ratelimits.ExponentialBackOff(maximum=-1)
        last_start = time.perf_counter()
        do_not_backoff = True

        while True:
            try:
                if not do_not_backoff and time.perf_counter() - last_start < 30:
                    next_backoff = next(backoff)
                    self.logger.info(
                        "shard %s has restarted within 30 seconds, will backoff for %ss", shard.shard_id, next_backoff,
                    )
                    await asyncio.sleep(next_backoff)
                else:
                    backoff.reset()

                last_start = time.perf_counter()

                do_not_backoff = False
                await shard.connect()
                self.logger.critical("shard %s shut down silently! this shouldn't happen!", shard.shard_id)

            except aiohttp.ClientConnectorError as ex:
                self.logger.exception(
                    "shard %s has failed to connect to Discord to initialize a websocket connection",
                    shard.shard_id,
                    exc_info=ex,
                )
            except errors.GatewayZombiedError:
                self.logger.warning("shard %s has entered a zombie state and will be restarted", shard.shard_id)
            except errors.GatewayInvalidSessionError as ex:
                if ex.can_resume:
                    self.logger.warning("shard %s has an invalid session, so will attempt to resume", shard.shard_id)
                else:
                    self.logger.warning("shard %s has an invalid session, so will attempt to reconnect", shard.shard_id)

                if not ex.can_resume:
                    shard.seq = None
                    shard.session_id = None
                do_not_backoff = True
                await asyncio.sleep(5)
            except errors.GatewayMustReconnectError:
                self.logger.warning("shard %s has been instructed by Discord to reconnect", shard.shard_id)
                shard.seq = None
                shard.session_id = None
                do_not_backoff = True
                await asyncio.sleep(5)
            except errors.GatewayConnectionClosedError:
                self.logger.warning("shard %s has been disconnected, will attempt to reconnect", shard.shard_id)
            except errors.GatewayClientClosedError:
                self.logger.warning("shard %s has shut down because the client is closing", shard.shard_id)
                return
            except Exception as ex:
                self.logger.debug("propagating exception %s", shard.shard_id, exc_info=ex)
                raise ex

    async def start(self):
        """
        Starts all shards without hitting the identify rate limit, but will not block afterwards.

        Warning:
            If any exception occurs, this will not close the client. You must catch any exception and/or signal
            yourself and invoke :meth:`shutdown` manually.

            For a complete solution to running a client with appropriate exception and signal handling, see
            :meth:`run`.

            Note that closing the client is the only way to invoke any shutdown events that are registered correctly.
        """
        await self.dispatch(event_types.EventType.PRE_STARTUP)
        await self._init_new_application_fabric()

        for shard in self._fabric.gateways.values():
            if shard.shard_id > 0:
                # https://github.com/discordapp/discord-api-docs/issues/1328

                # Discord will make us have an invalid session if we identify twice within 5 seconds. If we get
                # disconnected after identifying for any other reason, tough luck I guess.
                # This stops this framework chewing up your precious identify counts for the day because of spam
                # causing invalid sessions.
                await asyncio.sleep(self._SHARD_IDENTIFY_WAIT)

            self._shard_keepalive_tasks[shard] = asyncio.create_task(self._shard_keep_alive(shard))
            await shard.identify_event.wait()

        await self.dispatch(event_types.EventType.POST_STARTUP)

    async def join(self):
        """
        Wait for shards to shut down. This can be used to keep your bot running after starting it.

        Warning:
            If any exception occurs, this will not close the client. You must catch any exception and/or signal
            yourself and invoke :meth:`shutdown` manually.

            For a complete solution to running a client with appropriate exception and signal handling, see
            :meth:`run`.

            Note that closing the client is the only way to invoke any shutdown events that are registered correctly.
        """
        await asyncio.gather(*self._shard_keepalive_tasks.values())

    async def destroy(self):
        """
        Destroys all shards without waiting for them to shut down properly first.

        Warning:
            You do not generally want to call this unless you want your bot to stop immediately.
            This will not invoke any shutdown events.

            If you simply wish to programmatically shut your bot down, you can just call
            :meth:`shutdown`.
        """
        for shard, task in self._shard_keepalive_tasks.items():
            if not task.done():
                self.logger.warning("destroying shard %s", shard.shard_id)
                task.cancel()

    async def shutdown(
        self, shard_timeout: type_hints.Nullable[float] = None,
    ):
        """
        Requests that the client safely shuts down any running shards.

        Args:
            shard_timeout:
                The time to wait for shards to shut down before forcefully destroying them. This
                defaults to `None`.
        """
        if self.is_closed:
            return

        self.logger.warning("client is shutting down permanently")

        await self.dispatch(event_types.EventType.PRE_SHUTDOWN)

        coros = []

        if self._fabric is not None:
            self._fabric.chunker.close()

            for shard in self._fabric.gateways.values():
                if not shard.requesting_close_event.is_set():
                    self.logger.debug("requesting shard %s shuts down now", shard.shard_id)
                    coros.append(shard.close())

            try:
                async with aio.maybe_timeout(shard_timeout):
                    if coros:
                        await asyncio.gather(*coros)
            except Exception as ex:
                self.logger.exception("failed to shut down shards safely, will destroy them instead", exc_info=ex)

        self.is_closed = True
        self.logger.warning("closing HTTP connection pool")

        try:
            # If we can't shut this down, we can't do much else. It is probably a bug.
            await self._fabric.http_client.close()
        except Exception as ex:
            self.logger.debug("failed to close HTTP client", exc_info=ex)
        finally:
            await self.dispatch(event_types.EventType.POST_SHUTDOWN)
            await self.destroy()

    def run(self):
        """
        Runs the client on the event loop associated with this :class:`Client`. This is similar to invoking
        :meth:`start` and then :meth:`join`, but has signal handling for OS signals such as `SIGINT` (which
        triggers a :class:`KeyboardInterrupt`), and `SIGTERM`, which is invoked when the OS politely requests
        that the process shuts down. This will also ensure that :meth:`shutdown` is invoked correctly
        regardless of how the client terminated.
        """
        self.logger.info("starting client")

        def sigterm_handler(*_):
            raise KeyboardInterrupt()

        try:
            # Not implemented on Windows
            with contextlib.suppress(NotImplementedError):
                self.loop.add_signal_handler(signal.SIGTERM, sigterm_handler)

            self.loop.run_until_complete(self.start())
            self.loop.run_until_complete(self.join())
        except KeyboardInterrupt:
            self.logger.info("received signal to shut down client")
        finally:

            self.loop.run_until_complete(self.shutdown())

            # Not implemented on Windows
            with contextlib.suppress(NotImplementedError):
                self.loop.remove_signal_handler(signal.SIGTERM)

            self.logger.info("client has shut down")

    def dispatch(self, event: str, *args):
        """
        Dispatches an event to any listeners.

        Args:
            event:
                The event name to dispatch.
            *args:
                Any arguments to pass to the event.

        Returns:
            The gathering future for any event handlers that will be dispatched, or a completed
            future with no result if no event handlers existed for this event. You may optionally
            await this future if you want to ensure you wait for all dispatchers to be executed,
            (for example, when handling shutdown event logic), but generally you should not
            await this result, as that will allow it to execute asynchronously.
        """
        self.logger.debug("dispatching event %s with %s args", event, len(args))
        return self._event_dispatcher.dispatch(event, *args)

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
        Un-subscribes the given event coroutine function from the given event name, if it is there.

        Args:
            event_name:
                The event to remove from.
            coroutine_function:
                The coroutine function callback to remove.
        """
        self.logger.debug(
            "un-subscribing %s%s from %s event",
            coroutine_function.__name__,
            inspect.signature(coroutine_function),
            event_name,
        )
        self._event_dispatcher.remove(event_name, coroutine_function)

    def event(
        self, name: type_hints.Nullable[str] = None
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
        if self._fabric and len(self._fabric.gateways) != 0:
            return sum(shard.heartbeat_latency for shard in self._fabric.gateways.values()) / len(self._fabric.gateways)
        # Bot has not yet started.
        return float("nan")

    @property
    def heartbeat_latencies(self) -> typing.Mapping[int, float]:
        """
        A mapping of each shard ID to the latest heartbeat latency for that shard.
        """
        if self._fabric:
            return {shard.shard_id: shard.heartbeat_latency for shard in self._fabric.gateways.values()}
        return containers.EMPTY_DICT

    @property
    def shards(self) -> typing.Mapping[int, gateway.GatewayClient]:
        """
        A mapping of each shard running, mapping the shard ID to the shard instance itself.
        """
        if self._fabric:
            return {shard.shard_id: shard for shard in self._fabric.gateways.values()}
        return containers.EMPTY_DICT
