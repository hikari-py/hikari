#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Implementation of the V7 HTTP REST API with rate-limiting.
"""
import http
import logging

import aiohttp

from hikari import errors
from hikari.compat import asyncio
from hikari.compat import typing
from hikari.net import rates

#: Format string for the default Discord API URL.
from hikari.net import utils

DISCORD_API_URI_FORMAT = "https://discordapp.com/api/v{VERSION}"

# Headers for rate limiting
_DATE = "Date"
_X_RATELIMIT_GLOBAL = "X-RateLimit-Global"
_X_RATELIMIT_LIMIT = "X-RateLimit-Limit"
_X_RATELIMIT_REMAINING = "X-RateLimit-Remaining"
_X_RATELIMIT_RESET = "X-RateLimit-Reset"
_X_RATELIMIT_LOCALS = [_X_RATELIMIT_LIMIT, _X_RATELIMIT_REMAINING, _X_RATELIMIT_RESET, _DATE]

# Used as a return type if we got rate limited and interrupted.
_RATE_LIMITED_SENTINEL = object()


class Resource:
    """
    Represents an HTTP request in a format that can be passed around atomically.

    Also provides a mechanism to handle producing a rate limit identifier.
    """

    __slots__ = ("method", "path", "params", "bucket")

    def __init__(self, method, path, **kwargs):
        #: The HTTP method to use (always upper-case)
        self.method = method.upper()
        #: The HTTP path to use (this can contain format-string style placeholders).
        self.path = path
        #: Any parameters to later interpolate into `path`.
        self.params = kwargs
        #: The bucket. This is a combination of the method, uninterpolated path, and optional `webhook_id`, `guild_id`
        #: and `channel_id`, and is how the hash code for this route is produced. The hash code is used to determine
        #: the bucket to use for local rate limiting in the HTTP component.
        self.bucket = "{0.method} {0.path} {0.webhook_id} {0.guild_id} {0.channel_id}".format(self)

    #: The webhook ID, or `None` if it is not present.
    webhook_id = property(lambda self: self.params.get("webhook_id"))
    #: The guild ID, or `None` if it is not present.
    guild_id = property(lambda self: self.params.get("guild_id"))
    #: The channel ID, or `None` if it is not present.
    channel_id = property(lambda self: self.params.get("channel_id"))

    def __hash__(self):
        return hash(self.bucket)

    def get_uri(self, base_uri):
        """Return the interpolated path concatenated onto the end of the `base_uri` parameter."""
        return base_uri + self.path.format(**self.params)


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
        base_uri:
            optional HTTP API base URI to hit. If unspecified, this defaults to Discord's API URI. This exists for the
            purpose of mocking for functional testing. Any URI should NOT end with a trailing forward slash, and any
            instance of `{VERSION}` in the URL will be replaced.
        **aiohttp_arguments:
            additional arguments to pass to the internal :class:`aiohttp.ClientSession` constructor used for making
            HTTP requests.
    """

    #: The target API version.
    VERSION = 7

    # Number of times to wait for a rate limit and then try again before giving up. This should never happen unless
    # the user is doing something mad enough to cause rate limits to immediately occur again after finishing
    # repeatedly.
    _RATELIMIT_RETRIES = 5

    def __init__(
        self,
        *,
        loop: asyncio.AbstractEventLoop,
        allow_redirects: bool = False,
        token: str,
        base_uri: str = DISCORD_API_URI_FORMAT.format(VERSION=VERSION),
        **aiohttp_arguments,
    ) -> None:
        # Used for internal bookkeeping
        self._correlation_id = 0
        #: Whether to allow redirects or not.
        self.allow_redirects = allow_redirects
        #: Local rate limit buckets.
        self.buckets: typing.Dict[Resource, rates.VariableTokenBucket] = {}
        #: The base URI to target.
        self.base_uri = base_uri
        #: The global rate limit bucket.
        self.global_rate_limit = rates.TimedLatchBucket(loop=loop)
        #: The HTTP session to target.
        self.session = aiohttp.ClientSession(loop=loop, **aiohttp_arguments)
        #: The session `Authorization` header to use.
        self.authorization = "Bot " + token
        #: The logger to use for this object.
        self.logger = logging.getLogger(type(self).__name__)
        #: The asyncio event loop to run on.
        self.loop = loop

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
        resource = Resource(method, path, **params)

        for retry in range(self._RATELIMIT_RETRIES):
            result = await self._request_once(retry=retry, resource=resource, **kwargs)
            if result is not _RATE_LIMITED_SENTINEL:
                break
        else:
            raise errors.DiscordHTTPError("the request failed too many times and thus was discarded. Try again later.")

        return result

    async def _request_once(self, *, retry=0, resource, headers=None, json_body=None, **kwargs):
        headers = headers if headers else {}

        headers.setdefault("Authorization", self.authorization)

        # Wait on the global bucket
        await self.global_rate_limit.acquire(self._log_rate_limit_already_in_progress, bucket_id=None)

        if resource in self.buckets:
            await self.buckets[resource].acquire(self._log_rate_limit_already_in_progress, resource)

        uri = resource.get_uri(self.base_uri)

        self._correlation_id += 1
        self.logger.debug("[%s/%s - %s] %s %s", retry, self._RATELIMIT_RETRIES, self._correlation_id, uri)

        async with self.session.request(resource.method, uri=uri, headers=headers, json=json_body, **kwargs) as resp:
            self.logger.debug(
                "[%s/%s - %s] %s responded with %s %s containing %s (%s bytes)",
                retry,
                self._RATELIMIT_RETRIES,
                self._correlation_id,
                uri,
                resp.status,
                resp.reason,
                resp.content_type,
                resp.content_length,
            )

            headers = resp.headers

            # Expect JSON for now...
            body = await resp.json()

        # Do this pre-emptively before anything else can fail.
        if self._is_rate_limited(resource, resp.status, headers, body):
            return _RATE_LIMITED_SENTINEL

        # TODO: HANDLE PARSE REQUEST CODE.
        # TODO: HANDLE PARSE JSON RESPONSE ERROR IF IT EXISTS.
        # TODO: HANDLE PARSE JSON RESPONSE IF NOT AN ERROR.
        # TODO: ANY OTHER STUFF I NEED TO DO TO FINISH THIS PROCESS.
        # TODO: RETURN RESPONSE.

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
        is_being_rate_limited = response_code == http.HTTPStatus.TOO_MANY_REQUESTS

        if is_global and is_being_rate_limited:
            # assume that is_global only ever occurs on TOO_MANY_REQUESTS response codes.
            retry_after = utils.get_from_map_as(body, "retry_after", float)
            self.global_rate_limit.lock(retry_after)
            self._log_rate_limit_starting(None, retry_after)

        if all(headers[k] is not None for k in _X_RATELIMIT_LOCALS):
            # If we don't get all the info we need, just forget about the rate limit as we can't act on missing
            # information.
            now = utils.parse_http_date(headers[_DATE]).timestamp()
            total = utils.get_from_map_as(headers, _X_RATELIMIT_LIMIT, int)
            reset_at = utils.get_from_map_as(headers, _X_RATELIMIT_RESET, float)
            remaining = utils.get_from_map_as(headers, _X_RATELIMIT_REMAINING, int)

            # This header only exists if we get a TOO_MANY_REQUESTS first.
            retry_after = headers.get("Retry-After", reset_at - now)

            if resource not in self.buckets:
                # Make new bucket first
                bucket = rates.VariableTokenBucket(total, remaining, now, reset_at, self.loop)
                self.buckets[resource] = bucket
            else:
                bucket = self.buckets[resource]
                bucket.update(total, remaining, now, reset_at)

            if bucket.is_limiting:
                self._log_rate_limit_starting(resource, retry_after)

            is_being_rate_limited = True

        return is_being_rate_limited
