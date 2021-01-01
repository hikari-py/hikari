# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021 davfsa
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
"""Provides an interface for gateway shard implementations to conform to."""
from __future__ import annotations

__all__: typing.List[str] = ["GatewayDataFormat", "GatewayCompression", "GatewayShard"]

import abc
import typing

from hikari import undefined
from hikari.internal import enums

if typing.TYPE_CHECKING:
    import datetime

    from hikari import channels
    from hikari import guilds
    from hikari import intents as intents_
    from hikari import presences
    from hikari import snowflakes
    from hikari import users as users_


@typing.final
class GatewayDataFormat(str, enums.Enum):
    """Format of inbound gateway payloads."""

    JSON = "json"
    """Javascript serialized object notation."""
    ETF = "etf"
    """Erlang transmission format."""


@typing.final
class GatewayCompression(str, enums.Enum):
    """Types of gateway compression that may be supported."""

    TRANSPORT_ZLIB_STREAM = "transport_zlib_stream"
    """Transport compression using ZLIB."""
    PAYLOAD_ZLIB_STREAM = "payload_zlib_stream"
    """Payload compression using ZLIB."""


class GatewayShard(abc.ABC):
    """Interface for a definition of a V8 compatible websocket gateway.

    Each instance should represent a single shard.
    """

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def heartbeat_latency(self) -> float:
        """Return the shard's most recent heartbeat latency.

        Returns
        -------
        builtins.float
            Heartbeat latency measured in seconds. If the information is
            not yet available, then this will be `float('nan')` instead.
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
    def intents(self) -> intents_.Intents:
        """Return the intents set on this shard.

        Returns
        -------
        hikari.intents.Intents
            The intents being used on this shard.
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
    def shard_count(self) -> int:
        """Return the total number of shards expected in the entire application.

        Returns
        -------
        builtins.int
            A number of shards greater than or equal to 1.
        """

    @abc.abstractmethod
    async def get_user_id(self) -> snowflakes.Snowflake:
        """Return the user ID.

        If the shard has not connected fully yet, this should wait until the ID
        is set before returning.

        Returns
        -------
        hikari.snowflakes.Snowflake
            The user ID for the application user.
        """

    @abc.abstractmethod
    async def close(self) -> None:
        """Close the websocket if it is connected, otherwise do nothing."""

    @abc.abstractmethod
    async def join(self) -> None:
        """Wait indefinitely until the websocket closes permanently.

        This can be placed in a task and cancelled without affecting the
        websocket runtime itself.
        """

    @abc.abstractmethod
    async def start(self) -> None:
        """Start the shard, wait for it to become ready."""

    @abc.abstractmethod
    async def update_presence(
        self,
        *,
        idle_since: undefined.UndefinedNoneOr[datetime.datetime] = undefined.UNDEFINED,
        afk: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        activity: undefined.UndefinedNoneOr[presences.Activity] = undefined.UNDEFINED,
        status: undefined.UndefinedOr[presences.Status] = undefined.UNDEFINED,
    ) -> None:
        """Update the presence of the shard user.

        If the shard is not alive, no physical data will be sent, however,
        the new presence settings will be remembered for when the shard
        does connect.

        Other Parameters
        ----------------
        idle_since : hikari.undefined.UndefinedNoneOr[datetime.datetime]
            The datetime that the user started being idle. If undefined, this
            will not be changed.
        afk : hikari.undefined.UndefinedOr[builtins.bool]
            If `builtins.True`, the user is marked as AFK. If `builtins.False`,
            the user is marked as being active. If undefined, this will not be
            changed.
        activity : hikari.undefined.UndefinedNoneOr[hikari.presences.Activity]
            The activity to appear to be playing. If undefined, this will not be
            changed.
        status : hikari.undefined.UndefinedOr[hikari.presences.Status]
            The web status to show. If undefined, this will not be changed.
        """

    @abc.abstractmethod
    async def update_voice_state(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        channel: typing.Optional[snowflakes.SnowflakeishOr[channels.GuildVoiceChannel]],
        *,
        self_mute: bool = False,
        self_deaf: bool = False,
    ) -> None:
        """Update the voice state for this shard in a given guild.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild or guild ID to update the voice state for.
        channel : typing.Optional[hikari.snowflakes.SnowflakeishOr[hikari.channels.GuildVoiceChannel]]
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

    @abc.abstractmethod
    async def request_guild_members(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        *,
        include_presences: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        query: str = "",
        limit: int = 0,
        users: undefined.UndefinedOr[snowflakes.SnowflakeishSequence[users_.User]] = undefined.UNDEFINED,
        nonce: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        """Request for a guild chunk.

        Parameters
        ----------
        guild: hikari.guilds.Guild
            The guild to request chunk for.

        Other Parameters
        ----------------
        include_presences: hikari.undefined.UndefinedOr[builtins.bool]
            If provided, whether to request presences.
        query: builtins.str
            If not `""`, request the members which username starts with the string.
        limit: builtins.int
            Maximum number of members to send matching the query.
        users: hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishSequence[hikari.users.User]]
            If provided, the users to request for.
        nonce: hikari.undefined.UndefinedOr[builtins.str]
            If provided, the nonce to be sent with guild chunks.

        !!! note
            To request the full list of members, set `query` to `""` (empty
            string) and `limit` to `0`.

        Raises
        ------
        ValueError
            When trying to specify `users` with `query`/`limit`, if `limit` is not between
            0 and 100, both inclusive or if `users` length is over 100.
        hikari.errors.MissingIntentError
            When trying to request presences without the `GUILD_MEMBERS` or when trying to
            request the full list of members without `GUILD_PRESENCES`.
        """
