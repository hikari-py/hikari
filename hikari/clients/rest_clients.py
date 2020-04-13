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
"""Marshall wrappings for the REST implementation in :mod:`hikari.net.rest`.

This provides an object-oriented interface for interacting with discord's REST
API.
"""

__all__ = ["RESTClient"]

import asyncio
import datetime
import types

import typing

from hikari.clients import configs
from hikari.internal import assertions
from hikari.internal import conversions
from hikari.internal import more_collections
from hikari.net import rest
from hikari import audit_logs
from hikari import channels as _channels
from hikari import colors
from hikari import embeds as _embeds
from hikari import emojis
from hikari import gateway_entities
from hikari import guilds
from hikari import invites
from hikari import media
from hikari import messages as _messages
from hikari import oauth2
from hikari import permissions as _permissions
from hikari import snowflakes
from hikari import users
from hikari import voices
from hikari import webhooks


def _get_member_id(member: guilds.GuildMember) -> str:
    return str(member.user.id)


class RESTClient:
    """
    A marshalling object-oriented HTTP API.

    This component bridges the basic HTTP API exposed by
    :obj:`hikari.net.rest.LowLevelRestfulClient` and wraps it in a unit of
    processing that can handle parsing API objects into Hikari entity objects.

    Parameters
    ----------
    config : :obj:`hikari.clients.configs.RESTConfig`
        A HTTP configuration object.

    Note
    ----
    For all endpoints where a ``reason`` argument is provided, this may be a
    string inclusively between ``0`` and ``512`` characters length, with any
    additional characters being cut off.
    """

    def __init__(self, config: configs.RESTConfig) -> None:
        self._session = rest.LowLevelRestfulClient(
            allow_redirects=config.allow_redirects,
            connector=config.tcp_connector,
            proxy_headers=config.proxy_headers,
            proxy_auth=config.proxy_auth,
            ssl_context=config.ssl_context,
            verify_ssl=config.verify_ssl,
            timeout=config.request_timeout,
            token=config.token,
            version=config.rest_version,
        )

    async def close(self) -> None:
        """Shut down the REST client safely."""
        await self._session.close()

    async def __aenter__(self) -> "RESTClient":
        return self

    async def __aexit__(
        self, exc_type: typing.Type[BaseException], exc_val: BaseException, exc_tb: types.TracebackType
    ) -> None:
        await self.close()

    async def fetch_gateway_url(self) -> str:
        """Get a generic url used for establishing a Discord gateway connection.

        Returns
        -------
        :obj:`str`
            A static URL to use to connect to the gateway with.

        Note
        ----
        Users are expected to attempt to cache this result.
        """
        return await self._session.get_gateway()

    async def fetch_gateway_bot(self) -> gateway_entities.GatewayBot:
        """Get bot specific gateway information.

        Returns
        -------
        :obj:`hikari.gateway_entities.GatewayBot`
            The bot specific gateway information object.

        Note
        ----
        Unlike :meth:`fetch_gateway_url`, this requires a valid token to work.
        """
        payload = await self._session.get_gateway_bot()
        return gateway_entities.GatewayBot.deserialize(payload)

    async def fetch_audit_log(
        self,
        guild: snowflakes.HashableT[guilds.Guild],
        *,
        user: snowflakes.HashableT[users.User] = ...,
        action_type: typing.Union[audit_logs.AuditLogEventType, int] = ...,
        limit: int = ...,
        before: typing.Union[datetime.datetime, snowflakes.HashableT[audit_logs.AuditLogEntry]] = ...,
    ) -> audit_logs.AuditLog:
        """Get an audit log object for the given guild.

        Parameters
        ----------
        guild : :obj:`typing.Union` [ :obj:`hikari.guilds.Guild`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the guild to get the audit logs for.
        user : :obj:`typing.Union` [ :obj:`hikari.users.User`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            If specified, the object or ID of the user to filter by.
        action_type : :obj:`typing.Union` [ :obj:`hikari.audit_logs.AuditLogEventType`, :obj:`int` ]
            If specified, the action type to look up. Passing a raw integer
            for this may lead to unexpected behaviour.
        limit : :obj:`int`
            If specified, the limit to apply to the number of records.
            Defaults to ``50``. Must be between ``1`` and ``100`` inclusive.
        before : :obj:`typing.Union` [ :obj:`datetime.datetime`, :obj:`hikari.audit_logs.AuditLogEntry`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            If specified, the object or ID of the entry that all retrieved
            entries should have occurred befor.

        Returns
        -------
        :obj:`hikari.audit_logs.AuditLog`
            An audit log object.

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you lack the given permissions to view an audit log.
        :obj:`hikari.errors.NotFoundHTTPError`
            If the guild does not exist.
        """
        if isinstance(before, datetime.datetime):
            before = str(snowflakes.Snowflake.from_datetime(before))
        elif before is not ...:
            before = str(before.id if isinstance(before, snowflakes.UniqueEntity) else int(before))
        payload = await self._session.get_guild_audit_log(
            guild_id=str(guild.id if isinstance(guilds, snowflakes.UniqueEntity) else int(guild)),
            user_id=(
                str(user.id if isinstance(user, snowflakes.UniqueEntity) else int(user)) if user is not ... else ...
            ),
            action_type=action_type,
            limit=limit,
            before=before,
        )
        return audit_logs.AuditLog.deserialize(payload)

    def fetch_audit_log_entries_before(
        self,
        guild: snowflakes.HashableT[guilds.Guild],
        *,
        before: typing.Union[datetime.datetime, snowflakes.HashableT[audit_logs.AuditLogEntry], None] = None,
        user: snowflakes.HashableT[users.User] = ...,
        action_type: typing.Union[audit_logs.AuditLogEventType, int] = ...,
        limit: typing.Optional[int] = None,
    ) -> audit_logs.AuditLogIterator:
        """Return an async iterator that retrieves a guild's audit log entries.

        This will return the audit log entries before a given entry object/ID or
        from the first guild audit log entry.

        Parameters
        ----------
        guild : :obj:`typing.Union` [ :obj:`hikari.guilds.Guild`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The ID or object of the guild to get audit log entries for
        before : :obj:`typing.Union` [ :obj:`datetime.datetime`, :obj:`hikari.audit_logs.AuditLogEntry`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ], optional
            If specified, the ID or object of the entry or datetime to get
            entries that happened before otherwise this will start from the
            newest entry.
        user : :obj:`typing.Union` [ :obj:`hikari.users.User`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            If specified, the object or ID of the user to filter by.
        action_type : :obj:`typing.Union` [ :obj:`hikari.audit_logs.AuditLogEventType`, :obj:`int` ]
            If specified, the action type to look up. Passing a raw integer
            for this may lead to unexpected behaviour.
        limit : :obj:`int`, optional
            If specified, the limit for how many entries this iterator should
            return, defaults to unlimited.

        Example
        -------
        .. code-block:: python

            audit_log_entries = client.fetch_audit_log_entries_before(guild, before=9876543, limit=6969)
            async for entry in audit_log_entries:
                if (user := audit_log_entries.users[entry.user_id]).is_bot:
                    await client.ban_member(guild, user)

        Note
        ----
        The returned iterator has the attributes ``users``, ``members`` and
        ``integrations`` which are mappings of snowflake IDs to objects for the
        relevant entities that are referenced by the retrieved audit log
        entries. These will be filled over time as more audit log entries are
        fetched by the iterator.

        Returns
        -------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.audit_logs.AuditLogIterator`
            An async iterator of the audit log entries in a guild (from newest
            to oldest).
        """
        if isinstance(before, datetime.datetime):
            before = str(snowflakes.Snowflake.from_datetime(before))
        elif before is not None:
            before = str(before.id if isinstance(before, snowflakes.UniqueEntity) else int(before))
        return audit_logs.AuditLogIterator(
            guild_id=str(guild.id if isinstance(guild, snowflakes.UniqueEntity) else int(guild)),
            request=self._session.get_guild_audit_log,
            before=before,
            user_id=(
                str(user.id if isinstance(user, snowflakes.UniqueEntity) else int(user)) if user is not ... else ...
            ),
            action_type=action_type,
            limit=limit,
        )

    async def fetch_channel(self, channel: snowflakes.HashableT[_channels.Channel]) -> _channels.Channel:
        """Get an up to date channel object from a given channel object or ID.

        Parameters
        ----------
        channel : :obj:`typing.Union` [ :obj:`hikari.channels.Channel`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object ID of the channel to look up.

        Returns
        -------
        :obj:`hikari.channels.Channel`
            The channel object that has been found.

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you don't have access to the channel.
        :obj:`hikari.errors.NotFoundHTTPError`
            If the channel does not exist.
        """
        payload = await self._session.get_channel(
            channel_id=str(channel.id if isinstance(channel, snowflakes.UniqueEntity) else int(channel))
        )
        return _channels.deserialize_channel(payload)

    async def update_channel(
        self,
        channel: snowflakes.HashableT[_channels.Channel],
        *,
        name: str = ...,
        position: int = ...,
        topic: str = ...,
        nsfw: bool = ...,
        bitrate: int = ...,
        user_limit: int = ...,
        rate_limit_per_user: typing.Union[int, datetime.timedelta] = ...,
        permission_overwrites: typing.Sequence[_channels.PermissionOverwrite] = ...,
        parent_category: typing.Optional[snowflakes.HashableT[_channels.GuildCategory]] = ...,
        reason: str = ...,
    ) -> _channels.Channel:
        """Update one or more aspects of a given channel ID.

        Parameters
        ----------
        channel : :obj:`typing.Union` [ :obj:`hikari.channels.Channel`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The channel ID to update.
        name : :obj:`str`
            If specified, the new name for the channel. This must be
            inclusively between ``1`` and ``100`` characters in length.
        position : :obj:`int`
            If specified, the position to change the channel to.
        topic : :obj:`str`
            If specified, the topic to set. This is only applicable to
            text channels. This must be inclusively between ``0`` and ``1024``
            characters in length.
        nsfw : :obj:`bool`
            Mark the channel as being not safe for work (NSFW) if :obj:`True`.
            If :obj:`False` or unspecified, then the channel is not marked as
            NSFW. Will have no visible effect for non-text guild channels.
        rate_limit_per_user : :obj:`typing.Union` [ :obj:`int`, :obj:`datetime.timedelta` ]
            If specified, the time delta of seconds  the user has to wait
            before sending another message. This will not apply to bots, or to
            members with ``MANAGE_MESSAGES`` or ``MANAGE_CHANNEL`` permissions.
            This must be inclusively between ``0`` and ``21600`` seconds.
        bitrate : :obj:`int`
            If specified, the bitrate in bits per second allowable for the
            channel. This only applies to voice channels and must be inclusively
            between ``8000`` and ``96000`` for normal servers or ``8000`` and
            ``128000`` for VIP servers.
        user_limit : :obj:`int`
            If specified, the new max number of users to allow in a voice
            channel. This must be between ``0`` and ``99`` inclusive, where
            ``0`` implies no limit.
        permission_overwrites : :obj:`typing.Sequence` [ :obj:`hikari.channels.PermissionOverwrite` ]
            If specified, the new list of permission overwrites that are
            category specific to replace the existing overwrites with.
        parent_category : :obj:`typing.Union` [ :obj:`hikari.channels.Channel`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ], optional
            If specified, the new parent category ID to set for the channel,
            pass :obj:`None` to unset.
        reason : :obj:`str`
            If specified, the audit log reason explaining why the operation
            was performed.

        Returns
        -------
        :obj:`hikari.channels.Channel`
            The channel object that has been modified.

        Raises
        ------
        :obj:`hikari.errors.NotFoundHTTPError`
            If the channel does not exist.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you lack the permission to make the change.
        :obj:`hikari.errors.BadRequestHTTPError`
            If you provide incorrect options for the corresponding channel type
            (e.g. a ``bitrate`` for a text channel).
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        """
        payload = await self._session.modify_channel(
            channel_id=str(channel.id if isinstance(channel, snowflakes.UniqueEntity) else int(channel)),
            name=name,
            position=position,
            topic=topic,
            nsfw=nsfw,
            bitrate=bitrate,
            user_limit=user_limit,
            rate_limit_per_user=(
                int(rate_limit_per_user.total_seconds())
                if isinstance(rate_limit_per_user, datetime.timedelta)
                else rate_limit_per_user
            ),
            permission_overwrites=(
                [po.serialize() for po in permission_overwrites] if permission_overwrites is not ... else ...
            ),
            parent_id=(
                str(
                    parent_category.id if isinstance(parent_category, snowflakes.UniqueEntity) else int(parent_category)
                )
                if parent_category is not ... and parent_category is not None
                else parent_category
            ),
            reason=reason,
        )
        return _channels.deserialize_channel(payload)

    async def delete_channel(self, channel: snowflakes.HashableT[_channels.Channel]) -> None:
        """Delete the given channel ID, or if it is a DM, close it.

        Parameters
        ----------
        channel : :obj:`typing.Union` [ :obj:`hikari.channels.Channel`, :obj:`hikari.snowflakes.Snowflake` :obj:`str` ]
            The object or ID of the channel to delete.

        Returns
        -------
        :obj:`None`
            Nothing, unlike what the API specifies. This is done to maintain
            consistency with other calls of a similar nature in this API
            wrapper.

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.NotFoundHTTPError`
            If the channel does not exist.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you do not have permission to delete the channel.

        Note
        ----
        Closing a DM channel won't raise an exception but will have no effect
        and "closed" DM channels will not have to be reopened to send messages
        in theme.

        Warning
        -------
        Deleted channels cannot be un-deleted.
        """
        await self._session.delete_close_channel(
            channel_id=str(channel.id if isinstance(channel, snowflakes.UniqueEntity) else int(channel))
        )

    def fetch_messages_after(
        self,
        channel: snowflakes.HashableT[_channels.Channel],
        *,
        after: typing.Union[datetime.datetime, snowflakes.HashableT[_messages.Message]] = 0,
        limit: typing.Optional[int] = None,
    ) -> typing.AsyncIterator[_messages.Message]:
        """Return an async iterator that retrieves a channel's message history.

        This will return the message created after a given message object/ID or
        from the first message in the channel.

        Parameters
        ----------
        channel : :obj:`typing.Union` [ :obj:`hikari.channels.Channel`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The ID of the channel to retrieve the messages from.
        limit : :obj:`int`
            If specified, the maximum number of how many messages this iterator
            should return.
        after : :obj:`typing.Union` [ :obj:`datetime.datetime`, :obj:`hikari.channels.Channel`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            A object or ID message. Only return messages sent AFTER this
            message if it's specified else this will return every message after
            (and including) the first message in the channel.

        Example
        -------
        .. code-block:: python

            async for message in client.fetch_messages_after(channel, after=9876543, limit=3232):
                if message.author.id in BLACKLISTED_USERS:
                    await client.ban_member(channel.guild_id,  message.author)

        Returns
        -------
        :obj:`typing.AsyncIterator` [ :obj:`hikari.messages.Message` ]
            An async iterator that retrieves the channel's message objects.

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you lack permission to read the channel.
        :obj:`hikari.errors.NotFoundHTTPError`
            If the channel is not found, or the message
            provided for one of the filter arguments is not found.

        Note
        ----
        If you are missing the ``VIEW_CHANNEL`` permission, you will receive a
        :obj:`hikari.errors.ForbiddenHTTPError`. If you are instead missing
        the ``READ_MESSAGE_HISTORY`` permission, you will always receive
        zero results, and thus an empty list will be returned instead.
        """
        if isinstance(after, datetime.datetime):
            after = str(snowflakes.Snowflake.from_datetime(after))
        else:
            after = str(after.id if isinstance(after, snowflakes.UniqueEntity) else int(after))
        return self._pagination_handler(
            channel_id=str(channel.id if isinstance(channel, snowflakes.UniqueEntity) else int(channel)),
            deserializer=_messages.Message.deserialize,
            direction="after",
            start=after,
            request=self._session.get_channel_messages,
            reversing=True,  # This is the only known endpoint where reversing is needed.
            limit=limit,
        )

    def fetch_messages_before(
        self,
        channel: snowflakes.HashableT[_channels.Channel],
        *,
        before: typing.Union[datetime.datetime, snowflakes.HashableT[_messages.Message], None] = None,
        limit: typing.Optional[int] = None,
    ) -> typing.AsyncIterator[_messages.Message]:
        """Return an async iterator that retrieves a channel's message history.

        This returns the message created after a given message object/ID or
        from the first message in the channel.

        Parameters
        ----------
        channel : :obj:`typing.Union` [ :obj:`hikari.channels.Channel`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The ID of the channel to retrieve the messages from.
        limit : :obj:`int`
            If specified, the maximum number of how many messages this iterator
            should return.
        before : :obj:`typing.Union` [ :obj:`datetime.datetime`, :obj:`hikari.channels.Channel`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            A message object or ID. Only return messages sent BEFORE
            this message if this is specified else this will return every
            message before (and including) the most recent message in the
            channel.

        Example
        -------
        .. code-block:: python

            async for message in client.fetch_messages_before(channel, before=9876543, limit=1231):
                if message.content.lower().contains("delete this"):
                    await client.delete_message(channel, message)

        Returns
        -------
        :obj:`typing.AsyncIterator` [ :obj:`hikari.messages.Message` ]
            An async iterator that retrieves the channel's message objects.

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you lack permission to read the channel.
        :obj:`hikari.errors.NotFoundHTTPError`
            If the channel is not found, or the message
            provided for one of the filter arguments is not found.

        Note
        ----
        If you are missing the ``VIEW_CHANNEL`` permission, you will receive a
        :obj:`hikari.errors.ForbiddenHTTPError`. If you are instead missing
        the ``READ_MESSAGE_HISTORY`` permission, you will always receive
        zero results, and thus an empty list will be returned instead.
        """
        if isinstance(before, datetime.datetime):
            before = str(snowflakes.Snowflake.from_datetime(before))
        elif before is not None:
            before = str(before.id if isinstance(before, snowflakes.UniqueEntity) else int(before))
        return self._pagination_handler(
            channel_id=str(channel.id if isinstance(channel, snowflakes.UniqueEntity) else int(channel)),
            deserializer=_messages.Message.deserialize,
            direction="before",
            start=before,
            request=self._session.get_channel_messages,
            reversing=False,
            limit=limit,
        )

    async def fetch_messages_around(
        self,
        channel: snowflakes.HashableT[_channels.Channel],
        around: typing.Union[datetime.datetime, snowflakes.HashableT[_messages.Message]],
        *,
        limit: int = ...,
    ) -> typing.AsyncIterator[_messages.Message]:
        """Return an async iterator that retrieves up to 100 messages.

        This will return messages in order from newest to oldest, is based
        around the creation time of the supplied message object/ID and will
        include the given message if it still exists.

        Parameters
        ----------
        channel : :obj:`typing.Union` [ :obj:`hikari.channels.Channel`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The ID of the channel to retrieve the messages from.
        around : :obj:`typing.Union` [ :obj:`datetime.datetime`, :obj:`hikari.channels.Channel`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the message to get messages that were sent
            AROUND it in the provided channel, unlike ``before`` and ``after``,
            this argument is required and the provided message will also be
            returned if it still exists.
        limit : :obj:`int`
            If specified, the maximum number of how many messages this iterator
            should return, cannot be more than `100`

        Example
        -------
        .. code-block:: python

            async for message in client.fetch_messages_around(channel, around=9876543, limit=42):
                if message.embeds and not message.author.is_bot:
                    await client.delete_message(channel, message)

        Returns
        -------
        :obj:`typing.AsyncIterator` [ :obj:`hikari.messages.Message` ]
            An async iterator that retrieves the found message objects.

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you lack permission to read the channel.
        :obj:`hikari.errors.NotFoundHTTPError`
            If the channel is not found, or the message
            provided for one of the filter arguments is not found.

        Note
        ----
        If you are missing the ``VIEW_CHANNEL`` permission, you will receive a
        :obj:`hikari.errors.ForbiddenHTTPError`. If you are instead missing
        the ``READ_MESSAGE_HISTORY`` permission, you will always receive
        zero results, and thus an empty list will be returned instead.
        """
        if isinstance(around, datetime.datetime):
            around = str(snowflakes.Snowflake.from_datetime(around))
        else:
            around = str(around.id if isinstance(around, snowflakes.UniqueEntity) else int(around))
        for payload in await self._session.get_channel_messages(
            channel_id=str(channel.id if isinstance(channel, snowflakes.UniqueEntity) else int(channel)),
            limit=limit,
            around=around,
        ):
            yield _messages.Message.deserialize(payload)

    @staticmethod
    async def _pagination_handler(
        deserializer: typing.Callable[[typing.Any], typing.Any],
        direction: typing.Union[typing.Literal["before"], typing.Literal["after"]],
        request: typing.Callable[..., typing.Coroutine[typing.Any, typing.Any, typing.Any]],
        reversing: bool,
        start: typing.Union[str, None],
        limit: typing.Optional[int] = None,
        id_getter: typing.Callable[[typing.Any], str] = lambda entity: str(entity.id),
        **kwargs,
    ) -> typing.AsyncIterator[typing.Any]:
        """Generate an async iterator for handling paginated endpoints.

        This will handle Discord's ``before`` and ``after`` pagination.

        Parameters
        ----------
        deserializer : :obj:`typing.Callable` [ [ :obj:`typing.Any` ], :obj:`typing.Any` ]
            The deserializer to use to deserialize raw elements.
        direction : :obj:`typing.Union` [ ``"before"``, ``"after"`` ]
            The direction that this paginator should go in.
        request : :obj:`typing.Callable` [ ``...``, :obj:`typing.Coroutine` [ :obj:`typing.Any`, :obj:`typing.Any`, :obj:`typing.Any` ] ]
            The function on :attr:`_session` that should be called to make
            requests for this paginator.
        reversing : :obj:`bool`
            Whether the retrieved array of objects should be reversed before
            iterating through it, this is needed for certain endpoints like
            ``fetch_messages_before`` where the order is static regardless of
            if you're using ``before`` or ``after``.
        start : :obj:`int`, optional
            The snowflake ID that this paginator should start at, ``0`` may be
            passed for ``forward`` pagination to start at the first created
            entity and :obj:`None` may be passed for ``before`` pagination to
            start at the newest entity (based on when it's snowflake timestamp).
        limit : :obj:`int`, optional
            The amount of deserialized entities that the iterator should return
            total, will be unlimited if set to :obj:`None`.
        id_getter : :obj:`typing.Callable` [ [ :obj:`typing.Any` ], :obj:`str` ]
        **kwargs
            Kwargs to pass through to ``request`` for every request made along
            with the current decided limit and direction snowflake.

        Returns
        -------
        :obj:`typing.AsyncIterator` [ :obj:`typing.Any` ]
            An async iterator of the found deserialized found objects.

        """
        while payloads := await request(
            limit=100 if limit is None or limit > 100 else limit,
            **{direction: start if start is not None else ...},
            **kwargs,
        ):
            if reversing:
                payloads.reverse()
            if limit is not None:
                limit -= len(payloads)

            for payload in payloads:
                entity = deserializer(payload)
                yield entity
            if limit == 0:
                break
            start = id_getter(entity)

    async def fetch_message(
        self, channel: snowflakes.HashableT[_channels.Channel], message: snowflakes.HashableT[_messages.Message],
    ) -> _messages.Message:
        """Get a message from known channel that we can access.

        Parameters
        ----------
        channel : :obj:`typing.Union` [ :obj:`hikari.channels.Channel`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the channel to get the message from.
        message : :obj:`typing.Union` [ :obj:`hikari.messages.Message`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the message to retrieve.

        Returns
        -------
        :obj:`hikari.messages.Message`
            The found message object.

        Note
        ----
        This requires the ``READ_MESSAGE_HISTORY`` permission.

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you lack permission to see the message.
        :obj:`hikari.errors.NotFoundHTTPError`
            If the channel or message is not found.
        """
        payload = await self._session.get_channel_message(
            channel_id=str(channel.id if isinstance(channel, snowflakes.UniqueEntity) else int(channel)),
            message_id=str(message.id if isinstance(message, snowflakes.UniqueEntity) else int(message)),
        )
        return _messages.Message.deserialize(payload)

    @staticmethod
    def _generate_allowed_mentions(
        mentions_everyone: bool,
        user_mentions: typing.Union[typing.Collection[snowflakes.HashableT[users.User]], bool],
        role_mentions: typing.Union[typing.Collection[snowflakes.HashableT[guilds.GuildRole]], bool],
    ) -> typing.Dict[str, typing.Sequence[str]]:
        """Generate an allowed mentions object based on input mention rules.

        Parameters
        ----------
        mentions_everyone : :obj:`bool`
            Whether ``@everyone`` and ``@here`` mentions should be resolved by
            discord and lead to actual pings.
        user_mentions : :obj:`typing.Union` [ :obj:`typing.Collection` [ :obj:`typing.Union` [ :obj:`hikari.users.User`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ], :obj:`bool` ]
            Either an array of user objects/IDs to allow mentions for,
            :obj:`True` to allow all user mentions or :obj:`False` to block all
            user mentions from resolving.
        role_mentions : :obj:`typing.Union` [ :obj:`typing.Collection` [ :obj:`typing.Union` [ :obj:`hikari.guilds.GuildRole`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ] ], :obj:`bool` ]
            Either an array of guild role objects/IDs to allow mentions for,
            :obj:`True` to allow all role mentions or :obj:`False` to block all
            role mentions from resolving.

        Returns
        -------
        :obj:`typing.Dict` [ :obj:`str`, :obj:`typing.Sequence` [ :obj:`str` ] ]
            The resulting allowed mentions dict object.
        """
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
                    str(user.id if isinstance(user, snowflakes.UniqueEntity) else int(user))
                    for user in user_mentions or more_collections.EMPTY_SEQUENCE
                )
            )
            assertions.assert_that(len(allowed_mentions["users"]) <= 100, "Only up to 100 users can be provided.")
        if role_mentions is True:
            parsed_mentions.append("roles")
        # This covers both `False` and an array of IDs/objs by using `user_mentions or EMPTY_SEQUENCE`, where a
        # resultant empty list will mean that all role mentions are blacklisted.
        else:
            allowed_mentions["roles"] = list(
                # dict.fromkeys is used to remove duplicate entries that would cause discord to return an error.
                dict.fromkeys(
                    str(role.id if isinstance(role, snowflakes.UniqueEntity) else int(role))
                    for role in role_mentions or more_collections.EMPTY_SEQUENCE
                )
            )
            assertions.assert_that(len(allowed_mentions["roles"]) <= 100, "Only up to 100 roles can be provided.")
        allowed_mentions["parse"] = parsed_mentions
        # As a note, discord will also treat an empty `allowed_mentions` object as if it wasn't passed at all, so we
        # want to use empty lists for blacklisting elements rather than just not including blacklisted elements.
        return allowed_mentions

    async def create_message(
        self,
        channel: snowflakes.HashableT[_channels.Channel],
        *,
        content: str = ...,
        nonce: str = ...,
        tts: bool = ...,
        files: typing.Collection[media.IO] = ...,
        embed: _embeds.Embed = ...,
        mentions_everyone: bool = True,
        user_mentions: typing.Union[typing.Collection[snowflakes.HashableT[users.User]], bool] = True,
        role_mentions: typing.Union[typing.Collection[snowflakes.HashableT[guilds.GuildRole]], bool] = True,
    ) -> _messages.Message:
        """Create a message in the given channel.

        Parameters
        ----------
        channel : :obj:`typing.Union` [ :obj:`hikari.channels.Channel`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The channel or ID of the channel to send to.
        content : :obj:`str`
            If specified, the message content to send with the message.
        nonce : :obj:`str`
            If specified, an optional ID to send for opportunistic message
            creation. This doesn't serve any real purpose for general use,
            and can usually be ignored.
        tts : :obj:`bool`
            If specified, whether the message will be sent as a TTS message.
        files : :obj:`typing.Collection` [ ``hikari.media.IO`` ]
            If specified, this should be a list of inclusively between ``1`` and
            ``5`` IO like media objects, as defined in :mod:`hikari.media`.
        embed : :obj:`hikari.embeds.Embed`
            If specified, the embed object to send with the message.
        mentions_everyone : :obj:`bool`
            Whether ``@everyone`` and ``@here`` mentions should be resolved by
            discord and lead to actual pings, defaults to :obj:`True`.
        user_mentions : :obj:`typing.Union` [ :obj:`typing.Collection` [ :obj:`typing.Union` [ :obj:`hikari.users.User`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ], :obj:`bool` ]
            Either an array of user objects/IDs to allow mentions for,
            :obj:`True` to allow all user mentions or :obj:`False` to block all
            user mentions from resolving, defaults to :obj:`True`.
        role_mentions : :obj:`typing.Union` [ :obj:`typing.Collection` [ :obj:`typing.Union` [ :obj:`hikari.guilds.GuildRole`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ] ], :obj:`bool` ]
            Either an array of guild role objects/IDs to allow mentions for,
            :obj:`True` to allow all role mentions or :obj:`False` to block all
            role mentions from resolving, defaults to :obj:`True`.

        Returns
        -------
        :obj:`hikari.messages.Message`
            The created message object.

        Raises
        ------
        :obj:`hikari.errors.NotFoundHTTPError`
            If the channel is not found.
        :obj:`hikari.errors.BadRequestHTTPError`
            This can be raised if the file is too large; if the embed exceeds
            the defined limits; if the message content is specified only and
            empty or greater than ``2000`` characters; if neither content, files
            or embed are specified.
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you lack permissions to send to this channel.
        """
        payload = await self._session.create_message(
            channel_id=str(channel.id if isinstance(channel, snowflakes.UniqueEntity) else int(channel)),
            content=content,
            nonce=nonce,
            tts=tts,
            files=await asyncio.gather(*(media.safe_read_file(file) for file in files)) if files is not ... else ...,
            embed=embed.serialize() if embed is not ... else ...,
            allowed_mentions=self._generate_allowed_mentions(
                mentions_everyone=mentions_everyone, user_mentions=user_mentions, role_mentions=role_mentions
            ),
        )
        return _messages.Message.deserialize(payload)

    def safe_create_message(
        self,
        channel: snowflakes.HashableT[_channels.Channel],
        *,
        content: str = ...,
        nonce: str = ...,
        tts: bool = ...,
        files: typing.Collection[media.IO] = ...,
        embed: _embeds.Embed = ...,
        mentions_everyone: bool = False,
        user_mentions: typing.Union[typing.Collection[snowflakes.HashableT[users.User]], bool] = False,
        role_mentions: typing.Union[typing.Collection[snowflakes.HashableT[guilds.GuildRole]], bool] = False,
    ) -> typing.Coroutine[typing.Any, typing.Any, _messages.Message]:
        """Create a message in the given channel with mention safety.

        This endpoint has the same signature as :attr:`create_message` with
        the only difference being that ``mentions_everyone``,
        ``user_mentions`` and ``role_mentions`` default to :obj:`False`.
        """
        return self.create_message(
            channel=channel,
            content=content,
            nonce=nonce,
            tts=tts,
            files=files,
            embed=embed,
            mentions_everyone=mentions_everyone,
            user_mentions=user_mentions,
            role_mentions=role_mentions,
        )

    async def create_reaction(
        self,
        channel: snowflakes.HashableT[_channels.Channel],
        message: snowflakes.HashableT[_messages.Message],
        emoji: typing.Union[emojis.Emoji, str],
    ) -> None:
        """Add a reaction to the given message in the given channel.

        Parameters
        ----------
        channel : :obj:`typing.Union` [ :obj:`hikari.channels.Channel`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the channel to add this reaction in.
        message : :obj:`typing.Union` [ :obj:`hikari.messages.Message`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the message to add the reaction in.
        emoji : :obj:`typing.Union` [ :obj:`hikari.emojis.Emoji`, :obj:`str` ]
            The emoji to add. This can either be an emoji object or a string
            representation of an emoji. The string representation will be either
            ``"name:id"`` for custom emojis else it's unicode character(s)  (can
            be UTF-32).

        Raises
        ------
        :obj:`hikari.errors.ForbiddenHTTPError`
            If this is the first reaction using this specific emoji on this
            message and you lack the ``ADD_REACTIONS`` permission. If you lack
            ``READ_MESSAGE_HISTORY``, this may also raise this error.
        :obj:`hikari.errors.NotFoundHTTPError`
            If the channel or message is not found, or if the emoji is not found.
        :obj:`hikari.errors.BadRequestHTTPError`
            If the emoji is not valid, unknown, or formatted incorrectly.
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        """
        await self._session.create_reaction(
            channel_id=str(channel.id if isinstance(channel, snowflakes.UniqueEntity) else int(channel)),
            message_id=str(message.id if isinstance(message, snowflakes.UniqueEntity) else int(message)),
            emoji=str(getattr(emoji, "url_name", emoji)),
        )

    async def delete_reaction(
        self,
        channel: snowflakes.HashableT[_channels.Channel],
        message: snowflakes.HashableT[_messages.Message],
        emoji: typing.Union[emojis.Emoji, str],
    ) -> None:
        """Remove your own reaction from the given message in the given channel.

        Parameters
        ----------
        channel : :obj:`typing.Union` [ :obj:`hikari.channels.Channel`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the channel to add this reaction in.
        message : :obj:`typing.Union` [ :obj:`hikari.messages.Message`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the message to add the reaction in.
        emoji : :obj:`typing.Union` [ :obj:`hikari.emojis.Emoji`, :obj:`str` ]
            The emoji to add. This can either be an emoji object or a
            string representation of an emoji. The string representation will be
            either ``"name:id"`` for custom emojis else it's unicode
            character(s) (can be UTF-32).

        Raises
        ------
        :obj:`hikari.errors.ForbiddenHTTPError`
            If this is the first reaction using this specific emoji on this
            message and you lack the ``ADD_REACTIONS`` permission. If you lack
            ``READ_MESSAGE_HISTORY``, this may also raise this error.
        :obj:`hikari.errors.NotFoundHTTPError`
            If the channel or message is not found, or if the emoji is not
            found.
        :obj:`hikari.errors.BadRequestHTTPError`
            If the emoji is not valid, unknown, or formatted incorrectly.
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        """
        await self._session.delete_own_reaction(
            channel_id=str(channel.id if isinstance(channel, snowflakes.UniqueEntity) else int(channel)),
            message_id=str(message.id if isinstance(message, snowflakes.UniqueEntity) else int(message)),
            emoji=str(getattr(emoji, "url_name", emoji)),
        )

    async def delete_all_reactions(
        self, channel: snowflakes.HashableT[_channels.Channel], message: snowflakes.HashableT[_messages.Message],
    ) -> None:
        """Delete all reactions from a given message in a given channel.

        Parameters
        ----------
        channel : :obj:`typing.Union` [ :obj:`hikari.channels.Channel`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the channel to get the message from.
        message : :obj:`typing.Union` [ :obj:`hikari.messages.Message`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the message to remove all reactions from.

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.NotFoundHTTPError`
            If the channel or message is not found.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you lack the ``MANAGE_MESSAGES`` permission.
        """
        await self._session.delete_all_reactions(
            channel_id=str(channel.id if isinstance(channel, snowflakes.UniqueEntity) else int(channel)),
            message_id=str(message.id if isinstance(message, snowflakes.UniqueEntity) else int(message)),
        )

    async def delete_all_reactions_for_emoji(
        self,
        channel: snowflakes.HashableT[_channels.Channel],
        message: snowflakes.HashableT[_messages.Message],
        emoji: typing.Union[emojis.Emoji, str],
    ) -> None:
        """Remove all reactions for a single given emoji on a given message.

        Parameters
        ----------
        channel : :obj:`typing.Union` [ :obj:`hikari.channels.Channel`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the channel to get the message from.
        message : :obj:`typing.Union` [ :obj:`hikari.messages.Message`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the message to delete the reactions from.
        emoji : :obj:`typing.Union` [ :obj:`hikari.emojis.Emoji`, :obj:`str` ]
            The object or string representatiom of the emoji to delete. The
            string representation will be either ``"name:id"`` for custom emojis
            else it's unicode character(s) (can be UTF-32).

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.NotFoundHTTPError`
            If the channel or message or emoji or user is not found.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you lack the ``MANAGE_MESSAGES`` permission, or the channel is a
            DM channel.
        """
        await self._session.delete_all_reactions_for_emoji(
            channel_id=str(channel.id if isinstance(channel, snowflakes.UniqueEntity) else int(channel)),
            message_id=str(message.id if isinstance(message, snowflakes.UniqueEntity) else int(message)),
            emoji=str(getattr(emoji, "url_name", emoji)),
        )

    def fetch_reactors_after(
        self,
        channel: snowflakes.HashableT[_channels.Channel],
        message: snowflakes.HashableT[_messages.Message],
        emoji: typing.Union[emojis.Emoji, str],
        *,
        after: typing.Union[datetime.datetime, snowflakes.HashableT[users.User]] = 0,
        limit: typing.Optional[int] = None,
    ) -> typing.AsyncIterator[users.User]:
        """Get an async iterator of the users who reacted to a message.

        This returns the users created after a given user object/ID or from the
        oldest user who reacted.

        Parameters
        ----------
        channel : :obj:`typing.Union` [ :obj:`hikari.channels.Channel`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the channel to get the message from.
        message : :obj:`typing.Union` [ :obj:`hikari.messages.Message`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the message to get the reactions from.
        emoji : :obj:`typing.Union` [ :obj:`hikari.emojis.Emoji`, :obj:`str` ]
            The emoji to get. This can either be it's object or the string
            representation of the emoji. The string representation will be
            either ``"name:id"`` for custom emojis else it's unicode
            character(s) (can be UTF-32).
        after : :obj:`typing.Union` [ :obj:`datetime.datetime`, :obj:`hikari.users.User`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            If specified, a object or ID user. If specified, only users with a
            snowflake that is lexicographically greater than the value will be
            returned.
        limit : :obj:`str`
            If specified, the limit of the number of users this iterator should
            return.

        Example
        -------
        .. code-block:: python

            async for user in client.fetch_reactors_after(channel, message, emoji, after=9876543, limit=1231):
                if user.is_bot:
                    await client.kick_member(channel.guild_id, user)

        Returns
        -------
        :obj:`typing.AsyncIterator` [ :obj:`hikari.users.User` ]
            An async iterator of user objects.

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you lack access to the message.
        :obj:`hikari.errors.NotFoundHTTPError`
            If the channel or message is not found.
        """
        if isinstance(after, datetime.datetime):
            after = str(snowflakes.Snowflake.from_datetime(after))
        else:
            after = str(after.id if isinstance(after, snowflakes.UniqueEntity) else int(after))
        return self._pagination_handler(
            channel_id=str(channel.id if isinstance(channel, snowflakes.UniqueEntity) else int(channel)),
            message_id=str(message.id if isinstance(message, snowflakes.UniqueEntity) else int(message)),
            emoji=getattr(emoji, "url_name", emoji),
            deserializer=users.User.deserialize,
            direction="after",
            request=self._session.get_reactions,
            reversing=False,
            start=after,
            limit=limit,
        )

    async def update_message(
        self,
        message: snowflakes.HashableT[_messages.Message],
        channel: snowflakes.HashableT[_channels.Channel],
        *,
        content: typing.Optional[str] = ...,
        embed: typing.Optional[_embeds.Embed] = ...,
        flags: int = ...,
        mentions_everyone: bool = True,
        user_mentions: typing.Union[typing.Collection[snowflakes.HashableT[users.User]], bool] = True,
        role_mentions: typing.Union[typing.Collection[snowflakes.HashableT[guilds.GuildRole]], bool] = True,
    ) -> _messages.Message:
        """Update the given message.

        Parameters
        ----------
        channel : :obj:`typing.Union` [ :obj:`hikari.channels.Channel`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the channel to get the message from.
        message : :obj:`typing.Union` [ :obj:`hikari.messages.Message`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the message to edit.
        content : :obj:`str`, optional
            If specified, the string content to replace with in the message.
            If :obj:`None`, the content will be removed from the message.
        embed : :obj:`hikari.embeds.Embed`, optional
            If specified, the embed to replace with in the message.
            If :obj:`None`, the embed will be removed from the message.
        flags : :obj:`hikari.messages.MessageFlag`
            If specified, the new flags for this message, while a raw int may
            be passed for this, this can lead to unexpected behaviour if it's
            outside the range of the MessageFlag int flag.
        mentions_everyone : :obj:`bool`
            Whether ``@everyone`` and ``@here`` mentions should be resolved by
            discord and lead to actual pings, defaults to :obj:`True`.
        user_mentions : :obj:`typing.Union` [ :obj:`typing.Collection` [ :obj:`typing.Union` [ :obj:`hikari.users.User`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ], :obj:`bool` ]
            Either an array of user objects/IDs to allow mentions for,
            :obj:`True` to allow all user mentions or :obj:`False` to block all
            user mentions from resolving, defaults to :obj:`True`.
        role_mentions : :obj:`typing.Union` [ :obj:`typing.Collection` [ :obj:`typing.Union` [ :obj:`hikari.guilds.GuildRole`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ] ], :obj:`bool` ]
            Either an array of guild role objects/IDs to allow mentions for,
            :obj:`True` to allow all role mentions or :obj:`False` to block all
            role mentions from resolving, defaults to :obj:`True`.

        Returns
        -------
        :obj:`hikari.messages.Message`
            The edited message object.

        Raises
        ------
        :obj:`hikari.errors.NotFoundHTTPError`
            If the channel or message is not found.
        :obj:`hikari.errors.BadRequestHTTPError`
            This can be raised if the embed exceeds the defined limits;
            if the message content is specified only and empty or greater
            than ``2000`` characters; if neither content, file or embed
            are specified.
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you try to edit ``content`` or ``embed`` or ``allowed_mentions`
            on a message you did not author.
            If you try to edit the flags on a message you did not author without
            the ``MANAGE_MESSAGES`` permission.
        """
        payload = await self._session.edit_message(
            channel_id=str(channel.id if isinstance(channel, snowflakes.UniqueEntity) else int(channel)),
            message_id=str(message.id if isinstance(message, snowflakes.UniqueEntity) else int(message)),
            content=content,
            embed=embed.serialize() if embed is not ... and embed is not None else embed,
            flags=flags,
            allowed_mentions=self._generate_allowed_mentions(
                mentions_everyone=mentions_everyone, user_mentions=user_mentions, role_mentions=role_mentions,
            ),
        )
        return _messages.Message.deserialize(payload)

    def safe_update_message(
        self,
        message: snowflakes.HashableT[_messages.Message],
        channel: snowflakes.HashableT[_channels.Channel],
        *,
        content: typing.Optional[str] = ...,
        embed: typing.Optional[_embeds.Embed] = ...,
        flags: int = ...,
        mentions_everyone: bool = False,
        user_mentions: typing.Union[typing.Collection[snowflakes.HashableT[users.User]], bool] = False,
        role_mentions: typing.Union[typing.Collection[snowflakes.HashableT[guilds.GuildRole]], bool] = False,
    ) -> typing.Coroutine[typing.Any, typing.Any, _messages.Message]:
        """Update a message in the given channel with mention safety.

        This endpoint has the same signature as :attr:`execute_webhook` with
        the only difference being that ``mentions_everyone``,
        ``user_mentions`` and ``role_mentions`` default to :obj:`False`.
        """
        return self.update_message(
            message=message,
            channel=channel,
            content=content,
            embed=embed,
            flags=flags,
            mentions_everyone=mentions_everyone,
            user_mentions=user_mentions,
            role_mentions=role_mentions,
        )

    async def delete_messages(
        self,
        channel: snowflakes.HashableT[_channels.Channel],
        message: snowflakes.HashableT[_messages.Message],
        *additional_messages: snowflakes.HashableT[_messages.Message],
    ) -> None:
        """Delete a message in a given channel.

        Parameters
        ----------
        channel : :obj:`typing.Union` [ :obj:`hikari.channels.Channel`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the channel to get the message from.
        message : :obj:`typing.Union` [ :obj:`hikari.messages.Message`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the message to delete.
        *additional_messages : :obj:`typing.Union` [ :obj:`hikari.messages.Message`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            Objects and/or IDs of additional messages to delete in the same
            channel, in total you can delete up to 100 messages in a request.

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you did not author the message and are in a DM, or if you did
            not author the message and lack the ``MANAGE_MESSAGES``
            permission in a guild channel.
        :obj:`hikari.errors.NotFoundHTTPError`
            If the channel or message is not found.
        :obj:`ValueError`
            If you try to delete over ``100`` messages in a single request.

        Note
        ----
        This can only be used on guild text channels.
        Any message IDs that do not exist or are invalid still add towards the
        total ``100`` max messages to remove. This can only delete messages
        that are newer than ``2`` weeks in age. If any of the messages ar
        older than ``2`` weeks then this call will fail.
        """
        if additional_messages:
            messages = list(
                # dict.fromkeys is used to remove duplicate entries that would cause discord to return an error.
                dict.fromkeys(
                    str(m.id if isinstance(m, snowflakes.UniqueEntity) else int(m))
                    for m in (message, *additional_messages)
                )
            )
            assertions.assert_that(
                len(messages) <= 100, "Only up to 100 messages can be bulk deleted in a single request."
            )

            if len(messages) > 1:
                await self._session.bulk_delete_messages(
                    channel_id=str(channel.id if isinstance(channel, snowflakes.UniqueEntity) else int(channel)),
                    messages=messages,
                )
                return None

        await self._session.delete_message(
            channel_id=str(channel.id if isinstance(channel, snowflakes.UniqueEntity) else int(channel)),
            message_id=str(message.id if isinstance(message, snowflakes.UniqueEntity) else int(message)),
        )

    async def update_channel_overwrite(
        self,
        channel: snowflakes.HashableT[_messages.Message],
        overwrite: typing.Union[_channels.PermissionOverwrite, users.User, guilds.GuildRole, snowflakes.Snowflake, int],
        target_type: typing.Union[_channels.PermissionOverwriteType, str],
        *,
        allow: typing.Union[_permissions.Permission, int] = ...,
        deny: typing.Union[_permissions.Permission, int] = ...,
        reason: str = ...,
    ) -> None:
        """Edit permissions for a given channel.

        Parameters
        ----------
        channel : :obj:`typing.Union` [ :obj:`hikari.messages.Message`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the channel to edit permissions for.
        overwrite : :obj:`typing.Union` [ :obj:`hikari.channels.PermissionOverwrite`, :obj:`hikari.guilds.GuildRole`, :obj:`hikari.users.User`, :obj:`hikari.snowflakes.Snowflake` , :obj:`int` ]
            The object or ID of the target member or role to  edit/create the
            overwrite for.
        target_type : :obj:`typing.Union` [ :obj:`hikari.channels.PermissionOverwriteType`, :obj:`int` ]
            The type of overwrite, passing a raw string that's outside of the
            enum's range for this may lead to unexpected behaviour.
        allow : :obj:`typing.Union` [ :obj:`hikari.permissions.Permission`, :obj:`int` ]
            If specified, the value of all permissions to set to be allowed,
            passing a raw integer for this may lead to unexpected behaviour.
        deny : :obj:`typing.Union` [ :obj:`hikari.permissions.Permission`, :obj:`int` ]
            If specified, the value of all permissions to set to be denied,
            passing a raw integer for this may lead to unexpected behaviour.
        reason : :obj:`str`
            If specified, the audit log reason explaining why the operation
            was performed.

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.NotFoundHTTPError`
            If the target channel or overwrite doesn't exist.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you lack permission to do this.
        """
        await self._session.edit_channel_permissions(
            channel_id=str(channel.id if isinstance(channel, snowflakes.UniqueEntity) else int(channel)),
            overwrite_id=str(overwrite.id if isinstance(overwrite, snowflakes.UniqueEntity) else int(overwrite)),
            type_=target_type,
            allow=allow,
            deny=deny,
            reason=reason,
        )

    async def fetch_invites_for_channel(
        self, channel: snowflakes.HashableT[_channels.Channel]
    ) -> typing.Sequence[invites.InviteWithMetadata]:
        """Get invites for a given channel.

        Parameters
        ----------
        channel : :obj:`typing.Union` [ :obj:`hikari.channels.Channel`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the channel to get invites for.

        Returns
        -------
        :obj:`typing.Sequence` [ :obj:`hikari.invites.InviteWithMetadata` ]
            A list of invite objects.

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you lack the ``MANAGE_CHANNELS`` permission.
        :obj:`hikari.errors.NotFoundHTTPError`
            If the channel does not exist.
        """
        payload = await self._session.get_channel_invites(
            channel_id=str(channel.id if isinstance(channel, snowflakes.UniqueEntity) else int(channel))
        )
        return [invites.InviteWithMetadata.deserialize(invite) for invite in payload]

    async def create_invite_for_channel(
        self,
        channel: snowflakes.HashableT[_channels.Channel],
        *,
        max_age: typing.Union[int, datetime.timedelta] = ...,
        max_uses: int = ...,
        temporary: bool = ...,
        unique: bool = ...,
        target_user: snowflakes.HashableT[users.User] = ...,
        target_user_type: typing.Union[invites.TargetUserType, int] = ...,
        reason: str = ...,
    ) -> invites.InviteWithMetadata:
        """Create a new invite for the given channel.

        Parameters
        ----------
        channel : :obj:`typing.Union` [ :obj:`datetime.timedelta`, :obj:`str` ]
            The object or ID of the channel to create the invite for.
        max_age : :obj:`int`
            If specified, the seconds time delta for the max age of the invite,
            defaults to ``86400`` seconds (``24`` hours).
            Set to ``0`` seconds to never expire.
        max_uses : :obj:`int`
            If specified, the max number of uses this invite can have, or ``0``
            for unlimited (as per the default).
        temporary : :obj:`bool`
            If specified, whether to grant temporary membership, meaning the
            user is kicked when their session ends unless they are given a role.
        unique : :obj:`bool`
            If specified, whether to try to reuse a similar invite.
        target_user : :obj:`typing.Union` [ :obj:`hikari.users.User`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            If specified, the object or ID of the user this invite should
            target.
        target_user_type : :obj:`typing.Union` [ :obj:`hikari.invites.TargetUserType`, :obj:`int` ]
            If specified, the type of target for this invite, passing a raw
            integer for this may lead to unexpected results.
        reason : :obj:`str`
            If specified, the audit log reason explaining why the operation
            was performed.

        Returns
        -------
        :obj:`hikari.invites.InviteWithMetadata`
            The created invite object.

        Raises
        ------
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you lack the ``CREATE_INSTANT_MESSAGES`` permission.
        :obj:`hikari.errors.NotFoundHTTPError`
            If the channel does not exist.
        :obj:`hikari.errors.BadRequestHTTPError`
            If the arguments provided are not valid (e.g. negative age, etc).
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        """
        payload = await self._session.create_channel_invite(
            channel_id=str(channel.id if isinstance(channel, snowflakes.UniqueEntity) else int(channel)),
            max_age=int(max_age.total_seconds()) if isinstance(max_age, datetime.timedelta) else max_age,
            max_uses=max_uses,
            temporary=temporary,
            unique=unique,
            target_user=(
                str(target_user.id if isinstance(target_user, snowflakes.UniqueEntity) else int(target_user))
                if target_user is not ...
                else ...
            ),
            target_user_type=target_user_type,
            reason=reason,
        )
        return invites.InviteWithMetadata.deserialize(payload)

    async def delete_channel_overwrite(
        self,
        channel: snowflakes.HashableT[_channels.Channel],
        overwrite: typing.Union[_channels.PermissionOverwrite, guilds.GuildRole, users.User, snowflakes.Snowflake, int],
    ) -> None:
        """Delete a channel permission overwrite for a user or a role.

        Parameters
        ----------
        channel : :obj:`typing.Union` [ :obj:`hikari.channels.Channel`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the channel to delete the overwrite from.
        overwrite : :obj:`typing.Union` [ :obj:`hikari.channels.PermissionOverwrite`, :obj:`hikari.guilds.GuildRole`, :obj:`hikari.users.User`, :obj:`hikari.snowflakes.Snowflake`, :obj:int ]
            The ID of the entity this overwrite targets.

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.NotFoundHTTPError`
            If the overwrite or channel do not exist.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you lack the ``MANAGE_ROLES`` permission for that channel.
        """
        await self._session.delete_channel_permission(
            channel_id=str(channel.id if isinstance(channel, snowflakes.UniqueEntity) else int(channel)),
            overwrite_id=str(overwrite.id if isinstance(overwrite, snowflakes.UniqueEntity) else int(overwrite)),
        )

    async def trigger_typing(self, channel: snowflakes.HashableT[_channels.Channel]) -> None:
        """Trigger the typing indicator for ``10`` seconds in a channel.

        Parameters
        ----------
        channel : :obj:`typing.Union` [ :obj:`hikari.channels.Channel`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the channel to appear to be typing in.

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.NotFoundHTTPError`
            If the channel is not found.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you are not able to type in the channel.
        """
        await self._session.trigger_typing_indicator(
            channel_id=str(channel.id if isinstance(channel, snowflakes.UniqueEntity) else int(channel))
        )

    async def fetch_pins(
        self, channel: snowflakes.HashableT[_channels.Channel]
    ) -> typing.Mapping[snowflakes.Snowflake, _messages.Message]:
        """Get pinned messages for a given channel.

        Parameters
        ----------
        channel : :obj:`typing.Union` [ :obj:`hikari.channels.Channel`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the channel to get messages from.

        Returns
        -------
        :obj:`typing.Mapping` [ :obj:`hikari.snowflakes.Snowflake`, :obj:`hikari.messages.Message` ]
            A list of message objects.

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.NotFoundHTTPError`
            If the channel is not found.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you are not able to see the channel.

        Note
        ----
        If you are not able to see the pinned message (eg. you are missing
        ``READ_MESSAGE_HISTORY`` and the pinned message is an old message), it
        will not be returned.
        """
        payload = await self._session.get_pinned_messages(
            channel_id=str(channel.id if isinstance(channel, snowflakes.UniqueEntity) else int(channel))
        )
        return {message.id: message for message in map(_messages.Message.deserialize, payload)}

    async def pin_message(
        self, channel: snowflakes.HashableT[_channels.Channel], message: snowflakes.HashableT[_messages.Message],
    ) -> None:
        """Add a pinned message to the channel.

        Parameters
        ----------
        channel : :obj:`typing.Union` [ :obj:`hikari.channels.Channel`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the channel to pin a message to.
        message : :obj:`typing.Union` [ :obj:`hikari.messages.Message`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the message to pin.

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you lack the ``MANAGE_MESSAGES`` permission.
        :obj:`hikari.errors.NotFoundHTTPError`
            If the message or channel do not exist.
        """
        await self._session.add_pinned_channel_message(
            channel_id=str(channel.id if isinstance(channel, snowflakes.UniqueEntity) else int(channel)),
            message_id=str(message.id if isinstance(message, snowflakes.UniqueEntity) else int(message)),
        )

    async def unpin_message(
        self, channel: snowflakes.HashableT[_channels.Channel], message: snowflakes.HashableT[_messages.Message],
    ) -> None:
        """Remove a pinned message from the channel.

        This will only unpin the message, not delete it.

        Parameters
        ----------
        channel : :obj:`typing.Union` [ :obj:`hikari.channels.Channel`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The ID of the channel to remove a pin from.
        message : :obj:`typing.Union` [ :obj:`hikari.messages.Message`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the message to unpin.

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you lack the ``MANAGE_MESSAGES`` permission.
        :obj:`hikari.errors.NotFoundHTTPError`
            If the message or channel do not exist.
        """
        await self._session.delete_pinned_channel_message(
            channel_id=str(channel.id if isinstance(channel, snowflakes.UniqueEntity) else int(channel)),
            message_id=str(message.id if isinstance(message, snowflakes.UniqueEntity) else int(message)),
        )

    async def fetch_guild_emoji(
        self, guild: snowflakes.HashableT[guilds.Guild], emoji: snowflakes.HashableT[emojis.GuildEmoji],
    ) -> emojis.GuildEmoji:
        """Get an updated emoji object from a specific guild.

        Parameters
        ----------
        guild : :obj:`typing.Union` [ :obj:`hikari.guilds.Guild`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the guild to get the emoji from.
        emoji : :obj:`typing.Union` [ :obj:`hikari.emojis.GuildEmoji`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the emoji to get.

        Returns
        -------
        :obj:`hikari.emojis.GuildEmoji`
            A guild emoji object.

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.NotFoundHTTPError`
            If either the guild or the emoji aren't found.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you aren't a member of said guild.
        """
        payload = await self._session.get_guild_emoji(
            guild_id=str(guild.id if isinstance(guild, snowflakes.UniqueEntity) else int(guild)),
            emoji_id=str(emoji.id if isinstance(emoji, snowflakes.UniqueEntity) else int(emoji)),
        )
        return emojis.GuildEmoji.deserialize(payload)

    async def fetch_guild_emojis(self, guild: snowflakes.HashableT[guilds.Guild]) -> typing.Sequence[emojis.GuildEmoji]:
        """Get emojis for a given guild object or ID.

        Parameters
        ----------
        guild : :obj:`typing.Union` [ :obj:`hikari.guilds.Guild`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the guild to get the emojis for.

        Returns
        -------
        :obj:`typing.Sequence` [ :obj:`hikari.emojis.GuildEmoji` ]
            A list of guild emoji objects.

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you aren't a member of the guild.
        """
        payload = await self._session.list_guild_emojis(
            guild_id=str(guild.id if isinstance(guild, snowflakes.UniqueEntity) else int(guild))
        )
        return [emojis.GuildEmoji.deserialize(emoji) for emoji in payload]

    async def create_guild_emoji(
        self,
        guild: snowflakes.HashableT[guilds.GuildRole],
        name: str,
        image_data: conversions.FileLikeT,
        *,
        roles: typing.Sequence[snowflakes.HashableT[guilds.GuildRole]] = ...,
        reason: str = ...,
    ) -> emojis.GuildEmoji:
        """Create a new emoji for a given guild.

        Parameters
        ----------
        guild : :obj:`typing.Union` [ :obj:`hikari.guilds.GuildRole`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the guild to create the emoji in.
        name : :obj:`str`
            The new emoji's name.
        image_data : ``hikari.internal.conversions.FileLikeT``
            The ``128x128`` image data.
        roles : :obj:`typing.Sequence` [ :obj:`typing.Union` [ :obj:`hikari.guilds.GuildRole`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ] ]
            If specified, a list of role objects or IDs for which the emoji
            will be whitelisted. If empty, all roles are whitelisted.
        reason : :obj:`str`
            If specified, the audit log reason explaining why the operation
            was performed.

        Returns
        -------
        :obj:`hikari.emojis.GuildEmoji`
            The newly created emoji object.

        Raises
        ------
        :obj:`ValueError`
            If ``image`` is :obj:`None`.
        :obj:`hikari.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you either lack the ``MANAGE_EMOJIS`` permission or aren't a
            member of said guild.
        :obj:`hikari.errors.BadRequestHTTPError`
            If you attempt to upload an image larger than ``256kb``, an empty
            image or an invalid image format.
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        """
        payload = await self._session.create_guild_emoji(
            guild_id=str(guild.id if isinstance(guild, snowflakes.UniqueEntity) else int(guild)),
            name=name,
            image=conversions.get_bytes_from_resource(image_data),
            roles=[str(role.id if isinstance(role, snowflakes.UniqueEntity) else int(role)) for role in roles]
            if roles is not ...
            else ...,
            reason=reason,
        )
        return emojis.GuildEmoji.deserialize(payload)

    async def update_guild_emoji(
        self,
        guild: snowflakes.HashableT[guilds.Guild],
        emoji: snowflakes.HashableT[emojis.GuildEmoji],
        *,
        name: str = ...,
        roles: typing.Sequence[snowflakes.HashableT[guilds.GuildRole]] = ...,
        reason: str = ...,
    ) -> emojis.GuildEmoji:
        """Edits an emoji of a given guild.

        Parameters
        ----------
        guild : :obj:`typing.Union` [ :obj:`hikari.guilds.Guild`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the guild to which the emoji to edit belongs to.
        emoji : :obj:`typing.Union` [ :obj:`hikari.emojis.GuildEmoji`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the emoji to edit.
        name : :obj:`str`
            If specified, a new emoji name string. Keep unspecified to leave the
            name unchanged.
        roles : :obj:`typing.Sequence` [ :obj:`typing.Union` [ :obj:`hikari.guilds.GuildRole`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ] ]
            If specified, a list of objects or IDs for the new whitelisted
            roles. Set to an empty list to whitelist all roles.
            Keep unspecified to leave the same roles already set.
        reason : :obj:`str`
            If specified, the audit log reason explaining why the operation
            was performed.

        Returns
        -------
        :obj:`hikari.emojis.GuildEmoji`
            The updated emoji object.

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.NotFoundHTTPError`
            If either the guild or the emoji aren't found.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you either lack the ``MANAGE_EMOJIS`` permission or are not a
            member of the given guild.
        """
        payload = await self._session.modify_guild_emoji(
            guild_id=str(guild.id if isinstance(guild, snowflakes.UniqueEntity) else int(guild)),
            emoji_id=str(emoji.id if isinstance(emoji, snowflakes.UniqueEntity) else int(emoji)),
            name=name,
            roles=[str(role.id if isinstance(role, snowflakes.UniqueEntity) else int(role)) for role in roles]
            if roles is not ...
            else ...,
            reason=reason,
        )
        return emojis.GuildEmoji.deserialize(payload)

    async def delete_guild_emoji(
        self, guild: snowflakes.HashableT[guilds.Guild], emoji: snowflakes.HashableT[emojis.GuildEmoji],
    ) -> None:
        """Delete an emoji from a given guild.

        Parameters
        ----------
        guild : :obj:`typing.Union` [ :obj:`hikari.guilds.Guild`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the guild to delete the emoji from.
        emoji : :obj:`typing.Union` [ :obj:`hikari.emojis.GuildEmoji`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the guild emoji to be deleted.

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.NotFoundHTTPError`
            If either the guild or the emoji aren't found.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you either lack the ``MANAGE_EMOJIS`` permission or aren't a
            member of said guild.
        """
        await self._session.delete_guild_emoji(
            guild_id=str(guild.id if isinstance(guild, snowflakes.UniqueEntity) else int(guild)),
            emoji_id=str(emoji.id if isinstance(emoji, snowflakes.UniqueEntity) else int(emoji)),
        )

    async def create_guild(
        self,
        name: str,
        *,
        region: typing.Union[voices.VoiceRegion, str] = ...,
        icon_data: conversions.FileLikeT = ...,
        verification_level: typing.Union[guilds.GuildVerificationLevel, int] = ...,
        default_message_notifications: typing.Union[guilds.GuildMessageNotificationsLevel, int] = ...,
        explicit_content_filter: typing.Union[guilds.GuildExplicitContentFilterLevel, int] = ...,
        roles: typing.Sequence[guilds.GuildRole] = ...,
        channels: typing.Sequence[_channels.GuildChannelBuilder] = ...,
    ) -> guilds.Guild:
        """Create a new guild.

        Warning
        -------
        Can only be used by bots in less than ``10`` guilds.

        Parameters
        ----------
        name : :obj:`str`
            The name string for the new guild (``2-100`` characters).
        region : :obj:`str`
            If specified, the voice region ID for new guild. You can use
            :meth:`fetch_guild_voice_regions` to see which region IDs are
            available.
        icon_data : ``hikari.internal.conversions.FileLikeT``
            If specified, the guild icon image data.
        verification_level : :obj:`typing.Union` [ :obj:`hikari.guilds.GuildVerificationLevel`, :obj:`int` ]
            If specified, the verification level. Passing a raw int for this
            may lead to unexpected behaviour.
        default_message_notifications : :obj:`typing.Union` [ :obj:`hikari.guilds.GuildMessageNotificationsLevel`, :obj:`int` ]
            If specified, the default notification level. Passing a raw int for
            this may lead to unexpected behaviour.
        explicit_content_filter : :obj:`typing.Union` [ :obj:`hikari.guilds.GuildExplicitContentFilterLevel`, :obj:`int` ]
            If specified, the explicit content filter. Passing a raw int for
            this may lead to unexpected behaviour.
        roles : :obj:`typing.Sequence` [ :obj:`hikari.guilds.GuildRole` ]
            If specified, an array of role objects to be created alongside the
            guild. First element changes the ``@everyone`` role.
        channels : :obj:`typing.Sequence` [ :obj:`hikari.channels.GuildChannelBuilder` ]
            If specified, an array of guild channel builder objects to be
            created within the guild.

        Returns
        -------
        :obj:`hikari.guilds.Guild`
            The newly created guild object.

        Raises
        ------
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you are in ``10`` or more guilds.
        :obj:`hikari.errors.BadRequestHTTPError`
            If you provide unsupported fields like ``parent_id`` in channel
            objects.
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        """
        payload = await self._session.create_guild(
            name=name,
            region=getattr(region, "id", region),
            icon=conversions.get_bytes_from_resource(icon_data),
            verification_level=verification_level,
            default_message_notifications=default_message_notifications,
            explicit_content_filter=explicit_content_filter,
            roles=[role.serialize() for role in roles] if roles is not ... else ...,
            channels=[channel.serialize() for channel in channels] if channels is not ... else ...,
        )
        return guilds.Guild.deserialize(payload)

    async def fetch_guild(self, guild: snowflakes.HashableT[guilds.Guild]) -> guilds.Guild:
        """Get a given guild's object.

        Parameters
        ----------
        guild : :obj:`typing.Union` [ :obj:`hikari.guilds.Guild`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the guild to get.

        Returns
        -------
        :obj:`hikari.guilds.Guild`
            The requested guild object.

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you don't have access to the guild.
        """
        payload = await self._session.get_guild(
            guild_id=str(guild.id if isinstance(guild, snowflakes.UniqueEntity) else int(guild))
        )
        return guilds.Guild.deserialize(payload)

    async def fetch_guild_preview(self, guild: snowflakes.HashableT[guilds.Guild]) -> guilds.GuildPreview:
        """Get a given guild's object.

        Parameters
        ----------
        guild : :obj:`typing.Union` [ :obj:`hikari.guilds.Guild`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the guild to get the preview object for.

        Returns
        -------
        :obj:`hikari.guilds.GuildPreview`
            The requested guild preview object.

        Note
        ----
        Unlike other guild endpoints, the bot doesn't have to be in the target
        guild to get it's preview.

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of UINT64.
        :obj:`hikari.errors.NotFoundHTTPError`
            If the guild is not found or it isn't ``PUBLIC``.
        """
        payload = await self._session.get_guild_preview(
            guild_id=str(guild.id if isinstance(guild, snowflakes.UniqueEntity) else int(guild))
        )
        return guilds.GuildPreview.deserialize(payload)

    async def update_guild(
        self,
        guild: snowflakes.HashableT[guilds.Guild],
        *,
        name: str = ...,
        region: typing.Union[voices.VoiceRegion, str] = ...,
        verification_level: typing.Union[guilds.GuildVerificationLevel, int] = ...,
        default_message_notifications: typing.Union[guilds.GuildMessageNotificationsLevel, int] = ...,
        explicit_content_filter: typing.Union[guilds.GuildExplicitContentFilterLevel, int] = ...,
        afk_channel: snowflakes.HashableT[_channels.GuildVoiceChannel] = ...,
        afk_timeout: typing.Union[datetime.timedelta, int] = ...,
        icon_data: conversions.FileLikeT = ...,
        owner: snowflakes.HashableT[users.User] = ...,
        splash_data: conversions.FileLikeT = ...,
        system_channel: snowflakes.HashableT[_channels.Channel] = ...,
        reason: str = ...,
    ) -> guilds.Guild:
        """Edit a given guild.

        Parameters
        ----------
        guild : :obj:`typing.Union` [ :obj:`hikari.guilds.Guild`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the guild to be edited.
        name : :obj:`str`
            If specified, the new name string for the guild (``2-100`` characters).
        region : :obj:`str`
            If specified, the new voice region ID for guild. You can use
            :meth:`fetch_guild_voice_regions` to see which region IDs are
            available.
        verification_level : :obj:`typing.Union` [ :obj:`hikari.guilds.GuildVerificationLevel`, :obj:`int` ]
            If specified, the new verification level. Passing a raw int for this
            may lead to unexpected behaviour.
        default_message_notifications : :obj:`typing.Union` [ :obj:`hikari.guilds.GuildMessageNotificationsLevel`, :obj:`int` ]
            If specified, the new default notification level. Passing a raw int
            for this may lead to unexpected behaviour.
        explicit_content_filter : :obj:`typing.Union` [ :obj:`hikari.guilds.GuildExplicitContentFilterLevel`, :obj:`int` ]
            If specified, the new explicit content filter. Passing a raw int for
            this may lead to unexpected behaviour.
        afk_channel : :obj:`typing.Union` [ :obj:`hikari.channels.GuildVoiceChannel`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            If specified, the object or ID for the new AFK voice channel.
        afk_timeout : :obj:`typing.Union` [ :obj:`datetime.timedelta`, :obj:`int` ]
            If specified, the new AFK timeout seconds timedelta.
        icon_data : ``hikari.internal.conversions.FileLikeT``
            If specified, the new guild icon image file data.
        owner : :obj:`typing.Union` [ :obj:`hikari.users.User`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            If specified, the object or ID of the new guild owner.
        splash_data : ``hikari.internal.conversions.FileLikeT``
            If specified, the new new splash image file data.
        system_channel : :obj:`typing.Union` [ :obj:`hikari.channels.GuildVoiceChannel`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            If specified, the object or ID of the new system channel.
        reason : :obj:`str`
            If specified, the audit log reason explaining why the operation
            was performed.

        Returns
        -------
        :obj:`hikari.guilds.Guild`
            The edited guild object.

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you lack the ``MANAGE_GUILD`` permission or are not in the guild.
        """
        payload = await self._session.modify_guild(
            guild_id=str(guild.id if isinstance(guild, snowflakes.UniqueEntity) else int(guild)),
            name=name,
            region=getattr(region, "id", region) if region is not ... else ...,
            verification_level=verification_level,
            default_message_notifications=default_message_notifications,
            explicit_content_filter=explicit_content_filter,
            afk_timeout=afk_timeout.total_seconds() if isinstance(afk_timeout, datetime.timedelta) else afk_timeout,
            afk_channel_id=(
                str(afk_channel.id if isinstance(afk_channel, snowflakes.UniqueEntity) else int(afk_channel))
                if afk_channel is not ...
                else ...
            ),
            icon=conversions.get_bytes_from_resource(icon_data) if icon_data is not ... else ...,
            owner_id=(
                str(owner.id if isinstance(owner, snowflakes.UniqueEntity) else int(owner)) if owner is not ... else ...
            ),
            splash=conversions.get_bytes_from_resource(splash_data) if splash_data is not ... else ...,
            system_channel_id=(
                str(system_channel.id if isinstance(system_channel, snowflakes.UniqueEntity) else int(system_channel))
                if system_channel is not ...
                else ...
            ),
            reason=reason,
        )
        return guilds.Guild.deserialize(payload)

    async def delete_guild(self, guild: snowflakes.HashableT[guilds.Guild]) -> None:
        """Permanently deletes the given guild.

        You must be owner of the guild to perform this action.

        Parameters
        ----------
        guild : :obj:`typing.Union` [ :obj:`hikari.guilds.Guild`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the guild to be deleted.

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you are not the guild owner.
        """
        await self._session.delete_guild(
            guild_id=str(guild.id if isinstance(guild, snowflakes.UniqueEntity) else int(guild))
        )

    async def fetch_guild_channels(
        self, guild: snowflakes.HashableT[guilds.Guild]
    ) -> typing.Sequence[_channels.GuildChannel]:
        """Get all the channels for a given guild.

        Parameters
        ----------
        guild : :obj:`typing.Union` [ :obj:`hikari.guilds.Guild`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the guild to get the channels from.

        Returns
        -------
        :obj:`typing.Sequence` [ :obj:`hikari.channels.GuildChannel` ]
            A list of guild channel objects.

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you are not in the guild.
        """
        payload = await self._session.list_guild_channels(
            guild_id=str(guild.id if isinstance(guild, snowflakes.UniqueEntity) else int(guild))
        )
        return [_channels.deserialize_channel(channel) for channel in payload]

    async def create_guild_channel(
        self,
        guild: snowflakes.HashableT[guilds.Guild],
        name: str,
        channel_type: typing.Union[_channels.ChannelType, int] = ...,
        position: int = ...,
        topic: str = ...,
        nsfw: bool = ...,
        rate_limit_per_user: typing.Union[datetime.timedelta, int] = ...,
        bitrate: int = ...,
        user_limit: int = ...,
        permission_overwrites: typing.Sequence[_channels.PermissionOverwrite] = ...,
        parent_category: snowflakes.HashableT[_channels.GuildCategory] = ...,
        reason: str = ...,
    ) -> _channels.GuildChannel:
        """Create a channel in a given guild.

        Parameters
        ----------
        guild : :obj:`typing.Union` [ :obj:`hikari.guilds.Guild`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the guild to create the channel in.
        name : :obj:`str`
            If specified, the name for the channel. This must be
            inclusively between ``1` and ``100`` characters in length.
        channel_type: :obj:`typing.Union` [ :obj:`hikari.channels.ChannelType`, :obj:`int` ]
            If specified, the channel type, passing through a raw integer here
            may lead to unexpected behaviour.
        position : :obj:`int`
            If specified, the position to change the channel to.
        topic : :obj:`str`
            If specified, the topic to set. This is only applicable to
            text channels. This must be inclusively between ``0`` and ``1024``
            characters in length.
        nsfw : :obj:`bool`
            If specified, whether the channel will be marked as NSFW.
            Only applicable for text channels.
        rate_limit_per_user : :obj:`typing.Union` [ :obj:`datetime.timedelta`, :obj:`int` ]
            If specified, the second time delta the user has to wait before
            sending another message.  This will not apply to bots, or to
            members with ``MANAGE_MESSAGES`` or ``MANAGE_CHANNEL`` permissions.
            This must be inclusively between ``0`` and ``21600`` seconds.
        bitrate : :obj:`int`
            If specified, the bitrate in bits per second allowable for the
            channel. This only applies to voice channels and must be inclusively
            between ``8000`` and ``96000`` for normal servers or ``8000`` and
            ``128000`` for VIP servers.
        user_limit : :obj:`int`
            If specified, the max number of users to allow in a voice channel.
            This must be between ``0`` and ``99`` inclusive, where
            ``0`` implies no limit.
        permission_overwrites : :obj:`typing.Sequence` [ :obj:`hikari.channels.PermissionOverwrite` ]
            If specified, the list of permission overwrite objects that are
            category specific to replace the existing overwrites with.
        parent_category : :obj:`typing.Union` [ :obj:`hikari.channels.GuildCategory`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            If specified, the object or ID of the parent category to set for
             the channel.
        reason : :obj:`str`
            If specified, the audit log reason explaining why the operation
            was performed.

        Returns
        -------
        :obj:`hikari.channels.GuildChannel`
            The newly created channel object.

        Raises
        ------
        :obj:`hikari.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you lack the ``MANAGE_CHANNEL`` permission or are not in the
            guild.
        :obj:`hikari.errors.BadRequestHTTPError`
            If you provide incorrect options for the corresponding channel type
            (e.g. a ``bitrate`` for a text channel).
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        """
        payload = await self._session.create_guild_channel(
            guild_id=str(guild.id if isinstance(guild, snowflakes.UniqueEntity) else int(guild)),
            name=name,
            type_=channel_type,
            position=position,
            topic=topic,
            nsfw=nsfw,
            rate_limit_per_user=(
                int(rate_limit_per_user.total_seconds())
                if isinstance(rate_limit_per_user, datetime.timedelta)
                else rate_limit_per_user
            ),
            bitrate=bitrate,
            user_limit=user_limit,
            permission_overwrites=(
                [po.serialize() for po in permission_overwrites] if permission_overwrites is not ... else ...
            ),
            parent_id=(
                str(
                    parent_category.id if isinstance(parent_category, snowflakes.UniqueEntity) else int(parent_category)
                )
                if parent_category is not ...
                else ...
            ),
            reason=reason,
        )
        return _channels.deserialize_channel(payload)

    async def reposition_guild_channels(
        self,
        guild: snowflakes.HashableT[guilds.Guild],
        channel: typing.Tuple[int, snowflakes.HashableT[_channels.GuildChannel]],
        *additional_channels: typing.Tuple[int, snowflakes.HashableT[_channels.GuildChannel]],
    ) -> None:
        """Edits the position of one or more given channels.

        Parameters
        ----------
        guild : :obj:`typing.Union` [ :obj:`hikari.guilds.Guild`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the guild in which to edit the channels.
        channel : :obj:`typing.Tuple` [ :obj:`int` , :obj:`typing.Union` [ :obj:`hikari.channels.GuildChannel`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ] ]
            The first channel to change the position of. This is a tuple of the
            integer position the channel object or ID.
        *additional_channels : :obj:`typing.Tuple` [ :obj:`int`, :obj:`typing.Union` [ :obj:`hikari.channels.GuildChannel`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ] ]
            Optional additional channels to change the position of. These must
            be tuples of integer positions to change to and the channel object
            or ID and the.

        Raises
        ------
        :obj:`hikari.errors.NotFoundHTTPError`
            If either the guild or any of the channels aren't found.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you either lack the ``MANAGE_CHANNELS`` permission or are not a
            member of said guild or are not in the guild.
        :obj:`hikari.errors.BadRequestHTTPError`
            If you provide anything other than the ``id`` and ``position``
            fields for the channels.
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        """
        await self._session.modify_guild_channel_positions(
            str(guild.id if isinstance(guild, snowflakes.UniqueEntity) else int(guild)),
            *[
                (str(channel.id if isinstance(channel, snowflakes.UniqueEntity) else int(channel)), position)
                for position, channel in [channel, *additional_channels]
            ],
        )

    async def fetch_member(
        self, guild: snowflakes.HashableT[guilds.Guild], user: snowflakes.HashableT[users.User],
    ) -> guilds.GuildMember:
        """Get a given guild member.

        Parameters
        ----------
        guild : :obj:`typing.Union` [ :obj:`hikari.guilds.Guild`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the guild to get the member from.
        user : :obj:`typing.Union` [ :obj:`hikari.users.User`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the member to get.

        Returns
        -------
        :obj:`hikari.guilds.GuildMember`
            The requested member object.

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.NotFoundHTTPError`
            If either the guild or the member aren't found.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you don't have access to the target guild.
        """
        payload = await self._session.get_guild_member(
            guild_id=str(guild.id if isinstance(guild, snowflakes.UniqueEntity) else int(guild)),
            user_id=str(user.id if isinstance(user, snowflakes.UniqueEntity) else int(user)),
        )
        return guilds.GuildMember.deserialize(payload)

    def fetch_members_after(
        self,
        guild: snowflakes.HashableT[guilds.Guild],
        *,
        after: typing.Union[datetime.datetime, snowflakes.HashableT[users.User]] = 0,
        limit: typing.Optional[int] = None,
    ) -> typing.AsyncIterator[guilds.GuildMember]:
        """Get an async iterator of all the members in a given guild.

        This returns the member objects with a user object/ID that was created
        after the given user object/ID or from the member object or the oldest
        user.

        Parameters
        ----------
        guild : :obj:`typing.Union` [ :obj:`hikari.guilds.Guild`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the guild to get the members from.
        limit : :obj:`int`
            If specified, the maximum number of members this iterator
            should return.
        after : :obj:`typing.Union` [ :obj:`datetime.datetime`, :obj:`hikari.users.User`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the user this iterator should start
            after if specified, else this will start at the oldest user.

        Example
        -------
        .. code-block:: python

            async for user in client.fetch_members_after(guild, after=9876543, limit=1231):
                if member.user.username[0] in HOIST_BLACKLIST:
                    await client.update_member(member, nickname="💩")

        Returns
        -------
        :obj:`typing.AsyncIterator` [ :obj:`hikari.guilds.GuildMember` ]
            An async iterator of member objects.

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you are not in the guild.
        """
        if isinstance(after, datetime.datetime):
            after = str(snowflakes.Snowflake.from_datetime(after))
        else:
            after = str(after.id if isinstance(after, snowflakes.UniqueEntity) else int(after))
        return self._pagination_handler(
            guild_id=str(guild.id if isinstance(guild, snowflakes.UniqueEntity) else int(guild)),
            deserializer=guilds.GuildMember.deserialize,
            direction="after",
            request=self._session.list_guild_members,
            reversing=False,
            start=after,
            limit=limit,
            id_getter=_get_member_id,
        )

    async def update_member(
        self,
        guild: snowflakes.HashableT[guilds.Guild],
        user: snowflakes.HashableT[users.User],
        nickname: typing.Optional[str] = ...,
        roles: typing.Sequence[snowflakes.HashableT[guilds.GuildRole]] = ...,
        mute: bool = ...,
        deaf: bool = ...,
        voice_channel: typing.Optional[snowflakes.HashableT[_channels.GuildVoiceChannel]] = ...,
        reason: str = ...,
    ) -> None:
        """Edits a guild's member, any unspecified fields will not be changed.

        Parameters
        ----------
        guild : :obj:`typing.Union` [ :obj:`hikari.guilds.Guild`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the guild to edit the member from.
        user : :obj:`typing.Union` [ :obj:`hikari.guilds.GuildMember`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the member to edit.
        nickname : :obj:`str`, optional
            If specified, the new nickname string. Setting it to :obj:`None`
            explicitly will clear the nickname.
        roles : :obj:`typing.Sequence` [ :obj:`typing.Union` [ :obj:`hikari.guilds.GuildRole`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ] ]
            If specified, a list of role IDs the member should have.
        mute : :obj:`bool`
            If specified, whether the user should be muted in the voice channel
            or not.
        deaf : :obj:`bool`
            If specified, whether the user should be deafen in the voice
            channel or not.
        voice_channel : :obj:`typing.Union` [ :obj:`hikari.channels.GuildVoiceChannel`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ], optional
            If specified, the ID of the channel to move the member to. Setting
            it to :obj:`None` explicitly will disconnect the user.
        reason : :obj:`str`
            If specified, the audit log reason explaining why the operation
            was performed.

        Raises
        ------
        :obj:`hikari.errors.NotFoundHTTPError`
            If either the guild, user, channel or any of the roles aren't found.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you lack any of the applicable permissions
            (``MANAGE_NICKNAMES``, ``MANAGE_ROLES``, ``MUTE_MEMBERS``, ``DEAFEN_MEMBERS`` or ``MOVE_MEMBERS``).
            Note that to move a member you must also have permission to connect
            to the end channel. This will also be raised if you're not in the
            guild.
        :obj:`hikari.errors.BadRequestHTTPError`
            If you pass ``mute``, ``deaf`` or ``channel_id`` while the member
            is not connected to a voice channel.
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        """
        await self._session.modify_guild_member(
            guild_id=str(guild.id if isinstance(guild, snowflakes.UniqueEntity) else int(guild)),
            user_id=str(user.id if isinstance(user, snowflakes.UniqueEntity) else int(user)),
            nick=nickname,
            roles=(
                [str(role.id if isinstance(role, snowflakes.UniqueEntity) else int(role)) for role in roles]
                if roles is not ...
                else ...
            ),
            mute=mute,
            deaf=deaf,
            channel_id=(
                str(voice_channel.id if isinstance(voice_channel, snowflakes.UniqueEntity) else int(voice_channel))
                if voice_channel is not ...
                else ...
            ),
            reason=reason,
        )

    async def update_my_member_nickname(
        self, guild: snowflakes.HashableT[guilds.Guild], nickname: typing.Optional[str], *, reason: str = ...,
    ) -> None:
        """Edits the current user's nickname for a given guild.

        Parameters
        ----------
        guild : :obj:`typing.Union` [ :obj:`hikari.guilds.Guild`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the guild you want to change the nick on.
        nickname : :obj:`str`, optional
            The new nick string. Setting this to `None` clears the nickname.
        reason : :obj:`str`
            If specified, the audit log reason explaining why the operation
            was performed.

        Raises
        ------
        :obj:`hikari.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you lack the ``CHANGE_NICKNAME`` permission or are not in the
            guild.
        :obj:`hikari.errors.BadRequestHTTPError`
            If you provide a disallowed nickname, one that is too long, or one
            that is empty.
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        """
        await self._session.modify_current_user_nick(
            guild_id=str(guild.id if isinstance(guild, snowflakes.UniqueEntity) else int(guild)),
            nick=nickname,
            reason=reason,
        )

    async def add_role_to_member(
        self,
        guild: snowflakes.HashableT[guilds.Guild],
        user: snowflakes.HashableT[users.User],
        role: snowflakes.HashableT[guilds.GuildRole],
        *,
        reason: str = ...,
    ) -> None:
        """Add a role to a given member.

        Parameters
        ----------
        guild : :obj:`typing.Union` [ :obj:`hikari.guilds.Guild`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the guild the member belongs to.
        user : :obj:`typing.Union` [ :obj:`hikari.users.User`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the member you want to add the role to.
        role : :obj:`typing.Union` [ :obj:`hikari.guilds.GuildRole`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the role you want to add.
        reason : :obj:`str`
            If specified, the audit log reason explaining why the operation
            was performed.

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.NotFoundHTTPError`
            If either the guild, member or role aren't found.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you lack the ``MANAGE_ROLES`` permission or are not in the guild.
        """
        await self._session.add_guild_member_role(
            guild_id=str(guild.id if isinstance(guild, snowflakes.UniqueEntity) else int(guild)),
            user_id=str(user.id if isinstance(user, snowflakes.UniqueEntity) else int(user)),
            role_id=str(role.id if isinstance(role, snowflakes.UniqueEntity) else int(role)),
            reason=reason,
        )

    async def remove_role_from_member(
        self,
        guild: snowflakes.HashableT[guilds.Guild],
        user: snowflakes.HashableT[users.User],
        role: snowflakes.HashableT[guilds.GuildRole],
        *,
        reason: str = ...,
    ) -> None:
        """Remove a role from a given member.

        Parameters
        ----------
        guild : :obj:`typing.Union` [ :obj:`hikari.guilds.Guild`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the guild the member belongs to.
        user : :obj:`typing.Union` [ :obj:`hikari.users.User`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the member you want to remove the role from.
        role : :obj:`typing.Union` [ :obj:`hikari.guilds.GuildRole`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the role you want to remove.
        reason : :obj:`str`
            If specified, the audit log reason explaining why the operation
            was performed.

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.NotFoundHTTPError`
            If either the guild, member or role aren't found.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you lack the ``MANAGE_ROLES`` permission or are not in the guild.
        """
        await self._session.remove_guild_member_role(
            guild_id=str(guild.id if isinstance(guild, snowflakes.UniqueEntity) else int(guild)),
            user_id=str(user.id if isinstance(user, snowflakes.UniqueEntity) else int(user)),
            role_id=str(role.id if isinstance(role, snowflakes.UniqueEntity) else int(role)),
            reason=reason,
        )

    async def kick_member(
        self, guild: snowflakes.HashableT[guilds.Guild], user: snowflakes.HashableT[users.User], *, reason: str = ...,
    ) -> None:
        """Kicks a user from a given guild.

        Parameters
        ----------
        guild : :obj:`typing.Union` [ :obj:`hikari.guilds.Guild`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the guild the member belongs to.
        user : :obj:`typing.Union` [ :obj:`hikari.users.User`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the member you want to kick.
        reason : :obj:`str`
            If specified, the audit log reason explaining why the operation
            was performed.

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.NotFoundHTTPError`
            If either the guild or member aren't found.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you lack the ``KICK_MEMBERS`` permission or are not in the guild.
        """
        await self._session.remove_guild_member(
            guild_id=str(guild.id if isinstance(guild, snowflakes.UniqueEntity) else int(guild)),
            user_id=str(user.id if isinstance(user, snowflakes.UniqueEntity) else int(user)),
            reason=reason,
        )

    async def fetch_ban(
        self, guild: snowflakes.HashableT[guilds.Guild], user: snowflakes.HashableT[users.User],
    ) -> guilds.GuildMemberBan:
        """Get a ban from a given guild.

        Parameters
        ----------
         guild : :obj:`typing.Union` [ :obj:`hikari.guilds.Guild`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the guild you want to get the ban from.
         user : :obj:`typing.Union` [ :obj:`hikari.users.User`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the user to get the ban information for.

        Returns
        -------
        :obj:`hikari.guilds.GuildMemberBan`
            A ban object for the requested user.

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.NotFoundHTTPError`
            If either the guild or the user aren't found, or if the user is not
            banned.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you lack the ``BAN_MEMBERS`` permission or are not in the guild.
        """
        payload = await self._session.get_guild_ban(
            guild_id=str(guild.id if isinstance(guild, snowflakes.UniqueEntity) else int(guild)),
            user_id=str(user.id if isinstance(user, snowflakes.UniqueEntity) else int(user)),
        )
        return guilds.GuildMemberBan.deserialize(payload)

    async def fetch_bans(self, guild: snowflakes.HashableT[guilds.Guild],) -> typing.Sequence[guilds.GuildMemberBan]:
        """Get the bans for a given guild.

        Parameters
        ----------
        guild : :obj:`typing.Union` [ :obj:`hikari.guilds.Guild`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the guild you want to get the bans from.

        Returns
        -------
        :obj:`typing.Sequence` [ :obj:`hikari.guilds.GuildMemberBan` ]
            A list of ban objects.

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you lack the ``BAN_MEMBERS`` permission or are not in the guild.
        """
        payload = await self._session.get_guild_bans(
            guild_id=str(guild.id if isinstance(guild, snowflakes.UniqueEntity) else int(guild))
        )
        return [guilds.GuildMemberBan.deserialize(ban) for ban in payload]

    async def ban_member(
        self,
        guild: snowflakes.HashableT[guilds.Guild],
        user: snowflakes.HashableT[users.User],
        *,
        delete_message_days: typing.Union[datetime.timedelta, int] = ...,
        reason: str = ...,
    ) -> None:
        """Bans a user from a given guild.

        Parameters
        ----------
        guild : :obj:`typing.Union` [ :obj:`hikari.guilds.Guild`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the guild the member belongs to.
        user : :obj:`typing.Union` [ :obj:`hikari.users.User`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the member you want to ban.
        delete_message_days : :obj:`typing.Union` [ :obj:`datetime.timedelta`, :obj:`int` ]
            If specified, the tim delta of how many days of messages from the
            user should be removed.
        reason : :obj:`str`
            If specified, the audit log reason explaining why the operation
            was performed.

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.NotFoundHTTPError`
            If either the guild or member aren't found.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you lack the ``BAN_MEMBERS`` permission or are not in the guild.
        """
        await self._session.create_guild_ban(
            guild_id=str(guild.id if isinstance(guild, snowflakes.UniqueEntity) else int(guild)),
            user_id=str(user.id if isinstance(user, snowflakes.UniqueEntity) else int(user)),
            delete_message_days=getattr(delete_message_days, "days", delete_message_days),
            reason=reason,
        )

    async def unban_member(
        self, guild: snowflakes.HashableT[guilds.Guild], user: snowflakes.HashableT[users.User], *, reason: str = ...,
    ) -> None:
        """Un-bans a user from a given guild.

        Parameters
        ----------
        guild : :obj:`typing.Union` [ :obj:`hikari.guilds.Guild`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the guild to un-ban the user from.
        user : :obj:`typing.Union` [ :obj:`hikari.users.User`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The ID of the user you want to un-ban.
        reason : :obj:`str`
            If specified, the audit log reason explaining why the operation
            was performed.

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.NotFoundHTTPError`
            If either the guild or member aren't found, or the member is not
            banned.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you lack the ``BAN_MEMBERS`` permission or are not a in the
            guild.
        """
        await self._session.remove_guild_ban(
            guild_id=str(guild.id if isinstance(guild, snowflakes.UniqueEntity) else int(guild)),
            user_id=str(user.id if isinstance(user, snowflakes.UniqueEntity) else int(user)),
            reason=reason,
        )

    async def fetch_roles(
        self, guild: snowflakes.HashableT[guilds.Guild],
    ) -> typing.Mapping[snowflakes.Snowflake, guilds.GuildRole]:
        """Get the roles for a given guild.

        Parameters
        ----------
        guild : :obj:`typing.Union` [ :obj:`hikari.guilds.Guild`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the guild you want to get the roles from.

        Returns
        -------
        :obj:`typing.Mapping` [ :obj:`hikari.snowflakes.Snowflake`, :obj:`hikari.guilds.GuildRole` ]
            A list of role objects.

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you're not in the guild.
        """
        payload = await self._session.get_guild_roles(
            guild_id=str(guild.id if isinstance(guild, snowflakes.UniqueEntity) else int(guild))
        )
        return {role.id: role for role in map(guilds.GuildRole.deserialize, payload)}

    async def create_role(
        self,
        guild: snowflakes.HashableT[guilds.Guild],
        *,
        name: str = ...,
        permissions: typing.Union[_permissions.Permission, int] = ...,
        color: typing.Union[colors.Color, int] = ...,
        hoist: bool = ...,
        mentionable: bool = ...,
        reason: str = ...,
    ) -> guilds.GuildRole:
        """Create a new role for a given guild.

        Parameters
        ----------
        guild : :obj:`typing.Union` [ :obj:`hikari.guilds.Guild`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the guild you want to create the role on.
        name : :obj:`str`
            If specified, the new role name string.
        permissions : :obj:`typing.Union` [ :obj:`hikari.permissions.Permission`, :obj:`int` ]
            If specified, the permissions integer for the role, passing a raw
            integer rather than the int flag may lead to unexpected results.
        color : :obj:`typing.Union` [ :obj:`hikari.colors.Color`, :obj:`int` ]
            If specified, the color for the role.
        hoist : :obj:`bool`
            If specified, whether the role will be hoisted.
        mentionable : :obj:`bool`
           If specified, whether the role will be able to be mentioned by any
           user.
        reason : :obj:`str`
            If specified, the audit log reason explaining why the operation
            was performed.

        Returns
        -------
        :obj:`hikari.guilds.GuildRole`
            The newly created role object.

        Raises
        ------
        :obj:`hikari.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you lack the ``MANAGE_ROLES`` permission or you're not in the
            guild.
        :obj:`hikari.errors.BadRequestHTTPError`
            If you provide invalid values for the role attributes.
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        """
        payload = await self._session.create_guild_role(
            guild_id=str(guild.id if isinstance(guild, snowflakes.UniqueEntity) else int(guild)),
            name=name,
            permissions=permissions,
            color=color,
            hoist=hoist,
            mentionable=mentionable,
            reason=reason,
        )
        return guilds.GuildRole.deserialize(payload)

    async def reposition_roles(
        self,
        guild: snowflakes.HashableT[guilds.Guild],
        role: typing.Tuple[int, snowflakes.HashableT[guilds.GuildRole]],
        *additional_roles: typing.Tuple[int, snowflakes.HashableT[guilds.GuildRole]],
    ) -> typing.Sequence[guilds.GuildRole]:
        """Edits the position of two or more roles in a given guild.

        Parameters
        ----------
        guild : :obj:`typing.Union` [ :obj:`hikari.guilds.Guild`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The ID of the guild the roles belong to.
        role : :obj:`typing.Tuple` [ :obj:`int`, :obj:`typing.Union` [ :obj:`hikari.guilds.GuildRole`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ] ]
            The first role to move. This is a tuple of the integer position and
            the role object or ID.
        *additional_roles : :obj:`typing.Tuple` [ :obj:`int`, :obj:`typing.Union` [ :obj:`hikari.guilds.GuildRole`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ] ]
            Optional extra roles to move. These must be tuples of the integer
            position and the role object or ID.

        Returns
        -------
        :obj:`typing.Sequence` [ :obj:`hikari.guilds.GuildRole` ]
            A list of all the guild roles.

        Raises
        ------
        :obj:`hikari.errors.NotFoundHTTPError`
            If either the guild or any of the roles aren't found.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you lack the ``MANAGE_ROLES`` permission or you're not in the
            guild.
        :obj:`hikari.errors.BadRequestHTTPError`
            If you provide invalid values for the `position` fields.
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        """
        payload = await self._session.modify_guild_role_positions(
            str(guild.id if isinstance(guild, snowflakes.UniqueEntity) else int(guild)),
            *[
                (str(channel.id if isinstance(channel, snowflakes.UniqueEntity) else int(channel)), position)
                for position, channel in [role, *additional_roles]
            ],
        )
        return [guilds.GuildRole.deserialize(role) for role in payload]

    async def update_role(
        self,
        guild: snowflakes.HashableT[guilds.Guild],
        role: snowflakes.HashableT[guilds.GuildRole],
        *,
        name: str = ...,
        permissions: typing.Union[_permissions.Permission, int] = ...,
        color: typing.Union[colors.Color, int] = ...,
        hoist: bool = ...,
        mentionable: bool = ...,
        reason: str = ...,
    ) -> guilds.GuildRole:
        """Edits a role in a given guild.

        Parameters
        ----------
        guild : :obj:`typing.Union` [ :obj:`hikari.guilds.Guild`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the guild the role belong to.
        role : :obj:`typing.Union` [ :obj:`hikari.guilds.GuildRole`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the role you want to edit.
        name : :obj:`str`
            If specified, the new role's name string.
        permissions : :obj:`typing.Union` [ :obj:`hikari.permissions.Permission`, :obj:`int` ]
            If specified, the new permissions integer for the role, passing a
            raw integer for this may lead to unexpected behaviour.
        color : :obj:`typing.Union` [ :obj:`hikari.colors.Color`, :obj:`int` ]
            If specified, the new color for the new role passing a raw integer
            for this may lead to unexpected behaviour.
        hoist : :obj:`bool`
            If specified, whether the role should hoist or not.
        mentionable : :obj:`bool`
            If specified, whether the role should be mentionable or not.
        reason : :obj:`str`
            If specified, the audit log reason explaining why the operation
            was performed.

        Returns
        -------
        :obj:`hikari.guilds.GuildRole`
            The edited role object.

        Raises
        ------
        :obj:`hikari.errors.NotFoundHTTPError`
            If either the guild or role aren't found.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you lack the ``MANAGE_ROLES`` permission or you're not in the
            guild.
        :obj:`hikari.errors.BadRequestHTTPError`
            If you provide invalid values for the role attributes.
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        """
        payload = await self._session.modify_guild_role(
            guild_id=str(guild.id if isinstance(guild, snowflakes.UniqueEntity) else int(guild)),
            role_id=str(role.id if isinstance(role, snowflakes.UniqueEntity) else int(role)),
            name=name,
            permissions=permissions,
            color=color,
            hoist=hoist,
            mentionable=mentionable,
            reason=reason,
        )
        return guilds.GuildRole.deserialize(payload)

    async def delete_role(
        self, guild: snowflakes.HashableT[guilds.Guild], role: snowflakes.HashableT[guilds.GuildRole],
    ) -> None:
        """Delete a role from a given guild.

        Parameters
        ----------
        guild : :obj:`typing.Union` [ :obj:`hikari.guilds.Guild`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the guild you want to remove the role from.
        role : :obj:`typing.Union` [ :obj:`hikari.guilds.GuildRole`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the role you want to delete.

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.NotFoundHTTPError`
            If either the guild or the role aren't found.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you lack the ``MANAGE_ROLES`` permission or are not in the guild.
        """
        await self._session.delete_guild_role(
            guild_id=str(guild.id if isinstance(guild, snowflakes.UniqueEntity) else int(guild)),
            role_id=str(role.id if isinstance(role, snowflakes.UniqueEntity) else int(role)),
        )

    async def estimate_guild_prune_count(
        self, guild: snowflakes.HashableT[guilds.Guild], days: typing.Union[datetime.timedelta, int],
    ) -> int:
        """Get the estimated prune count for a given guild.

        Parameters
        ----------
        guild : :obj:`typing.Union` [ :obj:`hikari.guilds.Guild`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the guild you want to get the count for.
        days : :obj:`typing.Union` [ :obj:`datetime.timedelta`, :obj:`int` ]
            The time delta of days to count prune for (at least ``1``).

        Returns
        -------
        :obj:`int`
            The number of members estimated to be pruned.

        Raises
        ------
        :obj:`hikari.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you lack the ``KICK_MEMBERS`` or you are not in the guild.
        :obj:`hikari.errors.BadRequestHTTPError`
            If you pass an invalid amount of days.
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        """
        return await self._session.get_guild_prune_count(
            guild_id=str(guild.id if isinstance(guild, snowflakes.UniqueEntity) else int(guild)),
            days=getattr(days, "days", days),
        )

    async def begin_guild_prune(
        self,
        guild: snowflakes.HashableT[guilds.Guild],
        days: typing.Union[datetime.timedelta, int],
        *,
        compute_prune_count: bool = ...,
        reason: str = ...,
    ) -> int:
        """Prunes members of a given guild based on the number of inactive days.

        Parameters
        ----------
        guild : :obj:`typing.Union` [ :obj:`hikari.guilds.Guild`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the guild you want to prune member of.
        days : :obj:`typing.Union` [ :obj:`datetime.timedelta`, :obj:`int` ]
            The time delta of inactivity days you want to use as filter.
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
            is :obj:`True`, else :obj:`None`.

        Raises
        ------
        :obj:`hikari.errors.NotFoundHTTPError`
            If the guild is not found:
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you lack the ``KICK_MEMBER`` permission or are not in the guild.
        :obj:`hikari.errors.BadRequestHTTPError`
            If you provide invalid values for the ``days`` or
            ``compute_prune_count`` fields.
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        """
        return await self._session.begin_guild_prune(
            guild_id=str(guild.id if isinstance(guild, snowflakes.UniqueEntity) else int(guild)),
            days=getattr(days, "days", days),
            compute_prune_count=compute_prune_count,
            reason=reason,
        )

    async def fetch_guild_voice_regions(
        self, guild: snowflakes.HashableT[guilds.Guild],
    ) -> typing.Sequence[voices.VoiceRegion]:
        """Get the voice regions for a given guild.

        Parameters
        ----------
        guild : :obj:`typing.Union` [ :obj:`hikari.guilds.Guild`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the guild to get the voice regions for.

        Returns
        -------
        :obj:`typing.Sequence` [ :obj:`hikari.voices.VoiceRegion` ]
            A list of voice region objects.

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you are not in the guild.
        """
        payload = await self._session.get_guild_voice_regions(
            guild_id=str(guild.id if isinstance(guild, snowflakes.UniqueEntity) else int(guild))
        )
        return [voices.VoiceRegion.deserialize(region) for region in payload]

    async def fetch_guild_invites(
        self, guild: snowflakes.HashableT[guilds.Guild],
    ) -> typing.Sequence[invites.InviteWithMetadata]:
        """Get the invites for a given guild.

        Parameters
        ----------
        guild : :obj:`typing.Union` [ :obj:`hikari.guilds.Guild`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the guild to get the invites for.

        Returns
        -------
        :obj:`typing.Sequence` [ :obj:`hikari.invites.InviteWithMetadata` ]
            A list of invite objects (with metadata).

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you lack the ``MANAGE_GUILD`` permission or are not in the guild.
        """
        payload = await self._session.get_guild_invites(
            guild_id=str(guild.id if isinstance(guild, snowflakes.UniqueEntity) else int(guild))
        )
        return [invites.InviteWithMetadata.deserialize(invite) for invite in payload]

    async def fetch_integrations(
        self, guild: snowflakes.HashableT[guilds.Guild]
    ) -> typing.Sequence[guilds.GuildIntegration]:
        """Get the integrations for a given guild.

        Parameters
        ----------
        guild : :obj:`typing.Union` [ :obj:`hikari.guilds.Guild`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the guild to get the integrations for.

        Returns
        -------
        :obj:`typing.Sequence` [ :obj:`hikari.guilds.GuildIntegration` ]
            A list of integration objects.

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you lack the ``MANAGE_GUILD`` permission or are not in the guild.
        """
        payload = await self._session.get_guild_integrations(
            guild_id=str(guild.id if isinstance(guild, snowflakes.UniqueEntity) else int(guild))
        )
        return [guilds.GuildIntegration.deserialize(integration) for integration in payload]

    async def update_integration(
        self,
        guild: snowflakes.HashableT[guilds.Guild],
        integration: snowflakes.HashableT[guilds.GuildIntegration],
        *,
        expire_behaviour: typing.Union[guilds.IntegrationExpireBehaviour, int] = ...,
        expire_grace_period: typing.Union[datetime.timedelta, int] = ...,
        enable_emojis: bool = ...,
        reason: str = ...,
    ) -> None:
        """Edits an integrations for a given guild.

        Parameters
        ----------
        guild : :obj:`typing.Union` [ :obj:`hikari.guilds.Guild`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the guild to which the integration belongs to.
        integration : :obj:`typing.Union` [ :obj:`hikari.guilds.GuildIntegration`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the integration to update.
        expire_behaviour : :obj:`typing.Union` [ :obj:`hikari.guilds.IntegrationExpireBehaviour`, :obj:`int` ]
            If specified, the behaviour for when an integration subscription
            expires (passing a raw integer for this may lead to unexpected
            behaviour).
        expire_grace_period : :obj:`typing.Union` [ :obj:`datetime.timedelta`, :obj:`int` ]
            If specified, time time delta of how many days the integration will
            ignore lapsed subscriptions for.
        enable_emojis : :obj:`bool`
            If specified, whether emojis should be synced for this integration.
        reason : :obj:`str`
            If specified, the audit log reason explaining why the operation
            was performed.

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.NotFoundHTTPError`
            If either the guild or the integration aren't found.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you lack the ``MANAGE_GUILD`` permission or are not in the guild.
        """
        await self._session.modify_guild_integration(
            guild_id=str(guild.id if isinstance(guild, snowflakes.UniqueEntity) else int(guild)),
            integration_id=str(
                integration.id if isinstance(integration, snowflakes.UniqueEntity) else int(integration)
            ),
            expire_behaviour=expire_behaviour,
            expire_grace_period=getattr(expire_grace_period, "days", expire_grace_period),
            enable_emojis=enable_emojis,
            reason=reason,
        )

    async def delete_integration(
        self,
        guild: snowflakes.HashableT[guilds.Guild],
        integration: snowflakes.HashableT[guilds.GuildIntegration],
        *,
        reason: str = ...,
    ) -> None:
        """Delete an integration for the given guild.

        Parameters
        ----------
        guild : :obj:`typing.Union` [ :obj:`hikari.guilds.Guild`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the guild to which the integration belongs to.
        integration : :obj:`typing.Union` [ :obj:`hikari.guilds.GuildIntegration`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the integration to delete.
        reason : :obj:`str`
            If specified, the audit log reason explaining why the operation
            was performed.

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.NotFoundHTTPError`
            If either the guild or the integration aren't found.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you lack the `MANAGE_GUILD` permission or are not in the guild.
        """
        await self._session.delete_guild_integration(
            guild_id=str(guild.id if isinstance(guild, snowflakes.UniqueEntity) else int(guild)),
            integration_id=str(
                integration.id if isinstance(integration, snowflakes.UniqueEntity) else int(integration)
            ),
            reason=reason,
        )

    async def sync_guild_integration(
        self, guild: snowflakes.HashableT[guilds.Guild], integration: snowflakes.HashableT[guilds.GuildIntegration],
    ) -> None:
        """Sync the given integration's subscribers/emojis.

        Parameters
        ----------
        guild : :obj:`typing.Union` [ :obj:`hikari.guilds.Guild`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the guild to which the integration belongs to.
        integration : :obj:`typing.Union` [ :obj:`hikari.guilds.GuildIntegration`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The ID of the integration to sync.

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.NotFoundHTTPError`
            If either the guild or the integration aren't found.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you lack the ``MANAGE_GUILD`` permission or are not in the guild.
        """
        await self._session.sync_guild_integration(
            guild_id=str(guild.id if isinstance(guild, snowflakes.UniqueEntity) else int(guild)),
            integration_id=str(
                integration.id if isinstance(integration, snowflakes.UniqueEntity) else int(integration)
            ),
        )

    async def fetch_guild_embed(self, guild: snowflakes.HashableT[guilds.Guild],) -> guilds.GuildEmbed:
        """Get the embed for a given guild.

        Parameters
        ----------
        guild : :obj:`typing.Union` [ :obj:`hikari.guilds.Guild`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the guild to get the embed for.

        Returns
        -------
        :obj:`hikari.guilds.GuildEmbed`
            A guild embed object.

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you either lack the ``MANAGE_GUILD`` permission or are not in
            the guild.
        """
        payload = await self._session.get_guild_embed(
            guild_id=str(guild.id if isinstance(guild, snowflakes.UniqueEntity) else int(guild))
        )
        return guilds.GuildEmbed.deserialize(payload)

    async def update_guild_embed(
        self,
        guild: snowflakes.HashableT[guilds.Guild],
        *,
        channel: snowflakes.HashableT[_channels.GuildChannel] = ...,
        enabled: bool = ...,
        reason: str = ...,
    ) -> guilds.GuildEmbed:
        """Edits the embed for a given guild.

        Parameters
        ----------
        guild : :obj:`typing.Union` [ :obj:`hikari.guilds.Guild`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the guild to edit the embed for.
        channel : :obj:`typing.Union` [ :obj:`hikari.channels.GuildChannel`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ], optional
            If specified, the object or ID of the channel that this embed's
            invite should target. Set to :obj:`None` to disable invites for this
            embed.
        enabled : :obj:`bool`
            If specified, whether this embed should be enabled.
        reason : :obj:`str`
            If specified, the audit log reason explaining why the operation
            was performed.

        Returns
        -------
        :obj:`hikari.guilds.GuildEmbed`
            The updated embed object.

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you either lack the ``MANAGE_GUILD`` permission or are not in
            the guild.
        """
        payload = await self._session.modify_guild_embed(
            guild_id=str(guild.id if isinstance(guild, snowflakes.UniqueEntity) else int(guild)),
            channel_id=(
                str(channel.id if isinstance(channel, snowflakes.UniqueEntity) else int(channel))
                if channel is not ...
                else ...
            ),
            enabled=enabled,
            reason=reason,
        )
        return guilds.GuildEmbed.deserialize(payload)

    async def fetch_guild_vanity_url(self, guild: snowflakes.HashableT[guilds.Guild],) -> invites.VanityUrl:
        """
        Get the vanity URL for a given guild.

        Parameters
        ----------
        guild : :obj:`typing.Union` [ :obj:`hikari.guilds.Guild`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the guild to get the vanity URL for.

        Returns
        -------
        :obj:`hikari.invites.VanityUrl`
            A partial invite object containing the vanity URL in the ``code``
            field.

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you either lack the ``MANAGE_GUILD`` permission or are not in
            the guild.
        """
        payload = await self._session.get_guild_vanity_url(
            guild_id=str(guild.id if isinstance(guild, snowflakes.UniqueEntity) else int(guild))
        )
        return invites.VanityUrl.deserialize(payload)

    def format_guild_widget_image(self, guild: snowflakes.HashableT[guilds.Guild], *, style: str = ...) -> str:
        """Get the URL for a guild widget.

        Parameters
        ----------
        guild : :obj:`typing.Union` [ :obj:`hikari.guilds.Guild`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the guild to form the widget.
        style : :obj:`str`
            If specified, the syle of the widget.

        Returns
        -------
        :obj:`str`
            A URL to retrieve a PNG widget for your guild.

        Note
        ----
        This does not actually make any form of request, and shouldn't be
        awaited. Thus, it doesn't have rate limits either.

        Warning
        -------
        The guild must have the widget enabled in the guild settings for this
        to be valid.
        """
        return self._session.get_guild_widget_image_url(
            guild_id=str(guild.id if isinstance(guild, snowflakes.UniqueEntity) else int(guild)), style=style
        )

    async def fetch_invite(
        self, invite: typing.Union[invites.Invite, str], *, with_counts: bool = ...
    ) -> invites.Invite:
        """Get the given invite.

        Parameters
        ----------
        invite : :obj:`typing.Union` [ :obj:`hikari.invites.Invite`, :obj:`str` ]
            The object or code of the wanted invite.
        with_counts : :bool:
            If specified, whether to attempt to count the number of
            times the invite has been used.

        Returns
        -------
        :obj:`hikari.invites.Invite`
            The requested invite object.

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.NotFoundHTTPError`
            If the invite is not found.
        """
        payload = await self._session.get_invite(invite_code=getattr(invite, "code", invite), with_counts=with_counts)
        return invites.Invite.deserialize(payload)

    async def delete_invite(self, invite: typing.Union[invites.Invite, str]) -> None:
        """Delete a given invite.

        Parameters
        ----------
        invite : :obj:`typing.Union` [ :obj:`hikari.invites.Invite`, :obj:`str` ]
            The object or ID for the invite to be deleted.

        Returns
        -------
        :obj:`None`
            Nothing, unlike what the API specifies. This is done to maintain
            consistency with other calls of a similar nature in this API wrapper.

        Raises
        ------
        :obj:`hikari.errors.NotFoundHTTPError`
            If the invite is not found.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you lack either ``MANAGE_CHANNELS`` on the channel the invite
            belongs to or ``MANAGE_GUILD`` for guild-global delete.
        """
        await self._session.delete_invite(invite_code=getattr(invite, "code", invite))

    async def fetch_user(self, user: snowflakes.HashableT[users.User]) -> users.User:
        """Get a given user.

        Parameters
        ----------
        user : :obj:`typing.Union` [ :obj:`hikari.users.User`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the user to get.

        Returns
        -------
        :obj:`hikari.users.User`
            The requested user object.

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.NotFoundHTTPError`
            If the user is not found.
        """
        payload = await self._session.get_user(
            user_id=str(user.id if isinstance(user, snowflakes.UniqueEntity) else int(user))
        )
        return users.User.deserialize(payload)

    async def fetch_my_application_info(self) -> oauth2.Application:
        """Get the current application information.

        Returns
        -------
        :obj:`hikari.oauth2.Application`
            An application info object.
        """
        payload = await self._session.get_current_application_info()
        return oauth2.Application.deserialize(payload)

    async def fetch_me(self) -> users.MyUser:
        """Get the current user that of the token given to the client.

        Returns
        -------
        :obj:`hikari.users.MyUser`
            The current user object.
        """
        payload = await self._session.get_current_user()
        return users.MyUser.deserialize(payload)

    async def update_me(
        self, *, username: str = ..., avatar_data: typing.Optional[conversions.FileLikeT] = ...,
    ) -> users.MyUser:
        """Edit the current user.

        Parameters
        ----------
        username : :obj:`str`
            If specified, the new username string.
        avatar_data : ``hikari.internal.conversions.FileLikeT``, optional
            If specified, the new avatar image data.
            If it is :obj:`None`, the avatar is removed.

        Returns
        -------
        :obj:`hikari.users.MyUser`
            The updated user object.

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If you pass username longer than the limit (``2-32``) or an invalid image.
        """
        payload = await self._session.modify_current_user(
            username=username,
            avatar=conversions.get_bytes_from_resource(avatar_data) if avatar_data is not ... else ...,
        )
        return users.MyUser.deserialize(payload)

    async def fetch_my_connections(self) -> typing.Sequence[oauth2.OwnConnection]:
        """
        Get the current user's connections.

        Note
        ----
        This endpoint can be used with both ``Bearer`` and ``Bot`` tokens but
        will usually return an empty list for bots (with there being some
        exceptions to this, like user accounts that have been converted to bots).

        Returns
        -------
        :obj:`typing.Sequence` [ :obj:`hikari.oauth2.OwnConnection` ]
            A list of connection objects.
        """
        payload = await self._session.get_current_user_connections()
        return [oauth2.OwnConnection.deserialize(connection) for connection in payload]

    def fetch_my_guilds_after(
        self,
        *,
        after: typing.Union[datetime.datetime, snowflakes.HashableT[guilds.Guild]] = 0,
        limit: typing.Optional[int] = None,
    ) -> typing.AsyncIterator[oauth2.OwnGuild]:
        """Get an async iterator of the guilds the current user is in.

        This returns the guilds created after a given guild object/ID or from
        the oldest guild.

        Parameters
        ----------
        after : :obj:`typing.Union` [ :obj:`datetime.datetime`, :obj:`hikari.guilds.Guild`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of a guild to get guilds that were created after
            it if specified, else this will start at the oldest guild.
        limit : :obj:`int`
            If specified, the maximum amount of guilds that this paginator
            should return.

        Example
        -------
        .. code-block:: python

            async for user in client.fetch_my_guilds_after(after=9876543, limit=1231):
                await client.leave_guild(guild)

        Returns
        -------
        :obj:`typing.AsyncIterator` [ :obj:`hikari.oauth2.OwnGuild` ]
            An async iterator of partial guild objects.

        Raises
        ------
        :obj:`hikari.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        """
        if isinstance(after, datetime.datetime):
            after = str(snowflakes.Snowflake.from_datetime(after))
        else:
            after = str(after.id if isinstance(after, snowflakes.UniqueEntity) else int(after))
        return self._pagination_handler(
            deserializer=oauth2.OwnGuild.deserialize,
            direction="after",
            request=self._session.get_current_user_guilds,
            reversing=False,
            start=after,
            limit=limit,
        )

    def fetch_my_guilds_before(
        self,
        *,
        before: typing.Union[datetime.datetime, snowflakes.HashableT[guilds.Guild], None] = None,
        limit: typing.Optional[int] = None,
    ) -> typing.AsyncIterator[oauth2.OwnGuild]:
        """Get an async iterator of the guilds the current user is in.

        This returns the guilds that were created before a given user object/ID
        or from the newest guild.

        Parameters
        ----------
        before : :obj:`typing.Union` [ :obj:`datetime.datetime`, :obj:`hikari.guilds.Guild`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of a guild to get guilds that were created
            before it if specified, else this will start at the newest guild.
        limit : :obj:`int`
            If specified, the maximum amount of guilds that this paginator
            should return.

        Returns
        -------
        :obj:`typing.AsyncIterator` [ :obj:`hikari.oauth2.OwnGuild` ]
            An async iterator of partial guild objects.

        Raises
        ------
        :obj:`hikari.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        """
        if isinstance(before, datetime.datetime):
            before = str(snowflakes.Snowflake.from_datetime(before))
        elif before is not None:
            before = str(before.id if isinstance(before, snowflakes.UniqueEntity) else int(before))
        return self._pagination_handler(
            deserializer=oauth2.OwnGuild.deserialize,
            direction="before",
            request=self._session.get_current_user_guilds,
            reversing=False,
            start=before,
            limit=limit,
        )

    async def leave_guild(self, guild: snowflakes.HashableT[guilds.Guild]) -> None:
        """Make the current user leave a given guild.

        Parameters
        ----------
        guild : :obj:`typing.Union` [ :obj:`hikari.guilds.Guild`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the guild to leave.

        Raises
        ------
        :obj:`hikari.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        """
        await self._session.leave_guild(
            guild_id=str(guild.id if isinstance(guild, snowflakes.UniqueEntity) else int(guild))
        )

    async def create_dm_channel(self, recipient: snowflakes.HashableT[users.User]) -> _channels.DMChannel:
        """Create a new DM channel with a given user.

        Parameters
        ----------
        recipient : :obj:`typing.Union` [ :obj:`hikari.users.User`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the user to create the new DM channel with.

        Returns
        -------
        :obj:`hikari.channels.DMChannel`
            The newly created DM channel object.

        Raises
        ------
        :obj:`hikari.errors.NotFoundHTTPError`
            If the recipient is not found.
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        """
        payload = await self._session.create_dm(
            recipient_id=str(recipient.id if isinstance(recipient, snowflakes.UniqueEntity) else int(recipient))
        )
        return _channels.DMChannel.deserialize(payload)

    async def fetch_voice_regions(self) -> typing.Sequence[voices.VoiceRegion]:
        """Get the voice regions that are available.

        Returns
        -------
        :obj:`typing.Sequence` [ :obj:`hikari.voices.VoiceRegion` ]
            A list of voice regions available

        Note
        ----
        This does not include VIP servers.
        """
        payload = await self._session.list_voice_regions()
        return [voices.VoiceRegion.deserialize(region) for region in payload]

    async def create_webhook(
        self,
        channel: snowflakes.HashableT[_channels.GuildChannel],
        name: str,
        *,
        avatar_data: conversions.FileLikeT = ...,
        reason: str = ...,
    ) -> webhooks.Webhook:
        """Create a webhook for a given channel.

        Parameters
        ----------
        channel : :obj:`typing.Union` [ :obj:`hikari.channels.GuildChannel`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the channel for webhook to be created in.
        name : :obj:`str`
            The webhook's name string.
        avatar_data : ``hikari.internal.conversions.FileLikeT``
            If specified, the avatar image data.
        reason : :obj:`str`
            If specified, the audit log reason explaining why the operation
            was performed.

        Returns
        -------
        :obj:`hikari.webhooks.Webhook`
            The newly created webhook object.

        Raises
        ------
        :obj:`hikari.errors.NotFoundHTTPError`
            If the channel is not found.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you either lack the ``MANAGE_WEBHOOKS`` permission or
            can not see the given channel.
        :obj:`hikari.errors.BadRequestHTTPError`
            If the avatar image is too big or the format is invalid.
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        """
        payload = await self._session.create_webhook(
            channel_id=str(channel.id if isinstance(channel, snowflakes.UniqueEntity) else int(channel)),
            name=name,
            avatar=conversions.get_bytes_from_resource(avatar_data) if avatar_data is not ... else ...,
            reason=reason,
        )
        return webhooks.Webhook.deserialize(payload)

    async def fetch_channel_webhooks(
        self, channel: snowflakes.HashableT[_channels.GuildChannel]
    ) -> typing.Sequence[webhooks.Webhook]:
        """Get all webhooks from a given channel.

        Parameters
        ----------
        channel : :obj:`typing.Union` [ :obj:`hikari.channels.GuildChannel`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the guild channel to get the webhooks from.

        Returns
        -------
        :obj:`typing.Sequence` [ :obj:`hikari.webhooks.Webhook` ]
            A list of webhook objects for the give channel.

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.NotFoundHTTPError`
            If the channel is not found.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you either lack the ``MANAGE_WEBHOOKS`` permission or
            can not see the given channel.
        """
        payload = await self._session.get_channel_webhooks(
            channel_id=str(channel.id if isinstance(channel, snowflakes.UniqueEntity) else int(channel))
        )
        return [webhooks.Webhook.deserialize(webhook) for webhook in payload]

    async def fetch_guild_webhooks(
        self, guild: snowflakes.HashableT[guilds.Guild]
    ) -> typing.Sequence[webhooks.Webhook]:
        """Get all webhooks for a given guild.

        Parameters
        ----------
        guild : :obj:`typing.Union` [ :obj:`hikari.guilds.Guild`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID for the guild to get the webhooks from.

        Returns
        -------
        :obj:`typing.Sequence` [ :obj:`hikari.webhooks.Webhook` ]
            A list of webhook objects for the given guild.

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you either lack the ``MANAGE_WEBHOOKS`` permission or
            aren't a member of the given guild.
        """
        payload = await self._session.get_guild_webhooks(
            guild_id=str(guild.id if isinstance(guild, snowflakes.UniqueEntity) else int(guild))
        )
        return [webhooks.Webhook.deserialize(webhook) for webhook in payload]

    async def fetch_webhook(
        self, webhook: snowflakes.HashableT[webhooks.Webhook], *, webhook_token: str = ...
    ) -> webhooks.Webhook:
        """Get a given webhook.

        Parameters
        ----------
        webhook : :obj:`typing.Union` [ :obj:`hikari.webhooks.Webhook`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the webhook to get.
        webhook_token : :obj:`str`
            If specified, the webhook token to use to get it (bypassing this
            session's provided authorization ``token``).

        Returns
        -------
        :obj:`hikari.webhooks.Webhook`
            The requested webhook object.

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.NotFoundHTTPError`
            If the webhook is not found.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you're not in the guild that owns this webhook or
            lack the ``MANAGE_WEBHOOKS`` permission.
        :obj:`hikari.errors.UnauthorizedHTTPError`
            If you pass a token that's invalid for the target webhook.
        """
        payload = await self._session.get_webhook(
            webhook_id=str(webhook.id if isinstance(webhook, snowflakes.UniqueEntity) else int(webhook)),
            webhook_token=webhook_token,
        )
        return webhooks.Webhook.deserialize(payload)

    async def update_webhook(
        self,
        webhook: snowflakes.HashableT[webhooks.Webhook],
        *,
        webhook_token: str = ...,
        name: str = ...,
        avatar_data: typing.Optional[conversions.FileLikeT] = ...,
        channel: snowflakes.HashableT[_channels.GuildChannel] = ...,
        reason: str = ...,
    ) -> webhooks.Webhook:
        """Edit a given webhook.

        Parameters
        ----------
        webhook : :obj:`typing.Union` [ :obj:`hikari.webhooks.Webhook`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the webhook to edit.
        webhook_token : :obj:`str`
            If specified, the webhook token to use to modify it (bypassing this
            session's provided authorization ``token``).
        name : :obj:`str`
            If specified, the new name string.
        avatar_data : ``hikari.internal.conversions.FileLikeT``, optional
            If specified, the new avatar image file object. If :obj:`None`, then
            it is removed.
        channel : :obj:`typing.Union` [ :obj:`hikari.channels.GuildChannel`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            If specified, the object or ID of the new channel the given
            webhook should be moved to.
        reason : :obj:`str`
            If specified, the audit log reason explaining why the operation
            was performed.

        Returns
        -------
        :obj:`hikari.webhooks.Webhook`
            The updated webhook object.

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.NotFoundHTTPError`
            If either the webhook or the channel aren't found.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you either lack the ``MANAGE_WEBHOOKS`` permission or
            aren't a member of the guild this webhook belongs to.
        :obj:`hikari.errors.UnauthorizedHTTPError`
            If you pass a token that's invalid for the target webhook.
        """
        payload = await self._session.modify_webhook(
            webhook_id=str(webhook.id if isinstance(webhook, snowflakes.UniqueEntity) else int(webhook)),
            webhook_token=webhook_token,
            name=name,
            avatar=(
                conversions.get_bytes_from_resource(avatar_data)
                if avatar_data and avatar_data is not ...
                else avatar_data
            ),
            channel_id=(
                str(channel.id if isinstance(channel, snowflakes.UniqueEntity) else int(channel))
                if channel and channel is not ...
                else channel
            ),
            reason=reason,
        )
        return webhooks.Webhook.deserialize(payload)

    async def delete_webhook(
        self, webhook: snowflakes.HashableT[webhooks.Webhook], *, webhook_token: str = ...
    ) -> None:
        """Delete a given webhook.

        Parameters
        ----------
        webhook : :obj:`typing.Union` [ :obj:`hikari.webhooks.Webhook`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the webhook to delete
        webhook_token : :obj:`str`
            If specified, the webhook token to use to delete it (bypassing this
            session's provided authorization ``token``).

        Raises
        ------
        :obj:`hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.NotFoundHTTPError`
            If the webhook is not found.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you either lack the ``MANAGE_WEBHOOKS`` permission or
            aren't a member of the guild this webhook belongs to.
        :obj:`hikari.errors.UnauthorizedHTTPError`
                If you pass a token that's invalid for the target webhook.
        """
        await self._session.delete_webhook(
            webhook_id=str(webhook.id if isinstance(webhook, snowflakes.UniqueEntity) else int(webhook)),
            webhook_token=webhook_token,
        )

    async def execute_webhook(
        self,
        webhook: snowflakes.HashableT[webhooks.Webhook],
        webhook_token: str,
        *,
        content: str = ...,
        username: str = ...,
        avatar_url: str = ...,
        tts: bool = ...,
        wait: bool = False,
        file: media.IO = ...,
        embeds: typing.Sequence[_embeds.Embed] = ...,
        mentions_everyone: bool = True,
        user_mentions: typing.Union[typing.Collection[snowflakes.HashableT[users.User]], bool] = True,
        role_mentions: typing.Union[typing.Collection[snowflakes.HashableT[guilds.GuildRole]], bool] = True,
    ) -> typing.Optional[_messages.Message]:
        """Execute a webhook to create a message.

        Parameters
        ----------
        webhook : :obj:`typing.Union` [ :obj:`hikari.webhooks.Webhook`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ]
            The object or ID of the webhook to execute.
        webhook_token : :obj:`str`
            The token of the webhook to execute.
        content : :obj:`str`
            If specified, the message content to send with the message.
        username : :obj:`str`
            If specified, the username to override the webhook's username
            for this request.
        avatar_url : :obj:`str`
            If specified, the url of an image to override the webhook's
            avatar with for this request.
        tts : :obj:`bool`
            If specified, whether the message will be sent as a TTS message.
        wait : :obj:`bool`
            If specified, whether this request should wait for the webhook
            to be executed and return the resultant message object.
        file : ``hikari.media.IO``
            If specified, this is a file object to send along with the webhook
            as defined in :mod:`hikari.media`.
        embeds : :obj:`typing.Sequence` [ :obj:`hikari.embeds.Embed` ]
            If specified, a sequence of ``1`` to ``10`` embed objects to send
            with the embed.
        mentions_everyone : :obj:`bool`
            Whether ``@everyone`` and ``@here`` mentions should be resolved by
            discord and lead to actual pings, defaults to :obj:`True`.
        user_mentions : :obj:`typing.Union` [ :obj:`typing.Collection` [ :obj:`typing.Union` [ :obj:`hikari.users.User`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ], :obj:`bool` ]
            Either an array of user objects/IDs to allow mentions for,
            :obj:`True` to allow all user mentions or :obj:`False` to block all
            user mentions from resolving, defaults to :obj:`True`.
        role_mentions : :obj:`typing.Union` [ :obj:`typing.Collection` [ :obj:`typing.Union` [ :obj:`hikari.guilds.GuildRole`, :obj:`hikari.snowflakes.Snowflake`, :obj:`int` ] ], :obj:`bool` ]
            Either an array of guild role objects/IDs to allow mentions for,
            :obj:`True` to allow all role mentions or :obj:`False` to block all
            role mentions from resolving, defaults to :obj:`True`.

        Returns
        -------
        :obj:`hikari.messages.Message`, optional
            The created message object, if ``wait`` is :obj:`True`, else
            :obj:`None`.

        Raises
        ------
        :obj:`hikari.errors.NotFoundHTTPError`
            If the channel ID or webhook ID is not found.
        :obj:`hikari.errors.BadRequestHTTPError`
            This can be raised if the file is too large; if the embed exceeds
            the defined limits; if the message content is specified only and
            empty or greater than ``2000`` characters; if neither content, file
            or embeds are specified.
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`hikari.errors.ForbiddenHTTPError`
            If you lack permissions to send to this channel.
        :obj:`hikari.errors.UnauthorizedHTTPError`
            If you pass a token that's invalid for the target webhook.
        """
        payload = await self._session.execute_webhook(
            webhook_id=str(webhook.id if isinstance(webhook, snowflakes.UniqueEntity) else int(webhook)),
            webhook_token=webhook_token,
            content=content,
            username=username,
            avatar_url=avatar_url,
            tts=tts,
            wait=wait,
            file=await media.safe_read_file(file) if file is not ... else ...,
            embeds=[embed.serialize() for embed in embeds] if embeds is not ... else ...,
            allowed_mentions=self._generate_allowed_mentions(
                mentions_everyone=mentions_everyone, user_mentions=user_mentions, role_mentions=role_mentions
            ),
        )
        if wait is True:
            return _messages.Message.deserialize(payload)
        return None

    def safe_webhook_execute(
        self,
        webhook: snowflakes.HashableT[webhooks.Webhook],
        webhook_token: str,
        *,
        content: str = ...,
        username: str = ...,
        avatar_url: str = ...,
        tts: bool = ...,
        wait: bool = False,
        file: media.IO = ...,
        embeds: typing.Sequence[_embeds.Embed] = ...,
        mentions_everyone: bool = False,
        user_mentions: typing.Union[typing.Collection[snowflakes.HashableT[users.User]], bool] = False,
        role_mentions: typing.Union[typing.Collection[snowflakes.HashableT[guilds.GuildRole]], bool] = False,
    ) -> typing.Coroutine[typing.Any, typing.Any, typing.Optional[_messages.Message]]:
        """Execute a webhook to create a message with mention safety.

        This endpoint has the same signature as :attr:`execute_webhook` with
        the only difference being that ``mentions_everyone``,
        ``user_mentions`` and ``role_mentions`` default to :obj:`False`.
        """
        return self.execute_webhook(
            webhook=webhook,
            webhook_token=webhook_token,
            content=content,
            username=username,
            avatar_url=avatar_url,
            tts=tts,
            wait=wait,
            file=file,
            embeds=embeds,
            mentions_everyone=mentions_everyone,
            user_mentions=user_mentions,
            role_mentions=role_mentions,
        )
