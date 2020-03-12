#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekokatt 2019-2020
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
"""
Provides a base utility class for any component needing an HTTP session that supports
proxying, SSL configuration, and a standard easy-to-use interface.
"""
__all__ = ["BaseHTTPClient"]

import abc
import asyncio
import contextlib
import json
import logging
import ssl
import typing

import aiohttp.typedefs

from hikari.internal_utilities import loggers
from hikari.net import user_agent


class BaseHTTPClient(abc.ABC):
    """
    Base utility class for any component which uses an HTTP session. Each instance represents a
    session. This class handles consuming and managing optional settings such as retries, proxies,
    and SSL customisation if desired.

    This can be used in a context manager:

    >>> class HTTPClientImpl(BaseHTTPClient):
    ...     def __init__(self, *args, **kwargs):
    ...         super().__init__(*args, **kwargs)
    ...    def request(self, *args, **kwargs):
    ...         return super()._request(*args, **kwargs)

    >>> async with HTTPClientImpl() as client:
    ...     async with client.request("GET", "https://some-websi.te") as resp:
    ...         resp.raise_for_status()
    ...         body = await resp.read()

    Warning:
        This must be initialized within a coroutine while an event loop is active
        and registered to the current thread.
    """

    DELETE = "delete"
    GET = "get"
    PATCH = "patch"
    POST = "post"
    PUT = "put"

    __slots__ = (
        "allow_redirects",
        "client_session",
        "in_count",
        "logger",
        "max_retries",
        "proxy_auth",
        "proxy_headers",
        "proxy_url",
        "ssl_context",
        "timeout",
        "user_agent",
        "verify_ssl",
    )

    #: Whether to allow following of redirects or not. Generally you do not want this.
    #: as it poses a security risk.
    #:
    #: :type: :class:`bool`
    allow_redirects: bool

    #: The underlying client session used to make low level HTTP requests.
    #:
    #: :type: :class:`aiohttp.ClientSession`
    client_session: aiohttp.ClientSession

    #: The number of requests that have been made. This acts as a unique ID for each request.
    #:
    #: :type: :class:`int`
    in_count: int

    #: The logger used to write log messages.
    #:
    #: :type: :class:`logging.Logger`
    logger: logging.Logger

    #: The asyncio event loop being used.
    #:
    #: :type: :class:`asyncio.AbstractEventLoop`
    loop: asyncio.AbstractEventLoop

    #: Proxy authorization info.
    #:
    #: :type: :class:`aiohttp.BasicAuth` or `None`
    proxy_auth: typing.Optional[aiohttp.BasicAuth]

    #: Proxy headers.
    #:
    #: :type: :class:`aiohttp.typedefs.LooseHeaders` or `None`
    proxy_headers: typing.Optional[aiohttp.typedefs.LooseHeaders]

    #: Proxy URL to use.
    #:
    #: :type: :class:`str` or `None`
    proxy_url: typing.Optional[str]

    #: SSL context to use.
    #:
    #: :type: :class:`ssl.SSLContext` or `None`
    ssl_context: typing.Optional[ssl.SSLContext]

    #: Response timeout.
    #:
    #: :type: :class:`float` or `None` if using the default for `aiohttp`.
    timeout: typing.Optional[float]

    #: The user agent being used.
    #:
    #: Warning:
    #:     Certain areas of the Discord API may enforce specific user agents
    #:     to be used for requests. You should not overwrite this generated value
    #:     unless you know what you are doing. Invalid useragents may lead to
    #:     bot account deauthorization.
    #:
    #: :type: :class:`str`
    user_agent: str

    #: Whether to verify SSL certificates or not. Generally you want this turned on
    #: to prevent the risk of fake certificates being used to perform a
    #: "man-in-the-middle" (MITM) attack on your application. However, if you are
    #: stuck behind a proxy that cannot verify the certificates correctly, or are
    #: having other SSL-related issues, you may wish to turn this off.
    #:
    #: :type: :class:`bool`
    verify_ssl: bool

    @abc.abstractmethod
    def __init__(
        self,
        *,
        allow_redirects: bool = False,
        json_serialize: typing.Callable = None,
        connector: aiohttp.BaseConnector = None,
        proxy_headers: aiohttp.typedefs.LooseHeaders = None,
        proxy_auth: aiohttp.BasicAuth = None,
        proxy_url: str = None,
        ssl_context: ssl.SSLContext = None,
        verify_ssl: bool = True,
        timeout: float = None,
    ) -> None:
        """
        Args:
            allow_redirects:
                defaults to False for security reasons. If you find you are receiving multiple redirection responses
                causing requests to fail, it is probably worth enabling this.
            connector:
                the :class:`aiohttp.BaseConnector` to use for the client session, or `None` if you wish to use the
                default instead.
            json_serialize:
                a callable that consumes a Python object and returns a JSON-encoded string.
                This defaults to :func:`json.dumps`.
            proxy_auth:
                optional proxy authentication to use.
            proxy_headers:
                optional proxy headers to pass.
            proxy_url:
                optional proxy URL to use.
            ssl_context:
                optional SSL context to use.
            verify_ssl:
                defaulting to True, setting this to false will disable SSL verification.
            timeout:
                optional timeout to apply to individual HTTP requests.
        """

        #: Whether to allow redirects or not.
        #:
        #: :type: :class:`bool`
        self.allow_redirects = allow_redirects

        #: The HTTP client session to use.
        #:
        #: :type: :class:`aiohttp.ClientSession`
        self.client_session = aiohttp.ClientSession(
            connector=connector, version=aiohttp.HttpVersion11, json_serialize=json_serialize or json.dumps,
        )

        #: The logger to use for this object.
        #:
        #: :type: :class:`logging.Logger`

        self.logger = loggers.get_named_logger(self)
        #: User agent to use.
        #:
        #: :type: :class:`str`
        self.user_agent = user_agent.user_agent()

        #: If `true`, this will enforce SSL signed certificate verification, otherwise it will
        #: ignore potentially malicious SSL certificates.
        #:
        #: :type: :class:`bool`
        self.verify_ssl = verify_ssl

        #: Optional proxy URL to use for HTTP requests.
        #:
        #: :type: :class:`str`
        self.proxy_url = proxy_url

        #: Optional authorization to use if using a proxy.
        #:
        #: :type: :class:`aiohttp.BasicAuth`
        self.proxy_auth = proxy_auth

        #: Optional proxy headers to pass.
        #:
        #: :type: :class:`aiohttp.typedefs.LooseHeaders`
        self.proxy_headers = proxy_headers

        #: Optional SSL context to use.
        #:
        #: :type: :class:`ssl.SSLContext`
        self.ssl_context: ssl.SSLContext = ssl_context

        #: Optional timeout for HTTP requests.
        #:
        #: :type: :class:`float`
        self.timeout = timeout

        #: How many responses have been received.
        #:
        #: :type: :class:`int`
        self.in_count = 0

    def _request(self, method, uri, **kwargs):
        """
        Calls :meth:`aiohttp.ClientSession.request` and returns the context manager result.

        Args:
            method:
                The HTTP method to use.
            uri:
                The URI to send to.
            **kwargs:
                Any other parameters to pass to the `request` method when invoking it.
        """
        return self.client_session.request(
            method,
            uri,
            allow_redirects=self.allow_redirects,
            proxy=self.proxy_url,
            proxy_auth=self.proxy_auth,
            proxy_headers=self.proxy_headers,
            verify_ssl=self.verify_ssl,
            ssl_context=self.ssl_context,
            timeout=self.timeout,
            **kwargs,
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        self.logger.debug("Closing HTTPClient")
        with contextlib.suppress(Exception):
            await self.client_session.close()
