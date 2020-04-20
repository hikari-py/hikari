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
"""Entities directly related to creating and managing gateway shards."""
__all__ = ["Activity", "GatewayBot", "SessionStartLimit"]

import datetime
import typing

import attr

from hikari import bases
from hikari import guilds
from hikari.internal import marshaller


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class SessionStartLimit(bases.HikariEntity, marshaller.Deserializable):
    """Used to represent information about the current session start limits."""

    total: int = marshaller.attrib(deserializer=int)
    """The total number of session starts the current bot is allowed."""

    remaining: int = marshaller.attrib(deserializer=int)
    """The remaining number of session starts this bot has."""

    reset_after: datetime.timedelta = marshaller.attrib(
        deserializer=lambda after: datetime.timedelta(milliseconds=after),
    )
    """When `SessionStartLimit.remaining` will reset for the current bot.

    After it resets it will be set to `SessionStartLimit.total`.
    """


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class GatewayBot(bases.HikariEntity, marshaller.Deserializable):
    """Used to represent gateway information for the connected bot."""

    url: str = marshaller.attrib(deserializer=str)
    """The WSS URL that can be used for connecting to the gateway."""

    shard_count: int = marshaller.attrib(raw_name="shards", deserializer=int)
    """The recommended number of shards to use when connecting to the gateway."""

    session_start_limit: SessionStartLimit = marshaller.attrib(deserializer=SessionStartLimit.deserialize)
    """Information about the bot's current session start limit."""


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class Activity(marshaller.Deserializable, marshaller.Serializable):
    """An activity that the bot can set for one or more shards.

    This will show the activity as the bot's presence.
    """

    name: str = marshaller.attrib(deserializer=str, serializer=str)
    """The activity name."""

    url: typing.Optional[str] = marshaller.attrib(
        deserializer=str, serializer=str, if_none=None, if_undefined=None, default=None
    )
    """The activity URL. Only valid for `STREAMING` activities."""

    type: guilds.ActivityType = marshaller.attrib(
        deserializer=guilds.ActivityType,
        serializer=int,
        if_undefined=lambda: guilds.ActivityType.PLAYING,
        default=guilds.ActivityType.PLAYING,
    )
    """The activity type."""
