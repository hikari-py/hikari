# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Component that provides the ability manage guild chunking."""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = ["GuildChunker"]

import abc
import typing

if typing.TYPE_CHECKING:
    from hikari import guilds


class GuildChunker(abc.ABC):
    """Component specialization that is used to manage guild chunking."""

    __slots__: typing.Sequence[str] = ()

    @abc.abstractmethod
    async def request_guild_chunk(self, guild: guilds.GatewayGuild) -> None:
        """Request for a guild chunk.

        Parameters
        ----------
        guild: hikari.guilds.Guild
            The guild to request chunk for.
        """

    def close(self) -> None:
        """Close the guild chunker."""
