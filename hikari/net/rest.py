#!/usr/bin/env python3
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

from __future__ import annotations

__all__ = ["REST"]

import asyncio
import datetime
import http
import json
import typing

import aiohttp

from hikari import base_app
from hikari import errors
from hikari import http_settings
from hikari.internal import conversions
from hikari.internal import more_typing
from hikari.internal import ratelimits
from hikari.models import bases
from hikari.models import channels
from hikari.models import unset
from hikari.net import buckets
from hikari.net import http_client
from hikari.net import routes


class _RateLimited(RuntimeError):
    __slots__ = ()


class REST(http_client.HTTPClient):
    def __init__(
        self,
        *,
        app: base_app.IBaseApp,
        config: http_settings.HTTPSettings,
        debug: bool = False,
        token: typing.Optional[str],
        token_type: str = "Bot",
        url: str,
        version: int,
    ) -> None:
        super().__init__(
            allow_redirects=config.allow_redirects,
            connector=config.tcp_connector,
            debug=debug,
            logger_name=f"{type(self).__module__}.{type(self).__qualname__}",
            proxy_auth=config.proxy_auth,
            proxy_headers=config.proxy_headers,
            proxy_url=config.proxy_url,
            ssl_context=config.ssl_context,
            verify_ssl=config.verify_ssl,
            timeout=config.request_timeout,
            trust_env=config.trust_env,
        )
        self.buckets = buckets.RESTBucketManager()
        self.global_rate_limit = ratelimits.ManualRateLimiter()
        self.version = version

        self._app = app
        self._token = f"{token_type.title()} {token}" if token is not None else None

        self._url = url.format(self)

    async def close(self) -> None:
        """Close the REST client."""
        await super().close()
        self.buckets.close()

    async def _request(
        self,
        compiled_route: routes.CompiledRoute,
        *,
        headers: more_typing.Headers = None,
        query: typing.Optional[more_typing.JSONObject] = None,
        body: typing.Optional[typing.Union[aiohttp.FormData, more_typing.JSONType]] = None,
        reason: typing.Union[unset.Unset, str] = None,
        suppress_authorization_header: bool = False,
    ) -> typing.Optional[more_typing.JSONObject, more_typing.JSONArray, bytes]:
        # Make a ratelimit-protected HTTP request to a JSON endpoint and expect some form
        # of JSON response. If an error occurs, the response body is returned in the
        # raised exception as a bytes object. This is done since the differences between
        # the V6 and V7 API error messages are not documented properly, and there are
        # edge cases such as Cloudflare issues where we may receive arbitrary data in
        # the response instead of a JSON object.

        if not self.buckets.is_started:
            self.buckets.start()

        headers = {} if headers is None else headers

        headers["x-ratelimit-precision"] = "millisecond"
        headers["accept"] = self._APPLICATION_JSON

        if self._token is not None and not suppress_authorization_header:
            headers["authorization"] = self._token

        if not unset.is_unset(reason):
            headers["x-audit-log-reason"] = reason

        while True:
            try:
                # Moved to a separate method to keep branch counts down.
                return await self._request_once(compiled_route, headers, body, query)
            except _RateLimited:
                pass

    async def _request_once(self, compiled_route, headers, body, query):
        url = compiled_route.create_url(self._url)

        # Wait for any ratelimits to finish.
        await asyncio.gather(self.buckets.acquire(compiled_route), self.global_rate_limit.acquire())

        # Make the request.
        response = await self._perform_request(
            method=compiled_route.method, url=url, headers=headers, body=body, query=query
        )

        real_url = str(response.real_url)

        # Ensure we aren't rate limited, and update rate limiting headers where appropriate.
        await self._handle_rate_limits_for_response(compiled_route, response)

        # Don't bother processing any further if we got NO CONTENT. There's not anything
        # to check.
        if response.status == http.HTTPStatus.NO_CONTENT:
            return None

        # Decode the body.
        raw_body = await response.read()

        # Handle the response.
        if 200 <= response.status < 300:
            if response.content_type == self._APPLICATION_JSON:
                # Only deserializing here stops Cloudflare shenanigans messing us around.
                return json.loads(raw_body)
            raise errors.HTTPError(real_url, f"Expected JSON response but received {response.content_type}")

        if response.status == http.HTTPStatus.BAD_REQUEST:
            raise errors.BadRequest(real_url, response.headers, raw_body)
        if response.status == http.HTTPStatus.UNAUTHORIZED:
            raise errors.Unauthorized(real_url, response.headers, raw_body)
        if response.status == http.HTTPStatus.FORBIDDEN:
            raise errors.Forbidden(real_url, response.headers, raw_body)
        if response.status == http.HTTPStatus.NOT_FOUND:
            raise errors.NotFound(real_url, response.headers, raw_body)

        # noinspection PyArgumentList
        status = http.HTTPStatus(response.status)

        if 400 <= status < 500:
            cls = errors.ClientHTTPErrorResponse
        elif 500 <= status < 600:
            cls = errors.ServerHTTPErrorResponse
        else:
            cls = errors.HTTPErrorResponse

        raise cls(real_url, status, response.headers, raw_body)

    async def _handle_rate_limits_for_response(self, compiled_route, response):
        # Worth noting there is some bug on V6 that ratelimits me immediately if I have an invalid token.
        # https://github.com/discord/discord-api-docs/issues/1569

        # Handle ratelimiting.
        resp_headers = response.headers
        limit = int(resp_headers.get("x-ratelimit-limit", "1"))
        remaining = int(resp_headers.get("x-ratelimit-remaining", "1"))
        bucket = resp_headers.get("x-ratelimit-bucket", "None")
        reset = float(resp_headers.get("x-ratelimit-reset", "0"))
        reset_date = datetime.datetime.fromtimestamp(reset, tz=datetime.timezone.utc)
        now_date = conversions.parse_http_date(resp_headers["date"])
        self.buckets.update_rate_limits(
            compiled_route=compiled_route,
            bucket_header=bucket,
            remaining_header=remaining,
            limit_header=limit,
            date_header=now_date,
            reset_at_header=reset_date,
        )

        if response.status == http.HTTPStatus.TOO_MANY_REQUESTS:
            body = await response.json() if response.content_type == self._APPLICATION_JSON else await response.read()

            # We are being rate limited.
            if isinstance(body, dict):
                if body.get("global", False):
                    retry_after = float(body["retry_after"]) / 1_000
                    self.global_rate_limit.throttle(retry_after)

                    self.logger.warning(
                        "you are being rate-limited globally - trying again after %ss", retry_after,
                    )
                else:
                    self.logger.warning(
                        "you are being rate-limited on bucket %s for route %s - trying again after %ss",
                        bucket,
                        compiled_route,
                        reset,
                    )

                raise _RateLimited()

            # We might find out Cloudflare causes this scenario to occur.
            # I hope we don't though.
            raise errors.HTTPError(
                str(response.real_url),
                f"We were ratelimited but did not understand the response. Perhaps Cloudflare did this? {body!r}",
            )

    async def fetch_channel(
        self, channel: typing.Union[channels.PartialChannel, bases.Snowflake, int],
    ) -> channels.PartialChannel:
        response = await self._request(routes.GET_CHANNEL.compile(channel_id=conversions.cast_to_str_id(channel)))

        # TODO: implement serialization.
        return NotImplemented

    async def edit_channel(
        self,
        channel: typing.Union[channels.PartialChannel, bases.Snowflake, int],
        *,
        name: typing.Union[unset.Unset, str] = unset.UNSET,
        position: typing.Union[unset.Unset, int] = unset.UNSET,
        topic: typing.Union[unset.Unset, str] = unset.UNSET,
        nsfw: typing.Union[unset.Unset, bool] = unset.UNSET,
        bitrate: typing.Union[unset.Unset, int] = unset.UNSET,
        user_limit: typing.Union[unset.Unset, int] = unset.UNSET,
        rate_limit_per_user: typing.Union[unset.Unset, more_typing.TimeSpanT] = unset.UNSET,
        permission_overwrites: typing.Union[unset.Unset, typing.Sequence[channels.PermissionOverwrite]] = unset.UNSET,
        parent_category: typing.Union[unset.Unset, channels.GuildCategory] = unset.UNSET,
        reason: typing.Union[unset.Unset, str] = unset.UNSET,
    ) -> channels.PartialChannel:
        payload = {}
        conversions.put_if_specified(payload, "name", name)
        conversions.put_if_specified(payload, "position", position)
        conversions.put_if_specified(payload, "topic", topic)
        conversions.put_if_specified(payload, "nsfw", nsfw)
        conversions.put_if_specified(payload, "bitrate", bitrate)
        conversions.put_if_specified(payload, "user_limit", user_limit)
        conversions.put_if_specified(payload, "rate_limit_per_user", rate_limit_per_user)
        conversions.put_if_specified(payload, "parent_id", parent_category, conversions.cast_to_str_id)

        if not unset.is_unset(permission_overwrites):
            # TODO: implement serialization
            raise NotImplementedError()

        response = await self._request(
            routes.PATCH_CHANNEL.compile(channel_id=str(int(channel))), body=payload, reason=reason,
        )

        # TODO: implement deserialization.
        return NotImplemented
