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


class HTTPLogger(logging.LoggerAdapter):
    """
    Internal functionality to log HTTP requests in a sane way.
    """

    def process(self, msg, kwargs):
        # Format into key value pairs within "[]"s if there are extras passed.
        extra = kwargs.pop("extra", {})
        extra.update(self.extra)
        extra = ((k, v() if callable(v) else v) for k, v in extra.items())
        extra = (f"{k!r}={v!r}" for k, v in extra)
        extra = extra and f"[{', '.join(extra)}] " or ""
        return f"{extra}{msg}", kwargs


_DATE = "Date"
_X_RATELIMIT_GLOBAL = "X-RateLimit-Global"
_X_RATELIMIT_LIMIT = "X-RateLimit-Limit"
_X_RATELIMIT_REMAINING = "X-RateLimit-Remaining"
_X_RATELIMIT_RESET = "X-RateLimit-Reset"
_X_RATELIMIT_LOCALS = [_X_RATELIMIT_LIMIT, _X_RATELIMIT_REMAINING, _X_RATELIMIT_RESET, _DATE]


class HTTP:
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
        self.allow_redirects = allow_redirects
        self.buckets: typing.Dict[str, rates.VariableTokenBucket] = {}
        self.base_uri = base_uri
        self.global_rate_limit = rates.TimedLatchBucket(loop=loop)
        self.session = aiohttp.ClientSession(loop=loop, **aiohttp_arguments)
        self.token = "Bot " + token
        self.logger = HTTPLogger(
            logging.getLogger(type(self).__name__), extra={"request": lambda: self._correlation_id}
        )
        #: The asyncio event loop to run on.
        self.loop = loop

    @staticmethod
    def _get_bucket_id(
        method: str, path: str, *, channel_id: int = None, guild_id: int = None, webhook_id: int = None, **_
    ):
        path = path.format(channel_id=channel_id, guild_id=guild_id, webhook_id=webhook_id)
        return f"{method}:{path}"

    async def _request(
        self,
        method: str,
        path_format: str,
        *,
        headers: dict = None,
        params: dict = None,
        json_body: dict = None,
        **kwargs,
    ) -> None:
        """

        Args:
            method:
                the HTTP method to use.
            path_format:
                the HTTP path to use, as a python format string.
            headers:
                any additional headers to use.
            params:
                an optional dict of parameters to interpolate into the `path_format`.
            json_body:
                an optional JSON body to send.
            **kwargs:
                any additional arguments to pass to `aiohttp.request`.

        Returns:
            The response.

        Raises:
            :class:`errors.DiscordHTTPError`:
                if the response retries too many times (e.g. after repeated rate-limits. This is very unlikely to ever
                occur directly.

        """
        kwargs.setdefault("allow_redirects", self.allow_redirects)

        headers = headers if headers is None else {}
        params = params if isinstance(params, dict) else {}
        method = method.upper()
        uri = self.base_uri + path_format.format(**params)
        bucket_id = self._get_bucket_id(method, path_format, **params)

        for i in range(self._RATELIMIT_RETRIES):
            # Wait on the global bucket
            await self.global_rate_limit.acquire(self._log_rate_limit_already_in_progress, bucket_id=None)

            if bucket_id in self.buckets:
                await self.buckets[bucket_id].acquire(self._log_rate_limit_already_in_progress, bucket_id=bucket_id)

            action = f"retrying {i + 1}/{self._RATELIMIT_RETRIES} " if i else ""
            self._correlation_id += 1
            self.logger.debug("%s%s %s", action, method, uri)

            async with self.session.request(method, uri, headers=headers, json=json_body, **kwargs) as resp:
                self.logger.debug(
                    "%s responded with %s %s containing %s (%s bytes)",
                    resp.status,
                    resp.reason,
                    resp.content_type,
                    resp.content_length,
                )

                headers = resp.headers

                if resp.content_type != "application/json":
                    body = await resp.read()
                    raise NotImplementedError(
                        f"Responding to {resp.content_type} is not implemented. Status was {resp.status}, "
                        f"body was {body}"
                    )
                else:
                    body = await resp.json()

                if not self._handle_rate_limiting(bucket_id, resp.status, headers, body):
                    break
        else:
            raise errors.DiscordHTTPError("the request failed too many times and thus was discarded. Try again later.")

    def _log_rate_limit_already_in_progress(self, bucket_id):
        if bucket_id is None:
            self.logger.debug("a global rate limit is already active, and the call is being suspended")
        else:
            self.logger.debug("a rate limit for %s is already active and the call is being suspended", bucket_id)

    def _log_rate_limit_starting(self, bucket_id, retry_after):
        if bucket_id is None:
            self.logger.warning("a global rate limit has been reached. Try again in %ss", retry_after)
        else:
            self.logger.debug("a rate limit for %s has been reached. Try again in %ss", bucket_id, retry_after)

    def _handle_rate_limiting(self, bucket_id, response_code, headers, body) -> bool:
        """
        Handle internal rate limits.
        Args:
            bucket_id:
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

        elif all(headers[k] is not None for k in _X_RATELIMIT_LOCALS):
            # If we don't get all the info we need, just forget about the rate limit as we can't act on missing
            # information.
            now = utils.parse_http_date(headers[_DATE]).timestamp()
            total = utils.get_from_map_as(headers, _X_RATELIMIT_LIMIT, int)
            reset_at = utils.get_from_map_as(headers, _X_RATELIMIT_RESET, float)
            remaining = utils.get_from_map_as(headers, _X_RATELIMIT_REMAINING, int)

            # This header only exists if we get a TOO_MANY_REQUESTS first.
            retry_after = headers.get("Retry-After", reset_at - now)

            if bucket_id not in self.buckets:
                # Make new bucket first
                bucket = rates.VariableTokenBucket(total, remaining, now, reset_at, self.loop)
                self.buckets[bucket_id] = bucket
            else:
                bucket = self.buckets[bucket_id]
                bucket.update(total, remaining, now, reset_at)

            if bucket.is_limiting:
                self._log_rate_limit_starting(bucket_id, retry_after)

            is_being_rate_limited = True

        return is_being_rate_limited
