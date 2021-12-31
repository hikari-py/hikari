# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021 davfsa
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
"""Implementation of a V8 compatible REST API for Discord.

This also includes implementations designed towards providing
RESTful functionality.
"""

from __future__ import annotations

__all__: typing.List[str] = ["ClientCredentialsStrategy", "RESTApp", "RESTClientImpl"]

import asyncio
import base64
import contextlib
import copy
import datetime
import http
import logging
import math
import os
import platform
import sys
import typing

import aiohttp
import attr

from hikari import _about as about
from hikari import applications
from hikari import channels as channels_
from hikari import colors
from hikari import config
from hikari import embeds as embeds_
from hikari import emojis
from hikari import errors
from hikari import files
from hikari import guilds
from hikari import iterators
from hikari import permissions as permissions_
from hikari import snowflakes
from hikari import traits
from hikari import undefined
from hikari import urls
from hikari import users
from hikari.api import rest as rest_api
from hikari.impl import buckets as buckets_
from hikari.impl import entity_factory as entity_factory_impl
from hikari.impl import rate_limits
from hikari.impl import special_endpoints as special_endpoints_impl
from hikari.internal import data_binding
from hikari.internal import deprecation
from hikari.internal import mentions
from hikari.internal import net
from hikari.internal import routes
from hikari.internal import time
from hikari.internal import ux

if typing.TYPE_CHECKING:
    import concurrent.futures
    import types

    from hikari import audit_logs
    from hikari import commands
    from hikari import invites
    from hikari import messages as messages_
    from hikari import sessions
    from hikari import stickers
    from hikari import templates
    from hikari import voices
    from hikari import webhooks
    from hikari.api import cache as cache_api
    from hikari.api import entity_factory as entity_factory_
    from hikari.api import special_endpoints
    from hikari.interactions import base_interactions

_LOGGER: typing.Final[logging.Logger] = logging.getLogger("hikari.rest")

_APPLICATION_JSON: typing.Final[str] = "application/json"
_AUTHORIZATION_HEADER: typing.Final[str] = sys.intern("Authorization")
_HTTP_USER_AGENT: typing.Final[str] = (
    f"DiscordBot ({about.__url__}, {about.__version__}) {about.__author__} "
    f"AIOHTTP/{aiohttp.__version__} "
    f"{platform.python_implementation()}/{platform.python_version()} {platform.system()} {platform.architecture()[0]}"
)
_USER_AGENT_HEADER: typing.Final[str] = sys.intern("User-Agent")
_X_AUDIT_LOG_REASON_HEADER: typing.Final[str] = sys.intern("X-Audit-Log-Reason")
_X_RATELIMIT_BUCKET_HEADER: typing.Final[str] = sys.intern("X-RateLimit-Bucket")
_X_RATELIMIT_LIMIT_HEADER: typing.Final[str] = sys.intern("X-RateLimit-Limit")
_X_RATELIMIT_REMAINING_HEADER: typing.Final[str] = sys.intern("X-RateLimit-Remaining")
_X_RATELIMIT_RESET_AFTER_HEADER: typing.Final[str] = sys.intern("X-RateLimit-Reset-After")
_RETRY_ERROR_CODES: typing.Final[typing.Set[int]] = {500, 502, 503, 504}
_MAX_BACKOFF_DURATION: typing.Final[int] = 16


class ClientCredentialsStrategy(rest_api.TokenStrategy):
    """Strategy class for handling client credential OAuth2 authorization.

    Parameters
    ----------
    client: typing.Optional[snowflakes.SnowflakeishOr[guilds.PartialApplication]]
        Object or ID of the application this client credentials strategy should
        authorize as.
    client_secret : typing.Optional[builtins.str]
        Client secret to use when authorizing.

    Other Parameters
    ----------------
    scopes : typing.Sequence[str]
        The scopes to authorize for.
    """

    __slots__: typing.Sequence[str] = (
        "_client_id",
        "_client_secret",
        "_exception",
        "_expire_at",
        "_lock",
        "_scopes",
        "_token",
    )

    def __init__(
        self,
        client: snowflakes.SnowflakeishOr[guilds.PartialApplication],
        client_secret: str,
        *,
        scopes: typing.Sequence[typing.Union[applications.OAuth2Scope, str]] = (
            applications.OAuth2Scope.APPLICATIONS_COMMANDS_UPDATE,
            applications.OAuth2Scope.IDENTIFY,
        ),
    ) -> None:
        self._client_id = snowflakes.Snowflake(client)
        self._client_secret = client_secret
        self._exception: typing.Optional[errors.ClientHTTPResponseError] = None
        self._expire_at = 0.0
        self._lock = asyncio.Lock()
        self._scopes = tuple(scopes)
        self._token: typing.Optional[str] = None

    @property
    def client_id(self) -> snowflakes.Snowflake:
        """ID of the application this token strategy authenticates with.

        Returns
        -------
        hikari.snowflakes.Snowflake
            ID of the application this token strategy authenticates with.
        """
        return self._client_id

    @property
    def _is_expired(self) -> bool:
        return time.monotonic() >= self._expire_at

    @property
    def scopes(self) -> typing.Sequence[typing.Union[applications.OAuth2Scope, str]]:
        """Scopes this token strategy authenticates for.

        Returns
        -------
        typing.Sequence[typing.Union[hikari.applications.OAuth2Scope, builtins.str]]
            The scopes this token strategy authenticates for.
        """
        return self._scopes

    @property
    def token_type(self) -> applications.TokenType:
        return applications.TokenType.BEARER

    async def acquire(self, client: rest_api.RESTClient) -> str:
        if self._token and not self._is_expired:
            return self._token

        async with self._lock:
            if self._token and not self._is_expired:
                return self._token

            if self._exception:
                # If we don't copy the exception then python keeps adding onto the stack each time it's raised.
                raise copy.copy(self._exception) from None

            try:
                response = await client.authorize_client_credentials_token(
                    client=self._client_id, client_secret=self._client_secret, scopes=self._scopes
                )

            except errors.ClientHTTPResponseError as exc:
                if not isinstance(exc, errors.RateLimitedError):
                    # If we don't copy the exception then python keeps adding onto the stack each time it's raised.
                    self._exception = copy.copy(exc)

                raise

            # Expires in is lowered a bit in-order to lower the chance of a dead token being used.
            self._expire_at = time.monotonic() + math.floor(response.expires_in.total_seconds() * 0.99)
            self._token = f"{response.token_type} {response.access_token}"
            return self._token

    def invalidate(self, token: typing.Optional[str]) -> None:
        if not token or token == self._token:
            self._expire_at = 0.0
            self._token = None


class _RESTProvider(traits.RESTAware):
    __slots__: typing.Sequence[str] = ("_entity_factory", "_executor", "_rest")

    def __init__(
        self,
        entity_factory: typing.Callable[[], entity_factory_.EntityFactory],
        executor: typing.Optional[concurrent.futures.Executor],
        rest: typing.Callable[[], rest_api.RESTClient],
    ) -> None:
        self._entity_factory = entity_factory
        self._executor = executor
        self._rest = rest

    @property
    def entity_factory(self) -> entity_factory_.EntityFactory:
        return self._entity_factory()

    @property
    def executor(self) -> typing.Optional[concurrent.futures.Executor]:
        return self._executor

    @property
    def rest(self) -> rest_api.RESTClient:
        return self._rest()

    @property
    def http_settings(self) -> config.HTTPSettings:
        return self._rest().http_settings

    @property
    def proxy_settings(self) -> config.ProxySettings:
        return self._rest().proxy_settings


_NONE_OR_UNDEFINED: typing.Final[typing.Tuple[None, undefined.UndefinedType]] = (None, undefined.UNDEFINED)


class RESTApp(traits.ExecutorAware):
    """The base for a HTTP-only Discord application.

    This comprises of a shared TCP connector connection pool, and can have
    `RESTClientImpl` instances for specific credentials acquired
    from it.

    Parameters
    ----------
    executor : typing.Optional[concurrent.futures.Executor]
        The executor to use for blocking file IO operations. If `builtins.None`
        is passed, then the default `concurrent.futures.ThreadPoolExecutor` for
        the `asyncio.AbstractEventLoop` will be used instead.
    http_settings : typing.Optional[hikari.config.HTTPSettings]
        HTTP settings to use. Sane defaults are used if this is
        `builtins.None`.
    max_rate_limit : builtins.float
        Maximum number of seconds to sleep for when rate limited. If a rate
        limit occurs that is longer than this value, then a
        `hikari.errors.RateLimitedError` will be raised instead of waiting.

        This is provided since some endpoints may respond with non-sensible
        rate limits.

        Defaults to five minutes if unspecified.
    max_retries : typing.Optional[builtins.int]
        Maximum number of times a request will be retried if
        it fails with a `5xx` status. Defaults to 3 if set to `builtins.None`.
    proxy_settings : typing.Optional[hikari.config.ProxySettings]
        Proxy settings to use. If `builtins.None` then no proxy configuration
        will be used.
    url : typing.Optional[builtins.str]
        The base URL for the API. You can generally leave this as being
        `builtins.None` and the correct default API base URL will be generated.

    !!! note
        This event loop will be bound to a connector when the first call
        to `acquire` is made.
    """

    __slots__: typing.Sequence[str] = (
        "_executor",
        "_http_settings",
        "_max_rate_limit",
        "_max_retries",
        "_proxy_settings",
        "_url",
    )

    def __init__(
        self,
        *,
        executor: typing.Optional[concurrent.futures.Executor] = None,
        http_settings: typing.Optional[config.HTTPSettings] = None,
        max_rate_limit: float = 300,
        max_retries: int = 3,
        proxy_settings: typing.Optional[config.ProxySettings] = None,
        url: typing.Optional[str] = None,
    ) -> None:
        self._http_settings = config.HTTPSettings() if http_settings is None else http_settings
        self._proxy_settings = config.ProxySettings() if proxy_settings is None else proxy_settings
        self._executor = executor
        self._max_rate_limit = max_rate_limit
        self._max_retries = max_retries
        self._url = url

    @property
    def executor(self) -> typing.Optional[concurrent.futures.Executor]:
        return self._executor

    @property
    def http_settings(self) -> config.HTTPSettings:
        return self._http_settings

    @property
    def proxy_settings(self) -> config.ProxySettings:
        return self._proxy_settings

    @typing.overload
    def acquire(self, token: typing.Optional[rest_api.TokenStrategy] = None) -> RESTClientImpl:
        ...

    @typing.overload
    def acquire(
        self,
        token: str,
        token_type: typing.Union[str, applications.TokenType] = applications.TokenType.BEARER,
    ) -> RESTClientImpl:
        ...

    def acquire(
        self,
        token: typing.Union[str, rest_api.TokenStrategy, None] = None,
        token_type: typing.Union[str, applications.TokenType, None] = None,
    ) -> RESTClientImpl:
        """Acquire an instance of this REST client.

        !!! note
            The returned REST client should be started before it can be used,
            either by calling `RESTClientImpl.start` or by using it as an
            asynchronous context manager.

        Examples
        --------
        ```py
        rest_app = RESTApp()

        # Using the returned client as a context manager to implicitly start
        # and stop it.
        async with rest_app.acquire("A token", "Bot") as client:
            user = await client.fetch_my_user()
        ```

        Parameters
        ----------
        token : typing.Union[builtins.str, builtins.None, hikari.api.rest.TokenStrategy]
            The bot or bearer token. If no token is to be used,
            this can be undefined.
        token_type : typing.Union[builtins.str, hikari.applications.TokenType, builtins.None]
            The type of token in use. This should only be passed when `builtins.str`
            is passed for `token`, can be `"Bot"` or `"Bearer"` and will be
            defaulted to `"Bearer"` in this situation.

            This should be left as `builtins.None` when either
            `hikari.api.rest.TokenStrategy` or `builtins.None` is passed for
            `token`.

        Returns
        -------
        RESTClientImpl
            An instance of the REST client.

        Raises
        ------
        builtins.ValueError
            If `token_type` is provided when a token strategy is passed for `token`.
        """
        # Since we essentially mimic a fake App instance, we need to make a circular provider.
        # We can achieve this using a lambda. This allows the entity factory to build models that
        # are also REST-aware
        provider = _RESTProvider(lambda: entity_factory, self._executor, lambda: rest_client)
        entity_factory = entity_factory_impl.EntityFactoryImpl(provider)

        if token_type is None and isinstance(token, str):
            token_type = applications.TokenType.BEARER

        rest_client = RESTClientImpl(
            cache=None,
            entity_factory=entity_factory,
            executor=self._executor,
            http_settings=self._http_settings,
            max_rate_limit=self._max_rate_limit,
            max_retries=self._max_retries,
            proxy_settings=self._proxy_settings,
            token=token,
            token_type=token_type,
            rest_url=self._url,
        )

        return rest_client


@attr.define()
class _LiveAttributes:
    """Fields which are only present within `RESTClientImpl` while it's "alive".

    !!! note
        This must be started within an active asyncio event loop.
    """

    buckets: buckets_.RESTBucketManager = attr.field()
    client_session: aiohttp.ClientSession = attr.field()
    closed_event: asyncio.Event = attr.field()
    # We've been told in DAPI that this is per token.
    global_rate_limit: rate_limits.ManualRateLimiter = attr.field()
    tcp_connector: aiohttp.TCPConnector = attr.field()
    is_closing: bool = attr.field(default=False, init=False)

    @classmethod
    def build(
        cls, max_rate_limit: float, http_settings: config.HTTPSettings, proxy_settings: config.ProxySettings
    ) -> _LiveAttributes:
        """Build a live attributes object.

        !!! warning
            This can only be called when the current thread has an active
            asyncio loop.
        """
        # This asserts that this is called within an active event loop.
        asyncio.get_running_loop()
        tcp_connector = net.create_tcp_connector(http_settings)
        _LOGGER.log(ux.TRACE, "acquired new tcp connector")
        client_session = net.create_client_session(
            connector=tcp_connector,
            # No, this is correct. We manage closing the connector ourselves in this class.
            # This works around some other lifespan issues.
            connector_owner=False,
            http_settings=http_settings,
            raise_for_status=False,
            trust_env=proxy_settings.trust_env,
        )
        _LOGGER.log(ux.TRACE, "acquired new aiohttp client session")
        return _LiveAttributes(
            buckets=buckets_.RESTBucketManager(max_rate_limit),
            client_session=client_session,
            closed_event=asyncio.Event(),
            global_rate_limit=rate_limits.ManualRateLimiter(),
            tcp_connector=tcp_connector,
        )

    async def close(self) -> None:
        self.is_closing = True
        self.closed_event.set()
        self.buckets.close()
        self.global_rate_limit.close()
        await self.client_session.close()
        await self.tcp_connector.close()

    def still_alive(self) -> _LiveAttributes:
        """Chained method used to Check if `close` has been called before using this object's resources."""
        if self.is_closing:
            raise errors.ComponentStateConflictError("The REST client was closed mid-request")

        return self


