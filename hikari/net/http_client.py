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
import types
import typing

import aiohttp.client
import aiohttp.typedefs

from hikari import errors
from hikari.net import http_settings
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
    config : hikari.net.http_settings.HTTPSettings or None
        Optional aiohttp settings for making HTTP connections.
        If `None`, defaults are used.
    debug : bool
        Defaults to `False`. If `True`, then a lot of contextual information
        regarding low-level HTTP communication will be logged to the _debug
        logger on this class.
    """

    __slots__ = (
        "logger",
        "_client_session",
        "_config",
        "_debug",
        "_tracers",
    )

    logger: logging.Logger
    """The logger to use for this object."""

    _config: http_settings.HTTPSettings
    """HTTP settings in-use."""

    _debug: bool
    """`True` if _debug mode is enabled. `False` otherwise."""

    _tracers: typing.List[tracing.BaseTracer]
    """Request _tracers.

    These can be used to intercept HTTP request events on a low level.
    """

    def __init__(
        self,
        logger: logging.Logger,
        *,
        config: typing.Optional[http_settings.HTTPSettings] = None,
        debug: bool = False,
    ) -> None:
        self.logger = logger

        if config is None:
            config = http_settings.HTTPSettings()

        self._client_session: typing.Optional[aiohttp.ClientSession] = None
        self._config = config
        self._debug = debug
        self._tracers = [(tracing.DebugTracer(self.logger) if debug else tracing.CFRayTracer(self.logger))]

    @typing.final
    async def __aenter__(self) -> HTTPClient:
        return self

    @typing.final
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

    @typing.final
    def get_client_session(self) -> aiohttp.ClientSession:
        """Acquire a client session to make requests with.

        !!! warning
            This must be invoked within a coroutine running in an event loop,
            or the behaviour will be undefined.

            Generally you should not need to use this unless you are interfacing
            with the Hikari API directly.

            This is not thread-safe.

        Returns
        -------
        aiohttp.ClientSession
            The client session to use for requests.
        """
        if self._client_session is None:
            connector = self._config.tcp_connector_factory() if self._config.tcp_connector_factory is not None else None
            self._client_session = aiohttp.ClientSession(
                connector=connector,
                trust_env=self._config.trust_env,
                version=aiohttp.HttpVersion11,
                json_serialize=json.dumps,
                trace_configs=[t.trace_config for t in self._tracers],
            )
            self.logger.debug("acquired new client session object %r", self._client_session)
        return self._client_session

    @typing.final
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

        return self.get_client_session().request(
            method=method,
            url=url,
            params=query,
            headers=headers,
            allow_redirects=self._config.allow_redirects,
            proxy=self._config.proxy_url,
            proxy_auth=self._config.proxy_auth,
            proxy_headers=self._config.proxy_headers,
            verify_ssl=self._config.verify_ssl,
            ssl_context=self._config.ssl_context,
            timeout=self._config.request_timeout,
            trace_request_ctx=trace_request_ctx,
            **kwargs,
        )

    @typing.final
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
        return await self.get_client_session().ws_connect(
            url=url,
            compress=compress,
            autoping=auto_ping,
            max_msg_size=max_msg_size,
            proxy=self._config.proxy_url,
            proxy_auth=self._config.proxy_auth,
            proxy_headers=self._config.proxy_headers,
            verify_ssl=self._config.verify_ssl,
            ssl_context=self._config.ssl_context,
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
