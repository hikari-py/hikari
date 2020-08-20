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

__all__: typing.Final[typing.List[str]] = [
    "AsyncCallbackT",
    "EventT_co",
    "EventT_inv",
    "PredicateT",
    "CacheAware",
    "DispatcherAware",
    "EntityFactoryAware",
    "EventFactoryAware",
    "ExecutorAware",
    "ChunkerAware",
    "NetworkSettingsAware",
    "RESTAware",
    "ShardAware",
    "VoiceAware",
    "BotAware",
]

import typing

if typing.TYPE_CHECKING:
    import concurrent.futures

    from hikari import config
    from hikari import intents as intents_
    from hikari import users
    from hikari.api import cache as cache_
    from hikari.api import chunker as chunker_
    from hikari.api import entity_factory as entity_factory_
    from hikari.api import event_dispatcher
    from hikari.api import event_factory as event_factory_
    from hikari.api import rest as rest_
    from hikari.api import shard as gateway_shard
    from hikari.api import voice as voice_

    # noinspection PyUnresolvedReferences
    from hikari.events import base_events  # noqa F401 - Unused (False positive)


EventT_co = typing.TypeVar("EventT_co", bound="base_events.Event", covariant=True)
"""Type-hint for a covariant event implementation instance.

This will bind to the bound event type, or any subclass of that type.
"""

EventT_inv = typing.TypeVar("EventT_inv", bound="base_events.Event")
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


class NetworkSettingsAware(typing.Protocol):
    """Structural supertype for any component aware of network settings."""

    __slots__: typing.Sequence[str] = ()

    @property
    def http_settings(self) -> config.HTTPSettings:
        """Return the HTTP settings in use by this component.

        Returns
        -------
        hikari.config.HTTPSettings
            The HTTP settings in use.
        """
        raise NotImplementedError

    @property
    def proxy_settings(self) -> config.ProxySettings:
        """Return the proxy settings in use by this component.

        Returns
        -------
        hikari.config.ProxySettings
            The proxy settings in use.
        """
        raise NotImplementedError


@typing.runtime_checkable
class CacheAware(typing.Protocol):
    """Structural supertype for a cache-aware object.

    Any cache-aware objects are able to access the Discord application cache.
    """

    __slots__: typing.Sequence[str] = ()

    @property
    def cache(self) -> cache_.Cache:
        """Return the immutable cache implementation for this object.

        Returns
        -------
        hikari.api.cache.Cache
            The cache component for this object.
        """
        raise NotImplementedError

    @property
    def is_stateless(self) -> bool:
        """Return `builtins.True` if the cache is stateless.

        Returns
        -------
        builtins.bool
            `builtins.True` if the cache is stateless. Otherwise,
            `builtins.False`.
        """
        raise NotImplementedError


@typing.runtime_checkable
class DispatcherAware(typing.Protocol):
    """Structural supertype for a dispatcher-aware object.

    Dispatcher-aware components are able to register and dispatch
    event listeners and waiters.
    """

    __slots__: typing.Sequence[str] = ()

    @property
    def dispatcher(self) -> event_dispatcher.EventDispatcher:
        """Return the event dispatcher for this object.

        Returns
        -------
        hikari.api.event_dispatcher.EventDispatcher
            The event dispatcher component.
        """
        raise NotImplementedError


@typing.runtime_checkable
class EntityFactoryAware(typing.Protocol):
    """Structural supertype for an entity factory-aware object.

    These components will be able to construct library entities.
    """

    __slots__: typing.Sequence[str] = ()

    @property
    def entity_factory(self) -> entity_factory_.EntityFactory:
        """Return the entity factory implementation for this object.

        Returns
        -------
        hikari.api.entity_factory.EntityFactory
            The entity factory component.
        """
        raise NotImplementedError


@typing.runtime_checkable
class ExecutorAware(typing.Protocol):
    """Structural supertype for an executor-aware object.

    These components will contain an `executor` attribute that may return
    a `concurrent.futures.Executor` or `builtins.None` if the
    default `asyncio` thread pool for the event loop is used.
    """

    __slots__: typing.Sequence[str] = ()

    @property
    def executor(self) -> typing.Optional[concurrent.futures.Executor]:
        """Return the executor to use for blocking operations.

        This may return `builtins.None` if the default `asyncio` thread pool
        should be used instead.

        Returns
        -------
        typing.Optional[concurrent.futures.Executor]
            The executor to use, or `builtins.None` to use the `asyncio` default
            instead.
        """
        raise NotImplementedError


