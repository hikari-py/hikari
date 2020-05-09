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
"""The logic for handling all requests to user endpoints."""

from __future__ import annotations

__all__ = ["RESTUserComponent"]

import abc
import typing

from hikari import bases
from hikari import users
from hikari.clients.rest import base


class RESTUserComponent(base.BaseRESTComponent, abc.ABC):  # pylint: disable=abstract-method
    """The REST client component for handling requests to user endpoints."""

    async def fetch_user(self, user: typing.Union[bases.Snowflake, int, str, users.User]) -> users.User:
        """Get a given user.

        Parameters
        ----------
        user : typing.Union[hikari.users.User, hikari.bases.Snowflake, int]
            The object or ID of the user to get.

        Returns
        -------
        hikari.users.User
            The requested user object.

        Raises
        ------
        hikari.errors.BadRequest
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        hikari.errors.NotFound
            If the user is not found.
        """
        payload = await self._session.get_user(user_id=str(user.id if isinstance(user, bases.Unique) else int(user)))
        return users.User.deserialize(payload, components=self._components)
