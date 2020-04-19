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
"""The logic for handling requests to ``@me`` endpoints."""

__all__ = ["RESTCurrentUserComponent"]

import abc
import datetime
import typing

from hikari import bases
from hikari import channels as _channels
from hikari import guilds
from hikari import oauth2
from hikari import users
from hikari.clients.rest_clients import component_base
from hikari.internal import conversions
from hikari.internal import pagination


class RESTCurrentUserComponent(component_base.BaseRESTComponent, abc.ABC):  # pylint: disable=W0223
    """The REST client component for handling requests to ``@me`` endpoints."""

    async def fetch_me(self) -> users.MyUser:
        """Get the current user that of the token given to the client.

        Returns
        -------
        :obj:`~hikari.users.MyUser`
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
        username : :obj:`~str`
            If specified, the new username string.
        avatar_data : ``hikari.internal.conversions.FileLikeT``, optional
            If specified, the new avatar image data.
            If it is :obj:`~None`, the avatar is removed.

        Returns
        -------
        :obj:`~hikari.users.MyUser`
            The updated user object.

        Raises
        ------
        :obj:`~hikari.errors.BadRequestHTTPError`
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
        :obj:`~typing.Sequence` [ :obj:`~hikari.oauth2.OwnConnection` ]
            A list of connection objects.
        """
        payload = await self._session.get_current_user_connections()
        return [oauth2.OwnConnection.deserialize(connection) for connection in payload]

    def fetch_my_guilds_after(
        self,
        *,
        after: typing.Union[datetime.datetime, bases.Hashable[guilds.Guild]] = 0,
        limit: typing.Optional[int] = None,
    ) -> typing.AsyncIterator[oauth2.OwnGuild]:
        """Get an async iterator of the guilds the current user is in.

        This returns the guilds created after a given guild object/ID or from
        the oldest guild.

        Parameters
        ----------
        after : :obj:`~typing.Union` [ :obj:`~datetime.datetime`, :obj:`~hikari.guilds.Guild`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of a guild to get guilds that were created after
            it if specified, else this will start at the oldest guild.
        limit : :obj:`~int`
            If specified, the maximum amount of guilds that this paginator
            should return.

        Example
        -------
        .. code-block:: python

            async for user in client.fetch_my_guilds_after(after=9876543, limit=1231):
                await client.leave_guild(guild)

        Returns
        -------
        :obj:`~typing.AsyncIterator` [ :obj:`~hikari.oauth2.OwnGuild` ]
            An async iterator of partial guild objects.

        Raises
        ------
        :obj:`~hikari.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`~hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        """
        if isinstance(after, datetime.datetime):
            after = str(bases.Snowflake.from_datetime(after))
        else:
            after = str(after.id if isinstance(after, bases.UniqueEntity) else int(after))
        return pagination.pagination_handler(
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
        before: typing.Union[datetime.datetime, bases.Hashable[guilds.Guild], None] = None,
        limit: typing.Optional[int] = None,
    ) -> typing.AsyncIterator[oauth2.OwnGuild]:
        """Get an async iterator of the guilds the current user is in.

        This returns the guilds that were created before a given user object/ID
        or from the newest guild.

        Parameters
        ----------
        before : :obj:`~typing.Union` [ :obj:`~datetime.datetime`, :obj:`~hikari.guilds.Guild`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of a guild to get guilds that were created
            before it if specified, else this will start at the newest guild.
        limit : :obj:`~int`
            If specified, the maximum amount of guilds that this paginator
            should return.

        Returns
        -------
        :obj:`~typing.AsyncIterator` [ :obj:`~hikari.oauth2.OwnGuild` ]
            An async iterator of partial guild objects.

        Raises
        ------
        :obj:`~hikari.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`~hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        """
        if isinstance(before, datetime.datetime):
            before = str(bases.Snowflake.from_datetime(before))
        elif before is not None:
            before = str(before.id if isinstance(before, bases.UniqueEntity) else int(before))
        return pagination.pagination_handler(
            deserializer=oauth2.OwnGuild.deserialize,
            direction="before",
            request=self._session.get_current_user_guilds,
            reversing=False,
            start=before,
            limit=limit,
        )

    async def leave_guild(self, guild: bases.Hashable[guilds.Guild]) -> None:
        """Make the current user leave a given guild.

        Parameters
        ----------
        guild : :obj:`~typing.Union` [ :obj:`~hikari.guilds.Guild`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the guild to leave.

        Raises
        ------
        :obj:`~hikari.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`~hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        """
        await self._session.leave_guild(guild_id=str(guild.id if isinstance(guild, bases.UniqueEntity) else int(guild)))

    async def create_dm_channel(self, recipient: bases.Hashable[users.User]) -> _channels.DMChannel:
        """Create a new DM channel with a given user.

        Parameters
        ----------
        recipient : :obj:`~typing.Union` [ :obj:`~hikari.users.User`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the user to create the new DM channel with.

        Returns
        -------
        :obj:`~hikari.channels.DMChannel`
            The newly created DM channel object.

        Raises
        ------
        :obj:`~hikari.errors.NotFoundHTTPError`
            If the recipient is not found.
        :obj:`~hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        """
        payload = await self._session.create_dm(
            recipient_id=str(recipient.id if isinstance(recipient, bases.UniqueEntity) else int(recipient))
        )
        return _channels.DMChannel.deserialize(payload)
