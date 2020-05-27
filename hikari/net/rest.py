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

from hikari import errors
from hikari import http_settings
from hikari import rest_app
from hikari.internal import class_helpers
from hikari.internal import conversions
from hikari.internal import more_collections
from hikari.internal import more_typing
from hikari.internal import ratelimits
from hikari.internal import unset
from hikari.net import buckets
from hikari.net import http_client
from hikari.net import iterators
from hikari.net import rest_utils
from hikari.net import routes

if typing.TYPE_CHECKING:
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


class REST(http_client.HTTPClient):
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
    token_type : str
        The type of token in use. If no token is used, this can be ignored and
        left to the default value. This can be `"Bot"` or `"Bearer"`.
    url : str
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
        app: rest_app.IRESTApp,
        config: http_settings.HTTPSettings,
        debug: bool = False,
        token: typing.Optional[str],
        token_type: str = "Bot",
        url: str,
        version: int,
    ) -> None:
        super().__init__(
            allow_redirects=config.allow_redirects,
            connector=config.tcp_connector_factory() if config.tcp_connector_factory else None,
            debug=debug,
            logger=class_helpers.get_logger(self),
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

    async def _request(
        self,
        compiled_route: routes.CompiledRoute,
        *,
        headers: typing.Union[unset.Unset, more_typing.Headers] = unset.UNSET,
        query: typing.Union[unset.Unset, typing.Mapping[str, str]] = unset.UNSET,
        body: typing.Union[unset.Unset, aiohttp.FormData, more_typing.JSONType] = unset.UNSET,
        reason: typing.Union[unset.Unset, str] = unset.UNSET,
        no_auth: bool = False,
    ) -> typing.Optional[more_typing.JSONObject, more_typing.JSONArray, bytes, str]:
        # Make a ratelimit-protected HTTP request to a JSON endpoint and expect some form
        # of JSON response. If an error occurs, the response body is returned in the
        # raised exception as a bytes object. This is done since the differences between
        # the V6 and V7 API error messages are not documented properly, and there are
        # edge cases such as Cloudflare issues where we may receive arbitrary data in
        # the response instead of a JSON object.

        if not self.buckets.is_started:
            self.buckets.start()

        headers = {} if unset.is_unset(headers) else headers

        headers["x-ratelimit-precision"] = "millisecond"
        headers["accept"] = self._APPLICATION_JSON

        if self._token is not None and not no_auth:
            headers["authorization"] = self._token

        if unset.is_unset(body):
            body = None

        if not unset.is_unset(reason):
            headers["x-audit-log-reason"] = reason

        if unset.is_unset(query):
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
        headers: more_typing.Headers,
        body: typing.Optional[typing.Union[aiohttp.FormData, more_typing.JSONType]],
        query: typing.Optional[typing.Dict[str, str]],
    ) -> typing.Optional[more_typing.JSONObject, more_typing.JSONArray, bytes, str]:
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
        reset = float(resp_headers.get("x-ratelimit-reset", "0"))
        reset_date = datetime.datetime.fromtimestamp(reset, tz=datetime.timezone.utc)
        now_date = conversions.rfc7231_datetime_string_to_datetime(resp_headers["date"])
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
                        "you are being rate-limited on bucket %s for _route %s - trying again after %ss",
                        bucket,
                        compiled_route,
                        reset,
                    )

                raise self._RateLimited()

            # We might find out Cloudflare causes this scenario to occur.
            # I hope we don't though.
            raise errors.HTTPError(
                str(response.real_url),
                f"We were rate limited but did not understand the response. Perhaps Cloudflare did this? {body!r}",
            )

    @staticmethod
    def _generate_allowed_mentions(
        mentions_everyone: bool,
        user_mentions: typing.Union[typing.Collection[typing.Union[bases.Snowflake, int, str, users.User]], bool],
        role_mentions: typing.Union[typing.Collection[typing.Union[bases.Snowflake, int, str, guilds.Role]], bool],
    ):
        parsed_mentions = []
        allowed_mentions = {}

        if mentions_everyone is True:
            parsed_mentions.append("everyone")
        if user_mentions is True:
            parsed_mentions.append("users")

        # This covers both `False` and an array of IDs/objs by using `user_mentions or EMPTY_SEQUENCE`, where a
        # resultant empty list will mean that all user mentions are blacklisted.
        else:
            allowed_mentions["users"] = list(
                # dict.fromkeys is used to remove duplicate entries that would cause discord to return an error.
                dict.fromkeys(
                    str(user.id if isinstance(user, bases.Unique) else int(user))
                    for user in user_mentions or more_collections.EMPTY_SEQUENCE
                )
            )
            if len(allowed_mentions["users"]) > 100:
                raise ValueError("Only up to 100 users can be provided.")
        if role_mentions is True:
            parsed_mentions.append("roles")

        # This covers both `False` and an array of IDs/objs by using `user_mentions or EMPTY_SEQUENCE`, where a
        # resultant empty list will mean that all role mentions are blacklisted.
        else:
            allowed_mentions["roles"] = list(
                # dict.fromkeys is used to remove duplicate entries that would cause discord to return an error.
                dict.fromkeys(
                    str(role.id if isinstance(role, bases.Unique) else int(role))
                    for role in role_mentions or more_collections.EMPTY_SEQUENCE
                )
            )
            if len(allowed_mentions["roles"]) > 100:
                raise ValueError("Only up to 100 roles can be provided.")
        allowed_mentions["parse"] = parsed_mentions

        # As a note, discord will also treat an empty `allowed_mentions` object as if it wasn't passed at all, so we
        # want to use empty lists for blacklisting elements rather than just not including blacklisted elements.
        return allowed_mentions

    def _build_message_creation_form(
        self, payload: typing.Dict[str, typing.Any], attachments: typing.Sequence[files.BaseStream],
    ) -> aiohttp.FormData:
        form = aiohttp.FormData()
        form.add_field("payload_json", json.dumps(payload), content_type=self._APPLICATION_JSON)
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
        self, channel: typing.Union[channels.PartialChannel, bases.UniqueObjectT], /,
    ) -> channels.PartialChannel:
        """Fetch a channel.

        Parameters
        ----------
        channel : hikari.models.channels.PartialChannel | hikari.models.bases.Snowflake | int | str
            The channel object to fetch. This can be an existing reference to a
            channel object (if you want a more up-to-date representation, or it
            can be a snowflake representation of the channel ID.

        Returns
        -------
        hikari.models.channels.PartialChannel
            The resultant channel.

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
        route = routes.GET_CHANNEL.compile(channel=conversions.value_to_snowflake(channel))
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
    ) -> _GuildChannelT:
        """Edit a guild channel, given an existing guild channel object."""

    async def edit_channel(
        self,
        channel: typing.Union[channels.PartialChannel, bases.UniqueObjectT],
        /,
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
        """Edit a channel.

        Parameters
        ----------
        channel
        name
        position
        topic
        nsfw
        bitrate
        user_limit
        rate_limit_per_user
        permission_overwrites
        parent_category
        reason

        Returns
        -------

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
        route = routes.PATCH_CHANNEL.compile(channel=conversions.value_to_snowflake(channel))
        payload = {}
        conversions.put_if_specified(payload, "name", name)
        conversions.put_if_specified(payload, "position", position)
        conversions.put_if_specified(payload, "topic", topic)
        conversions.put_if_specified(payload, "nsfw", nsfw)
        conversions.put_if_specified(payload, "bitrate", bitrate)
        conversions.put_if_specified(payload, "user_limit", user_limit)
        conversions.put_if_specified(payload, "rate_limit_per_user", rate_limit_per_user)
        conversions.put_if_specified(payload, "parent_id", parent_category, conversions.value_to_snowflake)

        if not unset.is_unset(permission_overwrites):
            payload["permission_overwrites"] = [
                self._app.entity_factory.serialize_permission_overwrite(p) for p in permission_overwrites
            ]

        response = await self._request(route, body=payload, reason=reason)
        return self._app.entity_factory.deserialize_channel(response)

    async def delete_channel(self, channel: typing.Union[channels.PartialChannel, bases.UniqueObjectT], /) -> None:
        """Delete a channel in a guild, or close a DM.

        Parameters
        ----------
        channel

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

        """
        route = routes.DELETE_CHANNEL.compile(channel=conversions.value_to_snowflake(channel))
        await self._request(route)

    @typing.overload
    async def edit_permission_overwrites(
        self,
        channel: typing.Union[channels.GuildChannel, bases.UniqueObjectT],
        target: typing.Union[channels.PermissionOverwrite, users.User, guilds.Role],
        *,
        allow: typing.Union[unset.Unset, permissions_.Permission] = unset.UNSET,
        deny: typing.Union[unset.Unset, permissions_.Permission] = unset.UNSET,
        reason: typing.Union[unset.Unset, str] = unset.UNSET,
    ) -> None:
        """Edit permissions for a target entity."""

    @typing.overload
    async def edit_permission_overwrites(
        self,
        channel: typing.Union[channels.GuildChannel, bases.UniqueObjectT],
        target: typing.Union[int, str, bases.Snowflake],
        target_type: typing.Union[channels.PermissionOverwriteType, str],
        *,
        allow: typing.Union[unset.Unset, permissions_.Permission] = unset.UNSET,
        deny: typing.Union[unset.Unset, permissions_.Permission] = unset.UNSET,
        reason: typing.Union[unset.Unset, str] = unset.UNSET,
    ) -> None:
        """Edit permissions for a given entity ID and type."""

    async def edit_permission_overwrites(
        self,
        channel: typing.Union[channels.GuildChannel, bases.UniqueObjectT],
        target: typing.Union[bases.UniqueObjectT, users.User, guilds.Role, channels.PermissionOverwrite],
        target_type: typing.Union[unset.Unset, channels.PermissionOverwriteType, str] = unset.UNSET,
        *,
        allow: typing.Union[unset.Unset, permissions_.Permission] = unset.UNSET,
        deny: typing.Union[unset.Unset, permissions_.Permission] = unset.UNSET,
        reason: typing.Union[unset.Unset, str] = unset.UNSET,
    ) -> None:
        """Edit permissions for a specific entity in the given guild channel.

        Parameters
        ----------
        channel
        target
        target_type
        allow
        deny
        reason

        Raises
        ------
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

        if unset.is_unset(target_type):
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

        payload = {"type": target_type}
        conversions.put_if_specified(payload, "allow", allow)
        conversions.put_if_specified(payload, "deny", deny)
        route = routes.PATCH_CHANNEL_PERMISSIONS.compile(
            channel=conversions.value_to_snowflake(channel), overwrite=conversions.value_to_snowflake(target),
        )

        await self._request(route, body=payload, reason=reason)

    async def delete_permission_overwrite(
        self,
        channel: typing.Union[channels.GuildChannel, bases.UniqueObjectT],
        target: typing.Union[channels.PermissionOverwrite, guilds.Role, users.User, bases.UniqueObjectT],
    ) -> None:
        """Delete a custom permission for an entity in a given guild channel.

        Parameters
        ----------
        channel
        target

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
        route = routes.DELETE_CHANNEL_PERMISSIONS.compile(
            channel=conversions.value_to_snowflake(channel), overwrite=conversions.value_to_snowflake(target),
        )
        await self._request(route)

    async def fetch_channel_invites(
        self, channel: typing.Union[channels.GuildChannel, bases.UniqueObjectT], /
    ) -> typing.Sequence[invites.InviteWithMetadata]:
        """Fetch all invites pointing to the given guild channel.

        Parameters
        ----------
        channel

        Returns
        -------

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
        route = routes.GET_CHANNEL_INVITES.compile(channel=conversions.value_to_snowflake(channel))
        response = await self._request(route)
        return conversions.json_to_collection(response, self._app.entity_factory.deserialize_invite_with_metadata)

    async def create_invite(
        self,
        channel: typing.Union[channels.GuildChannel, bases.UniqueObjectT],
        /,
        *,
        max_age: typing.Union[unset.Unset, int, float, datetime.timedelta] = unset.UNSET,
        max_uses: typing.Union[unset.Unset, int] = unset.UNSET,
        temporary: typing.Union[unset.Unset, bool] = unset.UNSET,
        unique: typing.Union[unset.Unset, bool] = unset.UNSET,
        target_user: typing.Union[unset.Unset, users.User, bases.UniqueObjectT] = unset.UNSET,
        target_user_type: typing.Union[unset.Unset, invites.TargetUserType] = unset.UNSET,
        reason: typing.Union[unset.Unset, str] = unset.UNSET,
    ) -> invites.InviteWithMetadata:
        """Create an invite to the given guild channel.

        Parameters
        ----------
        channel
        max_age
        max_uses
        temporary
        unique
        target_user
        target_user_type
        reason

        Returns
        -------

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
        payload = {}
        conversions.put_if_specified(payload, "max_age", max_age, conversions.timespan_to_int)
        conversions.put_if_specified(payload, "max_uses", max_uses)
        conversions.put_if_specified(payload, "temporary", temporary)
        conversions.put_if_specified(payload, "unique", unique),
        conversions.put_if_specified(payload, "target_user", target_user, conversions.value_to_snowflake)
        conversions.put_if_specified(payload, "target_user_type", target_user_type)
        route = routes.POST_CHANNEL_INVITES.compile(channel=conversions.value_to_snowflake(channel))
        response = await self._request(route, body=payload, reason=reason)
        return self._app.entity_factory.deserialize_invite_with_metadata(response)

    def trigger_typing(
        self, channel: typing.Union[channels.TextChannel, bases.UniqueObjectT], /
    ) -> rest_utils.TypingIndicator:
        """Trigger typing in a text channel.

        Parameters
        ----------
        channel

        Returns
        -------

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
        self, channel: typing.Union[channels.TextChannel, bases.UniqueObjectT], /
    ) -> typing.Sequence[messages_.Message]:
        """Fetch the pinned messages in this text channel.

        Parameters
        ----------
        channel

        Returns
        -------

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
        route = routes.GET_CHANNEL_PINS.compile(channel=conversions.value_to_snowflake(channel))
        response = await self._request(route)
        return conversions.json_to_collection(response, self._app.entity_factory.deserialize_message)

    async def pin_message(
        self,
        channel: typing.Union[channels.TextChannel, bases.UniqueObjectT],
        message: typing.Union[messages_.Message, bases.UniqueObjectT],
    ) -> None:
        """Pin an existing message in the given text channel.

        Parameters
        ----------
        channel
        message

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
        route = routes.PUT_CHANNEL_PINS.compile(
            channel=conversions.value_to_snowflake(channel), message=conversions.value_to_snowflake(message),
        )
        await self._request(route)

    async def unpin_message(
        self,
        channel: typing.Union[channels.TextChannel, bases.UniqueObjectT],
        message: typing.Union[messages_.Message, bases.UniqueObjectT],
    ) -> None:
        """

        Parameters
        ----------
        channel
        message

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

        !!! note
            The exceptions on this endpoint will only be raised once the result
            is awaited or interacted with. Invoking this function itself will
            not raise any of the above types.
        """
        route = routes.DELETE_CHANNEL_PIN.compile(
            channel=conversions.value_to_snowflake(channel), message=conversions.value_to_snowflake(message),
        )
        await self._request(route)

    @typing.overload
    def fetch_messages(
        self, channel: typing.Union[channels.TextChannel, bases.UniqueObjectT], /
    ) -> iterators.LazyIterator[messages_.Message]:
        """Fetch messages, newest first, sent in the given channel."""

    @typing.overload
    def fetch_messages(
        self,
        channel: typing.Union[channels.TextChannel, bases.UniqueObjectT],
        /,
        *,
        before: typing.Union[datetime.datetime, bases.UniqueObjectT],
    ) -> iterators.LazyIterator[messages_.Message]:
        """Fetch messages, newest first, sent before a timestamp in the channel."""

    @typing.overload
    def fetch_messages(
        self,
        channel: typing.Union[channels.TextChannel, bases.UniqueObjectT],
        /,
        *,
        around: typing.Union[datetime.datetime, bases.UniqueObjectT],
    ) -> iterators.LazyIterator[messages_.Message]:
        """Fetch messages sent around a given time in the channel."""

    @typing.overload
    def fetch_messages(
        self,
        channel: typing.Union[channels.TextChannel, bases.UniqueObjectT],
        /,
        *,
        after: typing.Union[datetime.datetime, bases.UniqueObjectT],
    ) -> iterators.LazyIterator[messages_.Message]:
        """Fetch messages, oldest first, sent after a timestamp in the channel."""

    def fetch_messages(
        self,
        channel: typing.Union[channels.TextChannel, bases.UniqueObjectT],
        /,
        *,
        before: typing.Union[unset.Unset, datetime.datetime, bases.UniqueObjectT] = unset.UNSET,
        after: typing.Union[unset.Unset, datetime.datetime, bases.UniqueObjectT] = unset.UNSET,
        around: typing.Union[unset.Unset, datetime.datetime, bases.UniqueObjectT] = unset.UNSET,
    ) -> iterators.LazyIterator[messages_.Message]:
        """Browse the message history for a given text channel.

        Parameters
        ----------
        channel
        before
        after
        around

        Returns
        -------

        Raises
        ------
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack permissions to read message history in the given
            channel.
        hikari.errors.NotFound
            If the channel is not found.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.
        TypeError
            If you specify more than one of `before`, `after`, `about`.

        !!! note
            The exceptions on this endpoint (other than `TypeError`) will only
            be raised once the result is awaited or interacted with. Invoking
            this function itself will not raise anything (other than
            `TypeError`).
        """
        if unset.count_unset_objects(before, after, around) < 2:
            raise TypeError(f"Expected no kwargs, or maximum of one of 'before', 'after', 'around'")
        elif not unset.is_unset(before):
            direction, timestamp = "before", before
        elif not unset.is_unset(after):
            direction, timestamp = "after", after
        elif not unset.is_unset(around):
            direction, timestamp = "around", around
        else:
            direction, timestamp = "before", bases.Snowflake.max()

        if isinstance(timestamp, datetime.datetime):
            timestamp = bases.Snowflake.from_datetime(timestamp)

        return iterators.MessageIterator(
            self._app,
            self._request,
            conversions.value_to_snowflake(channel),
            direction,
            conversions.value_to_snowflake(timestamp),
        )

    async def fetch_message(
        self,
        channel: typing.Union[channels.TextChannel, bases.UniqueObjectT],
        message: typing.Union[messages_.Message, bases.UniqueObjectT],
    ) -> messages_.Message:
        """Fetch a specific message in the given text channel.

        Parameters
        ----------
        channel
        message

        Returns
        -------

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
        route = routes.GET_CHANNEL_MESSAGE.compile(
            channel=conversions.value_to_snowflake(channel), message=conversions.value_to_snowflake(message),
        )
        response = await self._request(route)
        return self._app.entity_factory.deserialize_message(response)

    async def create_message(
        self,
        channel: typing.Union[channels.TextChannel, bases.UniqueObjectT],
        text: typing.Union[unset.Unset, typing.Any] = unset.UNSET,
        *,
        embed: typing.Union[unset.Unset, embeds_.Embed] = unset.UNSET,
        attachments: typing.Union[unset.Unset, typing.Sequence[files.BaseStream]] = unset.UNSET,
        tts: typing.Union[unset.Unset, bool] = unset.UNSET,
        nonce: typing.Union[unset.Unset, str] = unset.UNSET,
        mentions_everyone: bool = False,
        user_mentions: typing.Union[typing.Collection[typing.Union[users.User, bases.UniqueObjectT]], bool] = True,
        role_mentions: typing.Union[typing.Collection[typing.Union[bases.UniqueObjectT, guilds.Role]], bool] = True,
    ) -> messages_.Message:
        """Create a message in the given channel.

        Parameters
        ----------
        channel
        text
        embed
        attachments
        tts
        nonce
        mentions_everyone
        user_mentions
        role_mentions

        Returns
        -------

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

        !!! warn
            You are expected to make a connection to the gateway and identify
            once before being able to use this endpoint for a bot.
        """

        route = routes.POST_CHANNEL_MESSAGES.compile(channel=conversions.value_to_snowflake(channel))

        payload = {"allowed_mentions": self._generate_allowed_mentions(mentions_everyone, user_mentions, role_mentions)}
        conversions.put_if_specified(payload, "content", text, str)
        conversions.put_if_specified(payload, "embed", embed, self._app.entity_factory.serialize_embed)
        conversions.put_if_specified(payload, "nonce", nonce)
        conversions.put_if_specified(payload, "tts", tts)

        attachments = [] if unset.is_unset(attachments) else [a for a in attachments]

        if not unset.is_unset(embed):
            attachments.extend(embed.assets_to_upload)

        response = await self._request(
            route, body=self._build_message_creation_form(payload, attachments) if attachments else payload
        )

        return self._app.entity_factory.deserialize_message(response)

    async def edit_message(
        self,
        channel: typing.Union[channels.TextChannel, bases.UniqueObjectT],
        message: typing.Union[messages_.Message, bases.UniqueObjectT],
        text: typing.Union[unset.Unset, typing.Any] = unset.UNSET,
        *,
        embed: typing.Union[unset.Unset, embeds_.Embed] = unset.UNSET,
        mentions_everyone: bool = False,
        user_mentions: typing.Union[typing.Collection[typing.Union[users.User, bases.UniqueObjectT]], bool] = True,
        role_mentions: typing.Union[typing.Collection[typing.Union[bases.UniqueObjectT, guilds.Role]], bool] = True,
        flags: typing.Union[unset.Unset, messages_.MessageFlag] = unset.UNSET,
    ) -> messages_.Message:
        """Edit an existing message in a given channel.

        Parameters
        ----------

        Returns
        -------

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

        route = routes.PATCH_CHANNEL_MESSAGE.compile(
            channel=conversions.value_to_snowflake(channel), message=conversions.value_to_snowflake(message),
        )
        payload = {}
        conversions.put_if_specified(payload, "content", text, str)
        conversions.put_if_specified(payload, "embed", embed, self._app.entity_factory.serialize_embed)
        conversions.put_if_specified(payload, "flags", flags)
        payload["allowed_mentions"] = self._generate_allowed_mentions(mentions_everyone, user_mentions, role_mentions)
        response = await self._request(route, body=payload)
        return self._app.entity_factory.deserialize_message(response)

    async def delete_message(
        self,
        channel: typing.Union[channels.TextChannel, bases.UniqueObjectT],
        message: typing.Union[messages_.Message, bases.UniqueObjectT],
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
        route = routes.DELETE_CHANNEL_MESSAGE.compile(
            channel=conversions.value_to_snowflake(channel), message=conversions.value_to_snowflake(message),
        )
        await self._request(route)

    async def delete_messages(
        self,
        channel: typing.Union[channels.GuildTextChannel, bases.UniqueObjectT],
        *messages: typing.Union[messages_.Message, bases.UniqueObjectT],
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
            route = routes.POST_DELETE_CHANNEL_MESSAGES_BULK.compile(channel=conversions.value_to_snowflake(channel))
            payload = {"messages": [conversions.value_to_snowflake(m) for m in messages]}
            await self._request(route, body=payload)
        else:
            raise TypeError("Must delete a minimum of 2 messages and a maximum of 100")

    async def add_reaction(
        self,
        channel: typing.Union[channels.TextChannel, bases.UniqueObjectT],
        message: typing.Union[messages_.Message, bases.UniqueObjectT],
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
            channel=conversions.value_to_snowflake(channel),
            message=conversions.value_to_snowflake(message),
        )
        await self._request(route)

    async def delete_my_reaction(
        self,
        channel: typing.Union[channels.TextChannel, bases.UniqueObjectT],
        message: typing.Union[messages_.Message, bases.UniqueObjectT],
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
            channel=conversions.value_to_snowflake(channel),
            message=conversions.value_to_snowflake(message),
        )
        await self._request(route)

    async def delete_all_reactions_for_emoji(
        self,
        channel: typing.Union[channels.TextChannel, bases.UniqueObjectT],
        message: typing.Union[messages_.Message, bases.UniqueObjectT],
        emoji: typing.Union[str, emojis.UnicodeEmoji, emojis.KnownCustomEmoji],
    ) -> None:
        route = routes.DELETE_REACTION_EMOJI.compile(
            emoji=emoji.url_name if isinstance(emoji, emojis.KnownCustomEmoji) else str(emoji),
            channel=conversions.value_to_snowflake(channel),
            message=conversions.value_to_snowflake(message),
        )
        await self._request(route)

    async def delete_reaction(
        self,
        channel: typing.Union[channels.TextChannel, bases.UniqueObjectT],
        message: typing.Union[messages_.Message, bases.UniqueObjectT],
        emoji: typing.Union[str, emojis.UnicodeEmoji, emojis.KnownCustomEmoji],
        user: typing.Union[users.User, bases.UniqueObjectT],
    ) -> None:
        route = routes.DELETE_REACTION_USER.compile(
            emoji=emoji.url_name if isinstance(emoji, emojis.KnownCustomEmoji) else str(emoji),
            channel=conversions.value_to_snowflake(channel),
            message=conversions.value_to_snowflake(message),
            user=conversions.value_to_snowflake(user),
        )
        await self._request(route)

    async def delete_all_reactions(
        self,
        channel: typing.Union[channels.TextChannel, bases.UniqueObjectT],
        message: typing.Union[messages_.Message, bases.UniqueObjectT],
    ) -> None:
        route = routes.DELETE_ALL_REACTIONS.compile(
            channel=conversions.value_to_snowflake(channel), message=conversions.value_to_snowflake(message),
        )

        await self._request(route)

    def fetch_reactions_for_emoji(
        self,
        channel: typing.Union[channels.TextChannel, bases.UniqueObjectT],
        message: typing.Union[messages_.Message, bases.UniqueObjectT],
        emoji: typing.Union[str, emojis.UnicodeEmoji, emojis.KnownCustomEmoji],
    ) -> iterators.LazyIterator[users.User]:
        return iterators.ReactorIterator(
            app=self._app,
            request_call=self._request,
            channel_id=conversions.value_to_snowflake(channel),
            message_id=conversions.value_to_snowflake(message),
            emoji=emoji.url_name if isinstance(emoji, emojis.KnownCustomEmoji) else str(emoji),
        )

    async def create_webhook(
        self,
        channel: typing.Union[channels.TextChannel, bases.UniqueObjectT],
        name: str,
        *,
        avatar: typing.Union[unset.Unset, files.BaseStream] = unset.UNSET,
        reason: typing.Union[unset.Unset, str] = unset.UNSET,
    ) -> webhooks.Webhook:
        route = routes.POST_WEBHOOK.compile(channel=conversions.value_to_snowflake(channel))
        payload = {"name": name}
        if not unset.is_unset(avatar):
            payload["avatar"] = await avatar.fetch_data_uri()
        response = await self._request(route, body=payload, reason=reason)
        return self._app.entity_factory.deserialize_webhook(response)

    async def fetch_webhook(
        self,
        webhook: typing.Union[webhooks.Webhook, bases.UniqueObjectT],
        /,
        *,
        token: typing.Union[unset.Unset, str] = unset.UNSET,
    ) -> webhooks.Webhook:
        if unset.is_unset(token):
            route = routes.GET_WEBHOOK.compile(webhook=conversions.value_to_snowflake(webhook))
        else:
            route = routes.GET_WEBHOOK_WITH_TOKEN.compile(webhook=conversions.value_to_snowflake(webhook), token=token)
        response = await self._request(route)
        return self._app.entity_factory.deserialize_webhook(response)

    async def fetch_channel_webhooks(
        self, channel: typing.Union[channels.TextChannel, bases.UniqueObjectT], /
    ) -> typing.Sequence[webhooks.Webhook]:
        route = routes.GET_CHANNEL_WEBHOOKS.compile(channel=conversions.value_to_snowflake(channel))
        response = await self._request(route)
        return conversions.json_to_collection(response, self._app.entity_factory.deserialize_webhook)

    async def fetch_guild_webhooks(
        self, guild: typing.Union[guilds.Guild, bases.UniqueObjectT], /
    ) -> typing.Sequence[webhooks.Webhook]:
        route = routes.GET_GUILD_WEBHOOKS.compile(channel=conversions.value_to_snowflake(guild))
        response = await self._request(route)
        return conversions.json_to_collection(response, self._app.entity_factory.deserialize_webhook)

    async def edit_webhook(
        self,
        webhook: typing.Union[webhooks.Webhook, bases.UniqueObjectT],
        /,
        *,
        token: typing.Union[unset.Unset, str] = unset.UNSET,
        name: typing.Union[unset.Unset, str] = unset.UNSET,
        avatar: typing.Union[unset.Unset, files.BaseStream] = unset.UNSET,
        channel: typing.Union[unset.Unset, channels.TextChannel, bases.UniqueObjectT] = unset.UNSET,
        reason: typing.Union[unset.Unset, str] = unset.UNSET,
    ) -> webhooks.Webhook:
        if unset.is_unset(token):
            route = routes.PATCH_WEBHOOK.compile(webhook=conversions.value_to_snowflake(webhook))
        else:
            route = routes.PATCH_WEBHOOK_WITH_TOKEN.compile(
                webhook=conversions.value_to_snowflake(webhook), token=token
            )

        payload = {}
        conversions.put_if_specified(payload, "name", name)
        conversions.put_if_specified(payload, "channel", channel, conversions.value_to_snowflake)
        if not unset.is_unset(avatar):
            payload["avatar"] = await avatar.fetch_data_uri()

        response = await self._request(route, body=payload, reason=reason)
        return self._app.entity_factory.deserialize_webhook(response)

    async def delete_webhook(
        self,
        webhook: typing.Union[webhooks.Webhook, bases.UniqueObjectT],
        /,
        *,
        token: typing.Union[unset.Unset, str] = unset.UNSET,
    ) -> None:
        if unset.is_unset(token):
            route = routes.DELETE_WEBHOOK.compile(webhook=conversions.value_to_snowflake(webhook))
        else:
            route = routes.DELETE_WEBHOOK_WITH_TOKEN.compile(
                webhook=conversions.value_to_snowflake(webhook), token=token
            )
        await self._request(route)

    async def execute_embed(
        self,
        webhook: typing.Union[webhooks.Webhook, bases.UniqueObjectT],
        text: typing.Union[unset.Unset, typing.Any] = unset.UNSET,
        *,
        token: typing.Union[unset.Unset, str] = unset.UNSET,
        username: typing.Union[unset.Unset, str] = unset.UNSET,
        avatar_url: typing.Union[unset.Unset, str] = unset.UNSET,
        embeds: typing.Union[unset.Unset, typing.Sequence[embeds_.Embed]] = unset.UNSET,
        attachments: typing.Union[unset.Unset, typing.Sequence[files.BaseStream]] = unset.UNSET,
        tts: typing.Union[unset.Unset, bool] = unset.UNSET,
        wait: typing.Union[unset.Unset, bool] = unset.UNSET,
        mentions_everyone: bool = False,
        user_mentions: typing.Union[typing.Collection[typing.Union[users.User, bases.UniqueObjectT]], bool] = True,
        role_mentions: typing.Union[typing.Collection[typing.Union[bases.UniqueObjectT, guilds.Role]], bool] = True,
    ) -> messages_.Message:
        if unset.is_unset(token):
            route = routes.POST_WEBHOOK.compile(webhook=conversions.value_to_snowflake(webhook))
            no_auth = False
        else:
            route = routes.POST_WEBHOOK_WITH_TOKEN.compile(webhook=conversions.value_to_snowflake(webhook), token=token)
            no_auth = True

        attachments = [] if unset.is_unset(attachments) else [a for a in attachments]
        serialized_embeds = []

        if not unset.is_unset(embeds):
            for embed in embeds:
                attachments.extend(embed.assets_to_upload)
                serialized_embeds.append(self._app.entity_factory.serialize_embed(embed))

        payload = {"mentions": self._generate_allowed_mentions(mentions_everyone, user_mentions, role_mentions)}
        conversions.put_if_specified(payload, "content", text, str)
        conversions.put_if_specified(payload, "embeds", serialized_embeds)
        conversions.put_if_specified(payload, "username", username)
        conversions.put_if_specified(payload, "avatar_url", avatar_url)
        conversions.put_if_specified(payload, "tts", tts)
        conversions.put_if_specified(payload, "wait", wait)

        response = await self._request(
            route,
            body=self._build_message_creation_form(payload, attachments) if attachments else payload,
            no_auth=no_auth,
        )

        return self._app.entity_factory.deserialize_message(response)

    async def fetch_gateway_url(self) -> str:
        route = routes.GET_GATEWAY.compile()
        # This doesn't need authorization.
        response = await self._request(route, no_auth=True)
        return response["url"]

    async def fetch_recommended_gateway_settings(self) -> gateway.GatewayBot:
        route = routes.GET_GATEWAY_BOT.compile()
        response = await self._request(route)
        return self._app.entity_factory.deserialize_gateway_bot(response)

    async def fetch_invite(self, invite: typing.Union[invites.Invite, str]) -> invites.Invite:
        route = routes.GET_INVITE.compile(invite_code=invite if isinstance(invite, str) else invite.code)
        payload = {"with_counts": True}
        response = await self._request(route, body=payload)
        return self._app.entity_factory.deserialize_invite(response)

    async def delete_invite(self, invite: typing.Union[invites.Invite, str]) -> None:
        route = routes.DELETE_INVITE.compile(invite_code=invite if isinstance(invite, str) else invite.code)
        await self._request(route)

    async def fetch_my_user(self) -> users.MyUser:
        route = routes.GET_MY_USER.compile()
        response = await self._request(route)
        return self._app.entity_factory.deserialize_my_user(response)

    async def edit_my_user(
        self,
        *,
        username: typing.Union[unset.Unset, str] = unset.UNSET,
        avatar: typing.Union[unset.Unset, files.BaseStream] = unset.UNSET,
    ) -> users.MyUser:
        route = routes.PATCH_MY_USER.compile()
        payload = {}
        conversions.put_if_specified(payload, "username", username)
        if not unset.is_unset(username):
            payload["avatar"] = await avatar.fetch_data_uri()
        response = await self._request(route, body=payload)
        return self._app.entity_factory.deserialize_my_user(response)

    async def fetch_my_connections(self) -> typing.Sequence[applications.OwnConnection]:
        route = routes.GET_MY_CONNECTIONS.compile()
        response = await self._request(route)
        return [self._app.entity_factory.deserialize_own_connection(c) for c in response]

    def fetch_my_guilds(
        self,
        *,
        newest_first: bool = False,
        start_at: typing.Union[unset.Unset, guilds.PartialGuild, bases.UniqueObjectT, datetime.datetime] = unset.UNSET,
    ) -> iterators.LazyIterator[applications.OwnGuild]:
        if unset.is_unset(start_at):
            start_at = bases.Snowflake.max() if newest_first else bases.Snowflake.min()
        elif isinstance(start_at, datetime.datetime):
            start_at = bases.Snowflake.from_datetime(start_at)

        return iterators.OwnGuildIterator(
            self._app, self._request, newest_first, conversions.value_to_snowflake(start_at)
        )

    async def leave_guild(self, guild: typing.Union[guilds.Guild, bases.UniqueObjectT], /) -> None:
        route = routes.DELETE_MY_GUILD.compile(guild=conversions.value_to_snowflake(guild))
        await self._request(route)

    async def create_dm_channel(self, user: typing.Union[users.User, bases.UniqueObjectT], /) -> channels.DMChannel:
        route = routes.POST_MY_CHANNELS.compile()
        response = await self._request(route, body={"recipient_id": conversions.value_to_snowflake(user)})
        return self._app.entity_factory.deserialize_dm_channel(response)

    async def fetch_application(self) -> applications.Application:
        route = routes.GET_MY_APPLICATION.compile()
        response = await self._request(route)
        return self._app.entity_factory.deserialize_application(response)

    async def add_user_to_guild(
        self,
        access_token: str,
        guild: typing.Union[guilds.Guild, bases.UniqueObjectT],
        user: typing.Union[users.User, bases.UniqueObjectT],
        *,
        nick: typing.Union[unset.Unset, str] = unset.UNSET,
        roles: typing.Union[
            unset.Unset, typing.Collection[typing.Union[guilds.Role, bases.UniqueObjectT]]
        ] = unset.UNSET,
        mute: typing.Union[unset.Unset, bool] = unset.UNSET,
        deaf: typing.Union[unset.Unset, bool] = unset.UNSET,
    ) -> typing.Optional[guilds.GuildMember]:
        route = routes.PUT_GUILD_MEMBER.compile(
            guild=conversions.value_to_snowflake(guild), user=conversions.value_to_snowflake(user),
        )
        payload = {"access_token": access_token}
        conversions.put_if_specified(payload, "nick", nick)
        conversions.put_if_specified(payload, "mute", mute)
        conversions.put_if_specified(payload, "deaf", deaf)
        if not unset.is_unset(roles):
            payload["roles"] = [conversions.value_to_snowflake(r) for r in roles]

        if (response := await self._request(route, body=payload)) is not None:
            return self._app.entity_factory.deserialize_guild_member(response)
        else:
            # User already is in the guild.
            return None

    async def fetch_voice_regions(self) -> typing.Sequence[voices.VoiceRegion]:
        route = routes.GET_VOICE_REGIONS.compile()
        response = await self._request(route)
        return conversions.json_to_collection(response, self._app.entity_factory.deserialize_voice_region)

    async def fetch_user(self, user: typing.Union[users.User, bases.UniqueObjectT]) -> users.User:
        route = routes.GET_USER.compile(user=conversions.value_to_snowflake(user))
        response = await self._request(route)
        return self._app.entity_factory.deserialize_user(response)

    def fetch_audit_log(
        self,
        guild: typing.Union[guilds.Guild, bases.UniqueObjectT],
        /,
        *,
        before: typing.Union[unset.Unset, datetime.datetime, bases.UniqueObjectT] = unset.UNSET,
        user: typing.Union[unset.Unset, users.User, bases.UniqueObjectT] = unset.UNSET,
        event_type: typing.Union[unset.Unset, audit_logs.AuditLogEventType] = unset.UNSET,
    ) -> iterators.LazyIterator[audit_logs.AuditLog]:
        guild = conversions.value_to_snowflake(guild)
        user = unset.UNSET if unset.is_unset(user) else conversions.value_to_snowflake(user)
        event_type = unset.UNSET if unset.is_unset(event_type) else int(event_type)

        if unset.is_unset(before):
            before = bases.Snowflake.max()
        elif isinstance(before, datetime.datetime):
            before = bases.Snowflake.from_datetime(before)

        before = conversions.value_to_snowflake(before)

        return iterators.AuditLogIterator(self._app, self._request, guild, before, user, event_type,)

    async def fetch_emoji(
        self,
        guild: typing.Union[guilds.Guild, bases.UniqueObjectT],
        # This is an emoji ID, which is the URL-safe emoji name, not the snowflake alone.
        emoji: typing.Union[emojis.KnownCustomEmoji, str],
    ) -> emojis.KnownCustomEmoji:
        route = routes.GET_GUILD_EMOJI.compile(
            guild=conversions.value_to_snowflake(guild),
            emoji=emoji.url_name if isinstance(emoji, emojis.Emoji) else emoji,
        )
        response = await self._request(route)
        return self._app.entity_factory.deserialize_known_custom_emoji(response)

    async def fetch_guild_emojis(
        self, guild: typing.Union[guilds.Guild, bases.UniqueObjectT], /
    ) -> typing.Set[emojis.KnownCustomEmoji]:
        route = routes.GET_GUILD_EMOJIS.compile(guild=conversions.value_to_snowflake(guild))
        response = await self._request(route)
        return conversions.json_to_collection(response, self._app.entity_factory.deserialize_known_custom_emoji, set)

    async def create_emoji(
        self,
        guild: typing.Union[guilds.Guild, bases.UniqueObjectT],
        name: str,
        image: files.BaseStream,
        *,
        roles: typing.Union[
            unset.Unset, typing.Collection[typing.Union[guilds.Role, bases.UniqueObjectT]]
        ] = unset.UNSET,
        reason: typing.Union[unset.Unset, str] = unset.UNSET,
    ) -> emojis.KnownCustomEmoji:
        route = routes.POST_GUILD_EMOJIS.compile(guild=conversions.value_to_snowflake(guild))
        payload = {"name": name, "image": await image.fetch_data_uri()}
        conversions.put_if_specified(
            payload, "roles", roles, lambda seq: [conversions.value_to_snowflake(r) for r in seq]
        )
        response = await self._request(route, body=payload, reason=reason)
        return self._app.entity_factory.deserialize_known_custom_emoji(response)

    async def edit_emoji(
        self,
        guild: typing.Union[guilds.Guild, bases.UniqueObjectT],
        # This is an emoji ID, which is the URL-safe emoji name, not the snowflake alone.
        emoji: typing.Union[emojis.KnownCustomEmoji, str],
        *,
        name: typing.Union[unset.Unset, str] = unset.UNSET,
        roles: typing.Union[
            unset.Unset, typing.Collection[typing.Union[guilds.Role, bases.UniqueObjectT]]
        ] = unset.UNSET,
        reason: typing.Union[unset.Unset, str] = unset.UNSET,
    ) -> emojis.KnownCustomEmoji:
        route = routes.PATCH_GUILD_EMOJI.compile(
            guild=conversions.value_to_snowflake(guild),
            emoji=emoji.url_name if isinstance(emoji, emojis.Emoji) else emoji,
        )
        payload = {}
        conversions.put_if_specified(payload, "name", name)
        conversions.put_if_specified(
            payload, "roles", roles, lambda seq: [conversions.value_to_snowflake(r) for r in seq]
        )
        response = await self._request(route, body=payload, reason=reason)
        return self._app.entity_factory.deserialize_known_custom_emoji(response)

    async def delete_emoji(
        self,
        guild: typing.Union[guilds.Guild, bases.UniqueObjectT],
        # This is an emoji ID, which is the URL-safe emoji name, not the snowflake alone.
        emoji: typing.Union[emojis.KnownCustomEmoji, str],
        # Reason is not currently supported for some reason. See
    ) -> None:
        route = routes.DELETE_GUILD_EMOJI.compile(
            guild=conversions.value_to_snowflake(guild),
            emoji=emoji.url_name if isinstance(emoji, emojis.Emoji) else emoji,
        )
        await self._request(route)

    def create_guild(self, name: str, /) -> rest_utils.GuildBuilder:
        return rest_utils.GuildBuilder(app=self._app, name=name, request_call=self._request)

    async def fetch_guild(self, guild: typing.Union[guilds.Guild, bases.UniqueObjectT], /) -> guilds.Guild:
        route = routes.GET_GUILD.compile(guild=conversions.value_to_snowflake(guild))
        response = await self._request(route)
        return self._app.entity_factory.deserialize_guild(response)

    async def fetch_guild_preview(
        self, guild: typing.Union[guilds.PartialGuild, bases.UniqueObjectT], /
    ) -> guilds.GuildPreview:
        route = routes.GET_GUILD_PREVIEW.compile(guild=conversions.value_to_snowflake(guild))
        response = await self._request(route)
        return self._app.entity_factory.deserialize_guild_preview(response)

    async def edit_guild(
        self,
        guild: typing.Union[guilds.Guild, bases.UniqueObjectT],
        /,
        *,
        name: typing.Union[unset.Unset, str] = unset.UNSET,
        region: typing.Union[unset.Unset, voices.VoiceRegion, str] = unset.UNSET,
        verification_level: typing.Union[unset.Unset, guilds.GuildVerificationLevel] = unset.UNSET,
        default_message_notifications: typing.Union[unset.Unset, guilds.GuildMessageNotificationsLevel] = unset.UNSET,
        explicit_content_filter_level: typing.Union[unset.Unset, guilds.GuildExplicitContentFilterLevel] = unset.UNSET,
        afk_channel: typing.Union[unset.Unset, channels.GuildVoiceChannel, bases.UniqueObjectT] = unset.UNSET,
        afk_timeout: typing.Union[unset.Unset, more_typing.TimeSpanT] = unset.UNSET,
        icon: typing.Union[unset.Unset, files.BaseStream] = unset.UNSET,
        owner: typing.Union[unset.Unset, users.User, bases.UniqueObjectT] = unset.UNSET,
        splash: typing.Union[unset.Unset, files.BaseStream] = unset.UNSET,
        banner: typing.Union[unset.Unset, files.BaseStream] = unset.UNSET,
        system_channel: typing.Union[unset.Unset, channels.GuildTextChannel] = unset.UNSET,
        rules_channel: typing.Union[unset.Unset, channels.GuildTextChannel] = unset.UNSET,
        public_updates_channel: typing.Union[unset.Unset, channels.GuildTextChannel] = unset.UNSET,
        preferred_locale: typing.Union[unset.Unset, str] = unset.UNSET,
        reason: typing.Union[unset.Unset, str] = unset.UNSET,
    ) -> guilds.Guild:
        route = routes.PATCH_GUILD.compile(guild=conversions.value_to_snowflake(guild))
        payload = {}
        conversions.put_if_specified(payload, "name", name)
        conversions.put_if_specified(payload, "region", region, str)
        conversions.put_if_specified(payload, "verification", verification_level)
        conversions.put_if_specified(payload, "notifications", default_message_notifications)
        conversions.put_if_specified(payload, "explicit_content_filter", explicit_content_filter_level)
        conversions.put_if_specified(payload, "afk_channel_id", afk_channel, conversions.value_to_snowflake)
        conversions.put_if_specified(payload, "afk_timeout", afk_timeout, conversions.timespan_to_int)
        conversions.put_if_specified(payload, "owner_id", owner, conversions.value_to_snowflake)
        conversions.put_if_specified(payload, "system_channel_id", system_channel, conversions.value_to_snowflake)
        conversions.put_if_specified(payload, "rules_channel_id", rules_channel, conversions.value_to_snowflake)
        conversions.put_if_specified(
            payload, "public_updates_channel_id", public_updates_channel, conversions.value_to_snowflake
        )
        conversions.put_if_specified(payload, "preferred_locale", preferred_locale, str)

        if not unset.is_unset(icon):
            payload["icon"] = await icon.fetch_data_uri()

        if not unset.is_unset(splash):
            payload["splash"] = await splash.fetch_data_uri()

        if not unset.is_unset(banner):
            payload["banner"] = await banner.fetch_data_uri()

        response = await self._request(route, body=payload, reason=reason)
        return self._app.entity_factory.deserialize_guild(response)

    async def delete_guild(self, guild: typing.Union[guilds.Guild, bases.UniqueObjectT]) -> None:
        route = routes.DELETE_GUILD.compile(guild=conversions.value_to_snowflake(guild))
        await self._request(route)

    async def fetch_guild_channels(
        self, guild: typing.Union[guilds.Guild, bases.UniqueObjectT]
    ) -> typing.Sequence[channels.GuildChannel]:
        route = routes.GET_GUILD_CHANNELS.compile(guild=conversions.value_to_snowflake(guild))
        response = await self._request(route)
        channel_sequence = [self._app.entity_factory.deserialize_channel(c) for c in response]
        # Will always be guild channels unless Discord messes up severely on something!
        return typing.cast(typing.Sequence[channels.GuildChannel], channel_sequence)

    async def create_guild_text_channel(
        self,
        guild: typing.Union[guilds.Guild, bases.UniqueObjectT],
        name: str,
        *,
        position: typing.Union[int, unset.Unset] = unset.UNSET,
        topic: typing.Union[str, unset.Unset] = unset.UNSET,
        nsfw: typing.Union[bool, unset.Unset] = unset.UNSET,
        rate_limit_per_user: typing.Union[int, unset.Unset] = unset.UNSET,
        permission_overwrites: typing.Union[typing.Sequence[channels.PermissionOverwrite], unset.Unset] = unset.UNSET,
        category: typing.Union[channels.GuildCategory, bases.UniqueObjectT, unset.Unset] = unset.UNSET,
        reason: typing.Union[str, unset.Unset] = unset.UNSET,
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
        guild: typing.Union[guilds.Guild, bases.UniqueObjectT],
        name: str,
        *,
        position: typing.Union[int, unset.Unset] = unset.UNSET,
        topic: typing.Union[str, unset.Unset] = unset.UNSET,
        nsfw: typing.Union[bool, unset.Unset] = unset.UNSET,
        rate_limit_per_user: typing.Union[int, unset.Unset] = unset.UNSET,
        permission_overwrites: typing.Union[typing.Sequence[channels.PermissionOverwrite], unset.Unset] = unset.UNSET,
        category: typing.Union[channels.GuildCategory, bases.UniqueObjectT, unset.Unset] = unset.UNSET,
        reason: typing.Union[str, unset.Unset] = unset.UNSET,
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
        guild: typing.Union[guilds.Guild, bases.UniqueObjectT],
        name: str,
        *,
        position: typing.Union[int, unset.Unset] = unset.UNSET,
        nsfw: typing.Union[bool, unset.Unset] = unset.UNSET,
        user_limit: typing.Union[int, unset.Unset] = unset.UNSET,
        bitrate: typing.Union[int, unset.Unset] = unset.UNSET,
        permission_overwrites: typing.Union[typing.Sequence[channels.PermissionOverwrite], unset.Unset] = unset.UNSET,
        category: typing.Union[channels.GuildCategory, bases.UniqueObjectT, unset.Unset] = unset.UNSET,
        reason: typing.Union[str, unset.Unset] = unset.UNSET,
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
        guild: typing.Union[guilds.Guild, bases.UniqueObjectT],
        name: str,
        *,
        position: typing.Union[int, unset.Unset] = unset.UNSET,
        nsfw: typing.Union[bool, unset.Unset] = unset.UNSET,
        permission_overwrites: typing.Union[typing.Sequence[channels.PermissionOverwrite], unset.Unset] = unset.UNSET,
        reason: typing.Union[str, unset.Unset] = unset.UNSET,
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
        guild: typing.Union[guilds.Guild, bases.UniqueObjectT],
        name: str,
        type_: channels.ChannelType,
        *,
        position: typing.Union[int, unset.Unset] = unset.UNSET,
        topic: typing.Union[str, unset.Unset] = unset.UNSET,
        nsfw: typing.Union[bool, unset.Unset] = unset.UNSET,
        bitrate: typing.Union[int, unset.Unset] = unset.UNSET,
        user_limit: typing.Union[int, unset.Unset] = unset.UNSET,
        rate_limit_per_user: typing.Union[int, unset.Unset] = unset.UNSET,
        permission_overwrites: typing.Union[typing.Sequence[channels.PermissionOverwrite], unset.Unset] = unset.UNSET,
        category: typing.Union[channels.GuildCategory, bases.UniqueObjectT, unset.Unset] = unset.UNSET,
        reason: typing.Union[str, unset.Unset] = unset.UNSET,
    ) -> channels.GuildChannel:
        route = routes.POST_GUILD_CHANNELS.compile(guild=conversions.value_to_snowflake(guild))
        payload = {"type": type_, "name": name}
        conversions.put_if_specified(payload, "position", position)
        conversions.put_if_specified(payload, "topic", topic)
        conversions.put_if_specified(payload, "nsfw", nsfw)
        conversions.put_if_specified(payload, "bitrate", bitrate)
        conversions.put_if_specified(payload, "user_limit", user_limit)
        conversions.put_if_specified(payload, "rate_limit_per_user", rate_limit_per_user)
        conversions.put_if_specified(payload, "category", category, conversions.value_to_snowflake)

        if not unset.is_unset(permission_overwrites):
            payload["permission_overwrites"] = [
                self._app.entity_factory.serialize_permission_overwrite(o) for o in permission_overwrites
            ]

        response = await self._request(route, body=payload, reason=reason)
        channel = self._app.entity_factory.deserialize_channel(response)
        return typing.cast(channels.GuildChannel, channel)

    async def reposition_channels(
        self,
        guild: typing.Union[guilds.Guild, bases.UniqueObjectT],
        positions: typing.Mapping[int, typing.Union[channels.GuildChannel, bases.UniqueObjectT]],
    ) -> None:
        route = routes.POST_GUILD_CHANNELS.compile(guild=conversions.value_to_snowflake(guild))
        payload = [
            {"id": conversions.value_to_snowflake(channel), "position": pos} for pos, channel in positions.items()
        ]
        await self._request(route, body=payload)

    async def fetch_member(
        self,
        guild: typing.Union[guilds.Guild, bases.UniqueObjectT],
        user: typing.Union[users.User, bases.UniqueObjectT],
    ) -> guilds.GuildMember:
        route = routes.GET_GUILD_MEMBER.compile(
            guild=conversions.value_to_snowflake(guild), user=conversions.value_to_snowflake(user)
        )
        response = await self._request(route)
        return self._app.entity_factory.deserialize_guild_member(response)

    def fetch_members(
        self, guild: typing.Union[guilds.Guild, bases.UniqueObjectT],
    ) -> iterators.LazyIterator[guilds.GuildMember]:
        return iterators.MemberIterator(self._app, self._request, conversions.value_to_snowflake(guild))

    async def edit_member(
        self,
        guild: typing.Union[guilds.Guild, bases.UniqueObjectT],
        user: typing.Union[users.User, bases.UniqueObjectT],
        *,
        nick: typing.Union[unset.Unset, str] = unset.UNSET,
        roles: typing.Union[
            unset.Unset, typing.Collection[typing.Union[guilds.Role, bases.UniqueObjectT]]
        ] = unset.UNSET,
        mute: typing.Union[unset.Unset, bool] = unset.UNSET,
        deaf: typing.Union[unset.Unset, bool] = unset.UNSET,
        voice_channel: typing.Union[unset.Unset, channels.GuildVoiceChannel, bases.UniqueObjectT, None] = unset.UNSET,
        reason: typing.Union[str, unset.Unset] = unset.UNSET,
    ) -> None:
        route = routes.PATCH_GUILD_MEMBER.compile(
            guild=conversions.value_to_snowflake(guild), user=conversions.value_to_snowflake(user)
        )
        payload = {}
        conversions.put_if_specified(payload, "nick", nick)
        conversions.put_if_specified(payload, "mute", mute)
        conversions.put_if_specified(payload, "deaf", deaf)

        if voice_channel is None:
            payload["channel_id"] = None
        elif not unset.is_unset(voice_channel):
            payload["channel_id"] = conversions.value_to_snowflake(voice_channel)

        if not unset.is_unset(roles):
            payload["roles"] = [conversions.value_to_snowflake(r) for r in roles]

        await self._request(route, body=payload, reason=reason)

    async def edit_my_nick(
        self,
        guild: typing.Union[guilds.Guild, bases.UniqueObjectT],
        nick: typing.Optional[str],
        *,
        reason: typing.Union[unset.Unset, str] = unset.UNSET,
    ) -> None:
        route = routes.PATCH_MY_GUILD_NICKNAME.compile(guild=conversions.value_to_snowflake(guild))
        payload = {"nick": nick}
        await self._request(route, body=payload, reason=reason)

    async def add_role_to_member(
        self,
        guild: typing.Union[guilds.Guild, bases.UniqueObjectT],
        user: typing.Union[users.User, bases.UniqueObjectT],
        role: typing.Union[guilds.Role, bases.UniqueObjectT],
        *,
        reason: typing.Union[unset.Unset, str] = unset.UNSET,
    ) -> None:
        route = routes.PUT_GUILD_MEMBER_ROLE.compile(
            guild=conversions.value_to_snowflake(guild),
            user=conversions.value_to_snowflake(user),
            role=conversions.value_to_snowflake(role),
        )
        await self._request(route, reason=reason)

    async def remove_role_from_member(
        self,
        guild: typing.Union[guilds.Guild, bases.UniqueObjectT],
        user: typing.Union[users.User, bases.UniqueObjectT],
        role: typing.Union[guilds.Role, bases.UniqueObjectT],
        *,
        reason: typing.Union[unset.Unset, str] = unset.UNSET,
    ) -> None:
        route = routes.DELETE_GUILD_MEMBER_ROLE.compile(
            guild=conversions.value_to_snowflake(guild),
            user=conversions.value_to_snowflake(user),
            role=conversions.value_to_snowflake(role),
        )
        await self._request(route, reason=reason)

    async def kick_member(
        self,
        guild: typing.Union[guilds.Guild, bases.UniqueObjectT],
        user: typing.Union[users.User, bases.UniqueObjectT],
        *,
        reason: typing.Union[unset.Unset, str] = unset.UNSET,
    ) -> None:
        route = routes.DELETE_GUILD_MEMBER.compile(
            guild=conversions.value_to_snowflake(guild), user=conversions.value_to_snowflake(user),
        )
        await self._request(route, reason=reason)

    async def ban_user(
        self,
        guild: typing.Union[guilds.Guild, bases.UniqueObjectT],
        user: typing.Union[users.User, bases.UniqueObjectT],
        *,
        reason: typing.Union[unset.Unset, str] = unset.UNSET,
    ) -> None:
        route = routes.PUT_GUILD_BAN.compile(
            guild=conversions.value_to_snowflake(guild), user=conversions.value_to_snowflake(user),
        )
        await self._request(route, reason=reason)

    async def unban_user(
        self,
        guild: typing.Union[guilds.Guild, bases.UniqueObjectT],
        user: typing.Union[users.User, bases.UniqueObjectT],
        *,
        reason: typing.Union[unset.Unset, str] = unset.UNSET,
    ) -> None:
        route = routes.DELETE_GUILD_BAN.compile(
            guild=conversions.value_to_snowflake(guild), user=conversions.value_to_snowflake(user),
        )
        await self._request(route, reason=reason)

    async def fetch_ban(
        self,
        guild: typing.Union[guilds.Guild, bases.UniqueObjectT],
        user: typing.Union[users.User, bases.UniqueObjectT],
    ) -> guilds.GuildMemberBan:
        route = routes.GET_GUILD_BAN.compile(
            guild=conversions.value_to_snowflake(guild), user=conversions.value_to_snowflake(user),
        )
        response = await self._request(route)
        return self._app.entity_factory.deserialize_guild_member_ban(response)

    async def fetch_bans(
        self, guild: typing.Union[guilds.Guild, bases.UniqueObjectT], /
    ) -> typing.Sequence[guilds.GuildMemberBan]:
        route = routes.GET_GUILD_BANS.compile(guild=conversions.value_to_snowflake(guild))
        response = await self._request(route)
        return [self._app.entity_factory.deserialize_guild_member_ban(b) for b in response]

    async def fetch_roles(
        self, guild: typing.Union[guilds.Guild, bases.UniqueObjectT], /
    ) -> typing.Sequence[guilds.Role]:
        route = routes.GET_GUILD_ROLES.compile(guild=conversions.value_to_snowflake(guild))
        response = await self._request(route)
        return [self._app.entity_factory.deserialize_role(r) for r in response]

    async def create_role(
        self,
        guild: typing.Union[guilds.Guild, bases.UniqueObjectT],
        /,
        *,
        name: typing.Union[unset.Unset, str] = unset.UNSET,
        permissions: typing.Union[unset.Unset, permissions_.Permission] = unset.UNSET,
        color: typing.Union[unset.Unset, colors.Color] = unset.UNSET,
        colour: typing.Union[unset.Unset, colors.Color] = unset.UNSET,
        hoist: typing.Union[unset.Unset, bool] = unset.UNSET,
        mentionable: typing.Union[unset.Unset, bool] = unset.UNSET,
        reason: typing.Union[unset.Unset, str] = unset.UNSET,
    ) -> guilds.Role:
        if not unset.count_unset_objects(color, colour):
            raise TypeError("Can not specify 'color' and 'colour' together.")

        route = routes.POST_GUILD_ROLES.compile(guild=conversions.value_to_snowflake(guild))
        payload = {}
        conversions.put_if_specified(payload, "name", name)
        conversions.put_if_specified(payload, "permissions", permissions)
        conversions.put_if_specified(payload, "color", color)
        conversions.put_if_specified(payload, "color", colour)
        conversions.put_if_specified(payload, "hoist", hoist)
        conversions.put_if_specified(payload, "mentionable", mentionable)

        response = await self._request(route, body=payload, reason=reason)
        return self._app.entity_factory.deserialize_role(response)

    async def reposition_roles(
        self,
        guild: typing.Union[guilds.Guild, bases.UniqueObjectT],
        positions: typing.Mapping[int, typing.Union[guilds.Role, bases.UniqueObjectT]],
    ) -> None:
        route = routes.POST_GUILD_ROLES.compile(guild=conversions.value_to_snowflake(guild))
        payload = [{"id": conversions.value_to_snowflake(role), "position": pos} for pos, role in positions.items()]
        await self._request(route, body=payload)

    async def edit_role(
        self,
        guild: typing.Union[guilds.Guild, bases.UniqueObjectT],
        role: typing.Union[guilds.Role, bases.UniqueObjectT],
        *,
        name: typing.Union[unset.Unset, str] = unset.UNSET,
        permissions: typing.Union[unset.Unset, permissions_.Permission] = unset.UNSET,
        color: typing.Union[unset.Unset, colors.Color] = unset.UNSET,
        colour: typing.Union[unset.Unset, colors.Color] = unset.UNSET,
        hoist: typing.Union[unset.Unset, bool] = unset.UNSET,
        mentionable: typing.Union[unset.Unset, bool] = unset.UNSET,
        reason: typing.Union[unset.Unset, str] = unset.UNSET,
    ) -> guilds.Role:
        if not unset.count_unset_objects(color, colour):
            raise TypeError("Can not specify 'color' and 'colour' together.")

        route = routes.PATCH_GUILD_ROLE.compile(
            guild=conversions.value_to_snowflake(guild), role=conversions.value_to_snowflake(role),
        )

        payload = {}
        conversions.put_if_specified(payload, "name", name)
        conversions.put_if_specified(payload, "permissions", permissions)
        conversions.put_if_specified(payload, "color", color)
        conversions.put_if_specified(payload, "color", colour)
        conversions.put_if_specified(payload, "hoist", hoist)
        conversions.put_if_specified(payload, "mentionable", mentionable)

        response = await self._request(route, body=payload, reason=reason)
        return self._app.entity_factory.deserialize_role(response)

    async def delete_role(
        self,
        guild: typing.Union[guilds.Guild, bases.UniqueObjectT],
        role: typing.Union[guilds.Role, bases.UniqueObjectT],
    ) -> None:
        route = routes.DELETE_GUILD_ROLE.compile(
            guild=conversions.value_to_snowflake(guild), role=conversions.value_to_snowflake(role),
        )
        await self._request(route)

    async def estimate_guild_prune_count(
        self, guild: typing.Union[guilds.Guild, bases.UniqueObjectT], days: int,
    ) -> int:
        route = routes.GET_GUILD_PRUNE.compile(guild=conversions.value_to_snowflake(guild))
        payload = {"days": str(days)}
        response = await self._request(route, query=payload)
        return int(response["pruned"])

    async def begin_guild_prune(
        self,
        guild: typing.Union[guilds.Guild, bases.UniqueObjectT],
        days: int,
        *,
        reason: typing.Union[unset.Unset, str],
    ) -> int:
        route = routes.POST_GUILD_PRUNE.compile(guild=conversions.value_to_snowflake(guild))
        payload = {"compute_prune_count": "true", "days": str(days)}
        response = await self._request(route, query=payload, reason=reason)
        return int(response["pruned"])

    async def fetch_guild_voice_regions(
        self, guild: typing.Union[guilds.Guild, bases.UniqueObjectT], /
    ) -> typing.Sequence[voices.VoiceRegion]:
        route = routes.GET_GUILD_VOICE_REGIONS.compile(guild=conversions.value_to_snowflake(guild))
        response = await self._request(route)
        return [self._app.entity_factory.deserialize_voice_region(r) for r in response]

    async def fetch_guild_invites(
        self, guild: typing.Union[guilds.Guild, bases.UniqueObjectT], /
    ) -> typing.Sequence[invites.InviteWithMetadata]:
        route = routes.GET_GUILD_INVITES.compile(guild=conversions.value_to_snowflake(guild))
        response = await self._request(route)
        return [self._app.entity_factory.deserialize_invite_with_metadata(r) for r in response]

    async def fetch_integrations(
        self, guild: typing.Union[guilds.Guild, bases.UniqueObjectT], /
    ) -> typing.Sequence[guilds.GuildIntegration]:
        route = routes.GET_GUILD_INTEGRATIONS.compile(guild=conversions.value_to_snowflake(guild))
        response = await self._request(route)
        return [self._app.entity_factory.deserialize_guild_integration(i) for i in response]

    async def edit_integration(
        self,
        guild: typing.Union[guilds.Guild, bases.UniqueObjectT],
        integration: typing.Union[guilds.GuildIntegration, bases.UniqueObjectT],
        *,
        expire_behaviour: typing.Union[unset.Unset, guilds.IntegrationExpireBehaviour] = unset.UNSET,
        expire_grace_period: typing.Union[unset.Unset, more_typing.TimeSpanT] = unset.UNSET,
        enable_emojis: typing.Union[unset.Unset, bool] = unset.UNSET,
        reason: typing.Union[unset.Unset, str] = unset.UNSET,
    ) -> None:
        route = routes.PATCH_GUILD_INTEGRATION.compile(
            guild=conversions.value_to_snowflake(guild), integration=conversions.value_to_snowflake(integration),
        )
        payload = {}
        conversions.put_if_specified(payload, "expire_behaviour", expire_behaviour)
        conversions.put_if_specified(payload, "expire_grace_period", expire_grace_period, conversions.timespan_to_int)
        # Inconsistent naming in the API itself, so I have changed the name.
        conversions.put_if_specified(payload, "enable_emoticons", enable_emojis)
        await self._request(route, body=payload, reason=reason)

    async def delete_integration(
        self,
        guild: typing.Union[guilds.Guild, bases.UniqueObjectT],
        integration: typing.Union[guilds.GuildIntegration, bases.UniqueObjectT],
        *,
        reason: typing.Union[unset.Unset, str] = unset.UNSET,
    ) -> None:
        route = routes.DELETE_GUILD_INTEGRATION.compile(
            guild=conversions.value_to_snowflake(guild), integration=conversions.value_to_snowflake(integration),
        )
        await self._request(route, reason=reason)

    async def sync_integration(
        self,
        guild: typing.Union[guilds.Guild, bases.UniqueObjectT],
        integration: typing.Union[guilds.GuildIntegration, bases.UniqueObjectT],
    ) -> None:
        route = routes.POST_GUILD_INTEGRATION_SYNC.compile(
            guild=conversions.value_to_snowflake(guild), integration=conversions.value_to_snowflake(integration),
        )
        await self._request(route)

    async def fetch_widget(self, guild: typing.Union[guilds.Guild, bases.UniqueObjectT], /) -> guilds.GuildWidget:
        route = routes.GET_GUILD_WIDGET.compile(guild=conversions.value_to_snowflake(guild))
        response = await self._request(route)
        return self._app.entity_factory.deserialize_guild_widget(response)

    async def edit_widget(
        self,
        guild: typing.Union[guilds.Guild, bases.UniqueObjectT],
        /,
        *,
        channel: typing.Union[unset.Unset, channels.GuildChannel, bases.UniqueObjectT, None] = unset.UNSET,
        enabled: typing.Union[unset.Unset, bool] = unset.UNSET,
        reason: typing.Union[unset.Unset, str] = unset.UNSET,
    ) -> guilds.GuildWidget:
        route = routes.PATCH_GUILD_WIDGET.compile(guild=conversions.value_to_snowflake(guild))

        payload = {}
        conversions.put_if_specified(payload, "enabled", enabled)
        if channel is None:
            payload["channel"] = None
        elif not unset.is_unset(channel):
            payload["channel"] = conversions.value_to_snowflake(channel)

        response = await self._request(route, body=payload, reason=reason)
        return self._app.entity_factory.deserialize_guild_widget(response)

    async def fetch_vanity_url(self, guild: typing.Union[guilds.Guild, bases.UniqueObjectT], /) -> invites.VanityURL:
        route = routes.GET_GUILD_VANITY_URL.compile(guild=conversions.value_to_snowflake(guild))
        response = await self._request(route)
        return self._app.entity_factory.deserialize_vanity_url(response)
