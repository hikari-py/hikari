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
"""Interface for gateway zookeeper applications."""

from __future__ import annotations

__all__: typing.Final[typing.Sequence[str]] = ["IGatewayZookeeperApp"]

import abc
import typing

from hikari.api import event_consumer
from hikari.utilities import undefined

if typing.TYPE_CHECKING:
    import datetime

    from hikari.models import presences
    from hikari.net import gateway


class IGatewayZookeeperApp(event_consumer.IEventConsumerApp, abc.ABC):
    """Component specialization that looks after a set of shards.

    These events will be produced by a low-level gateway implementation, and
    will produce `list` and `dict` types only.

    This may be combined with `IEventDispatcherApp` for most single-process
    bots, or may be a specific component for large distributed applications
    that feed new events into a message queue, for example.
    """

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def shards(self) -> typing.Mapping[int, gateway.Gateway]:
        """Map of each shard ID to the corresponding client for it.

        If the shards have not started, and auto=sharding is in-place, then it
        is acceptable for this to return an empty mapping.

        !!! note
            "Non-sharded" bots should expect one value to be in this mapping
            under the shard ID `0`.

                >>> bot.gateway_shards[0].heartbeat_latency
                0.145612141

        Returns
        -------
        typing.Mapping[int, hikari.net.gateway.Gateway]
            The mapping of shard IDs to gateway connections for the
            corresponding shard. These shard IDs are 0-indexed.
        """

    @property
    @abc.abstractmethod
    def shard_count(self) -> int:
        """Count the number of shards in the entire distributed application.

        If the shards have not started, and auto-sharding is in-place, then it
        is acceptable for this to return `0`. When the application is running,
        this should always be a non-zero natural number that is greater than the
        maximum ID in `gateway_shards`.

        Returns
        -------
        int
            The number of shards in the entire application.
        """

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
        status: typing.Union[undefined.UndefinedType, presences.Status] = undefined.UNDEFINED,
        activity: typing.Union[undefined.UndefinedType, presences.Activity, None] = undefined.UNDEFINED,
        idle_since: typing.Union[undefined.UndefinedType, datetime.datetime, None] = undefined.UNDEFINED,
        afk: typing.Union[undefined.UndefinedType, bool] = undefined.UNDEFINED,
    ) -> None:
        """Update the presence of the user for all shards.

        This will only update arguments that you explicitly specify a value for.
        Any arguments that you do not explicitly provide some value for will
        not be changed (these values will default to be `undefined`).

        !!! warning
            This will only apply to connected shards.

        !!! note
            If you wish to update a presence for a specific shard, you can do
            this by using `gateway_shards` to find the shard you wish to
            update.

        Parameters
        ----------
        status : hikari.models.presences.Status or hikari.utilities.undefined.UndefinedType
            If defined, the new status to set.
        activity : hikari.models.presences.Activity or None or hikari.utilities.undefined.UndefinedType
            If defined, the new activity to set.
        idle_since : datetime.datetime or None or hikari.utilities.undefined.UndefinedType
            If defined, the time to show up as being idle since, or `None` if
            not applicable. If undefined, then it is not changed.
        afk : bool or hikari.utilities.undefined.UndefinedType
            If defined, `True` if the user should be marked as AFK,
            or `False` if not AFK.
        """

    @abc.abstractmethod
    def run(self) -> None:
        """Execute this component on an event loop.

        Performs the same job as `RunnableClient.start`, but provides additional
        preparation such as registering OS signal handlers for interrupts,
        and preparing the initial event loop.

        This enables the client to be run immediately without having to
        set up the `asyncio` event loop manually first.
        """
