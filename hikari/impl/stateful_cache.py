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
import itertools
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
from hikari.models import voices
from hikari.utilities import iterators
from hikari.utilities import snowflake

if typing.TYPE_CHECKING:
    import datetime

    from hikari.api import rest as rest_app
    from hikari.models import users
    from hikari.utilities import undefined

_DataT = typing.TypeVar("_DataT", bound="_BaseData")
_LOGGER: typing.Final[logging.Logger] = logging.getLogger("hikari.cache")
_T = typing.TypeVar("_T")


class _IDTable(typing.MutableSet[snowflake.Snowflake]):
    """Compact 64-bit integer bisected-array-set of snowflakes."""

    __slots__: typing.Sequence[str] = ("_ids",)

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
        return map(snowflake.Snowflake, self._ids)

    def __repr__(self) -> str:
        return "SnowflakeTable" + reprlib.repr(self._ids)[5:]


class _StatefulCacheMappingView(cache.ICacheView[_T], typing.Generic[_T]):
    __slots__: typing.Sequence[str] = ("_builder", "_data")

    def __init__(
        self,
        items: typing.Mapping[snowflake.Snowflake, typing.Union[_T, _DataT]],
        *,
        builder: typing.Optional[typing.Callable[[_DataT], _T]] = None,
    ) -> None:
        self._builder = builder
        self._data = items

    def __contains__(self, key: typing.Any) -> bool:
        return key in self._data

    def __getitem__(self, sf: snowflake.Snowflake) -> _T:
        entry = self._data[sf]

        if self._builder:
            entry = self._builder(entry)  # type: ignore[arg-type]

        return entry  # type: ignore[return-value]

    def __iter__(self) -> typing.Iterator[snowflake.Snowflake]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def get_item_at(self, index: int) -> _T:
        try:
            return next(itertools.islice(self.values(), index, None))
        except StopIteration:
            raise IndexError(index) from None

    def iterator(self) -> iterators.LazyIterator[_T]:
        return iterators.FlatLazyIterator(self.values())


class _EmptyCacheView(cache.ICacheView[typing.Any]):
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

    def iterator(self) -> iterators.LazyIterator[_T]:
        return iterators.FlatLazyIterator(())


@attr.s(slots=True, repr=False, hash=False)
class _GuildRecord:
    is_available: typing.Optional[bool] = attr.ib(default=None)
    guild: typing.Optional[guilds.GatewayGuild] = attr.ib(default=None)
    # TODO: some of these will be iterated across more than they will searched by a specific ID...
    # ... identify these cases and convert to lists.
    channels: typing.Optional[_IDTable] = attr.ib(default=None)
    emojis: typing.Optional[_IDTable] = attr.ib(default=None)
    members: typing.Optional[typing.Dict[snowflake.Snowflake, _MemberData]] = attr.ib(default=None)
    presences: typing.Optional[typing.Dict[snowflake.Snowflake, presences.MemberPresence]] = attr.ib(default=None)
    roles: typing.Optional[_IDTable] = attr.ib(default=None)
    voice_states: typing.Optional[typing.Dict[snowflake.Snowflake, _VoiceStateData]] = attr.ib(default=None)

    _FIELDS_TO_CHECK: typing.Final[typing.Collection[str]] = (
        "guild",
        "roles",
        "members",
        "presences",
        "voice_states",
        "emojis",
        "channels",
    )

    def __bool__(self) -> bool:
        return any(getattr(self, attribute) for attribute in self._FIELDS_TO_CHECK)


