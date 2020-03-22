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
"""Implementation of a basic HTTP client that uses aiohttp to interact with the Discord API."""
__all__ = ["HTTPClient"]

import asyncio
import contextlib
import datetime
import email.utils
import json
import ssl
import typing
import uuid

import aiohttp.typedefs

from hikari.internal_utilities import assertions
from hikari.internal_utilities import containers
from hikari.internal_utilities import storage
from hikari.internal_utilities import transformations
from hikari.net import base_http_client
from hikari.net import codes
from hikari.net import errors
from hikari.net import ratelimits
from hikari.net import routes
from hikari.net import versions


class HTTPClient(base_http_client.BaseHTTPClient):
    """A RESTful client to allow you to interact with the Discord API."""

    _AUTHENTICATION_SCHEMES = ("Bearer", "Bot")

    def __init__(
        self,
        *,
        base_url="https://discordapp.com/api/v{0.version}",
        allow_redirects: bool = False,
        connector: aiohttp.BaseConnector = None,
        proxy_headers: aiohttp.typedefs.LooseHeaders = None,
        proxy_auth: aiohttp.BasicAuth = None,
        proxy_url: str = None,
        ssl_context: ssl.SSLContext = None,
        verify_ssl: bool = True,
        timeout: float = None,
        json_deserialize=json.loads,
        json_serialize=json.dumps,
        token,
        version: typing.Union[int, versions.HTTPAPIVersion] = versions.HTTPAPIVersion.STABLE,
    ):
        super().__init__(
            allow_redirects=allow_redirects,
            connector=connector,
            proxy_headers=proxy_headers,
            proxy_auth=proxy_auth,
            proxy_url=proxy_url,
            ssl_context=ssl_context,
            verify_ssl=verify_ssl,
            timeout=timeout,
            json_serialize=json_serialize,
        )
        self.version = int(version)
        self.base_url = base_url.format(self)
        self.global_ratelimiter = ratelimits.ManualRateLimiter()
        self.json_serialize = json_serialize
        self.json_deserialize = json_deserialize
        self.ratelimiter = ratelimits.HTTPBucketRateLimiterManager()
        self.ratelimiter.start()

        if token is not None and not token.startswith(self._AUTHENTICATION_SCHEMES):
            this_type = type(self).__name__
            auth_schemes = " or ".join(self._AUTHENTICATION_SCHEMES)
            raise RuntimeError(f"Any token passed to {this_type} should begin with {auth_schemes}")

        self.token = token

    async def close(self):
        with contextlib.suppress(Exception):
            self.ratelimiter.close()
        await super().close()

    async def _request(
        self,
        compiled_route,
        *,
        headers=None,
        query=None,
        form_body=None,
        json_body: typing.Optional[typing.Union[typing.Dict, typing.Sequence[typing.Any]]] = None,
        reason: typing.Union[typing.Literal[...], str] = ...,
        re_seekable_resources: typing.Collection[typing.Any] = containers.EMPTY_COLLECTION,
        suppress_authorization_header: bool = False,
        **kwargs,
    ) -> typing.Union[typing.Dict, typing.Sequence[typing.Any], None]:
        bucket_ratelimit_future = self.ratelimiter.acquire(compiled_route)
        request_headers = {"X-RateLimit-Precision": "millisecond"}

        if self.token is not None and not suppress_authorization_header:
            request_headers["Authorization"] = self.token

        if reason and reason is not ...:
            request_headers["X-Audit-Log-Reason"] = reason

        if headers is not None:
            request_headers.update(headers)

        backoff = ratelimits.ExponentialBackOff()

        while True:
            # If we are uploading files with io objects in a form body, we need to reset the seeks to 0 to ensure
            # we can re-read the buffer.
            for resource in re_seekable_resources:
                resource.seek(0)

            # Aids logging when lots of entries are being logged at once by matching a unique UUID
            # between the request and response
            request_uuid = uuid.uuid4()

            await asyncio.gather(bucket_ratelimit_future, self.global_ratelimiter.acquire())

            if json_body is not None:
                body_type = "json"
            elif form_body is not None:
                body_type = "form"
            else:
                body_type = "None"

            self.logger.debug(
                "%s send to %s headers=%s query=%s body_type=%s body=%s",
                request_uuid,
                compiled_route,
                request_headers,
                query,
                body_type,
                json_body if json_body is not None else form_body,
            )

            async with super()._request(
                compiled_route.method,
                compiled_route.create_url(self.base_url),
                headers=request_headers,
                json=json_body,
                params=query,
                data=form_body,
                **kwargs,
            ) as resp:
                raw_body = await resp.read()
                headers = resp.headers

                self.logger.debug(
                    "%s recv from %s status=%s reason=%s headers=%s body=%s",
                    request_uuid,
                    compiled_route,
                    resp.status,
                    resp.reason,
                    headers,
                    raw_body,
                )

                limit = int(headers.get("X-RateLimit-Limit", "1"))
                remaining = int(headers.get("X-RateLimit-Remaining", "1"))
                bucket = headers.get("X-RateLimit-Bucket", "None")
                reset = float(headers.get("X-RateLimit-Reset", "0"))
                reset_date = datetime.datetime.fromtimestamp(reset, tz=datetime.timezone.utc)
                now_date = email.utils.parsedate_to_datetime(headers["Date"])
                content_type = headers.get("Content-Type")

                status = resp.status

                with contextlib.suppress(ValueError):
                    status = codes.HTTPStatusCode(status)

                if status == codes.HTTPStatusCode.NO_CONTENT:
                    body = None
                elif content_type == "application/json":
                    body = self.json_deserialize(raw_body)
                elif content_type == "text/plain" or content_type == "text/html":
                    await self._handle_bad_response(
                        backoff,
                        status,
                        compiled_route,
                        f"Received unexpected response of type {content_type} with body: {raw_body!r}",
                        None,
                    )
                    continue
                else:
                    body = None

            self.ratelimiter.update_rate_limits(compiled_route, bucket, remaining, limit, now_date, reset_date)

            if status == codes.HTTPStatusCode.TOO_MANY_REQUESTS:
                # We are being rate limited.
                if body["global"]:
                    retry_after = float(body["retry_after"]) / 1_000
                    self.global_ratelimiter.throttle(retry_after)
                continue

            if status >= codes.HTTPStatusCode.BAD_REQUEST:
                code = None

                if self.version == versions.HTTPAPIVersion.V6:
                    message = ", ".join(f"{k} - {v}" for k, v in body.items())
                else:
                    message = body.get("message")
                    with contextlib.suppress(ValueError):
                        code = codes.JSONErrorCode(body.get("code"))

                if status == codes.HTTPStatusCode.BAD_REQUEST:
                    raise errors.BadRequestHTTPError(compiled_route, message, code)
                elif status == codes.HTTPStatusCode.UNAUTHORIZED:
                    raise errors.UnauthorizedHTTPError(compiled_route, message, code)
                elif status == codes.HTTPStatusCode.FORBIDDEN:
                    raise errors.ForbiddenHTTPError(compiled_route, message, code)
                elif status == codes.HTTPStatusCode.NOT_FOUND:
                    raise errors.NotFoundHTTPError(compiled_route, message, code)
                elif status < codes.HTTPStatusCode.INTERNAL_SERVER_ERROR:
                    raise errors.ClientHTTPError(status, compiled_route, message, code)

                await self._handle_bad_response(backoff, status, compiled_route, message, code)
                continue

            return body

    async def _handle_bad_response(
        self,
        backoff: ratelimits.ExponentialBackOff,
        status: typing.Union[codes.HTTPStatusCode, int, None],
        route: routes.CompiledRoute,
        message: typing.Optional[str],
        code: typing.Union[codes.JSONErrorCode, int, None],
    ) -> None:
        try:
            next_sleep = next(backoff)
            self.logger.warning("received a server error response, backing off for %ss and trying again", next_sleep)
            await asyncio.sleep(next_sleep)
        except asyncio.TimeoutError:
            raise errors.ServerHTTPError(status, route, message, code)

    async def get_gateway(self) -> str:
        """
        Returns
        -------
        :obj:`str`
            A static URL to use to connect to the gateway with.

        Note
        ----
        Users are expected to attempt to cache this result.
        """
        result = await self._request(routes.GATEWAY.compile(self.GET))
        return result["url"]

    async def get_gateway_bot(self) -> typing.Dict:
        """
        Returns
        -------
        :obj:`typing.Dict`
            An object containing a ``url`` to connect to, an :obj:`int` number of shards recommended to use
            for connecting, and a ``session_start_limit`` object.

        Note
        ----
        Unlike :meth:`get_gateway`, this requires a valid token to work.
        """
        return await self._request(routes.GATEWAY_BOT.compile(self.GET))

    async def get_guild_audit_log(
        self,
        guild_id: str,
        *,
        user_id: typing.Union[typing.Literal[...], str] = ...,
        action_type: typing.Union[typing.Literal[...], int] = ...,
        limit: typing.Union[typing.Literal[...], int] = ...,
    ) -> typing.Dict:
        """Get an audit log object for the given guild.

        Parameters
        ----------
        guild_id : :obj:`str`
            The guild ID to look up.
        user_id : :obj:`str`
            If specified, the user ID to filter by.
        action_type : :obj:`int`
            If specified, the action type to look up.
        limit : :obj:`int`
            If specified, the limit to apply to the number of records. 
            Defaults to ``50``. Must be between ``1`` and ``100`` inclusive.

        Returns
        -------
        :obj:`typing.Dict`
            An audit log object.

        Raises
        ------
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you lack the given permissions to view an audit log.
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the guild does not exist.
        """
        query = {}
        transformations.put_if_specified(query, "user_id", user_id)
        transformations.put_if_specified(query, "action_type", action_type)
        transformations.put_if_specified(query, "limit", limit)
        route = routes.GUILD_AUDIT_LOGS.compile(self.GET, guild_id=guild_id)
        return await self._request(route, query=query)

    async def get_channel(self, channel_id: str) -> typing.Dict:
        """Get a channel object from a given channel ID.

        Parameters
        ----------
        channel_id : :obj:`str`
            The channel ID to look up.

        Returns
        -------
        :obj:`typing.Dict`
            The channel object that has been found.

        Raises
        ------
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you don't have access to the channel.
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the channel does not exist.
        """
        route = routes.CHANNEL.compile(self.GET, channel_id=channel_id)
        return await self._request(route)

    async def modify_channel(  # lgtm [py/similar-function]
        self,
        channel_id: str,
        *,
        name: typing.Union[typing.Literal[...], str] = ...,
        position: typing.Union[typing.Literal[...], int] = ...,
        topic: typing.Union[typing.Literal[...], str] = ...,
        nsfw: typing.Union[typing.Literal[...], bool] = ...,
        rate_limit_per_user: typing.Union[typing.Literal[...], int] = ...,
        bitrate: typing.Union[typing.Literal[...], int] = ...,
        user_limit: typing.Union[typing.Literal[...], int] = ...,
        permission_overwrites: typing.Union[typing.Literal[...], typing.Sequence[typing.Dict]] = ...,
        parent_id: typing.Union[typing.Literal[...], str] = ...,
        reason: typing.Union[typing.Literal[...], str] = ...,
    ) -> typing.Dict:
        """Update one or more aspects of a given channel ID.

        Parameters
        ----------
        channel_id : :obj:`str`
            The channel ID to update.
        name : :obj:`str`
            If specified, the new name for the channel.This must be 
            between ``2`` and ``100`` characters in length.
        position : :obj:`int`
            If specified, the position to change the channel to.
        topic : :obj:`str`
            If specified, the topic to set. This is only applicable to 
            text channels. This must be between ``0`` and ``1024`` 
            characters in length.
        nsfw : :obj:`bool`
            If specified, wheather the  channel will be marked as NSFW. 
            Only applicable to text channels.
        rate_limit_per_user : :obj:`int`
            If specified, the number of seconds the user has to wait before sending 
            another message.  This will not apply to bots, or to members with 
            ``MANAGE_MESSAGES`` or ``MANAGE_CHANNEL`` permissions. This must 
            be between ``0`` and ``21600`` seconds.
        bitrate : :obj:`int`
            If specified, the bitrate in bits per second allowable for the channel. 
            This only applies to voice channels and must be between ``8000`` 
            and ``96000`` for normal servers or ``8000`` and ``128000`` for 
            VIP servers.
        user_limit : :obj:`int`
            If specified, the new max number of users to allow in a voice channel. 
            This must be between ``0`` and ``99`` inclusive, where 
            ``0`` implies no limit.
        permission_overwrites : :obj:`typing.Sequence` [ :obj:`typing.Dict` ]
            If specified, the new list of permission overwrites that are category 
            specific to replace the existing overwrites with.
        parent_id : :obj:`str`
            If specified, the new parent category ID to set for the channel.
        reason : :obj:`str`
            If specified, the audit log reason explaining why the operation 
            was performed.
        
        Returns
        -------
        :obj:`typing.Dict`
            The channel object that has been modified.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the channel does not exist.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you lack the permission to make the change.
        :obj:`hikari.net.errors.BadRequestHTTPError`
            If you provide incorrect options for the corresponding channel type 
            (e.g. a ``bitrate`` for a text channel).
        """
        payload = {}
        transformations.put_if_specified(payload, "name", name)
        transformations.put_if_specified(payload, "position", position)
        transformations.put_if_specified(payload, "topic", topic)
        transformations.put_if_specified(payload, "nsfw", nsfw)
        transformations.put_if_specified(payload, "rate_limit_per_user", rate_limit_per_user)
        transformations.put_if_specified(payload, "bitrate", bitrate)
        transformations.put_if_specified(payload, "user_limit", user_limit)
        transformations.put_if_specified(payload, "permission_overwrites", permission_overwrites)
        transformations.put_if_specified(payload, "parent_id", parent_id)
        route = routes.CHANNEL.compile(self.PATCH, channel_id=channel_id)
        return await self._request(route, json_body=payload, reason=reason)

    async def delete_close_channel(self, channel_id: str) -> None:
        """Delete the given channel ID, or if it is a DM, close it.

        Parameters
        ----------
        channel_id : :obj:`str`
            The channel ID to delete, or the user ID of the direct message to close.

        Returns
        -------
        ``None``
            Nothing, unlike what the API specifies. This is done to maintain 
            consistency with other calls of a similar nature in this API wrapper.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the channel does not exist.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you do not have permission to delete the channel.

        Warning
        -------
        Deleted channels cannot be un-deleted. Deletion of DMs is able to be undone by reopening the DM.
        """
        route = routes.CHANNEL.compile(self.DELETE, channel_id=channel_id)
        await self._request(route)

    async def get_channel_messages(
        self,
        channel_id: str,
        *,
        limit: typing.Union[typing.Literal[...], int] = ...,
        after: typing.Union[typing.Literal[...], str] = ...,
        before: typing.Union[typing.Literal[...], str] = ...,
        around: typing.Union[typing.Literal[...], str] = ...,
    ) -> typing.Sequence[typing.Dict]:
        """Retrieve message history for a given channel. 
        If a user is provided, retrieve the DM history.

        Parameters
        ----------
        channel_id : :obj:`str`
            The ID of the channel to retrieve the messages from.
        limit : :obj:`int`
            If specified, the number of messages to return. Must be 
            between ``1`` and ``100`` inclusive.Defaults to ``50`` 
            if unspecified.
        after : :obj:`str`
            A message ID. If specified, only return messages sent AFTER this message.
        before : :obj:`str`
            A message ID. If specified, only return messages sent BEFORE this message.
        around : :obj:`str`
            A message ID. If specified, only return messages sent AROUND this message.
      
        Returns
        -------
        :obj:`typing.Sequence` [ :obj:`typing.Dict` ]
            A list of message objects.

        Raises
        ------
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you lack permission to read the channel.
        :obj:`hikari.net.errors.BadRequestHTTPError`
            If your query is malformed, has an invalid value for ``limit``, 
            or contains more than one of ``after``, ``before`` and ``around``.
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the channel is not found, or the message 
            provided for one of the filter arguments is not found.
        
        Note
        ----
        If you are missing the ``VIEW_CHANNEL`` permission, you will receive a 
        :obj:`hikari.net.errors.ForbiddenHTTPError`. If you are instead missing 
        the ``READ_MESSAGE_HISTORY`` permission, you will always receive 
        zero results, and thus an empty list will be returned instead.

        Warning
        -------
        You can only specify a maximum of one from ``before``, ``after``, and ``around``.
        Specifying more than one will cause a :obj:`hikari.net.errors.BadRequestHTTPError` to be raised.
        """
        query = {}
        transformations.put_if_specified(query, "limit", limit)
        transformations.put_if_specified(query, "before", before)
        transformations.put_if_specified(query, "after", after)
        transformations.put_if_specified(query, "around", around)
        route = routes.CHANNEL_MESSAGES.compile(self.GET, channel_id=channel_id)
        return await self._request(route, query=query)

    async def get_channel_message(self, channel_id: str, message_id: str) -> typing.Dict:
        """Get the message with the given message ID from the channel with the given channel ID.

        Parameters
        ----------
        channel_id : :obj:`str`
            The ID of the channel to get the message from.
        message_id : :obj:`str`
            The ID of the message to retrieve.

        Returns
        -------
        :obj:`typing.Dict`
            A message object.

        Note
        ----
        This requires the ``READ_MESSAGE_HISTORY`` permission.

        Raises
        ------
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you lack permission to see the message.
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the channel or message is not found.
        """
        route = routes.CHANNEL_MESSAGE.compile(self.GET, channel_id=channel_id, message_id=message_id)
        return await self._request(route)

    async def create_message(
        self,
        channel_id: str,
        *,
        content: typing.Union[typing.Literal[...], str] = ...,
        nonce: typing.Union[typing.Literal[...], str] = ...,
        tts: typing.Union[typing.Literal[...], bool] = ...,
        files: typing.Union[typing.Literal[...], typing.Sequence[typing.Tuple[str, storage.FileLikeT]]] = ...,
        embed: typing.Union[typing.Literal[...], typing.Dict] = ...,
        allowed_mentions: typing.Union[typing.Literal[...], typing.Dict] = ...,
    ) -> typing.Dict:
        """Create a message in the given channel or DM.

        Parameters
        ----------
        channel_id : :obj:`str`
            The channel or user ID to send to.
        content : :obj:`str`
            If specified, the message content to send with the message.
        nonce : :obj:`str`
            If specified, an optional ID to send for opportunistic message 
            creation. This doesn't serve any real purpose for general use, 
            and can usually be ignored.
        tts : :obj:`bool`
            If specified, whether the message will be sent as a TTS message.
        files : :obj:`typing.Sequence` [ :obj:`typing.Tuple` [ :obj:`str`, :obj:`storage.FileLikeT` ] ]
            If specified, this should be a list of between ``1`` and ``5`` tuples. 
            Each tuple should consist of the file name, and either 
            raw :obj:`bytes` or an :obj:`io.IOBase` derived object with 
            a seek that points to a buffer containing said file.
        embed : :obj:`typing.Dict`
            If specified, the embed to send with the message.
        allowed_mentions : :obj:`typing.Dict`
            If specified, the mentions to parse from the ``content``. 
            If not specified, will parse all mentions from the ``content``.

        Returns
        -------
        :obj:`typing.Dict`
            The created message object.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the channel is not found.
        :obj:`hikari.net.errors.BadRequestHTTPError`
            This can be raised if the file is too large; if the embed exceeds 
            the defined limits; if the message content is specified only and 
            empty or greater than ``2000`` characters; if neither content, file 
            or embed are specified; if there is a duplicate id in only of the
            fields in ``allowed_mentions``; if you specify to parse all 
            users/roles mentions but also specify which users/roles to 
            parse only.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you lack permissions to send to this channel.
        """
        form = aiohttp.FormData()

        json_payload = {}
        transformations.put_if_specified(json_payload, "content", content)
        transformations.put_if_specified(json_payload, "nonce", nonce)
        transformations.put_if_specified(json_payload, "tts", tts)
        transformations.put_if_specified(json_payload, "embed", embed)
        transformations.put_if_specified(json_payload, "allowed_mentions", allowed_mentions)

        form.add_field("payload_json", json.dumps(json_payload), content_type="application/json")

        re_seekable_resources = []
        if files is not ...:
            for i, (file_name, file) in enumerate(files):
                file = storage.make_resource_seekable(file)
                re_seekable_resources.append(file)
                form.add_field(f"file{i}", file, filename=file_name, content_type="application/octet-stream")

        route = routes.CHANNEL_MESSAGES.compile(self.POST, channel_id=channel_id)
        return await self._request(route, form_body=form, re_seekable_resources=re_seekable_resources)

    async def create_reaction(self, channel_id: str, message_id: str, emoji: str) -> None:
        """Add a reaction to the given message in the given channel or user DM.

        Parameters
        ----------
        channel_id : :obj:`str`
            The ID of the channel to get the message from.
        message_id : :obj:`str`
            The ID of the message to add the reaction in.
        emoji : :obj:`str`
            The emoji to add. This can either be a series of unicode 
            characters making up a valid Discord emoji, or it can be a 
            snowflake ID for a custom emoji.

        Raises
        ------
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If this is the first reaction using this specific emoji on this 
            message and you lack the ``ADD_REACTIONS`` permission. If you lack 
            ``READ_MESSAGE_HISTORY``, this may also raise this error.
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the channel or message is not found, or if the emoji is not found.
        :obj:`hikari.net.errors.BadRequestHTTPError`
            If the emoji is not valid, unknown, or formatted incorrectly.
        """
        route = routes.OWN_REACTION.compile(self.PUT, channel_id=channel_id, message_id=message_id, emoji=emoji)
        await self._request(route)

    async def delete_own_reaction(self, channel_id: str, message_id: str, emoji: str) -> None:
        """Remove a reaction you made using a given emoji from a given message in a given channel or user DM.

        Parameters
        ----------
        channel_id : :obj:`str`
            The ID of the channel to get the message from.
        message_id : :obj:`str`
            The ID of the message to delete the reaction from.
        emoji : :obj:`str`
            The emoji to delete. This can either be a series of unicode 
            characters making up a valid Discord emoji, or it can be a 
            snowflake ID for a custom emoji.

        Raises
        ------
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you lack permission to do this.
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the channel or message or emoji is not found.
        """
        route = routes.OWN_REACTION.compile(self.DELETE, channel_id=channel_id, message_id=message_id, emoji=emoji)
        await self._request(route)

    async def delete_all_reactions_for_emoji(self, channel_id: str, message_id: str, emoji: str) -> None:
        """Remove all reactions for a single given emoji on a given message in a given channel or user DM.

        Parameters
        ----------
        channel_id : :obj:`str`
            The ID of the channel to get the message from.
        message_id : :obj:`str`
            The ID of the message to delete the reactions from.
        emoji : :obj:`str`
            The emoji to delete. This can either be a series of unicode 
            characters making up a valid Discord emoji, or it can be a 
            snowflake ID for a custom emoji.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundError`
            If the channel or message or emoji or user is not found.
        :obj:`hikari.net.errors.ForbiddenError`
            If you lack the ``MANAGE_MESSAGES`` permission, or are in DMs.
        """
        route = routes.REACTION_EMOJI.compile(self.DELETE, channel_id=channel_id, message_id=message_id, emoji=emoji)
        await self._request(route)

    async def delete_user_reaction(self, channel_id: str, message_id: str, emoji: str, user_id: str) -> None:
        """Remove a reaction made by a given user using a given emoji on a given message in a given channel or user DM.

        Parameters
        ----------
        channel_id : :obj:`str`
            The ID of the channel to get the message from.
        message_id : :obj:`str`
            The ID of the message to remove the reaction from.
        emoji : :obj:`str`
            The emoji to delete. This can either be a series of unicode 
            characters making up a valid Discord emoji, or it can be a 
            snowflake ID for a custom emoji.
        user_id : :obj:`str`
            The ID of the user who made the reaction that you wish to remove.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the channel or message or emoji or user is not found.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you lack the ``MANAGE_MESSAGES`` permission, or are in DMs.
        """
        route = routes.REACTION_EMOJI_USER.compile(
            self.DELETE, channel_id=channel_id, message_id=message_id, emoji=emoji, user_id=user_id,
        )
        await self._request(route)

    async def get_reactions(
        self,
        channel_id: str,
        message_id: str,
        emoji: str,
        *,
        after: typing.Union[typing.Literal[...], str] = ...,
        limit: typing.Union[typing.Literal[...], int] = ...,
    ) -> typing.Sequence[typing.Dict]:
        """Get a list of users who reacted with the given emoji on 
        the given message in the given channel or user DM.

        Parameters
        ----------
        channel_id : :obj:`str`
            The ID of the channel to get the message from.
        message_id : :obj:`str`
            The ID of the message to get the reactions from.
        emoji : :obj:`str`
            The emoji to get. This can either be a series of unicode 
            characters making up a valid Discord emoji, or it can be a 
            snowflake ID for a custom emoji.
        after : :obj:`str`
            If specified, the user ID. If specified, only users with a snowflake 
            that is lexicographically greater thanthe value will be returned.
        limit : :obj:`str`
            If specified, the limit of the number of values to return. Must be 
            between ``1`` and ``100`` inclusive. If unspecified, 
            defaults to ``25``.

        Returns
        -------
        :obj:`typing.Sequence` [ :obj:`typing.Dict` ]
            A list of user objects.

        Raises
        ------
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you lack access to the message.
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the channel or message is not found.
        """
        query = {}
        transformations.put_if_specified(query, "after", after)
        transformations.put_if_specified(query, "limit", limit)
        route = routes.REACTIONS.compile(self.GET, channel_id=channel_id, message_id=message_id, emoji=emoji)
        return await self._request(route, query=query)

    async def delete_all_reactions(self, channel_id: str, message_id: str) -> None:
        """Deletes all reactions from a given message in a given channel.

        Parameters
        ----------
        channel_id : :obj:`str`
            The ID of the channel to get the message from.
        message_id:
            The ID of the message to remove all reactions from.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the channel or message is not found.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you lack the ``MANAGE_MESSAGES`` permission.
        """
        route = routes.ALL_REACTIONS.compile(self.DELETE, channel_id=channel_id, message_id=message_id)
        await self._request(route)

    async def edit_message(
        self,
        channel_id: str,
        message_id: str,
        *,
        content: typing.Optional[typing.Union[typing.Literal[...], str]] = ...,
        embed: typing.Optional[typing.Union[typing.Literal[...], typing.Dict]] = ...,
        flags: typing.Union[typing.Literal[...], int] = ...,
    ) -> typing.Dict:
        """Update the given message.

        Parameters
        ----------
        channel_id : :obj:`str`
            The ID of the channel to get the message from.
        message_id : :obj:`str` 
            The ID of the message to edit.
        content : :obj:`str`, optional
            If specified, the string content to replace with in the message.
            If ``None``, the content will be removed from the message.
        embed : :obj:`typing.Dict`, optional
            If specified, the embed to replace with in the message.
            If ``None``, the embed will be removed from the message.
        flags : :obj:`int`
            If specified, the integer to replace the message's current flags.

        Returns
        -------
        :obj:`typing.Dict`
            The edited message object.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the channel or message is not found.
        :obj:`hikari.net.errors.BadRequestHTTPError`
            This can be raised if the embed exceeds the defined limits; 
            if the message content is specified only and empty or greater 
            than ``2000`` characters; if neither content, file or embed 
            are specified.
            parse only.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you try to edit content or embed on a message you did not author or try to edit the flags
            on a message you did not author without the ``MANAGE_MESSAGES`` permission.
        """
        payload = {}
        transformations.put_if_specified(payload, "content", content)
        transformations.put_if_specified(payload, "embed", embed)
        transformations.put_if_specified(payload, "flags", flags)
        route = routes.CHANNEL_MESSAGE.compile(self.PATCH, channel_id=channel_id, message_id=message_id)
        return await self._request(route, json_body=payload)

    async def delete_message(self, channel_id: str, message_id: str) -> None:
        """Delete a message in a given channel.

        Parameters
        ----------
        channel_id : :obj:`str`
            The ID of the channel to get the message from.
        message_id : :obj:`str`
            The ID of the message to delete.

        Raises
        ------
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you did not author the message and are in a DM, or if you did not author the message and lack the
            ``MANAGE_MESSAGES`` permission in a guild channel.
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the channel or message is not found.
        """
        route = routes.CHANNEL_MESSAGE.compile(self.DELETE, channel_id=channel_id, message_id=message_id)
        await self._request(route)

    async def bulk_delete_messages(self, channel_id: str, messages: typing.Sequence[str]) -> None:
        """Delete multiple messages in a given channel.

        Parameters
        ----------
        channel_id : :obj:`str`
            The ID of the channel to get the message from.
        messages : :obj:`typing.Sequence` [ :obj:`str` ]
            A list of ``2-100`` message IDs to remove in the channel.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the channel is not found.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you lack the ``MANAGE_MESSAGES`` permission in the channel.
        :obj:`hikari.net.errors.BadRequestHTTPError`
            If any of the messages passed are older than ``2`` weeks in age or any duplicate message IDs are passed.

        Note
        ----
        This can only be used on guild text channels.
        Any message IDs that do not exist or are invalid still add towards the total ``100`` max messages to remove.
        This can only delete messages that are newer than ``2`` weeks in age. If any of the messages are older than ``2`` weeks
        then this call will fail.
        """
        payload = {"messages": messages}
        route = routes.CHANNEL_MESSAGES_BULK_DELETE.compile(self.POST, channel_id=channel_id)
        await self._request(route, json_body=payload)

    async def edit_channel_permissions(
        self,
        channel_id: str,
        overwrite_id: str,
        *,
        allow: typing.Union[typing.Literal[...], int] = ...,
        deny: typing.Union[typing.Literal[...], int] = ...,
        type_: typing.Union[typing.Literal[...], str] = ...,
        reason: typing.Union[typing.Literal[...], str] = ...,
    ) -> None:
        """Edit permissions for a given channel.

        Parameters
        ----------
        channel_id : :obj:`str`
            The ID of the channel to edit permissions for.
        overwrite_id : :obj:`str`
            The overwrite ID to edit.
        allow : :obj:`int`
            If specified, the bitwise value of all permissions to set to be allowed.
        deny : :obj:`int`
            If specified, the bitwise value of all permissions to set to be denied.
        type_ : :obj:`str`
            If specified, the type of overwrite. ``"member"`` if it is for a member, 
            or ``"role"`` if it is for a role.
        reason : :obj:`str`
            If specified, the audit log reason explaining why the operation 
            was performed.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the target channel or overwrite doesn't exist.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you lack permission to do this.
        """
        payload = {}
        transformations.put_if_specified(payload, "allow", allow)
        transformations.put_if_specified(payload, "deny", deny)
        transformations.put_if_specified(payload, "type", type_)
        route = routes.CHANNEL_PERMISSIONS.compile(self.PATCH, channel_id=channel_id, overwrite_id=overwrite_id)
        await self._request(route, json_body=payload, reason=reason)

    async def get_channel_invites(self, channel_id: str) -> typing.Sequence[typing.Dict]:
        """Get invites for a given channel.

        Parameters
        ----------
        channel_id : :obj:`str`
            The ID of the channel to get invites for.

        Returns
        -------
        :obj:`typing.Sequence` [ :obj:`typing.Dict` ]
            A list of invite objects.

        Raises
        ------
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you lack the ``MANAGE_CHANNELS`` permission.
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the channel does not exist.
        """
        route = routes.CHANNEL_INVITES.compile(self.GET, channel_id=channel_id)
        return await self._request(route)

    async def create_channel_invite(
        self,
        channel_id: str,
        *,
        max_age: typing.Union[typing.Literal[...], int] = ...,
        max_uses: typing.Union[typing.Literal[...], int] = ...,
        temporary: typing.Union[typing.Literal[...], bool] = ...,
        unique: typing.Union[typing.Literal[...], bool] = ...,
        target_user: typing.Union[typing.Literal[...], str] = ...,
        target_user_type: typing.Union[typing.Literal[...], int] = ...,
        reason: typing.Union[typing.Literal[...], str] = ...,
    ) -> typing.Dict:
        """Create a new invite for the given channel.

        Parameters
        ----------
        channel_id : :obj:`str`
            The ID of the channel to create the invite for.
        max_age : :obj:`int`
            If specified, the max age of the invite in seconds, defaults to 
            ``86400`` (``24`` hours). 
            Set to ``0`` to never expire.
        max_uses : :obj:`int`
            If specified, the max number of uses this invite can have, or ``0`` for 
            unlimited (as per the default).
        temporary : :obj:`bool`
            If specified, whether to grant temporary membership, meaning the user 
            is kicked when their session ends unless they are given a role.
        unique : :obj:`bool`
            If specified, whether to try to reuse a similar invite.
        target_user : :obj:`str`
            If specified, the ID of the user this invite should target.
        target_user_type : :obj:`int`
            If specified, the type of target for this invite.
        reason : :obj:`str`
            If specified, the audit log reason explaining why the operation 
            was performed.

        Returns
        -------
        :obj:`typing.Dict`
            An invite object.

        Raises
        ------
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you lack the ``CREATE_INSTANT_MESSAGES`` permission.
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the channel does not exist.
        :obj:`hikari.net.errors.BadRequestHTTPError`
            If the arguments provided are not valid (e.g. negative age, etc).
        """
        payload = {}
        transformations.put_if_specified(payload, "max_age", max_age)
        transformations.put_if_specified(payload, "max_uses", max_uses)
        transformations.put_if_specified(payload, "temporary", temporary)
        transformations.put_if_specified(payload, "unique", unique)
        transformations.put_if_specified(payload, "target_user", target_user)
        transformations.put_if_specified(payload, "target_user_type", target_user_type)
        route = routes.CHANNEL_INVITES.compile(self.POST, channel_id=channel_id)
        return await self._request(route, json_body=payload, reason=reason)

    async def delete_channel_permission(self, channel_id: str, overwrite_id: str) -> None:
        """Delete a channel permission overwrite for a user or a role in a channel.

        Parameters
        ----------
        channel_id : :obj:`str`
            The ID of the channel to delete the overwire from.
        overwrite_id : :obj:`str`
            The ID of the overwrite to remove.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the overwrite or channel do not exist.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you lack the ``MANAGE_ROLES`` permission for that channel.
        """
        route = routes.CHANNEL_PERMISSIONS.compile(self.DELETE, channel_id=channel_id, overwrite_id=overwrite_id)
        await self._request(route)

    async def trigger_typing_indicator(self, channel_id: str) -> None:
        """Trigger the account to appear to be typing for the next ``10`` seconds in the given channel.

        Parameters
        ----------
        channel_id : :obj:`str`
            The ID of the channel to appear to be typing in. This may be 
            a user ID if you wish to appear to be typing in DMs.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the channel is not found.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you are not able to type in the channel.
        """
        route = routes.CHANNEL_TYPING.compile(self.POST, channel_id=channel_id)
        await self._request(route)

    async def get_pinned_messages(self, channel_id: str) -> typing.Sequence[typing.Dict]:
        """Get pinned messages for a given channel.

        Parameters
        ----------
        channel_id : :obj:`str`
            The channel ID to get messages from.

        Returns
        -------
        :obj:`typing.Sequence` [ :obj:`typing.Dict` ]
            A list of messages.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the channel is not found.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you are not able to see the channel.

        Note
        ----
        If you are not able to see the pinned message (eg. you are missing ``READ_MESSAGE_HISTORY`` 
        and the pinned message is an old message), it will not be returned.
        """
        route = routes.CHANNEL_PINS.compile(self.GET, channel_id=channel_id)
        return await self._request(route)

    async def add_pinned_channel_message(self, channel_id: str, message_id: str) -> None:
        """Add a pinned message to the channel.

        Parameters
        ----------
        channel_id : :obj:`str`
            The ID of the channel to pin a message to.
        message_id : :obj:`str`
            The ID of the message to pin.

        Raises
        ------
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you lack the ``MANAGE_MESSAGES`` permission.
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the message or channel do not exist.
        """
        route = routes.CHANNEL_PINS.compile(self.PUT, channel_id=channel_id, message_id=message_id)
        await self._request(route)

    async def delete_pinned_channel_message(self, channel_id: str, message_id: str) -> None:
        """Remove a pinned message from the channel. 
        
        This will only unpin the message, not delete it.

        Parameters
        ----------
        channel_id : :obj:`str`
            The ID of the channel to remove a pin from.
        message_id : :obj:`str`
            The ID of the message to unpin.

        Raises
        ------
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you lack the ``MANAGE_MESSAGES`` permission.
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the message or channel do not exist.
        """
        route = routes.CHANNEL_PIN.compile(self.DELETE, channel_id=channel_id, message_id=message_id)
        await self._request(route)

    async def list_guild_emojis(self, guild_id: str) -> typing.Sequence[typing.Dict]:
        """Gets emojis for a given guild ID.

        Parameters
        ----------
        guild_id : :obj:`str`
            The ID of the guild to get the emojis for.

        Returns
        -------
        :obj:`typing.Sequence` [ :obj:`typing.Dict` ]
            A list of emoji objects.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you aren't a member of the guild.
        """
        route = routes.GUILD_EMOJIS.compile(self.GET, guild_id=guild_id)
        return await self._request(route)

    async def get_guild_emoji(self, guild_id: str, emoji_id: str) -> typing.Dict:
        """Gets an emoji from a given guild and emoji IDs.

        Parameters
        ----------
        guild_id : :obj:`str`
            The ID of the guild to get the emoji from.
        emoji_id : :obj:`str`
            The ID of the emoji to get.

        Returns
        -------
        :obj:`typing.Dict`
            An emoji object.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If either the guild or the emoji aren't found.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you aren't a member of said guild.
        """
        route = routes.GUILD_EMOJI.compile(self.GET, guild_id=guild_id, emoji_id=emoji_id)
        return await self._request(route)

    async def create_guild_emoji(
        self,
        guild_id: str,
        name: str,
        image: bytes,
        *,
        roles: typing.Union[typing.Literal[...], typing.Sequence[str]] = ...,
        reason: typing.Union[typing.Literal[...], str] = ...,
    ) -> typing.Dict:
        """Creates a new emoji for a given guild.

        Parameters
        ----------
        guild_id : :obj:`str`
            The ID of the guild to create the emoji in.
        name : :obj:`str`
            The new emoji's name.
        image : :obj:`bytes`
            The ``128x128`` image in bytes form.
        roles : :obj:`typing.Sequence` [ :obj:`str` ]
            If specified, a list of roles for which the emoji will be whitelisted. 
            If empty, all roles are whitelisted.
        reason : :obj:`str`
            If specified, the audit log reason explaining why the operation 
            was performed.

        Returns
        -------
        :obj:`typing.Dict`
            The newly created emoji object.

        Raises
        ------
        :obj:`ValueError`
            If ``image`` is ``None``.
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you either lack the ``MANAGE_EMOJIS`` permission or aren't a member of said guild.
        :obj:`hikari.net.errors.BadRequestHTTPError`
            If you attempt to upload an image larger than ``256kb``, an empty image or an invalid image format.
        """
        assertions.assert_not_none(image, "image must be a valid image")
        payload = {
            "name": name,
            "roles": [] if roles is ... else roles,
            "image": transformations.image_bytes_to_image_data(image),
        }
        route = routes.GUILD_EMOJIS.compile(self.POST, guild_id=guild_id)
        return await self._request(route, json_body=payload, reason=reason)

    async def modify_guild_emoji(
        self,
        guild_id: str,
        emoji_id: str,
        *,
        name: typing.Union[typing.Literal[...], str] = ...,
        roles: typing.Union[typing.Literal[...], typing.Sequence[str]] = ...,
        reason: typing.Union[typing.Literal[...], str] = ...,
    ) -> typing.Dict:
        """Edits an emoji of a given guild

        Parameters
        ----------
        guild_id : :obj:`str`
            The ID of the guild to which the edited emoji belongs to.
        emoji_id : :obj:`str`
            The ID of the edited emoji.
        name : :obj:`str`
            If specified, a new emoji name string. Keep unspecified to keep the name the same.
        roles : :obj:`typing.Sequence` [ :obj:`str` ]
            If specified, a list of IDs for the new whitelisted roles.
            Set to an empty list to whitelist all roles.
            Keep unspecified to leave the same roles already set.
        reason : :obj:`str`
            If specified, the audit log reason explaining why the operation 
            was performed.

        Returns
        -------
        :obj:`typing.Dict`
            The updated emoji object.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If either the guild or the emoji aren't found.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you either lack the ``MANAGE_EMOJIS`` permission or are not a member of the given guild.
        """
        payload = {}
        transformations.put_if_specified(payload, "name", name)
        transformations.put_if_specified(payload, "roles", roles)
        route = routes.GUILD_EMOJI.compile(self.PATCH, guild_id=guild_id, emoji_id=emoji_id)
        return await self._request(route, json_body=payload, reason=reason)

    async def delete_guild_emoji(self, guild_id: str, emoji_id: str) -> None:
        """Deletes an emoji from a given guild

        Parameters
        ----------
        guild_id : :obj:`str`
            The ID of the guild to delete the emoji from.
        emoji_id : :obj:`str`
            The ID of the emoji to be deleted.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If either the guild or the emoji aren't found.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you either lack the ``MANAGE_EMOJIS`` permission or aren't a member of said guild.
        """
        route = routes.GUILD_EMOJI.compile(self.DELETE, guild_id=guild_id, emoji_id=emoji_id)
        await self._request(route)

    async def create_guild(
        self,
        name: str,
        *,
        region: typing.Union[typing.Literal[...], str] = ...,
        icon: typing.Union[typing.Literal[...], bytes] = ...,
        verification_level: typing.Union[typing.Literal[...], int] = ...,
        default_message_notifications: typing.Union[typing.Literal[...], int] = ...,
        explicit_content_filter: typing.Union[typing.Literal[...], int] = ...,
        roles: typing.Union[typing.Literal[...], typing.Sequence[typing.Dict]] = ...,
        channels: typing.Union[typing.Literal[...], typing.Sequence[typing.Dict]] = ...,
    ) -> typing.Dict:
        """Creates a new guild. Can only be used by bots in less than ``10`` guilds.

        Parameters
        ----------
        name : :obj:`str`
            The name string for the new guild (``2-100`` characters).
        region : :obj:`str`
            If specified, the voice region ID for new guild. You can use 
            :meth:`list_voice_regions` to see which region IDs are available.
        icon : :obj:`bytes`
            If specified, the guild icon image in bytes form.
        verification_level : :obj:`int`
            If specified, the verification level integer (``0-5``).
        default_message_notifications : :obj:`int`
            If specified, the default notification level integer (``0-1``).
        explicit_content_filter : :obj:`int`
            If specified, the explicit content filter integer (``0-2``).
        roles : :obj:`typing.Sequence` [ :obj:`typing.Dict` ]
            If specified, an array of role objects to be created alongside the 
            guild. First element changes the ``@everyone`` role.
        channels : :obj:`typing.Sequence` [ :obj:`typing.Dict` ]
            If specified, an array of channel objects to be created alongside the guild.

        Returns
        -------
        :obj:`typing.Dict`
            The newly created guild object.

        Raises
        ------
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you are on ``10`` or more guilds.
        :obj:`hikari.net.errors.BadRequestHTTPError`
            If you provide unsupported fields like ``parent_id`` in channel objects.
        """
        payload = {"name": name}
        transformations.put_if_specified(payload, "region", region)
        transformations.put_if_specified(payload, "verification_level", verification_level)
        transformations.put_if_specified(payload, "default_message_notifications", default_message_notifications)
        transformations.put_if_specified(payload, "explicit_content_filter", explicit_content_filter)
        transformations.put_if_specified(payload, "roles", roles)
        transformations.put_if_specified(payload, "channels", channels)
        transformations.put_if_specified(payload, "icon", icon, transformations.image_bytes_to_image_data)
        route = routes.GUILDS.compile(self.POST)
        return await self._request(route, json_body=payload)

    async def get_guild(self, guild_id: str) -> typing.Dict:
        """Gets a given guild's object.

        Parameters
        ----------
        guild_id : :obj:`str`
            The ID of the guild to get.

        Returns
        -------
        :obj:`typing.Dict`
            The requested guild object.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you don't have access to the guild.
        """
        route = routes.GUILD.compile(self.GET, guild_id=guild_id)
        return await self._request(route)

    # pylint: disable=too-many-locals
    async def modify_guild(  # lgtm [py/similar-function]
        self,
        guild_id: str,
        *,
        name: typing.Union[typing.Literal[...], str] = ...,
        region: typing.Union[typing.Literal[...], str] = ...,
        verification_level: typing.Union[typing.Literal[...], int] = ...,
        default_message_notifications: typing.Union[typing.Literal[...], int] = ...,
        explicit_content_filter: typing.Union[typing.Literal[...], int] = ...,
        afk_channel_id: typing.Union[typing.Literal[...], str] = ...,
        afk_timeout: typing.Union[typing.Literal[...], int] = ...,
        icon: typing.Union[typing.Literal[...], bytes] = ...,
        owner_id: typing.Union[typing.Literal[...], str] = ...,
        splash: typing.Union[typing.Literal[...], bytes] = ...,
        system_channel_id: typing.Union[typing.Literal[...], str] = ...,
        reason: typing.Union[typing.Literal[...], str] = ...,
    ) -> typing.Dict:
        """Edits a given guild.

        Parameters
        ----------
        guild_id : :obj:`str`
            The ID of the guild to be edited.
        name : :obj:`str`
            If specified, the new name string for the guild (``2-100`` characters).
        region : :obj:`str`
            If specified, the new voice region ID for guild. You can use 
            :meth:`list_voice_regions` to see which region IDs are available.
        verification_level : :obj:`int`
            If specified, the new verification level integer (``0-5``).
        default_message_notifications : :obj:`int`
            If specified, the new default notification level integer (``0-1``).
        explicit_content_filter : :obj:`int`
            If specified, the new explicit content filter integer (``0-2``).
        afk_channel_id : :obj:`str`
            If specified, the new ID for the AFK voice channel.
        afk_timeout : :obj:`int`
            If specified, the new AFK timeout period in seconds
        icon : :obj:`bytes`
            If specified, the new guild icon image in bytes form.
        owner_id : :obj:`str`
            If specified, the new ID of the new guild owner.
        splash : :obj:`bytes`
            If specified, the new new splash image in bytes form.
        system_channel_id : :obj:`str`
            If specified, the new ID of the new system channel.
        reason : :obj:`str`
            If specified, the audit log reason explaining why the operation 
            was performed.

        Returns
        -------
        :obj:`typing.Dict`
            The edited guild object.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you lack the ``MANAGE_GUILD`` permission or are not in the guild.
        """
        payload = {}
        transformations.put_if_specified(payload, "name", name)
        transformations.put_if_specified(payload, "region", region)
        transformations.put_if_specified(payload, "verification_level", verification_level)
        transformations.put_if_specified(payload, "default_message_notifications", default_message_notifications)
        transformations.put_if_specified(payload, "explicit_content_filter", explicit_content_filter)
        transformations.put_if_specified(payload, "afk_channel_id", afk_channel_id)
        transformations.put_if_specified(payload, "afk_timeout", afk_timeout)
        transformations.put_if_specified(payload, "icon", icon, transformations.image_bytes_to_image_data)
        transformations.put_if_specified(payload, "owner_id", owner_id)
        transformations.put_if_specified(payload, "splash", splash, transformations.image_bytes_to_image_data)
        transformations.put_if_specified(payload, "system_channel_id", system_channel_id)
        route = routes.GUILD.compile(self.PATCH, guild_id=guild_id)
        return await self._request(route, json_body=payload, reason=reason)

    # pylint: enable=too-many-locals

    async def delete_guild(self, guild_id: str) -> None:
        """Permanently deletes the given guild. 
        
        You must be owner of the guild to perform this action.

        Parameters
        ----------
        guild_id : :obj:`str`
            The ID of the guild to be deleted.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you are not the guild owner.
        """
        route = routes.GUILD.compile(self.DELETE, guild_id=guild_id)
        await self._request(route)

    async def get_guild_channels(self, guild_id: str) -> typing.Sequence[typing.Dict]:
        """Gets all the channels for a given guild.

        Parameters
        ----------
        guild_id : :obj:`str`
            The ID of the guild to get the channels from.

        Returns
        -------
        :obj:`typing.Sequence` [ :obj:`typing.Dict` ]
            A list of channel objects.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you are not in the guild.
        """
        route = routes.GUILD_CHANNELS.compile(self.GET, guild_id=guild_id)
        return await self._request(route)

    async def create_guild_channel(
        self,
        guild_id: str,
        name: str,
        *,
        type_: typing.Union[typing.Literal[...], int] = ...,
        position: typing.Union[typing.Literal[...], int] = ...,
        topic: typing.Union[typing.Literal[...], str] = ...,
        nsfw: typing.Union[typing.Literal[...], bool] = ...,
        rate_limit_per_user: typing.Union[typing.Literal[...], int] = ...,
        bitrate: typing.Union[typing.Literal[...], int] = ...,
        user_limit: typing.Union[typing.Literal[...], int] = ...,
        permission_overwrites: typing.Union[typing.Literal[...], typing.Sequence[typing.Dict]] = ...,
        parent_id: typing.Union[typing.Literal[...], str] = ...,
        reason: typing.Union[typing.Literal[...], str] = ...,
    ) -> typing.Dict:
        """Creates a channel in a given guild.

        Parameters
        ----------
        guild_id:
            The ID of the guild to create the channel in.
        name : :obj:`str`
            If specified, the name for the channel.This must be 
            between ``2`` and ``100`` characters in length.
        type_: :obj:`int`
            If specified, the channel type integer (``0-6``).
        position : :obj:`int`
            If specified, the position to change the channel to.
        topic : :obj:`str`
            If specified, the topic to set. This is only applicable to 
            text channels. This must be between ``0`` and ``1024`` 
            characters in length.
        nsfw : :obj:`bool`
            If specified, whether the channel will be marked as NSFW. 
            Only applicable to text channels.
        rate_limit_per_user : :obj:`int`
            If specified, the number of seconds the user has to wait before sending 
            another message.  This will not apply to bots, or to members with 
            ``MANAGE_MESSAGES`` or ``MANAGE_CHANNEL`` permissions. This must 
            be between ``0`` and ``21600`` seconds.
        bitrate : :obj:`int`
            If specified, the bitrate in bits per second allowable for the channel. 
            This only applies to voice channels and must be between ``8000`` 
            and ``96000`` for normal servers or ``8000`` and ``128000`` for 
            VIP servers.
        user_limit : :obj:`int`
            If specified, the max number of users to allow in a voice channel. 
            This must be between ``0`` and ``99`` inclusive, where 
            ``0`` implies no limit.
        permission_overwrites : :obj:`typing.Sequence` [ :obj:`typing.Dict` ]
            If specified, the list of permission overwrites that are category 
            specific to replace the existing overwrites with.
        parent_id : :obj:`str`
            If specified, the parent category ID to set for the channel.
        reason : :obj:`str`
            If specified, the audit log reason explaining why the operation 
            was performed.

        Returns
        -------
        :obj:`typing.Dict`
            The newly created channel object.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you lack the ``MANAGE_CHANNEL`` permission or are not in the guild.
        :obj:`hikari.net.errors.BadRequestHTTPError`
            If you provide incorrect options for the corresponding channel type 
            (e.g. a ``bitrate`` for a text channel).
        """
        payload = {}
        transformations.put_if_specified(payload, "name", name)
        transformations.put_if_specified(payload, "type", type_)
        transformations.put_if_specified(payload, "position", position)
        transformations.put_if_specified(payload, "topic", topic)
        transformations.put_if_specified(payload, "nsfw", nsfw)
        transformations.put_if_specified(payload, "rate_limit_per_user", rate_limit_per_user)
        transformations.put_if_specified(payload, "bitrate", bitrate)
        transformations.put_if_specified(payload, "user_limit", user_limit)
        transformations.put_if_specified(payload, "permission_overwrites", permission_overwrites)
        transformations.put_if_specified(payload, "parent_id", parent_id)
        route = routes.GUILD_CHANNELS.compile(self.POST, guild_id=guild_id)
        return await self._request(route, json_body=payload, reason=reason)

    async def modify_guild_channel_positions(
        self, guild_id: str, channel: typing.Tuple[str, int], *channels: typing.Tuple[str, int]
    ) -> None:
        """Edits the position of one or more given channels.

        Parameters
        ----------
        guild_id : :obj:`str`
            The ID of the guild in which to edit the channels.
        channel : :obj:`typing.Tuple` [ :obj:`str`, :obj:`int` ]
            The first channel to change the position of. This is a tuple of the channel ID and the integer position.
        *channels : :obj:`typing.Tuple` [ :obj:`str`, :obj:`int` ]
            Optional additional channels to change the position of. These must be tuples of the channel ID and the
            integer positions to change to.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If either the guild or any of the channels aren't found.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you either lack the ``MANAGE_CHANNELS`` permission or are not a member of said guild or are not in
            the guild.
        :obj:`hikari.net.errors.BadRequestHTTPError`
            If you provide anything other than the ``id`` and ``position`` fields for the channels.
        """
        payload = [{"id": ch[0], "position": ch[1]} for ch in (channel, *channels)]
        route = routes.GUILD_CHANNELS.compile(self.PATCH, guild_id=guild_id)
        await self._request(route, json_body=payload)

    async def get_guild_member(self, guild_id: str, user_id: str) -> typing.Dict:
        """Gets a given guild member.

        Parameters
        ----------
        guild_id : :obj:`str`
            The ID of the guild to get the member from.
        user_id : :obj:`str`
            The ID of the member to get.
    
        Returns
        -------
        :obj:`typing.Dict`
            The requested member object.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If either the guild or the member aren't found.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you don't have access to the target guild.
        """
        route = routes.GUILD_MEMBER.compile(self.GET, guild_id=guild_id, user_id=user_id)
        return await self._request(route)

    async def list_guild_members(
        self,
        guild_id: str,
        *,
        limit: typing.Union[typing.Literal[...], int] = ...,
        after: typing.Union[typing.Literal[...], str] = ...,
    ) -> typing.Sequence[typing.Dict]:
        """Lists all members of a given guild.

        Parameters
        ----------
            guild_id : :obj:`str`
                The ID of the guild to get the members from.
            limit : :obj:`int`
                If specified, the maximum number of members to return. This has to be between 
                ``1`` and ``1000`` inclusive.
            after : :obj:`str`
                If specified, the highest ID in the previous page. This is used for retrieving more 
                than ``1000`` members in a server using consecutive requests.
                
        Example
        -------
            .. code-block:: python
                
                members = []
                last_id = 0
                
                while True:
                    next_members = await client.list_guild_members(1234567890, limit=1000, after=last_id)
                    members += next_members
                    
                    if len(next_members) == 1000:
                        last_id = next_members[-1]
                    else:
                        break                  

        Returns
        -------
        :obj:`typing.Dict`
            A list of member objects.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you are not in the guild.
        :obj:`hikari.net.errors.BadRequestHTTPError`
            If you provide invalid values for the ``limit`` or `after`` fields.
        """
        query = {}
        transformations.put_if_specified(query, "limit", limit)
        transformations.put_if_specified(query, "after", after)
        route = routes.GUILD_MEMBERS.compile(self.GET, guild_id=guild_id)
        return await self._request(route, query=query)

    async def modify_guild_member(  # lgtm [py/similar-function]
        self,
        guild_id: str,
        user_id: str,
        *,
        nick: typing.Optional[typing.Union[typing.Literal[...], str]] = ...,
        roles: typing.Union[typing.Literal[...], typing.Sequence[str]] = ...,
        mute: typing.Union[typing.Literal[...], bool] = ...,
        deaf: typing.Union[typing.Literal[...], bool] = ...,
        channel_id: typing.Optional[typing.Union[typing.Literal[...], str]] = ...,
        reason: typing.Union[typing.Literal[...], str] = ...,
    ) -> None:
        """Edits a member of a given guild.

        Parameters
        ----------
        guild_id : :obj:`str`
            The ID of the guild to edit the member from.
        user_id : :obj:`str`
            The ID of the member to edit.
        nick : :obj:`str`
            If specified, the new nickname string. Setting it to ``None`` explicitly 
            will clear the nickname.
        roles : :obj:`str`
            If specified, a list of role IDs the member should have.
        mute : :obj:`bool`
            If specified, whether the user should be muted in the voice channel or not.
        deaf : :obj:`bool`
            If specified, whether the user should be deafen in the voice channel or not.
        channel_id : :obj:`str`
            If specified, the ID of the channel to move the member to. Setting it to
            ``None`` explicitly will disconnect the user.
        reason : :obj:`str`
            If specified, the audit log reason explaining why the operation 
            was performed.
    
        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If either the guild, user, channel or any of the roles aren't found.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you lack any of the applicable permissions
            (``MANAGE_NICKNAMES``, ``MANAGE_ROLES``, ``MUTE_MEMBERS``, ``DEAFEN_MEMBERS`` or ``MOVE_MEMBERS``).
            Note that to move a member you must also have permission to connect to the end channel.
            This will also be raised if you're not in the guild.
        :obj:`hikari.net.errors.BadRequestHTTPError`
            If you pass ```mute``, ``deaf`` or ``channel_id`` while the member is not connected to a voice channel.
        """
        payload = {}
        transformations.put_if_specified(payload, "nick", nick)
        transformations.put_if_specified(payload, "roles", roles)
        transformations.put_if_specified(payload, "mute", mute)
        transformations.put_if_specified(payload, "deaf", deaf)
        transformations.put_if_specified(payload, "channel_id", channel_id)
        route = routes.GUILD_MEMBER.compile(self.PATCH, guild_id=guild_id, user_id=user_id)
        await self._request(route, json_body=payload, reason=reason)

    async def modify_current_user_nick(
        self, guild_id: str, nick: typing.Optional[str], *, reason: typing.Union[typing.Literal[...], str] = ...,
    ) -> None:
        """Edits the current user's nickname for a given guild.

        Parameters
        ----------
        guild_id : :obj:`str`
            The ID of the guild you want to change the nick on.
        nick : :obj:`str`, optional
            The new nick string. Setting this to `None` clears the nickname.
        reason : :obj:`str`
            If specified, the audit log reason explaining why the operation 
            was performed.
                
        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you lack the ``CHANGE_NICKNAME`` permission or are not in the guild.
        :obj:`hikari.net.errors.BadRequestHTTPError`
            If you provide a disallowed nickname, one that is too long, or one that is empty.
        """
        payload = {"nick": nick}
        route = routes.OWN_GUILD_NICKNAME.compile(self.PATCH, guild_id=guild_id)
        await self._request(route, json_body=payload, reason=reason)

    async def add_guild_member_role(
        self, guild_id: str, user_id: str, role_id: str, *, reason: typing.Union[typing.Literal[...], str] = ...,
    ) -> None:
        """Adds a role to a given member.

        Parameters
        ----------
        guild_id : :obj:`str`
            The ID of the guild the member belongs to.
        user_id : :obj:`str`
            The ID of the member you want to add the role to.
        role_id : :obj:`str`
            The ID of the role you want to add.
        reason : :obj:`str`
            If specified, the audit log reason explaining why the operation 
            was performed.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If either the guild, member or role aren't found.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you lack the ``MANAGE_ROLES`` permission or are not in the guild.
        """
        route = routes.GUILD_MEMBER_ROLE.compile(self.PUT, guild_id=guild_id, user_id=user_id, role_id=role_id)
        await self._request(route, reason=reason)

    async def remove_guild_member_role(
        self, guild_id: str, user_id: str, role_id: str, *, reason: typing.Union[typing.Literal[...], str] = ...,
    ) -> None:
        """Removed a role from a given member.

        Parameters
        ----------
        guild_id : :obj:`str`
            The ID of the guild the member belongs to.
        user_id : :obj:`str`
            The ID of the member you want to remove the role from.
        role_id : :obj:`str`
            The ID of the role you want to remove.
        reason : :obj:`str`
            If specified, the audit log reason explaining why the operation 
            was performed.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If either the guild, member or role aren't found.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you lack the ``MANAGE_ROLES`` permission or are not in the guild.
        """
        route = routes.GUILD_MEMBER_ROLE.compile(self.DELETE, guild_id=guild_id, user_id=user_id, role_id=role_id)
        await self._request(route, reason=reason)

    async def remove_guild_member(
        self, guild_id: str, user_id: str, *, reason: typing.Union[typing.Literal[...], str] = ...,
    ) -> None:
        """Kicks a user from a given guild.

        Parameters
        ----------
        guild_id: :obj:`str`
            The ID of the guild the member belongs to.
        user_id: :obj:`str`
            The ID of the member you want to kick.
        reason : :obj:`str`
            If specified, the audit log reason explaining why the operation 
            was performed.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If either the guild or member aren't found.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you lack the ``KICK_MEMBERS`` permission or are not in the guild.
        """
        route = routes.GUILD_MEMBER.compile(self.DELETE, guild_id=guild_id, user_id=user_id)
        await self._request(route, reason=reason)

    async def get_guild_bans(self, guild_id: str) -> typing.Sequence[typing.Dict]:
        """Gets the bans for a given guild.

        Parameters
        ----------
        guild_id : :obj:`str`
            The ID of the guild you want to get the bans from.

        Returns
        -------
        :obj:`typing.Sequence` [ :obj:`typing.Dict` ]
            A list of ban objects.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you lack the ``BAN_MEMBERS`` permission or are not in the guild.
        """
        route = routes.GUILD_BANS.compile(self.GET, guild_id=guild_id)
        return await self._request(route)

    async def get_guild_ban(self, guild_id: str, user_id: str) -> typing.Dict:
        """Gets a ban from a given guild.

        Parameters
        ----------
        guild_id : :obj:`str`
            The ID of the guild you want to get the ban from.
        user_id : :obj:`str`
            The ID of the user to get the ban information for.

        Returns
        -------
        :obj:`typing.Dict`
            A ban object for the requested user.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If either the guild or the user aren't found, or if the user is not banned.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you lack the ``BAN_MEMBERS`` permission or are not in the guild.
        """
        route = routes.GUILD_BAN.compile(self.GET, guild_id=guild_id, user_id=user_id)
        return await self._request(route)

    async def create_guild_ban(
        self,
        guild_id: str,
        user_id: str,
        *,
        delete_message_days: typing.Union[typing.Literal[...], int] = ...,
        reason: typing.Union[typing.Literal[...], str] = ...,
    ) -> None:
        """Bans a user from a given guild.

        Parameters
        ----------
        guild_id : :obj:`str`
            The ID of the guild the member belongs to.
        user_id : :obj:`str`
            The ID of the member you want to ban.
        delete_message_days : :obj:`str`
            If specified, how many days of messages from the user should 
            be removed.
        reason : :obj:`str`
            If specified, the audit log reason explaining why the operation 
            was performed.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If either the guild or member aren't found.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you lack the ``BAN_MEMBERS`` permission or are not in the guild.
        """
        query = {}
        transformations.put_if_specified(query, "delete-message-days", delete_message_days)
        transformations.put_if_specified(query, "reason", reason)
        route = routes.GUILD_BAN.compile(self.PUT, guild_id=guild_id, user_id=user_id)
        await self._request(route, query=query)

    async def remove_guild_ban(
        self, guild_id: str, user_id: str, *, reason: typing.Union[typing.Literal[...], str] = ...,
    ) -> None:
        """Un-bans a user from a given guild.

        Parameters
        ----------
        guild_id : :obj:`str`
            The ID of the guild to un-ban the user from.
        user_id : :obj:`str`
            The ID of the user you want to un-ban.
        reason : :obj:`str`
            If specified, the audit log reason explaining why the operation 
            was performed.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If either the guild or member aren't found, or the member is not banned.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you lack the ``BAN_MEMBERS`` permission or are not a in the guild.
        """
        route = routes.GUILD_BAN.compile(self.DELETE, guild_id=guild_id, user_id=user_id)
        await self._request(route, reason=reason)

    async def get_guild_roles(self, guild_id: str) -> typing.Sequence[typing.Dict]:
        """Gets the roles for a given guild.

        Parameters
        ----------
        guild_id : :obj:`str`
            The ID of the guild you want to get the roles from.

        Returns
        -------
        :obj:`typing.Sequence` [ :obj:`typing.Dict` ]
            A list of role objects.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you're not in the guild.
        """
        route = routes.GUILD_ROLES.compile(self.GET, guild_id=guild_id)
        return await self._request(route)

    async def create_guild_role(
        self,
        guild_id: str,
        *,
        name: typing.Union[typing.Literal[...], str] = ...,
        permissions: typing.Union[typing.Literal[...], int] = ...,
        color: typing.Union[typing.Literal[...], int] = ...,
        hoist: typing.Union[typing.Literal[...], bool] = ...,
        mentionable: typing.Union[typing.Literal[...], bool] = ...,
        reason: typing.Union[typing.Literal[...], str] = ...,
    ) -> typing.Dict:
        """Creates a new role for a given guild.

        Parameters
        ----------
        guild_id : :obj:`str`
            The ID of the guild you want to create the role on.
        name : :obj:`str`
            If specified, the new role name string.
        permissions : :obj:`int`
            If specified, the permissions integer for the role.
        color : :obj:`int`
            If specified, the color for the role.
        hoist : :obj:`bool`
            If specified, whether the role will be hoisted.
        mentionable : :obj:`bool`
           If specified, whether the role will be able to be mentioned by any user.
        reason : :obj:`str`
            If specified, the audit log reason explaining why the operation 
            was performed.

        Returns
        -------
        :obj:`typing.Dict`
            The newly created role object.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you lack the ``MANAGE_ROLES`` permission or you're not in the guild.
        :obj:`hikari.net.errors.BadRequestHTTPError`
            If you provide invalid values for the role attributes.
        """
        payload = {}
        transformations.put_if_specified(payload, "name", name)
        transformations.put_if_specified(payload, "permissions", permissions)
        transformations.put_if_specified(payload, "color", color)
        transformations.put_if_specified(payload, "hoist", hoist)
        transformations.put_if_specified(payload, "mentionable", mentionable)
        route = routes.GUILD_ROLES.compile(self.POST, guild_id=guild_id)
        return await self._request(route, json_body=payload, reason=reason)

    async def modify_guild_role_positions(
        self, guild_id: str, role: typing.Tuple[str, int], *roles: typing.Tuple[str, int]
    ) -> typing.Sequence[typing.Dict]:
        """Edits the position of two or more roles in a given guild.

        Parameters
        ----------
        guild_id:
            The ID of the guild the roles belong to.
        role:
            The first role to move.
        *roles:
            Optional extra roles to move.

        Returns
        -------
        :obj:`typing.Sequence` [ :obj:`typing.Dict` ]
            A list of all the guild roles.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If either the guild or any of the roles aren't found.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you lack the ``MANAGE_ROLES`` permission or you're not in the guild.
        :obj:`hikari.net.errors.BadRequestHTTPError`
            If you provide invalid values for the `position` fields.
        """
        payload = [{"id": r[0], "position": r[1]} for r in (role, *roles)]
        route = routes.GUILD_ROLES.compile(self.PATCH, guild_id=guild_id)
        return await self._request(route, json_body=payload)

    async def modify_guild_role(  # lgtm [py/similar-function]
        self,
        guild_id: str,
        role_id: str,
        *,
        name: typing.Union[typing.Literal[...], str] = ...,
        permissions: typing.Union[typing.Literal[...], int] = ...,
        color: typing.Union[typing.Literal[...], int] = ...,
        hoist: typing.Union[typing.Literal[...], bool] = ...,
        mentionable: typing.Union[typing.Literal[...], bool] = ...,
        reason: typing.Union[typing.Literal[...], str] = ...,
    ) -> typing.Dict:
        """Edits a role in a given guild.

        Parameters
        ----------
        guild_id : :obj:`str`
            The ID of the guild the role belong to.
        role_id : :obj:`str`
            The ID of the role you want to edit.
        name : :obj:`str`
            If specified, the new role's name string.
        permissions : :obj:`int`
            If specified, the new permissions integer for the role.
        color : :obj:`int`
            If specified, the new color for the new role.
        hoist : :obj:`bool`
            If specified, whether the role should hoist or not.
        mentionable : :obj:`bool`
            If specified, whether the role should be mentionable or not.
        reason : :obj:`str`
            If specified, the audit log reason explaining why the operation 
            was performed.
                
        Returns
        -------
        :obj:`typing.Dict`
            The edited role object.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If either the guild or role aren't found.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you lack the ``MANAGE_ROLES`` permission or you're not in the guild.
        :obj:`hikari.net.errors.BadRequestHTTPError`
            If you provide invalid values for the role attributes.
        """
        payload = {}
        transformations.put_if_specified(payload, "name", name)
        transformations.put_if_specified(payload, "permissions", permissions)
        transformations.put_if_specified(payload, "color", color)
        transformations.put_if_specified(payload, "hoist", hoist)
        transformations.put_if_specified(payload, "mentionable", mentionable)
        route = routes.GUILD_ROLE.compile(self.PATCH, guild_id=guild_id, role_id=role_id)
        return await self._request(route, json_body=payload, reason=reason)

    async def delete_guild_role(self, guild_id: str, role_id: str) -> None:
        """Deletes a role from a given guild.

        Parameters
        ----------
        guild_id : :obj:`str`
            The ID of the guild you want to remove the role from.
        role_id : :obj:`str`
            The ID of the role you want to delete.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If either the guild or the role aren't found.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you lack the ``MANAGE_ROLES`` permission or are not in the guild.
        """
        route = routes.GUILD_ROLE.compile(self.DELETE, guild_id=guild_id, role_id=role_id)
        await self._request(route)

    async def get_guild_prune_count(self, guild_id: str, days: int) -> int:
        """Gets the estimated prune count for a given guild.

        Parameters
        ----------
        guild_id : :obj:`str`
            The ID of the guild you want to get the count for.
        days : :obj:`int`
            The number of days to count prune for (at least ``1``).

        Returns
        -------
        :obj:`int`
            The number of members estimated to be pruned.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you lack the ``KICK_MEMBERS`` or you are not in the guild.
        :obj:`hikari.net.errors.BadRequestHTTPError`
            If you pass an invalid amount of days.
        """
        payload = {"days": days}
        route = routes.GUILD_PRUNE.compile(self.GET, guild_id=guild_id)
        result = await self._request(route, query=payload)
        return int(result["pruned"])

    async def begin_guild_prune(
        self,
        guild_id: str,
        days: int,
        *,
        compute_prune_count: typing.Union[typing.Literal[...], bool] = ...,
        reason: typing.Union[typing.Literal[...], str] = ...,
    ) -> typing.Optional[int]:
        """Prunes members of a given guild based on the number of inactive days.

        Parameters
        ----------
        guild_id : :obj:`str`
            The ID of the guild you want to prune member of.
        days : :obj:`int`
            The number of inactivity days you want to use as filter.
        compute_prune_count : :obj:`bool`
            Whether a count of pruned members is returned or not. 
            Discouraged for large guilds out of politeness.
        reason : :obj:`str`
            If specified, the audit log reason explaining why the operation 
            was performed.

        Returns
        -------
        :obj:`int`, optional
            The number of members who were kicked if ``compute_prune_count`` 
            is ``True``, else ``None``.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the guild is not found:
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you lack the ``KICK_MEMBER`` permission or are not in the guild.
        :obj:`hikari.net.errors.BadRequestHTTPError`
            If you provide invalid values for the ``days`` or ``compute_prune_count`` fields.
        """
        query = {"days": days}
        transformations.put_if_specified(query, "compute_prune_count", compute_prune_count, str)
        route = routes.GUILD_PRUNE.compile(self.POST, guild_id=guild_id)
        result = await self._request(route, query=query, reason=reason)

        try:
            return int(result["pruned"])
        except (TypeError, KeyError):
            return None

    async def get_guild_voice_regions(self, guild_id: str) -> typing.Sequence[typing.Dict]:
        """Gets the voice regions for a given guild.

        Parameters
        ----------
        guild_id : :obj:`str`
            The ID of the guild to get the voice regions for.

        Returns
        -------
        :obj:`typing.Sequence` [ :obj:`typing.Dict` ]
            A list of voice region objects.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you are not in the guild.
        """
        route = routes.GUILD_VOICE_REGIONS.compile(self.GET, guild_id=guild_id)
        return await self._request(route)

    async def get_guild_invites(self, guild_id: str) -> typing.Sequence[typing.Dict]:
        """Gets the invites for a given guild.

        Parameters
        ----------
        guild_id : :obj:`str`
            The ID of the guild to get the invites for.

        Returns
        -------
        :obj:`typing.Sequence` [ :obj:`typing.Dict` ]
            A list of invite objects (with metadata).

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you lack the ``MANAGE_GUILD`` permission or are not in the guild.
        """
        route = routes.GUILD_INVITES.compile(self.GET, guild_id=guild_id)
        return await self._request(route)

    async def get_guild_integrations(self, guild_id: str) -> typing.Sequence[typing.Dict]:
        """Gets the integrations for a given guild.

        Parameters
        ----------
        guild_id:
            The ID of the guild to get the integrations for.

        Returns
        -------
        :obj:`typing.Sequence` [ :obj:`typing.Dict` ]
            A list of integration objects.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you lack the ``MANAGE_GUILD`` permission or are not in the guild.
        """
        route = routes.GUILD_INTEGRATIONS.compile(self.GET, guild_id=guild_id)
        return await self._request(route)

    async def create_guild_integration(
        self, guild_id: str, type_: str, integration_id: str, *, reason: typing.Union[typing.Literal[...], str] = ...,
    ) -> typing.Dict:
        """Creates an integrations for a given guild.

        Parameters
        ----------
        guild_id : :obj:`str`
            The ID of the guild to create the integrations in.
        type_ : :obj:`str`
            The integration type string (e.g. "twitch" or "youtube").
        integration_id : :obj:`str`
            The ID for the new integration.
        reason : :obj:`str`
            If specified, the audit log reason explaining why the operation 
            was performed.

        Returns
        -------
        :obj:`typing.Dict`
            The newly created integration object.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you lack the ``MANAGE_GUILD`` permission or are not in the guild.
        """
        payload = {"type": type_, "id": integration_id}
        route = routes.GUILD_INTEGRATIONS.compile(self.POST, guild_id=guild_id)
        return await self._request(route, json_body=payload, reason=reason)

    async def modify_guild_integration(
        self,
        guild_id: str,
        integration_id: str,
        *,
        expire_behaviour: typing.Union[typing.Literal[...], int] = ...,
        expire_grace_period: typing.Union[typing.Literal[...], int] = ...,
        enable_emojis: typing.Union[typing.Literal[...], bool] = ...,
        reason: typing.Union[typing.Literal[...], str] = ...,
    ) -> None:
        """Edits an integrations for a given guild.

        Parameters
        ----------
        guild_id : :obj:`str`
            The ID of the guild to which the integration belongs to.
        integration_id : :obj:`str`
            The ID of the integration.
        expire_behaviour : :obj:`int`
            If specified, the behaviour for when an integration subscription 
            lapses.
        expire_grace_period : :obj:`int`
            If specified, time interval in seconds in which the integration 
            will ignore lapsed subscriptions.
        enable_emojis : :obj:`bool`
            If specified, whether emojis should be synced for this integration.
        reason : :obj:`str`
            If specified, the audit log reason explaining why the operation 
            was performed.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If either the guild or the integration aren't found.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you lack the ``MANAGE_GUILD`` permission or are not in the guild.
        """
        payload = {}
        transformations.put_if_specified(payload, "expire_behaviour", expire_behaviour)
        transformations.put_if_specified(payload, "expire_grace_period", expire_grace_period)
        # This is inconsistently named in their API.
        transformations.put_if_specified(payload, "enable_emoticons", enable_emojis)
        route = routes.GUILD_INTEGRATION.compile(self.PATCH, guild_id=guild_id, integration_id=integration_id)
        await self._request(route, json_body=payload, reason=reason)

    async def delete_guild_integration(
        self, guild_id: str, integration_id: str, *, reason: typing.Union[typing.Literal[...], str] = ...,
    ) -> None:
        """Deletes an integration for the given guild.

        Parameters
        ----------
        guild_id : :obj:`str`
            The ID of the guild to which the integration belongs to.
        integration_id : :obj:`str`
            The ID of the integration to delete.
        reason : :obj:`str`
            If specified, the audit log reason explaining why the operation 
            was performed.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
                If either the guild or the integration aren't found.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
                If you lack the `MANAGE_GUILD` permission or are not in the guild.
        """
        route = routes.GUILD_INTEGRATION.compile(self.DELETE, guild_id=guild_id, integration_id=integration_id)
        await self._request(route, reason=reason)

    async def sync_guild_integration(self, guild_id: str, integration_id: str) -> None:
        """Syncs the given integration.

        Parameters
        ----------
        guild_id : :obj:`str`
            The ID of the guild to which the integration belongs to.
        integration_id : :obj:`str`
            The ID of the integration to sync.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If either the guild or the integration aren't found.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you lack the ``MANAGE_GUILD`` permission or are not in the guild.
        """
        route = routes.GUILD_INTEGRATION_SYNC.compile(self.POST, guild_id=guild_id, integration_id=integration_id)
        await self._request(route)

    async def get_guild_embed(self, guild_id: str) -> typing.Dict:
        """Gets the embed for a given guild.

        Parameters
        ----------
        guild_id : :obj:`str`
            The ID of the guild to get the embed for.

        Returns
        -------
        :obj:`typing.Dict`
            A guild embed object.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you either lack the ``MANAGE_GUILD`` permission or are not in the guild.
        """
        route = routes.GUILD_EMBED.compile(self.GET, guild_id=guild_id)
        return await self._request(route)

    async def modify_guild_embed(
        self, guild_id: str, embed: typing.Dict, *, reason: typing.Union[typing.Literal[...], str] = ...,
    ) -> typing.Dict:
        """Edits the embed for a given guild.

        Parameters
        ----------
        guild_id : :obj:`str`
            The ID of the guild to edit the embed for.
        embed : :obj:`typing.Dict`
            The new embed object to be set.
        reason : :obj:`str`
            If specified, the audit log reason explaining why the operation 
            was performed.

        Returns
        -------
        :obj:`typing.Dict`
            The updated embed object.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you either lack the ``MANAGE_GUILD`` permission or are not in the guild.
        """
        route = routes.GUILD_EMBED.compile(self.PATCH, guild_id=guild_id)
        return await self._request(route, json_body=embed, reason=reason)

    async def get_guild_vanity_url(self, guild_id: str) -> typing.Dict:
        """
        Gets the vanity URL for a given guild.

        Parameters
        ----------
        guild_id : :obj:`str`
            The ID of the guild to get the vanity URL for.

        Returns
        -------
        :obj:`typing.Dict`
            A partial invite object containing the vanity URL in the ``code`` field.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you either lack the ``MANAGE_GUILD`` permission or are not in the guild.
        """
        route = routes.GUILD_VANITY_URL.compile(self.GET, guild_id=guild_id)
        return await self._request(route)

    def get_guild_widget_image_url(self, guild_id: str, *, style: typing.Union[typing.Literal[...], str] = ...,) -> str:
        """Get the URL for a guild widget.

        Parameters
        ----------
        guild_id : :obj:`str`
            The guild ID to use for the widget.
        style : :obj:`str`
            If specified, the syle of the widget.

        Returns
        -------
        :obj:`str`
            A URL to retrieve a PNG widget for your guild.

        Note
        ----
        This does not actually make any form of request, and shouldn't be awaited. 
        Thus, it doesn't have rate limits either.

        Warning
        -------
        The guild must have the widget enabled in the guild settings for this to be valid.
        """
        query = "" if style is ... else f"?style={style}"
        return f"{self.base_url}/guilds/{guild_id}/widget.png" + query

    async def get_invite(
        self, invite_code: str, *, with_counts: typing.Union[typing.Literal[...], bool] = ...
    ) -> typing.Dict:
        """Gets the given invite.

        Parameters
        ----------
        invite_code : :str:
            The ID for wanted invite.
        with_counts : :bool:
            If specified, wheter to attempt to count the number of 
            times the invite has been used.

        Returns
        -------
        :obj:`typing.Dict`
            The requested invite object.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the invite is not found.
        """
        query = {}
        transformations.put_if_specified(query, "with_counts", with_counts, str)
        route = routes.INVITE.compile(self.GET, invite_code=invite_code)
        return await self._request(route, query=query)

    async def delete_invite(self, invite_code: str) -> None:
        """Deletes a given invite.

        Parameters
        ----------
        invite_code : :obj:`str`
            The ID for the invite to be deleted.

        Returns
        -------
        ``None`` # Marker
            Nothing, unlike what the API specifies. This is done to maintain 
            consistency with other calls of a similar nature in this API wrapper.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the invite is not found.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you lack either ``MANAGE_CHANNELS`` on the channel the invite 
            belongs to or ``MANAGE_GUILD`` for guild-global delete.
        """
        route = routes.INVITE.compile(self.DELETE, invite_code=invite_code)
        return await self._request(route)

    async def get_current_user(self) -> typing.Dict:
        """Gets the current user that is represented by token given to the client.

        Returns
        -------
        :obj:`typing.Dict`
            The current user object.
        """
        route = routes.OWN_USER.compile(self.GET)
        return await self._request(route)

    async def get_user(self, user_id: str) -> typing.Dict:
        """Gets a given user.

        Parameters
        ----------
        user_id : :obj:`str`
            The ID of the user to get.

        Returns
        -------
        :obj:`typing.Dict`
            The requested user object.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the user is not found.
        """
        route = routes.USER.compile(self.GET, user_id=user_id)
        return await self._request(route)

    async def modify_current_user(
        self,
        *,
        username: typing.Union[typing.Literal[...], str] = ...,
        avatar: typing.Optional[typing.Union[typing.Literal[...], bytes]] = ...,
    ) -> typing.Dict:
        """Edits the current user.

        Parameters
        ----------
        username : :obj:`str`
            If specified, the new username string.
        avatar : :obj:`bytes`
            If specified, the new avatar image in bytes form. 
            If it is ``None``, the avatar is removed.

        Returns
        -------
        :obj:`typing.Dict`
            The updated user object.

        Raises
        ------
        :obj:`hikari.net.errors.BadRequestHTTPError`
            If you pass username longer than the limit (``2-32``) or an invalid image.
        """
        payload = {}
        transformations.put_if_specified(payload, "username", username)
        transformations.put_if_specified(payload, "avatar", avatar, transformations.image_bytes_to_image_data)
        route = routes.OWN_USER.compile(self.PATCH)
        return await self._request(route, json_body=payload)

    async def get_current_user_connections(self) -> typing.Sequence[typing.Dict]:
        """
        Gets the current user's connections. This endpoint can be 
        used with both ``Bearer`` and ``Bot`` tokens but will usually return an 
        empty list for bots (with there being some exceptions to this, like 
        user accounts that have been converted to bots).

        Returns
        -------
        :obj:`typing.Sequence` [ :obj:`typing.Dict` ]
            A list of connection objects.
        """
        route = routes.OWN_CONNECTIONS.compile(self.GET)
        return await self._request(route)

    async def get_current_user_guilds(
        self,
        *,
        before: typing.Union[typing.Literal[...], str] = ...,
        after: typing.Union[typing.Literal[...], str] = ...,
        limit: typing.Union[typing.Literal[...], int] = ...,
    ) -> typing.Sequence[typing.Dict]:
        """Gets the guilds the current user is in.

        Parameters
        ----------
        before : :obj:`str`
            If specified, the guild ID to get guilds before it.

        after : :obj:`str`
            If specified, the guild ID to get guilds after it.

        limit : :obj:`int`
            If specified, the limit of guilds to get. Has to be between
            ``1`` and ``100``.

        Returns
        -------
        :obj:`typing.Sequence` [ :obj:`typing.Dict` ]
            A list of partial guild objects.

        Raises
        ------
        :obj:`hikari.net.errors.BadRequestHTTPError`
            If you pass both ``before`` and ``after`` or an 
            invalid value for ``limit``.
        """
        query = {}
        transformations.put_if_specified(query, "before", before)
        transformations.put_if_specified(query, "after", after)
        transformations.put_if_specified(query, "limit", limit)
        route = routes.OWN_GUILDS.compile(self.GET)
        return await self._request(route, query=query)

    async def leave_guild(self, guild_id: str) -> None:
        """Makes the current user leave a given guild.

        Parameters
        ----------
        guild_id : :obj:`str`
            The ID of the guild to leave.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the guild is not found.
        """
        route = routes.LEAVE_GUILD.compile(self.DELETE, guild_id=guild_id)
        await self._request(route)

    async def create_dm(self, recipient_id: str) -> typing.Dict:
        """Creates a new DM channel with a given user.

        Parameters
        ----------
        recipient_id : :obj:`str`
            The ID of the user to create the new DM channel with.

        Returns
        -------
        :obj:`typing.Dict`
            The newly created DM channel object.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the recipient is not found.
        """
        payload = {"recipient_id": recipient_id}
        route = routes.OWN_DMS.compile(self.POST)
        return await self._request(route, json_body=payload)

    async def list_voice_regions(self) -> typing.Sequence[typing.Dict]:
        """Get the voice regions that are available.

        Returns
        -------
        :obj:`typing.Sequence` [ :obj:`typing.Dict` ]
            A list of voice regions available

        Note
        ----
        This does not include VIP servers.
        """
        route = routes.VOICE_REGIONS.compile(self.GET)
        return await self._request(route)

    async def create_webhook(
        self,
        channel_id: str,
        name: str,
        *,
        avatar: typing.Union[typing.Literal[...], bytes] = ...,
        reason: typing.Union[typing.Literal[...], str] = ...,
    ) -> typing.Dict:
        """
        Creates a webhook for a given channel.

        Parameters
        ----------
        channel_id : :obj:`str`
            The ID of the channel for webhook to be created in.
        name : :obj:`str`
            The webhook's name string.
        avatar : :obj:`bytes`
            If specified, the avatar image in bytes form.
        reason : :obj:`str`
            If specified, the audit log reason explaining why the operation 
            was performed.

        Returns
        -------
        :obj:`typing.Dict`
            The newly created webhook object.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the channel is not found.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you either lack the ``MANAGE_WEBHOOKS`` permission or 
            can not see the given channel.
        :obj:`hikari.net.errors.BadRequestHTTPError`
            If the avatar image is too big or the format is invalid.
        """
        payload = {"name": name}
        transformations.put_if_specified(payload, "avatar", avatar, transformations.image_bytes_to_image_data)
        route = routes.CHANNEL_WEBHOOKS.compile(self.POST, channel_id=channel_id)
        return await self._request(route, json_body=payload, reason=reason)

    async def get_channel_webhooks(self, channel_id: str) -> typing.Sequence[typing.Dict]:
        """Gets all webhooks from a given channel.

        Parameters
        ----------
        channel_id : :obj:`str`
            The ID of the channel to get the webhooks from.

        Returns
        -------
        :obj:`typing.Sequence` [ :obj:`typing.Dict` ]
            A list of webhook objects for the give channel.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the channel is not found.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you either lack the ``MANAGE_WEBHOOKS`` permission or 
            can not see the given channel.
        """
        route = routes.CHANNEL_WEBHOOKS.compile(self.GET, channel_id=channel_id)
        return await self._request(route)

    async def get_guild_webhooks(self, guild_id: str) -> typing.Sequence[typing.Dict]:
        """Gets all webhooks for a given guild.

        Parameters
        ----------
        guild_id : :obj:`str`
            The ID for the guild to get the webhooks from.

        Returns
        -------
        :obj:`typing.Sequence` [ :obj:`typing.Dict` ]
            A list of webhook objects for the given guild.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you either lack the ``MANAGE_WEBHOOKS`` permission or 
            aren't a member of the given guild.
        """
        route = routes.GUILD_WEBHOOKS.compile(self.GET, guild_id=guild_id)
        return await self._request(route)

    async def get_webhook(
        self, webhook_id: str, *, webhook_token: typing.Union[typing.Literal[...], str] = ...
    ) -> typing.Dict:
        """Gets a given webhook.

        Parameters
        ----------
        webhook_id : :obj:`str`
            The ID of the webhook to get.
        webhook_token : :obj:`str`
            If specified, the webhook token to use to get it (bypassing bot authorization).

        Returns
        -------
        :obj:`typing.Dict`
            The requested webhook object.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the webhook is not found.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you're not in the guild that owns this webhook or 
            lack the ``MANAGE_WEBHOOKS`` permission.
        :obj:`hikari.net.errors.UnauthorizedHTTPError`
            If you pass a token that's invalid for the target webhook.
        """
        if webhook_token is ...:
            route = routes.WEBHOOK.compile(self.GET, webhook_id=webhook_id)
        else:
            route = routes.WEBHOOK_WITH_TOKEN.compile(self.GET, webhook_id=webhook_id, webhook_token=webhook_token)
        return await self._request(route, suppress_authorization_header=webhook_token is not ...)

    async def modify_webhook(
        self,
        webhook_id: str,
        *,
        webhook_token: typing.Union[typing.Literal[...], str] = ...,
        name: typing.Union[typing.Literal[...], str] = ...,
        avatar: typing.Optional[typing.Union[typing.Literal[...], bytes]] = ...,
        channel_id: typing.Union[typing.Literal[...], str] = ...,
        reason: typing.Union[typing.Literal[...], str] = ...,
    ) -> typing.Dict:
        """Edits a given webhook.

        Parameters
        ----------
        webhook_id : :obj:`str`
            The ID of the webhook to edit.
        webhook_token : :obj:`str`
            If specified, the webhook token to use to modify it (bypassing bot authorization).
        name : :obj:`str`
            If specified, the new name string.
        avatar : :obj:`bytes`
            If specified, the new avatar image in bytes form. If None, then
            it is removed.
        channel_id : :obj:`str`
            If specified, the ID of the new channel the given 
            webhook should be moved to.
        reason : :obj:`str`
            If specified, the audit log reason explaining why the operation 
            was performed.

        Returns
        -------
        :obj:`typing.Dict`
            The updated webhook object.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If either the webhook or the channel aren't found.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you either lack the ``MANAGE_WEBHOOKS`` permission or 
            aren't a member of the guild this webhook belongs to.
        :obj:`hikari.net.errors.UnauthorizedHTTPError`
            If you pass a token that's invalid for the target webhook.
        """
        payload = {}
        transformations.put_if_specified(payload, "name", name)
        transformations.put_if_specified(payload, "channel_id", channel_id)
        transformations.put_if_specified(payload, "avatar", avatar, transformations.image_bytes_to_image_data)
        if webhook_token is ...:
            route = routes.WEBHOOK.compile(self.PATCH, webhook_id=webhook_id)
        else:
            route = routes.WEBHOOK_WITH_TOKEN.compile(self.PATCH, webhook_id=webhook_id, webhook_token=webhook_token)
        return await self._request(
            route, json_body=payload, reason=reason, suppress_authorization_header=webhook_token is not ...,
        )

    async def delete_webhook(
        self, webhook_id: str, *, webhook_token: typing.Union[typing.Literal[...], str] = ...
    ) -> None:
        """Deletes a given webhook.

        Parameters
        ----------
        webhook_id : :obj:`str`
            The ID of the webhook to delete
        webhook_token : :obj:`str`
            If specified, the webhook token to use to 
            delete it (bypassing bot authorization).

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the webhook is not found.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you either lack the ``MANAGE_WEBHOOKS`` permission or 
            aren't a member of the guild this webhook belongs to.
        :obj:`hikari.net.errors.UnauthorizedHTTPError`
                If you pass a token that's invalid for the target webhook.
        """
        if webhook_token is ...:
            route = routes.WEBHOOK.compile(self.DELETE, webhook_id=webhook_id)
        else:
            route = routes.WEBHOOK_WITH_TOKEN.compile(self.DELETE, webhook_id=webhook_id, webhook_token=webhook_token)
        await self._request(route, suppress_authorization_header=webhook_token is not ...)

    async def execute_webhook(
        self,
        webhook_id: str,
        webhook_token: str,
        *,
        content: typing.Union[typing.Literal[...], str] = ...,
        username: typing.Union[typing.Literal[...], str] = ...,
        avatar_url: typing.Union[typing.Literal[...], str] = ...,
        tts: typing.Union[typing.Literal[...], bool] = ...,
        wait: typing.Union[typing.Literal[...], bool] = ...,
        file: typing.Union[typing.Literal[...], typing.Tuple[str, storage.FileLikeT]] = ...,
        embeds: typing.Union[typing.Literal[...], typing.Sequence[typing.Dict]] = ...,
        allowed_mentions: typing.Union[typing.Literal[...], typing.Dict] = ...,
    ) -> typing.Optional[typing.Dict]:
        """Create a message in the given channel or DM.

        Parameters
        ----------
        webhook_id : :obj:`str`
            The ID of the webhook to execute.
        webhook_token : :obj:`str`
            The token of the webhook to execute.
        content : :obj:`str`
            If specified, the webhook message content to send.
        username : :obj:`str`
            If specified, the username to override the webhook's username 
            for this request.
        avatar_url : :obj:`str`
            If specified, the url of an image to override the webhook's 
            avatar with for this request.
        tts : :obj:`bool`
            If specified, whether this webhook should create a TTS message.
        wait : :obj:`bool`
            If specified, whether this request should wait for the webhook 
            to be executed and return the resultant message object.
        file : :obj:`typing.Tuple` [ :obj:`str`, :obj:`storage.FileLikeT` ]
            If specified, a tuple of the file name and either raw :obj:`bytes` 
            or a :obj:`io.IOBase` derived object that points to a buffer 
            containing said file.
        embeds : :obj:`typing.Sequence` [:obj:`typing.Dict`]
            If specified, the sequence of embed objects that will be sent 
            with this message.
        allowed_mentions : :obj:`typing.Dict`
            If specified, the mentions to parse from the ``content``. 
            If not specified, will parse all mentions from the ``content``.

        Raises
        ------
        :obj:`hikari.net.errors.NotFoundHTTPError`
            If the channel ID or webhook ID is not found.
        :obj:`hikari.net.errors.BadRequestHTTPError`
            This can be raised if the file is too large; if the embed exceeds 
            the defined limits; if the message content is specified only and 
            empty or greater than ``2000`` characters; if neither content, file 
            or embed are specified; if there is a duplicate id in only of the
            fields in ``allowed_mentions``; if you specify to parse all 
            users/roles mentions but also specify which users/roles to 
            parse only.
        :obj:`hikari.net.errors.ForbiddenHTTPError`
            If you lack permissions to send to this channel.
        :obj:`hikari.net.errors.UnauthorizedHTTPError`
            If you pass a token that's invalid for the target webhook.

        Returns
        -------
        :obj:`hikari.internal_utilities.typing.Dict`, optional
            The created message object if ``wait`` is ``True``, else ``None``.
        """
        form = aiohttp.FormData()

        json_payload = {}
        transformations.put_if_specified(json_payload, "content", content)
        transformations.put_if_specified(json_payload, "username", username)
        transformations.put_if_specified(json_payload, "avatar_url", avatar_url)
        transformations.put_if_specified(json_payload, "tts", tts)
        transformations.put_if_specified(json_payload, "embeds", embeds)
        transformations.put_if_specified(json_payload, "allowed_mentions", allowed_mentions)

        form.add_field("payload_json", json.dumps(json_payload), content_type="application/json")

        if file is not ...:
            file_name, file = file
            file = storage.make_resource_seekable(file)
            re_seekable_resources = [file]
            form.add_field("file", file, filename=file_name, content_type="application/octet-stream")
        else:
            re_seekable_resources = []

        query = {}
        transformations.put_if_specified(query, "wait", wait, str)

        route = routes.WEBHOOK_WITH_TOKEN.compile(self.POST, webhook_id=webhook_id, webhook_token=webhook_token)
        return await self._request(
            route,
            form_body=form,
            re_seekable_resources=re_seekable_resources,
            query=query,
            suppress_authorization_header=True,
        )

    ##########
    # OAUTH2 #
    ##########

    async def get_current_application_info(self) -> typing.Dict:
        """Get the current application information.

        Returns
        -------
        :obj:`typing.Dict`
            An application info object.
        """
        route = routes.OAUTH2_APPLICATIONS_ME.compile(self.GET)
        return await self._request(route)
