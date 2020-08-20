# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
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
"""Implementation of a V6 and V7 compatible HTTP API for Discord.

This also includes implementations of `hikari.api.app.IApp` designed towards
providing RESTful functionality.
"""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = [
    "BasicLazyCachedTCPConnectorFactory",
    "RESTApp",
    "RESTClientImpl",
]

import asyncio
import collections
import contextlib
import datetime
import http
import logging
import math
import os
import re
import typing

import aiohttp
import attr

from hikari import channels
from hikari import config
from hikari import embeds as embeds_
from hikari import emojis
from hikari import errors
from hikari import files
from hikari import guilds
from hikari import iterators
from hikari import snowflakes
from hikari import traits
from hikari import undefined
from hikari import users
from hikari.api import rest as rest_api
from hikari.impl import buckets
from hikari.impl import entity_factory as entity_factory_impl
from hikari.impl import rate_limits
from hikari.impl import special_endpoints
from hikari.utilities import constants
from hikari.utilities import data_binding
from hikari.utilities import date
from hikari.utilities import net
from hikari.utilities import routes

if typing.TYPE_CHECKING:
    import concurrent.futures
    import types

    from hikari import applications
    from hikari import audit_logs
    from hikari import colors
    from hikari import invites
    from hikari import messages as messages_
    from hikari import permissions as permissions_
    from hikari import sessions
    from hikari import voices
    from hikari import webhooks
    from hikari.api import entity_factory as entity_factory_

_LOGGER: typing.Final[logging.Logger] = logging.getLogger("hikari.rest")


@typing.final
class BasicLazyCachedTCPConnectorFactory(rest_api.ConnectorFactory):
    """Lazy cached TCP connector factory."""

    __slots__: typing.Sequence[str] = ("connector", "connector_kwargs")

    def __init__(self, **kwargs: typing.Any) -> None:
        self.connector: typing.Optional[aiohttp.TCPConnector] = None
        self.connector_kwargs = kwargs

    async def close(self) -> None:
        if self.connector is not None:
            await self.connector.close()
            self.connector = None

    def acquire(self) -> aiohttp.BaseConnector:
        if self.connector is None:
            self.connector = aiohttp.TCPConnector(**self.connector_kwargs)

        return self.connector


class _RESTProvider(traits.RESTAware):
    __slots__: typing.Sequence[str] = ("_rest",)

    def __init__(self, rest: typing.Callable[[], rest_api.RESTClient]) -> None:
        self._rest = rest

    @property
    def rest(self) -> rest_api.RESTClient:
        return self._rest()

    @property
    def http_settings(self) -> config.HTTPSettings:
        return self._rest().http_settings

    @property
    def proxy_settings(self) -> config.ProxySettings:
        return self._rest().proxy_settings


class RESTApp(traits.ExecutorAware):
    """The base for a HTTP-only Discord application.

    This comprises of a shared TCP connector connection pool, and can have
    `hikari.api.rest.IRESTApp` instances for specific credentials acquired
    from it.

    Parameters
    ----------
    connector_factory : typing.Optional[ConnectorFactory]
        A factory that produces an `aiohttp.BaseConnector` when requested.

        Defaults to a connector for a shared `aiohttp.TCPConnector` if
        `builtins.None`.

        The connector factory is expected to handle providing locks around
        resources and caching any result as desired.
    connector_owner : builtins.bool
        If you created the connector yourself, set this to `builtins.True` if
        you want this component to destroy the connector once closed. Otherwise,
        `builtins.False` will prevent this and you will have to do this
        manually. The latter is useful if you wish to maintain a shared
        connection pool across your application with other non-Hikari
        components.
    debug : builtins.bool
        If `builtins.True`, then much more information is logged each time a
        request is made. Generally you do not need this to be on, so it will
        default to `builtins.False` instead.
    executor : typing.Optional[concurrent.futures.Executor]
        The executor to use for blocking file IO operations. If `builtins.None`
        is passed, then the default `concurrent.futures.ThreadPoolExecutor` for
        the `asyncio.AbstractEventLoop` will be used instead.
    http_settings : typing.Optional[hikari.config.HTTPSettings]
        HTTP settings to use. Sane defaults are used if this is
        `builtins.None`.
    proxy_settings : typing.Optional[hikari.config.ProxySettings]
        Proxy settings to use. If `builtins.None` then no proxy configuration
        will be used.
    url : str or hikari.undefined.UndefinedType
        The base URL for the API. You can generally leave this as being
        `undefined` and the correct default API base URL will be generated.
    version : builtins.int
        The Discord API version to use. Can be `6` (stable, default), or `7`
        (undocumented development release).

    !!! note
        This event loop will be bound to a connector when the first call
        to `acquire` is made.
    """

    __slots__: typing.Sequence[str] = (
        "_connector_factory",
        "_connector_owner",
        "_debug",
        "_event_loop",
        "_executor",
        "_http_settings",
        "_proxy_settings",
        "_url",
        "_version",
    )

    def __init__(
        self,
        *,
        connector_factory: typing.Optional[rest_api.ConnectorFactory] = None,
        connector_owner: bool = True,
        debug: bool = False,
        executor: typing.Optional[concurrent.futures.Executor] = None,
        http_settings: typing.Optional[config.HTTPSettings] = None,
        proxy_settings: typing.Optional[config.ProxySettings] = None,
        url: typing.Optional[str] = None,
        version: int = 6,
    ) -> None:
        # Lazy initialized later, since we must initialize this in the event
        # loop we run the application from, otherwise aiohttp throws complaints
        # at us. Quart, amongst other libraries, causes issues with this by
        # making a new event loop on startup, which means if we initialised
        # the connector here and initialised this class in global scope, it
        # would potentially end up using the wrong event loop and aiohttp
        # would then fail when creating an HTTP request.
        self._connector_factory: rest_api.ConnectorFactory = connector_factory or BasicLazyCachedTCPConnectorFactory()
        self._connector_owner = connector_owner
        self._debug = debug
        self._event_loop: typing.Optional[asyncio.AbstractEventLoop] = None
        self._executor = executor
        self._http_settings = config.HTTPSettings() if http_settings is None else http_settings
        self._proxy_settings = config.ProxySettings() if proxy_settings is None else proxy_settings
        self._url = url
        self._version = version

    @property
    def executor(self) -> typing.Optional[concurrent.futures.Executor]:
        return self._executor

    @property
    def http_settings(self) -> config.HTTPSettings:
        return self._http_settings

    @property
    def is_debug_enabled(self) -> bool:
        return self._debug

    @property
    def proxy_settings(self) -> config.ProxySettings:
        return self._proxy_settings

    def acquire(self, token: str, token_type: str = constants.BEARER_TOKEN) -> rest_api.RESTClient:
        loop = asyncio.get_running_loop()

        if self._event_loop is None:
            self._event_loop = loop

        if loop != self._event_loop:
            raise RuntimeError("Cannot use this object on a different event loop... please create a new instance.")

        # Since we essentially mimic a fake App instance, we need to make a circular provider.
        # We can achieve this using a lambda. This allows the entity factory to build models that
        # are also REST-aware
        entity_factory = entity_factory_impl.EntityFactoryImpl(_RESTProvider(lambda: rest_client))

        rest_client = RESTClientImpl(
            connector_factory=self._connector_factory,
            connector_owner=self._connector_owner,
            debug=self._debug,
            entity_factory=entity_factory,
            executor=self._executor,
            http_settings=self._http_settings,
            proxy_settings=self._proxy_settings,
            token=token,
            token_type=token_type,
            rest_url=self._url,
            version=self._version,
        )

        return rest_client

    async def close(self) -> None:
        if self._connector_owner:
            await self._connector_factory.close()

    async def __aenter__(self) -> RESTApp:
        return self

    async def __aexit__(
        self,
        exc_type: typing.Optional[typing.Type[BaseException]],
        exc_val: typing.Optional[BaseException],
        exc_tb: typing.Optional[types.TracebackType],
    ) -> None:
        await self.close()


