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
"""Core app interface for application implementations."""
from __future__ import annotations

__all__: typing.Final[typing.List[str]] = ["IApp"]

import abc
import typing

if typing.TYPE_CHECKING:
    import concurrent.futures

    from hikari import config
    from hikari.api import cache as cache_
    from hikari.api import entity_factory as entity_factory_


class IApp(abc.ABC):
    """The core interface for a Hikari application."""

    __slots__ = ()

    @property
    @abc.abstractmethod
    def cache(self) -> cache_.ICacheComponent:
        """Entity cache.

        Returns
        -------
        hikari.api.cache.ICacheComponent
            The cache implementation used in this application.
        """

    @property
    @abc.abstractmethod
    def entity_factory(self) -> entity_factory_.IEntityFactoryComponent:
        """Entity creator and updater facility.

        Returns
        -------
        hikari.api.entity_factory.IEntityFactoryComponent
            The factory object used to produce and update Python entities.
        """

    @property
    @abc.abstractmethod
    def executor(self) -> typing.Optional[concurrent.futures.Executor]:
        """Thread-pool to utilise for file IO within the library, if set.

        Returns
        -------
        concurrent.futures.Executor or builtins.None
            The custom thread-pool being used for blocking IO. If the
            default event loop thread-pool is being used, then this will
            return `builtins.None` instead.
        """

    @property
    @abc.abstractmethod
    def http_settings(self) -> config.HTTPSettings:
        """HTTP-specific settings."""

    @property
    @abc.abstractmethod
    def proxy_settings(self) -> config.ProxySettings:
        """Proxy-specific settings."""

    @abc.abstractmethod
    async def close(self) -> None:
        """Safely shut down all resources."""
