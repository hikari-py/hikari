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
"""Various utilities that may be used in a cache-impl."""
from __future__ import annotations

__all__: typing.List[str] = [
    "StatefulCacheMappingView",
    "EmptyCacheView",
    "GuildRecord",
    "BaseData",
    "InviteData",
    "MemberData",
    "KnownCustomEmojiData",
    "RichActivityData",
    "MemberPresenceData",
    "VoiceStateData",
    "GenericRefWrapper",
    "copy_guild_channel",
    "GuildChannelCacheMappingView",
    "Cache3DMappingView",
    "DataT",
    "KeyT",
    "ValueT",
]

import abc
import copy
import datetime
import typing

import attr

from hikari import channels
from hikari import emojis
from hikari import guilds
from hikari import invites
from hikari import iterators
from hikari import presences
from hikari import snowflakes
from hikari import undefined
from hikari import voices
from hikari.api import cache
from hikari.internal import attr_extensions
from hikari.internal import collections

DataT = typing.TypeVar("DataT", bound="BaseData[typing.Any]")
"""Type-hint for "data" objects used for storing and building entities."""
KeyT = typing.TypeVar("KeyT", bound=typing.Hashable)
"""Type-hint for mapping keys."""
ValueT = typing.TypeVar("ValueT")
"""Type-hint for mapping values."""


class StatefulCacheMappingView(cache.CacheView[KeyT, ValueT], typing.Generic[KeyT, ValueT]):
    """A cache mapping view implementation used for representing cached data.

    Parameters
    ----------
    items : typing.Mapping[KeyT, typing.Union[ValueT, DataT, GenericRefWrapper[ValueT]]]
        A mapping of keys to the values in their raw forms, wrapped by a ref
        wrapper or in a data form.
    builder : typing.Optional[typing.Callable[[DataT], ValueT]]
        The callable used to build entities before they're returned by the
        mapping. This is used to cover the case when items stores `DataT` objects.
    unpack : bool
        Whether to unpack items from their ref wrappers or not before returning
        them. This accounts for when `items` is `GenericRefWrapper[ValueT]`.
    predicate : typing.Optional[typing.Callable[[typing.Any], bool]]
        A callable to use to determine whether entries should be returned or hidden,
        this should take in whatever raw type was passed for the value in `items`.
        This may be `builtins.None` if all entries should be exposed.
    """

    __slots__: typing.Sequence[str] = ("_builder", "_data", "_unpack", "_predicate")

    def __init__(
        self,
        items: typing.Mapping[KeyT, typing.Union[ValueT, DataT, GenericRefWrapper[ValueT]]],
        *,
        builder: typing.Optional[typing.Callable[[DataT], ValueT]] = None,
        unpack: bool = False,
        predicate: typing.Optional[typing.Callable[[typing.Any], bool]] = None,
    ) -> None:
        self._builder = builder
        self._data = items
        self._unpack = unpack
        self._predicate = predicate

    @classmethod
    def _copy(cls, value: ValueT) -> ValueT:
        return copy.copy(value)

    def __contains__(self, key: typing.Any) -> bool:
        return key in self._data and (self._predicate is None or self._predicate(self._data[key]))

    def __getitem__(self, key: KeyT) -> ValueT:
        entry = self._data[key]

        if self._predicate is not None and not self._predicate(entry):
            raise KeyError(key)

        if self._builder is not None:
            entry = self._builder(entry)  # type: ignore[arg-type]
        elif self._unpack:
            assert isinstance(entry, GenericRefWrapper)
            entry = self._copy(entry.object)
        else:
            entry = self._copy(entry)  # type: ignore[arg-type]

        return entry

    def __iter__(self) -> typing.Iterator[KeyT]:
        if self._predicate is None:
            return iter(self._data)
        else:
            return (key for key, value in self._data.items() if self._predicate(value))

    def __len__(self) -> int:
        if self._predicate is None:
            return len(self._data)
        else:
            return sum(1 for value in self._data.values() if self._predicate(value))

    def get_item_at(self, index: int) -> ValueT:
        current_index = -1

        for key, value in self._data.items():
            if self._predicate is None or self._predicate(value):
                index += 1

            if current_index == index:
                return self[key]

        raise IndexError(index)

    def iterator(self) -> iterators.LazyIterator[ValueT]:
        return iterators.FlatLazyIterator(self.values())


