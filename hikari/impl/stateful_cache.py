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

import abc
import array
import bisect
import copy
import logging
import reprlib
import typing

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
    import datetime

    from hikari.api import rest as rest_app
    from hikari.models import users
    from hikari.models import voices
    from hikari.utilities import undefined

_LOGGER: typing.Final[logging.Logger] = logging.getLogger("hikari.cache")

_T = typing.TypeVar("_T", bound=snowflake.Unique)
_T_co = typing.TypeVar("_T_co", bound=snowflake.Unique)
_U = typing.TypeVar("_U")


class _IDTable(typing.MutableSet[snowflake.Snowflake]):
    """Compact 64-bit integer bisected-array-set of snowflakes."""

    __slots__ = ("_ids",)

    def __init__(self) -> None:
        self._ids = array.array("Q")

    #  TODO: equality check?

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


_BuilderT = typing.TypeVar("_BuilderT")


class _StatefulCacheMappingView(cache.ICacheView[_T], typing.Generic[_T]):
    __slots__ = ("_builder", "_data")

    def __init__(
        self,
        items: typing.Mapping[snowflake.Snowflake, typing.Union[_T, _BuilderT]],
        *,
        builder: typing.Optional[typing.Callable[[_BuilderT], _T]] = None,
    ) -> None:
        self._builder = builder
        self._data = items

    def __contains__(self, key: typing.Any) -> bool:
        return key in self._data

    def __getitem__(self, sf: snowflake.Snowflake) -> _T:
        entry = self._data[sf]

        if self._builder:
            entry = self._builder(entry)  # type: ignore

        return entry  # type: ignore

    def __iter__(self) -> typing.Iterator[snowflake.Snowflake]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def get_item_at(self, index: int) -> _T:
        i = 0
        items = iter(self)

        try:
            while i < index:
                next(items)
        except StopIteration:
            raise IndexError(index) from None

        return self[next(items)]

    def iterator(self) -> iterators.LazyIterator[_T_co]:
        return iterators.FlatLazyIterator(self.values())


class _EmptyCacheView(cache.ICacheView[_T], typing.Generic[_T]):
    def __contains__(self, _: typing.Any) -> typing.Literal[False]:
        return False

    def __getitem__(self, sf: snowflake.Snowflake) -> typing.NoReturn:
        raise KeyError(sf)

    def __iter__(self) -> typing.Iterator[snowflake.Snowflake]:
        yield from ()

    def __len__(self) -> typing.Literal[0]:
        return 0

    def get_item_at(self, index: int) -> typing.NoReturn:
        raise IndexError(index)

    def iterator(self) -> iterators.LazyIterator[_T_co]:
        return iterators.FlatLazyIterator(())


@attr.s(slots=True, repr=False, hash=False)
class _GuildRecord:
    is_available: typing.Optional[bool] = attr.ib(default=None)
    guild: typing.Optional[guilds.GatewayGuild] = attr.ib(default=None)
    # TODO: some of these will be iterated across more than they will searched by a specific ID...
    # ... identify these cases and convert to lists.
    roles: typing.Optional[_IDTable] = attr.ib(default=None)
    members: typing.Optional[typing.Dict[snowflake.Snowflake, _MemberData]] = attr.ib(default=None)
    presences: typing.Optional[typing.Dict[snowflake.Snowflake, presences.MemberPresence]] = attr.ib(default=None)
    voice_statuses: typing.Optional[typing.Dict[snowflake.Snowflake, voices.VoiceState]] = attr.ib(default=None)
    emojis: typing.Optional[_IDTable] = attr.ib(default=None)
    channels: typing.Optional[_IDTable] = attr.ib(default=None)

    _FIELDS_TO_CHECK: typing.Final[typing.Collection[str]] = (
        "guild",
        "roles",
        "members",
        "presences",
        "voice_statuses",
        "emojis",
        "channels",
    )

    def __bool__(self) -> bool:
        return any(getattr(self, attribute) for attribute in self._FIELDS_TO_CHECK)


_TargetEntityT = typing.TypeVar("_TargetEntityT")


