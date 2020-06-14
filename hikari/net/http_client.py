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

__all__: typing.Final[typing.List[str]] = ["HTTPClient"]

import abc
import http
import json
import logging
import ssl
import types
import typing

import aiohttp.client
import aiohttp.typedefs

from hikari import errors
from hikari.net import tracing
from hikari.utilities import data_binding

try:
    # noinspection PyProtectedMember
    RequestContextManager = aiohttp.client._RequestContextManager
    """Type hint for an AIOHTTP session context manager.

    This is stored as aiohttp does not expose the type-hint directly, despite
    exposing the rest of the API it is part of.
    """
except NameError:
    RequestContextManager = typing.Any  # type: ignore


class HTTPClient(abc.ABC):  # pylint:disable=too-many-instance-attributes
    """An HTTP client base for Hikari.

    The purpose of this is to provide a consistent interface for any network
    facing application that need an HTTP connection or websocket connection.

    This class takes care of initializing the underlying client session, etc.

    This class will also register interceptors for HTTP requests to produce an
    appropriate level of debugging context when needed.

    Parameters
    ----------
    allow_redirects : bool
        Whether to allow redirects or not. Defaults to `False`.
    connector : aiohttp.BaseConnector or None
        Optional aiohttp _connector info for making an HTTP connection
    debug : bool
        Defaults to `False`. If `True`, then a lot of contextual information
        regarding low-level HTTP communication will be logged to the _debug
        logger on this class.
    proxy_auth : aiohttp.BasicAuth or None
        Optional authorization to be used if using a proxy.
    proxy_url : str or None
        Optional proxy URL to use for HTTP requests.
    ssl_context : ssl.SSLContext or None
        The optional SSL context to be used.
    verify_ssl : bool
        Whether or not the client should enforce SSL signed certificate
        verification. If 1 it will ignore potentially malicious
        SSL certificates.
    timeout : float or None
        The optional _request_timeout for all HTTP requests.
    trust_env : bool
        If `True`, and no proxy info is given, then `HTTP_PROXY` and
        `HTTPS_PROXY` will be used from the environment variables if present.
        Any proxy credentials will be read from the user's `netrc` file
        (https://www.gnu.org/software/inetutils/manual/html_node/The-_002enetrc-file.html)
        If `False`, then this information is instead ignored.
        Defaults to `False`.
    """

    __slots__ = (
        "logger",
        "_client_session",
        "_allow_redirects",
        "_connector",
        "_debug",
        "_json_deserialize",
        "_json_serialize",
        "_proxy_auth",
        "_proxy_headers",
        "_proxy_url",
        "_ssl_context",
        "_request_timeout",
        "_tracers",
        "_trust_env",
        "_verify_ssl",
    )

    _APPLICATION_JSON: typing.Final[str] = "application/json"
    _APPLICATION_X_WWW_FORM_URLENCODED: typing.Final[str] = "application/x-www-form-urlencoded"
    _APPLICATION_OCTET_STREAM: typing.Final[str] = "application/octet-stream"
    _MULTIPART_FORM_DATA: typing.Final[str] = "multipart/form-data"

    logger: logging.Logger
    """The logger to use for this object."""

    _allow_redirects: bool
    """`True` if HTTP redirects are enabled, or `False` otherwise."""

    _connector: typing.Optional[aiohttp.BaseConnector]
    """The base _connector for the `aiohttp.ClientSession`, if provided."""

    _debug: bool
    """`True` if _debug mode is enabled. `False` otherwise."""

    _proxy_auth: typing.Optional[aiohttp.BasicAuth]
    """Proxy authorization to use."""

    _proxy_headers: typing.Optional[typing.Mapping[str, str]]
    """A set of headers to provide to a proxy server."""

    _proxy_url: typing.Optional[str]
    """An optional proxy URL to send requests to."""

    _ssl_context: typing.Optional[ssl.SSLContext]
    """The custom SSL context to use."""

    _request_timeout: typing.Optional[float]
    """The HTTP request _request_timeout to abort requests after."""

    _tracers: typing.List[tracing.BaseTracer]
    """Request _tracers.

    These can be used to intercept HTTP request events on a low level.
    """

    _trust_env: bool
    """Whether to take notice of proxy environment variables.

    If `True`, and no proxy info is given, then `HTTP_PROXY` and
    `HTTPS_PROXY` will be used from the environment variables if present.
    Any proxy credentials will be read from the user's `netrc` file
    (https://www.gnu.org/software/inetutils/manual/html_node/The-_002enetrc-file.html)
    If `False`, then this information is instead ignored.
    """

    _verify_ssl: bool
    """Whether SSL certificates should be verified for each request.

    When this is `True` then an exception will be raised whenever invalid SSL
    certificates are received. When this is `False` unrecognised certificates
    that may be illegitimate are accepted and ignored.
    """

    def __init__(
        self,
        logger: logging.Logger,
        *,
        allow_redirects: bool = False,
        connector: typing.Optional[aiohttp.BaseConnector] = None,
        debug: bool = False,
        proxy_auth: typing.Optional[aiohttp.BasicAuth] = None,
        proxy_headers: typing.Optional[aiohttp.typedefs.LooseHeaders] = None,
        proxy_url: typing.Optional[str] = None,
        ssl_context: typing.Optional[ssl.SSLContext] = None,
        verify_ssl: bool = True,
        timeout: typing.Optional[float] = None,
        trust_env: bool = False,
    ) -> None:
        self.logger = logger

        self._client_session: typing.Optional[aiohttp.ClientSession] = None
        self._allow_redirects = allow_redirects
        self._connector = connector
        self._debug = debug
        self._proxy_auth = proxy_auth
        self._proxy_headers = proxy_headers
        self._proxy_url = proxy_url
        self._ssl_context = ssl_context
        self._request_timeout = timeout
        self._trust_env = trust_env
        self._tracers = [(tracing.DebugTracer(self.logger) if debug else tracing.CFRayTracer(self.logger))]
        self._verify_ssl = verify_ssl

    async def __aenter__(self) -> HTTPClient:
        return self

    async def __aexit__(
        self, exc_type: typing.Type[BaseException], exc_val: BaseException, exc_tb: types.TracebackType
    ) -> None:
        await self.close()

    async def close(self) -> None:
        """Close the client safely."""
        if self._client_session is not None:
            await self._client_session.close()
            self.logger.debug("closed client session object %r", self._client_session)
            self._client_session = None

    def client_session(self) -> aiohttp.ClientSession:
        """Acquire a client session to make requests with.

        !!! warning
            This must be invoked within a coroutine running in an event loop,
            or the behaviour will be undefined.

            Generally you should not need to use this unless you are interfacing
            with the Hikari API directly.

        Returns
        -------
        aiohttp.ClientSession
            The client session to use for requests.
        """
        if self._client_session is None:
            self._client_session = aiohttp.ClientSession(
                connector=self._connector,
                trust_env=self._trust_env,
                version=aiohttp.HttpVersion11,
                json_serialize=json.dumps,
                trace_configs=[t.trace_config for t in self._tracers],
            )
            self.logger.debug("acquired new client session object %r", self._client_session)
        return self._client_session

    def _perform_request(
        self,
        *,
        method: str,
        url: str,
        headers: data_binding.Headers = typing.cast(data_binding.Headers, types.MappingProxyType({})),
        body: typing.Union[
            data_binding.JSONObjectBuilder, aiohttp.FormData, data_binding.JSONObject, data_binding.JSONArray, None
        ] = None,
        query: typing.Union[data_binding.Query, data_binding.StringMapBuilder, None] = None,
    ) -> RequestContextManager:
        """Make an HTTP request and return the response.

        Parameters
        ----------
        method : str
            The verb to use.
        url : str
            The URL to hit.
        headers : typing.Dict[str, str]
            Headers to use when making the request.
        body : aiohttp.FormData or dict or list or None
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
        kwargs: typing.Dict[str, typing.Any] = {}

        if isinstance(body, (dict, list)):
            kwargs["json"] = body

        elif isinstance(body, aiohttp.FormData):
            kwargs["data"] = body

        trace_request_ctx = types.SimpleNamespace()
        trace_request_ctx.request_body = body

        return self.client_session().request(
            method=method,
            url=url,
            params=query,
            headers=headers,
            allow_redirects=self._allow_redirects,
            proxy=self._proxy_url,
            proxy_auth=self._proxy_auth,
            proxy_headers=self._proxy_headers,
            verify_ssl=self._verify_ssl,
            ssl_context=self._ssl_context,
            timeout=self._request_timeout,
            trace_request_ctx=trace_request_ctx,
            **kwargs,
        )

    async def _create_ws(
        self, url: str, *, compress: int = 0, auto_ping: bool = True, max_msg_size: int = 0
    ) -> aiohttp.ClientWebSocketResponse:
        """Create a websocket.

        Parameters
        ----------
        url : str
            The URL to connect the websocket to.
        compress : int
            The compression type to use, as an int value. Use `0` to disable
            compression.
        auto_ping : bool
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
        return await self.client_session().ws_connect(
            url=url,
            compress=compress,
            autoping=auto_ping,
            max_msg_size=max_msg_size,
            proxy=self._proxy_url,
            proxy_auth=self._proxy_auth,
            proxy_headers=self._proxy_headers,
            verify_ssl=self._verify_ssl,
            ssl_context=self._ssl_context,
        )


async def generate_error_response(response: aiohttp.ClientResponse) -> errors.HTTPError:
    """Given an erroneous HTTP response, return a corresponding exception."""
    real_url = str(response.real_url)
    raw_body = await response.read()

    if response.status == http.HTTPStatus.BAD_REQUEST:
        return errors.BadRequest(real_url, response.headers, raw_body)
    if response.status == http.HTTPStatus.UNAUTHORIZED:
        return errors.Unauthorized(real_url, response.headers, raw_body)
    if response.status == http.HTTPStatus.FORBIDDEN:
        return errors.Forbidden(real_url, response.headers, raw_body)
    if response.status == http.HTTPStatus.NOT_FOUND:
        return errors.NotFound(real_url, response.headers, raw_body)

    # noinspection PyArgumentList
    status = http.HTTPStatus(response.status)

    cls: typing.Type[errors.HikariError]
    if 400 <= status < 500:
        cls = errors.ClientHTTPErrorResponse
    elif 500 <= status < 600:
        cls = errors.ServerHTTPErrorResponse
    else:
        cls = errors.HTTPErrorResponse

    return cls(real_url, status, response.headers, raw_body)
