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
"""Implementation of a simple voice management system."""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = []

import asyncio

# noinspection PyUnresolvedReferences
import logging
import typing

from hikari import errors
from hikari.api import bot
from hikari.api import voice
from hikari.api.gateway import dispatcher
from hikari.events import voice as voice_events
from hikari.models import channels
from hikari.models import guilds
from hikari.utilities import snowflake

if typing.TYPE_CHECKING:
    _VoiceEventCallbackT = typing.Callable[[voice_events.VoiceEvent], typing.Coroutine[None, typing.Any, None]]


_LOGGER: typing.Final[logging.Logger] = logging.getLogger("hikari.voice.management")


_VoiceConnectionT = typing.TypeVar("_VoiceConnectionT", bound="voice.IVoiceConnection")


class VoiceComponentImpl(voice.IVoiceComponent):
    """A standard voice component management implementation.

    This is the regular implementation you will generally use to connect to
    voice channels with.
    """

    __slots__ = ("_app", "_connections", "_dispatcher")

    def __init__(self, app: bot.IBotApp, event_dispatcher: dispatcher.IEventDispatcherComponent) -> None:
        self._app = app
        self._dispatcher = event_dispatcher
        self._connections: typing.Dict[snowflake.Snowflake, voice.IVoiceConnection] = {}

        self._dispatcher.subscribe(voice_events.VoiceEvent, self._on_voice_event)

    @property
    def app(self) -> bot.IBotApp:
        return self._app

    @property
    def connections(self) -> typing.Mapping[snowflake.Snowflake, voice.IVoiceConnection]:
        return self._connections.copy()

    async def close(self) -> None:
        if self._connections:
            _LOGGER.info("shutting down %s voice connection(s)", len(self._connections))
            await asyncio.gather(*(c.disconnect() for c in self._connections.values()))

        self._dispatcher.unsubscribe(voice_events.VoiceEvent, self._on_voice_event)

    async def connect_to(
        self,
        channel: typing.Union[channels.GuildVoiceChannel, snowflake.UniqueObject],
        guild: typing.Union[guilds.Guild, snowflake.UniqueObject],
        *,
        deaf: bool = False,
        mute: bool = False,
        voice_connection_type: typing.Type[_VoiceConnectionT],
        **kwargs: typing.Any,
    ) -> _VoiceConnectionT:
        guild_id = snowflake.Snowflake(int(guild))
        shard_id = (guild_id >> 22) % self._app.shard_count

        if shard_id is None:
            raise errors.VoiceError(
                "Cannot connect to voice. Ensure the application is configured as a gateway zookeeper and try again."
            )

        if guild_id in self._connections:
            raise errors.VoiceError(
                "The bot is already in a voice channel for this guild. Close the other connection first, or "
                "request that the application moves to the new voice channel instead."
            )

        try:
            shard = self._app.shards[shard_id]
        except KeyError:
            raise errors.VoiceError(
                f"Cannot connect to shard {shard_id}, it is not present in this application."
            ) from None

        if not shard.is_alive:
            # Not sure if I can think of a situation this will happen in... really.
            # Unless the user sleeps for a bit then tries to connect, and in the mean time the
            # shard has disconnected.
            # TODO: make shards declare if they are in the process of reconnecting, if they are, make them wait
            # for a little bit.
            raise errors.VoiceError(f"Cannot connect to shard {shard_id}, the shard is not online.")

        _LOGGER.debug("attempting to connect to voice channel %s in %s via shard %s", channel, guild, shard_id)

        user_id = await shard.get_user_id()
        await asyncio.wait_for(shard.update_voice_state(guild, channel, self_deaf=deaf, self_mute=mute), timeout=5.0)

        _LOGGER.debug(
            "waiting for voice events for connecting to voice channel %s in %s via shard %s", channel, guild, shard_id
        )

        state, server = await asyncio.wait_for(
            asyncio.gather(
                # Voice state update:
                self._dispatcher.wait_for(
                    voice_events.VoiceStateUpdateEvent,
                    timeout=None,
                    predicate=self._init_state_update_predicate(guild_id, user_id),
                ),
                # Server update:
                self._dispatcher.wait_for(
                    voice_events.VoiceServerUpdateEvent,
                    timeout=None,
                    predicate=self._init_server_update_predicate(guild_id),
                ),
            ),
            timeout=10.0,
        )

        _LOGGER.debug(
            "joined voice channel %s in guild %s via shard %s using endpoint %s, starting voice websocket",
            state.state.channel_id,
            state.state.guild_id,
            shard_id,
            server.endpoint,
        )

        voice_connection = await voice_connection_type.initialize(**kwargs)
        self._connections[guild_id] = voice_connection
        return voice_connection

    @staticmethod
    def _init_state_update_predicate(
        guild_id: snowflake.Snowflake, user_id: snowflake.Snowflake,
    ) -> typing.Callable[[voice_events.VoiceStateUpdateEvent], bool]:
        def predicate(event: voice_events.VoiceStateUpdateEvent) -> bool:
            return event.state.guild_id == guild_id and event.state.user_id == user_id

        return predicate

    @staticmethod
    def _init_server_update_predicate(
        guild_id: snowflake.Snowflake,
    ) -> typing.Callable[[voice_events.VoiceServerUpdateEvent], bool]:
        def predicate(event: voice_events.VoiceServerUpdateEvent) -> bool:
            return event.guild_id == guild_id

        return predicate

    async def _on_voice_event(self, event: voice_events.VoiceEvent) -> None:
        if event.guild_id is not None and event.guild_id in self._connections:
            connection = self._connections[event.guild_id]
            _LOGGER.debug("notifying voice connection %s in guild %s of event %s", connection, event.guild_id, event)
            await connection.notify(event)
