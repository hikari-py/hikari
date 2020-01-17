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

    # TODO: reimplement this sharding stuff.

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
