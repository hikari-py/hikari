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

from __future__ import annotations

__all__ = ["RESTChannelComponent"]

import abc
import datetime
import typing

from hikari import pagination
from hikari import bases
from hikari import channels as _channels
from hikari import invites
from hikari import messages as _messages
from hikari import webhooks
from hikari.clients.rest import base
from hikari.internal import helpers

if typing.TYPE_CHECKING:
    from hikari import embeds as _embeds
    from hikari import files as _files
    from hikari import guilds
    from hikari import permissions as _permissions
    from hikari import users

    from hikari.internal import more_typing


class _MessagePaginator(pagination.BufferedPaginatedResults[_messages.Message]):
    __slots__ = ("_channel_id", "_direction", "_first_id", "_components", "_session")

    def __init__(self, channel, direction, first, components, session) -> None:
        super().__init__()
        self._channel_id = str(int(channel))
        self._direction = direction
        self._first_id = (
            bases.Snowflake.from_datetime(first) if isinstance(first, datetime.datetime) else str(int(first))
        )
        self._components = components
        self._session = session

    async def _next_chunk(self):
        kwargs = {
            self._direction: self._first_id,
            "channel_id": self._channel_id,
            "limit": 100,
        }

        chunk = await self._session.get_channel_messages(**kwargs)

        if not chunk:
            return None
        if self._direction == "after":
            chunk.reverse()

        self._first_id = chunk[-1]["id"]

        return (_messages.Message.deserialize(m, components=self._components) for m in chunk)


