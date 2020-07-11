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
"""Interfaces used to describe voice client implementations."""
from __future__ import annotations

__all__: typing.Final[typing.List[str]] = ["IVoiceComponent", "IVoiceConnection"]

import abc
import typing

from hikari.api import app
from hikari.api import component
from hikari.events import voice

if typing.TYPE_CHECKING:
    from hikari.models import channels
    from hikari.models import guilds
    from hikari.utilities import snowflake


class IVoiceApp(app.IApp, abc.ABC):
    """Voice application mixin."""

    __slots__ = ()

    @property
    @abc.abstractmethod
    def voice(self) -> IVoiceComponent:
        """Return the voice component."""


_VoiceConnectionT = typing.TypeVar("_VoiceConnectionT", bound="IVoiceConnection")


class IVoiceComponent(component.IComponent, abc.ABC):
    """Interface for a voice system implementation."""

    __slots__ = ()

    @property
    @abc.abstractmethod
    def connections(self) -> typing.Mapping[snowflake.Snowflake, IVoiceConnection]:
        """Return a mapping of guild-id to active voice connection."""

    @abc.abstractmethod
    async def close(self) -> None:
        """Shut down all connections, waiting for them to terminate."""

    @abc.abstractmethod
    async def connect_to(
        self,
        channel: typing.Union[channels.GuildVoiceChannel, snowflake.UniqueObject],
        guild: typing.Union[guilds.Guild, snowflake.UniqueObject],
        *,
        deaf: bool = False,
        mute: bool = False,
        voice_connection_type: typing.Type[_VoiceConnectionT],
        **kwargs: typing.Any,
    ) -> _VoiceConnectionT:
        """Connect to a given voice channel.

        Parameters
        ----------
        channel : hikari.models.channels.GuildVoiceChannel or hikari.utilities.snowflake.UniqueObject
            The channel or channel ID to connect to.
        guild : hikari.models.guilds.Guild or hikari.utilities.snowflake.UniqueObject
            The guild to connect to.
        deaf : builtins.bool
            Defaulting to `builtins.False`, if `builtins.True`, the client will
            enter the voice channel deafened (thus unable to hear other users).
        mute : builtins.bool
            Defaulting to `builtins.False`, if `builtins.True`, the client will
            enter the voice channel muted (thus unable to send audio).
        voice_connection_type : typing.Type[IVoiceConnection]
            The type of voice connection to use. This should be initialized
            internally using the `IVoiceConnection.initialize`
            `builtins.classmethod`.
        **kwargs : typing.Any
            Any arguments to provide to the `IVoiceConnection.initialize`
            method.


        Returns
        -------
        IVoiceConnection
            A voice connection implementation of some sort.
        """


class IVoiceConnection(abc.ABC):
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

    __slots__ = ()

    if typing.TYPE_CHECKING:
        _T = typing.TypeVar("_T")

    @classmethod
    @abc.abstractmethod
    async def initialize(cls: typing.Type[_T], owner: IVoiceComponent, **kwargs: typing.Any) -> _T:
        """Initialize and connect the voice connection.

        Parameters
        ----------
        owner : IVoiceComponent
            The component that made this connection object.
        **kwargs : typing.Any
            Any implementation-specific arguments to provide to the
            voice connection that is being initialized.
        """

    @property
    @abc.abstractmethod
    def owner(self) -> IVoiceComponent:
        """Return the component that is managing this connection."""

    @property
    @abc.abstractmethod
    def is_alive(self) -> bool:
        """Return `builtins.True` if the connection is alive."""

    @property
    @abc.abstractmethod
    def guild_id(self) -> snowflake.Snowflake:
        """Return the ID of the guild this voice connection is in."""

    @abc.abstractmethod
    async def disconnect(self) -> None:
        """Signal the process to shut down."""

    @abc.abstractmethod
    async def join(self) -> None:
        """Wait for the process to halt before continuing."""

    @abc.abstractmethod
    async def notify(self, event: voice.VoiceEvent) -> None:
        """Submit an event to the voice connection to be processed."""