@attr.s(auto_attribs=False, kw_only=True, slots=True, repr=False, hash=False)
class _BaseData(abc.ABC):
    """A data class used for storing entities in a more primitive form.

    !!! note
        This base implementation assumes that all the fields it'll handle will
        be immutable and to handle mutable fields you'll have to override
        build_entity and build_from_entity to explicitly copy them.
    """

    __slots__: typing.Sequence[str] = ()

    @classmethod
    @abc.abstractmethod
    def get_fields(cls) -> typing.Collection[str]:
        """Get the fields that should be handled on the relevant target entity.

        !!! note
            These fields should match up with both the target entity and the
            data class itself.

        Returns
        -------
        typing.Collection[builtins.str]
            A collection of the names of fields to handle.
        """

    def build_entity(self, target: _T) -> _T:
        """Build an entity object from this data object.

        Parameters
        ----------
        target
            The pre-initialised entity object to add attributes to.

        Returns
        -------
        The initialised entity object.
        """
        for field in self.get_fields():
            setattr(target, field, getattr(self, field))

        return target

    @classmethod
    def build_from_entity(cls: typing.Type[_DataT], entity: _T, **kwargs: typing.Any) -> _DataT:
        """Build a data object from an initialised entity.

        Parameters
        ----------
        entity
            The entity object to build a data class from.
        kwargs
            Extra fields to add to the data class.

        Returns
        -------
        The built data class.
        """
        for field in cls.get_fields():
            kwargs[field] = getattr(entity, field)

        return cls(**kwargs)  # type: ignore[call-arg]


@attr.s(auto_attribs=True, kw_only=True, slots=True, repr=False, hash=False)
class _DMChannelData(_BaseData):
    id: snowflake.Snowflake
    name: typing.Optional[str]
    last_message_id: typing.Optional[snowflake.Snowflake]
    recipient_id: snowflake.Snowflake

    @classmethod
    def get_fields(cls) -> typing.Collection[str]:
        return "id", "name", "last_message_id"

    def build_entity(self, target: _T) -> _T:
        super().build_entity(target)
        target.type = channels.ChannelType.DM  # type: ignore[attr-defined]
        return target


@attr.s(auto_attribs=True, kw_only=True, slots=True, repr=False, hash=False)
class _MemberData(_BaseData):
    id: snowflake.Snowflake
    guild_id: snowflake.Snowflake
    nickname: undefined.UndefinedNoneOr[str]
    role_ids: typing.Sequence[snowflake.Snowflake]
    joined_at: undefined.UndefinedOr[datetime.datetime]
    premium_since: undefined.UndefinedNoneOr[datetime.datetime]
    is_deaf: undefined.UndefinedOr[bool]
    is_mute: undefined.UndefinedOr[bool]

    @classmethod
    def get_fields(cls) -> typing.Collection[str]:
        return "guild_id", "nickname", "role_ids", "joined_at", "premium_since", "is_deaf", "is_mute"

    @classmethod
    def build_from_entity(cls: typing.Type[_DataT], entity: _T, **kwargs: typing.Any) -> _DataT:
        data_object = super().build_from_entity(entity, **kwargs)
        data_object.role_ids = tuple(data_object.role_ids)
        return data_object


@attr.s(auto_attribs=True, kw_only=True, slots=True, repr=False, hash=False)
class _KnownCustomEmojiData(_BaseData):
    id: snowflake.Snowflake
    name: typing.Optional[str]  # TODO: Shouldn't ever be None here
    is_animated: typing.Optional[bool]  # TODO: Shouldn't ever be None here
    guild_id: snowflake.Snowflake
    role_ids: snowflake.Snowflake
    user_id: typing.Optional[snowflake.Snowflake]
    is_colons_required: bool
    is_managed: bool
    is_available: bool

    @classmethod
    def get_fields(cls) -> typing.Collection[str]:
        return "id", "name", "is_animated", "guild_id", "role_ids", "is_colons_required", "is_managed", "is_available"

    @classmethod
    def build_from_entity(cls: typing.Type[_DataT], entity: _T, **kwargs: typing.Any) -> _DataT:
        data_object = super().build_from_entity(entity, **kwargs)
        data_object.role_ids = tuple(data_object.role_ids)
        return data_object


