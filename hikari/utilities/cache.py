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

__all__: typing.Final[typing.List[str]] = [
    "IDTable",
    "StatefulCacheMappingView",
    "EmptyCacheView",
    "GuildRecord",
    "BaseData",
    "PrivateTextChannelData",
    "InviteData",
    "MemberData",
    "KnownCustomEmojiData",
    "RichActivityData",
    "MemberPresenceData",
    "VoiceStateData",
    "GenericRefWrapper",
    "PrivateTextChannelMRUMutableMapping",
    "copy_guild_channel",
    "GuildChannelCacheMappingView",
    "Cache3DMappingView",
    "DataT",
    "KeyT",
    "ValueT",
]

import abc
import array
import bisect
import copy
import datetime
import reprlib
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
from hikari.utilities import attr_extensions
from hikari.utilities import date
from hikari.utilities import mapping

DataT = typing.TypeVar("DataT", bound="BaseData[typing.Any]")
"""Type-hint for "data" objects used for storing and building entities."""
KeyT = typing.TypeVar("KeyT", bound=typing.Hashable)
"""Type-hint for mapping keys."""
ValueT = typing.TypeVar("ValueT")
"""Type-hint for mapping values."""


class IDTable(typing.MutableSet[snowflakes.Snowflake]):
    """Compact 64-bit integer bisected-array-set of snowflakes."""

    __slots__: typing.Sequence[str] = ("_ids",)

    def __init__(self) -> None:
        self._ids = array.array("Q")

    def add(self, sf: snowflakes.Snowflake) -> None:
        """Add a snowflake to this set."""
        if not self._ids:
            self._ids.append(sf)
        else:
            index = bisect.bisect_left(self._ids, sf)
            if len(self._ids) == index or self._ids[index] != sf:
                self._ids.insert(index, sf)

    def add_all(self, sfs: typing.Iterable[snowflakes.Snowflake]) -> None:
        """Add a collection of snowflakes to this set."""
        for sf in sfs:
            self.add(sf)

    def discard(self, sf: snowflakes.Snowflake) -> None:
        """Remove a snowflake from this set if it's present."""
        index = self._index_of(sf)
        if index != -1:
            del self._ids[index]

    def _index_of(self, sf: int) -> int:
        index = bisect.bisect_left(self._ids, sf)
        return index if index < len(self._ids) or self._ids[index] == sf else -1

    def __contains__(self, value: typing.Any) -> bool:
        if not isinstance(value, int):
            return False

        return self._index_of(value) != -1

    def __len__(self) -> int:
        return len(self._ids)

    def __iter__(self) -> typing.Iterator[snowflakes.Snowflake]:
        return map(snowflakes.Snowflake, self._ids)

    def __repr__(self) -> str:
        return "SnowflakeTable" + reprlib.repr(self._ids)[5:]


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
    guild: typing.Optional[guilds.GatewayGuild] = attr.ib(default=None)
    channels: typing.Optional[typing.MutableSet[snowflakes.Snowflake]] = attr.ib(default=None)
    emojis: typing.Optional[typing.MutableSet[snowflakes.Snowflake]] = attr.ib(default=None)
    invites: typing.Optional[typing.MutableSequence[str]] = attr.ib(default=None)
    members: typing.Optional[mapping.MappedCollection[snowflakes.Snowflake, MemberData]] = attr.ib(default=None)
    presences: typing.Optional[mapping.MappedCollection[snowflakes.Snowflake, MemberPresenceData]] = attr.ib(
        default=None
    )
    roles: typing.Optional[typing.MutableSet[snowflakes.Snowflake]] = attr.ib(default=None)
    voice_states: typing.Optional[mapping.MappedCollection[snowflakes.Snowflake, VoiceStateData]] = attr.ib(
        default=None
    )

    def __bool__(self) -> bool:  # TODO: should "is_available" keep this alive?
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

    @classmethod
    @abc.abstractmethod
    def get_fields(cls) -> typing.Collection[str]:
        """Get the fields that should be automatically handled on the target entity.

        !!! note
            These fields should match up with both the target entity and the
            data class itself.

        Returns
        -------
        typing.Collection[builtins.str]
            A collection of the names of fields to handle.
        """

    def build_entity(self, target: typing.Type[ValueT], **kwargs: typing.Any) -> ValueT:
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
        for field in self.get_fields():
            if field not in kwargs:
                kwargs[field] = getattr(self, field)

        return target(**kwargs)  # type: ignore[call-arg]

    @classmethod
    def build_from_entity(cls: typing.Type[DataT], entity: ValueT, **kwargs: typing.Any) -> DataT:
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

    def replace(self: DataT, **kwargs: typing.Any) -> DataT:
        data = copy.copy(self)

        for attribute, value in kwargs.items():
            setattr(data, attribute, value)

        return data


