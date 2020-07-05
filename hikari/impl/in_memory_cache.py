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

import array
import bisect
import logging
import reprlib
import typing

import attr
import immutables

from hikari import errors
from hikari.api import cache
from hikari.models import channels
from hikari.models import emojis
from hikari.models import guilds
from hikari.models import intents as intents_
from hikari.models import presences
from hikari.utilities import iterators
from hikari.utilities import snowflake

if typing.TYPE_CHECKING:
    from hikari.api import rest as rest_app
    from hikari.models import users
    from hikari.utilities import snowflake


_LOGGER: typing.Final[logging.Logger] = logging.getLogger("hikari.cache")


class InMemoryCacheComponentImpl(cache.ICacheComponent):
    """In-memory cache implementation."""

    def __init__(self, app: rest_app.IRESTApp, intents: typing.Optional[intents_.Intent]) -> None:
        self._me: typing.Optional[users.OwnUser] = None
        self._dm_channel_entries: IDMap[channels.DMChannel] = IDMap()

        # Points to guild record objects.
        self._guild_entries: IDMap[GuildRecord] = IDMap()
        self._guild_channel_entries: IDMap[channels.GuildChannel] = IDMap()
        self._emoji_entries: IDMap[emojis.KnownCustomEmoji] = IDMap()
        self._user_entries: IDMap[UserRecord] = IDMap()
        self._app = app
        self._intents = intents

    @property
    @typing.final
    def app(self) -> rest_app.IRESTApp:
        return self._app

    def _assert_has_intent(self, intents: intents_.Intent, /) -> None:
        if self._intents is not None and self._intents ^ intents:
            raise errors.MissingIntentError(intents)

    def _is_intent_enabled(self, intents: intents_.Intent, /) -> bool:
        return self._intents is None or self._intents & intents

    def get_me(self) -> typing.Optional[users.OwnUser]:
        return self._me

    def set_me(self, new: users.OwnUser, /) -> typing.Optional[users.OwnUser]:
        _LOGGER.debug("setting my user to %s", new)
        old = self._me
        self._me = new
        return old

    async def get_guild(self, guild_id: snowflake.Snowflake) -> typing.Optional[guilds.GatewayGuild]:
        if (entry := self._guild_entries.get(guild_id)) is not None:
            if not entry.is_available:
                raise errors.UnavailableGuildError(entry.guild)
            return entry.guild
        return None

    async def set_initial_unavailable_guilds(self, *guild_ids: snowflake.Snowflake) -> None:
        # Invoked when we receive ON_READY, assume all of these are unavailable on startup.

        _LOGGER.debug("adding %s initial guilds from READY event", len(guild_ids))

        self._guild_entries.set_many((guild_id, GuildRecord(guild_id, is_available=False)) for guild_id in guild_ids)

    async def set_guild(self, new: guilds.GatewayGuild) -> typing.Optional[guilds.GatewayGuild]:
        if new.id not in self._guild_entries:
            _LOGGER.debug("inserting new guild record for %s", new.id)
            self._guild_entries[new.id] = GuildRecord(new.id, guild=new, is_available=True,)
            return None
        else:
            _LOGGER.debug("updating existing guild record for %s", new.id)

        guild_record = self._guild_entries[new.id]
        old = guild_record.guild

        # We have to manually update these because inconsistency by Discord.
        if old is not None:
            new.member_count = old.member_count
            new.joined_at = old.joined_at
            new.is_large = old.is_large

        guild_record.guild = new
        guild_record.is_available = True
        return old

    async def delete_guild(self, guild_id: snowflake.Snowflake) -> typing.Optional[guilds.Guild]:
        if guild_id not in self._guild_entries:
            return None

        guild_record = self._guild_entries[guild_id]
        self._guild_channel_entries.delete_many(guild_record.channels)
        self._emoji_entries.delete_many(guild_record.emojis)

        user_ids_to_remove: typing.List[int] = []

        for member_id in guild_record.members:
            if member_id in self._user_entries:
                entry = self._user_entries[member_id]
                entry.dec()

                if entry.should_be_destroyed:
                    user_ids_to_remove.append(member_id)

        self._user_entries.delete_many(user_ids_to_remove)

        del self._guild_entries[guild_id]
        return guild_record.guild

    async def set_guild_availability(self, guild_id: snowflake.Snowflake, is_available: bool) -> None:
        if guild_id in self._guild_entries:
            self._guild_entries[guild_id].is_available = is_available
        else:
            _LOGGER.debug(
                "guild %s has become %savailable, but it is not cached, so is being ignored",
                guild_id,
                "un" if not is_available else "",
            )

    def iter_guilds(self) -> iterators.FlatLazyIterator[guilds.GatewayGuild]:
        return iterators.FlatLazyIterator(
            record.guild for record in self._guild_entries.values() if record.guild is not None
        )

    async def get_guild_channel(self, channel_id: snowflake.Snowflake) -> typing.Optional[channels.GuildChannel]:
        return self._guild_channel_entries.get(channel_id)

    async def set_all_guild_channels(
        self, guild_id: snowflake.Snowflake, channel_objs: typing.Iterable[channels.GuildChannel]
    ) -> None:
        if (channel_map := self._guild_entries[guild_id].channels) is not None:
            self._guild_channel_entries.delete_many(channel_map)

        self._guild_entries[guild_id].channels = IDTable()
        self._guild_entries[guild_id].channels.add_all(channel.id for channel in channel_objs)
        self._guild_channel_entries.set_many((channel.id, channel) for channel in channel_objs)

    def iter_guild_channels(self, guild_id: snowflake.Snowflake) -> iterators.FlatLazyIterator[channels.GuildChannel]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is None or guild_record.channels is None:
            return iterators.FlatLazyIterator(())

        return iterators.FlatLazyIterator(
            (self._guild_channel_entries.get(channel_id) for channel_id in guild_record.channels)
        )

    async def get_guild_emoji(self, emoji_id: snowflake.Snowflake) -> typing.Optional[emojis.KnownCustomEmoji]:
        return self._emoji_entries.get(emoji_id)

    async def set_all_guild_emojis(
        self, guild_id: snowflake.Snowflake, emoji_objs: typing.Iterable[emojis.KnownCustomEmoji]
    ) -> None:
        if (emojis_map := self._guild_entries[guild_id].emojis) is not None:
            self._emoji_entries.delete_many(emojis_map)

        self._guild_entries[guild_id].emojis = IDTable()
        self._guild_entries[guild_id].emojis.add_all(emoji.id for emoji in emoji_objs)
        self._emoji_entries.set_many((emoji.id, emoji) for emoji in emoji_objs)

    def iter_guild_emojis(self, guild_id: snowflake.Snowflake) -> iterators.FlatLazyIterator[emojis.KnownCustomEmoji]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is None or guild_record.emojis is None:
            return iterators.FlatLazyIterator(())

        return iterators.FlatLazyIterator((self._emoji_entries.get(emoji_id) for emoji_id in guild_record.emojis))

    async def get_guild_role(
        self, guild_id: snowflake.Snowflake, role_id: snowflake.Snowflake
    ) -> typing.Optional[guilds.Role]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record.emojis is None or guild_record.roles is None:
            return None
        return guild_record.roles[role_id]

    async def set_all_guild_roles(self, guild_id: snowflake.Snowflake, roles: typing.Iterable[guilds.Role]) -> None:
        self._guild_entries[guild_id].roles = IDMap()
        self._guild_entries[guild_id].roles.set_many((role.id, role) for role in roles)

    def iter_guild_roles(self, guild_id: snowflake.Snowflake) -> iterators.FlatLazyIterator[guilds.Role]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is None or guild_record.roles is None:
            return iterators.FlatLazyIterator(())

        return iterators.FlatLazyIterator(guild_record.roles.values())

    async def get_guild_member(
        self, guild_id: snowflake.Snowflake, user_id: snowflake.Snowflake
    ) -> typing.Optional[guilds.Member]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is None or guild_record.members is None:
            return None
        return guild_record.members.get(user_id)

    async def set_all_guild_members(
        self, guild_id: snowflake.Snowflake, members: typing.Iterable[guilds.Member]
    ) -> None:
        self._guild_entries[guild_id].members = IDMap()
        self._guild_entries[guild_id].members.set_many((member.id, member) for member in members)

    def iter_guild_members(self, guild_id: snowflake.Snowflake) -> iterators.LazyIterator[guilds.Member]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is None or guild_record.members is None:
            return iterators.FlatLazyIterator(())

        return iterators.FlatLazyIterator(guild_record.members.values())

    async def get_guild_presence(
        self, guild_id: snowflake.Snowflake, user_id: snowflake.Snowflake
    ) -> typing.Optional[presences.MemberPresence]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is None or guild_record.members is None:
            return None
        return guild_record.presences.get(user_id)

    def iter_guild_presences(self, guild_id: snowflake.Snowflake) -> iterators.LazyIterator[presences.MemberPresence]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is None or guild_record.presences is None:
            return iterators.FlatLazyIterator(())

        return iterators.FlatLazyIterator(guild_record.presences.values())

    async def set_all_guild_presences(
        self, guild_id: snowflake.Snowflake, presence_objs: typing.Iterable[presences.MemberPresence]
    ) -> None:
        self._guild_entries[guild_id].presences = IDMap()
        self._guild_entries[guild_id].presences.set_many(
            (presence_obj.user_id, presence_obj) for presence_obj in presence_objs
        )


