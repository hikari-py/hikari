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

from __future__ import annotations

__all__ = [
    "BaseConfig",
    "DebugConfig",
    "AIOHTTPConfig",
    "TokenConfig",
    "GatewayConfig",
    "RESTConfig",
    "BotConfig",
]

import datetime
import re
import typing

import aiohttp
import attr

from hikari import gateway_entities
from hikari import guilds
from hikari import intents as _intents
from hikari.internal import conversions
from hikari.internal import marshaller
from hikari.internal import urls

if typing.TYPE_CHECKING:
    import ssl


@marshaller.marshallable()
@attr.s(kw_only=True, repr=False)
class BaseConfig(marshaller.Deserializable):
    """Base class for any configuration data class."""


@marshaller.marshallable()
@attr.s(kw_only=True, repr=False)
class DebugConfig(BaseConfig):
    """Configuration for anything with a debugging mode.

    Attributes
    ----------
    debug : bool
        Whether to enable debugging mode. Usually you don't want to enable this.
    """

    debug: bool = marshaller.attrib(deserializer=bool, if_undefined=False, default=False)


@marshaller.marshallable()
@attr.s(kw_only=True, repr=False)
class AIOHTTPConfig(BaseConfig):
    """Config for components that use AIOHTTP somewhere.

    Attributes
    ----------
    allow_redirects : bool
        If `True`, allow following redirects from `3xx` HTTP responses.
        Generally you do not want to enable this unless you have a good reason to.
        Defaults to `False` if unspecified during deserialization.
    proxy_auth : aiohttp.BasicAuth, optional
        Optional proxy authorization to provide in any HTTP requests.
        This is deserialized using the format `"basic {{base 64 string here}}"`.
        Defaults to `None` if unspecified during deserialization.
    proxy_headers : typing.Mapping[str, str], optional
        Optional proxy headers to provide in any HTTP requests.
        Defaults to `None` if unspecified during deserialization.
    proxy_url : str, optional
        The optional URL of the proxy to send requests via.
        Defaults to `None` if unspecified during deserialization.
    request_timeout : float, optional
        Optional request timeout to use. If an HTTP request takes longer than
        this, it will be aborted.
        If not `None`, the value represents a number of seconds as a floating
        point number.
        Defaults to `None` if unspecified during deserialization.
    ssl_context : ssl.SSLContext, optional
        The optional SSL context to use.
        This is deserialized as an object reference in the format
        `package.module#object.attribute` that is expected to point to the
        desired value.
        Defaults to `None` if unspecified during deserialization.
    tcp_connector : aiohttp.TCPConnector, optional
        This may otherwise be `None` to use the default settings provided by
        `aiohttp`.
        This is deserialized as an object reference in the format
        `package.module#object.attribute` that is expected to point to the
        desired value.
        Defaults to `None` if unspecified during deserialization.
    trust_env: bool
        If `True`, and no proxy info is given, then `HTTP_PROXY` and
        `HTTPS_PROXY` will be used from the environment variables if present.
        Any proxy credentials will be read from the user's `netrc` file
        (https://www.gnu.org/software/inetutils/manual/html_node/The-_002enetrc-file.html)
        If `False`, then this information is instead ignored.
        Defaults to `False` if unspecified.
    verify_ssl : bool
        If `True`, then responses with invalid SSL certificates will be
        rejected. Generally you want to keep this enabled unless you have a
        problem with SSL and you know exactly what you are doing by disabling
        this. Disabling SSL  verification can have major security implications.
        You turn this off at your own risk.
        Defaults to `True` if unspecified during deserialization.
    """

    allow_redirects: bool = marshaller.attrib(deserializer=bool, if_undefined=False, default=False)

    tcp_connector: typing.Optional[aiohttp.TCPConnector] = marshaller.attrib(
        deserializer=marshaller.dereference_handle, if_none=None, if_undefined=None, default=None
    )

    proxy_auth: typing.Optional[aiohttp.BasicAuth] = marshaller.attrib(
        deserializer=aiohttp.BasicAuth.decode, if_none=None, if_undefined=None, default=None
    )

    proxy_headers: typing.Optional[typing.Mapping[str, str]] = marshaller.attrib(
        deserializer=dict, if_none=None, if_undefined=None, default=None
    )

    proxy_url: typing.Optional[str] = marshaller.attrib(deserializer=str, if_undefined=None, if_none=None, default=None)

    request_timeout: typing.Optional[float] = marshaller.attrib(
        deserializer=float, if_undefined=None, if_none=None, default=None
    )

    ssl_context: typing.Optional[ssl.SSLContext] = marshaller.attrib(
        deserializer=marshaller.dereference_handle, if_none=None, if_undefined=None, default=None
    )

    trust_env: bool = marshaller.attrib(deserializer=bool, if_undefined=True, default=False)

    verify_ssl: bool = marshaller.attrib(deserializer=bool, if_undefined=True, default=True)


