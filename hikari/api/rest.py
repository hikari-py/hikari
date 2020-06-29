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
"""REST application interface."""

from __future__ import annotations

__all__: typing.Final[typing.Sequence[str]] = ["IRESTClient", "IRESTClientFactory", "IRESTClientContextManager"]

import abc
import typing

from hikari.net import strings

if typing.TYPE_CHECKING:
    import concurrent.futures
    import types

    from hikari.api import cache as cache_
    from hikari.api import entity_factory as entity_factory_
    from hikari.net import config
    from hikari.net import rest as rest_


class IRESTClient(abc.ABC):
    """Component specialization that is used for REST-only applications.

    This is a specific instance of a REST-only client provided by pooled
    implementations of `IRESTClientFactory`. It may also be used by bots
    as a base if they require REST-API access.
    """

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def rest(self) -> rest_.REST:
        """REST API Client.

        Use this to make calls to Discord's REST API over HTTPS.

        Returns
        -------
        hikari.net.rest.REST
            The REST API client.
        """

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
        concurrent.futures.Executor or None
            The custom thread-pool being used for blocking IO. If the
            default event loop thread-pool is being used, then this will
            return `None` instead.
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


class IRESTClientContextManager(IRESTClient):
    """An IRESTClient that may behave as a context manager."""

    @abc.abstractmethod
    async def __aenter__(self) -> IRESTClientContextManager:
        ...

    @abc.abstractmethod
    async def __aexit__(
        self,
        exc_type: typing.Optional[typing.Type[BaseException]],
        exc_val: typing.Optional[BaseException],
        exc_tb: typing.Optional[types.TracebackType],
    ) -> None:
        ...


class IRESTClientFactory(abc.ABC):
    """A client factory that emits clients.

    This enables a connection pool to be shared for stateless REST-only
    applications such as web dashboards, while still using the HTTP architecture
    that the bot system will use.
    """

    __slots__: typing.Sequence[str] = ()

    @abc.abstractmethod
    def acquire(self, token: str, token_type: str = strings.BEARER_TOKEN) -> IRESTClientContextManager:
        """Acquire a REST client for the given authentication details.

        Parameters
        ----------
        token : str
            The token to use.
        token_type : str
            The token type to use. Defaults to `"Bearer"`.

        Returns
        -------
        IRESTClient
            The REST client to use.
        """

    @abc.abstractmethod
    async def close(self) -> None:
        """Safely shut down all resources."""

    @property
    @abc.abstractmethod
    def http_settings(self) -> config.HTTPSettings:
        """HTTP-specific settings."""

    @property
    @abc.abstractmethod
    def proxy_settings(self) -> config.ProxySettings:
        """Proxy-specific settings."""

    @abc.abstractmethod
    async def __aenter__(self) -> IRESTClientFactory:
        ...

    @abc.abstractmethod
    async def __aexit__(
        self,
        exc_type: typing.Optional[typing.Type[BaseException]],
        exc_val: typing.Optional[BaseException],
        exc_tb: typing.Optional[types.TracebackType],
    ) -> None:
        ...
