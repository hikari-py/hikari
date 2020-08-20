# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
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
"""Events relating to specific shards connecting and disconnecting."""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = [
    "ShardEvent",
    "ShardStateEvent",
    "ShardConnectedEvent",
    "ShardDisconnectedEvent",
    "ShardReadyEvent",
    "ShardResumedEvent",
]

import abc
import typing

import attr

from hikari.events import base_events
from hikari.utilities import attr_extensions

if typing.TYPE_CHECKING:
    from hikari import snowflakes
    from hikari import traits
    from hikari import users
    from hikari.api import shard as gateway_shard


@attr.s(kw_only=True, slots=True, weakref_slot=False)
class ShardEvent(base_events.Event, abc.ABC):
    """Base class for any event that was shard-specific."""

    @property
    @abc.abstractmethod
    def shard(self) -> gateway_shard.GatewayShard:
        """Shard that received this event.

        Returns
        -------
        hikari.api.shard.GatewayShard
            The shard that triggered the event.
        """


@attr.s(kw_only=True, slots=True, weakref_slot=False)
class ShardStateEvent(ShardEvent, abc.ABC):
    """Base class for any event concerning the state/connectivity of a shard.

    This currently wraps connection/disconnection/ready/resumed events only.
    """


@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, weakref_slot=False)
class ShardConnectedEvent(ShardStateEvent):
    """Event fired when a shard connects."""

    app: traits.RESTAware = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<docstring inherited from ShardEvent>>.


@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, weakref_slot=False)
class ShardDisconnectedEvent(ShardStateEvent):
    """Event fired when a shard disconnects."""

    app: traits.RESTAware = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<docstring inherited from ShardEvent>>.


@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, weakref_slot=False)
class ShardReadyEvent(ShardStateEvent):
    """Event fired when a shard declares it is ready."""

    app: traits.RESTAware = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
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
    hikari.users.OwnUser
        This bot's user.
    """

    unavailable_guilds: typing.Sequence[snowflakes.Snowflake] = attr.ib(repr=False)
    """Sequence of the IDs for all guilds this bot is currently in.

    All guilds will start off "unavailable" and should become available after
    a few seconds of connecting one-by-one.

    Returns
    -------
    typing.Sequence[hikari.snowflakes.Snowflake]
        All guild IDs that the bot is in for this shard.
    """


@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, weakref_slot=False)
class ShardResumedEvent(ShardStateEvent):
    """Event fired when a shard resumes an existing session."""

    app: traits.RESTAware = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<docstring inherited from ShardEvent>>.
