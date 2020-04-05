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
"""Configuration data classes."""

__all__ = [
    "generate_config_attrs",
    "BaseConfig",
    "DebugConfig",
    "AIOHTTPConfig",
    "TokenConfig",
    "WebsocketConfig",
    "ShardConfig",
    "RESTConfig",
    "BotConfig",
]

import datetime
import re
import ssl
import typing

import aiohttp

from hikari import entities
from hikari import gateway_entities
from hikari import guilds
from hikari.internal import conversions
from hikari.internal import marshaller
from hikari.net import codes


class BaseConfig(entities.Deserializable):
    """Base class for any configuration data class."""

    if typing.TYPE_CHECKING:
        # pylint:disable=unused-argument
        # Screws up PyCharm and makes annoying warnings everywhere, so just
        # mute this. We can always make dummy constructors later, or find
        # another way around this perhaps.
        # This only ever takes kwargs.
        @typing.no_type_check
        def __init__(self, **kwargs) -> None:
            ...

        # pylint:enable=unused-argument


#: Decorator for :obj:`attr.s` classes that use the
#: :obj:`hikari.internal.marshaller` protocol.
generate_config_attrs = marshaller.attrs(kw_only=True)


@generate_config_attrs
class DebugConfig(BaseConfig):
    """Configuration for anything with a debugging mode."""

    #: Whether to enable debugging mode. Usually you don't want to enable this.
    #:
    #: :type: :obj:`bool`
    debug: bool = marshaller.attrib(deserializer=bool, if_undefined=False, default=False)