@marshaller.marshallable()
@attr.s(kw_only=True, repr=False)
class TokenConfig(BaseConfig):
    """Token config options.

    Attributes
    ----------
    token : str, optional
        The token to use.
    """

    token: typing.Optional[str] = marshaller.attrib(deserializer=str, if_none=None, if_undefined=None, default=None)
    """The token to use."""


def _parse_shard_info(payload):
    range_matcher = re.search(r"(\d+)\s*(\.{2,3})\s*(\d+)", payload) if isinstance(payload, str) else None

    if not range_matcher:
        if isinstance(payload, int):
            return [payload]

        if isinstance(payload, list):
            return payload

        raise ValueError('expected shard_ids to be one of int, list of int, or range string ("x..y" or "x...y")')

    minimum, range_mod, maximum = range_matcher.groups()
    minimum, maximum = int(minimum), int(maximum)
    if len(range_mod) == 3:
        maximum += 1

    return [*range(minimum, maximum)]


def _gateway_version_default() -> int:
    return 6


def _initial_status_default() -> typing.Literal[guilds.PresenceStatus.ONLINE]:
    return guilds.PresenceStatus.ONLINE


def _deserialize_intents(value) -> _intents.Intent:
    return conversions.dereference_int_flag(_intents.Intent, value)


def _large_threshold_default() -> int:
    return 250


