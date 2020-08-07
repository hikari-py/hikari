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
"""Component that provides the ability manage guild chunking."""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = ["IGuildChunkerComponent"]

import abc
import typing

from hikari.api import component

if typing.TYPE_CHECKING:
    from hikari.models import guilds


class IGuildChunkerComponent(component.IComponent, abc.ABC):
    """Component specialization that is used to manage guild chunking."""

    __slots__: typing.Sequence[str] = ()

    @abc.abstractmethod
    async def request_guild_chunk(self, guild: guilds.Guild, shard_id: int) -> None:
        """Request for a guild chunk.

        Parameters
        ----------
        guild: hikari.models.guilds.Guild
            The guild to request chunk for.
        """

    def close(self) -> None:
        """Close the guild chunker."""
