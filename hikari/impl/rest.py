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
"""Implementation of a V6 and V7 compatible HTTP API for Discord.

This also includes implementations of `hikari.api.app.IApp` designed towards
providing RESTful functionality.
"""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = ["RESTAppImpl", "RESTAppFactoryImpl", "RESTClientImpl"]

import asyncio
import contextlib
import datetime
import http
import logging
import math
import re
import typing

import aiohttp

from hikari import config
from hikari import errors
from hikari.api import rest as rest_api
from hikari.impl import buckets
from hikari.impl import entity_factory as entity_factory_impl
from hikari.impl import rate_limits
from hikari.impl import special_endpoints
from hikari.impl import stateless_cache
from hikari.models import channels
from hikari.models import embeds as embeds_
from hikari.models import emojis
from hikari.utilities import constants
from hikari.utilities import data_binding
from hikari.utilities import date
from hikari.utilities import files
from hikari.utilities import iterators
from hikari.utilities import net
from hikari.utilities import routes
from hikari.utilities import snowflake
from hikari.utilities import undefined

if typing.TYPE_CHECKING:
    import concurrent.futures
    import types

    from hikari.models import applications
    from hikari.models import audit_logs
    from hikari.models import colors
    from hikari.models import colours
    from hikari.models import gateway
    from hikari.models import guilds
    from hikari.models import invites
    from hikari.models import messages as messages_
    from hikari.models import permissions as permissions_
    from hikari.models import users
    from hikari.models import voices
    from hikari.models import webhooks
    from hikari.api import cache as cache_
    from hikari.api import entity_factory as entity_factory_


_LOGGER: typing.Final[logging.Logger] = logging.getLogger("hikari.rest")


class RESTAppImpl(rest_api.IRESTAppContextManager):
    """Client for a specific set of credentials within a HTTP-only application.

    Parameters
    ----------
    connector : aiohttp.BaseConnector
        The AIOHTTP connector to use. This must be closed by the caller, and
        will not be terminated when this class closes (since you will generally
        expect this to be a connection pool).
    debug : builtins.bool
        Defaulting to `builtins.False`, if `builtins.True`, then each payload
        sent and received in HTTP requests will be dumped to debug logs. This
        will provide useful debugging context at the cost of performance.
        Generally you do not need to enable this.
    executor : concurrent.futures.Executor or builtins.None
        The executor to use for blocking file IO operations. If `builtins.None`
        is passed, then the default `concurrent.futures.ThreadPoolExecutor` for
        the `asyncio.AbstractEventLoop` will be used instead.
    global_ratelimit : hikari.impl.rate_limits.ManualRateLimiter
        The global ratelimiter.
    http_settings : hikari.config.HTTPSettings
        HTTP-related settings.
    proxy_settings : hikari.config.ProxySettings
        Proxy-related settings.
    token : builtins.str or builtins.None
        If defined, the token to use. If not defined, no token will be injected
        into the `Authorization` header for requests.
    token_type : builtins.str or builtins.None
        The token type to use. If undefined, a default is used instead, which
        will be `Bot`. If no `token` is provided, this is ignored.
    url : builtins.str or builtins.None
        The API URL to hit. Generally you can leave this undefined and use the
        default.
    version : builtins.int
        The API version to use. This is interpolated into the default `url`
        to create the full URL. Currently this only supports `6` or `7`.
    """

    def __init__(
        self,
        *,
        connector: aiohttp.BaseConnector,
        debug: bool = False,
        executor: typing.Optional[concurrent.futures.Executor],
        global_ratelimit: rate_limits.ManualRateLimiter,
        http_settings: config.HTTPSettings,
        proxy_settings: config.ProxySettings,
        token: typing.Optional[str],
        token_type: typing.Optional[str],
        url: typing.Optional[str],
        version: int,
    ) -> None:
        self._cache: cache_.ICacheComponent = stateless_cache.StatelessCacheImpl()
        self._debug = debug
        self._entity_factory = entity_factory_impl.EntityFactoryComponentImpl(self)
        self._executor = executor
        self._http_settings = http_settings
        self._proxy_settings = proxy_settings
        self._rest = RESTClientImpl(
            app=self,
            connector=connector,
            connector_owner=False,
            debug=debug,
            http_settings=http_settings,
            global_ratelimit=global_ratelimit,
            proxy_settings=proxy_settings,
            token=token,
            token_type=token_type,
            rest_url=url,
            version=version,
        )

    @property
    def cache(self) -> cache_.ICacheComponent:
        """Return the cache component.

        !!! warn
            This will always return `builtins.NotImplemented` for HTTP-only applications.
        """
        return self._cache

    @property
    def debug(self) -> bool:
        return self._debug

    @property
    def executor(self) -> typing.Optional[concurrent.futures.Executor]:
        return self._executor

    @property
    def entity_factory(self) -> entity_factory_.IEntityFactoryComponent:
        return self._entity_factory

    @property
    def http_settings(self) -> config.HTTPSettings:
        return self._http_settings

    @property
    def proxy_settings(self) -> config.ProxySettings:
        return self._proxy_settings

    @property
    def rest(self) -> rest_api.IRESTClient:
        return self._rest

    async def close(self) -> None:
        await self._rest.close()

    async def __aenter__(self) -> rest_api.IRESTAppContextManager:
        return self

    async def __aexit__(
        self,
        exc_type: typing.Optional[typing.Type[BaseException]],
        exc_val: typing.Optional[BaseException],
        exc_tb: typing.Optional[types.TracebackType],
    ) -> None:
        await self.close()