class _BaseData(abc.ABC):
    __slots__ = ()

    @staticmethod
    @abc.abstractmethod
    def get_blacklisted_fields() -> typing.Collection[str]:
        ...

    def build_entity(self, target: _TargetEntityT) -> _TargetEntityT:
        blacklisted_fields = self.get_blacklisted_fields()
        for field in attr.fields(type(target)):
            if field.name in blacklisted_fields:
                continue

            value = copy.copy(getattr(self, field.name))  # TODO: deepcopy?
            setattr(target, field.name, value)

        return target

    @classmethod
    def build_from_entity(cls: typing.Type[_DataT], entity: _TargetEntityT, **kwargs: typing.Any) -> _DataT:
        blacklisted_fields = cls.get_blacklisted_fields()
        for field in attr.fields(type(entity)):
            if field.name in blacklisted_fields:
                continue

            kwargs[field.name] = copy.copy(getattr(entity, field.name))

        return cls(**kwargs)  # type: ignore


_DataT = typing.TypeVar("_DataT", bound=_BaseData)


@attr.s(auto_attribs=True, kw_only=True, slots=True, repr=False, hash=False)
class _MemberData(_BaseData):
    @staticmethod
    def get_blacklisted_fields() -> typing.Collection[str]:
        return ("user",)

    id: snowflake.Snowflake
    guild_id: snowflake.Snowflake
    nickname: typing.Union[str, None, undefined.UndefinedType]
    role_ids: _IDTable  # TODO: use IDTable on actual model.
    joined_at: typing.Union[datetime.datetime, undefined.UndefinedType]
    premium_since: typing.Union[datetime.date, None, undefined.UndefinedType]
    is_deaf: typing.Union[bool, undefined.UndefinedType]
    is_mute: typing.Union[bool, undefined.UndefinedType]


@attr.s(auto_attribs=True, kw_only=True, slots=True, repr=False, hash=False)
class _DMChannelData(_BaseData):
    @staticmethod
    def get_blacklisted_fields() -> typing.Collection[str]:
        return "app", "recipient", "type"

    id: snowflake.Snowflake
    name: typing.Optional[str]
    last_message_id: typing.Optional[snowflake.Snowflake]
    recipient_id: snowflake.Snowflake

    def build_entity(self, target: channels.DMChannel) -> channels.DMChannel:
        super().build_entity(target)
        target.type = channels.ChannelType.DM
        return target


@attr.s(auto_attribs=True, kw_only=True, slots=True, repr=False, hash=False)
class _VoiceStateData(_BaseData):
    @staticmethod
    def get_blacklisted_fields() -> typing.Collection[str]:
        return "app", "member"

    channel_id: typing.Optional[snowflake.Snowflake]
    guild_id: snowflake.Snowflake
    is_guild_deafened: bool
    is_guild_muted: bool
    is_self_deafened: bool
    is_self_muted: bool
    is_streaming: bool
    is_suppressed: bool
    is_video_enabled: bool
    user_id: snowflake.Snowflake
    session_id: str


@attr.s(auto_attribs=True, kw_only=True, slots=True, repr=False, hash=False)
class _KnownCustomEmojiData(_BaseData):
    @staticmethod
    def get_blacklisted_fields() -> typing.Collection[str]:
        return "app", "user"

    id: snowflake.Snowflake
    name: typing.Optional[str]  # TODO: Shouldn't ever be None here
    is_animated: typing.Optional[bool]  # TODO: Shouldn't ever be None here
    guild_id: snowflake.Snowflake
    role_ids: snowflake.Snowflake
    user_id: typing.Optional[snowflake.Snowflake]
    is_animated: bool
    is_colons_required: bool
    is_managed: bool
    is_available: bool


def _set_fields_if_defined(
    target: _TargetEntityT, source: typing.Any, *, blacklist: typing.Tuple[str, ...] = ()
) -> _TargetEntityT:
    for field in attr.fields(type(source)):
        value = getattr(source, field.name, undefined.UNDEFINED)
        if value is not undefined.UNDEFINED and hasattr(target, field.name) and field.name not in blacklist:
            setattr(target, field.name, value)

    return target


