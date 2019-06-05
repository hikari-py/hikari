#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Implementation of the V7 HTTP REST API with rate-limiting.
"""
import logging
import time

import aiohttp

from hikari.compat import asyncio
from hikari.compat import typing
from hikari.net import rates

#: Format string for the default Discord API URL.
DISCORD_API_URI_FORMAT = "https://discordapp.com/api/v{VERSION}"


class HTTPLogger(logging.LoggerAdapter):
    """
    Internal functionality to log HTTP requests in a sane way.
    """

    def __init__(self, logger):
        super().__init__(logger, extra={})

    def process(self, msg, kwargs):
        # Format into key value pairs within "[]"s if there are extras passed.
        extra = kwargs.pop("extra", {})
        extra = ((k, v() if callable(v) else v) for k, v in extra.items())
        extra = (f"{k!r}={v!r}" for k, v in extra)
        extra = extra and f"[{', '.join(extra)}] " or ""
        return f"{extra}{msg}", kwargs


class HTTP:
    """
    Args:
        loop:
            the asyncio event loop to run on.
        token:
            the token to use for authentication. This should not start with `Bearer ` or `Bot ` and will always have
            `Bot ` prepended to it in requests.
        base_uri:
            optional HTTP API base URI to hit. If unspecified, this defaults to Discord's API URI. This exists for the
            purpose of mocking for functional testing. Any URI should NOT end with a trailing forward slash, and any
            instance of `{VERSION}` in the URL will be replaced.
        **aiohttp_arguments:
            additional arguments to pass to the internal :class:`aiohttp.ClientSession` constructor used for making
            HTTP requests.
    """

    VERSION = 7

    def __init__(
        self,
        *,
        loop: asyncio.AbstractEventLoop,
        token: str,
        base_uri: str = DISCORD_API_URI_FORMAT.format(VERSION=VERSION),
        **aiohttp_arguments,
    ) -> None:
        self._buckets: typing.Dict[str, rates.VariableTokenBucket] = {}
        self._base_uri = base_uri
        # Identifies each request made for logging purposes.
        self._correlation_id = 0
        self._logger = logging.getLogger(type(self).__name__)
        self._session = aiohttp.ClientSession(loop=loop, **aiohttp_arguments)
        self._token = "Bot " + token

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
        headers = headers if headers is None else {}
        params = params if isinstance(params, dict) else {}
        method = method.upper()
        uri = self._base_uri + path_format.format(**params)
        bucket_id = self._get_bucket_id(method, path_format, **params)

        if bucket_id not in self._buckets:
            # For now, we don't know what our first limit is, so make an estimate and update it once we have more info.
            # 10 seems like a good number to me. If we get 429'ed then we can amend ourselves then...
            self._buckets[bucket_id] = rates.VariableTokenBucket(10, 10, time.perf_counter() + 10, self.loop)

        bucket = self._buckets[bucket_id]

        async with bucket:
            async with self._session.request(method, uri, headers=headers, json=json_body, **kwargs) as resp:
                resp_headers = resp.headers
