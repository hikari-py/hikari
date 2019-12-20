#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekokatt 2019-2020
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
"""
Implementation of the base components required for working with the V7 HTTP REST API with consistent rate-limiting.
"""
from __future__ import annotations

import asyncio
import json as _json
import ssl
import typing

import aiohttp.typedefs

from hikari import errors
from hikari.internal_utilities import containers
from hikari.internal_utilities import dates
from hikari.internal_utilities import transformations
from hikari.internal_utilities import unspecified
from hikari.net import http_client
from hikari.net import opcodes
from hikari.net import rates

# Common strings and values I reused a lot
_ACCEPT_HEADER = "Accept"
_AUTHORIZATION_HEADER = "Authorization"
_APPLICATION_JSON_MIMETYPE = "application/json"
_TEXT_HTML_MIMETYPE = "text/html"
_TEXT_PLAIN_MIMETYPE = "text/plain"
_DATE_HEADER = "Date"
_GRAINULARITY, _GRAINULARITY_MULTIPLIER = "millisecond", 1 / 1_000
_RETRY_AFTER_HEADER = "Retry-After"
_USER_AGENT_HEADER = "User-Agent"
_X_AUDIT_LOG_REASON_HEADER = "X-Audit-Log-Reason"
_X_RATELIMIT_GLOBAL_HEADER = "X-RateLimit-Global"
_X_RATELIMIT_LIMIT_HEADER = "X-RateLimit-Limit"
_X_RATELIMIT_PRECISION_HEADER = "X-RateLimit-Precision"
_X_RATELIMIT_REMAINING_HEADER = "X-RateLimit-Remaining"
_X_RATELIMIT_RESET_HEADER = "X-RateLimit-Reset"
_X_RATELIMIT_RESET_AFTER_HEADER = "X-RateLimit-Reset-After"
_X_RATELIMIT_LOCALS = [
    _X_RATELIMIT_LIMIT_HEADER,
    _X_RATELIMIT_REMAINING_HEADER,
    _X_RATELIMIT_RESET_HEADER,
    _DATE_HEADER,
]

_RequestReturnSignature = typing.Tuple[opcodes.HTTPStatus, typing.Mapping, typing.Any]


class _RateLimited(Exception):
    """Used as an internal flag. This should not ever be used outside this API."""

    __slots__ = ()


class Resource:
    """
    Represents an HTTP request in a format that can be passed around atomically.

    Also provides a mechanism to handle producing a rate limit identifier.

    Note:
        Equality comparisons and hashes occur on the :attr:`bucket` attribute only.
    """

    __slots__ = ("method", "path", "bucket", "uri", "params")

    def __init__(self, base_uri, method, path, **kwargs):
        #: All arguments to interpolate into the URL.
        self.params = kwargs
        #: The HTTP method to use (always upper-case)
        self.method = method.upper()
        #: The HTTP path to use (this can contain format-string style placeholders).
        self.path = path

        #: The full URI to use.
        self.uri = base_uri + path.format(**kwargs)

        bucket_path_str = transformations.format_present_placeholders(self.path, **self.bucket_params)
        #: The bucket identifier. This is used internally to uniquely identify a rate limit bucket.
        self.bucket = f"{self.method} {bucket_path_str}"

    @property
    def bucket_params(self) -> typing.Dict[str, str]:
        """
        Returns a :class:`dict` of any arguments that we will interpolate into the bucket URI.
        """
        params = self.params
        return {
            "webhook_id": params.get("webhook_id"),
            "channel_id": params.get("channel_id"),
            "guild_id": params.get("guild_id"),
        }

    def __hash__(self):
        return hash(self.bucket)

    def __eq__(self, other) -> bool:
        return isinstance(other, Resource) and hash(self) == hash(other)

    def __repr__(self):
        return self.bucket

    __str__ = __repr__


