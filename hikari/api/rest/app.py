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

from hikari.api import app

if typing.TYPE_CHECKING:
    import types

    from hikari import config
    from hikari.api.rest import client


class IRESTApp(app.IApp, abc.ABC):
    """Component specialization that is used for HTTP-only applications.

    This is a specific instance of a HTTP-only client provided by pooled
    implementations of `IRESTAppFactory`. It may also be used by bots
    as a base if they require HTTP-API access.
    """

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def rest(self) -> client.IRESTClient:
        """HTTP API Client.

        Use this to make calls to Discord's HTTP API over HTTPS.

        Returns
        -------
        hikari.api.rest_client.IRESTClient
            The HTTP API client.
        """


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


class IRESTAppFactory(app.IApp, abc.ABC):
    """A client factory that emits clients.

    This enables a connection pool to be shared for stateless HTTP-only
    applications such as web dashboards, while still using the HTTP architecture
    that the bot system will use.
    """

    __slots__: typing.Sequence[str] = ()

    @abc.abstractmethod
    def acquire(self, token: str, token_type: str) -> IRESTAppContextManager:
        """Acquire a HTTP client for the given authentication details.

        Parameters
        ----------
        token : builtins.str
            The token to use.
        token_type : builtins.str
            The token type to use.

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
