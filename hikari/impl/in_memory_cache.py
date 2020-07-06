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

__all__: typing.Final[typing.List[str]] = ["StatefulCacheComponentImpl"]

import array
import bisect
import logging
import reprlib
import typing
import weakref

import attr

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


_LOGGER: typing.Final[logging.Logger] = logging.getLogger("hikari.cache")

_T = typing.TypeVar("_T", bound=snowflake.Unique)
_T_co = typing.TypeVar("_T_co", bound=snowflake.Unique)
_U = typing.TypeVar("_U")


class _IDTable(typing.MutableSet[snowflake.Snowflake]):
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


class _StatefulCacheMappingView(cache.ICacheView[_T], typing.Generic[_T]):
    def __init__(self, items: typing.Mapping[snowflake.Snowflake, _T]) -> None:
        self._data = items

    def __len__(self) -> int:
        return len(self._data)

    def __iter__(self) -> typing.Iterator[_T_co]:
        return iter(self._data.values())

    def __contains__(self, item: typing.Any) -> bool:
        return item in self._data.values()

    def get_item_at(self, index: int) -> _T:
        i = 0
        items = iter(self)

        try:
            while i < index:
                next(items)
        except StopIteration:
            raise IndexError(index)

        return next(items)

    def get_item_with_id(self, sf: snowflake.Snowflake, default: _U = None) -> typing.Union[_T, _U]:
        return self._data.get(sf, default)

    def iterator(self, sf: snowflake.Snowflake) -> iterators.LazyIterator[_T_co]:
        return iterators.FlatLazyIterator(iter(self))


class _EmptyCacheView(cache.ICacheView[_T], typing.Generic[_T]):
    def __len__(self) -> int:
        return 0

    def __iter__(self) -> typing.Iterator[_T_co]:
        yield from ()

    def __contains__(self, item: typing.Any) -> bool:
        return False

    def get_item_at(self, index: int) -> _T:
        raise IndexError(index)

    def get_item_with_id(self, sf: snowflake.Snowflake, default: _U = None) -> typing.Union[_T, _U]:
        return default

    def iterator(self, sf: snowflake.Snowflake) -> iterators.LazyIterator[_T_co]:
        return iterators.FlatLazyIterator(iter(self))


@attr.s(slots=True, repr=False, hash=False, auto_attribs=True)
class GuildRecord:
    id: snowflake.Snowflake
    is_available: typing.Optional[bool] = False
    guild: typing.Optional[guilds.GatewayGuild] = None

    # TODO: some of these will be iterated across more than they will searched by a specific ID...
    # ... identify these cases and convert to lists.
    roles: typing.Optional[typing.MutableMapping[snowflake.Snowflake, guilds.Role]] = None
    members: typing.Optional[typing.MutableMapping[snowflake.Snowflake, guilds.Member]] = None
    presences: typing.Optional[typing.MutableMapping[snowflake.Snowflake, presences.MemberPresence]] = None
    channels: typing.Optional[typing.MutableMapping[snowflake.Snowflake, channels.GuildChannel]] = None
    emojis: typing.Optional[typing.MutableMapping[snowflake.Snowflake, emojis.KnownCustomEmoji]] = None

    def __hash__(self) -> int:
        return hash(self.id)