class RESTChannelComponent(base.BaseRESTComponent, abc.ABC):  # pylint: disable=abstract-method, too-many-public-methods
    """The REST client component for handling requests to channel endpoints."""

    async def fetch_channel(
        self, channel: typing.Union[bases.Snowflake, int, str, _channels.PartialChannel]
    ) -> _channels.PartialChannel:
        """Get an up to date channel object from a given channel object or ID.

        Parameters
        ----------
        channel : typing.Union[hikari.channels.PartialChannel, hikari.bases.Snowflake, int]
            The object ID of the channel to look up.

        Returns
        -------
        hikari.channels.PartialChannel
            The channel object that has been found.

        Raises
        ------
        hikari.errors.BadRequest
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        hikari.errors.Forbidden
            If you don't have access to the channel.
        hikari.errors.NotFound
            If the channel does not exist.
        """
        payload = await self._session.get_channel(
            channel_id=str(channel.id if isinstance(channel, bases.Unique) else int(channel))
        )
        return _channels.deserialize_channel(payload, components=self._components)

    async def update_channel(
        self,
        channel: typing.Union[bases.Snowflake, int, str, _channels.PartialChannel],
        *,
        name: str = ...,
        position: int = ...,
        topic: str = ...,
        nsfw: bool = ...,
        bitrate: int = ...,
        user_limit: int = ...,
        rate_limit_per_user: typing.Union[int, datetime.timedelta] = ...,
        permission_overwrites: typing.Sequence[_channels.PermissionOverwrite] = ...,
        parent_category: typing.Optional[typing.Union[bases.Snowflake, int, str, _channels.GuildCategory]] = ...,
        reason: str = ...,
    ) -> _channels.PartialChannel:
        """Update one or more aspects of a given channel ID.

        Parameters
        ----------
        channel : typing.Union[hikari.channels.PartialChannel, hikari.bases.Snowflake, int]
            The channel ID to update.
        name : str
            If specified, the new name for the channel. This must be
            inclusively between `1` and `100` characters in length.
        position : int
            If specified, the position to change the channel to.
        topic : str
            If specified, the topic to set. This is only applicable to
            text channels. This must be inclusively between `0` and `1024`
            characters in length.
        nsfw : bool
            Mark the channel as being not safe for work (NSFW) if `True`.
            If `False` or unspecified, then the channel is not marked as
            NSFW. Will have no visible effect for non-text guild channels.
        rate_limit_per_user : typing.Union[int, datetime.timedelta]
            If specified, the time delta of seconds  the user has to wait
            before sending another message. This will not apply to bots, or to
            members with `MANAGE_MESSAGES` or `MANAGE_CHANNEL` permissions.
            This must be inclusively between `0` and `21600` seconds.
        bitrate : int
            If specified, the bitrate in bits per second allowable for the
            channel. This only applies to voice channels and must be inclusively
            between `8000` and `96000` for normal servers or `8000` and
            `128000` for VIP servers.
        user_limit : int
            If specified, the new max number of users to allow in a voice
            channel. This must be between `0` and `99` inclusive, where
            `0` implies no limit.
        permission_overwrites : typing.Sequence[hikari.channels.PermissionOverwrite]
            If specified, the new list of permission overwrites that are
            category specific to replace the existing overwrites with.
        parent_category : typing.Union[hikari.channels.PartialChannel, hikari.bases.Snowflake, int], optional
            If specified, the new parent category ID to set for the channel,
            pass `None` to unset.
        reason : str
            If specified, the audit log reason explaining why the operation
            was performed.

        Returns
        -------
        hikari.channels.PartialChannel
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
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        """
        payload = await self._session.modify_channel(
            channel_id=str(channel.id if isinstance(channel, bases.Unique) else int(channel)),
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
                str(parent_category.id if isinstance(parent_category, bases.Unique) else int(parent_category))
                if parent_category is not ... and parent_category is not None
                else parent_category
            ),
            reason=reason,
        )
        return _channels.deserialize_channel(payload, components=self._components)

    async def delete_channel(self, channel: typing.Union[bases.Snowflake, int, str, _channels.PartialChannel]) -> None:
        """Delete the given channel ID, or if it is a DM, close it.

        Parameters
        ----------
        channel : typing.Union[hikari.channels.PartialChannel, hikari.bases.Snowflake str]
            The object or ID of the channel to delete.

        Returns
        -------
        None
            Nothing, unlike what the API specifies. This is done to maintain
            consistency with other calls of a similar nature in this API
            wrapper.

        Raises
        ------
        hikari.errors.BadRequest
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        hikari.errors.NotFound
            If the channel does not exist.
        hikari.errors.Forbidden
            If you do not have permission to delete the channel.

        !!! note
            Closing a DM channel won't raise an exception but will have no
            effect and "closed" DM channels will not have to be reopened to send
            messages in theme.

        !!! warning
            Deleted channels cannot be un-deleted.
        """
        await self._session.delete_close_channel(
            channel_id=str(channel.id if isinstance(channel, bases.Unique) else int(channel))
        )

    @typing.overload
    def fetch_messages(
        self, channel: typing.Union[bases.Snowflake, int, str, _channels.PartialChannel]
    ) -> pagination.PaginatedResults[_messages.Message]:
        """Fetch the channel history, starting with the newest messages."""

    @typing.overload
    def fetch_messages(
        self,
        channel: typing.Union[bases.Snowflake, int, str, _channels.PartialChannel],
        before: typing.Union[datetime.datetime, int, str, bases.Unique, bases.Snowflake],
    ) -> pagination.PaginatedResults[_messages.Message]:
        """Fetch the channel history before a given message/time."""

    @typing.overload
    def fetch_messages(
        self,
        channel: typing.Union[bases.Snowflake, int, str, _channels.PartialChannel],
        after: typing.Union[datetime.datetime, int, str, bases.Unique, bases.Snowflake],
    ) -> pagination.PaginatedResults[_messages.Message]:
        """Fetch the channel history after a given message/time."""

    @typing.overload
    def fetch_messages(
        self,
        channel: typing.Union[bases.Snowflake, int, str, _channels.PartialChannel],
        around: typing.Union[datetime.datetime, int, str, bases.Unique, bases.Snowflake],
    ) -> pagination.PaginatedResults[_messages.Message]:
        """Fetch the channel history around a given message/time."""

    def fetch_messages(
        self,
        channel: typing.Union[bases.Snowflake, int, str, _channels.PartialChannel],
        **kwargs: typing.Union[datetime.datetime, int, str, bases.Unique, bases.Snowflake],
    ) -> pagination.PaginatedResults[_messages.Message]:
        """Fetch messages from the channel's history.

        Parameters
        ----------
        channel : hikari.channels.PartialChannel OR hikari.bases.Snowflake OR int OR str
            The channel to fetch messages from.

        Keyword Arguments
        -----------------
        before : datetime.datetime OR int OR str OR hikari.bases.Unique OR hikari.bases.Snowflake
            If a unique object (like a message), then message created before
            this object will be returned. If a datetime, then messages before
            that datetime will be returned. If unspecified or None, the filter
            is not used.
        after : datetime.datetime OR int OR str OR hikari.bases.Unique OR hikari.bases.Snowflake
            If a unique object (like a message), then message created after this
            object will be returned. If a datetime, then messages after that
            datetime will be returned. If unspecified or None, the filter is not
            used.
        around : datetime.datetime OR int OR str OR hikari.bases.Unique OR hikari.bases.Snowflake
            If a unique object (like a message), then message created around the
            same time as this object will be returned. If a datetime, then
            messages around that datetime will be returned. If unspecified or
            None, the filter is not used.

        !!! info
            Using `before` or no filter will return messages in the order
            of newest-to-oldest. Using the `after` filter will return
            messages in the order of oldest-to-newest. Using th `around`
            filter may have arbitrary ordering.

        !!! warning
            Only one of `before`, `after`, or `around` may be specified.

        !!! note
            Passing no value for `before`, `after`, or `around` will have the
            same effect as passing `before=hikari.bases.Snowflake.max()`. This
            will return all messages that can be found, newest to oldest.

        Examples
        --------
        Fetching the last 20 messages before May 2nd, 2020:

            timestamp = datetime.datetime(2020, 5, 2)

            async for message in rest.fetch_messages(channel, before=timestamp).limit(20):
                print(message.author, message.content)

        Fetching messages sent around the same time as a given message.

            async for message in rest.fetch_messages(channel, around=event.message):
                print(message.author, message.content)

        Fetching messages after May 3rd, 2020 at 15:33 UTC.

            timestamp = datetime.datetime(2020, 5, 3, 15, 33, tzinfo=datetime.timezone.utc)

            async for message in rest.fetch_messages(channel, after=timestamp):
                print(message.author, message.content)

        Fetching all messages, newest to oldest:

            async for message in rest.fetch_messages(channel, before=datetime.datetime.utcnow()):
                print(message)

            # More efficient alternative
            async for message in rest.fetch_messages(channel):
                print(message)

        Fetching all messages, oldest to newest:

            async for message in rest.fetch_messages(channel, after=):
                print(message)

        !!! warning
            `datetime.datetime` objects are expected to be `utc` if timezone
            naieve (which they are by default). This means that
            `datetime.datetime.now` will always be treated as if it were
            UTC unless you specify a timezone. Thus, it is important to always
            use `datetime.datetime.utcnow` over `datetime.datetime.now` if you
            want your application to work outside the `GMT+0` timezone.

        !!! note
            The `around` parameter is not documented clearly by Discord.
            The actual number of messages returned by this, and the direction
            (e.g. older/newer/both) is not overly intuitive. Thus, this
            specific functionality may be deprecated in the future in favour
            of a cleaner Python API until a time comes where this information is
            documented at a REST API level by Discord.

        Returns
        -------
        hikari.pagination.PaginatedResults[hikari.messages.Message]
            An async iterator of message objects.

        Raises
        ------
        hikari.errors.NotFound
            If the channel is not found.
        hikari.errors.Forbidden
            If you are missing the `READ_MESSAGE_HISTORY` permission for the
            channel or guild.
        """
        if len(kwargs) > 1:
            raise TypeError("only one of 'before', 'after', 'around' can be specified")

        try:
            direction, first = kwargs.popitem()
        except KeyError:
            direction, first = "before", bases.Snowflake.max()

        return _MessagePaginator(
            channel=channel, direction=direction, first=first, components=self._components, session=self._session,
        )

    async def fetch_message(
        self,
        channel: typing.Union[bases.Snowflake, int, str, _channels.PartialChannel],
        message: typing.Union[bases.Snowflake, int, str, _messages.Message],
    ) -> _messages.Message:
        """Get a message from known channel that we can access.

        Parameters
        ----------
        channel : typing.Union[hikari.channels.PartialChannel, hikari.bases.Snowflake, int]
            The object or ID of the channel to get the message from.
        message : typing.Union[hikari.messages.Message, hikari.bases.Snowflake, int]
            The object or ID of the message to retrieve.

        Returns
        -------
        hikari.messages.Message
            The found message object.

        !!! note
            This requires the `READ_MESSAGE_HISTORY` permission.

        Raises
        ------
        hikari.errors.BadRequest
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        hikari.errors.Forbidden
            If you lack permission to see the message.
        hikari.errors.NotFound
            If the channel or message is not found.
        """
        payload = await self._session.get_channel_message(
            channel_id=str(channel.id if isinstance(channel, bases.Unique) else int(channel)),
            message_id=str(message.id if isinstance(message, bases.Unique) else int(message)),
        )
        return _messages.Message.deserialize(payload, components=self._components)

    async def create_message(  # pylint: disable=line-too-long
        self,
        channel: typing.Union[bases.Snowflake, int, str, _channels.PartialChannel],
        *,
        content: str = ...,
        nonce: str = ...,
        tts: bool = ...,
        files: typing.Sequence[_files.BaseStream] = ...,
        embed: _embeds.Embed = ...,
        mentions_everyone: bool = True,
        user_mentions: typing.Union[
            typing.Collection[typing.Union[bases.Snowflake, int, str, users.User]], bool
        ] = True,
        role_mentions: typing.Union[
            typing.Collection[typing.Union[bases.Snowflake, int, str, guilds.GuildRole]], bool
        ] = True,
    ) -> _messages.Message:
        """Create a message in the given channel.

        Parameters
        ----------
        channel : typing.Union[hikari.channels.PartialChannel, hikari.bases.Snowflake, int]
            The channel or ID of the channel to send to.
        content : str
            If specified, the message content to send with the message.
        nonce : str
            If specified, an optional ID to send for opportunistic message
            creation. Any created message will have this nonce set on it.
            Nonces are limited to 32 bytes in size.
        tts : bool
            If specified, whether the message will be sent as a TTS message.
        files : typing.Sequence[hikari.files.BaseStream]
            If specified, a sequence of files to upload, if desired. Should be
            between 1 and 10 objects in size (inclusive), also including embed
            attachments.
        embed : hikari.embeds.Embed
            If specified, the embed object to send with the message.
        mentions_everyone : bool
            Whether `@everyone` and `@here` mentions should be resolved by
            discord and lead to actual pings, defaults to `True`.
        user_mentions : typing.Union[typing.Collection[typing.Union[hikari.users.User, hikari.bases.Snowflake, int]], bool]
            Either an array of user objects/IDs to allow mentions for,
            `True` to allow all user mentions or `False` to block all
            user mentions from resolving, defaults to `True`.
        role_mentions: typing.Union[typing.Collection[typing.Union[hikari.guilds.GuildRole, hikari.bases.Snowflake, int]], bool]
            Either an array of guild role objects/IDs to allow mentions for,
            `True` to allow all role mentions or `False` to block all
            role mentions from resolving, defaults to `True`.

        Returns
        -------
        hikari.messages.Message
            The created message object.

        Raises
        ------
        hikari.errors.NotFound
            If the channel is not found.
        hikari.errors.BadRequest
            This can be raised if the file is too large; if the embed exceeds
            the defined limits; if the message content is specified only and
            empty or greater than `2000` characters; if neither content, files
            or embed are specified.
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
            If you are trying to upload more than 10 files in total (including
            embed attachments).
        hikari.errors.Forbidden
            If you lack permissions to send to this channel.
        ValueError
            If more than 100 unique objects/entities are passed for
            `role_mentions` or `user_mentions`.
        """
        file_resources = []
        if files is not ...:
            file_resources += files
        if embed is not ...:
            file_resources += embed.assets_to_upload

        payload = await self._session.create_message(
            channel_id=str(channel.id if isinstance(channel, bases.Unique) else int(channel)),
            content=content,
            nonce=nonce,
            tts=tts,
            files=file_resources if file_resources else ...,
            embed=embed.serialize() if embed is not ... else ...,
            allowed_mentions=helpers.generate_allowed_mentions(
                mentions_everyone=mentions_everyone, user_mentions=user_mentions, role_mentions=role_mentions
            ),
        )
        return _messages.Message.deserialize(payload, components=self._components)

    def safe_create_message(
        self,
        channel: typing.Union[bases.Snowflake, int, str, _channels.PartialChannel],
        *,
        content: str = ...,
        nonce: str = ...,
        tts: bool = ...,
        files: typing.Sequence[_files.BaseStream] = ...,
        embed: _embeds.Embed = ...,
        mentions_everyone: bool = False,
        user_mentions: typing.Union[
            typing.Collection[typing.Union[bases.Snowflake, int, str, users.User]], bool
        ] = False,
        role_mentions: typing.Union[
            typing.Collection[typing.Union[bases.Snowflake, int, str, guilds.GuildRole]], bool
        ] = False,
    ) -> more_typing.Coroutine[_messages.Message]:
        """Create a message in the given channel with mention safety.

        This endpoint has the same signature as
        `RESTChannelComponent.create_message` with the only difference being
        that `mentions_everyone`, `user_mentions` and `role_mentions` default to
        `False`.
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

    async def update_message(  # pylint: disable=line-too-long
        self,
        message: typing.Union[bases.Snowflake, int, str, _messages.Message],
        channel: typing.Union[bases.Snowflake, int, str, _channels.PartialChannel],
        *,
        content: typing.Optional[str] = ...,
        embed: typing.Optional[_embeds.Embed] = ...,
        flags: int = ...,
        mentions_everyone: bool = True,
        user_mentions: typing.Union[
            typing.Collection[typing.Union[bases.Snowflake, int, str, users.User]], bool
        ] = True,
        role_mentions: typing.Union[
            typing.Collection[typing.Union[bases.Snowflake, int, str, guilds.GuildRole]], bool
        ] = True,
    ) -> _messages.Message:
        """Update the given message.

        Parameters
        ----------
        channel : typing.Union[hikari.channels.PartialChannel, hikari.bases.Snowflake, int]
            The object or ID of the channel to get the message from.
        message : typing.Union[hikari.messages.Message, hikari.bases.Snowflake, int]
            The object or ID of the message to edit.
        content : str, optional
            If specified, the string content to replace with in the message.
            If `None`, then the content will be removed from the message.
        embed : hikari.embeds.Embed, optional
            If specified, then the embed to replace with in the message.
            If `None`, then the embed will be removed from the message.
        flags : hikari.messages.MessageFlag
            If specified, the new flags for this message, while a raw int may
            be passed for this, this can lead to unexpected behaviour if it's
            outside the range of the MessageFlag int flag.
        mentions_everyone : bool
            Whether `@everyone` and `@here` mentions should be resolved by
            discord and lead to actual pings, defaults to `True`.
        user_mentions: typing.Union[typing.Collection[typing.Union[hikari.users.User, hikari.bases.Snowflake, int]], bool]
            Either an array of user objects/IDs to allow mentions for,
            `True` to allow all user mentions or `False` to block all
            user mentions from resolving, defaults to `True`.
        role_mentions: typing.Union[typing.Collection[typing.Union[hikari.guilds.GuildRole, hikari.bases.Snowflake, int]], bool]
            Either an array of guild role objects/IDs to allow mentions for,
            `True` to allow all role mentions or `False` to block all
            role mentions from resolving, defaults to `True`.

        Returns
        -------
        hikari.messages.Message
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
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        hikari.errors.Forbidden
            If you try to edit `content` or `embed` or `allowed_mentions`
            on a message you did not author.
            If you try to edit the flags on a message you did not author without
            the `MANAGE_MESSAGES` permission.
        ValueError
            If more than 100 unique objects/entities are passed for
            `role_mentions` or `user_mentions`.
        """
        payload = await self._session.edit_message(
            channel_id=str(channel.id if isinstance(channel, bases.Unique) else int(channel)),
            message_id=str(message.id if isinstance(message, bases.Unique) else int(message)),
            content=content,
            embed=embed.serialize() if embed is not ... and embed is not None else embed,
            flags=flags,
            allowed_mentions=helpers.generate_allowed_mentions(
                mentions_everyone=mentions_everyone, user_mentions=user_mentions, role_mentions=role_mentions,
            ),
        )
        return _messages.Message.deserialize(payload, components=self._components)

    def safe_update_message(
        self,
        message: typing.Union[bases.Snowflake, int, str, _messages.Message],
        channel: typing.Union[bases.Snowflake, int, str, _channels.PartialChannel],
        *,
        content: typing.Optional[str] = ...,
        embed: typing.Optional[_embeds.Embed] = ...,
        flags: int = ...,
        mentions_everyone: bool = False,
        user_mentions: typing.Union[
            typing.Collection[typing.Union[bases.Snowflake, int, str, users.User]], bool
        ] = False,
        role_mentions: typing.Union[
            typing.Collection[typing.Union[bases.Snowflake, int, str, guilds.GuildRole]], bool
        ] = False,
    ) -> typing.Coroutine[typing.Any, typing.Any, _messages.Message]:
        """Update a message in the given channel with mention safety.

        This endpoint has the same signature as
        `RESTChannelComponent.update_message` with the only difference being
        that `mentions_everyone`, `user_mentions` and `role_mentions` default to
        `False`.
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
        channel: typing.Union[bases.Snowflake, int, str, _channels.PartialChannel],
        message: typing.Union[bases.Snowflake, int, str, _messages.Message],
        *additional_messages: typing.Union[bases.Snowflake, int, str, _messages.Message],
    ) -> None:
        """Delete a message in a given channel.

        Parameters
        ----------
        channel : typing.Union[hikari.channels.PartialChannel, hikari.bases.Snowflake, int]
            The object or ID of the channel to get the message from.
        message : typing.Union[hikari.messages.Message, hikari.bases.Snowflake, int]
            The object or ID of the message to delete.
        *additional_messages : typing.Union[hikari.messages.Message, hikari.bases.Snowflake, int]
            Objects and/or IDs of additional messages to delete in the same
            channel, in total you can delete up to 100 messages in a request.

        Raises
        ------
        hikari.errors.BadRequest
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        hikari.errors.Forbidden
            If you did not author the message and are in a DM, or if you did
            not author the message and lack the `MANAGE_MESSAGES`
            permission in a guild channel.
        hikari.errors.NotFound
            If the channel or message is not found.
        ValueError
            If you try to delete over `100` messages in a single request.

        !!! note
            This can only be used on guild text channels.
            Any message IDs that do not exist or are invalid still add towards
            the total `100` max messages to remove. This can only delete
            messages that are newer than `2` weeks in age. If any of the
            messages are older than `2` weeks then this call will fail.
        """
        if additional_messages:
            messages = list(
                # dict.fromkeys is used to remove duplicate entries that would cause discord to return an error.
                dict.fromkeys(
                    str(m.id if isinstance(m, bases.Unique) else int(m)) for m in (message, *additional_messages)
                )
            )
            if len(messages) > 100:
                raise ValueError("Only up to 100 messages can be bulk deleted in a single request.")

            if len(messages) > 1:
                await self._session.bulk_delete_messages(
                    channel_id=str(channel.id if isinstance(channel, bases.Unique) else int(channel)),
                    messages=messages,
                )
                return None

        await self._session.delete_message(
            channel_id=str(channel.id if isinstance(channel, bases.Unique) else int(channel)),
            message_id=str(message.id if isinstance(message, bases.Unique) else int(message)),
        )

    async def update_channel_overwrite(  # pylint: disable=line-too-long
        self,
        channel: typing.Union[bases.Snowflake, int, str, _messages.Message],
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
        channel : typing.Union[hikari.messages.Message, hikari.bases.Snowflake, int]
            The object or ID of the channel to edit permissions for.
        overwrite : typing.Union[hikari.channels.PermissionOverwrite, hikari.guilds.GuildRole, hikari.users.User, hikari.bases.Snowflake , int]
            The object or ID of the target member or role to  edit/create the
            overwrite for.
        target_type : typing.Union[hikari.channels.PermissionOverwriteType, int]
            The type of overwrite, passing a raw string that's outside of the
            enum's range for this may lead to unexpected behaviour.
        allow : typing.Union[hikari.permissions.Permission, int]
            If specified, the value of all permissions to set to be allowed,
            passing a raw integer for this may lead to unexpected behaviour.
        deny : typing.Union[hikari.permissions.Permission, int]
            If specified, the value of all permissions to set to be denied,
            passing a raw integer for this may lead to unexpected behaviour.
        reason : str
            If specified, the audit log reason explaining why the operation
            was performed.

        Raises
        ------
        hikari.errors.BadRequest
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        hikari.errors.NotFound
            If the target channel or overwrite doesn't exist.
        hikari.errors.Forbidden
            If you lack permission to do this.
        """
        # pylint: enable=line-too-long
        await self._session.edit_channel_permissions(
            channel_id=str(channel.id if isinstance(channel, bases.Unique) else int(channel)),
            overwrite_id=str(overwrite.id if isinstance(overwrite, bases.Unique) else int(overwrite)),
            type_=target_type,
            allow=allow,
            deny=deny,
            reason=reason,
        )

    async def fetch_invites_for_channel(
        self, channel: typing.Union[bases.Snowflake, int, str, _channels.PartialChannel]
    ) -> typing.Sequence[invites.InviteWithMetadata]:
        """Get invites for a given channel.

        Parameters
        ----------
        channel : typing.Union[hikari.channels.PartialChannel, hikari.bases.Snowflake, int]
            The object or ID of the channel to get invites for.

        Returns
        -------
        typing.Sequence[hikari.invites.InviteWithMetadata]
            A list of invite objects.

        Raises
        ------
        hikari.errors.BadRequest
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        hikari.errors.Forbidden
            If you lack the `MANAGE_CHANNELS` permission.
        hikari.errors.NotFound
            If the channel does not exist.
        """
        payload = await self._session.get_channel_invites(
            channel_id=str(channel.id if isinstance(channel, bases.Unique) else int(channel))
        )
        return [invites.InviteWithMetadata.deserialize(invite, components=self._components) for invite in payload]

    async def create_invite_for_channel(
        self,
        channel: typing.Union[bases.Snowflake, int, str, _channels.PartialChannel],
        *,
        max_age: typing.Union[int, datetime.timedelta] = ...,
        max_uses: int = ...,
        temporary: bool = ...,
        unique: bool = ...,
        target_user: typing.Union[bases.Snowflake, int, str, users.User] = ...,
        target_user_type: typing.Union[invites.TargetUserType, int] = ...,
        reason: str = ...,
    ) -> invites.InviteWithMetadata:
        """Create a new invite for the given channel.

        Parameters
        ----------
        channel : typing.Union[datetime.timedelta, str]
            The object or ID of the channel to create the invite for.
        max_age : int
            If specified, the seconds time delta for the max age of the invite,
            defaults to `86400` seconds (`24` hours).
            Set to `0` seconds to never expire.
        max_uses : int
            If specified, the max number of uses this invite can have, or `0`
            for unlimited (as per the default).
        temporary : bool
            If specified, whether to grant temporary membership, meaning the
            user is kicked when their session ends unless they are given a role.
        unique : bool
            If specified, whether to try to reuse a similar invite.
        target_user : typing.Union[hikari.users.User, hikari.bases.Snowflake, int]
            If specified, the object or ID of the user this invite should
            target.
        target_user_type : typing.Union[hikari.invites.TargetUserType, int]
            If specified, the type of target for this invite, passing a raw
            integer for this may lead to unexpected results.
        reason : str
            If specified, the audit log reason explaining why the operation
            was performed.

        Returns
        -------
        hikari.invites.InviteWithMetadata
            The created invite object.

        Raises
        ------
        hikari.errors.Forbidden
            If you lack the `CREATE_INSTANT_MESSAGES` permission.
        hikari.errors.NotFound
            If the channel does not exist.
        hikari.errors.BadRequest
            If the arguments provided are not valid (e.g. negative age, etc).
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        """
        payload = await self._session.create_channel_invite(
            channel_id=str(channel.id if isinstance(channel, bases.Unique) else int(channel)),
            max_age=int(max_age.total_seconds()) if isinstance(max_age, datetime.timedelta) else max_age,
            max_uses=max_uses,
            temporary=temporary,
            unique=unique,
            target_user=(
                str(target_user.id if isinstance(target_user, bases.Unique) else int(target_user))
                if target_user is not ...
                else ...
            ),
            target_user_type=target_user_type,
            reason=reason,
        )
        return invites.InviteWithMetadata.deserialize(payload, components=self._components)

    async def delete_channel_overwrite(  # pylint: disable=line-too-long
        self,
        channel: typing.Union[bases.Snowflake, int, str, _channels.PartialChannel],
        overwrite: typing.Union[_channels.PermissionOverwrite, guilds.GuildRole, users.User, bases.Snowflake, int],
    ) -> None:
        """Delete a channel permission overwrite for a user or a role.

        Parameters
        ----------
        channel : typing.Union[hikari.channels.PartialChannel, hikari.bases.Snowflake, int]
            The object or ID of the channel to delete the overwrite from.
        overwrite : typing.Union[hikari.channels.PermissionOverwrite, hikari.guilds.GuildRole, hikari.users.User, hikari.bases.Snowflake, int]
            The ID of the entity this overwrite targets.

        Raises
        ------
        hikari.errors.BadRequest
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        hikari.errors.NotFound
            If the overwrite or channel do not exist.
        hikari.errors.Forbidden
            If you lack the `MANAGE_ROLES` permission for that channel.
        """
        # pylint: enable=line-too-long
        await self._session.delete_channel_permission(
            channel_id=str(channel.id if isinstance(channel, bases.Unique) else int(channel)),
            overwrite_id=str(overwrite.id if isinstance(overwrite, bases.Unique) else int(overwrite)),
        )

    async def trigger_typing(self, channel: typing.Union[bases.Snowflake, int, str, _channels.PartialChannel]) -> None:
        """Trigger the typing indicator for `10` seconds in a channel.

        Parameters
        ----------
        channel : typing.Union[hikari.channels.PartialChannel, hikari.bases.Snowflake, int]
            The object or ID of the channel to appear to be typing in.

        Raises
        ------
        hikari.errors.BadRequest
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        hikari.errors.NotFound
            If the channel is not found.
        hikari.errors.Forbidden
            If you are not able to type in the channel.
        """
        await self._session.trigger_typing_indicator(
            channel_id=str(channel.id if isinstance(channel, bases.Unique) else int(channel))
        )

    async def fetch_pins(
        self, channel: typing.Union[bases.Snowflake, int, str, _channels.PartialChannel]
    ) -> typing.Mapping[bases.Snowflake, _messages.Message]:
        """Get pinned messages for a given channel.

        Parameters
        ----------
        channel : typing.Union[hikari.channels.PartialChannel, hikari.bases.Snowflake, int]
            The object or ID of the channel to get messages from.

        Returns
        -------
        typing.Mapping[hikari.bases.Snowflake, hikari.messages.Message]
            A list of message objects.

        Raises
        ------
        hikari.errors.BadRequest
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        hikari.errors.NotFound
            If the channel is not found.
        hikari.errors.Forbidden
            If you are not able to see the channel.

        !!! note
            If you are not able to see the pinned message (eg. you are missing
            `READ_MESSAGE_HISTORY` and the pinned message is an old message), it
            will not be returned.
        """
        payload = await self._session.get_pinned_messages(
            channel_id=str(channel.id if isinstance(channel, bases.Unique) else int(channel))
        )
        return {
            bases.Snowflake(message["id"]): _messages.Message.deserialize(message, components=self._components)
            for message in payload
        }

    async def pin_message(
        self,
        channel: typing.Union[bases.Snowflake, int, str, _channels.PartialChannel],
        message: typing.Union[bases.Snowflake, int, str, _messages.Message],
    ) -> None:
        """Add a pinned message to the channel.

        Parameters
        ----------
        channel : typing.Union[hikari.channels.PartialChannel, hikari.bases.Snowflake, int]
            The object or ID of the channel to pin a message to.
        message : typing.Union[hikari.messages.Message, hikari.bases.Snowflake, int]
            The object or ID of the message to pin.

        Raises
        ------
        hikari.errors.BadRequest
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        hikari.errors.Forbidden
            If you lack the `MANAGE_MESSAGES` permission.
        hikari.errors.NotFound
            If the message or channel do not exist.
        """
        await self._session.add_pinned_channel_message(
            channel_id=str(channel.id if isinstance(channel, bases.Unique) else int(channel)),
            message_id=str(message.id if isinstance(message, bases.Unique) else int(message)),
        )

    async def unpin_message(
        self,
        channel: typing.Union[bases.Snowflake, int, str, _channels.PartialChannel],
        message: typing.Union[bases.Snowflake, int, str, _messages.Message],
    ) -> None:
        """Remove a pinned message from the channel.

        This will only unpin the message, not delete it.

        Parameters
        ----------
        channel : typing.Union[hikari.channels.PartialChannel, hikari.bases.Snowflake, int]
            The ID of the channel to remove a pin from.
        message : typing.Union[hikari.messages.Message, hikari.bases.Snowflake, int]
            The object or ID of the message to unpin.

        Raises
        ------
        hikari.errors.BadRequest
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        hikari.errors.Forbidden
            If you lack the `MANAGE_MESSAGES` permission.
        hikari.errors.NotFound
            If the message or channel do not exist.
        """
        await self._session.delete_pinned_channel_message(
            channel_id=str(channel.id if isinstance(channel, bases.Unique) else int(channel)),
            message_id=str(message.id if isinstance(message, bases.Unique) else int(message)),
        )

    async def create_webhook(
        self,
        channel: typing.Union[bases.Snowflake, int, str, _channels.GuildChannel],
        name: str,
        *,
        avatar: _files.BaseStream = ...,
        reason: str = ...,
    ) -> webhooks.Webhook:
        """Create a webhook for a given channel.

        Parameters
        ----------
        channel : typing.Union[hikari.channels.GuildChannel, hikari.bases.Snowflake, int]
            The object or ID of the channel for webhook to be created in.
        name : str
            The webhook's name string.
        avatar : hikari.files.BaseStream
            If specified, the avatar image to use.
        reason : str
            If specified, the audit log reason explaining why the operation
            was performed.

        Returns
        -------
        hikari.webhooks.Webhook
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
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        """
        payload = await self._session.create_webhook(
            channel_id=str(channel.id if isinstance(channel, bases.Unique) else int(channel)),
            name=name,
            avatar=await avatar.read() if avatar is not ... else ...,
            reason=reason,
        )
        return webhooks.Webhook.deserialize(payload, components=self._components)

    async def fetch_channel_webhooks(
        self, channel: typing.Union[bases.Snowflake, int, str, _channels.GuildChannel]
    ) -> typing.Sequence[webhooks.Webhook]:
        """Get all webhooks from a given channel.

        Parameters
        ----------
        channel : typing.Union[hikari.channels.GuildChannel, hikari.bases.Snowflake, int]
            The object or ID of the guild channel to get the webhooks from.

        Returns
        -------
        typing.Sequence[hikari.webhooks.Webhook]
            A list of webhook objects for the give channel.

        Raises
        ------
        hikari.errors.BadRequest
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        hikari.errors.NotFound
            If the channel is not found.
        hikari.errors.Forbidden
            If you either lack the `MANAGE_WEBHOOKS` permission or
            can not see the given channel.
        """
        payload = await self._session.get_channel_webhooks(
            channel_id=str(channel.id if isinstance(channel, bases.Unique) else int(channel))
        )
        return [webhooks.Webhook.deserialize(webhook, components=self._components) for webhook in payload]