@marshaller.marshallable()
@attr.s(kw_only=True, repr=False)
class GatewayConfig(AIOHTTPConfig, DebugConfig, TokenConfig):
    """Single-websocket specific configuration options.

    Attributes
    ----------
    allow_redirects : bool
        If `True`, allow following redirects from `3xx` HTTP responses.
        Generally you do not want to enable this unless you have a good reason to.
        Defaults to `False` if unspecified during deserialization.
    debug : bool
        Whether to enable debugging mode. Usually you don't want to enable this.
    gateway_use_compression : bool
        Whether to use zlib compression on the gateway for inbound messages.
        Usually you want this turned on.
    gateway_version : int
        The gateway API version to use. Defaults to v6
    initial_activity : hikari.gateway_entities.Activity, optional
        The initial activity to set all shards to when starting the gateway.
        If this is `None` then no activity will be set, this is the default.
    initial_status : hikari.guilds.PresenceStatus
        The initial status to set the shards to when starting the gateway.
        Defaults to `ONLINE`.
    initial_is_afk : bool
        Whether to show up as AFK or not on sign-in.
    initial_idle_since : datetime.datetime, optional
        The idle time to show on signing in.
        If set to `None` to not show an idle time, this is the default.
    intents : hikari.intents.Intent
        The intents to use for the connection.
        If being deserialized, this can be an integer bitfield, or a sequence of
        intent names. If unspecified, this will be set to `None`.
    large_threshold : int
        The large threshold to use.
    proxy_headers : typing.Mapping[str, str], optional
        Optional proxy headers to provide in any HTTP requests.
        Defaults to `None` if unspecified during deserialization.
    proxy_auth : aiohttp.BasicAuth, optional
        Optional proxy authorization to provide in any HTTP requests.
        This is deserialized using the format `"basic {{base 64 string here}}"`.
        Defaults to `None` if unspecified during deserialization.
    proxy_url : str, optional
        The optional URL of the proxy to send requests via.
        Defaults to `None` if unspecified during deserialization.
    request_timeout : float, optional
        Optional request timeout to use. If an HTTP request takes longer than
        this, it will be aborted.
        If not `None`, the value represents a number of seconds as a floating
        point number.
        Defaults to `None` if unspecified during deserialization.
    shard_count : int, optional
        The number of shards the entire distributed application should consists
        of. If you run multiple distributed instances of the bot, you should
        ensure this value is consistent.
        This can be set to `None` to enable auto-sharding. This is the default.
    shard_id : typing.Sequence[int], optional
        The shard IDs to produce shard connections for.
        If being deserialized, this can be several formats shown in `notes`.
    ssl_context : ssl.SSLContext, optional
        The optional SSL context to use.
        This is deserialized as an object reference in the format
        `package.module#object.attribute` that is expected to point to the
        desired value.
        Defaults to `None` if unspecified during deserialization.
    tcp_connector : aiohttp.TCPConnector, optional
        This may otherwise be `None` to use the default settings provided by
        `aiohttp`.
        This is deserialized as an object reference in the format
        `package.module#object.attribute` that is expected to point to the
        desired value.
        Defaults to `None` if unspecified during deserialization.
    token : str, optional
        The token to use.
    verify_ssl : bool
        If `True`, then responses with invalid SSL certificates will be
        rejected. Generally you want to keep this enabled unless you have a
        problem with SSL and you know exactly what you are doing by disabling
        this. Disabling SSL  verification can have major security implications.
        You turn this off at your own risk.
        Defaults to `True` if unspecified during deserialization.

    !!! note
        The several formats for `shard_id` are as follows:

        * A specific shard ID (e.g. `12`);
        * A sequence of shard IDs (e.g. `[0, 1, 2, 3, 8, 9, 10]`);
        * A range string. Two periods indicate a range of `[5, 16]`
            (inclusive beginning, exclusive end).
        * A range string. Three periods indicate a range of
            `[5, 17]` (inclusive beginning, inclusive end);
        * `None` this means `shard_count` will be considered and that many
            shards will be created for you. If the `shard_count` is also
            `None` then auto-sharding will be performed for you.

    !!! note

        If being deserialized, `intents` can be an integer bitfield, or a
        sequence of intent names. If unspecified, `intents` will be set to
        `None`.

        See `hikari.intents.Intent` for valid names of intents you
        can use. Integer values are as documented on Discord's developer portal.

    !!! warning
        If you are using the V7 gateway implementation, you will NEED to provide
        explicit `intents` values for this field in order to get online.
        Additionally, intents that are classed by Discord as being privileged
        will require you to whitelist your application in order to use them.

        If you are using the V6 gateway implementation, setting `intents` to
        `None` will simply opt you into every event you can subscribe to.
    """

    gateway_use_compression: bool = marshaller.attrib(deserializer=bool, if_undefined=True, default=True)

    gateway_version: int = marshaller.attrib(deserializer=int, if_undefined=_gateway_version_default, default=6)

    initial_activity: typing.Optional[gateway_entities.Activity] = marshaller.attrib(
        deserializer=gateway_entities.Activity.deserialize, if_none=None, if_undefined=None, default=None
    )

    initial_status: guilds.PresenceStatus = marshaller.attrib(
        deserializer=guilds.PresenceStatus, if_undefined=_initial_status_default, default=guilds.PresenceStatus.ONLINE,
    )

    initial_is_afk: bool = marshaller.attrib(deserializer=bool, if_undefined=False, default=False)

    initial_idle_since: typing.Optional[datetime.datetime] = marshaller.attrib(
        deserializer=datetime.datetime.fromtimestamp, if_none=None, if_undefined=None, default=None
    )

    intents: typing.Optional[_intents.Intent] = marshaller.attrib(
        deserializer=_deserialize_intents, if_undefined=None, default=None,
    )

    large_threshold: int = marshaller.attrib(deserializer=int, if_undefined=_large_threshold_default, default=250)

    shard_ids: typing.Optional[typing.Sequence[int]] = marshaller.attrib(
        deserializer=_parse_shard_info, if_none=None, if_undefined=None, default=None
    )

    shard_count: typing.Optional[int] = marshaller.attrib(deserializer=int, if_undefined=None, default=None)


def _token_type_default() -> str:
    return "Bot"


def _rest_version_default() -> int:
    return 6


def _rest_url_default() -> str:
    return urls.REST_API_URL


def _cdn_url_default() -> str:
    return urls.BASE_CDN_URL


def _oauth2_url_default() -> str:
    return urls.OAUTH2_API_URL


