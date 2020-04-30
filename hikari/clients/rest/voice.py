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
"""The logic for handling all requests to voice endpoints."""

from __future__ import annotations

__all__ = ["RESTVoiceComponent"]

import abc
import typing

from hikari import voices
from hikari.clients.rest import base


class RESTVoiceComponent(base.BaseRESTComponent, abc.ABC):  # pylint: disable=abstract-method
    """The REST client component for handling requests to voice endpoints."""

    async def fetch_voice_regions(self) -> typing.Sequence[voices.VoiceRegion]:
        """Get the voice regions that are available.

        Returns
        -------
        typing.Sequence[hikari.voices.VoiceRegion]
            A list of voice regions available

        !!! note
            This does not include VIP servers.
        """
        payload = await self._session.list_voice_regions()
        return [voices.VoiceRegion.deserialize(region, components=self._components) for region in payload]
