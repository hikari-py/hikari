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

from hikari.api.gateway import consumer
from hikari.api.gateway import dispatcher

if typing.TYPE_CHECKING:
    import datetime


class IBotApp(consumer.IEventConsumerApp, dispatcher.IEventDispatcherApp, abc.ABC):
    """Base for bot applications.

    Bots are components that have access to a HTTP API, an event dispatcher,
    and an event consumer.

    Additionally, bots will contain a collection of Gateway client objects.
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
