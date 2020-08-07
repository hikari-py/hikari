# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Core interfaces for types of Hikari application."""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = ["IBotApp"]

import abc
import typing

from hikari.api import event_consumer
from hikari.api import event_dispatcher
from hikari.api import shard
from hikari.api import voice

if typing.TYPE_CHECKING:
    import datetime

    from hikari.api import guild_chunker as guild_chunker_
    from hikari.models import intents as intents_
    from hikari.models import users


class IBotApp(event_consumer.IEventConsumerApp, event_dispatcher.IEventDispatcherApp, voice.IVoiceApp, abc.ABC):
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
    def guild_chunker(self) -> guild_chunker_.IGuildChunkerComponent:
        """Guild chunker.

        Returns
        -------
        hikari.api.guild_chunker.IGuildChunkerComponent
            The guild chunker implementation used in this application.
        """

    @property
    @abc.abstractmethod
    def heartbeat_latencies(self) -> typing.Mapping[int, typing.Optional[datetime.timedelta]]:
        """Return a mapping of shard ID to heartbeat latency.

        Any shards that are not yet started will be `builtins.None`.

        Returns
        -------
        typing.Mapping[builtins.int, datetime.timedelta]
            Each shard ID mapped to the corresponding heartbeat latency.
        """

    @property
    @abc.abstractmethod
    def heartbeat_latency(self) -> typing.Optional[datetime.timedelta]:
        """Return the average heartbeat latency of all started shards.

        If no shards are started, this will return `None`.

        Returns
        -------
        datetime.timedelta or builtins.None
            The average heartbeat latency of all started shards, or
            `builtins.None`.
        """

    @property
    @abc.abstractmethod
    def intents(self) -> typing.Optional[intents_.Intent]:
        """Return the intents registered for the application.

        If no intents are in use, `builtins.None` is returned instead.

        Returns
        -------
        hikari.models.intents.Intent or builtins.None
            The intents registered on this application.
        """

    @property
    @abc.abstractmethod
    def me(self) -> typing.Optional[users.OwnUser]:
        """Return the bot user, if known.

        This should be available as soon as the bot has fired the
        `hikari.events.lifetime_events.StartingEvent`.

        Until then, this may or may not be `builtins.None`.

        Returns
        -------
        hikari.models.users.OwnUser or builtins.None
            The bot user, if known, otherwise `builtins.None`.
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
    def uptime(self) -> datetime.timedelta:
        """Return how long the bot has been alive for.

        If the application has not been started, then this will return
        a `datetime.timedelta` of 0 seconds.

        Returns
        -------
        datetime.timedelta
            The number of seconds the application has been running.
        """
