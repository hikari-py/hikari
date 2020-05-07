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

from __future__ import annotations

__all__ = ["REST"]

import asyncio
import contextlib
import datetime
import http
import json
import typing

import aiohttp.typedefs

from hikari import errors
from hikari.internal import assertions
from hikari.internal import conversions
from hikari.internal import more_collections
from hikari.internal import urls
from hikari.net import http_client
from hikari.net import ratelimits
from hikari.net import routes
from hikari.net import user_agents

if typing.TYPE_CHECKING:
    import ssl

    from hikari import files as _files
    from hikari.internal import more_typing

VERSION_6: typing.Final[int] = 6
VERSION_7: typing.Final[int] = 7


class _RateLimited(RuntimeError):
    __slots__ = ()


class REST(http_client.HTTPClient):  # pylint: disable=too-many-public-methods, too-many-instance-attributes
    """A low-level RESTful client to allow you to interact with the Discord API.

    Parameters
    ----------
    allow_redirects : bool
        Whether to allow redirects or not. Defaults to `False`.
    base_url : str
        The base URL and route for the discord API
    connector : aiohttp.BaseConnector, optional
        Optional aiohttp connector info for making an HTTP connection
    debug : bool
        Defaults to `False`. If `True`, then a lot of contextual information
        regarding low-level HTTP communication will be logged to the debug
        logger on this class.
    json_deserialize : deserialization function
        A custom JSON deserializer function to use. Defaults to `json.loads`.
    json_serialize : serialization function
        A custom JSON serializer function to use. Defaults to `json.dumps`.
    proxy_headers : typing.Mapping[str, str], optional
        Optional proxy headers to pass to HTTP requests.
    proxy_auth : aiohttp.BasicAuth, optional
        Optional authorization to be used if using a proxy.
    proxy_url : str, optional
        Optional proxy URL to use for HTTP requests.
    ssl_context : ssl.SSLContext, optional
        The optional SSL context to be used.
    verify_ssl : bool
        Whether or not the client should enforce SSL signed certificate
        verification. If 1 it will ignore potentially malicious
        SSL certificates.
    timeout : float, optional
        The optional timeout for all HTTP requests.
    token : string, optional
        The bot token for the client to use. You may start this with
        a prefix of either `Bot` or `Bearer` to force the token type, or
        not provide this information if you want to have it auto-detected.
        If this is passed as `None`, then no token is used.
        This will be passed as the `Authorization` header if not `None`
        for each request.
    trust_env : bool
        If `True`, and no proxy info is given, then `HTTP_PROXY` and
        `HTTPS_PROXY` will be used from the environment variables if present.
        Any proxy credentials will be read from the user's `netrc` file
        (https://www.gnu.org/software/inetutils/manual/html_node/The-_002enetrc-file.html)
        If `False`, then this information is instead ignored.
        Defaults to `False`.
    version : int
        The version of the API to use. Defaults to the most recent stable
        version (v6).
    """

    _AUTHENTICATION_SCHEMES: typing.Final[typing.Tuple[str, ...]] = ("Bearer", "Bot")

    base_url: str
    """The base URL to send requests to."""

    global_ratelimiter: ratelimits.ManualRateLimiter
    """The global ratelimiter.

    This is used if Discord declares a ratelimit across the entire API,
    regardless of the endpoint. If this is set, then any HTTP operation using
    this session will be paused.
    """

    bucket_ratelimiters: ratelimits.RESTBucketManager
    """The per-route ratelimit manager.

    This handles tracking any ratelimits for routes that have recently been used
    or are in active use, as well as keeping memory usage to a minimum where
    possible for large numbers of varying requests. This encapsulates a lot of
    complex rate limiting rules to reduce the number of active `429` responses
    this client gets, and thus reducing your chances of an API ban by Discord.

    You should not ever need to touch this implementation.
    """

    user_agent: str
    """The `User-Agent` header to send to Discord.

    !!! warning
        Changing this value may lead to undesirable results, as Discord document
        that they can actively IP ban any client that does not have a valid
        `User-Agent` header that conforms to specific requirements.
        Your mileage may vary (YMMV).
    """

    verify_ssl: bool
    """Whether SSL certificates should be verified for each request.

    When this is `True` then an exception will be raised whenever invalid SSL
    certificates are received. When this is `False` unrecognised certificates
    that may be illegitimate are accepted and ignored.
    """

    version: int
    """The API version number that is being used."""

    def __init__(  # pylint: disable=too-many-locals
        self,
        *,
        base_url: str = urls.REST_API_URL,
        allow_redirects: bool = False,
        connector: typing.Optional[aiohttp.BaseConnector] = None,
        debug: bool = False,
        json_deserialize: typing.Callable[[typing.AnyStr], typing.Dict] = json.loads,
        json_serialize: typing.Callable[[typing.Dict], typing.AnyStr] = json.dumps,
        proxy_auth: typing.Optional[aiohttp.BasicAuth] = None,
        proxy_headers: typing.Optional[aiohttp.typedefs.LooseHeaders] = None,
        proxy_url: typing.Optional[str] = None,
        ssl_context: typing.Optional[ssl.SSLContext] = None,
        verify_ssl: bool = True,
        timeout: typing.Optional[float] = None,
        trust_env: bool = False,
        token: typing.Optional[str],
        version: int = VERSION_6,
    ) -> None:
        super().__init__(
            allow_redirects=allow_redirects,
            connector=connector,
            debug=debug,
            json_deserialize=json_deserialize,
            json_serialize=json_serialize,
            proxy_auth=proxy_auth,
            proxy_headers=proxy_headers,
            proxy_url=proxy_url,
            ssl_context=ssl_context,
            verify_ssl=verify_ssl,
            timeout=timeout,
            trust_env=trust_env,
        )
        self.user_agent = user_agents.UserAgent().user_agent
        self.version = version
        self.global_ratelimiter = ratelimits.ManualRateLimiter()
        self.bucket_ratelimiters = ratelimits.RESTBucketManager()

        if token is not None and not token.startswith(self._AUTHENTICATION_SCHEMES):
            this_type = type(self).__name__
            auth_schemes = " or ".join(self._AUTHENTICATION_SCHEMES)
            raise RuntimeError(f"Any token passed to {this_type} should begin with {auth_schemes}")

        self._token = token
        self.base_url = base_url.format(self)

    async def close(self) -> None:
        """Shut down the REST client safely, and terminate any rate limiters executing in the background."""
        with contextlib.suppress(Exception):
            self.bucket_ratelimiters.close()
        with contextlib.suppress(Exception):
            self.global_ratelimiter.close()
        await super().close()

    async def _request_json_response(
        self,
        compiled_route: routes.CompiledRoute,
        *,
        headers: typing.Optional[typing.Dict[str, str]] = None,
        query: typing.Optional[more_typing.JSONObject] = None,
        body: typing.Optional[typing.Union[aiohttp.FormData, dict, list]] = None,
        reason: str = ...,
        suppress_authorization_header: bool = False,
    ) -> typing.Optional[more_typing.JSONObject, more_typing.JSONArray, bytes]:
        # Make a ratelimit-protected HTTP request to a JSON endpoint and expect some form
        # of JSON response. If an error occurs, the response body is returned in the
        # raised exception as a bytes object. This is done since the differences between
        # the V6 and V7 API error messages are not documented properly, and there are
        # edge cases such as Cloudflare issues where we may receive arbitrary data in
        # the response instead of a JSON object.

        if not self.bucket_ratelimiters.is_started:
            self.bucket_ratelimiters.start()

        headers = {} if headers is None else headers

        headers["x-ratelimit-precision"] = "millisecond"
        headers["accept"] = self.APPLICATION_JSON

        if self._token is not None and not suppress_authorization_header:
            headers["authorization"] = self._token

        if reason and reason is not ...:
            headers["x-audit-log-reason"] = reason

        while True:
            try:
                # Moved to a separate method to keep branch counts down.
                return await self.__request_json_response(compiled_route, headers, body, query)
            except _RateLimited:
                pass

    async def __request_json_response(self, compiled_route, headers, body, query):
        url = compiled_route.create_url(self.base_url)

        # Wait for any ratelimits to finish.
        await asyncio.gather(self.bucket_ratelimiters.acquire(compiled_route), self.global_ratelimiter.acquire())

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
            if response.content_type == self.APPLICATION_JSON:
                # Only deserializing here stops Cloudflare shenanigans messing us around.
                return self.json_deserialize(raw_body)
            raise errors.HTTPError(real_url, f"Expected JSON response but received {response.content_type}")

        if response.status == http.HTTPStatus.BAD_REQUEST:
            raise errors.BadRequest(real_url, response.headers, raw_body)
        if response.status == http.HTTPStatus.UNAUTHORIZED:
            raise errors.Unauthorized(real_url, response.headers, raw_body)
        if response.status == http.HTTPStatus.FORBIDDEN:
            raise errors.Forbidden(real_url, response.headers, raw_body)
        if response.status == http.HTTPStatus.NOT_FOUND:
            raise errors.NotFound(real_url, response.headers, raw_body)

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
        self.bucket_ratelimiters.update_rate_limits(
            compiled_route=compiled_route,
            bucket_header=bucket,
            remaining_header=remaining,
            limit_header=limit,
            date_header=now_date,
            reset_at_header=reset_date,
        )

        if response.status == http.HTTPStatus.TOO_MANY_REQUESTS:
            body = await response.json() if response.content_type == self.APPLICATION_JSON else await response.read()

            # We are being rate limited.
            if isinstance(body, dict):
                if body.get("global", False):
                    retry_after = float(body["retry_after"]) / 1_000
                    self.global_ratelimiter.throttle(retry_after)

                raise _RateLimited()

            # We might find out Cloudflare causes this scenario to occur.
            # I hope we don't though.
            raise errors.HTTPError(
                str(response.real_url),
                f"We were ratelimited but did not understand the response. Perhaps Cloudflare did this? {body!r}",
            )

    async def get_gateway(self) -> str:
        """Get the URL to use to connect to the gateway with.

        Returns
        -------
        str
            A static URL to use to connect to the gateway with.

        !!! note
            Users are expected to attempt to cache this result.
        """
        result = await self._request_json_response(routes.GET_GATEWAY.compile())
        return result["url"]

    async def get_gateway_bot(self) -> more_typing.JSONObject:
        """Get the gateway info for the bot.

        Returns
        -------
        more_typing.JSONObject
            An object containing a `url` to connect to, an `int` number of
            shards recommended to use for connecting, and a
            `session_start_limit` object.

        !!! note
            Unlike `REST.get_gateway`, this requires a valid token to work.
        """
        return await self._request_json_response(routes.GET_GATEWAY_BOT.compile())

    async def get_guild_audit_log(
        self, guild_id: str, *, user_id: str = ..., action_type: int = ..., limit: int = ..., before: str = ...
    ) -> more_typing.JSONObject:
        """Get an audit log object for the given guild.

        Parameters
        ----------
        guild_id : str
            The guild ID to look up.
        user_id : str
            If specified, the user ID to filter by.
        action_type : int
            If specified, the action type to look up.
        limit : int
            If specified, the limit to apply to the number of records.
            Defaults to `50`. Must be between `1` and `100` inclusive.
        before : str
            If specified, the ID of the entry that all retrieved entries will
            have occurred before.

        Returns
        -------
        more_typing.JSONObject
            An audit log object.

        Raises
        ------
        hikari.errors.Forbidden
            If you lack the given permissions to view an audit log.
        hikari.errors.NotFound
            If the guild does not exist.
        """
        query = {}
        conversions.put_if_specified(query, "user_id", user_id)
        conversions.put_if_specified(query, "action_type", action_type)
        conversions.put_if_specified(query, "limit", limit)
        conversions.put_if_specified(query, "before", before)
        route = routes.GET_GUILD_AUDIT_LOGS.compile(guild_id=guild_id)
        return await self._request_json_response(route, query=query)

    async def get_channel(self, channel_id: str) -> more_typing.JSONObject:
        """Get a channel object from a given channel ID.

        Parameters
        ----------
        channel_id : str
            The channel ID to look up.

        Returns
        -------
        more_typing.JSONObject
            The channel object that has been found.

        Raises
        ------
        hikari.errors.Forbidden
            If you don't have access to the channel.
        hikari.errors.NotFound
            If the channel does not exist.
        """
        route = routes.GET_CHANNEL.compile(channel_id=channel_id)
        return await self._request_json_response(route)

    async def modify_channel(  # lgtm [py/similar-function]
        self,
        channel_id: str,
        *,
        name: str = ...,
        position: int = ...,
        topic: str = ...,
        nsfw: bool = ...,
        rate_limit_per_user: int = ...,
        bitrate: int = ...,
        user_limit: int = ...,
        permission_overwrites: typing.Sequence[more_typing.JSONObject] = ...,
        parent_id: str = ...,
        reason: str = ...,
    ) -> more_typing.JSONObject:
        """Update one or more aspects of a given channel ID.

        Parameters
        ----------
        channel_id : str
            The channel ID to update.
        name : str
            If specified, the new name for the channel. This must be
            between `2` and `100` characters in length.
        position : int
            If specified, the position to change the channel to.
        topic : str
            If specified, the topic to set. This is only applicable to
            text channels. This must be between `0` and `1024`
            characters in length.
        nsfw : bool
            If specified, whether the  channel will be marked as NSFW.
            Only applicable to text channels.
        rate_limit_per_user : int
            If specified, the number of seconds the user has to wait before sending
            another message.  This will not apply to bots, or to members with
            `MANAGE_MESSAGES` or `MANAGE_CHANNEL` permissions. This must
            be between `0` and `21600` seconds.
        bitrate : int
            If specified, the bitrate in bits per second allowable for the channel.
            This only applies to voice channels and must be between `8000`
            and `96000` for normal servers or `8000` and `128000` for
            VIP servers.
        user_limit : int
            If specified, the new max number of users to allow in a voice channel.
            This must be between `0` and `99` inclusive, where
            `0` implies no limit.
        permission_overwrites : typing.Sequence[more_typing.JSONObject]
            If specified, the new list of permission overwrites that are category
            specific to replace the existing overwrites with.
        parent_id : str, optional
            If specified, the new parent category ID to set for the channel.,
            pass `None` to unset.
        reason : str
            If specified, the audit log reason explaining why the operation
            was performed.

        Returns
        -------
        more_typing.JSONObject
            The channel object that has been modified.

        Raises
        ------
        hikari.errors.NotFound
            If the channel does not exist.
        hikari.errors.Forbidden
            If you lack the permission to make the change.
        hikari.errors.BadRequest
            If you provide incorrect options for the corresponding channel type
            (e.g. a `bitrate` for a text channel).
        """
        payload = {}
        conversions.put_if_specified(payload, "name", name)
        conversions.put_if_specified(payload, "position", position)
        conversions.put_if_specified(payload, "topic", topic)
        conversions.put_if_specified(payload, "nsfw", nsfw)
        conversions.put_if_specified(payload, "rate_limit_per_user", rate_limit_per_user)
        conversions.put_if_specified(payload, "bitrate", bitrate)
        conversions.put_if_specified(payload, "user_limit", user_limit)
        conversions.put_if_specified(payload, "permission_overwrites", permission_overwrites)
        conversions.put_if_specified(payload, "parent_id", parent_id)
        route = routes.PATCH_CHANNEL.compile(channel_id=channel_id)
        return await self._request_json_response(route, body=payload, reason=reason)

    async def delete_close_channel(self, channel_id: str) -> None:
        """Delete the given channel ID, or if it is a DM, close it.

        Parameters
        ----------
        channel_id : str
            The channel ID to delete, or direct message channel to close.

        Returns
        -------
        None
            Nothing, unlike what the API specifies. This is done to maintain
            consistency with other calls of a similar nature in this API wrapper.

        Raises
        ------
        hikari.errors.NotFound
            If the channel does not exist.
        hikari.errors.Forbidden
            If you do not have permission to delete the channel.

        !!! warning
            Deleted channels cannot be un-deleted. Deletion of DMs is able to be
            undone by reopening the DM.
        """
        route = routes.DELETE_CHANNEL.compile(channel_id=channel_id)
        await self._request_json_response(route)

    async def get_channel_messages(
        self, channel_id: str, *, limit: int = ..., after: str = ..., before: str = ..., around: str = ...,
    ) -> typing.Sequence[more_typing.JSONObject]:
        """Retrieve message history for a given channel.

        Parameters
        ----------
        channel_id : str
            The ID of the channel to retrieve the messages from.
        limit : int
            If specified, the number of messages to return. Must be
            between `1` and `100` inclusive.Defaults to `50`
            if unspecified.
        after : str
            A message ID. If specified, only return messages sent AFTER this message.
        before : str
            A message ID. If specified, only return messages sent BEFORE this message.
        around : str
            A message ID. If specified, only return messages sent AROUND and
            including (if it still exists) this message.

        Returns
        -------
        typing.Sequence[more_typing.JSONObject]
            A list of message objects.

        Raises
        ------
        hikari.errors.Forbidden
            If you lack permission to read the channel.
        hikari.errors.BadRequest
            If your query is malformed, has an invalid value for `limit`,
            or contains more than one of `after`, `before` and `around`.
        hikari.errors.NotFound
            If the channel is not found, or the message
            provided for one of the filter arguments is not found.

        !!! note
            If you are missing the `VIEW_CHANNEL` permission, you will receive a
            `hikari.errors.Forbidden`. If you are instead missing
            the `READ_MESSAGE_HISTORY` permission, you will always receive
            zero results, and thus an empty list will be returned instead.

        !!! warning
            You can only specify a maximum of one from `before`, `after`, and
            `around`; specifying more than one will cause a
            `hikari.errors.BadRequest` to be raised.
        """
        query = {}
        conversions.put_if_specified(query, "limit", limit)
        conversions.put_if_specified(query, "before", before)
        conversions.put_if_specified(query, "after", after)
        conversions.put_if_specified(query, "around", around)
        route = routes.GET_CHANNEL_MESSAGES.compile(channel_id=channel_id)
        return await self._request_json_response(route, query=query)

    async def get_channel_message(self, channel_id: str, message_id: str) -> more_typing.JSONObject:
        """Get the message with the given message ID from the channel with the given channel ID.

        Parameters
        ----------
        channel_id : str
            The ID of the channel to get the message from.
        message_id : str
            The ID of the message to retrieve.

        Returns
        -------
        more_typing.JSONObject
            A message object.

        !!! note
            This requires the `READ_MESSAGE_HISTORY` permission.

        Raises
        ------
        hikari.errors.Forbidden
            If you lack permission to see the message.
        hikari.errors.NotFound
            If the channel or message is not found.
        """
        route = routes.GET_CHANNEL_MESSAGE.compile(channel_id=channel_id, message_id=message_id)
        return await self._request_json_response(route)

    async def create_message(
        self,
        channel_id: str,
        *,
        content: str = ...,
        nonce: str = ...,
        tts: bool = ...,
        files: typing.Sequence[_files.BaseStream] = ...,
        embed: more_typing.JSONObject = ...,
        allowed_mentions: more_typing.JSONObject = ...,
    ) -> more_typing.JSONObject:
        """Create a message in the given channel or DM.

        Parameters
        ----------
        channel_id : str
            The ID of the channel to send to.
        content : str
            If specified, the message content to send with the message.
        nonce : str
            If specified, an optional ID to send for opportunistic message
            creation. Any created message will have this nonce set on it.
            Nonces are limited to 32 bytes in size.
        tts : bool
            If specified, whether the message will be sent as a TTS message.
        files : typing.Sequence[hikari.files.BaseStream]
            If specified, this should be a list of between `1` and `5` file
            objects to upload. Each should have a unique name.
        embed : more_typing.JSONObject
            If specified, the embed to send with the message.
        allowed_mentions : more_typing.JSONObject
            If specified, the mentions to parse from the `content`.
            If not specified, will parse all mentions from the `content`.

        Returns
        -------
        more_typing.JSONObject
            The created message object.

        Raises
        ------
        hikari.errors.NotFound
            If the channel is not found.
        hikari.errors.BadRequest
            This can be raised if the file is too large; if the embed exceeds
            the defined limits; if the message content is specified only and
            empty or greater than `2000` characters; if neither content, file
            or embed are specified; if there is a duplicate id in only of the
            fields in `allowed_mentions`; if you specify to parse all
            users/roles mentions but also specify which users/roles to
            parse only.
        hikari.errors.Forbidden
            If you lack permissions to send to this channel.
        """
        form = aiohttp.FormData()

        json_payload = {}
        conversions.put_if_specified(json_payload, "content", content)
        conversions.put_if_specified(json_payload, "nonce", nonce)
        conversions.put_if_specified(json_payload, "tts", tts)
        conversions.put_if_specified(json_payload, "embed", embed)
        conversions.put_if_specified(json_payload, "allowed_mentions", allowed_mentions)

        form.add_field("payload_json", json.dumps(json_payload), content_type=self.APPLICATION_JSON)

        if files is ...:
            files = more_collections.EMPTY_SEQUENCE

        for i, file in enumerate(files):
            form.add_field(f"file{i}", file, filename=file.filename, content_type=self.APPLICATION_OCTET_STREAM)

        route = routes.POST_CHANNEL_MESSAGES.compile(channel_id=channel_id)

        return await self._request_json_response(route, body=form)

    async def create_reaction(self, channel_id: str, message_id: str, emoji: str) -> None:
        """Add a reaction to the given message in the given channel.

        Parameters
        ----------
        channel_id : str
            The ID of the channel to add this reaction in.
        message_id : str
            The ID of the message to add the reaction in.
        emoji : str
            The emoji to add. This can either be a series of unicode
            characters making up a valid Discord emoji, or it can be a the url
            representation of a custom emoji `<{emoji.name}:{emoji.id}>`.

        Raises
        ------
        hikari.errors.Forbidden
            If this is the first reaction using this specific emoji on this
            message and you lack the `ADD_REACTIONS` permission. If you lack
            `READ_MESSAGE_HISTORY`, this may also raise this error.
        hikari.errors.NotFound
            If the channel or message is not found, or if the emoji is not found.
        hikari.errors.BadRequest
            If the emoji is not valid, unknown, or formatted incorrectly.
        """
        route = routes.PUT_MY_REACTION.compile(channel_id=channel_id, message_id=message_id, emoji=emoji)
        await self._request_json_response(route)

    async def delete_own_reaction(self, channel_id: str, message_id: str, emoji: str) -> None:
        """Remove your own reaction from the given message in the given channel.

        Parameters
        ----------
        channel_id : str
            The ID of the channel to get the message from.
        message_id : str
            The ID of the message to delete the reaction from.
        emoji : str
            The emoji to delete. This can either be a series of unicode
            characters making up a valid Discord emoji, or it can be a
            snowflake ID for a custom emoji.

        Raises
        ------
        hikari.errors.Forbidden
            If you lack permission to do this.
        hikari.errors.NotFound
            If the channel or message or emoji is not found.
        """
        route = routes.DELETE_MY_REACTION.compile(channel_id=channel_id, message_id=message_id, emoji=emoji)
        await self._request_json_response(route)

    async def delete_all_reactions_for_emoji(self, channel_id: str, message_id: str, emoji: str) -> None:
        """Remove all reactions for a single given emoji on a given message in a given channel.

        Parameters
        ----------
        channel_id : str
            The ID of the channel to get the message from.
        message_id : str
            The ID of the message to delete the reactions from.
        emoji : str
            The emoji to delete. This can either be a series of unicode
            characters making up a valid Discord emoji, or it can be a
            snowflake ID for a custom emoji.

        Raises
        ------
        hikari.errors.NotFound
            If the channel or message or emoji or user is not found.
        hikari.errors.Forbidden
            If you lack the `MANAGE_MESSAGES` permission, or are in DMs.
        """
        route = routes.DELETE_REACTION_EMOJI.compile(channel_id=channel_id, message_id=message_id, emoji=emoji)
        await self._request_json_response(route)

    async def delete_user_reaction(self, channel_id: str, message_id: str, emoji: str, user_id: str) -> None:
        """Remove a reaction made by a given user using a given emoji on a given message in a given channel.

        Parameters
        ----------
        channel_id : str
            The ID of the channel to get the message from.
        message_id : str
            The ID of the message to remove the reaction from.
        emoji : str
            The emoji to delete. This can either be a series of unicode
            characters making up a valid Discord emoji, or it can be a
            snowflake ID for a custom emoji.
        user_id : str
            The ID of the user who made the reaction that you wish to remove.

        Raises
        ------
        hikari.errors.NotFound
            If the channel or message or emoji or user is not found.
        hikari.errors.Forbidden
            If you lack the `MANAGE_MESSAGES` permission, or are in DMs.
        """
        route = routes.DELETE_REACTION_USER.compile(
            channel_id=channel_id, message_id=message_id, emoji=emoji, user_id=user_id,
        )
        await self._request_json_response(route)

    async def get_reactions(
        self, channel_id: str, message_id: str, emoji: str, *, after: str = ..., limit: int = ...,
    ) -> typing.Sequence[more_typing.JSONObject]:
        """Get a list of users who reacted with the given emoji on the given message.

        Parameters
        ----------
        channel_id : str
            The ID of the channel to get the message from.
        message_id : str
            The ID of the message to get the reactions from.
        emoji : str
            The emoji to get. This can either be a series of unicode
            characters making up a valid Discord emoji, or it can be a
            snowflake ID for a custom emoji.
        after : str
            If specified, the user ID. If specified, only users with a snowflake
            that is lexicographically greater than the value will be returned.
        limit : str
            If specified, the limit of the number of values to return. Must be
            between `1` and `100` inclusive. If unspecified,
            defaults to `25`.

        Returns
        -------
        typing.Sequence[more_typing.JSONObject]
            A list of user objects.

        Raises
        ------
        hikari.errors.Forbidden
            If you lack access to the message.
        hikari.errors.NotFound
            If the channel or message is not found.
        """
        query = {}
        conversions.put_if_specified(query, "after", after)
        conversions.put_if_specified(query, "limit", limit)
        route = routes.GET_REACTIONS.compile(channel_id=channel_id, message_id=message_id, emoji=emoji)
        return await self._request_json_response(route, query=query)

    async def delete_all_reactions(self, channel_id: str, message_id: str) -> None:
        """Delete all reactions from a given message in a given channel.

        Parameters
        ----------
        channel_id : str
            The ID of the channel to get the message from.
        message_id : str
            The ID of the message to remove all reactions from.

        Raises
        ------
        hikari.errors.NotFound
            If the channel or message is not found.
        hikari.errors.Forbidden
            If you lack the `MANAGE_MESSAGES` permission.
        """
        route = routes.DELETE_ALL_REACTIONS.compile(channel_id=channel_id, message_id=message_id)
        await self._request_json_response(route)

    async def edit_message(
        self,
        channel_id: str,
        message_id: str,
        *,
        content: typing.Optional[str] = ...,
        embed: typing.Optional[more_typing.JSONObject] = ...,
        flags: int = ...,
        allowed_mentions: more_typing.JSONObject = ...,
    ) -> more_typing.JSONObject:
        """Update the given message.

        Parameters
        ----------
        channel_id : str
            The ID of the channel to get the message from.
        message_id : str
            The ID of the message to edit.
        content : str, optional
            If specified, the string content to replace with in the message.
            If `None`, the content will be removed from the message.
        embed : more_typing.JSONObject, optional
            If specified, the embed to replace with in the message.
            If `None`, the embed will be removed from the message.
        flags : int
            If specified, the integer to replace the message's current flags.
        allowed_mentions : more_typing.JSONObject
            If specified, the mentions to parse from the `content`.
            If not specified, will parse all mentions from the `content`.

        Returns
        -------
        more_typing.JSONObject
            The edited message object.

        Raises
        ------
        hikari.errors.NotFound
            If the channel or message is not found.
        hikari.errors.BadRequest
            This can be raised if the embed exceeds the defined limits;
            if the message content is specified only and empty or greater
            than `2000` characters; if neither content, file or embed
            are specified.
            parse only.
        hikari.errors.Forbidden
            If you try to edit `content` or `embed` or `allowed_mentions`
            on a message you did not author or try to edit the flags on a
            message you did not author without the `MANAGE_MESSAGES`
            permission.
        """
        payload = {}
        conversions.put_if_specified(payload, "content", content)
        conversions.put_if_specified(payload, "embed", embed)
        conversions.put_if_specified(payload, "flags", flags)
        conversions.put_if_specified(payload, "allowed_mentions", allowed_mentions)
        route = routes.PATCH_CHANNEL_MESSAGE.compile(channel_id=channel_id, message_id=message_id)
        return await self._request_json_response(route, body=payload)

    async def delete_message(self, channel_id: str, message_id: str) -> None:
        """Delete a message in a given channel.

        Parameters
        ----------
        channel_id : str
            The ID of the channel to get the message from.
        message_id : str
            The ID of the message to delete.

        Raises
        ------
        hikari.errors.Forbidden
            If you did not author the message and are in a DM, or if you did not author the message and lack the
            `MANAGE_MESSAGES` permission in a guild channel.
        hikari.errors.NotFound
            If the channel or message is not found.
        """
        route = routes.DELETE_CHANNEL_MESSAGE.compile(channel_id=channel_id, message_id=message_id)
        await self._request_json_response(route)

    async def bulk_delete_messages(self, channel_id: str, messages: typing.Sequence[str]) -> None:
        """Delete multiple messages in a given channel.

        Parameters
        ----------
        channel_id : str
            The ID of the channel to get the message from.
        messages : typing.Sequence[str]
            A list of `2-100` message IDs to remove in the channel.

        Raises
        ------
        hikari.errors.NotFound
            If the channel is not found.
        hikari.errors.Forbidden
            If you lack the `MANAGE_MESSAGES` permission in the channel.
        hikari.errors.BadRequest
            If any of the messages passed are older than `2` weeks in age or
            any duplicate message IDs are passed.

        !!! note
            This can only be used on guild text channels. Any message IDs that
            do not exist or are invalid still add towards the total `100` max
            messages to remove. This can only delete messages that are newer
            than `2` weeks in age. If any of the messages are older than
            `2` weeks then this call will fail.
        """
        payload = {"messages": messages}
        route = routes.POST_DELETE_CHANNEL_MESSAGES_BULK.compile(channel_id=channel_id)
        await self._request_json_response(route, body=payload)

    async def edit_channel_permissions(
        self, channel_id: str, overwrite_id: str, type_: str, *, allow: int = ..., deny: int = ..., reason: str = ...,
    ) -> None:
        """Edit permissions for a given channel.

        Parameters
        ----------
        channel_id : str
            The ID of the channel to edit permissions for.
        overwrite_id : str
            The overwrite ID to edit.
        type_ : str
            The type of overwrite. `"member"` if it is for a member,
            or `"role"` if it is for a role.
        allow : int
            If specified, the bitwise value of all permissions to set to be allowed.
        deny : int
            If specified, the bitwise value of all permissions to set to be denied.
        reason : str
            If specified, the audit log reason explaining why the operation
            was performed.

        Raises
        ------
        hikari.errors.NotFound
            If the target channel or overwrite doesn't exist.
        hikari.errors.Forbidden
            If you lack permission to do this.
        """
        payload = {"type": type_}
        conversions.put_if_specified(payload, "allow", allow)
        conversions.put_if_specified(payload, "deny", deny)
        route = routes.PATCH_CHANNEL_PERMISSIONS.compile(channel_id=channel_id, overwrite_id=overwrite_id)
        await self._request_json_response(route, body=payload, reason=reason)

    async def get_channel_invites(self, channel_id: str) -> typing.Sequence[more_typing.JSONObject]:
        """Get invites for a given channel.

        Parameters
        ----------
        channel_id : str
            The ID of the channel to get invites for.

        Returns
        -------
        typing.Sequence[more_typing.JSONObject]
            A list of invite objects.

        Raises
        ------
        hikari.errors.Forbidden
            If you lack the `MANAGE_CHANNELS` permission.
        hikari.errors.NotFound
            If the channel does not exist.
        """
        route = routes.GET_CHANNEL_INVITES.compile(channel_id=channel_id)
        return await self._request_json_response(route)

    async def create_channel_invite(
        self,
        channel_id: str,
        *,
        max_age: int = ...,
        max_uses: int = ...,
        temporary: bool = ...,
        unique: bool = ...,
        target_user: str = ...,
        target_user_type: int = ...,
        reason: str = ...,
    ) -> more_typing.JSONObject:
        """Create a new invite for the given channel.

        Parameters
        ----------
        channel_id : str
            The ID of the channel to create the invite for.
        max_age : int
            If specified, the max age of the invite in seconds, defaults to
            `86400` (`24` hours).
            Set to `0` to never expire.
        max_uses : int
            If specified, the max number of uses this invite can have, or `0`
            for unlimited (as per the default).
        temporary : bool
            If specified, whether to grant temporary membership, meaning the
            user is kicked when their session ends unless they are given a role.
        unique : bool
            If specified, whether to try to reuse a similar invite.
        target_user : str
            If specified, the ID of the user this invite should target.
        target_user_type : int
            If specified, the type of target for this invite.
        reason : str
            If specified, the audit log reason explaining why the operation
            was performed.

        Returns
        -------
        more_typing.JSONObject
            An invite object.

        Raises
        ------
        hikari.errors.Forbidden
            If you lack the `CREATE_INSTANT_MESSAGES` permission.
        hikari.errors.NotFound
            If the channel does not exist.
        hikari.errors.BadRequest
            If the arguments provided are not valid (e.g. negative age, etc).
        """
        payload = {}
        conversions.put_if_specified(payload, "max_age", max_age)
        conversions.put_if_specified(payload, "max_uses", max_uses)
        conversions.put_if_specified(payload, "temporary", temporary)
        conversions.put_if_specified(payload, "unique", unique)
        conversions.put_if_specified(payload, "target_user", target_user)
        conversions.put_if_specified(payload, "target_user_type", target_user_type)
        route = routes.POST_CHANNEL_INVITES.compile(channel_id=channel_id)
        return await self._request_json_response(route, body=payload, reason=reason)

    async def delete_channel_permission(self, channel_id: str, overwrite_id: str) -> None:
        """Delete a channel permission overwrite for a user or a role in a channel.

        Parameters
        ----------
        channel_id : str
            The ID of the channel to delete the overwrite from.
        overwrite_id : str
            The ID of the overwrite to remove.

        Raises
        ------
        hikari.errors.NotFound
            If the overwrite or channel do not exist.
        hikari.errors.Forbidden
            If you lack the `MANAGE_ROLES` permission for that channel.
        """
        route = routes.DELETE_CHANNEL_PERMISSIONS.compile(channel_id=channel_id, overwrite_id=overwrite_id)
        await self._request_json_response(route)

    async def trigger_typing_indicator(self, channel_id: str) -> None:
        """Trigger the account to appear to be typing for the next `10` seconds in the given channel.

        Parameters
        ----------
        channel_id : str
            The ID of the channel to appear to be typing in.

        Raises
        ------
        hikari.errors.NotFound
            If the channel is not found.
        hikari.errors.Forbidden
            If you are not able to type in the channel.
        """
        route = routes.POST_CHANNEL_TYPING.compile(channel_id=channel_id)
        await self._request_json_response(route)

    async def get_pinned_messages(self, channel_id: str) -> typing.Sequence[more_typing.JSONObject]:
        """Get pinned messages for a given channel.

        Parameters
        ----------
        channel_id : str
            The channel ID to get messages from.

        Returns
        -------
        typing.Sequence[more_typing.JSONObject]
            A list of messages.

        Raises
        ------
        hikari.errors.NotFound
            If the channel is not found.
        hikari.errors.Forbidden
            If you are not able to see the channel.

        !!! note
            If you are not able to see the pinned message (eg. you are missing
            `READ_MESSAGE_HISTORY` and the pinned message is an old message), it
            will not be returned.
        """
        route = routes.GET_CHANNEL_PINS.compile(channel_id=channel_id)
        return await self._request_json_response(route)

    async def add_pinned_channel_message(self, channel_id: str, message_id: str) -> None:
        """Add a pinned message to the channel.

        Parameters
        ----------
        channel_id : str
            The ID of the channel to pin a message to.
        message_id : str
            The ID of the message to pin.

        Raises
        ------
        hikari.errors.Forbidden
            If you lack the `MANAGE_MESSAGES` permission.
        hikari.errors.NotFound
            If the message or channel do not exist.
        """
        route = routes.PUT_CHANNEL_PINS.compile(channel_id=channel_id, message_id=message_id)
        await self._request_json_response(route)

    async def delete_pinned_channel_message(self, channel_id: str, message_id: str) -> None:
        """Remove a pinned message from the channel.

        This will only unpin the message, not delete it.

        Parameters
        ----------
        channel_id : str
            The ID of the channel to remove a pin from.
        message_id : str
            The ID of the message to unpin.

        Raises
        ------
        hikari.errors.Forbidden
            If you lack the `MANAGE_MESSAGES` permission.
        hikari.errors.NotFound
            If the message or channel do not exist.
        """
        route = routes.DELETE_CHANNEL_PIN.compile(channel_id=channel_id, message_id=message_id)
        await self._request_json_response(route)

    async def list_guild_emojis(self, guild_id: str) -> typing.Sequence[more_typing.JSONObject]:
        """Get a list of the emojis for a given guild ID.

        Parameters
        ----------
        guild_id : str
            The ID of the guild to get the emojis for.

        Returns
        -------
        typing.Sequence[more_typing.JSONObject]
            A list of emoji objects.

        Raises
        ------
        hikari.errors.NotFound
            If the guild is not found.
        hikari.errors.Forbidden
            If you aren't a member of the guild.
        """
        route = routes.GET_GUILD_EMOJIS.compile(guild_id=guild_id)
        return await self._request_json_response(route)

    async def get_guild_emoji(self, guild_id: str, emoji_id: str) -> more_typing.JSONObject:
        """Get an emoji from a given guild and emoji IDs.

        Parameters
        ----------
        guild_id : str
            The ID of the guild to get the emoji from.
        emoji_id : str
            The ID of the emoji to get.

        Returns
        -------
        more_typing.JSONObject
            An emoji object.

        Raises
        ------
        hikari.errors.NotFound
            If either the guild or the emoji aren't found.
        hikari.errors.Forbidden
            If you aren't a member of said guild.
        """
        route = routes.GET_GUILD_EMOJI.compile(guild_id=guild_id, emoji_id=emoji_id)
        return await self._request_json_response(route)

    async def create_guild_emoji(
        self, guild_id: str, name: str, image: bytes, *, roles: typing.Sequence[str] = ..., reason: str = ...,
    ) -> more_typing.JSONObject:
        """Create a new emoji for a given guild.

        Parameters
        ----------
        guild_id : str
            The ID of the guild to create the emoji in.
        name : str
            The new emoji's name.
        image : bytes
            The `128x128` image in bytes form.
        roles : typing.Sequence[str]
            If specified, a list of roles for which the emoji will be whitelisted.
            If empty, all roles are whitelisted.
        reason : str
            If specified, the audit log reason explaining why the operation
            was performed.

        Returns
        -------
        more_typing.JSONObject
            The newly created emoji object.

        Raises
        ------
        ValueError
            If `image` is `None`.
        hikari.errors.NotFound
            If the guild is not found.
        hikari.errors.Forbidden
            If you either lack the `MANAGE_EMOJIS` permission or aren't a member of said guild.
        hikari.errors.BadRequest
            If you attempt to upload an image larger than `256kb`, an empty image or an invalid image format.
        """
        assertions.assert_not_none(image, "image must be a valid image")
        payload = {
            "name": name,
            "roles": [] if roles is ... else roles,
            "image": conversions.image_bytes_to_image_data(image),
        }
        route = routes.POST_GUILD_EMOJIS.compile(guild_id=guild_id)
        return await self._request_json_response(route, body=payload, reason=reason)

    async def modify_guild_emoji(
        self, guild_id: str, emoji_id: str, *, name: str = ..., roles: typing.Sequence[str] = ..., reason: str = ...,
    ) -> more_typing.JSONObject:
        """Edit an emoji of a given guild.

        Parameters
        ----------
        guild_id : str
            The ID of the guild to which the emoji to update belongs to.
        emoji_id : str
            The ID of the emoji to update.
        name : str
            If specified, a new emoji name string. Keep unspecified to keep the name the same.
        roles : typing.Sequence[str]
            If specified, a list of IDs for the new whitelisted roles.
            Set to an empty list to whitelist all roles.
            Keep unspecified to leave the same roles already set.
        reason : str
            If specified, the audit log reason explaining why the operation
            was performed.

        Returns
        -------
        more_typing.JSONObject
            The updated emoji object.

        Raises
        ------
        hikari.errors.NotFound
            If either the guild or the emoji aren't found.
        hikari.errors.Forbidden
            If you either lack the `MANAGE_EMOJIS` permission or are not a member of the given guild.
        """
        payload = {}
        conversions.put_if_specified(payload, "name", name)
        conversions.put_if_specified(payload, "roles", roles)
        route = routes.PATCH_GUILD_EMOJI.compile(guild_id=guild_id, emoji_id=emoji_id)
        return await self._request_json_response(route, body=payload, reason=reason)

    async def delete_guild_emoji(self, guild_id: str, emoji_id: str) -> None:
        """Delete an emoji from a given guild.

        Parameters
        ----------
        guild_id : str
            The ID of the guild to delete the emoji from.
        emoji_id : str
            The ID of the emoji to be deleted.

        Raises
        ------
        hikari.errors.NotFound
            If either the guild or the emoji aren't found.
        hikari.errors.Forbidden
            If you either lack the `MANAGE_EMOJIS` permission or aren't a member of said guild.
        """
        route = routes.DELETE_GUILD_EMOJI.compile(guild_id=guild_id, emoji_id=emoji_id)
        await self._request_json_response(route)

    async def create_guild(
        self,
        name: str,
        *,
        region: str = ...,
        icon: bytes = ...,
        verification_level: int = ...,
        default_message_notifications: int = ...,
        explicit_content_filter: int = ...,
        roles: typing.Sequence[more_typing.JSONObject] = ...,
        channels: typing.Sequence[more_typing.JSONObject] = ...,
    ) -> more_typing.JSONObject:
        """Create a new guild.

        !!! warning
            Can only be used by bots in less than `10` guilds.

        Parameters
        ----------
        name : str
            The name string for the new guild (`2-100` characters).
        region : str
            If specified, the voice region ID for new guild. You can use
            `REST.list_voice_regions` to see which region IDs are available.
        icon : bytes
            If specified, the guild icon image in bytes form.
        verification_level : int
            If specified, the verification level integer (`0-5`).
        default_message_notifications : int
            If specified, the default notification level integer (`0-1`).
        explicit_content_filter : int
            If specified, the explicit content filter integer (`0-2`).
        roles : typing.Sequence[more_typing.JSONObject]
            If specified, an array of role objects to be created alongside the
            guild. First element changes the `@everyone` role.
        channels : typing.Sequence[more_typing.JSONObject]
            If specified, an array of channel objects to be created alongside the guild.

        Returns
        -------
        more_typing.JSONObject
            The newly created guild object.

        Raises
        ------
        hikari.errors.Forbidden
            If you are on `10` or more guilds.
        hikari.errors.BadRequest
            If you provide unsupported fields like `parent_id` in channel objects.
        """
        payload = {"name": name}
        conversions.put_if_specified(payload, "region", region)
        conversions.put_if_specified(payload, "verification_level", verification_level)
        conversions.put_if_specified(payload, "default_message_notifications", default_message_notifications)
        conversions.put_if_specified(payload, "explicit_content_filter", explicit_content_filter)
        conversions.put_if_specified(payload, "roles", roles)
        conversions.put_if_specified(payload, "channels", channels)
        conversions.put_if_specified(payload, "icon", icon, conversions.image_bytes_to_image_data)
        route = routes.POST_GUILDS.compile()
        return await self._request_json_response(route, body=payload)

    async def get_guild(self, guild_id: str, *, with_counts: bool = True) -> more_typing.JSONObject:
        """Get the information for the guild with the given ID.

        Parameters
        ----------
        guild_id : str
            The ID of the guild to get.
        with_counts: bool
            `True` if you wish to receive approximate member and presence counts
            in the response, or `False` otherwise. Will default to `True`.

        Returns
        -------
        more_typing.JSONObject
            The requested guild object.

        Raises
        ------
        hikari.errors.NotFound
            If the guild is not found.
        hikari.errors.Forbidden
            If you do not have access to the guild.
        """
        route = routes.GET_GUILD.compile(guild_id=guild_id)
        return await self._request_json_response(
            route, query={"with_counts": "true" if with_counts is True else "false"}
        )

    async def get_guild_preview(self, guild_id: str) -> more_typing.JSONObject:
        """Get a public guild's preview object.

        Parameters
        ----------
        guild_id : str
            The ID of the guild to get the preview object of.

        Returns
        -------
        more_typing.JSONObject
            The requested guild preview object.

        !!! note
            Unlike other guild endpoints, the bot doesn't have to be in the
            target guild to get it's preview.

        Raises
        ------
        hikari.errors.NotFound
            If the guild is not found or it isn't `PUBLIC`.
        """
        route = routes.GET_GUILD_PREVIEW.compile(guild_id=guild_id)
        return await self._request_json_response(route)

    # pylint: disable=too-many-locals
    async def modify_guild(  # lgtm [py/similar-function]
        self,
        guild_id: str,
        *,
        name: str = ...,
        region: str = ...,
        verification_level: int = ...,
        default_message_notifications: int = ...,
        explicit_content_filter: int = ...,
        afk_channel_id: str = ...,
        afk_timeout: int = ...,
        icon: bytes = ...,
        owner_id: str = ...,
        splash: bytes = ...,
        system_channel_id: str = ...,
        reason: str = ...,
    ) -> more_typing.JSONObject:
        """Edit a given guild.

        Parameters
        ----------
        guild_id : str
            The ID of the guild to be edited.
        name : str
            If specified, the new name string for the guild (`2-100` characters).
        region : str
            If specified, the new voice region ID for guild. You can use
            `REST.list_voice_regions` to see which region IDs are available.
        verification_level : int
            If specified, the new verification level integer (`0-5`).
        default_message_notifications : int
            If specified, the new default notification level integer (`0-1`).
        explicit_content_filter : int
            If specified, the new explicit content filter integer (`0-2`).
        afk_channel_id : str
            If specified, the new ID for the AFK voice channel.
        afk_timeout : int
            If specified, the new AFK timeout period in seconds
        icon : bytes
            If specified, the new guild icon image in bytes form.
        owner_id : str
            If specified, the new ID of the new guild owner.
        splash : bytes
            If specified, the new new splash image in bytes form.
        system_channel_id : str
            If specified, the new ID of the new system channel.
        reason : str
            If specified, the audit log reason explaining why the operation
            was performed.

        Returns
        -------
        more_typing.JSONObject
            The edited guild object.

        Raises
        ------
        hikari.errors.NotFound
            If the guild is not found.
        hikari.errors.Forbidden
            If you lack the `MANAGE_GUILD` permission or are not in the guild.
        """
        payload = {}
        conversions.put_if_specified(payload, "name", name)
        conversions.put_if_specified(payload, "region", region)
        conversions.put_if_specified(payload, "verification_level", verification_level)
        conversions.put_if_specified(payload, "default_message_notifications", default_message_notifications)
        conversions.put_if_specified(payload, "explicit_content_filter", explicit_content_filter)
        conversions.put_if_specified(payload, "afk_channel_id", afk_channel_id)
        conversions.put_if_specified(payload, "afk_timeout", afk_timeout)
        conversions.put_if_specified(payload, "icon", icon, conversions.image_bytes_to_image_data)
        conversions.put_if_specified(payload, "owner_id", owner_id)
        conversions.put_if_specified(payload, "splash", splash, conversions.image_bytes_to_image_data)
        conversions.put_if_specified(payload, "system_channel_id", system_channel_id)
        route = routes.PATCH_GUILD.compile(guild_id=guild_id)
        return await self._request_json_response(route, body=payload, reason=reason)

    # pylint: enable=too-many-locals

    async def delete_guild(self, guild_id: str) -> None:
        """Permanently delete the given guild.

        You must be owner of the guild to perform this action.

        Parameters
        ----------
        guild_id : str
            The ID of the guild to be deleted.

        Raises
        ------
        hikari.errors.NotFound
            If the guild is not found.
        hikari.errors.Forbidden
            If you are not the guild owner.
        """
        route = routes.DELETE_GUILD.compile(guild_id=guild_id)
        await self._request_json_response(route)

    async def list_guild_channels(self, guild_id: str) -> typing.Sequence[more_typing.JSONObject]:
        """Get all the channels for a given guild.

        Parameters
        ----------
        guild_id : str
            The ID of the guild to get the channels from.

        Returns
        -------
        typing.Sequence[more_typing.JSONObject]
            A list of channel objects.

        Raises
        ------
        hikari.errors.NotFound
            If the guild is not found.
        hikari.errors.Forbidden
            If you are not in the guild.
        """
        route = routes.GET_GUILD_CHANNELS.compile(guild_id=guild_id)
        return await self._request_json_response(route)

    async def create_guild_channel(
        self,
        guild_id: str,
        name: str,
        *,
        type_: int = ...,
        position: int = ...,
        topic: str = ...,
        nsfw: bool = ...,
        rate_limit_per_user: int = ...,
        bitrate: int = ...,
        user_limit: int = ...,
        permission_overwrites: typing.Sequence[more_typing.JSONObject] = ...,
        parent_id: str = ...,
        reason: str = ...,
    ) -> more_typing.JSONObject:
        """Create a channel in a given guild.

        Parameters
        ----------
        guild_id : str
            The ID of the guild to create the channel in.
        name : str
            If specified, the name for the channel.This must be
            between `2` and `100` characters in length.
        type_: int
            If specified, the channel type integer (`0-6`).
        position : int
            If specified, the position to change the channel to.
        topic : str
            If specified, the topic to set. This is only applicable to
            text channels. This must be between `0` and `1024`
            characters in length.
        nsfw : bool
            If specified, whether the channel will be marked as NSFW.
            Only applicable to text channels.
        rate_limit_per_user : int
            If specified, the number of seconds the user has to wait before sending
            another message.  This will not apply to bots, or to members with
            `MANAGE_MESSAGES` or `MANAGE_CHANNEL` permissions. This must
            be between `0` and `21600` seconds.
        bitrate : int
            If specified, the bitrate in bits per second allowable for the channel.
            This only applies to voice channels and must be between `8000`
            and `96000` for normal servers or `8000` and `128000` for
            VIP servers.
        user_limit : int
            If specified, the max number of users to allow in a voice channel.
            This must be between `0` and `99` inclusive, where
            `0` implies no limit.
        permission_overwrites : typing.Sequence[more_typing.JSONObject]
            If specified, the list of permission overwrites that are category
            specific to replace the existing overwrites with.
        parent_id : str
            If specified, the parent category ID to set for the channel.
        reason : str
            If specified, the audit log reason explaining why the operation
            was performed.

        Returns
        -------
        more_typing.JSONObject
            The newly created channel object.

        Raises
        ------
        hikari.errors.NotFound
            If the guild is not found.
        hikari.errors.Forbidden
            If you lack the `MANAGE_CHANNEL` permission or are not in the guild.
        hikari.errors.BadRequest
            If you provide incorrect options for the corresponding channel type
            (e.g. a `bitrate` for a text channel).
        """
        payload = {}
        conversions.put_if_specified(payload, "name", name)
        conversions.put_if_specified(payload, "type", type_)
        conversions.put_if_specified(payload, "position", position)
        conversions.put_if_specified(payload, "topic", topic)
        conversions.put_if_specified(payload, "nsfw", nsfw)
        conversions.put_if_specified(payload, "rate_limit_per_user", rate_limit_per_user)
        conversions.put_if_specified(payload, "bitrate", bitrate)
        conversions.put_if_specified(payload, "user_limit", user_limit)
        conversions.put_if_specified(payload, "permission_overwrites", permission_overwrites)
        conversions.put_if_specified(payload, "parent_id", parent_id)
        route = routes.POST_GUILD_CHANNELS.compile(guild_id=guild_id)
        return await self._request_json_response(route, body=payload, reason=reason)

    async def modify_guild_channel_positions(
        self, guild_id: str, channel: typing.Tuple[str, int], *channels: typing.Tuple[str, int]
    ) -> None:
        """Edit the position of one or more given channels.

        Parameters
        ----------
        guild_id : str
            The ID of the guild in which to edit the channels.
        channel : typing.Tuple[str, int]
            The first channel to change the position of. This is a tuple of the channel ID and the integer position.
        *channels : typing.Tuple[str, int]
            Optional additional channels to change the position of. These must be tuples of the channel ID and the
            integer positions to change to.

        Raises
        ------
        hikari.errors.NotFound
            If either the guild or any of the channels aren't found.
        hikari.errors.Forbidden
            If you either lack the `MANAGE_CHANNELS` permission or are not a member of said guild or are not in
            the guild.
        hikari.errors.BadRequest
            If you provide anything other than the `id` and `position` fields for the channels.
        """
        payload = [{"id": ch[0], "position": ch[1]} for ch in (channel, *channels)]
        route = routes.PATCH_GUILD_CHANNELS.compile(guild_id=guild_id)
        await self._request_json_response(route, body=payload)

    async def get_guild_member(self, guild_id: str, user_id: str) -> more_typing.JSONObject:
        """Get a given guild member.

        Parameters
        ----------
        guild_id : str
            The ID of the guild to get the member from.
        user_id : str
            The ID of the member to get.

        Returns
        -------
        more_typing.JSONObject
            The requested member object.

        Raises
        ------
        hikari.errors.NotFound
            If either the guild or the member aren't found.
        hikari.errors.Forbidden
            If you don't have access to the target guild.
        """
        route = routes.GET_GUILD_MEMBER.compile(guild_id=guild_id, user_id=user_id)
        return await self._request_json_response(route)

    async def list_guild_members(
        self, guild_id: str, *, limit: int = ..., after: str = ...,
    ) -> typing.Sequence[more_typing.JSONObject]:
        """List all members of a given guild.

        Parameters
        ----------
        guild_id : str
            The ID of the guild to get the members from.
        limit : int
            If specified, the maximum number of members to return. This has to be between
            `1` and `1000` inclusive.
        after : str
            If specified, the highest ID in the previous page. This is used for retrieving more
            than `1000` members in a server using consecutive requests.

        Examples
        --------
            members = []
            last_id = 0

            while True:
                next_members = await client.list_guild_members(1234567890, limit=1000, after=last_id)
                members += next_members

                if len(next_members) == 1000:
                    last_id = next_members[-1]["user"]["id"]
                else:
                    break

        Returns
        -------
        more_typing.JSONObject
            A list of member objects.

        Raises
        ------
        hikari.errors.NotFound
            If the guild is not found.
        hikari.errors.Forbidden
            If you are not in the guild.
        hikari.errors.BadRequest
            If you provide invalid values for the `limit` or `after` fields.
        """
        query = {}
        conversions.put_if_specified(query, "limit", limit)
        conversions.put_if_specified(query, "after", after)
        route = routes.GET_GUILD_MEMBERS.compile(guild_id=guild_id)
        return await self._request_json_response(route, query=query)

    async def modify_guild_member(  # lgtm [py/similar-function]
        self,
        guild_id: str,
        user_id: str,
        *,
        nick: typing.Optional[str] = ...,
        roles: typing.Sequence[str] = ...,
        mute: bool = ...,
        deaf: bool = ...,
        channel_id: typing.Optional[str] = ...,
        reason: str = ...,
    ) -> None:
        """Edit a member of a given guild.

        Parameters
        ----------
        guild_id : str
            The ID of the guild to edit the member from.
        user_id : str
            The ID of the member to edit.
        nick : str, optional
            If specified, the new nickname string. Setting it to None
            explicitly will clear the nickname.
        roles : typing.Sequence[str]
            If specified, a list of role IDs the member should have.
        mute : bool
            If specified, whether the user should be muted in the voice channel
            or not.
        deaf : bool
            If specified, whether the user should be deafen in the voice channel
            or not.
        channel_id : str
            If specified, the ID of the channel to move the member to. Setting
            it to None explicitly will disconnect the user.
        reason : str
            If specified, the audit log reason explaining why the operation
            was performed.

        Raises
        ------
        hikari.errors.NotFound
            If either the guild, user, channel or any of the roles aren't found.
        hikari.errors.Forbidden
            If you lack any of the applicable permissions (`MANAGE_NICKNAMES`,
            `MANAGE_ROLES`, `MUTE_MEMBERS`,`DEAFEN_MEMBERS` or `MOVE_MEMBERS`).
            Note that to move a member you must also have permission to connect
            to the end channel. This will also be raised if you're not in the
            guild.
        hikari.errors.BadRequest
            If you pass `mute`, `deaf` or `channel_id` while the member is not connected to a voice channel.
        """
        payload = {}
        conversions.put_if_specified(payload, "nick", nick)
        conversions.put_if_specified(payload, "roles", roles)
        conversions.put_if_specified(payload, "mute", mute)
        conversions.put_if_specified(payload, "deaf", deaf)
        conversions.put_if_specified(payload, "channel_id", channel_id)
        route = routes.PATCH_GUILD_MEMBER.compile(guild_id=guild_id, user_id=user_id)
        await self._request_json_response(route, body=payload, reason=reason)

    async def modify_current_user_nick(self, guild_id: str, nick: typing.Optional[str], *, reason: str = ...) -> None:
        """Edit the current user's nickname for a given guild.

        Parameters
        ----------
        guild_id : str
            The ID of the guild you want to change the nick on.
        nick : str, optional
            The new nick string. Setting this to `None` clears the nickname.
        reason : str
            If specified, the audit log reason explaining why the operation
            was performed.

        Raises
        ------
        hikari.errors.NotFound
            If the guild is not found.
        hikari.errors.Forbidden
            If you lack the `CHANGE_NICKNAME` permission or are not in the guild.
        hikari.errors.BadRequest
            If you provide a disallowed nickname, one that is too long, or one that is empty.
        """
        payload = {"nick": nick}
        route = routes.PATCH_MY_GUILD_NICKNAME.compile(guild_id=guild_id)
        await self._request_json_response(route, body=payload, reason=reason)

    async def add_guild_member_role(self, guild_id: str, user_id: str, role_id: str, *, reason: str = ...) -> None:
        """Add a role to a given member.

        Parameters
        ----------
        guild_id : str
            The ID of the guild the member belongs to.
        user_id : str
            The ID of the member you want to add the role to.
        role_id : str
            The ID of the role you want to add.
        reason : str
            If specified, the audit log reason explaining why the operation
            was performed.

        Raises
        ------
        hikari.errors.NotFound
            If either the guild, member or role aren't found.
        hikari.errors.Forbidden
            If you lack the `MANAGE_ROLES` permission or are not in the guild.
        """
        route = routes.PUT_GUILD_MEMBER_ROLE.compile(guild_id=guild_id, user_id=user_id, role_id=role_id)
        await self._request_json_response(route, reason=reason)

    async def remove_guild_member_role(self, guild_id: str, user_id: str, role_id: str, *, reason: str = ...) -> None:
        """Remove a role from a given member.

        Parameters
        ----------
        guild_id : str
            The ID of the guild the member belongs to.
        user_id : str
            The ID of the member you want to remove the role from.
        role_id : str
            The ID of the role you want to remove.
        reason : str
            If specified, the audit log reason explaining why the operation
            was performed.

        Raises
        ------
        hikari.errors.NotFound
            If either the guild, member or role aren't found.
        hikari.errors.Forbidden
            If you lack the `MANAGE_ROLES` permission or are not in the guild.
        """
        route = routes.DELETE_GUILD_MEMBER_ROLE.compile(guild_id=guild_id, user_id=user_id, role_id=role_id)
        await self._request_json_response(route, reason=reason)

    async def remove_guild_member(self, guild_id: str, user_id: str, *, reason: str = ...) -> None:
        """Kick a user from a given guild.

        Parameters
        ----------
        guild_id: str
            The ID of the guild the member belongs to.
        user_id: str
            The ID of the member you want to kick.
        reason : str
            If specified, the audit log reason explaining why the operation
            was performed.

        Raises
        ------
        hikari.errors.NotFound
            If either the guild or member aren't found.
        hikari.errors.Forbidden
            If you lack the `KICK_MEMBERS` permission or are not in the guild.
        """
        route = routes.DELETE_GUILD_MEMBER.compile(guild_id=guild_id, user_id=user_id)
        await self._request_json_response(route, reason=reason)

    async def get_guild_bans(self, guild_id: str) -> typing.Sequence[more_typing.JSONObject]:
        """Get the bans for a given guild.

        Parameters
        ----------
        guild_id : str
            The ID of the guild you want to get the bans from.

        Returns
        -------
        typing.Sequence[more_typing.JSONObject]
            A list of ban objects.

        Raises
        ------
        hikari.errors.NotFound
            If the guild is not found.
        hikari.errors.Forbidden
            If you lack the `BAN_MEMBERS` permission or are not in the guild.
        """
        route = routes.GET_GUILD_BANS.compile(guild_id=guild_id)
        return await self._request_json_response(route)

    async def get_guild_ban(self, guild_id: str, user_id: str) -> more_typing.JSONObject:
        """Get a ban from a given guild.

        Parameters
        ----------
        guild_id : str
            The ID of the guild you want to get the ban from.
        user_id : str
            The ID of the user to get the ban information for.

        Returns
        -------
        more_typing.JSONObject
            A ban object for the requested user.

        Raises
        ------
        hikari.errors.NotFound
            If either the guild or the user aren't found, or if the user is not banned.
        hikari.errors.Forbidden
            If you lack the `BAN_MEMBERS` permission or are not in the guild.
        """
        route = routes.GET_GUILD_BAN.compile(guild_id=guild_id, user_id=user_id)
        return await self._request_json_response(route)

    async def create_guild_ban(
        self, guild_id: str, user_id: str, *, delete_message_days: int = ..., reason: str = ...,
    ) -> None:
        """Ban a user from a given guild.

        Parameters
        ----------
        guild_id : str
            The ID of the guild the member belongs to.
        user_id : str
            The ID of the member you want to ban.
        delete_message_days : str
            If specified, how many days of messages from the user should
            be removed.
        reason : str
            If specified, the audit log reason explaining why the operation
            was performed.

        Raises
        ------
        hikari.errors.NotFound
            If either the guild or member aren't found.
        hikari.errors.Forbidden
            If you lack the `BAN_MEMBERS` permission or are not in the guild.
        """
        query = {}
        conversions.put_if_specified(query, "delete-message-days", delete_message_days)
        conversions.put_if_specified(query, "reason", reason)
        route = routes.PUT_GUILD_BAN.compile(guild_id=guild_id, user_id=user_id)
        await self._request_json_response(route, query=query)

    async def remove_guild_ban(self, guild_id: str, user_id: str, *, reason: str = ...) -> None:
        """Un-bans a user from a given guild.

        Parameters
        ----------
        guild_id : str
            The ID of the guild to un-ban the user from.
        user_id : str
            The ID of the user you want to un-ban.
        reason : str
            If specified, the audit log reason explaining why the operation
            was performed.

        Raises
        ------
        hikari.errors.NotFound
            If either the guild or member aren't found, or the member is not banned.
        hikari.errors.Forbidden
            If you lack the `BAN_MEMBERS` permission or are not a in the guild.
        """
        route = routes.DELETE_GUILD_BAN.compile(guild_id=guild_id, user_id=user_id)
        await self._request_json_response(route, reason=reason)

    async def get_guild_roles(self, guild_id: str) -> typing.Sequence[more_typing.JSONObject]:
        """Get the roles for a given guild.

        Parameters
        ----------
        guild_id : str
            The ID of the guild you want to get the roles from.

        Returns
        -------
        typing.Sequence[more_typing.JSONObject]
            A list of role objects.

        Raises
        ------
        hikari.errors.NotFound
            If the guild is not found.
        hikari.errors.Forbidden
            If you're not in the guild.
        """
        route = routes.GET_GUILD_ROLES.compile(guild_id=guild_id)
        return await self._request_json_response(route)

    async def create_guild_role(
        self,
        guild_id: str,
        *,
        name: str = ...,
        permissions: int = ...,
        color: int = ...,
        hoist: bool = ...,
        mentionable: bool = ...,
        reason: str = ...,
    ) -> more_typing.JSONObject:
        """Create a new role for a given guild.

        Parameters
        ----------
        guild_id : str
            The ID of the guild you want to create the role on.
        name : str
            If specified, the new role name string.
        permissions : int
            If specified, the permissions integer for the role.
        color : int
            If specified, the color for the role.
        hoist : bool
            If specified, whether the role will be hoisted.
        mentionable : bool
           If specified, whether the role will be able to be mentioned by any user.
        reason : str
            If specified, the audit log reason explaining why the operation
            was performed.

        Returns
        -------
        more_typing.JSONObject
            The newly created role object.

        Raises
        ------
        hikari.errors.NotFound
            If the guild is not found.
        hikari.errors.Forbidden
            If you lack the `MANAGE_ROLES` permission or you're not in the guild.
        hikari.errors.BadRequest
            If you provide invalid values for the role attributes.
        """
        payload = {}
        conversions.put_if_specified(payload, "name", name)
        conversions.put_if_specified(payload, "permissions", permissions)
        conversions.put_if_specified(payload, "color", color)
        conversions.put_if_specified(payload, "hoist", hoist)
        conversions.put_if_specified(payload, "mentionable", mentionable)
        route = routes.POST_GUILD_ROLES.compile(guild_id=guild_id)
        return await self._request_json_response(route, body=payload, reason=reason)

    async def modify_guild_role_positions(
        self, guild_id: str, role: typing.Tuple[str, int], *roles: typing.Tuple[str, int]
    ) -> typing.Sequence[more_typing.JSONObject]:
        """Edit the position of two or more roles in a given guild.

        Parameters
        ----------
        guild_id : str
            The ID of the guild the roles belong to.
        role : typing.Tuple[str, int]
            The first role to move. This is a tuple of the role ID and the
            integer position.
        *roles : typing.Tuple[str, int]
            Optional extra roles to move. These must be tuples of the role ID
            and the integer position.

        Returns
        -------
        typing.Sequence[more_typing.JSONObject]
            A list of all the guild roles.

        Raises
        ------
        hikari.errors.NotFound
            If either the guild or any of the roles aren't found.
        hikari.errors.Forbidden
            If you lack the `MANAGE_ROLES` permission or you're not in the guild.
        hikari.errors.BadRequest
            If you provide invalid values for the `position` fields.
        """
        payload = [{"id": r[0], "position": r[1]} for r in (role, *roles)]
        route = routes.PATCH_GUILD_ROLES.compile(guild_id=guild_id)
        return await self._request_json_response(route, body=payload)

    async def modify_guild_role(  # lgtm [py/similar-function]
        self,
        guild_id: str,
        role_id: str,
        *,
        name: str = ...,
        permissions: int = ...,
        color: int = ...,
        hoist: bool = ...,
        mentionable: bool = ...,
        reason: str = ...,
    ) -> more_typing.JSONObject:
        """Edits a role in a given guild.

        Parameters
        ----------
        guild_id : str
            The ID of the guild the role belong to.
        role_id : str
            The ID of the role you want to edit.
        name : str
            If specified, the new role's name string.
        permissions : int
            If specified, the new permissions integer for the role.
        color : int
            If specified, the new color for the new role.
        hoist : bool
            If specified, whether the role should hoist or not.
        mentionable : bool
            If specified, whether the role should be mentionable or not.
        reason : str
            If specified, the audit log reason explaining why the operation
            was performed.

        Returns
        -------
        more_typing.JSONObject
            The edited role object.

        Raises
        ------
        hikari.errors.NotFound
            If either the guild or role aren't found.
        hikari.errors.Forbidden
            If you lack the `MANAGE_ROLES` permission or you're not in the guild.
        hikari.errors.BadRequest
            If you provide invalid values for the role attributes.
        """
        payload = {}
        conversions.put_if_specified(payload, "name", name)
        conversions.put_if_specified(payload, "permissions", permissions)
        conversions.put_if_specified(payload, "color", color)
        conversions.put_if_specified(payload, "hoist", hoist)
        conversions.put_if_specified(payload, "mentionable", mentionable)
        route = routes.PATCH_GUILD_ROLE.compile(guild_id=guild_id, role_id=role_id)
        return await self._request_json_response(route, body=payload, reason=reason)

    async def delete_guild_role(self, guild_id: str, role_id: str) -> None:
        """Delete a role from a given guild.

        Parameters
        ----------
        guild_id : str
            The ID of the guild you want to remove the role from.
        role_id : str
            The ID of the role you want to delete.

        Raises
        ------
        hikari.errors.NotFound
            If either the guild or the role aren't found.
        hikari.errors.Forbidden
            If you lack the `MANAGE_ROLES` permission or are not in the guild.
        """
        route = routes.DELETE_GUILD_ROLE.compile(guild_id=guild_id, role_id=role_id)
        await self._request_json_response(route)

    async def get_guild_prune_count(self, guild_id: str, days: int) -> int:
        """Get the estimated prune count for a given guild.

        Parameters
        ----------
        guild_id : str
            The ID of the guild you want to get the count for.
        days : int
            The number of days to count prune for (at least `1`).

        Returns
        -------
        int
            The number of members estimated to be pruned.

        Raises
        ------
        hikari.errors.NotFound
            If the guild is not found.
        hikari.errors.Forbidden
            If you lack the `KICK_MEMBERS` or you are not in the guild.
        hikari.errors.BadRequest
            If you pass an invalid amount of days.
        """
        payload = {"days": days}
        route = routes.GET_GUILD_PRUNE.compile(guild_id=guild_id)
        result = await self._request_json_response(route, query=payload)
        return int(result["pruned"])

    async def begin_guild_prune(
        self, guild_id: str, days: int, *, compute_prune_count: bool = ..., reason: str = ...,
    ) -> typing.Optional[int]:
        """Prune members of a given guild based on the number of inactive days.

        Parameters
        ----------
        guild_id : str
            The ID of the guild you want to prune member of.
        days : int
            The number of inactivity days you want to use as filter.
        compute_prune_count : bool
            Whether a count of pruned members is returned or not.
            Discouraged for large guilds out of politeness.
        reason : str
            If specified, the audit log reason explaining why the operation
            was performed.

        Returns
        -------
        int, optional
            The number of members who were kicked if `compute_prune_count`
            is True, else None.

        Raises
        ------
        hikari.errors.NotFound
            If the guild is not found:
        hikari.errors.Forbidden
            If you lack the `KICK_MEMBER` permission or are not in the guild.
        hikari.errors.BadRequest
            If you provide invalid values for the `days` or `compute_prune_count` fields.
        """
        query = {"days": days}
        conversions.put_if_specified(query, "compute_prune_count", compute_prune_count, lambda v: str(v).lower())
        route = routes.POST_GUILD_PRUNE.compile(guild_id=guild_id)
        result = await self._request_json_response(route, query=query, reason=reason)

        try:
            return int(result["pruned"])
        except (TypeError, KeyError):
            return None

    async def get_guild_voice_regions(self, guild_id: str) -> typing.Sequence[more_typing.JSONObject]:
        """Get the voice regions for a given guild.

        Parameters
        ----------
        guild_id : str
            The ID of the guild to get the voice regions for.

        Returns
        -------
        typing.Sequence[more_typing.JSONObject]
            A list of voice region objects.

        Raises
        ------
        hikari.errors.NotFound
            If the guild is not found.
        hikari.errors.Forbidden
            If you are not in the guild.
        """
        route = routes.GET_GUILD_VOICE_REGIONS.compile(guild_id=guild_id)
        return await self._request_json_response(route)

    async def get_guild_invites(self, guild_id: str) -> typing.Sequence[more_typing.JSONObject]:
        """Get the invites for a given guild.

        Parameters
        ----------
        guild_id : str
            The ID of the guild to get the invites for.

        Returns
        -------
        typing.Sequence[more_typing.JSONObject]
            A list of invite objects (with metadata).

        Raises
        ------
        hikari.errors.NotFound
            If the guild is not found.
        hikari.errors.Forbidden
            If you lack the `MANAGE_GUILD` permission or are not in the guild.
        """
        route = routes.GET_GUILD_INVITES.compile(guild_id=guild_id)
        return await self._request_json_response(route)

    async def get_guild_integrations(self, guild_id: str) -> typing.Sequence[more_typing.JSONObject]:
        """Get the integrations for a given guild.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to get the integrations for.

        Returns
        -------
        typing.Sequence[more_typing.JSONObject]
            A list of integration objects.

        Raises
        ------
        hikari.errors.NotFound
            If the guild is not found.
        hikari.errors.Forbidden
            If you lack the `MANAGE_GUILD` permission or are not in the guild.
        """
        route = routes.GET_GUILD_INTEGRATIONS.compile(guild_id=guild_id)
        return await self._request_json_response(route)

    async def modify_guild_integration(
        self,
        guild_id: str,
        integration_id: str,
        *,
        expire_behaviour: int = ...,
        expire_grace_period: int = ...,
        enable_emojis: bool = ...,
        reason: str = ...,
    ) -> None:
        """Edit an integrations for a given guild.

        Parameters
        ----------
        guild_id : str
            The ID of the guild to which the integration belongs to.
        integration_id : str
            The ID of the integration.
        expire_behaviour : int
            If specified, the behaviour for when an integration subscription
            lapses.
        expire_grace_period : int
            If specified, time interval in seconds in which the integration
            will ignore lapsed subscriptions.
        enable_emojis : bool
            If specified, whether emojis should be synced for this integration.
        reason : str
            If specified, the audit log reason explaining why the operation
            was performed.

        Raises
        ------
        hikari.errors.NotFound
            If either the guild or the integration aren't found.
        hikari.errors.Forbidden
            If you lack the `MANAGE_GUILD` permission or are not in the guild.
        """
        payload = {}
        conversions.put_if_specified(payload, "expire_behaviour", expire_behaviour)
        conversions.put_if_specified(payload, "expire_grace_period", expire_grace_period)
        # This is inconsistently named in their API.
        conversions.put_if_specified(payload, "enable_emoticons", enable_emojis)
        route = routes.PATCH_GUILD_INTEGRATION.compile(guild_id=guild_id, integration_id=integration_id)
        await self._request_json_response(route, body=payload, reason=reason)

    async def delete_guild_integration(self, guild_id: str, integration_id: str, *, reason: str = ...) -> None:
        """Delete an integration for the given guild.

        Parameters
        ----------
        guild_id : str
            The ID of the guild to which the integration belongs to.
        integration_id : str
            The ID of the integration to delete.
        reason : str
            If specified, the audit log reason explaining why the operation
            was performed.

        Raises
        ------
        hikari.errors.NotFound
                If either the guild or the integration aren't found.
        hikari.errors.Forbidden
                If you lack the `MANAGE_GUILD` permission or are not in the guild.
        """
        route = routes.DELETE_GUILD_INTEGRATION.compile(guild_id=guild_id, integration_id=integration_id)
        await self._request_json_response(route, reason=reason)

    async def sync_guild_integration(self, guild_id: str, integration_id: str) -> None:
        """Sync the given integration.

        Parameters
        ----------
        guild_id : str
            The ID of the guild to which the integration belongs to.
        integration_id : str
            The ID of the integration to sync.

        Raises
        ------
        hikari.errors.NotFound
            If either the guild or the integration aren't found.
        hikari.errors.Forbidden
            If you lack the `MANAGE_GUILD` permission or are not in the guild.
        """
        route = routes.POST_GUILD_INTEGRATION_SYNC.compile(guild_id=guild_id, integration_id=integration_id)
        await self._request_json_response(route)

    async def get_guild_embed(self, guild_id: str) -> more_typing.JSONObject:
        """Get the embed for a given guild.

        Parameters
        ----------
        guild_id : str
            The ID of the guild to get the embed for.

        Returns
        -------
        more_typing.JSONObject
            A guild embed object.

        Raises
        ------
        hikari.errors.NotFound
            If the guild is not found.
        hikari.errors.Forbidden
            If you either lack the `MANAGE_GUILD` permission or are not in the guild.
        """
        route = routes.GET_GUILD_EMBED.compile(guild_id=guild_id)
        return await self._request_json_response(route)

    async def modify_guild_embed(
        self, guild_id: str, *, channel_id: typing.Optional[str] = ..., enabled: bool = ..., reason: str = ...,
    ) -> more_typing.JSONObject:
        """Edit the embed for a given guild.

        Parameters
        ----------
        guild_id : str
            The ID of the guild to edit the embed for.
        channel_id : str, optional
            If specified, the channel that this embed's invite should target.
            Set to None to disable invites for this embed.
        enabled : bool
            If specified, whether this embed should be enabled.
        reason : str
            If specified, the audit log reason explaining why the operation
            was performed.

        Returns
        -------
        more_typing.JSONObject
            The updated embed object.

        Raises
        ------
        hikari.errors.NotFound
            If the guild is not found.
        hikari.errors.Forbidden
            If you either lack the `MANAGE_GUILD` permission or are not in the guild.
        """
        payload = {}
        conversions.put_if_specified(payload, "channel_id", channel_id)
        conversions.put_if_specified(payload, "enabled", enabled)
        route = routes.PATCH_GUILD_EMBED.compile(guild_id=guild_id)
        return await self._request_json_response(route, body=payload, reason=reason)

    async def get_guild_vanity_url(self, guild_id: str) -> more_typing.JSONObject:
        """Get the vanity URL for a given guild.

        Parameters
        ----------
        guild_id : str
            The ID of the guild to get the vanity URL for.

        Returns
        -------
        more_typing.JSONObject
            A partial invite object containing the vanity URL in the `code` field.

        Raises
        ------
        hikari.errors.NotFound
            If the guild is not found.
        hikari.errors.Forbidden
            If you either lack the `MANAGE_GUILD` permission or are not in the guild.
        """
        route = routes.GET_GUILD_VANITY_URL.compile(guild_id=guild_id)
        return await self._request_json_response(route)

    def get_guild_widget_image_url(self, guild_id: str, *, style: str = ...) -> str:
        """Get the URL for a guild widget.

        Parameters
        ----------
        guild_id : str
            The guild ID to use for the widget.
        style : str
            If specified, the style of the widget.

        Returns
        -------
        str
            A URL to retrieve a PNG widget for your guild.

        !!! note
            This does not actually make any form of request, and shouldn't be
            awaited. Thus, it doesn't have rate limits either.

        !!! warning
            The guild must have the widget enabled in the guild settings for
            this to be valid.
        """
        query = "" if style is ... else f"?style={style}"
        route = routes.GET_GUILD_WIDGET_IMAGE.compile(guild_id=guild_id)
        return route.create_url(self.base_url) + query

    async def get_invite(self, invite_code: str, *, with_counts: bool = ...) -> more_typing.JSONObject:
        """Getsthe given invite.

        Parameters
        ----------
        invite_code : str
            The ID for wanted invite.
        with_counts : bool
            If specified, whether to attempt to count the number of
            times the invite has been used.

        Returns
        -------
        more_typing.JSONObject
            The requested invite object.

        Raises
        ------
        hikari.errors.NotFound
            If the invite is not found.
        """
        query = {}
        conversions.put_if_specified(query, "with_counts", with_counts, lambda v: str(v).lower())
        route = routes.GET_INVITE.compile(invite_code=invite_code)
        return await self._request_json_response(route, query=query)

    async def delete_invite(self, invite_code: str) -> None:
        """Delete a given invite.

        Parameters
        ----------
        invite_code : str
            The ID for the invite to be deleted.

        Returns
        -------
        None # Marker
            Nothing, unlike what the API specifies. This is done to maintain
            consistency with other calls of a similar nature in this API wrapper.

        Raises
        ------
        hikari.errors.NotFound
            If the invite is not found.
        hikari.errors.Forbidden
            If you lack either `MANAGE_CHANNELS` on the channel the invite
            belongs to or `MANAGE_GUILD` for guild-global delete.
        """
        route = routes.DELETE_INVITE.compile(invite_code=invite_code)
        return await self._request_json_response(route)

    async def get_current_user(self) -> more_typing.JSONObject:
        """Get the current user that is represented by token given to the client.

        Returns
        -------
        more_typing.JSONObject
            The current user object.
        """
        route = routes.GET_MY_USER.compile()
        return await self._request_json_response(route)

    async def get_user(self, user_id: str) -> more_typing.JSONObject:
        """Get a given user.

        Parameters
        ----------
        user_id : str
            The ID of the user to get.

        Returns
        -------
        more_typing.JSONObject
            The requested user object.

        Raises
        ------
        hikari.errors.NotFound
            If the user is not found.
        """
        route = routes.GET_USER.compile(user_id=user_id)
        return await self._request_json_response(route)

    async def modify_current_user(
        self, *, username: str = ..., avatar: typing.Optional[bytes] = ...,
    ) -> more_typing.JSONObject:
        """Edit the current user.

        Parameters
        ----------
        username : str
            If specified, the new username string.
        avatar : bytes, optional
            If specified, the new avatar image in bytes form.
            If it is None, the avatar is removed.

        !!! warning
            Verified bots will not be able to change their username on this
            endpoint, and should contact Discord support instead to change
            this value.

        Returns
        -------
        more_typing.JSONObject
            The updated user object.

        Raises
        ------
        hikari.errors.BadRequest
            If you pass username longer than the limit (`2-32`) or an invalid image.
        """
        payload = {}
        conversions.put_if_specified(payload, "username", username)
        conversions.put_if_specified(payload, "avatar", avatar, conversions.image_bytes_to_image_data)
        route = routes.PATCH_MY_USER.compile()
        return await self._request_json_response(route, body=payload)

    async def get_current_user_connections(self) -> typing.Sequence[more_typing.JSONObject]:
        """Get the current user's connections.

        This endpoint can be used with both `Bearer` and `Bot` tokens but
        will usually return an empty list for bots (with there being some exceptions
        to this, like user accounts that have been converted to bots).

        Returns
        -------
        typing.Sequence[more_typing.JSONObject]
            A list of connection objects.
        """
        route = routes.GET_MY_CONNECTIONS.compile()
        return await self._request_json_response(route)

    async def get_current_user_guilds(
        self, *, before: str = ..., after: str = ..., limit: int = ...,
    ) -> typing.Sequence[more_typing.JSONObject]:
        """Get the guilds the current user is in.

        Parameters
        ----------
        before : str
            If specified, the guild ID to get guilds before it.

        after : str
            If specified, the guild ID to get guilds after it.

        limit : int
            If specified, the limit of guilds to get. Has to be between
            `1` and `100`.

        Returns
        -------
        typing.Sequence[more_typing.JSONObject]
            A list of partial guild objects.

        Raises
        ------
        hikari.errors.BadRequest
            If you pass both `before` and `after` or an
            invalid value for `limit`.
        """
        query = {}
        conversions.put_if_specified(query, "before", before)
        conversions.put_if_specified(query, "after", after)
        conversions.put_if_specified(query, "limit", limit)
        route = routes.GET_MY_GUILDS.compile()
        return await self._request_json_response(route, query=query)

    async def leave_guild(self, guild_id: str) -> None:
        """Make the current user leave a given guild.

        Parameters
        ----------
        guild_id : str
            The ID of the guild to leave.

        Raises
        ------
        hikari.errors.NotFound
            If the guild is not found.
        """
        route = routes.DELETE_MY_GUILD.compile(guild_id=guild_id)
        await self._request_json_response(route)

    async def create_dm(self, recipient_id: str) -> more_typing.JSONObject:
        """Create a new DM channel with a given user.

        Parameters
        ----------
        recipient_id : str
            The ID of the user to create the new DM channel with.

        Returns
        -------
        more_typing.JSONObject
            The newly created DM channel object.

        Raises
        ------
        hikari.errors.NotFound
            If the recipient is not found.
        """
        payload = {"recipient_id": recipient_id}
        route = routes.POST_MY_CHANNELS.compile()
        return await self._request_json_response(route, body=payload)

    async def list_voice_regions(self) -> typing.Sequence[more_typing.JSONObject]:
        """Get the voice regions that are available.

        Returns
        -------
        typing.Sequence[more_typing.JSONObject]
            A list of voice regions available

        !!! note
            This does not include VIP servers.
        """
        route = routes.GET_VOICE_REGIONS.compile()
        return await self._request_json_response(route)

    async def create_webhook(
        self, channel_id: str, name: str, *, avatar: bytes = ..., reason: str = ...,
    ) -> more_typing.JSONObject:
        """Create a webhook for a given channel.

        Parameters
        ----------
        channel_id : str
            The ID of the channel for webhook to be created in.
        name : str
            The webhook's name string.
        avatar : bytes
            If specified, the avatar image in bytes form.
        reason : str
            If specified, the audit log reason explaining why the operation
            was performed.

        Returns
        -------
        more_typing.JSONObject
            The newly created webhook object.

        Raises
        ------
        hikari.errors.NotFound
            If the channel is not found.
        hikari.errors.Forbidden
            If you either lack the `MANAGE_WEBHOOKS` permission or
            can not see the given channel.
        hikari.errors.BadRequest
            If the avatar image is too big or the format is invalid.
        """
        payload = {"name": name}
        conversions.put_if_specified(payload, "avatar", avatar, conversions.image_bytes_to_image_data)
        route = routes.POST_CHANNEL_WEBHOOKS.compile(channel_id=channel_id)
        return await self._request_json_response(route, body=payload, reason=reason)

    async def get_channel_webhooks(self, channel_id: str) -> typing.Sequence[more_typing.JSONObject]:
        """Get all webhooks from a given channel.

        Parameters
        ----------
        channel_id : str
            The ID of the channel to get the webhooks from.

        Returns
        -------
        typing.Sequence[more_typing.JSONObject]
            A list of webhook objects for the give channel.

        Raises
        ------
        hikari.errors.NotFound
            If the channel is not found.
        hikari.errors.Forbidden
            If you either lack the `MANAGE_WEBHOOKS` permission or
            can not see the given channel.
        """
        route = routes.GET_CHANNEL_WEBHOOKS.compile(channel_id=channel_id)
        return await self._request_json_response(route)

    async def get_guild_webhooks(self, guild_id: str) -> typing.Sequence[more_typing.JSONObject]:
        """Get all webhooks for a given guild.

        Parameters
        ----------
        guild_id : str
            The ID for the guild to get the webhooks from.

        Returns
        -------
        typing.Sequence[more_typing.JSONObject]
            A list of webhook objects for the given guild.

        Raises
        ------
        hikari.errors.NotFound
            If the guild is not found.
        hikari.errors.Forbidden
            If you either lack the `MANAGE_WEBHOOKS` permission or
            aren't a member of the given guild.
        """
        route = routes.GET_GUILD_WEBHOOKS.compile(guild_id=guild_id)
        return await self._request_json_response(route)

    async def get_webhook(self, webhook_id: str, *, webhook_token: str = ...) -> more_typing.JSONObject:
        """Get a given webhook.

        Parameters
        ----------
        webhook_id : str
            The ID of the webhook to get.
        webhook_token : str
            If specified, the webhook token to use to get it (bypassing bot authorization).

        Returns
        -------
        more_typing.JSONObject
            The requested webhook object.

        Raises
        ------
        hikari.errors.NotFound
            If the webhook is not found.
        hikari.errors.Forbidden
            If you're not in the guild that owns this webhook or
            lack the `MANAGE_WEBHOOKS` permission.
        hikari.errors.Unauthorized
            If you pass a token that's invalid for the target webhook.
        """
        if webhook_token is ...:
            route = routes.GET_WEBHOOK.compile(webhook_id=webhook_id)
        else:
            route = routes.GET_WEBHOOK_WITH_TOKEN.compile(webhook_id=webhook_id, webhook_token=webhook_token)
        return await self._request_json_response(route, suppress_authorization_header=webhook_token is not ...)

    async def modify_webhook(
        self,
        webhook_id: str,
        *,
        webhook_token: str = ...,
        name: str = ...,
        avatar: typing.Optional[bytes] = ...,
        channel_id: str = ...,
        reason: str = ...,
    ) -> more_typing.JSONObject:
        """Edit a given webhook.

        Parameters
        ----------
        webhook_id : str
            The ID of the webhook to edit.
        webhook_token : str
            If specified, the webhook token to use to modify it (bypassing bot authorization).
        name : str
            If specified, the new name string.
        avatar : bytes
            If specified, the new avatar image in bytes form. If None, then
            it is removed.
        channel_id : str
            If specified, the ID of the new channel the given
            webhook should be moved to.
        reason : str
            If specified, the audit log reason explaining why the operation
            was performed.

        Returns
        -------
        more_typing.JSONObject
            The updated webhook object.

        Raises
        ------
        hikari.errors.NotFound
            If either the webhook or the channel aren't found.
        hikari.errors.Forbidden
            If you either lack the `MANAGE_WEBHOOKS` permission or
            aren't a member of the guild this webhook belongs to.
        hikari.errors.Unauthorized
            If you pass a token that's invalid for the target webhook.
        """
        payload = {}
        conversions.put_if_specified(payload, "name", name)
        conversions.put_if_specified(payload, "channel_id", channel_id)
        conversions.put_if_specified(payload, "avatar", avatar, conversions.image_bytes_to_image_data)
        if webhook_token is ...:
            route = routes.PATCH_WEBHOOK.compile(webhook_id=webhook_id)
        else:
            route = routes.PATCH_WEBHOOK_WITH_TOKEN.compile(webhook_id=webhook_id, webhook_token=webhook_token)
        return await self._request_json_response(
            route, body=payload, reason=reason, suppress_authorization_header=webhook_token is not ...,
        )

    async def delete_webhook(self, webhook_id: str, *, webhook_token: str = ...) -> None:
        """Delete a given webhook.

        Parameters
        ----------
        webhook_id : str
            The ID of the webhook to delete
        webhook_token : str
            If specified, the webhook token to use to
            delete it (bypassing bot authorization).

        Raises
        ------
        hikari.errors.NotFound
            If the webhook is not found.
        hikari.errors.Forbidden
            If you either lack the `MANAGE_WEBHOOKS` permission or
            aren't a member of the guild this webhook belongs to.
        hikari.errors.Unauthorized
            If you pass a token that's invalid for the target webhook.
        """
        if webhook_token is ...:
            route = routes.DELETE_WEBHOOK.compile(webhook_id=webhook_id)
        else:
            route = routes.DELETE_WEBHOOK_WITH_TOKEN.compile(webhook_id=webhook_id, webhook_token=webhook_token)
        await self._request_json_response(route, suppress_authorization_header=webhook_token is not ...)

    async def execute_webhook(  # pylint:disable=too-many-locals
        self,
        webhook_id: str,
        webhook_token: str,
        *,
        content: str = ...,
        username: str = ...,
        avatar_url: str = ...,
        tts: bool = ...,
        wait: bool = ...,
        files: typing.Sequence[_files.BaseStream] = ...,
        embeds: typing.Sequence[more_typing.JSONObject] = ...,
        allowed_mentions: more_typing.JSONObject = ...,
    ) -> typing.Optional[more_typing.JSONObject]:
        """Execute a webhook to create a message in its channel.

        Parameters
        ----------
        webhook_id : str
            The ID of the webhook to execute.
        webhook_token : str
            The token of the webhook to execute.
        content : str
            If specified, the webhook message content to send.
        username : str
            If specified, the username to override the webhook's username
            for this request.
        avatar_url : str
            If specified, the url of an image to override the webhook's
            avatar with for this request.
        tts : bool
            If specified, whether this webhook should create a TTS message.
        wait : bool
            If specified, whether this request should wait for the webhook
            to be executed and return the resultant message object.
        files : typing.Sequence[hikari.files.BaseStream]
            If specified, the optional file objects to upload.
        embeds : typing.Sequence[more_typing.JSONObject]
            If specified, the sequence of embed objects that will be sent
            with this message.
        allowed_mentions : more_typing.JSONObject
            If specified, the mentions to parse from the `content`.
            If not specified, will parse all mentions from the `content`.

        Returns
        -------
        more_typing.JSONObject, optional
            The created message object if `wait` is `True`, else
            `None`.

        Raises
        ------
        hikari.errors.NotFound
            If the channel ID or webhook ID is not found.
        hikari.errors.BadRequest
            This can be raised if the file is too large; if the embed exceeds
            the defined limits; if the message content is specified only and
            empty or greater than `2000` characters; if neither content, file
            or embed are specified; if there is a duplicate id in only of the
            fields in `allowed_mentions`; if you specify to parse all
            users/roles mentions but also specify which users/roles to parse
            only.
        hikari.errors.Forbidden
            If you lack permissions to send to this channel.
        hikari.errors.Unauthorized
            If you pass a token that's invalid for the target webhook.
        """
        form = aiohttp.FormData()

        json_payload = {}
        conversions.put_if_specified(json_payload, "content", content)
        conversions.put_if_specified(json_payload, "username", username)
        conversions.put_if_specified(json_payload, "avatar_url", avatar_url)
        conversions.put_if_specified(json_payload, "tts", tts)
        conversions.put_if_specified(json_payload, "embeds", embeds)
        conversions.put_if_specified(json_payload, "allowed_mentions", allowed_mentions)

        form.add_field("payload_json", json.dumps(json_payload), content_type="application/json")

        if files is ...:
            files = more_collections.EMPTY_SEQUENCE

        for i, file in enumerate(files):
            form.add_field(f"file{i}", file, filename=file.name, content_type="application/octet-stream")

        query = {}
        conversions.put_if_specified(query, "wait", wait, lambda v: str(v).lower())

        route = routes.POST_WEBHOOK_WITH_TOKEN.compile(webhook_id=webhook_id, webhook_token=webhook_token)
        return await self._request_json_response(route, body=form, query=query, suppress_authorization_header=True)

    ##########
    # OAUTH2 #
    ##########

    async def get_current_application_info(self) -> more_typing.JSONObject:
        """Get the current application information.

        Returns
        -------
        more_typing.JSONObject
            An application info object.
        """
        route = routes.GET_MY_APPLICATION.compile()
        return await self._request_json_response(route)
