# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021 davfsa
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

__all__: typing.List[str] = [
    "CacheAware",
    "EventManagerAware",
    "EntityFactoryAware",
    "EventFactoryAware",
    "ExecutorAware",
    "GatewayBotAware",
    "IntentsAware",
    "NetworkSettingsAware",
    "RESTAware",
    "RESTBotAware",
    "Runnable",
    "InteractionServerAware",
    "ShardAware",
    "VoiceAware",
]

import typing

from hikari import presences
from hikari import undefined
from hikari.internal import fast_protocol

if typing.TYPE_CHECKING:
    import datetime
    from concurrent import futures

    from hikari import channels
    from hikari import config
    from hikari import guilds
    from hikari import intents as intents_
    from hikari import snowflakes
    from hikari import users as users_
    from hikari.api import cache as cache_
    from hikari.api import entity_factory as entity_factory_
    from hikari.api import event_factory as event_factory_
    from hikari.api import event_manager as event_manager_
    from hikari.api import interaction_server as interaction_server_
    from hikari.api import rest as rest_
    from hikari.api import shard as gateway_shard
    from hikari.api import voice as voice_


@typing.runtime_checkable
class NetworkSettingsAware(fast_protocol.FastProtocolChecking, typing.Protocol):
    """Structural supertype for any component aware of network settings."""

    __slots__: typing.Sequence[str] = ()

    @property
    def http_settings(self) -> config.HTTPSettings:
        """HTTP settings in use by this component."""
        raise NotImplementedError

    @property
    def proxy_settings(self) -> config.ProxySettings:
        """Proxy settings in use by this component."""
        raise NotImplementedError


@typing.runtime_checkable
class EventManagerAware(fast_protocol.FastProtocolChecking, typing.Protocol):
    """Structural supertype for a event manager-aware object.

    event manager-aware components are able to manage event listeners and waiters.
    """

    __slots__: typing.Sequence[str] = ()

    @property
    def event_manager(self) -> event_manager_.EventManager:
        """Event manager for this object."""
        raise NotImplementedError


@typing.runtime_checkable
class EntityFactoryAware(fast_protocol.FastProtocolChecking, typing.Protocol):
    """Structural supertype for an entity factory-aware object.

    These components will be able to construct library entities.
    """

    __slots__: typing.Sequence[str] = ()

    @property
    def entity_factory(self) -> entity_factory_.EntityFactory:
        """Entity factory implementation for this object."""
        raise NotImplementedError


@typing.runtime_checkable
class ExecutorAware(fast_protocol.FastProtocolChecking, typing.Protocol):
    """Structural supertype for an executor-aware object.

    These components will contain an `executor` attribute that may return
    a `concurrent.futures.Executor` or `None` if the
    default `asyncio` thread pool for the event loop is used.
    """

    __slots__: typing.Sequence[str] = ()

    @property
    def executor(self) -> typing.Optional[futures.Executor]:
        """Executor to use for blocking operations.

        This may return `None` if the default `asyncio` thread pool
        should be used instead.
        """
        raise NotImplementedError


@typing.runtime_checkable
class EventFactoryAware(fast_protocol.FastProtocolChecking, typing.Protocol):
    """Structural supertype for an event factory-aware object.

    These components are able to construct library events.
    """

    __slots__: typing.Sequence[str] = ()

    @property
    def event_factory(self) -> event_factory_.EventFactory:
        """Event factory component."""
        raise NotImplementedError


@typing.runtime_checkable
class IntentsAware(fast_protocol.FastProtocolChecking, typing.Protocol):
    """A component that is aware of the application intents."""

    __slots__: typing.Sequence[str] = ()

    @property
    def intents(self) -> intents_.Intents:
        """Intents registered for the application."""
        raise NotImplementedError


@typing.runtime_checkable
class RESTAware(
    EntityFactoryAware, NetworkSettingsAware, ExecutorAware, fast_protocol.FastProtocolChecking, typing.Protocol
):
    """Structural supertype for a REST-aware object.

    These are able to perform REST API calls.
    """

    __slots__: typing.Sequence[str] = ()

    @property
    def rest(self) -> rest_.RESTClient:
        """REST client to use for HTTP requests."""
        raise NotImplementedError


@typing.runtime_checkable
class VoiceAware(fast_protocol.FastProtocolChecking, typing.Protocol):
    """Structural supertype for a voice-aware object.

    This is an object that provides a `voice` property to allow the creation
    of custom voice client instances.
    """

    __slots__: typing.Sequence[str] = ()

    @property
    def voice(self) -> voice_.VoiceComponent:
        """Voice connection manager component for this application."""
        raise NotImplementedError


