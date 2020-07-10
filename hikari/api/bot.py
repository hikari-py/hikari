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
"""Core interfaces for types of Hikari application."""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = ["IBotApp"]

import abc
import typing

from hikari.api import voice
from hikari.api.gateway import consumer
from hikari.api.gateway import dispatcher
from hikari.api.gateway import shard

if typing.TYPE_CHECKING:
    import datetime


class IBotApp(consumer.IEventConsumerApp, dispatcher.IEventDispatcherApp, voice.IVoiceApp, abc.ABC):
    """Base for bot applications.

    Bots are components that have access to a HTTP API, an event dispatcher,
    and an event consumer.

    Additionally, bots may contain a collection of Gateway client objects. This
    is not mandatory though, as the bot may consume its events from another managed
    component that manages gateway zookeeping instead.
    """

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def uptime(self) -> datetime.timedelta:
        """Return how long the bot has been alive for.

        If the application has not been started, then this will return
        a `datetime.timedelta` of 0 seconds.

        Returns
        -------
        datetime.timedelta
            The number of seconds the application has been running.
        """

    @property
    @abc.abstractmethod
    def started_at(self) -> typing.Optional[datetime.datetime]:
        """Return the timestamp when the bot was started.

        If the application has not been started, then this will return
        `builtins.None`.

        Returns
        -------
        datetime.datetime or builtins.None
            The date/time that the application started at, or `builtins.None` if
            not yet running.
        """

    @property
    @abc.abstractmethod
    def shards(self) -> typing.Mapping[int, shard.IGatewayShard]:
        """Return a mapping of the shards managed by this process.

        This mapping will map each shard ID to the shard instance.

        If the application has not started, it is acceptable to assume that
        this will be empty.

        Returns
        -------
        typing.Mapping[builtins.int, hikari.api.gateway.shard.IGatewayShard]
            The mapping of shard ID to shard instance.
        """

    @property
    @abc.abstractmethod
    def shard_count(self) -> int:
        """Return the number of shards in the application in total.

        This does not count the active shards, but produces the total shard
        count sent when you connected. If you distribute your shards between
        multiple processes or hosts, this will represent the combined total
        shard count (minus any duplicates).

        For the instance specific shard count, return the `builtins.len` of
        `IBotApp.shards`.

        If you are using auto-sharding (i.e. not providing explicit sharding
        preferences on startup), then this will be `0` until the application
        has been started properly.

        Returns
        -------
        builtins.int
            The number of shards in the entire application.
        """

    @property
    @abc.abstractmethod
    def heartbeat_latencies(self) -> typing.Mapping[int, typing.Optional[float]]:
        """Return a mapping of shard ID to heartbeat latency.

        Any shards that are not yet started will be `builtins.None`.

        Returns
        -------
        typing.Mapping[builtins.int, builtins.float]
            Each shard ID mapped to the corresponding heartbeat latency.
        """

    @property
    @abc.abstractmethod
    def heartbeat_latency(self) -> typing.Optional[float]:
        """Return the average heartbeat latency of all started shards.

        If no shards are started, this will return `None`.

        Returns
        -------
        builtins.float or builtins.None
            The average heartbeat latency of all started shards, or `builtins.None`.
        """
