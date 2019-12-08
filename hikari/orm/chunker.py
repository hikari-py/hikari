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
"""
Chunking management.

A chunker is a callable object that can consume incoming chunk payloads and
manage dispatching the parsed results to the state registry in the correct
place.
"""
from __future__ import annotations

import abc
import typing

from hikari.internal_utilities import data_structures
from hikari.orm.models import guilds


class IChunker(abc.ABC):
    """
    Abstract interface for a chunker that handles member chunks.
    """

    __slots__ = ()

    @abc.abstractmethod
    def load_members_for(
        self,
        guild_obj: guilds.Guild,
        *guild_objs: guilds.Guild,
        limit: int = 0,
        presences: bool = True,
        query: str = None,
        user_ids: typing.Optional[typing.Sequence[int]] = None,
    ) -> None:
        """
        Request chunks for the given guilds.

        Args:
            guild_obj:
                The first guild object to request member chunks for.
            guild_objs:
                Zero or more additional guilds to request member chunks for.
            limit:
                Optional limit to the number of members to send that match the
                criteria.
            presences:
                If `True`, then presence data is sent as well for each member.
                If `False`, then it is omitted.
            query:
                Look only for members who have a username beginning with this string
                if specified.
            user_ids:
                If specified and not empty, only find users who have an ID
                in the given sequence.

        Warning:
            Specifying both a query and user_ids is not supported and will raise
            a :class:`RuntimeError`.
        """

    @abc.abstractmethod
    async def handle_next_chunk(self, chunk_payload: data_structures.DiscordObjectT, shard_id: int) -> None:
        """
        Handle a new chunk from the gateway.

        Args:
            chunk_payload:
                The received payload.
            shard_id:
                The shard that received the payload.
        """

    @abc.abstractmethod
    async def close(self):
        """Close the chunker safely (kill any tasks running) if applicable."""
