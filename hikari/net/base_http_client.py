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
"""Provides a base utility class for any component needing an HTTP session 
that supports proxying, SSL configuration, and a standard easy-to-use interface."""
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
    """Base utility class for any component which uses an HTTP session.
    
    Each instance represents a session. This class handles consuming and managing 
    optional settings such as retries, proxies, and SSL customisation if desired.

    Examples
    --------
    This can be used in a context manager:

    .. code-block:: python

        >>> class HTTPClientImpl(BaseHTTPClient):
        ...     def __init__(self, *args, **kwargs):
        ...         super().__init__(*args, **kwargs)
        ...    def request(self, *args, **kwargs):
        ...         return super()._request(*args, **kwargs)

        >>> async with HTTPClientImpl() as client:
        ...     async with client.request("GET", "https://some-websi.te") as resp:
        ...         resp.raise_for_status()
        ...         body = await resp.read()

    Warning
    -------
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
        "proxy_auth",
        "proxy_headers",
        "proxy_url",
        "ssl_context",
        "timeout",
        "user_agent",
        "verify_ssl",
    )

    #: Whether to allow following of redirects or not. Generally you do not want this
    #: as it poses a security risk.
    #:
    #: :type: :obj:`bool`
    allow_redirects: bool

    #: The underlying client session used to make low level HTTP requests.
    #:
    #: :type: :obj:`aiohttp.ClientSession`
    client_session: aiohttp.ClientSession

    #: The number of requests that have been made. This acts as a unique ID for each request.
    #:
    #: :type: :obj:`int`
    in_count: int

    #: The logger used to write log messages.
    #:
    #: :type: :obj:`logging.Logger`
    logger: logging.Logger

    #: The asyncio event loop being used.
    #:
    #: :type: :obj:`asyncio.AbstractEventLoop`
    loop: asyncio.AbstractEventLoop

    #: Proxy authorization info.
    #:
    #: :type: :obj:`aiohttp.BasicAuth`, optional
    proxy_auth: typing.Optional[aiohttp.BasicAuth]

    #: Proxy headers.
    #:
    #: :type: :obj:`aiohttp.typedefs.LooseHeaders`, optional
    proxy_headers: typing.Optional[aiohttp.typedefs.LooseHeaders]

    #: Proxy URL to use.
    #:
    #: :type: :obj:`str`, optional
    proxy_url: typing.Optional[str]

    #: SSL context to use.
    #:
    #: :type: :obj:`ssl.SSLContext`, optional
    ssl_context: typing.Optional[ssl.SSLContext]

    #: Response timeout or``None`` if you are using the
    #: default for :mod:`aiohttp`.
    #:
    #: :type: :obj:`float`, optional
    timeout: typing.Optional[float]

    #: The user agent being used.
    #:
    #: Warning
    #: -------
    #: Certain areas of the Discord API may enforce specific user agents
    #: to be used for requests. You should not overwrite this generated value
    #: unless you know what you are doing. Invalid useragents may lead to
    #: bot account deauthorization.
    #:
    #: :type: :obj:`str`
    user_agent: str

    #: Whether to verify SSL certificates or not. Generally you want this turned on
    #: to prevent the risk of fake certificates being used to perform a
    #: "man-in-the-middle" (MITM) attack on your application. However, if you are
    #: stuck behind a proxy that cannot verify the certificates correctly, or are
    #: having other SSL-related issues, you may wish to turn this off.
    #:
    #: :type: :obj:`bool`
    verify_ssl: bool

    @abc.abstractmethod
    def __init__(
        self,
        *,
        allow_redirects: bool = False,
        json_serialize: typing.Optional[typing.Callable] = None,
        connector: typing.Optional[aiohttp.BaseConnector] = None,
        proxy_headers: typing.Optional[aiohttp.typedefs.LooseHeaders] = None,
        proxy_auth: typing.Optional[aiohttp.BasicAuth] = None,
        proxy_url: typing.Optional[str] = None,
        ssl_context: typing.Optional[ssl.SSLContext] = None,
        verify_ssl: bool = True,
        timeout: typing.Optional[float] = None,
    ) -> None:
        """
        Parameters
        ----------
        allow_redirects : :obj:`bool`
            If you find you are receiving multiple redirection responses causing 
            requests to fail, it is probably worth enabling this. Defaults to ``False`` 
            for security reasons. 
        json_serialize : :obj:`typing.Callable`, optional
            A callable that consumes a Python object and returns a JSON-encoded string.
            This defaults to :func:`json.dumps`.
        connector : :obj:`aiohttp.BaseConnector`, optional
            The :obj:`aiohttp.BaseConnector` to use for the client session, or ``None`` 
            if you wish to use the default instead.
        proxy_headers : :obj:`aiohttp.typedefs.LooseHeaders`, optional
            Proxy headers to pass.
        proxy_auth : :obj:`aiohttp.BasicAuth`, optional
            Proxy authentication to use.
        proxy_url : :obj:`str`, optional
            Proxy URL to use.
        ssl_context : :obj:`ssl.SSLContext`, optional
            SSL context to use.
        verify_ssl : :obj:`bool`
            Wheather to verify SSL.
        timeout : :obj:`float`, optional
            Timeout to apply to individual HTTP requests.
        """

        #: Whether to allow redirects or not.
        #:
        #: :type: :obj:`bool`
        self.allow_redirects = allow_redirects

        #: The HTTP client session to use.
        #:
        #: :type: :obj:`aiohttp.ClientSession`
        self.client_session = aiohttp.ClientSession(
            connector=connector, version=aiohttp.HttpVersion11, json_serialize=json_serialize or json.dumps,
        )

        #: The logger to use for this object.
        #:
        #: :type: :obj:`logging.Logger`
        self.logger = loggers.get_named_logger(self)

        #: User agent to use.
        #:
        #: :type: :obj:`str`
        self.user_agent = user_agent.user_agent()

        #: If ``True``, this will enforce SSL signed certificate verification, otherwise it will
        #: ignore potentially malicious SSL certificates.
        #:
        #: :type: :obj:`bool`
        self.verify_ssl = verify_ssl

        #: Optional proxy URL to use for HTTP requests.
        #:
        #: :type: :obj:`str`
        self.proxy_url = proxy_url

        #: Optional authorization to use if using a proxy.
        #:
        #: :type: :obj:`aiohttp.BasicAuth`
        self.proxy_auth = proxy_auth

        #: Optional proxy headers to pass.
        #:
        #: :type: :obj:`aiohttp.typedefs.LooseHeaders`
        self.proxy_headers = proxy_headers

        #: Optional SSL context to use.
        #:
        #: :type: :obj:`ssl.SSLContext`
        self.ssl_context: ssl.SSLContext = ssl_context

        #: Optional timeout for HTTP requests.
        #:
        #: :type: :obj:`float`
        self.timeout = timeout

        #: How many responses have been received.
        #:
        #: :type: :obj:`int`
        self.in_count = 0

    def _request(self, method, uri, **kwargs):
        """Calls :func:`aiohttp.ClientSession.request` and returns the context manager result.

        Parameters
        ----------
        method
            The HTTP method to use.
        uri
            The URI to send to.
        **kwargs
            Any other parameters to pass to :func:`aiohttp.ClientSession.request` when invoking it.
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
