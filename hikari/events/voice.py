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
"""Voice server event types."""

from __future__ import annotations

__all__ = ["VoiceStateUpdateEvent", "VoiceServerUpdateEvent"]

import attr

from hikari.events import base as base_events
from hikari import bases as base_entities
from hikari import intents
from hikari import voices
from hikari.internal import marshaller


@base_events.requires_intents(intents.Intent.GUILD_VOICE_STATES)
@marshaller.marshallable()
@attr.s(eq=False, hash=False, kw_only=True, slots=True)
class VoiceStateUpdateEvent(base_events.HikariEvent, voices.VoiceState):
    """Used to represent voice state update gateway events.

    Sent when a user joins, leaves or moves voice channel(s).
    """


@marshaller.marshallable()
@attr.s(eq=False, hash=False, kw_only=True, slots=True)
class VoiceServerUpdateEvent(base_events.HikariEvent, marshaller.Deserializable):
    """Used to represent voice server update gateway events.

    Sent when initially connecting to voice and when the current voice instance
    falls over to a new server.
    """

    token: str = marshaller.attrib(deserializer=str)
    """The voice connection's string token."""

    guild_id: base_entities.Snowflake = marshaller.attrib(deserializer=base_entities.Snowflake, repr=True)
    """The ID of the guild this voice server update is for."""

    endpoint: str = marshaller.attrib(deserializer=str, repr=True)
    """The URI for this voice server host."""