@typing.runtime_checkable
class EventFactoryAware(typing.Protocol):
    """Structural supertype for an event factory-aware object.

    These components are able to construct library events.
    """

    __slots__: typing.Sequence[str] = ()

    @property
    def event_factory(self) -> event_factory_.EventFactory:
        """Return the event factory component.

        Returns
        -------
        hikari.api.event_factory.EventFactory
            The event factory component.
        """
        raise NotImplementedError


@typing.runtime_checkable
class ChunkerAware(typing.Protocol):
    """Structural supertype for a guild chunker-aware object.

    These are able to request member chunks for guilds via the gateway to
    retrieve mass member and presence information in bulk.
    """

    __slots__: typing.Sequence[str] = ()

    @property
    def chunker(self) -> chunker_.GuildChunker:
        """Return the guild chunker component.

        Returns
        -------
        hikari.api.chunker.GuildChunker
            The guild chunker component.
        """
        raise NotImplementedError


@typing.runtime_checkable
class RESTAware(EntityFactoryAware, NetworkSettingsAware, ExecutorAware, CacheAware, typing.Protocol):
    """Structural supertype for a REST-aware object.

    These are able to perform REST API calls.
    """

    __slots__: typing.Sequence[str] = ()

    @property
    def rest(self) -> rest_.RESTClient:
        """Return the REST client to use for HTTP requests.

        Returns
        -------
        hikari.api.rest.RESTClient
            The REST client to use.
        """
        raise NotImplementedError


@typing.runtime_checkable
class VoiceAware(typing.Protocol):
    """Structural supertype for a voice-aware object.

    This is an object that provides a `voice` property to allow the creation
    of custom voice client instances.
    """

    __slots__: typing.Sequence[str] = ()

    @property
    def voice(self) -> voice_.VoiceComponent:
        """Return the voice connection manager component for this application.

        Returns
        -------
        hikari.api.voice.VoiceComponent
            The voice component for the application.
        """
        raise NotImplementedError


@typing.runtime_checkable
class ShardAware(NetworkSettingsAware, ExecutorAware, CacheAware, ChunkerAware, VoiceAware, typing.Protocol):
    """Structural supertype for a shard-aware object.

    These will expose a mapping of shards, the intents in use
    and the bot user object.
    """

    __slots__: typing.Sequence[str] = ()

    @property
    def heartbeat_latencies(self) -> typing.Mapping[int, float]:
        """Return a mapping of shard ID to heartbeat latency.

        Any shards that are not yet started will be `float('nan')`.

        Returns
        -------
        typing.Mapping[builtins.int, builtins.float]
            Each shard ID mapped to the corresponding heartbeat latency in
            seconds.
        """
        raise NotImplementedError

    @property
    def heartbeat_latency(self) -> float:
        """Return the average heartbeat latency of all started shards.

        If no shards are started, this will return `float('nan')`.

        Returns
        -------
        builtins.float
            The average heartbeat latency of all started shards, or
            `float('nan')` if no shards are started.
        """
        raise NotImplementedError

    @property
    def intents(self) -> typing.Optional[intents_.Intents]:
        """Return the intents registered for the application.

        If no intents are in use, `builtins.None` is returned instead.

        Returns
        -------
        typing.Optional[hikari.intents.Intent]
            The intents registered on this application.
        """
        raise NotImplementedError

    @property
    def me(self) -> typing.Optional[users.OwnUser]:
        """Return the bot user, if known.

        This should be available as soon as the bot has fired the
        `hikari.events.lifetime_events.StartingEvent`.

        Until then, this may or may not be `builtins.None`.

        Returns
        -------
        typing.Optional[hikari.users.OwnUser]
            The bot user, if known, otherwise `builtins.None`.
        """
        raise NotImplementedError

    @property
    def shards(self) -> typing.Mapping[int, gateway_shard.GatewayShard]:
        """Return a mapping of shards in this application instance.

        Each shard ID is mapped to the corresponding shard instance.

        If the application has not started, it is acceptable to assume the
        result of this call will be an empty mapping.

        Returns
        -------
        typing.Mapping[int, hikari.api.shard.GatewayShard]
            The shard mapping.
        """
        raise NotImplementedError

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
        raise NotImplementedError


@typing.runtime_checkable
class BotAware(RESTAware, ShardAware, EventFactoryAware, DispatcherAware, typing.Protocol):
    """Structural supertype for a component that is aware of all internals."""