class EmptyCacheView(cache.CacheView[typing.Any, typing.Any]):
    """An empty cache view implementation."""

    __slots__: typing.Sequence[str] = ()

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

    def iterator(self) -> iterators.LazyIterator[ValueT]:
        return iterators.FlatLazyIterator(())


@attr_extensions.with_copy
@attr.s(slots=True, repr=False, hash=False, weakref_slot=False)
class GuildRecord:
    """An object used for storing guild specific cached information in-memory.

    This includes references to the cached entities that "belong" to the guild
    by ID if it's globally unique or by object if it's only unique within the
    guild.
    """

    is_available: typing.Optional[bool] = attr.ib(default=None)
    """Whether the chached guild is available or not.

    This will be `builtins.None` when no `GuildRecord.guild` is also
    `builtins.None` else `builtins.bool`.
    """

    guild: typing.Optional[guilds.GatewayGuild] = attr.ib(default=None)
    """A cached guild object.

    This will be `hikari.guilds.GatewayGuild` or `builtins.None` if not cached.
    """

    channels: typing.Optional[typing.MutableSet[snowflakes.Snowflake]] = attr.ib(default=None)
    """A set of the IDs of the guild channels cached for this guild.

    This will be `builtins.None` if no channels are cached for this guild else
    `typing.MutableSet[hikari.snowflakes.Snowflake]` of channel IDs.
    """

    emojis: typing.Optional[typing.MutableSet[snowflakes.Snowflake]] = attr.ib(default=None)
    """A set of the IDs of the emojis cached for this guild.

    This will be `builtins.None` if no emojis are cached for this guild else
    `typing.MutableSet[hikari.snowflakes.Snowflake]` of emoji IDs.
    """

    invites: typing.Optional[typing.MutableSequence[str]] = attr.ib(default=None)
    """A set of the `builtins.str` codes of the invites cached for this guild.

    This will be `builtins.None` if no invites are cached for this guild else
    `typing.MutableSequence[str]` of invite codes.
    """

    members: typing.Optional[collections.ExtendedMutableMapping[snowflakes.Snowflake, MemberData]] = attr.ib(
        default=None
    )
    """A mapping of user IDs to the objects of members cached for this guild.

    This will be `builtins.None` if no members are cached for this guild else
    `hikari.internal.collections.ExtendedMutableMapping[hikari.snowflakes.Snowflake, MemberData]`.
    """

    presences: typing.Optional[collections.ExtendedMutableMapping[snowflakes.Snowflake, MemberPresenceData]] = attr.ib(
        default=None
    )
    """A mapping of user IDs to objects of the presences cached for this guild.

    This will be `builtins.None` if no presences are cached for this guild else
    `hikari.internal.collections.ExtendedMutableMapping[hikari.snowflakes.Snowflake, MemberPresenceData]`.
    """

    roles: typing.Optional[typing.MutableSet[snowflakes.Snowflake]] = attr.ib(default=None)
    """A set of the IDs of the roles cached for this guild.

    This will be `builtins.None` if no roles are cached for this guild else
    `typing.MutableSet[hikari.snowflakes.Snowflake]` of role IDs.
    """

    voice_states: typing.Optional[collections.ExtendedMutableMapping[snowflakes.Snowflake, VoiceStateData]] = attr.ib(
        default=None
    )
    """A mapping of user IDs to objects of the voice states cached for this guild.

    This will be `builtins.None` if no voice states are cached for this guild else
    `hikari.internal.collections.ExtendedMutableMapping[hikari.snowflakes.Snowflake, VoiceStateData]`.
    """

    def __bool__(self) -> bool:
        # As `.is_available` should be paired with `.guild`, we don't need to check both.
        return any(
            (
                self.channels,
                self.emojis,
                self.guild,
                self.invites,
                self.members,
                self.presences,
                self.roles,
                self.voice_states,
            )
        )


