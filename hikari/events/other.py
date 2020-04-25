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
"""Components and entities that are used to describe Discord gateway other events."""
__all__ = [
    "ExceptionEvent",
    "ConnectedEvent",
    "DisconnectedEvent",
    "StartingEvent",
    "StartedEvent",
    "StoppingEvent",
    "StoppedEvent",
    "ReadyEvent",
    "ResumedEvent",
    "UserUpdateEvent",
]

import typing

import attr

from hikari import users
from hikari import guilds
from hikari import bases as _bases
from hikari.events import bases
from hikari.clients import shards
from hikari.internal import marshaller

# Synthetic event, is not deserialized, and is produced by the dispatcher.
@attr.s(slots=True, auto_attribs=True)
class ExceptionEvent(bases.HikariEvent):
    """Descriptor for an exception thrown while processing an event."""

    exception: Exception
    """The exception that was raised."""

    event: bases.HikariEvent
    """The event that was being invoked when the exception occurred."""

    callback: typing.Callable[[bases.HikariEvent], typing.Awaitable[None]]
    """The event that was being invoked when the exception occurred."""


# Synthetic event, is not deserialized
@attr.s(slots=True, auto_attribs=True)
class StartingEvent(bases.HikariEvent):
    """Event that is fired before the gateway client starts all shards."""


# Synthetic event, is not deserialized
@attr.s(slots=True, auto_attribs=True)
class StartedEvent(bases.HikariEvent):
    """Event that is fired when the gateway client starts all shards."""


# Synthetic event, is not deserialized
@attr.s(slots=True, auto_attribs=True)
class StoppingEvent(bases.HikariEvent):
    """Event that is fired when the gateway client is instructed to disconnect all shards."""


# Synthetic event, is not deserialized
@attr.s(slots=True, auto_attribs=True)
class StoppedEvent(bases.HikariEvent):
    """Event that is fired when the gateway client has finished disconnecting all shards."""


@attr.s(slots=True, kw_only=True, auto_attribs=True)
class ConnectedEvent(bases.HikariEvent, marshaller.Deserializable):
    """Event invoked each time a shard connects."""

    shard: shards.ShardClient
    """The shard that connected."""


@attr.s(slots=True, kw_only=True, auto_attribs=True)
class DisconnectedEvent(bases.HikariEvent, marshaller.Deserializable):
    """Event invoked each time a shard disconnects."""

    shard: shards.ShardClient
    """The shard that disconnected."""


@attr.s(slots=True, kw_only=True, auto_attribs=True)
class ResumedEvent(bases.HikariEvent):
    """Represents a gateway Resume event."""

    shard: shards.ShardClient
    """The shard that reconnected."""


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class ReadyEvent(bases.HikariEvent, marshaller.Deserializable):
    """Represents the gateway Ready event.

    This is received only when IDENTIFYing with the gateway.
    """

    gateway_version: int = marshaller.attrib(raw_name="v", deserializer=int)
    """The gateway version this is currently connected to."""

    my_user: users.MyUser = marshaller.attrib(raw_name="user", deserializer=users.MyUser.deserialize)
    """The object of the current bot account this connection is for."""

    unavailable_guilds: typing.Mapping[_bases.Snowflake, guilds.UnavailableGuild] = marshaller.attrib(
        raw_name="guilds",
        deserializer=lambda guilds_objs: {g.id: g for g in map(guilds.UnavailableGuild.deserialize, guilds_objs)},
    )
    """A mapping of the guilds this bot is currently in.

    All guilds will start off "unavailable".
    """

    session_id: str = marshaller.attrib(deserializer=str)
    """The id of the current gateway session, used for reconnecting."""

    _shard_information: typing.Optional[typing.Tuple[int, int]] = marshaller.attrib(
        raw_name="shard", deserializer=tuple, if_undefined=None, default=None
    )
    """Information about the current shard, only provided when IDENTIFYing."""

    @property
    def shard_id(self) -> typing.Optional[int]:
        """Zero-indexed ID of the current shard.

        This is only available if this ready event was received while IDENTIFYing.
        """
        return self._shard_information[0] if self._shard_information else None

    @property
    def shard_count(self) -> typing.Optional[int]:
        """Total shard count for this bot.

        This is only available if this ready event was received while IDENTIFYing.
        """
        return self._shard_information[1] if self._shard_information else None


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class UserUpdateEvent(bases.HikariEvent, users.MyUser):
    """Used to represent User Update gateway events.

    Sent when the current user is updated.
    """
