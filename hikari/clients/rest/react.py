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
"""Logic for handling all requests to reaction endpoints."""

__all__ = ["RESTReactionComponent"]

import abc
import datetime
import typing

from hikari import bases
from hikari import channels as _channels
from hikari import emojis
from hikari import messages as _messages
from hikari import users
from hikari.clients.rest import base
from hikari.internal import helpers


class RESTReactionComponent(base.BaseRESTComponent, abc.ABC):  # pylint: disable=abstract-method
    """The REST client component for handling requests to reaction endpoints."""

    async def create_reaction(
        self,
        channel: bases.Hashable[_channels.Channel],
        message: bases.Hashable[_messages.Message],
        emoji: typing.Union[emojis.Emoji, str],
    ) -> None:
        """Add a reaction to the given message in the given channel.

        Parameters
        ----------
        channel : typing.Union[hikari.channels.Channel, hikari.bases.Snowflake, int]
            The object or ID of the channel to add this reaction in.
        message : typing.Union[hikari.messages.Message, hikari.bases.Snowflake, int]
            The object or ID of the message to add the reaction in.
        emoji : typing.Union[hikari.emojis.Emoji, str]
            The emoji to add. This can either be an emoji object or a string
            representation of an emoji. The string representation will be either
            `"name:id"` for custom emojis else it's unicode character(s)  (can
            be UTF-32).

        Raises
        ------
        hikari.errors.ForbiddenHTTPError
            If this is the first reaction using this specific emoji on this
            message and you lack the `ADD_REACTIONS` permission. If you lack
            `READ_MESSAGE_HISTORY`, this may also raise this error.
        hikari.errors.NotFoundHTTPError
            If the channel or message is not found, or if the emoji is not found.
        hikari.errors.BadRequestHTTPError
            If the emoji is not valid, unknown, or formatted incorrectly.
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        """
        await self._session.create_reaction(
            channel_id=str(channel.id if isinstance(channel, bases.UniqueEntity) else int(channel)),
            message_id=str(message.id if isinstance(message, bases.UniqueEntity) else int(message)),
            emoji=str(getattr(emoji, "url_name", emoji)),
        )

    async def delete_reaction(
        self,
        channel: bases.Hashable[_channels.Channel],
        message: bases.Hashable[_messages.Message],
        emoji: typing.Union[emojis.Emoji, str],
    ) -> None:
        """Remove your own reaction from the given message in the given channel.

        Parameters
        ----------
        channel : typing.Union[hikari.channels.Channel, hikari.bases.Snowflake, int]
            The object or ID of the channel to add this reaction in.
        message : typing.Union[hikari.messages.Message, hikari.bases.Snowflake, int]
            The object or ID of the message to add the reaction in.
        emoji : typing.Union[hikari.emojis.Emoji, str]
            The emoji to add. This can either be an emoji object or a
            string representation of an emoji. The string representation will be
            either `"name:id"` for custom emojis else it's unicode
            character(s) (can be UTF-32).

        Raises
        ------
        hikari.errors.ForbiddenHTTPError
            If this is the first reaction using this specific emoji on this
            message and you lack the `ADD_REACTIONS` permission. If you lack
            `READ_MESSAGE_HISTORY`, this may also raise this error.
        hikari.errors.NotFoundHTTPError
            If the channel or message is not found, or if the emoji is not
            found.
        hikari.errors.BadRequestHTTPError
            If the emoji is not valid, unknown, or formatted incorrectly.
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        """
        await self._session.delete_own_reaction(
            channel_id=str(channel.id if isinstance(channel, bases.UniqueEntity) else int(channel)),
            message_id=str(message.id if isinstance(message, bases.UniqueEntity) else int(message)),
            emoji=str(getattr(emoji, "url_name", emoji)),
        )

    async def delete_all_reactions(
        self, channel: bases.Hashable[_channels.Channel], message: bases.Hashable[_messages.Message],
    ) -> None:
        """Delete all reactions from a given message in a given channel.

        Parameters
        ----------
        channel : typing.Union[hikari.channels.Channel, hikari.bases.Snowflake, int]
            The object or ID of the channel to get the message from.
        message : typing.Union[hikari.messages.Message, hikari.bases.Snowflake, int]
            The object or ID of the message to remove all reactions from.

        Raises
        ------
        hikari.errors.BadRequestHTTPError
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        hikari.errors.NotFoundHTTPError
            If the channel or message is not found.
        hikari.errors.ForbiddenHTTPError
            If you lack the `MANAGE_MESSAGES` permission.
        """
        await self._session.delete_all_reactions(
            channel_id=str(channel.id if isinstance(channel, bases.UniqueEntity) else int(channel)),
            message_id=str(message.id if isinstance(message, bases.UniqueEntity) else int(message)),
        )

    async def delete_all_reactions_for_emoji(
        self,
        channel: bases.Hashable[_channels.Channel],
        message: bases.Hashable[_messages.Message],
        emoji: typing.Union[emojis.Emoji, str],
    ) -> None:
        """Remove all reactions for a single given emoji on a given message.

        Parameters
        ----------
        channel : typing.Union[hikari.channels.Channel, hikari.bases.Snowflake, int]
            The object or ID of the channel to get the message from.
        message : typing.Union[hikari.messages.Message, hikari.bases.Snowflake, int]
            The object or ID of the message to delete the reactions from.
        emoji : typing.Union[hikari.emojis.Emoji, str]
            The object or string representation of the emoji to delete. The
            string representation will be either `"name:id"` for custom emojis
            else it's unicode character(s) (can be UTF-32).

        Raises
        ------
        hikari.errors.BadRequestHTTPError
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        hikari.errors.NotFoundHTTPError
            If the channel or message or emoji or user is not found.
        hikari.errors.ForbiddenHTTPError
            If you lack the `MANAGE_MESSAGES` permission, or the channel is a
            DM channel.
        """
        await self._session.delete_all_reactions_for_emoji(
            channel_id=str(channel.id if isinstance(channel, bases.UniqueEntity) else int(channel)),
            message_id=str(message.id if isinstance(message, bases.UniqueEntity) else int(message)),
            emoji=str(getattr(emoji, "url_name", emoji)),
        )

    def fetch_reactors_after(
        self,
        channel: bases.Hashable[_channels.Channel],
        message: bases.Hashable[_messages.Message],
        emoji: typing.Union[emojis.Emoji, str],
        *,
        after: typing.Union[datetime.datetime, bases.Hashable[users.User]] = 0,
        limit: typing.Optional[int] = None,
    ) -> typing.AsyncIterator[users.User]:
        """Get an async iterator of the users who reacted to a message.

        This returns the users created after a given user object/ID or from the
        oldest user who reacted.

        Parameters
        ----------
        channel : typing.Union[hikari.channels.Channel, hikari.bases.Snowflake, int]
            The object or ID of the channel to get the message from.
        message : typing.Union[hikari.messages.Message, hikari.bases.Snowflake, int]
            The object or ID of the message to get the reactions from.
        emoji : typing.Union[hikari.emojis.Emoji, str]
            The emoji to get. This can either be it's object or the string
            representation of the emoji. The string representation will be
            either `"name:id"` for custom emojis else it's unicode
            character(s) (can be UTF-32).
        after : typing.Union[datetime.datetime, hikari.users.User, hikari.bases.Snowflake, int]
            If specified, a object or ID user. If specified, only users with a
            snowflake that is lexicographically greater than the value will be
            returned.
        limit : str
            If specified, the limit of the number of users this iterator should
            return.

        Examples
        --------
            async for user in client.fetch_reactors_after(channel, message, emoji, after=9876543, limit=1231):
                if user.is_bot:
                    await client.kick_member(channel.guild_id, user)

        Returns
        -------
        typing.AsyncIterator[hikari.users.User]
            An async iterator of user objects.

        Raises
        ------
        hikari.errors.BadRequestHTTPError
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        hikari.errors.ForbiddenHTTPError
            If you lack access to the message.
        hikari.errors.NotFoundHTTPError
            If the channel or message is not found.
        """
        if isinstance(after, datetime.datetime):
            after = str(bases.Snowflake.from_datetime(after))
        else:
            after = str(after.id if isinstance(after, bases.UniqueEntity) else int(after))
        return helpers.pagination_handler(
            channel_id=str(channel.id if isinstance(channel, bases.UniqueEntity) else int(channel)),
            message_id=str(message.id if isinstance(message, bases.UniqueEntity) else int(message)),
            emoji=getattr(emoji, "url_name", emoji),
            deserializer=users.User.deserialize,
            direction="after",
            request=self._session.get_reactions,
            reversing=False,
            start=after,
            limit=limit,
        )