@attr.s(slots=True, repr=False, hash=False, init=True, weakref_slot=False)
class BaseData(abc.ABC, typing.Generic[ValueT]):
    """A data class used for in-memory storage of entities in a more primitive form.

    !!! note
        This base implementation assumes that all the fields it'll handle will
        be immutable and to handle mutable fields you'll have to override
        build_entity and build_from_entity to explicitly copy them.
    """

    __slots__: typing.Sequence[str] = ()

    @abc.abstractmethod
    def build_entity(self, **kwargs: typing.Any) -> ValueT:
        """Build an entity object from this data object.

        Parameters
        ----------
        target
            The class of the entity object to build.
        kwargs
            Extra fields to pass on to the entity's initialiser. These will take
            priority over fields on the builder.

        Returns
        -------
        The initialised entity object.
        """

    @classmethod
    @abc.abstractmethod
    def build_from_entity(cls: typing.Type[DataT], entity: ValueT) -> DataT:
        """Build a data object from an initialised entity.

        Parameters
        ----------
        entity
            The entity object to build a data class from.

        Returns
        -------
        The built data class.
        """

    def replace(self: DataT, **kwargs: typing.Any) -> DataT:
        data = copy.copy(self)

        for attribute, value in kwargs.items():
            setattr(data, attribute, value)

        return data


@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, repr=False, hash=False, weakref_slot=False)
class InviteData(BaseData[invites.InviteWithMetadata]):
    """A data model for storing invite data in an in-memory cache."""

    code: str = attr.ib()
    guild_id: typing.Optional[snowflakes.Snowflake] = attr.ib()
    channel_id: snowflakes.Snowflake = attr.ib()
    inviter_id: typing.Optional[snowflakes.Snowflake] = attr.ib()
    target_user_id: typing.Optional[snowflakes.Snowflake] = attr.ib()
    target_user_type: typing.Union[invites.TargetUserType, int, None] = attr.ib()
    uses: int = attr.ib()
    max_uses: typing.Optional[int] = attr.ib()
    max_age: typing.Optional[datetime.timedelta] = attr.ib()
    is_temporary: bool = attr.ib()
    created_at: datetime.datetime = attr.ib()

    def build_entity(self, **kwargs: typing.Any) -> invites.InviteWithMetadata:
        return invites.InviteWithMetadata(
            code=self.code,
            guild_id=self.guild_id,
            channel_id=self.channel_id,
            target_user_type=self.target_user_type,
            uses=self.uses,
            max_uses=self.max_uses,
            max_age=self.max_age,
            is_temporary=self.is_temporary,
            created_at=self.created_at,
            approximate_member_count=None,
            approximate_active_member_count=None,
            channel=None,
            guild=None,
            app=kwargs["app"],
            inviter=kwargs["inviter"],
            target_user=kwargs["target_user"],
        )

    @classmethod
    def build_from_entity(cls: typing.Type[InviteData], entity: invites.InviteWithMetadata) -> InviteData:
        return cls(
            code=entity.code,
            guild_id=entity.guild_id,
            channel_id=entity.channel_id,
            target_user_type=entity.target_user_type,
            uses=entity.uses,
            max_uses=entity.max_uses,
            max_age=entity.max_age,
            is_temporary=entity.is_temporary,
            created_at=entity.created_at,
            inviter_id=entity.inviter.id if entity.inviter is not None else None,
            target_user_id=entity.target_user.id if entity.target_user is not None else None,
        )


