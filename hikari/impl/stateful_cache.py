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
"""Basic implementation of a cache for general bots and gateway apps."""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = ["StatefulCacheImpl"]

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

_DataT = typing.TypeVar("_DataT", bound="_BaseData[typing.Any]")
_KeyT = typing.TypeVar("_KeyT", bound=typing.Hashable)
_LOGGER: typing.Final[logging.Logger] = logging.getLogger("hikari.cache")
_ValueT = typing.TypeVar("_ValueT")


class _IDTable(typing.MutableSet[snowflake.Snowflake]):
    """Compact 64-bit integer bisected-array-set of snowflakes."""

    __slots__: typing.Sequence[str] = ("_ids",)

    def __init__(self) -> None:
        self._ids = array.array("Q")

    def add(self, sf: snowflake.Snowflake) -> None:
        if not self._ids:
            self._ids.append(sf)
        else:
            index = bisect.bisect_left(self._ids, sf)
            if len(self._ids) == index or self._ids[index] != sf:
                self._ids.insert(index, sf)

    def add_all(self, sfs: typing.Iterable[snowflake.Snowflake]) -> None:
        for sf in sfs:
            self.add(sf)

    def discard(self, sf: snowflake.Snowflake) -> None:
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

    @classmethod
    def _copy(cls, value: _ValueT) -> _ValueT:
        return copy.copy(value)

    def __contains__(self, key: typing.Any) -> bool:
        return key in self._data

    def __getitem__(self, key: _KeyT) -> _ValueT:
        entry = self._data[key]

        if self._builder is not None:
            entry = self._builder(entry)  # type: ignore[arg-type]
        else:
            entry = self._copy(entry)  # type: ignore[arg-type]

        return entry

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


@attr.s(slots=True, repr=False, hash=False, weakref_slot=False)
class _GuildRecord:
    is_available: typing.Optional[bool] = attr.ib(default=None)
    guild: typing.Optional[guilds.GatewayGuild] = attr.ib(default=None)
    # TODO: some of these will be iterated across more than they will searched by a specific ID...
    # ... identify these cases and convert to lists.
    channels: typing.Optional[typing.MutableSet[snowflake.Snowflake]] = attr.ib(default=None)
    emojis: typing.Optional[typing.MutableSet[snowflake.Snowflake]] = attr.ib(default=None)
    invites: typing.Optional[typing.MutableSequence[str]] = attr.ib(default=None)
    members: typing.Optional[typing.MutableMapping[snowflake.Snowflake, _MemberData]] = attr.ib(default=None)
    presences: typing.Optional[typing.MutableMapping[snowflake.Snowflake, _MemberPresenceData]] = attr.ib(default=None)
    roles: typing.Optional[typing.MutableSet[snowflake.Snowflake]] = attr.ib(default=None)
    voice_states: typing.Optional[typing.MutableMapping[snowflake.Snowflake, _VoiceStateData]] = attr.ib(default=None)

    _FIELDS_TO_CHECK: typing.Final[typing.Collection[str]] = (
        "channels",
        "emojis",
        "guild",
        "invites",
        "members",
        "presences",
        "roles",
        "voice_states",
    )

    def __bool__(self) -> bool:
        return any(getattr(self, attribute) for attribute in self._FIELDS_TO_CHECK)