@marshaller.marshallable()
@attr.s(kw_only=True, repr=False)
class RESTConfig(AIOHTTPConfig, DebugConfig, TokenConfig):
    """Single-websocket specific configuration options.

    Attributes
    ----------
    allow_redirects : bool
        If `True`, allow following redirects from `3xx` HTTP responses.
        Generally you do not want to enable this unless you have a good reason to.
        Defaults to `False` if unspecified during deserialization.
    oauth2_url : str
        Can be specified to override the default URL for the Discord OAuth2 API.
        Generally there is no reason to need to specify this, but it can be
        useful for testing, amongst other things.
    rest_url : str
        Can be specified to override the default URL for the Discord API itself.
        Generally there is no reason to need to specify this, but it can be
        useful for testing, amongst other things.
        You can put format-string placeholders in the URL such as `{0.version}`
        to interpolate the chosen API version to use.
    proxy_headers : typing.Mapping[str, str], optional
        Optional proxy headers to provide in any HTTP requests.
        Defaults to `None` if unspecified during deserialization.
    proxy_auth : aiohttp.BasicAuth, optional
        Optional proxy authorization to provide in any HTTP requests.
        This is deserialized using the format `"basic {{base 64 string here}}"`.
        Defaults to `None` if unspecified during deserialization.
    proxy_url : str, optional
        The optional URL of the proxy to send requests via.
        Defaults to `None` if unspecified during deserialization.
    request_timeout : float, optional
        Optional request timeout to use. If an HTTP request takes longer than
        this, it will be aborted.
        If not `None`, the value represents a number of seconds as a floating
        point number.
        Defaults to `None` if unspecified during deserialization.
    ssl_context : ssl.SSLContext, optional
        The optional SSL context to use.
        This is deserialized as an object reference in the format
        `package.module#object.attribute` that is expected to point to the
        desired value.
        Defaults to `None` if unspecified during deserialization.
    tcp_connector : aiohttp.TCPConnector, optional
        This may otherwise be `None` to use the default settings provided by
        `aiohttp`.
        This is deserialized as an object reference in the format
        `package.module#object.attribute` that is expected to point to the
        desired value.
        Defaults to `None` if unspecified during deserialization.
    verify_ssl : bool
        If `True`, then responses with invalid SSL certificates will be
        rejected. Generally you want to keep this enabled unless you have a
        problem with SSL and you know exactly what you are doing by disabling
        this. Disabling SSL  verification can have major security implications.
        You turn this off at your own risk.
        Defaults to `True` if unspecified during deserialization.
    token : str, optional
        The token to use.
    debug : bool
        Whether to enable debugging mode. Usually you don't want to enable this.
    token_type : str, optional
        Token authentication scheme, this defaults to `"Bot"` and  should be
        one of `"Bot"` or `"Bearer"`, or `None` if not relevant.
    rest_version : int
        The HTTP API version to use. If unspecified, then V7 is used.
    """

    oauth2_url: str = marshaller.attrib(
        deserializer=str, if_undefined=_oauth2_url_default, default=_oauth2_url_default()
    )

    rest_url: str = marshaller.attrib(deserializer=str, if_undefined=_rest_url_default, default=_rest_url_default())

    rest_version: int = marshaller.attrib(
        deserializer=int, if_undefined=_rest_version_default, default=_rest_version_default()
    )

    token_type: typing.Optional[str] = marshaller.attrib(
        deserializer=str, if_undefined=_token_type_default, if_none=None, default="Bot"
    )