@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, repr=False, hash=False, weakref_slot=False)
class MemberData(BaseData[guilds.Member]):
    """A data model for storing member data in an in-memory cache."""

    id: snowflakes.Snowflake = attr.ib()
    guild_id: snowflakes.Snowflake = attr.ib()
    nickname: undefined.UndefinedNoneOr[str] = attr.ib()
    role_ids: typing.Tuple[snowflakes.Snowflake, ...] = attr.ib()
    joined_at: datetime.datetime = attr.ib()
    premium_since: typing.Optional[datetime.datetime] = attr.ib()
    is_deaf: undefined.UndefinedOr[bool] = attr.ib()
    is_mute: undefined.UndefinedOr[bool] = attr.ib()
    # meta-attribute
    has_been_deleted: bool = attr.ib(default=False)
    ref_count: int = attr.ib(default=0)

    @classmethod
    def build_from_entity(cls: typing.Type[MemberData], entity: guilds.Member) -> MemberData:
        return cls(
            guild_id=entity.guild_id,
            nickname=entity.nickname,
            joined_at=entity.joined_at,
            premium_since=entity.premium_since,
            is_deaf=entity.is_deaf,
            is_mute=entity.is_mute,
            id=entity.user.id,
            # role_ids is a special case as it may be mutable so we want to ensure it's immutable when cached.
            role_ids=tuple(entity.role_ids),
        )

    def build_entity(self, **kwargs: typing.Any) -> guilds.Member:
        return guilds.Member(
            guild_id=self.guild_id,
            nickname=self.nickname,
            role_ids=self.role_ids,
            joined_at=self.joined_at,
            premium_since=self.premium_since,
            is_deaf=self.is_deaf,
            is_mute=self.is_mute,
            user=kwargs["user"],
        )


@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, repr=False, hash=False, weakref_slot=False)
class KnownCustomEmojiData(BaseData[emojis.KnownCustomEmoji]):
    """A data model for storing known custom emoji data in an in-memory cache."""

    id: snowflakes.Snowflake = attr.ib()
    name: typing.Optional[str] = attr.ib()
    is_animated: bool = attr.ib()
    guild_id: snowflakes.Snowflake = attr.ib()
    role_ids: typing.Tuple[snowflakes.Snowflake, ...] = attr.ib()
    user_id: typing.Optional[snowflakes.Snowflake] = attr.ib()
    is_colons_required: bool = attr.ib()
    is_managed: bool = attr.ib()
    is_available: bool = attr.ib()
    # meta-attributes
    has_been_deleted: bool = attr.ib(default=False)  # We need test coverage for this systm
    ref_count: int = attr.ib(default=0)

    @classmethod
    def build_from_entity(
        cls: typing.Type[KnownCustomEmojiData], entity: emojis.KnownCustomEmoji
    ) -> KnownCustomEmojiData:
        return cls(
            id=entity.id,
            name=entity.name,
            is_animated=entity.is_animated,
            guild_id=entity.guild_id,
            is_colons_required=entity.is_colons_required,
            is_managed=entity.is_managed,
            is_available=entity.is_available,
            user_id=entity.user.id if entity.user else None,
            # role_ids is a special case as it may be a mutable sequence so we want to ensure it's immutable when cached.
            role_ids=tuple(entity.role_ids),
        )

    def build_entity(self, **kwargs: typing.Any) -> emojis.KnownCustomEmoji:
        return emojis.KnownCustomEmoji(
            id=self.id,
            name=self.name,
            is_animated=self.is_animated,
            guild_id=self.guild_id,
            role_ids=self.role_ids,
            is_colons_required=self.is_colons_required,
            is_managed=self.is_managed,
            is_available=self.is_available,
            app=kwargs["app"],
            user=kwargs["user"],
        )


