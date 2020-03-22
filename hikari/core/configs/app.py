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
"""Core application configuration objects and options."""
__all__ = ["AppConfig"]

import typing

from hikari.core.configs import http as http_
from hikari.core.configs import gateway as gateway_
from hikari.internal_utilities import marshaller


@marshaller.attrs(kw_only=True)
class AppConfig:
    """Root application configuration object.

    All fields are optional kwargs that can be passed to the constructor.

    "Deserialized" and "unspecified" defaults are only applicable if you
    create the object using :meth:`deserialize`.

    Examples
    --------

    Initializing programatically:
        .. code-block:: python

            # Basic config
            config = AppConfig(token="1a2b3c4da9089288a.23rhagaa8==")

        .. code-block:: python

            # A more complicated config example
            config = AppConfig(
                gateway=GatewayConfig(
                    protocol=HTTPProtocolConfig(
                        allow_redirects=False,
                        proxy_auth=aiohttp.BasicAuth("username", "password"),
                        proxy_url="http://my.first.proxy.net:8080",
                        request_timeout=30.0,
                        verify_ssl=False,     # heresy! do not do this!
                    ),
                    sharding=ShardConfig(
                        shard_ids=range(0, 10),
                        shard_count=10
                    ),
                    version=6,
                ),
                http=HTTPConfig(
                    protocol=HTTPProtocolConfig(
                        allow_redirects=True,
                        proxy_auth=aiohttp.BasicAuth.decode("Basic dXNlcm5hbWU6cGFzc3dvcmQ="),
                        proxy_url="http://my.other.proxy.net:8080",
                        request_timeout=30.0,
                        ssl_context=mybot.utils.ssl.MySSLContext,
                        verify_ssl=True
                    ),
                    version=7,
                ),
                token="1a2b3c4da9089288a.23rhagaa8==",
            )

    Initializing from a file:
        .. code-block:: python

            # loading a JSON file
            with open("foo.json") as fp:
                config = AppConfig.deserialize(json.load(fp))

        .. code-block:: js

            /* basic config */
            {
                "token": "1a2b3c4da9089288a.23rhagaa8=="
            }

        .. code-block:: js

            /* a more complicated config example */
            {
                "gateway": {
                    "protocol": {
                        "allow_redirects": false,
                        "proxy_auth": "Basic dXNlcm5hbWU6cGFzc3dvcmQ=",
                        "proxy_url": "http://my.first.proxy.net:8080",
                        "request_timeout": 30.0,
                        "verify_ssl": false      // heresy, do not do this!
                    },
                    "sharding": {
                        "shard_ids": "0..10",
                        "shard_count": 10
                    },
                    "version": 6
                },
                "http": {
                    "protocol": {
                        "allow_redirects": true,
                        "proxy_auth": "Basic dXNlcm5hbWU6cGFzc3dvcmQ=",
                        "proxy_url": "http://my.other.proxy.net:8080",
                        "request_timeout": 30.0,
                        "ssl_context": "mybot.utils.ssl#MySSLContext",
                        "verify_ssl": true
                    },
                    "version": 7
                },
                "token": "1a2b3c4da9089288a.23rhagaa8=="
            }

    Of course, comments are not valid in actual standard JSON; I added them
    simply for reference for this example.
    """

    #: The HTTP configuration to use.
    #:
    #: If unspecified or None, then this will be a set of default values.
    #:
    #: :type: :obj:`hikari.core.configs.http.HTTPConfig`, optional
    http: typing.Optional[http_.HTTPConfig] = marshaller.attrib(
        deserializer=http_.HTTPConfig.deserialize, if_none=None, if_undefined=None, default=None
    )

    #: The gateway configuration to use.
    #:
    #: If unspecified or None, then this will be a set of default values.
    #:
    #: :type: :obj:`hikari.core.configs.gateway.GatewayConfig`, optional
    gateway: typing.Optional[gateway_.GatewayConfig] = marshaller.attrib(
        deserializer=gateway_.GatewayConfig.deserialize, if_none=None, if_undefined=None, default=None
    )

    #: The global token to use, if applicable. This can be overridden for each
    #: component that requires it.
    #:
    #: Note that this should not start with ``Bot`` or ``Bearer``. This is
    #: detected automatically.
    #:
    #: :type: :obj:`str`, optional
    token: typing.Optional[str] = marshaller.attrib(deserializer=str, if_none=None, if_undefined=None, default=None)