class StatefulCacheComponentImpl(cache.ICacheComponent):
    """In-memory cache implementation."""

    __slots__ = (
        "_me",
        "_dm_channel_entries",
        "_emoji_entries",
        "_guild_channel_entries",
        "_guild_entries",
        "_role_entries",
        "_user_entries",
        "_role_entries",
        "_app",
        "_intents",
    )

    def __init__(self, app: rest_app.IRESTApp, intents: typing.Optional[intents_.Intent]) -> None:
        self._me: typing.Optional[users.OwnUser] = None
        self._dm_channel_entries: typing.Dict[snowflake.Snowflake, channels.DMChannel] = {}
        self._emoji_entries: typing.Dict[snowflake.Snowflake, emojis.KnownCustomEmoji] = {}
        self._guild_channel_entries: typing.Dict[snowflake.Snowflake, channels.GuildChannel] = {}
        self._guild_entries: typing.Dict[snowflake.Snowflake, _GuildRecord] = {}
        self._role_entries: typing.Dict[snowflake.Snowflake, guilds.Role] = {}
        self._user_entries: typing.Dict[snowflake.Snowflake, users.User] = {}

        self._app = app
        self._intents = intents

    def _get_or_create_guild_record(self, guild_id: snowflake.Snowflake) -> _GuildRecord:
        if guild_id not in self._guild_entries:
            self._guild_entries[guild_id] = _GuildRecord()

        return self._guild_entries[guild_id]

    def _delete_guild_record_if_empty(self, guild_id: snowflake.Snowflake) -> None:
        if guild_id in self._guild_entries and not self._guild_entries[guild_id]:
            del self._guild_entries[guild_id]

    def _garbage_collect_user(self, user_id: snowflake.Snowflake) -> None:
        if user_id not in self._user_entries or users in self._dm_channel_entries:
            return

        if any(
            record.members
            and user_id in record.members
            or record.voice_statuses
            and user_id in record.voice_statuses
            or record.presences
            and user_id in record.presences
            for record in self._guild_entries.values()
        ):
            return

        del self._user_entries[user_id]

    @property
    @typing.final
    def app(self) -> rest_app.IRESTApp:
        return self._app

    def _assert_has_intent(self, intents: intents_.Intent, /) -> None:
        if self._intents is not None and self._intents ^ intents:
            raise errors.MissingIntentError(intents)

    def _is_intent_enabled(self, intents: intents_.Intent, /) -> bool:
        return self._intents is None or self._intents & intents

    def clear_guilds(self) -> cache.ICacheView[guilds.Guild]:
        result = {}

        for sf, record in tuple(self._guild_entries.items()):
            if record.guild is None:
                continue

            result[sf] = record.guild
            record.guild = None
            record.is_available = None
            self._delete_guild_record_if_empty(sf)

        return _StatefulCacheMappingView(result) if result else _EmptyCacheView()

    def delete_guild(self, guild_id: snowflake.Snowflake, /) -> typing.Optional[guilds.Guild]:
        if guild_id not in self._guild_entries:
            return None

        record = self._guild_entries[guild_id]
        guild = record.guild

        if guild is not None:
            record.guild = None
            record.is_available = None
            self._delete_guild_record_if_empty(guild_id)

        return guild

    def get_guild(self, guild_id: snowflake.Snowflake, /) -> typing.Optional[guilds.GatewayGuild]:
        if (record := self._guild_entries.get(guild_id)) is not None:
            if record.guild and not record.is_available:
                raise errors.UnavailableGuildError(record.guild)

            return record.guild

        return None

    def get_guilds_view(self) -> cache.ICacheView[guilds.GatewayGuild]:
        results = {sf: record.guild for sf, record in self._guild_entries.items() if record.guild}
        return _StatefulCacheMappingView(results) if results else _EmptyCacheView()

    def set_guild(self, guild: guilds.GatewayGuild, /):
        record = self._get_or_create_guild_record(guild.id)
        record.guild = copy.deepcopy(guild)
        record.is_available = True

    def set_guild_availability(self, guild_id: snowflake.Snowflake, is_available: bool) -> None:
        record = self._get_or_create_guild_record(guild_id=guild_id)  # TODO: only set this if guild object cached?
        record.is_available = is_available

    def update_guild(
        self, guild: guilds.GatewayGuild, /
    ) -> typing.Tuple[typing.Optional[guilds.GatewayGuild], typing.Optional[guilds.GatewayGuild]]:
        guild = copy.copy(guild)
        record = self._guild_entries.get(guild.id)
        cached_guild = record.guild if record is not None else None

        # We have to manually update these because inconsistency by Discord.
        if cached_guild is not None:
            guild.member_count = cached_guild.member_count
            guild.joined_at = cached_guild.joined_at
            guild.is_large = cached_guild.is_large

        self.set_guild(guild)
        record = self._guild_entries.get(guild.id)
        return cached_guild, record.guild if record is not None else None

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

    def delete_me(self) -> typing.Optional[users.OwnUser]:
        cached_user = self._me
        self._me = None
        return cached_user

    def get_me(self) -> typing.Optional[users.OwnUser]:
        return copy.deepcopy(self._me)

    def set_me(self, user: users.OwnUser, /):
        self._me = copy.deepcopy(user)

    def update_me(
        self, user: users.OwnUser, /
    ) -> typing.Tuple[typing.Optional[users.OwnUser], typing.Optional[users.OwnUser]]:
        _LOGGER.debug("setting my user to %s", user)
        cached_user = self._me
        self.set_me(user)
        return cached_user, self._me

    def _build_member(
        self,
        member_data: _MemberData,
        user_entries: typing.Optional[typing.Mapping[snowflake.Snowflake, users.User]] = None,
    ) -> guilds.Member:
        member = member_data.build_entity(guilds.Member())
        user = user_entries[member_data.id] if user_entries is not None else self._user_entries[member_data.id]
        member.user = copy.copy(user)
        return member

    def clear_members(
        self, guild_id: snowflake.Snowflake, /
    ) -> typing.Optional[_StatefulCacheMappingView[guilds.Member]]:
        guild_record = self._guild_entries.get(guild_id)

        members: typing.Optional[_StatefulCacheMappingView[guilds.Member]]
        if guild_record is not None and guild_record.members is not None:
            cached_members = guild_record.members
            cached_users = {sf: self._user_entries[sf] for sf in cached_members.keys()}
            guild_record.members = None
            self._delete_guild_record_if_empty(guild_id)

            for user_id in cached_members.keys():
                self._garbage_collect_user(user_id)

            members = _StatefulCacheMappingView(
                cached_members, builder=lambda member: self._build_member(member, user_entries=cached_users)
            )
        else:
            members = None

        return members

    def delete_member(
        self, guild_id: snowflake.Snowflake, user_id: snowflake.Snowflake, /
    ) -> typing.Optional[guilds.Member]:
        guild_record = self._guild_entries.get(guild_id)
        member = guild_record.members.pop(user_id, None) if guild_record and guild_record.members else None

        built_member: typing.Optional[guilds.Member]
        if member is not None:
            self._delete_guild_record_if_empty(guild_id)
            self._garbage_collect_user(member.id)
            built_member = self._build_member(member)
        else:
            built_member = None

        return built_member

    def get_member(self, guild_id: snowflake.Snowflake, user_id: snowflake.Snowflake) -> typing.Optional[guilds.Member]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is None or guild_record.members is None:
            return None

        member = guild_record.members.get(user_id)
        return self._build_member(member) if member is not None else None

    def get_members_view(self, guild_id: snowflake.Snowflake, /) -> cache.ICacheView[guilds.Member]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is None or guild_record.members is None:
            return _EmptyCacheView()

        cached_users = {sf: self._user_entries[sf] for sf in guild_record.members.keys()}
        return _StatefulCacheMappingView(
            copy.deepcopy(guild_record.members),
            builder=lambda member: self._build_member(member, user_entries=cached_users),
        )

    def set_member(self, member_obj: guilds.Member, /) -> None:
        guild_record = self._get_or_create_guild_record(member_obj.guild_id)
        member_data = _MemberData.build_from_entity(member_obj, id=member_obj.user.id)

        if guild_record.members is None:
            guild_record.members = {}

        guild_record.members[member_data.id] = member_data

    def update_member(
        self, member_obj: guilds.Member
    ) -> typing.Tuple[typing.Optional[guilds.Member], typing.Optional[guilds.Member]]:
        cached_member = self.get_member(member_obj.guild_id, member_obj.user.id)
        self.set_member(member_obj)
        return cached_member, self.get_member(member_obj.guild_id, member_obj.user.id)

    def clear_users(self) -> cache.ICacheView[users.User]:
        if not self._user_entries:
            return _EmptyCacheView()

        cached_users = self._user_entries.copy()
        self._user_entries.clear()
        return _StatefulCacheMappingView(cached_users)

    def delete_user(self, user_id: snowflake.Snowflake) -> typing.Optional[users.User]:
        return self._user_entries.pop(user_id, None)

    def get_user(self, user_id: snowflake.Snowflake) -> typing.Optional[users.User]:
        return copy.deepcopy(self._user_entries.get(user_id))

    def get_users_view(self) -> cache.ICacheView[users.User]:
        if not self._user_entries:
            return _EmptyCacheView()

        return _StatefulCacheMappingView(copy.deepcopy(self._user_entries))

    def set_user(self, user: users.User) -> None:
        self._user_entries[user.id] = copy.deepcopy(user)

    def update_user(self, user: users.User) -> typing.Tuple[typing.Optional[users.User], typing.Optional[users.User]]:
        cached_user = self.get_user(user.id)
        self.set_user(user)
        return cached_user, self.get_user(user.id)

    def get_guild_presence(
        self, guild_id: snowflake.Snowflake, user_id: snowflake.Snowflake
    ) -> typing.Optional[presences.MemberPresence]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is None or guild_record.presences is None:
            return None
        return guild_record.presences.get(user_id)

    def get_guild_role(
        self, guild_id: snowflake.Snowflake, role_id: snowflake.Snowflake
    ) -> typing.Optional[guilds.Role]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record.emojis is None or guild_record.roles is None:
            return None
        return guild_record.roles[role_id]

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

    def get_presences_view_for_guild(
        self, guild_id: snowflake.Snowflake, /
    ) -> cache.ICacheView[presences.MemberPresence]:
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
        self._guild_entries = {guild_id: _GuildRecord(is_available=False) for guild_id in guild_ids}

    def replace_all_guild_channels(
        self, guild_id: snowflake.Snowflake, channel_objs: typing.Collection[channels.GuildChannel]
    ) -> None:
        if guild_id not in self._guild_entries:
            self._guild_entries[guild_id] = _GuildRecord()

        self._guild_entries[guild_id].channels = sorted(channel_objs, key=lambda c: c.position)

    def replace_all_guild_emojis(
        self, guild_id: snowflake.Snowflake, emoji_objs: typing.Collection[emojis.KnownCustomEmoji]
    ) -> None:
        if guild_id not in self._guild_entries:
            self._guild_entries[guild_id] = _GuildRecord()

        guild_record = self._guild_entries.get(guild_id)
        if guild_record is not None:
            guild_record.emojis = {emoji_obj.id: emoji_obj for emoji_obj in emoji_objs}

    def replace_all_guild_presences(
        self, guild_id: snowflake.Snowflake, presence_objs: typing.Collection[presences.MemberPresence]
    ) -> None:
        if guild_id not in self._guild_entries:
            self._guild_entries[guild_id] = _GuildRecord()

        self._guild_entries[guild_id].presences = {presence_obj.user_id: presence_obj for presence_obj in presence_objs}

    def replace_all_guild_roles(self, guild_id: snowflake.Snowflake, roles: typing.Collection[guilds.Role]) -> None:
        if guild_id not in self._guild_entries:
            self._guild_entries[guild_id] = _GuildRecord()

        # Top role first!
        self._guild_entries[guild_id].roles = {
            role.id: role for role in sorted(roles, key=lambda r: r.position, reverse=True)
        }