@attr.s(slots=True, repr=False)
class GuildRecord:
    id: snowflake.Snowflake = attr.ib(hash=True)
    is_available: typing.Optional[bool] = attr.ib(default=None, hash=False)
    guild: typing.Optional[guilds.GatewayGuild] = attr.ib(default=None, hash=False)

    roles: typing.Optional[typing.MutableSequence[guilds.Role]] = attr.ib(default=None, hash=False)
    members: typing.Optional[IDMap[guilds.Member]] = attr.ib(default=None, hash=False)
    presences: typing.Optional[IDMap[presences.MemberPresence]] = attr.ib(default=None, hash=False)

    channels: typing.Optional[IDTable] = attr.ib(default=None, hash=False)
    emojis: typing.Optional[IDTable] = attr.ib(default=None, hash=False)
    voice_states: typing.Optional[IDTable] = attr.ib(default=None, hash=False)


@attr.s(slots=True, repr=False)
class UserRecord:
    user: users.User = attr.ib(hash=True)

    # Users can be in more than one guild, so we have to keep a reference count so that we know
    # when to remove the entire object.
    _ref_count: int = attr.ib(hash=False, default=0)

    def inc(self) -> None:
        self._ref_count += 1

    def dec(self) -> None:
        self._ref_count -= 1

    @property
    def should_be_destroyed(self) -> bool:
        return self._ref_count <= 0


