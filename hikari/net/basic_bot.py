#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019
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
A basic HTTP/Gateway client for a simple lightweight bot. This does not use any fancy models, stores no state
information, and provides no command subsystem.
"""
import logging
from hikari import utils

from hikari.compat import asyncio
from hikari.compat import typing
from hikari.net import debug
from hikari.net import http
from hikari.net import gateway

DispatchFunction = typing.Callable[[str, utils.ObjectProxy], typing.Awaitable[None]]


class BasicBot:
    """
    A very basic bot client. This provides no form of state caching and no pretty transformations into object-oriented
    models. Every payload is a dict (or a dict wrapped within a :class:`DiscordObjectProxy`) and you have to implement
    event dispatching yourself.

    .. code-block::

        import logging
        import os

        from hikari.net import basic_bot
        from hikari import utils

        logging.basicConfig(level='INFO')


        async def dispatch_event(event: str, payload: utils.ObjectProxy):
            if event == 'MESSAGE_CREATE':
                if payload.content == 'hk.ping':
                    latency = bot.gateway.heartbeat_latency
                    if latency == float('nan'):
                        response = 'No heartbeat has occurred yet'
                    else:
                        response = f'Pong {latency * 1_000:.2f}ms'
                    await bot.http.create_message(payload.channel_id, content=response)


        bot = basic_bot.BasicBot(os.environ["TOKEN"], dispatch_event)
        bot.run()

    Args:
        token:
            The token to use for authentication.
        dispatch:
            A :attr:`DispatchFunction` to invoke when an event occurs.
        loop:
            The :class:`asyncio.AbstractEventLoop` to use for the event loop.
        **http_kwargs:
            Arguments to pass to the :class:`http.HTTPClient` constructor.

    """

    def __init__(
        self, token: str, dispatch: DispatchFunction, loop: asyncio.AbstractEventLoop = None, **http_kwargs
    ) -> None:
        loop = loop or asyncio.get_event_loop()
        self.logger = logging.getLogger(BasicBot.__name__)
        self.loop: asyncio.AbstractEventLoop = loop
        self.dispatch: DispatchFunction = dispatch
        self.token: str = token
        self.http: http.HTTPClient = http.HTTPClient(token=token, loop=loop, **http_kwargs)
        self.gateway: typing.Optional[gateway.GatewayClient] = None

    async def start(self, **gateway_kwargs) -> None:
        """
        Starts the bot connection to the gateway.

        Args:
            **gateway_kwargs:
                any additional arguments to pass to the :class:`gateway.GatewayClient`
        """
        data = await debug.get_debug_data()
        self.logger.info("Your data center is %s", data.colo)

        url = await self.http.get_gateway()
        self._init_gateway(url, **gateway_kwargs)
        await self.gateway.run()

    def run(self, **gateway_kwargs):
        """
        Run the basic bot.

        Args:
            **gateway_kwargs:
                any additional arguments to pass to the :class:`gateway.GatewayClient`

        """
        self.loop.run_until_complete(self.start(**gateway_kwargs))

    def _init_gateway(self, url, **gateway_kwargs):
        self.gateway = gateway.GatewayClient(
            host=url, token=self.token, loop=self.loop, dispatch=self._dispatch, **gateway_kwargs
        )

    async def _dispatch(self, event_name: str, payload: dict):
        # pylint: disable=broad-except
        try:
            self.logger.info("Handling incoming event %s", event_name)
            await self.dispatch(event_name, utils.ObjectProxy(payload))
        except Exception as ex:
            self.logger.exception("An exception occurred in your event handler", exc_info=ex)
        # pylint: enable=broad-except