@marshaller.marshallable()
@attr.s(kw_only=True, repr=False)
class BotConfig(RESTConfig, GatewayConfig):
    """Configuration for a standard bot.

    Attributes
    ----------
    allow_redirects : bool
        If `True`, allow following redirects from `3xx` HTTP responses.
        Generally you do not want to enable this unless you have a good reason to.
        Defaults to `False` if unspecified during deserialization.
    debug : bool
        Whether to enable debugging mode. Usually you don't want to enable this.
    gateway_use_compression : bool
        Whether to use zlib compression on the gateway for inbound messages.
        Usually you want this turned on.
    gateway_version : int
        The gateway API version to use. Defaults to v6
    initial_activity : hikari.gateway_entities.Activity, optional
        The initial activity to set all shards to when starting the gateway.
        If this is `None` then no activity will be set, this is the default.
    initial_status : hikari.guilds.PresenceStatus
        The initial status to set the shards to when starting the gateway.
        Defaults to `ONLINE`.
    initial_is_afk : bool
        Whether to show up as AFK or not on sign-in.
    initial_idle_since : datetime.datetime, optional
        The idle time to show on signing in.
        If set to `None` to not show an idle time, this is the default.
    intents : hikari.intents.Intent
        The intents to use for the connection.
        If being deserialized, this can be an integer bitfield, or a sequence of
        intent names. If unspecified, this will be set to `None`.
    large_threshold : int
        The large threshold to use.
    oauth2_url : str
        Can be specified to override the default URL for the Discord OAuth2 API.
        Generally there is no reason to need to specify this, but it can be
        useful for testing, amongst other things.
    proxy_headers : typing.Mapping[str, str], optional
        Optional proxy headers to provide in any HTTP requests.
        Defaults to `None` if unspecified during deserialization.
    proxy_auth : aiohttp.BasicAuth, optional
        Optional proxy authorization to provide in any HTTP requests.
        This is deserialized using the format `"basic {{base 64 string here}}"`.
        Defaults to `None` if unspecified during deserialization.
    proxy_url : str, optional
        The optional URL of the proxy to send requests via.
        Defaults to `None` if unspecified during deserialization.
    request_timeout : float, optional
        Optional request timeout to use. If an HTTP request takes longer than
        this, it will be aborted.
        If not `None`, the value represents a number of seconds as a floating
        point number.
        Defaults to `None` if unspecified during deserialization.
    rest_url : str
        Can be specified to override the default URL for the Discord API itself.
        Generally there is no reason to need to specify this, but it can be
        useful for testing, amongst other things.
        You can put format-string placeholders in the URL such as `{0.version}`
        to interpolate the chosen API version to use.
    rest_version : int
        The HTTP API version to use. If unspecified, then V7 is used.
    shard_count : int, optional
        The number of shards the entire distributed application should consists
        of. If you run multiple distributed instances of the bot, you should
        ensure this value is consistent.
        This can be set to `None` to enable auto-sharding. This is the default.
    shard_id : typing.Sequence[int], optional
        The shard IDs to produce shard connections for.
        If being deserialized, this can be several formats shown in `notes`.
    ssl_context : ssl.SSLContext, optional
        The optional SSL context to use.
        This is deserialized as an object reference in the format
        `package.module#object.attribute` that is expected to point to the
        desired value.
        Defaults to `None` if unspecified during deserialization.
    tcp_connector : aiohttp.TCPConnector, optional
        This may otherwise be `None` to use the default settings provided by
        `aiohttp`.
        This is deserialized as an object reference in the format
        `package.module#object.attribute` that is expected to point to the
        desired value.
        Defaults to `None` if unspecified during deserialization.
    token : str, optional
        The token to use.
    token_type : str, optional
        Token authentication scheme, this defaults to `"Bot"` and  should be
        one of `"Bot"` or `"Bearer"`, or `None` if not relevant.
    verify_ssl : bool
        If `True`, then responses with invalid SSL certificates will be
        rejected. Generally you want to keep this enabled unless you have a
        problem with SSL and you know exactly what you are doing by disabling
        this. Disabling SSL  verification can have major security implications.
        You turn this off at your own risk.
        Defaults to `True` if unspecified during deserialization.

    !!! note
        The several formats for `shard_id` are as follows:

        * A specific shard ID (e.g. `12`);
        * A sequence of shard IDs (e.g. `[0, 1, 2, 3, 8, 9, 10]`);
        * A range string. Two periods indicate a range of `[5, 16]`
            (inclusive beginning, exclusive end).
        * A range string. Three periods indicate a range of
            `[5, 17]` (inclusive beginning, inclusive end);
        * `None` this means `shard_count` will be considered and that many
            shards will be created for you. If the `shard_count` is also
            `None` then auto-sharding will be performed for you.

    !!! note

        If being deserialized, `intents` can be an integer bitfield, or a
        sequence of intent names. If unspecified, `intents` will be set to
        `None`.

        See `hikari.intents.Intent` for valid names of intents you
        can use. Integer values are as documented on Discord's developer portal.

    !!! warning
        If you are using the V7 gateway implementation, you will NEED to provide
        explicit `intents` values for this field in order to get online.
        Additionally, intents that are classed by Discord as being privileged
        will require you to whitelist your application in order to use them.

        If you are using the V6 gateway implementation, setting `intents` to
        `None` will simply opt you into every event you can subscribe to.
    """