class HTTPAPIBase(http_client.HTTPClient):
    """
    The core low level logic for any HTTP-API components that require rate-limiting and consistent logging to be
    implemented.

    Any HTTP API-specific components should derive their implementation from this class.

    Warning:
        This must be initialized within a coroutine while an event loop is active
        and registered to the current thread.
    """

    __slots__ = [
        "authorization",
        "buckets",
        "base_uri",
        "max_retries",
        "global_rate_limit",
        "json_unmarshaller",
        "json_unmarshaller_object_hook",
    ]

    def __init__(
        self,
        *,
        loop: asyncio.AbstractEventLoop = None,
        allow_redirects: bool = False,
        max_retries: int = 5,
        token: str = None,
        base_uri: str = None,
        json_unmarshaller: typing.Callable = None,
        json_unmarshaller_object_hook: typing.Type[dict] = None,
        json_marshaller: typing.Callable = None,
        connector: aiohttp.BaseConnector = None,
        proxy_headers: aiohttp.typedefs.LooseHeaders = None,
        proxy_auth: aiohttp.BasicAuth = None,
        proxy_url: str = None,
        ssl_context: ssl.SSLContext = None,
        verify_ssl: bool = True,
        timeout: float = None,
    ) -> None:
        """
        Optional Keyword Arguments:
            allow_redirects:
                defaults to False for security reasons. If you find you are receiving multiple redirection responses
                causing requests to fail, it is probably worth enabling this.
            base_uri:
                optional HTTP API base URI to hit. If unspecified, this defaults to Discord's API URI. This exists for
                the purpose of mocking for functional testing. Any URI should NOT end with a trailing forward slash, and
                any instance of `{VERSION}` in the URL will be replaced.
            connector:
                the :class:`aiohttp.BaseConnector` to use for the client session, or `None` if you wish to use the
                default instead.
            json_marshaller:
                a callable that consumes a Python object and returns a JSON-encoded string.
                This defaults to :func:`json.dumps`.
            json_unmarshaller:
                a callable that consumes a JSON-encoded string and returns a Python object.
                This defaults to :func:`json.loads`.
            json_unmarshaller_object_hook:
                the object hook to use to parse a JSON object into a Python object. Defaults to
                :class:`hikari.internal_utilities.data_structures.ObjectProxy`. This means that you can use any
                received dict as a regular dict, or use "JavaScript"-like dot-notation to access members.
            loop:
                the asyncio event loop to run on.
            max_retries:
                The max number of times to retry in certain scenarios before giving up on making the request.
            proxy_auth:
                optional proxy authentication to use.
            proxy_headers:
                optional proxy headers to pass.
            proxy_url:
                optional proxy URL to use.
            ssl_context:
                optional SSL context to use.
            verify_ssl:
                defaulting to True, setting this to false will disable SSL verification.
            timeout:
                optional timeout to apply to individual HTTP requests.
            token:
                the token to use for authentication. This should not start with `Bearer` or `Bot`. If this is not
                specified, no Authentication is used by default. This enables this client to be used by endpoints that
                do not require active authentication.
        """
        super().__init__(
            loop=loop,
            allow_redirects=allow_redirects,
            json_marshaller=json_marshaller,
            connector=connector,
            proxy_headers=proxy_headers,
            proxy_auth=proxy_auth,
            proxy_url=proxy_url,
            ssl_context=ssl_context,
            verify_ssl=verify_ssl,
            timeout=timeout,
        )

        #: Number of times to retry a request before giving up.
        #:
        #: :type: :class:`int`
        self.max_retries = max_retries

        #: Local rate limit buckets.
        #:
        #: :type: :class:`dict` mapping :class:`Resource` keys to :class:`hikari.net.rates.VariableTokenBucket`
        self.buckets: typing.Dict[Resource, rates.VariableTokenBucket] = {}

        #: The base URI to target.
        #:
        #: :type: :class:`str`
        self.base_uri = (base_uri or "https://discordapp.com/api/v{version}").format(version=self.version)

        #: The global rate limit bucket.
        #:
        #: :type: :class:`hikari.net.rates.TimedLatchBucket`
        self.global_rate_limit = rates.TimedLatchBucket(loop=self.loop)

        #: Callable used to unmarshal (deserialize) JSON-encoded payloads into native Python objects.
        #:
        #: Defaults to :func:`json.loads`. You may want to override this if you choose to use a different
        #: JSON library, such as one that is compiled.
        self.json_unmarshaller = json_unmarshaller or _json.loads

        #: Dict-derived type to use for unmarshalled JSON objects.
        #:
        #: For convenience, this defaults to :class:`hikari.internal_utilities.data_structures.ObjectProxy`, since
        #: this provides a benefit of allowing you to use dicts as if they were normal python objects. If you wish
        #: to use another implementation, or just default to :class:`dict` instead, it is worth changing this
        #: attribute.
        self.json_unmarshaller_object_hook = json_unmarshaller_object_hook or containers.ObjectProxy

        if token is None:
            #: The session `Authorization` header to use.
            #:
            #: :type: :class:`str`
            self.authorization: typing.Optional[str] = None
        elif "." in token:
            #: The session `Authorization` header to use.
            #:
            #: :type: :class:`str`
            self.authorization: typing.Optional[str] = f"Bot {token}"
        else:
            #: The session `Authorization` header to use.
            #:
            #: :type: :class:`str`
            self.authorization: typing.Optional[str] = f"Bearer {token}"

    @property
    def version(self) -> int:
        """The version of the client being used."""
        return 7

    async def request(
        self,
        method,
        path,
        re_seekable_resources=(),
        headers=None,
        query=None,
        data=None,
        json=None,
        reason=None,
        **kwargs,
    ) -> typing.Any:
        """
        Send a request to the given path using the given method, parameters, and keyword arguments. If a failure occurs
        that is able to be retried, this will be retried up to 5 times before failing.

        Args:
            method:
                The HTTP method to use.
            path:
                The format-string path to hit. Any `kwargs` will be interpolated into this when making the URL.
            re_seekable_resources:
                Any :class:`io.IOBase`-derived resources that will need their `seek` setting to `0` again before
                retrying in the case of an error we can retry the request for occurring. This is necessary for uploading
                files, etc so that we can read the file more than once without loading several megabytes into memory
                directly.
            headers:
                Any additional headers to send.
            data:
                :class:`aiohttp.FormData` body to send.
            query:
                query-string args to use.
            json:
                JSON body to send.
            reason:
                Audit-log reason.
            kwargs:
                Any arguments to interpolate into the `path`.

        Returns:
            The response.

        Note:
            Any dicts that get parsed in any form of nested structure from a JSON payload will be parsed as an
            :class:`hikari.internal_utilities.data_structures.ObjectProxy`. This means that you can use the dict as a
            regular dict, or use "JavaScript"-like dot-notation to access members.

            .. code-block:: python

                d = ObjectProxy(...)
                assert d.foo[1].bar == d["foo"][1]["bar"]
        """
        resource = Resource(self.base_uri, method, path, **kwargs)

        while True:
            try:
                result = await self.request_once(
                    resource=resource, query=query, headers=headers, data=data, json=json, reason=reason
                )
            except _RateLimited:
                # If we are uploading files with io objects in a form body, we need to reset the seeks to 0 to ensure
                # we can re-read the buffer
                for seekable_resource in re_seekable_resources:
                    seekable_resource.seek(0)
            else:
                return result

    async def request_once(
        self, *, resource, query=None, headers=None, data=None, json=None, reason=None
    ) -> typing.Any:
        headers = headers if headers else {}
        query = query if query else {}

        headers.setdefault(_USER_AGENT_HEADER, self.user_agent)
        headers.setdefault(_ACCEPT_HEADER, _APPLICATION_JSON_MIMETYPE)
        # Allows us to request millisecond durations for greater accuracy as per
        # https://github.com/discordapp/discord-api-docs/pull/1064
        headers.setdefault(_X_RATELIMIT_PRECISION_HEADER, _GRAINULARITY)

        # Prevent inconsistencies causing weird behaviour: check both args.
        if reason is not None and reason is not unspecified.UNSPECIFIED:
            headers.setdefault(_X_AUDIT_LOG_REASON_HEADER, reason)

        if self.authorization is not None:
            headers.setdefault(_AUTHORIZATION_HEADER, self.authorization)

        # Wait on the global bucket
        await self.global_rate_limit.acquire(self._log_rate_limit_already_in_progress, bucket_id=None)

        if resource in self.buckets:
            await self.buckets[resource].acquire(self._log_rate_limit_already_in_progress, resource=resource)

        self.in_count += 1
        self.logger.debug("[%s] %s %s", self.in_count, resource.method, resource.uri)

        kwargs = dict(headers=headers, data=data, json=json, params=query,)

        async with super()._request(resource.method, resource.uri, **kwargs) as response:
            self.logger.debug(
                "[%s] RESPONSE %s %s %s content_type=%s size=%s",
                self.in_count,
                resource.uri,
                response.status,
                response.reason,
                response.content_type,
                response.content_length,
            )
            headers = response.headers
            status = opcodes.HTTPStatus(response.status)
            body = await response.read()

            if response.content_type == _APPLICATION_JSON_MIMETYPE:
                body = self.json_unmarshaller(body, object_hook=self.json_unmarshaller_object_hook)
            elif response.content_type in (_TEXT_PLAIN_MIMETYPE, _TEXT_HTML_MIMETYPE):
                # Cloudflare commonly will cause text/html (e.g. Discord is down)
                self.logger.warning("Received %s-type response. Is Discord down?", response.content_type)
                body = body.decode()

        # Do this pre-emptively before anything else can fail.
        if self._is_rate_limited(resource, response.status, headers, body):
            raise _RateLimited()

        # 2xx, 3xx do not indicate errors. 4xx indicates an error our side, 5xx is usually the server unable to
        # tell what went wrong.
        if 200 <= status < 400:
            return body
        if 400 <= status < 500:
            return self._handle_client_error_response(resource, status, body)

        # The server returned something we didn't understand and thus was not in the documentation. Treat it as a
        # server error.
        return self._handle_server_error_response(resource, status, body)

    def _log_rate_limit_already_in_progress(self, resource):
        name = f"local rate limit for {resource.bucket}" if resource is not None else "global rate limit"
        self.logger.debug("a %s is already active, and the call is being suspended", name)

    def _is_rate_limited(self, resource, response_code, headers, body) -> bool:
        """
        Handle internal rate limits.
        Args:
            resource:
                The bucket to use.
            response_code:
                The HTTP response code given
            headers:
                The headers given in the response.
            body:
                The JSON response body.

        Returns:
            True if we are being rate limited and the current call failed, False if it succeeded and we do not need
            to try again.
        """
        is_global = headers.get(_X_RATELIMIT_GLOBAL_HEADER) == "true"
        is_being_rate_limited = response_code == opcodes.HTTPStatus.TOO_MANY_REQUESTS

        # assume that is_global only ever occurs on TOO_MANY_REQUESTS response codes.
        if is_global and is_being_rate_limited:
            # Retry-after is always in milliseconds.
            # This is only in the body if we get rate limited, which is a pain, but who
            # could expect an API to have consistent behaviour.
            retry_after = body.get("retry_after", 0) * _GRAINULARITY_MULTIPLIER
            self.global_rate_limit.lock(retry_after)

        if all(header in headers for header in _X_RATELIMIT_LOCALS):
            # If we don't get all the info we need, just forget about the rate limit as we can't act on missing
            # information.
            now = dates.parse_http_date(headers[_DATE_HEADER]).timestamp()
            total = transformations.nullable_cast(headers.get(_X_RATELIMIT_LIMIT_HEADER), int)
            # https://github.com/discordapp/discord-api-docs/pull/1064
            reset_after = transformations.nullable_cast(headers.get(_X_RATELIMIT_RESET_AFTER_HEADER), float) or 0
            reset_at = now + reset_after
            remaining = transformations.nullable_cast(headers.get(_X_RATELIMIT_REMAINING_HEADER), int)

            # This header only exists if we get a TOO_MANY_REQUESTS first, annoyingly, and it isn't
            # in the body...
            retry_after = transformations.nullable_cast(headers.get(_RETRY_AFTER_HEADER), float)
            retry_after = retry_after / 1000 if retry_after is not None else reset_at - now

            if resource not in self.buckets:
                # Make new bucket first
                bucket = rates.VariableTokenBucket(total, remaining, now, reset_at, self.loop)
                self.buckets[resource] = bucket
            else:
                bucket = self.buckets[resource]
                bucket.update(total, remaining, now, reset_at)

            self.logger.debug(
                "Rate limit data for %s: "
                "now=%s, total=%s, reset_after=%s, reset_at=%s, remaining=%s, retry_after=%s is_being_rate_limited=%s",
                resource,
                now,
                total,
                reset_after,
                reset_at,
                remaining,
                retry_after,
                is_being_rate_limited,
            )

        return is_being_rate_limited

    @staticmethod
    def _handle_client_error_response(resource, status, body) -> typing.NoReturn:
        # Assume Discord's spec is right and they don't send us random codes we don't know about...
        if isinstance(body, dict):
            error_message = body.get("message")
            try:
                error_code = opcodes.JSONErrorCode(body.get("code"))
            except ValueError:
                error_code = None
        else:
            error_code = None
            error_message = str(body)

        if status == opcodes.HTTPStatus.BAD_REQUEST:
            raise errors.BadRequest(resource, error_code, error_message)
        if status == opcodes.HTTPStatus.UNAUTHORIZED:
            raise errors.Unauthorized(resource, error_code, error_message)
        if status == opcodes.HTTPStatus.FORBIDDEN:
            raise errors.Forbidden(resource, error_code, error_message)
        if status == opcodes.HTTPStatus.NOT_FOUND:
            raise errors.NotFound(resource, error_code, error_message)
        raise errors.ClientError(resource, status, error_code, error_message)

    @staticmethod
    def _handle_server_error_response(resource, status, body) -> typing.NoReturn:
        if isinstance(body, dict):
            error_message = body.get("message")
        else:
            error_message = str(body)

        raise errors.ServerError(resource, status, error_message)


__all__ = ["HTTPAPIBase"]
