# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021 davfsa
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
    "CacheMappingView",
    "EmptyCacheView",
    "GuildRecord",
    "BaseData",
    "InviteData",
    "MemberData",
    "KnownCustomEmojiData",
    "RichActivityData",
    "MemberPresenceData",
    "MentionsData",
    "MessageData",
    "VoiceStateData",
    "RefCell",
    "unwrap_ref_cell",
    "copy_guild_channel",
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

from hikari import embeds as embeds_
from hikari import emojis
from hikari import guilds
from hikari import invites
from hikari import iterators
from hikari import messages
from hikari import presences
from hikari import snowflakes
from hikari import undefined
from hikari import voices
from hikari.api import cache
from hikari.internal import attr_extensions
from hikari.internal import collections

if typing.TYPE_CHECKING:
    from hikari import channels as channels_
    from hikari import traits
    from hikari import users as users_

ChannelT = typing.TypeVar("ChannelT", bound="channels_.GuildChannel")
DataT = typing.TypeVar("DataT", bound="BaseData[typing.Any]")
"""Type-hint for "data" objects used for storing and building entities."""
KeyT = typing.TypeVar("KeyT", bound=typing.Hashable)
"""Type-hint for mapping keys."""
ValueT = typing.TypeVar("ValueT")
"""Type-hint for mapping values."""


class CacheMappingView(cache.CacheView[KeyT, ValueT], typing.Generic[KeyT, ValueT]):
    """A cache mapping view implementation used for representing cached data.

    Parameters
    ----------
    items : typing.Mapping[KeyT, typing.Union[ValueT, DataT, RefCell[ValueT]]]
        A mapping of keys to the values in their raw forms, wrapped by a ref
        wrapper or in a data form.
    builder : typing.Optional[typing.Callable[[DataT], ValueT]]
        The callable used to build entities before they're returned by the
        mapping. This is used to cover the case when items stores `DataT` objects.
    predicate : typing.Optional[typing.Callable[[typing.Any], bool]]
        A callable to use to determine whether entries should be returned or hidden,
        this should take in whatever raw type was passed for the value in `items`.
        This may be `builtins.None` if all entries should be exposed.
    """

    __slots__: typing.Sequence[str] = ("_builder", "_data", "_predicate")

    def __init__(
        self,
        items: typing.Mapping[KeyT, typing.Union[ValueT, DataT]],
        *,
        builder: typing.Optional[typing.Callable[[DataT], ValueT]] = None,
        predicate: typing.Optional[typing.Callable[[typing.Any], bool]] = None,
    ) -> None:
        self._builder = builder
        self._data = items
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

    members: typing.Optional[collections.ExtendedMutableMapping[snowflakes.Snowflake, RefCell[MemberData]]] = attr.ib(
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

    def empty(self) -> bool:
        """Check whether this guild record has any resources attached to it.

        Returns
        -------
        builtins.bool
            Whether this guild record has any resources attached to it.
        """
        # As `.is_available` should be paired with `.guild`, we don't need to check both.
        return not any(
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
    def build_entity(self, app: traits.RESTAware, /) -> ValueT:
        """Build an entity object from this data object.

        Parameters
        ----------
        app : hikari.traits.RESTAware
            The hikari application the built object should be bound to.

        Returns
        -------
        The initialised entity object.
        """

    @classmethod
    @abc.abstractmethod
    def build_from_entity(cls: typing.Type[DataT], entity: ValueT, /) -> DataT:
        """Build a data object from an initialised entity.

        Parameters
        ----------
        entity : ValueT
            The entity object to build a data class from.

        Returns
        -------
        The built data class.
        """


@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, repr=False, hash=False, weakref_slot=False)
class InviteData(BaseData[invites.InviteWithMetadata]):
    """A data model for storing invite data in an in-memory cache."""

    code: str = attr.ib()
    guild_id: typing.Optional[snowflakes.Snowflake] = attr.ib()
    channel_id: snowflakes.Snowflake = attr.ib()
    inviter: typing.Optional[RefCell[users_.User]] = attr.ib()
    target_user: typing.Optional[RefCell[users_.User]] = attr.ib()
    target_user_type: typing.Union[invites.TargetUserType, int, None] = attr.ib()
    uses: int = attr.ib()
    max_uses: typing.Optional[int] = attr.ib()
    max_age: typing.Optional[datetime.timedelta] = attr.ib()
    is_temporary: bool = attr.ib()
    created_at: datetime.datetime = attr.ib()

    def build_entity(self, app: traits.RESTAware, /) -> invites.InviteWithMetadata:
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
            app=app,
            inviter=self.inviter.copy() if self.inviter else None,
            target_user=self.target_user.copy() if self.target_user else None,
        )

    @classmethod
    def build_from_entity(
        cls,
        invite: invites.InviteWithMetadata,
        /,
        *,
        inviter: typing.Optional[RefCell[users_.User]] = None,
        target_user: typing.Optional[RefCell[users_.User]] = None,
    ) -> InviteData:
        if not inviter and invite.inviter:
            inviter = RefCell(copy.copy(invite.inviter))

        if not target_user and invite.target_user:
            target_user = RefCell(copy.copy(invite.target_user))

        return cls(
            code=invite.code,
            guild_id=invite.guild_id,
            channel_id=invite.channel_id,
            target_user_type=invite.target_user_type,
            uses=invite.uses,
            max_uses=invite.max_uses,
            max_age=invite.max_age,
            is_temporary=invite.is_temporary,
            created_at=invite.created_at,
            inviter=inviter,
            target_user=target_user,
        )