class RESTClientImpl(rest_api.RESTClient):
    """Implementation of the V6 and V7-compatible Discord HTTP API.

    This manages making HTTP/1.1 requests to the API and using the entity
    factory within the passed application instance to deserialize JSON responses
    to Pythonic data classes that are used throughout this library.

    Parameters
    ----------
    connector_factory : typing.Optional[ConnectorFactory]
        A factory that produces an `aiohttp.BaseConnector` when requested.

        Defaults to a connector for a shared `aiohttp.TCPConnector` if
        `builtins.None`.

        The connector factory is expected to handle providing locks around
        resources and caching any result as desired.
    connector_owner : builtins.bool
        If you created the connector yourself, set this to `builtins.True` if
        you want this component to destroy the connector once closed. Otherwise,
        `builtins.False` will prevent this and you will have to do this
        manually. The latter is useful if you wish to maintain a shared
        connection pool across your application with other non-Hikari
        components.
    debug : builtins.bool
        If `builtins.True`, this will enable logging of each payload sent and
        received, as well as information such as DNS cache hits and misses, and
        other information useful for debugging this application. These logs will
        be written as DEBUG log entries. For most purposes, this should be
        left `builtins.False`.
    entity_factory : hikari.api.entity_factory.EntityFactory
        The entity factory to use.
    executor : typing.Optional[concurrent.futures.Executor]
        The executor to use for blocking IO. Defaults to the `asyncio` thread
        pool if set to `builtins.None`.
    token : hikari.undefined.UndefinedOr[builtins.str]
        The bot or bearer token. If no token is to be used,
        this can be undefined.
    token_type : hikari.undefined.UndefinedOr[builtins.str]
        The type of token in use. If no token is used, this can be ignored and
        left to the default value. This can be `"Bot"` or `"Bearer"`.
    rest_url : builtins.str
        The HTTP API base URL. This can contain format-string specifiers to
        interpolate information such as API version in use.
    version : builtins.int
        The API version to use. Currently only supports `6` and `7`.

    !!! warning
        The V7 API at the time of writing is considered to be experimental and
        is undocumented. While currently almost identical in most places to the
        V6 API, it should not be used unless you are sure you understand the
        risk that it might break without warning.
    """

    __slots__: typing.Sequence[str] = (
        "buckets",
        "global_rate_limit",
        "version",
        "_client_session",
        "_closed_event",
        "_connector_factory",
        "_connector_owner",
        "_debug",
        "_entity_factory",
        "_executor",
        "_http_settings",
        "_proxy_settings",
        "_rest_url",
        "_token",
    )

    buckets: buckets.RESTBucketManager
    """Bucket ratelimiter manager."""

    global_rate_limit: rate_limits.ManualRateLimiter
    """Global ratelimiter."""

    version: int
    """API version in-use."""

    @attr.s(auto_exc=True, slots=True, repr=False, weakref_slot=False)
    class _RetryRequest(RuntimeError):
        ...

    def __init__(
        self,
        *,
        connector_factory: rest_api.ConnectorFactory,
        connector_owner: bool,
        debug: bool,
        entity_factory: entity_factory_.EntityFactory,
        executor: typing.Optional[concurrent.futures.Executor],
        http_settings: config.HTTPSettings,
        proxy_settings: config.ProxySettings,
        token: typing.Optional[str],
        token_type: typing.Optional[str],
        rest_url: typing.Optional[str],
        version: int,
    ) -> None:
        self.buckets = buckets.RESTBucketManager()
        # We've been told in DAPI that this is per token.
        self.global_rate_limit = rate_limits.ManualRateLimiter()
        self.version = version

        self._client_session: typing.Optional[aiohttp.ClientSession] = None
        self._closed_event = asyncio.Event()
        self._connector_factory = connector_factory
        self._connector_owner = connector_owner
        self._debug = debug
        self._entity_factory = entity_factory
        self._executor = executor
        self._http_settings = http_settings
        self._proxy_settings = proxy_settings

        if token is None:
            full_token = None
        else:
            if token_type is None:
                token_type = constants.BOT_TOKEN

            full_token = f"{token_type.title()} {token}"

        self._token: typing.Optional[str] = full_token

        if rest_url is None:
            rest_url = constants.REST_API_URL

        self._rest_url = rest_url.format(self)

    @property
    def http_settings(self) -> config.HTTPSettings:
        return self._http_settings

    @property
    def proxy_settings(self) -> config.ProxySettings:
        return self._proxy_settings

    @typing.final
    async def close(self) -> None:
        """Close the HTTP client and any open HTTP connections."""
        if self._client_session is not None:
            await self._client_session.close()
        self.global_rate_limit.close()
        self.buckets.close()
        self._closed_event.set()

    async def __aenter__(self) -> RESTClientImpl:
        return self

    async def __aexit__(
        self,
        exc_type: typing.Optional[typing.Type[BaseException]],
        exc_val: typing.Optional[BaseException],
        exc_tb: typing.Optional[types.TracebackType],
    ) -> None:
        await self.close()

    @typing.final
    def _acquire_client_session(self) -> aiohttp.ClientSession:
        if self._client_session is None:
            self._closed_event.clear()
            self._client_session = aiohttp.ClientSession(
                # Should not need a lock, since we don't technically await anything.
                connector=self._connector_factory.acquire(),
                connector_owner=self._connector_owner,
                version=aiohttp.HttpVersion11,
                timeout=aiohttp.ClientTimeout(
                    total=self._http_settings.timeouts.total,
                    connect=self._http_settings.timeouts.acquire_and_connect,
                    sock_read=self._http_settings.timeouts.request_socket_read,
                    sock_connect=self._http_settings.timeouts.request_socket_connect,
                ),
                trust_env=self._proxy_settings.trust_env,
            )

        elif self._client_session.closed:
            raise errors.HTTPClientClosedError

        return self._client_session

    @typing.final
    async def _request(
        self,
        compiled_route: routes.CompiledRoute,
        *,
        query: typing.Optional[data_binding.StringMapBuilder] = None,
        form: typing.Optional[aiohttp.FormData] = None,
        json: typing.Union[data_binding.JSONObjectBuilder, data_binding.JSONArray, None] = None,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        no_auth: bool = False,
    ) -> typing.Union[None, data_binding.JSONObject, data_binding.JSONArray]:
        # Make a ratelimit-protected HTTP request to a JSON endpoint and expect some form
        # of JSON response. If an error occurs, the response body is returned in the
        # raised exception as a bytes object. This is done since the differences between
        # the V6 and V7 API error messages are not documented properly, and there are
        # edge cases such as Cloudflare issues where we may receive arbitrary data in
        # the response instead of a JSON object.

        if not self.buckets.is_started:
            self.buckets.start()

        headers = data_binding.StringMapBuilder()
        headers.setdefault(constants.USER_AGENT_HEADER, constants.HTTP_USER_AGENT)
        headers.put(constants.X_RATELIMIT_PRECISION_HEADER, constants.MILLISECOND_PRECISION)

        if self._token is not None and not no_auth:
            headers[constants.AUTHORIZATION_HEADER] = self._token

        headers.put(constants.X_AUDIT_LOG_REASON_HEADER, reason)

        while True:
            try:
                url = compiled_route.create_url(self._rest_url)

                # Wait for any rate-limits to finish.
                await asyncio.gather(self.buckets.acquire(compiled_route), self.global_rate_limit.acquire())

                uuid = date.uuid()

                if self._debug:
                    headers_str = "\n".join(f"\t\t{name}:{value}" for name, value in headers.items())
                    _LOGGER.debug(
                        "%s %s %s\n\theaders:\n%s\n\tbody:\n\t\t%r",
                        uuid,
                        compiled_route.method,
                        url,
                        headers_str,
                        json,
                    )
                else:
                    _LOGGER.debug("%s %s %s", uuid, compiled_route.method, url)

                # Make the request.
                session = self._acquire_client_session()
                start = date.monotonic()
                response = await session.request(
                    compiled_route.method,
                    url,
                    headers=headers,
                    params=query,
                    json=json,
                    data=form,
                    allow_redirects=self._http_settings.allow_redirects,
                    max_redirects=self._http_settings.max_redirects,
                    proxy=self._proxy_settings.url,
                    proxy_headers=self._proxy_settings.all_headers,
                    verify_ssl=self._http_settings.verify_ssl,
                )
                time_taken = (date.monotonic() - start) * 1_000

                if self._debug:
                    headers_str = "\n".join(
                        f"\t\t{name.decode('utf-8')}:{value.decode('utf-8')}" for name, value in response.raw_headers
                    )
                    _LOGGER.debug(
                        "%s %s %s in %sms\n\theaders:\n%s\n\tbody:\n\t\t%r",
                        uuid,
                        response.status,
                        response.reason,
                        time_taken,
                        headers_str,
                        await response.read(),
                    )
                else:
                    _LOGGER.debug("%s %s %s in %sms", uuid, response.status, response.reason, time_taken)

                # Ensure we aren't rate limited, and update rate limiting headers where appropriate.
                await self._parse_ratelimits(compiled_route, response)

                # Don't bother processing any further if we got NO CONTENT. There's not anything
                # to check.
                if response.status == http.HTTPStatus.NO_CONTENT:
                    return None

                # Handle the response.
                if 200 <= response.status < 300:
                    if response.content_type == constants.APPLICATION_JSON:
                        # Only deserializing here stops Cloudflare shenanigans messing us around.
                        return data_binding.load_json(await response.read())

                    real_url = str(response.real_url)
                    raise errors.HTTPError(f"Expected JSON [{response.content_type=}, {real_url=}]")

                await self._handle_error_response(response)

            except self._RetryRequest:
                continue

    @staticmethod
    @typing.final
    async def _handle_error_response(response: aiohttp.ClientResponse) -> typing.NoReturn:
        raise await net.generate_error_response(response)

    @typing.final
    async def _parse_ratelimits(self, compiled_route: routes.CompiledRoute, response: aiohttp.ClientResponse) -> None:
        # Worth noting there is some bug on V6 that rate limits me immediately if I have an invalid token.
        # https://github.com/discord/discord-api-docs/issues/1569

        # Handle rate limiting.
        resp_headers = response.headers
        limit = int(resp_headers.get(constants.X_RATELIMIT_LIMIT_HEADER, "1"))
        remaining = int(resp_headers.get(constants.X_RATELIMIT_REMAINING_HEADER, "1"))
        bucket = resp_headers.get(constants.X_RATELIMIT_BUCKET_HEADER, "None")
        reset_at = float(resp_headers.get(constants.X_RATELIMIT_RESET_HEADER, "0"))
        reset_after = float(resp_headers.get(constants.X_RATELIMIT_RESET_AFTER_HEADER, "0"))
        reset_date = datetime.datetime.fromtimestamp(reset_at, tz=datetime.timezone.utc)
        now_date = date.rfc7231_datetime_string_to_datetime(resp_headers[constants.DATE_HEADER])

        is_rate_limited = response.status == http.HTTPStatus.TOO_MANY_REQUESTS

        self.buckets.update_rate_limits(
            compiled_route=compiled_route,
            bucket_header=bucket,
            remaining_header=remaining,
            limit_header=limit,
            date_header=now_date,
            reset_at_header=reset_date,
        )

        if not is_rate_limited:
            return

        if response.content_type != constants.APPLICATION_JSON:
            # We don't know exactly what this could imply. It is likely Cloudflare interfering
            # but I'd rather we just give up than do something resulting in multiple failed
            # requests repeatedly.
            raise errors.HTTPResponseError(
                str(response.real_url),
                http.HTTPStatus.TOO_MANY_REQUESTS,
                response.headers,
                await response.read(),
                f"received rate limited response with unexpected response type {response.content_type}",
            )

        body = await response.json()
        body_retry_after = float(body["retry_after"]) / 1_000

        if body.get("global", False) is True:
            self.global_rate_limit.throttle(body_retry_after)

            raise self._RetryRequest

        # Discord have started applying ratelimits to operations on some endpoints
        # based on specific fields used in the JSON body.
        # This does not get reflected in the headers. The first we know is when we
        # get a 429.
        # The issue is that we may get the same response if Discord dynamically
        # adjusts the bucket ratelimits.
        #
        # We have no mechanism for handing field-based ratelimits, so if we get
        # to here, but notice remaining is greater than zero, we should just error.
        #
        # Worth noting we still ignore the retry_after in the body. I have no clue
        # if there is some weird edge case where a bucket rate limit can occur on
        # top of a non-global one, but in this case this check will misbehave and
        # instead of erroring, will trigger a backoff that might be 10 minutes or
        # more...

        # I realise remaining should never be less than zero, but quite frankly, I don't
        # trust that voodoo type stuff will not ever occur with that value from them...
        if remaining <= 0:
            # We can retry and we will then abide by the updated bucket ratelimits.
            _LOGGER.debug(
                "rate-limited on bucket %s at %s. This is a bucket discrepancy, so we will retry at %s",
                bucket,
                compiled_route,
                reset_date,
            )

        # If the values are within 20% of eachother by relativistic tolerance, it is probably
        # safe to retry the request, as they are likely the same value just with some
        # measuring difference. 20% was used as a rounded figure.
        if math.isclose(body_retry_after, reset_after, rel_tol=0.20):
            raise self._RetryRequest

        raise errors.RateLimitedError(
            url=str(response.real_url),
            route=compiled_route,
            headers=response.headers,
            raw_body=body,
            retry_after=body_retry_after,
        )

    @staticmethod
    @typing.final
    def _generate_allowed_mentions(
        mentions_everyone: undefined.UndefinedOr[bool],
        user_mentions: undefined.UndefinedOr[
            typing.Union[typing.Collection[snowflakes.SnowflakeishOr[users.PartialUser]], bool]
        ],
        role_mentions: undefined.UndefinedOr[
            typing.Union[typing.Collection[snowflakes.SnowflakeishOr[guilds.PartialRole]], bool]
        ],
    ) -> data_binding.JSONObject:
        parsed_mentions: typing.List[str] = []
        allowed_mentions = {"parse": parsed_mentions}

        if mentions_everyone is True:
            parsed_mentions.append("everyone")

        if user_mentions is True:
            parsed_mentions.append("users")
        elif isinstance(user_mentions, typing.Collection):
            # Duplicates will cause discord to error.
            snowflakes = {str(int(u)) for u in user_mentions}
            allowed_mentions["users"] = list(snowflakes)

        if role_mentions is True:
            parsed_mentions.append("roles")
        elif isinstance(role_mentions, typing.Collection):
            # Duplicates will cause discord to error.
            snowflakes = {str(int(r)) for r in role_mentions}
            allowed_mentions["roles"] = list(snowflakes)

        return allowed_mentions

    async def fetch_channel(
        self, channel: snowflakes.SnowflakeishOr[channels.PartialChannel]
    ) -> channels.PartialChannel:
        route = routes.GET_CHANNEL.compile(channel=channel)
        raw_response = await self._request(route)
        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._entity_factory.deserialize_channel(response)

    async def edit_channel(
        self,
        channel: snowflakes.SnowflakeishOr[channels.GuildChannel],
        /,
        *,
        name: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        position: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        topic: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        nsfw: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        bitrate: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        user_limit: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        rate_limit_per_user: undefined.UndefinedOr[date.Intervalish] = undefined.UNDEFINED,
        permission_overwrites: undefined.UndefinedOr[
            typing.Sequence[channels.PermissionOverwrite]
        ] = undefined.UNDEFINED,
        parent_category: undefined.UndefinedOr[snowflakes.SnowflakeishOr[channels.GuildCategory]] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> channels.PartialChannel:
        route = routes.PATCH_CHANNEL.compile(channel=channel)
        body = data_binding.JSONObjectBuilder()
        body.put("name", name)
        body.put("position", position)
        body.put("topic", topic)
        body.put("nsfw", nsfw)
        body.put("bitrate", bitrate)
        body.put("user_limit", user_limit)
        body.put("rate_limit_per_user", rate_limit_per_user)
        body.put_snowflake("parent_id", parent_category)
        body.put_array(
            "permission_overwrites",
            permission_overwrites,
            conversion=self._entity_factory.serialize_permission_overwrite,
        )

        raw_response = await self._request(route, json=body, reason=reason)
        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._entity_factory.deserialize_channel(response)

    async def delete_channel(self, channel: snowflakes.SnowflakeishOr[channels.PartialChannel]) -> None:
        route = routes.DELETE_CHANNEL.compile(channel=channel)
        await self._request(route)

    async def edit_permission_overwrites(
        self,
        channel: snowflakes.SnowflakeishOr[channels.GuildChannel],
        target: typing.Union[
            snowflakes.Snowflakeish, users.PartialUser, guilds.PartialRole, channels.PermissionOverwrite
        ],
        *,
        target_type: undefined.UndefinedOr[typing.Union[channels.PermissionOverwriteType, str]] = undefined.UNDEFINED,
        allow: undefined.UndefinedOr[permissions_.Permissions] = undefined.UNDEFINED,
        deny: undefined.UndefinedOr[permissions_.Permissions] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        if target_type is undefined.UNDEFINED:
            if isinstance(target, users.PartialUser):
                target_type = channels.PermissionOverwriteType.MEMBER
            elif isinstance(target, guilds.Role):
                target_type = channels.PermissionOverwriteType.ROLE
            elif isinstance(target, channels.PermissionOverwrite):
                target_type = target.type
            else:
                raise TypeError(
                    "Cannot determine the type of the target to update. Try specifying 'target_type' manually."
                )

        route = routes.PATCH_CHANNEL_PERMISSIONS.compile(channel=channel, overwrite=target)
        body = data_binding.JSONObjectBuilder()
        body.put("type", target_type)
        body.put("allow", allow)
        body.put("deny", deny)

        await self._request(route, json=body, reason=reason)

    async def delete_permission_overwrite(
        self,
        channel: snowflakes.SnowflakeishOr[channels.GuildChannel],
        target: snowflakes.SnowflakeishOr[
            typing.Union[channels.PermissionOverwrite, guilds.PartialRole, users.PartialUser, snowflakes.Snowflakeish]
        ],
    ) -> None:
        route = routes.DELETE_CHANNEL_PERMISSIONS.compile(channel=channel, overwrite=target)
        await self._request(route)

    async def fetch_channel_invites(
        self, channel: snowflakes.SnowflakeishOr[channels.GuildChannel]
    ) -> typing.Sequence[invites.InviteWithMetadata]:
        route = routes.GET_CHANNEL_INVITES.compile(channel=channel)
        raw_response = await self._request(route)
        response = typing.cast(data_binding.JSONArray, raw_response)
        return data_binding.cast_json_array(response, self._entity_factory.deserialize_invite_with_metadata)

    async def create_invite(
        self,
        channel: snowflakes.SnowflakeishOr[channels.GuildChannel],
        *,
        max_age: undefined.UndefinedOr[date.Intervalish] = undefined.UNDEFINED,
        max_uses: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        temporary: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        unique: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        target_user: undefined.UndefinedOr[snowflakes.SnowflakeishOr[users.PartialUser]] = undefined.UNDEFINED,
        target_user_type: undefined.UndefinedOr[invites.TargetUserType] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> invites.InviteWithMetadata:
        route = routes.POST_CHANNEL_INVITES.compile(channel=channel)
        body = data_binding.JSONObjectBuilder()
        body.put("max_age", max_age, conversion=date.timespan_to_int)
        body.put("max_uses", max_uses)
        body.put("temporary", temporary)
        body.put("unique", unique)
        body.put_snowflake("target_user_id", target_user)
        body.put("target_user_type", target_user_type)
        raw_response = await self._request(route, json=body, reason=reason)
        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._entity_factory.deserialize_invite_with_metadata(response)

    def trigger_typing(
        self, channel: snowflakes.SnowflakeishOr[channels.TextChannel]
    ) -> special_endpoints.TypingIndicator:
        return special_endpoints.TypingIndicator(
            request_call=self._request, channel=channel, rest_closed_event=self._closed_event
        )

    async def fetch_pins(
        self, channel: snowflakes.SnowflakeishOr[channels.TextChannel]
    ) -> typing.Sequence[messages_.Message]:
        route = routes.GET_CHANNEL_PINS.compile(channel=channel)
        raw_response = await self._request(route)
        response = typing.cast(data_binding.JSONArray, raw_response)
        return data_binding.cast_json_array(response, self._entity_factory.deserialize_message)

    async def pin_message(
        self,
        channel: snowflakes.SnowflakeishOr[channels.TextChannel],
        message: snowflakes.SnowflakeishOr[messages_.Message],
    ) -> None:
        route = routes.PUT_CHANNEL_PINS.compile(channel=channel, message=message)
        await self._request(route)

    async def unpin_message(
        self,
        channel: snowflakes.SnowflakeishOr[channels.TextChannel],
        message: snowflakes.SnowflakeishOr[messages_.Message],
    ) -> None:
        route = routes.DELETE_CHANNEL_PIN.compile(channel=channel, message=message)
        await self._request(route)

    def fetch_messages(
        self,
        channel: snowflakes.SnowflakeishOr[channels.TextChannel],
        *,
        before: undefined.UndefinedOr[snowflakes.SearchableSnowflakeishOr[snowflakes.Unique]] = undefined.UNDEFINED,
        after: undefined.UndefinedOr[snowflakes.SearchableSnowflakeishOr[snowflakes.Unique]] = undefined.UNDEFINED,
        around: undefined.UndefinedOr[snowflakes.SearchableSnowflakeishOr[snowflakes.Unique]] = undefined.UNDEFINED,
    ) -> iterators.LazyIterator[messages_.Message]:
        if undefined.count(before, after, around) < 2:
            raise TypeError("Expected no kwargs, or maximum of one of 'before', 'after', 'around'")

        timestamp: undefined.UndefinedOr[str]

        if before is not undefined.UNDEFINED:
            direction = "before"
            if isinstance(before, datetime.datetime):
                timestamp = str(snowflakes.Snowflake.from_datetime(before))
            else:
                timestamp = str(int(before))
        elif after is not undefined.UNDEFINED:
            direction = "after"
            if isinstance(after, datetime.datetime):
                timestamp = str(snowflakes.Snowflake.from_datetime(after))
            else:
                timestamp = str(int(after))
        elif around is not undefined.UNDEFINED:
            direction = "around"
            if isinstance(around, datetime.datetime):
                timestamp = str(snowflakes.Snowflake.from_datetime(around))
            else:
                timestamp = str(int(around))
        else:
            direction = "before"
            timestamp = undefined.UNDEFINED

        return special_endpoints.MessageIterator(
            entity_factory=self._entity_factory,
            request_call=self._request,
            channel=channel,
            direction=direction,
            first_id=timestamp,
        )

    async def fetch_message(
        self,
        channel: snowflakes.SnowflakeishOr[channels.TextChannel],
        message: snowflakes.SnowflakeishOr[messages_.Message],
    ) -> messages_.Message:
        route = routes.GET_CHANNEL_MESSAGE.compile(channel=channel, message=message)
        raw_response = await self._request(route)
        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._entity_factory.deserialize_message(response)

    async def create_message(
        self,
        channel: snowflakes.SnowflakeishOr[channels.TextChannel],
        content: undefined.UndefinedOr[typing.Any] = undefined.UNDEFINED,
        *,
        embed: undefined.UndefinedOr[embeds_.Embed] = undefined.UNDEFINED,
        attachment: undefined.UndefinedOr[files.Resourceish] = undefined.UNDEFINED,
        attachments: undefined.UndefinedOr[typing.Sequence[files.Resourceish]] = undefined.UNDEFINED,
        tts: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        nonce: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        mentions_everyone: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        user_mentions: undefined.UndefinedOr[
            typing.Union[typing.Collection[snowflakes.SnowflakeishOr[users.PartialUser]], bool]
        ] = undefined.UNDEFINED,
        role_mentions: undefined.UndefinedOr[
            typing.Union[typing.Collection[snowflakes.SnowflakeishOr[guilds.PartialRole]], bool]
        ] = undefined.UNDEFINED,
    ) -> messages_.Message:
        if not undefined.count(attachment, attachments):
            raise ValueError("You may only specify one of 'attachment' or 'attachments', not both")

        if not isinstance(attachments, typing.Collection) and attachments is not undefined.UNDEFINED:
            raise ValueError(
                "You passed a non-collection to 'attachments', but this expects a collection. Maybe you meant to "
                "use 'attachment' (singular) instead?"
            )

        route = routes.POST_CHANNEL_MESSAGES.compile(channel=channel)

        if embed is undefined.UNDEFINED and isinstance(content, embeds_.Embed):
            # Syntatic sugar, common mistake to accidentally send an embed
            # as the content, so lets detect this and fix it for the user.
            embed = content
            content = undefined.UNDEFINED

        elif undefined.count(attachment, attachments) == 2 and isinstance(
            content, (files.Resource, files.RAWISH_TYPES, os.PathLike)
        ):
            # Syntatic sugar, common mistake to accidentally send an attachment
            # as the content, so lets detect this and fix it for the user. This
            # will still then work with normal implicit embed attachments as
            # we work this out later.
            attachment = content
            content = undefined.UNDEFINED

        body = data_binding.JSONObjectBuilder()
        body.put("allowed_mentions", self._generate_allowed_mentions(mentions_everyone, user_mentions, role_mentions))
        body.put("content", content, conversion=str)
        body.put("nonce", nonce)
        body.put("tts", tts)

        final_attachments: typing.List[files.Resource[files.AsyncReader]] = []

        if attachment is not undefined.UNDEFINED:
            final_attachments.append(files.ensure_resource(attachment))
        if attachments is not undefined.UNDEFINED:
            final_attachments.extend([files.ensure_resource(a) for a in attachments])

        if embed is not undefined.UNDEFINED:
            embed_payload, embed_attachments = self._entity_factory.serialize_embed(embed)
            body.put("embed", embed_payload)
            final_attachments.extend(embed_attachments)

        if final_attachments:
            form = data_binding.URLEncodedForm()
            form.add_field("payload_json", data_binding.dump_json(body), content_type=constants.APPLICATION_JSON)

            stack = contextlib.AsyncExitStack()

            try:
                for i, attachment in enumerate(final_attachments):
                    stream = await stack.enter_async_context(attachment.stream(executor=self._executor))
                    form.add_field(
                        f"file{i}", stream, filename=stream.filename, content_type=constants.APPLICATION_OCTET_STREAM
                    )

                raw_response = await self._request(route, form=form)
            finally:
                await stack.aclose()
        else:
            raw_response = await self._request(route, json=body)

        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._entity_factory.deserialize_message(response)

    async def edit_message(
        self,
        channel: typing.Union[snowflakes.SnowflakeishOr[channels.TextChannel]],
        message: typing.Union[snowflakes.SnowflakeishOr[messages_.Message]],
        content: undefined.UndefinedOr[typing.Any] = undefined.UNDEFINED,
        *,
        embed: undefined.UndefinedNoneOr[embeds_.Embed] = undefined.UNDEFINED,
        mentions_everyone: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        user_mentions: undefined.UndefinedOr[
            typing.Union[typing.Collection[snowflakes.SnowflakeishOr[users.PartialUser]], bool]
        ] = undefined.UNDEFINED,
        role_mentions: undefined.UndefinedOr[
            typing.Union[typing.Collection[snowflakes.SnowflakeishOr[guilds.PartialRole]], bool]
        ] = undefined.UNDEFINED,
        flags: undefined.UndefinedOr[messages_.MessageFlag] = undefined.UNDEFINED,
    ) -> messages_.Message:
        route = routes.PATCH_CHANNEL_MESSAGE.compile(channel=channel, message=message)
        body = data_binding.JSONObjectBuilder()
        body.put("flags", flags)
        if undefined.count(mentions_everyone, user_mentions, role_mentions) != 3:
            body.put(
                "allowed_mentions", self._generate_allowed_mentions(mentions_everyone, user_mentions, role_mentions)
            )

        if embed is undefined.UNDEFINED and isinstance(content, embeds_.Embed):
            # Syntatic sugar, common mistake to accidentally send an embed
            # as the content, so lets detect this and fix it for the user.
            embed = content
            content = undefined.UNDEFINED

        if content is not None:
            body.put("content", content, conversion=str)
        else:
            body.put("content", None)

        if isinstance(embed, embeds_.Embed):
            embed_payload, _ = self._entity_factory.serialize_embed(embed)
            body.put("embed", embed_payload)
        elif embed is None:
            body.put("embed", None)

        raw_response = await self._request(route, json=body)
        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._entity_factory.deserialize_message(response)

    async def delete_message(
        self,
        channel: snowflakes.SnowflakeishOr[channels.TextChannel],
        message: snowflakes.SnowflakeishOr[messages_.Message],
    ) -> None:
        route = routes.DELETE_CHANNEL_MESSAGE.compile(channel=channel, message=message)
        await self._request(route)

    async def delete_messages(
        self,
        channel: snowflakes.SnowflakeishOr[channels.TextChannel],
        /,
        *messages: snowflakes.SnowflakeishOr[messages_.Message],
    ) -> None:
        route = routes.POST_DELETE_CHANNEL_MESSAGES_BULK.compile(channel=channel)

        pending: typing.Deque[snowflakes.SnowflakeishOr[messages_.Message]] = collections.deque(messages)
        deleted: typing.Deque[snowflakes.SnowflakeishOr[messages_.Message]] = collections.deque()

        while pending:
            # Discord only allows 2-100 messages in the BULK_DELETE endpoint. Because of that,
            # if the user wants 101 messages deleted, we will post 100 messages in bulk delete
            # and then the last message in a normal delete.
            # Along with this, the bucket size for v6 and v7 seems to be a bit restrictive. As of
            # 30th July 2020, this endpoint returned the following headers when being ratelimited:
            #       x-ratelimit-bucket         b05c0d8c2ab83895085006a8eae073a3
            #       x-ratelimit-limit          1
            #       x-ratelimit-remaining      0
            #       x-ratelimit-reset          1596033974.096
            #       x-ratelimit-reset-after    3.000
            # This kind of defeats the point of asynchronously gathering any of these
            # in the first place really. To save clogging up the event loop
            # (albeit at a cost of maybe a couple-dozen milliseconds per call),
            # I am just gonna invoke these sequentially instead.
            try:
                if len(pending) == 1:
                    message = pending.popleft()
                    await self.delete_message(channel, message)
                    deleted.append(message)
                else:
                    body = data_binding.JSONObjectBuilder()
                    chunk = [pending.popleft() for _ in range(min(100, len(pending)))]
                    body.put_snowflake_array("messages", chunk)
                    await self._request(route, json=body)
                    deleted += chunk
            except Exception as ex:
                raise errors.BulkDeleteError(deleted, pending) from ex

    # Custom emoji mentions are in the format of <:name:id> for static emoji, or
    # <a:name:id> for animated emoji.
    _CUSTOM_EMOJI_PATTERN: typing.Final[typing.ClassVar[re.Pattern[str]]] = re.compile(r"<a?:([^:]+:\d+)>")

    def _transform_emoji_to_url_format(self, emoji: emojis.Emojiish) -> str:
        # Given an emojiish, check if it is a valid custom emoji mention. If it
        # is, then convert it to the name:id format (remove the wrapping
        # characters), then return it. If the emoji is an emojis.CustomEmoji
        # directly, then get the url_name of it. All other emojis and objects
        # can just be cast to string, as they are probably unicode emoji objects
        # or unicode emoji strings.
        if isinstance(emoji, emojis.CustomEmoji):
            return emoji.url_name

        if isinstance(emoji, str) and (custom_mention_match := self._CUSTOM_EMOJI_PATTERN.match(emoji)) is not None:
            # False positive in PyCharm, yet again.
            # noinspection PyUnboundLocalVariable
            return custom_mention_match.group(1)

        return str(emoji)

    async def add_reaction(
        self,
        channel: snowflakes.SnowflakeishOr[channels.TextChannel],
        message: snowflakes.SnowflakeishOr[messages_.Message],
        emoji: emojis.Emojiish,
    ) -> None:
        route = routes.PUT_MY_REACTION.compile(
            emoji=self._transform_emoji_to_url_format(emoji), channel=channel, message=message,
        )
        await self._request(route)

    async def delete_my_reaction(
        self,
        channel: snowflakes.SnowflakeishOr[channels.TextChannel],
        message: snowflakes.SnowflakeishOr[messages_.Message],
        emoji: emojis.Emojiish,
    ) -> None:
        route = routes.DELETE_MY_REACTION.compile(
            emoji=self._transform_emoji_to_url_format(emoji), channel=channel, message=message,
        )
        await self._request(route)

    async def delete_all_reactions_for_emoji(
        self,
        channel: snowflakes.SnowflakeishOr[channels.TextChannel],
        message: snowflakes.SnowflakeishOr[messages_.Message],
        emoji: emojis.Emojiish,
    ) -> None:
        route = routes.DELETE_REACTION_EMOJI.compile(
            emoji=self._transform_emoji_to_url_format(emoji), channel=channel, message=message,
        )
        await self._request(route)

    async def delete_reaction(
        self,
        channel: snowflakes.SnowflakeishOr[channels.TextChannel],
        message: snowflakes.SnowflakeishOr[messages_.Message],
        emoji: emojis.Emojiish,
        user: snowflakes.SnowflakeishOr[users.PartialUser],
    ) -> None:
        route = routes.DELETE_REACTION_USER.compile(
            emoji=self._transform_emoji_to_url_format(emoji), channel=channel, message=message, user=user,
        )
        await self._request(route)

    async def delete_all_reactions(
        self,
        channel: snowflakes.SnowflakeishOr[channels.TextChannel],
        message: snowflakes.SnowflakeishOr[messages_.Message],
    ) -> None:
        route = routes.DELETE_ALL_REACTIONS.compile(channel=channel, message=message)
        await self._request(route)

    def fetch_reactions_for_emoji(
        self,
        channel: snowflakes.SnowflakeishOr[channels.TextChannel],
        message: snowflakes.SnowflakeishOr[messages_.Message],
        emoji: emojis.Emojiish,
    ) -> iterators.LazyIterator[users.User]:
        return special_endpoints.ReactorIterator(
            entity_factory=self._entity_factory,
            request_call=self._request,
            channel=channel,
            message=message,
            emoji=self._transform_emoji_to_url_format(emoji),
        )

    async def create_webhook(
        self,
        channel: snowflakes.SnowflakeishOr[channels.TextChannel],
        name: str,
        *,
        avatar: typing.Optional[files.Resourceish] = None,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> webhooks.Webhook:
        route = routes.POST_CHANNEL_WEBHOOKS.compile(channel=channel)
        body = data_binding.JSONObjectBuilder()
        body.put("name", name)

        if avatar is not None:
            avatar_resource = files.ensure_resource(avatar)
            async with avatar_resource.stream(executor=self._executor) as stream:
                body.put("avatar", await stream.data_uri())

        raw_response = await self._request(route, json=body, reason=reason)
        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._entity_factory.deserialize_webhook(response)

    async def fetch_webhook(
        self,
        webhook: snowflakes.SnowflakeishOr[webhooks.Webhook],
        *,
        token: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> webhooks.Webhook:
        if token is undefined.UNDEFINED:
            route = routes.GET_WEBHOOK.compile(webhook=webhook)
            no_auth = False
        else:
            route = routes.GET_WEBHOOK_WITH_TOKEN.compile(webhook=webhook, token=token)
            no_auth = True

        raw_response = await self._request(route, no_auth=no_auth)
        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._entity_factory.deserialize_webhook(response)

    async def fetch_channel_webhooks(
        self, channel: snowflakes.SnowflakeishOr[channels.TextChannel],
    ) -> typing.Sequence[webhooks.Webhook]:
        route = routes.GET_CHANNEL_WEBHOOKS.compile(channel=channel)
        raw_response = await self._request(route)
        response = typing.cast(data_binding.JSONArray, raw_response)
        return data_binding.cast_json_array(response, self._entity_factory.deserialize_webhook)

    async def fetch_guild_webhooks(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
    ) -> typing.Sequence[webhooks.Webhook]:
        route = routes.GET_GUILD_WEBHOOKS.compile(guild=guild)
        raw_response = await self._request(route)
        response = typing.cast(data_binding.JSONArray, raw_response)
        return data_binding.cast_json_array(response, self._entity_factory.deserialize_webhook)

    async def edit_webhook(
        self,
        webhook: snowflakes.SnowflakeishOr[webhooks.Webhook],
        *,
        token: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        name: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        avatar: undefined.UndefinedNoneOr[files.Resourceish] = undefined.UNDEFINED,
        channel: undefined.UndefinedOr[snowflakes.SnowflakeishOr[channels.TextChannel]] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> webhooks.Webhook:
        if token is undefined.UNDEFINED:
            route = routes.PATCH_WEBHOOK.compile(webhook=webhook)
            no_auth = False
        else:
            route = routes.PATCH_WEBHOOK_WITH_TOKEN.compile(webhook=webhook, token=token)
            no_auth = True

        body = data_binding.JSONObjectBuilder()
        body.put("name", name)
        body.put_snowflake("channel", channel)

        if avatar is None:
            body.put("avatar", None)
        elif avatar is not undefined.UNDEFINED:
            avatar_resource = files.ensure_resource(avatar)
            async with avatar_resource.stream(executor=self._executor) as stream:
                body.put("avatar", await stream.data_uri())

        raw_response = await self._request(route, json=body, reason=reason, no_auth=no_auth)
        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._entity_factory.deserialize_webhook(response)

    async def delete_webhook(
        self,
        webhook: snowflakes.SnowflakeishOr[webhooks.Webhook],
        *,
        token: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        if token is undefined.UNDEFINED:
            route = routes.DELETE_WEBHOOK.compile(webhook=webhook)
            no_auth = False
        else:
            route = routes.DELETE_WEBHOOK_WITH_TOKEN.compile(webhook=webhook, token=token)
            no_auth = True

        await self._request(route, no_auth=no_auth)

    async def execute_webhook(
        self,
        webhook: snowflakes.SnowflakeishOr[webhooks.Webhook],
        token: str,
        content: undefined.UndefinedOr[typing.Any] = undefined.UNDEFINED,
        *,
        username: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        avatar_url: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        embed: undefined.UndefinedOr[embeds_.Embed] = undefined.UNDEFINED,
        embeds: undefined.UndefinedOr[typing.Sequence[embeds_.Embed]] = undefined.UNDEFINED,
        attachment: undefined.UndefinedOr[files.Resourceish] = undefined.UNDEFINED,
        attachments: undefined.UndefinedOr[typing.Sequence[files.Resourceish]] = undefined.UNDEFINED,
        tts: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        mentions_everyone: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        user_mentions: undefined.UndefinedOr[
            typing.Union[typing.Collection[snowflakes.SnowflakeishOr[users.PartialUser]], bool]
        ] = undefined.UNDEFINED,
        role_mentions: undefined.UndefinedOr[
            typing.Union[typing.Collection[snowflakes.SnowflakeishOr[guilds.PartialRole]], bool]
        ] = undefined.UNDEFINED,
    ) -> messages_.Message:
        if not undefined.count(attachment, attachments):
            raise ValueError("You may only specify one of 'attachment' or 'attachments', not both")

        if not undefined.count(embed, embeds):
            raise ValueError("You may only specify one of 'embed' or 'embeds', not both")

        if not isinstance(embeds, typing.Collection) and embeds is not undefined.UNDEFINED:
            raise TypeError(
                "You passed a non collection to 'embeds', but this expects a collection. Maybe you meant to "
                "use 'embed' (singular) instead?"
            )

        if not isinstance(attachments, typing.Collection) and attachments is not undefined.UNDEFINED:
            raise TypeError(
                "You passed a non collection to 'attachments', but this expects a collection. Maybe you meant to "
                "use 'attachment' (singular) instead?"
            )

        if undefined.count(embed, embeds) == 2 and isinstance(content, embeds_.Embed):
            # Syntatic sugar, common mistake to accidentally send an embed
            # as the content, so lets detect this and fix it for the user.
            embed = content
            content = undefined.UNDEFINED

        elif undefined.count(attachment, attachments) == 2 and isinstance(
            content, (files.Resource, files.RAWISH_TYPES, os.PathLike)
        ):
            # Syntatic sugar, common mistake to accidentally send an attachment
            # as the content, so lets detect this and fix it for the user. This
            # will still then work with normal implicit embed attachments as
            # we work this out later.
            attachment = content
            content = undefined.UNDEFINED

        route = routes.POST_WEBHOOK_WITH_TOKEN.compile(webhook=webhook, token=token)

        final_attachments: typing.List[files.Resource[files.AsyncReader]] = []
        if attachment is not undefined.UNDEFINED:
            final_attachments.append(files.ensure_resource(attachment))
        if attachments is not undefined.UNDEFINED:
            final_attachments.extend([files.ensure_resource(a) for a in attachments])

        serialized_embeds: data_binding.JSONArray = []

        if embeds is not undefined.UNDEFINED:
            for embed in embeds:
                embed_payload, embed_attachments = self._entity_factory.serialize_embed(embed)
                serialized_embeds.append(embed_payload)
                final_attachments.extend(embed_attachments)

        body = data_binding.JSONObjectBuilder()
        body.put("mentions", self._generate_allowed_mentions(mentions_everyone, user_mentions, role_mentions))
        body.put("content", content, conversion=str)
        body.put("embeds", serialized_embeds)
        body.put("username", username)
        body.put("avatar_url", avatar_url)
        body.put("tts", tts)
        query = data_binding.StringMapBuilder()
        query.put("wait", True)

        if final_attachments:
            form = data_binding.URLEncodedForm()
            form.add_field("payload_json", data_binding.dump_json(body), content_type=constants.APPLICATION_JSON)

            stack = contextlib.AsyncExitStack()

            try:
                for i, attachment in enumerate(final_attachments):
                    stream = await stack.enter_async_context(attachment.stream(executor=self._executor))
                    form.add_field(
                        f"file{i}", stream, filename=stream.filename, content_type=constants.APPLICATION_OCTET_STREAM
                    )

                raw_response = await self._request(route, query=query, form=form, no_auth=True)
            finally:
                await stack.aclose()
        else:
            raw_response = await self._request(route, query=query, json=body, no_auth=True)

        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._entity_factory.deserialize_message(response)

    async def fetch_gateway_url(self) -> str:
        route = routes.GET_GATEWAY.compile()
        # This doesn't need authorization.
        raw_response = await self._request(route, no_auth=True)
        response = typing.cast("typing.Mapping[str, str]", raw_response)
        return response["url"]

    async def fetch_gateway_bot(self) -> sessions.GatewayBot:
        route = routes.GET_GATEWAY_BOT.compile()
        raw_response = await self._request(route)
        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._entity_factory.deserialize_gateway_bot(response)

    async def fetch_invite(self, invite: invites.Inviteish) -> invites.Invite:
        route = routes.GET_INVITE.compile(invite_code=invite if isinstance(invite, str) else invite.code)
        query = data_binding.StringMapBuilder()
        query.put("with_counts", True)
        raw_response = await self._request(route, query=query)
        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._entity_factory.deserialize_invite(response)

    async def delete_invite(self, invite: invites.Inviteish) -> None:
        route = routes.DELETE_INVITE.compile(invite_code=invite if isinstance(invite, str) else invite.code)
        await self._request(route)

    async def fetch_my_user(self) -> users.OwnUser:
        route = routes.GET_MY_USER.compile()
        raw_response = await self._request(route)
        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._entity_factory.deserialize_my_user(response)

    async def edit_my_user(
        self,
        *,
        username: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        avatar: undefined.UndefinedNoneOr[files.Resourceish] = undefined.UNDEFINED,
    ) -> users.OwnUser:
        route = routes.PATCH_MY_USER.compile()
        body = data_binding.JSONObjectBuilder()
        body.put("username", username)

        if avatar is None:
            body.put("avatar", None)
        elif avatar is not undefined.UNDEFINED:
            avatar_resource = files.ensure_resource(avatar)
            async with avatar_resource.stream(executor=self._executor) as stream:
                body.put("avatar", await stream.data_uri())

        raw_response = await self._request(route, json=body)
        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._entity_factory.deserialize_my_user(response)

    async def fetch_my_connections(self) -> typing.Sequence[applications.OwnConnection]:
        route = routes.GET_MY_CONNECTIONS.compile()
        raw_response = await self._request(route)
        response = typing.cast(data_binding.JSONArray, raw_response)
        return data_binding.cast_json_array(response, self._entity_factory.deserialize_own_connection)

    def fetch_my_guilds(
        self,
        *,
        newest_first: bool = False,
        start_at: undefined.UndefinedOr[snowflakes.SearchableSnowflakeishOr[guilds.PartialGuild]] = undefined.UNDEFINED,
    ) -> iterators.LazyIterator[applications.OwnGuild]:
        if start_at is undefined.UNDEFINED:
            start_at = snowflakes.Snowflake.max() if newest_first else snowflakes.Snowflake.min()
        elif isinstance(start_at, datetime.datetime):
            start_at = snowflakes.Snowflake.from_datetime(start_at)
        else:
            start_at = int(start_at)

        return special_endpoints.OwnGuildIterator(
            entity_factory=self._entity_factory,
            request_call=self._request,
            newest_first=newest_first,
            first_id=str(start_at),
        )

    async def leave_guild(self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], /) -> None:
        route = routes.DELETE_MY_GUILD.compile(guild=guild)
        await self._request(route)

    async def create_dm_channel(
        self, user: snowflakes.SnowflakeishOr[users.PartialUser], /
    ) -> channels.PrivateTextChannel:
        route = routes.POST_MY_CHANNELS.compile()
        body = data_binding.JSONObjectBuilder()
        body.put_snowflake("recipient_id", user)
        raw_response = await self._request(route, json=body)
        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._entity_factory.deserialize_private_text_channel(response)

    async def fetch_application(self) -> applications.Application:
        route = routes.GET_MY_APPLICATION.compile()
        raw_response = await self._request(route)
        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._entity_factory.deserialize_application(response)

    async def add_user_to_guild(
        self,
        access_token: str,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        *,
        nick: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        roles: undefined.UndefinedOr[
            typing.Collection[snowflakes.SnowflakeishOr[guilds.PartialRole]]
        ] = undefined.UNDEFINED,
        mute: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        deaf: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
    ) -> typing.Optional[guilds.Member]:
        route = routes.PUT_GUILD_MEMBER.compile(guild=guild, user=user)
        body = data_binding.JSONObjectBuilder()
        body.put("access_token", access_token)
        body.put("nick", nick)
        body.put("mute", mute)
        body.put("deaf", deaf)
        body.put_snowflake_array("roles", roles)

        if (raw_response := await self._request(route, json=body)) is not None:
            response = typing.cast(data_binding.JSONObject, raw_response)
            return self._entity_factory.deserialize_member(response, guild_id=snowflakes.Snowflake(guild))
        else:
            # User already is in the guild.
            return None

    async def fetch_voice_regions(self) -> typing.Sequence[voices.VoiceRegion]:
        route = routes.GET_VOICE_REGIONS.compile()
        raw_response = await self._request(route)
        response = typing.cast(data_binding.JSONArray, raw_response)
        return data_binding.cast_json_array(response, self._entity_factory.deserialize_voice_region)

    async def fetch_user(self, user: snowflakes.SnowflakeishOr[users.PartialUser]) -> users.User:
        route = routes.GET_USER.compile(user=user)
        raw_response = await self._request(route)
        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._entity_factory.deserialize_user(response)

    def fetch_audit_log(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        *,
        before: undefined.UndefinedOr[snowflakes.SearchableSnowflakeishOr[snowflakes.Unique]] = undefined.UNDEFINED,
        user: undefined.UndefinedOr[snowflakes.SnowflakeishOr[users.PartialUser]] = undefined.UNDEFINED,
        event_type: undefined.UndefinedOr[audit_logs.AuditLogEventType] = undefined.UNDEFINED,
    ) -> iterators.LazyIterator[audit_logs.AuditLog]:

        timestamp: undefined.UndefinedOr[str]
        if before is undefined.UNDEFINED:
            timestamp = undefined.UNDEFINED
        elif isinstance(before, datetime.datetime):
            timestamp = str(snowflakes.Snowflake.from_datetime(before))
        else:
            timestamp = str(int(before))

        return special_endpoints.AuditLogIterator(
            entity_factory=self._entity_factory,
            request_call=self._request,
            guild=guild,
            before=timestamp,
            user=user,
            action_type=event_type,
        )

    async def fetch_emoji(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        # This is an emoji ID, which is the URL-safe emoji name, not the snowflake alone.
        # likewise this only is valid for custom emojis, unicode emojis make little sense here.
        emoji: typing.Union[str, emojis.CustomEmoji],
    ) -> emojis.KnownCustomEmoji:
        route = routes.GET_GUILD_EMOJI.compile(guild=guild, emoji=self._transform_emoji_to_url_format(emoji))
        raw_response = await self._request(route)
        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._entity_factory.deserialize_known_custom_emoji(response, guild_id=snowflakes.Snowflake(guild))

    async def fetch_guild_emojis(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild]
    ) -> typing.Sequence[emojis.KnownCustomEmoji]:
        route = routes.GET_GUILD_EMOJIS.compile(guild=guild)
        raw_response = await self._request(route)
        response = typing.cast(data_binding.JSONArray, raw_response)
        return data_binding.cast_json_array(
            response, self._entity_factory.deserialize_known_custom_emoji, guild_id=snowflakes.Snowflake(guild)
        )

    async def create_emoji(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        name: str,
        image: files.Resourceish,
        *,
        roles: undefined.UndefinedOr[
            typing.Collection[snowflakes.SnowflakeishOr[guilds.PartialRole]]
        ] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> emojis.KnownCustomEmoji:
        route = routes.POST_GUILD_EMOJIS.compile(guild=guild)
        body = data_binding.JSONObjectBuilder()
        body.put("name", name)
        image_resource = files.ensure_resource(image)
        async with image_resource.stream(executor=self._executor) as stream:
            body.put("image", await stream.data_uri())

        body.put_snowflake_array("roles", roles)

        raw_response = await self._request(route, json=body, reason=reason)
        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._entity_factory.deserialize_known_custom_emoji(response, guild_id=snowflakes.Snowflake(guild))

    async def edit_emoji(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        # This is an emoji ID, which is the URL-safe emoji name, not the snowflake alone.
        # likewise this only is valid for custom emojis, unicode emojis make little sense here.
        emoji: typing.Union[str, emojis.CustomEmoji],
        *,
        name: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        roles: undefined.UndefinedOr[
            typing.Collection[snowflakes.SnowflakeishOr[guilds.PartialRole]]
        ] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> emojis.KnownCustomEmoji:
        route = routes.PATCH_GUILD_EMOJI.compile(guild=guild, emoji=self._transform_emoji_to_url_format(emoji))
        body = data_binding.JSONObjectBuilder()
        body.put("name", name)
        body.put_snowflake_array("roles", roles)

        raw_response = await self._request(route, json=body, reason=reason)
        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._entity_factory.deserialize_known_custom_emoji(response, guild_id=snowflakes.Snowflake(guild))

    async def delete_emoji(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        # This is an emoji ID, which is the URL-safe emoji name, not the snowflake alone.
        # likewise this only is valid for custom emojis, unicode emojis make little sense here.
        emoji: typing.Union[str, emojis.CustomEmoji],
    ) -> None:
        route = routes.DELETE_GUILD_EMOJI.compile(guild=guild, emoji=self._transform_emoji_to_url_format(emoji))
        await self._request(route)

    def guild_builder(self, name: str, /) -> special_endpoints.GuildBuilder:
        return special_endpoints.GuildBuilder(
            entity_factory=self._entity_factory, executor=self._executor, request_call=self._request, name=name
        )

    async def fetch_guild(self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild]) -> guilds.RESTGuild:
        route = routes.GET_GUILD.compile(guild=guild)
        query = data_binding.StringMapBuilder()
        query.put("with_counts", True)
        raw_response = await self._request(route, query=query)
        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._entity_factory.deserialize_rest_guild(response)

    async def fetch_guild_preview(self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild]) -> guilds.GuildPreview:
        route = routes.GET_GUILD_PREVIEW.compile(guild=guild)
        raw_response = await self._request(route)
        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._entity_factory.deserialize_guild_preview(response)

    async def edit_guild(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        *,
        name: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        region: undefined.UndefinedOr[voices.VoiceRegionish] = undefined.UNDEFINED,
        verification_level: undefined.UndefinedOr[guilds.GuildVerificationLevel] = undefined.UNDEFINED,
        default_message_notifications: undefined.UndefinedOr[
            guilds.GuildMessageNotificationsLevel
        ] = undefined.UNDEFINED,
        explicit_content_filter_level: undefined.UndefinedOr[
            guilds.GuildExplicitContentFilterLevel
        ] = undefined.UNDEFINED,
        afk_channel: undefined.UndefinedOr[snowflakes.SnowflakeishOr[channels.GuildVoiceChannel]] = undefined.UNDEFINED,
        afk_timeout: undefined.UndefinedOr[date.Intervalish] = undefined.UNDEFINED,
        icon: undefined.UndefinedNoneOr[files.Resourceish] = undefined.UNDEFINED,
        owner: undefined.UndefinedOr[snowflakes.SnowflakeishOr[users.PartialUser]] = undefined.UNDEFINED,
        splash: undefined.UndefinedNoneOr[files.Resourceish] = undefined.UNDEFINED,
        banner: undefined.UndefinedNoneOr[files.Resourceish] = undefined.UNDEFINED,
        system_channel: undefined.UndefinedNoneOr[
            snowflakes.SnowflakeishOr[channels.GuildTextChannel]
        ] = undefined.UNDEFINED,
        rules_channel: undefined.UndefinedNoneOr[
            snowflakes.SnowflakeishOr[channels.GuildTextChannel]
        ] = undefined.UNDEFINED,
        public_updates_channel: undefined.UndefinedNoneOr[
            snowflakes.SnowflakeishOr[channels.GuildTextChannel]
        ] = undefined.UNDEFINED,
        preferred_locale: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> guilds.RESTGuild:
        route = routes.PATCH_GUILD.compile(guild=guild)
        body = data_binding.JSONObjectBuilder()
        body.put("name", name)
        body.put("region", region, conversion=str)
        body.put("verification", verification_level)
        body.put("notifications", default_message_notifications)
        body.put("explicit_content_filter", explicit_content_filter_level)
        body.put("afk_timeout", afk_timeout)
        body.put("preferred_locale", preferred_locale, conversion=str)
        body.put_snowflake("afk_channel_id", afk_channel)
        body.put_snowflake("owner_id", owner)
        body.put_snowflake("system_channel_id", system_channel)
        body.put_snowflake("rules_channel_id", rules_channel)
        body.put_snowflake("public_updates_channel_id", public_updates_channel)

        tasks: typing.List[asyncio.Task[str]] = []

        if icon is None:
            body.put("icon", None)
        elif icon is not undefined.UNDEFINED:
            icon_resource = files.ensure_resource(icon)
            async with icon_resource.stream(executor=self._executor) as stream:
                task = asyncio.create_task(stream.data_uri())
                task.add_done_callback(lambda future: body.put("icon", future.result()))
                tasks.append(task)

        if splash is None:
            body.put("splash", None)
        elif splash is not undefined.UNDEFINED:
            splash_resource = files.ensure_resource(splash)
            async with splash_resource.stream(executor=self._executor) as stream:
                task = asyncio.create_task(stream.data_uri())
                task.add_done_callback(lambda future: body.put("splash", future.result()))
                tasks.append(task)

        if banner is None:
            body.put("banner", None)
        elif banner is not undefined.UNDEFINED:
            banner_resource = files.ensure_resource(banner)
            async with banner_resource.stream(executor=self._executor) as stream:
                task = asyncio.create_task(stream.data_uri())
                task.add_done_callback(lambda future: body.put("banner", future.result()))
                tasks.append(task)

        await asyncio.gather(*tasks)

        raw_response = await self._request(route, json=body, reason=reason)
        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._entity_factory.deserialize_rest_guild(response)

    async def delete_guild(self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild]) -> None:
        route = routes.DELETE_GUILD.compile(guild=guild)
        await self._request(route)

    async def fetch_guild_channels(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild]
    ) -> typing.Sequence[channels.GuildChannel]:
        route = routes.GET_GUILD_CHANNELS.compile(guild=guild)
        raw_response = await self._request(route)
        response = typing.cast(data_binding.JSONArray, raw_response)
        channel_sequence = data_binding.cast_json_array(response, self._entity_factory.deserialize_channel)
        # Will always be guild channels unless Discord messes up severely on something!
        return typing.cast("typing.Sequence[channels.GuildChannel]", channel_sequence)

    async def create_guild_text_channel(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        name: str,
        *,
        position: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        topic: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        nsfw: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        rate_limit_per_user: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        permission_overwrites: undefined.UndefinedOr[
            typing.Sequence[channels.PermissionOverwrite]
        ] = undefined.UNDEFINED,
        category: undefined.UndefinedOr[snowflakes.SnowflakeishOr[channels.GuildCategory]] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> channels.GuildTextChannel:
        channel = await self._create_guild_channel(
            guild,
            name,
            channels.ChannelType.GUILD_TEXT,
            position=position,
            topic=topic,
            nsfw=nsfw,
            rate_limit_per_user=rate_limit_per_user,
            permission_overwrites=permission_overwrites,
            category=category,
            reason=reason,
        )
        return typing.cast(channels.GuildTextChannel, channel)

    async def create_guild_news_channel(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        name: str,
        *,
        position: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        topic: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        nsfw: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        rate_limit_per_user: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        permission_overwrites: undefined.UndefinedOr[
            typing.Sequence[channels.PermissionOverwrite]
        ] = undefined.UNDEFINED,
        category: undefined.UndefinedOr[snowflakes.SnowflakeishOr[channels.GuildCategory]] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> channels.GuildNewsChannel:
        channel = await self._create_guild_channel(
            guild,
            name,
            channels.ChannelType.GUILD_NEWS,
            position=position,
            topic=topic,
            nsfw=nsfw,
            rate_limit_per_user=rate_limit_per_user,
            permission_overwrites=permission_overwrites,
            category=category,
            reason=reason,
        )
        return typing.cast(channels.GuildNewsChannel, channel)

    async def create_guild_voice_channel(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        name: str,
        *,
        position: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        user_limit: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        bitrate: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        permission_overwrites: undefined.UndefinedOr[
            typing.Sequence[channels.PermissionOverwrite]
        ] = undefined.UNDEFINED,
        category: undefined.UndefinedOr[snowflakes.SnowflakeishOr[channels.GuildCategory]] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> channels.GuildVoiceChannel:
        channel = await self._create_guild_channel(
            guild,
            name,
            channels.ChannelType.GUILD_VOICE,
            position=position,
            user_limit=user_limit,
            bitrate=bitrate,
            permission_overwrites=permission_overwrites,
            category=category,
            reason=reason,
        )
        return typing.cast(channels.GuildVoiceChannel, channel)

    async def create_guild_category(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        name: str,
        *,
        position: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        permission_overwrites: undefined.UndefinedOr[
            typing.Sequence[channels.PermissionOverwrite]
        ] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> channels.GuildCategory:
        channel = await self._create_guild_channel(
            guild,
            name,
            channels.ChannelType.GUILD_CATEGORY,
            position=position,
            permission_overwrites=permission_overwrites,
            reason=reason,
        )
        return typing.cast(channels.GuildCategory, channel)

    async def _create_guild_channel(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        name: str,
        type_: channels.ChannelType,
        *,
        position: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        topic: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        nsfw: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        bitrate: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        user_limit: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        rate_limit_per_user: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        permission_overwrites: undefined.UndefinedOr[
            typing.Sequence[channels.PermissionOverwrite]
        ] = undefined.UNDEFINED,
        category: undefined.UndefinedOr[snowflakes.SnowflakeishOr[channels.GuildCategory]] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> channels.GuildChannel:
        route = routes.POST_GUILD_CHANNELS.compile(guild=guild)
        body = data_binding.JSONObjectBuilder()
        body.put("type", type_)
        body.put("name", name)
        body.put("position", position)
        body.put("topic", topic)
        body.put("nsfw", nsfw)
        body.put("bitrate", bitrate)
        body.put("user_limit", user_limit)
        body.put("rate_limit_per_user", rate_limit_per_user)
        body.put_snowflake("category_id", category)
        body.put_array(
            "permission_overwrites",
            permission_overwrites,
            conversion=self._entity_factory.serialize_permission_overwrite,
        )

        raw_response = await self._request(route, json=body, reason=reason)
        response = typing.cast(data_binding.JSONObject, raw_response)
        channel = self._entity_factory.deserialize_channel(response)
        return typing.cast(channels.GuildChannel, channel)

    async def reposition_channels(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        positions: typing.Mapping[int, typing.Union[snowflakes.SnowflakeishOr[channels.GuildChannel]]],
    ) -> None:
        route = routes.POST_GUILD_CHANNELS.compile(guild=guild)
        body = [{"id": str(int(channel)), "position": pos} for pos, channel in positions.items()]
        await self._request(route, json=body)

    async def fetch_member(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], user: snowflakes.SnowflakeishOr[users.PartialUser],
    ) -> guilds.Member:
        route = routes.GET_GUILD_MEMBER.compile(guild=guild, user=user)
        raw_response = await self._request(route)
        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._entity_factory.deserialize_member(response, guild_id=snowflakes.Snowflake(guild))

    def fetch_members(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild]
    ) -> iterators.LazyIterator[guilds.Member]:
        return special_endpoints.MemberIterator(
            entity_factory=self._entity_factory, request_call=self._request, guild=guild
        )

    async def edit_member(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        *,
        nick: undefined.UndefinedNoneOr[str] = undefined.UNDEFINED,
        roles: undefined.UndefinedOr[
            typing.Collection[snowflakes.SnowflakeishOr[guilds.PartialRole]]
        ] = undefined.UNDEFINED,
        mute: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        deaf: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        voice_channel: undefined.UndefinedNoneOr[
            snowflakes.SnowflakeishOr[channels.GuildVoiceChannel]
        ] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        route = routes.PATCH_GUILD_MEMBER.compile(guild=guild, user=user)
        body = data_binding.JSONObjectBuilder()
        body.put("nick", nick)
        body.put("mute", mute)
        body.put("deaf", deaf)
        body.put_snowflake_array("roles", roles)

        if voice_channel is None:
            body.put("channel_id", None)
        elif voice_channel is not undefined.UNDEFINED:
            body.put_snowflake("channel_id", voice_channel)

        await self._request(route, json=body, reason=reason)

    async def edit_my_nick(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.Guild],
        nick: typing.Optional[str],
        *,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        route = routes.PATCH_MY_GUILD_NICKNAME.compile(guild=guild)
        body = data_binding.JSONObjectBuilder()
        body.put("nick", nick)
        await self._request(route, json=body, reason=reason)

    async def add_role_to_member(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        role: snowflakes.SnowflakeishOr[guilds.PartialRole],
        *,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        route = routes.PUT_GUILD_MEMBER_ROLE.compile(guild=guild, user=user, role=role)
        await self._request(route, reason=reason)

    async def remove_role_from_member(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        role: snowflakes.SnowflakeishOr[guilds.PartialRole],
        *,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        route = routes.DELETE_GUILD_MEMBER_ROLE.compile(guild=guild, user=user, role=role)
        await self._request(route, reason=reason)

    async def kick_user(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        *,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        route = routes.DELETE_GUILD_MEMBER.compile(guild=guild, user=user)
        await self._request(route, reason=reason)

    kick_member = kick_user

    async def ban_user(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        *,
        delete_message_days: undefined.UndefinedNoneOr[int] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        body = data_binding.JSONObjectBuilder()
        body.put("delete_message_days", delete_message_days)
        # This endpoint specifies a reason in the body, specifically.
        body.put("reason", reason)
        route = routes.PUT_GUILD_BAN.compile(guild=guild, user=user)
        await self._request(route, json=body)

    ban_member = ban_user

    async def unban_user(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        *,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        route = routes.DELETE_GUILD_BAN.compile(guild=guild, user=user)
        await self._request(route, reason=reason)

    unban_member = unban_user

    async def fetch_ban(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], user: snowflakes.SnowflakeishOr[users.PartialUser],
    ) -> guilds.GuildMemberBan:
        route = routes.GET_GUILD_BAN.compile(guild=guild, user=user)
        raw_response = await self._request(route)
        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._entity_factory.deserialize_guild_member_ban(response)

    async def fetch_bans(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild]
    ) -> typing.Sequence[guilds.GuildMemberBan]:
        route = routes.GET_GUILD_BANS.compile(guild=guild)
        raw_response = await self._request(route)
        response = typing.cast(data_binding.JSONArray, raw_response)
        return data_binding.cast_json_array(response, self._entity_factory.deserialize_guild_member_ban)

    async def fetch_roles(self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],) -> typing.Sequence[guilds.Role]:
        route = routes.GET_GUILD_ROLES.compile(guild=guild)
        raw_response = await self._request(route)
        response = typing.cast(data_binding.JSONArray, raw_response)
        return data_binding.cast_json_array(
            response, self._entity_factory.deserialize_role, guild_id=snowflakes.Snowflake(guild)
        )

    async def create_role(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        *,
        name: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        permissions: undefined.UndefinedOr[permissions_.Permissions] = undefined.UNDEFINED,
        color: undefined.UndefinedOr[colors.Colorish] = undefined.UNDEFINED,
        colour: undefined.UndefinedOr[colors.Colorish] = undefined.UNDEFINED,
        hoist: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        mentionable: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> guilds.Role:
        if not undefined.count(color, colour):
            raise TypeError("Can not specify 'color' and 'colour' together.")

        route = routes.POST_GUILD_ROLES.compile(guild=guild)
        body = data_binding.JSONObjectBuilder()
        body.put("name", name)
        body.put("permissions", permissions)
        body.put("color", color)
        body.put("color", colour)
        body.put("hoist", hoist)
        body.put("mentionable", mentionable)

        raw_response = await self._request(route, json=body, reason=reason)
        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._entity_factory.deserialize_role(response, guild_id=snowflakes.Snowflake(guild))

    async def reposition_roles(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        positions: typing.Mapping[int, snowflakes.SnowflakeishOr[guilds.PartialRole]],
    ) -> None:
        route = routes.POST_GUILD_ROLES.compile(guild=guild)
        body = [{"id": str(int(role)), "position": pos} for pos, role in positions.items()]
        await self._request(route, json=body)

    async def edit_role(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        role: snowflakes.SnowflakeishOr[guilds.PartialRole],
        *,
        name: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        permissions: undefined.UndefinedOr[permissions_.Permissions] = undefined.UNDEFINED,
        color: undefined.UndefinedOr[colors.Colorish] = undefined.UNDEFINED,
        colour: undefined.UndefinedOr[colors.Colorish] = undefined.UNDEFINED,
        hoist: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        mentionable: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> guilds.Role:
        if not undefined.count(color, colour):
            raise TypeError("Can not specify 'color' and 'colour' together.")

        route = routes.PATCH_GUILD_ROLE.compile(guild=guild, role=role)

        body = data_binding.JSONObjectBuilder()
        body.put("name", name)
        body.put("permissions", permissions)
        body.put("color", color)
        body.put("color", colour)
        body.put("hoist", hoist)
        body.put("mentionable", mentionable)

        raw_response = await self._request(route, json=body, reason=reason)
        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._entity_factory.deserialize_role(response, guild_id=snowflakes.Snowflake(guild))

    async def delete_role(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        role: snowflakes.SnowflakeishOr[guilds.PartialRole],
    ) -> None:
        route = routes.DELETE_GUILD_ROLE.compile(guild=guild, role=role)
        await self._request(route)

    async def estimate_guild_prune_count(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        *,
        days: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        include_roles: undefined.UndefinedOr[
            typing.Collection[snowflakes.SnowflakeishOr[guilds.PartialRole]]
        ] = undefined.UNDEFINED,
    ) -> int:
        route = routes.GET_GUILD_PRUNE.compile(guild=guild)
        query = data_binding.StringMapBuilder()
        query.put("days", days)
        if include_roles is not undefined.UNDEFINED:
            roles = ",".join(str(int(role)) for role in include_roles)
            query.put("include_roles", roles)
        raw_response = await self._request(route, query=query)
        response = typing.cast(data_binding.JSONObject, raw_response)
        return int(response["pruned"])

    async def begin_guild_prune(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        *,
        days: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        compute_prune_count: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        include_roles: undefined.UndefinedOr[
            typing.Collection[snowflakes.SnowflakeishOr[guilds.PartialRole]]
        ] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> typing.Optional[int]:
        route = routes.POST_GUILD_PRUNE.compile(guild=guild)
        body = data_binding.JSONObjectBuilder()
        body.put("days", days)
        body.put("compute_prune_count", compute_prune_count)
        body.put_snowflake_array("include_roles", include_roles)
        raw_response = await self._request(route, json=body, reason=reason)
        response = typing.cast(data_binding.JSONObject, raw_response)
        pruned = response.get("pruned")
        return int(pruned) if pruned is not None else None

    async def fetch_guild_voice_regions(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
    ) -> typing.Sequence[voices.VoiceRegion]:
        route = routes.GET_GUILD_VOICE_REGIONS.compile(guild=guild)
        raw_response = await self._request(route)
        response = typing.cast(data_binding.JSONArray, raw_response)
        return data_binding.cast_json_array(response, self._entity_factory.deserialize_voice_region)

    async def fetch_guild_invites(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
    ) -> typing.Sequence[invites.InviteWithMetadata]:
        route = routes.GET_GUILD_INVITES.compile(guild=guild)
        raw_response = await self._request(route)
        response = typing.cast(data_binding.JSONArray, raw_response)
        return data_binding.cast_json_array(response, self._entity_factory.deserialize_invite_with_metadata)

    async def fetch_integrations(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
    ) -> typing.Sequence[guilds.Integration]:
        route = routes.GET_GUILD_INTEGRATIONS.compile(guild=guild)
        raw_response = await self._request(route)
        response = typing.cast(data_binding.JSONArray, raw_response)
        return data_binding.cast_json_array(response, self._entity_factory.deserialize_integration)

    async def edit_integration(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        integration: snowflakes.SnowflakeishOr[guilds.Integration],
        *,
        expire_behaviour: undefined.UndefinedOr[guilds.IntegrationExpireBehaviour] = undefined.UNDEFINED,
        expire_grace_period: undefined.UndefinedOr[date.Intervalish] = undefined.UNDEFINED,
        enable_emojis: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        route = routes.PATCH_GUILD_INTEGRATION.compile(guild=guild, integration=integration)
        body = data_binding.JSONObjectBuilder()
        body.put("expire_behaviour", expire_behaviour)
        body.put("expire_grace_period", expire_grace_period, conversion=date.timespan_to_int)
        # Inconsistent naming in the API itself, so I have changed the name.
        body.put("enable_emoticons", enable_emojis)
        await self._request(route, json=body, reason=reason)

    async def delete_integration(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        integration: snowflakes.SnowflakeishOr[guilds.Integration],
        *,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        route = routes.DELETE_GUILD_INTEGRATION.compile(guild=guild, integration=integration)
        await self._request(route, reason=reason)

    async def sync_integration(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        integration: snowflakes.SnowflakeishOr[guilds.Integration],
    ) -> None:
        route = routes.POST_GUILD_INTEGRATION_SYNC.compile(guild=guild, integration=integration)
        await self._request(route)

    async def fetch_widget(self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild]) -> guilds.GuildWidget:
        route = routes.GET_GUILD_WIDGET.compile(guild=guild)
        raw_response = await self._request(route)
        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._entity_factory.deserialize_guild_widget(response)

    async def edit_widget(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        *,
        channel: undefined.UndefinedNoneOr[snowflakes.SnowflakeishOr[channels.GuildChannel]] = undefined.UNDEFINED,
        enabled: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> guilds.GuildWidget:
        route = routes.PATCH_GUILD_WIDGET.compile(guild=guild)

        body = data_binding.JSONObjectBuilder()
        body.put("enabled", enabled)
        if channel is None:
            body.put("channel", None)
        elif channel is not undefined.UNDEFINED:
            body.put_snowflake("channel", channel)

        raw_response = await self._request(route, json=body, reason=reason)
        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._entity_factory.deserialize_guild_widget(response)

    async def fetch_vanity_url(self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild]) -> invites.VanityURL:
        route = routes.GET_GUILD_VANITY_URL.compile(guild=guild)
        raw_response = await self._request(route)
        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._entity_factory.deserialize_vanity_url(response)
