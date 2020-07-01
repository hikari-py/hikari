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
"""HTTP application interface."""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = ["IRESTApp", "IRESTAppFactory", "IRESTAppContextManager"]

import abc
import typing

from hikari.impl import constants

if typing.TYPE_CHECKING:
    import concurrent.futures
    import types

    from hikari import config
    from hikari.api import cache as cache_
    from hikari.api import entity_factory as entity_factory_
    from hikari.api import rest_client


class IRESTApp(abc.ABC):
    """Component specialization that is used for HTTP-only applications.

    This is a specific instance of a HTTP-only client provided by pooled
    implementations of `IRESTAppFactory`. It may also be used by bots
    as a base if they require HTTP-API access.
    """

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def rest(self) -> rest_client.IRESTClient:
        """HTTP API Client.

        Use this to make calls to Discord's HTTP API over HTTPS.

        Returns
        -------
        hikari.api.rest_client.IRESTClient
            The HTTP API client.
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


class IRESTAppContextManager(IRESTApp):
    """An IRESTApp that may behave as a context manager."""

    @abc.abstractmethod
    async def __aenter__(self) -> IRESTAppContextManager:
        ...

    @abc.abstractmethod
    async def __aexit__(
        self,
        exc_type: typing.Optional[typing.Type[BaseException]],
        exc_val: typing.Optional[BaseException],
        exc_tb: typing.Optional[types.TracebackType],
    ) -> None:
        ...


class IRESTAppFactory(abc.ABC):
    """A client factory that emits clients.

    This enables a connection pool to be shared for stateless HTTP-only
    applications such as web dashboards, while still using the HTTP architecture
    that the bot system will use.
    """

    __slots__: typing.Sequence[str] = ()

    @abc.abstractmethod
    def acquire(self, token: str, token_type: str = constants.BEARER_TOKEN) -> IRESTAppContextManager:
        """Acquire a HTTP client for the given authentication details.

        Parameters
        ----------
        token : builtins.str
            The token to use.
        token_type : builtins.str
            The token type to use. Defaults to `"Bearer"`.

        Returns
        -------
        IRESTApp
            The HTTP client to use.
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
    async def __aenter__(self) -> IRESTAppFactory:
        ...

    @abc.abstractmethod
    async def __aexit__(
        self,
        exc_type: typing.Optional[typing.Type[BaseException]],
        exc_val: typing.Optional[BaseException],
        exc_tb: typing.Optional[types.TracebackType],
    ) -> None:
        ...
