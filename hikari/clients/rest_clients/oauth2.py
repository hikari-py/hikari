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
"""The logic for handling all requests to oauth2 endpoints."""

__all__ = ["RESTOAuth2Component"]

import abc

from hikari import applications
from hikari.clients.rest_clients import base


class RESTOAuth2Component(base.BaseRESTComponent, abc.ABC):  # pylint: disable=W0223
    """The REST client component for handling requests to oauth2 endpoints."""

    async def fetch_my_application_info(self) -> applications.Application:
        """Get the current application information.

        Returns
        -------
        :obj:`~hikari.oauth2.Application`
            An application info object.
        """
        payload = await self._session.get_current_application_info()
        return applications.Application.deserialize(payload)