@attr.s(auto_attribs=True, kw_only=True, slots=True, repr=False, hash=False)
class _VoiceStateData(_BaseData):
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

    @classmethod
    def get_fields(cls) -> typing.Collection[str]:
        return (
            "channel_id",
            "guild_id",
            "is_guild_deafened",
            "is_guild_muted",
            "is_self_deafened",
            "is_self_muted",
            "is_streaming",
            "is_suppressed",
            "is_video_enabled",
            "user_id",
            "session_id",
        )


def _set_fields_if_defined(target: _T, source: typing.Any, *, blacklist: typing.Tuple[str, ...] = ()) -> _T:
    for field in attr.fields(type(source)):
        value = getattr(source, field.name, undefined.UNDEFINED)
        if value is not undefined.UNDEFINED and hasattr(target, field.name) and field.name not in blacklist:
            setattr(target, field.name, value)

    return target


class StatefulCacheComponentImpl(cache.ICacheComponent):
    """In-memory cache implementation."""

    __slots__: typing.Sequence[str] = (
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
        self._dm_channel_entries: typing.Dict[snowflake.Snowflake, _DMChannelData] = {}
        self._emoji_entries: typing.Dict[snowflake.Snowflake, emojis.KnownCustomEmoji] = {}
        self._guild_channel_entries: typing.Dict[snowflake.Snowflake, channels.GuildChannel] = {}
        self._guild_entries: typing.Dict[snowflake.Snowflake, _GuildRecord] = {}
        self._role_entries: typing.Dict[snowflake.Snowflake, guilds.Role] = {}
        self._user_entries: typing.Dict[snowflake.Snowflake, users.User] = {}

        self._app = app
        self._intents = intents

    @property
    @typing.final
    def app(self) -> rest_app.IRESTApp:
        return self._app

    def _get_or_create_guild_record(self, guild_id: snowflake.Snowflake) -> _GuildRecord:
        if guild_id not in self._guild_entries:
            self._guild_entries[guild_id] = _GuildRecord()

        return self._guild_entries[guild_id]

    def _delete_guild_record_if_empty(self, guild_id: snowflake.Snowflake) -> None:
        if guild_id in self._guild_entries and not self._guild_entries[guild_id]:
            del self._guild_entries[guild_id]

    def _garbage_collect_user(self, user_id: snowflake.Snowflake) -> None:
        if self._can_user_be_removed(user_id):
            del self._user_entries[user_id]

    def _assert_has_intent(self, intents: intents_.Intent, /) -> None:
        if self._intents is not None and self._intents ^ intents:
            raise errors.MissingIntentError(intents) from None

    def _is_intent_enabled(self, intents: intents_.Intent, /) -> bool:
        return self._intents is None or (self._intents & intents) == intents

    def _build_dm_channel(
        self,
        channel_data: _DMChannelData,
        cached_users: typing.Optional[typing.Mapping[snowflake.Snowflake, users.User]] = None,
    ) -> channels.DMChannel:
        channel = channel_data.build_entity(channels.DMChannel())
        channel.app = self._app
        recipient = (
            cached_users[channel_data.recipient_id] if cached_users else self._user_entries[channel_data.recipient_id]
        )
        channel.recipient = copy.copy(recipient)  # type: ignore[assignment]
        return channel

    def clear_dm_channels(self) -> cache.ICacheView[channels.DMChannel]:
        if not self._dm_channel_entries:
            return _EmptyCacheView()

        cached_dm_channels = self._dm_channel_entries.copy()
        self._dm_channel_entries.clear()
        cached_users = {}

        for user_id in cached_dm_channels.keys():
            cached_users[user_id] = self._user_entries[user_id]
            self._garbage_collect_user(user_id)

        return _StatefulCacheMappingView(
            cached_dm_channels, builder=lambda channel: self._build_dm_channel(channel, cached_users)
        )

    def delete_dm_channel(self, user_id: snowflake.Snowflake) -> typing.Optional[channels.DMChannel]:
        channel_data = self._dm_channel_entries.pop(user_id, None)

        if channel_data is None:
            return None

        channel = self._build_dm_channel(channel_data)
        self._garbage_collect_user(user_id)
        return channel

    def get_dm_channel(self, user_id: snowflake.Snowflake) -> typing.Optional[channels.DMChannel]:
        channel_data = self._dm_channel_entries.get(user_id)
        return self._build_dm_channel(channel_data) if channel_data is not None else None

    def get_dm_channels_view(self) -> cache.ICacheView[channels.DMChannel]:
        if not self._dm_channel_entries:
            return _EmptyCacheView()

        cached_users = {sf: user for sf, user in self._user_entries.items() if sf in self._dm_channel_entries}
        return _StatefulCacheMappingView(
            self._dm_channel_entries.copy(), builder=lambda channel: self._build_dm_channel(channel, cached_users)
        )

    def set_dm_channel(self, channel: channels.DMChannel) -> None:  # TODO: cache the user object here.
        self._dm_channel_entries[channel.recipient.id] = _DMChannelData.build_from_entity(
            channel, recipient_id=channel.recipient.id
        )

    def update_dm_channel(
        self, channel: channels.DMChannel
    ) -> typing.Tuple[typing.Optional[channels.DMChannel], typing.Optional[channels.DMChannel]]:
        cached_dm_channel = self.get_dm_channel(channel.recipient.id)
        self.set_dm_channel(channel)
        return cached_dm_channel, self.get_dm_channel(channel.recipient.id)

    def clear_emojis(self, guild_id: snowflake.Snowflake) -> cache.ICacheView[emojis.KnownCustomEmoji]:
        raise NotImplementedError

    def delete_emoji(self, emoji_id: snowflake.Snowflake) -> typing.Optional[emojis.KnownCustomEmoji]:
        raise NotImplementedError

    def get_emoji(self, emoji_id: snowflake.Snowflake) -> typing.Optional[emojis.KnownCustomEmoji]:
        raise NotImplementedError

    def get_emojis_view(self, guild_id: snowflake.Snowflake) -> cache.ICacheView[emojis.KnownCustomEmoji]:
        raise NotImplementedError

    def set_emoji(self, emoji: emojis.KnownCustomEmoji) -> None:
        raise NotImplementedError

    def update_emoji(
        self, emoji: emojis.KnownCustomEmoji
    ) -> typing.Tuple[typing.Optional[emojis.KnownCustomEmoji], typing.Optional[emojis.KnownCustomEmoji]]:
        ...

    def clear_guilds(self) -> cache.ICacheView[guilds.GatewayGuild]:
        result = {}

        for sf, record in tuple(self._guild_entries.items()):
            if record.guild is None:
                continue

            result[sf] = record.guild
            record.guild = None
            record.is_available = None
            self._delete_guild_record_if_empty(sf)

        return _StatefulCacheMappingView(result) if result else _EmptyCacheView()

    def delete_guild(self, guild_id: snowflake.Snowflake, /) -> typing.Optional[guilds.GatewayGuild]:
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
                raise errors.UnavailableGuildError(record.guild) from None

            return record.guild

        return None

    def get_guilds_view(self) -> cache.ICacheView[guilds.GatewayGuild]:
        results = {sf: copy.copy(record.guild) for sf, record in self._guild_entries.items() if record.guild}
        return _StatefulCacheMappingView(results) if results else _EmptyCacheView()

    def set_guild(self, guild: guilds.GatewayGuild, /) -> None:
        record = self._get_or_create_guild_record(guild.id)
        record.guild = copy.copy(guild)
        record.is_available = True

    def set_guild_availability(self, guild_id: snowflake.Snowflake, is_available: bool) -> None:
        record = self._get_or_create_guild_record(guild_id=guild_id)  # TODO: only set this if guild object cached?
        record.is_available = is_available

    # TODO: is this the best way to handle this?
    def set_initial_unavailable_guilds(self, guild_ids: typing.Collection[snowflake.Snowflake]) -> None:
        # Invoked when we receive ON_READY, assume all of these are unavailable on startup.
        self._guild_entries = {guild_id: _GuildRecord(is_available=False) for guild_id in guild_ids}

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

    def clear_guild_channels(self, guild_id: snowflake.Snowflake) -> cache.ICacheView[channels.GuildChannel]:
        raise NotImplementedError

    def delete_guild_channel(self, channel_id: snowflake.Snowflake) -> typing.Optional[channels.GuildChannel]:
        raise NotImplementedError

    def get_guild_channel(self, channel_id: snowflake.Snowflake) -> typing.Optional[channels.GuildChannel]:
        raise NotImplementedError

    def get_guild_channels_view(self, guild_id: snowflake.Snowflake) -> cache.ICacheView[channels.GuildChannel]:
        raise NotImplementedError

    def set_guild_channel(self, channel: channels.GuildChannel) -> None:
        raise NotImplementedError

    def update_guild_channel(
        self, channel: channels.GuildChannel
    ) -> typing.Tuple[typing.Optional[channels.GuildChannel], typing.Optional[channels.GuildChannel]]:
        raise NotImplementedError

    def delete_me(self) -> typing.Optional[users.OwnUser]:
        cached_user = self._me
        self._me = None
        return cached_user

    def get_me(self) -> typing.Optional[users.OwnUser]:
        return copy.copy(self._me)

    def set_me(self, user: users.OwnUser, /) -> None:
        self._me = copy.copy(user)

    def update_me(
        self, user: users.OwnUser, /
    ) -> typing.Tuple[typing.Optional[users.OwnUser], typing.Optional[users.OwnUser]]:
        _LOGGER.debug("setting my user to %s", user)
        cached_user = self.get_me()
        self.set_me(user)
        return cached_user, self._me

    def _build_member(
        self,
        member_data: _MemberData,
        user_entries: typing.Optional[typing.Mapping[snowflake.Snowflake, users.User]] = None,
    ) -> guilds.Member:
        member = member_data.build_entity(guilds.Member())
        user = user_entries[member_data.id] if user_entries is not None else self._user_entries[member_data.id]
        member.user = copy.copy(user)  # type: ignore[assignment]
        return member

    def clear_members(self, guild_id: snowflake.Snowflake, /) -> cache.ICacheView[guilds.Member]:
        guild_record = self._guild_entries.get(guild_id)  # TODO: optional return on clear?

        members: cache.ICacheView[guilds.Member]
        if guild_record is None or guild_record.members is None:
            return _EmptyCacheView()

        cached_members = guild_record.members
        cached_users = {sf: self._user_entries[sf] for sf in cached_members.keys()}
        guild_record.members = None
        self._delete_guild_record_if_empty(guild_id)

        for user_id in cached_members.keys():
            self._garbage_collect_user(user_id)

        return _StatefulCacheMappingView(
            cached_members, builder=lambda member: self._build_member(member, user_entries=cached_users)
        )

    def delete_member(
        self, guild_id: snowflake.Snowflake, user_id: snowflake.Snowflake, /
    ) -> typing.Optional[guilds.Member]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is None:
            return None

        member = guild_record.members.pop(user_id, None) if guild_record.members else None
        if member is None:
            return None

        built_member = self._build_member(member)
        if not guild_record.members:
            guild_record.members = None

        self._delete_guild_record_if_empty(guild_id)
        self._garbage_collect_user(member.id)
        return built_member

    def get_member(
        self, guild_id: snowflake.Snowflake, user_id: snowflake.Snowflake, /
    ) -> typing.Optional[guilds.Member]:
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
            guild_record.members.copy(), builder=lambda member: self._build_member(member, user_entries=cached_users),
        )

    def set_member(self, member: guilds.Member, /) -> None:  # TODO: add recipient to cache here.
        guild_record = self._get_or_create_guild_record(member.guild_id)
        member_data = _MemberData.build_from_entity(member, id=member.user.id)

        if guild_record.members is None:
            guild_record.members = {}

        guild_record.members[member_data.id] = member_data

    def update_member(
        self, member: guilds.Member
    ) -> typing.Tuple[typing.Optional[guilds.Member], typing.Optional[guilds.Member]]:
        cached_member = self.get_member(member.guild_id, member.user.id)
        self.set_member(member)
        return cached_member, self.get_member(member.guild_id, member.user.id)

    def clear_presences(self, guild_id: snowflake.Snowflake) -> cache.ICacheView[presences.MemberPresence]:
        ...

    def delete_presence(
        self, guild_id: snowflake.Snowflake, user_id: snowflake.Snowflake
    ) -> typing.Optional[presences.MemberPresence]:
        ...

    def get_presence(
        self, guild_id: snowflake.Snowflake, user_id: snowflake.Snowflake
    ) -> typing.Optional[presences.MemberPresence]:
        raise NotImplementedError

    def get_presences_view(self, guild_id: snowflake.Snowflake) -> cache.ICacheView[presences.MemberPresence]:
        raise NotImplementedError

    def set_presence(self, presence: presences.MemberPresence) -> None:
        raise NotImplementedError

    def update_presence(
        self, presence: presences.MemberPresence
    ) -> typing.Tuple[typing.Optional[presences.MemberPresence], typing.Optional[presences.MemberPresence]]:
        raise NotImplementedError

    def clear_roles(self, guild_id: snowflake.Snowflake) -> cache.ICacheView[guilds.Role]:
        raise NotImplementedError

    def delete_role(self, role_id: snowflake.Snowflake) -> typing.Optional[guilds.Role]:
        raise NotImplementedError

    def get_role(self, role_id: snowflake.Snowflake) -> typing.Optional[guilds.Role]:
        raise NotImplementedError

    def get_roles_view(self, guild_id: snowflake.Snowflake) -> cache.ICacheView[guilds.Role]:
        raise NotImplementedError

    def set_role(self, role: guilds.Role) -> None:
        raise NotImplementedError

    def update_role(
        self, role: guilds.Role
    ) -> typing.Tuple[typing.Optional[guilds.Role], typing.Optional[guilds.Role]]:
        raise NotImplementedError

    def _can_user_be_removed(self, user_id: snowflake.Snowflake) -> bool:
        if user_id not in self._user_entries or user_id in self._dm_channel_entries:
            return False

        return not any(  # TODO: switch to ref counting
            record.members
            and user_id in record.members
            or record.voice_states
            and user_id in record.voice_states
            or record.presences
            and user_id in record.presences
            for record in self._guild_entries.values()
        )

    def clear_users(self) -> cache.ICacheView[users.User]:
        if not self._user_entries:  # TODO: don't remove users that are required for other cached entities or something.
            return _EmptyCacheView()

        cached_users = self._user_entries.copy()
        self._user_entries.clear()
        return _StatefulCacheMappingView(cached_users)

    def delete_user(self, user_id: snowflake.Snowflake) -> typing.Optional[users.User]:
        return self._user_entries.pop(user_id, None)

    def get_user(self, user_id: snowflake.Snowflake) -> typing.Optional[users.User]:
        return copy.copy(self._user_entries.get(user_id))

    def get_users_view(self) -> cache.ICacheView[users.User]:
        if not self._user_entries:
            return _EmptyCacheView()

        return _StatefulCacheMappingView(self._user_entries.copy())

    def set_user(self, user: users.User) -> None:
        self._user_entries[user.id] = copy.copy(user)

    def update_user(self, user: users.User) -> typing.Tuple[typing.Optional[users.User], typing.Optional[users.User]]:
        cached_user = self.get_user(user.id)
        self.set_user(user)
        return cached_user, self.get_user(user.id)

    def _build_voice_status(
        self,
        voice_data: _VoiceStateData,
        member_entries: typing.Optional[typing.Mapping[snowflake.Snowflake, _MemberData]] = None,
        user_entries: typing.Optional[typing.Mapping[snowflake.Snowflake, users.User]] = None,
    ) -> voices.VoiceState:
        voice_state = voice_data.build_entity(voices.VoiceState())
        voice_state.app = self._app

        if member_entries:
            voice_state.member = self._build_member(member_entries[voice_state.user_id], user_entries=user_entries)
        else:
            record = self._guild_entries[voice_state.guild_id]
            assert record.members is not None  # noqa S101
            member_data = record.members[voice_state.user_id]
            voice_state.member = self._build_member(member_data, user_entries=user_entries)

        return voice_state

    def clear_voice_states(self, guild_id: snowflake.Snowflake) -> cache.ICacheView[voices.VoiceState]:
        record = self._guild_entries.get(guild_id)

        if record is None or record.voice_states is None:
            return _EmptyCacheView()

        cached_voice_states = record.voice_states
        record.voice_states = None
        # TODO: garbage collect these members and users?

        cached_members = {}
        cached_users = {}

        for sf in cached_voice_states.keys():
            assert record.members is not None  # noqa S101
            cached_members[sf] = record.members[sf]
            cached_users[sf] = self._user_entries[sf]

        self._delete_guild_record_if_empty(guild_id)
        return _StatefulCacheMappingView(
            cached_voice_states,
            builder=lambda voice_data: self._build_voice_status(
                voice_data, member_entries=cached_members, user_entries=cached_users
            ),
        )

    def delete_voice_state(
        self, guild_id: snowflake.Snowflake, user_id: snowflake.Snowflake
    ) -> typing.Optional[voices.VoiceState]:
        record = self._guild_entries.get(guild_id)
        if record is None:
            return None

        voice_state_data = record.voice_states.pop(user_id, None) if record.voice_states else None
        if voice_state_data is None:
            return None

        # TODO: garbage collect member and user here
        built_voice_state = self._build_voice_status(voice_state_data)

        if not record.voice_states:
            record.voice_states = None

        # TODO: consistently do this in other places
        self._delete_guild_record_if_empty(guild_id)
        return built_voice_state

    def get_voice_state(
        self, guild_id: snowflake.Snowflake, user_id: snowflake.Snowflake
    ) -> typing.Optional[voices.VoiceState]:
        record = self._guild_entries.get(guild_id)
        voice_data = record.voice_states.get(user_id) if record and record.voice_states else None
        return self._build_voice_status(voice_data) if voice_data else None

    def get_voice_state_view(self, guild_id: snowflake.Snowflake) -> cache.ICacheView[voices.VoiceState]:
        record = self._guild_entries.get(guild_id)
        if record is None or record.voice_states is None:
            return _EmptyCacheView()

        voice_states = record.voice_states.copy()  # TODO: rename to "states"
        cached_members = {}
        cached_users = {}

        for sf in voice_states.keys():
            assert record.members is not None  # noqa S101
            cached_members[sf] = record.members[sf]
            cached_users[sf] = self._user_entries[sf]

        return _StatefulCacheMappingView(
            voice_states,
            builder=lambda voice_data: self._build_voice_status(
                voice_data, member_entries=cached_members, user_entries=cached_users
            ),
        )

    def set_voice_state(self, voice_state: voices.VoiceState) -> None:
        record = self._get_or_create_guild_record(voice_state.guild_id)

        if record.voice_states is None:
            record.voice_states = {}

        record.voice_states[voice_state.user_id] = _VoiceStateData.build_from_entity(voice_state)

    def update_voice_state(
        self, voice_state: voices.VoiceState
    ) -> typing.Tuple[typing.Optional[voices.VoiceState], typing.Optional[voices.VoiceState]]:
        cached_voice_state = self.get_voice_state(voice_state.guild_id, voice_state.user_id)
        self.set_voice_state(voice_state)
        return cached_voice_state, self.get_voice_state(voice_state.guild_id, voice_state.user_id)
