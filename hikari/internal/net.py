# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021 davfsa
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""General bits and pieces that are reused between components."""

from __future__ import annotations

__all__: typing.List[str] = ["generate_error_response", "create_client_session"]

import http
import typing

import aiohttp

from hikari import config
from hikari import errors


async def generate_error_response(response: aiohttp.ClientResponse) -> errors.HTTPError:
    """Given an erroneous HTTP response, return a corresponding exception."""
    real_url = str(response.real_url)
    raw_body = await response.read()

    # Little hack to stop mypy from complaining when using `*args`
    args: typing.List[typing.Any] = [real_url, response.headers, raw_body]
    try:
        json_body = await response.json()
        args.append(json_body.get("message", ""))
        args.append(errors.RESTErrorCode(json_body.get("code", 0)))
    except aiohttp.ContentTypeError:
        pass

    if response.status == http.HTTPStatus.BAD_REQUEST:
        return errors.BadRequestError(*args)
    if response.status == http.HTTPStatus.UNAUTHORIZED:
        return errors.UnauthorizedError(*args)
    if response.status == http.HTTPStatus.FORBIDDEN:
        return errors.ForbiddenError(*args)
    if response.status == http.HTTPStatus.NOT_FOUND:
        return errors.NotFoundError(*args)

    status = http.HTTPStatus(response.status)

    if 400 <= status < 500:
        return errors.ClientHTTPResponseError(real_url, status, response.headers, raw_body)
    elif 500 <= status < 600:
        return errors.InternalServerError(real_url, status, response.headers, raw_body)
    else:
        return errors.HTTPResponseError(real_url, status, response.headers, raw_body)


def create_tcp_connector(
    http_settings: config.HTTPSettings,
    *,
    dns_cache: typing.Union[bool, int] = True,
    limit: int = 100,
) -> aiohttp.TCPConnector:
    """Create a TCP connector and return it.

    Parameters
    ----------
    dns_cache: typing.Union[builtins.None, builtins.bool, int]
        If `builtins.True`, DNS caching is used with a default TTL of 10 seconds.
        If `builtins.False`, DNS cacheing is disabled. If an `builtins.int` is
        given, then DNS caching is enabled with an explicit TTL set. If
        `builtins.None`, the cache will be enabled and never invalitime.
    http_settings : config.HTTPSettings
        HTTP settings to use for the connector.
    limit : builtins.int
        Number of connections to allow in the pool at a maximum.

    Returns
    -------
    aiohttp.TCPConnector
        TCP connector to use.
    """
    return aiohttp.TCPConnector(
        enable_cleanup_closed=http_settings.enable_cleanup_closed,
        force_close=http_settings.force_close_transports,
        limit=limit,
        ssl_context=http_settings.ssl,
        ttl_dns_cache=dns_cache if not isinstance(dns_cache, bool) else 10,
        use_dns_cache=dns_cache is not False,
    )


def create_client_session(
    connector: aiohttp.BaseConnector,
    connector_owner: bool,
    http_settings: config.HTTPSettings,
    raise_for_status: bool,
    trust_env: bool,
    ws_response_cls: typing.Type[aiohttp.ClientWebSocketResponse] = aiohttp.ClientWebSocketResponse,
) -> aiohttp.ClientSession:
    """Generate a client session using the given settings.

    !!! warning
        You must invoke this from within a running event loop.

    !!! note
        If you pass an explicit connector, then the connection
        that is created will not own the connector. You will be
        expected to manually close it __after__ the returned
        client session is closed to prevent leaking resources.

    Parameters
    ----------
    connector : aiohttp.BaseConnector
        The connector to use.
    connector_owner : builtins.bool
        If `builtins.True`, then the client session will close the
        connector on shutdown. Otherwise, you must do it manually.
    http_settings : hikari.config.HTTPSettings
        HTTP settings to use.
    raise_for_status : builtins.bool
        `builtins.True` to default to throwing exceptions if a request
        fails, or `builtins.False` to default to not.
    trust_env : builtins.bool
        `builtins.True` to trust anything in environment variables
        and the `netrc` file, `builtins.False` to ignore it.
    ws_response_cls : typing.Type[aiohttp.ClientWebSocketResponse]
        The websocket response class to use.

        Defaults to `aiohttp.ClientWebSocketResponse`.

    Returns
    -------
    aiohttp.ClientSession
        The client session to use.
    """
    return aiohttp.ClientSession(
        connector=connector,
        connector_owner=connector_owner,
        raise_for_status=raise_for_status,
        timeout=aiohttp.ClientTimeout(
            connect=http_settings.timeouts.acquire_and_connect,
            sock_connect=http_settings.timeouts.request_socket_connect,
            sock_read=http_settings.timeouts.request_socket_read,
            total=http_settings.timeouts.total,
        ),
        trust_env=trust_env,
        version=aiohttp.HttpVersion11,
        ws_response_class=ws_response_cls,
    )
