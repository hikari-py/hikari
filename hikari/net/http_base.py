#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019
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
import json as libjson
import typing

import aiohttp

from hikari import errors
from hikari.internal_utilities import data_structures
from hikari.internal_utilities import date_helpers
from hikari.internal_utilities import logging_helpers
from hikari.internal_utilities import transformations
from hikari.internal_utilities import unspecified
from hikari.internal_utilities import user_agent
from hikari.net import opcodes
from hikari.net import rates

#: Format string for the default Discord API URL.
_DISCORD_API_URI_FORMAT = "https://discordapp.com/api/v{VERSION}"

# Headers for rate limiting
_ACCEPT = "Accept"
_APPLICATION_JSON = "application/json"
_DATE = "Date"
_GRAINULARITY = "millisecond"
_GRAINULARITY_MULTIPLIER = 1 / 1000
_RETRY_AFTER = "Retry-After"
_USER_AGENT = "User-Agent"
_X_RATELIMIT_GLOBAL = "X-RateLimit-Global"
_X_RATELIMIT_LIMIT = "X-RateLimit-Limit"
_X_RATELIMIT_PRECISION = "X-RateLimit-Precision"
_X_RATELIMIT_REMAINING = "X-RateLimit-Remaining"
_X_RATELIMIT_RESET = "X-RateLimit-Reset"
_X_RATELIMIT_RESET_AFTER = "X-RateLimit-Reset-After"
_X_RATELIMIT_LOCALS = [_X_RATELIMIT_LIMIT, _X_RATELIMIT_REMAINING, _X_RATELIMIT_RESET, _DATE]

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


