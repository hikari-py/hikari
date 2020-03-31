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
"""Provides a facade around the :obj:`hikari.net.shard.ShardConnection`
implementation which handles parsing and initializing the object from a
configuration, as well as restarting it if it disconnects.

Additional functions and coroutines are provided to update the presence on the
shard using models defined in :mod:`hikari.core`.
"""
__all__ = ["ShardState", "ShardClient"]

import abc
import asyncio
import contextlib
import datetime
import enum
import logging
import signal
import time
import typing

import aiohttp

from hikari.internal import more_asyncio
from hikari.internal import more_logging
from hikari.core import events
from hikari.core import gateway_entities
from hikari.core import guilds
from hikari.core.clients import gateway_config
from hikari.net import codes
from hikari.net import errors
from hikari.net import ratelimits
from hikari.net import shard

_EventT = typing.TypeVar("_EventT", bound=events.HikariEvent)


@enum.unique
class ShardState(enum.IntEnum):
    """Describes the state of a shard."""

    #: The shard is not running.
    NOT_RUNNING = 0
    #: The shard is undergoing the initial connection handshake.
    HANDSHAKE = enum.auto()
    #: The initialization handshake has completed. We are waiting for the shard
    #: to receive the ``READY`` event.
    WAITING_FOR_READY = enum.auto()
    #: The shard is ``READY``.
    READY = enum.auto()
    #: The shard has disconnected and is currently attempting to reconnect
    #: again.
    RECONNECTING = enum.auto()
    #: The shard is currently shutting down permanently.
    STOPPING = enum.auto()
    #: The shard has shut down and is no longer connected.
    STOPPED = enum.auto()


class WebsocketClientBase(abc.ABC):
    """Base for any socket-based communication medium to provide functionality
    for more automated control given certain method constraints.
    """

    logger: logging.Logger

    @abc.abstractmethod
    async def start(self):
        """Starts the component."""

    @abc.abstractmethod
    async def close(self, wait: bool = True):
        """Shuts down the component."""

    @abc.abstractmethod
    async def join(self):
        """Waits for the component to terminate."""

    def run(self):
        """Performs the same job as :meth:`start`, but provides additional
        preparation such as registering OS signal handlers for interrupts,
        and preparing the initial event loop.

        This enables the client to be run immediately without having to
        set up the :mod:`asyncio` event loop manually first.
        """
        loop = asyncio.get_event_loop()

        def sigterm_handler(*_):
            raise KeyboardInterrupt()

        ex = None

        try:
            with contextlib.suppress(NotImplementedError):
                # Not implemented on Windows
                loop.add_signal_handler(signal.SIGTERM, sigterm_handler)

            loop.run_until_complete(self.start())
            loop.run_until_complete(self.join())

            self.logger.info("client has shut down")

        except KeyboardInterrupt as _ex:
            self.logger.info("received signal to shut down client")
            loop.run_until_complete(self.close())
            # Apparently you have to alias except clauses or you get an
            # UnboundLocalError.
            ex = _ex
        finally:
            loop.run_until_complete(self.close(True))
            with contextlib.suppress(NotImplementedError):
                # Not implemented on Windows
                loop.remove_signal_handler(signal.SIGTERM)

        if ex:
            raise ex from ex


