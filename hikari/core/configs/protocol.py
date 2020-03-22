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
"""Configuration objects for various low-level protocols such as HTTP
connections and SSL management, proxies, etc."""
__all__ = ["HTTPProtocolConfig"]

import ssl
import typing

import aiohttp

from hikari.core import entities
from hikari.internal_utilities import marshaller


@marshaller.attrs(kw_only=True)
class HTTPProtocolConfig(entities.Deserializable):
    """A configuration class that can be deserialized from a :obj:`dict`. This
    represents any HTTP-specific implementation and protocol details such as
    how to manage redirects, how to manage SSL, and how to use a proxy if
    needed.

    All fields are optional kwargs that can be passed to the constructor.

    "Deserialized" and "unspecified" defaults are only applicable if you
    create the object using :meth:`deserialize`.
    """

    #: If ``True``, allow following redirects from ``3xx`` HTTP responses.
    #: Generally you do not want to enable this unless you have a good reason
    #: to.
    #:
    #: Defaults to ``False`` if unspecified during deserialization.
    #:
    #: :type: :obj:`bool`
    allow_redirects: bool = marshaller.attrib(deserializer=bool, if_undefined=lambda: False, default=False)

    #: Either an implementation of :obj:`aiohttp.BaseConnector`.
    #:
    #: This may otherwise be ``None`` to use the default settings provided
    #: by :mod:`aiohttp`.
    #:
    #: This is deserialized as an object reference in the format
    #: ``package.module#object.attribute`` that is expected to point to the
    #: desired value.
    #:
    #: Defaults to ``None`` if unspecified during deserialization.
    #:
    #: :type: :obj:`aiohttp.BaseConnector`, optional
    connector: typing.Optional[aiohttp.BaseConnector] = marshaller.attrib(
        deserializer=marshaller.dereference_handle, if_none=None, if_undefined=None, default=None
    )

    #: Optional proxy headers to provide in any HTTP requests.
    #:
    #: Defaults to ``None`` if unspecified during deserialization.
    #:
    #: :type: :obj:`typing.Dict` [ :obj:`str`, :obj:`str` ], optional
    proxy_headers: typing.Optional[typing.Dict[str, str]] = marshaller.attrib(
        deserializer=dict, if_none=None, if_undefined=None, default=None
    )

    #: Optional proxy authorization to provide in any HTTP requests.
    #:
    #: This is deserialized using the format ``"basic {{base 64 string here}}"``.
    #:
    #: Defaults to ``None`` if unspecified during deserialization.
    #:
    #: :type: :obj:`aiohttp.BasicAuth`, optional
    proxy_auth: typing.Optional[aiohttp.BasicAuth] = marshaller.attrib(
        deserializer=aiohttp.BasicAuth.decode, if_none=None, if_undefined=None, default=None
    )

    #: The optional URL of the proxy to send requests via.
    #:
    #: Defaults to ``None`` if unspecified during deserialization.
    #:
    #: :type: :obj:`str`, optional
    proxy_url: typing.Optional[str] = marshaller.attrib(deserializer=str, if_undefined=None, if_none=None, default=None)

    #: Optional request timeout to use. If an HTTP request takes longer than
    #: this, it will be aborted.
    #:
    #: If not ``None``, the value represents a number of seconds as a floating
    #: point number.
    #:
    #: Defaults to ``None`` if unspecified during deserialization.
    #:
    #: :type: :obj:`float`, optional
    request_timeout: typing.Optional[float] = marshaller.attrib(
        deserializer=float, if_undefined=None, if_none=None, default=None
    )

    #: The optional SSL context to use.
    #:
    #: This is deserialized as an object reference in the format
    #: ``package.module#object.attribute`` that is expected to point to the
    #: desired value.
    #:
    #: Defaults to ``None`` if unspecified during deserialization.
    #:
    #: :type: :obj:`ssl.SSLContext`, optional
    ssl_context: typing.Optional[ssl.SSLContext] = marshaller.attrib(
        deserializer=marshaller.dereference_handle, if_none=None, if_undefined=None, default=None
    )

    #: If ``True``, then responses with invalid SSL certificates will be
    #: rejected. Generally you want to keep this enabled unless you have a
    #: problem with SSL and you know exactly what you are doing by disabling
    #: this. Disabling SSL verification can have major security implications.
    #: You turn this off at your own risk.
    #:
    #: Defaults to ``True`` if unspecified during deserialization.
    #:
    #: :type: :obj:`bool`
    verify_ssl: bool = marshaller.attrib(deserializer=bool, if_undefined=lambda: True, default=True)
