# -*- coding: utf-8 -*-
# cython: language_level=3
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
"""Basic implementation of a guild chunker."""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = ["StatelessGuildChunkerImpl"]

import typing

from hikari.api import guild_chunker

if typing.TYPE_CHECKING:
    from hikari.api import bot
    from hikari.models import guilds


class StatelessGuildChunkerImpl(guild_chunker.IGuildChunkerComponent):
    """Stateless guild chunker.

    A stateless guild chunker implementation that implements dummy operations
    for each of the required attributes of a functional guild chunker
    implementation. Any methods will always raise `builtins.NotImplemented`
    when being invoked.
    """

    __slots__: typing.Sequence[str] = ("_app")

    def __init__(self, app: bot.IBotApp) -> None:
        self._app = app

    @property
    @typing.final
    def app(self) -> bot.IBotApp:
        return self._app

    async def request_guild_chunk(self, guild: guilds.Guild, shard_id: int) -> None:
        raise NotImplementedError("This application is stateless, guild chunking operations are not implemented.")

    def close(self) -> None:
        return
