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
from __future__ import annotations

__all__ = ["IGatewayZookeeper"]

import abc
import asyncio
import contextlib
import datetime
import signal
import typing

from hikari.api import base_app
from hikari.models import guilds

if typing.TYPE_CHECKING:
    from hikari.api import event_consumer
    from hikari import gateway


class IGatewayZookeeper(base_app.IBaseApp, abc.ABC):
    """Component specialization that looks after a set of shards.

    These events will be produced by a low-level gateway implementation, and
    will produce `list` and `dict` types only.

    This may be combined with `IGatewayDispatcher` for most single-process
    bots, or may be a specific component for large distributed applications
    that feed new events into a message queue, for example.
    """

    __slots__ = ()

    @property
    @abc.abstractmethod
    def event_consumer(self) -> event_consumer.IEventConsumer:
        """Raw event consumer."""

    @property
    @abc.abstractmethod
    def gateway_shards(self) -> typing.Mapping[int, gateway.Gateway]:
        """Mapping of each shard ID to the corresponding client for it."""

    @property
    @abc.abstractmethod
    def shard_count(self) -> int:
        """The number of shards in the entire distributed application."""

    @abc.abstractmethod
    async def start(self) -> None:
        """Start all shards and wait for them to be READY."""

    @abc.abstractmethod
    async def join(self) -> None:
        """Wait for all shards to shut down."""

    @abc.abstractmethod
    async def update_presence(
        self,
        *,
        status: guilds.PresenceStatus = ...,
        activity: typing.Optional[gateway.Activity] = ...,
        idle_since: typing.Optional[datetime.datetime] = ...,
        is_afk: bool = ...,
    ) -> None:
        """Update the presence of the user for all shards.

        This will only update arguments that you explicitly specify a value for.
        Any arguments that you do not explicitly provide some value for will
        not be changed.

        !!! warning
            This will only apply to connected shards.

        !!! note
            If you wish to update a presence for a specific shard, you can do
            this by using the `gateway_shards` `typing.Mapping` to find the
            shard you wish to update.

        Parameters
        ----------
        status : hikari.models.guilds.PresenceStatus
            If specified, the new status to set.
        activity : hikari.models.gateway.Activity | None
            If specified, the new activity to set.
        idle_since : datetime.datetime | None
            If specified, the time to show up as being idle since,
            or `None` if not applicable.
        is_afk : bool
            If specified, `True` if the user should be marked as AFK,
            or `False` otherwise.
        """

    def run(self) -> None:
        """Execute this component on an event loop.

        Performs the same job as `RunnableClient.start`, but provides additional
        preparation such as registering OS signal handlers for interrupts,
        and preparing the initial event loop.

        This enables the client to be run immediately without having to
        set up the `asyncio` event loop manually first.
        """
        loop = asyncio.get_event_loop()

        def sigterm_handler(*_):
            raise KeyboardInterrupt()

        ex = None

        try:
            with contextlib.suppress(NotImplementedError):
                # Not implemented on Windows
                loop.add_signal_handler(signal.SIGTERM, sigterm_handler)

            loop.run_until_complete(self.start())
            loop.run_until_complete(self.join())

            self.logger.info("client has shut down")

        except KeyboardInterrupt as _ex:
            self.logger.info("received signal to shut down client")
            loop.run_until_complete(self.close())
            # Apparently you have to alias except clauses or you get an
            # UnboundLocalError.
            ex = _ex
        finally:
            loop.run_until_complete(self.close())
            with contextlib.suppress(NotImplementedError):
                # Not implemented on Windows
                loop.remove_signal_handler(signal.SIGTERM)

        if ex:
            raise ex from ex
