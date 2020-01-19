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
import signal
import typing

from hikari import client_options
from hikari.internal_utilities import aio
from hikari.internal_utilities import assertions
from hikari.internal_utilities import loggers
from hikari.net import errors
from hikari.net import gateway
from hikari.net import http_client
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

    def __init__(
        self,
        token: str,
        loop: typing.Optional[asyncio.AbstractEventLoop] = None,
        options: typing.Optional[client_options.ClientOptions] = None,
    ) -> None:
        self._client_options = options or client_options.ClientOptions()
        self._event_dispatcher = aio.MuxMap()
        self._fabric: typing.Optional[fabric.Fabric] = None
        self._shard_keepalive_tasks = {}
        self.logger = loggers.get_named_logger(self)
        self.token = token

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

            if isinstance(shard_ids, client_options.ShardOptions):
                if isinstance(shard_ids.shards, slice):
                    shard_count = shard_ids.shard_count
                    shard_ids = [i for i in range(shard_ids.shards.start, shard_ids.shards.stop, shard_ids.shards.step)]
                else:
                    shard_ids, shard_count = list(shard_ids.shards), shard_ids.shard_count
            else:
                shard_count = 1
                shard_ids = [0]

        shard_map = {}
        for shard_id in shard_ids:
            shard_map[shard_id] = gateway.GatewayClient(
                dispatch=self._fabric.event_handler.consume_raw_event,
                debug=self._client_options.debug,
                token=self.token,
                url=url,
                connector=self._client_options.connector,
                proxy_headers=self._client_options.proxy_headers,
                proxy_auth=self._client_options.proxy_auth,
                proxy_url=self._client_options.proxy_url,
                ssl_context=self._client_options.ssl_context,
                verify_ssl=self._client_options.verify_ssl,
                http_timeout=self._client_options.http_timeout,
                large_threshold=self._client_options.large_guild_threshold,
                guild_subscriptions=self._client_options.enable_guild_subscription_events,
                initial_presence=self._client_options.presence.to_dict(),
                shard_id=shard_id,
                shard_count=shard_count,
            )

        return shard_map

    async def _new_chunker(self):
        return basic_chunker_impl.BasicChunkerImpl(self._fabric)

    async def _shard_keepalive(self, shard: gateway.GatewayClient) -> None:
        self.logger.debug("starting keepalive task for shard %s", shard.shard_id)
        while True:
            connect_task = asyncio.create_task(shard.connect())
            try:
                await connect_task
                self.logger.critical("shard %s shut down silently! this shouldn't happen!", shard.shard_id)
                shard.close()
                await connect_task

            except errors.GatewayZombiedError:
                self.logger.warning("shard %s has entered a zombie state and will be restarted", shard.shard_id)
                shard.close()
                await connect_task

            except errors.GatewayInvalidSessionError as ex:
                if ex.can_resume:
                    self.logger.warning("shard %s has an invalid session, so will attempt to resume", shard.shard_id)
                else:
                    self.logger.warning("shard %s has an invalid session, so will attempt to reconnect", shard.shard_id)

                shard.close()
                await connect_task

                if not ex.can_resume:
                    shard.seq = None
                    shard.session_id = None

            except errors.GatewayMustReconnectError:
                self.logger.warning("shard %s has been instructed by Discord to reconnect", shard.shard_id)
                shard.close()
                await connect_task
                shard.seq = None
                shard.session_id = None
            except Exception as ex:
                self.logger.debug("propagating exception after tidying up shard %s", shard.shard_id, exc_info=ex)
                shard.close()
                await connect_task
                raise ex

    async def start(self):
        await self._init_new_application_fabric()
        for shard in self._fabric.gateways.values():
            self._shard_keepalive_tasks[shard] = asyncio.create_task(self._shard_keepalive(shard))
        try:
            await asyncio.gather(*self._shard_keepalive_tasks.values())
        finally:
            await self.close()

    async def close(self):
        for shard in self._fabric.gateways.values():
            if not shard.closed_event.is_set():
                self.logger.info("requesting shard %s shuts down now", shard.shard_id)
                shard.close()

    def run(self):
        try:
            self.logger.info("starting bot")
            self.loop.run_until_complete(self.start())
        except KeyboardInterrupt:
            self.logger.info("received KeyboardInterrupt to shut down bot")
        finally:
            self.logger.info("bot has shut down")

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