class ShardClient(WebsocketClientBase):
    """The primary interface for a single shard connection. This contains
    several abstractions to enable usage of the low level gateway network
    interface with the higher level constructs in :mod:`hikari.core`.

    Parameters
    ----------
    shard_id : :obj:`int`
        The ID of this specific shard.
    config : :obj:`gateway_config.GatewayConfig`
        The gateway configuration to use to initialize this shard.
    low_level_dispatch : :obj:`typing.Callable` [ [ :obj:`Shard`, :obj:`str`, :obj:`typing.Any` ] ]
        A function that is fed any low-level event payloads. This will consist
        of three arguments: an :obj:`Shard` which is this shard instance,
        a :obj:`str` of the raw event name, and any naive raw payload that was
        passed with the event. The expectation is the function passed here
        will pass the payload onto any event handling and state handling system
        to be transformed into a higher-level representation.
    url : :obj:`str`
        The URL to connect the gateway to.

    Notes
    -----
    Generally, you want to use :class:`GatewayClient` rather than this class
    directly, as that will handle sharding where enabled and applicable, and
    provides a few more bits and pieces that may be useful such as state
    management and event dispatcher integration. and If you want to customize
    this, you can subclass it and simply override anything you want.
    """

    __slots__ = (
        "logger",
        "_dispatch",
        "_client",
        "_status",
        "_activity",
        "_idle_since",
        "_is_afk",
        "_task",
        "_shard_state",
    )

    def __init__(
        self,
        shard_id: int,
        config: gateway_config.GatewayConfig,
        low_level_dispatch: typing.Callable[["ShardClient", str, typing.Any], None],
        url: str,
    ) -> None:
        self.logger = more_logging.get_named_logger(self, shard_id)
        self._dispatch = low_level_dispatch
        self._activity = config.initial_activity
        self._idle_since = config.initial_idle_since
        self._is_afk = config.initial_is_afk
        self._status = config.initial_status
        self._shard_state = ShardState.NOT_RUNNING
        self._task = None
        self._client = shard.ShardConnection(
            compression=config.use_compression,
            connector=config.protocol.connector if config.protocol is not None else None,
            debug=config.debug,
            dispatch=self._dispatch,
            initial_presence=self._create_presence_pl(
                status=config.initial_status,
                activity=config.initial_activity,
                idle_since=config.initial_idle_since,
                is_afk=config.initial_is_afk,
            ),
            intents=config.intents,
            large_threshold=config.large_threshold,
            proxy_auth=config.protocol.proxy_auth if config.protocol is not None else None,
            proxy_headers=config.protocol.proxy_headers if config.protocol is not None else None,
            proxy_url=config.protocol.proxy_url if config.protocol is not None else None,
            session_id=None,
            seq=None,
            shard_id=shard_id,
            shard_count=config.shard_config.shard_count,
            ssl_context=config.protocol.ssl_context if config.protocol is not None else None,
            token=config.token,
            url=url,
            verify_ssl=config.protocol.verify_ssl if config.protocol is not None else None,
            version=config.version,
        )

    @property
    def client(self) -> shard.ShardConnection:
        """
        Returns
        -------
        :obj:`hikari.net.gateway.GatewayClient`
            The low-level gateway client used for this shard.
        """
        return self._client

    #: TODO: use enum
    @property
    def status(self) -> guilds.PresenceStatus:
        """
        Returns
        -------
        :obj:`guilds.PresenceStatus`
            The current user status for this shard.
        """
        return self._status

    @property
    def activity(self) -> typing.Optional[gateway_entities.GatewayActivity]:
        """
        Returns
        -------
        :obj:`hikari.core.gateway_entities.GatewayActivity`, optional
            The current activity for the user on this shard, or ``None`` if
            there is no activity.
        """
        return self._activity

    @property
    def idle_since(self) -> typing.Optional[datetime.datetime]:
        """
        Returns
        -------
        :obj:`datetime.datetime`, optional
            The timestamp when the user of this shard appeared to be idle, or
            ``None`` if not applicable.
        """
        return self._idle_since

    @property
    def is_afk(self) -> bool:
        """
        Returns
        -------
        :obj:`bool`
            ``True`` if the user is AFK, ``False`` otherwise.
        """
        return self._is_afk

    async def start(self):
        """Connect to the gateway on this shard and schedule tasks to keep this
        connection alive. Wait for the shard to dispatch a ``READY`` event, and
        then return.
        """
        if self._shard_state not in (ShardState.NOT_RUNNING, ShardState.STOPPED):
            raise RuntimeError("Cannot start a shard twice")

        self.logger.debug("starting shard")
        self._shard_state = ShardState.HANDSHAKE
        self._task = asyncio.create_task(self._keep_alive())
        self.logger.info("waiting for READY")
        completed, _ = await asyncio.wait(
            [self._task, self._client.identify_event.wait()], return_when=asyncio.FIRST_COMPLETED
        )

        if self._task in completed:
            raise self._task.exception()

        self._shard_state = ShardState.WAITING_FOR_READY

        completed, _ = await asyncio.wait(
            [self._task, self._client.ready_event.wait()], return_when=asyncio.FIRST_COMPLETED
        )

        if self._task in completed:
            raise self._task.exception()

        self.logger.info("now READY")
        self._shard_state = ShardState.READY

    async def join(self) -> None:
        """Wait for the shard to shut down fully."""
        await self._task if self._task is not None else more_asyncio.completed_future()

    async def close(self, wait: bool = True) -> None:
        """Request that the shard shuts down.

        Parameters
        ----------
        wait : :obj:`bool`
            If ``True`` (default), then wait for the client to shut down fully.
            If ``False``, only send the signal to shut down, but do not wait
            for it explicitly.
        """
        if self._shard_state != ShardState.STOPPING:
            self._shard_state = ShardState.STOPPING
            self.logger.debug("stopping shard")
            await self._client.close()
            if wait:
                await self._task
            with contextlib.suppress():
                self._task.result()

    async def _keep_alive(self):
        back_off = ratelimits.ExponentialBackOff(maximum=None)
        last_start = time.perf_counter()
        do_not_back_off = True

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
                await self._client.connect()
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

                if not ex.can_resume:
                    self._client.seq = None
                    self._client.session_id = None
                do_not_back_off = True
                await asyncio.sleep(5)
            except errors.GatewayMustReconnectError:
                self.logger.warning("instructed by Discord to reconnect")
                self._client.seq = None
                self._client.session_id = None
                do_not_back_off = True
                await asyncio.sleep(5)
            except errors.GatewayServerClosedConnectionError as ex:
                if ex.close_code in (
                    codes.GatewayCloseCode.RATE_LIMITED,
                    codes.GatewayCloseCode.SESSION_TIMEOUT,
                    codes.GatewayCloseCode.INVALID_SEQ,
                    codes.GatewayCloseCode.UNKNOWN_ERROR,
                    codes.GatewayCloseCode.SESSION_TIMEOUT,
                    codes.GatewayCloseCode.NORMAL_CLOSURE,
                ):
                    self.logger.warning("disconnected by Discord, will attempt to reconnect")
                else:
                    self.logger.error("disconnected by Discord, %s: %s", type(ex).__name__, ex.reason)
                    raise ex
            except errors.GatewayClientClosedError:
                self.logger.warning("shutting down")
                return
            except Exception as ex:
                self.logger.debug("propagating unexpected exception %s", exc_info=ex)
                raise ex

    async def update_presence(
        self,
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
        status : :obj:`guilds.PresenceStatus`
            The new status to set.
        activity : :obj:`hikari.core.gateway_entities.GatewayActivity`, optional
            The new activity to set.
        idle_since : :obj:`datetime.datetime`, optional
            The time to show up as being idle since, or ``None`` if not
            applicable.
        is_afk : :obj:`bool`
            ``True`` if the user should be marked as AFK, or ``False``
            otherwise.
        """
        status = self._status if status is ... else status
        activity = self._activity if activity is ... else activity
        idle_since = self._idle_since if idle_since is ... else idle_since
        is_afk = self._is_afk if is_afk is ... else is_afk

        presence = self._create_presence_pl(status=status, activity=activity, idle_since=idle_since, is_afk=is_afk)
        await self._client.update_presence(presence)

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
            "idle_since": idle_since.timestamp() if idle_since is not None else None,
            "game": activity.serialize() if activity is not None else None,
            "afk": is_afk,
        }
