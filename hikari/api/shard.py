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

__all__: typing.Final[typing.List[str]] = ["GatewayDataFormat", "GatewayCompression", "IGatewayShard"]

import abc
import enum
import typing

from hikari.api import component
from hikari.utilities import undefined

if typing.TYPE_CHECKING:
    import asyncio
    import datetime

    from hikari import config
    from hikari.models import channels
    from hikari.models import guilds
    from hikari.models import intents as intents_
    from hikari.models import presences
    from hikari.utilities import snowflake


@enum.unique
@typing.final
class GatewayDataFormat(str, enum.Enum):
    """Format of inbound gateway payloads."""

    JSON = "json"
    """Javascript serialized object notation."""
    ETF = "etf"
    """Erlang transmission format."""


@enum.unique
@typing.final
class GatewayCompression(str, enum.Enum):
    """Types of gateway compression that may be supported."""

    TRANSPORT_ZLIB_STREAM = "transport_zlib_stream"
    """Transport compression using ZLIB."""
    PAYLOAD_ZLIB_STREAM = "payload_zlib_stream"
    """Payload compression using ZLIB."""


class IGatewayShard(component.IComponent, abc.ABC):
    """Interface for a definition of a V6/V7 compatible websocket gateway.

    Each instance should represent a single shard.
    """

    __slots__ = ()

    @property
    @abc.abstractmethod
    def compression(self) -> typing.Optional[str]:
        """Return the compression being used.

        This may be one of `GatewayCompression`, or may be a custom
        format for custom implementations in the future.

        Returns
        -------
        builtins.str or builtins.None
            The name of the compression method being used. Will be
            `builtins.None` if no compression is being used.
        """

    @property
    @abc.abstractmethod
    def connection_uptime(self) -> datetime.timedelta:
        """Return the uptime of the connected shard.

        If the shard is not yet connected, this will be 0.

        This is measured as the time since the last disconnect, whether the
        session has been kept alive or not. This will be measured as a monotonic
        timedelta.

        Returns
        -------
        datetime.timedelta
            Uptime of this shard.
        """

    @property
    @abc.abstractmethod
    def data_format(self) -> str:
        """Return name of the data format for inbound payloads.

        This may be a value in `GatewayDataFormat`, or it may
        be a custom name in custom implementations.

        Returns
        -------
        builtins.str
            The name of the data format being used on this shard.
        """

    @property
    @abc.abstractmethod
    def heartbeat_interval(self) -> typing.Optional[datetime.timedelta]:
        """Return the heartbeat interval for this shard.

        Returns
        -------
        datetime.timedelta or builtins.None
            How often the shard will send a heartbeat in seconds. If the
            information is not yet available, this returns `builtins.None`
            instead.
        """

    @property
    @abc.abstractmethod
    def heartbeat_latency(self) -> typing.Optional[datetime.timedelta]:
        """Return the shard's most recent heartbeat latency.

        Returns
        -------
        datetime.timedelta or builtins.None
            Heartbeat latency measured in seconds. If the information is
            not yet available, then this will be `builtins.None` instead.
        """

    @property
    @abc.abstractmethod
    def http_settings(self) -> config.HTTPSettings:
        """Return the HTTP settings in use for this shard.

        Returns
        -------
        hikari.config.HTTPSettings
            The HTTP settings in-use.
        """

    @property
    @abc.abstractmethod
    def id(self) -> int:
        """Return the shard ID for this shard.

        Returns
        -------
        builtins.int
            The integer 0-based shard ID.
        """

    @property
    @abc.abstractmethod
    def intents(self) -> typing.Optional[intents_.Intent]:
        """Return the intents set on this shard.

        Returns
        -------
        hikari.models.intents.Intent or builtins.None
            The intents being used on this shard. This may be
            `builtins.None` if intents were not specified.

        !!! warning
            As of October 2020, Intents will become mandatory,
            at which point this API will be changed to always
            return a value here.
        """

    @property
    @abc.abstractmethod
    def is_alive(self) -> bool:
        """Return `builtins.True` if the shard is alive and connected.

        Returns
        -------
        builtins.bool
            `builtins.True` if connected, or `builtins.False` if not.
        """

    @property
    @abc.abstractmethod
    def proxy_settings(self) -> config.ProxySettings:
        """Return the proxy settings in use for this shard.

        Returns
        -------
        hikari.config.ProxySettings
            The proxy settings in-use.
        """

    @property
    @abc.abstractmethod
    def sequence(self) -> typing.Optional[int]:
        """Return the sequence number for this shard.

        This roughly corresponds to how many payloads have been
        received since the current session started.

        Returns
        -------
        builtins.int or builtins.None
            The session sequence, or `builtins.None` if no session is active.
        """

    @property
    @abc.abstractmethod
    def session_id(self) -> typing.Optional[str]:
        """Return the session ID for this shard.

        Returns
        -------
        builtins.str or builtins.None
            The session ID, or `builtins.None` if no session is active.
        """

    @property
    @abc.abstractmethod
    def session_uptime(self) -> typing.Optional[datetime.timedelta]:
        """Return the time that the session has been active for.

        This will be measured as a monotonic time delta.

        Returns
        -------
        datetime.timedelta or builtins.None
            The session uptime, or `builtins.None` if no session is
            active.
        """

    @property
    @abc.abstractmethod
    def shard_count(self) -> int:
        """Return the total number of shards expected in the entire application.

        Returns
        -------
        builtins.int
            A number of shards greater than or equal to 1.
        """

    @property
    @abc.abstractmethod
    def version(self) -> int:
        """Return the gateway API version in use.

        Returns
        -------
        builtins.int
            The gateway API version being used.
        """

    @abc.abstractmethod
    async def get_user_id(self) -> snowflake.Snowflake:
        """Return the user ID.

        If the shard has not connected fully yet, this should wait until the ID
        is set before returning.

        Returns
        -------
        hikari.utilities.snowflake.Snowflake
            The user ID for the application user.
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
