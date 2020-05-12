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

from __future__ import annotations

__all__ = ["RESTReactionComponent"]

import abc
import datetime
import typing

from hikari import bases
from hikari import pagination
from hikari import users
from hikari import messages as _messages
from hikari.clients.rest import base

if typing.TYPE_CHECKING:
    from hikari import channels as _channels
    from hikari import emojis


class _ReactionPaginator(pagination.BufferedPaginatedResults[_messages.Reaction]):
    __slots__ = ("_channel_id", "_message_id", "_first_id", "_emoji", "_components", "_session")

    def __init__(self, channel, message, emoji, users_after, components, session) -> None:
        super().__init__()
        self._channel_id = str(int(channel))
        self._message_id = str(int(message))
        self._emoji = getattr(emoji, "url_name", emoji)
        self._first_id = self._prepare_first_id(users_after)
        self._components = components
        self._session = session

    async def _next_chunk(self):
        chunk = await self._session.get_reactions(
            channel_id=self._channel_id, message_id=self._message_id, emoji=self._emoji, after=self._first_id
        )

        if not chunk:
            return None

        self._first_id = chunk[-1]["id"]

        return (users.User.deserialize(u, components=self._components) for u in chunk)


class RESTReactionComponent(base.BaseRESTComponent, abc.ABC):  # pylint: disable=abstract-method
    """The REST client component for handling requests to reaction endpoints."""

    async def add_reaction(
        self,
        channel: typing.Union[bases.Snowflake, int, str, _channels.PartialChannel],
        message: typing.Union[bases.Snowflake, int, str, _messages.Message],
        emoji: typing.Union[emojis.Emoji, str],
    ) -> None:
        """Add a reaction to the given message in the given channel.

        Parameters
        ----------
        channel : typing.Union[hikari.channels.PartialChannel, hikari.bases.Snowflake, int]
            The object or ID of the channel to add this reaction in.
        message : typing.Union[hikari.messages.Message, hikari.bases.Snowflake, int]
            The object or ID of the message to add the reaction in.
        emoji : typing.Union[hikari.emojis.Emoji, str]
            The emoji to add. This can either be an emoji object or a string
            representation of an emoji. The string representation will be either
            `"name:id"` for custom emojis, or it's unicode character(s) for
            standard emojis.

        Raises
        ------
        hikari.errors.Forbidden
            If this is the first reaction using this specific emoji on this
            message and you lack the `ADD_REACTIONS` permission. If you lack
            `READ_MESSAGE_HISTORY`, this may also raise this error.
        hikari.errors.NotFound
            If the channel or message is not found, or if the emoji is not found.
        hikari.errors.BadRequest
            If the emoji is invalid, unknown, or formatted incorrectly.
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        """
        await self._session.create_reaction(
            channel_id=str(channel.id if isinstance(channel, bases.Unique) else int(channel)),
            message_id=str(message.id if isinstance(message, bases.Unique) else int(message)),
            emoji=str(getattr(emoji, "url_name", emoji)),
        )

    async def remove_reaction(
        self,
        channel: typing.Union[bases.Snowflake, int, str, _channels.PartialChannel],
        message: typing.Union[bases.Snowflake, int, str, _messages.Message],
        emoji: typing.Union[emojis.Emoji, str],
        *,
        user: typing.Optional[typing.Hashable[users.User]] = None,
    ) -> None:
        """Remove a given reaction from a given message in a given channel.

        If the user is `None`, then the bot's own reaction is removed, otherwise
        the given user's reaction is removed instead.

        Parameters
        ----------
        channel : typing.Union[hikari.channels.PartialChannel, hikari.bases.Snowflake, int]
            The object or ID of the channel to add this reaction in.
        message : typing.Union[hikari.messages.Message, hikari.bases.Snowflake, int]
            The object or ID of the message to add the reaction in.
        emoji : typing.Union[hikari.emojis.Emoji, str]
            The emoji to add. This can either be an emoji object or a
            string representation of an emoji. The string representation will be
            either `"name:id"` for custom emojis else it's unicode
            character(s) (can be UTF-32).
        user : typing.Union[hikari.users.User, hikari.bases.Snowflake, int], optional
            The user to remove the reaction of. If this is `None`, then the
            bot's own reaction is removed instead.

        Raises
        ------
        hikari.errors.Forbidden
            If this is the first reaction using this specific emoji on this
            message and you lack the `ADD_REACTIONS` permission. If you lack
            `READ_MESSAGE_HISTORY`, this may also raise this error.
            If the `user` is not `None` and the bot lacks permissions to
            modify other user's reactions, this will also be raised.
        hikari.errors.NotFound
            If the channel or message is not found, or if the emoji is not
            found.
        hikari.errors.BadRequest
            If the emoji is not valid, unknown, or formatted incorrectly.
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        """
        if user is None:
            await self._session.delete_own_reaction(
                channel_id=str(channel.id if isinstance(channel, bases.Unique) else int(channel)),
                message_id=str(message.id if isinstance(message, bases.Unique) else int(message)),
                emoji=str(getattr(emoji, "url_name", emoji)),
            )
        else:
            await self._session.delete_user_reaction(
                channel_id=str(channel.id if isinstance(channel, bases.Unique) else int(channel)),
                message_id=str(message.id if isinstance(message, bases.Unique) else int(message)),
                emoji=str(getattr(emoji, "url_name", emoji)),
                user_id=str(user.id if isinstance(user, bases.Unique) else int(user)),
            )

    async def remove_all_reactions(
        self,
        channel: typing.Union[bases.Snowflake, int, str, _channels.PartialChannel],
        message: typing.Union[bases.Snowflake, int, str, _messages.Message],
        *,
        emoji: typing.Optional[typing.Union[emojis.Emoji, str]] = None,
    ) -> None:
        """Remove all reactions for a single given emoji on a given message.

        Parameters
        ----------
        channel : typing.Union[hikari.channels.PartialChannel, hikari.bases.Snowflake, int]
            The object or ID of the channel to get the message from.
        message : typing.Union[hikari.messages.Message, hikari.bases.Snowflake, int]
            The object or ID of the message to delete the reactions from.
        emoji : typing.Union[hikari.emojis.Emoji, str], optional
            The object or string representation of the emoji to delete. The
            string representation will be either `"name:id"` for custom emojis
            else it's unicode character(s) (can be UTF-32).
            If `None` or unspecified, then all reactions are removed.

        Raises
        ------
        hikari.errors.BadRequest
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        hikari.errors.NotFound
            If the channel or message or emoji or user is not found.
        hikari.errors.Forbidden
            If you lack the `MANAGE_MESSAGES` permission, or the channel is a
            DM channel.
        """
        if emoji is None:
            await self._session.delete_all_reactions(
                channel_id=str(channel.id if isinstance(channel, bases.Unique) else int(channel)),
                message_id=str(message.id if isinstance(message, bases.Unique) else int(message)),
            )
        else:
            await self._session.delete_all_reactions_for_emoji(
                channel_id=str(channel.id if isinstance(channel, bases.Unique) else int(channel)),
                message_id=str(message.id if isinstance(message, bases.Unique) else int(message)),
                emoji=str(getattr(emoji, "url_name", emoji)),
            )

    def fetch_reactors(
        self,
        channel: typing.Union[bases.Snowflake, int, str, _channels.PartialChannel],
        message: typing.Union[bases.Snowflake, int, str, _messages.Message],
        emoji: typing.Union[emojis.Emoji, str],
        after: typing.Optional[typing.Union[datetime.datetime, bases.Unique, bases.Snowflake, int, str]] = None,
    ) -> pagination.PaginatedResults[users.User]:
        """Get an async iterator of the users who reacted to a message.

        This returns the users created after a given user object/ID or from the
        oldest user who reacted.

        Parameters
        ----------
        channel : typing.Union[hikari.channels.PartialChannel, hikari.bases.Snowflake, int]
            The object or ID of the channel to get the message from.
        message : typing.Union[hikari.messages.Message, hikari.bases.Snowflake, int]
            The object or ID of the message to get the reactions from.
        emoji : typing.Union[hikari.emojis.Emoji, str]
            The emoji to get. This can either be it's object or the string
            representation of the emoji. The string representation will be
            either `"name:id"` for custom emojis else it's unicode
            character(s) (can be UTF-32).
        after : datetime.datetime OR hikari.bases.Unique OR hikari.bases.Snowflake OR int OR str, optional
            A limit to the users returned. This allows you to only receive
            users that were created after the given object, if desired.
            If a snowflake/int/str/unique object, then this will use the
            corresponding user creation date. If a datetime, the date will
            be the limit. If unspecified/None, per the default, then all
            valid users will be returned instead.

        Examples
        --------
            async for user in client.fetch_reactors_after(channel, message, emoji):
                if user.is_bot:
                    await client.kick_member(channel.guild_id, user)

        Returns
        -------
        hikari.pagination.PaginatedResults[hikari.users.User]
            An async iterator of user objects.

        Raises
        ------
        hikari.errors.BadRequest
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        hikari.errors.Forbidden
            If you lack access to the message.
        hikari.errors.NotFound
            If the channel or message is not found.
        """
        return _ReactionPaginator(
            channel=channel,
            message=message,
            emoji=emoji,
            users_after=after,
            components=self._components,
            session=self._session,
        )
