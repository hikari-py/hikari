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
"""Basic implementation of a cache for general bots and gateway apps."""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = ["InMemoryCacheComponentImpl"]

import logging
import typing

from hikari import errors
from hikari.api import cache
from hikari.impl import in_memory_schema
from hikari.models import channels
from hikari.models import emojis
from hikari.models import guilds
from hikari.models import intents as intents_
from hikari.models import presences
from hikari.utilities import iterators

if typing.TYPE_CHECKING:
    from hikari.api import rest as rest_app
    from hikari.models import users
    from hikari.utilities import snowflake


_LOGGER: typing.Final[logging.Logger] = logging.getLogger("hikari.cache")


class InMemoryCacheComponentImpl(cache.ICacheComponent):
    """In-memory cache implementation."""

    def __init__(self, app: rest_app.IRESTApp, intents: typing.Optional[intents_.Intent]) -> None:
        self._app = app
        self._intents = intents
        self._table = in_memory_schema.InMemorySchema()

    @property
    @typing.final
    def app(self) -> rest_app.IRESTApp:
        return self._app

    def get_me(self) -> typing.Optional[users.OwnUser]:
        return self._table.get_me()

    def set_me(self, me: users.OwnUser) -> typing.Optional[users.OwnUser]:
        return self._table.update_me(me)

    async def get_guild(self, guild_id: snowflake.Snowflake) -> typing.Optional[guilds.GatewayGuild]:
        self._assert_has_intent(intents_.Intent.GUILDS)
        return self._table.get_guild(guild_id)

    async def set_guild(self, new_guild: guilds.GatewayGuild) -> typing.Optional[guilds.GatewayGuild]:
        self._assert_has_intent(intents_.Intent.GUILDS)
        return self._table.update_guild(new_guild)

    async def set_initial_unavailable_guilds(self, *guild_ids: snowflake.Snowflake) -> None:
        if self._is_intent_enabled(intents_.Intent.GUILDS):
            self._table.create_initial_guilds(*guild_ids)
        else:
            _LOGGER.debug("ignoring initial unavailable guilds from READY event as GUILDS intent not set")

    async def set_guild_availability(self, guild_id: snowflake.Snowflake, is_available: bool) -> None:
        self._assert_has_intent(intents_.Intent.GUILDS)
        return self._table.set_guild_availability(guild_id, is_available)

    async def delete_guild(self, guild_id: snowflake.Snowflake) -> typing.Optional[guilds.GatewayGuild]:
        self._assert_has_intent(intents_.Intent.GUILDS)
        return self._table.delete_guild(guild_id)

    def iter_guilds(self) -> iterators.LazyIterator[guilds.GatewayGuild]:
        return self._table.iter_guilds()

    async def get_guild_channel(self, channel_id: snowflake.Snowflake) -> typing.Optional[channels.GuildChannel]:
        return self._table.get_guild_channel(channel_id)

    def iter_guild_channels(self, guild_id: snowflake.Snowflake) -> iterators.LazyIterator[channels.GuildChannel]:
        return self._table.iter_guild_channels(guild_id)

    async def get_emoji(self, emoji_id: snowflake.Snowflake) -> typing.Optional[emojis.KnownCustomEmoji]:
        return self._table.get_guild_emoji(emoji_id)

    def iter_guild_emojis(self, guild_id: snowflake.Snowflake) -> iterators.LazyIterator[emojis.KnownCustomEmoji]:
        return self._table.iter_guild_emojis(guild_id)

    async def get_guild_role(
        self, guild_id: snowflake.Snowflake, role_id: snowflake.Snowflake
    ) -> typing.Optional[guilds.Role]:
        return self._table.get_guild_role(guild_id, role_id)

    def iter_guild_roles(self, guild_id: snowflake.Snowflake) -> iterators.LazyIterator[guilds.Role]:
        return self._table.iter_guild_roles(guild_id)

    async def get_guild_member(
        self, guild_id: snowflake.Snowflake, user_id: snowflake.Snowflake
    ) -> typing.Optional[guilds.Member]:
        return self._table.get_guild_member(guild_id, user_id)

    def iter_guild_members(self, guild_id: snowflake.Snowflake) -> iterators.LazyIterator[guilds.Member]:
        return self._table.iter_guild_members(guild_id)

    async def get_guild_presence(
        self, guild_id: snowflake.Snowflake, user_id: snowflake.Snowflake
    ) -> typing.Optional[presences.MemberPresence]:
        return self._table.get_guild_presence(guild_id, user_id)

    def iter_guild_presences(self, guild_id: snowflake.Snowflake) -> iterators.LazyIterator[presences.MemberPresence]:
        return self._table.iter_guild_presences(guild_id)

    def _assert_has_intent(self, intents: intents_.Intent, /) -> None:
        if self._intents is not None and self._intents ^ intents:
            raise errors.MissingIntentError(intents)

    def _is_intent_enabled(self, intents: intents_.Intent, /) -> bool:
        return self._intents is None or self._intents & intents
