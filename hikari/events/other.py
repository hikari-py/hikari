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
"""Application and entities that are used to describe Discord gateway other events."""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = [
    "ExceptionEvent",
    "ConnectedEvent",
    "DisconnectedEvent",
    "StartingEvent",
    "StartedEvent",
    "StoppingEvent",
    "StoppedEvent",
    "ReadyEvent",
    "ResumedEvent",
    "OwnUserUpdateEvent",
    "MemberChunkEvent",
]

import typing

import attr

from hikari.api.gateway import shard as gateway_shard
from hikari.events import base as base_events

if typing.TYPE_CHECKING:
    from hikari.api.rest import app as rest_app
    from hikari.models import guilds
    from hikari.models import presences as presences_
    from hikari.models import users
    from hikari.utilities import snowflake


EventT_inv = typing.TypeVar("EventT_inv", bound=base_events.Event)


# Synthetic event, is not deserialized, and is produced by the dispatcher.
@base_events.no_catch()
@attr.s(eq=False, hash=False, init=True, kw_only=True, slots=True)
class ExceptionEvent(base_events.Event, typing.Generic[EventT_inv]):
    """Descriptor for an exception thrown while processing an event."""

    exception: Exception = attr.ib(repr=True)
    """The exception that was raised."""

    event: base_events.Event = attr.ib(repr=True)
    """The event that was being invoked when the exception occurred."""

    callback: typing.Callable[[EventT_inv], typing.Coroutine[None, typing.Any, None]] = attr.ib(repr=False)
    """The event that was being invoked when the exception occurred."""


# Synthetic event, is not deserialized
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class StartingEvent(base_events.Event):
    """Event that is fired before the gateway client starts all shards."""


# Synthetic event, is not deserialized
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class StartedEvent(base_events.Event):
    """Event that is fired when the gateway client starts all shards."""


# Synthetic event, is not deserialized
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class StoppingEvent(base_events.Event):
    """Event that is fired when the gateway client is instructed to disconnect all shards."""


# Synthetic event, is not deserialized
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class StoppedEvent(base_events.Event):
    """Event that is fired when the gateway client has finished disconnecting all shards."""


# Synthetic event, is not deserialized
@attr.s(eq=False, hash=False, init=True, kw_only=True, slots=True)
class ConnectedEvent(base_events.Event):
    """Event invoked each time a shard connects."""

    shard: gateway_shard.IGatewayShard = attr.ib(repr=True)
    """The shard that connected."""


# Synthetic event, is not deserialized
@attr.s(eq=False, hash=False, init=True, kw_only=True, slots=True)
class DisconnectedEvent(base_events.Event):
    """Event invoked each time a shard disconnects."""

    shard: gateway_shard.IGatewayShard = attr.ib(repr=True)
    """The shard that disconnected."""


@attr.s(eq=False, hash=False, init=True, kw_only=True, slots=True)
class ResumedEvent(base_events.Event):
    """Represents a gateway Resume event."""

    shard: gateway_shard.IGatewayShard = attr.ib(repr=True)
    """The shard that reconnected."""


@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class ReadyEvent(base_events.Event):
    """Represents the gateway Ready event.

    This is received only when IDENTIFYing with the gateway.
    """

    shard: gateway_shard.IGatewayShard = attr.ib(repr=False)
    """The shard that is ready."""

    gateway_version: int = attr.ib(repr=True)
    """The gateway version this is currently connected to."""

    my_user: users.OwnUser = attr.ib(repr=True)
    """The object of the current bot account this connection is for."""

    unavailable_guilds: typing.Mapping[snowflake.Snowflake, guilds.UnavailableGuild] = attr.ib(repr=False)
    """A mapping of the guilds this bot is currently in.

    All guilds will start off "unavailable".
    """

    session_id: str = attr.ib(repr=True)
    """The id of the current gateway session, used for reconnecting."""

    shard_id: typing.Optional[int] = attr.ib(repr=True)
    """Zero-indexed ID of the current shard.

    This is only available if this ready event was received while IDENTIFYing.
    """

    shard_count: typing.Optional[int] = attr.ib(repr=True)
    """Total shard count for this bot.

    This is only available if this ready event was received while IDENTIFYing.
    """


@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class OwnUserUpdateEvent(base_events.Event):
    """Used to represent user update gateway events.

    Sent when the current user is updated.
    """

    my_user: users.OwnUser = attr.ib(repr=True)
    """The updated object of the current application's user."""


@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class MemberChunkEvent(base_events.Event):
    """Used to represent the response to Guild Request Members."""

    app: rest_app.IRESTApp = attr.ib(default=None, repr=False, eq=False, hash=False)
    """The client application that models may use for procedures."""

    guild_id: snowflake.Snowflake = attr.ib(repr=True)
    """The ID of the guild this member chunk is for."""

    members: typing.Mapping[snowflake.Snowflake, guilds.Member] = attr.ib(repr=False)
    """A mapping of snowflake IDs to the objects of the members in this chunk."""

    index: int = attr.ib(repr=True)
    """The zero-indexed position of this within the queued up chunks for this request."""

    count: int = attr.ib(repr=True)
    """The total number of expected chunks for the request this is associated with."""

    not_found: typing.Sequence[snowflake.Snowflake] = attr.ib(repr=True)
    """An array of the snowflakes that weren't found while making this request.

    This is only applicable when user ids are specified while making the
    member request the chunk is associated with.
    """

    presences: typing.Mapping[snowflake.Snowflake, presences_.MemberPresence] = attr.ib(repr=False)
    """A mapping of snowflakes to found member presence objects.

    This will be empty if no presences are found or `presences` isn't passed as
    `True` while requesting the member chunks.
    """

    nonce: typing.Optional[str] = attr.ib(repr=True)
    """The string nonce used to identify the request member chunks are associated with.

    This is the nonce value passed while requesting member chunks.
    """
