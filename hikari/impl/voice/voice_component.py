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
"""Implementation of a simple voice management system."""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = []

import asyncio

# noinspection PyUnresolvedReferences
import logging
import typing

from hikari.api import voice
from hikari.api.rest import app as rest_app
from hikari.models import channels
from hikari.utilities import snowflake

_LOGGER: typing.Final[logging.Logger] = logging.getLogger("hikari.voice.management")


class VoiceComponentImpl(voice.IVoiceComponent):
    """A standard voice component management implementation.

    This is the regular implementation you will generally use to connect to
    voice channels with.
    """

    __slots__ = ("_app", "_connections")

    def __init__(self, app: rest_app.IRESTApp) -> None:
        self._app = app
        self._connections: typing.Dict[snowflake.Snowflake, voice.IVoiceConnection] = {}

    @property
    def app(self) -> rest_app.IRESTApp:
        return self._app

    @property
    def connections(self) -> typing.Mapping[snowflake.Snowflake, voice.IVoiceConnection]:
        return self._connections.copy()

    async def close(self) -> None:
        if self._connections:
            _LOGGER.info("shutting down %s voice connection(s)", len(self._connections))
            await asyncio.gather(*(c.disconnect() for c in self._connections.values()))

    async def connect_to(
        self,
        channel: channels.GuildVoiceChannel,
        *,
        deaf: bool = False,
        mute: bool = False,
        voice_connection_type: typing.Type[voice.IVoiceConnection],
        **kwargs: typing.Any,
    ) -> voice.IVoiceConnection:
        pass
