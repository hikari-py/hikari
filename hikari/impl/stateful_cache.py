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
import datetime
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
from hikari.models import invites
from hikari.models import presences
from hikari.models import users
from hikari.models import voices
from hikari.utilities import date
from hikari.utilities import iterators
from hikari.utilities import snowflake
from hikari.utilities import undefined

if typing.TYPE_CHECKING:
    from hikari.api import rest as rest_app

_DataT = typing.TypeVar("_DataT", bound="_BaseData")
_KeyT = typing.TypeVar("_KeyT")
_LOGGER: typing.Final[logging.Logger] = logging.getLogger("hikari.cache")
_ValueT = typing.TypeVar("_ValueT")


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


class _StatefulCacheMappingView(cache.ICacheView[_KeyT, _ValueT], typing.Generic[_KeyT, _ValueT]):
    __slots__: typing.Sequence[str] = ("_builder", "_data")

    def __init__(
        self,
        items: typing.Mapping[_KeyT, typing.Union[_ValueT, _DataT]],
        *,
        builder: typing.Optional[typing.Callable[[_DataT], _ValueT]] = None,
    ) -> None:
        self._builder = builder
        self._data = items

    def __contains__(self, key: typing.Any) -> bool:
        return key in self._data

    def __getitem__(self, key: _KeyT) -> _ValueT:
        entry = self._data[key]

        if self._builder:
            entry = self._builder(entry)  # type: ignore[arg-type]

        return entry  # type: ignore[return-value]

    def __iter__(self) -> typing.Iterator[_KeyT]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def get_item_at(self, index: int) -> _ValueT:
        try:
            return next(itertools.islice(self.values(), index, None))
        except StopIteration:
            raise IndexError(index) from None

    def iterator(self) -> iterators.LazyIterator[_ValueT]:
        return iterators.FlatLazyIterator(self.values())


class _EmptyCacheView(cache.ICacheView[typing.Any, typing.Any]):
    def __contains__(self, _: typing.Any) -> typing.Literal[False]:
        return False

    def __getitem__(self, key: typing.Any) -> typing.NoReturn:
        raise KeyError(key)

    def __iter__(self) -> typing.Iterator[typing.Any]:
        yield from ()

    def __len__(self) -> typing.Literal[0]:
        return 0

    def get_item_at(self, index: int) -> typing.NoReturn:
        raise IndexError(index)

    def iterator(self) -> iterators.LazyIterator[_ValueT]:
        return iterators.FlatLazyIterator(())


@attr.s(slots=True, repr=False, hash=False)
class _GuildRecord:
    is_available: typing.Optional[bool] = attr.ib(default=None)
    guild: typing.Optional[guilds.GatewayGuild] = attr.ib(default=None)
    # TODO: some of these will be iterated across more than they will searched by a specific ID...
    # ... identify these cases and convert to lists.
    channels: typing.Optional[typing.MutableSet[snowflake.Snowflake]] = attr.ib(default=None)
    emojis: typing.Optional[typing.MutableSet[snowflake.Snowflake]] = attr.ib(default=None)
    invites: typing.Optional[typing.MutableSequence[str]] = attr.ib(default=None)
    members: typing.Optional[typing.MutableMapping[snowflake.Snowflake, _MemberData]] = attr.ib(default=None)
    presences: typing.Optional[typing.MutableMapping[snowflake.Snowflake, presences.MemberPresence]] = attr.ib(
        default=None
    )
    roles: typing.Optional[typing.MutableSet[snowflake.Snowflake]] = attr.ib(default=None)
    voice_states: typing.Optional[typing.MutableMapping[snowflake.Snowflake, _VoiceStateData]] = attr.ib(default=None)

    _FIELDS_TO_CHECK: typing.Final[typing.Collection[str]] = (
        "guild",
        "invites",
        "members",
        "presences",
        "roles",
        "voice_states",
        "emojis",
        "channels",
    )

    def __bool__(self) -> bool:
        return any(getattr(self, attribute) for attribute in self._FIELDS_TO_CHECK)


@attr.s(auto_attribs=False, kw_only=True, slots=True, repr=False, hash=False)
class _BaseData(abc.ABC, typing.Generic[_ValueT]):
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

    def build_entity(self, target: _ValueT) -> _ValueT:
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
    def build_from_entity(cls: typing.Type[_DataT], entity: _ValueT, **kwargs: typing.Any) -> _DataT:
        """Build a data object from an initialised entity.

        Parameters
        ----------
        entity
            The entity object to build a data class from.
        kwargs
            Extra fields to add to the data class. Fields here will take
            priority over fields on `entity`.

        Returns
        -------
        The built data class.
        """
        for field in cls.get_fields():
            if field not in kwargs:
                kwargs[field] = getattr(entity, field)

        return cls(**kwargs)  # type: ignore[call-arg]

    def replace(self: _DataT, **kwargs: typing.Any) -> _DataT:
        data = copy.copy(self)

        for attribute, value in kwargs.items():
            setattr(data, attribute, value)

        return data


@attr.s(auto_attribs=True, kw_only=True, slots=True, repr=False, hash=False)
class _DMChannelData(_BaseData[channels.DMChannel]):
    id: snowflake.Snowflake
    name: typing.Optional[str]
    last_message_id: typing.Optional[snowflake.Snowflake]
    recipient_id: snowflake.Snowflake

    @classmethod
    def get_fields(cls) -> typing.Collection[str]:
        return "id", "name", "last_message_id"

    def build_entity(self, target: channels.DMChannel) -> channels.DMChannel:
        super().build_entity(target)
        target.type = channels.ChannelType.DM
        return target

    @classmethod
    def build_from_entity(
        cls: typing.Type[_DMChannelData], entity: channels.DMChannel, **kwargs: typing.Any
    ) -> _DMChannelData:
        return super().build_from_entity(entity, **kwargs, recipient_id=entity.recipient.id)


@attr.s(auto_attribs=True, kw_only=True, slots=True, repr=False, hash=False)
class _InviteData(_BaseData[invites.InviteWithMetadata]):
    code: str
    guild_id: typing.Optional[snowflake.Snowflake]  # TODO: This shouldn't ever be none here
    channel_id: snowflake.Snowflake
    inviter_id: typing.Optional[
        snowflake.Snowflake
    ]  # TODO: do we get these events if we don't have manage invite perm? ( we don't )
    target_user_id: snowflake.Snowflake
    target_user_type: typing.Optional[invites.TargetUserType]
    uses: int
    max_uses: typing.Optional[int]
    max_age: typing.Optional[datetime.timedelta]
    is_temporary: bool
    created_at: datetime.datetime

    @classmethod
    def get_fields(cls) -> typing.Collection[str]:
        return (
            "code",
            "guild_id",
            "channel_id",
            "target_user_type",
            "uses",
            "max_uses",
            "max_age",
            "is_temporary",
            "created_at",
        )

    def build_entity(self, target: invites.InviteWithMetadata) -> invites.InviteWithMetadata:
        super().build_entity(target)
        target.approximate_member_count = None
        target.approximate_presence_count = None
        target.channel = None
        target.guild = None
        return target

    @classmethod
    def build_from_entity(
        cls: typing.Type[_InviteData], entity: invites.InviteWithMetadata, **kwargs: typing.Any
    ) -> _InviteData:
        return super().build_from_entity(
            entity,
            **kwargs,
            inviter_id=entity.inviter.id if entity.inviter is not None else None,
            target_user_id=entity.target_user.id if entity.target_user is not None else None,
        )


