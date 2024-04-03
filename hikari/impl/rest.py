# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021-present davfsa
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
"""Implementation of a V10 compatible REST API for Discord.

This also includes implementations designed towards providing
RESTful functionality.
"""

from __future__ import annotations

__all__: typing.Sequence[str] = ("ClientCredentialsStrategy", "RESTApp", "RESTClientImpl")

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
import urllib.parse

import aiohttp

from hikari import _about as about
from hikari import applications
from hikari import channels as channels_
from hikari import colors
from hikari import commands
from hikari import embeds as embeds_
from hikari import emojis
from hikari import errors
from hikari import files
from hikari import guilds
from hikari import iterators
from hikari import locales
from hikari import messages as messages_
from hikari import permissions as permissions_
from hikari import scheduled_events
from hikari import snowflakes
from hikari import traits
from hikari import undefined
from hikari import urls
from hikari import users
from hikari.api import rest as rest_api
from hikari.impl import buckets as buckets_impl
from hikari.impl import config as config_impl
from hikari.impl import entity_factory as entity_factory_impl
from hikari.impl import rate_limits
from hikari.impl import special_endpoints as special_endpoints_impl
from hikari.interactions import base_interactions
from hikari.internal import aio
from hikari.internal import data_binding
from hikari.internal import mentions
from hikari.internal import net
from hikari.internal import routes
from hikari.internal import time
from hikari.internal import ux

if typing.TYPE_CHECKING:
    import concurrent.futures
    import types

    from hikari import audit_logs
    from hikari import invites
    from hikari import sessions
    from hikari import stickers as stickers_
    from hikari import templates
    from hikari import voices
    from hikari import webhooks
    from hikari.api import cache as cache_api
    from hikari.api import entity_factory as entity_factory_
    from hikari.api import special_endpoints

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
_X_RATELIMIT_SCOPE_HEADER: typing.Final[str] = sys.intern("X-RateLimit-Scope")
_RETRY_ERROR_CODES: typing.Final[typing.FrozenSet[int]] = frozenset((500, 502, 503, 504))
_MAX_BACKOFF_DURATION: typing.Final[int] = 16


