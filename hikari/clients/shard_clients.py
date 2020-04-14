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
"""Provides a facade around :obj:`hikari.net.shard.ShardConnection`.

This handles parsing and initializing the object from a configuration, as
well as restarting it if it disconnects.

Additional functions and coroutines are provided to update the presence on the
shard using models defined in :mod:`hikari`.
"""
from __future__ import annotations

__all__ = ["ShardState", "ShardClient"]

import asyncio
import contextlib
import datetime
import enum
import time
import typing

import aiohttp

from hikari import errors
from hikari import events
from hikari import gateway_entities
from hikari import guilds
from hikari.clients import configs
from hikari.clients import runnable
from hikari.internal import more_logging
from hikari.net import codes
from hikari.net import ratelimits
from hikari.net import shard
from hikari.state import event_dispatchers
from hikari.state import raw_event_consumers


@enum.unique
class ShardState(enum.IntEnum):
    """Describes the state of a shard."""

    #: The shard is not running.
    NOT_RUNNING = 0

    #: The shard is undergoing the initial connection handshake.
    CONNECTING = enum.auto()

    #: The initialization handshake has completed. We are waiting for the shard
    #: to receive the ``READY`` event.
    WAITING_FOR_READY = enum.auto()

    #: The shard is ``READY``.
    READY = enum.auto()

    #: The shard has sent a request to ``RESUME`` and is waiting for a response.
    RESUMING = enum.auto()

    #: The shard is currently shutting down permanently.
    STOPPING = enum.auto()

    #: The shard has shut down and is no longer connected.
    STOPPED = enum.auto()


