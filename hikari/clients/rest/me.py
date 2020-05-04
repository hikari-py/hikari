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
import functools
import typing

from hikari import applications
from hikari import bases
from hikari import channels as _channels
from hikari import users
from hikari.clients.rest import base
from hikari.internal import helpers

if typing.TYPE_CHECKING:
    from hikari import guilds
    from hikari import files


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
            username=username, avatar=await avatar.read_all() if avatar is not ... else ...,
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

    def fetch_my_guilds_after(
        self,
        *,
        after: typing.Union[datetime.datetime, bases.Hashable[guilds.Guild]] = 0,
        limit: typing.Optional[int] = None,
    ) -> typing.AsyncIterator[applications.OwnGuild]:
        """Get an async iterator of the guilds the current user is in.

        This returns the guilds created after a given guild object/ID or from
        the oldest guild.

        Parameters
        ----------
        after : typing.Union[datetime.datetime, hikari.guilds.Guild, hikari.bases.Snowflake, int]
            The object or ID of a guild to get guilds that were created after
            it if specified, else this will start at the oldest guild.
        limit : int
            If specified, the maximum amount of guilds that this paginator
            should return.

        Examples
        --------
            async for user in client.fetch_my_guilds_after(after=9876543, limit=1231):
                await client.leave_guild(guild)

        Returns
        -------
        typing.AsyncIterator[hikari.applications.OwnGuild]
            An async iterator of partial guild objects.

        Raises
        ------
        hikari.errors.NotFound
            If the guild is not found.
        hikari.errors.BadRequest
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        """
        if isinstance(after, datetime.datetime):
            after = str(bases.Snowflake.from_datetime(after))
        else:
            after = str(after.id if isinstance(after, bases.UniqueEntity) else int(after))
        deserializer = functools.partial(applications.OwnGuild.deserialize, components=self._components)
        return helpers.pagination_handler(
            deserializer=deserializer,
            direction="after",
            request=self._session.get_current_user_guilds,
            reversing=False,
            start=after,
            maximum_limit=100,
            limit=limit,
        )

    def fetch_my_guilds_before(
        self,
        *,
        before: typing.Union[datetime.datetime, bases.Hashable[guilds.Guild]] = bases.Snowflake.max(),
        limit: typing.Optional[int] = None,
    ) -> typing.AsyncIterator[applications.OwnGuild]:
        """Get an async iterator of the guilds the current user is in.

        This returns the guilds that were created before a given user object/ID
        or from the newest guild.

        Parameters
        ----------
        before : typing.Union[datetime.datetime, hikari.guilds.Guild, hikari.bases.Snowflake, int]
            The object or ID of a guild to get guilds that were created
            before it if specified, else this will start at the newest guild.
        limit : int
            If specified, the maximum amount of guilds that this paginator
            should return.

        Returns
        -------
        typing.AsyncIterator[hikari.applications.OwnGuild]
            An async iterator of partial guild objects.

        Raises
        ------
        hikari.errors.NotFound
            If the guild is not found.
        hikari.errors.BadRequest
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        """
        if isinstance(before, datetime.datetime):
            before = str(bases.Snowflake.from_datetime(before))
        else:
            before = str(before.id if isinstance(before, bases.UniqueEntity) else int(before))
        deserializer = functools.partial(applications.OwnGuild.deserialize, components=self._components)
        return helpers.pagination_handler(
            deserializer=deserializer,
            direction="before",
            request=self._session.get_current_user_guilds,
            reversing=False,
            start=before,
            maximum_limit=100,
            limit=limit,
        )

    async def leave_guild(self, guild: bases.Hashable[guilds.Guild]) -> None:
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
        await self._session.leave_guild(guild_id=str(guild.id if isinstance(guild, bases.UniqueEntity) else int(guild)))

    async def create_dm_channel(self, recipient: bases.Hashable[users.User]) -> _channels.DMChannel:
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
            recipient_id=str(recipient.id if isinstance(recipient, bases.UniqueEntity) else int(recipient))
        )
        return _channels.DMChannel.deserialize(payload, components=self._components)
