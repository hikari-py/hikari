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
"""The logic for handling requests to `@me` endpoints."""

from __future__ import annotations

__all__ = ["RESTCurrentUserComponent"]

import abc
import datetime
import typing

from hikari import applications
from hikari import bases
from hikari import channels as _channels
from hikari import guilds
from hikari import pagination
from hikari import users
from hikari.clients.rest import base

if typing.TYPE_CHECKING:
    from hikari import files


class _GuildPaginator(pagination.BufferedPaginatedResults[guilds.Guild]):
    __slots__ = ("_session", "_components", "_newest_first", "_first_id")

    def __init__(self, newest_first, first_item, components, session):
        super().__init__()
        self._newest_first = newest_first
        self._first_id = self._prepare_first_id(
            first_item, bases.Snowflake.max() if newest_first else bases.Snowflake.min(),
        )
        self._components = components
        self._session = session

    async def _next_chunk(self):
        kwargs = {"before" if self._newest_first else "after": self._first_id}

        chunk = await self._session.get_current_user_guilds(**kwargs)

        if not chunk:
            return None

        self._first_id = chunk[-1]["id"]

        return (applications.OwnGuild.deserialize(g, components=self._components) for g in chunk)


class RESTCurrentUserComponent(base.BaseRESTComponent, abc.ABC):  # pylint: disable=abstract-method
    """The REST client component for handling requests to `@me` endpoints."""

    async def fetch_me(self) -> users.MyUser:
        """Get the current user that of the token given to the client.

        Returns
        -------
        hikari.users.MyUser
            The current user object.
        """
        payload = await self._session.get_current_user()
        return users.MyUser.deserialize(payload, components=self._components)

    async def update_me(self, *, username: str = ..., avatar: typing.Optional[files.BaseStream] = ...) -> users.MyUser:
        """Edit the current user.

        Parameters
        ----------
        username : str
            If specified, the new username string.
        avatar : hikari.files.BaseStream, optional
            If specified, the new avatar image data.
            If it is None, the avatar is removed.

        !!! warning
            Verified bots will not be able to change their username on this
            endpoint, and should contact Discord support instead to change
            this value.

        Returns
        -------
        hikari.users.MyUser
            The updated user object.

        Raises
        ------
        hikari.errors.BadRequest
            If you pass username longer than the limit (`2-32`) or an invalid image.
        """
        payload = await self._session.modify_current_user(
            username=username, avatar=await avatar.read() if avatar is not ... else ...,
        )
        return users.MyUser.deserialize(payload, components=self._components)

    async def fetch_my_connections(self) -> typing.Sequence[applications.OwnConnection]:
        """
        Get the current user's connections.

        !!! note
            This endpoint can be used with both `Bearer` and `Bot` tokens but
            will usually return an empty list for bots (with there being some
            exceptions to this, like user accounts that have been converted to
            bots).

        Returns
        -------
        typing.Sequence[hikari.applications.OwnConnection]
            A list of connection objects.
        """
        payload = await self._session.get_current_user_connections()
        return [
            applications.OwnConnection.deserialize(connection, components=self._components) for connection in payload
        ]

    def fetch_my_guilds(
        self,
        *,
        newest_first: bool = False,
        start_at: typing.Optional[typing.Union[datetime.datetime, bases.Unique, bases.Snowflake, int]] = None,
    ) -> pagination.PaginatedResults[applications.OwnGuild]:
        """Get an async iterable of the guilds the current user is in.

        Parameters
        ----------
        newest_first : bool
            If specified and `True`, the guilds are returned in the order of
            newest to oldest. The default is to return oldest guilds first.
        start_at : datetime.datetime OR hikari.bases.UniqueEntity OR hikari.bases.Snowflake or int, optional
            The optional first item to start at, if you want to limit your
            results. This will be interpreted as the date of creation for a
            guild. If unspecified, the newest or older possible snowflake is
            used, for `newest_first` being `True` and `False` respectively.

        Returns
        -------
        hikari.pagination.PaginatedResults[hikari.applications.OwnGuild]
            An async iterable of partial guild objects.

        Raises
        ------
        hikari.errors.NotFound
            If the guild is not found.
        """
        return _GuildPaginator(
            newest_first=newest_first, first_item=start_at, components=self._components, session=self._session
        )

    async def leave_guild(self, guild: typing.Union[bases.Snowflake, int, str, guilds.Guild]) -> None:
        """Make the current user leave a given guild.

        Parameters
        ----------
        guild : typing.Union[hikari.guilds.Guild, hikari.bases.Snowflake, int]
            The object or ID of the guild to leave.

        Raises
        ------
        hikari.errors.NotFound
            If the guild is not found.
        hikari.errors.BadRequest
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        """
        await self._session.leave_guild(guild_id=str(guild.id if isinstance(guild, bases.Unique) else int(guild)))

    async def create_dm_channel(
        self, recipient: typing.Union[bases.Snowflake, int, str, users.User]
    ) -> _channels.DMChannel:
        """Create a new DM channel with a given user.

        Parameters
        ----------
        recipient : typing.Union[hikari.users.User, hikari.bases.Snowflake, int]
            The object or ID of the user to create the new DM channel with.

        Returns
        -------
        hikari.channels.DMChannel
            The newly created DM channel object.

        Raises
        ------
        hikari.errors.NotFound
            If the recipient is not found.
        hikari.errors.BadRequest
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        """
        payload = await self._session.create_dm(
            recipient_id=str(recipient.id if isinstance(recipient, bases.Unique) else int(recipient))
        )
        return _channels.DMChannel.deserialize(payload, components=self._components)
