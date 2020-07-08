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
"""Implementation of a HTTP application.

This provides functionality for projects that only need to use the RESTful
API, such as web dashboards and other OAuth2-based scripts.
"""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = ["RESTAppFactoryImpl", "RESTAppImpl"]

import typing

import aiohttp

from hikari import config
from hikari.api.rest import app
from hikari.api.rest import client
from hikari.impl import entity_factory as entity_factory_impl
from hikari.impl import rate_limits
from hikari.impl.cache import stateless
from hikari.impl.rest import client as rest_client_impl
from hikari.utilities import constants

if typing.TYPE_CHECKING:
    import concurrent.futures
    import types

    from hikari.api import cache as cache_
    from hikari.api import entity_factory as entity_factory_


class RESTAppImpl(app.IRESTAppContextManager):
    """Client for a specific set of credentials within a HTTP-only application.

    Parameters
    ----------
    debug : builtins.bool
        Defaulting to `builtins.False`, if `builtins.True`, then each payload
        sent and received in HTTP requests will be dumped to debug logs. This
        will provide useful debugging context at the cost of performance.
        Generally you do not need to enable this.
    connector : aiohttp.BaseConnector
        The AIOHTTP connector to use. This must be closed by the caller, and
        will not be terminated when this class closes (since you will generally
        expect this to be a connection pool).
    global_ratelimit : hikari.impl.rate_limits.ManualRateLimiter
        The global ratelimiter.
    http_settings : hikari.config.HTTPSettings
        HTTP-related settings.
    proxy_settings : hikari.config.ProxySettings
        Proxy-related settings.
    token : builtins.str or builtins.None
        If defined, the token to use. If not defined, no token will be injected
        into the `Authorization` header for requests.
    token_type : builtins.str or builtins.None
        The token type to use. If undefined, a default is used instead, which
        will be `Bot`. If no `token` is provided, this is ignored.
    url : builtins.str or builtins.None
        The API URL to hit. Generally you can leave this undefined and use the
        default.
    version : builtins.int
        The API version to use. This is interpolated into the default `url`
        to create the full URL. Currently this only supports `6` or `7`.
    """

    def __init__(
        self,
        *,
        debug: bool = False,
        connector: aiohttp.BaseConnector,
        global_ratelimit: rate_limits.ManualRateLimiter,
        http_settings: config.HTTPSettings,
        proxy_settings: config.ProxySettings,
        token: typing.Optional[str],
        token_type: typing.Optional[str],
        url: typing.Optional[str],
        version: int,
    ) -> None:
        self._cache: cache_.ICacheComponent = stateless.StatelessCacheImpl()
        self._entity_factory = entity_factory_impl.EntityFactoryComponentImpl(self)
        self._executor = None
        self._http_settings = http_settings
        self._proxy_settings = proxy_settings

        self._rest = rest_client_impl.RESTClientImpl(
            app=self,
            connector=connector,
            connector_owner=False,
            debug=debug,
            http_settings=http_settings,
            global_ratelimit=global_ratelimit,
            proxy_settings=proxy_settings,
            token=token,
            token_type=token_type,
            rest_url=url,
            version=version,
        )

    @property
    def cache(self) -> cache_.ICacheComponent:
        """Return the cache component.

        !!! warn
            This will always return `builtins.NotImplemented` for HTTP-only applications.
        """
        return self._cache

    @property
    def executor(self) -> typing.Optional[concurrent.futures.Executor]:
        return self._executor

    @property
    def entity_factory(self) -> entity_factory_.IEntityFactoryComponent:
        return self._entity_factory

    @property
    def http_settings(self) -> config.HTTPSettings:
        return self._http_settings

    @property
    def proxy_settings(self) -> config.ProxySettings:
        return self._proxy_settings

    @property
    def rest(self) -> client.IRESTClient:
        return self._rest

    async def close(self) -> None:
        await self._rest.close()

    async def __aenter__(self) -> app.IRESTAppContextManager:
        return self

    async def __aexit__(
        self,
        exc_type: typing.Optional[typing.Type[BaseException]],
        exc_val: typing.Optional[BaseException],
        exc_tb: typing.Optional[types.TracebackType],
    ) -> None:
        await self.close()


class RESTAppFactoryImpl(app.IRESTAppFactory):
    """The base for a HTTP-only Discord application.

    This comprises of a shared TCP connector connection pool, and can have
    `hikari.api.rest.IRESTApp` instances for specific credentials acquired
    from it.

    Parameters
    ----------
    debug : builtins.bool
        If `builtins.True`, then much more information is logged each time a
        request is made. Generally you do not need this to be on, so it will
        default to `builtins.False` instead.
    url : str or hikari.utilities.undefined.UndefinedType
        The base URL for the API. You can generally leave this as being
        `undefined` and the correct default API base URL will be generated.
    version : builtins.int
        The Discord API version to use. Can be `6` (stable, default), or `7`
        (undocumented development release).
    """

    def __init__(
        self,
        *,
        connector: typing.Optional[aiohttp.BaseConnector] = None,
        connector_owner: bool = True,
        debug: bool = False,
        http_settings: typing.Optional[config.HTTPSettings] = None,
        proxy_settings: typing.Optional[config.ProxySettings] = None,
        url: typing.Optional[str] = None,
        version: int = 6,
    ) -> None:
        self._connector = aiohttp.TCPConnector() if connector is None else connector
        self._connector_owner = connector_owner
        self._debug = debug
        self._global_ratelimit = rate_limits.ManualRateLimiter()
        self._http_settings = config.HTTPSettings() if http_settings is None else http_settings
        self._proxy_settings = config.ProxySettings() if proxy_settings is None else proxy_settings
        self._url = url
        self._version = version

    @property
    def http_settings(self) -> config.HTTPSettings:
        return self._http_settings

    @property
    def proxy_settings(self) -> config.ProxySettings:
        return self._proxy_settings

    def acquire(self, token: str, token_type: str = constants.BEARER_TOKEN) -> app.IRESTAppContextManager:
        return RESTAppImpl(
            connector=self._connector,
            debug=self._debug,
            http_settings=self._http_settings,
            global_ratelimit=self._global_ratelimit,
            proxy_settings=self._proxy_settings,
            token=token,
            token_type=token_type,
            url=self._url,
            version=self._version,
        )

    async def close(self) -> None:
        if self._connector_owner:
            await self._connector.close()
        self._global_ratelimit.close()

    async def __aenter__(self) -> RESTAppFactoryImpl:
        return self

    async def __aexit__(
        self,
        exc_type: typing.Optional[typing.Type[BaseException]],
        exc_val: typing.Optional[BaseException],
        exc_tb: typing.Optional[types.TracebackType],
    ) -> None:
        await self.close()