@attr.s(auto_attribs=True, kw_only=True, slots=True, repr=False, hash=False)
class _MemberData(_BaseData[guilds.Member]):
    id: snowflake.Snowflake
    guild_id: snowflake.Snowflake
    nickname: undefined.UndefinedNoneOr[str]
    role_ids: typing.Tuple[snowflake.Snowflake, ...]
    joined_at: undefined.UndefinedOr[datetime.datetime]
    premium_since: undefined.UndefinedNoneOr[datetime.datetime]
    is_deaf: undefined.UndefinedOr[bool]
    is_mute: undefined.UndefinedOr[bool]

    @classmethod
    def get_fields(cls) -> typing.Collection[str]:
        return "guild_id", "nickname", "role_ids", "joined_at", "premium_since", "is_deaf", "is_mute"

    @classmethod
    def build_from_entity(cls: typing.Type[_MemberData], entity: guilds.Member, **kwargs: typing.Any) -> _MemberData:
        return super().build_from_entity(entity, **kwargs, id=entity.user.id, role_ids=tuple(entity.role_ids))


@attr.s(auto_attribs=True, kw_only=True, slots=True, repr=False, hash=False)
class _UserData(_BaseData[users.User]):
    id: snowflake.Snowflake
    discriminator: str
    username: str
    avatar_hash: typing.Optional[str]
    is_bot: undefined.UndefinedOr[bool]
    is_system: undefined.UndefinedOr[bool]
    flags: users.UserFlag
    # meta attributes
    ref_count: int = 0
    """The amount of reference that are keeping this user alive in the cache."""

    @classmethod
    def get_fields(cls) -> typing.Collection[str]:
        return "id", "discriminator", "username", "avatar_hash", "is_bot", "is_system", "flags"


@attr.s(auto_attribs=True, kw_only=True, slots=True, repr=False, hash=False)
class _KnownCustomEmojiData(_BaseData[emojis.KnownCustomEmoji]):
    id: snowflake.Snowflake
    name: typing.Optional[str]  # TODO: Shouldn't ever be None here
    is_animated: typing.Optional[bool]  # TODO: Shouldn't ever be None here
    guild_id: snowflake.Snowflake
    role_ids: typing.Tuple[snowflake.Snowflake, ...]
    user_id: typing.Optional[snowflake.Snowflake]
    is_colons_required: bool
    is_managed: bool
    is_available: bool

    @classmethod
    def get_fields(cls) -> typing.Collection[str]:
        return "id", "name", "is_animated", "guild_id", "role_ids", "is_colons_required", "is_managed", "is_available"

    @classmethod
    def build_from_entity(
        cls: typing.Type[_KnownCustomEmojiData], entity: emojis.KnownCustomEmoji, **kwargs: typing.Any
    ) -> _KnownCustomEmojiData:
        return super().build_from_entity(
            entity, **kwargs, user_id=entity.user.id if entity.user else None, role_ids=tuple(entity.role_ids)
        )


@attr.s(auto_attribs=True, kw_only=True, slots=True, repr=False, hash=False)
class _VoiceStateData(_BaseData[voices.VoiceState]):
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


class _DMTimeBasedMRUDict(typing.MutableMapping[snowflake.Snowflake, _DMChannelData]):
    __slots__ = ("_data", "_expiry")

    def __init__(
        self,
        source: typing.Union[typing.Mapping[snowflake.Snowflake, _DMChannelData], None] = None,
        /,
        *,
        expiry: datetime.timedelta,
    ) -> None:
        if expiry <= datetime.timedelta():
            raise ValueError("expiry time must be greater than 0 microseconds.")

        self._data: typing.Dict[snowflake.Snowflake, _DMChannelData] = dict(source or ())
        self._expiry = expiry

    def _garbage_collect(self) -> None:
        current_time = date.utc_datetime()
        for channel_id, dm_channel in tuple(self._data.items()):
            if dm_channel.last_message_id and current_time - dm_channel.last_message_id.created_at < self._expiry:
                break

            del self._data[channel_id]

    def __delitem__(self, sf: snowflake.Snowflake) -> None:
        del self._data[sf]
        self._garbage_collect()

    def __getitem__(self, sf: snowflake.Snowflake) -> _DMChannelData:
        return self._data[sf]

    def __iter__(self) -> typing.Iterator[snowflake.Snowflake]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __setitem__(self, sf: snowflake.Snowflake, value: _DMChannelData) -> None:
        self._garbage_collect()
        #  Seeing as we rely on insertion order in _garbage_collect, we have to make sure that each item is added to
        #  the end of the dict.
        if value.last_message_id is not None and sf in self:
            del self[sf]

        self._data[sf] = value


def _set_fields_if_defined(target: _ValueT, source: typing.Any, *, blacklist: typing.Tuple[str, ...] = ()) -> _ValueT:
    for field in attr.fields(type(source)):
        value = getattr(source, field.name, undefined.UNDEFINED)
        if value is not undefined.UNDEFINED and hasattr(target, field.name) and field.name not in blacklist:
            setattr(target, field.name, value)

    return target