@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, repr=False, hash=False, weakref_slot=False)
class MemberData(BaseData[guilds.Member]):
    """A data model for storing member data in an in-memory cache."""

    user: RefCell[users_.User] = attr.ib()
    guild_id: snowflakes.Snowflake = attr.ib()
    nickname: undefined.UndefinedNoneOr[str] = attr.ib()
    role_ids: typing.Tuple[snowflakes.Snowflake, ...] = attr.ib()
    joined_at: datetime.datetime = attr.ib()
    premium_since: typing.Optional[datetime.datetime] = attr.ib()
    is_deaf: undefined.UndefinedOr[bool] = attr.ib()
    is_mute: undefined.UndefinedOr[bool] = attr.ib()
    is_pending: undefined.UndefinedOr[bool] = attr.ib()
    # meta-attribute
    has_been_deleted: bool = attr.ib(default=False)

    @classmethod
    def build_from_entity(
        cls, member: guilds.Member, /, *, user: typing.Optional[RefCell[users_.User]] = None
    ) -> MemberData:
        return cls(
            guild_id=member.guild_id,
            nickname=member.nickname,
            joined_at=member.joined_at,
            premium_since=member.premium_since,
            is_deaf=member.is_deaf,
            is_mute=member.is_mute,
            is_pending=member.is_pending,
            user=user or RefCell(copy.copy(member.user)),
            # role_ids is a special case as it may be mutable so we want to ensure it's immutable when cached.
            role_ids=tuple(member.role_ids),
        )

    def build_entity(self, _: traits.RESTAware, /) -> guilds.Member:
        return guilds.Member(
            guild_id=self.guild_id,
            nickname=self.nickname,
            role_ids=self.role_ids,
            joined_at=self.joined_at,
            premium_since=self.premium_since,
            is_deaf=self.is_deaf,
            is_mute=self.is_mute,
            is_pending=self.is_pending,
            user=self.user.copy(),
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
    user: typing.Optional[RefCell[users_.User]] = attr.ib()
    is_colons_required: bool = attr.ib()
    is_managed: bool = attr.ib()
    is_available: bool = attr.ib()

    @classmethod
    def build_from_entity(
        cls,
        emoji: emojis.KnownCustomEmoji,
        /,
        *,
        user: typing.Optional[RefCell[users_.User]] = None,
    ) -> KnownCustomEmojiData:
        if not user and emoji.user:
            user = RefCell(copy.copy(emoji.user))

        return cls(
            id=emoji.id,
            name=emoji.name,
            is_animated=emoji.is_animated,
            guild_id=emoji.guild_id,
            is_colons_required=emoji.is_colons_required,
            is_managed=emoji.is_managed,
            is_available=emoji.is_available,
            user=user,
            # role_ids is a special case as it may be a mutable sequence so we want to ensure it's immutable when cached.
            role_ids=tuple(emoji.role_ids),
        )

    def build_entity(self, app: traits.RESTAware, /) -> emojis.KnownCustomEmoji:
        return emojis.KnownCustomEmoji(
            id=self.id,
            name=self.name,
            is_animated=self.is_animated,
            guild_id=self.guild_id,
            role_ids=self.role_ids,
            is_colons_required=self.is_colons_required,
            is_managed=self.is_managed,
            is_available=self.is_available,
            app=app,
            user=self.user.copy() if self.user else None,
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
    emoji: typing.Union[RefCell[emojis.CustomEmoji], str, None] = attr.ib()
    party: typing.Optional[presences.ActivityParty] = attr.ib()
    assets: typing.Optional[presences.ActivityAssets] = attr.ib()
    secrets: typing.Optional[presences.ActivitySecret] = attr.ib()
    is_instance: typing.Optional[bool] = attr.ib()
    flags: typing.Optional[presences.ActivityFlag] = attr.ib()

    @classmethod
    def build_from_entity(
        cls,
        activity: presences.RichActivity,
        /,
        *,
        emoji: typing.Union[RefCell[emojis.CustomEmoji], str, None] = None,
    ) -> RichActivityData:
        if emoji:
            pass

        elif isinstance(activity.emoji, emojis.CustomEmoji):
            emoji = RefCell(copy.copy(activity.emoji))

        elif activity.emoji:
            emoji = activity.emoji.name

        timestamps = copy.copy(activity.timestamps) if activity.timestamps is not None else None
        party = copy.copy(activity.party) if activity.party is not None else None
        assets = copy.copy(activity.assets) if activity.assets is not None else None
        secrets = copy.copy(activity.secrets) if activity.secrets is not None else None
        return cls(
            name=activity.name,
            url=activity.url,
            type=activity.type,
            created_at=activity.created_at,
            application_id=activity.application_id,
            details=activity.details,
            state=activity.state,
            is_instance=activity.is_instance,
            flags=activity.flags,
            emoji=emoji,
            timestamps=timestamps,
            party=party,
            assets=assets,
            secrets=secrets,
        )

    def build_entity(self, _: traits.RESTAware, /) -> presences.RichActivity:
        emoji: typing.Optional[emojis.Emoji] = None
        if isinstance(self.emoji, RefCell):
            emoji = self.emoji.copy()

        elif self.emoji is not None:
            emoji = emojis.UnicodeEmoji(self.emoji)

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
            emoji=emoji,
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
    def build_from_entity(cls, presence: presences.MemberPresence, /) -> MemberPresenceData:
        # role_ids and activities are special cases as may be mutable sequences, therefor we ant to ensure they're
        # stored in immutable sequences (tuples). Plus activities need to be converted to Data objects.
        return cls(
            user_id=presence.user_id,
            guild_id=presence.guild_id,
            visible_status=presence.visible_status,
            activities=tuple(RichActivityData.build_from_entity(activity) for activity in presence.activities),
            client_status=copy.copy(presence.client_status),
        )

    def build_entity(self, app: traits.RESTAware, /) -> presences.MemberPresence:
        return presences.MemberPresence(
            user_id=self.user_id,
            guild_id=self.guild_id,
            visible_status=self.visible_status,
            app=app,
            activities=[activity.build_entity(app) for activity in self.activities],
            client_status=copy.copy(self.client_status),
        )


@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, repr=False, hash=False, weakref_slot=False)
class MentionsData(BaseData[messages.Mentions]):
    """A model for storing message mentions data in an in-memory cache."""

    users: undefined.UndefinedOr[typing.Mapping[snowflakes.Snowflake, RefCell[users_.User]]] = attr.ib()
    role_ids: undefined.UndefinedOr[typing.Tuple[snowflakes.Snowflake, ...]] = attr.ib()
    channels: undefined.UndefinedOr[typing.Mapping[snowflakes.Snowflake, channels_.PartialChannel]] = attr.ib()
    everyone: undefined.UndefinedOr[bool] = attr.ib()

    @classmethod
    def build_from_entity(
        cls,
        mentions: messages.Mentions,
        /,
        *,
        users: undefined.UndefinedOr[typing.Mapping[snowflakes.Snowflake, RefCell[users_.User]]] = undefined.UNDEFINED,
    ) -> MentionsData:
        if not users and mentions.users is not undefined.UNDEFINED:
            users = {user_id: RefCell(copy.copy(user)) for user_id, user in mentions.users.items()}

        channels: undefined.UndefinedOr[
            typing.Mapping[snowflakes.Snowflake, "channels_.PartialChannel"]
        ] = undefined.UNDEFINED
        if mentions.channels is not undefined.UNDEFINED:
            channels = {channel_id: copy.copy(channel) for channel_id, channel in mentions.channels.items()}

        return cls(
            users=users,
            role_ids=tuple(mentions.role_ids) if mentions.role_ids is not undefined.UNDEFINED else undefined.UNDEFINED,
            # TODO: do we want to de-duplicate mention_channels?
            channels=channels,
            everyone=mentions.everyone,
        )

    def build_entity(
        self, _: traits.RESTAware, /, *, message: typing.Optional[messages.Message] = None
    ) -> messages.Mentions:
        users: undefined.UndefinedOr[typing.Mapping[snowflakes.Snowflake, users_.User]] = undefined.UNDEFINED
        if self.users is not undefined.UNDEFINED:
            users = {user_id: user.copy() for user_id, user in self.users.items()}

        channels: undefined.UndefinedOr[
            typing.Mapping[snowflakes.Snowflake, channels_.PartialChannel]
        ] = undefined.UNDEFINED
        if self.channels is not undefined.UNDEFINED:
            channels = {channel_id: copy.copy(channel) for channel_id, channel in self.channels.items()}

        return messages.Mentions(
            message=message or NotImplemented,
            users=users,
            role_ids=self.role_ids,
            channels=channels,
            everyone=self.everyone,
        )

    def update(
        self,
        mention: messages.Mentions,
        /,
        *,
        users: undefined.UndefinedOr[typing.Mapping[snowflakes.Snowflake, RefCell[users_.User]]] = undefined.UNDEFINED,
    ) -> None:
        if users is not undefined.UNDEFINED:
            self.users = users

        elif mention.users is not undefined.UNDEFINED:
            self.users = {user_id: RefCell(copy.copy(user)) for user_id, user in mention.users.items()}

        if mention.role_ids is not undefined.UNDEFINED:
            self.role_ids = tuple(mention.role_ids)

        if mention.channels is not undefined.UNDEFINED:
            self.channels = {channel_id: copy.copy(channel) for channel_id, channel in mention.channels.items()}

        if mention.everyone is not undefined.UNDEFINED:
            self.everyone = mention.everyone


def _copy_embed(embed: embeds_.Embed) -> embeds_.Embed:
    return embeds_.Embed.from_received_embed(
        title=embed.title,
        description=embed.description,
        url=embed.url,
        color=embed.color,
        timestamp=embed.timestamp,
        image=copy.copy(embed.image) if embed.image else None,
        thumbnail=copy.copy(embed.thumbnail) if embed.thumbnail else None,
        video=copy.copy(embed.video) if embed.video else None,
        author=copy.copy(embed.author) if embed.author else None,
        provider=copy.copy(embed.provider) if embed.provider else None,
        footer=copy.copy(embed.footer) if embed.footer else None,
        fields=list(map(copy.copy, embed.fields)),  # type: ignore[arg-type]
    )


@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, repr=False, hash=False, weakref_slot=False)
class MessageData(BaseData[messages.Message]):
    """A model for storing message data in an in-memory cache."""

    id: snowflakes.Snowflake = attr.ib()
    channel_id: snowflakes.Snowflake = attr.ib()
    guild_id: typing.Optional[snowflakes.Snowflake] = attr.ib()
    author: RefCell[users_.User] = attr.ib()
    member: typing.Optional[RefCell[MemberData]] = attr.ib()
    content: typing.Optional[str] = attr.ib()
    timestamp: datetime.datetime = attr.ib()
    edited_timestamp: typing.Optional[datetime.datetime] = attr.ib()
    is_tts: bool = attr.ib()
    mentions: MentionsData = attr.ib()
    attachments: typing.Tuple[messages.Attachment, ...] = attr.ib()
    embeds: typing.Tuple[embeds_.Embed, ...] = attr.ib()
    reactions: typing.Tuple[messages.Reaction, ...] = attr.ib()
    is_pinned: bool = attr.ib()
    webhook_id: typing.Optional[snowflakes.Snowflake] = attr.ib()
    type: typing.Union[messages.MessageType, int] = attr.ib()
    activity: typing.Optional[messages.MessageActivity] = attr.ib()
    application: typing.Optional[messages.MessageApplication] = attr.ib()
    message_reference: typing.Optional[messages.MessageReference] = attr.ib()
    flags: typing.Optional[messages.MessageFlag] = attr.ib()
    stickers: typing.Tuple[messages.Sticker, ...] = attr.ib()
    nonce: typing.Optional[str] = attr.ib()
    referenced_message: undefined.UndefinedNoneOr[RefCell[MessageData]] = attr.ib()

    @classmethod
    def build_from_entity(
        cls,
        message: messages.Message,
        /,
        *,
        author: typing.Optional[RefCell[users_.User]] = None,
        member: typing.Optional[RefCell[MemberData]] = None,
        mention_users: undefined.UndefinedOr[
            typing.Mapping[snowflakes.Snowflake, RefCell[users_.User]]
        ] = undefined.UNDEFINED,
        referenced_message: typing.Optional[RefCell[MessageData]] = None,
    ) -> MessageData:
        if not member and message.member:
            member = RefCell(MemberData.build_from_entity(message.member))

        if not referenced_message and message.referenced_message:
            referenced_message = RefCell(MessageData.build_from_entity(message.referenced_message))

        return cls(
            id=message.id,
            channel_id=message.channel_id,
            guild_id=message.guild_id,
            author=author or RefCell(copy.copy(message.author)),
            member=member,
            content=message.content,
            timestamp=message.timestamp,
            edited_timestamp=message.edited_timestamp,
            is_tts=message.is_tts,
            mentions=MentionsData.build_from_entity(message.mentions, users=mention_users),
            attachments=tuple(map(copy.copy, message.attachments)),
            embeds=tuple(map(_copy_embed, message.embeds)),
            reactions=tuple(map(copy.copy, message.reactions)),
            is_pinned=message.is_pinned,
            webhook_id=message.webhook_id,
            type=message.type,
            activity=copy.copy(message.activity) if message.activity else None,
            application=copy.copy(message.application) if message.application else None,
            message_reference=copy.copy(message.message_reference) if message.message_reference else None,
            flags=copy.copy(message.flags),
            stickers=tuple(map(copy.copy, message.stickers)),
            nonce=message.nonce,
            referenced_message=referenced_message,
        )

    def build_entity(self, app: traits.RESTAware, /) -> messages.Message:
        referenced_message: undefined.UndefinedNoneOr[messages.Message]
        if isinstance(self.referenced_message, RefCell):
            referenced_message = self.referenced_message.object.build_entity(app)

        else:
            referenced_message = self.referenced_message

        message = messages.Message(
            id=self.id,
            app=app,
            channel_id=self.channel_id,
            guild_id=self.guild_id,
            author=self.author.copy(),
            member=self.member.object.build_entity(app) if self.member else None,
            content=self.content,
            timestamp=self.timestamp,
            edited_timestamp=self.edited_timestamp,
            is_tts=self.is_tts,
            mentions=NotImplemented,
            attachments=tuple(map(copy.copy, self.attachments)),
            embeds=tuple(map(_copy_embed, self.embeds)),
            reactions=tuple(map(copy.copy, self.reactions)),
            is_pinned=self.is_pinned,
            webhook_id=self.webhook_id,
            type=self.type,
            activity=copy.copy(self.activity) if self.activity else None,
            application=copy.copy(self.application) if self.application else None,
            message_reference=copy.copy(self.message_reference) if self.message_reference else None,
            flags=self.flags,
            stickers=tuple(map(copy.copy, self.stickers)),
            nonce=self.nonce,
            referenced_message=referenced_message,
        )
        message.mentions = self.mentions.build_entity(app, message=message)
        return message

    def update(
        self,
        message: messages.PartialMessage,
        /,
        *,
        mention_users: undefined.UndefinedOr[
            typing.Mapping[snowflakes.Snowflake, RefCell[users_.User]]
        ] = undefined.UNDEFINED,
    ) -> None:
        if message.content is not undefined.UNDEFINED:
            self.content = message.content

        if message.edited_timestamp is not undefined.UNDEFINED:
            self.edited_timestamp = message.edited_timestamp

        if message.is_pinned is not undefined.UNDEFINED:
            self.is_pinned = message.is_pinned

        if message.attachments is not undefined.UNDEFINED:
            self.attachments = tuple(map(copy.copy, message.attachments))

        if message.embeds is not undefined.UNDEFINED:
            self.embeds = tuple(map(_copy_embed, message.embeds))

        self.mentions.update(message.mentions, users=mention_users)


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
    member: RefCell[MemberData] = attr.ib()
    session_id: str = attr.ib()

    def build_entity(self, app: traits.RESTAware, /) -> voices.VoiceState:
        member = self.member.object.build_entity(app)
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
            user_id=member.user.id,
            session_id=self.session_id,
            app=app,
            member=member,
        )

    @classmethod
    def build_from_entity(
        cls,
        voice_state: voices.VoiceState,
        /,
        *,
        member: typing.Optional[RefCell[MemberData]] = None,
    ) -> VoiceStateData:
        return cls(
            channel_id=voice_state.channel_id,
            guild_id=voice_state.guild_id,
            is_self_deafened=voice_state.is_self_deafened,
            is_self_muted=voice_state.is_self_muted,
            is_guild_deafened=voice_state.is_guild_deafened,
            is_guild_muted=voice_state.is_guild_muted,
            is_streaming=voice_state.is_streaming,
            is_suppressed=voice_state.is_suppressed,
            is_video_enabled=voice_state.is_video_enabled,
            member=member or RefCell(MemberData.build_from_entity(voice_state.member)),
            session_id=voice_state.session_id,
        )