@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, repr=False, hash=False, weakref_slot=False)
class PrivateTextChannelData(BaseData[channels.PrivateTextChannel]):
    """A data model for storing private text channel data in an in-memory cache.

    !!! note
        This doesn't cover private group text channels as we won't ever receive
        those over the gateway.
    """

    id: snowflakes.Snowflake = attr.ib()
    name: typing.Optional[str] = attr.ib()
    last_message_id: typing.Optional[snowflakes.Snowflake] = attr.ib()
    recipient_id: snowflakes.Snowflake = attr.ib()

    @classmethod
    def get_fields(cls) -> typing.Collection[str]:
        return "id", "name", "last_message_id"

    def build_entity(
        self, target: typing.Type[channels.PrivateTextChannel], **kwargs: typing.Any
    ) -> channels.PrivateTextChannel:
        return super().build_entity(target, type=channels.ChannelType.PRIVATE_TEXT, **kwargs)

    @classmethod
    def build_from_entity(
        cls: typing.Type[PrivateTextChannelData], entity: channels.PrivateTextChannel, **kwargs: typing.Any
    ) -> PrivateTextChannelData:
        return super().build_from_entity(entity, **kwargs, recipient_id=entity.recipient.id)


@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, repr=False, hash=False, weakref_slot=False)
class InviteData(BaseData[invites.InviteWithMetadata]):
    """A data model for storing invite data in an in-memory cache."""

    code: str = attr.ib()
    guild_id: typing.Optional[snowflakes.Snowflake] = attr.ib()
    channel_id: snowflakes.Snowflake = attr.ib()
    inviter_id: typing.Optional[snowflakes.Snowflake] = attr.ib()
    target_user_id: typing.Optional[snowflakes.Snowflake] = attr.ib()
    target_user_type: typing.Optional[invites.TargetUserType] = attr.ib()
    uses: int = attr.ib()
    max_uses: typing.Optional[int] = attr.ib()
    max_age: typing.Optional[datetime.timedelta] = attr.ib()
    is_temporary: bool = attr.ib()
    created_at: datetime.datetime = attr.ib()

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

    def build_entity(
        self, target: typing.Type[invites.InviteWithMetadata], **kwargs: typing.Any
    ) -> invites.InviteWithMetadata:
        return super().build_entity(
            target,
            approximate_member_count=None,
            approximate_active_member_count=None,
            channel=None,
            guild=None,
            **kwargs,
        )

    @classmethod
    def build_from_entity(
        cls: typing.Type[InviteData], entity: invites.InviteWithMetadata, **kwargs: typing.Any
    ) -> InviteData:
        return super().build_from_entity(
            entity,
            **kwargs,
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
    joined_at: undefined.UndefinedOr[datetime.datetime] = attr.ib()
    premium_since: undefined.UndefinedNoneOr[datetime.datetime] = attr.ib()
    is_deaf: undefined.UndefinedOr[bool] = attr.ib()
    is_mute: undefined.UndefinedOr[bool] = attr.ib()
    # meta-attribute
    has_been_deleted: bool = attr.ib(default=False)
    ref_count: int = attr.ib(default=0)

    @classmethod
    def get_fields(cls) -> typing.Collection[str]:
        return "guild_id", "nickname", "role_ids", "joined_at", "premium_since", "is_deaf", "is_mute"

    @classmethod
    def build_from_entity(cls: typing.Type[MemberData], entity: guilds.Member, **kwargs: typing.Any) -> MemberData:
        # role_ids is a special case as it may be a mutable sequence so we want to ensure it's immutable when cached.
        return super().build_from_entity(entity, **kwargs, id=entity.user.id, role_ids=tuple(entity.role_ids))


@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, repr=False, hash=False, weakref_slot=False)
class KnownCustomEmojiData(BaseData[emojis.KnownCustomEmoji]):
    """A data model for storing known custom emoji data in an in-memory cache."""

    id: snowflakes.Snowflake = attr.ib()
    name: typing.Optional[str] = attr.ib()
    is_animated: typing.Optional[bool] = attr.ib()
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
    def get_fields(cls) -> typing.Collection[str]:
        return "id", "name", "is_animated", "guild_id", "role_ids", "is_colons_required", "is_managed", "is_available"

    @classmethod
    def build_from_entity(
        cls: typing.Type[KnownCustomEmojiData], entity: emojis.KnownCustomEmoji, **kwargs: typing.Any
    ) -> KnownCustomEmojiData:
        # role_ids is a special case as it may be a mutable sequence so we want to ensure it's immutable when cached.
        return super().build_from_entity(
            entity, **kwargs, user_id=entity.user.id if entity.user else None, role_ids=tuple(entity.role_ids)
        )


