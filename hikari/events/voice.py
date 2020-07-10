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
"""Voice server event types."""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = ["VoiceStateUpdateEvent", "VoiceServerUpdateEvent", "VoiceEvent"]

import abc
import typing

import attr

from hikari.events import base as base_events
from hikari.models import intents

if typing.TYPE_CHECKING:
    from hikari.models import voices
    from hikari.utilities import snowflake


@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class VoiceEvent(base_events.Event):
    """Base for any voice-related event."""

    @property
    @abc.abstractmethod
    def guild_id(self) -> typing.Optional[snowflake.Snowflake]:
        """Return the ID of the guild this event was for, if known."""


@base_events.requires_intents(intents.Intent.GUILD_VOICE_STATES)
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class VoiceStateUpdateEvent(VoiceEvent):
    """Used to represent voice state update gateway events.

    Sent when a user joins, leaves or moves voice channel(s).
    """

    state: voices.VoiceState = attr.ib(repr=True)
    """The object of the voice state that's being updated."""

    @property
    def guild_id(self) -> typing.Optional[snowflake.Snowflake]:
        return self.state.guild_id


@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class VoiceServerUpdateEvent(VoiceEvent):
    """Used to represent voice server update gateway events.

    Sent when initially connecting to voice and when the current voice instance
    falls over to a new server.
    """

    token: str = attr.ib(repr=False)
    """The voice connection's string token."""

    guild_id: snowflake.Snowflake = attr.ib(repr=True)
    """The ID of the guild this voice server update is for."""

    _endpoint: str = attr.ib(repr=True)

    @property
    def endpoint(self) -> str:
        """Return the URI for this voice server host, with the correct port."""
        # Discord have had this wrong for like 4 years, bleh.
        uri, _, _ = self._endpoint.rpartition(":")
        return f"wss://{uri}:443"
