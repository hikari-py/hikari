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
"""Provides a facade around `hikari.net.shards.Shard`.

This handles parsing and initializing the object from a configuration, as
well as restarting it if it disconnects.

Additional functions and coroutines are provided to update the presence on the
shard using models defined in `hikari`.
"""

from __future__ import annotations

__all__ = ["ShardClient", "ShardClientImpl"]

import abc
import asyncio
import logging
import time
import typing

import aiohttp

from hikari import errors
from hikari.clients import runnable
from hikari.clients import shard_states
from hikari.net import codes
from hikari.net import ratelimits
from hikari.net import shards

if typing.TYPE_CHECKING:
    import datetime

    from hikari import gateway_entities
    from hikari import guilds
    from hikari import intents as _intents
    from hikari.clients import components as _components


class ShardClient(runnable.RunnableClient, abc.ABC):
    """Definition of the interface for a conforming shard client."""

    __slots__ = ()

    @property
    @abc.abstractmethod
    def shard_id(self) -> int:
        """Shard ID (this is 0-indexed)."""

    @property
    @abc.abstractmethod
    def shard_count(self) -> int:
        """Count of how many shards make up this bot."""

    @property
    @abc.abstractmethod
    def status(self) -> guilds.PresenceStatus:
        """User status for this shard."""

    @property
    @abc.abstractmethod
    def activity(self) -> typing.Optional[gateway_entities.Activity]:
        """Activity for the user status for this shard.

        This will be `None` if there is no activity.
        """

    @property
    @abc.abstractmethod
    def idle_since(self) -> typing.Optional[datetime.datetime]:
        """Timestamp of when the user of this shard appeared to be idle.

        This will be `None` if not applicable.
        """

    @property
    @abc.abstractmethod
    def is_afk(self) -> bool:
        """Whether the user is appearing as AFK or not.."""

    @property
    @abc.abstractmethod
    def heartbeat_latency(self) -> float:
        """Latency between sending a HEARTBEAT and receiving an ACK in seconds.

        This will be `float("nan")` until the first heartbeat is performed.
        """

    @property
    @abc.abstractmethod
    def heartbeat_interval(self) -> float:
        """Time period to wait between sending HEARTBEAT payloads in seconds.

        This will be `float("nan")` until the connection has received a `HELLO`
        payload.
        """

    @property
    @abc.abstractmethod
    def disconnect_count(self) -> int:
        """Count of number of times this shard's connection has disconnected."""

    @property
    @abc.abstractmethod
    def reconnect_count(self) -> int:
        """Count of number of times this shard's connection has reconnected.

        This includes RESUME and re-IDENTIFY events.
        """

    @property
    @abc.abstractmethod
    def connection_state(self) -> shard_states.ShardState:
        """State of this shard's connection."""

    @property
    @abc.abstractmethod
    def is_connected(self) -> bool:
        """Whether the shard is connected or not."""

    @property
    @abc.abstractmethod
    def seq(self) -> typing.Optional[int]:
        """Sequence ID of the shard.

        This is the number of payloads that have been received since the last
        `IDENTIFY` was sent.
        """

    @property
    @abc.abstractmethod
    def session_id(self) -> typing.Optional[str]:
        """Session ID of the shard connection.

        Will be `None` if there is no session.
        """

    @property
    @abc.abstractmethod
    def version(self) -> float:
        """Version being used for the gateway API."""

    @property
    @abc.abstractmethod
    def intents(self) -> typing.Optional[_intents.Intent]:
        """Intents that are in use for the shard connection.

        If intents are not being used at all, then this will be `None` instead.
        """

    @abc.abstractmethod
    async def update_presence(
        self,
        *,
        status: guilds.PresenceStatus = ...,
        activity: typing.Optional[gateway_entities.Activity] = ...,
        idle_since: typing.Optional[datetime.datetime] = ...,
        is_afk: bool = ...,
    ) -> None:
        """Update the presence of the user for the shard.

        This will only update arguments that you explicitly specify a value for.
        Any arguments that you do not explicitly provide some value for will
        not be changed.

        !!! warning
            This will fail if the shard is not online.

        Parameters
        ----------
        status : hikari.guilds.PresenceStatus
            If specified, the new status to set.
        activity : hikari.gateway_entities.Activity, optional
            If specified, the new activity to set.
        idle_since : datetime.datetime, optional
            If specified, the time to show up as being idle since, or
            `None` if not applicable.
        is_afk : bool
            If specified, whether the user should be marked as AFK.
        """


