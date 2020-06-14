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

from hikari.api import event_consumer
from hikari.api import event_dispatcher

if typing.TYPE_CHECKING:
    from hikari.net import http_settings as http_settings_


class IBotApp(event_consumer.IEventConsumerApp, event_dispatcher.IEventDispatcherApp, abc.ABC):
    """Base for bot applications.

    Bots are components that have access to a REST API, an event dispatcher,
    and an event consumer.

    Additionally, bots will contain a collection of Gateway client objects.
    """

    __slots__ = ()

    @property
    @abc.abstractmethod
    def http_settings(self) -> http_settings_.HTTPSettings:
        """HTTP settings to use for the shards when they get created.

        !!! info
            This is stored only for bots, since shards are generated lazily on
            start-up once sharding information has been retrieved from the REST
            API on startup.

        Returns
        -------
        hikari.net.http_settings.HTTPSettings
            The HTTP settings to use.
        """