_VT = typing.TypeVar("_VT")


class IDMap(typing.MutableMapping[snowflake.Snowflake, _VT], typing.Generic[_VT]):
    """A hash array mapped trie of snowflakes mapping to a value type."""

    __slots__ = ("_data",)

    def __init__(self) -> None:
        self._data = immutables.Map()

    def __getitem__(self, key: snowflake.Snowflake) -> _VT:
        return self._data[key]

    def __setitem__(self, key: snowflake.Snowflake, value: _VT) -> None:
        self._data = self._data.set(key, value)

    def __delitem__(self, key: snowflake.Snowflake) -> None:
        self._data = self._data.delete(key)

    set = __setitem__
    delete = __delitem__

    def set_many(self, pairs: typing.Iterable[typing.Tuple[snowflake.Snowflake, _VT]]) -> None:
        mutation = self._data.mutate()
        for key, value in pairs:
            mutation[key] = value

        self._data = mutation.finish()

    def delete_many(self, keys: typing.Iterable[int]) -> None:
        mutation = self._data.mutate()

        for key in keys:
            del mutation[key]

        self._data = mutation.finish()

    def __len__(self) -> int:
        return len(self._data)

    def __iter__(self) -> typing.Iterator[snowflake.Snowflake]:
        return iter((snowflake.Snowflake(i) for i in self._data))

    def __repr__(self) -> str:
        return "SnowflakeMapping(" + reprlib.repr(dict(self._data)) + ")"


class IDTable(typing.MutableSet[snowflake.Snowflake]):
    """Compact 64-bit integer bisected-array-set of snowflakes."""

    __slots__ = ("_ids",)

    def __init__(self) -> None:
        self._ids = array.array("Q")

    def add(self, sf: snowflake.Snowflake) -> None:
        if not self._ids:
            self._ids.append(sf)
        else:
            index = bisect.bisect_right(self._ids, sf)
            if self._ids[index - 1] != sf:
                self._ids.insert(index - 1, sf)

    def add_all(self, sfs: typing.Iterable[snowflake.Snowflake]) -> None:
        for sf in sfs:
            self.add(sf)

    def discard(self, sf: snowflake.Snowflake) -> None:
        index = self._index_of(sf)
        if index != -1:
            del self._ids[index]

    def _index_of(self, sf: int) -> int:
        bottom, top = 0, len(self._ids) - 1

        while top - bottom:
            pos = (bottom + top) // 2
            item = self._ids[pos]
            if item == sf:
                return pos

            if item < sf:
                bottom = pos
            else:
                top = pos

        return -1

    def __contains__(self, value: typing.Any) -> bool:
        if not isinstance(value, int):
            return False
        return self._index_of(value) != -1

    def __len__(self) -> int:
        return len(self._ids)

    def __iter__(self) -> typing.Iterator[snowflake.Snowflake]:
        return iter((snowflake.Snowflake(i) for i in self._ids))

    def __repr__(self) -> str:
        return "SnowflakeTable" + reprlib.repr(self._ids)[5:]