@generate_config_attrs
class AIOHTTPConfig(BaseConfig):
    """Config for components that use AIOHTTP somewhere."""

    #: If ``True``, allow following redirects from ``3xx`` HTTP responses.
    #: Generally you do not want to enable this unless you have a good reason
    #: to.
    #:
    #: Defaults to ``False`` if unspecified during deserialization.
    #:
    #: :type: :obj:`bool`
    allow_redirects: bool = marshaller.attrib(deserializer=bool, if_undefined=False, default=False)

    #: Either an implementation of :obj:`aiohttp.TCPConnector`.
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
    #: :type: :obj:`aiohttp.TCPConnector`, optional
    tcp_connector: typing.Optional[aiohttp.TCPConnector] = marshaller.attrib(
        deserializer=marshaller.dereference_handle, if_none=None, if_undefined=None, default=None
    )

    #: Optional proxy headers to provide in any HTTP requests.
    #:
    #: Defaults to ``None`` if unspecified during deserialization.
    #:
    #: :type: :obj:`typing.Mapping` [ :obj:`str`, :obj:`str` ], optional
    proxy_headers: typing.Optional[typing.Mapping[str, str]] = marshaller.attrib(
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
    verify_ssl: bool = marshaller.attrib(deserializer=bool, if_undefined=True, default=True)


@generate_config_attrs
class TokenConfig(BaseConfig):
    """Token config options."""

    #: The token to use.
    #:
    #: :type: :obj:`str`, optional
    token: typing.Optional[str] = marshaller.attrib(deserializer=str, if_none=None, if_undefined=None, default=None)


@generate_config_attrs
class WebsocketConfig(AIOHTTPConfig, TokenConfig, DebugConfig):
    """Single-websocket specific configuration options."""

    #: Whether to use zlib compression on the gateway for inbound messages or
    #: not. Usually you want this turned on.
    #:
    #: :type: :obj:`bool`
    gateway_use_compression: bool = marshaller.attrib(deserializer=bool, if_undefined=True, default=True)

    #: The gateway API version to use.
    #:
    #: If unspecified, then V6 is used.
    #:
    #: :type: :obj:`int`
    gateway_version: int = marshaller.attrib(deserializer=int, if_undefined=lambda: 6, default=6)

    #: The initial activity to set all shards to when starting the gateway. If
    #: ``None``, then no activity will be set.
    #:
    #: :type: :obj:`hikari.gateway_entities.GatewayActivity`, optional
    initial_activity: typing.Optional[gateway_entities.GatewayActivity] = marshaller.attrib(
        deserializer=gateway_entities.GatewayActivity.deserialize, if_none=None, if_undefined=None, default=None
    )

    #: The initial status to set the shards to when starting the gateway.
    #:
    #: :type: :obj:`str`
    initial_status: guilds.PresenceStatus = marshaller.attrib(
        deserializer=guilds.PresenceStatus.__getitem__, if_undefined=lambda: "online", default="online",
    )

    #: Whether to show up as AFK or not on sign-in.
    #:
    #: :type: :obj:`bool`
    initial_is_afk: bool = marshaller.attrib(deserializer=bool, if_undefined=False, default=False)

    #: The idle time to show on signing in, or ``None`` to not show an idle
    #: time.
    #:
    #: :type: :obj:`datetime.datetime`, optional
    initial_idle_since: typing.Optional[datetime.datetime] = marshaller.attrib(
        deserializer=conversions.unix_epoch_to_ts, if_none=None, if_undefined=None, default=None
    )

    #: The intents to use for the connection.
    #:
    #: If being deserialized, this can be an integer bitfield, or a sequence of
    #: intent names. If
    #: unspecified, this will be set to ``None``.
    #:
    #: :type: :obj:`hikari.net.codes.GatewayIntent`, optional
    #:
    #: Examples
    #: --------
    #:
    #: .. code-block:: python
    #:
    #:    # Python example
    #:    GatewayIntent.GUILDS | GatewayIntent.GUILD_MESSAGES
    #:
    #: ..code-block:: js
    #:
    #:    // JSON example, using explicit bitfield values
    #:    513
    #:    // JSON example, using an array of names
    #:    [ "GUILDS", "GUILD_MESSAGES" ]
    #:
    #: See :obj:`hikari.net.codes.GatewayIntent` for valid names of
    #: intents you can use. Integer values are as documented on Discord's
    #: developer portal.
    #:
    #: Warnings
    #: --------
    #: If you are using the V7 gateway implementation, you will NEED to provide
    #: explicit intent values for this field in order to get online.
    #: Additionally, intents that are classed by Discord as being privileged
    #: will require you to whitelist your application in order to use them.
    #:
    #: If you are using the V6 gateway implementation, setting this to ``None``
    #: will simply opt you into every event you can subscribe to.
    intents: typing.Optional[codes.GatewayIntent] = marshaller.attrib(
        deserializer=lambda value: marshaller.dereference_int_flag(codes.GatewayIntent, value),
        if_undefined=None,
        default=None,
    )

    #: The large threshold to use.
    large_threshold: int = marshaller.attrib(deserializer=int, if_undefined=lambda: 250, default=True)


def _parse_shard_info(payload):
    range_matcher = re.search(r"(\d+)\s*(\.{2,3})\s*(\d+)", payload)

    if not range_matcher:
        if isinstance(payload, str):
            payload = int(payload)

        if isinstance(payload, int):
            return [payload]

        raise ValueError('expected shard_ids to be one of int, list of int, or range string ("x..y")')

    minimum, range_mod, maximum = range_matcher.groups()
    minimum, maximum = int(minimum), int(maximum)
    if len(range_mod) == 3:
        maximum += 1

    return [*range(minimum, maximum)]


@generate_config_attrs
class ShardConfig(BaseConfig):
    """Definition of shard management configuration settings."""

    #: The shard IDs to produce shard connections for.
    #:
    #: If being deserialized, this can be several formats.
    #:     ``12``, ``"12"``:
    #:         A specific shard ID.
    #:     ``[0, 1, 2, 3, 8, 9, 10]``, ``["0", "1", "2", "3", "8", "9", "10"]``:
    #:         A sequence of shard IDs.
    #:     ``"5..16"``:
    #:         A range string. Two periods indicate a range of ``[5, 16)``
    #:         (inclusive beginning, exclusive end).
    #:     ``"5...16"``:
    #:         A range string. Three periods indicate a range of
    #:         ``[5, 17]`` (inclusive beginning, inclusive end).
    #:     ``None``:
    #:         The ``shard_count`` will be considered and that many shards will
    #:         be created for you. If the ``shard_count`` is also ``None``, then
    #:         auto-sharding will be performed for you.
    #:
    #: :type: :obj:`typing.Sequence` [ :obj:`int` ], optional
    shard_ids: typing.Sequence[int] = marshaller.attrib(
        deserializer=_parse_shard_info, if_none=None, if_undefined=None, default=None
    )

    #: The number of shards the entire distributed application should consist
    #: of. If you run multiple distributed instances of the bot, you should
    #: ensure this value is consistent.
    #:
    #: This can be set to `None` to enable auto-sharding. This is the default.
    #:
    #: :type: :obj:`int`, optional.
    shard_count: typing.Optional[int] = marshaller.attrib(deserializer=int, if_undefined=None, default=None)


@generate_config_attrs
class RESTConfig(AIOHTTPConfig, TokenConfig):
    """REST-specific configuration details."""

    #: The HTTP API version to use.
    #:
    #: If unspecified, then V7 is used.
    #:
    #: :type: :obj:`int`
    rest_version: int = marshaller.attrib(deserializer=int, if_undefined=lambda: 7, default=7)


@generate_config_attrs
class BotConfig(RESTConfig, ShardConfig, WebsocketConfig):
    """Configuration for a standard bot."""
