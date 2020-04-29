#!/usr/bin/env python3
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
from __future__ import annotations

import abc
import contextlib
import json
import logging
import ssl
import types
import typing

import aiohttp.typedefs

from hikari.internal import more_typing
from hikari.net import tracing


class _AIOHTTPRequestContext(typing.Protocol):
    """A dummy AIOHTTP request context manager object protocol.

    This is provided for internal documentation purposes only, and does not
    implement any form of actual functionality.
    """

    def __aenter__(self) -> aiohttp.ClientResponse:
        ...

    def __await__(self) -> typing.Generator[typing.Any, None, aiohttp.ClientResponse]:
        ...


class HTTPClient(abc.ABC):
    __slots__ = (
        "__client_session",
        "allow_redirects",
        "connector",
        "debug",
        "logger",
        "json_deserialize",
        "json_serialize",
        "proxy_auth",
        "proxy_headers",
        "proxy_url",
        "ssl_context",
        "timeout",
        "tracers",
        "trust_env",
        "verify_ssl",
    )

    GET: typing.Final[str] = "get"
    POST: typing.Final[str] = "post"
    PATCH: typing.Final[str] = "patch"
    PUT: typing.Final[str] = "put"
    HEAD: typing.Final[str] = "head"
    DELETE: typing.Final[str] = "delete"
    OPTIONS: typing.Final[str] = "options"
    APPLICATION_JSON: typing.Final[str] = "application/json"

    allow_redirects: bool
    """`True` if HTTP redirects are enabled, or `False` otherwise."""

    connector: typing.Optional[aiohttp.BaseConnector]
    """The base connector for the `aiohttp.ClientSession`, if provided."""

    debug: bool
    """`True` if debug mode is enabled. `False` otherwise."""

    logger: logging.Logger
    """The logger to use for this object."""

    json_deserialize: typing.Callable[[typing.AnyStr], typing.Any]
    """The JSON deserialization function.

    This consumes a JSON string and produces some object.
    """

    json_serialize: typing.Callable[[typing.Any], typing.AnyStr]
    """The JSON deserialization function.

    This consumes an object and produces some JSON string.
    """

    proxy_auth: typing.Optional[aiohttp.BasicAuth]
    """Proxy authorization to use."""

    proxy_headers: typing.Optional[typing.Mapping[str, str]]
    """A set of headers to provide to a proxy server."""

    proxy_url: typing.Optional[str]
    """An optional proxy URL to send requests to."""

    ssl_context: typing.Optional[ssl.SSLContext]
    """The custom SSL context to use."""

    timeout: typing.Optional[float]
    """The HTTP request timeout to abort requests after."""

    tracers: typing.List[aiohttp.TraceConfig]
    """Request tracers.

    These can be used to intercept HTTP request events on a low level.
    """

    trust_env: bool
    """Whether to take notice of proxy environment variables.

    If `True`, and no proxy info is given, then `HTTP_PROXY` and
    `HTTPS_PROXY` will be used from the environment variables if present.
    Any proxy credentials will be read from the user's `netrc` file
    (https://www.gnu.org/software/inetutils/manual/html_node/The-_002enetrc-file.html)
    If `False`, then this information is instead ignored.
    """

    verify_ssl: bool
    """Whether SSL certificates should be verified for each request.

    When this is `True` then an exception will be raised whenever invalid SSL
    certificates are received. When this is `False` unrecognised certificates
    that may be illegitimate are accepted and ignored.
    """

    def __init__(  # pylint: disable=too-many-locals
        self,
        *,
        allow_redirects: bool,
        connector: typing.Optional[aiohttp.BaseConnector],
        debug: bool,
        json_deserialize: typing.Callable[[typing.AnyStr], typing.Dict],
        json_serialize: typing.Callable[[typing.Dict], typing.AnyStr],
        logger_name: typing.Optional[str] = None,
        proxy_auth: typing.Optional[aiohttp.BasicAuth],
        proxy_headers: typing.Optional[aiohttp.typedefs.LooseHeaders],
        proxy_url: typing.Optional[str],
        ssl_context: typing.Optional[ssl.SSLContext],
        verify_ssl: bool,
        timeout: typing.Optional[float],
        trust_env: bool,
    ) -> None:
        self.logger = logging.getLogger(
            f"{type(self).__module__}.{type(self).__qualname__}" if logger_name is None else logger_name
        )

        self.__client_session = None
        self.allow_redirects = allow_redirects
        self.connector = connector
        self.debug = debug
        self.json_serialize = json_serialize
        self.json_deserialize = json_deserialize
        self.proxy_auth = proxy_auth
        self.proxy_headers = proxy_headers
        self.proxy_url = proxy_url
        self.ssl_context: ssl.SSLContext = ssl_context
        self.timeout = timeout
        self.trust_env = trust_env
        self.tracers = [(tracing.DebugTracer(self.logger) if debug else tracing.CFRayTracer(self.logger)).trace_config]
        self.verify_ssl = verify_ssl

    async def __aenter__(self) -> HTTPClient:
        return self

    async def __aexit__(
        self, exc_type: typing.Type[BaseException], exc_val: BaseException, exc_tb: types.TracebackType
    ) -> None:
        await self.close()

    async def close(self) -> None:
        """Close the client safely."""
        with contextlib.suppress(Exception):
            await self.__client_session.close()
            self.__client_session = None
            self.logger.debug("closed %s", type(self).__qualname__)

    def _acquire_client_session(self) -> aiohttp.ClientSession:
        """The `aiohttp.ClientSession` to use for requests.

        !!! warn:
            This must only be accessed within an asyncio event loop, otherwise
            there is a risk that the session will not have the correct event
            loop; hence why this is private.
        """
        if self.__client_session is None:
            self.__client_session = aiohttp.ClientSession(
                connector=self.connector,
                trust_env=self.trust_env,
                version=aiohttp.HttpVersion11,
                json_serialize=self.json_serialize or json.dumps,
                trace_configs=self.tracers,
            )
        return self.__client_session

    async def _perform_request(self, method, url, *, headers, body, query) -> aiohttp.ClientResponse:
        trace_request_ctx = types.SimpleNamespace()
        trace_request_ctx.request_body = body

        return await self._acquire_client_session().request(
            method=method,
            url=url,
            headers=headers,
            allow_redirects=self.allow_redirects,
            proxy=self.proxy_url,
            proxy_auth=self.proxy_auth,
            proxy_headers=self.proxy_headers,
            verify_ssl=self.verify_ssl,
            ssl_context=self.ssl_context,
            timeout=self.timeout,
            params=query,
            trace_request_ctx=trace_request_ctx,
            data=body if isinstance(body, aiohttp.FormData) else None,
            json=body if isinstance(body, (dict, list)) else None,
        )

    async def _create_ws(self, url, compress, autoping, max_msg_size) -> aiohttp.ClientWebSocketResponse:
        self.logger.debug("creating underlying websocket object from HTTP session")
        return await self._acquire_client_session().ws_connect(
            url=url,
            compress=compress,
            autoping=autoping,
            max_msg_size=max_msg_size,
            proxy=self.proxy_url,
            proxy_auth=self.proxy_auth,
            proxy_headers=self.proxy_headers,
            verify_ssl=self.verify_ssl,
            ssl_context=self.ssl_context,
        )