@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, repr=False, hash=False, weakref_slot=False)
class RichActivityData(BaseData[presences.RichActivity]):
    """A data model for storing rich activity data in an in-memory cache."""

    name: str = attr.ib()
    url: str = attr.ib()
    type: presences.ActivityType = attr.ib()
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
    def get_fields(cls) -> typing.Collection[str]:
        return "name", "url", "type", "created_at", "application_id", "details", "state", "is_instance", "flags"

    @classmethod
    def build_from_entity(
        cls: typing.Type[RichActivityData], entity: presences.RichActivity, **kwargs: typing.Any
    ) -> RichActivityData:
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
        return super().build_from_entity(
            entity,
            emoji_id_or_name=emoji_id_or_name,
            timestamps=timestamps,
            party=party,
            assets=assets,
            secrets=secrets,
        )

    def build_entity(self, target: typing.Type[presences.RichActivity], **kwargs: typing.Any) -> presences.RichActivity:
        return super().build_entity(
            target,
            timestamps=copy.copy(self.timestamps) if self.timestamps is not None else None,
            party=copy.copy(self.party) if self.party is not None else None,
            assets=copy.copy(self.assets) if self.assets is not None else None,
            secrets=copy.copy(self.secrets) if self.secrets is not None else None,
            **kwargs,
        )