@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, repr=False, hash=False, weakref_slot=False)
class RichActivityData(BaseData[presences.RichActivity]):
    """A data model for storing rich activity data in an in-memory cache."""

    name: str = attr.ib()
    url: typing.Optional[str] = attr.ib()
    type: typing.Union[presences.ActivityType, int] = attr.ib()
    created_at: datetime.datetime = attr.ib()
    timestamps: typing.Optional[presences.ActivityTimestamps] = attr.ib()
    application_id: typing.Optional[snowflakes.Snowflake] = attr.ib()
    details: typing.Optional[str] = attr.ib()
    state: typing.Optional[str] = attr.ib()
    emoji_id_or_name: typing.Union[snowflakes.Snowflake, str, None] = attr.ib()
    party: typing.Optional[presences.ActivityParty] = attr.ib()
    assets: typing.Optional[presences.ActivityAssets] = attr.ib()
    secrets: typing.Optional[presences.ActivitySecret] = attr.ib()
    is_instance: typing.Optional[bool] = attr.ib()
    flags: typing.Optional[presences.ActivityFlag] = attr.ib()

    @classmethod
    def build_from_entity(cls: typing.Type[RichActivityData], entity: presences.RichActivity) -> RichActivityData:
        emoji_id_or_name: typing.Union[snowflakes.Snowflake, str, None]
        if entity.emoji is None:
            emoji_id_or_name = None
        elif isinstance(entity.emoji, emojis.CustomEmoji):
            emoji_id_or_name = entity.emoji.id
        else:
            emoji_id_or_name = entity.emoji.name

        timestamps = copy.copy(entity.timestamps) if entity.timestamps is not None else None
        party = copy.copy(entity.party) if entity.party is not None else None
        assets = copy.copy(entity.assets) if entity.assets is not None else None
        secrets = copy.copy(entity.secrets) if entity.secrets is not None else None
        return cls(
            name=entity.name,
            url=entity.url,
            type=entity.type,
            created_at=entity.created_at,
            application_id=entity.application_id,
            details=entity.details,
            state=entity.state,
            is_instance=entity.is_instance,
            flags=entity.flags,
            emoji_id_or_name=emoji_id_or_name,
            timestamps=timestamps,
            party=party,
            assets=assets,
            secrets=secrets,
        )

    def build_entity(self, **kwargs: typing.Any) -> presences.RichActivity:
        return presences.RichActivity(
            name=self.name,
            url=self.url,
            type=self.type,
            created_at=self.created_at,
            application_id=self.application_id,
            details=self.details,
            is_instance=self.is_instance,
            flags=self.flags,
            state=self.state,
            timestamps=copy.copy(self.timestamps) if self.timestamps is not None else None,
            party=copy.copy(self.party) if self.party is not None else None,
            assets=copy.copy(self.assets) if self.assets is not None else None,
            secrets=copy.copy(self.secrets) if self.secrets is not None else None,
            emoji=kwargs["emoji"],
        )


@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, repr=False, hash=False, weakref_slot=False)
class MemberPresenceData(BaseData[presences.MemberPresence]):
    """A data model for storing presence data in an in-memory cache."""

    user_id: snowflakes.Snowflake = attr.ib()
    guild_id: snowflakes.Snowflake = attr.ib()
    visible_status: typing.Union[presences.Status, str] = attr.ib()
    activities: typing.Tuple[RichActivityData, ...] = attr.ib()
    client_status: presences.ClientStatus = attr.ib()

    @classmethod
    def build_from_entity(
        cls: typing.Type[MemberPresenceData], entity: presences.MemberPresence, **kwargs: typing.Any
    ) -> MemberPresenceData:
        # role_ids and activities are special cases as may be mutable sequences, therefor we ant to ensure they're
        # stored in immutable sequences (tuples). Plus activities need to be converted to Data objects.
        return cls(
            user_id=entity.user_id,
            guild_id=entity.guild_id,
            visible_status=entity.visible_status,
            activities=tuple(RichActivityData.build_from_entity(activity) for activity in entity.activities),
            client_status=copy.copy(entity.client_status),
        )

    def build_entity(
        self,
        **kwargs: typing.Any,
    ) -> presences.MemberPresence:
        presence_kwargs = kwargs["presence_kwargs"]
        activities = [activity.build_entity(**kwargs_) for activity, kwargs_ in zip(self.activities, presence_kwargs)]
        return presences.MemberPresence(
            user_id=self.user_id,
            guild_id=self.guild_id,
            visible_status=self.visible_status,
            app=kwargs["app"],
            activities=activities,
            client_status=copy.copy(self.client_status),
        )