@typing.runtime_checkable
class ShardAware(
    IntentsAware,
    NetworkSettingsAware,
    ExecutorAware,
    VoiceAware,
    fast_protocol.FastProtocolChecking,
    typing.Protocol,
):
    """Structural supertype for a shard-aware object.

    These will expose a mapping of shards, the intents in use
    and the bot user object.
    """

    __slots__: typing.Sequence[str] = ()

    @property
    def heartbeat_latencies(self) -> typing.Mapping[int, float]:
        """Mapping of shard ID to heartbeat latency.

        Any shards that are not yet started will be `float('nan')`.
        """  # noqa: D401 - Imperative mood
        raise NotImplementedError

    @property
    def heartbeat_latency(self) -> float:
        """Average heartbeat latency of all started shards.

        If no shards are started, this will return `float('nan')`.
        """  # noqa: D401 - Imperative mood
        raise NotImplementedError

    @property
    def shards(self) -> typing.Mapping[int, gateway_shard.GatewayShard]:
        """Mapping of shards in this application instance.

        Each shard ID is mapped to the corresponding shard instance.

        If the application has not started, it is acceptable to assume the
        result of this call will be an empty mapping.
        """  # noqa: D401 - Imperative mood
        raise NotImplementedError

    @property
    def shard_count(self) -> int:
        """Number of shards in the total application.

        This may not be the same as the size of `shards`. If the application
        is auto-sharded, this may be `0` until the shards are started.
        """  # noqa: D401 - Imperative mood
        raise NotImplementedError

    def get_me(self) -> typing.Optional[users_.OwnUser]:
        """Return the bot user, if known.

        This should be available as soon as the bot has fired the
        `hikari.events.lifetime_events.StartingEvent`.

        Until then, this may or may not be `None`.

        Returns
        -------
        typing.Optional[hikari.users.OwnUser]
            The bot user, if known, otherwise `None`.
        """
        raise NotImplementedError

    async def update_presence(
        self,
        *,
        status: undefined.UndefinedOr[presences.Status] = undefined.UNDEFINED,
        idle_since: undefined.UndefinedNoneOr[datetime.datetime] = undefined.UNDEFINED,
        activity: undefined.UndefinedNoneOr[presences.Activity] = undefined.UNDEFINED,
        afk: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
    ) -> None:
        """Update the presence on all shards.

        This call will patch the presence on each shard. This means that
        unless you explicitly specify a parameter, the previous value will be
        retained. This means you do not have to track the global presence
        in your code.

        .. note::
            This will only send the update payloads to shards that are alive.
            Any shards that are not alive will cache the new presence for
            when they do start.

        .. note::
            If you want to set presences per shard, access the shard you wish
            to update (e.g. by using `GatewayBot.shards`), and call
            `hikari.api.shard.GatewayShard.update_presence` on that shard.
            This method is simply a facade to make performing this in bulk
            simpler.

        Other Parameters
        ----------------
        idle_since : hikari.undefined.UndefinedNoneOr[datetime.datetime]
            The datetime that the user started being idle. If undefined, this
            will not be changed.
        afk : hikari.undefined.UndefinedOr[bool]
            If `True`, the user is marked as AFK. If `False`,
            the user is marked as being active. If undefined, this will not be
            changed.
        activity : hikari.undefined.UndefinedNoneOr[hikari.presences.Activity]
            The activity to appear to be playing. If undefined, this will not be
            changed.
        status : hikari.undefined.UndefinedOr[hikari.presences.Status]
            The web status to show. If undefined, this will not be changed.
        """
        raise NotImplementedError

    async def update_voice_state(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        channel: typing.Optional[snowflakes.SnowflakeishOr[channels.GuildVoiceChannel]],
        *,
        self_mute: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        self_deaf: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
    ) -> None:
        """Update the voice state for this bot in a given guild.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild or guild ID to update the voice state for.
        channel : typing.Optional[hikari.snowflakes.SnowflakeishOr[hikari.channels.GuildVoiceChannel]]
            The channel or channel ID to update the voice state for. If `None`
            then the bot will leave the voice channel that it is in for the
            given guild.
        self_mute : bool
            If specified and `True`, the bot will mute itself in that
            voice channel. If `False`, then it will unmute itself.
        self_deaf : bool
            If specified and `True`, the bot will deafen itself in that
            voice channel. If `False`, then it will undeafen itself.

        Raises
        ------
        RuntimeError
            If the guild passed isn't covered by any of the shards in this sharded
            client.
        """

    async def request_guild_members(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        *,
        include_presences: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        query: str = "",
        limit: int = 0,
        users: undefined.UndefinedOr[snowflakes.SnowflakeishSequence[users_.User]] = undefined.UNDEFINED,
        nonce: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        """Request for a guild chunk.

        .. note::
            To request the full list of members, set `query` to `""` (empty
            string) and `limit` to `0`.

        Parameters
        ----------
        guild: hikari.guilds.Guild
            The guild to request chunk for.

        Other Parameters
        ----------------
        include_presences: hikari.undefined.UndefinedOr[bool]
            If provided, whether to request presences.
        query: str
            If not `""`, request the members which username starts with the string.
        limit: int
            Maximum number of members to send matching the query.
        users: hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishSequence[hikari.users.User]]
            If provided, the users to request for.
        nonce: hikari.undefined.UndefinedOr[str]
            If provided, the nonce to be sent with guild chunks.

        Raises
        ------
        ValueError
            When trying to specify `users` with `query`/`limit`, if `limit` is not between
            0 and 100, both inclusive or if `users` length is over 100.
        hikari.errors.MissingIntentError
            When trying to request presences without the `GUILD_MEMBERS` or when trying to
            request the full list of members without `GUILD_PRESENCES`.
        RuntimeError
            If the guild passed isn't covered by any of the shards in this sharded
            client.
        """


@typing.runtime_checkable
class InteractionServerAware(RESTAware, EntityFactoryAware, fast_protocol.FastProtocolChecking, typing.Protocol):
    """Structural supertype for a interaction REST server-aware object."""

    __slots__: typing.Sequence[str] = ()

    @property
    def interaction_server(self) -> interaction_server_.InteractionServer:
        """Interaction server this app is bound to."""
        raise NotImplementedError


@typing.runtime_checkable
class CacheAware(fast_protocol.FastProtocolChecking, typing.Protocol):
    """Structural supertype for a cache-aware object.

    Any cache-aware objects are able to access the Discord application cache.
    """

    __slots__: typing.Sequence[str] = ()

    @property
    def cache(self) -> cache_.Cache:
        """Immutable cache implementation for this object."""
        raise NotImplementedError


@typing.runtime_checkable
class Runnable(fast_protocol.FastProtocolChecking, typing.Protocol):
    """Structural super-type for an application which can be run independently."""

    __slots__: typing.Sequence[str] = ()

    @property
    def is_alive(self) -> bool:
        """Whether the application is running or not.

        This is useful as some functions might raise
        `hikari.errors.ComponentStateConflictError` if this is
        `False`.
        """
        raise NotImplementedError

    async def close(self) -> None:
        """Kill the application by shutting all components down."""

    async def join(self) -> None:
        """Wait indefinitely until the application closes.

        This can be placed in a task and cancelled without affecting the
        application runtime itself. Any exceptions raised by shards will be
        propagated to here.
        """
        raise NotImplementedError

    def run(self) -> None:
        """Start the application and block until it's finished running."""
        raise NotImplementedError

    async def start(self) -> None:
        """Start the application and then return."""
        raise NotImplementedError


@typing.runtime_checkable
class GatewayBotAware(
    RESTAware,
    Runnable,
    ShardAware,
    EventFactoryAware,
    EventManagerAware,
    CacheAware,
    fast_protocol.FastProtocolChecking,
    typing.Protocol,
):
    """Structural supertype for a component that has all the gateway components."""

    __slots__: typing.Sequence[str] = ()

    async def join(self, until_close: bool = True) -> None:
        """Wait indefinitely until the application closes.

        This can be placed in a task and cancelled without affecting the
        application runtime itself. Any exceptions raised by shards will be
        propagated to here.

        Other Parameters
        ----------------
        until_close : bool
            Defaults to `True`. If set, the waiter will stop as soon as
            a request for shut down is processed. This can allow you to break
            and begin closing your own resources.

            If `False`, then this will wait until all shards' tasks
            have died.
        """
        raise NotImplementedError

    def run(
        self,
        *,
        activity: typing.Optional[presences.Activity] = None,
        afk: bool = False,
        close_passed_executor: bool = False,
        idle_since: typing.Optional[datetime.datetime] = None,
        ignore_session_start_limit: bool = False,
        large_threshold: int = 250,
        status: presences.Status = presences.Status.ONLINE,
        shard_ids: typing.Optional[typing.AbstractSet[int]] = None,
        shard_count: typing.Optional[int] = None,
    ) -> None:
        """Start the bot and block until it's finished running.

        Other Parameters
        ----------------
        activity : typing.Optional[hikari.presences.Activity]
            The initial activity to display in the bot user presence, or
            `None` (default) to not show any.
        afk : bool
            The initial AFK state to display in the bot user presence, or
            `False` (default) to not show any.
        close_passed_executor : bool
            Defaults to `False`. If `True`, any custom
            `concurrent.futures.Executor` passed to the constructor will be
            shut down when the application terminates. This does not affect the
            default executor associated with the event loop, and will not
            do anything if you do not provide a custom executor to the
            constructor.
        idle_since : typing.Optional[datetime.datetime]
            The `datetime.datetime` the user should be marked as being idle
            since, or `None` (default) to not show this.
        ignore_session_start_limit : bool
            Defaults to `False`. If `False`, then attempting
            to start more sessions than you are allowed in a 24 hour window
            will throw a `hikari.errors.GatewayError` rather than going ahead
            and hitting the IDENTIFY limit, which may result in your token
            being reset. Setting to `True` disables this behavior.
        large_threshold : int
            Threshold for members in a guild before it is treated as being
            "large" and no longer sending member details in the `GUILD CREATE`
            event. Defaults to `250`.
        shard_ids : typing.Optional[typing.AbstractSet[int]]
            The shard IDs to create shards for. If not `None`, then
            a non-`None` `shard_count` must ALSO be provided. Defaults to
            `None`, which means the Discord-recommended count is used
            for your application instead.
        shard_count : typing.Optional[int]
            The number of shards to use in the entire distributed application.
            Defaults to `None` which results in the count being
            determined dynamically on startup.
        status : hikari.presences.Status
            The initial status to show for the user presence on startup.
            Defaults to `hikari.presences.Status.ONLINE`.
        """
        raise NotImplementedError

    async def start(
        self,
        *,
        activity: typing.Optional[presences.Activity] = None,
        afk: bool = False,
        idle_since: typing.Optional[datetime.datetime] = None,
        ignore_session_start_limit: bool = False,
        large_threshold: int = 250,
        shard_ids: typing.Optional[typing.AbstractSet[int]] = None,
        shard_count: typing.Optional[int] = None,
        status: presences.Status = presences.Status.ONLINE,
    ) -> None:
        """Start the bot, wait for all shards to become ready, and then return.

        Other Parameters
        ----------------
        activity : typing.Optional[hikari.presences.Activity]
            The initial activity to display in the bot user presence, or
            `None` (default) to not show any.
        afk : bool
            The initial AFK state to display in the bot user presence, or
            `False` (default) to not show any.
        idle_since : typing.Optional[datetime.datetime]
            The `datetime.datetime` the user should be marked as being idle
            since, or `None` (default) to not show this.
        ignore_session_start_limit : bool
            Defaults to `False`. If `False`, then attempting
            to start more sessions than you are allowed in a 24 hour window
            will throw a `hikari.errors.GatewayError` rather than going ahead
            and hitting the IDENTIFY limit, which may result in your token
            being reset. Setting to `True` disables this behavior.
        large_threshold : int
            Threshold for members in a guild before it is treated as being
            "large" and no longer sending member details in the `GUILD CREATE`
            event. Defaults to `250`.
        shard_ids : typing.Optional[typing.AbstractSet[int]]
            The shard IDs to create shards for. If not `None`, then
            a non-`None` `shard_count` must ALSO be provided. Defaults to
            `None`, which means the Discord-recommended count is used
            for your application instead.
        shard_count : typing.Optional[int]
            The number of shards to use in the entire distributed application.
            Defaults to `None` which results in the count being
            determined dynamically on startup.
        status : hikari.presences.Status
            The initial status to show for the user presence on startup.
            Defaults to `hikari.presences.Status.ONLINE`.
        """
        raise NotImplementedError


@typing.runtime_checkable
class RESTBotAware(InteractionServerAware, Runnable, fast_protocol.FastProtocolChecking, typing.Protocol):
    """Structural supertype for a component that has all the RESTful components."""

    __slots__: typing.Sequence[str] = ()