@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, repr=False, hash=False, weakref_slot=False)
class MemberPresenceData(BaseData[presences.MemberPresence]):
    """A data model for storing presence data in an in-memory cache."""

    user_id: snowflakes.Snowflake = attr.ib()
    role_ids: typing.Optional[typing.Tuple[snowflakes.Snowflake, ...]] = attr.ib()
    guild_id: typing.Optional[snowflakes.Snowflake] = attr.ib()
    visible_status: presences.Status = attr.ib()
    activities: typing.Tuple[RichActivityData, ...] = attr.ib()
    client_status: presences.ClientStatus = attr.ib()
    premium_since: typing.Optional[datetime.datetime] = attr.ib()
    nickname: typing.Optional[str] = attr.ib()

    @classmethod
    def get_fields(cls) -> typing.Collection[str]:
        return "user_id", "role_ids", "guild_id", "visible_status", "premium_since", "nickname"

    @classmethod
    def build_from_entity(
        cls: typing.Type[MemberPresenceData], entity: presences.MemberPresence, **kwargs: typing.Any
    ) -> MemberPresenceData:
        # role_ids and activities are special cases as may be mutable sequences, therefor we ant to ensure they're
        # stored in immutable sequences (tuples). Plus activities need to be converted to Data objects.
        return super().build_from_entity(
            entity,
            role_ids=tuple(entity.role_ids) if entity.role_ids is not None else None,
            activities=tuple(RichActivityData.build_from_entity(activity) for activity in entity.activities),
            client_status=copy.copy(entity.client_status),
        )

    def build_entity(
        self,
        target: typing.Type[presences.MemberPresence],
        **kwargs: typing.Any,
    ) -> presences.MemberPresence:
        presence_kwargs = kwargs.pop("presence_kwargs")
        activities = [
            activity.build_entity(presences.RichActivity, **kwargs_)
            for activity, kwargs_ in zip(self.activities, presence_kwargs)
        ]
        return super().build_entity(
            target, activities=activities, client_status=copy.copy(self.client_status), **kwargs
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


class PrivateTextChannelMRUMutableMapping(mapping.MappedCollection[snowflakes.Snowflake, PrivateTextChannelData]):
    """A specialised Most-recently-used limited mapping for private text channels.

    This allows us to stop the private message cached from growing
    un-controllably by removing old private channels rather than waiting for
    delete events that'll never come or querying every guild the bot is in
    (which sounds rather bad as far as scaling goes).

    Parameters
    ----------
    expiry : datetime.timedelta
        The timedelta of how long this should keep private channels for before
        deleting them.

    Raises
    ------
    ValueError
        If `expiry` is a negative timedelta.
    """

    __slots__: typing.Sequence[str] = ("_channels", "_expiry")

    def __init__(
        self,
        source: typing.Optional[typing.Dict[snowflakes.Snowflake, PrivateTextChannelData]] = None,
        /,
        *,
        expiry: datetime.timedelta,
    ) -> None:
        if expiry <= datetime.timedelta():
            raise ValueError("expiry time must be greater than 0 microseconds.")

        self._channels = source or {}
        self._expiry = expiry

    def copy(self) -> PrivateTextChannelMRUMutableMapping:
        return PrivateTextChannelMRUMutableMapping(self._channels.copy(), expiry=self._expiry)

    def freeze(self) -> typing.Dict[snowflakes.Snowflake, PrivateTextChannelData]:
        return self._channels.copy()

    def _garbage_collect(self) -> None:
        current_time = date.utc_datetime()
        for channel_id, channel in self._channels.copy().items():
            if channel.last_message_id and current_time - channel.last_message_id.created_at < self._expiry:
                break

            del self._channels[channel_id]

    def __delitem__(self, sf: snowflakes.Snowflake) -> None:
        del self._channels[sf]
        self._garbage_collect()

    def __getitem__(self, sf: snowflakes.Snowflake) -> PrivateTextChannelData:
        return self._channels[sf]

    def __iter__(self) -> typing.Iterator[snowflakes.Snowflake]:
        return iter(self._channels)

    def __len__(self) -> int:
        return len(self._channels)

    def __setitem__(self, sf: snowflakes.Snowflake, value: PrivateTextChannelData) -> None:
        self._garbage_collect()
        #  Seeing as we rely on insertion order in _garbage_collect, we have to make sure that each item is added to
        #  the end of the dict.
        if value.last_message_id is not None and sf in self:
            del self[sf]

        self._channels[sf] = value


def copy_guild_channel(channel: channels.GuildChannel) -> channels.GuildChannel:
    """Logic for handling the copying of guild channel objects.

    This exists account for the permission overwrite objects attached to guild
    channel objects which need to be copied themselves.
    """
    channel = copy.copy(channel)
    channel.permission_overwrites = {
        sf: copy.copy(overwrite) for sf, overwrite in mapping.copy_mapping(channel.permission_overwrites).items()
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