class ClientCredentialsStrategy(rest_api.TokenStrategy):
    """Strategy class for handling client credential OAuth2 authorization.

    Parameters
    ----------
    client : typing.Optional[hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialApplication]]
        Object or ID of the application this client credentials strategy should
        authorize as.
    client_secret : typing.Optional[str]
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
        """ID of the application this token strategy authenticates with."""
        return self._client_id

    @property
    def _is_expired(self) -> bool:
        return time.monotonic() >= self._expire_at

    @property
    def scopes(self) -> typing.Sequence[typing.Union[applications.OAuth2Scope, str]]:
        """Sequence of scopes this token strategy authenticates for."""
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
                if not isinstance(exc, errors.RateLimitTooLongError):
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
        rest: typing.Callable[[], RESTClientImpl],
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
    def http_settings(self) -> config_impl.HTTPSettings:
        return self._rest().http_settings

    @property
    def proxy_settings(self) -> config_impl.ProxySettings:
        return self._rest().proxy_settings


class RESTApp(traits.ExecutorAware):
    """The base for a HTTP-only Discord application.

    This comprises of a shared TCP connector connection pool, and can have
    [`hikari.impl.rest.RESTClientImpl`][] instances for specific credentials acquired
    from it.

    Parameters
    ----------
    executor : typing.Optional[concurrent.futures.Executor]
        The executor to use for blocking file IO operations. If [`None`][]
        is passed, then the default [`concurrent.futures.ThreadPoolExecutor`][] for
        the [`asyncio.AbstractEventLoop`][] will be used instead.
    http_settings : typing.Optional[hikari.impl.config.HTTPSettings]
        HTTP settings to use. Sane defaults are used if this is
        [`None`][].
    dumps : hikari.internal.data_binding.JSONEncoder
        The JSON encoder this application should use.
    loads : hikari.internal.data_binding.JSONDecoder
        The JSON decoder this application should use.
    max_rate_limit : float
        Maximum number of seconds to sleep for when rate limited. If a rate
        limit occurs that is longer than this value, then a
        [`hikari.errors.RateLimitTooLongError`][] will be raised instead of waiting.

        This is provided since some endpoints may respond with non-sensible
        rate limits.

        Defaults to five minutes if unspecified.
    max_retries : typing.Optional[int]
        Maximum number of times a request will be retried if
        it fails with a `5xx` status.

        Defaults to 3 if set to [`None`][].
    proxy_settings : typing.Optional[hikari.impl.config.ProxySettings]
        Proxy settings to use. If [`None`][] then no proxy configuration
        will be used.
    url : typing.Optional[str]
        The base URL for the API. You can generally leave this as being
        [`None`][] and the correct default API base URL will be generated.
    """

    __slots__: typing.Sequence[str] = (
        "_executor",
        "_http_settings",
        "_max_retries",
        "_proxy_settings",
        "_url",
        "_bucket_manager",
        "_client_session",
        "_loads",
        "_dumps",
    )

    def __init__(
        self,
        *,
        executor: typing.Optional[concurrent.futures.Executor] = None,
        http_settings: typing.Optional[config_impl.HTTPSettings] = None,
        dumps: data_binding.JSONEncoder = data_binding.default_json_dumps,
        loads: data_binding.JSONDecoder = data_binding.default_json_loads,
        max_rate_limit: float = 300.0,
        max_retries: int = 3,
        proxy_settings: typing.Optional[config_impl.ProxySettings] = None,
        url: typing.Optional[str] = None,
    ) -> None:
        self._http_settings = config_impl.HTTPSettings() if http_settings is None else http_settings
        self._proxy_settings = config_impl.ProxySettings() if proxy_settings is None else proxy_settings
        self._loads = loads
        self._dumps = dumps
        self._executor = executor
        self._max_retries = max_retries
        self._url = url
        self._bucket_manager = buckets_impl.RESTBucketManager(max_rate_limit)
        self._client_session: typing.Optional[aiohttp.ClientSession] = None

    @property
    def executor(self) -> typing.Optional[concurrent.futures.Executor]:
        return self._executor

    @property
    def http_settings(self) -> config_impl.HTTPSettings:
        return self._http_settings

    @property
    def proxy_settings(self) -> config_impl.ProxySettings:
        return self._proxy_settings

    async def start(self) -> None:
        if self._client_session:
            raise errors.ComponentStateConflictError("Rest app has already been started")

        self._bucket_manager.start()
        self._client_session = net.create_client_session(
            connector=net.create_tcp_connector(self._http_settings),
            connector_owner=True,  # Ensure closing the TCP connector
            http_settings=self._http_settings,
            raise_for_status=False,
            trust_env=self._proxy_settings.trust_env,
        )

    async def close(self) -> None:
        if self._client_session is None:
            raise errors.ComponentStateConflictError("Rest app is not running")

        await self._client_session.close()
        await self._bucket_manager.close()

    @typing.overload
    def acquire(self, token: typing.Optional[rest_api.TokenStrategy] = None) -> RESTClientImpl: ...

    @typing.overload
    def acquire(
        self, token: str, token_type: typing.Union[str, applications.TokenType] = applications.TokenType.BEARER
    ) -> RESTClientImpl: ...

    def acquire(
        self,
        token: typing.Union[str, rest_api.TokenStrategy, None] = None,
        token_type: typing.Union[str, applications.TokenType, None] = None,
    ) -> RESTClientImpl:
        """Acquire an instance of this REST client.

        !!! note
            The returned REST client should be started before it can be used,
            either by calling [`hikari.impl.rest.RESTClientImpl.start`][] or by using it as an
            asynchronous context manager.

        Examples
        --------
        ```py
            rest_app = RESTApp()
            await rest_app.start()

            # Using the returned client as a context manager to implicitly start
            # and stop it.
            async with rest_app.acquire("A token", "Bot") as client:
                user = await client.fetch_my_user()

            await rest_app.close()
        ```

        Parameters
        ----------
        token : typing.Union[str, None, hikari.api.rest.TokenStrategy]
            The bot or bearer token. If no token is to be used,
            this can be undefined.
        token_type : typing.Union[str, hikari.applications.TokenType, None]
            The type of token in use. This should only be passed when [`str`][]
            is passed for `token`, can be `"Bot"` or `"Bearer"` and will be
            defaulted to `"Bearer"` in this situation.

            This should be left as [`None`][] when either
            [`hikari.api.rest.TokenStrategy`][] or [`None`][] is passed for
            `token`.

        Returns
        -------
        RESTClientImpl
            An instance of the REST client.

        Raises
        ------
        ValueError
            If `token_type` is provided when a token strategy is passed for `token`.
        """
        if not self._client_session:
            raise errors.ComponentStateConflictError("Rest app is not running so it cannot be interacted with")

        # Since we essentially mimic a fake App instance, we need to make a circular provider.
        # We can achieve this using a lambda. This allows the entity factory to build models that
        # are also REST-aware
        provider = _RESTProvider(lambda: entity_factory, self._executor, lambda: rest_client)
        entity_factory = entity_factory_impl.EntityFactoryImpl(provider)

        if isinstance(token, str):
            token = token.strip()

            if token_type is None:
                token_type = applications.TokenType.BEARER

        rest_client = RESTClientImpl(
            cache=None,
            entity_factory=entity_factory,
            executor=self._executor,
            http_settings=self._http_settings,
            max_retries=self._max_retries,
            proxy_settings=self._proxy_settings,
            loads=self._loads,
            dumps=self._dumps,
            token=token,
            token_type=token_type,
            rest_url=self._url,
            bucket_manager=self._bucket_manager,
            bucket_manager_owner=False,
            client_session=self._client_session,
            client_session_owner=False,
        )

        return rest_client


def _stringify_http_message(headers: data_binding.Headers, body: typing.Any) -> str:
    string = "\n".join(
        f"    {name}: {value}" if name != _AUTHORIZATION_HEADER else f"    {name}: **REDACTED TOKEN**"
        for name, value in headers.items()
    )

    if body is not None:
        string += "\n\n    "
        string += body.decode("ascii") if isinstance(body, bytes) else str(body)

    return string


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


class RESTClientImpl(rest_api.RESTClient):
    """Implementation of the V10-compatible Discord HTTP API.

    This manages making HTTP/1.1 requests to the API and using the entity
    factory within the passed application instance to deserialize JSON responses
    to Pythonic data classes that are used throughout this library.

    Parameters
    ----------
    entity_factory : hikari.api.entity_factory.EntityFactory
        The entity factory to use.
    executor : typing.Optional[concurrent.futures.Executor]
        The executor to use for blocking IO.

        Defaults to the [`asyncio`][] thread pool if set to [`None`][].
    max_retries : typing.Optional[int]
        Maximum number of times a request will be retried if
        it fails with a `5xx` status.

        Defaults to 3 if set to [`None`][].
    dumps : hikari.internal.data_binding.JSONEncoder
        The JSON encoder this application should use.
    loads : hikari.internal.data_binding.JSONDecoder
        The JSON decoder this application should use.
    token : typing.Union[str, None, hikari.api.rest.TokenStrategy]
        The bot or bearer token. If no token is to be used,
        this can be undefined.
    token_type : typing.Union[str, hikari.applications.TokenType, None]
        The type of token in use. This must be passed when a [`str`][] is
        passed for `token` but and can be `"Bot"` or `"Bearer"`.

        This should be left as [`None`][] when either
        [`hikari.api.rest.TokenStrategy`][] or [`None`][] is passed for
        `token`.
    rest_url : str
        The HTTP API base URL. This can contain format-string specifiers to
        interpolate information such as API version in use.

    Raises
    ------
    ValueError
        If `token_type` is provided when a token strategy is passed for `token`, if
        `token_type` is left as [`None`][] when a string is passed for `token` or if a
        value greater than 5 is provided for `max_retries`.
    """

    __slots__: typing.Sequence[str] = (
        "_bucket_manager",
        "_bucket_manager_owner",
        "_cache",
        "_entity_factory",
        "_executor",
        "_http_settings",
        "_max_retries",
        "_proxy_settings",
        "_dumps",
        "_loads",
        "_rest_url",
        "_token",
        "_token_type",
        "_client_session",
        "_client_session_owner",
        "_close_event",
    )

    def __init__(
        self,
        *,
        cache: typing.Optional[cache_api.MutableCache],
        entity_factory: entity_factory_.EntityFactory,
        executor: typing.Optional[concurrent.futures.Executor],
        http_settings: config_impl.HTTPSettings,
        bucket_manager: typing.Optional[buckets_impl.RESTBucketManager] = None,
        bucket_manager_owner: bool = True,
        client_session: typing.Optional[aiohttp.ClientSession] = None,
        client_session_owner: bool = True,
        max_rate_limit: float = 300.0,
        max_retries: int = 3,
        proxy_settings: config_impl.ProxySettings,
        dumps: data_binding.JSONEncoder = data_binding.default_json_dumps,
        loads: data_binding.JSONDecoder = data_binding.default_json_loads,
        token: typing.Union[str, None, rest_api.TokenStrategy],
        token_type: typing.Union[applications.TokenType, str, None],
        rest_url: typing.Optional[str],
    ) -> None:
        if max_retries > 5:
            raise ValueError("'max_retries' must be below or equal to 5")

        if client_session_owner is False and client_session is None:
            raise ValueError(
                "Cannot delegate ownership of unknown client session [client_session_owner=False, client_session=None]"
            )
        if bucket_manager_owner is False and bucket_manager is None:
            raise ValueError(
                "Cannot delegate ownership of unknown bucket manager [bucket_manager_owner=False, bucket_manager=None]"
            )

        self._cache = cache
        self._entity_factory = entity_factory
        self._executor = executor
        self._http_settings = http_settings
        self._max_retries = max_retries
        self._proxy_settings = proxy_settings
        self._dumps = dumps
        self._loads = loads
        self._bucket_manager = (
            buckets_impl.RESTBucketManager(max_rate_limit) if bucket_manager is None else bucket_manager
        )
        self._bucket_manager_owner = bucket_manager_owner
        self._client_session = client_session
        self._client_session_owner = client_session_owner
        self._close_event: typing.Optional[asyncio.Event] = None

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
        return self._close_event is not None

    @property
    def http_settings(self) -> config_impl.HTTPSettings:
        return self._http_settings

    @property
    def proxy_settings(self) -> config_impl.ProxySettings:
        return self._proxy_settings

    @property
    def entity_factory(self) -> entity_factory_.EntityFactory:
        return self._entity_factory

    @property
    def token_type(self) -> typing.Union[str, applications.TokenType, None]:
        return self._token_type

    async def close(self) -> None:
        """Close the HTTP client and any open HTTP connections."""
        if not self._close_event or not self._client_session:
            raise errors.ComponentStateConflictError("Cannot close an inactive REST client")

        self._close_event.set()
        self._close_event = None

        if self._client_session_owner:
            await self._client_session.close()
            self._client_session = None

        if self._bucket_manager_owner:
            await self._bucket_manager.close()

    def start(self) -> None:
        """Start the HTTP client.

        !!! note
            This must be called within an active event loop.

        Raises
        ------
        RuntimeError
            If this is called in an environment without an active event loop.
        """
        if self._close_event:
            raise errors.ComponentStateConflictError("Cannot start a REST Client which is already alive")

        # Assert is in running loop
        asyncio.get_running_loop()

        self._close_event = asyncio.Event()

        if self._client_session_owner:
            self._client_session = net.create_client_session(
                connector=net.create_tcp_connector(self._http_settings),
                connector_owner=True,  # Ensure closing the TCP connector
                http_settings=self._http_settings,
                raise_for_status=False,
                trust_env=self._proxy_settings.trust_env,
            )

        if self._bucket_manager_owner:
            self._bucket_manager.start()

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
        auth: undefined.UndefinedNoneOr[str] = undefined.UNDEFINED,
    ) -> typing.Union[None, data_binding.JSONObject, data_binding.JSONArray]:
        if not self._close_event:
            raise errors.ComponentStateConflictError("Cannot use an inactive REST client")

        request_task = asyncio.create_task(
            self._perform_request(
                compiled_route=compiled_route,
                query=query,
                form_builder=form_builder,
                json=json,
                reason=reason,
                auth=auth,
            )
        )

        await aio.first_completed(request_task, self._close_event.wait())

        if not request_task.cancelled():
            return request_task.result()

        raise errors.ComponentStateConflictError("The REST client was closed mid-request")

    # Ignore too long and too complex, respectively
    # We rather keep everything we can here inline.
    @typing.final
    async def _perform_request(  # noqa: CFQ001, C901
        self,
        compiled_route: routes.CompiledRoute,
        *,
        query: typing.Optional[data_binding.StringMapBuilder] = None,
        form_builder: typing.Optional[data_binding.URLEncodedFormBuilder] = None,
        json: typing.Union[data_binding.JSONObject, data_binding.JSONArray, None] = None,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        auth: undefined.UndefinedNoneOr[str] = undefined.UNDEFINED,
    ) -> typing.Union[None, data_binding.JSONObject, data_binding.JSONArray]:
        # Make a ratelimit-protected HTTP request to a JSON endpoint and expect some form
        # of JSON response.

        assert self._client_session is not None  # This will never be None here

        headers = data_binding.StringMapBuilder()
        headers.put(_USER_AGENT_HEADER, _HTTP_USER_AGENT)
        # As per the docs, UTF-8 characters are only supported here if it's url-encoded.
        headers.put(_X_AUDIT_LOG_REASON_HEADER, reason, conversion=urllib.parse.quote)

        can_re_auth = False
        if auth is undefined.UNDEFINED:
            if isinstance(self._token, rest_api.TokenStrategy):
                auth = await self._token.acquire(self)
                can_re_auth = True

            else:
                auth = self._token

        if auth:
            headers[_AUTHORIZATION_HEADER] = auth

        data: typing.Union[None, aiohttp.BytesPayload, aiohttp.FormData] = None
        if json is not None:
            if form_builder:
                raise ValueError("Can only provide one of 'json' or 'form_builder', not both")

            data = data_binding.JSONPayload(json, dumps=self._dumps)

        url = compiled_route.create_url(self._rest_url)

        stack = contextlib.AsyncExitStack()
        # This is initiated the first time we time out or hit a 5xx error to
        # save a little memory when nothing goes wrong
        backoff: typing.Optional[rate_limits.ExponentialBackOff] = None
        retry_count = 0
        trace_logging_enabled = _LOGGER.isEnabledFor(ux.TRACE)

        while True:
            try:
                if form_builder:
                    data = await form_builder.build(stack, executor=self._executor)

                if compiled_route.route.has_ratelimits:
                    await stack.enter_async_context(self._bucket_manager.acquire_bucket(compiled_route, auth))

                if trace_logging_enabled:
                    uuid = time.uuid()
                    _LOGGER.log(
                        ux.TRACE,
                        "%s %s %s\n%s",
                        uuid,
                        compiled_route.method,
                        url,
                        _stringify_http_message(headers, json),
                    )
                    start = time.monotonic()

                # Make the request.
                response = await self._client_session.request(
                    compiled_route.method,
                    url,
                    headers=headers,
                    params=query,
                    data=data,
                    allow_redirects=self._http_settings.max_redirects is not None,
                    max_redirects=self._http_settings.max_redirects,
                    proxy=self._proxy_settings.url,
                    proxy_headers=self._proxy_settings.all_headers,
                )

                if trace_logging_enabled:
                    time_taken = (time.monotonic() - start) * 1_000  # pyright: ignore[reportUnboundVariable]
                    _LOGGER.log(
                        ux.TRACE,
                        "%s %s %s in %sms\n%s",
                        uuid,  # pyright: ignore[reportUnboundVariable]
                        response.status,
                        response.reason,
                        time_taken,
                        _stringify_http_message(response.headers, await response.read()),
                    )

                # Ensure we are not rate limited, and update rate limiting headers where appropriate.
                time_before_retry = await self._parse_ratelimits(compiled_route, auth, response)

            except (asyncio.TimeoutError, aiohttp.ClientConnectionError) as ex:
                if retry_count >= self._max_retries:
                    raise errors.HTTPError(message=str(ex)) from ex

                if backoff is None:
                    backoff = rate_limits.ExponentialBackOff(maximum=_MAX_BACKOFF_DURATION)

                sleep_time = next(backoff)
                _LOGGER.warning(
                    "Connection error (%s), backing off for %.2fs and retrying. Retries remaining: %s",
                    type(ex).__name__,
                    sleep_time,
                    self._max_retries - retry_count,
                )
                retry_count += 1

                await asyncio.sleep(sleep_time)
                continue

            finally:
                await stack.aclose()

            if time_before_retry is not None:
                await asyncio.sleep(time_before_retry)
                continue

            # Don't bother processing any further if we got NO CONTENT. There's not anything
            # to check.
            if response.status == http.HTTPStatus.NO_CONTENT:
                return None

            # Handle the response when everything went good
            if 200 <= response.status < 300:
                if response.content_type == _APPLICATION_JSON:
                    # Only deserializing here stops Cloudflare shenanigans messing us around.
                    return self._loads(await response.read())

                real_url = str(response.real_url)
                raise errors.HTTPError(f"Expected JSON [{response.content_type=}, {real_url=}]")

            # Handling 5xx errors
            if response.status in _RETRY_ERROR_CODES and retry_count < self._max_retries:
                if not backoff:
                    backoff = rate_limits.ExponentialBackOff(maximum=_MAX_BACKOFF_DURATION)

                sleep_time = next(backoff)
                retry_count += 1
                _LOGGER.warning(
                    "Received status %s on request, backing off for %.2fs and retrying. Retries remaining: %s",
                    response.status,
                    sleep_time,
                    self._max_retries - retry_count,
                )

                await asyncio.sleep(sleep_time)
                continue

            # Attempt to re-auth on UNAUTHORIZED if we are using a TokenStrategy
            if can_re_auth and response.status == 401:
                # can_re_auth ensures that it is a token strategy
                assert isinstance(self._token, rest_api.TokenStrategy)

                self._token.invalidate(auth)
                auth = headers[_AUTHORIZATION_HEADER] = await self._token.acquire(self)
                can_re_auth = False
                continue

            raise await net.generate_error_response(response)

    @typing.final
    async def _parse_ratelimits(
        self,
        compiled_route: routes.CompiledRoute,
        authentication: typing.Optional[str],
        response: aiohttp.ClientResponse,
    ) -> typing.Optional[float]:
        # Handle rate limiting.
        #
        # If returns a `float`, the time to wait before retrying the request. If `None`, the request
        # does not need to be retried.
        resp_headers = response.headers
        limit = int(resp_headers.get(_X_RATELIMIT_LIMIT_HEADER, "1"))
        remaining = int(resp_headers.get(_X_RATELIMIT_REMAINING_HEADER, "1"))
        bucket = resp_headers.get(_X_RATELIMIT_BUCKET_HEADER)
        reset_after = float(resp_headers.get(_X_RATELIMIT_RESET_AFTER_HEADER, "0"))

        if bucket:
            if not compiled_route.route.has_ratelimits:
                # This should theoretically never see the light of day, but it scares me that Discord might
                # pull a funny one and this may go unnoticed, so better safe to have it!
                _LOGGER.error(
                    "Received an unexpected bucket header for '%s'. "
                    "The route will be treated as having a ratelimit for the duration of this applications runtime. "
                    "If you see this, please report it to the maintainers so the route can be updated!",
                    compiled_route.route,
                )
                compiled_route.route.has_ratelimits = True

            self._bucket_manager.update_rate_limits(
                compiled_route=compiled_route,
                authentication=authentication,
                bucket_header=bucket,
                remaining_header=remaining,
                limit_header=limit,
                reset_after=reset_after,
            )

        if response.status != http.HTTPStatus.TOO_MANY_REQUESTS:
            return None

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
            return 0

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

        body = self._loads(await response.read())
        assert isinstance(body, dict)
        body_retry_after = float(body["retry_after"])

        if body.get("global", False) is True:
            _LOGGER.error(
                "rate limited on the global bucket. You should consider lowering the number of requests you make or "
                "contacting Discord to raise this limit. Backing off and retrying request..."
            )
            self._bucket_manager.throttle(body_retry_after)
            return 0

        _LOGGER.error(
            "rate limited on a %s sub bucket on bucket %s. You should consider lowering the number of requests "
            "you make to '%s'. Backing off and retrying request...",
            resp_headers.get(_X_RATELIMIT_SCOPE_HEADER, "route"),
            bucket,
            compiled_route.route,
        )

        if body_retry_after > self._bucket_manager.max_rate_limit:
            raise errors.RateLimitTooLongError(
                route=compiled_route,
                is_global=False,
                retry_after=body_retry_after,
                max_retry_after=self._bucket_manager.max_rate_limit,
                reset_at=time.monotonic() + body_retry_after,
                limit=None,
                period=None,
            )

        return body_retry_after

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
        flags: undefined.UndefinedOr[channels_.ChannelFlag] = undefined.UNDEFINED,
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
        default_auto_archive_duration: undefined.UndefinedOr[time.Intervalish] = undefined.UNDEFINED,
        default_thread_rate_limit_per_user: undefined.UndefinedOr[time.Intervalish] = undefined.UNDEFINED,
        default_forum_layout: undefined.UndefinedOr[typing.Union[channels_.ForumLayoutType, int]] = undefined.UNDEFINED,
        default_sort_order: undefined.UndefinedOr[
            typing.Union[channels_.ForumSortOrderType, int]
        ] = undefined.UNDEFINED,
        available_tags: undefined.UndefinedOr[typing.Sequence[channels_.ForumTag]] = undefined.UNDEFINED,
        default_reaction_emoji: typing.Union[
            str, emojis.Emoji, undefined.UndefinedType, snowflakes.Snowflake, None
        ] = undefined.UNDEFINED,
        archived: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        locked: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        invitable: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        auto_archive_duration: undefined.UndefinedOr[time.Intervalish] = undefined.UNDEFINED,
        applied_tags: undefined.UndefinedOr[snowflakes.SnowflakeishSequence[channels_.ForumTag]] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> channels_.PartialChannel:
        if isinstance(auto_archive_duration, datetime.timedelta):
            auto_archive_duration = round(auto_archive_duration.total_seconds() / 60)
        if isinstance(default_auto_archive_duration, datetime.timedelta):
            default_auto_archive_duration = round(default_auto_archive_duration.total_seconds() / 60)

        route = routes.PATCH_CHANNEL.compile(channel=channel)
        body = data_binding.JSONObjectBuilder()
        body.put("name", name)
        body.put("flags", flags)
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
        body.put("default_auto_archive_duration", default_auto_archive_duration, conversion=int)
        # forum-only fields
        body.put(
            "default_thread_rate_limit_per_user", default_thread_rate_limit_per_user, conversion=time.timespan_to_int
        )
        body.put_array("available_tags", available_tags, conversion=self._entity_factory.serialize_forum_tag)
        body.put("default_forum_layout", default_forum_layout)
        body.put("default_sort_order", default_sort_order)

        if default_reaction_emoji is not undefined.UNDEFINED:
            if default_reaction_emoji is None:
                emoji_id = None
                emoji_name = None
            elif isinstance(default_reaction_emoji, (int, emojis.CustomEmoji)):
                emoji_id = int(default_reaction_emoji)
                emoji_name = None
            else:
                emoji_id = None
                emoji_name = str(default_reaction_emoji)

            body.put("default_reaction_emoji", {"emoji_id": emoji_id, "emoji_name": emoji_name})
        # thread-only fields
        body.put("archived", archived)
        body.put("auto_archive_duration", auto_archive_duration, conversion=time.timespan_to_int)
        body.put("locked", locked)
        body.put("invitable", invitable)
        body.put_snowflake_array("applied_tags", applied_tags)

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

    async def edit_permission_overwrite(
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
        if not self._close_event:
            raise errors.ComponentStateConflictError("Cannot use an inactive REST client")

        return special_endpoints_impl.TypingIndicator(
            request_call=self._request, channel=channel, rest_close_event=self._close_event
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

    def _build_message_payload(  # noqa: C901- Function too complex
        self,
        /,
        *,
        content: undefined.UndefinedOr[typing.Any] = undefined.UNDEFINED,
        attachment: undefined.UndefinedNoneOr[
            typing.Union[files.Resourceish, messages_.Attachment]
        ] = undefined.UNDEFINED,
        attachments: undefined.UndefinedNoneOr[
            typing.Sequence[typing.Union[files.Resourceish, messages_.Attachment]]
        ] = undefined.UNDEFINED,
        component: undefined.UndefinedNoneOr[special_endpoints.ComponentBuilder] = undefined.UNDEFINED,
        components: undefined.UndefinedNoneOr[
            typing.Sequence[special_endpoints.ComponentBuilder]
        ] = undefined.UNDEFINED,
        embed: undefined.UndefinedNoneOr[embeds_.Embed] = undefined.UNDEFINED,
        embeds: undefined.UndefinedNoneOr[typing.Sequence[embeds_.Embed]] = undefined.UNDEFINED,
        sticker: undefined.UndefinedOr[snowflakes.SnowflakeishOr[stickers_.PartialSticker]] = undefined.UNDEFINED,
        stickers: undefined.UndefinedOr[
            snowflakes.SnowflakeishSequence[stickers_.PartialSticker]
        ] = undefined.UNDEFINED,
        flags: typing.Union[undefined.UndefinedType, int, messages_.MessageFlag] = undefined.UNDEFINED,
        tts: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        mentions_everyone: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        mentions_reply: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        user_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[users.PartialUser], bool]
        ] = undefined.UNDEFINED,
        role_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[guilds.PartialRole], bool]
        ] = undefined.UNDEFINED,
        edit: bool = False,
    ) -> typing.Tuple[data_binding.JSONObjectBuilder, typing.Optional[data_binding.URLEncodedFormBuilder]]:
        if not undefined.any_undefined(attachment, attachments):
            raise ValueError("You may only specify one of 'attachment' or 'attachments', not both")

        if not undefined.any_undefined(component, components):
            raise ValueError("You may only specify one of 'component' or 'components', not both")

        if not undefined.any_undefined(embed, embeds):
            raise ValueError("You may only specify one of 'embed' or 'embeds', not both")

        if not undefined.any_undefined(sticker, stickers):
            raise ValueError("You may only specify one of 'sticker' or 'stickers', not both")

        if undefined.all_undefined(embed, embeds) and isinstance(content, embeds_.Embed):
            # Syntactic sugar, common mistake to accidentally send an embed
            # as the content, so let's detect this and fix it for the user.
            embed = content
            content = undefined.UNDEFINED

        elif undefined.all_undefined(attachment, attachments) and isinstance(
            content, (files.Resource, files.RAWISH_TYPES, os.PathLike)
        ):
            # Syntactic sugar, common mistake to accidentally send an attachment
            # as the content, so let's detect this and fix it for the user. This
            # will still then work with normal implicit embed attachments as
            # we work this out later.
            attachment = content
            content = undefined.UNDEFINED

        final_attachments: typing.List[typing.Union[files.Resourceish, messages_.Attachment]] = []
        if attachment:
            final_attachments.append(attachment)
        elif attachments:
            final_attachments.extend(attachments)

        serialized_components: undefined.UndefinedOr[typing.List[data_binding.JSONObject]] = undefined.UNDEFINED
        if component is not undefined.UNDEFINED:
            if component is not None:
                serialized_components = [component.build()]
            else:
                serialized_components = []

        elif components is not undefined.UNDEFINED:
            if components is not None:
                serialized_components = [component.build() for component in components]
            else:
                serialized_components = []

        serialized_embeds: undefined.UndefinedOr[data_binding.JSONArray] = undefined.UNDEFINED
        if embed is not undefined.UNDEFINED:
            if embed is not None:
                embed_payload, embed_attachments = self._entity_factory.serialize_embed(embed)
                final_attachments.extend(embed_attachments)
                serialized_embeds = [embed_payload]

            else:
                serialized_embeds = []

        elif embeds is not undefined.UNDEFINED:
            serialized_embeds = []
            if embeds is not None:
                for e in embeds:
                    embed_payload, embed_attachments = self._entity_factory.serialize_embed(e)
                    final_attachments.extend(embed_attachments)
                    serialized_embeds.append(embed_payload)

        body = data_binding.JSONObjectBuilder()
        body.put("content", content, conversion=lambda v: v if v is None else str(v))
        body.put("tts", tts)
        body.put("flags", flags)
        body.put("embeds", serialized_embeds)
        body.put("components", serialized_components)
        body.put_snowflake_array("sticker_ids", (sticker,) if sticker else stickers)

        if not edit or not undefined.all_undefined(mentions_everyone, mentions_reply, user_mentions, role_mentions):
            body.put(
                "allowed_mentions",
                mentions.generate_allowed_mentions(mentions_everyone, mentions_reply, user_mentions, role_mentions),
            )

        form_builder: typing.Optional[data_binding.URLEncodedFormBuilder] = None
        if final_attachments:
            attachments_payload = []
            attachment_id = 0

            for f in final_attachments:
                if edit and isinstance(f, messages_.Attachment):
                    attachments_payload.append({"id": f.id, "filename": f.filename})
                    continue

                if not form_builder:
                    form_builder = data_binding.URLEncodedFormBuilder()

                resource = files.ensure_resource(f)
                attachments_payload.append({"id": attachment_id, "filename": resource.filename})
                form_builder.add_resource(f"files[{attachment_id}]", resource)
                attachment_id += 1

            body.put("attachments", attachments_payload)

        elif attachment is None or attachments is None:
            body.put("attachments", [])

        return body, form_builder

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
        sticker: undefined.UndefinedOr[snowflakes.SnowflakeishOr[stickers_.PartialSticker]] = undefined.UNDEFINED,
        stickers: undefined.UndefinedOr[
            snowflakes.SnowflakeishSequence[stickers_.PartialSticker]
        ] = undefined.UNDEFINED,
        tts: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        reply: undefined.UndefinedOr[snowflakes.SnowflakeishOr[messages_.PartialMessage]] = undefined.UNDEFINED,
        reply_must_exist: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        mentions_everyone: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        mentions_reply: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        user_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[users.PartialUser], bool]
        ] = undefined.UNDEFINED,
        role_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[guilds.PartialRole], bool]
        ] = undefined.UNDEFINED,
        flags: typing.Union[undefined.UndefinedType, int, messages_.MessageFlag] = undefined.UNDEFINED,
    ) -> messages_.Message:
        route = routes.POST_CHANNEL_MESSAGES.compile(channel=channel)
        body, form_builder = self._build_message_payload(
            content=content,
            attachment=attachment,
            attachments=attachments,
            component=component,
            components=components,
            embed=embed,
            embeds=embeds,
            sticker=sticker,
            stickers=stickers,
            tts=tts,
            mentions_everyone=mentions_everyone,
            mentions_reply=mentions_reply,
            user_mentions=user_mentions,
            role_mentions=role_mentions,
            flags=flags,
        )

        if reply:
            message_reference = data_binding.JSONObjectBuilder()
            message_reference.put("message_id", str(int(reply)))
            message_reference.put("fail_if_not_exists", reply_must_exist)

            body.put("message_reference", message_reference)

        if form_builder is not None:
            form_builder.add_field("payload_json", self._dumps(body), content_type=_APPLICATION_JSON)
            response = await self._request(route, form_builder=form_builder)
        else:
            response = await self._request(route, json=body)

        assert isinstance(response, dict)
        return self._entity_factory.deserialize_message(response)

    async def crosspost_message(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.GuildNewsChannel],
        message: snowflakes.SnowflakeishOr[messages_.PartialMessage],
    ) -> messages_.Message:
        route = routes.POST_CHANNEL_CROSSPOST.compile(channel=channel, message=message)

        response = await self._request(route)

        assert isinstance(response, dict)
        return self._entity_factory.deserialize_message(response)

    async def edit_message(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.TextableChannel],
        message: snowflakes.SnowflakeishOr[messages_.PartialMessage],
        content: undefined.UndefinedOr[typing.Any] = undefined.UNDEFINED,
        *,
        attachment: undefined.UndefinedNoneOr[
            typing.Union[files.Resourceish, messages_.Attachment]
        ] = undefined.UNDEFINED,
        attachments: undefined.UndefinedNoneOr[
            typing.Sequence[typing.Union[files.Resourceish, messages_.Attachment]]
        ] = undefined.UNDEFINED,
        component: undefined.UndefinedNoneOr[special_endpoints.ComponentBuilder] = undefined.UNDEFINED,
        components: undefined.UndefinedNoneOr[
            typing.Sequence[special_endpoints.ComponentBuilder]
        ] = undefined.UNDEFINED,
        embed: undefined.UndefinedNoneOr[embeds_.Embed] = undefined.UNDEFINED,
        embeds: undefined.UndefinedNoneOr[typing.Sequence[embeds_.Embed]] = undefined.UNDEFINED,
        mentions_everyone: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        mentions_reply: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        user_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[users.PartialUser], bool]
        ] = undefined.UNDEFINED,
        role_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[guilds.PartialRole], bool]
        ] = undefined.UNDEFINED,
        flags: typing.Union[undefined.UndefinedType, int, messages_.MessageFlag] = undefined.UNDEFINED,
    ) -> messages_.Message:
        route = routes.PATCH_CHANNEL_MESSAGE.compile(channel=channel, message=message)
        body, form_builder = self._build_message_payload(
            content=content,
            attachment=attachment,
            attachments=attachments,
            component=component,
            components=components,
            embed=embed,
            embeds=embeds,
            flags=flags,
            mentions_everyone=mentions_everyone,
            mentions_reply=mentions_reply,
            user_mentions=user_mentions,
            role_mentions=role_mentions,
            edit=True,
        )

        if form_builder is not None:
            form_builder.add_field("payload_json", self._dumps(body), content_type=_APPLICATION_JSON)
            response = await self._request(route, form_builder=form_builder)
        else:
            response = await self._request(route, json=body)

        assert isinstance(response, dict)
        return self._entity_factory.deserialize_message(response)

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
            typing.Iterable[snowflakes.SnowflakeishOr[messages_.PartialMessage]],
            typing.AsyncIterable[snowflakes.SnowflakeishOr[messages_.PartialMessage]],
        ],
        /,
        *other_messages: snowflakes.SnowflakeishOr[messages_.PartialMessage],
    ) -> None:
        route = routes.POST_DELETE_CHANNEL_MESSAGES_BULK.compile(channel=channel)

        deleted: typing.List[snowflakes.SnowflakeishOr[messages_.PartialMessage]] = []

        iterator: iterators.LazyIterator[snowflakes.SnowflakeishOr[messages_.PartialMessage]]
        if isinstance(messages, typing.AsyncIterable):
            if other_messages:
                raise TypeError("Cannot use *args with an async iterable.")

            iterator = iterators.NOOPLazyIterator(messages)
        else:
            messages = tuple(messages) if isinstance(messages, typing.Iterable) else (messages,)
            iterator = iterators.FlatLazyIterator(messages + other_messages)

        async for chunk in iterator.chunk(100):
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
            # we will invoke them sequentially instead.
            try:
                if len(chunk) == 1:
                    message = chunk[0]
                    try:
                        await self.delete_message(channel, message)
                    except errors.NotFoundError as ex:
                        # If the message is not found then this error should be suppressed
                        # to keep consistency with how the bulk delete endpoint functions.
                        if ex.code != 10008:  # Unknown Message
                            raise

                    deleted.append(message)

                else:
                    body = data_binding.JSONObjectBuilder()
                    body.put_snowflake_array("messages", chunk)
                    await self._request(route, json=body)
                    deleted += chunk

            except Exception as ex:
                raise errors.BulkDeleteError(deleted) from ex

    async def add_reaction(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.TextableChannel],
        message: snowflakes.SnowflakeishOr[messages_.PartialMessage],
        emoji: typing.Union[str, emojis.Emoji],
        emoji_id: undefined.UndefinedOr[snowflakes.SnowflakeishOr[emojis.CustomEmoji]] = undefined.UNDEFINED,
    ) -> None:
        route = routes.PUT_MY_REACTION.compile(
            emoji=_transform_emoji_to_url_format(emoji, emoji_id), channel=channel, message=message
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
            emoji=_transform_emoji_to_url_format(emoji, emoji_id), channel=channel, message=message
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
            emoji=_transform_emoji_to_url_format(emoji, emoji_id), channel=channel, message=message
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
            emoji=_transform_emoji_to_url_format(emoji, emoji_id), channel=channel, message=message, user=user
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
            emoji=_transform_emoji_to_url_format(emoji, emoji_id),
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
            auth = undefined.UNDEFINED
        else:
            route = routes.GET_WEBHOOK_WITH_TOKEN.compile(webhook=webhook, token=token)
            auth = None

        response = await self._request(route, auth=auth)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_webhook(response)

    async def fetch_channel_webhooks(
        self, channel: snowflakes.SnowflakeishOr[channels_.WebhookChannelT]
    ) -> typing.Sequence[webhooks.PartialWebhook]:
        route = routes.GET_CHANNEL_WEBHOOKS.compile(channel=channel)
        response = await self._request(route)
        assert isinstance(response, list)
        return data_binding.cast_variants_array(self._entity_factory.deserialize_webhook, response)

    async def fetch_guild_webhooks(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild]
    ) -> typing.Sequence[webhooks.PartialWebhook]:
        route = routes.GET_GUILD_WEBHOOKS.compile(guild=guild)
        response = await self._request(route)
        assert isinstance(response, list)
        return data_binding.cast_variants_array(self._entity_factory.deserialize_webhook, response)

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
            auth = undefined.UNDEFINED
        else:
            route = routes.PATCH_WEBHOOK_WITH_TOKEN.compile(webhook=webhook, token=token)
            auth = None

        body = data_binding.JSONObjectBuilder()
        body.put("name", name)
        body.put_snowflake("channel", channel)

        if avatar is None:
            body.put("avatar", None)
        elif avatar is not undefined.UNDEFINED:
            avatar_resource = files.ensure_resource(avatar)
            async with avatar_resource.stream(executor=self._executor) as stream:
                body.put("avatar", await stream.data_uri())

        response = await self._request(route, json=body, reason=reason, auth=auth)
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
            auth = undefined.UNDEFINED
        else:
            route = routes.DELETE_WEBHOOK_WITH_TOKEN.compile(webhook=webhook, token=token)
            auth = None

        await self._request(route, auth=auth)

    async def execute_webhook(
        self,
        webhook: typing.Union[webhooks.ExecutableWebhook, snowflakes.Snowflakeish],
        token: str,
        content: undefined.UndefinedOr[typing.Any] = undefined.UNDEFINED,
        *,
        thread: typing.Union[
            undefined.UndefinedType, snowflakes.SnowflakeishOr[channels_.GuildThreadChannel]
        ] = undefined.UNDEFINED,
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

        query = data_binding.StringMapBuilder()
        query.put("wait", True)
        query.put("thread_id", thread)

        body, form_builder = self._build_message_payload(
            content=content,
            attachment=attachment,
            attachments=attachments,
            component=component,
            components=components,
            embed=embed,
            embeds=embeds,
            tts=tts,
            flags=flags,
            mentions_everyone=mentions_everyone,
            user_mentions=user_mentions,
            role_mentions=role_mentions,
        )
        body.put("username", username)
        body.put("avatar_url", avatar_url, conversion=str)

        if form_builder is not None:
            form_builder.add_field("payload_json", self._dumps(body), content_type=_APPLICATION_JSON)
            response = await self._request(route, form_builder=form_builder, query=query, auth=None)
        else:
            response = await self._request(route, json=body, query=query, auth=None)

        assert isinstance(response, dict)
        return self._entity_factory.deserialize_message(response)

    async def fetch_webhook_message(
        self,
        webhook: typing.Union[webhooks.ExecutableWebhook, snowflakes.Snowflakeish],
        token: str,
        message: snowflakes.SnowflakeishOr[messages_.PartialMessage],
        *,
        thread: typing.Union[
            undefined.UndefinedType, snowflakes.SnowflakeishOr[channels_.GuildThreadChannel]
        ] = undefined.UNDEFINED,
    ) -> messages_.Message:
        # int(ExecutableWebhook) isn't guaranteed to be valid nor the ID used to execute this entity as a webhook.
        webhook_id = webhook if isinstance(webhook, int) else webhook.webhook_id
        route = routes.GET_WEBHOOK_MESSAGE.compile(webhook=webhook_id, token=token, message=message)
        query = data_binding.StringMapBuilder()
        query.put("thread_id", thread)
        response = await self._request(route, auth=None, query=query)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_message(response)

    async def edit_webhook_message(
        self,
        webhook: typing.Union[webhooks.ExecutableWebhook, snowflakes.Snowflakeish],
        token: str,
        message: snowflakes.SnowflakeishOr[messages_.Message],
        content: undefined.UndefinedNoneOr[typing.Any] = undefined.UNDEFINED,
        *,
        thread: typing.Union[
            undefined.UndefinedType, snowflakes.SnowflakeishOr[channels_.GuildThreadChannel]
        ] = undefined.UNDEFINED,
        attachment: undefined.UndefinedNoneOr[
            typing.Union[files.Resourceish, messages_.Attachment]
        ] = undefined.UNDEFINED,
        attachments: undefined.UndefinedNoneOr[
            typing.Sequence[typing.Union[files.Resourceish, messages_.Attachment]]
        ] = undefined.UNDEFINED,
        component: undefined.UndefinedNoneOr[special_endpoints.ComponentBuilder] = undefined.UNDEFINED,
        components: undefined.UndefinedNoneOr[
            typing.Sequence[special_endpoints.ComponentBuilder]
        ] = undefined.UNDEFINED,
        embed: undefined.UndefinedNoneOr[embeds_.Embed] = undefined.UNDEFINED,
        embeds: undefined.UndefinedNoneOr[typing.Sequence[embeds_.Embed]] = undefined.UNDEFINED,
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
        query = data_binding.StringMapBuilder()
        query.put("thread_id", thread)

        body, form_builder = self._build_message_payload(
            content=content,
            attachment=attachment,
            attachments=attachments,
            component=component,
            components=components,
            embed=embed,
            embeds=embeds,
            mentions_everyone=mentions_everyone,
            user_mentions=user_mentions,
            role_mentions=role_mentions,
            edit=True,
        )

        if form_builder is not None:
            form_builder.add_field("payload_json", self._dumps(body), content_type=_APPLICATION_JSON)
            response = await self._request(route, form_builder=form_builder, query=query, auth=None)
        else:
            response = await self._request(route, json=body, query=query, auth=None)

        assert isinstance(response, dict)
        return self._entity_factory.deserialize_message(response)

    async def delete_webhook_message(
        self,
        webhook: typing.Union[webhooks.ExecutableWebhook, snowflakes.Snowflakeish],
        token: str,
        message: snowflakes.SnowflakeishOr[messages_.Message],
        *,
        thread: typing.Union[
            undefined.UndefinedType, snowflakes.SnowflakeishOr[channels_.GuildThreadChannel]
        ] = undefined.UNDEFINED,
    ) -> None:
        # int(ExecutableWebhook) isn't guaranteed to be valid nor the ID used to execute this entity as a webhook.
        webhook_id = webhook if isinstance(webhook, int) else webhook.webhook_id
        query = data_binding.StringMapBuilder()
        query.put("thread_id", thread)
        route = routes.DELETE_WEBHOOK_MESSAGE.compile(webhook=webhook_id, token=token, message=message)
        await self._request(route, query=query, auth=None)

    async def fetch_gateway_url(self) -> str:
        route = routes.GET_GATEWAY.compile()
        # This doesn't need authorization.
        response = await self._request(route, auth=None)
        assert isinstance(response, dict)
        url = response["url"]
        assert isinstance(url, str)
        return url

    async def fetch_gateway_bot_info(self) -> sessions.GatewayBotInfo:
        route = routes.GET_GATEWAY_BOT.compile()
        response = await self._request(route)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_gateway_bot_info(response)

    async def fetch_invite(
        self, invite: typing.Union[invites.InviteCode, str], with_counts: bool = True, with_expiration: bool = True
    ) -> invites.Invite:
        route = routes.GET_INVITE.compile(invite_code=invite if isinstance(invite, str) else invite.code)
        query = data_binding.StringMapBuilder()
        query.put("with_counts", with_counts)
        query.put("with_expiration", with_expiration)
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

    async def fetch_my_user_application_role_connection(
        self, application: snowflakes.SnowflakeishOr[guilds.PartialApplication]
    ) -> applications.OwnApplicationRoleConnection:
        route = routes.GET_MY_USER_APPLICATION_ROLE_CONNECTIONS.compile(application=application)

        response = await self._request(route)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_own_application_role_connection(response)

    async def set_my_user_application_role_connection(
        self,
        application: snowflakes.SnowflakeishOr[guilds.PartialApplication],
        platform_name: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        platform_username: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        metadata: undefined.UndefinedOr[
            typing.Mapping[str, typing.Union[str, int, bool, datetime.datetime]]
        ] = undefined.UNDEFINED,
    ) -> applications.OwnApplicationRoleConnection:
        route = routes.PUT_MY_USER_APPLICATION_ROLE_CONNECTIONS.compile(application=application)
        body = data_binding.JSONObjectBuilder()
        body.put("platform_name", platform_name)
        body.put("platform_username", platform_username)

        if metadata is not undefined.UNDEFINED:
            # Syntactic sugar for metadata to allow booleans and datetime.datetime
            metadata = dict(metadata)

            for key, value in metadata.items():
                if isinstance(value, bool):
                    metadata[key] = int(value)
                elif isinstance(value, datetime.datetime):
                    metadata[key] = value.isoformat()

            body.put("metadata", metadata)

        response = await self._request(route, json=body)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_own_application_role_connection(response)

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

    async def fetch_application_role_connection_metadata_records(
        self, application: snowflakes.SnowflakeishOr[guilds.PartialApplication]
    ) -> typing.Sequence[applications.ApplicationRoleConnectionMetadataRecord]:
        route = routes.GET_APPLICATION_ROLE_CONNECTION_METADATA_RECORDS.compile(application=application)

        response = await self._request(route)
        assert isinstance(response, list)
        return [self._entity_factory.deserialize_application_connection_metadata_record(r) for r in response]

    async def set_application_role_connection_metadata_records(
        self,
        application: snowflakes.SnowflakeishOr[guilds.PartialApplication],
        records: typing.Sequence[applications.ApplicationRoleConnectionMetadataRecord],
    ) -> typing.Sequence[applications.ApplicationRoleConnectionMetadataRecord]:
        route = routes.PUT_APPLICATION_ROLE_CONNECTION_METADATA_RECORDS.compile(application=application)

        body = [self._entity_factory.serialize_application_connection_metadata_record(r) for r in records]

        response = await self._request(route, json=body)
        assert isinstance(response, list)
        return [self._entity_factory.deserialize_application_connection_metadata_record(r) for r in response]

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
        form_builder = data_binding.URLEncodedFormBuilder()
        form_builder.add_field("grant_type", "client_credentials")
        form_builder.add_field("scope", " ".join(scopes))

        response = await self._request(
            route, form_builder=form_builder, auth=self._gen_oauth2_token(client, client_secret)
        )
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
        form_builder = data_binding.URLEncodedFormBuilder()
        form_builder.add_field("grant_type", "authorization_code")
        form_builder.add_field("code", code)
        form_builder.add_field("redirect_uri", redirect_uri)

        response = await self._request(
            route, form_builder=form_builder, auth=self._gen_oauth2_token(client, client_secret)
        )
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
        form_builder = data_binding.URLEncodedFormBuilder()
        form_builder.add_field("grant_type", "refresh_token")
        form_builder.add_field("refresh_token", refresh_token)

        if scopes is not undefined.UNDEFINED:
            form_builder.add_field("scope", " ".join(scopes))

        response = await self._request(
            route, form_builder=form_builder, auth=self._gen_oauth2_token(client, client_secret)
        )
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_authorization_token(response)

    async def revoke_access_token(
        self,
        client: snowflakes.SnowflakeishOr[guilds.PartialApplication],
        client_secret: str,
        token: typing.Union[str, applications.PartialOAuth2Token],
    ) -> None:
        route = routes.POST_TOKEN_REVOKE.compile()
        form_builder = data_binding.URLEncodedFormBuilder()
        form_builder.add_field("token", str(token))
        await self._request(route, form_builder=form_builder, auth=self._gen_oauth2_token(client, client_secret))

    async def add_user_to_guild(
        self,
        access_token: typing.Union[str, applications.PartialOAuth2Token],
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        *,
        nickname: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        nick: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        roles: undefined.UndefinedOr[snowflakes.SnowflakeishSequence[guilds.PartialRole]] = undefined.UNDEFINED,
        mute: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        deaf: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
    ) -> typing.Optional[guilds.Member]:
        route = routes.PUT_GUILD_MEMBER.compile(guild=guild, user=user)
        body = data_binding.JSONObjectBuilder()
        body.put("access_token", str(access_token))
        body.put("nick", nickname)
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

    async def fetch_available_sticker_packs(self) -> typing.Sequence[stickers_.StickerPack]:
        route = routes.GET_STICKER_PACKS.compile()
        response = await self._request(route, auth=None)
        assert isinstance(response, dict)
        return [
            self._entity_factory.deserialize_sticker_pack(sticker_pack_payload)
            for sticker_pack_payload in response["sticker_packs"]
        ]

    async def fetch_sticker(
        self, sticker: snowflakes.SnowflakeishOr[stickers_.PartialSticker]
    ) -> typing.Union[stickers_.StandardSticker, stickers_.GuildSticker]:
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
    ) -> typing.Sequence[stickers_.GuildSticker]:
        route = routes.GET_GUILD_STICKERS.compile(guild=guild)
        response = await self._request(route)
        assert isinstance(response, list)
        return [
            self._entity_factory.deserialize_guild_sticker(guild_sticker_payload) for guild_sticker_payload in response
        ]

    async def fetch_guild_sticker(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        sticker: snowflakes.SnowflakeishOr[stickers_.PartialSticker],
    ) -> stickers_.GuildSticker:
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
    ) -> stickers_.GuildSticker:
        route = routes.POST_GUILD_STICKERS.compile(guild=guild)
        form = data_binding.URLEncodedFormBuilder()
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
        sticker: snowflakes.SnowflakeishOr[stickers_.PartialSticker],
        *,
        name: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        description: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        tag: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> stickers_.GuildSticker:
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
        sticker: snowflakes.SnowflakeishOr[stickers_.PartialSticker],
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
        preferred_locale: undefined.UndefinedOr[typing.Union[str, locales.Locale]] = undefined.UNDEFINED,
        features: undefined.UndefinedOr[typing.Sequence[typing.Union[str, guilds.GuildFeature]]] = undefined.UNDEFINED,
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
        body.put_array("features", features, conversion=str)
        body.put_snowflake("afk_channel_id", afk_channel)
        body.put_snowflake("owner_id", owner)
        body.put_snowflake("system_channel_id", system_channel)
        body.put_snowflake("rules_channel_id", rules_channel)
        body.put_snowflake("public_updates_channel_id", public_updates_channel)

        stack = contextlib.AsyncExitStack()
        tasks: typing.List[asyncio.Task[str]] = []

        async with stack:
            if icon is None:
                body.put("icon", None)
            elif icon is not undefined.UNDEFINED:
                icon_resource = files.ensure_resource(icon)
                stream = await stack.enter_async_context(icon_resource.stream(executor=self._executor))

                task = asyncio.create_task(stream.data_uri())
                task.add_done_callback(lambda future: body.put("icon", future.result()))
                tasks.append(task)

            if splash is None:
                body.put("splash", None)
            elif splash is not undefined.UNDEFINED:
                splash_resource = files.ensure_resource(splash)
                stream = await stack.enter_async_context(splash_resource.stream(executor=self._executor))

                task = asyncio.create_task(stream.data_uri())
                task.add_done_callback(lambda future: body.put("splash", future.result()))
                tasks.append(task)

            if banner is None:
                body.put("banner", None)
            elif banner is not undefined.UNDEFINED:
                banner_resource = files.ensure_resource(banner)
                stream = await stack.enter_async_context(banner_resource.stream(executor=self._executor))

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
        channels = data_binding.cast_variants_array(self._entity_factory.deserialize_channel, response)
        # Will always be guild channels unless Discord messes up severely on something!
        return typing.cast("typing.Sequence[channels_.GuildChannel]", channels)

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
        default_auto_archive_duration: undefined.UndefinedOr[time.Intervalish] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> channels_.GuildTextChannel:
        response = await self._create_guild_channel(
            guild,
            name,
            channels_.ChannelType.GUILD_TEXT,
            position=position,
            topic=topic,
            nsfw=nsfw,
            rate_limit_per_user=rate_limit_per_user,
            permission_overwrites=permission_overwrites,
            category=category,
            default_auto_archive_duration=default_auto_archive_duration,
            reason=reason,
        )
        return self._entity_factory.deserialize_guild_text_channel(response)

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
        default_auto_archive_duration: undefined.UndefinedOr[time.Intervalish] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> channels_.GuildNewsChannel:
        response = await self._create_guild_channel(
            guild,
            name,
            channels_.ChannelType.GUILD_NEWS,
            position=position,
            topic=topic,
            nsfw=nsfw,
            rate_limit_per_user=rate_limit_per_user,
            permission_overwrites=permission_overwrites,
            category=category,
            default_auto_archive_duration=default_auto_archive_duration,
            reason=reason,
        )
        return self._entity_factory.deserialize_guild_news_channel(response)

    async def create_guild_forum_channel(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        name: str,
        *,
        position: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        category: undefined.UndefinedOr[snowflakes.SnowflakeishOr[channels_.GuildCategory]] = undefined.UNDEFINED,
        permission_overwrites: undefined.UndefinedOr[
            typing.Sequence[channels_.PermissionOverwrite]
        ] = undefined.UNDEFINED,
        topic: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        nsfw: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        rate_limit_per_user: undefined.UndefinedOr[time.Intervalish] = undefined.UNDEFINED,
        default_auto_archive_duration: undefined.UndefinedOr[time.Intervalish] = undefined.UNDEFINED,
        default_thread_rate_limit_per_user: undefined.UndefinedOr[time.Intervalish] = undefined.UNDEFINED,
        default_forum_layout: undefined.UndefinedOr[typing.Union[channels_.ForumLayoutType, int]] = undefined.UNDEFINED,
        default_sort_order: undefined.UndefinedOr[
            typing.Union[channels_.ForumSortOrderType, int]
        ] = undefined.UNDEFINED,
        available_tags: undefined.UndefinedOr[typing.Sequence[channels_.ForumTag]] = undefined.UNDEFINED,
        default_reaction_emoji: typing.Union[
            str, emojis.Emoji, undefined.UndefinedType, snowflakes.Snowflake
        ] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> channels_.GuildForumChannel:
        response = await self._create_guild_channel(
            guild,
            name,
            channels_.ChannelType.GUILD_FORUM,
            topic=topic,
            nsfw=nsfw,
            rate_limit_per_user=rate_limit_per_user,
            default_auto_archive_duration=default_auto_archive_duration,
            default_thread_rate_limit_per_user=default_thread_rate_limit_per_user,
            default_forum_layout=default_forum_layout,
            default_sort_order=default_sort_order,
            position=position,
            permission_overwrites=permission_overwrites,
            category=category,
            available_tags=available_tags,
            default_reaction_emoji=default_reaction_emoji,
            reason=reason,
        )
        return self._entity_factory.deserialize_guild_forum_channel(response)

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
        response = await self._create_guild_channel(
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
        return self._entity_factory.deserialize_guild_voice_channel(response)

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
        response = await self._create_guild_channel(
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
        return self._entity_factory.deserialize_guild_stage_channel(response)

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
        response = await self._create_guild_channel(
            guild,
            name,
            channels_.ChannelType.GUILD_CATEGORY,
            position=position,
            permission_overwrites=permission_overwrites,
            reason=reason,
        )
        return self._entity_factory.deserialize_guild_category(response)

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
        default_auto_archive_duration: undefined.UndefinedOr[time.Intervalish] = undefined.UNDEFINED,
        default_thread_rate_limit_per_user: undefined.UndefinedOr[time.Intervalish] = undefined.UNDEFINED,
        default_forum_layout: undefined.UndefinedOr[typing.Union[channels_.ForumLayoutType, int]] = undefined.UNDEFINED,
        default_sort_order: undefined.UndefinedOr[
            typing.Union[channels_.ForumSortOrderType, int]
        ] = undefined.UNDEFINED,
        available_tags: undefined.UndefinedOr[typing.Sequence[channels_.ForumTag]] = undefined.UNDEFINED,
        default_reaction_emoji: typing.Union[
            str, emojis.Emoji, undefined.UndefinedType, snowflakes.Snowflake
        ] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> data_binding.JSONObject:
        if isinstance(default_auto_archive_duration, datetime.timedelta):
            default_auto_archive_duration = round(default_auto_archive_duration.total_seconds() / 60)

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
        body.put("default_auto_archive_duration", default_auto_archive_duration, conversion=int)
        body.put(
            "default_thread_rate_limit_per_user", default_thread_rate_limit_per_user, conversion=time.timespan_to_int
        )
        body.put_array("available_tags", available_tags, conversion=self._entity_factory.serialize_forum_tag)
        body.put("default_forum_layout", default_forum_layout)
        body.put("default_sort_order", default_sort_order)

        if default_reaction_emoji:
            if isinstance(default_reaction_emoji, (int, emojis.CustomEmoji)):
                emoji_id = int(default_reaction_emoji)
                emoji_name = None
            else:
                emoji_id = None
                emoji_name = str(default_reaction_emoji)

            body.put("default_reaction_emoji", {"emoji_id": emoji_id, "emoji_name": emoji_name})

        response = await self._request(route, json=body, reason=reason)
        assert isinstance(response, dict)
        return response

    async def create_message_thread(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.PermissibleGuildChannel],
        message: snowflakes.SnowflakeishOr[messages_.PartialMessage],
        name: str,
        /,
        *,
        auto_archive_duration: undefined.UndefinedOr[time.Intervalish] = datetime.timedelta(days=1),
        rate_limit_per_user: undefined.UndefinedOr[time.Intervalish] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> typing.Union[channels_.GuildPublicThread, channels_.GuildNewsThread]:
        if isinstance(auto_archive_duration, datetime.timedelta):
            auto_archive_duration = round(auto_archive_duration.total_seconds() / 60)

        route = routes.POST_MESSAGE_THREADS.compile(channel=channel, message=message)
        body = data_binding.JSONObjectBuilder()
        body.put("name", name)
        body.put("auto_archive_duration", auto_archive_duration, conversion=time.timespan_to_int)
        body.put("rate_limit_per_user", rate_limit_per_user, conversion=time.timespan_to_int)

        response = await self._request(route, json=body, reason=reason)

        assert isinstance(response, dict)
        channel = self._entity_factory.deserialize_guild_thread(response)
        assert isinstance(channel, (channels_.GuildPublicThread, channels_.GuildNewsThread))
        return channel

    async def create_thread(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.PermissibleGuildChannel],
        type: typing.Union[channels_.ChannelType, int],
        name: str,
        /,
        *,
        auto_archive_duration: undefined.UndefinedOr[time.Intervalish] = datetime.timedelta(days=1),
        invitable: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        rate_limit_per_user: undefined.UndefinedOr[time.Intervalish] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> channels_.GuildThreadChannel:
        if isinstance(auto_archive_duration, datetime.timedelta):
            auto_archive_duration = round(auto_archive_duration.total_seconds() / 60)

        route = routes.POST_CHANNEL_THREADS.compile(channel=channel)
        body = data_binding.JSONObjectBuilder()
        body.put("name", name)
        body.put("auto_archive_duration", auto_archive_duration, conversion=time.timespan_to_int)
        body.put("type", type)
        body.put("invitable", invitable)
        body.put("rate_limit_per_user", rate_limit_per_user, conversion=time.timespan_to_int)

        response = await self._request(route, json=body, reason=reason)

        assert isinstance(response, dict)
        return self._entity_factory.deserialize_guild_thread(response)

    async def create_forum_post(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.PermissibleGuildChannel],
        name: str,
        /,
        # Message arguments
        content: undefined.UndefinedOr[typing.Any] = undefined.UNDEFINED,
        *,
        attachment: undefined.UndefinedOr[files.Resourceish] = undefined.UNDEFINED,
        attachments: undefined.UndefinedOr[typing.Sequence[files.Resourceish]] = undefined.UNDEFINED,
        component: undefined.UndefinedOr[special_endpoints.ComponentBuilder] = undefined.UNDEFINED,
        components: undefined.UndefinedOr[typing.Sequence[special_endpoints.ComponentBuilder]] = undefined.UNDEFINED,
        embed: undefined.UndefinedOr[embeds_.Embed] = undefined.UNDEFINED,
        embeds: undefined.UndefinedOr[typing.Sequence[embeds_.Embed]] = undefined.UNDEFINED,
        sticker: undefined.UndefinedOr[snowflakes.SnowflakeishOr[stickers_.PartialSticker]] = undefined.UNDEFINED,
        stickers: undefined.UndefinedOr[
            snowflakes.SnowflakeishSequence[stickers_.PartialSticker]
        ] = undefined.UNDEFINED,
        tts: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        mentions_everyone: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        mentions_reply: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        user_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[users.PartialUser], bool]
        ] = undefined.UNDEFINED,
        role_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[guilds.PartialRole], bool]
        ] = undefined.UNDEFINED,
        flags: typing.Union[undefined.UndefinedType, int, messages_.MessageFlag] = undefined.UNDEFINED,
        # Channel arguments
        auto_archive_duration: undefined.UndefinedOr[time.Intervalish] = datetime.timedelta(days=1),
        rate_limit_per_user: undefined.UndefinedOr[time.Intervalish] = undefined.UNDEFINED,
        tags: undefined.UndefinedOr[
            typing.Sequence[snowflakes.SnowflakeishOr[channels_.ForumTag]]
        ] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> channels_.GuildPublicThread:
        if isinstance(auto_archive_duration, datetime.timedelta):
            auto_archive_duration = round(auto_archive_duration.total_seconds() / 60)

        route = routes.POST_CHANNEL_THREADS.compile(channel=channel)

        body = data_binding.JSONObjectBuilder()
        # Channel arguments
        body.put("name", name)
        body.put("auto_archive_duration", auto_archive_duration, conversion=time.timespan_to_int)
        body.put("rate_limit_per_user", rate_limit_per_user, conversion=time.timespan_to_int)
        body.put_snowflake_array("applied_tags", tags)

        # Message arguments
        message_body, form_builder = self._build_message_payload(
            content=content,
            attachment=attachment,
            attachments=attachments,
            component=component,
            components=components,
            embed=embed,
            embeds=embeds,
            sticker=sticker,
            stickers=stickers,
            tts=tts,
            mentions_everyone=mentions_everyone,
            mentions_reply=mentions_reply,
            user_mentions=user_mentions,
            role_mentions=role_mentions,
            flags=flags,
        )
        body.put("message", message_body)

        if form_builder is not None:
            form_builder.add_field("payload_json", self._dumps(body), content_type=_APPLICATION_JSON)
            response = await self._request(route, form_builder=form_builder, reason=reason)
        else:
            response = await self._request(route, json=body, reason=reason)

        assert isinstance(response, dict)
        return self._entity_factory.deserialize_guild_public_thread(response)

    async def join_thread(self, channel: snowflakes.SnowflakeishOr[channels_.GuildTextChannel], /) -> None:
        route = routes.PUT_MY_THREAD_MEMBER.compile(channel=channel)
        await self._request(route)

    async def add_thread_member(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.GuildThreadChannel],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        /,
    ) -> None:
        route = routes.PUT_THREAD_MEMBER.compile(channel=channel, user=user)
        await self._request(route)

    async def leave_thread(self, channel: snowflakes.SnowflakeishOr[channels_.GuildThreadChannel]) -> None:
        route = routes.DELETE_MY_THREAD_MEMBER.compile(channel=channel)
        await self._request(route)

    async def remove_thread_member(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.GuildThreadChannel],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        /,
    ) -> None:
        route = routes.DELETE_THREAD_MEMBER.compile(channel=channel, user=user)
        await self._request(route)

    async def fetch_thread_member(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.GuildThreadChannel],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        /,
    ) -> channels_.ThreadMember:
        route = routes.GET_THREAD_MEMBER.compile(channel=channel, user=user)
        response = await self._request(route)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_thread_member(response)

    async def fetch_thread_members(
        self, channel: snowflakes.SnowflakeishOr[channels_.GuildThreadChannel], /
    ) -> typing.Sequence[channels_.ThreadMember]:
        route = routes.GET_THREAD_MEMBERS.compile(channel=channel)
        response = await self._request(route)
        assert isinstance(response, list)
        return [self._entity_factory.deserialize_thread_member(member) for member in response]

    async def fetch_active_threads(
        self, guild: snowflakes.SnowflakeishOr[guilds.Guild], /
    ) -> typing.Sequence[channels_.GuildThreadChannel]:
        route = routes.GET_ACTIVE_THREADS.compile(guild=guild)
        response = await self._request(route)
        assert isinstance(response, dict)
        members = {
            member.thread_id: member
            for member in map(self._entity_factory.deserialize_thread_member, response["members"])
        }
        return [
            self._entity_factory.deserialize_guild_thread(
                thread, member=members.get(snowflakes.Snowflake(thread["id"]))
            )
            for thread in response["threads"]
        ]

    def _deserialize_public_thread(
        self,
        payload: data_binding.JSONObject,
        *,
        guild_id: undefined.UndefinedOr[snowflakes.Snowflake] = undefined.UNDEFINED,
        member: undefined.UndefinedNoneOr[channels_.ThreadMember] = undefined.UNDEFINED,
    ) -> typing.Union[channels_.GuildNewsThread, channels_.GuildPublicThread]:
        channel = self._entity_factory.deserialize_guild_thread(payload, guild_id=guild_id, member=member)
        assert isinstance(channel, (channels_.GuildNewsThread, channels_.GuildPublicThread))
        return channel

    def fetch_public_archived_threads(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.PermissibleGuildChannel],
        /,
        *,
        before: undefined.UndefinedOr[datetime.datetime] = undefined.UNDEFINED,
    ) -> iterators.LazyIterator[typing.Union[channels_.GuildNewsThread, channels_.GuildPublicThread]]:
        return special_endpoints_impl.GuildThreadIterator(
            deserialize=self._deserialize_public_thread,
            entity_factory=self._entity_factory,
            request_call=self._request,
            route=routes.GET_PUBLIC_ARCHIVED_THREADS.compile(channel=channel),
            before=before.isoformat() if before is not undefined.UNDEFINED else undefined.UNDEFINED,
            before_is_timestamp=True,
        )

    def fetch_private_archived_threads(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.PermissibleGuildChannel],
        /,
        *,
        before: undefined.UndefinedOr[datetime.datetime] = undefined.UNDEFINED,
    ) -> iterators.LazyIterator[channels_.GuildPrivateThread]:
        return special_endpoints_impl.GuildThreadIterator(
            deserialize=self._entity_factory.deserialize_guild_private_thread,
            entity_factory=self._entity_factory,
            request_call=self._request,
            route=routes.GET_PRIVATE_ARCHIVED_THREADS.compile(channel=channel),
            before=before.isoformat() if before is not undefined.UNDEFINED else undefined.UNDEFINED,
            before_is_timestamp=True,
        )

    def fetch_joined_private_archived_threads(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.PermissibleGuildChannel],
        /,
        *,
        before: undefined.UndefinedOr[
            snowflakes.SearchableSnowflakeishOr[channels_.GuildThreadChannel]
        ] = undefined.UNDEFINED,
    ) -> iterators.LazyIterator[channels_.GuildPrivateThread]:
        if before is undefined.UNDEFINED:
            start: undefined.UndefinedOr[str] = undefined.UNDEFINED

        elif isinstance(before, datetime.datetime):
            start = str(snowflakes.Snowflake.from_datetime(before))

        else:
            start = str(snowflakes.Snowflake(before))

        return special_endpoints_impl.GuildThreadIterator(
            deserialize=self._entity_factory.deserialize_guild_private_thread,
            entity_factory=self._entity_factory,
            request_call=self._request,
            route=routes.GET_JOINED_PRIVATE_ARCHIVED_THREADS.compile(channel=channel),
            before=start,
            before_is_timestamp=False,
        )

    async def reposition_channels(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        positions: typing.Mapping[int, snowflakes.SnowflakeishOr[channels_.GuildChannel]],
    ) -> None:
        route = routes.PATCH_GUILD_CHANNELS.compile(guild=guild)
        body = [{"id": str(int(channel)), "position": pos} for pos, channel in positions.items()]
        await self._request(route, json=body)

    async def fetch_member(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], user: snowflakes.SnowflakeishOr[users.PartialUser]
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

    async def fetch_my_member(self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild]) -> guilds.Member:
        route = routes.GET_MY_GUILD_MEMBER.compile(guild=guild)
        response = await self._request(route)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_member(response, guild_id=snowflakes.Snowflake(guild))

    async def search_members(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], name: str
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
        nickname: undefined.UndefinedNoneOr[str] = undefined.UNDEFINED,
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
        body.put("nick", nickname)
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
        delete_message_seconds: undefined.UndefinedOr[time.Intervalish] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        if isinstance(delete_message_seconds, datetime.timedelta):
            delete_message_seconds = delete_message_seconds.total_seconds()

        body = data_binding.JSONObjectBuilder()
        body.put("delete_message_seconds", delete_message_seconds)
        route = routes.PUT_GUILD_BAN.compile(guild=guild, user=user)
        await self._request(route, json=body, reason=reason)

    def ban_member(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        *,
        delete_message_seconds: undefined.UndefinedOr[time.Intervalish] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> typing.Coroutine[typing.Any, typing.Any, None]:
        return self.ban_user(guild, user, delete_message_seconds=delete_message_seconds, reason=reason)

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
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], user: snowflakes.SnowflakeishOr[users.PartialUser]
    ) -> guilds.GuildBan:
        route = routes.GET_GUILD_BAN.compile(guild=guild, user=user)
        response = await self._request(route)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_guild_member_ban(response)

    def fetch_bans(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        /,
        *,
        newest_first: bool = False,
        start_at: undefined.UndefinedOr[snowflakes.SearchableSnowflakeishOr[users.PartialUser]] = undefined.UNDEFINED,
    ) -> iterators.LazyIterator[guilds.GuildBan]:
        if start_at is undefined.UNDEFINED:
            start_at = snowflakes.Snowflake.max() if newest_first else snowflakes.Snowflake.min()
        elif isinstance(start_at, datetime.datetime):
            start_at = snowflakes.Snowflake.from_datetime(start_at)
        else:
            start_at = int(start_at)

        return special_endpoints_impl.GuildBanIterator(
            self._entity_factory, self._request, guild, newest_first, str(start_at)
        )

    async def fetch_roles(self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild]) -> typing.Sequence[guilds.Role]:
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
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], role: snowflakes.SnowflakeishOr[guilds.PartialRole]
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
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild]
    ) -> typing.Sequence[voices.VoiceRegion]:
        route = routes.GET_GUILD_VOICE_REGIONS.compile(guild=guild)
        response = await self._request(route)
        assert isinstance(response, list)
        return [
            self._entity_factory.deserialize_voice_region(voice_region_payload) for voice_region_payload in response
        ]

    async def fetch_guild_invites(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild]
    ) -> typing.Sequence[invites.InviteWithMetadata]:
        route = routes.GET_GUILD_INVITES.compile(guild=guild)
        response = await self._request(route)
        assert isinstance(response, list)
        return [self._entity_factory.deserialize_invite_with_metadata(invite_payload) for invite_payload in response]

    async def fetch_integrations(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild]
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
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], template: typing.Union[templates.Template, str]
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
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], template: typing.Union[str, templates.Template]
    ) -> templates.Template:
        template = template if isinstance(template, str) else template.code
        route = routes.DELETE_GUILD_TEMPLATE.compile(guild=guild, template=template)
        response = await self._request(route)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_template(response)

    def slash_command_builder(self, name: str, description: str) -> special_endpoints.SlashCommandBuilder:
        return special_endpoints_impl.SlashCommandBuilder(name, description)

    def context_menu_command_builder(
        self, type: typing.Union[commands.CommandType, int], name: str
    ) -> special_endpoints.ContextMenuCommandBuilder:
        return special_endpoints_impl.ContextMenuCommandBuilder(commands.CommandType(type), name)

    async def fetch_application_command(
        self,
        application: snowflakes.SnowflakeishOr[guilds.PartialApplication],
        command: snowflakes.SnowflakeishOr[commands.PartialCommand],
        guild: undefined.UndefinedOr[snowflakes.SnowflakeishOr[guilds.PartialGuild]] = undefined.UNDEFINED,
    ) -> commands.PartialCommand:
        if guild is undefined.UNDEFINED:
            route = routes.GET_APPLICATION_COMMAND.compile(application=application, command=command)

        else:
            route = routes.GET_APPLICATION_GUILD_COMMAND.compile(application=application, guild=guild, command=command)

        response = await self._request(route)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_command(
            response, guild_id=snowflakes.Snowflake(guild) if guild is not undefined.UNDEFINED else None
        )

    def _deserialize_command_list(
        self, command_payloads: data_binding.JSONArray, guild_id: typing.Optional[snowflakes.Snowflake]
    ) -> typing.List[commands.PartialCommand]:
        command_objs: typing.List[commands.PartialCommand] = []
        for payload in command_payloads:
            try:
                command_objs.append(self._entity_factory.deserialize_command(payload, guild_id=guild_id))

            except errors.UnrecognisedEntityError:
                pass

        return command_objs

    async def fetch_application_commands(
        self,
        application: snowflakes.SnowflakeishOr[guilds.PartialApplication],
        guild: undefined.UndefinedOr[snowflakes.SnowflakeishOr[guilds.PartialGuild]] = undefined.UNDEFINED,
    ) -> typing.Sequence[commands.PartialCommand]:
        if guild is undefined.UNDEFINED:
            route = routes.GET_APPLICATION_COMMANDS.compile(application=application)

        else:
            route = routes.GET_APPLICATION_GUILD_COMMANDS.compile(application=application, guild=guild)

        query = data_binding.StringMapBuilder()
        query.put("with_localizations", True)

        response = await self._request(route, query=query)
        assert isinstance(response, list)
        guild_id = snowflakes.Snowflake(guild) if guild is not undefined.UNDEFINED else None
        return self._deserialize_command_list(response, guild_id)

    async def _create_application_command(
        self,
        application: snowflakes.SnowflakeishOr[guilds.PartialApplication],
        type: typing.Union[commands.CommandType, int],
        name: str,
        description: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        *,
        guild: undefined.UndefinedOr[snowflakes.SnowflakeishOr[guilds.PartialGuild]] = undefined.UNDEFINED,
        options: undefined.UndefinedOr[typing.Sequence[commands.CommandOption]] = undefined.UNDEFINED,
        name_localizations: undefined.UndefinedOr[
            typing.Mapping[typing.Union[locales.Locale, str], str]
        ] = undefined.UNDEFINED,
        description_localizations: undefined.UndefinedOr[
            typing.Mapping[typing.Union[locales.Locale, str], str]
        ] = undefined.UNDEFINED,
        default_member_permissions: typing.Union[
            undefined.UndefinedType, int, permissions_.Permissions
        ] = undefined.UNDEFINED,
        dm_enabled: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        nsfw: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
    ) -> data_binding.JSONObject:
        if guild is undefined.UNDEFINED:
            route = routes.POST_APPLICATION_COMMAND.compile(application=application)

        else:
            route = routes.POST_APPLICATION_GUILD_COMMAND.compile(application=application, guild=guild)

        body = data_binding.JSONObjectBuilder()
        body.put("name", name)
        body.put("description", description)
        body.put("type", type)
        body.put_array("options", options, conversion=self._entity_factory.serialize_command_option)
        body.put("name_localizations", name_localizations)
        body.put("description_localizations", description_localizations)
        body.put("nsfw", nsfw)

        # Discord has some funky behaviour around what 0 means. They consider it to be the same as ADMINISTRATOR,
        # but we consider it to be the same as None for developer sanity reasons
        body.put("default_member_permissions", None if default_member_permissions == 0 else default_member_permissions)
        body.put("dm_permission", dm_enabled)

        response = await self._request(route, json=body)
        assert isinstance(response, dict)
        return response

    async def create_slash_command(
        self,
        application: snowflakes.SnowflakeishOr[guilds.PartialApplication],
        name: str,
        description: str,
        *,
        guild: undefined.UndefinedOr[snowflakes.SnowflakeishOr[guilds.PartialGuild]] = undefined.UNDEFINED,
        options: undefined.UndefinedOr[typing.Sequence[commands.CommandOption]] = undefined.UNDEFINED,
        name_localizations: undefined.UndefinedOr[
            typing.Mapping[typing.Union[locales.Locale, str], str]
        ] = undefined.UNDEFINED,
        description_localizations: undefined.UndefinedOr[
            typing.Mapping[typing.Union[locales.Locale, str], str]
        ] = undefined.UNDEFINED,
        default_member_permissions: typing.Union[
            undefined.UndefinedType, int, permissions_.Permissions
        ] = undefined.UNDEFINED,
        dm_enabled: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        nsfw: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
    ) -> commands.SlashCommand:
        response = await self._create_application_command(
            application=application,
            type=commands.CommandType.SLASH,
            name=name,
            description=description,
            guild=guild,
            options=options,
            name_localizations=name_localizations,
            description_localizations=description_localizations,
            default_member_permissions=default_member_permissions,
            dm_enabled=dm_enabled,
            nsfw=nsfw,
        )
        return self._entity_factory.deserialize_slash_command(
            response, guild_id=snowflakes.Snowflake(guild) if guild is not undefined.UNDEFINED else None
        )

    async def create_context_menu_command(
        self,
        application: snowflakes.SnowflakeishOr[guilds.PartialApplication],
        type: typing.Union[commands.CommandType, int],
        name: str,
        *,
        guild: undefined.UndefinedOr[snowflakes.SnowflakeishOr[guilds.PartialGuild]] = undefined.UNDEFINED,
        name_localizations: undefined.UndefinedOr[
            typing.Mapping[typing.Union[locales.Locale, str], str]
        ] = undefined.UNDEFINED,
        default_member_permissions: typing.Union[
            undefined.UndefinedType, int, permissions_.Permissions
        ] = undefined.UNDEFINED,
        dm_enabled: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        nsfw: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
    ) -> commands.ContextMenuCommand:
        response = await self._create_application_command(
            application=application,
            type=type,
            name=name,
            guild=guild,
            name_localizations=name_localizations,
            default_member_permissions=default_member_permissions,
            dm_enabled=dm_enabled,
            nsfw=nsfw,
        )
        return self._entity_factory.deserialize_context_menu_command(
            response, guild_id=snowflakes.Snowflake(guild) if guild is not undefined.UNDEFINED else None
        )

    async def set_application_commands(
        self,
        application: snowflakes.SnowflakeishOr[guilds.PartialApplication],
        commands: typing.Sequence[special_endpoints.CommandBuilder],
        guild: undefined.UndefinedOr[snowflakes.SnowflakeishOr[guilds.PartialGuild]] = undefined.UNDEFINED,
    ) -> typing.Sequence[commands.PartialCommand]:
        if guild is undefined.UNDEFINED:
            route = routes.PUT_APPLICATION_COMMANDS.compile(application=application)

        else:
            route = routes.PUT_APPLICATION_GUILD_COMMANDS.compile(application=application, guild=guild)

        response = await self._request(route, json=[command.build(self._entity_factory) for command in commands])
        assert isinstance(response, list)
        guild_id = snowflakes.Snowflake(guild) if guild is not undefined.UNDEFINED else None
        return self._deserialize_command_list(response, guild_id)

    async def edit_application_command(
        self,
        application: snowflakes.SnowflakeishOr[guilds.PartialApplication],
        command: snowflakes.SnowflakeishOr[commands.PartialCommand],
        guild: undefined.UndefinedOr[snowflakes.SnowflakeishOr[guilds.PartialGuild]] = undefined.UNDEFINED,
        *,
        name: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        description: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        options: undefined.UndefinedOr[typing.Sequence[commands.CommandOption]] = undefined.UNDEFINED,
        default_member_permissions: typing.Union[
            undefined.UndefinedType, int, permissions_.Permissions
        ] = undefined.UNDEFINED,
        dm_enabled: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        nsfw: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
    ) -> commands.PartialCommand:
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
        body.put("nsfw", nsfw)
        # Discord has some funky behaviour around what 0 means. They consider it to be the same as ADMINISTRATOR,
        # but we consider it to be the same as None for developer sanity reasons
        body.put("default_member_permissions", None if default_member_permissions == 0 else default_member_permissions)
        body.put("dm_permission", dm_enabled)

        response = await self._request(route, json=body)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_command(
            response, guild_id=snowflakes.Snowflake(guild) if guild is not undefined.UNDEFINED else None
        )

    async def delete_application_command(
        self,
        application: snowflakes.SnowflakeishOr[guilds.PartialApplication],
        command: snowflakes.SnowflakeishOr[commands.PartialCommand],
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
        command: snowflakes.SnowflakeishOr[commands.PartialCommand],
    ) -> commands.GuildCommandPermissions:
        route = routes.GET_APPLICATION_COMMAND_PERMISSIONS.compile(
            application=application, guild=guild, command=command
        )
        response = await self._request(route)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_guild_command_permissions(response)

    async def set_application_command_permissions(
        self,
        application: snowflakes.SnowflakeishOr[guilds.PartialApplication],
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        command: snowflakes.SnowflakeishOr[commands.PartialCommand],
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

    def interaction_autocomplete_builder(
        self, choices: typing.Sequence[special_endpoints.AutocompleteChoiceBuilder]
    ) -> special_endpoints.InteractionAutocompleteBuilder:
        return special_endpoints_impl.InteractionAutocompleteBuilder(choices)

    def interaction_message_builder(
        self, type_: typing.Union[base_interactions.ResponseType, int], /
    ) -> special_endpoints.InteractionMessageBuilder:
        return special_endpoints_impl.InteractionMessageBuilder(type=type_)

    def interaction_modal_builder(self, title: str, custom_id: str) -> special_endpoints.InteractionModalBuilder:
        return special_endpoints_impl.InteractionModalBuilder(title=title, custom_id=custom_id)

    async def fetch_interaction_response(
        self, application: snowflakes.SnowflakeishOr[guilds.PartialApplication], token: str
    ) -> messages_.Message:
        route = routes.GET_INTERACTION_RESPONSE.compile(webhook=application, token=token)
        response = await self._request(route, auth=None)
        assert isinstance(response, dict)
        return self._entity_factory.deserialize_message(response)

    async def create_interaction_response(
        self,
        interaction: snowflakes.SnowflakeishOr[base_interactions.PartialInteraction],
        token: str,
        response_type: typing.Union[int, base_interactions.ResponseType],
        content: undefined.UndefinedNoneOr[typing.Any] = undefined.UNDEFINED,
        *,
        flags: typing.Union[int, messages_.MessageFlag, undefined.UndefinedType] = undefined.UNDEFINED,
        tts: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        attachment: undefined.UndefinedNoneOr[files.Resourceish] = undefined.UNDEFINED,
        attachments: undefined.UndefinedNoneOr[typing.Sequence[files.Resourceish]] = undefined.UNDEFINED,
        component: undefined.UndefinedNoneOr[special_endpoints.ComponentBuilder] = undefined.UNDEFINED,
        components: undefined.UndefinedNoneOr[
            typing.Sequence[special_endpoints.ComponentBuilder]
        ] = undefined.UNDEFINED,
        embed: undefined.UndefinedNoneOr[embeds_.Embed] = undefined.UNDEFINED,
        embeds: undefined.UndefinedNoneOr[typing.Sequence[embeds_.Embed]] = undefined.UNDEFINED,
        mentions_everyone: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        user_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[users.PartialUser], bool]
        ] = undefined.UNDEFINED,
        role_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[guilds.PartialRole], bool]
        ] = undefined.UNDEFINED,
    ) -> None:
        route = routes.POST_INTERACTION_RESPONSE.compile(interaction=interaction, token=token)

        data, form = self._build_message_payload(
            content=content,
            attachment=attachment,
            attachments=attachments,
            component=component,
            components=components,
            embed=embed,
            embeds=embeds,
            tts=tts,
            flags=flags,
            mentions_everyone=mentions_everyone,
            user_mentions=user_mentions,
            role_mentions=role_mentions,
        )
        body = data_binding.JSONObjectBuilder()
        body.put("type", response_type)
        body.put("data", data)

        if form is not None:
            form.add_field("payload_json", self._dumps(body), content_type=_APPLICATION_JSON)
            await self._request(route, form_builder=form, auth=None)
        else:
            await self._request(route, json=body, auth=None)

    async def edit_interaction_response(
        self,
        application: snowflakes.SnowflakeishOr[guilds.PartialApplication],
        token: str,
        content: undefined.UndefinedNoneOr[typing.Any] = undefined.UNDEFINED,
        *,
        attachment: undefined.UndefinedNoneOr[
            typing.Union[files.Resourceish, messages_.Attachment]
        ] = undefined.UNDEFINED,
        attachments: undefined.UndefinedNoneOr[
            typing.Sequence[typing.Union[files.Resourceish, messages_.Attachment]]
        ] = undefined.UNDEFINED,
        component: undefined.UndefinedNoneOr[special_endpoints.ComponentBuilder] = undefined.UNDEFINED,
        components: undefined.UndefinedNoneOr[
            typing.Sequence[special_endpoints.ComponentBuilder]
        ] = undefined.UNDEFINED,
        embed: undefined.UndefinedNoneOr[embeds_.Embed] = undefined.UNDEFINED,
        embeds: undefined.UndefinedNoneOr[typing.Sequence[embeds_.Embed]] = undefined.UNDEFINED,
        mentions_everyone: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        user_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[users.PartialUser], bool]
        ] = undefined.UNDEFINED,
        role_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[guilds.PartialRole], bool]
        ] = undefined.UNDEFINED,
    ) -> messages_.Message:
        route = routes.PATCH_INTERACTION_RESPONSE.compile(webhook=application, token=token)

        body, form_builder = self._build_message_payload(
            content=content,
            attachment=attachment,
            attachments=attachments,
            component=component,
            components=components,
            embed=embed,
            embeds=embeds,
            mentions_everyone=mentions_everyone,
            user_mentions=user_mentions,
            role_mentions=role_mentions,
            edit=True,
        )

        if form_builder is not None:
            form_builder.add_field("payload_json", self._dumps(body), content_type=_APPLICATION_JSON)
            response = await self._request(route, form_builder=form_builder, auth=None)
        else:
            response = await self._request(route, json=body, auth=None)

        assert isinstance(response, dict)
        return self._entity_factory.deserialize_message(response)

    async def delete_interaction_response(
        self, application: snowflakes.SnowflakeishOr[guilds.PartialApplication], token: str
    ) -> None:
        route = routes.DELETE_INTERACTION_RESPONSE.compile(webhook=application, token=token)
        await self._request(route, auth=None)

    async def create_autocomplete_response(
        self,
        interaction: snowflakes.SnowflakeishOr[base_interactions.PartialInteraction],
        token: str,
        choices: typing.Sequence[special_endpoints.AutocompleteChoiceBuilder],
    ) -> None:
        route = routes.POST_INTERACTION_RESPONSE.compile(interaction=interaction, token=token)

        body = data_binding.JSONObjectBuilder()
        body.put("type", base_interactions.ResponseType.AUTOCOMPLETE)

        data = data_binding.JSONObjectBuilder()
        data.put("choices", [{"name": choice.name, "value": choice.value} for choice in choices])

        body.put("data", data)
        await self._request(route, json=body, auth=None)

    async def create_modal_response(
        self,
        interaction: snowflakes.SnowflakeishOr[base_interactions.PartialInteraction],
        token: str,
        *,
        title: str,
        custom_id: str,
        component: undefined.UndefinedOr[special_endpoints.ComponentBuilder] = undefined.UNDEFINED,
        components: undefined.UndefinedOr[typing.Sequence[special_endpoints.ComponentBuilder]] = undefined.UNDEFINED,
    ) -> None:
        if undefined.all_undefined(component, components) or not undefined.any_undefined(component, components):
            raise ValueError("Must specify exactly only one of 'component' or 'components'")

        route = routes.POST_INTERACTION_RESPONSE.compile(interaction=interaction, token=token)

        body = data_binding.JSONObjectBuilder()
        body.put("type", base_interactions.ResponseType.MODAL)

        data = data_binding.JSONObjectBuilder()
        data.put("title", title)
        data.put("custom_id", custom_id)

        if component:
            components = (component,)

        data.put_array("components", components, conversion=lambda c: c.build())

        body.put("data", data)

        await self._request(route, json=body, auth=None)

    def build_message_action_row(self) -> special_endpoints.MessageActionRowBuilder:
        return special_endpoints_impl.MessageActionRowBuilder()

    def build_modal_action_row(self) -> special_endpoints.ModalActionRowBuilder:
        return special_endpoints_impl.ModalActionRowBuilder()

    async def fetch_scheduled_event(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        event: snowflakes.SnowflakeishOr[scheduled_events.ScheduledEvent],
        /,
    ) -> scheduled_events.ScheduledEvent:
        route = routes.GET_GUILD_SCHEDULED_EVENT.compile(guild=guild, scheduled_event=event)
        query = data_binding.StringMapBuilder()
        query.put("with_user_count", True)

        response = await self._request(route, query=query)

        assert isinstance(response, dict)
        return self._entity_factory.deserialize_scheduled_event(response)

    async def fetch_scheduled_events(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], /
    ) -> typing.Sequence[scheduled_events.ScheduledEvent]:
        route = routes.GET_GUILD_SCHEDULED_EVENTS.compile(guild=guild)
        query = data_binding.StringMapBuilder()
        query.put("with_user_count", True)

        response = await self._request(route, query=query)

        assert isinstance(response, list)
        return data_binding.cast_variants_array(self._entity_factory.deserialize_scheduled_event, response)

    async def _create_or_edit_scheduled_stage(
        self,
        route: routes.CompiledRoute,
        entity_type: undefined.UndefinedNoneOr[typing.Union[int, scheduled_events.ScheduledEventType]],
        name: undefined.UndefinedOr[str],
        *,
        channel: undefined.UndefinedNoneOr[snowflakes.SnowflakeishOr[channels_.PartialChannel]] = undefined.UNDEFINED,
        location: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        start_time: undefined.UndefinedOr[datetime.datetime] = undefined.UNDEFINED,
        description: undefined.UndefinedNoneOr[str] = undefined.UNDEFINED,
        end_time: undefined.UndefinedNoneOr[datetime.datetime] = undefined.UNDEFINED,
        image: undefined.UndefinedOr[files.Resourceish] = undefined.UNDEFINED,
        privacy_level: undefined.UndefinedOr[
            typing.Union[int, scheduled_events.EventPrivacyLevel]
        ] = undefined.UNDEFINED,
        status: undefined.UndefinedOr[typing.Union[int, scheduled_events.ScheduledEventStatus]] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> data_binding.JSONObject:
        body = data_binding.JSONObjectBuilder()
        body.put_snowflake("channel_id", channel)
        body.put("name", name)
        body.put("privacy_level", privacy_level)
        body.put("scheduled_start_time", start_time, conversion=datetime.datetime.isoformat)
        body.put("scheduled_end_time", end_time, conversion=datetime.datetime.isoformat)
        body.put("description", description)
        body.put("entity_type", entity_type)
        body.put("status", status)

        if image is not undefined.UNDEFINED:
            image_resource = files.ensure_resource(image)
            async with image_resource.stream(executor=self._executor) as stream:
                body.put("image", await stream.data_uri())

        if location is not undefined.UNDEFINED:
            body["entity_metadata"] = {"location": location}

        response = await self._request(route, json=body, reason=reason)
        assert isinstance(response, dict)
        return response

    async def create_external_event(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        name: str,
        /,
        location: str,
        start_time: datetime.datetime,
        end_time: datetime.datetime,
        *,
        description: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        image: undefined.UndefinedOr[files.Resourceish] = undefined.UNDEFINED,
        privacy_level: typing.Union[
            int, scheduled_events.EventPrivacyLevel
        ] = scheduled_events.EventPrivacyLevel.GUILD_ONLY,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> scheduled_events.ScheduledExternalEvent:
        route = routes.POST_GUILD_SCHEDULED_EVENT.compile(guild=guild)
        response = await self._create_or_edit_scheduled_stage(
            route,
            scheduled_events.ScheduledEventType.EXTERNAL,
            name,
            location=location,
            start_time=start_time,
            description=description,
            end_time=end_time,
            image=image,
            privacy_level=privacy_level,
            reason=reason,
        )
        return self._entity_factory.deserialize_scheduled_external_event(response)

    async def create_stage_event(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        channel: snowflakes.SnowflakeishOr[channels_.PartialChannel],
        name: str,
        /,
        start_time: datetime.datetime,
        *,
        description: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        end_time: undefined.UndefinedOr[datetime.datetime] = undefined.UNDEFINED,
        image: undefined.UndefinedOr[files.Resourceish] = undefined.UNDEFINED,
        privacy_level: typing.Union[
            int, scheduled_events.EventPrivacyLevel
        ] = scheduled_events.EventPrivacyLevel.GUILD_ONLY,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> scheduled_events.ScheduledStageEvent:
        route = routes.POST_GUILD_SCHEDULED_EVENT.compile(guild=guild)
        response = await self._create_or_edit_scheduled_stage(
            route,
            scheduled_events.ScheduledEventType.STAGE_INSTANCE,
            name,
            channel=channel,
            start_time=start_time,
            description=description,
            end_time=end_time,
            image=image,
            privacy_level=privacy_level,
            reason=reason,
        )
        return self._entity_factory.deserialize_scheduled_stage_event(response)

    async def create_voice_event(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        channel: snowflakes.SnowflakeishOr[channels_.PartialChannel],
        name: str,
        /,
        start_time: datetime.datetime,
        *,
        description: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        end_time: undefined.UndefinedOr[datetime.datetime] = undefined.UNDEFINED,
        image: undefined.UndefinedOr[files.Resourceish] = undefined.UNDEFINED,
        privacy_level: typing.Union[
            int, scheduled_events.EventPrivacyLevel
        ] = scheduled_events.EventPrivacyLevel.GUILD_ONLY,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> scheduled_events.ScheduledVoiceEvent:
        route = routes.POST_GUILD_SCHEDULED_EVENT.compile(guild=guild)
        response = await self._create_or_edit_scheduled_stage(
            route,
            scheduled_events.ScheduledEventType.VOICE,
            name,
            channel=channel,
            start_time=start_time,
            description=description,
            end_time=end_time,
            image=image,
            privacy_level=privacy_level,
            reason=reason,
        )
        return self._entity_factory.deserialize_scheduled_voice_event(response)

    async def edit_scheduled_event(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        event: snowflakes.SnowflakeishOr[scheduled_events.ScheduledEvent],
        /,
        *,
        channel: undefined.UndefinedNoneOr[snowflakes.SnowflakeishOr[channels_.PartialChannel]] = undefined.UNDEFINED,
        description: undefined.UndefinedNoneOr[str] = undefined.UNDEFINED,
        entity_type: undefined.UndefinedOr[
            typing.Union[int, scheduled_events.ScheduledEventType]
        ] = undefined.UNDEFINED,
        image: undefined.UndefinedOr[files.Resourceish] = undefined.UNDEFINED,
        location: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        name: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        privacy_level: undefined.UndefinedOr[
            typing.Union[int, scheduled_events.EventPrivacyLevel]
        ] = undefined.UNDEFINED,
        start_time: undefined.UndefinedOr[datetime.datetime] = undefined.UNDEFINED,
        end_time: undefined.UndefinedNoneOr[datetime.datetime] = undefined.UNDEFINED,
        status: undefined.UndefinedOr[typing.Union[int, scheduled_events.ScheduledEventStatus]] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> scheduled_events.ScheduledEvent:
        route = routes.PATCH_GUILD_SCHEDULED_EVENT.compile(guild=guild, scheduled_event=event)

        if entity_type is not undefined.UNDEFINED:
            entity_type = scheduled_events.ScheduledEventType(entity_type)

            # Yes this does have to be explicitly set to None when changing to EXTERNAL
            if entity_type is scheduled_events.ScheduledEventType.EXTERNAL and channel is undefined.UNDEFINED:
                channel = None

        response = await self._create_or_edit_scheduled_stage(
            route,
            entity_type,
            name,
            channel=channel,
            start_time=start_time,
            description=description,
            end_time=end_time,
            image=image,
            location=location,
            privacy_level=privacy_level,
            status=status,
            reason=reason,
        )
        return self._entity_factory.deserialize_scheduled_event(response)

    async def delete_scheduled_event(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        event: snowflakes.SnowflakeishOr[scheduled_events.ScheduledEvent],
        /,
    ) -> None:
        route = routes.DELETE_GUILD_SCHEDULED_EVENT.compile(guild=guild, scheduled_event=event)

        await self._request(route)

    def fetch_scheduled_event_users(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        event: snowflakes.SnowflakeishOr[scheduled_events.ScheduledEvent],
        /,
        *,
        newest_first: bool = False,
        start_at: undefined.UndefinedOr[snowflakes.SearchableSnowflakeishOr[users.PartialUser]] = undefined.UNDEFINED,
    ) -> iterators.LazyIterator[scheduled_events.ScheduledEventUser]:
        if start_at is undefined.UNDEFINED:
            start_at = snowflakes.Snowflake.max() if newest_first else snowflakes.Snowflake.min()
        elif isinstance(start_at, datetime.datetime):
            start_at = snowflakes.Snowflake.from_datetime(start_at)
        else:
            start_at = int(start_at)

        return special_endpoints_impl.ScheduledEventUserIterator(
            self._entity_factory, self._request, newest_first, str(start_at), guild, event
        )