@attr_extensions.with_copy
@attr.s(slots=True, repr=True, hash=False, weakref_slot=True)
class Cell(typing.Generic[ValueT]):
    """Object used to store mutable references to a value in multiple places."""

    object: ValueT = attr.ib(repr=True)

    def copy(self) -> ValueT:
        """Get a copy of the contents of this cell.

        Returns
        -------
        ValueT
            The copied contents of this cell.
        """
        return copy.copy(self.object)


@attr_extensions.with_copy
@attr.s(slots=True, repr=False, hash=False, weakref_slot=False)
class RefCell(typing.Generic[ValueT]):
    """Object used to track mutable references to a value in multiple places.

    This is intended to enable reference counting for entities that are only kept
    alive by reference (e.g. the unknown emoji objects attached to presence
    activities and user objects) without the use of a "Data" object which lowers
    the time spent building these entities for the objects that reference them.
    """

    object: ValueT = attr.ib(repr=True)
    ref_count: int = attr.ib(default=0, kw_only=True)

    def copy(self) -> ValueT:
        """Get a copy of the contents of this cell.

        Returns
        -------
        ValueT
            The copied contents of this cell.
        """
        return copy.copy(self.object)


def unwrap_ref_cell(cell: RefCell[ValueT]) -> ValueT:
    """Unwrap a `RefCell` instance to it's contents.

    Parameters
    ----------
    cell : RefCell[ValueT]
        The reference cell instance to unwrap

    Returns
    -------
    ValueT
        The reference cell's content.
    """
    return cell.copy()


def copy_guild_channel(channel: ChannelT) -> ChannelT:
    """Logic for handling the copying of guild channel objects.

    This exists account for the permission overwrite objects attached to guild
    channel objects which need to be copied themselves.
    """
    channel = copy.copy(channel)
    channel.permission_overwrites = {
        sf: copy.copy(overwrite) for sf, overwrite in channel.permission_overwrites.items()
    }
    return channel


class Cache3DMappingView(CacheMappingView[snowflakes.Snowflake, cache.CacheView[KeyT, ValueT]]):
    """A special case of the Mapping View which avoids copying the already immutable views contained within it."""

    __slots__: typing.Sequence[str] = ()

    @classmethod
    def _copy(cls, value: cache.CacheView[KeyT, ValueT]) -> cache.CacheView[KeyT, ValueT]:
        return value