@attr.define(auto_exc=True, repr=False, weakref_slot=False)
class _RetryRequest(RuntimeError):
    ...


class RESTClientImpl(rest_api.RESTClient):
    """Implementation of the V8-compatible Discord HTTP API.

    This manages making HTTP/1.1 requests to the API and using the entity
    factory within the passed application instance to deserialize JSON responses
    to Pythonic data classes that are used throughout this library.

    Parameters
    ----------
    entity_factory : hikari.api.entity_factory.EntityFactory
        The entity factory to use.
    executor : typing.Optional[concurrent.futures.Executor]
        The executor to use for blocking IO. Defaults to the `asyncio` thread
        pool if set to `builtins.None`.
    max_rate_limit : builtins.float
        Maximum number of seconds to sleep for when rate limited. If a rate
        limit occurs that is longer than this value, then a
        `hikari.errors.RateLimitedError` will be raised instead of waiting.

        This is provided since some endpoints may respond with non-sensible
        rate limits.
    max_retries : typing.Optional[builtins.int]
        Maximum number of times a request will be retried if
        it fails with a `5xx` status. Defaults to 3 if set to `builtins.None`.
    token : typing.Union[builtins.str, builtins.None, hikari.api.rest.TokenStrategy]
        The bot or bearer token. If no token is to be used,
        this can be undefined.
    token_type : typing.Union[builtins.str, hikari.applications.TokenType, builtins.None]
        The type of token in use. This must be passed when a `builtins.str` is
        passed for `token` but and can be `"Bot"` or `"Bearer"`.

        This should be left as `builtins.None` when either
        `hikari.api.rest.TokenStrategy` or `builtins.None` is passed for
        `token`.
    rest_url : builtins.str
        The HTTP API base URL. This can contain format-string specifiers to
        interpolate information such as API version in use.

    Raises
    ------
    builtins.ValueError
        * If `token_type` is provided when a token strategy is passed for `token`.
        * if `token_type` is left as `builtins.None` when a string is passed for `token`.
        * If the a value more than 5 is provided for `max_retries`
    """

    __slots__: typing.Sequence[str] = (
        "_cache",
        "_entity_factory",
        "_executor",
        "_http_settings",
        "_live_attributes",
        "_max_rate_limit",
        "_max_retries",
        "_proxy_settings",
        "_rest_url",
        "_token",
        "_token_type",
    )

    def __init__(
        self,
        *,
        cache: typing.Optional[cache_api.MutableCache],
        entity_factory: entity_factory_.EntityFactory,
        executor: typing.Optional[concurrent.futures.Executor],
        http_settings: config.HTTPSettings,
        max_rate_limit: float,
        max_retries: int = 3,
        proxy_settings: config.ProxySettings,
        token: typing.Union[str, None, rest_api.TokenStrategy],
        token_type: typing.Union[applications.TokenType, str, None],
        rest_url: typing.Optional[str],
    ) -> None:
        if max_retries > 5:
            raise ValueError("'max_retries' must be below or equal to 5")

        self._cache = cache
        self._entity_factory = entity_factory
        self._executor = executor
        self._http_settings = http_settings
        self._live_attributes: typing.Optional[_LiveAttributes] = None
        self._max_rate_limit = max_rate_limit
        self._max_retries = max_retries
        self._proxy_settings = proxy_settings

        self._token: typing.Union[str, rest_api.TokenStrategy, None] = None
        self._token_type: typing.Optional[str] = None
        if isinstance(token, str):
            if token_type is None:
                raise ValueError("Token type required when a str is passed for `token`")

            self._token = f"{token_type.title()} {token}"
            self._token_type = applications.TokenType(token_type.title())

        elif isinstance(token, rest_api.TokenStrategy):
            if token_type is not None:
                raise ValueError("Token type should be handled by the token strategy")

            self._token = token
            self._token_type = token.token_type

        # While passing files.URL for rest_url is not officially supported, this is still
        # casted to string here to avoid confusing issues passing a URL here could lead to.
        self._rest_url = str(rest_url) if rest_url is not None else urls.REST_API_URL

    @property
    def is_alive(self) -> bool:
        return self._live_attributes is not None

    @property
    def http_settings(self) -> config.HTTPSettings:
        return self._http_settings

    @property
    def proxy_settings(self) -> config.ProxySettings:
        return self._proxy_settings

    @property
    def entity_factory(self) -> entity_factory_.EntityFactory:
        return self._entity_factory

    @property
    def token_type(self) -> typing.Union[str, applications.TokenType, None]:
        return self._token_type

    @typing.final
    async def close(self) -> None:
        """Close the HTTP client and any open HTTP connections."""
        live_attributes = self._get_live_attributes()
        self._live_attributes = None
        await live_attributes.close()

    @typing.final
    def start(self) -> None:
        """Start the HTTP client.

        !!! note
            This must be called within an active event loop.

        Raises
        ------
        RuntimeError
            If this is called in an environment without an active event loop.
        """
        if self._live_attributes:
            raise errors.ComponentStateConflictError("Cannot start a REST Client which is already alive")

        self._live_attributes = _LiveAttributes.build(self._max_rate_limit, self._http_settings, self._proxy_settings)

    def _get_live_attributes(self) -> _LiveAttributes:
        if self._live_attributes:
            return self._live_attributes

        raise errors.ComponentStateConflictError("Cannot use an inactive REST client")

    async def __aenter__(self) -> RESTClientImpl:
        self.start()
        return self

    async def __aexit__(
        self,
        exc_type: typing.Optional[typing.Type[BaseException]],
        exc_val: typing.Optional[BaseException],
        exc_tb: typing.Optional[types.TracebackType],
    ) -> None:
        await self.close()

    # These are only included at runtime in-order to avoid the model being typed as a synchronous context manager.
    if not typing.TYPE_CHECKING:

        def __enter__(self) -> typing.NoReturn:
            # This is async only.
            cls = type(self)
            raise TypeError(f"{cls.__module__}.{cls.__qualname__} is async-only, did you mean 'async with'?") from None

        def __exit__(
            self,
            exc_type: typing.Optional[typing.Type[BaseException]],
            exc_val: typing.Optional[BaseException],
            exc_tb: typing.Optional[types.TracebackType],
        ) -> None:
            return None

    @typing.final
    async def _request(
        self,
        compiled_route: routes.CompiledRoute,
        *,
        query: typing.Optional[data_binding.StringMapBuilder] = None,
        form_builder: typing.Optional[data_binding.URLEncodedFormBuilder] = None,
        json: typing.Union[data_binding.JSONObjectBuilder, data_binding.JSONArray, None] = None,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        no_auth: bool = False,
        auth: typing.Optional[str] = None,
    ) -> typing.Union[None, data_binding.JSONObject, data_binding.JSONArray]:
        # Make a ratelimit-protected HTTP request to a JSON endpoint and expect some form
        # of JSON response.
        live_attributes = self._get_live_attributes()
        headers = data_binding.StringMapBuilder()
        headers.setdefault(_USER_AGENT_HEADER, _HTTP_USER_AGENT)

        re_authed = False
        token: typing.Optional[str] = None
        if auth:
            headers[_AUTHORIZATION_HEADER] = auth

        elif not no_auth:
            if isinstance(self._token, str):
                headers[_AUTHORIZATION_HEADER] = self._token

            elif self._token is not None:
                token = await self._token.acquire(self)
                headers[_AUTHORIZATION_HEADER] = token

        headers.put(_X_AUDIT_LOG_REASON_HEADER, reason)

        url = compiled_route.create_url(self._rest_url)

        # This is initiated the first time we hit a 5xx error to save a little memory when nothing goes wrong
        backoff: typing.Optional[rate_limits.ExponentialBackOff] = None
        retry_count = 0

        stack = contextlib.AsyncExitStack()
        while True:
            try:
                uuid = time.uuid()
                async with stack:
                    form = await form_builder.build(stack) if form_builder else None

                    await stack.enter_async_context(live_attributes.still_alive().buckets.acquire(compiled_route))
                    # Buckets not using authentication still have a global
                    # rate limit, but it is different from the token one.
                    if not no_auth:
                        await live_attributes.still_alive().global_rate_limit.acquire()

                    if _LOGGER.isEnabledFor(ux.TRACE):
                        _LOGGER.log(
                            ux.TRACE,
                            "%s %s %s\n%s",
                            uuid,
                            compiled_route.method,
                            url,
                            self._stringify_http_message(headers, json),
                        )
                        start = time.monotonic()

                    # Make the request.
                    response = await live_attributes.still_alive().client_session.request(
                        compiled_route.method,
                        url,
                        headers=headers,
                        params=query,
                        json=json,
                        data=form,
                        allow_redirects=self._http_settings.max_redirects is not None,
                        max_redirects=self._http_settings.max_redirects,
                        proxy=self._proxy_settings.url,
                        proxy_headers=self._proxy_settings.all_headers,
                    )

                    if _LOGGER.isEnabledFor(ux.TRACE):
                        time_taken = (time.monotonic() - start) * 1_000
                        _LOGGER.log(
                            ux.TRACE,
                            "%s %s %s in %sms\n%s",
                            uuid,
                            response.status,
                            response.reason,
                            time_taken,
                            self._stringify_http_message(response.headers, await response.read()),
                        )

                    # Ensure we are not rate limited, and update rate limiting headers where appropriate.
                    await self._parse_ratelimits(compiled_route, response, live_attributes)

                # Don't bother processing any further if we got NO CONTENT. There's not anything
                # to check.
                if response.status == http.HTTPStatus.NO_CONTENT:
                    return None

                # Handle the response when everything went good
                if 200 <= response.status < 300:
                    if response.content_type == _APPLICATION_JSON:
                        # Only deserializing here stops Cloudflare shenanigans messing us around.
                        return data_binding.load_json(await response.read())

                    real_url = str(response.real_url)
                    raise errors.HTTPError(f"Expected JSON [{response.content_type=}, {real_url=}]")

                # Handling 5xx errors
                if response.status in _RETRY_ERROR_CODES and retry_count < self._max_retries:
                    if backoff is None:
                        backoff = rate_limits.ExponentialBackOff(maximum=_MAX_BACKOFF_DURATION)

                    sleep_time = next(backoff)
                    _LOGGER.warning(
                        "Received status %s on request, backing off for %.2fs and retrying. Retries remaining: %s",
                        response.status,
                        sleep_time,
                        self._max_retries - retry_count,
                    )
                    retry_count += 1

                    await asyncio.sleep(sleep_time)
                    continue

                # Attempt to re-auth on UNAUTHORIZED if we are using a TokenStrategy
                can_re_auth = response.status == 401 and not (auth or no_auth or re_authed)
                if can_re_auth and isinstance(self._token, rest_api.TokenStrategy):
                    assert token is not None
                    self._token.invalidate(token)
                    token = await self._token.acquire(self)
                    headers[_AUTHORIZATION_HEADER] = token
                    re_authed = True
                    continue

                await self._handle_error_response(response)

            except _RetryRequest:
                continue

    @staticmethod
    @typing.final
    def _stringify_http_message(headers: data_binding.Headers, body: typing.Any) -> str:
        string = "\n".join(
            f"    {name}: {value}" if name != _AUTHORIZATION_HEADER else f"    {name}: **REDACTED TOKEN**"
            for name, value in headers.items()
        )

        if body is not None:
            string += "\n\n    "
            string += body.decode("ascii") if isinstance(body, bytes) else str(body)

        return string

    @staticmethod
    @typing.final
    async def _handle_error_response(response: aiohttp.ClientResponse) -> typing.NoReturn:
        raise await net.generate_error_response(response)

    @typing.final
    async def _parse_ratelimits(
        self, compiled_route: routes.CompiledRoute, response: aiohttp.ClientResponse, live_attributes: _LiveAttributes
    ) -> None:
        # Handle rate limiting.
        resp_headers = response.headers
        limit = int(resp_headers.get(_X_RATELIMIT_LIMIT_HEADER, "1"))
        remaining = int(resp_headers.get(_X_RATELIMIT_REMAINING_HEADER, "1"))
        bucket = resp_headers.get(_X_RATELIMIT_BUCKET_HEADER)
        reset_after = float(resp_headers.get(_X_RATELIMIT_RESET_AFTER_HEADER, "0"))

        if bucket:
            live_attributes.still_alive().buckets.update_rate_limits(
                compiled_route=compiled_route,
                bucket_header=bucket,
                remaining_header=remaining,
                limit_header=limit,
                reset_after=reset_after,
            )

        if response.status != http.HTTPStatus.TOO_MANY_REQUESTS:
            return

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
        # Seems Discord may raise this on some other undocumented cases, which
        # is nice of them. Apparently some dude spamming slurs in the Python
        # guild via a leaked webhook URL made people's clients exhibit this
        # behaviour.
        #
        # If we get ratelimited when running more than one bot under the same token,
        # or if the ratelimiting logic goes wrong, we will get a 429 and expect the
        # "remaining" header to be zeroed, or even negative as I don't trust that there
        # isn't some weird edge case here somewhere in Discord's implementation.
        # We can safely retry if this happens as acquiring the bucket will handle
        # this.
        if remaining <= 0:
            _LOGGER.warning(
                "rate limited on bucket %s, maybe you are running more than one bot on this token? Retrying request...",
                bucket,
            )
            raise _RetryRequest

        if response.content_type != _APPLICATION_JSON:
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
        body_retry_after = float(body["retry_after"])

        if body.get("global", False) is True:
            _LOGGER.error(
                "rate limited on the global bucket. You should consider lowering the number of requests you make or "
                "contacting Discord to raise this limit. Backing off and retrying request..."
            )
            live_attributes.still_alive().global_rate_limit.throttle(body_retry_after)
            raise _RetryRequest

        # If the values are within 20% of each other by relativistic tolerance, it is probably
        # safe to retry the request, as they are likely the same value just with some
        # measuring difference. 20% was used as a rounded figure.
        if math.isclose(body_retry_after, reset_after, rel_tol=0.20):
            _LOGGER.error("rate limited on a sub bucket on bucket %s, but it is safe to retry", bucket)
            raise _RetryRequest

        raise errors.RateLimitedError(
            url=str(response.real_url),
            route=compiled_route,
            headers=response.headers,
            raw_body=body,
            retry_after=body_retry_after,
        )

    async def fetch_channel(
        self, channel: snowflakes.SnowflakeishOr[channels_.PartialChannel]
    ) -> channels_.PartialChannel:
        route = routes.GET_CHANNEL.compile(channel=channel)
        response = await self._request(route)
        assert isinstance(response, dict)
        result = self._entity_factory.deserialize_channel(response)

        if self._cache and isinstance(result, channels_.DMChannel):
            self._cache.set_dm_channel_id(result.recipient.id, result.id)

        return result

    async def edit_channel(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.GuildChannel],
        /,
        *,
        name: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        position: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        topic: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        nsfw: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        bitrate: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        video_quality_mode: undefined.UndefinedOr[typing.Union[channels_.VideoQualityMode, int]] = undefined.UNDEFINED,
        user_limit: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        rate_limit_per_user: undefined.UndefinedOr[time.Intervalish] = undefined.UNDEFINED,
        region: undefined.UndefinedNoneOr[typing.Union[voices.VoiceRegion, str]] = undefined.UNDEFINED,
        permission_overwrites: undefined.UndefinedOr[
            typing.Sequence[channels_.PermissionOverwrite]
        ] = undefined.UNDEFINED,
        parent_category: undefined.UndefinedOr[
            snowflakes.SnowflakeishOr[channels_.GuildCategory]
        ] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> channels_.PartialChannel:
        route = routes.PATCH_CHANNEL.compile(channel=channel)
        body = data_binding.JSONObjectBuilder()
        body.put("name", name)
        body.put("position", position)
        body.put("topic", topic)
        body.put("nsfw", nsfw)
        body.put("bitrate", bitrate)
        body.put("video_quality_mode", video_quality_mode)
        body.put("user_limit", user_limit)
        body.put("rate_limit_per_user", rate_limit_per_user, conversion=time.timespan_to_int)
        body.put("rtc_region", region, conversion=str)
        body.put_snowflake("parent_id", parent_category)
        body.put_array(
            "permission_overwrites",
            permission_overwrites,
            conversion=self._entity_factory.serialize_permission_overwrite,
        )

        response = await self._request(route, json=body, reason=reason)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_channel(response)

    async def follow_channel(
        self,
        news_channel: snowflakes.SnowflakeishOr[channels_.GuildNewsChannel],
        target_channel: snowflakes.SnowflakeishOr[channels_.GuildChannel],
        *,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> channels_.ChannelFollow:
        route = routes.POST_CHANNEL_FOLLOWERS.compile(channel=news_channel)
        body = data_binding.JSONObjectBuilder()
        body.put_snowflake("webhook_channel_id", target_channel)

        response = await self._request(route, json=body, reason=reason)

        assert isinstance(response, dict)
        return self._entity_factory.deserialize_channel_follow(response)

    async def delete_channel(
        self, channel: snowflakes.SnowflakeishOr[channels_.PartialChannel]
    ) -> channels_.PartialChannel:
        route = routes.DELETE_CHANNEL.compile(channel=channel)
        response = await self._request(route)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_channel(response)

    async def edit_my_voice_state(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        channel: snowflakes.SnowflakeishOr[channels_.GuildStageChannel],
        *,
        suppress: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        request_to_speak: typing.Union[undefined.UndefinedType, bool, datetime.datetime] = undefined.UNDEFINED,
    ) -> None:
        route = routes.PATCH_MY_GUILD_VOICE_STATE.compile(guild=guild)
        body = data_binding.JSONObjectBuilder()
        body.put_snowflake("channel_id", channel)
        body.put("suppress", suppress)

        if isinstance(request_to_speak, datetime.datetime):
            body.put("request_to_speak_timestamp", request_to_speak.isoformat())

        elif request_to_speak is True:
            body.put("request_to_speak_timestamp", time.utc_datetime().isoformat())

        elif request_to_speak is False:
            body.put("request_to_speak_timestamp", None)

        await self._request(route, json=body)

    async def edit_voice_state(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        channel: snowflakes.SnowflakeishOr[channels_.GuildStageChannel],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        *,
        suppress: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
    ) -> None:
        route = routes.PATCH_GUILD_VOICE_STATE.compile(guild=guild, user=user)
        body = data_binding.JSONObjectBuilder()
        body.put_snowflake("channel_id", channel)
        body.put("suppress", suppress)
        await self._request(route, json=body)

    async def edit_permission_overwrites(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.GuildChannel],
        target: typing.Union[
            snowflakes.Snowflakeish, users.PartialUser, guilds.PartialRole, channels_.PermissionOverwrite
        ],
        *,
        target_type: undefined.UndefinedOr[typing.Union[channels_.PermissionOverwriteType, int]] = undefined.UNDEFINED,
        allow: undefined.UndefinedOr[permissions_.Permissions] = undefined.UNDEFINED,
        deny: undefined.UndefinedOr[permissions_.Permissions] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        if target_type is undefined.UNDEFINED:
            if isinstance(target, users.PartialUser):
                target_type = channels_.PermissionOverwriteType.MEMBER
            elif isinstance(target, guilds.Role):
                target_type = channels_.PermissionOverwriteType.ROLE
            elif isinstance(target, channels_.PermissionOverwrite):
                target_type = target.type
            else:
                raise TypeError(
                    "Cannot determine the type of the target to update. Try specifying 'target_type' manually."
                )

        target = target.id if isinstance(target, channels_.PermissionOverwrite) else target
        route = routes.PUT_CHANNEL_PERMISSIONS.compile(channel=channel, overwrite=target)
        body = data_binding.JSONObjectBuilder()
        body.put("type", target_type)
        body.put("allow", allow)
        body.put("deny", deny)
        await self._request(route, json=body, reason=reason)

    async def delete_permission_overwrite(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.GuildChannel],
        target: typing.Union[
            channels_.PermissionOverwrite, guilds.PartialRole, users.PartialUser, snowflakes.Snowflakeish
        ],
    ) -> None:
        route = routes.DELETE_CHANNEL_PERMISSIONS.compile(channel=channel, overwrite=target)
        await self._request(route)

    async def fetch_channel_invites(
        self, channel: snowflakes.SnowflakeishOr[channels_.GuildChannel]
    ) -> typing.Sequence[invites.InviteWithMetadata]:
        route = routes.GET_CHANNEL_INVITES.compile(channel=channel)
        response = await self._request(route)
        assert isinstance(response, list)
        return [self._entity_factory.deserialize_invite_with_metadata(invite_payload) for invite_payload in response]

    async def create_invite(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.GuildChannel],
        *,
        max_age: undefined.UndefinedOr[time.Intervalish] = undefined.UNDEFINED,
        max_uses: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        temporary: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        unique: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        target_type: undefined.UndefinedOr[invites.TargetType] = undefined.UNDEFINED,
        target_user: undefined.UndefinedOr[snowflakes.SnowflakeishOr[users.PartialUser]] = undefined.UNDEFINED,
        target_application: undefined.UndefinedOr[
            snowflakes.SnowflakeishOr[guilds.PartialApplication]
        ] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> invites.InviteWithMetadata:
        route = routes.POST_CHANNEL_INVITES.compile(channel=channel)
        body = data_binding.JSONObjectBuilder()
        body.put("max_age", max_age, conversion=time.timespan_to_int)
        body.put("max_uses", max_uses)
        body.put("temporary", temporary)
        body.put("unique", unique)
        body.put("target_type", target_type)
        body.put_snowflake("target_user_id", target_user)
        body.put_snowflake("target_application_id", target_application)
        response = await self._request(route, json=body, reason=reason)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_invite_with_metadata(response)

    def trigger_typing(
        self, channel: snowflakes.SnowflakeishOr[channels_.TextableChannel]
    ) -> special_endpoints.TypingIndicator:
        return special_endpoints_impl.TypingIndicator(
            request_call=self._request, channel=channel, rest_closed_event=self._get_live_attributes().closed_event
        )

    async def fetch_pins(
        self, channel: snowflakes.SnowflakeishOr[channels_.TextableChannel]
    ) -> typing.Sequence[messages_.Message]:
        route = routes.GET_CHANNEL_PINS.compile(channel=channel)
        response = await self._request(route)
        assert isinstance(response, list)
        return [self._entity_factory.deserialize_message(message_pl) for message_pl in response]

    async def pin_message(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.TextableChannel],
        message: snowflakes.SnowflakeishOr[messages_.PartialMessage],
    ) -> None:
        route = routes.PUT_CHANNEL_PINS.compile(channel=channel, message=message)
        await self._request(route)

    async def unpin_message(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.TextableChannel],
        message: snowflakes.SnowflakeishOr[messages_.PartialMessage],
    ) -> None:
        route = routes.DELETE_CHANNEL_PIN.compile(channel=channel, message=message)
        await self._request(route)

    def fetch_messages(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.TextableChannel],
        *,
        before: undefined.UndefinedOr[snowflakes.SearchableSnowflakeishOr[snowflakes.Unique]] = undefined.UNDEFINED,
        after: undefined.UndefinedOr[snowflakes.SearchableSnowflakeishOr[snowflakes.Unique]] = undefined.UNDEFINED,
        around: undefined.UndefinedOr[snowflakes.SearchableSnowflakeishOr[snowflakes.Unique]] = undefined.UNDEFINED,
    ) -> iterators.LazyIterator[messages_.Message]:
        if undefined.count(before, after, around) < 2:
            raise TypeError("Expected no kwargs, or a maximum of one of 'before', 'after', 'around'")

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

        return special_endpoints_impl.MessageIterator(
            entity_factory=self._entity_factory,
            request_call=self._request,
            channel=channel,
            direction=direction,
            first_id=timestamp,
        )

    async def fetch_message(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.TextableChannel],
        message: snowflakes.SnowflakeishOr[messages_.PartialMessage],
    ) -> messages_.Message:
        route = routes.GET_CHANNEL_MESSAGE.compile(channel=channel, message=message)
        response = await self._request(route)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_message(response)

    async def _create_message(
        self,
        route: routes.CompiledRoute,
        body: data_binding.JSONObjectBuilder,
        query: typing.Optional[data_binding.StringMapBuilder] = None,
        *,
        no_auth: bool = False,
        content: undefined.UndefinedOr[typing.Any],
        attachment: undefined.UndefinedOr[files.Resourceish],
        attachments: undefined.UndefinedOr[typing.Sequence[files.Resourceish]],
        component: undefined.UndefinedOr[special_endpoints.ComponentBuilder] = undefined.UNDEFINED,
        components: undefined.UndefinedOr[typing.Sequence[special_endpoints.ComponentBuilder]] = undefined.UNDEFINED,
        embed: undefined.UndefinedOr[embeds_.Embed],
        embeds: undefined.UndefinedOr[typing.Sequence[embeds_.Embed]],
        tts: undefined.UndefinedOr[bool],
        mentions_everyone: undefined.UndefinedOr[bool],
        mentions_reply: undefined.UndefinedOr[bool],
        user_mentions: undefined.UndefinedOr[typing.Union[snowflakes.SnowflakeishSequence[users.PartialUser], bool]],
        role_mentions: undefined.UndefinedOr[typing.Union[snowflakes.SnowflakeishSequence[guilds.PartialRole], bool]],
    ) -> messages_.Message:
        if not undefined.any_undefined(attachment, attachments):
            raise ValueError("You may only specify one of 'attachment' or 'attachments', not both")

        if not undefined.any_undefined(component, components):
            raise ValueError("You may only specify one of 'component' or 'components', not both")

        if not undefined.any_undefined(embed, embeds):
            raise ValueError("You may only specify one of 'embed' or 'embeds', not both")

        if attachments is not undefined.UNDEFINED and not isinstance(attachments, typing.Collection):
            raise TypeError(
                "You passed a non-collection to 'attachments', but this expects a collection. Maybe you meant to "
                "use 'attachment' (singular) instead?"
            )

        if components is not undefined.UNDEFINED and not isinstance(components, typing.Collection):
            raise TypeError(
                "You passed a non-collection to 'components', but this expects a collection. Maybe you meant to "
                "use 'component' (singular) instead?"
            )

        if embeds not in _NONE_OR_UNDEFINED and not isinstance(embeds, typing.Collection):
            raise TypeError(
                "You passed a non-collection to 'embeds', but this expects a collection. Maybe you meant to "
                "use 'embed' (singular) instead?"
            )

        if undefined.all_undefined(embed, embeds) and isinstance(content, embeds_.Embed):
            # Syntactic sugar, common mistake to accidentally send an embed
            # as the content, so lets detect this and fix it for the user.
            embed = content
            content = undefined.UNDEFINED

        elif undefined.all_undefined(attachment, attachments) and isinstance(
            content, (files.Resource, files.RAWISH_TYPES, os.PathLike)
        ):
            # Syntactic sugar, common mistake to accidentally send an attachment
            # as the content, so lets detect this and fix it for the user. This
            # will still then work with normal implicit embed attachments as
            # we work this out later.
            attachment = content
            content = undefined.UNDEFINED

        final_attachments: typing.List[files.Resource[files.AsyncReader]] = []
        if attachment is not undefined.UNDEFINED:
            final_attachments.append(files.ensure_resource(attachment))
        if attachments is not undefined.UNDEFINED:
            final_attachments.extend([files.ensure_resource(a) for a in attachments])

        if component is not undefined.UNDEFINED:
            body.put("components", [component.build()])

        elif components is not undefined.UNDEFINED:
            body.put("components", [component.build() for component in components])

        serialized_embeds: undefined.UndefinedOr[data_binding.JSONArray] = undefined.UNDEFINED

        if embed is not undefined.UNDEFINED:
            embed_payload, embed_attachments = self._entity_factory.serialize_embed(embed)
            final_attachments.extend(embed_attachments)
            serialized_embeds = [embed_payload]
        elif embeds is not undefined.UNDEFINED:
            serialized_embeds = []
            for embed in embeds:
                embed_payload, embed_attachments = self._entity_factory.serialize_embed(embed)
                final_attachments.extend(embed_attachments)
                serialized_embeds.append(embed_payload)

        body.put(
            "allowed_mentions",
            mentions.generate_allowed_mentions(mentions_everyone, mentions_reply, user_mentions, role_mentions),
        )
        body.put("content", content, conversion=str)
        body.put("tts", tts)
        body.put("embeds", serialized_embeds)

        if final_attachments:
            form = data_binding.URLEncodedFormBuilder(executor=self._executor)
            form.add_field("payload_json", data_binding.dump_json(body), content_type=_APPLICATION_JSON)

            for i, attachment in enumerate(final_attachments):
                form.add_resource(f"file{i}", attachment)

            response = await self._request(route, form_builder=form, query=query, no_auth=no_auth)
        else:
            response = await self._request(route, json=body, query=query, no_auth=no_auth)

        assert isinstance(response, dict)
        return self._entity_factory.deserialize_message(response)

    async def create_message(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.TextableChannel],
        content: undefined.UndefinedOr[typing.Any] = undefined.UNDEFINED,
        *,
        attachment: undefined.UndefinedOr[files.Resourceish] = undefined.UNDEFINED,
        attachments: undefined.UndefinedOr[typing.Sequence[files.Resourceish]] = undefined.UNDEFINED,
        component: undefined.UndefinedOr[special_endpoints.ComponentBuilder] = undefined.UNDEFINED,
        components: undefined.UndefinedOr[typing.Sequence[special_endpoints.ComponentBuilder]] = undefined.UNDEFINED,
        embed: undefined.UndefinedOr[embeds_.Embed] = undefined.UNDEFINED,
        embeds: undefined.UndefinedOr[typing.Sequence[embeds_.Embed]] = undefined.UNDEFINED,
        tts: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        nonce: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        reply: undefined.UndefinedOr[snowflakes.SnowflakeishOr[messages_.PartialMessage]] = undefined.UNDEFINED,
        mentions_everyone: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        mentions_reply: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        user_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[users.PartialUser], bool]
        ] = undefined.UNDEFINED,
        role_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[guilds.PartialRole], bool]
        ] = undefined.UNDEFINED,
    ) -> messages_.Message:
        route = routes.POST_CHANNEL_MESSAGES.compile(channel=channel)
        body = data_binding.JSONObjectBuilder()
        body.put("nonce", nonce)
        body.put("message_reference", reply, conversion=lambda m: {"message_id": str(int(m))})
        return await self._create_message(
            route,
            body,
            content=content,
            attachment=attachment,
            attachments=attachments,
            component=component,
            components=components,
            embed=embed,
            embeds=embeds,
            tts=tts,
            mentions_everyone=mentions_everyone,
            mentions_reply=mentions_reply,
            user_mentions=user_mentions,
            role_mentions=role_mentions,
        )

    async def crosspost_message(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.GuildNewsChannel],
        message: snowflakes.SnowflakeishOr[messages_.PartialMessage],
    ) -> messages_.Message:
        route = routes.POST_CHANNEL_CROSSPOST.compile(channel=channel, message=message)

        response = await self._request(route)

        assert isinstance(response, dict)
        return self._entity_factory.deserialize_message(response)

    async def _edit_message(  # noqa: C901 - Function too complex
        self,
        route: routes.CompiledRoute,
        body: data_binding.JSONObjectBuilder,
        *,
        no_auth: bool = False,
        content: undefined.UndefinedOr[typing.Any],
        attachment: undefined.UndefinedOr[files.Resourceish],
        attachments: undefined.UndefinedOr[typing.Sequence[files.Resourceish]],
        component: undefined.UndefinedNoneOr[special_endpoints.ComponentBuilder] = undefined.UNDEFINED,
        components: undefined.UndefinedNoneOr[
            typing.Sequence[special_endpoints.ComponentBuilder]
        ] = undefined.UNDEFINED,
        embed: undefined.UndefinedNoneOr[embeds_.Embed],
        embeds: undefined.UndefinedNoneOr[typing.Sequence[embeds_.Embed]],
        replace_attachments: bool,
        mentions_everyone: undefined.UndefinedOr[bool],
        mentions_reply: undefined.UndefinedOr[bool],
        user_mentions: undefined.UndefinedOr[typing.Union[snowflakes.SnowflakeishSequence[users.PartialUser], bool]],
        role_mentions: undefined.UndefinedOr[typing.Union[snowflakes.SnowflakeishSequence[guilds.PartialRole], bool]],
    ) -> messages_.Message:
        if not undefined.any_undefined(attachment, attachments):
            raise ValueError("You may only specify one of 'attachment' or 'attachments', not both")

        if not undefined.any_undefined(component, components):
            raise ValueError("You may only specify one of 'component' or 'components', not both")

        if not undefined.any_undefined(embed, embeds):
            raise ValueError("You may only specify one of 'embed' or 'embeds', not both")

        if attachments is not undefined.UNDEFINED and not isinstance(attachments, typing.Collection):
            raise TypeError(
                "You passed a non-collection to 'attachments', but this expects a collection. Maybe you meant to "
                "use 'attachment' (singular) instead?"
            )

        if components is not undefined.UNDEFINED and not isinstance(components, typing.Collection):
            raise TypeError(
                "You passed a non-collection to 'components', but this expects a collection. Maybe you meant to "
                "use 'component' (singular) instead?"
            )

        if embeds not in _NONE_OR_UNDEFINED and not isinstance(embeds, typing.Collection):
            raise TypeError(
                "You passed a non-collection to 'embeds', but this expects a collection. Maybe you meant to "
                "use 'embed' (singular) instead?"
            )

        if not undefined.all_undefined(mentions_everyone, mentions_reply, user_mentions, role_mentions):
            body.put(
                "allowed_mentions",
                mentions.generate_allowed_mentions(mentions_everyone, mentions_reply, user_mentions, role_mentions),
            )

        if embed is undefined.UNDEFINED and isinstance(content, embeds_.Embed):
            # Syntactic sugar, common mistake to accidentally send an embed
            # as the content, so lets detect this and fix it for the user.
            embed = content
            content = undefined.UNDEFINED
        elif undefined.all_undefined(attachment, attachments) and isinstance(
            content, (files.Resource, files.RAWISH_TYPES, os.PathLike)
        ):
            # Syntactic sugar, common mistake to accidentally send an attachment
            # as the content, so lets detect this and fix it for the user. This
            # will still then work with normal implicit embed attachments as
            # we work this out later.
            attachment = content
            content = undefined.UNDEFINED

        if content is not None:
            body.put("content", content, conversion=str)
        else:
            body.put("content", None)

        final_attachments: typing.List[files.Resource[files.AsyncReader]] = []
        if attachment is not undefined.UNDEFINED:
            final_attachments.append(files.ensure_resource(attachment))
        if attachments is not undefined.UNDEFINED:
            final_attachments.extend([files.ensure_resource(a) for a in attachments])

        serialized_components: typing.Optional[typing.List[data_binding.JSONObject]] = None
        if component is not undefined.UNDEFINED:
            if component is not None:
                serialized_components = [component.build()]

            body.put("components", serialized_components)

        elif components is not undefined.UNDEFINED:
            if components is not None:
                serialized_components = [component.build() for component in components]

            body.put("components", serialized_components)

        serialized_embeds: data_binding.JSONArray = []
        update_embeds = False
        if embed is not undefined.UNDEFINED:
            update_embeds = True
            if embed is not None:
                embed_payload, embed_attachments = self._entity_factory.serialize_embed(embed)
                serialized_embeds.append(embed_payload)
                final_attachments.extend(embed_attachments)
        elif embeds is not undefined.UNDEFINED:
            update_embeds = True
            if embeds is not None:
                for embed in embeds:
                    embed_payload, embed_attachments = self._entity_factory.serialize_embed(embed)
                    serialized_embeds.append(embed_payload)
                    final_attachments.extend(embed_attachments)

        if update_embeds:
            body.put("embeds", serialized_embeds)

        if replace_attachments:
            body.put("attachments", None)

        if final_attachments:
            form_builder = data_binding.URLEncodedFormBuilder(executor=self._executor)
            form_builder.add_field("payload_json", data_binding.dump_json(body), content_type=_APPLICATION_JSON)

            for i, attachment in enumerate(final_attachments):
                form_builder.add_resource(f"file{i}", attachment)

            response = await self._request(route, form_builder=form_builder, no_auth=no_auth)
        else:
            response = await self._request(route, json=body, no_auth=no_auth)

        assert isinstance(response, dict)
        return self._entity_factory.deserialize_message(response)

    async def edit_message(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.TextableChannel],
        message: snowflakes.SnowflakeishOr[messages_.PartialMessage],
        content: undefined.UndefinedOr[typing.Any] = undefined.UNDEFINED,
        *,
        attachment: undefined.UndefinedOr[files.Resourceish] = undefined.UNDEFINED,
        attachments: undefined.UndefinedOr[typing.Sequence[files.Resourceish]] = undefined.UNDEFINED,
        component: undefined.UndefinedNoneOr[special_endpoints.ComponentBuilder] = undefined.UNDEFINED,
        components: undefined.UndefinedNoneOr[
            typing.Sequence[special_endpoints.ComponentBuilder]
        ] = undefined.UNDEFINED,
        embed: undefined.UndefinedNoneOr[embeds_.Embed] = undefined.UNDEFINED,
        embeds: undefined.UndefinedNoneOr[typing.Sequence[embeds_.Embed]] = undefined.UNDEFINED,
        replace_attachments: bool = False,
        mentions_everyone: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        mentions_reply: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        user_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[users.PartialUser], bool]
        ] = undefined.UNDEFINED,
        role_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[guilds.PartialRole], bool]
        ] = undefined.UNDEFINED,
        flags: undefined.UndefinedOr[messages_.MessageFlag] = undefined.UNDEFINED,
    ) -> messages_.Message:
        route = routes.PATCH_CHANNEL_MESSAGE.compile(channel=channel, message=message)
        body = data_binding.JSONObjectBuilder()
        body.put("flags", flags)
        return await self._edit_message(
            route,
            body,
            content=content,
            attachment=attachment,
            attachments=attachments,
            component=component,
            components=components,
            embed=embed,
            embeds=embeds,
            replace_attachments=replace_attachments,
            mentions_everyone=mentions_everyone,
            mentions_reply=mentions_reply,
            user_mentions=user_mentions,
            role_mentions=role_mentions,
        )

    async def delete_message(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.TextableChannel],
        message: snowflakes.SnowflakeishOr[messages_.PartialMessage],
    ) -> None:
        route = routes.DELETE_CHANNEL_MESSAGE.compile(channel=channel, message=message)
        await self._request(route)

    async def delete_messages(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.TextableChannel],
        messages: typing.Union[
            snowflakes.SnowflakeishOr[messages_.PartialMessage],
            snowflakes.SnowflakeishIterable[messages_.PartialMessage],
        ],
        /,
        *other_messages: snowflakes.SnowflakeishOr[messages_.PartialMessage],
    ) -> None:
        route = routes.POST_DELETE_CHANNEL_MESSAGES_BULK.compile(channel=channel)

        pending: typing.List[snowflakes.SnowflakeishOr[messages_.PartialMessage]] = []
        deleted: typing.List[snowflakes.SnowflakeishOr[messages_.PartialMessage]] = []

        if isinstance(messages, typing.Iterable):  # Syntactic sugar. Allows to use iterables
            pending.extend(messages)

        else:
            pending.append(messages)

        # This maintains the order in-order to keep a predictable deletion order.
        pending.extend(other_messages)

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
                    message = pending[0]
                    try:
                        await self.delete_message(channel, message)
                    except errors.NotFoundError as exc:
                        # If the message is not found then this error should be suppressed
                        # to keep consistency with how the bulk delete endpoint functions.
                        if exc.code != 10008:  # Unknown Message
                            raise

                    deleted.append(message)

                else:
                    body = data_binding.JSONObjectBuilder()
                    chunk = pending[:100]
                    body.put_snowflake_array("messages", chunk)
                    await self._request(route, json=body)
                    deleted += chunk

                pending = pending[100:]
            except Exception as ex:
                raise errors.BulkDeleteError(deleted, pending) from ex

    @staticmethod
    def _transform_emoji_to_url_format(
        emoji: typing.Union[str, emojis.Emoji],
        emoji_id: undefined.UndefinedOr[snowflakes.SnowflakeishOr[emojis.CustomEmoji]],
        /,
    ) -> str:
        if isinstance(emoji, emojis.Emoji):
            if emoji_id is not undefined.UNDEFINED:
                raise ValueError("emoji_id shouldn't be passed when an Emoji object is passed for emoji")

            return emoji.url_name

        if emoji_id is not undefined.UNDEFINED:
            return f"{emoji}:{snowflakes.Snowflake(emoji_id)}"

        return emoji

    async def add_reaction(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.TextableChannel],
        message: snowflakes.SnowflakeishOr[messages_.PartialMessage],
        emoji: typing.Union[str, emojis.Emoji],
        emoji_id: undefined.UndefinedOr[snowflakes.SnowflakeishOr[emojis.CustomEmoji]] = undefined.UNDEFINED,
    ) -> None:
        route = routes.PUT_MY_REACTION.compile(
            emoji=self._transform_emoji_to_url_format(emoji, emoji_id),
            channel=channel,
            message=message,
        )
        await self._request(route)

    async def delete_my_reaction(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.TextableChannel],
        message: snowflakes.SnowflakeishOr[messages_.PartialMessage],
        emoji: typing.Union[str, emojis.Emoji],
        emoji_id: undefined.UndefinedOr[snowflakes.SnowflakeishOr[emojis.CustomEmoji]] = undefined.UNDEFINED,
    ) -> None:
        route = routes.DELETE_MY_REACTION.compile(
            emoji=self._transform_emoji_to_url_format(emoji, emoji_id),
            channel=channel,
            message=message,
        )
        await self._request(route)

    async def delete_all_reactions_for_emoji(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.TextableChannel],
        message: snowflakes.SnowflakeishOr[messages_.PartialMessage],
        emoji: typing.Union[str, emojis.Emoji],
        emoji_id: undefined.UndefinedOr[snowflakes.SnowflakeishOr[emojis.CustomEmoji]] = undefined.UNDEFINED,
    ) -> None:
        route = routes.DELETE_REACTION_EMOJI.compile(
            emoji=self._transform_emoji_to_url_format(emoji, emoji_id),
            channel=channel,
            message=message,
        )
        await self._request(route)

    async def delete_reaction(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.TextableChannel],
        message: snowflakes.SnowflakeishOr[messages_.PartialMessage],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        emoji: typing.Union[str, emojis.Emoji],
        emoji_id: undefined.UndefinedOr[snowflakes.SnowflakeishOr[emojis.CustomEmoji]] = undefined.UNDEFINED,
    ) -> None:
        route = routes.DELETE_REACTION_USER.compile(
            emoji=self._transform_emoji_to_url_format(emoji, emoji_id),
            channel=channel,
            message=message,
            user=user,
        )
        await self._request(route)

    async def delete_all_reactions(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.TextableChannel],
        message: snowflakes.SnowflakeishOr[messages_.PartialMessage],
    ) -> None:
        route = routes.DELETE_ALL_REACTIONS.compile(channel=channel, message=message)
        await self._request(route)

    def fetch_reactions_for_emoji(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.TextableChannel],
        message: snowflakes.SnowflakeishOr[messages_.PartialMessage],
        emoji: typing.Union[str, emojis.Emoji],
        emoji_id: undefined.UndefinedOr[snowflakes.SnowflakeishOr[emojis.CustomEmoji]] = undefined.UNDEFINED,
    ) -> iterators.LazyIterator[users.User]:
        return special_endpoints_impl.ReactorIterator(
            entity_factory=self._entity_factory,
            request_call=self._request,
            channel=channel,
            message=message,
            emoji=self._transform_emoji_to_url_format(emoji, emoji_id),
        )

    async def create_webhook(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.WebhookChannelT],
        name: str,
        *,
        avatar: undefined.UndefinedOr[files.Resourceish] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> webhooks.IncomingWebhook:
        route = routes.POST_CHANNEL_WEBHOOKS.compile(channel=channel)
        body = data_binding.JSONObjectBuilder()
        body.put("name", name)

        if avatar is not undefined.UNDEFINED:
            avatar_resource = files.ensure_resource(avatar)
            async with avatar_resource.stream(executor=self._executor) as stream:
                body.put("avatar", await stream.data_uri())

        response = await self._request(route, json=body, reason=reason)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_incoming_webhook(response)

    async def fetch_webhook(
        self,
        webhook: snowflakes.SnowflakeishOr[webhooks.PartialWebhook],
        *,
        token: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> webhooks.PartialWebhook:
        if token is undefined.UNDEFINED:
            route = routes.GET_WEBHOOK.compile(webhook=webhook)
            no_auth = False
        else:
            route = routes.GET_WEBHOOK_WITH_TOKEN.compile(webhook=webhook, token=token)
            no_auth = True

        response = await self._request(route, no_auth=no_auth)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_webhook(response)

    async def fetch_channel_webhooks(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.WebhookChannelT],
    ) -> typing.Sequence[webhooks.PartialWebhook]:
        route = routes.GET_CHANNEL_WEBHOOKS.compile(channel=channel)
        response = await self._request(route)
        assert isinstance(response, list)
        return [self._entity_factory.deserialize_webhook(webhook_pl) for webhook_pl in response]

    async def fetch_guild_webhooks(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
    ) -> typing.Sequence[webhooks.PartialWebhook]:
        route = routes.GET_GUILD_WEBHOOKS.compile(guild=guild)
        response = await self._request(route)
        assert isinstance(response, list)
        return [self._entity_factory.deserialize_webhook(webhook_payload) for webhook_payload in response]

    async def edit_webhook(
        self,
        webhook: snowflakes.SnowflakeishOr[webhooks.PartialWebhook],
        *,
        token: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        name: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        avatar: undefined.UndefinedNoneOr[files.Resourceish] = undefined.UNDEFINED,
        channel: undefined.UndefinedOr[snowflakes.SnowflakeishOr[channels_.WebhookChannelT]] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> webhooks.PartialWebhook:
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

        response = await self._request(route, json=body, reason=reason, no_auth=no_auth)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_webhook(response)

    async def delete_webhook(
        self,
        webhook: snowflakes.SnowflakeishOr[webhooks.PartialWebhook],
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
        webhook: typing.Union[webhooks.ExecutableWebhook, snowflakes.Snowflakeish],
        token: str,
        content: undefined.UndefinedOr[typing.Any] = undefined.UNDEFINED,
        *,
        username: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        avatar_url: typing.Union[undefined.UndefinedType, str, files.URL] = undefined.UNDEFINED,
        attachment: undefined.UndefinedOr[files.Resourceish] = undefined.UNDEFINED,
        attachments: undefined.UndefinedOr[typing.Sequence[files.Resourceish]] = undefined.UNDEFINED,
        component: undefined.UndefinedOr[special_endpoints.ComponentBuilder] = undefined.UNDEFINED,
        components: undefined.UndefinedOr[typing.Sequence[special_endpoints.ComponentBuilder]] = undefined.UNDEFINED,
        embed: undefined.UndefinedOr[embeds_.Embed] = undefined.UNDEFINED,
        embeds: undefined.UndefinedOr[typing.Sequence[embeds_.Embed]] = undefined.UNDEFINED,
        tts: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        mentions_everyone: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        user_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[users.PartialUser], bool]
        ] = undefined.UNDEFINED,
        role_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[guilds.PartialRole], bool]
        ] = undefined.UNDEFINED,
        flags: typing.Union[undefined.UndefinedType, int, messages_.MessageFlag] = undefined.UNDEFINED,
    ) -> messages_.Message:
        # int(ExecutableWebhook) isn't guaranteed to be valid nor the ID used to execute this entity as a webhook.
        webhook_id = webhook if isinstance(webhook, int) else webhook.webhook_id
        route = routes.POST_WEBHOOK_WITH_TOKEN.compile(webhook=webhook_id, token=token)

        body = data_binding.JSONObjectBuilder()
        body.put("username", username)
        body.put("avatar_url", avatar_url, conversion=str)
        body.put("flags", flags)
        query = data_binding.StringMapBuilder()
        query.put("wait", True)
        return await self._create_message(
            route,
            body,
            query,
            no_auth=True,
            content=content,
            attachment=attachment,
            attachments=attachments,
            component=component,
            components=components,
            embed=embed,
            embeds=embeds,
            tts=tts,
            mentions_everyone=mentions_everyone,
            user_mentions=user_mentions,
            role_mentions=role_mentions,
            mentions_reply=undefined.UNDEFINED,
        )

    async def fetch_webhook_message(
        self,
        webhook: typing.Union[webhooks.ExecutableWebhook, snowflakes.Snowflakeish],
        token: str,
        message: snowflakes.SnowflakeishOr[messages_.PartialMessage],
    ) -> messages_.Message:
        # int(ExecutableWebhook) isn't guaranteed to be valid nor the ID used to execute this entity as a webhook.
        webhook_id = webhook if isinstance(webhook, int) else webhook.webhook_id
        route = routes.GET_WEBHOOK_MESSAGE.compile(webhook=webhook_id, token=token, message=message)
        response = await self._request(route, no_auth=True)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_message(response)

    async def edit_webhook_message(
        self,
        webhook: typing.Union[webhooks.ExecutableWebhook, snowflakes.Snowflakeish],
        token: str,
        message: snowflakes.SnowflakeishOr[messages_.Message],
        content: undefined.UndefinedNoneOr[typing.Any] = undefined.UNDEFINED,
        *,
        attachment: undefined.UndefinedOr[files.Resourceish] = undefined.UNDEFINED,
        attachments: undefined.UndefinedOr[typing.Sequence[files.Resourceish]] = undefined.UNDEFINED,
        component: undefined.UndefinedNoneOr[special_endpoints.ComponentBuilder] = undefined.UNDEFINED,
        components: undefined.UndefinedNoneOr[
            typing.Sequence[special_endpoints.ComponentBuilder]
        ] = undefined.UNDEFINED,
        embed: undefined.UndefinedNoneOr[embeds_.Embed] = undefined.UNDEFINED,
        embeds: undefined.UndefinedNoneOr[typing.Sequence[embeds_.Embed]] = undefined.UNDEFINED,
        replace_attachments: bool = False,
        mentions_everyone: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        user_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[users.PartialUser], bool]
        ] = undefined.UNDEFINED,
        role_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[guilds.PartialRole], bool]
        ] = undefined.UNDEFINED,
    ) -> messages_.Message:
        # int(ExecutableWebhook) isn't guaranteed to be valid nor the ID used to execute this entity as a webhook.
        webhook_id = webhook if isinstance(webhook, int) else webhook.webhook_id
        route = routes.PATCH_WEBHOOK_MESSAGE.compile(webhook=webhook_id, token=token, message=message)
        return await self._edit_message(
            route,
            data_binding.JSONObjectBuilder(),
            no_auth=True,
            content=content,
            attachment=attachment,
            attachments=attachments,
            component=component,
            components=components,
            embed=embed,
            embeds=embeds,
            replace_attachments=replace_attachments,
            mentions_everyone=mentions_everyone,
            mentions_reply=undefined.UNDEFINED,
            user_mentions=user_mentions,
            role_mentions=role_mentions,
        )

    async def delete_webhook_message(
        self,
        webhook: typing.Union[webhooks.ExecutableWebhook, snowflakes.Snowflakeish],
        token: str,
        message: snowflakes.SnowflakeishOr[messages_.Message],
    ) -> None:
        # int(ExecutableWebhook) isn't guaranteed to be valid nor the ID used to execute this entity as a webhook.
        webhook_id = webhook if isinstance(webhook, int) else webhook.webhook_id
        route = routes.DELETE_WEBHOOK_MESSAGE.compile(webhook=webhook_id, token=token, message=message)
        await self._request(route, no_auth=True)

    async def fetch_gateway_url(self) -> str:
        route = routes.GET_GATEWAY.compile()
        # This doesn't need authorization.
        response = await self._request(route, no_auth=True)
        assert isinstance(response, dict)
        url = response["url"]
        assert isinstance(url, str)
        return url

    async def fetch_gateway_bot_info(self) -> sessions.GatewayBotInfo:
        route = routes.GET_GATEWAY_BOT.compile()
        response = await self._request(route)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_gateway_bot_info(response)

    async def fetch_invite(self, invite: typing.Union[invites.InviteCode, str]) -> invites.Invite:
        route = routes.GET_INVITE.compile(invite_code=invite if isinstance(invite, str) else invite.code)
        query = data_binding.StringMapBuilder()
        query.put("with_counts", True)
        query.put("with_expiration", True)
        response = await self._request(route, query=query)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_invite(response)

    async def delete_invite(self, invite: typing.Union[invites.InviteCode, str]) -> invites.Invite:
        route = routes.DELETE_INVITE.compile(invite_code=invite if isinstance(invite, str) else invite.code)
        response = await self._request(route)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_invite(response)

    async def fetch_my_user(self) -> users.OwnUser:
        route = routes.GET_MY_USER.compile()
        response = await self._request(route)
        assert isinstance(response, dict)
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

        response = await self._request(route, json=body)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_my_user(response)

    async def fetch_my_connections(self) -> typing.Sequence[applications.OwnConnection]:
        route = routes.GET_MY_CONNECTIONS.compile()
        response = await self._request(route)
        assert isinstance(response, list)
        return [self._entity_factory.deserialize_own_connection(connection_payload) for connection_payload in response]

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

        return special_endpoints_impl.OwnGuildIterator(
            entity_factory=self._entity_factory,
            request_call=self._request,
            newest_first=newest_first,
            first_id=str(start_at),
        )

    async def leave_guild(self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], /) -> None:
        route = routes.DELETE_MY_GUILD.compile(guild=guild)
        await self._request(route)

    async def create_dm_channel(self, user: snowflakes.SnowflakeishOr[users.PartialUser], /) -> channels_.DMChannel:
        route = routes.POST_MY_CHANNELS.compile()
        body = data_binding.JSONObjectBuilder()
        body.put_snowflake("recipient_id", user)
        response = await self._request(route, json=body)
        assert isinstance(response, dict)
        channel = self._entity_factory.deserialize_dm(response)

        if self._cache:
            self._cache.set_dm_channel_id(user, channel.id)

        return channel

    async def fetch_application(self) -> applications.Application:
        route = routes.GET_MY_APPLICATION.compile()
        response = await self._request(route)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_application(response)

    async def fetch_authorization(self) -> applications.AuthorizationInformation:
        route = routes.GET_MY_AUTHORIZATION.compile()
        response = await self._request(route)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_authorization_information(response)

    @staticmethod
    def _gen_oauth2_token(client: snowflakes.SnowflakeishOr[guilds.PartialApplication], client_secret: str) -> str:
        token = base64.b64encode(f"{int(client)}:{client_secret}".encode()).decode("utf-8")
        return f"{applications.TokenType.BASIC} {token}"

    async def authorize_client_credentials_token(
        self,
        client: snowflakes.SnowflakeishOr[guilds.PartialApplication],
        client_secret: str,
        scopes: typing.Sequence[typing.Union[applications.OAuth2Scope, str]],
    ) -> applications.PartialOAuth2Token:
        route = routes.POST_TOKEN.compile()
        form = data_binding.URLEncodedFormBuilder()
        form.add_field("grant_type", "client_credentials")
        form.add_field("scope", " ".join(scopes))

        response = await self._request(route, form_builder=form, auth=self._gen_oauth2_token(client, client_secret))
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_partial_token(response)

    async def authorize_access_token(
        self,
        client: snowflakes.SnowflakeishOr[guilds.PartialApplication],
        client_secret: str,
        code: str,
        redirect_uri: str,
    ) -> applications.OAuth2AuthorizationToken:
        route = routes.POST_TOKEN.compile()
        form = data_binding.URLEncodedFormBuilder()
        form.add_field("grant_type", "authorization_code")
        form.add_field("code", code)
        form.add_field("redirect_uri", redirect_uri)

        response = await self._request(route, form_builder=form, auth=self._gen_oauth2_token(client, client_secret))
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_authorization_token(response)

    async def refresh_access_token(
        self,
        client: snowflakes.SnowflakeishOr[guilds.PartialApplication],
        client_secret: str,
        refresh_token: str,
        *,
        scopes: undefined.UndefinedOr[
            typing.Sequence[typing.Union[applications.OAuth2Scope, str]]
        ] = undefined.UNDEFINED,
    ) -> applications.OAuth2AuthorizationToken:
        route = routes.POST_TOKEN.compile()
        form = data_binding.URLEncodedFormBuilder()
        form.add_field("grant_type", "refresh_token")
        form.add_field("refresh_token", refresh_token)

        if scopes is not undefined.UNDEFINED:
            form.add_field("scope", " ".join(scopes))

        response = await self._request(route, form_builder=form, auth=self._gen_oauth2_token(client, client_secret))
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_authorization_token(response)

    async def revoke_access_token(
        self,
        client: snowflakes.SnowflakeishOr[guilds.PartialApplication],
        client_secret: str,
        token: typing.Union[str, applications.PartialOAuth2Token],
    ) -> None:
        route = routes.POST_TOKEN_REVOKE.compile()
        form = data_binding.URLEncodedFormBuilder()
        form.add_field("token", str(token))
        await self._request(route, form_builder=form, auth=self._gen_oauth2_token(client, client_secret))

    async def add_user_to_guild(
        self,
        access_token: typing.Union[str, applications.PartialOAuth2Token],
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        *,
        nick: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        roles: undefined.UndefinedOr[snowflakes.SnowflakeishSequence[guilds.PartialRole]] = undefined.UNDEFINED,
        mute: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        deaf: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
    ) -> typing.Optional[guilds.Member]:
        route = routes.PUT_GUILD_MEMBER.compile(guild=guild, user=user)
        body = data_binding.JSONObjectBuilder()
        body.put("access_token", str(access_token))
        body.put("nick", nick)
        body.put("mute", mute)
        body.put("deaf", deaf)
        body.put_snowflake_array("roles", roles)

        if (response := await self._request(route, json=body)) is not None:
            assert isinstance(response, dict)
            return self._entity_factory.deserialize_member(response, guild_id=snowflakes.Snowflake(guild))
        else:
            # User already is in the guild.
            return None

    async def fetch_voice_regions(self) -> typing.Sequence[voices.VoiceRegion]:
        route = routes.GET_VOICE_REGIONS.compile()
        response = await self._request(route)
        assert isinstance(response, list)
        return [
            self._entity_factory.deserialize_voice_region(voice_region_payload) for voice_region_payload in response
        ]

    async def fetch_user(self, user: snowflakes.SnowflakeishOr[users.PartialUser]) -> users.User:
        route = routes.GET_USER.compile(user=user)
        response = await self._request(route)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_user(response)

    def fetch_audit_log(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        *,
        before: undefined.UndefinedOr[snowflakes.SearchableSnowflakeishOr[snowflakes.Unique]] = undefined.UNDEFINED,
        user: undefined.UndefinedOr[snowflakes.SnowflakeishOr[users.PartialUser]] = undefined.UNDEFINED,
        event_type: undefined.UndefinedOr[typing.Union[audit_logs.AuditLogEventType, int]] = undefined.UNDEFINED,
    ) -> iterators.LazyIterator[audit_logs.AuditLog]:

        timestamp: undefined.UndefinedOr[str]
        if before is undefined.UNDEFINED:
            timestamp = undefined.UNDEFINED
        elif isinstance(before, datetime.datetime):
            timestamp = str(snowflakes.Snowflake.from_datetime(before))
        else:
            timestamp = str(int(before))

        return special_endpoints_impl.AuditLogIterator(
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
        emoji: snowflakes.SnowflakeishOr[emojis.CustomEmoji],
    ) -> emojis.KnownCustomEmoji:
        route = routes.GET_GUILD_EMOJI.compile(guild=guild, emoji=emoji)
        response = await self._request(route)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_known_custom_emoji(response, guild_id=snowflakes.Snowflake(guild))

    async def fetch_guild_emojis(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild]
    ) -> typing.Sequence[emojis.KnownCustomEmoji]:
        route = routes.GET_GUILD_EMOJIS.compile(guild=guild)
        response = await self._request(route)
        assert isinstance(response, list)
        guild_id = snowflakes.Snowflake(guild)
        return [
            self._entity_factory.deserialize_known_custom_emoji(emoji_payload, guild_id=guild_id)
            for emoji_payload in response
        ]

    async def create_emoji(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        name: str,
        image: files.Resourceish,
        *,
        roles: undefined.UndefinedOr[snowflakes.SnowflakeishSequence[guilds.PartialRole]] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> emojis.KnownCustomEmoji:
        route = routes.POST_GUILD_EMOJIS.compile(guild=guild)
        body = data_binding.JSONObjectBuilder()
        body.put("name", name)
        image_resource = files.ensure_resource(image)
        async with image_resource.stream(executor=self._executor) as stream:
            body.put("image", await stream.data_uri())

        body.put_snowflake_array("roles", roles)

        response = await self._request(route, json=body, reason=reason)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_known_custom_emoji(response, guild_id=snowflakes.Snowflake(guild))

    async def edit_emoji(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        emoji: snowflakes.SnowflakeishOr[emojis.CustomEmoji],
        *,
        name: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        roles: undefined.UndefinedOr[snowflakes.SnowflakeishSequence[guilds.PartialRole]] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> emojis.KnownCustomEmoji:
        route = routes.PATCH_GUILD_EMOJI.compile(guild=guild, emoji=emoji)
        body = data_binding.JSONObjectBuilder()
        body.put("name", name)
        body.put_snowflake_array("roles", roles)

        response = await self._request(route, json=body, reason=reason)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_known_custom_emoji(response, guild_id=snowflakes.Snowflake(guild))

    async def delete_emoji(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        emoji: snowflakes.SnowflakeishOr[emojis.CustomEmoji],
        *,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        route = routes.DELETE_GUILD_EMOJI.compile(guild=guild, emoji=emoji)
        await self._request(route, reason=reason)

    async def fetch_available_sticker_packs(self) -> typing.Sequence[stickers.StickerPack]:
        route = routes.GET_STICKER_PACKS.compile()
        response = await self._request(route, no_auth=True)
        assert isinstance(response, dict)
        return [
            self._entity_factory.deserialize_sticker_pack(sticker_pack_payload)
            for sticker_pack_payload in response["sticker_packs"]
        ]

    async def fetch_sticker(
        self,
        sticker: snowflakes.SnowflakeishOr[stickers.PartialSticker],
    ) -> typing.Union[stickers.StandardSticker, stickers.GuildSticker]:
        route = routes.GET_STICKER.compile(sticker=sticker)
        response = await self._request(route)
        assert isinstance(response, dict)
        return (
            self._entity_factory.deserialize_guild_sticker(response)
            if "guild_id" in response
            else self._entity_factory.deserialize_standard_sticker(response)
        )

    async def fetch_guild_stickers(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild]
    ) -> typing.Sequence[stickers.GuildSticker]:
        route = routes.GET_GUILD_STICKERS.compile(guild=guild)
        response = await self._request(route)
        assert isinstance(response, list)
        return [
            self._entity_factory.deserialize_guild_sticker(guild_sticker_payload) for guild_sticker_payload in response
        ]

    async def fetch_guild_sticker(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        sticker: snowflakes.SnowflakeishOr[stickers.PartialSticker],
    ) -> stickers.GuildSticker:
        route = routes.GET_GUILD_STICKER.compile(guild=guild, sticker=sticker)
        response = await self._request(route)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_guild_sticker(response)

    async def create_sticker(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        name: str,
        tag: str,
        image: files.Resourceish,
        *,
        description: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> stickers.GuildSticker:
        route = routes.POST_GUILD_STICKERS.compile(guild=guild)
        form = data_binding.URLEncodedFormBuilder(executor=self._executor)
        form.add_field("name", name)
        form.add_field("tags", tag)
        form.add_field("description", description or "")
        form.add_resource("file", files.ensure_resource(image))

        response = await self._request(route, form_builder=form, reason=reason)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_guild_sticker(response)

    async def edit_sticker(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        sticker: snowflakes.SnowflakeishOr[stickers.PartialSticker],
        *,
        name: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        description: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        tag: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> stickers.GuildSticker:
        route = routes.PATCH_GUILD_STICKER.compile(guild=guild, sticker=sticker)
        body = data_binding.JSONObjectBuilder()
        body.put("name", name)
        body.put("tags", tag)
        body.put("description", description)

        response = await self._request(route, json=body, reason=reason)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_guild_sticker(response)

    async def delete_sticker(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        sticker: snowflakes.SnowflakeishOr[stickers.PartialSticker],
        *,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        route = routes.DELETE_GUILD_STICKER.compile(guild=guild, sticker=sticker)
        await self._request(route, reason=reason)

    def guild_builder(self, name: str, /) -> special_endpoints.GuildBuilder:
        return special_endpoints_impl.GuildBuilder(
            entity_factory=self._entity_factory, executor=self._executor, request_call=self._request, name=name
        )

    async def fetch_guild(self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild]) -> guilds.RESTGuild:
        route = routes.GET_GUILD.compile(guild=guild)
        query = data_binding.StringMapBuilder()
        query.put("with_counts", True)
        response = await self._request(route, query=query)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_rest_guild(response)

    async def fetch_guild_preview(self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild]) -> guilds.GuildPreview:
        route = routes.GET_GUILD_PREVIEW.compile(guild=guild)
        response = await self._request(route)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_guild_preview(response)

    async def edit_guild(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        *,
        name: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        verification_level: undefined.UndefinedOr[guilds.GuildVerificationLevel] = undefined.UNDEFINED,
        default_message_notifications: undefined.UndefinedOr[
            guilds.GuildMessageNotificationsLevel
        ] = undefined.UNDEFINED,
        explicit_content_filter_level: undefined.UndefinedOr[
            guilds.GuildExplicitContentFilterLevel
        ] = undefined.UNDEFINED,
        afk_channel: undefined.UndefinedOr[
            snowflakes.SnowflakeishOr[channels_.GuildVoiceChannel]
        ] = undefined.UNDEFINED,
        afk_timeout: undefined.UndefinedOr[time.Intervalish] = undefined.UNDEFINED,
        icon: undefined.UndefinedNoneOr[files.Resourceish] = undefined.UNDEFINED,
        owner: undefined.UndefinedOr[snowflakes.SnowflakeishOr[users.PartialUser]] = undefined.UNDEFINED,
        splash: undefined.UndefinedNoneOr[files.Resourceish] = undefined.UNDEFINED,
        banner: undefined.UndefinedNoneOr[files.Resourceish] = undefined.UNDEFINED,
        system_channel: undefined.UndefinedNoneOr[
            snowflakes.SnowflakeishOr[channels_.GuildTextChannel]
        ] = undefined.UNDEFINED,
        rules_channel: undefined.UndefinedNoneOr[
            snowflakes.SnowflakeishOr[channels_.GuildTextChannel]
        ] = undefined.UNDEFINED,
        public_updates_channel: undefined.UndefinedNoneOr[
            snowflakes.SnowflakeishOr[channels_.GuildTextChannel]
        ] = undefined.UNDEFINED,
        preferred_locale: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> guilds.RESTGuild:
        route = routes.PATCH_GUILD.compile(guild=guild)
        body = data_binding.JSONObjectBuilder()
        body.put("name", name)
        body.put("verification_level", verification_level)
        body.put("default_message_notifications", default_message_notifications)
        body.put("explicit_content_filter", explicit_content_filter_level)
        body.put("afk_timeout", afk_timeout, conversion=time.timespan_to_int)
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

        response = await self._request(route, json=body, reason=reason)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_rest_guild(response)

    async def delete_guild(self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild]) -> None:
        route = routes.DELETE_GUILD.compile(guild=guild)
        await self._request(route)

    async def fetch_guild_channels(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild]
    ) -> typing.Sequence[channels_.GuildChannel]:
        route = routes.GET_GUILD_CHANNELS.compile(guild=guild)
        response = await self._request(route)
        assert isinstance(response, list)
        channel_sequence = [self._entity_factory.deserialize_channel(channel_payload) for channel_payload in response]
        # Will always be guild channels unless Discord messes up severely on something!
        return typing.cast("typing.Sequence[channels_.GuildChannel]", channel_sequence)

    async def create_guild_text_channel(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        name: str,
        *,
        position: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        topic: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        nsfw: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        rate_limit_per_user: undefined.UndefinedOr[time.Intervalish] = undefined.UNDEFINED,
        permission_overwrites: undefined.UndefinedOr[
            typing.Sequence[channels_.PermissionOverwrite]
        ] = undefined.UNDEFINED,
        category: undefined.UndefinedOr[snowflakes.SnowflakeishOr[channels_.GuildCategory]] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> channels_.GuildTextChannel:
        channel = await self._create_guild_channel(
            guild,
            name,
            channels_.ChannelType.GUILD_TEXT,
            position=position,
            topic=topic,
            nsfw=nsfw,
            rate_limit_per_user=rate_limit_per_user,
            permission_overwrites=permission_overwrites,
            category=category,
            reason=reason,
        )
        assert isinstance(channel, channels_.GuildTextChannel)
        return channel

    async def create_guild_news_channel(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        name: str,
        *,
        position: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        topic: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        nsfw: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        rate_limit_per_user: undefined.UndefinedOr[time.Intervalish] = undefined.UNDEFINED,
        permission_overwrites: undefined.UndefinedOr[
            typing.Sequence[channels_.PermissionOverwrite]
        ] = undefined.UNDEFINED,
        category: undefined.UndefinedOr[snowflakes.SnowflakeishOr[channels_.GuildCategory]] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> channels_.GuildNewsChannel:
        channel = await self._create_guild_channel(
            guild,
            name,
            channels_.ChannelType.GUILD_NEWS,
            position=position,
            topic=topic,
            nsfw=nsfw,
            rate_limit_per_user=rate_limit_per_user,
            permission_overwrites=permission_overwrites,
            category=category,
            reason=reason,
        )
        assert isinstance(channel, channels_.GuildNewsChannel)
        return channel

    async def create_guild_voice_channel(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        name: str,
        *,
        position: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        user_limit: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        bitrate: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        video_quality_mode: undefined.UndefinedOr[typing.Union[channels_.VideoQualityMode, int]] = undefined.UNDEFINED,
        permission_overwrites: undefined.UndefinedOr[
            typing.Sequence[channels_.PermissionOverwrite]
        ] = undefined.UNDEFINED,
        region: undefined.UndefinedOr[typing.Union[voices.VoiceRegion, str]] = undefined.UNDEFINED,
        category: undefined.UndefinedOr[snowflakes.SnowflakeishOr[channels_.GuildCategory]] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> channels_.GuildVoiceChannel:
        channel = await self._create_guild_channel(
            guild,
            name,
            channels_.ChannelType.GUILD_VOICE,
            position=position,
            user_limit=user_limit,
            bitrate=bitrate,
            video_quality_mode=video_quality_mode,
            permission_overwrites=permission_overwrites,
            region=region,
            category=category,
            reason=reason,
        )
        assert isinstance(channel, channels_.GuildVoiceChannel)
        return channel

    async def create_guild_stage_channel(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        name: str,
        *,
        position: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        user_limit: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        bitrate: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        permission_overwrites: undefined.UndefinedOr[
            typing.Sequence[channels_.PermissionOverwrite]
        ] = undefined.UNDEFINED,
        region: undefined.UndefinedOr[typing.Union[voices.VoiceRegion, str]] = undefined.UNDEFINED,
        category: undefined.UndefinedOr[snowflakes.SnowflakeishOr[channels_.GuildCategory]] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> channels_.GuildStageChannel:
        channel = await self._create_guild_channel(
            guild,
            name,
            channels_.ChannelType.GUILD_STAGE,
            position=position,
            user_limit=user_limit,
            bitrate=bitrate,
            permission_overwrites=permission_overwrites,
            region=region,
            category=category,
            reason=reason,
        )
        assert isinstance(channel, channels_.GuildStageChannel)
        return channel

    async def create_guild_category(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        name: str,
        *,
        position: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        permission_overwrites: undefined.UndefinedOr[
            typing.Sequence[channels_.PermissionOverwrite]
        ] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> channels_.GuildCategory:
        channel = await self._create_guild_channel(
            guild,
            name,
            channels_.ChannelType.GUILD_CATEGORY,
            position=position,
            permission_overwrites=permission_overwrites,
            reason=reason,
        )
        assert isinstance(channel, channels_.GuildCategory)
        return channel

    async def _create_guild_channel(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        name: str,
        type_: channels_.ChannelType,
        *,
        position: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        topic: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        nsfw: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        bitrate: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        video_quality_mode: undefined.UndefinedOr[typing.Union[channels_.VideoQualityMode, int]] = undefined.UNDEFINED,
        user_limit: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        rate_limit_per_user: undefined.UndefinedOr[time.Intervalish] = undefined.UNDEFINED,
        permission_overwrites: undefined.UndefinedOr[
            typing.Sequence[channels_.PermissionOverwrite]
        ] = undefined.UNDEFINED,
        region: undefined.UndefinedOr[typing.Union[voices.VoiceRegion, str]] = undefined.UNDEFINED,
        category: undefined.UndefinedOr[snowflakes.SnowflakeishOr[channels_.GuildCategory]] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> channels_.GuildChannel:
        route = routes.POST_GUILD_CHANNELS.compile(guild=guild)
        body = data_binding.JSONObjectBuilder()
        body.put("type", type_)
        body.put("name", name)
        body.put("position", position)
        body.put("topic", topic)
        body.put("nsfw", nsfw)
        body.put("bitrate", bitrate)
        body.put("video_quality_mode", video_quality_mode)
        body.put("user_limit", user_limit)
        body.put("rate_limit_per_user", rate_limit_per_user, conversion=time.timespan_to_int)
        body.put("rtc_region", region, conversion=str)
        body.put_snowflake("parent_id", category)
        body.put_array(
            "permission_overwrites",
            permission_overwrites,
            conversion=self._entity_factory.serialize_permission_overwrite,
        )

        response = await self._request(route, json=body, reason=reason)
        assert isinstance(response, dict)
        channel = self._entity_factory.deserialize_channel(response)
        assert isinstance(channel, channels_.GuildChannel)
        return channel

    async def reposition_channels(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        positions: typing.Mapping[int, snowflakes.SnowflakeishOr[channels_.GuildChannel]],
    ) -> None:
        route = routes.POST_GUILD_CHANNELS.compile(guild=guild)
        body = [{"id": str(int(channel)), "position": pos} for pos, channel in positions.items()]
        await self._request(route, json=body)

    async def fetch_member(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
    ) -> guilds.Member:
        route = routes.GET_GUILD_MEMBER.compile(guild=guild, user=user)
        response = await self._request(route)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_member(response, guild_id=snowflakes.Snowflake(guild))

    def fetch_members(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild]
    ) -> iterators.LazyIterator[guilds.Member]:
        return special_endpoints_impl.MemberIterator(
            entity_factory=self._entity_factory, request_call=self._request, guild=guild
        )

    async def search_members(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        name: str,
    ) -> typing.Sequence[guilds.Member]:
        route = routes.GET_GUILD_MEMBERS_SEARCH.compile(guild=guild)
        query = data_binding.StringMapBuilder()
        query.put("query", name)
        query.put("limit", 1000)
        response = await self._request(route, query=query)
        assert isinstance(response, list)
        guild_id = snowflakes.Snowflake(guild)
        return [
            self._entity_factory.deserialize_member(member_payload, guild_id=guild_id) for member_payload in response
        ]

    async def edit_member(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        *,
        nick: undefined.UndefinedNoneOr[str] = undefined.UNDEFINED,
        roles: undefined.UndefinedOr[snowflakes.SnowflakeishSequence[guilds.PartialRole]] = undefined.UNDEFINED,
        mute: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        deaf: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        voice_channel: undefined.UndefinedNoneOr[
            snowflakes.SnowflakeishOr[channels_.GuildVoiceChannel]
        ] = undefined.UNDEFINED,
        communication_disabled_until: undefined.UndefinedNoneOr[datetime.datetime] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> guilds.Member:
        route = routes.PATCH_GUILD_MEMBER.compile(guild=guild, user=user)
        body = data_binding.JSONObjectBuilder()
        body.put("nick", nick)
        body.put("mute", mute)
        body.put("deaf", deaf)
        body.put_snowflake_array("roles", roles)

        if voice_channel is None:
            body.put("channel_id", None)
        else:
            body.put_snowflake("channel_id", voice_channel)

        if isinstance(communication_disabled_until, datetime.datetime):
            body.put("communication_disabled_until", communication_disabled_until.isoformat())
        else:
            body.put("communication_disabled_until", communication_disabled_until)

        response = await self._request(route, json=body, reason=reason)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_member(response, guild_id=snowflakes.Snowflake(guild))

    async def edit_my_member(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        *,
        nickname: undefined.UndefinedNoneOr[str] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> guilds.Member:
        route = routes.PATCH_MY_GUILD_MEMBER.compile(guild=guild)
        body = data_binding.JSONObjectBuilder()
        body.put("nick", nickname)

        response = await self._request(route, json=body, reason=reason)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_member(response, guild_id=snowflakes.Snowflake(guild))

    @deprecation.deprecated("2.0.0.dev104", alternative="RESTClientImpl.edit_my_member's nickname parameter")
    async def edit_my_nick(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.Guild],
        nick: typing.Optional[str],
        *,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        await self.edit_my_member(guild, nickname=nick, reason=reason)

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

    def kick_member(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        *,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> typing.Coroutine[typing.Any, typing.Any, None]:
        return self.kick_user(guild, user, reason=reason)

    async def ban_user(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        *,
        delete_message_days: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        body = data_binding.JSONObjectBuilder()
        body.put("delete_message_days", delete_message_days)
        route = routes.PUT_GUILD_BAN.compile(guild=guild, user=user)
        await self._request(route, json=body, reason=reason)

    def ban_member(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        *,
        delete_message_days: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> typing.Coroutine[typing.Any, typing.Any, None]:
        return self.ban_user(guild, user, delete_message_days=delete_message_days, reason=reason)

    async def unban_user(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        *,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        route = routes.DELETE_GUILD_BAN.compile(guild=guild, user=user)
        await self._request(route, reason=reason)

    def unban_member(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        *,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> typing.Coroutine[typing.Any, typing.Any, None]:
        return self.unban_user(guild, user, reason=reason)

    async def fetch_ban(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
    ) -> guilds.GuildBan:
        route = routes.GET_GUILD_BAN.compile(guild=guild, user=user)
        response = await self._request(route)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_guild_member_ban(response)

    async def fetch_bans(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild]
    ) -> typing.Sequence[guilds.GuildBan]:
        route = routes.GET_GUILD_BANS.compile(guild=guild)
        response = await self._request(route)
        assert isinstance(response, list)
        return [self._entity_factory.deserialize_guild_member_ban(ban_payload) for ban_payload in response]

    async def fetch_roles(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
    ) -> typing.Sequence[guilds.Role]:
        route = routes.GET_GUILD_ROLES.compile(guild=guild)
        response = await self._request(route)
        assert isinstance(response, list)
        guild_id = snowflakes.Snowflake(guild)
        return [self._entity_factory.deserialize_role(role_payload, guild_id=guild_id) for role_payload in response]

    async def create_role(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        *,
        name: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        permissions: undefined.UndefinedOr[permissions_.Permissions] = permissions_.Permissions.NONE,
        color: undefined.UndefinedOr[colors.Colorish] = undefined.UNDEFINED,
        colour: undefined.UndefinedOr[colors.Colorish] = undefined.UNDEFINED,
        hoist: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        icon: undefined.UndefinedOr[files.Resourceish] = undefined.UNDEFINED,
        unicode_emoji: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        mentionable: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> guilds.Role:
        if not undefined.any_undefined(color, colour):
            raise TypeError("Can not specify 'color' and 'colour' together.")

        if not undefined.any_undefined(icon, unicode_emoji):
            raise TypeError("Can not specify 'icon' and 'unicode_emoji' together.")

        route = routes.POST_GUILD_ROLES.compile(guild=guild)
        body = data_binding.JSONObjectBuilder()
        body.put("name", name)
        body.put("permissions", permissions)
        body.put("color", color, conversion=colors.Color.of)
        body.put("color", colour, conversion=colors.Color.of)
        body.put("hoist", hoist)
        body.put("unicode_emoji", unicode_emoji)
        body.put("mentionable", mentionable)

        if icon is not undefined.UNDEFINED:
            icon_resource = files.ensure_resource(icon)
            async with icon_resource.stream(executor=self._executor) as stream:
                body.put("icon", await stream.data_uri())

        response = await self._request(route, json=body, reason=reason)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_role(response, guild_id=snowflakes.Snowflake(guild))

    async def reposition_roles(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        positions: typing.Mapping[int, snowflakes.SnowflakeishOr[guilds.PartialRole]],
    ) -> None:
        route = routes.PATCH_GUILD_ROLES.compile(guild=guild)
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
        icon: undefined.UndefinedNoneOr[files.Resourceish] = undefined.UNDEFINED,
        unicode_emoji: undefined.UndefinedNoneOr[str] = undefined.UNDEFINED,
        mentionable: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> guilds.Role:
        if not undefined.any_undefined(color, colour):
            raise TypeError("Can not specify 'color' and 'colour' together.")

        if not undefined.any_undefined(icon, unicode_emoji):
            raise TypeError("Can not specify 'icon' and 'unicode_emoji' together.")

        route = routes.PATCH_GUILD_ROLE.compile(guild=guild, role=role)

        body = data_binding.JSONObjectBuilder()
        body.put("name", name)
        body.put("permissions", permissions)
        body.put("color", color, conversion=colors.Color.of)
        body.put("color", colour, conversion=colors.Color.of)
        body.put("hoist", hoist)
        body.put("unicode_emoji", unicode_emoji)
        body.put("mentionable", mentionable)

        if icon is None:
            body.put("icon", None)
        elif icon is not undefined.UNDEFINED:
            icon_resource = files.ensure_resource(icon)
            async with icon_resource.stream(executor=self._executor) as stream:
                body.put("icon", await stream.data_uri())

        response = await self._request(route, json=body, reason=reason)
        assert isinstance(response, dict)
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
        include_roles: undefined.UndefinedOr[snowflakes.SnowflakeishSequence[guilds.PartialRole]] = undefined.UNDEFINED,
    ) -> int:
        route = routes.GET_GUILD_PRUNE.compile(guild=guild)
        query = data_binding.StringMapBuilder()
        query.put("days", days)
        if include_roles is not undefined.UNDEFINED:
            roles = ",".join(str(int(role)) for role in include_roles)
            query.put("include_roles", roles)
        response = await self._request(route, query=query)
        assert isinstance(response, dict)
        return int(response["pruned"])

    async def begin_guild_prune(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        *,
        days: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        compute_prune_count: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        include_roles: undefined.UndefinedOr[snowflakes.SnowflakeishSequence[guilds.PartialRole]] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> typing.Optional[int]:
        route = routes.POST_GUILD_PRUNE.compile(guild=guild)
        body = data_binding.JSONObjectBuilder()
        body.put("days", days)
        body.put("compute_prune_count", compute_prune_count)
        body.put_snowflake_array("include_roles", include_roles)
        response = await self._request(route, json=body, reason=reason)
        assert isinstance(response, dict)
        pruned = response.get("pruned")
        return int(pruned) if pruned is not None else None

    async def fetch_guild_voice_regions(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
    ) -> typing.Sequence[voices.VoiceRegion]:
        route = routes.GET_GUILD_VOICE_REGIONS.compile(guild=guild)
        response = await self._request(route)
        assert isinstance(response, list)
        return [
            self._entity_factory.deserialize_voice_region(voice_region_payload) for voice_region_payload in response
        ]

    async def fetch_guild_invites(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
    ) -> typing.Sequence[invites.InviteWithMetadata]:
        route = routes.GET_GUILD_INVITES.compile(guild=guild)
        response = await self._request(route)
        assert isinstance(response, list)
        return [self._entity_factory.deserialize_invite_with_metadata(invite_payload) for invite_payload in response]

    async def fetch_integrations(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
    ) -> typing.Sequence[guilds.Integration]:
        route = routes.GET_GUILD_INTEGRATIONS.compile(guild=guild)
        response = await self._request(route)
        assert isinstance(response, list)
        guild_id = snowflakes.Snowflake(guild)
        return [
            self._entity_factory.deserialize_integration(integration_payload, guild_id=guild_id)
            for integration_payload in response
        ]

    async def fetch_widget(self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild]) -> guilds.GuildWidget:
        route = routes.GET_GUILD_WIDGET.compile(guild=guild)
        response = await self._request(route)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_guild_widget(response)

    async def edit_widget(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        *,
        channel: undefined.UndefinedNoneOr[snowflakes.SnowflakeishOr[channels_.GuildChannel]] = undefined.UNDEFINED,
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

        response = await self._request(route, json=body, reason=reason)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_guild_widget(response)

    async def fetch_welcome_screen(self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild]) -> guilds.WelcomeScreen:
        route = routes.GET_GUILD_WELCOME_SCREEN.compile(guild=guild)
        response = await self._request(route)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_welcome_screen(response)

    async def edit_welcome_screen(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        *,
        description: undefined.UndefinedNoneOr[str] = undefined.UNDEFINED,
        enabled: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        channels: undefined.UndefinedNoneOr[typing.Sequence[guilds.WelcomeChannel]] = undefined.UNDEFINED,
    ) -> guilds.WelcomeScreen:
        route = routes.PATCH_GUILD_WELCOME_SCREEN.compile(guild=guild)

        body = data_binding.JSONObjectBuilder()

        body.put("description", description)
        body.put("enabled", enabled)

        if channels is not None:
            body.put_array("welcome_channels", channels, conversion=self._entity_factory.serialize_welcome_channel)

        else:
            body.put("welcome_channels", None)

        response = await self._request(route, json=body)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_welcome_screen(response)

    async def fetch_vanity_url(self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild]) -> invites.VanityURL:
        route = routes.GET_GUILD_VANITY_URL.compile(guild=guild)
        response = await self._request(route)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_vanity_url(response)

    async def fetch_template(self, template: typing.Union[templates.Template, str]) -> templates.Template:
        template = template if isinstance(template, str) else template.code
        route = routes.GET_TEMPLATE.compile(template=template)
        response = await self._request(route)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_template(response)

    async def fetch_guild_templates(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild]
    ) -> typing.Sequence[templates.Template]:
        route = routes.GET_GUILD_TEMPLATES.compile(guild=guild)
        response = await self._request(route)
        assert isinstance(response, list)
        return [self._entity_factory.deserialize_template(template_payload) for template_payload in response]

    async def sync_guild_template(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        template: typing.Union[templates.Template, str],
    ) -> templates.Template:
        template = template if isinstance(template, str) else template.code
        route = routes.PUT_GUILD_TEMPLATE.compile(guild=guild, template=template)
        response = await self._request(route)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_template(response)

    async def create_guild_from_template(
        self,
        template: typing.Union[str, templates.Template],
        name: str,
        *,
        icon: undefined.UndefinedOr[files.Resourceish] = undefined.UNDEFINED,
    ) -> guilds.RESTGuild:
        template = template if isinstance(template, str) else template.code
        route = routes.POST_TEMPLATE.compile(template=template)
        body = data_binding.JSONObjectBuilder()
        body.put("name", name)

        if icon is not undefined.UNDEFINED:
            icon_resource = files.ensure_resource(icon)
            async with icon_resource.stream(executor=self._executor) as stream:
                body.put("icon", await stream.data_uri())

        response = await self._request(route, json=body)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_rest_guild(response)

    async def create_template(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        name: str,
        *,
        description: undefined.UndefinedNoneOr[str] = undefined.UNDEFINED,
    ) -> templates.Template:
        route = routes.POST_GUILD_TEMPLATES.compile(guild=guild)
        body = data_binding.JSONObjectBuilder()
        body.put("name", name)
        body.put("description", description)
        response = await self._request(route, json=body)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_template(response)

    async def edit_template(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        template: typing.Union[str, templates.Template],
        *,
        name: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        description: undefined.UndefinedNoneOr[str] = undefined.UNDEFINED,
    ) -> templates.Template:
        template = template if isinstance(template, str) else template.code
        route = routes.PATCH_GUILD_TEMPLATE.compile(guild=guild, template=template)
        body = data_binding.JSONObjectBuilder()
        body.put("name", name)
        body.put("description", description)

        response = await self._request(route, json=body)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_template(response)

    async def delete_template(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        template: typing.Union[str, templates.Template],
    ) -> templates.Template:
        template = template if isinstance(template, str) else template.code
        route = routes.DELETE_GUILD_TEMPLATE.compile(guild=guild, template=template)
        response = await self._request(route)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_template(response)

    def command_builder(self, name: str, description: str, /) -> special_endpoints.CommandBuilder:
        return special_endpoints_impl.CommandBuilder(name=name, description=description)

    async def fetch_application_command(
        self,
        application: snowflakes.SnowflakeishOr[guilds.PartialApplication],
        command: snowflakes.SnowflakeishOr[commands.Command],
        guild: undefined.UndefinedOr[snowflakes.SnowflakeishOr[guilds.PartialGuild]] = undefined.UNDEFINED,
    ) -> commands.Command:
        if guild is undefined.UNDEFINED:
            route = routes.GET_APPLICATION_COMMAND.compile(application=application, command=command)

        else:
            route = routes.GET_APPLICATION_GUILD_COMMAND.compile(application=application, guild=guild, command=command)

        response = await self._request(route)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_command(
            response, guild_id=snowflakes.Snowflake(guild) if guild is not undefined.UNDEFINED else None
        )

    async def fetch_application_commands(
        self,
        application: snowflakes.SnowflakeishOr[guilds.PartialApplication],
        guild: undefined.UndefinedOr[snowflakes.SnowflakeishOr[guilds.PartialGuild]] = undefined.UNDEFINED,
    ) -> typing.Sequence[commands.Command]:
        if guild is undefined.UNDEFINED:
            route = routes.GET_APPLICATION_COMMANDS.compile(application=application)

        else:
            route = routes.GET_APPLICATION_GUILD_COMMANDS.compile(application=application, guild=guild)

        response = await self._request(route)
        assert isinstance(response, list)
        guild_id = snowflakes.Snowflake(guild) if guild is not undefined.UNDEFINED else None
        return [self._entity_factory.deserialize_command(command, guild_id=guild_id) for command in response]

    async def create_application_command(
        self,
        application: snowflakes.SnowflakeishOr[guilds.PartialApplication],
        name: str,
        description: str,
        guild: undefined.UndefinedOr[snowflakes.SnowflakeishOr[guilds.PartialGuild]] = undefined.UNDEFINED,
        *,
        options: undefined.UndefinedOr[typing.Sequence[commands.CommandOption]] = undefined.UNDEFINED,
        default_permission: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
    ) -> commands.Command:
        if guild is undefined.UNDEFINED:
            route = routes.POST_APPLICATION_COMMAND.compile(application=application)

        else:
            route = routes.POST_APPLICATION_GUILD_COMMAND.compile(application=application, guild=guild)

        body = data_binding.JSONObjectBuilder()
        body.put("name", name)
        body.put("description", description)
        body.put_array("options", options, conversion=self._entity_factory.serialize_command_option)
        body.put("default_permission", default_permission)

        response = await self._request(route, json=body)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_command(
            response, guild_id=snowflakes.Snowflake(guild) if guild is not undefined.UNDEFINED else None
        )

    async def set_application_commands(
        self,
        application: snowflakes.SnowflakeishOr[guilds.PartialApplication],
        commands: typing.Sequence[special_endpoints.CommandBuilder],
        guild: undefined.UndefinedOr[snowflakes.SnowflakeishOr[guilds.PartialGuild]] = undefined.UNDEFINED,
    ) -> typing.Sequence[commands.Command]:
        if guild is undefined.UNDEFINED:
            route = routes.PUT_APPLICATION_COMMANDS.compile(application=application)

        else:
            route = routes.PUT_APPLICATION_GUILD_COMMANDS.compile(application=application, guild=guild)

        response = await self._request(route, json=[command.build(self._entity_factory) for command in commands])
        assert isinstance(response, list)
        guild_id = snowflakes.Snowflake(guild) if guild is not undefined.UNDEFINED else None
        return [self._entity_factory.deserialize_command(payload, guild_id=guild_id) for payload in response]

    async def edit_application_command(
        self,
        application: snowflakes.SnowflakeishOr[guilds.PartialApplication],
        command: snowflakes.SnowflakeishOr[commands.Command],
        guild: undefined.UndefinedOr[snowflakes.SnowflakeishOr[guilds.PartialGuild]] = undefined.UNDEFINED,
        *,
        name: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        description: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        options: undefined.UndefinedOr[typing.Sequence[commands.CommandOption]] = undefined.UNDEFINED,
    ) -> commands.Command:
        if guild is undefined.UNDEFINED:
            route = routes.PATCH_APPLICATION_COMMAND.compile(application=application, command=command)

        else:
            route = routes.PATCH_APPLICATION_GUILD_COMMAND.compile(
                application=application, command=command, guild=guild
            )

        body = data_binding.JSONObjectBuilder()
        body.put("name", name)
        body.put("description", description)
        body.put_array("options", options, conversion=self._entity_factory.serialize_command_option)

        response = await self._request(route, json=body)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_command(
            response, guild_id=snowflakes.Snowflake(guild) if guild is not undefined.UNDEFINED else None
        )

    async def delete_application_command(
        self,
        application: snowflakes.SnowflakeishOr[guilds.PartialApplication],
        command: snowflakes.SnowflakeishOr[commands.Command],
        guild: undefined.UndefinedOr[snowflakes.SnowflakeishOr[guilds.PartialGuild]] = undefined.UNDEFINED,
    ) -> None:
        if guild is undefined.UNDEFINED:
            route = routes.DELETE_APPLICATION_COMMAND.compile(application=application, command=command)

        else:
            route = routes.DELETE_APPLICATION_GUILD_COMMAND.compile(
                application=application, command=command, guild=guild
            )

        await self._request(route)

    async def fetch_application_guild_commands_permissions(
        self,
        application: snowflakes.SnowflakeishOr[guilds.PartialApplication],
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
    ) -> typing.Sequence[commands.GuildCommandPermissions]:
        route = routes.GET_APPLICATION_GUILD_COMMANDS_PERMISSIONS.compile(application=application, guild=guild)
        response = await self._request(route)
        assert isinstance(response, list)
        return [self._entity_factory.deserialize_guild_command_permissions(payload) for payload in response]

    async def fetch_application_command_permissions(
        self,
        application: snowflakes.SnowflakeishOr[guilds.PartialApplication],
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        command: snowflakes.SnowflakeishOr[commands.Command],
    ) -> commands.GuildCommandPermissions:
        route = routes.GET_APPLICATION_COMMAND_PERMISSIONS.compile(
            application=application, guild=guild, command=command
        )
        response = await self._request(route)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_guild_command_permissions(response)

    async def set_application_guild_commands_permissions(
        self,
        application: snowflakes.SnowflakeishOr[guilds.PartialApplication],
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        permissions: typing.Mapping[
            snowflakes.SnowflakeishOr[commands.Command], typing.Sequence[commands.CommandPermission]
        ],
    ) -> typing.Sequence[commands.GuildCommandPermissions]:
        route = routes.PUT_APPLICATION_GUILD_COMMANDS_PERMISSIONS.compile(application=application, guild=guild)
        body = [
            {
                "id": str(snowflakes.Snowflake(command)),
                "permissions": [self._entity_factory.serialize_command_permission(permission) for permission in perms],
            }
            for command, perms in permissions.items()
        ]
        response = await self._request(route, json=body)

        assert isinstance(response, list)
        return [self._entity_factory.deserialize_guild_command_permissions(payload) for payload in response]

    async def set_application_command_permissions(
        self,
        application: snowflakes.SnowflakeishOr[guilds.PartialApplication],
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        command: snowflakes.SnowflakeishOr[commands.Command],
        permissions: typing.Sequence[commands.CommandPermission],
    ) -> commands.GuildCommandPermissions:
        route = routes.PUT_APPLICATION_COMMAND_PERMISSIONS.compile(
            application=application, guild=guild, command=command
        )
        body = data_binding.JSONObjectBuilder()
        body.put_array("permissions", permissions, conversion=self._entity_factory.serialize_command_permission)
        response = await self._request(route, json=body)

        assert isinstance(response, dict)
        return self._entity_factory.deserialize_guild_command_permissions(response)

    def interaction_deferred_builder(
        self, type_: typing.Union[base_interactions.ResponseType, int], /
    ) -> special_endpoints.InteractionDeferredBuilder:
        return special_endpoints_impl.InteractionDeferredBuilder(type=type_)

    def interaction_message_builder(
        self, type_: typing.Union[base_interactions.ResponseType, int], /
    ) -> special_endpoints.InteractionMessageBuilder:
        return special_endpoints_impl.InteractionMessageBuilder(type=type_)

    async def fetch_interaction_response(
        self, application: snowflakes.SnowflakeishOr[guilds.PartialApplication], token: str
    ) -> messages_.Message:
        route = routes.GET_INTERACTION_RESPONSE.compile(webhook=application, token=token)
        response = await self._request(route, no_auth=True)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_message(response)

    async def create_interaction_response(
        self,
        interaction: snowflakes.SnowflakeishOr[base_interactions.PartialInteraction],
        token: str,
        response_type: typing.Union[int, base_interactions.ResponseType],
        content: undefined.UndefinedOr[typing.Any] = undefined.UNDEFINED,
        *,
        flags: typing.Union[int, messages_.MessageFlag, undefined.UndefinedType] = undefined.UNDEFINED,
        tts: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        component: undefined.UndefinedOr[special_endpoints.ComponentBuilder] = undefined.UNDEFINED,
        components: undefined.UndefinedOr[typing.Sequence[special_endpoints.ComponentBuilder]] = undefined.UNDEFINED,
        embed: undefined.UndefinedOr[embeds_.Embed] = undefined.UNDEFINED,
        embeds: undefined.UndefinedOr[typing.Sequence[embeds_.Embed]] = undefined.UNDEFINED,
        mentions_everyone: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        user_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[users.PartialUser], bool]
        ] = undefined.UNDEFINED,
        role_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[guilds.PartialRole], bool]
        ] = undefined.UNDEFINED,
    ) -> None:
        if not undefined.any_undefined(component, components):
            raise ValueError("You may only specify one of 'component' or 'components', not both")

        if not undefined.any_undefined(embed, embeds):
            raise ValueError("You may only specify one of 'embed' or 'embeds', not both")

        if components is not undefined.UNDEFINED and not isinstance(components, typing.Collection):
            raise TypeError(
                "You passed a non-collection to 'components', but this expects a collection. Maybe you meant to "
                "use 'component' (singular) instead?"
            )

        if embeds not in _NONE_OR_UNDEFINED and not isinstance(embeds, typing.Collection):
            raise TypeError(
                "You passed a non-collection to 'embeds', but this expects a collection. Maybe you meant to "
                "use 'embed' (singular) instead?"
            )

        if undefined.all_undefined(embed, embeds) and isinstance(content, embeds_.Embed):
            # Syntactic sugar, common mistake to accidentally send an embed
            # as the content, so lets detect this and fix it for the user.
            embed = content
            content = undefined.UNDEFINED

        route = routes.POST_INTERACTION_RESPONSE.compile(interaction=interaction, token=token)

        body = data_binding.JSONObjectBuilder()
        body.put("type", response_type)

        data = data_binding.JSONObjectBuilder()
        data.put("content", content, conversion=str)
        data.put("flags", flags)
        data.put("tts", tts)
        data.put(
            "allowed_mentions",
            mentions.generate_allowed_mentions(mentions_everyone, undefined.UNDEFINED, user_mentions, role_mentions),
        )

        if component is not undefined.UNDEFINED:
            data.put("components", [component.build()])

        elif components is not undefined.UNDEFINED:
            data.put("components", [component.build() for component in components])

        if embed is not undefined.UNDEFINED:
            embed_payload, attachments = self._entity_factory.serialize_embed(embed)
            if attachments:
                raise ValueError("Cannot send an embed with attachments in a slash command's initial response")

            data.put("embeds", [embed_payload])

        elif embeds is not undefined.UNDEFINED:
            embed_payloads: data_binding.JSONArray = []
            for embed in embeds:
                serialized_embed, attachments = self._entity_factory.serialize_embed(embed)
                embed_payloads.append(serialized_embed)
                if attachments:
                    raise ValueError("Cannot send an embed with attachments in a slash command's initial response")

            data.put("embeds", embed_payloads)

        body.put("data", data)
        await self._request(route, json=body, no_auth=True)

    async def edit_interaction_response(
        self,
        application: snowflakes.SnowflakeishOr[guilds.PartialApplication],
        token: str,
        content: undefined.UndefinedNoneOr[typing.Any] = undefined.UNDEFINED,
        *,
        attachment: undefined.UndefinedOr[files.Resourceish] = undefined.UNDEFINED,
        attachments: undefined.UndefinedOr[typing.Sequence[files.Resourceish]] = undefined.UNDEFINED,
        component: undefined.UndefinedNoneOr[special_endpoints.ComponentBuilder] = undefined.UNDEFINED,
        components: undefined.UndefinedNoneOr[
            typing.Sequence[special_endpoints.ComponentBuilder]
        ] = undefined.UNDEFINED,
        embed: undefined.UndefinedNoneOr[embeds_.Embed] = undefined.UNDEFINED,
        embeds: undefined.UndefinedNoneOr[typing.Sequence[embeds_.Embed]] = undefined.UNDEFINED,
        replace_attachments: bool = False,
        mentions_everyone: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        user_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[users.PartialUser], bool]
        ] = undefined.UNDEFINED,
        role_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[guilds.PartialRole], bool]
        ] = undefined.UNDEFINED,
    ) -> messages_.Message:
        route = routes.PATCH_INTERACTION_RESPONSE.compile(webhook=application, token=token)
        return await self._edit_message(
            route,
            data_binding.JSONObjectBuilder(),
            no_auth=True,
            content=content,
            attachment=attachment,
            attachments=attachments,
            component=component,
            components=components,
            embed=embed,
            embeds=embeds,
            replace_attachments=replace_attachments,
            mentions_everyone=mentions_everyone,
            user_mentions=user_mentions,
            role_mentions=role_mentions,
            mentions_reply=undefined.UNDEFINED,
        )

    async def delete_interaction_response(
        self, application: snowflakes.SnowflakeishOr[guilds.PartialApplication], token: str
    ) -> None:
        route = routes.DELETE_INTERACTION_RESPONSE.compile(webhook=application, token=token)
        await self._request(route, no_auth=True)

    def build_action_row(self) -> special_endpoints.ActionRowBuilder:
        return special_endpoints_impl.ActionRowBuilder()
