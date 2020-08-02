# -*- coding: utf-8 -*-
# cython: language_level=3
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
"""Events relating to specific shards connecting and disconnecting."""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = [
    "ShardEvent",
    "ShardStateEvent",
    "ShardConnectedEvent",
    "ShardDisconnectedEvent",
    "ShardReadyEvent",
    "ShardResumedEvent",
    "MemberChunkEvent",
]

import abc
import typing

import attr

from hikari.events import base_events

if typing.TYPE_CHECKING:
    from hikari.api import event_consumer
    from hikari.api import shard as gateway_shard
    from hikari.models import guilds
    from hikari.models import presences as presences_
    from hikari.models import users
    from hikari.utilities import snowflake


@attr.s(kw_only=True, slots=True, weakref_slot=False)
class ShardEvent(base_events.Event, abc.ABC):
    """Base class for any event that was shard-specific."""

    @property
    def app(self) -> event_consumer.IEventConsumerApp:
        # <<inherited docstring from Event>>.
        return self.shard.app

    @property
    @abc.abstractmethod
    def shard(self) -> gateway_shard.IGatewayShard:
        """Shard that received this event.

        Returns
        -------
        hikari.api.shard.IGatewayShard
            The shard that triggered the event.
        """


@attr.s(kw_only=True, slots=True, weakref_slot=False)
class ShardStateEvent(ShardEvent, abc.ABC):
    """Base class for any event concerning the state/connectivity of a shard.

    This currently wraps connection/disconnection/ready/resumed events only.
    """


@attr.s(kw_only=True, slots=True, weakref_slot=False)
class ShardConnectedEvent(ShardStateEvent):
    """Event fired when a shard connects."""

    shard: gateway_shard.IGatewayShard = attr.ib()
    # <<docstring inherited from ShardEvent>>.


@attr.s(kw_only=True, slots=True, weakref_slot=False)
class ShardDisconnectedEvent(ShardStateEvent):
    """Event fired when a shard disconnects."""

    shard: gateway_shard.IGatewayShard = attr.ib()
    # <<docstring inherited from ShardEvent>>.


@attr.s(kw_only=True, slots=True, weakref_slot=False)
class ShardReadyEvent(ShardStateEvent):
    """Event fired when a shard declares it is ready."""

    shard: gateway_shard.IGatewayShard = attr.ib()
    # <<docstring inherited from ShardEvent>>.

    actual_gateway_version: int = attr.ib(repr=True)
    """Actual gateway version being used.

    Returns
    -------
    builtins.int
        The actual gateway version we are actively using for this protocol.
    """

    session_id: str = attr.ib(repr=True)
    """ID for this session.

    Returns
    -------
    builtins.str
        The session ID for this gateway session.
    """

    my_user: users.OwnUser = attr.ib(repr=True)
    """User for the current bot account this connection is authenticated with.

    Returns
    -------
    hikari.models.users.OwnUser
        This bot's user.
    """

    unavailable_guilds: typing.Sequence[snowflake.Snowflake] = attr.ib(repr=False)
    """Sequence of the IDs for all guilds this bot is currently in.

    All guilds will start off "unavailable" and should become available after
    a few seconds of connecting one-by-one.

    Returns
    -------
    typing.Sequence[hikari.utilities.snowflake.Snowflake]
        All guild IDs that the bot is in for this shard.
    """


@attr.s(kw_only=True, slots=True, weakref_slot=False)
class ShardResumedEvent(ShardStateEvent):
    """Event fired when a shard resumes an existing session."""

    shard: gateway_shard.IGatewayShard = attr.ib()
    # <<docstring inherited from ShardEvent>>.


@attr.s(kw_only=True, slots=True, weakref_slot=False)
class MemberChunkEvent(ShardEvent):
    """Used to represent the response to Guild Request Members."""

    shard: gateway_shard.IGatewayShard = attr.ib()
    # <<docstring inherited from ShardEvent>>.

    guild_id: snowflake.Snowflake = attr.ib(repr=True)
    # <<docstring inherited from ShardEvent>>.

    members: typing.Mapping[snowflake.Snowflake, guilds.Member] = attr.ib(repr=False)
    """Mapping of snowflake IDs to the objects of the members in this chunk.

    Returns
    -------
    typing.Mapping[hikari.utilities.snowflake.Snowflake, hikari.models.guilds.Member]
        Mapping of user IDs to corresponding member objects.
    """

    index: int = attr.ib(repr=True)
    """Zero-indexed position of this within the queued up chunks for this request.

    Returns
    -------
    builtins.int
        The sequence index for this chunk.
    """

    count: int = attr.ib(repr=True)
    """Total number of expected chunks for the request this is associated with.

    Returns
    -------
    builtins.int
        Total number of chunks to be expected.
    """

    not_found: typing.Sequence[snowflake.Snowflake] = attr.ib(repr=True)
    """Sequence of the snowflakes that were not found while making this request.

    This is only applicable when user ids are specified while making the
    member request the chunk is associated with.

    Returns
    -------
    typing.Sequence[hikari.utilities.snowflake.Snowflake]
        Sequence of user IDs that were not found.
    """

    presences: typing.Mapping[snowflake.Snowflake, presences_.MemberPresence] = attr.ib(repr=False)
    """Mapping of snowflakes to found member presence objects.

    This will be empty if no presences are found or `presences` isn't passed as
    `True` while requesting the member chunks.

    Returns
    -------
    typing.Mapping[hikari.utilities.snowflake.Snowflake, hikari.models.presences.MemberPresence]
        Mapping of user IDs to corresponding presences.
    """

    nonce: typing.Optional[str] = attr.ib(repr=True)
    """String nonce used to identify the request member chunks are associated with.

    This is the nonce value passed while requesting member chunks.

    Returns
    -------
    builtins.str or builtins.None
        The request nonce if specified, or `builtins.None` otherwise.
    """
