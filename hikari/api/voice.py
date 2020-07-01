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

from hikari.api import component

if typing.TYPE_CHECKING:
    from hikari.models import channels


class IVoiceComponent(component.IComponent, abc.ABC):
    """Interface for a voice system implementation."""

    __slots__ = ()

    @abc.abstractmethod
    async def connect_to(
        self, channel: channels.GuildVoiceChannel, *, deaf: bool = False, mute: bool = False,
    ) -> IVoiceConnection:
        """Connect to a given voice channel.

        Parameters
        ----------
        channel : hikari.models.channels.GuildVoiceChannel or hikari.utilities.snowflake.UniqueObject
            The channel or channel ID to connect to.
        deaf : builtins.bool
            Defaulting to `builtins.False`, if `builtins.True`, the client will
            enter the voice channel deafened (thus unable to hear other users).
        mute : builtins.bool
            Defaulting to `builtins.False`, if `builtins.True`, the client will
            enter the voice channel muted (thus unable to send audio).
        """


class IVoiceConnection(abc.ABC):
    """Interface for defining what a voice connection should look like."""
