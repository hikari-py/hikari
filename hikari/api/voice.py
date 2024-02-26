# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021-present davfsa
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
"""Interfaces used to describe voice client implementations."""
from __future__ import annotations

__all__: typing.Sequence[str] = ("VoiceComponent", "VoiceConnection")

import abc
import typing

from hikari.events import voice_events

if typing.TYPE_CHECKING:
    from typing_extensions import Self

    from hikari import channels
    from hikari import guilds
    from hikari import snowflakes

    _VoiceConnectionT = typing.TypeVar("_VoiceConnectionT", bound="VoiceConnection")


class VoiceComponent(abc.ABC):
    """Interface for a voice system implementation."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def is_alive(self) -> bool:
        """Whether this component is alive."""

    @property
    @abc.abstractmethod
    def connections(self) -> typing.Mapping[snowflakes.Snowflake, VoiceConnection]:
        """Return a mapping of guild-id to active voice connection."""

    @abc.abstractmethod
    async def close(self) -> None:
        """Shut down all connections, waiting for them to terminate.

        Once this is done, unsubscribe from any events.

        If you simply wish to disconnect every connection, use
        [hikari.api.VoiceComponent.disconnect][] instead.
        """

    @abc.abstractmethod
    async def disconnect(self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild]) -> None:
        """Disconnect from a given guild.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.Guild]
            The guild to disconnect from.
        """

    @abc.abstractmethod
    async def disconnect_all(self) -> None:
        """Disconnect all the active voice connections."""

    @abc.abstractmethod
    async def connect_to(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.Guild],
        channel: snowflakes.SnowflakeishOr[channels.GuildVoiceChannel],
        voice_connection_type: typing.Type[_VoiceConnectionT],
        *,
        deaf: bool = False,
        mute: bool = False,
        timeout: typing.Optional[int] = 5,
        **kwargs: typing.Any,
    ) -> _VoiceConnectionT:
        """Connect to a given voice channel.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.Guild]
            The guild to connect to.
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.GuildVoiceChannel]
            The channel or channel ID to connect to.
        voice_connection_type : typing.Type[VoiceConnection]
            The type of voice connection to use. This should be initialized
            internally using the [hikari.api.voice.VoiceConnection.initialize][]
            classmethod.
        deaf : bool
            If [True][], the client will enter the voice channel deafened
            (thus unable to hear other users).
        mute : bool
            If [True][], the client will enter the voice channel muted
            (thus unable to send audio).
        timeout : typing.Optional[int]
            The amount of time, in seconds, to wait before erroring when
            connecting to the voice channel. If timeout is [None][] there will be
            no timeout.

            !!! warning
                If timeout is [None][], this function will be awaited forever if an
                invalid `guild_id` or `channel_id` is provided.

        **kwargs : typing.Any
            Any arguments to provide to the
            [hikari.api.voice.VoiceConnection.initialize][] method.

        Returns
        -------
        VoiceConnection
            A voice connection implementation of some sort.
        """


class VoiceConnection(abc.ABC):
    """An abstract interface for defining how bots can interact with voice.

    Since voice will generally be run in a subprocess to prevent interfering
    with the bot when performing CPU-bound encoding/encryption, any
    implementation of this is expected to implement the appropriate mechanisms
    for communicating with a voice subprocess and controlling it, however, this
    is left to the discretion of each implementation.

    Control is left to the implementation to define how to perform it. The
    idea is to allow various decoders to be implemented to allow this to direct
    interface with other types of system outside this library, such as LavaLink,
    for example.
    """

    __slots__: typing.Sequence[str] = ()

    @classmethod
    @abc.abstractmethod
    async def initialize(
        cls,
        channel_id: snowflakes.Snowflake,
        endpoint: str,
        guild_id: snowflakes.Snowflake,
        on_close: typing.Callable[[Self], typing.Awaitable[None]],
        owner: VoiceComponent,
        session_id: str,
        shard_id: int,
        token: str,
        user_id: snowflakes.Snowflake,
        **kwargs: typing.Any,
    ) -> Self:
        """Initialize and connect the voice connection.

        Parameters
        ----------
        channel_id : hikari.snowflakes.Snowflake
            The channel ID that the voice connection is actively connected to.
        endpoint : str
            The voice websocket endpoint to connect to. Will contain the
            protocol at the start (i.e. [wss://][]), and end with the **correct**
            port (the port and protocol are sanitized since Discord still
            provide the wrong information four years later).
        guild_id : hikari.snowflakes.Snowflake
            The guild ID that the websocket should connect to.
        on_close : typing.Callable[[T], typing.Awaitable[None]]
            A shutdown hook to invoke when closing a connection to ensure the
            connection is unregistered from the voice component safely.
        owner : VoiceComponent
            The component that made this connection object.
        session_id : str
            The voice session ID to use.
        shard_id : int
            The associated shard ID that the voice connection was generated
            from.
        token : str
            The voice token to use.
        user_id : hikari.snowflakes.Snowflake
            The user ID of the account that just joined the voice channel.
        **kwargs : typing.Any
            Any implementation-specific arguments to provide to the
            voice connection that is being initialized.

        Returns
        -------
        VoiceConnection
            The type of this connection object.
        """

    @property
    @abc.abstractmethod
    def channel_id(self) -> snowflakes.Snowflake:
        """ID of the voice channel this voice connection is in."""

    @property
    @abc.abstractmethod
    def guild_id(self) -> snowflakes.Snowflake:
        """ID of the guild this voice connection is in."""

    @property
    @abc.abstractmethod
    def is_alive(self) -> bool:
        """Whether the connection is alive."""

    @property
    @abc.abstractmethod
    def shard_id(self) -> int:
        """ID of the shard that requested the connection."""

    @property
    @abc.abstractmethod
    def owner(self) -> VoiceComponent:
        """Return the component that is managing this connection."""

    @abc.abstractmethod
    async def disconnect(self) -> None:
        """Signal the process to shut down."""

    @abc.abstractmethod
    async def join(self) -> None:
        """Wait for the process to halt before continuing."""

    @abc.abstractmethod
    async def notify(self, event: voice_events.VoiceEvent) -> None:
        """Submit an event to the voice connection to be processed."""