class BaseHTTPClient:
    """
    The core low level logic for any HTTP components that require rate-limiting and consistent logging to be
    implemented.

    Any HTTP components should derive their implementation from this class.
    """

    __slots__ = [
        "_correlation_id",
        "allow_redirects",
        "buckets",
        "base_uri",
        "global_rate_limit",
        "max_retries",
        "session",
        "authorization",
        "logger",
        "loop",
        "user_agent",
    ]

    #: The target API version.
    VERSION = 7

    def __init__(
        self,
        *,
        loop: asyncio.AbstractEventLoop = None,
        allow_redirects: bool = False,
        max_retries: int = 5,
        token: str = unspecified.UNSPECIFIED,
        base_uri: str = _DISCORD_API_URI_FORMAT.format(VERSION=VERSION),
        **aiohttp_arguments,
    ) -> None:
        """
        Args:
            loop:
                the asyncio event loop to run on.
            token:
                the token to use for authentication. This should not start with `Bearer` or `Bot`. If this is not 
                specified, no Authentication is used by default. This enables this client to be used by endpoints that 
                do not require active authentication.
            allow_redirects:
                defaults to False for security reasons. If you find you are receiving multiple redirection responses
                causing requests to fail, it is probably worth enabling this.
            max_retries:
                The max number of times to retry in certain scenarios before giving up on making the request.
            base_uri:
                optional HTTP API base URI to hit. If unspecified, this defaults to Discord's API URI. This exists for
                the purpose of mocking for functional testing. Any URI should NOT end with a trailing forward slash, and
                any instance of `{VERSION}` in the URL will be replaced.
            **aiohttp_arguments:
                additional arguments to pass to the internal :class:`aiohttp.ClientSession` constructor used for making
                HTTP requests.
        """
        # Used for internal bookkeeping
        self._correlation_id = 0
        #: The asyncio event loop to run on.
        self.loop = loop or asyncio.get_running_loop()
        #: Whether to allow redirects or not.
        self.allow_redirects = allow_redirects
        #: Local rate limit buckets.
        self.buckets: typing.Dict[Resource, rates.VariableTokenBucket] = {}
        #: The base URI to target.
        self.base_uri = base_uri
        #: The global rate limit bucket.
        self.global_rate_limit = rates.TimedLatchBucket(loop=self.loop)
        #: Max number of times to retry before giving up.
        self.max_retries = max_retries
        #: The HTTP session to target.
        self.session = aiohttp.ClientSession(**aiohttp_arguments)
        #: The session `Authorization` header to use.
        if token is unspecified.UNSPECIFIED:
            self.authorization = None
        elif "." in token:
            self.authorization = f"Bot {token}"
        else:
            self.authorization = f"Bearer {token}"
        #: The logger to use for this object.
        self.logger = logging_helpers.get_named_logger(self)
        #: User agent to use
        self.user_agent = user_agent.user_agent()

    async def close(self):
        """
        Close the HTTP connection.
        """
        await self.session.close()

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
            :class:`hikari.core.utils.custom_types.ObjectProxy`. This means that you can use the dict as a regular dict,
            or use "JavaScript"-like dot-notation to access members.

            .. code-block:: python

                d = ObjectProxy(...)
                assert d.foo[1].bar == d["foo"][1]["bar"]
        """
        resource = Resource(self.base_uri, method, path, **kwargs)

        while True:
            try:
                result = await self._request_once(
                    resource=resource, query=query, headers=headers, data=data, json=json, reason=reason
                )
            except _RateLimited:
                # If we are uploading files with io objects in a form body, we need to reset the seeks to 0 to ensure
                # we can re-read the buffer
                for seekable_resource in re_seekable_resources:
                    seekable_resource.seek(0)
            else:
                return result

    async def _request_once(
        self, *, resource, query=None, headers=None, data=None, json=None, reason=None
    ) -> typing.Any:
        headers = headers if headers else {}
        query = query if query else {}

        headers.setdefault(_USER_AGENT, self.user_agent)
        headers.setdefault(_ACCEPT, _APPLICATION_JSON)
        # https://github.com/discordapp/discord-api-docs/pull/1064
        headers.setdefault(_X_RATELIMIT_PRECISION, _GRAINULARITY)

        # Prevent inconsistencies causing weird behaviour: check both args.
        if reason is not None and reason is not unspecified.UNSPECIFIED:
            headers.setdefault("X-Audit-Log-Reason", reason)

        if self.authorization is not None:
            headers.setdefault("Authorization", self.authorization)

        # Wait on the global bucket
        await self.global_rate_limit.acquire(self._log_rate_limit_already_in_progress, bucket_id=None)

        if resource in self.buckets:
            await self.buckets[resource].acquire(self._log_rate_limit_already_in_progress, resource=resource)

        self._correlation_id += 1
        self.logger.debug("[%s] %s %s", self._correlation_id, resource.method, resource.uri)

        async with self.session.request(
            resource.method,
            url=resource.uri,
            headers=headers,
            data=data,
            json=json,
            allow_redirects=self.allow_redirects,
            params=query,
        ) as r:
            self.logger.debug(
                "[%s] %s %s %s content_type=%s size=%s",
                self._correlation_id,
                resource.uri,
                r.status,
                r.reason,
                r.content_type,
                r.content_length,
            )

            headers = r.headers
            status = opcodes.HTTPStatus(r.status)
            body = await r.read()

            if r.content_type == "application/json":
                body = libjson.loads(body, object_hook=data_structures.ObjectProxy)
            elif r.content_type in ("text/plain", "text/html"):
                # Cloudflare commonly will cause text/html (e.g. Discord is down)
                body = body.decode()

        # Do this pre-emptively before anything else can fail.
        if self._is_rate_limited(resource, r.status, headers, body):
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
        self.logger.debug("a %s is already active, and the call is being    suspended", name)

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
        is_global = headers.get(_X_RATELIMIT_GLOBAL) == "true"
        is_being_rate_limited = response_code == opcodes.HTTPStatus.TOO_MANY_REQUESTS

        # assume that is_global only ever occurs on TOO_MANY_REQUESTS response codes.
        if is_global and is_being_rate_limited:
            # Retry-after is always in milliseconds.
            # This is only in the body if we get ratelimited, which is a pain, but who
            # could expect an API to have consistent behaviour, amirite?
            retry_after = body.get("retry_after", 0) * _GRAINULARITY_MULTIPLIER
            self.global_rate_limit.lock(retry_after)

        if all(header in headers for header in _X_RATELIMIT_LOCALS):
            # If we don't get all the info we need, just forget about the rate limit as we can't act on missing
            # information.
            now = date_helpers.parse_http_date(headers[_DATE]).timestamp()
            total = transformations.nullable_cast(headers.get(_X_RATELIMIT_LIMIT), int)
            # https://github.com/discordapp/discord-api-docs/pull/1064
            reset_after = transformations.nullable_cast(headers.get(_X_RATELIMIT_RESET_AFTER), float) or 0
            reset_at = now + reset_after
            remaining = transformations.nullable_cast(headers.get(_X_RATELIMIT_REMAINING), int)

            # This header only exists if we get a TOO_MANY_REQUESTS first, annoyingly, and it isn't
            # in the body...
            retry_after = transformations.nullable_cast(headers.get(_RETRY_AFTER), float)
            retry_after = retry_after / 1_000 if retry_after is not None else reset_at - now

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


__all__ = ["BaseHTTPClient"]
