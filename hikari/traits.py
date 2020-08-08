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
"""Core app interface for application implementations."""
from __future__ import annotations

__all__: typing.Final[typing.List[str]] = []

import typing

if typing.TYPE_CHECKING:
    import asyncio

    from hikari.api import cache
    from hikari.api import entity_factory
    from hikari.api import event_consumer
    from hikari.api import event_dispatcher
    from hikari.api import event_factory
    from hikari.api import guild_chunker
    from hikari.api import rest
    from hikari.api import shard as gateway_shard
    from hikari.api import voice
    from hikari.events import base_events
    from hikari.utilities import data_binding

EventT_co = typing.TypeVar("EventT_co", bound=base_events.Event, covariant=True)
"""Type-hint for a covariant event implementation instance.

This will bind to the bound event type, or any subclass of that type.
"""

EventT_inv = typing.TypeVar("EventT_inv", bound=base_events.Event)
"""Type-hint for an invariant event implementation instance.

This will bind to the bound event type only. Subclasses and superclasses will 
not be matched.
"""

PredicateT = typing.Callable[[EventT_co], typing.Union[bool, typing.Coroutine[typing.Any, typing.Any, bool]]]
"""Type-hint for an event waiter predicate.

This should be a function or coroutine function that consumes a covariant 
instance of the bound event type and returns a boolean that matches
`builtins.True` if the event is a match for the waiter, or `builtins.False`
otherwise.
"""

# Fixme: shouldn't this be using covariance instead of invariance?
AsyncCallbackT = typing.Callable[[EventT_inv], typing.Coroutine[typing.Any, typing.Any, None]]
"""Type-hint for an asynchronous coroutine function event callback.

This should consume a single argument: the event that was dispatched.

This is not expected to return anything.
"""


@typing.runtime_checkable
class CacheAware(typing.Protocol):
    """Structural supertype for a cache-aware object.

    Any cache-aware objects are able to access the Discord application cache.
    """
    __slots__: typing.Sequence[str] = ()

    @property
    def cache(self) -> cache.ICacheComponent:
        """Return the immutable cache implementation for this object.

        Returns
        -------
        hikari.api.cache.ICacheComponent
            The cache component for this object.
        """


@typing.runtime_checkable
class DispatcherAware(typing.Protocol):
    """Structural supertype for a dispatcher-aware object.

    Dispatcher-aware components are able to register and dispatch
    event listeners and waiters.
    """
    __slots__: typing.Sequence[str] = ()

    @property
    def dispatcher(self) -> event_dispatcher.IEventDispatcherComponent:
        """Return the event dispatcher for this object.

        Returns
        -------
        hikari.api.event_dispatcher.IEventDispatcherComponent
            The event dispatcher component.
        """


@typing.runtime_checkable
class EntityFactoryAware(typing.Protocol):
    """Structural supertype for an entity factory-aware object.

    These components will be able to construct library entities.
    """
    __slots__: typing.Sequence[str] = ()

    @property
    def entity_factory(self) -> entity_factory.IEntityFactoryComponent:
        """Return the entity factory implementation for this object.

        Returns
        -------
        hikari.api.entity_factory.IEntityFactoryComponent
            The entity factory component.
        """


@typing.runtime_checkable
class EventFactoryAware(typing.Protocol):
    """Structural supertype for an event factory-aware object.

    These components are able to construct library events.
    """
    __slots__: typing.Sequence[str] = ()

    @property
    def event_factory(self) -> event_factory.IEventFactoryComponent:
        """Return the event factory component.

        Returns
        -------
        hikari.api.event_factory.IEventFactoryComponent
            The event factory component.
        """


@typing.runtime_checkable
class GuildChunkerAware(typing.Protocol):
    """Structural supertype for a guild chunker-aware object.

    These are able to request member chunks for guilds via the
    gateway to retrieve mass member and presence information in
    bulk.
    """

    __slots__: typing.Sequence[str] = ()

    @property
    def chunker(self) -> guild_chunker.IGuildChunkerComponent:
        """Return the guild chunker component.

        Returns
        -------
        hikari.api.guild_chunker.IGuildChunkerComponent
            The guild chunker component.
        """


@typing.runtime_checkable
class ShardAware(typing.Protocol):
    """Structural supertype for a shard-aware object.

    These will expose a mapping of shards and a
    """

    __slots__: typing.Sequence[str] = ()

    @property
    def shards(self) -> typing.Mapping[int, gateway_shard.IGatewayShard]:
        """Return a mapping of shards in this application instance.

        Each shard ID is mapped to the corresponding shard instance.

        If the application has not started, it is acceptable to assume the
        result of this call will be an empty mapping.

        Returns
        -------
        typing.Mapping[int, hikari.api.shard.IGatewayShard]
            The shard mapping.
        """

    @property
    def shard_count(self) -> int:
        """Return the number of shards in the total application.

        This may not be the same as the size of `shards`. If the application
        is auto-sharded, this may be `0` until the shards are started.

        Returns
        -------
        builtins.int
            The number of shards in the total application.
        """


@typing.runtime_checkable
class VoiceAware(typing.Protocol):
    """Structural supertype for a voice-aware object.

    This is an object that provides a `voice` property to allow the creation
    of custom voice client instances.
    """

    __slots__: typing.Sequence[str] = ()