class RESTAppFactoryImpl(rest_api.IRESTAppFactory):
    """The base for a HTTP-only Discord application.

    This comprises of a shared TCP connector connection pool, and can have
    `hikari.api.rest.IRESTApp` instances for specific credentials acquired
    from it.

    Parameters
    ----------
    connector : aiohttp.BaseConnector or builtins.None
        The connector to use for HTTP sockets. If `builtins.None`, this will be
        automatically created for you.
    connector_owner : builtins.bool
        If you created the connector yourself, set this to `builtins.True` if
        you want this component to destroy the connector once closed. Otherwise,
        `builtins.False` will prevent this and you will have to do this
        manually. The latter is useful if you wish to maintain a shared
        connection pool across your application.
    debug : builtins.bool
        If `builtins.True`, then much more information is logged each time a
        request is made. Generally you do not need this to be on, so it will
        default to `builtins.False` instead.
    executor : concurrent.futures.Executor or builtins.None
        The executor to use for blocking file IO operations. If `builtins.None`
        is passed, then the default `concurrent.futures.ThreadPoolExecutor` for
        the `asyncio.AbstractEventLoop` will be used instead.
    http_settings : hikari.config.HTTPSettings or builtins.None
        HTTP settings to use. Sane defaults are used if this is
        `builtins.None`.
    proxy_settings : hikari.config.ProxySettings or builtins.None
        Proxy settings to use. If `builtins.None` then no proxy configuration
        will be used.
    url : str or hikari.utilities.undefined.UndefinedType
        The base URL for the API. You can generally leave this as being
        `undefined` and the correct default API base URL will be generated.
    version : builtins.int
        The Discord API version to use. Can be `6` (stable, default), or `7`
        (undocumented development release).
    """

    def __init__(
        self,
        *,
        connector: typing.Optional[aiohttp.BaseConnector] = None,
        connector_owner: bool = True,
        debug: bool = False,
        executor: typing.Optional[concurrent.futures.Executor] = None,
        http_settings: typing.Optional[config.HTTPSettings] = None,
        proxy_settings: typing.Optional[config.ProxySettings] = None,
        url: typing.Optional[str] = None,
        version: int = 6,
    ) -> None:
        self._connector = aiohttp.TCPConnector() if connector is None else connector
        self._connector_owner = connector_owner
        self._debug = debug
        self._executor = executor
        self._global_ratelimit = rate_limits.ManualRateLimiter()
        self._http_settings = config.HTTPSettings() if http_settings is None else http_settings
        self._proxy_settings = config.ProxySettings() if proxy_settings is None else proxy_settings
        self._url = url
        self._version = version

    @property
    def debug(self) -> bool:
        return self._debug

    @property
    def http_settings(self) -> config.HTTPSettings:
        return self._http_settings

    @property
    def proxy_settings(self) -> config.ProxySettings:
        return self._proxy_settings

    def acquire(self, token: str, token_type: str = constants.BEARER_TOKEN) -> rest_api.IRESTAppContextManager:
        return RESTAppImpl(
            connector=self._connector,
            debug=self._debug,
            executor=self._executor,
            http_settings=self._http_settings,
            global_ratelimit=self._global_ratelimit,
            proxy_settings=self._proxy_settings,
            token=token,
            token_type=token_type,
            url=self._url,
            version=self._version,
        )

    async def close(self) -> None:
        if self._connector_owner:
            await self._connector.close()
        self._global_ratelimit.close()

    async def __aenter__(self) -> RESTAppFactoryImpl:
        return self

    async def __aexit__(
        self,
        exc_type: typing.Optional[typing.Type[BaseException]],
        exc_val: typing.Optional[BaseException],
        exc_tb: typing.Optional[types.TracebackType],
    ) -> None:
        await self.close()


