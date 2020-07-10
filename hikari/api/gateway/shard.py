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
"""Provides an interface for gateway shard implementations to conform to."""
from __future__ import annotations

__all__: typing.Final[typing.List[str]] = ["IGatewayShard"]

import abc
import typing

from hikari.api import component
from hikari.utilities import undefined

if typing.TYPE_CHECKING:
    import asyncio
    import datetime

    from hikari.models import channels
    from hikari.models import guilds
    from hikari.models import presences
    from hikari.utilities import snowflake


class IGatewayShard(component.IComponent, abc.ABC):
    """Interface for a definition of a V6/V7 compatible websocket gateway.

    Each instance should represent a single shard.
    """

    __slots__ = ()

    @property
    @abc.abstractmethod
    def is_alive(self) -> bool:
        """Return `builtins.True` if the shard is alive and connected."""

    @property
    @abc.abstractmethod
    def heartbeat_latency(self) -> float:
        """Return the shard's most recent heartbeat latency."""

    @abc.abstractmethod
    async def get_user_id(self) -> snowflake.Snowflake:
        """Return the user ID.

        If the shard has not connected fully yet, this should wait until the ID
        is set before returning.
        """

    @abc.abstractmethod
    async def start(self) -> asyncio.Task[None]:
        """Start the shard, wait for it to become ready.

        Returns
        -------
        asyncio.Task[builtins.None]
            The task containing the shard running logic. Awaiting this will
            wait until the shard has shut down before returning.
        """

    @abc.abstractmethod
    async def close(self) -> None:
        """Close the websocket if it is connected, otherwise do nothing."""

    @abc.abstractmethod
    async def update_presence(
        self,
        *,
        idle_since: typing.Union[undefined.UndefinedType, None, datetime.datetime] = undefined.UNDEFINED,
        afk: typing.Union[undefined.UndefinedType, bool] = undefined.UNDEFINED,
        activity: typing.Union[undefined.UndefinedType, None, presences.Activity] = undefined.UNDEFINED,
        status: typing.Union[undefined.UndefinedType, presences.Status] = undefined.UNDEFINED,
    ) -> None:
        """Update the presence of the shard user.

        Parameters
        ----------
        idle_since : datetime.datetime or builtins.None or hikari.utilities.undefined.UndefinedType
            The datetime that the user started being idle. If undefined, this
            will not be changed.
        afk : builtins.bool or hikari.utilities.undefined.UndefinedType
            If `builtins.True`, the user is marked as AFK. If `builtins.False`,
            the user is marked as being active. If undefined, this will not be
            changed.
        activity : hikari.models.presences.Activity or builtins.None or hikari.utilities.undefined.UndefinedType
            The activity to appear to be playing. If undefined, this will not be
            changed.
        status : hikari.models.presences.Status or hikari.utilities.undefined.UndefinedType
            The web status to show. If undefined, this will not be changed.
        """

    @abc.abstractmethod
    async def update_voice_state(
        self,
        guild: typing.Union[guilds.PartialGuild, snowflake.UniqueObject],
        channel: typing.Union[channels.GuildVoiceChannel, snowflake.UniqueObject, None],
        *,
        self_mute: bool = False,
        self_deaf: bool = False,
    ) -> None:
        """Update the voice state for this shard in a given guild.

        Parameters
        ----------
        guild : hikari.models.guilds.PartialGuild or hikari.utilities.snowflake.UniqueObject
            The guild or guild ID to update the voice state for.
        channel : hikari.models.channels.GuildVoiceChannel or hikari.utilities.snowflake.UniqueObject or builtins.None
            The channel or channel ID to update the voice state for. If `builtins.None`
            then the bot will leave the voice channel that it is in for the
            given guild.
        self_mute : builtins.bool
            If `builtins.True`, the bot will mute itself in that voice channel. If
            `builtins.False`, then it will unmute itself.
        self_deaf : builtins.bool
            If `builtins.True`, the bot will deafen itself in that voice channel. If
            `builtins.False`, then it will undeafen itself.
        """
