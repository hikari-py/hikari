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
"""The logic for handling requests to channel endpoints."""

__all__ = ["RESTChannelComponent"]

import abc
import asyncio
import datetime
import typing

from hikari import bases
from hikari import channels as _channels
from hikari import embeds as _embeds
from hikari import guilds
from hikari import invites
from hikari import media
from hikari import messages as _messages
from hikari import permissions as _permissions
from hikari import users
from hikari import webhooks
from hikari.clients.rest_clients import base
from hikari.internal import allowed_mentions
from hikari.internal import assertions
from hikari.internal import conversions
from hikari.internal import more_typing
from hikari.internal import pagination


class RESTChannelComponent(base.BaseRESTComponent, abc.ABC):  # pylint: disable=W0223
    """The REST client component for handling requests to channel endpoints."""

    async def fetch_channel(self, channel: bases.Hashable[_channels.Channel]) -> _channels.Channel:
        """Get an up to date channel object from a given channel object or ID.

        Parameters
        ----------
        channel : :obj:`~typing.Union` [ :obj:`~hikari.channels.Channel`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object ID of the channel to look up.

        Returns
        -------
        :obj:`~hikari.channels.Channel`
            The channel object that has been found.

        Raises
        ------
        :obj:`~hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you don't have access to the channel.
        :obj:`~hikari.errors.NotFoundHTTPError`
            If the channel does not exist.
        """
        payload = await self._session.get_channel(
            channel_id=str(channel.id if isinstance(channel, bases.UniqueEntity) else int(channel))
        )
        return _channels.deserialize_channel(payload)

    async def update_channel(
        self,
        channel: bases.Hashable[_channels.Channel],
        *,
        name: str = ...,
        position: int = ...,
        topic: str = ...,
        nsfw: bool = ...,
        bitrate: int = ...,
        user_limit: int = ...,
        rate_limit_per_user: typing.Union[int, datetime.timedelta] = ...,
        permission_overwrites: typing.Sequence[_channels.PermissionOverwrite] = ...,
        parent_category: typing.Optional[bases.Hashable[_channels.GuildCategory]] = ...,
        reason: str = ...,
    ) -> _channels.Channel:
        """Update one or more aspects of a given channel ID.

        Parameters
        ----------
        channel : :obj:`~typing.Union` [ :obj:`~hikari.channels.Channel`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The channel ID to update.
        name : :obj:`~str`
            If specified, the new name for the channel. This must be
            inclusively between ``1`` and ``100`` characters in length.
        position : :obj:`~int`
            If specified, the position to change the channel to.
        topic : :obj:`~str`
            If specified, the topic to set. This is only applicable to
            text channels. This must be inclusively between ``0`` and ``1024``
            characters in length.
        nsfw : :obj:`~bool`
            Mark the channel as being not safe for work (NSFW) if :obj:`~True`.
            If :obj:`~False` or unspecified, then the channel is not marked as
            NSFW. Will have no visible effect for non-text guild channels.
        rate_limit_per_user : :obj:`~typing.Union` [ :obj:`~int`, :obj:`~datetime.timedelta` ]
            If specified, the time delta of seconds  the user has to wait
            before sending another message. This will not apply to bots, or to
            members with ``MANAGE_MESSAGES`` or ``MANAGE_CHANNEL`` permissions.
            This must be inclusively between ``0`` and ``21600`` seconds.
        bitrate : :obj:`~int`
            If specified, the bitrate in bits per second allowable for the
            channel. This only applies to voice channels and must be inclusively
            between ``8000`` and ``96000`` for normal servers or ``8000`` and
            ``128000`` for VIP servers.
        user_limit : :obj:`~int`
            If specified, the new max number of users to allow in a voice
            channel. This must be between ``0`` and ``99`` inclusive, where
            ``0`` implies no limit.
        permission_overwrites : :obj:`~typing.Sequence` [ :obj:`~hikari.channels.PermissionOverwrite` ]
            If specified, the new list of permission overwrites that are
            category specific to replace the existing overwrites with.
        parent_category : :obj:`~typing.Union` [ :obj:`~hikari.channels.Channel`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ], optional
            If specified, the new parent category ID to set for the channel,
            pass :obj:`~None` to unset.
        reason : :obj:`~str`
            If specified, the audit log reason explaining why the operation
            was performed.

        Returns
        -------
        :obj:`~hikari.channels.Channel`
            The channel object that has been modified.

        Raises
        ------
        :obj:`~hikari.errors.NotFoundHTTPError`
            If the channel does not exist.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you lack the permission to make the change.
        :obj:`~hikari.errors.BadRequestHTTPError`
            If you provide incorrect options for the corresponding channel type
            (e.g. a ``bitrate`` for a text channel).
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        """
        payload = await self._session.modify_channel(
            channel_id=str(channel.id if isinstance(channel, bases.UniqueEntity) else int(channel)),
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
                str(parent_category.id if isinstance(parent_category, bases.UniqueEntity) else int(parent_category))
                if parent_category is not ... and parent_category is not None
                else parent_category
            ),
            reason=reason,
        )
        return _channels.deserialize_channel(payload)

    async def delete_channel(self, channel: bases.Hashable[_channels.Channel]) -> None:
        """Delete the given channel ID, or if it is a DM, close it.

        Parameters
        ----------
        channel : :obj:`~typing.Union` [ :obj:`~hikari.channels.Channel`, :obj:`~hikari.entities.Snowflake` :obj:`~str` ]
            The object or ID of the channel to delete.

        Returns
        -------
        :obj:`~None`
            Nothing, unlike what the API specifies. This is done to maintain
            consistency with other calls of a similar nature in this API
            wrapper.

        Raises
        ------
        :obj:`~hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`~hikari.errors.NotFoundHTTPError`
            If the channel does not exist.
        :obj:`~hikari.errors.ForbiddenHTTPError`
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
            channel_id=str(channel.id if isinstance(channel, bases.UniqueEntity) else int(channel))
        )

    def fetch_messages_after(
        self,
        channel: bases.Hashable[_channels.Channel],
        *,
        after: typing.Union[datetime.datetime, bases.Hashable[_messages.Message]] = 0,
        limit: typing.Optional[int] = None,
    ) -> typing.AsyncIterator[_messages.Message]:
        """Return an async iterator that retrieves a channel's message history.

        This will return the message created after a given message object/ID or
        from the first message in the channel.

        Parameters
        ----------
        channel : :obj:`~typing.Union` [ :obj:`~hikari.channels.Channel`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The ID of the channel to retrieve the messages from.
        limit : :obj:`~int`
            If specified, the maximum number of how many messages this iterator
            should return.
        after : :obj:`~typing.Union` [ :obj:`~datetime.datetime`, :obj:`~hikari.channels.Channel`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
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
        :obj:`~typing.AsyncIterator` [ :obj:`~hikari.messages.Message` ]
            An async iterator that retrieves the channel's message objects.

        Raises
        ------
        :obj:`~hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you lack permission to read the channel.
        :obj:`~hikari.errors.NotFoundHTTPError`
            If the channel is not found, or the message
            provided for one of the filter arguments is not found.

        Note
        ----
        If you are missing the ``VIEW_CHANNEL`` permission, you will receive a
        :obj:`~hikari.errors.ForbiddenHTTPError`. If you are instead missing
        the ``READ_MESSAGE_HISTORY`` permission, you will always receive
        zero results, and thus an empty list will be returned instead.
        """
        if isinstance(after, datetime.datetime):
            after = str(bases.Snowflake.from_datetime(after))
        else:
            after = str(after.id if isinstance(after, bases.UniqueEntity) else int(after))
        return pagination.pagination_handler(
            channel_id=str(channel.id if isinstance(channel, bases.UniqueEntity) else int(channel)),
            deserializer=_messages.Message.deserialize,
            direction="after",
            start=after,
            request=self._session.get_channel_messages,
            reversing=True,  # This is the only known endpoint where reversing is needed.
            limit=limit,
        )

    def fetch_messages_before(
        self,
        channel: bases.Hashable[_channels.Channel],
        *,
        before: typing.Union[datetime.datetime, bases.Hashable[_messages.Message], None] = None,
        limit: typing.Optional[int] = None,
    ) -> typing.AsyncIterator[_messages.Message]:
        """Return an async iterator that retrieves a channel's message history.

        This returns the message created after a given message object/ID or
        from the first message in the channel.

        Parameters
        ----------
        channel : :obj:`~typing.Union` [ :obj:`~hikari.channels.Channel`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The ID of the channel to retrieve the messages from.
        limit : :obj:`~int`
            If specified, the maximum number of how many messages this iterator
            should return.
        before : :obj:`~typing.Union` [ :obj:`~datetime.datetime`, :obj:`~hikari.channels.Channel`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
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
        :obj:`~typing.AsyncIterator` [ :obj:`~hikari.messages.Message` ]
            An async iterator that retrieves the channel's message objects.

        Raises
        ------
        :obj:`~hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you lack permission to read the channel.
        :obj:`~hikari.errors.NotFoundHTTPError`
            If the channel is not found, or the message
            provided for one of the filter arguments is not found.

        Note
        ----
        If you are missing the ``VIEW_CHANNEL`` permission, you will receive a
        :obj:`~hikari.errors.ForbiddenHTTPError`. If you are instead missing
        the ``READ_MESSAGE_HISTORY`` permission, you will always receive
        zero results, and thus an empty list will be returned instead.
        """
        if isinstance(before, datetime.datetime):
            before = str(bases.Snowflake.from_datetime(before))
        elif before is not None:
            before = str(before.id if isinstance(before, bases.UniqueEntity) else int(before))
        return pagination.pagination_handler(
            channel_id=str(channel.id if isinstance(channel, bases.UniqueEntity) else int(channel)),
            deserializer=_messages.Message.deserialize,
            direction="before",
            start=before,
            request=self._session.get_channel_messages,
            reversing=False,
            limit=limit,
        )

    async def fetch_messages_around(
        self,
        channel: bases.Hashable[_channels.Channel],
        around: typing.Union[datetime.datetime, bases.Hashable[_messages.Message]],
        *,
        limit: int = ...,
    ) -> typing.AsyncIterator[_messages.Message]:
        """Return an async iterator that retrieves up to 100 messages.

        This will return messages in order from newest to oldest, is based
        around the creation time of the supplied message object/ID and will
        include the given message if it still exists.

        Parameters
        ----------
        channel : :obj:`~typing.Union` [ :obj:`~hikari.channels.Channel`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The ID of the channel to retrieve the messages from.
        around : :obj:`~typing.Union` [ :obj:`~datetime.datetime`, :obj:`~hikari.channels.Channel`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the message to get messages that were sent
            AROUND it in the provided channel, unlike ``before`` and ``after``,
            this argument is required and the provided message will also be
            returned if it still exists.
        limit : :obj:`~int`
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
        :obj:`~typing.AsyncIterator` [ :obj:`~hikari.messages.Message` ]
            An async iterator that retrieves the found message objects.

        Raises
        ------
        :obj:`~hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you lack permission to read the channel.
        :obj:`~hikari.errors.NotFoundHTTPError`
            If the channel is not found, or the message
            provided for one of the filter arguments is not found.

        Note
        ----
        If you are missing the ``VIEW_CHANNEL`` permission, you will receive a
        :obj:`~hikari.errors.ForbiddenHTTPError`. If you are instead missing
        the ``READ_MESSAGE_HISTORY`` permission, you will always receive
        zero results, and thus an empty list will be returned instead.
        """
        if isinstance(around, datetime.datetime):
            around = str(bases.Snowflake.from_datetime(around))
        else:
            around = str(around.id if isinstance(around, bases.UniqueEntity) else int(around))
        for payload in await self._session.get_channel_messages(
            channel_id=str(channel.id if isinstance(channel, bases.UniqueEntity) else int(channel)),
            limit=limit,
            around=around,
        ):
            yield _messages.Message.deserialize(payload)

    async def fetch_message(
        self, channel: bases.Hashable[_channels.Channel], message: bases.Hashable[_messages.Message],
    ) -> _messages.Message:
        """Get a message from known channel that we can access.

        Parameters
        ----------
        channel : :obj:`~typing.Union` [ :obj:`~hikari.channels.Channel`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the channel to get the message from.
        message : :obj:`~typing.Union` [ :obj:`~hikari.messages.Message`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the message to retrieve.

        Returns
        -------
        :obj:`~hikari.messages.Message`
            The found message object.

        Note
        ----
        This requires the ``READ_MESSAGE_HISTORY`` permission.

        Raises
        ------
        :obj:`~hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you lack permission to see the message.
        :obj:`~hikari.errors.NotFoundHTTPError`
            If the channel or message is not found.
        """
        payload = await self._session.get_channel_message(
            channel_id=str(channel.id if isinstance(channel, bases.UniqueEntity) else int(channel)),
            message_id=str(message.id if isinstance(message, bases.UniqueEntity) else int(message)),
        )
        return _messages.Message.deserialize(payload)

    async def create_message(
        self,
        channel: bases.Hashable[_channels.Channel],
        *,
        content: str = ...,
        nonce: str = ...,
        tts: bool = ...,
        files: typing.Collection[media.IO] = ...,
        embed: _embeds.Embed = ...,
        mentions_everyone: bool = True,
        user_mentions: typing.Union[typing.Collection[bases.Hashable[users.User]], bool] = True,
        role_mentions: typing.Union[typing.Collection[bases.Hashable[guilds.GuildRole]], bool] = True,
    ) -> _messages.Message:
        """Create a message in the given channel.

        Parameters
        ----------
        channel : :obj:`~typing.Union` [ :obj:`~hikari.channels.Channel`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The channel or ID of the channel to send to.
        content : :obj:`~str`
            If specified, the message content to send with the message.
        nonce : :obj:`~str`
            If specified, an optional ID to send for opportunistic message
            creation. This doesn't serve any real purpose for general use,
            and can usually be ignored.
        tts : :obj:`~bool`
            If specified, whether the message will be sent as a TTS message.
        files : :obj:`~typing.Collection` [ ``hikari.media.IO`` ]
            If specified, this should be a list of inclusively between ``1`` and
            ``5`` IO like media objects, as defined in :mod:`hikari.media`.
        embed : :obj:`~hikari.embeds.Embed`
            If specified, the embed object to send with the message.
        mentions_everyone : :obj:`~bool`
            Whether ``@everyone`` and ``@here`` mentions should be resolved by
            discord and lead to actual pings, defaults to :obj:`~True`.
        user_mentions : :obj:`~typing.Union` [ :obj:`~typing.Collection` [ :obj:`~typing.Union` [ :obj:`~hikari.users.User`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ], :obj:`~bool` ]
            Either an array of user objects/IDs to allow mentions for,
            :obj:`~True` to allow all user mentions or :obj:`~False` to block all
            user mentions from resolving, defaults to :obj:`~True`.
        role_mentions : :obj:`~typing.Union` [ :obj:`~typing.Collection` [ :obj:`~typing.Union` [ :obj:`~hikari.guilds.GuildRole`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ] ], :obj:`~bool` ]
            Either an array of guild role objects/IDs to allow mentions for,
            :obj:`~True` to allow all role mentions or :obj:`~False` to block all
            role mentions from resolving, defaults to :obj:`~True`.

        Returns
        -------
        :obj:`~hikari.messages.Message`
            The created message object.

        Raises
        ------
        :obj:`~hikari.errors.NotFoundHTTPError`
            If the channel is not found.
        :obj:`~hikari.errors.BadRequestHTTPError`
            This can be raised if the file is too large; if the embed exceeds
            the defined limits; if the message content is specified only and
            empty or greater than ``2000`` characters; if neither content, files
            or embed are specified.
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you lack permissions to send to this channel.
        :obj:`~ValueError`
            If more than 100 unique objects/entities are passed for
            ``role_mentions`` or ``user_mentions``.
        """
        payload = await self._session.create_message(
            channel_id=str(channel.id if isinstance(channel, bases.UniqueEntity) else int(channel)),
            content=content,
            nonce=nonce,
            tts=tts,
            files=await asyncio.gather(*(media.safe_read_file(file) for file in files)) if files is not ... else ...,
            embed=embed.serialize() if embed is not ... else ...,
            allowed_mentions=allowed_mentions.generate_allowed_mentions(
                mentions_everyone=mentions_everyone, user_mentions=user_mentions, role_mentions=role_mentions
            ),
        )
        return _messages.Message.deserialize(payload)

    def safe_create_message(
        self,
        channel: bases.Hashable[_channels.Channel],
        *,
        content: str = ...,
        nonce: str = ...,
        tts: bool = ...,
        files: typing.Collection[media.IO] = ...,
        embed: _embeds.Embed = ...,
        mentions_everyone: bool = False,
        user_mentions: typing.Union[typing.Collection[bases.Hashable[users.User]], bool] = False,
        role_mentions: typing.Union[typing.Collection[bases.Hashable[guilds.GuildRole]], bool] = False,
    ) -> more_typing.Coroutine[_messages.Message]:
        """Create a message in the given channel with mention safety.

        This endpoint has the same signature as :attr:`create_message` with
        the only difference being that ``mentions_everyone``,
        ``user_mentions`` and ``role_mentions`` default to :obj:`~False`.
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

    async def update_message(
        self,
        message: bases.Hashable[_messages.Message],
        channel: bases.Hashable[_channels.Channel],
        *,
        content: typing.Optional[str] = ...,
        embed: typing.Optional[_embeds.Embed] = ...,
        flags: int = ...,
        mentions_everyone: bool = True,
        user_mentions: typing.Union[typing.Collection[bases.Hashable[users.User]], bool] = True,
        role_mentions: typing.Union[typing.Collection[bases.Hashable[guilds.GuildRole]], bool] = True,
    ) -> _messages.Message:
        """Update the given message.

        Parameters
        ----------
        channel : :obj:`~typing.Union` [ :obj:`~hikari.channels.Channel`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the channel to get the message from.
        message : :obj:`~typing.Union` [ :obj:`~hikari.messages.Message`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the message to edit.
        content : :obj:`~str`, optional
            If specified, the string content to replace with in the message.
            If :obj:`~None`, the content will be removed from the message.
        embed : :obj:`~hikari.embeds.Embed`, optional
            If specified, the embed to replace with in the message.
            If :obj:`~None`, the embed will be removed from the message.
        flags : :obj:`~hikari.messages.MessageFlag`
            If specified, the new flags for this message, while a raw int may
            be passed for this, this can lead to unexpected behaviour if it's
            outside the range of the MessageFlag int flag.
        mentions_everyone : :obj:`~bool`
            Whether ``@everyone`` and ``@here`` mentions should be resolved by
            discord and lead to actual pings, defaults to :obj:`~True`.
        user_mentions : :obj:`~typing.Union` [ :obj:`~typing.Collection` [ :obj:`~typing.Union` [ :obj:`~hikari.users.User`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ], :obj:`~bool` ]
            Either an array of user objects/IDs to allow mentions for,
            :obj:`~True` to allow all user mentions or :obj:`~False` to block all
            user mentions from resolving, defaults to :obj:`~True`.
        role_mentions : :obj:`~typing.Union` [ :obj:`~typing.Collection` [ :obj:`~typing.Union` [ :obj:`~hikari.guilds.GuildRole`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ] ], :obj:`~bool` ]
            Either an array of guild role objects/IDs to allow mentions for,
            :obj:`~True` to allow all role mentions or :obj:`~False` to block all
            role mentions from resolving, defaults to :obj:`~True`.

        Returns
        -------
        :obj:`~hikari.messages.Message`
            The edited message object.

        Raises
        ------
        :obj:`~hikari.errors.NotFoundHTTPError`
            If the channel or message is not found.
        :obj:`~hikari.errors.BadRequestHTTPError`
            This can be raised if the embed exceeds the defined limits;
            if the message content is specified only and empty or greater
            than ``2000`` characters; if neither content, file or embed
            are specified.
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you try to edit ``content`` or ``embed`` or ``allowed_mentions`
            on a message you did not author.
            If you try to edit the flags on a message you did not author without
            the ``MANAGE_MESSAGES`` permission.
        :obj:`~ValueError`
            If more than 100 unique objects/entities are passed for
            ``role_mentions`` or ``user_mentions``.
        """
        payload = await self._session.edit_message(
            channel_id=str(channel.id if isinstance(channel, bases.UniqueEntity) else int(channel)),
            message_id=str(message.id if isinstance(message, bases.UniqueEntity) else int(message)),
            content=content,
            embed=embed.serialize() if embed is not ... and embed is not None else embed,
            flags=flags,
            allowed_mentions=allowed_mentions.generate_allowed_mentions(
                mentions_everyone=mentions_everyone, user_mentions=user_mentions, role_mentions=role_mentions,
            ),
        )
        return _messages.Message.deserialize(payload)

    def safe_update_message(
        self,
        message: bases.Hashable[_messages.Message],
        channel: bases.Hashable[_channels.Channel],
        *,
        content: typing.Optional[str] = ...,
        embed: typing.Optional[_embeds.Embed] = ...,
        flags: int = ...,
        mentions_everyone: bool = False,
        user_mentions: typing.Union[typing.Collection[bases.Hashable[users.User]], bool] = False,
        role_mentions: typing.Union[typing.Collection[bases.Hashable[guilds.GuildRole]], bool] = False,
    ) -> typing.Coroutine[typing.Any, typing.Any, _messages.Message]:
        """Update a message in the given channel with mention safety.

        This endpoint has the same signature as :attr:`update_message` with
        the only difference being that ``mentions_everyone``,
        ``user_mentions`` and ``role_mentions`` default to :obj:`~False`.
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
        channel: bases.Hashable[_channels.Channel],
        message: bases.Hashable[_messages.Message],
        *additional_messages: bases.Hashable[_messages.Message],
    ) -> None:
        """Delete a message in a given channel.

        Parameters
        ----------
        channel : :obj:`~typing.Union` [ :obj:`~hikari.channels.Channel`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the channel to get the message from.
        message : :obj:`~typing.Union` [ :obj:`~hikari.messages.Message`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the message to delete.
        *additional_messages : :obj:`~typing.Union` [ :obj:`~hikari.messages.Message`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            Objects and/or IDs of additional messages to delete in the same
            channel, in total you can delete up to 100 messages in a request.

        Raises
        ------
        :obj:`~hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you did not author the message and are in a DM, or if you did
            not author the message and lack the ``MANAGE_MESSAGES``
            permission in a guild channel.
        :obj:`~hikari.errors.NotFoundHTTPError`
            If the channel or message is not found.
        :obj:`~ValueError`
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
                    str(m.id if isinstance(m, bases.UniqueEntity) else int(m)) for m in (message, *additional_messages)
                )
            )
            assertions.assert_that(
                len(messages) <= 100, "Only up to 100 messages can be bulk deleted in a single request."
            )

            if len(messages) > 1:
                await self._session.bulk_delete_messages(
                    channel_id=str(channel.id if isinstance(channel, bases.UniqueEntity) else int(channel)),
                    messages=messages,
                )
                return None

        await self._session.delete_message(
            channel_id=str(channel.id if isinstance(channel, bases.UniqueEntity) else int(channel)),
            message_id=str(message.id if isinstance(message, bases.UniqueEntity) else int(message)),
        )

    async def update_channel_overwrite(
        self,
        channel: bases.Hashable[_messages.Message],
        overwrite: typing.Union[_channels.PermissionOverwrite, users.User, guilds.GuildRole, bases.Snowflake, int],
        target_type: typing.Union[_channels.PermissionOverwriteType, str],
        *,
        allow: typing.Union[_permissions.Permission, int] = ...,
        deny: typing.Union[_permissions.Permission, int] = ...,
        reason: str = ...,
    ) -> None:
        """Edit permissions for a given channel.

        Parameters
        ----------
        channel : :obj:`~typing.Union` [ :obj:`~hikari.messages.Message`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the channel to edit permissions for.
        overwrite : :obj:`~typing.Union` [ :obj:`~hikari.channels.PermissionOverwrite`, :obj:`~hikari.guilds.GuildRole`, :obj:`~hikari.users.User`, :obj:`~hikari.entities.Snowflake` , :obj:`~int` ]
            The object or ID of the target member or role to  edit/create the
            overwrite for.
        target_type : :obj:`~typing.Union` [ :obj:`~hikari.channels.PermissionOverwriteType`, :obj:`~int` ]
            The type of overwrite, passing a raw string that's outside of the
            enum's range for this may lead to unexpected behaviour.
        allow : :obj:`~typing.Union` [ :obj:`~hikari.permissions.Permission`, :obj:`~int` ]
            If specified, the value of all permissions to set to be allowed,
            passing a raw integer for this may lead to unexpected behaviour.
        deny : :obj:`~typing.Union` [ :obj:`~hikari.permissions.Permission`, :obj:`~int` ]
            If specified, the value of all permissions to set to be denied,
            passing a raw integer for this may lead to unexpected behaviour.
        reason : :obj:`~str`
            If specified, the audit log reason explaining why the operation
            was performed.

        Raises
        ------
        :obj:`~hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`~hikari.errors.NotFoundHTTPError`
            If the target channel or overwrite doesn't exist.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you lack permission to do this.
        """
        await self._session.edit_channel_permissions(
            channel_id=str(channel.id if isinstance(channel, bases.UniqueEntity) else int(channel)),
            overwrite_id=str(overwrite.id if isinstance(overwrite, bases.UniqueEntity) else int(overwrite)),
            type_=target_type,
            allow=allow,
            deny=deny,
            reason=reason,
        )

    async def fetch_invites_for_channel(
        self, channel: bases.Hashable[_channels.Channel]
    ) -> typing.Sequence[invites.InviteWithMetadata]:
        """Get invites for a given channel.

        Parameters
        ----------
        channel : :obj:`~typing.Union` [ :obj:`~hikari.channels.Channel`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the channel to get invites for.

        Returns
        -------
        :obj:`~typing.Sequence` [ :obj:`~hikari.invites.InviteWithMetadata` ]
            A list of invite objects.

        Raises
        ------
        :obj:`~hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you lack the ``MANAGE_CHANNELS`` permission.
        :obj:`~hikari.errors.NotFoundHTTPError`
            If the channel does not exist.
        """
        payload = await self._session.get_channel_invites(
            channel_id=str(channel.id if isinstance(channel, bases.UniqueEntity) else int(channel))
        )
        return [invites.InviteWithMetadata.deserialize(invite) for invite in payload]

    async def create_invite_for_channel(
        self,
        channel: bases.Hashable[_channels.Channel],
        *,
        max_age: typing.Union[int, datetime.timedelta] = ...,
        max_uses: int = ...,
        temporary: bool = ...,
        unique: bool = ...,
        target_user: bases.Hashable[users.User] = ...,
        target_user_type: typing.Union[invites.TargetUserType, int] = ...,
        reason: str = ...,
    ) -> invites.InviteWithMetadata:
        """Create a new invite for the given channel.

        Parameters
        ----------
        channel : :obj:`~typing.Union` [ :obj:`~datetime.timedelta`, :obj:`~str` ]
            The object or ID of the channel to create the invite for.
        max_age : :obj:`~int`
            If specified, the seconds time delta for the max age of the invite,
            defaults to ``86400`` seconds (``24`` hours).
            Set to ``0`` seconds to never expire.
        max_uses : :obj:`~int`
            If specified, the max number of uses this invite can have, or ``0``
            for unlimited (as per the default).
        temporary : :obj:`~bool`
            If specified, whether to grant temporary membership, meaning the
            user is kicked when their session ends unless they are given a role.
        unique : :obj:`~bool`
            If specified, whether to try to reuse a similar invite.
        target_user : :obj:`~typing.Union` [ :obj:`~hikari.users.User`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            If specified, the object or ID of the user this invite should
            target.
        target_user_type : :obj:`~typing.Union` [ :obj:`~hikari.invites.TargetUserType`, :obj:`~int` ]
            If specified, the type of target for this invite, passing a raw
            integer for this may lead to unexpected results.
        reason : :obj:`~str`
            If specified, the audit log reason explaining why the operation
            was performed.

        Returns
        -------
        :obj:`~hikari.invites.InviteWithMetadata`
            The created invite object.

        Raises
        ------
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you lack the ``CREATE_INSTANT_MESSAGES`` permission.
        :obj:`~hikari.errors.NotFoundHTTPError`
            If the channel does not exist.
        :obj:`~hikari.errors.BadRequestHTTPError`
            If the arguments provided are not valid (e.g. negative age, etc).
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        """
        payload = await self._session.create_channel_invite(
            channel_id=str(channel.id if isinstance(channel, bases.UniqueEntity) else int(channel)),
            max_age=int(max_age.total_seconds()) if isinstance(max_age, datetime.timedelta) else max_age,
            max_uses=max_uses,
            temporary=temporary,
            unique=unique,
            target_user=(
                str(target_user.id if isinstance(target_user, bases.UniqueEntity) else int(target_user))
                if target_user is not ...
                else ...
            ),
            target_user_type=target_user_type,
            reason=reason,
        )
        return invites.InviteWithMetadata.deserialize(payload)

    async def delete_channel_overwrite(
        self,
        channel: bases.Hashable[_channels.Channel],
        overwrite: typing.Union[_channels.PermissionOverwrite, guilds.GuildRole, users.User, bases.Snowflake, int],
    ) -> None:
        """Delete a channel permission overwrite for a user or a role.

        Parameters
        ----------
        channel : :obj:`~typing.Union` [ :obj:`~hikari.channels.Channel`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the channel to delete the overwrite from.
        overwrite : :obj:`~typing.Union` [ :obj:`~hikari.channels.PermissionOverwrite`, :obj:`~hikari.guilds.GuildRole`, :obj:`~hikari.users.User`, :obj:`~hikari.entities.Snowflake`, :obj:int ]
            The ID of the entity this overwrite targets.

        Raises
        ------
        :obj:`~hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`~hikari.errors.NotFoundHTTPError`
            If the overwrite or channel do not exist.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you lack the ``MANAGE_ROLES`` permission for that channel.
        """
        await self._session.delete_channel_permission(
            channel_id=str(channel.id if isinstance(channel, bases.UniqueEntity) else int(channel)),
            overwrite_id=str(overwrite.id if isinstance(overwrite, bases.UniqueEntity) else int(overwrite)),
        )

    async def trigger_typing(self, channel: bases.Hashable[_channels.Channel]) -> None:
        """Trigger the typing indicator for ``10`` seconds in a channel.

        Parameters
        ----------
        channel : :obj:`~typing.Union` [ :obj:`~hikari.channels.Channel`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the channel to appear to be typing in.

        Raises
        ------
        :obj:`~hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`~hikari.errors.NotFoundHTTPError`
            If the channel is not found.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you are not able to type in the channel.
        """
        await self._session.trigger_typing_indicator(
            channel_id=str(channel.id if isinstance(channel, bases.UniqueEntity) else int(channel))
        )

    async def fetch_pins(
        self, channel: bases.Hashable[_channels.Channel]
    ) -> typing.Mapping[bases.Snowflake, _messages.Message]:
        """Get pinned messages for a given channel.

        Parameters
        ----------
        channel : :obj:`~typing.Union` [ :obj:`~hikari.channels.Channel`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the channel to get messages from.

        Returns
        -------
        :obj:`~typing.Mapping` [ :obj:`~hikari.entities.Snowflake`, :obj:`~hikari.messages.Message` ]
            A list of message objects.

        Raises
        ------
        :obj:`~hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`~hikari.errors.NotFoundHTTPError`
            If the channel is not found.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you are not able to see the channel.

        Note
        ----
        If you are not able to see the pinned message (eg. you are missing
        ``READ_MESSAGE_HISTORY`` and the pinned message is an old message), it
        will not be returned.
        """
        payload = await self._session.get_pinned_messages(
            channel_id=str(channel.id if isinstance(channel, bases.UniqueEntity) else int(channel))
        )
        return {message.id: message for message in map(_messages.Message.deserialize, payload)}

    async def pin_message(
        self, channel: bases.Hashable[_channels.Channel], message: bases.Hashable[_messages.Message],
    ) -> None:
        """Add a pinned message to the channel.

        Parameters
        ----------
        channel : :obj:`~typing.Union` [ :obj:`~hikari.channels.Channel`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the channel to pin a message to.
        message : :obj:`~typing.Union` [ :obj:`~hikari.messages.Message`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the message to pin.

        Raises
        ------
        :obj:`~hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you lack the ``MANAGE_MESSAGES`` permission.
        :obj:`~hikari.errors.NotFoundHTTPError`
            If the message or channel do not exist.
        """
        await self._session.add_pinned_channel_message(
            channel_id=str(channel.id if isinstance(channel, bases.UniqueEntity) else int(channel)),
            message_id=str(message.id if isinstance(message, bases.UniqueEntity) else int(message)),
        )

    async def unpin_message(
        self, channel: bases.Hashable[_channels.Channel], message: bases.Hashable[_messages.Message],
    ) -> None:
        """Remove a pinned message from the channel.

        This will only unpin the message, not delete it.

        Parameters
        ----------
        channel : :obj:`~typing.Union` [ :obj:`~hikari.channels.Channel`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The ID of the channel to remove a pin from.
        message : :obj:`~typing.Union` [ :obj:`~hikari.messages.Message`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the message to unpin.

        Raises
        ------
        :obj:`~hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you lack the ``MANAGE_MESSAGES`` permission.
        :obj:`~hikari.errors.NotFoundHTTPError`
            If the message or channel do not exist.
        """
        await self._session.delete_pinned_channel_message(
            channel_id=str(channel.id if isinstance(channel, bases.UniqueEntity) else int(channel)),
            message_id=str(message.id if isinstance(message, bases.UniqueEntity) else int(message)),
        )

    async def create_webhook(
        self,
        channel: bases.Hashable[_channels.GuildChannel],
        name: str,
        *,
        avatar_data: conversions.FileLikeT = ...,
        reason: str = ...,
    ) -> webhooks.Webhook:
        """Create a webhook for a given channel.

        Parameters
        ----------
        channel : :obj:`~typing.Union` [ :obj:`~hikari.channels.GuildChannel`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the channel for webhook to be created in.
        name : :obj:`~str`
            The webhook's name string.
        avatar_data : ``hikari.internal.conversions.FileLikeT``
            If specified, the avatar image data.
        reason : :obj:`~str`
            If specified, the audit log reason explaining why the operation
            was performed.

        Returns
        -------
        :obj:`~hikari.webhooks.Webhook`
            The newly created webhook object.

        Raises
        ------
        :obj:`~hikari.errors.NotFoundHTTPError`
            If the channel is not found.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you either lack the ``MANAGE_WEBHOOKS`` permission or
            can not see the given channel.
        :obj:`~hikari.errors.BadRequestHTTPError`
            If the avatar image is too big or the format is invalid.
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        """
        payload = await self._session.create_webhook(
            channel_id=str(channel.id if isinstance(channel, bases.UniqueEntity) else int(channel)),
            name=name,
            avatar=conversions.get_bytes_from_resource(avatar_data) if avatar_data is not ... else ...,
            reason=reason,
        )
        return webhooks.Webhook.deserialize(payload)

    async def fetch_channel_webhooks(
        self, channel: bases.Hashable[_channels.GuildChannel]
    ) -> typing.Sequence[webhooks.Webhook]:
        """Get all webhooks from a given channel.

        Parameters
        ----------
        channel : :obj:`~typing.Union` [ :obj:`~hikari.channels.GuildChannel`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the guild channel to get the webhooks from.

        Returns
        -------
        :obj:`~typing.Sequence` [ :obj:`~hikari.webhooks.Webhook` ]
            A list of webhook objects for the give channel.

        Raises
        ------
        :obj:`~hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`~hikari.errors.NotFoundHTTPError`
            If the channel is not found.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you either lack the ``MANAGE_WEBHOOKS`` permission or
            can not see the given channel.
        """
        payload = await self._session.get_channel_webhooks(
            channel_id=str(channel.id if isinstance(channel, bases.UniqueEntity) else int(channel))
        )
        return [webhooks.Webhook.deserialize(webhook) for webhook in payload]