@attr.s(slots=True, repr=False, hash=False, init=True, weakref_slot=False)
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
        """Get the fields that should be automatically handled on the target entity.

        !!! note
            These fields should match up with both the target entity and the
            data class itself.

        Returns
        -------
        typing.Collection[builtins.str]
            A collection of the names of fields to handle.
        """

    def build_entity(self, target: typing.Type[_ValueT], **kwargs: typing.Any) -> _ValueT:
        """Build an entity object from this data object.

        Parameters
        ----------
        target
            The class of the entity object to add attributes to.
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


@attr.s(kw_only=True, slots=True, repr=False, hash=False, weakref_slot=False)
class _PrivateTextChannelData(_BaseData[channels.PrivateTextChannel]):
    id: snowflake.Snowflake = attr.ib()
    name: typing.Optional[str] = attr.ib()
    last_message_id: typing.Optional[snowflake.Snowflake] = attr.ib()
    recipient_id: snowflake.Snowflake = attr.ib()

    @classmethod
    def get_fields(cls) -> typing.Collection[str]:
        return "id", "name", "last_message_id"

    def build_entity(
        self, target: typing.Type[channels.PrivateTextChannel], **kwargs: typing.Any
    ) -> channels.PrivateTextChannel:
        return super().build_entity(target, type=channels.ChannelType.PRIVATE_TEXT, **kwargs)

    @classmethod
    def build_from_entity(
        cls: typing.Type[_PrivateTextChannelData], entity: channels.PrivateTextChannel, **kwargs: typing.Any
    ) -> _PrivateTextChannelData:
        return super().build_from_entity(entity, **kwargs, recipient_id=entity.recipient.id)


@attr.s(kw_only=True, slots=True, repr=False, hash=False, weakref_slot=False)
class _InviteData(_BaseData[invites.InviteWithMetadata]):
    code: str = attr.ib()
    guild_id: typing.Optional[snowflake.Snowflake] = attr.ib()  # TODO: This should not ever be none here
    channel_id: snowflake.Snowflake = attr.ib()
    inviter_id: typing.Optional[
        snowflake.Snowflake
    ] = attr.ib()  # TODO: do we get these events if we don't have manage invite perm? ( we don't )
    target_user_id: typing.Optional[snowflake.Snowflake] = attr.ib()
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
            target, approximate_member_count=None, approximate_presence_count=None, channel=None, guild=None, **kwargs,
        )

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


@attr.s(kw_only=True, slots=True, repr=False, hash=False, weakref_slot=False)
class _MemberData(_BaseData[guilds.Member]):
    id: snowflake.Snowflake = attr.ib()
    guild_id: snowflake.Snowflake = attr.ib()
    nickname: undefined.UndefinedNoneOr[str] = attr.ib()
    role_ids: typing.Tuple[snowflake.Snowflake, ...] = attr.ib()
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
    def build_from_entity(cls: typing.Type[_MemberData], entity: guilds.Member, **kwargs: typing.Any) -> _MemberData:
        return super().build_from_entity(entity, **kwargs, id=entity.user.id, role_ids=tuple(entity.role_ids))


@attr.s(kw_only=True, slots=True, repr=False, hash=False, weakref_slot=False)
class _KnownCustomEmojiData(_BaseData[emojis.KnownCustomEmoji]):
    id: snowflake.Snowflake = attr.ib()
    name: typing.Optional[str] = attr.ib()  # TODO: should not ever be None here
    is_animated: typing.Optional[bool] = attr.ib()  # TODO: should not ever be None here
    guild_id: snowflake.Snowflake = attr.ib()
    role_ids: typing.Tuple[snowflake.Snowflake, ...] = attr.ib()
    user_id: typing.Optional[snowflake.Snowflake] = attr.ib()
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
        cls: typing.Type[_KnownCustomEmojiData], entity: emojis.KnownCustomEmoji, **kwargs: typing.Any
    ) -> _KnownCustomEmojiData:
        return super().build_from_entity(
            entity, **kwargs, user_id=entity.user.id if entity.user else None, role_ids=tuple(entity.role_ids)
        )


@attr.s(kw_only=True, slots=True, repr=False, hash=False, weakref_slot=False)
class _RichActivityData(_BaseData[presences.RichActivity]):
    name: str = attr.ib()
    url: str = attr.ib()
    type: presences.ActivityType = attr.ib()
    created_at: datetime.datetime = attr.ib()
    timestamps: presences.ActivityTimestamps = attr.ib()
    application_id: typing.Optional[snowflake.Snowflake] = attr.ib()
    details: typing.Optional[str] = attr.ib()
    state: typing.Optional[str] = attr.ib()
    emoji_id_or_name: typing.Union[snowflake.Snowflake, str, None] = attr.ib()
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
        cls: typing.Type[_RichActivityData], entity: presences.RichActivity, **kwargs: typing.Any
    ) -> _RichActivityData:
        emoji_id_or_name: typing.Union[snowflake.Snowflake, str, None]
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
            timestamps=copy.copy(self.timestamps),
            party=copy.copy(self.party),
            assets=copy.copy(self.assets),
            secrets=copy.copy(self.secrets),
            **kwargs,
        )


@attr.s(kw_only=True, slots=True, repr=False, hash=False, weakref_slot=False)
class _MemberPresenceData(_BaseData[presences.MemberPresence]):
    user_id: snowflake.Snowflake = attr.ib()
    role_ids: typing.Optional[typing.Tuple[snowflake.Snowflake, ...]] = attr.ib()
    guild_id: typing.Optional[snowflake.Snowflake] = attr.ib()
    visible_status: presences.Status = attr.ib()
    activities: typing.Tuple[_RichActivityData, ...] = attr.ib()
    client_status: presences.ClientStatus = attr.ib()
    premium_since: typing.Optional[datetime.datetime] = attr.ib()
    nickname: typing.Optional[str] = attr.ib()

    @classmethod
    def get_fields(cls) -> typing.Collection[str]:
        return "user_id", "role_ids", "guild_id", "visible_status", "premium_since", "nickname"

    @classmethod
    def build_from_entity(
        cls: typing.Type[_MemberPresenceData], entity: presences.MemberPresence, **kwargs: typing.Any
    ) -> _MemberPresenceData:
        return super().build_from_entity(
            entity,
            role_ids=tuple(entity.role_ids) if entity.role_ids is not None else None,
            activities=tuple(_RichActivityData.build_from_entity(activity) for activity in entity.activities),
            client_status=copy.copy(entity.client_status),
        )

    def build_entity(
        self, target: typing.Type[presences.MemberPresence], **kwargs: typing.Any,
    ) -> presences.MemberPresence:
        presence_kwargs = kwargs.pop("presence_kwargs")
        activities = [
            activity.build_entity(presences.RichActivity, **kwargs_)
            for activity, kwargs_ in zip(self.activities, presence_kwargs)
        ]
        return super().build_entity(
            target, activities=activities, client_status=copy.copy(self.client_status), **kwargs
        )


@attr.s(kw_only=True, slots=True, repr=False, hash=False, weakref_slot=False)
class _VoiceStateData(_BaseData[voices.VoiceState]):
    channel_id: typing.Optional[snowflake.Snowflake] = attr.ib()
    guild_id: snowflake.Snowflake = attr.ib()
    is_guild_deafened: bool = attr.ib()
    is_guild_muted: bool = attr.ib()
    is_self_deafened: bool = attr.ib()
    is_self_muted: bool = attr.ib()
    is_streaming: bool = attr.ib()
    is_suppressed: bool = attr.ib()
    is_video_enabled: bool = attr.ib()
    user_id: snowflake.Snowflake = attr.ib()
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


@attr.s(kw_only=True, slots=True, repr=False, hash=False, weakref_slot=False)
class _GenericRefWrapper(typing.Generic[_ValueT]):
    object: _ValueT = attr.ib()
    ref_count: int = attr.ib(default=0)


class _PrivateTextChannelMRUMutableMapping(typing.MutableMapping[snowflake.Snowflake, _PrivateTextChannelData]):
    __slots__: typing.Sequence[str] = ("_data", "_expiry")

    def __init__(
        self,
        source: typing.Union[typing.Mapping[snowflake.Snowflake, _PrivateTextChannelData], None] = None,
        /,
        *,
        expiry: datetime.timedelta,
    ) -> None:
        if expiry <= datetime.timedelta():
            raise ValueError("expiry time must be greater than 0 microseconds.")

        self._data: typing.Dict[snowflake.Snowflake, _PrivateTextChannelData] = dict(source or ())
        self._expiry = expiry

    def _garbage_collect(self) -> None:
        current_time = date.utc_datetime()
        for channel_id, channel in tuple(self._data.items()):
            if channel.last_message_id and current_time - channel.last_message_id.created_at < self._expiry:
                break

            del self._data[channel_id]

    def __delitem__(self, sf: snowflake.Snowflake) -> None:
        del self._data[sf]
        self._garbage_collect()

    def __getitem__(self, sf: snowflake.Snowflake) -> _PrivateTextChannelData:
        return self._data[sf]

    def __iter__(self) -> typing.Iterator[snowflake.Snowflake]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __setitem__(self, sf: snowflake.Snowflake, value: _PrivateTextChannelData) -> None:
        self._garbage_collect()
        #  Seeing as we rely on insertion order in _garbage_collect, we have to make sure that each item is added to
        #  the end of the dict.
        if value.last_message_id is not None and sf in self:
            del self[sf]

        self._data[sf] = value


def _copy_guild_channel(channel: channels.GuildChannel) -> channels.GuildChannel:
    channel = copy.copy(channel)
    channel.permission_overwrites = {
        sf: copy.copy(channel.permission_overwrites[sf]) for sf in channel.permission_overwrites
    }
    return channel


class _GuildChannelCacheMappingView(_StatefulCacheMappingView[snowflake.Snowflake, channels.GuildChannel]):
    @classmethod
    def _copy(cls, value: channels.GuildChannel) -> channels.GuildChannel:
        return _copy_guild_channel(value)


class StatefulCacheImpl(cache.IMutableCacheComponent):
    """In-memory cache implementation."""

    __slots__: typing.Sequence[str] = (
        "_app",
        "_private_text_channel_entries",
        "_emoji_entries",
        "_guild_channel_entries",
        "_guild_entries",
        "_intents",
        "_invite_entries",
        "_me",
        "_role_entries",
        "_unknown_emoji_entries",
        "_user_entries",
    )

    def __init__(self, app: rest_app.IRESTApp, intents: typing.Optional[intents_.Intent]) -> None:
        self._me: typing.Optional[users.OwnUser] = None
        self._private_text_channel_entries: typing.MutableMapping[
            snowflake.Snowflake, _PrivateTextChannelData
        ] = _PrivateTextChannelMRUMutableMapping(expiry=datetime.timedelta(minutes=5))
        self._emoji_entries: typing.MutableMapping[snowflake.Snowflake, _KnownCustomEmojiData] = {}
        self._guild_channel_entries: typing.MutableMapping[snowflake.Snowflake, channels.GuildChannel] = {}
        self._guild_entries: typing.MutableMapping[snowflake.Snowflake, _GuildRecord] = {}
        self._invite_entries: typing.MutableMapping[str, _InviteData] = {}
        self._role_entries: typing.MutableMapping[snowflake.Snowflake, guilds.Role] = {}
        self._unknown_emoji_entries: typing.MutableMapping[
            typing.Union[str, snowflake.Snowflake],
            _GenericRefWrapper[typing.Union[emojis.UnicodeEmoji, emojis.CustomEmoji]],
        ] = {}
        self._user_entries: typing.MutableMapping[snowflake.Snowflake, _GenericRefWrapper[users.User]] = {}

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

    def _build_private_text_channel(
        self,
        channel_data: _PrivateTextChannelData,
        cached_users: typing.Optional[typing.Mapping[snowflake.Snowflake, users.User]] = None,
    ) -> channels.PrivateTextChannel:
        if cached_users:
            recipient = copy.copy(cached_users[channel_data.recipient_id])
        else:
            recipient = copy.copy(self._user_entries[channel_data.recipient_id].object)

        return channel_data.build_entity(channels.PrivateTextChannel, app=self._app, recipient=recipient)

    def clear_private_text_channels(self) -> cache.ICacheView[snowflake.Snowflake, channels.PrivateTextChannel]:
        if not self._private_text_channel_entries:
            return _EmptyCacheView()

        cached_channels = self._private_text_channel_entries
        self._private_text_channel_entries = {}
        cached_users = {}

        for user_id in cached_channels.keys():
            cached_users[user_id] = self._user_entries[user_id].object
            self._garbage_collect_user(user_id, decrement=1)

        return _StatefulCacheMappingView(
            cached_channels, builder=lambda channel: self._build_private_text_channel(channel, cached_users)
        )

    def delete_private_text_channel(
        self, user_id: snowflake.Snowflake, /
    ) -> typing.Optional[channels.PrivateTextChannel]:
        channel_data = self._private_text_channel_entries.pop(user_id, None)
        if channel_data is None:
            return None

        channel = self._build_private_text_channel(channel_data)
        self._garbage_collect_user(user_id, decrement=1)
        return channel

    def get_private_text_channel(self, user_id: snowflake.Snowflake, /) -> typing.Optional[channels.PrivateTextChannel]:
        if user_id in self._private_text_channel_entries:
            return self._build_private_text_channel(self._private_text_channel_entries[user_id])

        return None

    def get_private_text_channels_view(self) -> cache.ICacheView[snowflake.Snowflake, channels.PrivateTextChannel]:
        if not self._private_text_channel_entries:
            return _EmptyCacheView()

        cached_users = {
            sf: user.object for sf, user in self._user_entries.items() if sf in self._private_text_channel_entries
        }
        return _StatefulCacheMappingView(
            dict(self._private_text_channel_entries),
            builder=lambda channel: self._build_private_text_channel(channel, cached_users),
        )

    def set_private_text_channel(self, channel: channels.PrivateTextChannel, /) -> None:
        self.set_user(channel.recipient)

        if channel.recipient.id not in self._private_text_channel_entries:
            self._increment_user_ref_count(channel.recipient.id)

        self._private_text_channel_entries[channel.recipient.id] = _PrivateTextChannelData.build_from_entity(channel)

    def update_private_text_channel(
        self, channel: channels.PrivateTextChannel, /
    ) -> typing.Tuple[typing.Optional[channels.PrivateTextChannel], typing.Optional[channels.PrivateTextChannel]]:
        cached_channel = self.get_private_text_channel(channel.recipient.id)
        self.set_private_text_channel(channel)
        return cached_channel, self.get_private_text_channel(channel.recipient.id)

    def _build_emoji(
        self,
        emoji_data: _KnownCustomEmojiData,
        cached_users: typing.Optional[typing.Mapping[snowflake.Snowflake, users.User]] = None,
    ) -> emojis.KnownCustomEmoji:
        user: typing.Optional[users.User]
        if cached_users is not None and emoji_data.user_id is not None:
            user = copy.copy(cached_users[emoji_data.user_id])
        elif emoji_data.user_id is not None:
            user = copy.copy(self._user_entries[emoji_data.user_id].object)
        else:
            user = None

        return emoji_data.build_entity(emojis.KnownCustomEmoji, app=self._app, user=user)

    def _increment_emoji_ref_count(self, emoji_id: snowflake.Snowflake, increment: int = 1) -> None:
        self._emoji_entries[emoji_id].ref_count += increment

    def _garbage_collect_emoji(self, emoji_id: snowflake.Snowflake, decrement: int = 0) -> None:
        emoji_data = self._emoji_entries.get(emoji_id)

        if emoji_data is None:
            return None

        emoji_data.ref_count -= decrement

        if self._can_delete_emoji(emoji_data):
            del self._emoji_entries[emoji_id]

    @staticmethod
    def _can_delete_emoji(emoji: _KnownCustomEmojiData) -> bool:
        return emoji.has_been_deleted is True and emoji.ref_count < 1

    def _clear_emojis(
        self, guild_id: undefined.UndefinedOr[snowflake.Snowflake] = undefined.UNDEFINED,
    ) -> cache.ICacheView[snowflake.Snowflake, emojis.KnownCustomEmoji]:
        emoji_ids: typing.Iterable[snowflake.Snowflake]
        if guild_id is undefined.UNDEFINED:
            emoji_ids = tuple(self._emoji_entries.keys())
        else:
            guild_record = self._guild_entries.get(guild_id)
            if guild_record is None or guild_record.emojis is None:  # TODO: explicit is vs implicit bool consistency
                return _EmptyCacheView()

            emoji_ids = guild_record.emojis
            guild_record.emojis = None
            self._delete_guild_record_if_empty(guild_id)

        cached_emojis = {}
        cached_users = {}

        for emoji_id in emoji_ids:
            emoji_data = self._emoji_entries[emoji_id]
            emoji_data.has_been_deleted = True
            if not self._can_delete_emoji(emoji_data):
                continue

            del self._emoji_entries[emoji_id]
            cached_emojis[emoji_id] = emoji_data

            if emoji_data.user_id is not None:
                cached_users[emoji_data.user_id] = self._user_entries[emoji_data.user_id].object
                self._garbage_collect_user(emoji_data.user_id, decrement=1)

        return _StatefulCacheMappingView(
            cached_emojis, builder=lambda emoji: self._build_emoji(emoji, cached_users=cached_users)
        )

    def clear_emojis(self) -> cache.ICacheView[snowflake.Snowflake, emojis.KnownCustomEmoji]:
        result = self._clear_emojis()

        for guild_id, guild_record in tuple(self._guild_entries.items()):
            if guild_record.emojis is not None:  # TODO: add test coverage for this.
                guild_record.emojis = None
                self._delete_guild_record_if_empty(guild_id)

        return result

    def clear_emojis_for_guild(
        self, guild_id: snowflake.Snowflake, /
    ) -> cache.ICacheView[snowflake.Snowflake, emojis.KnownCustomEmoji]:
        return self._clear_emojis(guild_id)

    def delete_emoji(self, emoji_id: snowflake.Snowflake, /) -> typing.Optional[emojis.KnownCustomEmoji]:
        emoji_data = self._emoji_entries.pop(emoji_id, None)
        if emoji_data is None:
            return None

        emoji_data.has_been_deleted = True
        if not self._can_delete_emoji(emoji_data):
            return None

        emoji = self._build_emoji(emoji_data)

        if emoji_data.user_id is not None:
            self._garbage_collect_user(emoji_data.user_id, decrement=1)

        guild_record = self._guild_entries.get(emoji_data.guild_id)
        if guild_record and guild_record.emojis:  # TODO: should this make assumptions and be flat?
            guild_record.emojis.remove(emoji_id)

            if not guild_record.emojis:
                guild_record.emojis = None

        return emoji

    def get_emoji(self, emoji_id: snowflake.Snowflake, /) -> typing.Optional[emojis.KnownCustomEmoji]:
        return self._build_emoji(self._emoji_entries[emoji_id]) if emoji_id in self._emoji_entries else None

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
                cached_users[emoji_data.user_id] = self._user_entries[emoji_data.user_id].object

        return _StatefulCacheMappingView(
            cached_emojis, builder=lambda emoji: self._build_emoji(emoji, cached_users=cached_users)
        )

    def get_emojis_view(self) -> cache.ICacheView[snowflake.Snowflake, emojis.KnownCustomEmoji]:
        return self._get_emojis_view()

    def get_emojis_view_for_guild(
        self, guild_id: snowflake.Snowflake, /
    ) -> cache.ICacheView[snowflake.Snowflake, emojis.KnownCustomEmoji]:
        return self._get_emojis_view(guild_id=guild_id)

    def set_emoji(self, emoji: emojis.KnownCustomEmoji, /) -> None:
        if emoji.user is not None:
            self.set_user(emoji.user)
            if emoji.id not in self._emoji_entries:
                self._increment_user_ref_count(emoji.user.id)

        self._emoji_entries[emoji.id] = _KnownCustomEmojiData.build_from_entity(emoji)
        guild_container = self._get_or_create_guild_record(emoji.guild_id)

        if guild_container.emojis is None:  # TODO: add test cases when it is not None?
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
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is not None:
            if guild_record.guild and not guild_record.is_available:
                raise errors.UnavailableGuildError(guild_record.guild) from None

            return copy.copy(guild_record.guild)

        return None

    def get_guilds_view(self) -> cache.ICacheView[snowflake.Snowflake, guilds.GatewayGuild]:
        results = {
            sf: guild_record.guild for sf, guild_record in self._guild_entries.items() if guild_record.guild
        }  # TODO: do we want to include unavailable guilds here or hide them?
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
        cached_channels = self._guild_channel_entries
        self._guild_channel_entries = {}

        for guild_id, guild_record in self._guild_entries.items():
            if guild_record.channels is not None:
                guild_record.channels = None
                self._garbage_collect_user(guild_id)

        return _StatefulCacheMappingView(cached_channels)

    def clear_guild_channels_for_guild(
        self, guild_id: snowflake.Snowflake, /
    ) -> cache.ICacheView[snowflake.Snowflake, channels.GuildChannel]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is None or guild_record.channels is None:
            return _EmptyCacheView()

        cached_channels = {sf: self._guild_channel_entries.pop(sf) for sf in guild_record.channels}
        guild_record.channels = None
        self._delete_guild_record_if_empty(guild_id)
        return _StatefulCacheMappingView(cached_channels)

    def delete_guild_channel(self, channel_id: snowflake.Snowflake, /) -> typing.Optional[channels.GuildChannel]:
        channel = self._guild_channel_entries.pop(channel_id, None)

        if channel is not None:  # TODO: flat and make assumptions?
            guild_record = self._guild_entries.get(channel.guild_id)

            if guild_record and guild_record.channels is not None:
                guild_record.channels.remove(channel_id)

        return channel

    def get_guild_channel(self, channel_id: snowflake.Snowflake, /) -> typing.Optional[channels.GuildChannel]:
        channel = self._guild_channel_entries.get(channel_id)
        return _copy_guild_channel(channel) if channel is not None else None

    def _get_guild_channels_view(
        self, guild_id: undefined.UndefinedOr[snowflake.Snowflake] = undefined.UNDEFINED
    ) -> cache.ICacheView[snowflake.Snowflake, channels.GuildChannel]:
        channel_ids: typing.Iterable[snowflake.Snowflake]
        if guild_id is undefined.UNDEFINED:
            channel_ids = self._guild_channel_entries.keys()
        else:
            guild_record = self._guild_entries.get(guild_id)
            if guild_record is None or not guild_record.channels:
                return _EmptyCacheView()

            channel_ids = guild_record.channels

        return _GuildChannelCacheMappingView({sf: self._guild_channel_entries[sf] for sf in channel_ids})

    def get_guild_channels_view(self) -> cache.ICacheView[snowflake.Snowflake, channels.GuildChannel]:
        return self._get_guild_channels_view()

    def get_guild_channels_view_for_guild(
        self, guild_id: snowflake.Snowflake, /
    ) -> cache.ICacheView[snowflake.Snowflake, channels.GuildChannel]:
        return self._get_guild_channels_view(guild_id=guild_id)

    def set_guild_channel(self, channel: channels.GuildChannel, /) -> None:
        self._guild_channel_entries[channel.id] = _copy_guild_channel(channel)
        guild_record = self._get_or_create_guild_record(channel.guild_id)

        if guild_record.channels is None:
            guild_record.channels = _IDTable()

        guild_record.channels.add(channel.id)

    def update_guild_channel(
        self, channel: channels.GuildChannel, /
    ) -> typing.Tuple[typing.Optional[channels.GuildChannel], typing.Optional[channels.GuildChannel]]:
        cached_channel = self.get_guild_channel(channel.id)
        self.set_guild_channel(channel)
        return cached_channel, self.get_guild_channel(channel.id)

    def _build_invite(
        self,
        invite_data: _InviteData,
        cached_users: undefined.UndefinedOr[typing.Mapping[snowflake.Snowflake, users.User]] = undefined.UNDEFINED,
    ) -> invites.InviteWithMetadata:
        inviter: typing.Optional[users.User]
        if cached_users is not undefined.UNDEFINED and invite_data.inviter_id is not None:
            inviter = copy.copy(cached_users[invite_data.inviter_id])
        elif invite_data.inviter_id is not None:
            inviter = copy.copy(self._user_entries[invite_data.inviter_id].object)
        else:
            inviter = None

        target_user: typing.Optional[users.User]
        if cached_users is not undefined.UNDEFINED and invite_data.target_user_id is not None:
            target_user = copy.copy(cached_users[invite_data.target_user_id])
        elif invite_data.target_user_id is not None:
            target_user = copy.copy(self._user_entries[invite_data.target_user_id].object)
        else:
            target_user = None

        return invite_data.build_entity(
            invites.InviteWithMetadata, app=self._app, inviter=inviter, target_user=target_user
        )

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
            invite_codes = tuple(self._invite_entries.keys())

        cached_invites = {}
        cached_users = {}

        for code in invite_codes:
            invite_data = self._invite_entries.pop(code)
            cached_invites[code] = invite_data

            if invite_data.inviter_id is not None:
                cached_users[invite_data.inviter_id] = self._user_entries[invite_data.inviter_id].object
                self._garbage_collect_user(invite_data.inviter_id, decrement=1)

            if invite_data.target_user_id is not None:
                cached_users[invite_data.target_user_id] = self._user_entries[invite_data.target_user_id].object
                self._garbage_collect_user(invite_data.target_user_id, decrement=1)

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
            del self._invite_entries[code]
            guild_record.invites.remove(code)

            if invite_data.inviter_id is not None:
                cached_users[invite_data.inviter_id] = self._user_entries[invite_data.inviter_id].object
                self._garbage_collect_user(invite_data.inviter_id, decrement=1)

            if invite_data.target_user_id is not None:
                cached_users[invite_data.target_user_id] = self._user_entries[invite_data.target_user_id].object
                self._garbage_collect_user(invite_data.target_user_id, decrement=1)

        if not guild_record.invites:
            guild_record.invites = None
            self._delete_guild_record_if_empty(guild_id)

        return _StatefulCacheMappingView(
            cached_invites, builder=lambda invite_data: self._build_invite(invite_data, cached_users=cached_users)
        )

    def delete_invite(self, code: str, /) -> typing.Optional[invites.InviteWithMetadata]:
        if code not in self._invite_entries:
            return None

        invite = self._build_invite(self._invite_entries.pop(code))

        if invite.inviter is not None:
            self._garbage_collect_user(invite.inviter.id, decrement=1)

        if invite.target_user is not None:
            self._garbage_collect_user(invite.target_user.id, decrement=1)

        if invite.guild_id is not None:  # TODO: test case when this is None?
            guild_record = self._guild_entries.get(invite.guild_id)
            if guild_record and guild_record.invites is not None:  # TODO: should this make assumptions and be flat?
                guild_record.invites.remove(code)

                if not guild_record.invites:
                    guild_record.invites = None  # TODO: test when this is set to None
                    self._delete_guild_record_if_empty(invite.guild_id)

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
                cached_users[invite_data.inviter_id] = self._user_entries[invite_data.inviter_id].object

            if invite_data.target_user_id is not None:
                cached_users[invite_data.target_user_id] = self._user_entries[invite_data.target_user_id].object

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

        for code in tuple(guild_entry.invites):
            invite_data = self._invite_entries[code]
            if invite_data.channel_id != channel_id:
                continue

            cached_invites[code] = invite_data
            guild_entry.invites.remove(code)
            del self._invite_entries[code]

            if invite_data.inviter_id is not None:
                cached_users[invite_data.inviter_id] = self._user_entries[invite_data.inviter_id].object

            if invite_data.target_user_id is not None:
                cached_users[invite_data.target_user_id] = self._user_entries[invite_data.target_user_id].object

        if not guild_entry.channels:  # TODO: test coverage
            guild_entry.channels = None
            self._delete_guild_record_if_empty(guild_id)

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
        cached_users: typing.Optional[typing.Mapping[snowflake.Snowflake, users.User]] = None,
    ) -> guilds.Member:
        if cached_users is None:
            user = copy.copy(self._user_entries[member_data.id].object)
        else:
            user = copy.copy(cached_users[member_data.id])

        return member_data.build_entity(guilds.Member, user=user)

    def _can_remove_member(self, member: _MemberData) -> bool:
        if member.has_been_deleted is False:
            return False

        guild_record = self._guild_entries[member.guild_id]
        return bool(not guild_record.voice_states or member.id not in guild_record.voice_states)

    def _garbage_collect_member(self, guild_id: snowflake.Snowflake, user_id: snowflake.Snowflake) -> None:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is None or guild_record.members is None or user_id not in guild_record.members:
            return

        member_data = guild_record.members[user_id]
        if not self._can_remove_member(member_data):
            return

        del guild_record.members[user_id]
        if not guild_record.members:
            guild_record.members = None
            self._delete_guild_record_if_empty(guild_id)

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

        for user_id, member_data in tuple(guild_record.members.items()):
            member_data.has_been_deleted = True
            if not self._can_remove_member(member_data):
                continue

            cached_members[user_id] = guild_record.members.pop(user_id)
            cached_users[user_id] = self._user_entries[user_id].object
            self._garbage_collect_user(user_id, decrement=1)

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
        if guild_record is None or guild_record.members is None:
            return None

        member_data = guild_record.members.get(user_id)
        if member_data is None or not self._can_remove_member(member_data):
            return None

        member = self._build_member(member_data)
        del guild_record.members[user_id]
        if not guild_record.members:
            guild_record.members = None
            self._delete_guild_record_if_empty(guild_id)

        self._garbage_collect_user(user_id, decrement=1)
        return member

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
            if not guild_record.members:  # TODO: if None?
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
            cached_users[user_id] = self._user_entries[user_id].object
            cached_members[user_id] = member

        return _StatefulCacheMappingView(
            cached_members, builder=lambda member: self._build_member(member, cached_users=cached_users)
        )

    def set_member(self, member: guilds.Member, /) -> None:
        guild_record = self._get_or_create_guild_record(member.guild_id)
        self.set_user(member.user)
        member_data = _MemberData.build_from_entity(member)

        if guild_record.members is None:  # TODO: test when this is not None
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

    def _build_presence(
        self,
        presence_data: _MemberPresenceData,
        cached_emojis: typing.Optional[
            typing.Mapping[typing.Union[str, snowflake.Snowflake], typing.Union[emojis.Emoji, _KnownCustomEmojiData]]
        ] = None,
        cached_users: typing.Optional[typing.Mapping[snowflake.Snowflake, users.User]] = None,
    ) -> presences.MemberPresence:
        presence_kwargs: typing.MutableSequence[typing.Mapping[str, typing.Optional[emojis.Emoji]]] = []
        for activity_data in presence_data.activities:
            identifier = activity_data.emoji_id_or_name
            if identifier is None:
                presence_kwargs.append({"emoji": None})

            elif cached_emojis:
                emoji = cached_emojis[identifier]
                if isinstance(emoji, _KnownCustomEmojiData):
                    presence_kwargs.append({"emoji": self._build_emoji(emoji, cached_users=cached_users)})
                else:
                    presence_kwargs.append({"emoji": copy.copy(emoji)})

                continue

            elif isinstance(identifier, snowflake.Snowflake) and identifier in self._emoji_entries:
                presence_kwargs.append(
                    {"emoji": self._build_emoji(self._emoji_entries[identifier], cached_users=cached_users)}
                )
                continue

            else:
                presence_kwargs.append({"emoji": copy.copy(self._unknown_emoji_entries[identifier].object)})

        return presence_data.build_entity(presences.MemberPresence, app=self._app, presence_kwargs=presence_kwargs)

    def _garbage_collect_unknown_emoji(
        self, emoji_id_or_name: typing.Union[snowflake.Snowflake, str], decrement: int = 0
    ) -> None:
        emoji = self._unknown_emoji_entries.get(emoji_id_or_name)  # TODO: use this style for all gc methods
        if emoji is None:
            return None

        emoji.ref_count -= decrement
        if emoji.ref_count == 0:
            del self._unknown_emoji_entries[emoji_id_or_name]

    def clear_presences(
        self,
    ) -> cache.ICacheView[snowflake.Snowflake, cache.ICacheView[snowflake.Snowflake, presences.MemberPresence]]:
        views = {}

        for guild_id, guild_record in self._guild_entries.items():
            if not guild_record.presences:
                continue

            views[guild_id] = self.clear_presences_for_guild(guild_id)

        return _StatefulCacheMappingView(views)

    def clear_presences_for_guild(
        self, guild_id: snowflake.Snowflake, /
    ) -> cache.ICacheView[snowflake.Snowflake, presences.MemberPresence]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is None or guild_record.presences is None:
            return _EmptyCacheView()

        cached_emojis: typing.MutableMapping[
            typing.Union[str, snowflake.Snowflake], typing.Union[emojis.Emoji, _KnownCustomEmojiData]
        ] = {}
        cached_users = {}
        cached_presences = {}

        for user_id, presence_data in guild_record.presences.items():
            cached_presences[user_id] = presence_data

            for activity_data in presence_data.activities:
                emoji_identifier = activity_data.emoji_id_or_name
                if emoji_identifier is None:
                    continue

                if isinstance(emoji_identifier, snowflake.Snowflake) and emoji_identifier in self._emoji_entries:
                    known_emoji_data = self._emoji_entries[emoji_identifier]

                    if known_emoji_data.user_id is not None:
                        cached_users[known_emoji_data.user_id] = self._user_entries[known_emoji_data.user_id].object

                    cached_emojis[emoji_identifier] = known_emoji_data
                    self._garbage_collect_emoji(emoji_identifier, decrement=-1)

                else:
                    cached_emojis[emoji_identifier] = self._unknown_emoji_entries[emoji_identifier].object
                    self._garbage_collect_unknown_emoji(emoji_identifier, decrement=1)

        return _StatefulCacheMappingView(
            cached_presences,
            builder=lambda presence_data_: self._build_presence(
                presence_data_, cached_users=cached_users, cached_emojis=cached_emojis
            ),
        )

    def delete_presence(
        self, guild_id: snowflake.Snowflake, user_id: snowflake.Snowflake, /
    ) -> typing.Optional[presences.MemberPresence]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is None or guild_record.presences is None:
            return None

        presence_data = guild_record.presences.pop(user_id, None)

        if presence_data is None:
            return None

        presence = self._build_presence(presence_data)

        for activity in presence.activities:
            if activity.emoji is None:
                continue

            if isinstance(activity.emoji, emojis.KnownCustomEmoji):
                self._garbage_collect_emoji(activity.emoji.id, decrement=-1)

            else:
                emoji_identifier: typing.Union[snowflake.Snowflake, str]
                if isinstance(activity.emoji, emojis.CustomEmoji):
                    emoji_identifier = activity.emoji.id
                else:
                    assert activity.emoji.name is not None
                    emoji_identifier = activity.emoji.name

                self._garbage_collect_unknown_emoji(
                    emoji_identifier, decrement=1,
                )

        return presence

    def get_presence(
        self, guild_id: snowflake.Snowflake, user_id: snowflake.Snowflake, /
    ) -> typing.Optional[presences.MemberPresence]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is None or guild_record.presences is None:
            return None

        return self._build_presence(guild_record.presences[user_id]) if user_id in guild_record.presences else None

    def get_presences_view(
        self,
    ) -> cache.ICacheView[snowflake.Snowflake, cache.ICacheView[snowflake.Snowflake, presences.MemberPresence]]:
        views = {}

        for guild_id, guild_record in self._guild_entries.items():
            if not guild_record.presences:
                continue

            views[guild_id] = self.get_presences_view_for_guild(guild_id)

        return _StatefulCacheMappingView(views)

    def get_presences_view_for_guild(
        self, guild_id: snowflake.Snowflake, /
    ) -> cache.ICacheView[snowflake.Snowflake, presences.MemberPresence]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is None or guild_record.presences is None:
            return _EmptyCacheView()

        cached_emojis: typing.MutableMapping[
            typing.Union[str, snowflake.Snowflake], typing.Union[emojis.Emoji, _KnownCustomEmojiData]
        ] = {}
        cached_users = {}
        cached_presences = {}

        for user_id, presence_data in guild_record.presences.items():
            cached_presences[user_id] = presence_data

            for activity_data in presence_data.activities:
                emoji_identifier = activity_data.emoji_id_or_name

                if emoji_identifier is None or emoji_identifier in cached_emojis:
                    continue

                if isinstance(emoji_identifier, snowflake.Snowflake) and emoji_identifier in self._emoji_entries:
                    emoji_data = self._emoji_entries[emoji_identifier]

                    if emoji_data.user_id is not None:
                        cached_users[emoji_data.user_id] = self._user_entries[emoji_data.user_id].object

                    cached_emojis[emoji_identifier] = emoji_data

                else:
                    cached_emojis[emoji_identifier] = self._unknown_emoji_entries[emoji_identifier].object

        return _StatefulCacheMappingView(
            cached_presences,
            builder=lambda presence_data_: self._build_presence(
                presence_data_, cached_users=cached_users, cached_emojis=cached_emojis
            ),
        )

    def set_presence(self, presence: presences.MemberPresence, /) -> None:
        presence_data = _MemberPresenceData.build_from_entity(presence)

        for activity in presence.activities:
            emoji = activity.emoji
            if not emoji:
                continue

            if isinstance(emoji, emojis.CustomEmoji) and emoji.id in self._emoji_entries:
                self._increment_emoji_ref_count(emoji.id)
            else:
                emoji_identifier: typing.Union[snowflake.Snowflake, str]
                if isinstance(emoji, emojis.CustomEmoji):
                    emoji_identifier = emoji.id
                else:
                    # should always be Unicode otherwise
                    emoji = typing.cast(emojis.UnicodeEmoji, emoji)
                    emoji_identifier = emoji.name

                wrapped_emoji = _GenericRefWrapper(object=copy.copy(emoji), ref_count=1)

                if emoji_identifier in self._unknown_emoji_entries:
                    wrapped_emoji.ref_count += self._unknown_emoji_entries[emoji_identifier].ref_count

                self._unknown_emoji_entries[emoji_identifier] = wrapped_emoji

        guild_record = self._get_or_create_guild_record(presence.guild_id)
        if guild_record.presences is None:
            guild_record.presences = {}

        guild_record.presences[presence.user_id] = presence_data

    def update_presence(
        self, presence: presences.MemberPresence, /
    ) -> typing.Tuple[typing.Optional[presences.MemberPresence], typing.Optional[presences.MemberPresence]]:
        cached_presence = self.get_presence(presence.guild_id, presence.user_id)
        self.set_presence(presence)
        return cached_presence, self.get_presence(presence.guild_id, presence.user_id)

    def clear_roles(self) -> cache.ICacheView[snowflake.Snowflake, guilds.Role]:
        if not self._role_entries:
            return _EmptyCacheView()

        roles = self._role_entries
        self._role_entries = {}

        for guild_id, guild_record in tuple(self._guild_entries.items()):
            if guild_record.roles is not None:  # TODO: test coverage for this
                guild_record.roles = None
                self._delete_guild_record_if_empty(guild_id)

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
        role = self._role_entries.pop(role_id, None)  # TODO: this honestly feels jank, should we redo this?
        if role is None:
            return None

        guild_record = self._guild_entries.get(role.guild_id)
        if guild_record and guild_record.roles is not None:
            guild_record.roles.remove(role_id)

            if not guild_record.roles:  # TODO: should this make assumptions and be flat?
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

        if guild_record.roles is None:  # TODO: test when this is not None
            guild_record.roles = _IDTable()

        guild_record.roles.add(role.id)

    def update_role(
        self, role: guilds.Role, /
    ) -> typing.Tuple[typing.Optional[guilds.Role], typing.Optional[guilds.Role]]:
        cached_role = self.get_role(role.id)
        self.set_role(role)
        return cached_role, self.get_role(role.id)

    def _can_remove_user(self, user_id: snowflake.Snowflake) -> bool:
        user_data = self._user_entries.get(user_id)
        return bool(user_data and user_data.ref_count == 0)

    def _increment_user_ref_count(self, user_id: snowflake.Snowflake, increment: int = 1) -> None:
        self._user_entries[user_id].ref_count += increment

    def _garbage_collect_user(self, user_id: snowflake.Snowflake, *, decrement: typing.Optional[int] = None) -> None:
        if decrement is not None and user_id in self._user_entries:
            self._increment_user_ref_count(user_id, -decrement)

        if self._can_remove_user(user_id):
            del self._user_entries[user_id]

    def clear_users(self) -> cache.ICacheView[snowflake.Snowflake, users.User]:
        if not self._user_entries:
            return _EmptyCacheView()

        cached_users = {}

        for user_id, user in tuple(self._user_entries.items()):
            if user.ref_count > 0:
                continue

            cached_users[user_id] = user.object
            del self._user_entries[user_id]

        return _StatefulCacheMappingView(cached_users) if cached_users else _EmptyCacheView()

    def delete_user(self, user_id: snowflake.Snowflake, /) -> typing.Optional[users.User]:
        if self._can_remove_user(user_id):
            return self._user_entries.pop(user_id).object

        return None

    def get_user(self, user_id: snowflake.Snowflake, /) -> typing.Optional[users.User]:
        return copy.copy(self._user_entries[user_id].object) if user_id in self._user_entries else None

    def get_users_view(self) -> cache.ICacheView[snowflake.Snowflake, users.User]:
        if not self._user_entries:
            return _EmptyCacheView()

        return _StatefulCacheMappingView({user_id: user.object for user_id, user in self._user_entries.items()})

    def set_user(self, user: users.User, /) -> None:
        wrapper_user = _GenericRefWrapper(object=copy.copy(user))

        if user.id in self._user_entries:  # TODO: test this behaviour
            wrapper_user.ref_count = self._user_entries[user.id].ref_count

        self._user_entries[user.id] = wrapper_user

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
        cached_users: typing.Optional[typing.Mapping[snowflake.Snowflake, users.User]] = None,
    ) -> voices.VoiceState:
        if cached_members:
            member = self._build_member(cached_members[voice_data.user_id], cached_users=cached_users)
        else:
            guild_record = self._guild_entries[voice_data.guild_id]
            assert guild_record.members is not None
            member_data = guild_record.members[voice_data.user_id]
            member = self._build_member(member_data, cached_users=cached_users)

        return voice_data.build_entity(voices.VoiceState, app=self._app, member=member)

    def clear_voice_states(
        self,
    ) -> cache.ICacheView[snowflake.Snowflake, cache.ICacheView[snowflake.Snowflake, voices.VoiceState]]:
        views = {}

        for guild_id, guild_record in tuple(self._guild_entries.items()):
            if not guild_record.voice_states:
                continue

            views[guild_id] = self.clear_voice_states_for_guild(guild_id)

        return _StatefulCacheMappingView(views)

    def clear_voice_states_for_channel(
        self, guild_id: snowflake.Snowflake, channel_id: snowflake.Snowflake, /
    ) -> cache.ICacheView[snowflake.Snowflake, voices.VoiceState]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is None or guild_record.voice_states is None:
            return _EmptyCacheView()

        assert guild_record.members is not None
        cached_members = {}
        cached_users = {}
        cached_voice_states = {}

        for user_id, voice_state in guild_record.voice_states.items():
            if voice_state.channel_id != channel_id:
                continue

            cached_members[user_id] = guild_record.members[user_id]
            cached_users[user_id] = self._user_entries[user_id].object
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

    def clear_voice_states_for_guild(
        self, guild_id: snowflake.Snowflake, /
    ) -> cache.ICacheView[snowflake.Snowflake, voices.VoiceState]:
        guild_record = self._guild_entries.get(guild_id)

        if guild_record is None or guild_record.voice_states is None:
            return _EmptyCacheView()

        assert guild_record.members is not None
        cached_voice_states = guild_record.voice_states
        guild_record.voice_states = None
        cached_members = {}
        cached_users = {}

        for user_id in cached_voice_states.keys():
            cached_members[user_id] = guild_record.members[user_id]
            cached_users[user_id] = self._user_entries[user_id].object
            self._garbage_collect_member(guild_id, user_id)

        self._delete_guild_record_if_empty(guild_id)
        return _StatefulCacheMappingView(
            cached_voice_states,
            builder=lambda voice_data: self._build_voice_state(
                voice_data, cached_members=cached_members, cached_users=cached_users
            ),
        )

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

        voice_state = self._build_voice_state(voice_state_data)
        self._garbage_collect_member(voice_state.guild_id, voice_state.user_id)
        self._delete_guild_record_if_empty(guild_id)
        return voice_state

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
            cached_users[user_id] = self._user_entries[user_id].object
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
            cached_users[user_id] = self._user_entries[user_id].object

        return _StatefulCacheMappingView(
            voice_states,
            builder=lambda voice_data: self._build_voice_state(
                voice_data, cached_members=cached_members, cached_users=cached_users
            ),
        )

    def set_voice_state(self, voice_state: voices.VoiceState, /) -> None:
        guild_record = self._get_or_create_guild_record(voice_state.guild_id)

        if guild_record.voice_states is None:  # TODO: test when this is not None
            guild_record.voice_states = {}

        self.set_member(voice_state.member)
        assert guild_record.members  # TOOD: account for this method not setting the member in some cases later on
        guild_record.members[voice_state.member.id].has_been_deleted = True
        guild_record.voice_states[voice_state.user_id] = _VoiceStateData.build_from_entity(voice_state)

    def update_voice_state(
        self, voice_state: voices.VoiceState, /
    ) -> typing.Tuple[typing.Optional[voices.VoiceState], typing.Optional[voices.VoiceState]]:
        cached_voice_state = self.get_voice_state(voice_state.guild_id, voice_state.user_id)
        self.set_voice_state(voice_state)
        return cached_voice_state, self.get_voice_state(voice_state.guild_id, voice_state.user_id)
