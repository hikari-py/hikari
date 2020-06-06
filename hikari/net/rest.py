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
"""Implementation of a V6 and V7 compatible REST API for Discord."""

from __future__ import annotations

__all__ = ["REST"]

import asyncio
import datetime
import http
import typing

import aiohttp

from hikari import errors
from hikari.api import component
from hikari.net import buckets
from hikari.net import http_client
from hikari.net import http_settings
from hikari.net import iterators
from hikari.net import rate_limits
from hikari.net import rest_utils
from hikari.net import routes
from hikari.utilities import data_binding
from hikari.utilities import date
from hikari.utilities import klass
from hikari.utilities import snowflake
from hikari.utilities import undefined

if typing.TYPE_CHECKING:
    from hikari.api import app as app_

    from hikari.models import applications
    from hikari.models import audit_logs
    from hikari.models import bases
    from hikari.models import channels
    from hikari.models import colors
    from hikari.models import embeds as embeds_
    from hikari.models import emojis
    from hikari.models import files
    from hikari.models import gateway
    from hikari.models import guilds
    from hikari.models import invites
    from hikari.models import messages as messages_
    from hikari.models import permissions as permissions_
    from hikari.models import users
    from hikari.models import voices
    from hikari.models import webhooks

_REST_API_URL: typing.Final[str] = "https://discord.com/api/v{0.version}"
"""The URL for the RESTSession API. This contains a version number parameter that
should be interpolated.
"""

_OAUTH2_API_URL: typing.Final[str] = "https://discord.com/api/oauth2"
"""The URL to the Discord OAuth2 API."""


