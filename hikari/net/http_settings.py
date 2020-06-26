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
"""Data class containing AIOHTTP-specific configuration settings."""

from __future__ import annotations

__all__: typing.Final[typing.Sequence[str]] = ["HTTPSettings"]

import typing

import aiohttp
import attr

if typing.TYPE_CHECKING:
    import ssl


@attr.s(kw_only=True, repr=False, auto_attribs=True)
@typing.final
class HTTPSettings:
    """Config for application that use AIOHTTP."""

    allow_redirects: bool = False
    """If `True`, allow following redirects from `3xx` HTTP responses.

    Generally you do not want to enable this unless you have a good reason to.
    """

    connector_owner: bool = True
    """Determines whether objects take ownership of their connectors.

    If `True`, the component consuming any connector will close the
    connector when closed.

    If you set this to `False`, and you provide a `tcp_connector_factory`,
    this will prevent the connector being closed by each component.

    Note that unless you provide a `tcp_connector_factory`, this will be
    ignored.
    """

    proxy_auth: typing.Optional[aiohttp.BasicAuth] = None
    """Optional proxy authorization to provide in any HTTP requests."""

    proxy_headers: typing.Optional[typing.Mapping[str, str]] = None
    """Optional proxy headers to provide in any HTTP requests."""

    proxy_url: typing.Optional[str] = None
    """The optional URL of the proxy to send requests via."""

    request_timeout: typing.Optional[float] = 10.0
    """Optional request timeout to use.

    If an HTTP request takes longer than this, it will be aborted.

    Defaults to 10 seconds.

    If not `None`, the value represents a number of seconds as a floating
    point number.
    """

    ssl_context: typing.Optional[ssl.SSLContext] = None
    """The optional SSL context to use."""

    tcp_connector: typing.Optional[aiohttp.TCPConnector] = None
    """An optional TCP connector to use.

    The client session will default to closing this connector on close unless
    you set the `connector_owner` to `False`. If you are planning to share
    the connector between clients, you should set that to `False`.
    """

    trust_env: bool = False
    """If `True`, and no proxy info is given, then `HTTP_PROXY` and
    `HTTPS_PROXY` will be used from the environment variables if present.

    Any proxy credentials will be read from the user's `netrc` file
    (https://www.gnu.org/software/inetutils/manual/html_node/The-_002enetrc-file.html)
    If `False`, then this information is instead ignored.
    Defaults to `False` if unspecified.
    """

    verify_ssl: bool = True
    """If `True`, then responses with invalid SSL certificates will be
    rejected. Generally you want to keep this enabled unless you have a
    problem with SSL and you know exactly what you are doing by disabling
    this. Disabling SSL  verification can have major security implications.
    You turn this off at your own risk.
    """
