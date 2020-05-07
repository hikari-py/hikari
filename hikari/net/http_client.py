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
"""Base functionality for any HTTP-based network component."""
from __future__ import annotations

import abc
import contextlib
import json
import logging
import ssl
import types
import typing

import aiohttp.typedefs

from hikari.net import tracing


class HTTPClient(abc.ABC):  # pylint:disable=too-many-instance-attributes
    """An HTTP client base for Hikari.

    The purpose of this is to provide a consistent interface for any network
    facing components that need an HTTP connection or websocket connection.

    This class takes care of initializing the underlying client session, etc.

    This class will also register interceptors for HTTP requests to produce an
    appropriate level of debugging context when needed.

    Parameters
    ----------
    allow_redirects : bool
        Whether to allow redirects or not. Defaults to `False`.
    connector : aiohttp.BaseConnector, optional
        Optional aiohttp connector info for making an HTTP connection
    debug : bool
        Defaults to `False`. If `True`, then a lot of contextual information
        regarding low-level HTTP communication will be logged to the debug
        logger on this class.
    json_deserialize : deserialization function
        A custom JSON deserializer function to use. Defaults to `json.loads`.
    json_serialize : serialization function
        A custom JSON serializer function to use. Defaults to `json.dumps`.
    proxy_headers : typing.Mapping[str, str], optional
        Optional proxy headers to pass to HTTP requests.
    proxy_auth : aiohttp.BasicAuth, optional
        Optional authorization to be used if using a proxy.
    proxy_url : str, optional
        Optional proxy URL to use for HTTP requests.
    ssl_context : ssl.SSLContext, optional
        The optional SSL context to be used.
    verify_ssl : bool
        Whether or not the client should enforce SSL signed certificate
        verification. If 1 it will ignore potentially malicious
        SSL certificates.
    timeout : float, optional
        The optional timeout for all HTTP requests.
    trust_env : bool
        If `True`, and no proxy info is given, then `HTTP_PROXY` and
        `HTTPS_PROXY` will be used from the environment variables if present.
        Any proxy credentials will be read from the user's `netrc` file
        (https://www.gnu.org/software/inetutils/manual/html_node/The-_002enetrc-file.html)
        If `False`, then this information is instead ignored.
        Defaults to `False`.
    """

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
    APPLICATION_X_WWW_FORM_URLENCODED: typing.Final[str] = "application/x-www-form-urlencoded"
    APPLICATION_OCTET_STREAM: typing.Final[str] = "application/octet-stream"

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

    tracers: typing.List[tracing.BaseTracer]
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

    def __init__(
        self,
        *,
        allow_redirects: bool = False,
        connector: typing.Optional[aiohttp.BaseConnector] = None,
        debug: bool = False,
        json_deserialize: typing.Callable[[typing.AnyStr], typing.Dict] = json.loads,
        json_serialize: typing.Callable[[typing.Dict], typing.AnyStr] = json.dumps,
        logger_name: typing.Optional[str] = None,
        proxy_auth: typing.Optional[aiohttp.BasicAuth] = None,
        proxy_headers: typing.Optional[aiohttp.typedefs.LooseHeaders] = None,
        proxy_url: typing.Optional[str] = None,
        ssl_context: typing.Optional[ssl.SSLContext] = None,
        verify_ssl: bool = True,
        timeout: typing.Optional[float] = None,
        trust_env: bool = False,
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
        self.tracers = [(tracing.DebugTracer(self.logger) if debug else tracing.CFRayTracer(self.logger))]
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
        """Acquire a client session to make requests with.

        Returns
        -------
        aiohttp.ClientSession
            The client session to use for requests.

        !!! warn
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
                trace_configs=[t.trace_config for t in self.tracers],
            )
        return self.__client_session

    async def _perform_request(
        self,
        *,
        method: str,
        url: str,
        headers: aiohttp.typedefs.LooseHeaders,
        body: typing.Union[aiohttp.FormData, dict, list, None],
        query: typing.Dict[str, str],
    ) -> aiohttp.ClientResponse:
        """Make an HTTP request and return the response.

        Parameters
        ----------
        method : str
            The verb to use.
        url : str
            The URL to hit.
        headers : typing.Dict[str, str]
            Headers to use when making the request.
        body : typing.Union[aiohttp.FormData, dict, list, None]
            The body to send. Currently this will send the content in
            a form body if you pass an instance of `aiohttp.FormData`, or
            as a JSON body if you pass a `list` or `dict`. Any other types
            will be ignored.
        query : typing.Dict[str, str]
            Mapping of query string arguments to pass in the URL.

        Returns
        -------
        aiohttp.ClientResponse
            The HTTP response.
        """
        if isinstance(body, (dict, list)):
            body = bytes(self.json_serialize(body), "utf-8")
            headers["content-type"] = self.APPLICATION_JSON

        trace_request_ctx = types.SimpleNamespace()
        trace_request_ctx.request_body = body

        return await self._acquire_client_session().request(
            method=method,
            url=url,
            params=query,
            headers=headers,
            data=body,
            allow_redirects=self.allow_redirects,
            proxy=self.proxy_url,
            proxy_auth=self.proxy_auth,
            proxy_headers=self.proxy_headers,
            verify_ssl=self.verify_ssl,
            ssl_context=self.ssl_context,
            timeout=self.timeout,
            trace_request_ctx=trace_request_ctx,
        )

    async def _create_ws(
        self, url: str, *, compress: int = 0, autoping: bool = True, max_msg_size: int = 0
    ) -> aiohttp.ClientWebSocketResponse:
        """Create a websocket.

        Parameters
        ----------
        url : str
            The URL to connect the websocket to.
        compress : int
            The compression type to use, as an int value. Use `0` to disable
            compression.
        autoping : bool
            If `True`, the client will manage automatically pinging/ponging
            in the background. If `False`, this will not occur.
        max_msg_size : int
            The maximum message size to allow to be received. If `0`, then
            no max limit is set.

        Returns
        -------
        aiohttp.ClientWebsocketResponse
            The websocket to use.
        """
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