class StatefulCacheComponentImpl(cache.ICacheComponent):
    """In-memory cache implementation."""

    __slots__: typing.Sequence[str] = (
        "_app",
        "_dm_channel_entries",
        "_emoji_entries",
        "_guild_channel_entries",
        "_guild_entries",
        "_intents",
        "_invite_entries",
        "_me",
        "_role_entries",
        "_user_entries",
    )

    def __init__(self, app: rest_app.IRESTApp, intents: typing.Optional[intents_.Intent]) -> None:
        self._me: typing.Optional[users.OwnUser] = None
        self._dm_channel_entries: typing.MutableMapping[snowflake.Snowflake, _DMChannelData] = _DMTimeBasedMRUDict(
            expiry=datetime.timedelta(minutes=5)
        )
        self._emoji_entries: typing.MutableMapping[snowflake.Snowflake, _KnownCustomEmojiData] = {}
        self._guild_channel_entries: typing.MutableMapping[snowflake.Snowflake, channels.GuildChannel] = {}
        self._guild_entries: typing.MutableMapping[snowflake.Snowflake, _GuildRecord] = {}
        self._invite_entries: typing.MutableMapping[str, _InviteData] = {}
        self._role_entries: typing.MutableMapping[snowflake.Snowflake, guilds.Role] = {}
        self._user_entries: typing.MutableMapping[snowflake.Snowflake, _UserData] = {}

        self._app = app
        self._intents = intents

    @property
    @typing.final
    def app(self) -> rest_app.IRESTApp:
        return self._app

    def _assert_has_intent(self, intents: intents_.Intent, /) -> None:
        if self._intents is not None and self._intents ^ intents:
            raise errors.MissingIntentError(intents) from None

    def _is_intent_enabled(self, intents: intents_.Intent, /) -> bool:
        return self._intents is None or (self._intents & intents) == intents

    def _build_dm_channel(
        self,
        channel_data: _DMChannelData,
        cached_users: typing.Optional[typing.Mapping[snowflake.Snowflake, _UserData]] = None,
    ) -> channels.DMChannel:
        channel = channel_data.build_entity(channels.DMChannel())
        channel.app = self._app

        if cached_users:
            channel.recipient = self._build_user(cached_users[channel_data.recipient_id])
        else:
            channel.recipient = self._build_user(self._user_entries[channel_data.recipient_id])

        return channel

    def clear_dm_channels(self) -> cache.ICacheView[snowflake.Snowflake, channels.DMChannel]:
        if not self._dm_channel_entries:
            return _EmptyCacheView()

        cached_dm_channels = self._dm_channel_entries
        self._dm_channel_entries = {}
        cached_users = {}

        for user_id in cached_dm_channels.keys():
            cached_users[user_id] = self._user_entries[user_id]
            self._increment_user_ref_count(user_id, -1)
            self._garbage_collect_user(user_id)

        return _StatefulCacheMappingView(
            cached_dm_channels, builder=lambda channel: self._build_dm_channel(channel, cached_users)
        )

    def delete_dm_channel(self, user_id: snowflake.Snowflake, /) -> typing.Optional[channels.DMChannel]:
        channel_data = self._dm_channel_entries.pop(user_id, None)
        if channel_data is None:
            return None

        channel = self._build_dm_channel(channel_data)
        self._increment_user_ref_count(user_id, -1)
        self._garbage_collect_user(user_id)
        return channel

    def get_dm_channel(self, user_id: snowflake.Snowflake, /) -> typing.Optional[channels.DMChannel]:
        if user_id in self._dm_channel_entries:
            return self._build_dm_channel(self._dm_channel_entries[user_id])

        return None

    def get_dm_channels_view(self) -> cache.ICacheView[snowflake.Snowflake, channels.DMChannel]:
        if not self._dm_channel_entries:
            return _EmptyCacheView()

        cached_users = {sf: user for sf, user in self._user_entries.items() if sf in self._dm_channel_entries}
        return _StatefulCacheMappingView(
            dict(self._dm_channel_entries), builder=lambda channel: self._build_dm_channel(channel, cached_users)
        )

    def set_dm_channel(self, channel: channels.DMChannel, /) -> None:
        self.set_user(channel.recipient)

        if channel.recipient.id not in self._dm_channel_entries:
            self._increment_user_ref_count(channel.recipient.id)

        self._dm_channel_entries[channel.recipient.id] = _DMChannelData.build_from_entity(channel)

    def update_dm_channel(
        self, channel: channels.DMChannel, /
    ) -> typing.Tuple[typing.Optional[channels.DMChannel], typing.Optional[channels.DMChannel]]:
        cached_dm_channel = self.get_dm_channel(channel.recipient.id)
        self.set_dm_channel(channel)
        return cached_dm_channel, self.get_dm_channel(channel.recipient.id)

    def _build_emoji(
        self,
        emoji_data: _KnownCustomEmojiData,
        cached_users: typing.Optional[typing.Mapping[snowflake.Snowflake, _UserData]] = None,
    ) -> emojis.KnownCustomEmoji:
        emoji = emoji_data.build_entity(emojis.KnownCustomEmoji())
        emoji.app = self._app

        if cached_users is not None and emoji_data.user_id is not None:
            emoji.user = self._build_user(cached_users[emoji_data.user_id])
        elif emoji_data.user_id is not None:
            emoji.user = self._build_user(self._user_entries[emoji_data.user_id])
        else:
            emoji.user = None

        return emoji

    def _clear_emojis(
        self, guild_id: undefined.UndefinedOr[snowflake.Snowflake] = undefined.UNDEFINED,
    ) -> cache.ICacheView[snowflake.Snowflake, emojis.KnownCustomEmoji]:
        emoji_ids: typing.Iterable[snowflake.Snowflake]
        if guild_id is undefined.UNDEFINED:
            emoji_ids = tuple(self._emoji_entries.keys())
        else:
            guild_record = self._guild_entries.get(guild_id)
            if guild_record is None or guild_record.emojis is None:  # TODO: explicit is vs implicit bool
                return _EmptyCacheView()

            emoji_ids = guild_record.emojis
            guild_record.emojis = None
            self._delete_guild_record_if_empty(guild_id)

        cached_emojis = {}
        cached_users = {}

        for emoji_id in emoji_ids:
            emoji_data = self._emoji_entries.pop(emoji_id)  # TODO: investigate bug with emojis update here.
            cached_emojis[emoji_id] = emoji_data

            if emoji_data.user_id is not None:
                cached_users[emoji_data.user_id] = self._user_entries[emoji_data.user_id]
                self._increment_user_ref_count(emoji_data.user_id, -1)
                self._garbage_collect_user(emoji_data.user_id)

        return _StatefulCacheMappingView(
            cached_emojis, builder=lambda emoji: self._build_emoji(emoji, cached_users=cached_users)
        )

    def clear_emojis(self) -> cache.ICacheView[snowflake.Snowflake, emojis.KnownCustomEmoji]:
        return self._clear_emojis()

    def clear_emojis_for_guild(
        self, guild_id: snowflake.Snowflake, /
    ) -> cache.ICacheView[snowflake.Snowflake, emojis.KnownCustomEmoji]:
        return self._clear_emojis(guild_id)

    def delete_emoji(self, emoji_id: snowflake.Snowflake, /) -> typing.Optional[emojis.KnownCustomEmoji]:
        emoji_data = self._emoji_entries.pop(emoji_id, None)
        if emoji_data is None:
            return None

        emoji = self._build_emoji(emoji_data)

        if emoji_data.user_id is not None:
            self._increment_user_ref_count(emoji_data.user_id, -1)
            self._garbage_collect_user(emoji_data.user_id)

        guild_record = self._guild_entries.get(emoji_data.guild_id)
        if guild_record and guild_record.roles:
            guild_record.roles.remove(emoji_id)

        return emoji

    def get_emoji(self, emoji_id: snowflake.Snowflake, /) -> typing.Optional[emojis.KnownCustomEmoji]:
        return self._build_emoji(self._emoji_entries[emoji_id]) if emojis in self._emoji_entries else None

    def get_emojis_view(self) -> cache.ICacheView[snowflake.Snowflake, emojis.KnownCustomEmoji]:
        return self._get_emojis_view()

    def get_emojis_view_for_guild(
        self, guild_id: snowflake.Snowflake, /
    ) -> cache.ICacheView[snowflake.Snowflake, emojis.KnownCustomEmoji]:
        return self._get_emojis_view(guild_id=guild_id)

    def _get_emojis_view(
        self, guild_id: undefined.UndefinedOr[snowflake.Snowflake] = undefined.UNDEFINED
    ) -> cache.ICacheView[snowflake.Snowflake, emojis.KnownCustomEmoji]:
        cached_emojis = {}
        cached_users = {}
        emoji_ids: typing.Iterable[snowflake.Snowflake]

        if guild_id is undefined.UNDEFINED:
            emoji_ids = self._emoji_entries.keys()
        else:
            guild_record = self._guild_entries.get(guild_id)
            if guild_record is None or not guild_record.emojis:
                return _EmptyCacheView()

            emoji_ids = guild_record.emojis

        for emoji_id in emoji_ids:
            emoji_data = self._emoji_entries[emoji_id]
            cached_emojis[emoji_id] = emoji_data

            if emoji_data.user_id is not None:
                cached_users[emoji_data.user_id] = self._user_entries[emoji_data.user_id]

        return _StatefulCacheMappingView(
            cached_emojis, builder=lambda emoji: self._build_emoji(emoji, cached_users=cached_users)
        )

    def set_emoji(self, emoji: emojis.KnownCustomEmoji, /) -> None:
        if emoji.user is not None:
            self.set_user(emoji.user)
            if emoji.id not in self._emoji_entries:
                self._increment_user_ref_count(emoji.user.id)

        self._emoji_entries[emoji.id] = _KnownCustomEmojiData.build_from_entity(emoji)
        guild_container = self._get_or_create_guild_record(emoji.guild_id)

        if guild_container.emojis is None:
            guild_container.emojis = _IDTable()

        guild_container.emojis.add(emoji.id)

    def update_emoji(
        self, emoji: emojis.KnownCustomEmoji, /
    ) -> typing.Tuple[typing.Optional[emojis.KnownCustomEmoji], typing.Optional[emojis.KnownCustomEmoji]]:
        cached_emoji = self.get_emoji(emoji.id)
        self.set_emoji(emoji)
        return cached_emoji, self.get_emoji(emoji.id)

    def _delete_guild_record_if_empty(self, guild_id: snowflake.Snowflake) -> None:
        if guild_id in self._guild_entries and not self._guild_entries[guild_id]:
            del self._guild_entries[guild_id]

    def _get_or_create_guild_record(self, guild_id: snowflake.Snowflake) -> _GuildRecord:
        if guild_id not in self._guild_entries:
            self._guild_entries[guild_id] = _GuildRecord()

        return self._guild_entries[guild_id]

    def clear_guilds(self) -> cache.ICacheView[snowflake.Snowflake, guilds.GatewayGuild]:
        cached_guilds = {}

        for guild_id, guild_record in tuple(self._guild_entries.items()):
            if guild_record.guild is None:
                continue

            cached_guilds[guild_id] = guild_record.guild
            guild_record.guild = None
            guild_record.is_available = None
            self._delete_guild_record_if_empty(guild_id)

        return _StatefulCacheMappingView(cached_guilds) if cached_guilds else _EmptyCacheView()

    def delete_guild(self, guild_id: snowflake.Snowflake, /) -> typing.Optional[guilds.GatewayGuild]:
        if guild_id not in self._guild_entries:
            return None

        guild_record = self._guild_entries[guild_id]
        guild = guild_record.guild

        if guild is not None:
            guild_record.guild = None
            guild_record.is_available = None
            self._delete_guild_record_if_empty(guild_id)

        return guild

    def get_guild(self, guild_id: snowflake.Snowflake, /) -> typing.Optional[guilds.GatewayGuild]:
        if (guild_record := self._guild_entries.get(guild_id)) is not None:
            if guild_record.guild and not guild_record.is_available:
                raise errors.UnavailableGuildError(guild_record.guild) from None

            return guild_record.guild

        return None

    def get_guilds_view(self) -> cache.ICacheView[snowflake.Snowflake, guilds.GatewayGuild]:
        results = {
            sf: copy.copy(guild_record.guild) for sf, guild_record in self._guild_entries.items() if guild_record.guild
        }  # TODO: include unavailable guilds here?
        return _StatefulCacheMappingView(results) if results else _EmptyCacheView()

    def set_guild(self, guild: guilds.GatewayGuild, /) -> None:
        guild_record = self._get_or_create_guild_record(guild.id)
        guild_record.guild = copy.copy(guild)
        guild_record.is_available = True

    def set_guild_availability(self, guild_id: snowflake.Snowflake, is_available: bool, /) -> None:
        guild_record = self._get_or_create_guild_record(guild_id=guild_id)
        guild_record.is_available = is_available  # TODO: only set this if guild object cached?

    # TODO: is this the best way to handle this?
    def set_initial_unavailable_guilds(self, guild_ids: typing.Collection[snowflake.Snowflake], /) -> None:
        # Invoked when we receive ON_READY, assume all of these are unavailable on startup.
        self._guild_entries = {guild_id: _GuildRecord(is_available=False) for guild_id in guild_ids}

    def update_guild(
        self, guild: guilds.GatewayGuild, /
    ) -> typing.Tuple[typing.Optional[guilds.GatewayGuild], typing.Optional[guilds.GatewayGuild]]:
        guild = copy.copy(guild)
        guild_record = self._guild_entries.get(guild.id)
        cached_guild = guild_record.guild if guild_record is not None else None

        # We have to manually update these because inconsistency by Discord.
        if cached_guild is not None:
            guild.member_count = cached_guild.member_count
            guild.joined_at = cached_guild.joined_at
            guild.is_large = cached_guild.is_large

        self.set_guild(guild)
        guild_record = self._guild_entries.get(guild.id)
        return cached_guild, guild_record.guild if guild_record is not None else None

    def clear_guild_channels(self) -> cache.ICacheView[snowflake.Snowflake, channels.GuildChannel]:
        raise NotImplementedError

    def clear_guild_channels_for_guild(
        self, guild_id: snowflake.Snowflake, /
    ) -> cache.ICacheView[snowflake.Snowflake, channels.GuildChannel]:
        raise NotImplementedError

    def delete_guild_channel(self, channel_id: snowflake.Snowflake, /) -> typing.Optional[channels.GuildChannel]:
        raise NotImplementedError

    def get_guild_channel(self, channel_id: snowflake.Snowflake, /) -> typing.Optional[channels.GuildChannel]:
        raise NotImplementedError

    def get_guild_channels_view(self) -> cache.ICacheView[snowflake.Snowflake, channels.GuildChannel]:
        raise NotImplementedError

    def get_guild_channels_view_for_guild(
        self, guild_id: snowflake.Snowflake, /
    ) -> cache.ICacheView[snowflake.Snowflake, channels.GuildChannel]:
        raise NotImplementedError

    def set_guild_channel(self, channel: channels.GuildChannel, /) -> None:
        raise NotImplementedError

    def update_guild_channel(
        self, channel: channels.GuildChannel, /
    ) -> typing.Tuple[typing.Optional[channels.GuildChannel], typing.Optional[channels.GuildChannel]]:
        raise NotImplementedError

    def _build_invite(
        self,
        invite_data: _InviteData,
        cached_users: undefined.UndefinedOr[typing.Mapping[snowflake.Snowflake, _UserData]] = undefined.UNDEFINED,
    ) -> invites.InviteWithMetadata:
        invite = invite_data.build_entity(invites.InviteWithMetadata())
        invite.app = self._app

        if cached_users is not undefined.UNDEFINED and invite_data.inviter_id is not None:
            invite.inviter = self._build_user(cached_users[invite_data.inviter_id])
        elif invite_data.inviter_id is not None:
            invite.inviter = self._build_user(self._user_entries[invite_data.inviter_id])
        else:
            invite.inviter = None

        return invite

    def _clear_invites(
        self, guild_id: undefined.UndefinedOr[snowflake.Snowflake] = undefined.UNDEFINED,
    ) -> cache.ICacheView[str, invites.InviteWithMetadata]:
        invite_codes: typing.Iterable[str]
        if guild_id is not undefined.UNDEFINED:
            guild_record = self._guild_entries.get(guild_id)

            if guild_record is None or guild_record.invites is None:
                return _EmptyCacheView()

            invite_codes = guild_record.invites
            guild_record.invites = None
            self._delete_guild_record_if_empty(guild_id)

        else:
            invite_codes = self._invite_entries.keys()

        cached_invites = {}
        cached_users = {}

        for code in invite_codes:
            invite_data = self._invite_entries.pop(code)
            cached_invites[code] = invite_data

            if invite_data.inviter_id is not None:
                cached_users[invite_data.inviter_id] = self._user_entries[invite_data.inviter_id]
                self._increment_user_ref_count(invite_data.inviter_id, -1)
                self._garbage_collect_user(invite_data.inviter_id)

            if invite_data.target_user_id is not None:
                cached_users[invite_data.target_user_id] = self._user_entries[invite_data.target_user_id]
                self._increment_user_ref_count(invite_data.target_user_id, -1)
                self._garbage_collect_user(invite_data.target_user_id)

        return _StatefulCacheMappingView(
            cached_invites, builder=lambda invite_data: self._build_invite(invite_data, cached_users=cached_users)
        )

    def clear_invites(self) -> cache.ICacheView[str, invites.InviteWithMetadata]:
        return self._clear_invites()

    def clear_invites_for_guild(
        self, guild_id: snowflake.Snowflake, /
    ) -> cache.ICacheView[str, invites.InviteWithMetadata]:
        return self._clear_invites(guild_id=guild_id)

    def clear_invites_for_channel(
        self, guild_id: snowflake.Snowflake, channel_id: snowflake.Snowflake, /
    ) -> cache.ICacheView[str, invites.InviteWithMetadata]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is None or guild_record.invites is None:
            return _EmptyCacheView()

        cached_invites = {}
        cached_users = {}

        for code in tuple(guild_record.invites):
            invite_data = self._invite_entries[code]
            if invite_data.channel_id != channel_id:
                continue

            cached_invites[code] = invite_data
            guild_record.invites.remove(code)

            if invite_data.inviter_id is not None:
                cached_users[invite_data.inviter_id] = self._user_entries[invite_data.inviter_id]
                self._increment_user_ref_count(invite_data.inviter_id, -1)
                self._garbage_collect_user(invite_data.inviter_id)

            if invite_data.target_user_id is not None:
                cached_users[invite_data.target_user_id] = self._user_entries[invite_data.target_user_id]
                self._increment_user_ref_count(invite_data.target_user_id, -1)
                self._garbage_collect_user(invite_data.target_user_id)

        if not guild_record.invites:
            guild_record.invites = None
            self._delete_guild_record_if_empty(guild_id)

        return _StatefulCacheMappingView(
            cached_invites, builder=lambda invite_data: self._build_invite(invite_data, cached_users=cached_users)
        )

    def delete_invite(self, code: str, /) -> typing.Optional[invites.InviteWithMetadata]:
        if code not in self._invite_entries:
            return None

        invite = self._invite_entries.pop(code).build_entity(invites.InviteWithMetadata())

        if invite.inviter is not None:
            self._increment_user_ref_count(invite.inviter.id, -1)
            self._garbage_collect_user(invite.inviter.id)

        if invite.target_user is not None:
            self._increment_user_ref_count(invite.target_user.id, -1)
            self._garbage_collect_user(invite.target_user.id)

        return invite

    def get_invite(self, code: str, /) -> typing.Optional[invites.InviteWithMetadata]:
        return self._build_invite(self._invite_entries[code]) if code in self._invite_entries else None

    def _get_invites_view(
        self, guild_id: undefined.UndefinedOr[snowflake.Snowflake] = undefined.UNDEFINED
    ) -> cache.ICacheView[str, invites.InviteWithMetadata]:
        invite_ids: typing.Iterable[str]
        if guild_id is undefined.UNDEFINED:
            invite_ids = self._invite_entries.keys()

        else:
            guild_entry = self._guild_entries.get(guild_id)
            if guild_entry is None or guild_entry.invites is None:
                return _EmptyCacheView()

            invite_ids = guild_entry.invites

        cached_invites = {}
        cached_users = {}

        for code in invite_ids:
            invite_data = self._invite_entries[code]
            cached_invites[code] = invite_data

            if invite_data.inviter_id is not None:
                cached_users[invite_data.inviter_id] = self._user_entries[invite_data.inviter_id]

            if invite_data.target_user_id is not None:
                cached_users[invite_data.target_user_id] = self._user_entries[invite_data.target_user_id]

        return _StatefulCacheMappingView(
            cached_invites, builder=lambda invite_data: self._build_invite(invite_data, cached_users=cached_users)
        )

    def get_invites_view(self) -> cache.ICacheView[str, invites.InviteWithMetadata]:
        return self._get_invites_view()

    def get_invites_view_for_guild(
        self, guild_id: snowflake.Snowflake, /
    ) -> cache.ICacheView[str, invites.InviteWithMetadata]:
        return self._get_invites_view(guild_id=guild_id)

    def get_invites_view_for_channel(
        self, guild_id: snowflake.Snowflake, channel_id: snowflake.Snowflake, /,
    ) -> cache.ICacheView[str, invites.InviteWithMetadata]:
        guild_entry = self._guild_entries.get(guild_id)
        if guild_entry is None or guild_entry.invites is None:
            return _EmptyCacheView()

        cached_invites = {}
        cached_users = {}
        invite_ids: typing.Iterable[str]

        for code in guild_entry.invites:
            invite_data = self._invite_entries[code]
            if invite_data.channel_id != channel_id:
                continue

            cached_invites[code] = invite_data

            if invite_data.inviter_id is not None:
                cached_users[invite_data.inviter_id] = self._user_entries[invite_data.inviter_id]

            if invite_data.target_user_id is not None:
                cached_users[invite_data.target_user_id] = self._user_entries[invite_data.target_user_id]

        return _StatefulCacheMappingView(
            cached_invites, builder=lambda invite_data: self._build_invite(invite_data, cached_users=cached_users)
        )

    def set_invite(self, invite: invites.InviteWithMetadata, /) -> None:
        if invite.inviter is not None:
            self.set_user(invite.inviter)
            if invite.code not in self._invite_entries:
                self._increment_user_ref_count(invite.inviter.id)

        if invite.target_user is not None:
            self.set_user(invite.target_user)
            if invite.code not in self._invite_entries:
                self._increment_user_ref_count(invite.target_user.id)

        self._invite_entries[invite.code] = _InviteData.build_from_entity(invite)
        if invite.guild_id:
            guild_entry = self._get_or_create_guild_record(invite.guild_id)

            if guild_entry.invites is None:
                guild_entry.invites = []

            guild_entry.invites.append(invite.code)

    def update_invite(
        self, invite: invites.InviteWithMetadata, /
    ) -> typing.Tuple[typing.Optional[invites.InviteWithMetadata], typing.Optional[invites.InviteWithMetadata]]:
        cached_invite = self.get_invite(invite.code)
        self.set_invite(invite)
        return cached_invite, self.get_invite(invite.code)

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
        cached_users: typing.Optional[typing.Mapping[snowflake.Snowflake, _UserData]] = None,
    ) -> guilds.Member:
        member = member_data.build_entity(guilds.Member())
        user_data = cached_users[member_data.id] if cached_users is not None else self._user_entries[member_data.id]
        member.user = self._build_user(user_data)
        return member

    @staticmethod
    def _can_remove_member(guild_record: _GuildRecord, user_id: snowflake.Snowflake) -> bool:
        return bool(not guild_record.voice_states or user_id not in guild_record.voice_states)

    def clear_members(
        self,
    ) -> cache.ICacheView[snowflake.Snowflake, cache.ICacheView[snowflake.Snowflake, guilds.Member]]:
        views = {}
        for guild_id, guild_record in tuple(self._guild_entries.items()):
            if not guild_record.members:
                continue

            views[guild_id] = self.clear_members_for_guild(guild_id)

        return _StatefulCacheMappingView(views)

    def clear_members_for_guild(
        self, guild_id: snowflake.Snowflake, /
    ) -> cache.ICacheView[snowflake.Snowflake, guilds.Member]:
        guild_record = self._guild_entries.get(guild_id)  # TODO: optional return on clear?
        if guild_record is None or guild_record.members is None:
            return _EmptyCacheView()

        cached_members = {}
        cached_users = {}

        for user_id in tuple(guild_record.members.keys()):
            if not self._can_remove_member(guild_record, user_id):
                continue

            cached_members[user_id] = guild_record.members[user_id]
            cached_users[user_id] = self._user_entries[user_id]
            self._increment_user_ref_count(user_id, -1)
            self._garbage_collect_user(user_id)

        if not guild_record.members:
            guild_record.members = None

        self._delete_guild_record_if_empty(guild_id)
        return _StatefulCacheMappingView(
            cached_members, builder=lambda member: self._build_member(member, cached_users=cached_users)
        )

    def delete_member(
        self, guild_id: snowflake.Snowflake, user_id: snowflake.Snowflake, /
    ) -> typing.Optional[guilds.Member]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is None or not self._can_remove_member(guild_record, user_id):
            return None

        member = guild_record.members.pop(user_id, None) if guild_record.members else None
        if member is None:
            return None

        built_member = self._build_member(member)
        if not guild_record.members:
            guild_record.members = None

        self._delete_guild_record_if_empty(guild_id)
        self._increment_user_ref_count(user_id, -1)
        self._garbage_collect_user(user_id)
        return built_member

    def get_member(
        self, guild_id: snowflake.Snowflake, user_id: snowflake.Snowflake, /
    ) -> typing.Optional[guilds.Member]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is None or guild_record.members is None:
            return None

        member = guild_record.members.get(user_id)
        return self._build_member(member) if member is not None else None

    def get_members_view(
        self,
    ) -> cache.ICacheView[snowflake.Snowflake, cache.ICacheView[snowflake.Snowflake, guilds.Member]]:
        views = {}

        for guild_id, guild_record in self._guild_entries.items():
            if guild_record.members is None:
                continue

            views[guild_id] = self.get_members_view_for_guild(guild_id)

        return _StatefulCacheMappingView(views)

    def get_members_view_for_guild(
        self, guild_id: snowflake.Snowflake, /
    ) -> cache.ICacheView[snowflake.Snowflake, guilds.Member]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is None or guild_record.members is None:
            return _EmptyCacheView()

        cached_members = {}
        cached_users = {}

        for user_id, member in guild_record.members.items():
            cached_users[user_id] = self._user_entries[user_id]
            cached_members[user_id] = member

        return _StatefulCacheMappingView(
            cached_members, builder=lambda member: self._build_member(member, cached_users=cached_users)
        )

    def set_member(self, member: guilds.Member, /) -> None:
        guild_record = self._get_or_create_guild_record(member.guild_id)
        self.set_user(member.user)
        member_data = _MemberData.build_from_entity(member)

        if guild_record.members is None:
            guild_record.members = {}

        if member.user.id not in guild_record.members:
            self._increment_user_ref_count(member.user.id)

        guild_record.members[member_data.id] = member_data

    def update_member(
        self, member: guilds.Member, /
    ) -> typing.Tuple[typing.Optional[guilds.Member], typing.Optional[guilds.Member]]:
        cached_member = self.get_member(member.guild_id, member.user.id)
        self.set_member(member)
        return cached_member, self.get_member(member.guild_id, member.user.id)

    def clear_presences(
        self,
    ) -> cache.ICacheView[snowflake.Snowflake, cache.ICacheView[snowflake.Snowflake, presences.MemberPresence]]:
        raise NotImplementedError

    def clear_presences_for_guild(
        self, guild_id: snowflake.Snowflake, /
    ) -> cache.ICacheView[snowflake.Snowflake, presences.MemberPresence]:
        raise NotImplementedError

    def delete_presence(
        self, guild_id: snowflake.Snowflake, user_id: snowflake.Snowflake, /
    ) -> typing.Optional[presences.MemberPresence]:
        raise NotImplementedError

    def get_presence(
        self, guild_id: snowflake.Snowflake, user_id: snowflake.Snowflake, /
    ) -> typing.Optional[presences.MemberPresence]:
        raise NotImplementedError

    def get_presences_view(
        self,
    ) -> cache.ICacheView[snowflake.Snowflake, cache.ICacheView[snowflake.Snowflake, presences.MemberPresence]]:
        raise NotImplementedError

    def get_presences_view_for_guild(
        self, guild_id: snowflake.Snowflake, /
    ) -> cache.ICacheView[snowflake.Snowflake, presences.MemberPresence]:
        raise NotImplementedError

    def get_presences_view_for_user(
        self, user_id: snowflake.Snowflake, /
    ) -> cache.ICacheView[snowflake.Snowflake, presences.MemberPresence]:
        raise NotImplementedError

    def set_presence(self, presence: presences.MemberPresence, /) -> None:
        raise NotImplementedError

    def update_presence(
        self, presence: presences.MemberPresence, /
    ) -> typing.Tuple[typing.Optional[presences.MemberPresence], typing.Optional[presences.MemberPresence]]:
        raise NotImplementedError

    def clear_roles(self) -> cache.ICacheView[snowflake.Snowflake, guilds.Role]:
        if not self._role_entries:
            return _EmptyCacheView()

        roles = self._role_entries
        self._role_entries = {}
        return _StatefulCacheMappingView(roles)

    def clear_roles_for_guild(
        self, guild_id: snowflake.Snowflake, /
    ) -> cache.ICacheView[snowflake.Snowflake, guilds.Role]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is None or not guild_record.roles:
            return _EmptyCacheView()

        view = _StatefulCacheMappingView({role_id: self._role_entries[role_id] for role_id in guild_record.roles})
        guild_record.roles = None
        self._delete_guild_record_if_empty(guild_id)
        return view

    def delete_role(self, role_id: snowflake.Snowflake, /) -> typing.Optional[guilds.Role]:
        role = self._role_entries.pop(role_id, None)  # TODO: this honestly feels jank, redo soon
        if role is None:
            return None

        guild_record = self._guild_entries.get(role.guild_id)
        if guild_record and guild_record.roles is not None:
            guild_record.roles.remove(role_id)

            if not guild_record.roles:
                guild_record.roles = None
                self._delete_guild_record_if_empty(role.guild_id)

        return role

    def get_role(self, role_id: snowflake.Snowflake, /) -> typing.Optional[guilds.Role]:
        return self._role_entries.get(role_id)

    def get_roles_view(self) -> cache.ICacheView[snowflake.Snowflake, guilds.Role]:
        return _StatefulCacheMappingView(dict(self._role_entries))

    def get_roles_view_for_guild(
        self, guild_id: snowflake.Snowflake, /
    ) -> cache.ICacheView[snowflake.Snowflake, guilds.Role]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is None or guild_record.roles is None:
            return _EmptyCacheView()

        return _StatefulCacheMappingView({role_id: self._role_entries[role_id] for role_id in guild_record.roles})

    def set_role(self, role: guilds.Role, /) -> None:
        self._role_entries[role.id] = role
        guild_record = self._get_or_create_guild_record(role.guild_id)

        if guild_record.roles is None:
            guild_record.roles = _IDTable()

        guild_record.roles.add(role.id)

    def update_role(
        self, role: guilds.Role, /
    ) -> typing.Tuple[typing.Optional[guilds.Role], typing.Optional[guilds.Role]]:
        cached_role = self.get_role(role.id)
        self.set_role(role)
        return cached_role, self.get_role(role.id)

    def _build_user(self, user_data: _UserData) -> users.User:
        user = users.UserImpl()
        user_data.build_entity(user)
        user.app = self._app
        return user

    def _can_remove_user(self, user_id: snowflake.Snowflake) -> bool:
        user_data = self._user_entries.get(user_id)
        return bool(user_data and user_data.ref_count == 0)

    def _increment_user_ref_count(self, user_id: snowflake.Snowflake, increment: int = 1) -> None:
        self._user_entries[user_id].ref_count += increment

    def _garbage_collect_user(self, user_id: snowflake.Snowflake) -> None:
        if self._can_remove_user(user_id):
            del self._user_entries[user_id]

    def clear_users(self) -> cache.ICacheView[snowflake.Snowflake, users.User]:
        if not self._user_entries:
            return _EmptyCacheView()

        cached_users = {}

        for user_id, user_data in tuple(self._user_entries.items()):
            if user_data.ref_count > 0:
                continue

            cached_users[user_id] = user_data
            del self._user_entries[user_id]

        return _StatefulCacheMappingView(cached_users, builder=self._build_user) if cached_users else _EmptyCacheView()

    def delete_user(self, user_id: snowflake.Snowflake, /) -> typing.Optional[users.User]:
        if self._can_remove_user(user_id):
            return self._build_user(self._user_entries.pop(user_id))

        return None

    def get_user(self, user_id: snowflake.Snowflake, /) -> typing.Optional[users.User]:
        return self._build_user(self._user_entries[user_id]) if user_id in self._user_entries else None

    def get_users_view(self) -> cache.ICacheView[snowflake.Snowflake, users.User]:
        if not self._user_entries:
            return _EmptyCacheView()

        return _StatefulCacheMappingView(dict(self._user_entries), builder=self._build_user)

    def set_user(self, user: users.User, /) -> None:
        user_data = _UserData.build_from_entity(user)

        if user.id in self._user_entries:
            user_data.ref_count = self._user_entries[user.id].ref_count

        self._user_entries[user.id] = user_data

    def update_user(
        self, user: users.User, /
    ) -> typing.Tuple[typing.Optional[users.User], typing.Optional[users.User]]:
        cached_user = self.get_user(user.id)
        self.set_user(user)
        return cached_user, self.get_user(user.id)

    def _build_voice_state(
        self,
        voice_data: _VoiceStateData,
        cached_members: typing.Optional[typing.Mapping[snowflake.Snowflake, _MemberData]] = None,
        cached_users: typing.Optional[typing.Mapping[snowflake.Snowflake, _UserData]] = None,
    ) -> voices.VoiceState:
        voice_state = voice_data.build_entity(voices.VoiceState())
        voice_state.app = self._app

        if cached_members:
            voice_state.member = self._build_member(cached_members[voice_state.user_id], cached_users=cached_users)
        else:
            guild_record = self._guild_entries[voice_state.guild_id]
            assert guild_record.members is not None  # noqa S101
            member_data = guild_record.members[voice_state.user_id]
            voice_state.member = self._build_member(member_data, cached_users=cached_users)

        return voice_state

    def clear_voice_states(
        self,
    ) -> cache.ICacheView[snowflake.Snowflake, cache.ICacheView[snowflake.Snowflake, voices.VoiceState]]:
        views = {}

        for guild_id, guild_record in tuple(self._guild_entries.items()):
            if not guild_record.voice_states:
                continue

            views[guild_id] = self.clear_voice_states_for_guild(guild_id)

        return _StatefulCacheMappingView(views)

    def clear_voice_states_for_guild(
        self, guild_id: snowflake.Snowflake, /
    ) -> cache.ICacheView[snowflake.Snowflake, voices.VoiceState]:
        guild_record = self._guild_entries.get(guild_id)

        if guild_record is None or guild_record.voice_states is None:
            return _EmptyCacheView()

        assert guild_record.members is not None  # noqa S101
        cached_voice_states = guild_record.voice_states
        guild_record.voice_states = None
        cached_members = {}
        cached_users = {}

        for user_id in cached_voice_states.keys():
            cached_members[user_id] = guild_record.members[user_id]
            cached_users[user_id] = self._user_entries[user_id]

        self._delete_guild_record_if_empty(guild_id)
        return _StatefulCacheMappingView(
            cached_voice_states,
            builder=lambda voice_data: self._build_voice_state(
                voice_data, cached_members=cached_members, cached_users=cached_users
            ),
        )

    def clear_voice_states_for_channel(
        self, guild_id: snowflake.Snowflake, channel_id: snowflake.Snowflake, /
    ) -> cache.ICacheView[snowflake.Snowflake, voices.VoiceState]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is None or guild_record.voice_states is None:
            return _EmptyCacheView()

        assert guild_record.members is not None  # noqa S101
        cached_members = {}
        cached_users = {}
        cached_voice_states = {}

        for user_id, voice_state in guild_record.voice_states.items():
            if voice_state.channel_id != channel_id:
                continue

            cached_members[user_id] = guild_record.members[user_id]
            cached_users[user_id] = self._user_entries[user_id]
            cached_voice_states[user_id] = voice_state

        if not guild_record.voice_states:
            guild_record.voice_states = None

        self._delete_guild_record_if_empty(guild_id)
        return _StatefulCacheMappingView(
            cached_voice_states,
            builder=lambda voice_state: self._build_voice_state(
                voice_state, cached_members=cached_members, cached_users=cached_users
            ),
        )

    # TODO: this needs also delete the relevant member object if the member cache is disabled
    def delete_voice_state(
        self, guild_id: snowflake.Snowflake, user_id: snowflake.Snowflake, /
    ) -> typing.Optional[voices.VoiceState]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is None:
            return None

        voice_state_data = guild_record.voice_states.pop(user_id, None) if guild_record.voice_states else None
        if voice_state_data is None:
            return None

        if not guild_record.voice_states:
            guild_record.voice_states = None

        self._delete_guild_record_if_empty(guild_id)
        return self._build_voice_state(voice_state_data)

    def get_voice_state(
        self, guild_id: snowflake.Snowflake, user_id: snowflake.Snowflake, /
    ) -> typing.Optional[voices.VoiceState]:
        guild_record = self._guild_entries.get(guild_id)
        voice_data = guild_record.voice_states.get(user_id) if guild_record and guild_record.voice_states else None
        return self._build_voice_state(voice_data) if voice_data else None

    def get_voice_states_view(
        self,
    ) -> cache.ICacheView[snowflake.Snowflake, cache.ICacheView[snowflake.Snowflake, voices.VoiceState]]:
        views = {}

        for guild_id, guild_record in self._guild_entries.items():
            if not guild_record.voice_states:
                continue

            views[guild_id] = self.get_voice_states_view_for_guild(guild_id)

        return _StatefulCacheMappingView(views)

    def get_voice_states_view_for_channel(
        self, guild_id: snowflake.Snowflake, channel_id: snowflake.Snowflake, /
    ) -> cache.ICacheView[snowflake.Snowflake, voices.VoiceState]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is None or guild_record.voice_states is None:
            return _EmptyCacheView()

        assert guild_record.members is not None  # noqa S10
        cached_members = {}
        cached_users = {}
        cached_voice_states = {}

        for user_id, voice_state in guild_record.voice_states.items():
            if voice_state.channel_id != channel_id:
                continue

            cached_members[user_id] = guild_record.members[user_id]
            cached_users[user_id] = self._user_entries[user_id]
            cached_voice_states[user_id] = voice_state

        return _StatefulCacheMappingView(
            cached_voice_states,
            builder=lambda voice_data: self._build_voice_state(
                voice_data, cached_members=cached_members, cached_users=cached_users
            ),
        )

    def get_voice_states_view_for_guild(
        self, guild_id: snowflake.Snowflake, /
    ) -> cache.ICacheView[snowflake.Snowflake, voices.VoiceState]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is None or guild_record.voice_states is None:
            return _EmptyCacheView()

        assert guild_record.members is not None  # noqa S10
        voice_states = dict(guild_record.voice_states)
        cached_members = {}
        cached_users = {}

        for user_id in voice_states.keys():
            cached_members[user_id] = guild_record.members[user_id]
            cached_users[user_id] = self._user_entries[user_id]

        return _StatefulCacheMappingView(
            voice_states,
            builder=lambda voice_data: self._build_voice_state(
                voice_data, cached_members=cached_members, cached_users=cached_users
            ),
        )

    def set_voice_state(self, voice_state: voices.VoiceState, /) -> None:
        guild_record = self._get_or_create_guild_record(voice_state.guild_id)

        if guild_record.voice_states is None:
            guild_record.voice_states = {}

        self.set_member(voice_state.member)
        guild_record.voice_states[voice_state.user_id] = _VoiceStateData.build_from_entity(voice_state)

    def update_voice_state(
        self, voice_state: voices.VoiceState, /
    ) -> typing.Tuple[typing.Optional[voices.VoiceState], typing.Optional[voices.VoiceState]]:
        cached_voice_state = self.get_voice_state(voice_state.guild_id, voice_state.user_id)
        self.set_voice_state(voice_state)
        return cached_voice_state, self.get_voice_state(voice_state.guild_id, voice_state.user_id)
