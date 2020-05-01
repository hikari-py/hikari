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
"""The logic for handling requests to invite endpoints."""

from __future__ import annotations

__all__ = ["RESTInviteComponent"]

import abc
import typing

from hikari import invites
from hikari.clients.rest import base


class RESTInviteComponent(base.BaseRESTComponent, abc.ABC):  # pylint: disable=abstract-method
    """The REST client component for handling requests to invite endpoints."""

    async def fetch_invite(
        self, invite: typing.Union[invites.Invite, str], *, with_counts: bool = ...
    ) -> invites.Invite:
        """Get the given invite.

        Parameters
        ----------
        invite : typing.Union[hikari.invites.Invite, str]
            The object or code of the wanted invite.
        with_counts : bool
            If specified, whether to attempt to count the number of
            times the invite has been used.

        Returns
        -------
        hikari.invites.Invite
            The requested invite object.

        Raises
        ------
        hikari.errors.BadRequest
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        hikari.errors.NotFound
            If the invite is not found.
        """
        payload = await self._session.get_invite(invite_code=getattr(invite, "code", invite), with_counts=with_counts)
        return invites.Invite.deserialize(payload, components=self._components)

    async def delete_invite(self, invite: typing.Union[invites.Invite, str]) -> None:
        """Delete a given invite.

        Parameters
        ----------
        invite : typing.Union[hikari.invites.Invite, str]
            The object or ID for the invite to be deleted.

        Returns
        -------
        None
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
        await self._session.delete_invite(invite_code=getattr(invite, "code", invite))