class StatefulCacheComponentImpl(cache.ICacheComponent):
    """In-memory cache implementation."""

    def __init__(self, app: rest_app.IRESTApp, intents: typing.Optional[intents_.Intent]) -> None:
        self._me: typing.Optional[users.OwnUser] = None
        self._dm_channel_entries: typing.MutableMapping[snowflake.Snowflake, channels.DMChannel] = {}

        # Points to guild record objects.
        self._guild_entries: typing.MutableMapping[snowflake.Snowflake, GuildRecord] = {}
        self._user_entries: typing.MutableMapping[snowflake.Snowflake, users.User] = weakref.WeakValueDictionary()

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

    def delete_guild(self, guild_id: snowflake.Snowflake) -> typing.Optional[guilds.Guild]:
        if guild_id not in self._guild_entries:
            return None

        guild_record = self._guild_entries[guild_id]
        del self._guild_entries[guild_id]
        return guild_record.guild

    def get_me(self) -> typing.Optional[users.OwnUser]:
        return self._me

    def get_guild(self, guild_id: snowflake.Snowflake) -> typing.Optional[guilds.GatewayGuild]:
        if (entry := self._guild_entries.get(guild_id)) is not None:
            if not entry.is_available:
                raise errors.UnavailableGuildError(entry.guild)
            return entry.guild
        return None

    def get_guild_channel(
        self, guild_id: snowflake.Snowflake, channel_id: snowflake.Snowflake
    ) -> typing.Optional[channels.GuildChannel]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is not None and guild_record.channels is not None:
            return guild_record.channels.get(channel_id)

    def get_guild_emoji(
        self, guild_id: snowflake.Snowflake, emoji_id: snowflake.Snowflake
    ) -> typing.Optional[emojis.KnownCustomEmoji]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is not None:
            return guild_record.emojis.get(emoji_id)

    def get_guild_member(
        self, guild_id: snowflake.Snowflake, user_id: snowflake.Snowflake
    ) -> typing.Optional[guilds.Member]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is None or guild_record.members is None:
            return None
        return guild_record.members.get(user_id)

    def get_guild_presence(
        self, guild_id: snowflake.Snowflake, user_id: snowflake.Snowflake
    ) -> typing.Optional[presences.MemberPresence]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is None or guild_record.members is None:
            return None
        return guild_record.presences.get(user_id)

    def get_guild_role(
        self, guild_id: snowflake.Snowflake, role_id: snowflake.Snowflake
    ) -> typing.Optional[guilds.Role]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record.emojis is None or guild_record.roles is None:
            return None
        return guild_record.roles[role_id]

    def get_guilds_view(self) -> cache.ICacheView[guilds.GatewayGuild]:
        for record in self._guild_entries.values():
            if record.guild is not None:
                yield record.guild

    def get_guild_channels_view(self, guild_id: snowflake.Snowflake) -> cache.ICacheView[channels.GuildChannel]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is not None and guild_record.channels is not None:
            return _StatefulCacheMappingView(guild_record.channels)
        return _EmptyCacheView()

    def get_guild_emojis_view(self, guild_id: snowflake.Snowflake) -> cache.ICacheView[emojis.KnownCustomEmoji]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is not None and guild_record.emojis is not None:
            return _StatefulCacheMappingView(guild_record.emojis)
        return _EmptyCacheView()

    def get_guild_members_view(self, guild_id: snowflake.Snowflake) -> cache.ICacheView[guilds.Member]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is not None and guild_record.members is not None:
            return _StatefulCacheMappingView(guild_record.members)

    def get_guild_presences_view(self, guild_id: snowflake.Snowflake) -> cache.ICacheView[presences.MemberPresence]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is not None and guild_record.presences is not None:
            return _StatefulCacheMappingView(guild_record.presences)
        return _EmptyCacheView()

    def get_guild_roles_view(self, guild_id: snowflake.Snowflake) -> cache.ICacheView[guilds.Role]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is not None and guild_record.roles is not None:
            return _StatefulCacheMappingView(guild_record.roles)
        return _EmptyCacheView()

    def set_initial_unavailable_guilds(self, guild_ids: typing.Collection[snowflake.Snowflake]) -> None:
        # Invoked when we receive ON_READY, assume all of these are unavailable on startup.
        self._guild_entries = {guild_id: GuildRecord(guild_id, is_available=False) for guild_id in guild_ids}

    def set_guild_availability(self, guild_id: snowflake.Snowflake, is_available: bool) -> None:
        if guild_id not in self._guild_entries:
            self._guild_entries[guild_id] = GuildRecord(guild_id)

        self._guild_entries[guild_id].is_available = is_available

    def replace_all_guild_channels(
        self, guild_id: snowflake.Snowflake, channel_objs: typing.Collection[channels.GuildChannel]
    ) -> None:
        if guild_id not in self._guild_entries:
            self._guild_entries[guild_id] = GuildRecord(guild_id)

        self._guild_entries[guild_id].channels = sorted(channel_objs, key=lambda c: c.position)

    def replace_all_guild_emojis(
        self, guild_id: snowflake.Snowflake, emoji_objs: typing.Collection[emojis.KnownCustomEmoji]
    ) -> None:
        if guild_id not in self._guild_entries:
            self._guild_entries[guild_id] = GuildRecord(guild_id)

        guild_record = self._guild_entries.get(guild_id)
        if guild_record is not None:
            guild_record.emojis = {emoji_obj.id: emoji_obj for emoji_obj in emoji_objs}

    def replace_all_guild_members(
        self, guild_id: snowflake.Snowflake, member_objs: typing.Collection[guilds.Member]
    ) -> None:
        if guild_id not in self._guild_entries:
            self._guild_entries[guild_id] = GuildRecord(guild_id)

        self._guild_entries[guild_id].members = {}

        for member in member_objs:
            if member.id in self._user_entries:
                member.user = self._user_entries[member.id]
            else:
                self._user_entries[member.id] = member.user
            self._guild_entries[guild_id].members[member.id] = member

    def replace_all_guild_presences(
        self, guild_id: snowflake.Snowflake, presence_objs: typing.Collection[presences.MemberPresence]
    ) -> None:
        if guild_id not in self._guild_entries:
            self._guild_entries[guild_id] = GuildRecord(guild_id)

        self._guild_entries[guild_id].presences = {presence_obj.user_id: presence_obj for presence_obj in presence_objs}

    def replace_all_guild_roles(self, guild_id: snowflake.Snowflake, roles: typing.Collection[guilds.Role]) -> None:
        if guild_id not in self._guild_entries:
            self._guild_entries[guild_id] = GuildRecord(guild_id)

        # Top role first!
        self._guild_entries[guild_id].roles = {
            role.id: role for role in sorted(roles, key=lambda r: r.position, reverse=True)
        }

    def replace_guild(self, new: guilds.GatewayGuild) -> typing.Optional[guilds.GatewayGuild]:
        if new.id not in self._guild_entries:
            self._guild_entries[new.id] = GuildRecord(new.id, guild=new, is_available=True)
            return None

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

    def replace_me(self, new: users.OwnUser, /) -> typing.Optional[users.OwnUser]:
        _LOGGER.debug("setting my user to %s", new)
        old = self._me
        self._me = new
        return old