@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, repr=False, hash=False, weakref_slot=False)
class VoiceStateData(BaseData[voices.VoiceState]):
    """A data model for storing voice state data in an in-memory cache."""

    channel_id: typing.Optional[snowflakes.Snowflake] = attr.ib()
    guild_id: snowflakes.Snowflake = attr.ib()
    is_guild_deafened: bool = attr.ib()
    is_guild_muted: bool = attr.ib()
    is_self_deafened: bool = attr.ib()
    is_self_muted: bool = attr.ib()
    is_streaming: bool = attr.ib()
    is_suppressed: bool = attr.ib()
    is_video_enabled: bool = attr.ib()
    user_id: snowflakes.Snowflake = attr.ib()
    session_id: str = attr.ib()

    def build_entity(self, **kwargs: typing.Any) -> voices.VoiceState:
        return voices.VoiceState(
            channel_id=self.channel_id,
            guild_id=self.guild_id,
            is_guild_deafened=self.is_guild_deafened,
            is_guild_muted=self.is_guild_muted,
            is_self_deafened=self.is_self_deafened,
            is_self_muted=self.is_self_muted,
            is_streaming=self.is_streaming,
            is_suppressed=self.is_suppressed,
            is_video_enabled=self.is_video_enabled,
            user_id=self.user_id,
            session_id=self.session_id,
            app=kwargs["app"],
            member=kwargs["member"],
        )

    @classmethod
    def build_from_entity(cls: typing.Type[VoiceStateData], entity: voices.VoiceState) -> VoiceStateData:
        return cls(
            channel_id=entity.channel_id,
            guild_id=entity.guild_id,
            is_self_deafened=entity.is_self_deafened,
            is_self_muted=entity.is_self_muted,
            is_guild_deafened=entity.is_guild_deafened,
            is_guild_muted=entity.is_guild_muted,
            is_streaming=entity.is_streaming,
            is_suppressed=entity.is_suppressed,
            is_video_enabled=entity.is_video_enabled,
            user_id=entity.user_id,
            session_id=entity.session_id,
        )


@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, repr=False, hash=False, weakref_slot=False)
class GenericRefWrapper(typing.Generic[ValueT]):
    """An object used for wrapping entities in an in-memory cache.

    This is intended to enable reference counting for entities that are only kept
    alive by reference (e.g. the unknown emoji objects attached to presence
    activities and user objects) without the use of a "Data" object which lowers
    the time spent building these entities for the objects that reference them.
    """

    object: ValueT = attr.ib()
    ref_count: int = attr.ib(default=0)


def copy_guild_channel(channel: channels.GuildChannel) -> channels.GuildChannel:
    """Logic for handling the copying of guild channel objects.

    This exists account for the permission overwrite objects attached to guild
    channel objects which need to be copied themselves.
    """
    channel = copy.copy(channel)
    channel.permission_overwrites = {
        sf: copy.copy(overwrite) for sf, overwrite in collections.copy_mapping(channel.permission_overwrites).items()
    }
    return channel


class GuildChannelCacheMappingView(StatefulCacheMappingView[snowflakes.Snowflake, channels.GuildChannel]):
    """A special case of the mapping view implements copy logic that targets guild channels specifically."""

    __slots__: typing.Sequence[str] = ()

    @classmethod
    def _copy(cls, value: channels.GuildChannel) -> channels.GuildChannel:
        return copy_guild_channel(value)


class Cache3DMappingView(StatefulCacheMappingView[snowflakes.Snowflake, cache.CacheView[KeyT, ValueT]]):
    """A special case of the Mapping View which avoids copying the already immutable views contained within it."""

    __slots__: typing.Sequence[str] = ()

    @classmethod
    def _copy(cls, value: cache.CacheView[KeyT, ValueT]) -> cache.CacheView[KeyT, ValueT]:
        return value
