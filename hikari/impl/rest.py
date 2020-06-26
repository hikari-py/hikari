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
"""Implementation of a REST application.

This provides functionality for projects that only need to use the RESTful
API, such as web dashboards and other OAuth2-based scripts.
"""

from __future__ import annotations

__all__: typing.Final[typing.Sequence[str]] = ["RESTClientFactoryImpl", "RESTClientImpl"]

import concurrent.futures
import copy
import typing

import aiohttp

from hikari.api import rest as rest_api
from hikari.impl import entity_factory as entity_factory_impl
from hikari.impl import stateless_cache
from hikari.net import http_settings as http_settings_
from hikari.net import rate_limits
from hikari.net import rest as rest_component
from hikari.net import strings
from hikari.utilities import undefined

if typing.TYPE_CHECKING:
    import types

    from hikari.api import cache as cache_
    from hikari.api import entity_factory as entity_factory_


class RESTClientImpl(rest_api.IRESTClientContextManager):
    """Client for a specific set of credentials within a REST-only application.

    Parameters
    ----------
    config : hikari.utilities.undefined.UndefinedType or hikari.net.http_settings.HTTPSettings
        Optional aiohttp settings to apply to the REST components. If undefined,
        then sane defaults are used.
    debug : bool
        Defaulting to `False`, if `True`, then each payload sent and received
        in HTTP requests will be dumped to debug logs. This will provide useful
        debugging context at the cost of performance. Generally you do not
        need to enable this.
    token : hikari.utilities.undefined.UndefinedType or str
        If defined, the token to use. If not defined, no token will be injected
        into the `Authorization` header for requests.
    token_type : hikari.utilities.undefined.UndefinedType or str
        The token type to use. If undefined, a default is used instead, which
        will be `Bot`. If no `token` is provided, this is ignored.
    url : hikari.utilities.undefined.UndefinedType or str
        The API URL to hit. Generally you can leave this undefined and use the
        default.
    version : int
        The API version to use. This is interpolated into the default `url`
        to create the full URL. Currently this only supports `6` or `7`, and
        defaults to `6` (since the v7 REST API is experimental, undocumented,
        and subject to breaking change without prior notice at any time).
    """

    def __init__(
        self,
        *,
        config: http_settings_.HTTPSettings,
        debug: bool = False,
        global_ratelimit: rate_limits.ManualRateLimiter,
        token: typing.Union[undefined.UndefinedType, str] = undefined.UNDEFINED,
        token_type: typing.Union[undefined.UndefinedType, str] = undefined.UNDEFINED,
        url: typing.Union[undefined.UndefinedType, str] = undefined.UNDEFINED,
        version: int = 6,
    ) -> None:
        self._cache: cache_.ICacheComponent = stateless_cache.StatelessCacheImpl()
        self._entity_factory = entity_factory_impl.EntityFactoryComponentImpl(self)
        self._executor = None
        self._rest = rest_component.REST(
            app=self,
            config=config,
            debug=debug,
            global_ratelimit=global_ratelimit,
            token=token,
            token_type=token_type,
            rest_url=url,
            version=version,
        )

    @property
    def executor(self) -> typing.Optional[concurrent.futures.Executor]:
        return self._executor

    @property
    def rest(self) -> rest_component.REST:
        return self._rest

    @property
    def cache(self) -> cache_.ICacheComponent:
        """Return the cache component.

        !!! warn
            This will always return `NotImplemented` for REST-only applications.
        """
        return self._cache

    @property
    def entity_factory(self) -> entity_factory_.IEntityFactoryComponent:
        return self._entity_factory

    async def close(self) -> None:
        await self._rest.close()

    async def __aenter__(self) -> rest_api.IRESTClientContextManager:
        return self

    async def __aexit__(
        self,
        exc_type: typing.Optional[typing.Type[BaseException]],
        exc_val: typing.Optional[BaseException],
        exc_tb: typing.Optional[types.TracebackType],
    ) -> None:
        await self.close()


class RESTClientFactoryImpl(rest_api.IRESTClientFactory):
    """The base for a REST-only Discord application.

    This comprises of a shared TCP connector connection pool, and can have
    `hikari.api.rest.IRESTClient` instances for specific credentials acquired
    from it.

    Parameters
    ----------
    config : hikari.net.http_settings.HTTPSettings or hikari.utilities.undefined.UndefinedType
        The config to use for HTTP settings. If `undefined`, then defaults are
        used instead.
    debug : bool
        If `True`, then much more information is logged each time a request is
        made. Generally you do not need this to be on, so it will default to
        `False` instead.
    url : str or hikari.utilities.undefined.UndefinedType
        The base URL for the API. You can generally leave this as being
        `undefined` and the correct default API base URL will be generated.
    version : int
        The Discord API version to use. Can be `6` (stable, default), or `7`
        (undocumented development release).
    """

    def __init__(
        self,
        config: typing.Union[undefined.UndefinedType, http_settings_.HTTPSettings] = undefined.UNDEFINED,
        debug: bool = False,
        url: typing.Union[undefined.UndefinedType, str] = undefined.UNDEFINED,
        version: int = 6,
    ) -> None:
        config = http_settings_.HTTPSettings() if config is undefined.UNDEFINED else config

        # Copy this, since we mutate the connector attribute on it in some cases.
        self._config = copy.copy(config)
        self._debug = debug
        self._global_ratelimit = rate_limits.ManualRateLimiter()
        self._url = url
        self._version = version

        # We should use a shared connector between clients, since we want to share
        # the connection pool, so tweak the defaults a little bit to achieve this.
        # I should probably separate this option out eventually.
        if self._config.connector_owner is True or self._config.tcp_connector is None:
            self._config.connector_owner = False
            self._connector_owner = True
        else:
            self._connector_owner = False

        self._tcp_connector = (
            aiohttp.TCPConnector() if self._config.tcp_connector is None else self._config.tcp_connector
        )
        self._config.tcp_connector = self._tcp_connector

    def acquire(self, token: str, token_type: str = strings.BEARER_TOKEN) -> rest_api.IRESTClientContextManager:
        return RESTClientImpl(
            config=self._config,
            debug=self._debug,
            global_ratelimit=self._global_ratelimit,
            token=token,
            token_type=token_type,
            url=self._url,
            version=self._version,
        )

    async def close(self) -> None:
        if self._connector_owner:
            await self._tcp_connector.close()
        self._global_ratelimit.close()

    async def __aenter__(self) -> RESTClientFactoryImpl:
        return self

    async def __aexit__(
        self,
        exc_type: typing.Optional[typing.Type[BaseException]],
        exc_val: typing.Optional[BaseException],
        exc_tb: typing.Optional[types.TracebackType],
    ) -> None:
        await self.close()
