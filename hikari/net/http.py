#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Implementation of the V7 HTTP REST API with rate-limiting.
"""
import json
import logging

import aiohttp
import multidict

from hikari import errors
from hikari.compat import asyncio
from hikari.compat import typing
from hikari.net import opcodes
from hikari.net import rates

#: Format string for the default Discord API URL.
from hikari.net import utils
from hikari.net.utils import Resource

DISCORD_API_URI_FORMAT = "https://discordapp.com/api/v{VERSION}"

# Headers for rate limiting
_DATE = "Date"
_X_RATELIMIT_GLOBAL = "X-RateLimit-Global"
_X_RATELIMIT_LIMIT = "X-RateLimit-Limit"
_X_RATELIMIT_REMAINING = "X-RateLimit-Remaining"
_X_RATELIMIT_RESET = "X-RateLimit-Reset"
_X_RATELIMIT_LOCALS = [_X_RATELIMIT_LIMIT, _X_RATELIMIT_REMAINING, _X_RATELIMIT_RESET, _DATE]


class _RateLimited(Exception):
    """Used as an internal flag. This should not ever be used outside this API."""

    __slots__ = ()


class HTTPConnection:
    """
    Args:
        loop:
            the asyncio event loop to run on.
        token:
            the token to use for authentication. This should not start with `Bearer ` or `Bot ` and will always have
            `Bot ` prepended to it in requests.
        allow_redirects:
            defaults to False for security reasons. If you find you are receiving multiple redirection responses causing
            requests to fail, it is probably worth enabling this.
        max_retries:
            The max number of times to retry in certain scenarios before giving up on making the request.
        base_uri:
            optional HTTP API base URI to hit. If unspecified, this defaults to Discord's API URI. This exists for the
            purpose of mocking for functional testing. Any URI should NOT end with a trailing forward slash, and any
            instance of `{VERSION}` in the URL will be replaced.
        **aiohttp_arguments:
            additional arguments to pass to the internal :class:`aiohttp.ClientSession` constructor used for making
            HTTP requests.
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
        loop: asyncio.AbstractEventLoop,
        allow_redirects: bool = False,
        max_retries: int = 5,
        token: str,
        base_uri: str = DISCORD_API_URI_FORMAT.format(VERSION=VERSION),
        **aiohttp_arguments,
    ) -> None:
        #: Used for internal bookkeeping
        self._correlation_id = 0
        #: Whether to allow redirects or not.
        self.allow_redirects = allow_redirects
        #: Local rate limit buckets.
        self.buckets: typing.Dict[Resource, rates.VariableTokenBucket] = {}
        #: The base URI to target.
        self.base_uri = base_uri
        #: The global rate limit bucket.
        self.global_rate_limit = rates.TimedLatchBucket(loop=loop)
        #: Max number of times to retry before giving up.
        self.max_retries = max_retries
        #: The HTTP session to target.
        self.session = aiohttp.ClientSession(loop=loop, **aiohttp_arguments)
        #: The session `Authorization` header to use.
        self.authorization = "Bot " + token
        #: The logger to use for this object.
        self.logger = logging.getLogger(type(self).__name__)
        #: The asyncio event loop to run on.
        self.loop = loop
        #: User agent to use
        self.user_agent = utils.user_agent()

    async def close(self):
        """
        Close the HTTP connection.
        """
        await self.session.close()

    async def _request(self, method, path, params=None, **kwargs):
        """
        See _request_once for signature.
        """
        kwargs.setdefault("allow_redirects", self.allow_redirects)
        params = params if params else {}
        resource = Resource(self.base_uri, method, path, **params)

        for retry in range(5):
            try:
                result = await self._request_once(retry=retry, resource=resource, **kwargs)
            except _RateLimited:
                continue
            else:
                return result
        raise errors.ClientError(
            resource, None, None, "the request failed too many times and thus was discarded. Try again later."
        )

    async def _request_once(
        self, *, retry=0, resource, headers=None, json_body=None, **kwargs
    ) -> typing.Tuple[opcodes.HTTPStatus, multidict.CIMultiDictProxy, typing.Any]:
        headers = headers if headers else {}

        headers.setdefault("Authorization", self.authorization)
        headers.setdefault("User-Agent", self.user_agent)
        headers.setdefault("Accept", "application/json")

        # Wait on the global bucket
        await self.global_rate_limit.acquire(self._log_rate_limit_already_in_progress, bucket_id=None)

        if resource in self.buckets:
            await self.buckets[resource].acquire(self._log_rate_limit_already_in_progress, resource)

        uri = resource.uri

        self._correlation_id += 1
        self.logger.debug("[try %s - %s] %s %s", retry + 1, self._correlation_id, uri)

        async with self.session.request(resource.method, uri=uri, headers=headers, json=json_body, **kwargs) as resp:
            self.logger.debug(
                "[try %s - %s] %s responded with %s %s containing %s (%s bytes)",
                retry,
                self._correlation_id,
                uri,
                resp.status,
                resp.reason,
                resp.content_type,
                resp.content_length,
            )

            headers = resp.headers
            status = opcodes.HTTPStatus(resp.status)
            body = await resp.read()

            if resp.content_type == "application/json":
                body = json.loads(body)
            elif resp.content_type in ("text/plain", "text/html"):
                # Cloudflare commonly will cause text/html (e.g. Discord is down)
                body = body.decode()

        # Do this pre-emptively before anything else can fail.
        if self._is_rate_limited(resource, resp.status, headers, body):
            raise _RateLimited()

        # 2xx, 3xx do not indicate errors. 4xx indicates an error our side, 5xx is usually the server unable to
        # tell what went wrong.
        if 200 <= status < 400:
            return status, headers, body
        if 400 <= status < 500:
            return self._handle_client_error_response(resource, status, body)
        else:
            # The server returned something we didn't understand and thus was not in the documentation. Treat it as a
            # server error.
            return self._handle_server_error_response(resource, status, body)

    def _log_rate_limit_already_in_progress(self, resource):
        name = f"local rate limit for {resource.bucket}" if resource is not None else "global rate limit"
        self.logger.debug("a %s is already active, and the call is being suspended", name)

    def _log_rate_limit_starting(self, resource, retry_after):
        name = f"local rate limit for {resource.bucket}" if resource is not None else "global rate limit"
        self.logger.debug("a %s has been reached. Try again after %ss", name, retry_after)

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

        # Retry-after is always in milliseconds.
        if is_global and is_being_rate_limited:
            # assume that is_global only ever occurs on TOO_MANY_REQUESTS response codes.
            retry_after = (utils.get_from_map_as(body, "retry_after", float) or 0) / 1_000
            self.global_rate_limit.lock(retry_after)
            self._log_rate_limit_starting(None, retry_after)

        if all(header in headers for header in _X_RATELIMIT_LOCALS):
            # If we don't get all the info we need, just forget about the rate limit as we can't act on missing
            # information.
            now = utils.parse_http_date(headers[_DATE]).timestamp()
            total = utils.get_from_map_as(headers, _X_RATELIMIT_LIMIT, int)
            reset_at = utils.get_from_map_as(headers, _X_RATELIMIT_RESET, float)
            remaining = utils.get_from_map_as(headers, _X_RATELIMIT_REMAINING, int)

            # This header only exists if we get a TOO_MANY_REQUESTS first, annoyingly.
            retry_after = utils.get_from_map_as(headers, "Retry-After", float)
            retry_after = retry_after / 1_000 if retry_after is not None else reset_at - now

            if resource not in self.buckets:
                # Make new bucket first
                bucket = rates.VariableTokenBucket(total, remaining, now, reset_at, self.loop)
                self.buckets[resource] = bucket
            else:
                bucket = self.buckets[resource]
                bucket.update(total, remaining, now, reset_at)

            if bucket.is_limiting:
                self._log_rate_limit_starting(resource, retry_after)

            is_being_rate_limited |= remaining == 0

        return is_being_rate_limited

    @staticmethod
    def _handle_client_error_response(resource, status, body) -> typing.NoReturn:
        # Assume Discord's spec is right and they don't send us random codes we don't know about...
        try:
            error_code = utils.get_from_map_as(body, "code", opcodes.JSONErrorCode, None)
            error_message = body.get("message")
        except AttributeError:
            error_code = None
            error_message = str(body)

        if status == opcodes.HTTPStatus.BAD_REQUEST:
            raise errors.BadRequest(resource, error_code, error_message)
        elif status == opcodes.HTTPStatus.UNAUTHORIZED:
            raise errors.Unauthorized(resource, error_code, error_message)
        elif status == opcodes.HTTPStatus.FORBIDDEN:
            raise errors.Forbidden(resource, error_code, error_message)
        elif status == opcodes.HTTPStatus.NOT_FOUND:
            raise errors.NotFound(resource, error_code, error_message)
        else:
            raise errors.ClientError(resource, status, error_code, error_message)

    @staticmethod
    def _handle_server_error_response(resource, status, body) -> typing.NoReturn:
        if isinstance(body, dict):
            error_message = body.get("message")
        else:
            error_message = str(body)

        raise errors.ServerError(resource, status, error_message)
