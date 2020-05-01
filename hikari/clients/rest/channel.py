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
import functools
import typing

from hikari import bases
from hikari import channels as _channels
from hikari import invites
from hikari import messages as _messages
from hikari import webhooks
from hikari.clients.rest import base
from hikari.internal import assertions
from hikari.internal import helpers

if typing.TYPE_CHECKING:
    from hikari import embeds as _embeds
    from hikari import files as _files
    from hikari import guilds
    from hikari import permissions as _permissions
    from hikari import users

    from hikari.internal import more_typing


class RESTChannelComponent(base.BaseRESTComponent, abc.ABC):  # pylint: disable=abstract-method, too-many-public-methods
    """The REST client component for handling requests to channel endpoints."""

    async def fetch_channel(self, channel: bases.Hashable[_channels.Channel]) -> _channels.Channel:
        """Get an up to date channel object from a given channel object or ID.

        Parameters
        ----------
        channel : typing.Union[hikari.channels.Channel, hikari.bases.Snowflake, int]
            The object ID of the channel to look up.

        Returns
        -------
        hikari.channels.Channel
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
            channel_id=str(channel.id if isinstance(channel, bases.UniqueEntity) else int(channel))
        )
        return _channels.deserialize_channel(payload, components=self._components)

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
        channel : typing.Union[hikari.channels.Channel, hikari.bases.Snowflake, int]
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
        parent_category : typing.Union[hikari.channels.Channel, hikari.bases.Snowflake, int], optional
            If specified, the new parent category ID to set for the channel,
            pass `None` to unset.
        reason : str
            If specified, the audit log reason explaining why the operation
            was performed.

        Returns
        -------
        hikari.channels.Channel
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
        return _channels.deserialize_channel(payload, components=self._components)

    async def delete_channel(self, channel: bases.Hashable[_channels.Channel]) -> None:
        """Delete the given channel ID, or if it is a DM, close it.

        Parameters
        ----------
        channel : typing.Union[hikari.channels.Channel, hikari.bases.Snowflake str]
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
        channel : typing.Union[hikari.channels.Channel, hikari.bases.Snowflake, int]
            The ID of the channel to retrieve the messages from.
        limit : int
            If specified, the maximum number of how many messages this iterator
            should return.
        after : typing.Union[datetime.datetime, hikari.channels.Channel, hikari.bases.Snowflake, int]
            A object or ID message. Only return messages sent AFTER this
            message if it's specified else this will return every message after
            (and including) the first message in the channel.

        Examples
        --------
            async for message in client.fetch_messages_after(channel, after=9876543, limit=3232):
                if message.author.id in BLACKLISTED_USERS:
                    await client.ban_member(channel.guild_id,  message.author)

        Returns
        -------
        typing.AsyncIterator[hikari.messages.Message]
            An async iterator that retrieves the channel's message objects.

        Raises
        ------
        hikari.errors.BadRequest
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        hikari.errors.Forbidden
            If you lack permission to read the channel.
        hikari.errors.NotFound
            If the channel is not found, or the message
            provided for one of the filter arguments is not found.

        !!! note
            If you are missing the `VIEW_CHANNEL` permission, you will receive a
            hikari.errors.Forbidden. If you are instead missing
            the `READ_MESSAGE_HISTORY` permission, you will always receive
            zero results, and thus an empty list will be returned instead.
        """
        if isinstance(after, datetime.datetime):
            after = str(bases.Snowflake.from_datetime(after))
        else:
            after = str(after.id if isinstance(after, bases.UniqueEntity) else int(after))
        request = functools.partial(
            self._session.get_channel_messages,
            channel_id=str(channel.id if isinstance(channel, bases.UniqueEntity) else int(channel)),
        )
        deserializer = functools.partial(_messages.Message.deserialize, components=self._components)
        return helpers.pagination_handler(
            deserializer=deserializer,
            direction="after",
            start=after,
            request=request,
            reversing=True,  # This is the only regular paginated endpoint where reversing is needed.
            maximum_limit=100,
            limit=limit,
        )

    def fetch_messages_before(
        self,
        channel: bases.Hashable[_channels.Channel],
        *,
        before: typing.Union[datetime.datetime, bases.Hashable[_messages.Message]] = bases.LARGEST_SNOWFLAKE,
        limit: typing.Optional[int] = None,
    ) -> typing.AsyncIterator[_messages.Message]:
        """Return an async iterator that retrieves a channel's message history.

        This returns the message created after a given message object/ID or
        from the first message in the channel.

        Parameters
        ----------
        channel : typing.Union[hikari.channels.Channel, hikari.bases.Snowflake, int]
            The ID of the channel to retrieve the messages from.
        limit : int
            If specified, the maximum number of how many messages this iterator
            should return.
        before : typing.Union[datetime.datetime, hikari.channels.Channel, hikari.bases.Snowflake, int]
            A message object or ID. Only return messages sent BEFORE
            this message if this is specified else this will return every
            message before (and including) the most recent message in the
            channel.

        Examples
        --------
            async for message in client.fetch_messages_before(channel, before=9876543, limit=1231):
                if message.content.lower().contains("delete this"):
                    await client.delete_message(channel, message)

        Returns
        -------
        typing.AsyncIterator[hikari.messages.Message]
            An async iterator that retrieves the channel's message objects.

        Raises
        ------
        hikari.errors.BadRequest
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        hikari.errors.Forbidden
            If you lack permission to read the channel.
        hikari.errors.NotFound
            If the channel is not found, or the message
            provided for one of the filter arguments is not found.

        !!! note
            If you are missing the `VIEW_CHANNEL` permission, you will receive a
            hikari.errors.Forbidden. If you are instead missing
            the `READ_MESSAGE_HISTORY` permission, you will always receive
            zero results, and thus an empty list will be returned instead.
        """
        if isinstance(before, datetime.datetime):
            before = str(bases.Snowflake.from_datetime(before))
        else:
            before = str(before.id if isinstance(before, bases.UniqueEntity) else int(before))
        request = functools.partial(
            self._session.get_channel_messages,
            channel_id=str(channel.id if isinstance(channel, bases.UniqueEntity) else int(channel)),
        )
        deserializer = functools.partial(_messages.Message.deserialize, components=self._components)
        return helpers.pagination_handler(
            deserializer=deserializer,
            direction="before",
            start=before,
            request=request,
            reversing=False,
            maximum_limit=100,
            limit=limit,
        )

    async def fetch_messages_around(
        self,
        channel: bases.Hashable[_channels.Channel],
        around: typing.Union[datetime.datetime, bases.Hashable[_messages.Message]],
        *,
        limit: int = ...,
    ) -> typing.AsyncIterator[_messages.Message]:
        """Yield up to 100 messages found around a given point.

        This will return messages in order from newest to oldest, is based
        around the creation time of the supplied message object/ID and will
        include the given message if it still exists.

        Parameters
        ----------
        channel : typing.Union[hikari.channels.Channel, hikari.bases.Snowflake, int]
            The ID of the channel to retrieve the messages from.
        around : typing.Union[datetime.datetime, hikari.channels.Channel, hikari.bases.Snowflake, int]
            The object or ID of the message to get messages that were sent
            AROUND it in the provided channel, unlike `before` and `after`,
            this argument is required and the provided message will also be
            returned if it still exists.
        limit : int
            If specified, the maximum number of how many messages this iterator
            should return, cannot be more than `100`

        Examples
        --------
            async for message in client.fetch_messages_around(channel, around=9876543, limit=42):
                if message.embeds and not message.author.is_bot:
                    await client.delete_message(channel, message)

        Yields
        ------
        hikari.messages.Message
            The messages found around the given point.

        Raises
        ------
        hikari.errors.BadRequest
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        hikari.errors.Forbidden
            If you lack permission to read the channel.
        hikari.errors.NotFound
            If the channel is not found, or the message
            provided for one of the filter arguments is not found.

        !!! note
            If you are missing the `VIEW_CHANNEL` permission, you will receive a
            `hikari.errors.Forbidden`. If you are instead missing
            the `READ_MESSAGE_HISTORY` permission, you will always receive
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
            yield _messages.Message.deserialize(payload, components=self._components)

    async def fetch_message(
        self, channel: bases.Hashable[_channels.Channel], message: bases.Hashable[_messages.Message],
    ) -> _messages.Message:
        """Get a message from known channel that we can access.

        Parameters
        ----------
        channel : typing.Union[hikari.channels.Channel, hikari.bases.Snowflake, int]
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
            channel_id=str(channel.id if isinstance(channel, bases.UniqueEntity) else int(channel)),
            message_id=str(message.id if isinstance(message, bases.UniqueEntity) else int(message)),
        )
        return _messages.Message.deserialize(payload, components=self._components)

    async def create_message(
        self,
        channel: bases.Hashable[_channels.Channel],
        *,
        content: str = ...,
        nonce: str = ...,
        tts: bool = ...,
        files: typing.Sequence[_files.File] = ...,
        embed: _embeds.Embed = ...,
        mentions_everyone: bool = True,
        user_mentions: typing.Union[typing.Collection[bases.Hashable[users.User]], bool] = True,
        role_mentions: typing.Union[typing.Collection[bases.Hashable[guilds.GuildRole]], bool] = True,
    ) -> _messages.Message:
        """Create a message in the given channel.

        Parameters
        ----------
        channel : typing.Union[hikari.channels.Channel, hikari.bases.Snowflake, int]
            The channel or ID of the channel to send to.
        content : str
            If specified, the message content to send with the message.
        nonce : str
            If specified, an optional ID to send for opportunistic message
            creation. This doesn't serve any real purpose for general use,
            and can usually be ignored.
        tts : bool
            If specified, whether the message will be sent as a TTS message.
        files : typing.Sequence[hikari.files.File]
            If specified, a sequence of files to upload, if desired. Should be
            between 1 and 10 objects in size (inclusive), also including embed
            attachments.
        embed : hikari.embeds.Embed
            If specified, the embed object to send with the message.
        mentions_everyone : bool
            Whether `@everyone` and `@here` mentions should be resolved by
            discord and lead to actual pings, defaults to `True`.
        user_mentions : typing.Collection[typing.Union[hikari.users.User, hikari.bases.Snowflake, int]] OR bool
            Either an array of user objects/IDs to allow mentions for,
            `True` to allow all user mentions or `False` to block all
            user mentions from resolving, defaults to `True`.
        role_mentions: typing.Collection[typing.Union[hikari.guilds.GuildRole, hikari.bases.Snowflake, int]] OR bool
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
            channel_id=str(channel.id if isinstance(channel, bases.UniqueEntity) else int(channel)),
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
        channel: bases.Hashable[_channels.Channel],
        *,
        content: str = ...,
        nonce: str = ...,
        tts: bool = ...,
        files: typing.Sequence[_files.File] = ...,
        embed: _embeds.Embed = ...,
        mentions_everyone: bool = False,
        user_mentions: typing.Union[typing.Collection[bases.Hashable[users.User]], bool] = False,
        role_mentions: typing.Union[typing.Collection[bases.Hashable[guilds.GuildRole]], bool] = False,
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
        channel : typing.Union[hikari.channels.Channel, hikari.bases.Snowflake, int]
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
        user_mentions: typing.Collection[typing.Union[hikari.users.User, hikari.bases.Snowflake, int]] OR bool
            Either an array of user objects/IDs to allow mentions for,
            `True` to allow all user mentions or `False` to block all
            user mentions from resolving, defaults to `True`.
        role_mentions: typing.Collection[typing.Union[hikari.guilds.GuildRole, hikari.bases.Snowflake, int]] bool
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
            channel_id=str(channel.id if isinstance(channel, bases.UniqueEntity) else int(channel)),
            message_id=str(message.id if isinstance(message, bases.UniqueEntity) else int(message)),
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
        channel: bases.Hashable[_channels.Channel],
        message: bases.Hashable[_messages.Message],
        *additional_messages: bases.Hashable[_messages.Message],
    ) -> None:
        """Delete a message in a given channel.

        Parameters
        ----------
        channel : typing.Union[hikari.channels.Channel, hikari.bases.Snowflake, int]
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

    # pylint: disable=line-too-long
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
        channel : typing.Union[hikari.channels.Channel, hikari.bases.Snowflake, int]
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
            channel_id=str(channel.id if isinstance(channel, bases.UniqueEntity) else int(channel))
        )
        return [invites.InviteWithMetadata.deserialize(invite, components=self._components) for invite in payload]

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
        return invites.InviteWithMetadata.deserialize(payload, components=self._components)

    # pylint: disable=line-too-long
    async def delete_channel_overwrite(
        self,
        channel: bases.Hashable[_channels.Channel],
        overwrite: typing.Union[_channels.PermissionOverwrite, guilds.GuildRole, users.User, bases.Snowflake, int],
    ) -> None:
        """Delete a channel permission overwrite for a user or a role.

        Parameters
        ----------
        channel : typing.Union[hikari.channels.Channel, hikari.bases.Snowflake, int]
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
            channel_id=str(channel.id if isinstance(channel, bases.UniqueEntity) else int(channel)),
            overwrite_id=str(overwrite.id if isinstance(overwrite, bases.UniqueEntity) else int(overwrite)),
        )

    async def trigger_typing(self, channel: bases.Hashable[_channels.Channel]) -> None:
        """Trigger the typing indicator for `10` seconds in a channel.

        Parameters
        ----------
        channel : typing.Union[hikari.channels.Channel, hikari.bases.Snowflake, int]
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
            channel_id=str(channel.id if isinstance(channel, bases.UniqueEntity) else int(channel))
        )

    async def fetch_pins(
        self, channel: bases.Hashable[_channels.Channel]
    ) -> typing.Mapping[bases.Snowflake, _messages.Message]:
        """Get pinned messages for a given channel.

        Parameters
        ----------
        channel : typing.Union[hikari.channels.Channel, hikari.bases.Snowflake, int]
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
            channel_id=str(channel.id if isinstance(channel, bases.UniqueEntity) else int(channel))
        )
        return {
            bases.Snowflake(message["id"]): _messages.Message.deserialize(message, components=self._components)
            for message in payload
        }

    async def pin_message(
        self, channel: bases.Hashable[_channels.Channel], message: bases.Hashable[_messages.Message],
    ) -> None:
        """Add a pinned message to the channel.

        Parameters
        ----------
        channel : typing.Union[hikari.channels.Channel, hikari.bases.Snowflake, int]
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
        channel : typing.Union[hikari.channels.Channel, hikari.bases.Snowflake, int]
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
            channel_id=str(channel.id if isinstance(channel, bases.UniqueEntity) else int(channel)),
            message_id=str(message.id if isinstance(message, bases.UniqueEntity) else int(message)),
        )

    async def create_webhook(
        self,
        channel: bases.Hashable[_channels.GuildChannel],
        name: str,
        *,
        avatar: _files.File = ...,
        reason: str = ...,
    ) -> webhooks.Webhook:
        """Create a webhook for a given channel.

        Parameters
        ----------
        channel : typing.Union[hikari.channels.GuildChannel, hikari.bases.Snowflake, int]
            The object or ID of the channel for webhook to be created in.
        name : str
            The webhook's name string.
        avatar : hikari.files.File
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
            channel_id=str(channel.id if isinstance(channel, bases.UniqueEntity) else int(channel)),
            name=name,
            avatar=await avatar.read_all() if avatar is not ... else ...,
            reason=reason,
        )
        return webhooks.Webhook.deserialize(payload, components=self._components)

    async def fetch_channel_webhooks(
        self, channel: bases.Hashable[_channels.GuildChannel]
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
            channel_id=str(channel.id if isinstance(channel, bases.UniqueEntity) else int(channel))
        )
        return [webhooks.Webhook.deserialize(webhook, components=self._components) for webhook in payload]
