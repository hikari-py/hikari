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
"""Implementation of a simple voice management system."""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = []

import asyncio

# noinspection PyUnresolvedReferences
import logging
import typing

from hikari import channels
from hikari import errors
from hikari import guilds
from hikari import snowflakes
from hikari.api import event_dispatcher
from hikari.api import voice
from hikari.events import voice_events
from hikari.impl import bot

if typing.TYPE_CHECKING:
    _VoiceEventCallbackT = typing.Callable[[voice_events.VoiceEvent], typing.Coroutine[None, typing.Any, None]]


_LOGGER: typing.Final[logging.Logger] = logging.getLogger("hikari.voice.management")


_VoiceConnectionT = typing.TypeVar("_VoiceConnectionT", bound="voice.VoiceConnection")


class VoiceComponentImpl(voice.VoiceComponent):
    """A standard voice component management implementation.

    This is the regular implementation you will generally use to connect to
    voice channels with.
    """

    __slots__: typing.Sequence[str] = ("_app", "_connections", "_dispatcher")

    def __init__(self, app: bot.BotApp, dispatcher: event_dispatcher.EventDispatcher) -> None:
        self._app = app
        self._dispatcher = dispatcher
        self._connections: typing.Dict[snowflakes.Snowflake, voice.VoiceConnection] = {}
        self._dispatcher.subscribe(voice_events.VoiceEvent, self._on_voice_event)

    @property
    def app(self) -> bot.BotApp:
        return self._app

    @property
    def connections(self) -> typing.Mapping[snowflakes.Snowflake, voice.VoiceConnection]:
        return self._connections.copy()

    async def disconnect(self) -> None:
        if self._connections:
            _LOGGER.info("shutting down %s voice connection(s)", len(self._connections))
            await asyncio.gather(*(c.disconnect() for c in self._connections.values()))

    async def close(self) -> None:
        await self.disconnect()
        self._dispatcher.unsubscribe(voice_events.VoiceEvent, self._on_voice_event)

    async def connect_to(
        self,
        channel: snowflakes.SnowflakeishOr[channels.GuildVoiceChannel],
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        *,
        deaf: bool = False,
        mute: bool = False,
        voice_connection_type: typing.Type[_VoiceConnectionT],
        **kwargs: typing.Any,
    ) -> _VoiceConnectionT:
        guild_id = snowflakes.Snowflake(guild)
        # TODO: this and the same logic in channels.py and guilds.py logic should go in a file somewhere
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

        state_event, server_event = await asyncio.wait_for(
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
            "joined voice channel %s in guild %s via shard %s using endpoint %s. Session will be %s. "
            "Delegating to voice websocket",
            state_event.state.channel_id,
            state_event.state.guild_id,
            shard_id,
            server_event.endpoint,
            state_event.state.session_id,
        )

        try:
            voice_connection = await voice_connection_type.initialize(
                channel_id=snowflakes.Snowflake(channel),
                debug=self._app.is_debug_enabled,
                endpoint=server_event.endpoint,
                guild_id=guild_id,
                on_close=self._on_connection_close,
                owner=self,
                session_id=state_event.state.session_id,
                shard_id=shard_id,
                token=server_event.token,
                user_id=user_id,
                **kwargs,
            )
        except Exception:
            _LOGGER.debug(
                "error occurred in initialization, leaving voice channel %s in guild %s again", channel, guild
            )
            await asyncio.wait_for(shard.update_voice_state(guild, None), timeout=5.0)
            raise

        self._connections[guild_id] = voice_connection
        return voice_connection

    @staticmethod
    def _init_state_update_predicate(
        guild_id: snowflakes.Snowflake, user_id: snowflakes.Snowflake,
    ) -> typing.Callable[[voice_events.VoiceStateUpdateEvent], bool]:
        def predicate(event: voice_events.VoiceStateUpdateEvent) -> bool:
            return event.state.guild_id == guild_id and event.state.user_id == user_id

        return predicate

    @staticmethod
    def _init_server_update_predicate(
        guild_id: snowflakes.Snowflake,
    ) -> typing.Callable[[voice_events.VoiceServerUpdateEvent], bool]:
        def predicate(event: voice_events.VoiceServerUpdateEvent) -> bool:
            return event.guild_id == guild_id

        return predicate

    async def _on_connection_close(self, connection: voice.VoiceConnection) -> None:
        try:
            del self._connections[connection.guild_id]

            # Leave the voice channel explicitly, otherwise we will just appear to
            # not leave properly.
            await self._app.shards[connection.shard_id].update_voice_state(
                guild=connection.guild_id, channel=None,
            )

            _LOGGER.debug(
                "successfully unregistered voice connection %s to guild %s and left voice channel %s",
                connection,
                connection.guild_id,
                connection.channel_id,
            )

        except KeyError:
            _LOGGER.warning(
                "ignored closure of phantom unregistered voice connection %s to guild %s. Perhaps this is a bug?",
                connection,
                connection.guild_id,
            )

    async def _on_voice_event(self, event: voice_events.VoiceEvent) -> None:
        if event.guild_id in self._connections:
            connection = self._connections[event.guild_id]
            _LOGGER.debug("notifying voice connection %s in guild %s of event %s", connection, event.guild_id, event)
            await connection.notify(event)
