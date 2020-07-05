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
"""Core interface for a cache implementation."""
from __future__ import annotations

__all__: typing.Final[typing.List[str]] = ["ICacheComponent"]

import abc
import typing

from hikari.api import component

if typing.TYPE_CHECKING:
    from hikari.models import channels
    from hikari.models import emojis
    from hikari.models import guilds
    from hikari.models import presences
    from hikari.models import users
    from hikari.utilities import iterators
    from hikari.utilities import snowflake


class ICacheComponent(component.IComponent, abc.ABC):
    """Interface describing the operations a cache component should provide.

    This will be used by the gateway and HTTP API to cache specific types of
    objects that the application should attempt to remember for later, depending
    on how this is implemented. The requirement for this stems from the
    assumption by Discord that bot applications will maintain some form of
    "memory" of the events that occur.

    The implementation may choose to use a simple in-memory collection of
    objects, or may decide to use a distributed system such as a Redis cache
    for cross-process bots.
    """

    __slots__: typing.Sequence[str] = ()

    @abc.abstractmethod
    def get_me(self) -> typing.Optional[users.OwnUser]:
        # Always expect caches to store this in-memory as it is needed regularly.
        ...

    @abc.abstractmethod
    def set_me(self, me: users.OwnUser) -> typing.Optional[users.OwnUser]:
        # Always expect caches to store this in-memory as it is needed regularly.
        ...

    @abc.abstractmethod
    async def get_guild(self, guild_id: snowflake.Snowflake) -> typing.Optional[guilds.GatewayGuild]:
        ...

    @abc.abstractmethod
    async def set_guild(self, new_guild: guilds.GatewayGuild) -> typing.Optional[guilds.GatewayGuild]:
        ...

    @abc.abstractmethod
    async def set_initial_unavailable_guilds(self, *guild_ids: snowflake.Snowflake) -> None:
        ...

    @abc.abstractmethod
    async def set_guild_availability(self, guild_id: snowflake.Snowflake, is_available: bool) -> None:
        ...

    @abc.abstractmethod
    async def delete_guild(self, guild_id: snowflake.Snowflake) -> typing.Optional[guilds.GatewayGuild]:
        ...

    @abc.abstractmethod
    def iter_guilds(self) -> iterators.LazyIterator[guilds.GatewayGuild]:
        ...

    @abc.abstractmethod
    async def get_guild_channel(self, channel_id: snowflake.Snowflake) -> typing.Optional[channels.GuildChannel]:
        ...

    @abc.abstractmethod
    def iter_guild_channels(self, guild_id: snowflake.Snowflake) -> iterators.LazyIterator[channels.GuildChannel]:
        ...

    @abc.abstractmethod
    async def get_emoji(self, emoji_id: snowflake.Snowflake) -> typing.Optional[emojis.KnownCustomEmoji]:
        ...

    @abc.abstractmethod
    def iter_guild_emojis(self, guild_id: snowflake.Snowflake) -> iterators.LazyIterator[emojis.KnownCustomEmoji]:
        ...

    @abc.abstractmethod
    async def get_guild_role(
        self, guild_id: snowflake.Snowflake, role_id: snowflake.Snowflake
    ) -> typing.Optional[guilds.Role]:
        ...

    @abc.abstractmethod
    def iter_guild_roles(self, guild_id: snowflake.Snowflake) -> iterators.LazyIterator[guilds.Role]:
        ...

    @abc.abstractmethod
    async def get_guild_member(
        self, guild_id: snowflake.Snowflake, user_id: snowflake.Snowflake
    ) -> typing.Optional[guilds.Member]:
        ...

    @abc.abstractmethod
    def iter_guild_members(self, guild_id: snowflake.Snowflake) -> iterators.LazyIterator[guilds.Member]:
        ...

    @abc.abstractmethod
    async def get_guild_presence(
        self, guild_id: snowflake.Snowflake, user_id: snowflake.Snowflake
    ) -> typing.Optional[presences.MemberPresence]:
        ...

    @abc.abstractmethod
    def iter_guild_presences(self, guild_id: snowflake.Snowflake) -> iterators.LazyIterator[presences.MemberPresence]:
        ...
