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
"""Data class containing network-related configuration settings."""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = [
    "BasicAuthHeader",
    "ProxySettings",
    "HTTPTimeoutSettings",
    "HTTPSettings",
]

import base64
import typing

import attr

from hikari.utilities import constants
from hikari.utilities import data_binding


@attr.s(slots=True, kw_only=True, repr=False)
class BasicAuthHeader:
    """An object that can be set as a producer for a basic auth header."""

    username: str = attr.ib()
    """Username for the header."""

    password: str = attr.ib()
    """Password for the header."""

    @property
    def header(self) -> str:
        """Generate the header value and return it."""
        raw_token = f"{self.username}:{self.password}".encode("ascii")
        token_part = base64.b64encode(raw_token).decode("ascii")
        return f"{constants.BASICAUTH_TOKEN} {token_part}"

    def __str__(self) -> str:
        return self.header

    __repr__ = __str__


@attr.s(slots=True, kw_only=True)
class ProxySettings:
    """The proxy settings to use."""

    auth: typing.Optional[typing.Any] = attr.ib(default=None)
    """An object that when cast to a string, yields the proxy auth header."""

    headers: typing.Optional[data_binding.Headers] = attr.ib(default=None)
    """Additional headers to use for requests via a proxy, if required."""

    url: typing.Optional[str] = attr.ib(default=None)
    """The URL of the proxy to use."""

    trust_env: bool = attr.ib(default=False)
    """If `builtins.True`, and no proxy info is given, then `HTTP_PROXY` and
    `HTTPS_PROXY` will be used from the environment variables if present.

    Any proxy credentials will be read from the user's `netrc` file
    (https://www.gnu.org/software/inetutils/manual/html_node/The-_002enetrc-file.html)
    If `builtins.False`, then this information is instead ignored.
    Defaults to `builtins.False` if unspecified.
    """

    @property
    def all_headers(self) -> typing.Optional[data_binding.Headers]:
        """Return all proxy headers.

        Returns
        -------
        hikari.utilities.data_binding.Headers or builtins.None
            Any headers that are set, or `builtins.None` if no headers are to
            be sent with any request.
        """
        if self.headers is None:
            if self.auth is None:
                return None
            return {constants.PROXY_AUTHENTICATION_HEADER: self.auth}

        if self.auth is None:
            return self.headers
        return {**self.headers, constants.PROXY_AUTHENTICATION_HEADER: self.auth}


@attr.s(slots=True, kw_only=True)
class HTTPTimeoutSettings:
    """Settings to control HTTP request timeouts."""

    acquire_and_connect: typing.Optional[float] = attr.ib(default=None)
    """Timeout for `request_socket_connect` PLUS connection acquisition."""

    request_socket_connect: typing.Optional[float] = attr.ib(default=None)
    """Timeout for connecting a socket."""

    request_socket_read: typing.Optional[float] = attr.ib(default=None)
    """Timeout for reading a socket."""

    total: typing.Optional[float] = attr.ib(default=30.0)
    """Total timeout for entire request.

    Defaults to 30 seconds.
    """


@attr.s(slots=True, kw_only=True)
class HTTPSettings:
    """Settings to control the HTTP client."""

    allow_redirects: bool = attr.ib(default=False)
    """If `builtins.True`, allow following redirects from `3xx` HTTP responses.

    Generally you do not want to enable this unless you have a good reason to.
    """

    max_redirects: int = attr.ib(default=10)
    """The maximum number of redirects to allow.

    If `allow_redirects` is `builtins.False`, then this is ignored.
    """

    timeouts: HTTPTimeoutSettings = attr.ib(factory=HTTPTimeoutSettings)
    """Settings to control HTTP request timeouts."""

    verify_ssl: bool = attr.ib(default=True)
    """If `builtins.True`, then responses with invalid SSL certificates will be
    rejected. Generally you want to keep this enabled unless you have a
    problem with SSL and you know exactly what you are doing by disabling
    this. Disabling SSL  verification can have major security implications.
    You turn this off at your own risk.
    """