class ShardClientImpl(ShardClient):
    """The primary interface for a single shard connection.

    This contains several abstractions to enable usage of the low
    level gateway network interface with the higher level constructs
    in `hikari`.

    Parameters
    ----------
    shard_id : int
        The ID of this specific shard.
    shard_id : int
        The number of shards that make up this distributed application.
    components : hikari.clients.components.Components
        The client components that this shard client should be bound by.
        Includes the the gateway configuration to use to initialize this shard
        and the consumer of a raw event.
    url : str
        The URL to connect the gateway to.

    !!! note
        Generally, you want to use
        `hikari.clients.bot_base.BotBase` rather than this class
        directly, as that will handle sharding where enabled and applicable,
        and provides a few more bits and pieces that may be useful such as state
        management and event dispatcher integration. and If you want to customize
        this, you can subclass it and simply override anything you want.
    """

    __slots__ = (
        "_activity",
        "_components",
        "_connection",
        "_idle_since",
        "_is_afk",
        "_raw_event_consumer",
        "_shard_state",
        "_status",
        "_task",
        "logger",
    )

    def __init__(self, shard_id: int, shard_count: int, components: _components.Components, url: str,) -> None:
        super().__init__(logging.getLogger(f"hikari.{type(self).__qualname__}.{shard_id}"))
        self._components = components
        self._raw_event_consumer = components.event_manager
        self._activity = components.config.initial_activity
        self._idle_since = components.config.initial_idle_since
        self._is_afk = components.config.initial_is_afk
        self._status = components.config.initial_status
        self._shard_state = shard_states.ShardState.NOT_RUNNING
        self._task = None
        self._connection = shards.Shard(
            compression=components.config.gateway_use_compression,
            connector=components.config.tcp_connector,
            debug=components.config.debug,
            # This is a bit of a cheat, we should pass a coroutine function here, but
            # instead we just use a lambda that does the transformation we want (replaces the
            # low-level shard argument with the reference to this class object), then return
            # the result of that coroutine. To the low level client, it looks the same :-)
            # (also hides a useless stack frame from tracebacks, I guess).
            dispatcher=lambda c, n, pl: components.event_manager.process_raw_event(self, n, pl),
            initial_presence=self._create_presence_pl(
                status=components.config.initial_status,
                activity=components.config.initial_activity,
                idle_since=components.config.initial_idle_since,
                is_afk=components.config.initial_is_afk,
            ),
            intents=components.config.intents,
            large_threshold=components.config.large_threshold,
            proxy_auth=components.config.proxy_auth,
            proxy_headers=components.config.proxy_headers,
            proxy_url=components.config.proxy_url,
            session_id=None,
            seq=None,
            shard_id=shard_id,
            shard_count=shard_count,
            ssl_context=components.config.ssl_context,
            token=components.config.token,
            url=url,
            verify_ssl=components.config.verify_ssl,
            version=components.config.gateway_version,
        )

    @property
    def shard_id(self) -> int:
        return self._connection.shard_id

    @property
    def shard_count(self) -> int:
        return self._connection.shard_count

    @property
    def status(self) -> guilds.PresenceStatus:
        return self._status

    @property
    def activity(self) -> typing.Optional[gateway_entities.Activity]:
        return self._activity

    @property
    def idle_since(self) -> typing.Optional[datetime.datetime]:
        return self._idle_since

    @property
    def is_afk(self) -> bool:
        return self._is_afk

    @property
    def heartbeat_latency(self) -> float:
        return self._connection.heartbeat_latency

    @property
    def heartbeat_interval(self) -> float:
        return self._connection.heartbeat_interval

    @property
    def disconnect_count(self) -> int:
        return self._connection.disconnect_count

    @property
    def reconnect_count(self) -> int:
        return self._connection.reconnect_count

    @property
    def connection_state(self) -> shard_states.ShardState:
        return self._shard_state

    @property
    def is_connected(self) -> bool:
        return self._connection.is_connected

    @property
    def seq(self) -> typing.Optional[int]:
        return self._connection.seq

    @property
    def session_id(self) -> typing.Optional[str]:
        return self._connection.session_id

    @property
    def version(self) -> float:
        return self._connection.version

    @property
    def intents(self) -> typing.Optional[_intents.Intent]:
        return self._connection.intents

    async def start(self):
        """Connect to the gateway on this shard and keep the connection alive.

        This will wait for the shard to dispatch a `READY` event, and
        then return.
        """
        if self._shard_state not in (shard_states.ShardState.NOT_RUNNING, shard_states.ShardState.STOPPED):
            raise RuntimeError("Cannot start a shard twice")

        self._task = asyncio.create_task(self._keep_alive(), name="ShardClient#keep_alive")

        completed, _ = await asyncio.wait(
            [self._task, self._connection.ready_event.wait()], return_when=asyncio.FIRST_COMPLETED
        )

        for task in completed:
            if ex := task.exception():
                raise ex

    async def join(self) -> None:
        """Wait for the shard to shut down fully."""
        if self._task:
            await self._task

    async def close(self) -> None:
        """Request that the shard shuts down.

        This will wait for the client to shut down before returning.
        """
        if self._shard_state != shard_states.ShardState.STOPPING:
            self._shard_state = shard_states.ShardState.STOPPING
            self.logger.debug("stopping shard")

            await self._connection.close()

            if self._task is not None:
                await self._task

    async def _keep_alive(self):  # pylint: disable=too-many-branches
        back_off = ratelimits.ExponentialBackOff(base=1.85, maximum=600, initial_increment=2)
        last_start = time.perf_counter()
        do_not_back_off = True

        while True:
            try:
                if not do_not_back_off and time.perf_counter() - last_start < 30:
                    next_back_off = next(back_off)
                    self.logger.info(
                        "restarted within 30 seconds, will backoff for %.2fs", next_back_off,
                    )
                    await asyncio.sleep(next_back_off)
                else:
                    back_off.reset()

                last_start = time.perf_counter()
                do_not_back_off = False

                connect_task = await self._spin_up()

                await connect_task
                self.logger.critical("shut down silently! this shouldn't happen!")

            except aiohttp.ClientConnectorError as ex:
                self.logger.exception(
                    "failed to connect to Discord to initialize a websocket connection", exc_info=ex,
                )

            except errors.GatewayZombiedError:
                self.logger.warning("entered a zombie state and will be restarted")

            except errors.GatewayInvalidSessionError as ex:
                if ex.can_resume:
                    self.logger.warning("invalid session, so will attempt to resume")
                else:
                    self.logger.warning("invalid session, so will attempt to reconnect")
                    self._connection.seq = None
                    self._connection.session_id = None

                do_not_back_off = True
                await asyncio.sleep(5)

            except errors.GatewayMustReconnectError:
                self.logger.warning("instructed by Discord to reconnect")
                do_not_back_off = True
                await asyncio.sleep(5)

            except errors.GatewayServerClosedConnectionError as ex:
                if ex.close_code in (
                    codes.GatewayCloseCode.NOT_AUTHENTICATED,
                    codes.GatewayCloseCode.AUTHENTICATION_FAILED,
                    codes.GatewayCloseCode.ALREADY_AUTHENTICATED,
                    codes.GatewayCloseCode.SHARDING_REQUIRED,
                    codes.GatewayCloseCode.INVALID_VERSION,
                    codes.GatewayCloseCode.INVALID_INTENT,
                    codes.GatewayCloseCode.DISALLOWED_INTENT,
                ):
                    self.logger.error("disconnected by Discord, %s: %s", type(ex).__name__, ex.reason)
                    raise ex from None

                self.logger.warning("disconnected by Discord, will attempt to reconnect")

            except errors.GatewayClientDisconnectedError:
                self.logger.warning("unexpected connection close, will attempt to reconnect")

            except errors.GatewayClientClosedError:
                self.logger.warning("gateway client closed by user, will not attempt to restart")
                return
            except Exception as ex:
                self.logger.debug("propagating unexpected exception", exc_info=ex)
                raise ex

    async def _spin_up(self) -> asyncio.Task:
        self.logger.debug("initializing shard")
        self._shard_state = shard_states.ShardState.CONNECTING

        is_resume = self._connection.seq is not None and self._connection.session_id is not None

        connect_task = asyncio.create_task(self._connection.connect(), name="Shard#connect")

        completed, _ = await asyncio.wait(
            [connect_task, self._connection.hello_event.wait()], return_when=asyncio.FIRST_COMPLETED
        )

        for task in completed:
            if ex := task.exception():
                raise ex

        self.logger.info("received HELLO, interval is %ss", self._connection.heartbeat_interval)

        completed, _ = await asyncio.wait(
            [connect_task, self._connection.handshake_event.wait()], return_when=asyncio.FIRST_COMPLETED
        )

        for task in completed:
            if ex := task.exception():
                raise ex

        if is_resume:
            self.logger.info("sent RESUME, waiting for RESUMED event")
            self._shard_state = shard_states.ShardState.RESUMING

            completed, _ = await asyncio.wait(
                [connect_task, self._connection.resumed_event.wait()], return_when=asyncio.FIRST_COMPLETED
            )

            for task in completed:
                if ex := task.exception():
                    raise ex

            self.logger.info("now RESUMED")

        else:
            self.logger.info("sent IDENTIFY, waiting for READY event")

            self._shard_state = shard_states.ShardState.WAITING_FOR_READY

            completed, _ = await asyncio.wait(
                [connect_task, self._connection.ready_event.wait()], return_when=asyncio.FIRST_COMPLETED
            )

            for task in completed:
                if ex := task.exception():
                    raise ex

            self.logger.info("now READY")

        self._shard_state = shard_states.ShardState.READY

        return connect_task

    async def update_presence(
        self,
        *,
        status: guilds.PresenceStatus = ...,
        activity: typing.Optional[gateway_entities.Activity] = ...,
        idle_since: typing.Optional[datetime.datetime] = ...,
        is_afk: bool = ...,
    ) -> None:
        # We wouldn't ever want to do this, so throw an error if it happens.
        if status is ... and activity is ... and idle_since is ... and is_afk is ...:
            raise ValueError("update_presence requires at least one argument to be passed")

        status = self._status if status is ... else status
        activity = self._activity if activity is ... else activity
        idle_since = self._idle_since if idle_since is ... else idle_since
        is_afk = self._is_afk if is_afk is ... else is_afk

        presence = self._create_presence_pl(status=status, activity=activity, idle_since=idle_since, is_afk=is_afk)
        await self._connection.update_presence(presence)

        # If we get this far, the update succeeded probably, or the gateway just died. Whatever.
        self._status = status
        self._activity = activity
        self._idle_since = idle_since
        self._is_afk = is_afk

    @staticmethod
    def _create_presence_pl(
        status: guilds.PresenceStatus,
        activity: typing.Optional[gateway_entities.Activity],
        idle_since: typing.Optional[datetime.datetime],
        is_afk: bool,
    ) -> typing.Dict[str, typing.Any]:
        return {
            "status": status,
            "idle_since": idle_since.timestamp() * 1000 if idle_since is not None else None,
            "game": activity.serialize() if activity is not None else None,
            "afk": is_afk,
        }

    def __str__(self) -> str:
        return f"Shard {self.shard_id} in pool of {self.shard_count} shards"

    def __repr__(self) -> str:
        return (
            "ShardClient("
            + ", ".join(
                f"{k}={getattr(self, k)!r}"
                for k in ("shard_id", "shard_count", "connection_state", "heartbeat_interval", "heartbeat_latency")
            )
            + ")"
        )