class ShardClient(runnable.RunnableClient):
    """The primary interface for a single shard connection.

    This contains several abstractions to enable usage of the low
    level gateway network interface with the higher level constructs
    in :mod:`hikari`.

    Parameters
    ----------
    shard_id : :obj:`int`
        The ID of this specific shard.
    shard_id : :obj:`int`
        The number of shards that make up this distributed application.
    config : :obj:`hikari.clients.configs.WebsocketConfig`
        The gateway configuration to use to initialize this shard.
    raw_event_consumer_impl : :obj:`hikari.state.raw_event_consumers.RawEventConsumer`
        The consumer of a raw event.
    url : :obj:`str`
        The URL to connect the gateway to.
    dispatcher : :obj:`hikari.state.event_dispatchers.EventDispatcher`, optional
        The high level event dispatcher to use for dispatching start and stop
        events. Set this to :obj:`None` to disable that functionality (useful if
        you use a gateway manager to orchestrate multiple shards instead and
        provide this functionality there). Defaults to :obj:`None` if
        unspecified.

    Notes
    -----
    Generally, you want to use
    :obj:`hikari.clients.gateway_managers.GatewayManager` rather than this class
    directly, as that will handle sharding where enabled and applicable, and
    provides a few more bits and pieces that may be useful such as state
    management and event dispatcher integration. and If you want to customize
    this, you can subclass it and simply override anything you want.
    """

    __slots__ = (
        "logger",
        "_raw_event_consumer",
        "_connection",
        "_status",
        "_activity",
        "_idle_since",
        "_is_afk",
        "_task",
        "_shard_state",
        "_dispatcher",
    )

    def __init__(
        self,
        shard_id: int,
        shard_count: int,
        config: configs.WebsocketConfig,
        raw_event_consumer_impl: raw_event_consumers.RawEventConsumer,
        url: str,
        dispatcher: typing.Optional[event_dispatchers.EventDispatcher] = None,
    ) -> None:
        super().__init__(more_logging.get_named_logger(self, f"#{shard_id}"))
        self._raw_event_consumer = raw_event_consumer_impl
        self._activity = config.initial_activity
        self._idle_since = config.initial_idle_since
        self._is_afk = config.initial_is_afk
        self._status = config.initial_status
        self._shard_state = ShardState.NOT_RUNNING
        self._task = None
        self._dispatcher = dispatcher
        self._connection = shard.ShardConnection(
            compression=config.gateway_use_compression,
            connector=config.tcp_connector,
            debug=config.debug,
            dispatch=lambda c, n, pl: raw_event_consumer_impl.process_raw_event(self, n, pl),
            initial_presence=self._create_presence_pl(
                status=config.initial_status,
                activity=config.initial_activity,
                idle_since=config.initial_idle_since,
                is_afk=config.initial_is_afk,
            ),
            intents=config.intents,
            large_threshold=config.large_threshold,
            proxy_auth=config.proxy_auth,
            proxy_headers=config.proxy_headers,
            proxy_url=config.proxy_url,
            session_id=None,
            seq=None,
            shard_id=shard_id,
            shard_count=shard_count,
            ssl_context=config.ssl_context,
            token=config.token,
            url=url,
            verify_ssl=config.verify_ssl,
            version=config.gateway_version,
        )

    @property
    def connection(self) -> shard.ShardConnection:
        """Low-level gateway client used for this shard.

        Returns
        -------
        :obj:`hikari.net.shard.ShardConnection`
            The low-level gateway client used for this shard.
        """
        return self._connection

    @property
    def shard_id(self) -> int:
        """Shard ID.

        Returns
        -------
        :obj:`int`
            The 0-indexed shard ID.
        """
        return self._connection.shard_id

    @property
    def shard_count(self) -> int:
        """Shard count.

        Returns
        -------
        :obj:`int`
            The number of shards that make up this bot.
        """
        return self._connection.shard_count

    # Ignore docstring not starting in an imperative mood
    @property
    def status(self) -> guilds.PresenceStatus:  # noqa: D401
        """Current user status for this shard.

        Returns
        -------
        :obj:`hikari.guilds.PresenceStatus`
            The current user status for this shard.
        """
        return self._status

    # Ignore docstring not starting in an imperative mood
    @property
    def activity(self) -> typing.Optional[gateway_entities.GatewayActivity]:  # noqa: D401
        """Current activity for the user status for this shard.

        Returns
        -------
        :obj:`hikari.gateway_entities.GatewayActivity`, optional
            The current activity for the user on this shard, or :obj:`None` if
            there is no activity.
        """
        return self._activity

    @property
    def idle_since(self) -> typing.Optional[datetime.datetime]:
        """Timestamp when the user of this shard appeared to be idle.

        Returns
        -------
        :obj:`datetime.datetime`, optional
            The timestamp when the user of this shard appeared to be idle, or
            :obj:`None` if not applicable.
        """
        return self._idle_since

    # Ignore docstring not starting in an imperative mood
    @property
    def is_afk(self) -> bool:  # noqa: D401
        """:obj:`True` if the user is AFK, :obj:`False` otherwise.

        Returns
        -------
        :obj:`bool`
            :obj:`True` if the user is AFK, :obj:`False` otherwise.
        """
        return self._is_afk

    @property
    def latency(self) -> float:
        """Latency between sending a HEARTBEAT and receiving an ACK.

        Returns
        -------
        :obj:`float`
            The heartbeat latency in seconds. This will be ``float('nan')``
            until the first heartbeat is performed.
        """
        return self._connection.heartbeat_latency

    @property
    def heartbeat_interval(self) -> float:
        """Time period to wait between sending HEARTBEAT payloads.

        Returns
        -------
        :obj:`float`
            The heartbeat interval in seconds. This will be ``float('nan')``
            until the connection has received a ``HELLO`` payload.
        """
        return self._connection.heartbeat_interval

    @property
    def reconnect_count(self) -> int:
        """Count of number of times the internal connection has reconnected.

        This includes RESUME and re-IDENTIFY events.

        Returns
        -------
        :obj:`int`
            The number of reconnects this shard has performed.
        """
        return self._connection.reconnect_count

    @property
    def connection_state(self) -> ShardState:
        """State of this shard.

        Returns
        -------
        :obj:`ShardState`
            The state of this shard.
        """
        return self._shard_state

    async def start(self):
        """Connect to the gateway on this shard and keep the connection alive.

        This will wait for the shard to dispatch a ``READY`` event, and
        then return.
        """
        if self._shard_state not in (ShardState.NOT_RUNNING, ShardState.STOPPED):
            raise RuntimeError("Cannot start a shard twice")

        self._task = asyncio.create_task(self._keep_alive(), name="ShardClient#keep_alive")

        completed, _ = await asyncio.wait(
            [self._task, self._connection.ready_event.wait()], return_when=asyncio.FIRST_COMPLETED
        )

        if self._task in completed:
            raise self._task.exception()

    async def join(self) -> None:
        """Wait for the shard to shut down fully."""
        if self._task:
            await self._task

    async def close(self) -> None:
        """Request that the shard shuts down.

        This will wait for the client to shut down before returning.
        """
        if self._shard_state != ShardState.STOPPING:
            self._shard_state = ShardState.STOPPING
            self.logger.debug("stopping shard")

            if self._dispatcher is not None:
                await self._dispatcher.dispatch_event(events.StoppingEvent())

            await self._connection.close()

            with contextlib.suppress():
                await self._task

            if self._dispatcher is not None:
                await self._dispatcher.dispatch_event(events.StoppedEvent())

    async def _keep_alive(self):
        back_off = ratelimits.ExponentialBackOff(maximum=None)
        last_start = time.perf_counter()
        do_not_back_off = True

        if self._dispatcher is not None:
            await self._dispatcher.dispatch_event(events.StartingEvent())

        while True:
            try:
                if not do_not_back_off and time.perf_counter() - last_start < 30:
                    next_backoff = next(back_off)
                    self.logger.info(
                        "restarted within 30 seconds, will backoff for %ss", next_backoff,
                    )
                    await asyncio.sleep(next_backoff)
                else:
                    back_off.reset()

                last_start = time.perf_counter()
                do_not_back_off = False

                connect_task = await self._spin_up()

                if self._dispatcher is not None and self.reconnect_count == 0:
                    # Only dispatch this on initial connect, not on reconnect.
                    await self._dispatcher.dispatch_event(events.StartedEvent())

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

            except errors.GatewayClientClosedError:
                self.logger.warning("shutting down")
                return
            except Exception as ex:
                self.logger.debug("propagating unexpected exception %s", exc_info=ex)
                raise ex

    async def _spin_up(self) -> asyncio.Task:
        self.logger.debug("initializing shard")
        self._shard_state = ShardState.CONNECTING

        is_resume = self._connection.seq is not None and self._connection.session_id is not None

        connect_task = asyncio.create_task(self._connection.connect(), name="ShardConnection#connect")

        completed, _ = await asyncio.wait(
            [connect_task, self._connection.hello_event.wait()], return_when=asyncio.FIRST_COMPLETED
        )

        if connect_task in completed:
            raise connect_task.exception()

        self.logger.info("received HELLO, interval is %ss", self.connection.heartbeat_interval)

        completed, _ = await asyncio.wait(
            [connect_task, self._connection.identify_event.wait()], return_when=asyncio.FIRST_COMPLETED
        )

        if connect_task in completed:
            raise connect_task.exception()

        if is_resume:
            self.logger.info("sent RESUME, waiting for RESUMED event")
            self._shard_state = ShardState.RESUMING

            completed, _ = await asyncio.wait(
                [connect_task, self._connection.resumed_event.wait()], return_when=asyncio.FIRST_COMPLETED
            )

            if connect_task in completed:
                raise connect_task.exception()

            self.logger.info("now RESUMED")

        else:
            self.logger.info("sent IDENTIFY, waiting for READY event")

            self._shard_state = ShardState.WAITING_FOR_READY

            completed, _ = await asyncio.wait(
                [connect_task, self._connection.ready_event.wait()], return_when=asyncio.FIRST_COMPLETED
            )

            if connect_task in completed:
                raise connect_task.exception()

            self.logger.info("now READY")

        self._shard_state = ShardState.READY

        return connect_task

    async def update_presence(
        self,
        *,
        status: guilds.PresenceStatus = ...,
        activity: typing.Optional[gateway_entities.GatewayActivity] = ...,
        idle_since: typing.Optional[datetime.datetime] = ...,
        is_afk: bool = ...,
    ) -> None:
        """Update the presence of the user for the shard.

        This will only update arguments that you explicitly specify a value for.
        Any arguments that you do not explicitly provide some value for will
        not be changed.

        Warnings
        --------
        This will fail if the shard is not online.

        Parameters
        ----------
        status : :obj:`hikari.guilds.PresenceStatus`
            If specified, the new status to set.
        activity : :obj:`hikari.gateway_entities.GatewayActivity`, optional
            If specified, the new activity to set.
        idle_since : :obj:`datetime.datetime`, optional
            If specified, the time to show up as being idle since, or
            :obj:`None` if not applicable.
        is_afk : :obj:`bool`
            If specified, whether the user should be marked as AFK.
        """
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
        activity: typing.Optional[gateway_entities.GatewayActivity],
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
        return f"Shard {self.connection.shard_id} in pool of {self.connection.shard_count} shards"

    def __repr__(self) -> str:
        return (
            "ShardClient("
            + ", ".join(
                f"{k}={getattr(self, k)!r}"
                for k in ("shard_id", "shard_count", "connection_state", "heartbeat_interval", "latency")
            )
            + ")"
        )