class REST(http_client.HTTPClient, component.IComponent):  # pylint:disable=too-many-public-methods
    """Implementation of the V6 and V7-compatible Discord REST API.

    This manages making HTTP/1.1 requests to the API and using the entity
    factory within the passed application instance to deserialize JSON responses
    to Pythonic data classes that are used throughout this library.

    Parameters
    ----------
    app : hikari.rest_app.IRESTApp
        The REST application containing all other application components
        that Hikari uses.
    config : hikari.http_settings.HTTPSettings
        The AIOHTTP-specific configuration settings. This is used to configure
        proxies, and specify TCP connectors to control the size of HTTP
        connection pools, etc.
    debug : bool
        If `True`, this will enable logging of each payload sent and received,
        as well as information such as DNS cache hits and misses, and other
        information useful for debugging this application. These logs will
        be written as DEBUG log entries. For most purposes, this should be
        left `False`.
    token : str
        The bot or bearer token. If no token is to be used, this can be `None`.
    token_type : str or hikari.utilities.undefined.Undefined
        The type of token in use. If no token is used, this can be ignored and
        left to the default value. This can be `"Bot"` or `"Bearer"`. The
        default if not provided will be `"Bot"`.
    rest_url : str
        The REST API base URL. This can contain format-string specifiers to
        interpolate information such as API version in use.
    version : int
        The API version to use.
    """

    class _RateLimited(RuntimeError):
        __slots__ = ()

    def __init__(
        self,
        *,
        app: app_.IRESTApp,
        config: http_settings.HTTPSettings,
        debug: bool = False,
        token: typing.Union[undefined.Undefined, str] = undefined.Undefined(),
        token_type: typing.Union[undefined.Undefined, str] = undefined.Undefined(),
        rest_url: typing.Union[undefined.Undefined, str] = undefined.Undefined(),
        oauth2_url: typing.Union[undefined.Undefined, str] = undefined.Undefined(),
        version: int,
    ) -> None:
        super().__init__(
            allow_redirects=config.allow_redirects,
            connector=config.tcp_connector_factory() if config.tcp_connector_factory else None,
            debug=debug,
            logger=klass.get_logger(self),
            proxy_auth=config.proxy_auth,
            proxy_headers=config.proxy_headers,
            proxy_url=config.proxy_url,
            ssl_context=config.ssl_context,
            verify_ssl=config.verify_ssl,
            timeout=config.request_timeout,
            trust_env=config.trust_env,
        )
        self.buckets = buckets.RESTBucketManager()
        self.global_rate_limit = rate_limits.ManualRateLimiter()
        self._invalid_requests = 0
        self._invalid_request_window = -float("inf")
        self.version = version

        self._app = app

        if isinstance(token, undefined.Undefined):
            self._token = None
        else:
            if isinstance(token_type, undefined.Undefined):
                token_type = "Bot"

            self._token = f"{token_type.title()} {token}" if token is not None else None

        if isinstance(rest_url, undefined.Undefined):
            rest_url = _REST_API_URL

        if isinstance(oauth2_url, undefined.Undefined):
            oauth2_url = _OAUTH2_API_URL

        self._rest_url = rest_url.format(self)
        self._oauth2_url = oauth2_url.format(self)

    @property
    def app(self) -> app_.IRESTApp:
        return self._app

    async def _request(
        self,
        compiled_route: routes.CompiledRoute,
        *,
        query: typing.Union[undefined.Undefined, data_binding.StringMapBuilder] = undefined.Undefined(),
        body: typing.Union[
            undefined.Undefined, aiohttp.FormData, data_binding.JSONObjectBuilder, data_binding.JSONArray
        ] = undefined.Undefined(),
        reason: typing.Union[undefined.Undefined, str] = undefined.Undefined(),
        no_auth: bool = False,
    ) -> typing.Optional[data_binding.JSONObject, data_binding.JSONArray, bytes, str]:
        # Make a ratelimit-protected HTTP request to a JSON endpoint and expect some form
        # of JSON response. If an error occurs, the response body is returned in the
        # raised exception as a bytes object. This is done since the differences between
        # the V6 and V7 API error messages are not documented properly, and there are
        # edge cases such as Cloudflare issues where we may receive arbitrary data in
        # the response instead of a JSON object.

        if not self.buckets.is_started:
            self.buckets.start()

        headers = data_binding.StringMapBuilder()

        headers.put("x-ratelimit-precision", "millisecond")
        headers.put("accept", self._APPLICATION_JSON)

        if self._token is not None and not no_auth:
            headers["authorization"] = self._token

        if isinstance(body, undefined.Undefined):
            body = None

        headers.put("x-audit-log-reason", reason)

        if isinstance(query, undefined.Undefined):
            query = None

        while True:
            try:
                # Moved to a separate method to keep branch counts down.
                return await self._request_once(compiled_route=compiled_route, headers=headers, body=body, query=query)
            except self._RateLimited:
                pass

    async def _request_once(
        self,
        compiled_route: routes.CompiledRoute,
        headers: data_binding.Headers,
        body: typing.Optional[typing.Union[aiohttp.FormData, data_binding.JSONArray, data_binding.JSONObject]],
        query: typing.Optional[typing.Dict[str, str]],
    ) -> typing.Optional[data_binding.JSONObject, data_binding.JSONArray, bytes, str]:
        url = compiled_route.create_url(self._rest_url)

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

        raw_body = await response.read()

        # Handle the response.
        if 200 <= response.status < 300:
            if response.content_type == self._APPLICATION_JSON:
                # Only deserializing here stops Cloudflare shenanigans messing us around.
                return data_binding.load_json(raw_body)
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

    async def _handle_rate_limits_for_response(
        self, compiled_route: routes.CompiledRoute, response: aiohttp.ClientResponse
    ) -> None:
        # Worth noting there is some bug on V6 that rate limits me immediately if I have an invalid token.
        # https://github.com/discord/discord-api-docs/issues/1569

        # Handle rate limiting.
        resp_headers = response.headers
        limit = int(resp_headers.get("x-ratelimit-limit", "1"))
        remaining = int(resp_headers.get("x-ratelimit-remaining", "1"))
        bucket = resp_headers.get("x-ratelimit-bucket", "None")
        reset_at = float(resp_headers.get("x-ratelimit-reset", "0"))
        reset_date = datetime.datetime.fromtimestamp(reset_at, tz=datetime.timezone.utc)
        now_date = date.rfc7231_datetime_string_to_datetime(resp_headers["date"])

        is_rate_limited = response.status == http.HTTPStatus.TOO_MANY_REQUESTS

        if is_rate_limited:
            if response.content_type != self._APPLICATION_JSON:
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

            if body.get("global", False):
                self.global_rate_limit.throttle(body_retry_after)

                self.logger.warning("you are being rate-limited globally - trying again after %ss", body_retry_after)
            else:
                # Discord can do a messed up thing where the headers suggest we aren't rate limited,
                # but we still get 429s with a different rate limit.
                # If this occurs, we need to take the rate limit that is furthest in the future
                # to avoid excessive 429ing everywhere repeatedly, causing an API ban,
                # since our logic assumes the rate limit info they give us is actually
                # remotely correct.
                #
                # At the time of writing, editing a channel more than twice per 10 minutes seems
                # to trigger this, which makes me nervous that the info we are receiving isn't
                # correct, but whatever... this is the best we can do.

                header_reset_at = reset_at
                body_retry_at = now_date.timestamp() + body_retry_after

                if body_retry_at > header_reset_at:
                    reset_date = datetime.datetime.fromtimestamp(body_retry_at, tz=datetime.timezone.utc)

                self.logger.warning(
                    "you are being rate-limited on bucket %s for route %s - trying again after %ss "
                    "(headers suggest %ss back-off finishing at %s; rate-limited response specifies %ss "
                    "back-off finishing at %s)",
                    bucket,
                    compiled_route,
                    reset_at,
                    header_reset_at - now_date.timestamp(),
                    header_reset_at,
                    body_retry_after,
                    body_retry_at,
                )

        self.buckets.update_rate_limits(
            compiled_route=compiled_route,
            bucket_header=bucket,
            remaining_header=remaining,
            limit_header=limit,
            date_header=now_date,
            reset_at_header=reset_date,
        )

        if is_rate_limited:
            raise self._RateLimited()

    @staticmethod
    def _generate_allowed_mentions(
        mentions_everyone: typing.Union[undefined.Undefined, bool],
        user_mentions: typing.Union[
            undefined.Undefined, typing.Collection[typing.Union[users.User, bases.UniqueObject]], bool
        ],
        role_mentions: typing.Union[
            undefined.Undefined, typing.Collection[typing.Union[bases.UniqueObject, guilds.Role]], bool
        ],
    ):
        parsed_mentions = []
        allowed_mentions = {}

        if mentions_everyone is True:
            parsed_mentions.append("everyone")

        if user_mentions is True:
            parsed_mentions.append("users")
        # This covers both `False` and an array of IDs/objs by using `user_mentions` or `EMPTY_SEQUENCE`, where a
        # resultant empty list will mean that all user mentions are blacklisted.
        elif not isinstance(user_mentions, undefined.Undefined):
            allowed_mentions["users"] = list(
                # dict.fromkeys is used to remove duplicate entries that would cause discord to return an error.
                dict.fromkeys(str(int(m)) for m in user_mentions or ())
            )
            if len(allowed_mentions["users"]) > 100:
                raise ValueError("Only up to 100 users can be provided.")

        if role_mentions is True:
            parsed_mentions.append("roles")
        # This covers both `False` and an array of IDs/objs by using `user_mentions` or `EMPTY_SEQUENCE`, where a
        # resultant empty list will mean that all role mentions are blacklisted.
        elif not isinstance(role_mentions, undefined.Undefined):
            allowed_mentions["roles"] = list(
                # dict.fromkeys is used to remove duplicate entries that would cause discord to return an error.
                dict.fromkeys(str(int(m)) for m in role_mentions or ())
            )
            if len(allowed_mentions["roles"]) > 100:
                raise ValueError("Only up to 100 roles can be provided.")

        if not parsed_mentions and not allowed_mentions:
            return undefined.Undefined()

        allowed_mentions["parse"] = parsed_mentions
        return allowed_mentions

    def _build_message_creation_form(
        self, payload: data_binding.JSONObject, attachments: typing.Sequence[files.BaseStream],
    ) -> aiohttp.FormData:
        form = data_binding.URLEncodedForm()
        form.add_field("payload_json", data_binding.dump_json(payload), content_type=self._APPLICATION_JSON)
        for i, attachment in enumerate(attachments):
            form.add_field(
                f"file{i}", attachment, filename=attachment.filename, content_type=self._APPLICATION_OCTET_STREAM
            )
        return form

    async def close(self) -> None:
        """Close the REST client and any open HTTP connections."""
        await super().close()
        self.buckets.close()

    async def fetch_channel(
        self, channel: typing.Union[channels.PartialChannel, bases.UniqueObject], /,
    ) -> channels.PartialChannel:
        """Fetch a channel.

        Parameters
        ----------
        channel : hikari.models.channels.PartialChannel or hikari.utilities.snowflake.Snowflake or int or str
            The channel to fetch. This may be a channel object, or the ID of an
            existing channel.

        Returns
        -------
        hikari.models.channels.PartialChannel
            The fetched channel.

        Raises
        ------
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack permissions to access the channel.
        hikari.errors.NotFound
            If the channel is not found.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.
        """
        route = routes.GET_CHANNEL.compile(channel=channel)
        response = await self._request(route)
        return self._app.entity_factory.deserialize_channel(response)

    if typing.TYPE_CHECKING:
        _GuildChannelT = typing.TypeVar("_GuildChannelT", bound=channels.GuildChannel, contravariant=True)

    # This overload just tells any static type checker that if we input, say,
    # a GuildTextChannel, we should always expect a GuildTextChannel as the
    # result. This only applies to actual Channel types... we cannot infer the
    # result of calling this endpoint with a snowflake.
    @typing.overload
    async def edit_channel(
        self,
        channel: _GuildChannelT,
        /,
        *,
        name: typing.Union[undefined.Undefined, str] = undefined.Undefined(),
        position: typing.Union[undefined.Undefined, int] = undefined.Undefined(),
        topic: typing.Union[undefined.Undefined, str] = undefined.Undefined(),
        nsfw: typing.Union[undefined.Undefined, bool] = undefined.Undefined(),
        bitrate: typing.Union[undefined.Undefined, int] = undefined.Undefined(),
        user_limit: typing.Union[undefined.Undefined, int] = undefined.Undefined(),
        rate_limit_per_user: typing.Union[undefined.Undefined, date.TimeSpan] = undefined.Undefined(),
        permission_overwrites: typing.Union[
            undefined.Undefined, typing.Sequence[channels.PermissionOverwrite]
        ] = undefined.Undefined(),
        parent_category: typing.Union[undefined.Undefined, channels.GuildCategory] = undefined.Undefined(),
        reason: typing.Union[undefined.Undefined, str] = undefined.Undefined(),
    ) -> _GuildChannelT:
        """Edit a guild channel, given an existing guild channel object."""

    async def edit_channel(
        self,
        channel: typing.Union[channels.PartialChannel, bases.UniqueObject],
        /,
        *,
        name: typing.Union[undefined.Undefined, str] = undefined.Undefined(),
        position: typing.Union[undefined.Undefined, int] = undefined.Undefined(),
        topic: typing.Union[undefined.Undefined, str] = undefined.Undefined(),
        nsfw: typing.Union[undefined.Undefined, bool] = undefined.Undefined(),
        bitrate: typing.Union[undefined.Undefined, int] = undefined.Undefined(),
        user_limit: typing.Union[undefined.Undefined, int] = undefined.Undefined(),
        rate_limit_per_user: typing.Union[undefined.Undefined, date.TimeSpan] = undefined.Undefined(),
        permission_overwrites: typing.Union[
            undefined.Undefined, typing.Sequence[channels.PermissionOverwrite]
        ] = undefined.Undefined(),
        parent_category: typing.Union[
            undefined.Undefined, channels.GuildCategory, bases.UniqueObject
        ] = undefined.Undefined(),
        reason: typing.Union[undefined.Undefined, str] = undefined.Undefined(),
    ) -> channels.PartialChannel:
        """Edit a channel.

        Parameters
        ----------
        channel : hikari.models.channels.PartialChannel or hikari.utilities.snowflake.Snowflake or int or str
            The channel to edit. This may be a channel object, or the ID of an
            existing channel.
        name : hikari.utilities.undefined.Undefined or str
            If provided, the new name for the channel.
        position : hikari.utilities.undefined.Undefined or int
            If provided, the new position for the channel.
        topic : hikari.utilities.undefined.Undefined or str
            If provided, the new topic for the channel.
        nsfw : hikari.utilities.undefined.Undefined or bool
            If provided, whether the channel should be marked as NSFW or not.
        bitrate : hikari.utilities.undefined.Undefined or int
            If provided, the new bitrate for the channel.
        user_limit : hikari.utilities.undefined.Undefined or int
            If provided, the new user limit in the channel.
        rate_limit_per_user : hikari.utilities.undefined.Undefined or datetime.timedelta or float or int
            If provided, the new rate limit per user in the channel.
        permission_overwrites : hikari.utilities.undefined.Undefined or typing.Sequence[hikari.models.channels.PermissionOverwrite]
            If provided, the new permission overwrites for the channel.
        parent_category : hikari.utilities.undefined.Undefined or hikari.models.channels.GuildCategory or hikari.utilities.snowflake.Snowflake or int or str
            If provided, the new guild category for the channel. This may be
            a category object, or the ID of an existing category.
        reason : hikari.utilities.undefined.Undefined or str
            If provided, the reason that will be recorded in the audit logs.

        Returns
        -------
        hikari.models.channels.PartialChannel
            The edited channel.

        Raises
        ------
        hikari.errors.BadRequest
            If any of the fields that are passed have an invalid value.
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack permissions to edit the channel
        hikari.errors.NotFound
            If the channel is not found.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.
        """
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

        response = await self._request(route, body=body, reason=reason)
        return self._app.entity_factory.deserialize_channel(response)

    async def delete_channel(self, channel: typing.Union[channels.PartialChannel, bases.UniqueObject], /) -> None:
        """Delete a channel in a guild, or close a DM.

        Parameters
        ----------
        channel : hikari.models.channels.PartialChannel or hikari.utilities.snowflake.Snowflake or int or str
            The channel to delete. This may be a channel object, or the ID of an
            existing channel.

        Raises
        ------
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack permissions to delete the channel in a guild.
        hikari.errors.NotFound
            If the channel is not found.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.

        !!! note
            For Public servers, the set 'Rules' or 'Guidelines' channels and the
            'Public Server Updates' channel cannot be deleted.
        """
        route = routes.DELETE_CHANNEL.compile(channel=channel)
        await self._request(route)

    @typing.overload
    async def edit_permission_overwrites(
        self,
        channel: typing.Union[channels.GuildChannel, bases.UniqueObject],
        target: typing.Union[channels.PermissionOverwrite, users.User, guilds.Role],
        *,
        allow: typing.Union[undefined.Undefined, permissions_.Permission] = undefined.Undefined(),
        deny: typing.Union[undefined.Undefined, permissions_.Permission] = undefined.Undefined(),
        reason: typing.Union[undefined.Undefined, str] = undefined.Undefined(),
    ) -> None:
        """Edit permissions for a target entity."""

    @typing.overload
    async def edit_permission_overwrites(
        self,
        channel: typing.Union[channels.GuildChannel, bases.UniqueObject],
        target: typing.Union[int, str, snowflake.Snowflake],
        target_type: typing.Union[channels.PermissionOverwriteType, str],
        *,
        allow: typing.Union[undefined.Undefined, permissions_.Permission] = undefined.Undefined(),
        deny: typing.Union[undefined.Undefined, permissions_.Permission] = undefined.Undefined(),
        reason: typing.Union[undefined.Undefined, str] = undefined.Undefined(),
    ) -> None:
        """Edit permissions for a given entity ID and type."""

    async def edit_permission_overwrites(
        self,
        channel: typing.Union[channels.GuildChannel, bases.UniqueObject],
        target: typing.Union[bases.UniqueObject, users.User, guilds.Role, channels.PermissionOverwrite],
        *,
        target_type: typing.Union[undefined.Undefined, channels.PermissionOverwriteType, str] = undefined.Undefined(),
        allow: typing.Union[undefined.Undefined, permissions_.Permission] = undefined.Undefined(),
        deny: typing.Union[undefined.Undefined, permissions_.Permission] = undefined.Undefined(),
        reason: typing.Union[undefined.Undefined, str] = undefined.Undefined(),
    ) -> None:
        """Edit permissions for a specific entity in the given guild channel.

        Parameters
        ----------
        channel : hikari.models.channels.PartialChannel or hikari.utilities.snowflake.Snowflake or int or str
            The channel to edit a permission overwrite in. This may be a channel object, or
            the ID of an existing channel.
        target : hikari.models.users.User or hikari.models.guidls.Role or hikari.models.channels.PermissionOverwrite or hikari.utilities.snowflake.Snowflake or int or str
            The channel overwrite to edit. This may be a overwrite object, or the ID of an
            existing channel.
        target_type : hikari.utilities.undefined.Undefined or hikari.models.channels.PermissionOverwriteType or str
            If provided, the type of the target to update. If unset, will attempt to get
            the type from `target`.
        allow : hikari.utilities.undefined.Undefined or hikari.models.permissions.Permission
            If provided, the new vale of all allowed permissions.
        deny : hikari.utilities.undefined.Undefined or hikari.models.permissions.Permission
            If provided, the new vale of all disallowed permissions.
        reason : hikari.utilities.undefined.Undefined or str
            If provided, the reason that will be recorded in the audit logs.

        Raises
        ------
        TypeError
            If `target_type` is unset and we were unable to determine the type
            from `target`.
        hikari.errors.BadRequest
            If any of the fields that are passed have an invalid value.
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack permissions to edit the permission overwrites.
        hikari.errors.NotFound
            If the channel is not found or the target is not found if it is
            a role.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.
        """
        if isinstance(target_type, undefined.Undefined):
            if isinstance(target, users.User):
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

        await self._request(route, body=body, reason=reason)

    async def delete_permission_overwrite(
        self,
        channel: typing.Union[channels.GuildChannel, bases.UniqueObject],
        target: typing.Union[channels.PermissionOverwrite, guilds.Role, users.User, bases.UniqueObject],
    ) -> None:
        """Delete a custom permission for an entity in a given guild channel.

        Parameters
        ----------
        channel : hikari.models.channels.PartialChannel or hikari.utilities.snowflake.Snowflake or int or str
            The channel to delete a permission overwrite in. This may be a channel
            object, or the ID of an existing channel.
        target : hikari.models.users.User or hikari.models.guidls.Role or hikari.models.channels.PermissionOverwrite or hikari.utilities.snowflake.Snowflake or int or str
            The channel overwrite to delete.

        Raises
        ------
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack permissions to delete the permission overwrite.
        hikari.errors.NotFound
            If the channel is not found or the target is not found.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.
        """
        route = routes.DELETE_CHANNEL_PERMISSIONS.compile(channel=channel, overwrite=target)
        await self._request(route)

    async def fetch_channel_invites(
        self, channel: typing.Union[channels.GuildChannel, bases.UniqueObject], /
    ) -> typing.Sequence[invites.InviteWithMetadata]:
        """Fetch all invites pointing to the given guild channel.

        Parameters
        ----------
        channel : hikari.models.channels.PartialChannel or hikari.utilities.snowflake.Snowflake or int or str
            The channel to fetch the invites from. This may be a channel
            object, or the ID of an existing channel.

        Returns
        -------
        typing.Sequence[hikari.models.invites.InviteWithMetadata]
            The invites pointing to the given guild channel.

        Raises
        ------
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack permissions to view the invites for the given channel.
        hikari.errors.NotFound
            If the channel is not found in any guilds you are a member of.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.
        """
        route = routes.GET_CHANNEL_INVITES.compile(channel=channel)
        response = await self._request(route)
        return data_binding.cast_json_array(response, self._app.entity_factory.deserialize_invite_with_metadata)

    async def create_invite(
        self,
        channel: typing.Union[channels.GuildChannel, bases.UniqueObject],
        /,
        *,
        max_age: typing.Union[undefined.Undefined, int, float, datetime.timedelta] = undefined.Undefined(),
        max_uses: typing.Union[undefined.Undefined, int] = undefined.Undefined(),
        temporary: typing.Union[undefined.Undefined, bool] = undefined.Undefined(),
        unique: typing.Union[undefined.Undefined, bool] = undefined.Undefined(),
        target_user: typing.Union[undefined.Undefined, users.User, bases.UniqueObject] = undefined.Undefined(),
        target_user_type: typing.Union[undefined.Undefined, invites.TargetUserType] = undefined.Undefined(),
        reason: typing.Union[undefined.Undefined, str] = undefined.Undefined(),
    ) -> invites.InviteWithMetadata:
        """Create an invite to the given guild channel.

        Parameters
        ----------
        channel : hikari.models.channels.PartialChannel or hikari.utilities.snowflake.Snowflake or int or str
            The channel to create a invite for. This may be a channel object,
            or the ID of an existing channel.
        max_age : hikari.utilities.undefined.Undefined or datetime.timedelta or float or int
            If provided, the duration of the invite before expiry.
        max_uses : hikari.utilities.undefined.Undefined or int
            If provided, the max uses the invite can have.
        temporary : hikari.utilities.undefined.Undefined or bool
            If provided, whether the invite only grants temporary membership.
        unique : hikari.utilities.undefined.Undefined or bool
            If provided, wheter the invite should be unique.
        target_user : hikari.utilities.undefined.Undefined or hikari.models.users.User or hikari.utilities.snowflake.Snowflake or int or str
            If provided, the target user id for this invite. This may be a
            user object, or the ID of an existing user.
        target_user_type : hikari.utilities.undefined.Undefined or hikari.models.invites.TargetUserType or int
            If provided, the type of target user for this invite.
        reason : hikari.utilities.undefined.Undefined or str
            If provided, the reason that will be recorded in the audit logs.

        Returns
        -------
        hikari.models.invites.InviteWithMetadata
            The invite to the given guild channel.

        Raises
        ------
        hikari.errors.BadRequest
            If any of the fields that are passed have an invalid value.
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack permissions to create the given channel.
        hikari.errors.NotFound
            If the channel is not found, or if the target user does not exist,
            if specified.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.
        """
        route = routes.POST_CHANNEL_INVITES.compile(channel=channel)
        body = data_binding.JSONObjectBuilder()
        body.put("max_age", max_age, conversion=date.timespan_to_int)
        body.put("max_uses", max_uses)
        body.put("temporary", temporary)
        body.put("unique", unique)
        body.put_snowflake("target_user_id", target_user)
        body.put("target_user_type", target_user_type)
        response = await self._request(route, body=body, reason=reason)
        return self._app.entity_factory.deserialize_invite_with_metadata(response)

    def trigger_typing(
        self, channel: typing.Union[channels.TextChannel, bases.UniqueObject], /
    ) -> rest_utils.TypingIndicator:
        """Trigger typing in a text channel.

        Parameters
        ----------
        channel : hikari.models.channels.PartialChannel or hikari.utilities.snowflake.Snowflake or int or str
            The channel to trigger typing in. This may be a channel object, or
            the ID of an existing channel.

        Returns
        -------
        hikari.net.rest_utils.TypingIndicator
            A typing indicator to use.

        Raises
        ------
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack permissions to read messages or send messages in the
            text channel.
        hikari.errors.NotFound
            If the channel is not found.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.

        !!! note
            The exceptions on this endpoint will only be raised once the result
            is awaited or interacted with. Invoking this function itself will
            not raise any of the above types.
        """
        return rest_utils.TypingIndicator(channel, self._request)

    async def fetch_pins(
        self, channel: typing.Union[channels.TextChannel, bases.UniqueObject], /
    ) -> typing.Sequence[messages_.Message]:
        """Fetch the pinned messages in this text channel.

        Parameters
        ----------
        channel : hikari.models.channels.PartialChannel or hikari.utilities.snowflake.Snowflake or int or str
            The channel to fetch pins from. This may be a channel object, or
            the ID of an existing channel.

        Returns
        -------
        typing.Sequence[hikari.models.messages.Message]
            The pinned messages in this text channel.

        Raises
        ------
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack permissions to read messages or send messages in the
            text channel.
        hikari.errors.NotFound
            If the channel is not found.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.
        """
        route = routes.GET_CHANNEL_PINS.compile(channel=channel)
        response = await self._request(route)
        return data_binding.cast_json_array(response, self._app.entity_factory.deserialize_message)

    async def pin_message(
        self,
        channel: typing.Union[channels.TextChannel, bases.UniqueObject],
        message: typing.Union[messages_.Message, bases.UniqueObject],
    ) -> None:
        """Pin an existing message in the given text channel.

        Parameters
        ----------
        channel : hikari.models.channels.PartialChannel or hikari.utilities.snowflake.Snowflake or int or str
            The channel to pin a message in. This may be a channel object, or
            the ID of an existing channel.
        message : hikari.models.messges.Message or hikari.utilities.snowflake.Snowflake or int or str
            The message to pin. This may be a message object,
            or the ID of an existing message.

        Raises
        ------
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack permissions to pin messages in the given channel.
        hikari.errors.NotFound
            If the channel is not found, or if the message does not exist in
            the given channel.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.
        """
        route = routes.PUT_CHANNEL_PINS.compile(channel=channel, message=message)
        await self._request(route)

    async def unpin_message(
        self,
        channel: typing.Union[channels.TextChannel, bases.UniqueObject],
        message: typing.Union[messages_.Message, bases.UniqueObject],
    ) -> None:
        """Unpin a given message from a given text channel.

        Parameters
        ----------
        channel : hikari.models.channels.PartialChannel or hikari.utilities.snowflake.Snowflake or int or str
            The channel to unpin a message in. This may be a channel object, or
            the ID of an existing channel.
        message : hikari.models.messges.Message or hikari.utilities.snowflake.Snowflake or int or str
            The message to unpin. This may be a message object, or the ID of an
            existing message.

        Raises
        ------
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack permissions pin messages in the given channel.
        hikari.errors.NotFound
            If the channel is not found or the message is not a pinned message
            in the given channel.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.
        """
        route = routes.DELETE_CHANNEL_PIN.compile(channel=channel, message=message)
        await self._request(route)

    @typing.overload
    def fetch_messages(
        self, channel: typing.Union[channels.TextChannel, bases.UniqueObject], /
    ) -> iterators.LazyIterator[messages_.Message]:
        """Fetch messages, newest first, sent in the given channel."""

    @typing.overload
    def fetch_messages(
        self,
        channel: typing.Union[channels.TextChannel, bases.UniqueObject],
        /,
        *,
        before: typing.Union[datetime.datetime, bases.UniqueObject],
    ) -> iterators.LazyIterator[messages_.Message]:
        """Fetch messages, newest first, sent before a timestamp in the channel."""

    @typing.overload
    def fetch_messages(
        self,
        channel: typing.Union[channels.TextChannel, bases.UniqueObject],
        /,
        *,
        around: typing.Union[datetime.datetime, bases.UniqueObject],
    ) -> iterators.LazyIterator[messages_.Message]:
        """Fetch messages sent around a given time in the channel."""

    @typing.overload
    def fetch_messages(
        self,
        channel: typing.Union[channels.TextChannel, bases.UniqueObject],
        /,
        *,
        after: typing.Union[datetime.datetime, bases.UniqueObject],
    ) -> iterators.LazyIterator[messages_.Message]:
        """Fetch messages, oldest first, sent after a timestamp in the channel."""

    def fetch_messages(
        self,
        channel: typing.Union[channels.TextChannel, bases.UniqueObject],
        /,
        *,
        before: typing.Union[undefined.Undefined, datetime.datetime, bases.UniqueObject] = undefined.Undefined(),
        after: typing.Union[undefined.Undefined, datetime.datetime, bases.UniqueObject] = undefined.Undefined(),
        around: typing.Union[undefined.Undefined, datetime.datetime, bases.UniqueObject] = undefined.Undefined(),
    ) -> iterators.LazyIterator[messages_.Message]:
        """Browse the message history for a given text channel.

        Parameters
        ----------
        channel : hikari.models.channels.PartialChannel or hikari.utilities.snowflake.Snowflake or int or str
            The channel to fetch messages in. This may be a channel object, or
            the ID of an existing channel.
        before : hikari.utilities.undefined.Undefined or datetime.datetime or hikari.utilities.snowflake.Snowflake or int or str
            If provided, fetch messages before this snowflake. If you provide
            a datetime object, it will be transformed into a snowflake.
        after : hikari.utilities.undefined.Undefined or datetime.datetime or hikari.utilities.snowflake.Snowflake or int or str
            If provided, fetch messages after this snowflake. If you provide
            a datetime object, it will be transformed into a snowflake.
        around : hikari.utilities.undefined.Undefined or datetime.datetime or hikari.utilities.snowflake.Snowflake or int or str
            If provided, fetch messages around this snowflake. If you provide
            a datetime object, it will be transformed into a snowflake.

        Returns
        -------
        hikari.net.iterators.LazyIterator[hikari.models.messages.Message]
            A iterator to fetch the messages.

        Raises
        ------
        TypeError
            If you specify more than one of `before`, `after`, `about`.
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack permissions to read message history in the given
            channel.
        hikari.errors.NotFound
            If the channel is not found.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.

        !!! note
            The exceptions on this endpoint (other than `TypeError`) will only
            be raised once the result is awaited or interacted with. Invoking
            this function itself will not raise anything (other than
            `TypeError`).
        """
        if undefined.Undefined.count(before, after, around) < 2:
            raise TypeError("Expected no kwargs, or maximum of one of 'before', 'after', 'around'")

        if not isinstance(before, undefined.Undefined):
            direction, timestamp = "before", before
        elif not isinstance(after, undefined.Undefined):
            direction, timestamp = "after", after
        elif not isinstance(around, undefined.Undefined):
            direction, timestamp = "around", around
        else:
            direction, timestamp = "before", snowflake.Snowflake.max()

        if isinstance(timestamp, datetime.datetime):
            timestamp = snowflake.Snowflake.from_datetime(timestamp)

        return iterators.MessageIterator(self._app, self._request, channel, direction, timestamp,)

    async def fetch_message(
        self,
        channel: typing.Union[channels.TextChannel, bases.UniqueObject],
        message: typing.Union[messages_.Message, bases.UniqueObject],
    ) -> messages_.Message:
        """Fetch a specific message in the given text channel.

        Parameters
        ----------
        channel : hikari.models.channels.PartialChannel or hikari.utilities.snowflake.Snowflake or int or str
            The channel to fetch messages in. This may be a channel object, or
            the ID of an existing channel.
        message : hikari.models.messages.Message or hikari.utilities.snowflake.Snowflake or int or str
            The message to fetch. This may be a channel object, or the ID of an
            existing channel.

        Returns
        -------
        hikari.models.messages.Message
            The requested message.

        Raises
        ------
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack permissions to read message history in the given
            channel.
        hikari.errors.NotFound
            If the channel is not found or the message is not found in the
            given text channel.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.
        """
        route = routes.GET_CHANNEL_MESSAGE.compile(channel=channel, message=message)
        response = await self._request(route)
        return self._app.entity_factory.deserialize_message(response)

    async def create_message(
        self,
        channel: typing.Union[channels.TextChannel, bases.UniqueObject],
        text: typing.Union[undefined.Undefined, typing.Any] = undefined.Undefined(),
        *,
        embed: typing.Union[undefined.Undefined, embeds_.Embed] = undefined.Undefined(),
        attachments: typing.Union[undefined.Undefined, typing.Sequence[files.BaseStream]] = undefined.Undefined(),
        tts: typing.Union[undefined.Undefined, bool] = undefined.Undefined(),
        nonce: typing.Union[undefined.Undefined, str] = undefined.Undefined(),
        mentions_everyone: bool = True,
        user_mentions: typing.Union[typing.Collection[typing.Union[users.User, bases.UniqueObject]], bool] = True,
        role_mentions: typing.Union[typing.Collection[typing.Union[guilds.Role, bases.UniqueObject]], bool] = True,
    ) -> messages_.Message:
        """Create a message in the given channel.

        Parameters
        ----------
        channel : hikari.models.channels.PartialChannel or hikari.utilities.snowflake.Snowflake or int or str
            The channel to create the message in. This may be a channel object, or
            the ID of an existing channel.
        text : hikari.utilities.undefined.Undefined or str
            If specified, the message contents.
        embed : hikari.utilities.undefined.Undefined or hikari.models.embeds.Embed
            If specified, the message embed.
        attachments : hikari.utilities.undefined.Undefined or typing.Sequence[hikari.models.files.BaseStream]
            If specified, the message attachments.
        tts : hikari.utilities.undefined.Undefined or bool
            If specified, whether the message will be TTS (Text To Speech).
        nonce : hikari.utilities.undefined.Undefined or str
            If specified, a nonce that can be used for optimistic message sending.
        mentions_everyone : bool
            If specified, whether the message should parse @everyone/@here mentions.
        user_mentions : typing.Collection[hikari.models.users.User or hikari.utilities.snowflake.Snowflake or int or str] or bool
            If specified, and `bool`, whether to parse user mentions. If specified and
            `list`, the users to parse the mention for. This may be a user object, or
            the ID of an existing user.
        role_mentions : typing.Collection[hikari.models.guilds.Role or hikari.utilities.snowflake.Snowflake or int or str] or bool
            If specified and `bool`, whether to parse role mentions. If specified and
            `list`, the roles to parse the mention for. This may be a role object, or
            the ID of an existing role.

        Returns
        -------
        hikari.models.messages.Message
            The created message.

        Raises
        ------
        hikari.errors.BadRequest
            This may be raised in several discrete situations, such as messages
            being empty with no attachments or embeds; messages with more than
            2000 characters in them, embeds that exceed one of the many embed
            limits; too many attachments; attachments that are too large;
            invalid image URLs in embeds; users in `user_mentions` not being
            mentioned in the message content; roles in `role_mentions` not
            being mentioned in the message content.
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack permissions to send messages in the given channel.
        hikari.errors.NotFound
            If the channel is not found.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.

        !!! warning
            You are expected to make a connection to the gateway and identify
            once before being able to use this endpoint for a bot.
        """
        route = routes.POST_CHANNEL_MESSAGES.compile(channel=channel)

        body = data_binding.JSONObjectBuilder()
        body.put("allowed_mentions", self._generate_allowed_mentions(mentions_everyone, user_mentions, role_mentions))
        body.put("content", text, conversion=str)
        body.put("embed", embed, conversion=self._app.entity_factory.serialize_embed)
        body.put("nonce", nonce)
        body.put("tts", tts)

        attachments = [] if isinstance(attachments, undefined.Undefined) else [a for a in attachments]

        if not isinstance(embed, undefined.Undefined):
            attachments.extend(embed.assets_to_upload)

        response = await self._request(
            route, body=self._build_message_creation_form(body, attachments) if attachments else body
        )

        return self._app.entity_factory.deserialize_message(response)

    async def edit_message(
        self,
        channel: typing.Union[channels.TextChannel, bases.UniqueObject],
        message: typing.Union[messages_.Message, bases.UniqueObject],
        text: typing.Union[undefined.Undefined, typing.Any] = undefined.Undefined(),
        *,
        embed: typing.Union[undefined.Undefined, embeds_.Embed] = undefined.Undefined(),
        mentions_everyone: typing.Union[undefined.Undefined, bool] = undefined.Undefined(),
        user_mentions: typing.Union[
            undefined.Undefined, typing.Collection[typing.Union[users.User, bases.UniqueObject]], bool
        ] = undefined.Undefined(),
        role_mentions: typing.Union[
            undefined.Undefined, typing.Collection[typing.Union[bases.UniqueObject, guilds.Role]], bool
        ] = undefined.Undefined(),
        flags: typing.Union[undefined.Undefined, messages_.MessageFlag] = undefined.Undefined(),
    ) -> messages_.Message:
        """Edit an existing message in a given channel.

        Parameters
        ----------
        channel : hikari.models.channels.PartialChannel or hikari.utilities.snowflake.Snowflake or int or str
            The channel to edit the message in. This may be a channel object, or
            the ID of an existing channel.
        message : hikari.models.messages.Messages or hikari.utilities.snowflake.Snowflake or int or str
            The message to fetch.
        text
        embed
        mentions_everyone
        user_mentions
        role_mentions
        flags

        Returns
        -------
        hikari.models.messages.Message
            The edited message.

        Raises
        ------
        hikari.errors.BadRequest
            This may be raised in several discrete situations, such as messages
            being empty with no embeds; messages with more than 2000 characters
            in them, embeds that exceed one of the many embed
            limits; invalid image URLs in embeds; users in `user_mentions` not
            being mentioned in the message content; roles in `role_mentions` not
            being mentioned in the message content.
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack permissions to send messages in the given channel; if
            you try to change the contents of another user's message; or if you
            try to edit the flags on another user's message without the
            permissions to manage messages_.
        hikari.errors.NotFound
            If the channel or message is not found.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.
        """
        route = routes.PATCH_CHANNEL_MESSAGE.compile(channel=channel, message=message)
        body = data_binding.JSONObjectBuilder()
        body.put("content", text, conversion=str)
        body.put("embed", embed, conversion=self._app.entity_factory.serialize_embed)
        body.put("flags", flags)
        body.put("allowed_mentions", self._generate_allowed_mentions(mentions_everyone, user_mentions, role_mentions))
        response = await self._request(route, body=body)
        return self._app.entity_factory.deserialize_message(response)

    async def delete_message(
        self,
        channel: typing.Union[channels.TextChannel, bases.UniqueObject],
        message: typing.Union[messages_.Message, bases.UniqueObject],
    ) -> None:
        """Delete a given message in a given channel.

        Parameters
        ----------
        channel
        message

        Raises
        ------
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack the permissions to manage messages, and the message is
            not composed by your associated user.
        hikari.errors.NotFound
            If the channel or message is not found.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.
        """
        route = routes.DELETE_CHANNEL_MESSAGE.compile(channel=channel, message=message)
        await self._request(route)

    async def delete_messages(
        self,
        channel: typing.Union[channels.GuildTextChannel, bases.UniqueObject],
        /,
        *messages: typing.Union[messages_.Message, bases.UniqueObject],
    ) -> None:
        """Bulk-delete between 2 and 100 messages from the given guild channel.

        Parameters
        ----------
        channel
        *messages

        Raises
        ------
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack the permissions to manage messages, and the message is
            not composed by your associated user.
        hikari.errors.NotFound
            If the channel or message is not found.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.
        TypeError
            If you do not provide between 2 and 100 messages (inclusive).
        """
        if 2 <= len(messages) <= 100:
            route = routes.POST_DELETE_CHANNEL_MESSAGES_BULK.compile(channel=channel)
            body = data_binding.JSONObjectBuilder()
            body.put_snowflake_array("messages", messages)
            await self._request(route, body=body)
        else:
            raise TypeError("Must delete a minimum of 2 messages and a maximum of 100")

    async def add_reaction(
        self,
        channel: typing.Union[channels.TextChannel, bases.UniqueObject],
        message: typing.Union[messages_.Message, bases.UniqueObject],
        emoji: typing.Union[str, emojis.UnicodeEmoji, emojis.KnownCustomEmoji],
    ) -> None:
        """Add a reaction emoji to a message in a given channel.

        Parameters
        ----------
        channel
        message
        emoji

        Raises
        ------
        hikari.errors.BadRequest
            If an invalid unicode emoji is given, or if the given custom emoji
            does not exist.
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack permissions to add reactions to messages.
        hikari.errors.NotFound
            If the channel or message is not found.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.
        """
        route = routes.PUT_MY_REACTION.compile(
            emoji=emoji.url_name if isinstance(emoji, emojis.KnownCustomEmoji) else str(emoji),
            channel=channel,
            message=message,
        )
        await self._request(route)

    async def delete_my_reaction(
        self,
        channel: typing.Union[channels.TextChannel, bases.UniqueObject],
        message: typing.Union[messages_.Message, bases.UniqueObject],
        emoji: typing.Union[str, emojis.UnicodeEmoji, emojis.KnownCustomEmoji],
    ) -> None:
        """Delete a reaction that your application user created.

        Parameters
        ----------
        channel
        message
        emoji

        Raises
        ------
        hikari.errors.BadRequest
            If an invalid unicode emoji is given, or if the given custom emoji
            does not exist.
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFound
            If the channel or message is not found.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.
        """
        route = routes.DELETE_MY_REACTION.compile(
            emoji=emoji.url_name if isinstance(emoji, emojis.KnownCustomEmoji) else str(emoji),
            channel=channel,
            message=message,
        )
        await self._request(route)

    async def delete_all_reactions_for_emoji(
        self,
        channel: typing.Union[channels.TextChannel, bases.UniqueObject],
        message: typing.Union[messages_.Message, bases.UniqueObject],
        emoji: typing.Union[str, emojis.UnicodeEmoji, emojis.KnownCustomEmoji],
    ) -> None:
        route = routes.DELETE_REACTION_EMOJI.compile(
            emoji=emoji.url_name if isinstance(emoji, emojis.KnownCustomEmoji) else str(emoji),
            channel=channel,
            message=message,
        )
        await self._request(route)

    async def delete_reaction(
        self,
        channel: typing.Union[channels.TextChannel, bases.UniqueObject],
        message: typing.Union[messages_.Message, bases.UniqueObject],
        emoji: typing.Union[str, emojis.UnicodeEmoji, emojis.KnownCustomEmoji],
        user: typing.Union[users.User, bases.UniqueObject],
    ) -> None:
        route = routes.DELETE_REACTION_USER.compile(
            emoji=emoji.url_name if isinstance(emoji, emojis.KnownCustomEmoji) else str(emoji),
            channel=channel,
            message=message,
            user=user,
        )
        await self._request(route)

    async def delete_all_reactions(
        self,
        channel: typing.Union[channels.TextChannel, bases.UniqueObject],
        message: typing.Union[messages_.Message, bases.UniqueObject],
    ) -> None:
        route = routes.DELETE_ALL_REACTIONS.compile(channel=channel, message=message)
        await self._request(route)

    def fetch_reactions_for_emoji(
        self,
        channel: typing.Union[channels.TextChannel, bases.UniqueObject],
        message: typing.Union[messages_.Message, bases.UniqueObject],
        emoji: typing.Union[str, emojis.UnicodeEmoji, emojis.KnownCustomEmoji],
    ) -> iterators.LazyIterator[users.User]:
        return iterators.ReactorIterator(
            app=self._app,
            request_call=self._request,
            channel_id=channel,
            message_id=message,
            emoji=emoji.url_name if isinstance(emoji, emojis.KnownCustomEmoji) else str(emoji),
        )

    async def create_webhook(
        self,
        channel: typing.Union[channels.TextChannel, bases.UniqueObject],
        name: str,
        *,
        avatar: typing.Union[undefined.Undefined, files.BaseStream] = undefined.Undefined(),
        reason: typing.Union[undefined.Undefined, str] = undefined.Undefined(),
    ) -> webhooks.Webhook:
        route = routes.POST_WEBHOOK.compile(channel=channel)
        body = data_binding.JSONObjectBuilder()
        body.put("name", name)
        if not isinstance(avatar, undefined.Undefined):
            body.put("avatar", await avatar.fetch_data_uri())

        response = await self._request(route, body=body, reason=reason)
        return self._app.entity_factory.deserialize_webhook(response)

    async def fetch_webhook(
        self,
        webhook: typing.Union[webhooks.Webhook, bases.UniqueObject],
        /,
        *,
        token: typing.Union[undefined.Undefined, str] = undefined.Undefined(),
    ) -> webhooks.Webhook:
        if isinstance(token, undefined.Undefined):
            route = routes.GET_WEBHOOK.compile(webhook=webhook)
        else:
            route = routes.GET_WEBHOOK_WITH_TOKEN.compile(webhook=webhook, token=token)
        response = await self._request(route)
        return self._app.entity_factory.deserialize_webhook(response)

    async def fetch_channel_webhooks(
        self, channel: typing.Union[channels.TextChannel, bases.UniqueObject], /
    ) -> typing.Sequence[webhooks.Webhook]:
        route = routes.GET_CHANNEL_WEBHOOKS.compile(channel=channel)
        response = await self._request(route)
        return data_binding.cast_json_array(response, self._app.entity_factory.deserialize_webhook)

    async def fetch_guild_webhooks(
        self, guild: typing.Union[guilds.Guild, bases.UniqueObject], /
    ) -> typing.Sequence[webhooks.Webhook]:
        route = routes.GET_GUILD_WEBHOOKS.compile(channel=guild)
        response = await self._request(route)
        return data_binding.cast_json_array(response, self._app.entity_factory.deserialize_webhook)

    async def edit_webhook(
        self,
        webhook: typing.Union[webhooks.Webhook, bases.UniqueObject],
        /,
        *,
        token: typing.Union[undefined.Undefined, str] = undefined.Undefined(),
        name: typing.Union[undefined.Undefined, str] = undefined.Undefined(),
        avatar: typing.Union[undefined.Undefined, files.BaseStream] = undefined.Undefined(),
        channel: typing.Union[undefined.Undefined, channels.TextChannel, bases.UniqueObject] = undefined.Undefined(),
        reason: typing.Union[undefined.Undefined, str] = undefined.Undefined(),
    ) -> webhooks.Webhook:
        if isinstance(token, undefined.Undefined):
            route = routes.PATCH_WEBHOOK.compile(webhook=webhook)
        else:
            route = routes.PATCH_WEBHOOK_WITH_TOKEN.compile(webhook=webhook, token=token)

        body = data_binding.JSONObjectBuilder()
        body.put("name", name)
        body.put_snowflake("channel", channel)
        if not isinstance(avatar, undefined.Undefined):
            body.put("avatar", await avatar.fetch_data_uri())

        response = await self._request(route, body=body, reason=reason)
        return self._app.entity_factory.deserialize_webhook(response)

    async def delete_webhook(
        self,
        webhook: typing.Union[webhooks.Webhook, bases.UniqueObject],
        /,
        *,
        token: typing.Union[undefined.Undefined, str] = undefined.Undefined(),
    ) -> None:
        if isinstance(token, undefined.Undefined):
            route = routes.DELETE_WEBHOOK.compile(webhook=webhook)
        else:
            route = routes.DELETE_WEBHOOK_WITH_TOKEN.compile(webhook=webhook, token=token)
        await self._request(route)

    async def execute_webhook(
        self,
        webhook: typing.Union[webhooks.Webhook, bases.UniqueObject],
        text: typing.Union[undefined.Undefined, typing.Any] = undefined.Undefined(),
        *,
        token: typing.Union[undefined.Undefined, str] = undefined.Undefined(),
        username: typing.Union[undefined.Undefined, str] = undefined.Undefined(),
        avatar_url: typing.Union[undefined.Undefined, str] = undefined.Undefined(),
        embeds: typing.Union[undefined.Undefined, typing.Sequence[embeds_.Embed]] = undefined.Undefined(),
        attachments: typing.Union[undefined.Undefined, typing.Sequence[files.BaseStream]] = undefined.Undefined(),
        tts: typing.Union[undefined.Undefined, bool] = undefined.Undefined(),
        wait: typing.Union[undefined.Undefined, bool] = undefined.Undefined(),
        mentions_everyone: bool = True,
        user_mentions: typing.Union[typing.Collection[typing.Union[users.User, bases.UniqueObject]], bool] = True,
        role_mentions: typing.Union[typing.Collection[typing.Union[bases.UniqueObject, guilds.Role]], bool] = True,
    ) -> messages_.Message:
        if isinstance(token, undefined.Undefined):
            route = routes.POST_WEBHOOK.compile(webhook=webhook)
            no_auth = False
        else:
            route = routes.POST_WEBHOOK_WITH_TOKEN.compile(webhook=webhook, token=token)
            no_auth = True

        attachments = [] if isinstance(attachments, undefined.Undefined) else [a for a in attachments]
        serialized_embeds = []

        if not isinstance(embeds, undefined.Undefined):
            for embed in embeds:
                attachments.extend(embed.assets_to_upload)
                serialized_embeds.append(self._app.entity_factory.serialize_embed(embed))

        body = data_binding.JSONObjectBuilder()
        body.put("mentions", self._generate_allowed_mentions(mentions_everyone, user_mentions, role_mentions))
        body.put("content", text, conversion=str)
        body.put("embeds", serialized_embeds)
        body.put("username", username)
        body.put("avatar_url", avatar_url)
        body.put("tts", tts)
        body.put("wait", wait)

        response = await self._request(
            route, body=self._build_message_creation_form(body, attachments) if attachments else body, no_auth=no_auth,
        )

        return self._app.entity_factory.deserialize_message(response)

    async def fetch_gateway_url(self) -> str:
        route = routes.GET_GATEWAY.compile()
        # This doesn't need authorization.
        response = await self._request(route, no_auth=True)
        return response["url"]

    async def fetch_gateway_bot(self) -> gateway.GatewayBot:
        route = routes.GET_GATEWAY_BOT.compile()
        response = await self._request(route)
        return self._app.entity_factory.deserialize_gateway_bot(response)

    async def fetch_invite(self, invite: typing.Union[invites.Invite, str]) -> invites.Invite:
        route = routes.GET_INVITE.compile(invite_code=invite if isinstance(invite, str) else invite.code)
        query = data_binding.StringMapBuilder()
        query.put("with_counts", True)
        response = await self._request(route, query=query)
        return self._app.entity_factory.deserialize_invite(response)

    async def delete_invite(self, invite: typing.Union[invites.Invite, str]) -> None:
        route = routes.DELETE_INVITE.compile(invite_code=invite if isinstance(invite, str) else invite.code)
        await self._request(route)

    async def fetch_my_user(self) -> users.OwnUser:
        route = routes.GET_MY_USER.compile()
        response = await self._request(route)
        return self._app.entity_factory.deserialize_my_user(response)

    async def edit_my_user(
        self,
        *,
        username: typing.Union[undefined.Undefined, str] = undefined.Undefined(),
        avatar: typing.Union[undefined.Undefined, files.BaseStream] = undefined.Undefined(),
    ) -> users.OwnUser:
        route = routes.PATCH_MY_USER.compile()
        body = data_binding.JSONObjectBuilder()
        body.put("username", username)

        if not isinstance(username, undefined.Undefined):
            body.put("avatar", await avatar.fetch_data_uri())

        response = await self._request(route, body=body)
        return self._app.entity_factory.deserialize_my_user(response)

    async def fetch_my_connections(self) -> typing.Sequence[applications.OwnConnection]:
        route = routes.GET_MY_CONNECTIONS.compile()
        response = await self._request(route)
        return data_binding.cast_json_array(response, self._app.entity_factory.deserialize_own_connection)

    def fetch_my_guilds(
        self,
        *,
        newest_first: bool = False,
        start_at: typing.Union[
            undefined.Undefined, guilds.PartialGuild, bases.UniqueObject, datetime.datetime
        ] = undefined.Undefined(),
    ) -> iterators.LazyIterator[applications.OwnGuild]:
        if isinstance(start_at, undefined.Undefined):
            start_at = snowflake.Snowflake.max() if newest_first else snowflake.Snowflake.min()
        elif isinstance(start_at, datetime.datetime):
            start_at = snowflake.Snowflake.from_datetime(start_at)

        return iterators.OwnGuildIterator(self._app, self._request, newest_first, start_at)

    async def leave_guild(self, guild: typing.Union[guilds.Guild, bases.UniqueObject], /) -> None:
        route = routes.DELETE_MY_GUILD.compile(guild=guild)
        await self._request(route)

    async def create_dm_channel(self, user: typing.Union[users.User, bases.UniqueObject], /) -> channels.DMChannel:
        route = routes.POST_MY_CHANNELS.compile()
        body = data_binding.JSONObjectBuilder()
        body.put_snowflake("recipient_id", user)
        response = await self._request(route, body=body)
        return self._app.entity_factory.deserialize_dm_channel(response)

    async def fetch_application(self) -> applications.Application:
        route = routes.GET_MY_APPLICATION.compile()
        response = await self._request(route)
        return self._app.entity_factory.deserialize_application(response)

    async def add_user_to_guild(
        self,
        access_token: str,
        guild: typing.Union[guilds.Guild, bases.UniqueObject],
        user: typing.Union[users.User, bases.UniqueObject],
        *,
        nick: typing.Union[undefined.Undefined, str] = undefined.Undefined(),
        roles: typing.Union[
            undefined.Undefined, typing.Collection[typing.Union[guilds.Role, bases.UniqueObject]]
        ] = undefined.Undefined(),
        mute: typing.Union[undefined.Undefined, bool] = undefined.Undefined(),
        deaf: typing.Union[undefined.Undefined, bool] = undefined.Undefined(),
    ) -> typing.Optional[guilds.Member]:
        route = routes.PUT_GUILD_MEMBER.compile(guild=guild, user=user)
        body = data_binding.JSONObjectBuilder()
        body.put("access_token", access_token)
        body.put("nick", nick)
        body.put("mute", mute)
        body.put("deaf", deaf)
        body.put_snowflake_array("roles", roles)

        if (response := await self._request(route, body=body)) is not None:
            return self._app.entity_factory.deserialize_member(response)
        else:
            # User already is in the guild.
            return None

    async def fetch_voice_regions(self) -> typing.Sequence[voices.VoiceRegion]:
        route = routes.GET_VOICE_REGIONS.compile()
        response = await self._request(route)
        return data_binding.cast_json_array(response, self._app.entity_factory.deserialize_voice_region)

    async def fetch_user(self, user: typing.Union[users.User, bases.UniqueObject]) -> users.User:
        route = routes.GET_USER.compile(user=user)
        response = await self._request(route)
        return self._app.entity_factory.deserialize_user(response)

    def fetch_audit_log(
        self,
        guild: typing.Union[guilds.Guild, bases.UniqueObject],
        /,
        *,
        before: typing.Union[undefined.Undefined, datetime.datetime, bases.UniqueObject] = undefined.Undefined(),
        user: typing.Union[undefined.Undefined, users.User, bases.UniqueObject] = undefined.Undefined(),
        event_type: typing.Union[undefined.Undefined, audit_logs.AuditLogEventType] = undefined.Undefined(),
    ) -> iterators.LazyIterator[audit_logs.AuditLog]:
        if isinstance(before, undefined.Undefined):
            before = snowflake.Snowflake.max()
        elif isinstance(before, datetime.datetime):
            before = snowflake.Snowflake.from_datetime(before)

        return iterators.AuditLogIterator(self._app, self._request, guild, before, user, event_type)

    async def fetch_emoji(
        self,
        guild: typing.Union[guilds.Guild, bases.UniqueObject],
        # This is an emoji ID, which is the URL-safe emoji name, not the snowflake alone.
        emoji: typing.Union[emojis.KnownCustomEmoji, str],
    ) -> emojis.KnownCustomEmoji:
        route = routes.GET_GUILD_EMOJI.compile(
            guild=guild, emoji=emoji.url_name if isinstance(emoji, emojis.Emoji) else emoji,
        )
        response = await self._request(route)
        return self._app.entity_factory.deserialize_known_custom_emoji(response)

    async def fetch_guild_emojis(
        self, guild: typing.Union[guilds.Guild, bases.UniqueObject], /
    ) -> typing.Set[emojis.KnownCustomEmoji]:
        route = routes.GET_GUILD_EMOJIS.compile(guild=guild)
        response = await self._request(route)
        return data_binding.cast_json_array(response, self._app.entity_factory.deserialize_known_custom_emoji, set)

    async def create_emoji(
        self,
        guild: typing.Union[guilds.Guild, bases.UniqueObject],
        name: str,
        image: files.BaseStream,
        *,
        roles: typing.Union[
            undefined.Undefined, typing.Collection[typing.Union[guilds.Role, bases.UniqueObject]]
        ] = undefined.Undefined(),
        reason: typing.Union[undefined.Undefined, str] = undefined.Undefined(),
    ) -> emojis.KnownCustomEmoji:
        route = routes.POST_GUILD_EMOJIS.compile(guild=guild)
        body = data_binding.JSONObjectBuilder()
        body.put("name", name)
        if not isinstance(image, undefined.Undefined):
            body.put("image", await image.fetch_data_uri())

        body.put_snowflake_array("roles", roles)

        response = await self._request(route, body=body, reason=reason)

        return self._app.entity_factory.deserialize_known_custom_emoji(response)

    async def edit_emoji(
        self,
        guild: typing.Union[guilds.Guild, bases.UniqueObject],
        # This is an emoji ID, which is the URL-safe emoji name, not the snowflake alone.
        emoji: typing.Union[emojis.KnownCustomEmoji, str],
        *,
        name: typing.Union[undefined.Undefined, str] = undefined.Undefined(),
        roles: typing.Union[
            undefined.Undefined, typing.Collection[typing.Union[guilds.Role, bases.UniqueObject]]
        ] = undefined.Undefined(),
        reason: typing.Union[undefined.Undefined, str] = undefined.Undefined(),
    ) -> emojis.KnownCustomEmoji:
        route = routes.PATCH_GUILD_EMOJI.compile(
            guild=guild, emoji=emoji.url_name if isinstance(emoji, emojis.Emoji) else emoji,
        )
        body = data_binding.JSONObjectBuilder()
        body.put("name", name)
        body.put_snowflake_array("roles", roles)

        response = await self._request(route, body=body, reason=reason)

        return self._app.entity_factory.deserialize_known_custom_emoji(response)

    async def delete_emoji(
        self,
        guild: typing.Union[guilds.Guild, bases.UniqueObject],
        # This is an emoji ID, which is the URL-safe emoji name, not the snowflake alone.
        emoji: typing.Union[emojis.KnownCustomEmoji, str],
        # Reason is not currently supported for some reason. See
    ) -> None:
        route = routes.DELETE_GUILD_EMOJI.compile(
            guild=guild, emoji=emoji.url_name if isinstance(emoji, emojis.Emoji) else emoji,
        )
        await self._request(route)

    def create_guild(self, name: str, /) -> rest_utils.GuildBuilder:
        return rest_utils.GuildBuilder(app=self._app, name=name, request_call=self._request)

    async def fetch_guild(self, guild: typing.Union[guilds.Guild, bases.UniqueObject], /) -> guilds.Guild:
        route = routes.GET_GUILD.compile(guild=guild)
        response = await self._request(route)
        return self._app.entity_factory.deserialize_guild(response)

    async def fetch_guild_preview(
        self, guild: typing.Union[guilds.PartialGuild, bases.UniqueObject], /
    ) -> guilds.GuildPreview:
        route = routes.GET_GUILD_PREVIEW.compile(guild=guild)
        response = await self._request(route)
        return self._app.entity_factory.deserialize_guild_preview(response)

    async def edit_guild(
        self,
        guild: typing.Union[guilds.Guild, bases.UniqueObject],
        /,
        *,
        name: typing.Union[undefined.Undefined, str] = undefined.Undefined(),
        region: typing.Union[undefined.Undefined, voices.VoiceRegion, str] = undefined.Undefined(),
        verification_level: typing.Union[undefined.Undefined, guilds.GuildVerificationLevel] = undefined.Undefined(),
        default_message_notifications: typing.Union[
            undefined.Undefined, guilds.GuildMessageNotificationsLevel
        ] = undefined.Undefined(),
        explicit_content_filter_level: typing.Union[
            undefined.Undefined, guilds.GuildExplicitContentFilterLevel
        ] = undefined.Undefined(),
        afk_channel: typing.Union[
            undefined.Undefined, channels.GuildVoiceChannel, bases.UniqueObject
        ] = undefined.Undefined(),
        afk_timeout: typing.Union[undefined.Undefined, date.TimeSpan] = undefined.Undefined(),
        icon: typing.Union[undefined.Undefined, files.BaseStream] = undefined.Undefined(),
        owner: typing.Union[undefined.Undefined, users.User, bases.UniqueObject] = undefined.Undefined(),
        splash: typing.Union[undefined.Undefined, files.BaseStream] = undefined.Undefined(),
        banner: typing.Union[undefined.Undefined, files.BaseStream] = undefined.Undefined(),
        system_channel: typing.Union[undefined.Undefined, channels.GuildTextChannel] = undefined.Undefined(),
        rules_channel: typing.Union[undefined.Undefined, channels.GuildTextChannel] = undefined.Undefined(),
        public_updates_channel: typing.Union[undefined.Undefined, channels.GuildTextChannel] = undefined.Undefined(),
        preferred_locale: typing.Union[undefined.Undefined, str] = undefined.Undefined(),
        reason: typing.Union[undefined.Undefined, str] = undefined.Undefined(),
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

        if not isinstance(icon, undefined.Undefined):
            body.put("icon", await icon.fetch_data_uri())

        if not isinstance(splash, undefined.Undefined):
            body.put("splash", await splash.fetch_data_uri())

        if not isinstance(banner, undefined.Undefined):
            body.put("banner", await banner.fetch_data_uri())

        response = await self._request(route, body=body, reason=reason)

        return self._app.entity_factory.deserialize_guild(response)

    async def delete_guild(self, guild: typing.Union[guilds.Guild, bases.UniqueObject]) -> None:
        route = routes.DELETE_GUILD.compile(guild=guild)
        await self._request(route)

    async def fetch_guild_channels(
        self, guild: typing.Union[guilds.Guild, bases.UniqueObject]
    ) -> typing.Sequence[channels.GuildChannel]:
        route = routes.GET_GUILD_CHANNELS.compile(guild=guild)
        response = await self._request(route)
        channel_sequence = data_binding.cast_json_array(response, self._app.entity_factory.deserialize_channel)
        # Will always be guild channels unless Discord messes up severely on something!
        return typing.cast(typing.Sequence[channels.GuildChannel], channel_sequence)

    async def create_guild_text_channel(
        self,
        guild: typing.Union[guilds.Guild, bases.UniqueObject],
        name: str,
        *,
        position: typing.Union[int, undefined.Undefined] = undefined.Undefined(),
        topic: typing.Union[str, undefined.Undefined] = undefined.Undefined(),
        nsfw: typing.Union[bool, undefined.Undefined] = undefined.Undefined(),
        rate_limit_per_user: typing.Union[int, undefined.Undefined] = undefined.Undefined(),
        permission_overwrites: typing.Union[
            typing.Sequence[channels.PermissionOverwrite], undefined.Undefined
        ] = undefined.Undefined(),
        category: typing.Union[channels.GuildCategory, bases.UniqueObject, undefined.Undefined] = undefined.Undefined(),
        reason: typing.Union[str, undefined.Undefined] = undefined.Undefined(),
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
        guild: typing.Union[guilds.Guild, bases.UniqueObject],
        name: str,
        *,
        position: typing.Union[int, undefined.Undefined] = undefined.Undefined(),
        topic: typing.Union[str, undefined.Undefined] = undefined.Undefined(),
        nsfw: typing.Union[bool, undefined.Undefined] = undefined.Undefined(),
        rate_limit_per_user: typing.Union[int, undefined.Undefined] = undefined.Undefined(),
        permission_overwrites: typing.Union[
            typing.Sequence[channels.PermissionOverwrite], undefined.Undefined
        ] = undefined.Undefined(),
        category: typing.Union[channels.GuildCategory, bases.UniqueObject, undefined.Undefined] = undefined.Undefined(),
        reason: typing.Union[str, undefined.Undefined] = undefined.Undefined(),
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
        guild: typing.Union[guilds.Guild, bases.UniqueObject],
        name: str,
        *,
        position: typing.Union[int, undefined.Undefined] = undefined.Undefined(),
        nsfw: typing.Union[bool, undefined.Undefined] = undefined.Undefined(),
        user_limit: typing.Union[int, undefined.Undefined] = undefined.Undefined(),
        bitrate: typing.Union[int, undefined.Undefined] = undefined.Undefined(),
        permission_overwrites: typing.Union[
            typing.Sequence[channels.PermissionOverwrite], undefined.Undefined
        ] = undefined.Undefined(),
        category: typing.Union[channels.GuildCategory, bases.UniqueObject, undefined.Undefined] = undefined.Undefined(),
        reason: typing.Union[str, undefined.Undefined] = undefined.Undefined(),
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
        guild: typing.Union[guilds.Guild, bases.UniqueObject],
        name: str,
        *,
        position: typing.Union[int, undefined.Undefined] = undefined.Undefined(),
        nsfw: typing.Union[bool, undefined.Undefined] = undefined.Undefined(),
        permission_overwrites: typing.Union[
            typing.Sequence[channels.PermissionOverwrite], undefined.Undefined
        ] = undefined.Undefined(),
        reason: typing.Union[str, undefined.Undefined] = undefined.Undefined(),
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
        guild: typing.Union[guilds.Guild, bases.UniqueObject],
        name: str,
        type_: channels.ChannelType,
        *,
        position: typing.Union[int, undefined.Undefined] = undefined.Undefined(),
        topic: typing.Union[str, undefined.Undefined] = undefined.Undefined(),
        nsfw: typing.Union[bool, undefined.Undefined] = undefined.Undefined(),
        bitrate: typing.Union[int, undefined.Undefined] = undefined.Undefined(),
        user_limit: typing.Union[int, undefined.Undefined] = undefined.Undefined(),
        rate_limit_per_user: typing.Union[int, undefined.Undefined] = undefined.Undefined(),
        permission_overwrites: typing.Union[
            typing.Sequence[channels.PermissionOverwrite], undefined.Undefined
        ] = undefined.Undefined(),
        category: typing.Union[channels.GuildCategory, bases.UniqueObject, undefined.Undefined] = undefined.Undefined(),
        reason: typing.Union[str, undefined.Undefined] = undefined.Undefined(),
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

        response = await self._request(route, body=body, reason=reason)
        channel = self._app.entity_factory.deserialize_channel(response)
        return typing.cast(channels.GuildChannel, channel)

    async def reposition_channels(
        self,
        guild: typing.Union[guilds.Guild, bases.UniqueObject],
        positions: typing.Mapping[int, typing.Union[channels.GuildChannel, bases.UniqueObject]],
    ) -> None:
        route = routes.POST_GUILD_CHANNELS.compile(guild=guild)
        body = [{"id": str(int(channel)), "position": pos} for pos, channel in positions.items()]
        await self._request(route, body=body)

    async def fetch_member(
        self, guild: typing.Union[guilds.Guild, bases.UniqueObject], user: typing.Union[users.User, bases.UniqueObject],
    ) -> guilds.Member:
        route = routes.GET_GUILD_MEMBER.compile(guild=guild, user=user)
        response = await self._request(route)
        return self._app.entity_factory.deserialize_member(response)

    def fetch_members(
        self, guild: typing.Union[guilds.Guild, bases.UniqueObject],
    ) -> iterators.LazyIterator[guilds.Member]:
        return iterators.MemberIterator(self._app, self._request, guild)

    async def edit_member(
        self,
        guild: typing.Union[guilds.Guild, bases.UniqueObject],
        user: typing.Union[users.User, bases.UniqueObject],
        *,
        nick: typing.Union[undefined.Undefined, str] = undefined.Undefined(),
        roles: typing.Union[
            undefined.Undefined, typing.Collection[typing.Union[guilds.Role, bases.UniqueObject]]
        ] = undefined.Undefined(),
        mute: typing.Union[undefined.Undefined, bool] = undefined.Undefined(),
        deaf: typing.Union[undefined.Undefined, bool] = undefined.Undefined(),
        voice_channel: typing.Union[
            undefined.Undefined, channels.GuildVoiceChannel, bases.UniqueObject, None
        ] = undefined.Undefined(),
        reason: typing.Union[str, undefined.Undefined] = undefined.Undefined(),
    ) -> None:
        route = routes.PATCH_GUILD_MEMBER.compile(guild=guild, user=user)
        body = data_binding.JSONObjectBuilder()
        body.put("nick", nick)
        body.put("mute", mute)
        body.put("deaf", deaf)
        body.put_snowflake_array("roles", roles)

        if voice_channel is None:
            body.put("channel_id", None)
        elif not isinstance(voice_channel, undefined.Undefined):
            body.put_snowflake("channel_id", voice_channel)

        await self._request(route, body=body, reason=reason)

    async def edit_my_nick(
        self,
        guild: typing.Union[guilds.Guild, bases.UniqueObject],
        nick: typing.Optional[str],
        *,
        reason: typing.Union[undefined.Undefined, str] = undefined.Undefined(),
    ) -> None:
        route = routes.PATCH_MY_GUILD_NICKNAME.compile(guild=guild)
        body = data_binding.JSONObjectBuilder()
        body.put("nick", nick)
        await self._request(route, body=body, reason=reason)

    async def add_role_to_member(
        self,
        guild: typing.Union[guilds.Guild, bases.UniqueObject],
        user: typing.Union[users.User, bases.UniqueObject],
        role: typing.Union[guilds.Role, bases.UniqueObject],
        *,
        reason: typing.Union[undefined.Undefined, str] = undefined.Undefined(),
    ) -> None:
        route = routes.PUT_GUILD_MEMBER_ROLE.compile(guild=guild, user=user, role=role)
        await self._request(route, reason=reason)

    async def remove_role_from_member(
        self,
        guild: typing.Union[guilds.Guild, bases.UniqueObject],
        user: typing.Union[users.User, bases.UniqueObject],
        role: typing.Union[guilds.Role, bases.UniqueObject],
        *,
        reason: typing.Union[undefined.Undefined, str] = undefined.Undefined(),
    ) -> None:
        route = routes.DELETE_GUILD_MEMBER_ROLE.compile(guild=guild, user=user, role=role)
        await self._request(route, reason=reason)

    async def kick_member(
        self,
        guild: typing.Union[guilds.Guild, bases.UniqueObject],
        user: typing.Union[users.User, bases.UniqueObject],
        *,
        reason: typing.Union[undefined.Undefined, str] = undefined.Undefined(),
    ) -> None:
        route = routes.DELETE_GUILD_MEMBER.compile(guild=guild, user=user,)
        await self._request(route, reason=reason)

    async def ban_user(
        self,
        guild: typing.Union[guilds.Guild, bases.UniqueObject],
        user: typing.Union[users.User, bases.UniqueObject],
        *,
        reason: typing.Union[undefined.Undefined, str] = undefined.Undefined(),
    ) -> None:
        route = routes.PUT_GUILD_BAN.compile(guild=guild, user=user)
        await self._request(route, reason=reason)

    async def unban_user(
        self,
        guild: typing.Union[guilds.Guild, bases.UniqueObject],
        user: typing.Union[users.User, bases.UniqueObject],
        *,
        reason: typing.Union[undefined.Undefined, str] = undefined.Undefined(),
    ) -> None:
        route = routes.DELETE_GUILD_BAN.compile(guild=guild, user=user)
        await self._request(route, reason=reason)

    async def fetch_ban(
        self, guild: typing.Union[guilds.Guild, bases.UniqueObject], user: typing.Union[users.User, bases.UniqueObject],
    ) -> guilds.GuildMemberBan:
        route = routes.GET_GUILD_BAN.compile(guild=guild, user=user)
        response = await self._request(route)
        return self._app.entity_factory.deserialize_guild_member_ban(response)

    async def fetch_bans(
        self, guild: typing.Union[guilds.Guild, bases.UniqueObject], /
    ) -> typing.Sequence[guilds.GuildMemberBan]:
        route = routes.GET_GUILD_BANS.compile(guild=guild)
        response = await self._request(route)
        return data_binding.cast_json_array(response, self._app.entity_factory.deserialize_guild_member_ban)

    async def fetch_roles(
        self, guild: typing.Union[guilds.Guild, bases.UniqueObject], /
    ) -> typing.Sequence[guilds.Role]:
        route = routes.GET_GUILD_ROLES.compile(guild=guild)
        response = await self._request(route)
        return data_binding.cast_json_array(response, self._app.entity_factory.deserialize_role)

    async def create_role(
        self,
        guild: typing.Union[guilds.Guild, bases.UniqueObject],
        /,
        *,
        name: typing.Union[undefined.Undefined, str] = undefined.Undefined(),
        permissions: typing.Union[undefined.Undefined, permissions_.Permission] = undefined.Undefined(),
        color: typing.Union[undefined.Undefined, colors.Color] = undefined.Undefined(),
        colour: typing.Union[undefined.Undefined, colors.Color] = undefined.Undefined(),
        hoist: typing.Union[undefined.Undefined, bool] = undefined.Undefined(),
        mentionable: typing.Union[undefined.Undefined, bool] = undefined.Undefined(),
        reason: typing.Union[undefined.Undefined, str] = undefined.Undefined(),
    ) -> guilds.Role:
        if not undefined.Undefined.count(color, colour):
            raise TypeError("Can not specify 'color' and 'colour' together.")

        route = routes.POST_GUILD_ROLES.compile(guild=guild)
        body = data_binding.JSONObjectBuilder()
        body.put("name", name)
        body.put("permissions", permissions)
        body.put("color", color)
        body.put("color", colour)
        body.put("hoist", hoist)
        body.put("mentionable", mentionable)

        response = await self._request(route, body=body, reason=reason)
        return self._app.entity_factory.deserialize_role(response)

    async def reposition_roles(
        self,
        guild: typing.Union[guilds.Guild, bases.UniqueObject],
        positions: typing.Mapping[int, typing.Union[guilds.Role, bases.UniqueObject]],
    ) -> None:
        route = routes.POST_GUILD_ROLES.compile(guild=guild)
        body = [{"id": str(int(role)), "position": pos} for pos, role in positions.items()]
        await self._request(route, body=body)

    async def edit_role(
        self,
        guild: typing.Union[guilds.Guild, bases.UniqueObject],
        role: typing.Union[guilds.Role, bases.UniqueObject],
        *,
        name: typing.Union[undefined.Undefined, str] = undefined.Undefined(),
        permissions: typing.Union[undefined.Undefined, permissions_.Permission] = undefined.Undefined(),
        color: typing.Union[undefined.Undefined, colors.Color] = undefined.Undefined(),
        colour: typing.Union[undefined.Undefined, colors.Color] = undefined.Undefined(),
        hoist: typing.Union[undefined.Undefined, bool] = undefined.Undefined(),
        mentionable: typing.Union[undefined.Undefined, bool] = undefined.Undefined(),
        reason: typing.Union[undefined.Undefined, str] = undefined.Undefined(),
    ) -> guilds.Role:
        if not undefined.Undefined.count(color, colour):
            raise TypeError("Can not specify 'color' and 'colour' together.")

        route = routes.PATCH_GUILD_ROLE.compile(guild=guild, role=role)

        body = data_binding.JSONObjectBuilder()
        body.put("name", name)
        body.put("permissions", permissions)
        body.put("color", color)
        body.put("color", colour)
        body.put("hoist", hoist)
        body.put("mentionable", mentionable)

        response = await self._request(route, body=body, reason=reason)
        return self._app.entity_factory.deserialize_role(response)

    async def delete_role(
        self,
        guild: typing.Union[guilds.Guild, bases.UniqueObject],
        role: typing.Union[guilds.Role, bases.UniqueObject],
    ) -> None:
        route = routes.DELETE_GUILD_ROLE.compile(guild=guild, role=role)
        await self._request(route)

    async def estimate_guild_prune_count(
        self, guild: typing.Union[guilds.Guild, bases.UniqueObject], days: int,
    ) -> int:
        route = routes.GET_GUILD_PRUNE.compile(guild=guild)
        query = data_binding.StringMapBuilder()
        query.put("days", days)
        response = await self._request(route, query=query)
        return int(response["pruned"])

    async def begin_guild_prune(
        self,
        guild: typing.Union[guilds.Guild, bases.UniqueObject],
        days: int,
        *,
        reason: typing.Union[undefined.Undefined, str],
    ) -> int:
        route = routes.POST_GUILD_PRUNE.compile(guild=guild)
        query = data_binding.StringMapBuilder()
        query.put("compute_prune_count", True)
        query.put("days", days)
        response = await self._request(route, query=query, reason=reason)
        return int(response["pruned"])

    async def fetch_guild_voice_regions(
        self, guild: typing.Union[guilds.Guild, bases.UniqueObject], /
    ) -> typing.Sequence[voices.VoiceRegion]:
        route = routes.GET_GUILD_VOICE_REGIONS.compile(guild=guild)
        response = await self._request(route)
        return data_binding.cast_json_array(response, self._app.entity_factory.deserialize_voice_region)

    async def fetch_guild_invites(
        self, guild: typing.Union[guilds.Guild, bases.UniqueObject], /
    ) -> typing.Sequence[invites.InviteWithMetadata]:
        route = routes.GET_GUILD_INVITES.compile(guild=guild)
        response = await self._request(route)
        return data_binding.cast_json_array(response, self._app.entity_factory.deserialize_invite_with_metadata)

    async def fetch_integrations(
        self, guild: typing.Union[guilds.Guild, bases.UniqueObject], /
    ) -> typing.Sequence[guilds.Integration]:
        route = routes.GET_GUILD_INTEGRATIONS.compile(guild=guild)
        response = await self._request(route)
        return data_binding.cast_json_array(response, self._app.entity_factory.deserialize_integration)

    async def edit_integration(
        self,
        guild: typing.Union[guilds.Guild, bases.UniqueObject],
        integration: typing.Union[guilds.Integration, bases.UniqueObject],
        *,
        expire_behaviour: typing.Union[undefined.Undefined, guilds.IntegrationExpireBehaviour] = undefined.Undefined(),
        expire_grace_period: typing.Union[undefined.Undefined, date.TimeSpan] = undefined.Undefined(),
        enable_emojis: typing.Union[undefined.Undefined, bool] = undefined.Undefined(),
        reason: typing.Union[undefined.Undefined, str] = undefined.Undefined(),
    ) -> None:
        route = routes.PATCH_GUILD_INTEGRATION.compile(guild=guild, integration=integration)
        body = data_binding.JSONObjectBuilder()
        body.put("expire_behaviour", expire_behaviour)
        body.put("expire_grace_period", expire_grace_period, conversion=date.timespan_to_int)
        # Inconsistent naming in the API itself, so I have changed the name.
        body.put("enable_emoticons", enable_emojis)
        await self._request(route, body=body, reason=reason)

    async def delete_integration(
        self,
        guild: typing.Union[guilds.Guild, bases.UniqueObject],
        integration: typing.Union[guilds.Integration, bases.UniqueObject],
        *,
        reason: typing.Union[undefined.Undefined, str] = undefined.Undefined(),
    ) -> None:
        route = routes.DELETE_GUILD_INTEGRATION.compile(guild=guild, integration=integration)
        await self._request(route, reason=reason)

    async def sync_integration(
        self,
        guild: typing.Union[guilds.Guild, bases.UniqueObject],
        integration: typing.Union[guilds.Integration, bases.UniqueObject],
    ) -> None:
        route = routes.POST_GUILD_INTEGRATION_SYNC.compile(guild=guild, integration=integration)
        await self._request(route)

    async def fetch_widget(self, guild: typing.Union[guilds.Guild, bases.UniqueObject], /) -> guilds.GuildWidget:
        route = routes.GET_GUILD_WIDGET.compile(guild=guild)
        response = await self._request(route)
        return self._app.entity_factory.deserialize_guild_widget(response)

    async def edit_widget(
        self,
        guild: typing.Union[guilds.Guild, bases.UniqueObject],
        /,
        *,
        channel: typing.Union[
            undefined.Undefined, channels.GuildChannel, bases.UniqueObject, None
        ] = undefined.Undefined(),
        enabled: typing.Union[undefined.Undefined, bool] = undefined.Undefined(),
        reason: typing.Union[undefined.Undefined, str] = undefined.Undefined(),
    ) -> guilds.GuildWidget:
        route = routes.PATCH_GUILD_WIDGET.compile(guild=guild)

        body = data_binding.JSONObjectBuilder()
        body.put("enabled", enabled)
        if channel is None:
            body.put("channel", None)
        elif not isinstance(channel, undefined.Undefined):
            body.put_snowflake("channel", channel)

        response = await self._request(route, body=body, reason=reason)
        return self._app.entity_factory.deserialize_guild_widget(response)

    async def fetch_vanity_url(self, guild: typing.Union[guilds.Guild, bases.UniqueObject], /) -> invites.VanityURL:
        route = routes.GET_GUILD_VANITY_URL.compile(guild=guild)
        response = await self._request(route)
        return self._app.entity_factory.deserialize_vanity_url(response)