class RESTClientImpl(rest_api.IRESTClient):
    """Implementation of the V6 and V7-compatible Discord HTTP API.

    This manages making HTTP/1.1 requests to the API and using the entity
    factory within the passed application instance to deserialize JSON responses
    to Pythonic data classes that are used throughout this library.

    Parameters
    ----------
    app : hikari.api.rest.app.IRESTApp
        The HTTP application containing all other application components
        that Hikari uses.
    debug : builtins.bool
        If `builtins.True`, this will enable logging of each payload sent and
        received, as well as information such as DNS cache hits and misses, and
        other information useful for debugging this application. These logs will
        be written as DEBUG log entries. For most purposes, this should be
        left `builtins.False`.
    global_ratelimit : hikari.impl.rate_limits.ManualRateLimiter
        The shared ratelimiter to use for the application.
    token : hikari.utilities.undefined.UndefinedOr[builtins.str]
        The bot or bearer token. If no token is to be used,
        this can be undefined.
    token_type : hikari.utilities.undefined.UndefinedOr[builtins.str]
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
        "_app",
        "_client_session",
        "_connector",
        "_connector_owner",
        "_debug",
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

    @typing.final
    class _RetryRequest(RuntimeError):
        __slots__: typing.Sequence[str] = ()

    def __init__(
        self,
        *,
        app: rest_api.IRESTApp,
        connector: typing.Optional[aiohttp.BaseConnector],
        connector_owner: bool,
        debug: bool,
        global_ratelimit: rate_limits.ManualRateLimiter,
        http_settings: config.HTTPSettings,
        proxy_settings: config.ProxySettings,
        token: typing.Optional[str],
        token_type: typing.Optional[str],
        rest_url: typing.Optional[str],
        version: int,
    ) -> None:
        self.buckets = buckets.RESTBucketManager()
        self.global_rate_limit = global_ratelimit
        self.version = version

        self._app = app
        self._client_session: typing.Optional[aiohttp.ClientSession] = None
        self._connector = connector
        self._connector_owner = connector_owner
        self._debug = debug
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
    def app(self) -> rest_api.IRESTApp:
        return self._app

    @typing.final
    def _acquire_client_session(self) -> aiohttp.ClientSession:
        if self._client_session is None:
            self._client_session = aiohttp.ClientSession(
                connector=self._connector,
                version=aiohttp.HttpVersion11,
                timeout=aiohttp.ClientTimeout(
                    total=self._http_settings.timeouts.total,
                    connect=self._http_settings.timeouts.acquire_and_connect,
                    sock_read=self._http_settings.timeouts.request_socket_read,
                    sock_connect=self._http_settings.timeouts.request_socket_connect,
                ),
                trust_env=self._proxy_settings.trust_env,
            )

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
        # Make a ratelimit-protected HTTP request to a JSON _endpoint and expect some form
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
                    raise errors.HTTPError(real_url, f"Expected JSON response but received {response.content_type}")

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
            raise errors.HTTPErrorResponse(
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

            _LOGGER.warning("you are being rate-limited globally - trying again after %ss", body_retry_after)
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
        # trust that voodoo type stuff won't ever occur with that value from them...
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

        raise errors.RateLimited(str(response.real_url), compiled_route, response.headers, body, body_retry_after)

    @staticmethod
    @typing.final
    def _generate_allowed_mentions(
        mentions_everyone: undefined.UndefinedOr[bool],
        user_mentions: undefined.UndefinedOr[
            typing.Union[typing.Collection[snowflake.SnowflakeishOr[users.PartialUser]], bool]
        ],
        role_mentions: undefined.UndefinedOr[
            typing.Union[typing.Collection[snowflake.SnowflakeishOr[guilds.PartialRole]], bool]
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

    @typing.final
    async def close(self) -> None:
        """Close the HTTP client and any open HTTP connections."""
        if self._client_session is not None:
            await self._client_session.close()
        self.buckets.close()

    async def fetch_channel(
        self, channel: snowflake.SnowflakeishOr[channels.PartialChannel]
    ) -> channels.PartialChannel:
        route = routes.GET_CHANNEL.compile(channel=channel)
        raw_response = await self._request(route)
        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._app.entity_factory.deserialize_channel(response)

    async def edit_channel(
        self,
        channel: snowflake.SnowflakeishOr[channels.GuildChannel],
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
        parent_category: undefined.UndefinedOr[snowflake.SnowflakeishOr[channels.GuildCategory]] = undefined.UNDEFINED,
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
            conversion=self._app.entity_factory.serialize_permission_overwrite,
        )

        raw_response = await self._request(route, json=body, reason=reason)
        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._app.entity_factory.deserialize_channel(response)

    async def delete_channel(self, channel: snowflake.SnowflakeishOr[channels.PartialChannel]) -> None:
        route = routes.DELETE_CHANNEL.compile(channel=channel)
        await self._request(route)

    async def edit_permission_overwrites(
        self,
        channel: snowflake.SnowflakeishOr[channels.GuildChannel],
        target: typing.Union[
            snowflake.Snowflakeish, users.PartialUser, guilds.PartialRole, channels.PermissionOverwrite
        ],
        *,
        target_type: undefined.UndefinedOr[typing.Union[channels.PermissionOverwriteType, str]] = undefined.UNDEFINED,
        allow: undefined.UndefinedOr[permissions_.Permission] = undefined.UNDEFINED,
        deny: undefined.UndefinedOr[permissions_.Permission] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        if target_type is undefined.UNDEFINED:
            if isinstance(target, users.UserImpl):
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
        channel: snowflake.SnowflakeishOr[channels.GuildChannel],
        target: snowflake.SnowflakeishOr[
            typing.Union[channels.PermissionOverwrite, guilds.PartialRole, users.PartialUser, snowflake.Snowflakeish]
        ],
    ) -> None:
        route = routes.DELETE_CHANNEL_PERMISSIONS.compile(channel=channel, overwrite=target)
        await self._request(route)

    async def fetch_channel_invites(
        self, channel: snowflake.SnowflakeishOr[channels.GuildChannel]
    ) -> typing.Sequence[invites.InviteWithMetadata]:
        route = routes.GET_CHANNEL_INVITES.compile(channel=channel)
        raw_response = await self._request(route)
        response = typing.cast(data_binding.JSONArray, raw_response)
        return data_binding.cast_json_array(response, self._app.entity_factory.deserialize_invite_with_metadata)

    async def create_invite(
        self,
        channel: snowflake.SnowflakeishOr[channels.GuildChannel],
        *,
        max_age: undefined.UndefinedOr[date.Intervalish] = undefined.UNDEFINED,
        max_uses: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        temporary: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        unique: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        target_user: undefined.UndefinedOr[snowflake.SnowflakeishOr[users.UserImpl]] = undefined.UNDEFINED,
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
        return self._app.entity_factory.deserialize_invite_with_metadata(response)

    def trigger_typing(
        self, channel: snowflake.SnowflakeishOr[channels.TextChannel]
    ) -> special_endpoints.TypingIndicator:
        return special_endpoints.TypingIndicator(self._request, channel)

    async def fetch_pins(
        self, channel: snowflake.SnowflakeishOr[channels.TextChannel]
    ) -> typing.Sequence[messages_.Message]:
        route = routes.GET_CHANNEL_PINS.compile(channel=channel)
        raw_response = await self._request(route)
        response = typing.cast(data_binding.JSONArray, raw_response)
        return data_binding.cast_json_array(response, self._app.entity_factory.deserialize_message)

    async def pin_message(
        self,
        channel: snowflake.SnowflakeishOr[channels.TextChannel],
        message: snowflake.SnowflakeishOr[messages_.Message],
    ) -> None:
        route = routes.PUT_CHANNEL_PINS.compile(channel=channel, message=message)
        await self._request(route)

    async def unpin_message(
        self,
        channel: snowflake.SnowflakeishOr[channels.TextChannel],
        message: snowflake.SnowflakeishOr[messages_.Message],
    ) -> None:
        route = routes.DELETE_CHANNEL_PIN.compile(channel=channel, message=message)
        await self._request(route)

    def fetch_messages(
        self,
        channel: snowflake.SnowflakeishOr[channels.TextChannel],
        *,
        before: undefined.UndefinedOr[snowflake.SearchableSnowflakeishOr[snowflake.Unique]] = undefined.UNDEFINED,
        after: undefined.UndefinedOr[snowflake.SearchableSnowflakeishOr[snowflake.Unique]] = undefined.UNDEFINED,
        around: undefined.UndefinedOr[snowflake.SearchableSnowflakeishOr[snowflake.Unique]] = undefined.UNDEFINED,
    ) -> iterators.LazyIterator[messages_.Message]:
        if undefined.count(before, after, around) < 2:
            raise TypeError("Expected no kwargs, or maximum of one of 'before', 'after', 'around'")

        timestamp: undefined.UndefinedOr[str]

        if before is not undefined.UNDEFINED:
            direction = "before"
            if isinstance(before, datetime.datetime):
                timestamp = str(snowflake.Snowflake.from_datetime(before))
            else:
                timestamp = str(int(before))
        elif after is not undefined.UNDEFINED:
            direction = "after"
            if isinstance(after, datetime.datetime):
                timestamp = str(snowflake.Snowflake.from_datetime(after))
            else:
                timestamp = str(int(after))
        elif around is not undefined.UNDEFINED:
            direction = "around"
            if isinstance(around, datetime.datetime):
                timestamp = str(snowflake.Snowflake.from_datetime(around))
            else:
                timestamp = str(int(around))
        else:
            direction = "before"
            timestamp = undefined.UNDEFINED

        return special_endpoints.MessageIterator(self._app, self._request, channel, direction, timestamp)

    async def fetch_message(
        self,
        channel: snowflake.SnowflakeishOr[channels.TextChannel],
        message: snowflake.SnowflakeishOr[messages_.Message],
    ) -> messages_.Message:
        route = routes.GET_CHANNEL_MESSAGE.compile(channel=channel, message=message)
        raw_response = await self._request(route)
        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._app.entity_factory.deserialize_message(response)

    async def create_message(
        self,
        channel: snowflake.SnowflakeishOr[channels.TextChannel],
        content: undefined.UndefinedOr[typing.Any] = undefined.UNDEFINED,
        *,
        embed: undefined.UndefinedOr[embeds_.Embed] = undefined.UNDEFINED,
        attachment: undefined.UndefinedOr[files.Resourceish] = undefined.UNDEFINED,
        attachments: undefined.UndefinedOr[typing.Sequence[files.Resourceish]] = undefined.UNDEFINED,
        tts: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        nonce: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        mentions_everyone: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        user_mentions: undefined.UndefinedOr[
            typing.Union[typing.Collection[snowflake.SnowflakeishOr[users.PartialUser]], bool]
        ] = undefined.UNDEFINED,
        role_mentions: undefined.UndefinedOr[
            typing.Union[typing.Collection[snowflake.SnowflakeishOr[guilds.PartialRole]], bool]
        ] = undefined.UNDEFINED,
    ) -> messages_.Message:
        if attachment is not undefined.UNDEFINED and attachments is not undefined.UNDEFINED:
            raise ValueError("You may only specify one of 'attachment' or 'attachments', not both")

        route = routes.POST_CHANNEL_MESSAGES.compile(channel=channel)

        if embed is undefined.UNDEFINED and isinstance(content, embeds_.Embed):
            # Syntatic sugar, common mistake to accidentally send an embed
            # as the content, so lets detect this and fix it for the user.
            embed = content
            content = undefined.UNDEFINED

        elif undefined.count(attachment, attachments) == 2 and isinstance(content, files.Resource):
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

        final_attachments: typing.List[files.Resource] = []

        if attachment is not undefined.UNDEFINED:
            final_attachments.append(files.ensure_resource(attachment))
        if attachments is not undefined.UNDEFINED:
            final_attachments.extend([files.ensure_resource(a) for a in attachments])

        if embed is not undefined.UNDEFINED:
            embed_payload, embed_attachments = self._app.entity_factory.serialize_embed(embed)
            body.put("embed", embed_payload)
            final_attachments.extend(embed_attachments)

        if final_attachments:
            form = data_binding.URLEncodedForm()
            form.add_field("payload_json", data_binding.dump_json(body), content_type=constants.APPLICATION_JSON)

            stack = contextlib.AsyncExitStack()

            try:
                for i, attachment in enumerate(final_attachments):
                    stream = await stack.enter_async_context(attachment.stream(executor=self._app.executor))
                    form.add_field(
                        f"file{i}", stream, filename=stream.filename, content_type=constants.APPLICATION_OCTET_STREAM
                    )

                raw_response = await self._request(route, form=form)
            finally:
                await stack.aclose()
        else:
            raw_response = await self._request(route, json=body)

        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._app.entity_factory.deserialize_message(response)

    async def edit_message(
        self,
        channel: typing.Union[snowflake.SnowflakeishOr[channels.TextChannel]],
        message: typing.Union[snowflake.SnowflakeishOr[messages_.Message]],
        content: undefined.UndefinedOr[typing.Any] = undefined.UNDEFINED,
        *,
        embed: undefined.UndefinedNoneOr[embeds_.Embed] = undefined.UNDEFINED,
        mentions_everyone: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        user_mentions: undefined.UndefinedOr[
            typing.Union[typing.Collection[snowflake.SnowflakeishOr[users.PartialUser]], bool]
        ] = undefined.UNDEFINED,
        role_mentions: undefined.UndefinedOr[
            typing.Union[typing.Collection[snowflake.SnowflakeishOr[guilds.PartialRole]], bool]
        ] = undefined.UNDEFINED,
        flags: undefined.UndefinedOr[messages_.MessageFlag] = undefined.UNDEFINED,
    ) -> messages_.Message:
        route = routes.PATCH_CHANNEL_MESSAGE.compile(channel=channel, message=message)
        body = data_binding.JSONObjectBuilder()
        body.put("flags", flags)
        if (
            mentions_everyone is not undefined.UNDEFINED
            or user_mentions is not undefined.UNDEFINED
            or role_mentions is not undefined.UNDEFINED
        ):
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
            embed_payload, _ = self._app.entity_factory.serialize_embed(embed)
            body.put("embed", embed_payload)
        elif embed is None:
            body.put("embed", None)

        raw_response = await self._request(route, json=body)
        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._app.entity_factory.deserialize_message(response)

    async def delete_message(
        self,
        channel: snowflake.SnowflakeishOr[channels.TextChannel],
        message: snowflake.SnowflakeishOr[messages_.Message],
    ) -> None:
        route = routes.DELETE_CHANNEL_MESSAGE.compile(channel=channel, message=message)
        await self._request(route)

    async def delete_messages(
        self,
        channel: snowflake.SnowflakeishOr[channels.TextChannel],
        /,
        *messages: snowflake.SnowflakeishOr[messages_.Message],
    ) -> None:
        coroutines: typing.List[typing.Coroutine[typing.Any, typing.Any, typing.Any]] = []

        while messages:
            if len(messages) == 1:
                coroutines.append(self.delete_message(channel, *messages))
            else:
                chunk = messages[:100]
                route = routes.POST_DELETE_CHANNEL_MESSAGES_BULK.compile(channel=channel)
                body = data_binding.JSONObjectBuilder()
                body.put_snowflake_array("messages", chunk)
                coroutines.append(self._request(route, json=body))
                messages = messages[100:]

        await asyncio.gather(*coroutines)

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
        channel: snowflake.SnowflakeishOr[channels.TextChannel],
        message: snowflake.SnowflakeishOr[messages_.Message],
        emoji: emojis.Emojiish,
    ) -> None:
        route = routes.PUT_MY_REACTION.compile(
            emoji=self._transform_emoji_to_url_format(emoji), channel=channel, message=message,
        )
        await self._request(route)

    async def delete_my_reaction(
        self,
        channel: snowflake.SnowflakeishOr[channels.TextChannel],
        message: snowflake.SnowflakeishOr[messages_.Message],
        emoji: emojis.Emojiish,
    ) -> None:
        route = routes.DELETE_MY_REACTION.compile(
            emoji=self._transform_emoji_to_url_format(emoji), channel=channel, message=message,
        )
        await self._request(route)

    async def delete_all_reactions_for_emoji(
        self,
        channel: snowflake.SnowflakeishOr[channels.TextChannel],
        message: snowflake.SnowflakeishOr[messages_.Message],
        emoji: emojis.Emojiish,
    ) -> None:
        route = routes.DELETE_REACTION_EMOJI.compile(
            emoji=self._transform_emoji_to_url_format(emoji), channel=channel, message=message,
        )
        await self._request(route)

    async def delete_reaction(
        self,
        channel: snowflake.SnowflakeishOr[channels.TextChannel],
        message: snowflake.SnowflakeishOr[messages_.Message],
        emoji: emojis.Emojiish,
        user: snowflake.SnowflakeishOr[users.PartialUser],
    ) -> None:
        route = routes.DELETE_REACTION_USER.compile(
            emoji=self._transform_emoji_to_url_format(emoji), channel=channel, message=message, user=user,
        )
        await self._request(route)

    async def delete_all_reactions(
        self,
        channel: snowflake.SnowflakeishOr[channels.TextChannel],
        message: snowflake.SnowflakeishOr[messages_.Message],
    ) -> None:
        route = routes.DELETE_ALL_REACTIONS.compile(channel=channel, message=message)
        await self._request(route)

    def fetch_reactions_for_emoji(
        self,
        channel: snowflake.SnowflakeishOr[channels.TextChannel],
        message: snowflake.SnowflakeishOr[messages_.Message],
        emoji: emojis.Emojiish,
    ) -> iterators.LazyIterator[users.UserImpl]:
        return special_endpoints.ReactorIterator(
            app=self._app,
            request_call=self._request,
            channel=channel,
            message=message,
            emoji=self._transform_emoji_to_url_format(emoji),
        )

    async def create_webhook(
        self,
        channel: snowflake.SnowflakeishOr[channels.TextChannel],
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
            async with avatar_resource.stream(executor=self._app.executor) as stream:
                body.put("avatar", await stream.data_uri())

        raw_response = await self._request(route, json=body, reason=reason)
        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._app.entity_factory.deserialize_webhook(response)

    async def fetch_webhook(
        self,
        webhook: snowflake.SnowflakeishOr[webhooks.Webhook],
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
        return self._app.entity_factory.deserialize_webhook(response)

    async def fetch_channel_webhooks(
        self, channel: snowflake.SnowflakeishOr[channels.TextChannel],
    ) -> typing.Sequence[webhooks.Webhook]:
        route = routes.GET_CHANNEL_WEBHOOKS.compile(channel=channel)
        raw_response = await self._request(route)
        response = typing.cast(data_binding.JSONArray, raw_response)
        return data_binding.cast_json_array(response, self._app.entity_factory.deserialize_webhook)

    async def fetch_guild_webhooks(
        self, guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
    ) -> typing.Sequence[webhooks.Webhook]:
        route = routes.GET_GUILD_WEBHOOKS.compile(channel=guild)
        raw_response = await self._request(route)
        response = typing.cast(data_binding.JSONArray, raw_response)
        return data_binding.cast_json_array(response, self._app.entity_factory.deserialize_webhook)

    async def edit_webhook(
        self,
        webhook: snowflake.SnowflakeishOr[webhooks.Webhook],
        *,
        token: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        name: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        avatar: undefined.UndefinedNoneOr[files.Resourceish] = undefined.UNDEFINED,
        channel: undefined.UndefinedOr[snowflake.SnowflakeishOr[channels.TextChannel]] = undefined.UNDEFINED,
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
            async with avatar_resource.stream(executor=self._app.executor) as stream:
                body.put("avatar", await stream.data_uri())

        raw_response = await self._request(route, json=body, reason=reason, no_auth=no_auth)
        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._app.entity_factory.deserialize_webhook(response)

    async def delete_webhook(
        self,
        webhook: typing.Union[webhooks.Webhook, snowflake.SnowflakeishOr],
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
        webhook: snowflake.SnowflakeishOr[webhooks.Webhook],
        token: str,
        text: undefined.UndefinedOr[typing.Any] = undefined.UNDEFINED,
        *,
        username: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        avatar_url: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        embeds: undefined.UndefinedOr[typing.Sequence[embeds_.Embed]] = undefined.UNDEFINED,
        attachment: undefined.UndefinedOr[files.Resourceish] = undefined.UNDEFINED,
        attachments: undefined.UndefinedOr[typing.Sequence[files.Resourceish]] = undefined.UNDEFINED,
        tts: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        mentions_everyone: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        user_mentions: undefined.UndefinedOr[
            typing.Union[typing.Collection[snowflake.SnowflakeishOr[users.PartialUser]], bool]
        ] = undefined.UNDEFINED,
        role_mentions: undefined.UndefinedOr[
            typing.Union[typing.Collection[snowflake.SnowflakeishOr[guilds.PartialRole]], bool]
        ] = undefined.UNDEFINED,
    ) -> messages_.Message:
        if attachment is not undefined.UNDEFINED and attachments is not undefined.UNDEFINED:
            raise ValueError("You may only specify one of 'attachment' or 'attachments', not both")

        route = routes.POST_WEBHOOK_WITH_TOKEN.compile(webhook=webhook, token=token)

        final_attachments: typing.List[files.Resource] = []
        if attachment is not undefined.UNDEFINED:
            final_attachments.append(files.ensure_resource(attachment))
        if attachments is not undefined.UNDEFINED:
            final_attachments.extend([files.ensure_resource(a) for a in attachments])

        serialized_embeds = []

        if embeds is not undefined.UNDEFINED:
            for embed in embeds:
                embed_payload, embed_attachments = self._app.entity_factory.serialize_embed(embed)
                serialized_embeds.append(embed_payload)
                final_attachments.extend(embed_attachments)

        body = data_binding.JSONObjectBuilder()
        body.put("mentions", self._generate_allowed_mentions(mentions_everyone, user_mentions, role_mentions))
        body.put("content", text, conversion=str)
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
                    stream = await stack.enter_async_context(attachment.stream(executor=self._app.executor))
                    form.add_field(
                        f"file{i}", stream, filename=stream.filename, content_type=constants.APPLICATION_OCTET_STREAM
                    )

                raw_response = await self._request(route, query=query, form=form, no_auth=True)
            finally:
                await stack.aclose()
        else:
            raw_response = await self._request(route, query=query, json=body, no_auth=True)

        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._app.entity_factory.deserialize_message(response)

    async def fetch_gateway_url(self) -> str:
        route = routes.GET_GATEWAY.compile()
        # This doesn't need authorization.
        raw_response = await self._request(route, no_auth=True)
        response = typing.cast("typing.Mapping[str, str]", raw_response)
        return response["url"]

    async def fetch_gateway_bot(self) -> gateway.GatewayBot:
        route = routes.GET_GATEWAY_BOT.compile()
        raw_response = await self._request(route)
        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._app.entity_factory.deserialize_gateway_bot(response)

    async def fetch_invite(self, invite: invites.Inviteish) -> invites.Invite:
        route = routes.GET_INVITE.compile(invite_code=invite if isinstance(invite, str) else invite.code)
        query = data_binding.StringMapBuilder()
        query.put("with_counts", True)
        raw_response = await self._request(route, query=query)
        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._app.entity_factory.deserialize_invite(response)

    async def delete_invite(self, invite: invites.Inviteish) -> None:
        route = routes.DELETE_INVITE.compile(invite_code=invite if isinstance(invite, str) else invite.code)
        await self._request(route)

    async def fetch_my_user(self) -> users.OwnUser:
        route = routes.GET_MY_USER.compile()
        raw_response = await self._request(route)
        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._app.entity_factory.deserialize_my_user(response)

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
            async with avatar_resource.stream(executor=self._app.executor) as stream:
                body.put("avatar", await stream.data_uri())

        raw_response = await self._request(route, json=body)
        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._app.entity_factory.deserialize_my_user(response)

    async def fetch_my_connections(self) -> typing.Sequence[applications.OwnConnection]:
        route = routes.GET_MY_CONNECTIONS.compile()
        raw_response = await self._request(route)
        response = typing.cast(data_binding.JSONArray, raw_response)
        return data_binding.cast_json_array(response, self._app.entity_factory.deserialize_own_connection)

    def fetch_my_guilds(
        self,
        *,
        newest_first: bool = False,
        start_at: undefined.UndefinedOr[snowflake.SearchableSnowflakeishOr[guilds.PartialGuild]] = undefined.UNDEFINED,
    ) -> iterators.LazyIterator[applications.OwnGuild]:
        if start_at is undefined.UNDEFINED:
            start_at = snowflake.Snowflake.max() if newest_first else snowflake.Snowflake.min()
        elif isinstance(start_at, datetime.datetime):
            start_at = snowflake.Snowflake.from_datetime(start_at)

        return special_endpoints.OwnGuildIterator(self._app, self._request, newest_first, str(start_at))

    async def leave_guild(self, guild: snowflake.SnowflakeishOr[guilds.PartialGuild], /) -> None:
        route = routes.DELETE_MY_GUILD.compile(guild=guild)
        await self._request(route)

    async def create_dm_channel(self, user: snowflake.SnowflakeishOr[users.PartialUser], /) -> channels.DMChannel:
        route = routes.POST_MY_CHANNELS.compile()
        body = data_binding.JSONObjectBuilder()
        body.put_snowflake("recipient_id", user)
        raw_response = await self._request(route, json=body)
        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._app.entity_factory.deserialize_dm_channel(response)

    async def fetch_application(self) -> applications.Application:
        route = routes.GET_MY_APPLICATION.compile()
        raw_response = await self._request(route)
        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._app.entity_factory.deserialize_application(response)

    async def add_user_to_guild(
        self,
        access_token: str,
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
        user: snowflake.SnowflakeishOr[users.PartialUser],
        *,
        nick: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        roles: undefined.UndefinedOr[
            typing.Collection[snowflake.SnowflakeishOr[guilds.PartialRole]]
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
            return self._app.entity_factory.deserialize_member(response, guild_id=snowflake.Snowflake(guild))
        else:
            # User already is in the guild.
            return None

    async def fetch_voice_regions(self) -> typing.Sequence[voices.VoiceRegion]:
        route = routes.GET_VOICE_REGIONS.compile()
        raw_response = await self._request(route)
        response = typing.cast(data_binding.JSONArray, raw_response)
        return data_binding.cast_json_array(response, self._app.entity_factory.deserialize_voice_region)

    async def fetch_user(self, user: snowflake.SnowflakeishOr[users.PartialUser]) -> users.UserImpl:
        route = routes.GET_USER.compile(user=user)
        raw_response = await self._request(route)
        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._app.entity_factory.deserialize_user(response)

    def fetch_audit_log(
        self,
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
        *,
        before: undefined.UndefinedOr[snowflake.SearchableSnowflakeishOr[snowflake.Unique]] = undefined.UNDEFINED,
        user: undefined.UndefinedOr[snowflake.SnowflakeishOr[users.PartialUser]] = undefined.UNDEFINED,
        event_type: undefined.UndefinedOr[audit_logs.AuditLogEventType] = undefined.UNDEFINED,
    ) -> iterators.LazyIterator[audit_logs.AuditLog]:

        timestamp: undefined.UndefinedOr[str]
        if isinstance(before, datetime.datetime):
            timestamp = str(snowflake.Snowflake.from_datetime(before))
        elif before is not undefined.UNDEFINED:
            timestamp = str(int(before))
        else:
            timestamp = undefined.UNDEFINED

        return special_endpoints.AuditLogIterator(self._app, self._request, guild, timestamp, user, event_type)

    async def fetch_emoji(
        self,
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
        # This is an emoji ID, which is the URL-safe emoji name, not the snowflake alone.
        # likewise this only is valid for custom emojis, unicode emojis make little sense here.
        emoji: typing.Union[str, emojis.CustomEmoji],
    ) -> emojis.KnownCustomEmoji:
        route = routes.GET_GUILD_EMOJI.compile(
            guild=guild, emoji=emoji.id if isinstance(emoji, emojis.CustomEmoji) else emoji,
        )
        raw_response = await self._request(route)
        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._app.entity_factory.deserialize_known_custom_emoji(response, guild_id=snowflake.Snowflake(guild))

    async def fetch_guild_emojis(
        self, guild: snowflake.SnowflakeishOr[guilds.PartialGuild]
    ) -> typing.Set[emojis.KnownCustomEmoji]:
        route = routes.GET_GUILD_EMOJIS.compile(guild=guild)
        raw_response = await self._request(route)
        response = typing.cast(data_binding.JSONArray, raw_response)
        return set(
            data_binding.cast_json_array(
                response, self._app.entity_factory.deserialize_known_custom_emoji, guild_id=snowflake.Snowflake(guild)
            )
        )

    async def create_emoji(
        self,
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
        name: str,
        image: files.Resourceish,
        *,
        roles: undefined.UndefinedOr[
            typing.Collection[snowflake.SnowflakeishOr[guilds.PartialRole]]
        ] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> emojis.KnownCustomEmoji:
        route = routes.POST_GUILD_EMOJIS.compile(guild=guild)
        body = data_binding.JSONObjectBuilder()
        body.put("name", name)
        if image is not undefined.UNDEFINED:
            image_resource = files.ensure_resource(image)
            async with image_resource.stream(executor=self._app.executor) as stream:
                body.put("image", await stream.data_uri())

        body.put_snowflake_array("roles", roles)

        raw_response = await self._request(route, json=body, reason=reason)
        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._app.entity_factory.deserialize_known_custom_emoji(response, guild_id=snowflake.Snowflake(guild))

    async def edit_emoji(
        self,
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
        # This is an emoji ID, which is the URL-safe emoji name, not the snowflake alone.
        # likewise this only is valid for custom emojis, unicode emojis make little sense here.
        emoji: typing.Union[str, emojis.CustomEmoji],
        *,
        name: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        roles: undefined.UndefinedOr[
            typing.Collection[snowflake.SnowflakeishOr[guilds.PartialRole]]
        ] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> emojis.KnownCustomEmoji:
        route = routes.PATCH_GUILD_EMOJI.compile(
            guild=guild, emoji=emoji.id if isinstance(emoji, emojis.CustomEmoji) else emoji,
        )
        body = data_binding.JSONObjectBuilder()
        body.put("name", name)
        body.put_snowflake_array("roles", roles)

        raw_response = await self._request(route, json=body, reason=reason)
        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._app.entity_factory.deserialize_known_custom_emoji(response, guild_id=snowflake.Snowflake(guild))

    async def delete_emoji(
        self,
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
        # This is an emoji ID, which is the URL-safe emoji name, not the snowflake alone.
        emoji: typing.Union[str, emojis.CustomEmoji],
    ) -> None:
        route = routes.DELETE_GUILD_EMOJI.compile(
            guild=guild, emoji=emoji.id if isinstance(emoji, emojis.CustomEmoji) else emoji,
        )
        await self._request(route)

    def guild_builder(self, name: str, /) -> special_endpoints.GuildBuilder:
        return special_endpoints.GuildBuilder(app=self._app, name=name, request_call=self._request)

    async def fetch_guild(self, guild: snowflake.SnowflakeishOr[guilds.PartialGuild]) -> guilds.Guild:
        route = routes.GET_GUILD.compile(guild=guild)
        raw_response = await self._request(route)
        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._app.entity_factory.deserialize_guild(response)

    async def fetch_guild_preview(self, guild: snowflake.SnowflakeishOr[guilds.PartialGuild],) -> guilds.GuildPreview:
        route = routes.GET_GUILD_PREVIEW.compile(guild=guild)
        raw_response = await self._request(route)
        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._app.entity_factory.deserialize_guild_preview(response)

    async def edit_guild(
        self,
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
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
        afk_channel: undefined.UndefinedOr[snowflake.SnowflakeishOr[channels.GuildVoiceChannel]] = undefined.UNDEFINED,
        afk_timeout: undefined.UndefinedOr[date.Intervalish] = undefined.UNDEFINED,
        icon: undefined.UndefinedNoneOr[files.Resourceish] = undefined.UNDEFINED,
        owner: undefined.UndefinedOr[snowflake.SnowflakeishOr[users.PartialUser]] = undefined.UNDEFINED,
        splash: undefined.UndefinedNoneOr[files.Resourceish] = undefined.UNDEFINED,
        banner: undefined.UndefinedNoneOr[files.Resourceish] = undefined.UNDEFINED,
        system_channel: undefined.UndefinedNoneOr[channels.GuildTextChannel] = undefined.UNDEFINED,
        rules_channel: undefined.UndefinedNoneOr[channels.GuildTextChannel] = undefined.UNDEFINED,
        public_updates_channel: undefined.UndefinedNoneOr[channels.GuildTextChannel] = undefined.UNDEFINED,
        preferred_locale: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> guilds.Guild:
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

        # TODO: gather these futures simultaneously for a 3x speedup...

        if icon is None:
            body.put("icon", None)
        elif icon is not undefined.UNDEFINED:
            icon_resource = files.ensure_resource(icon)
            async with icon_resource.stream(executor=self._app.executor) as stream:
                body.put("icon", await stream.data_uri())

        if splash is None:
            body.put("splash", None)
        elif splash is not undefined.UNDEFINED:
            splash_resource = files.ensure_resource(splash)
            async with splash_resource.stream(executor=self._app.executor) as stream:
                body.put("splash", await stream.data_uri())

        if banner is None:
            body.put("banner", None)
        elif banner is not undefined.UNDEFINED:
            banner_resource = files.ensure_resource(banner)
            async with banner_resource.stream(executor=self._app.executor) as stream:
                body.put("banner", await stream.data_uri())

        raw_response = await self._request(route, json=body, reason=reason)
        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._app.entity_factory.deserialize_guild(response)

    async def delete_guild(self, guild: snowflake.SnowflakeishOr[guilds.PartialGuild]) -> None:
        route = routes.DELETE_GUILD.compile(guild=guild)
        await self._request(route)

    async def fetch_guild_channels(
        self, guild: snowflake.SnowflakeishOr[guilds.PartialGuild]
    ) -> typing.Sequence[channels.GuildChannel]:
        route = routes.GET_GUILD_CHANNELS.compile(guild=guild)
        raw_response = await self._request(route)
        response = typing.cast(data_binding.JSONArray, raw_response)
        channel_sequence = data_binding.cast_json_array(response, self._app.entity_factory.deserialize_channel)
        # Will always be guild channels unless Discord messes up severely on something!
        return typing.cast("typing.Sequence[channels.GuildChannel]", channel_sequence)

    async def create_guild_text_channel(
        self,
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
        name: str,
        *,
        position: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        topic: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        nsfw: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        rate_limit_per_user: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        permission_overwrites: undefined.UndefinedOr[
            typing.Sequence[channels.PermissionOverwrite]
        ] = undefined.UNDEFINED,
        category: undefined.UndefinedOr[snowflake.SnowflakeishOr[channels.GuildCategory]] = undefined.UNDEFINED,
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
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
        name: str,
        *,
        position: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        topic: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        nsfw: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        rate_limit_per_user: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        permission_overwrites: undefined.UndefinedOr[
            typing.Sequence[channels.PermissionOverwrite]
        ] = undefined.UNDEFINED,
        category: undefined.UndefinedOr[snowflake.SnowflakeishOr[channels.GuildCategory]] = undefined.UNDEFINED,
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
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
        name: str,
        *,
        position: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        nsfw: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        user_limit: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        bitrate: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        permission_overwrites: undefined.UndefinedOr[
            typing.Sequence[channels.PermissionOverwrite]
        ] = undefined.UNDEFINED,
        category: undefined.UndefinedOr[snowflake.SnowflakeishOr[channels.GuildCategory]] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> channels.GuildVoiceChannel:
        channel = await self._create_guild_channel(
            guild,
            name,
            channels.ChannelType.GUILD_VOICE,
            position=position,
            nsfw=nsfw,
            user_limit=user_limit,
            bitrate=bitrate,
            permission_overwrites=permission_overwrites,
            category=category,
            reason=reason,
        )
        return typing.cast(channels.GuildVoiceChannel, channel)

    async def create_guild_category(
        self,
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
        name: str,
        *,
        position: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        nsfw: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
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
            nsfw=nsfw,
            permission_overwrites=permission_overwrites,
            reason=reason,
        )
        return typing.cast(channels.GuildCategory, channel)

    async def _create_guild_channel(
        self,
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
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
        category: undefined.UndefinedOr[snowflake.SnowflakeishOr[channels.GuildCategory]] = undefined.UNDEFINED,
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
            conversion=self._app.entity_factory.serialize_permission_overwrite,
        )

        raw_response = await self._request(route, json=body, reason=reason)
        response = typing.cast(data_binding.JSONObject, raw_response)
        channel = self._app.entity_factory.deserialize_channel(response)
        return typing.cast(channels.GuildChannel, channel)

    async def reposition_channels(
        self,
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
        positions: typing.Mapping[int, typing.Union[snowflake.SnowflakeishOr[channels.GuildChannel]]],
    ) -> None:
        route = routes.POST_GUILD_CHANNELS.compile(guild=guild)
        body = [{"id": str(int(channel)), "position": pos} for pos, channel in positions.items()]
        await self._request(route, json=body)

    async def fetch_member(
        self, guild: snowflake.SnowflakeishOr[guilds.PartialGuild], user: snowflake.SnowflakeishOr[users.PartialUser],
    ) -> guilds.Member:
        route = routes.GET_GUILD_MEMBER.compile(guild=guild, user=user)
        raw_response = await self._request(route)
        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._app.entity_factory.deserialize_member(response, guild_id=snowflake.Snowflake(guild))

    def fetch_members(
        self, guild: snowflake.SnowflakeishOr[guilds.PartialGuild]
    ) -> iterators.LazyIterator[guilds.Member]:
        return special_endpoints.MemberIterator(self._app, self._request, guild)

    async def edit_member(
        self,
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
        user: snowflake.SnowflakeishOr[users.PartialUser],
        *,
        nick: undefined.UndefinedNoneOr[str] = undefined.UNDEFINED,
        roles: undefined.UndefinedOr[
            typing.Collection[snowflake.SnowflakeishOr[guilds.PartialRole]]
        ] = undefined.UNDEFINED,
        mute: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        deaf: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        voice_channel: undefined.UndefinedNoneOr[
            snowflake.SnowflakeishOr[channels.GuildVoiceChannel]
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
        guild: snowflake.SnowflakeishOr[guilds.Guild],
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
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
        user: snowflake.SnowflakeishOr[users.PartialUser],
        role: snowflake.SnowflakeishOr[guilds.PartialRole],
        *,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        route = routes.PUT_GUILD_MEMBER_ROLE.compile(guild=guild, user=user, role=role)
        await self._request(route, reason=reason)

    async def remove_role_from_member(
        self,
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
        user: snowflake.SnowflakeishOr[users.PartialUser],
        role: snowflake.SnowflakeishOr[guilds.PartialRole],
        *,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        route = routes.DELETE_GUILD_MEMBER_ROLE.compile(guild=guild, user=user, role=role)
        await self._request(route, reason=reason)

    async def kick_user(
        self,
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
        user: snowflake.SnowflakeishOr[users.PartialUser],
        *,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        route = routes.DELETE_GUILD_MEMBER.compile(guild=guild, user=user)
        await self._request(route, reason=reason)

    kick_member = kick_user

    async def ban_user(
        self,
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
        user: snowflake.SnowflakeishOr[users.PartialUser],
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
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
        user: snowflake.SnowflakeishOr[users.PartialUser],
        *,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        route = routes.DELETE_GUILD_BAN.compile(guild=guild, user=user)
        await self._request(route, reason=reason)

    unban_member = unban_user

    async def fetch_ban(
        self, guild: snowflake.SnowflakeishOr[guilds.PartialGuild], user: snowflake.SnowflakeishOr[users.PartialUser],
    ) -> guilds.GuildMemberBan:
        route = routes.GET_GUILD_BAN.compile(guild=guild, user=user)
        raw_response = await self._request(route)
        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._app.entity_factory.deserialize_guild_member_ban(response)

    async def fetch_bans(
        self, guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
    ) -> typing.Sequence[guilds.GuildMemberBan]:
        route = routes.GET_GUILD_BANS.compile(guild=guild)
        raw_response = await self._request(route)
        response = typing.cast(data_binding.JSONArray, raw_response)
        return data_binding.cast_json_array(response, self._app.entity_factory.deserialize_guild_member_ban)

    async def fetch_roles(self, guild: snowflake.SnowflakeishOr[guilds.PartialGuild],) -> typing.Sequence[guilds.Role]:
        route = routes.GET_GUILD_ROLES.compile(guild=guild)
        raw_response = await self._request(route)
        response = typing.cast(data_binding.JSONArray, raw_response)
        return data_binding.cast_json_array(
            response, self._app.entity_factory.deserialize_role, guild_id=snowflake.Snowflake(guild)
        )

    async def create_role(
        self,
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
        *,
        name: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        permissions: undefined.UndefinedOr[permissions_.Permission] = undefined.UNDEFINED,
        color: undefined.UndefinedOr[colors.Color] = undefined.UNDEFINED,
        colour: undefined.UndefinedOr[colours.Colour] = undefined.UNDEFINED,
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
        return self._app.entity_factory.deserialize_role(response, guild_id=snowflake.Snowflake(guild))

    async def reposition_roles(
        self,
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
        positions: typing.Mapping[int, snowflake.SnowflakeishOr[guilds.PartialRole]],
    ) -> None:
        route = routes.POST_GUILD_ROLES.compile(guild=guild)
        body = [{"id": str(int(role)), "position": pos} for pos, role in positions.items()]
        await self._request(route, json=body)

    async def edit_role(
        self,
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
        role: snowflake.SnowflakeishOr[guilds.PartialRole],
        *,
        name: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        permissions: undefined.UndefinedOr[permissions_.Permission] = undefined.UNDEFINED,
        color: undefined.UndefinedOr[colors.Color] = undefined.UNDEFINED,
        colour: undefined.UndefinedOr[colours.Colour] = undefined.UNDEFINED,
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
        return self._app.entity_factory.deserialize_role(response, guild_id=snowflake.Snowflake(guild))

    async def delete_role(
        self, guild: snowflake.SnowflakeishOr[guilds.PartialGuild], role: snowflake.SnowflakeishOr[guilds.PartialRole],
    ) -> None:
        route = routes.DELETE_GUILD_ROLE.compile(guild=guild, role=role)
        await self._request(route)

    async def estimate_guild_prune_count(
        self,
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
        *,
        days: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        include_roles: undefined.UndefinedOr[
            typing.Collection[snowflake.SnowflakeishOr[guilds.PartialRole]]
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
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
        *,
        days: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        compute_prune_count: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        include_roles: undefined.UndefinedOr[
            typing.Collection[snowflake.SnowflakeishOr[guilds.PartialRole]]
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
        self, guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
    ) -> typing.Sequence[voices.VoiceRegion]:
        route = routes.GET_GUILD_VOICE_REGIONS.compile(guild=guild)
        raw_response = await self._request(route)
        response = typing.cast(data_binding.JSONArray, raw_response)
        return data_binding.cast_json_array(response, self._app.entity_factory.deserialize_voice_region)

    async def fetch_guild_invites(
        self, guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
    ) -> typing.Sequence[invites.InviteWithMetadata]:
        route = routes.GET_GUILD_INVITES.compile(guild=guild)
        raw_response = await self._request(route)
        response = typing.cast(data_binding.JSONArray, raw_response)
        return data_binding.cast_json_array(response, self._app.entity_factory.deserialize_invite_with_metadata)

    async def fetch_integrations(
        self, guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
    ) -> typing.Sequence[guilds.Integration]:
        route = routes.GET_GUILD_INTEGRATIONS.compile(guild=guild)
        raw_response = await self._request(route)
        response = typing.cast(data_binding.JSONArray, raw_response)
        return data_binding.cast_json_array(response, self._app.entity_factory.deserialize_integration)

    async def edit_integration(
        self,
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
        integration: snowflake.SnowflakeishOr[guilds.Integration],
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
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
        integration: snowflake.SnowflakeishOr[guilds.Integration],
        *,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        route = routes.DELETE_GUILD_INTEGRATION.compile(guild=guild, integration=integration)
        await self._request(route, reason=reason)

    async def sync_integration(
        self,
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
        integration: snowflake.SnowflakeishOr[guilds.Integration],
    ) -> None:
        route = routes.POST_GUILD_INTEGRATION_SYNC.compile(guild=guild, integration=integration)
        await self._request(route)

    async def fetch_widget(self, guild: snowflake.SnowflakeishOr[guilds.PartialGuild]) -> guilds.GuildWidget:
        route = routes.GET_GUILD_WIDGET.compile(guild=guild)
        raw_response = await self._request(route)
        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._app.entity_factory.deserialize_guild_widget(response)

    async def edit_widget(
        self,
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
        *,
        channel: undefined.UndefinedNoneOr[snowflake.SnowflakeishOr[channels.GuildChannel]] = undefined.UNDEFINED,
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
        return self._app.entity_factory.deserialize_guild_widget(response)

    async def fetch_vanity_url(self, guild: snowflake.SnowflakeishOr[guilds.PartialGuild]) -> invites.VanityURL:
        route = routes.GET_GUILD_VANITY_URL.compile(guild=guild)
        raw_response = await self._request(route)
        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._app.entity_factory.deserialize_vanity_url(response)
