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
    "MessageInteractionData",
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
    from hikari import applications
    from hikari import channels as channels_
    from hikari import stickers as stickers_
    from hikari import traits
    from hikari import users as users_
    from hikari.interactions import base_interactions

ChannelT = typing.TypeVar("ChannelT", bound="channels_.GuildChannel")
DataT = typing.TypeVar("DataT", bound="BaseData[typing.Any]")
"""Type-hint for "data" objects used for storing and building entities."""
KeyT = typing.TypeVar("KeyT", bound=typing.Hashable)
"""Type-hint for mapping keys."""
ValueT = typing.TypeVar("ValueT")
"""Type-hint for mapping values."""


class CacheMappingView(cache.CacheView[KeyT, ValueT]):
    """A cache mapping view implementation used for representing cached data.

    Parameters
    ----------
    items : typing.Union[typing.Mapping[KeyT, ValueT], typing.Mapping[KeyT, DataT]]
        A mapping of keys to the values in their raw forms, wrapped by a ref
        wrapper or in a data form.
    builder : typing.Optional[typing.Callable[[DataT], ValueT]]
        The callable used to build entities before they're returned by the
        mapping. This is used to cover the case when items stores `DataT` objects.
    """

    __slots__: typing.Sequence[str] = ("_data", "_builder")

    @typing.overload
    def __init__(
        self,
        items: typing.Mapping[KeyT, ValueT],
    ) -> None:
        ...

    @typing.overload
    def __init__(
        self,
        items: typing.Mapping[KeyT, DataT],
        *,
        builder: typing.Callable[[DataT], ValueT],
    ) -> None:
        ...

    def __init__(
        self,
        items: typing.Union[typing.Mapping[KeyT, ValueT], typing.Mapping[KeyT, DataT]],
        *,
        builder: typing.Optional[typing.Callable[[DataT], ValueT]] = None,
    ) -> None:
        self._builder = builder
        self._data = items

    @staticmethod
    def _copy(value: ValueT) -> ValueT:
        return copy.copy(value)

    def __contains__(self, key: typing.Any) -> bool:
        return key in self._data

    def __getitem__(self, key: KeyT) -> ValueT:
        entry = self._data[key]

        if self._builder:
            return self._builder(entry)  # type: ignore[arg-type]

        return self._copy(entry)  # type: ignore[arg-type]

    def __iter__(self) -> typing.Iterator[KeyT]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    @typing.overload
    def get_item_at(self, index: int, /) -> ValueT:
        ...

    @typing.overload
    def get_item_at(self, index: slice, /) -> typing.Sequence[ValueT]:
        ...

    def get_item_at(self, index: typing.Union[slice, int], /) -> typing.Union[ValueT, typing.Sequence[ValueT]]:
        return collections.get_index_or_slice(self, index)

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

    def get_item_at(self, index: typing.Union[slice, int]) -> typing.NoReturn:
        raise IndexError(index)

    def iterator(self) -> iterators.LazyIterator[ValueT]:
        return iterators.FlatLazyIterator(())


@attr_extensions.with_copy
@attr.define(repr=False, hash=False, weakref_slot=False)
class GuildRecord:
    """An object used for storing guild specific cached information in-memory.

    This includes references to the cached entities that "belong" to the guild
    by ID if it's globally unique or by object if it's only unique within the
    guild.
    """

    is_available: typing.Optional[bool] = attr.field(default=None)
    """Whether the cached guild is available or not.

    This will be `builtins.None` when no `GuildRecord.guild` is also
    `builtins.None` else `builtins.bool`.
    """

    guild: typing.Optional[guilds.GatewayGuild] = attr.field(default=None)
    """A cached guild object.

    This will be `hikari.guilds.GatewayGuild` or `builtins.None` if not cached.
    """

    channels: typing.Optional[typing.MutableSet[snowflakes.Snowflake]] = attr.field(default=None)
    """A set of the IDs of the guild channels cached for this guild.

    This will be `builtins.None` if no channels are cached for this guild else
    `typing.MutableSet[hikari.snowflakes.Snowflake]` of channel IDs.
    """

    emojis: typing.Optional[typing.MutableSet[snowflakes.Snowflake]] = attr.field(default=None)
    """A set of the IDs of the emojis cached for this guild.

    This will be `builtins.None` if no emojis are cached for this guild else
    `typing.MutableSet[hikari.snowflakes.Snowflake]` of emoji IDs.
    """

    invites: typing.Optional[typing.MutableSequence[str]] = attr.field(default=None)
    """A set of the `builtins.str` codes of the invites cached for this guild.

    This will be `builtins.None` if no invites are cached for this guild else
    `typing.MutableSequence[str]` of invite codes.
    """

    members: typing.Optional[
        collections.ExtendedMutableMapping[snowflakes.Snowflake, RefCell[MemberData]]
    ] = attr.field(default=None)
    """A mapping of user IDs to the objects of members cached for this guild.

    This will be `builtins.None` if no members are cached for this guild else
    `hikari.internal.collections.ExtendedMutableMapping[hikari.snowflakes.Snowflake, MemberData]`.
    """

    presences: typing.Optional[
        collections.ExtendedMutableMapping[snowflakes.Snowflake, MemberPresenceData]
    ] = attr.field(default=None)
    """A mapping of user IDs to objects of the presences cached for this guild.

    This will be `builtins.None` if no presences are cached for this guild else
    `hikari.internal.collections.ExtendedMutableMapping[hikari.snowflakes.Snowflake, MemberPresenceData]`.
    """

    roles: typing.Optional[typing.MutableSet[snowflakes.Snowflake]] = attr.field(default=None)
    """A set of the IDs of the roles cached for this guild.

    This will be `builtins.None` if no roles are cached for this guild else
    `typing.MutableSet[hikari.snowflakes.Snowflake]` of role IDs.
    """

    voice_states: typing.Optional[
        collections.ExtendedMutableMapping[snowflakes.Snowflake, VoiceStateData]
    ] = attr.field(default=None)
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
@attr.define(kw_only=True, repr=False, hash=False, weakref_slot=False)
class InviteData(BaseData[invites.InviteWithMetadata]):
    """A data model for storing invite data in an in-memory cache."""

    code: str = attr.field()
    guild_id: typing.Optional[snowflakes.Snowflake] = attr.field()
    channel_id: snowflakes.Snowflake = attr.field()
    inviter: typing.Optional[RefCell[users_.User]] = attr.field()
    target_type: typing.Union[invites.TargetType, int, None] = attr.field()
    target_user: typing.Optional[RefCell[users_.User]] = attr.field()
    target_application: typing.Optional[applications.InviteApplication] = attr.ib()
    uses: int = attr.field()
    max_uses: typing.Optional[int] = attr.field()
    max_age: typing.Optional[datetime.timedelta] = attr.field()
    is_temporary: bool = attr.field()
    created_at: datetime.datetime = attr.field()

    def build_entity(self, app: traits.RESTAware, /) -> invites.InviteWithMetadata:
        return invites.InviteWithMetadata(
            code=self.code,
            guild_id=self.guild_id,
            channel_id=self.channel_id,
            target_type=self.target_type,
            target_application=self.target_application,
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
            expires_at=self.created_at + self.max_age if self.max_age else None,
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
            target_type=invite.target_type,
            target_application=invite.target_application,
            uses=invite.uses,
            max_uses=invite.max_uses,
            max_age=invite.max_age,
            is_temporary=invite.is_temporary,
            created_at=invite.created_at,
            inviter=inviter,
            target_user=target_user,
        )


@attr_extensions.with_copy
@attr.define(kw_only=True, repr=False, hash=False, weakref_slot=False)
class MemberData(BaseData[guilds.Member]):
    """A data model for storing member data in an in-memory cache."""

    user: RefCell[users_.User] = attr.field()
    guild_id: snowflakes.Snowflake = attr.field()
    nickname: typing.Optional[str] = attr.field()
    guild_avatar_hash: typing.Optional[str] = attr.field()
    role_ids: typing.Tuple[snowflakes.Snowflake, ...] = attr.field()
    joined_at: datetime.datetime = attr.field()
    premium_since: typing.Optional[datetime.datetime] = attr.field()
    is_deaf: undefined.UndefinedOr[bool] = attr.field()
    is_mute: undefined.UndefinedOr[bool] = attr.field()
    is_pending: undefined.UndefinedOr[bool] = attr.field()
    raw_communication_disabled_until: typing.Optional[datetime.datetime] = attr.field()
    # meta-attribute
    has_been_deleted: bool = attr.field(default=False)

    @classmethod
    def build_from_entity(
        cls, member: guilds.Member, /, *, user: typing.Optional[RefCell[users_.User]] = None
    ) -> MemberData:
        return cls(
            guild_id=member.guild_id,
            nickname=member.nickname,
            joined_at=member.joined_at,
            premium_since=member.premium_since,
            guild_avatar_hash=member.guild_avatar_hash,
            is_deaf=member.is_deaf,
            is_mute=member.is_mute,
            is_pending=member.is_pending,
            user=user or RefCell(copy.copy(member.user)),
            raw_communication_disabled_until=member.raw_communication_disabled_until,
            # role_ids is a special case as it may be mutable so we want to ensure it's immutable when cached.
            role_ids=tuple(member.role_ids),
        )

    def build_entity(self, _: traits.RESTAware, /) -> guilds.Member:
        return guilds.Member(
            guild_id=self.guild_id,
            nickname=self.nickname,
            role_ids=self.role_ids,
            joined_at=self.joined_at,
            guild_avatar_hash=self.guild_avatar_hash,
            premium_since=self.premium_since,
            is_deaf=self.is_deaf,
            is_mute=self.is_mute,
            is_pending=self.is_pending,
            raw_communication_disabled_until=self.raw_communication_disabled_until,
            user=self.user.copy(),
        )


@attr_extensions.with_copy
@attr.define(kw_only=True, repr=False, hash=False, weakref_slot=False)
class KnownCustomEmojiData(BaseData[emojis.KnownCustomEmoji]):
    """A data model for storing known custom emoji data in an in-memory cache."""

    id: snowflakes.Snowflake = attr.field()
    name: str = attr.field()
    is_animated: bool = attr.field()
    guild_id: snowflakes.Snowflake = attr.field()
    role_ids: typing.Tuple[snowflakes.Snowflake, ...] = attr.field()
    user: typing.Optional[RefCell[users_.User]] = attr.field()
    is_colons_required: bool = attr.field()
    is_managed: bool = attr.field()
    is_available: bool = attr.field()

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
@attr.define(kw_only=True, repr=False, hash=False, weakref_slot=False)
class RichActivityData(BaseData[presences.RichActivity]):
    """A data model for storing rich activity data in an in-memory cache."""

    name: str = attr.field()
    url: typing.Optional[str] = attr.field()
    type: typing.Union[presences.ActivityType, int] = attr.field()
    created_at: datetime.datetime = attr.field()
    timestamps: typing.Optional[presences.ActivityTimestamps] = attr.field()
    application_id: typing.Optional[snowflakes.Snowflake] = attr.field()
    details: typing.Optional[str] = attr.field()
    state: typing.Optional[str] = attr.field()
    emoji: typing.Union[RefCell[emojis.CustomEmoji], str, None] = attr.field()
    party: typing.Optional[presences.ActivityParty] = attr.field()
    assets: typing.Optional[presences.ActivityAssets] = attr.field()
    secrets: typing.Optional[presences.ActivitySecret] = attr.field()
    is_instance: typing.Optional[bool] = attr.field()
    flags: typing.Optional[presences.ActivityFlag] = attr.field()
    buttons: typing.Tuple[str, ...] = attr.field()

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
            buttons=tuple(activity.buttons),
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
            buttons=self.buttons,
        )


@attr_extensions.with_copy
@attr.define(kw_only=True, repr=False, hash=False, weakref_slot=False)
class MemberPresenceData(BaseData[presences.MemberPresence]):
    """A data model for storing presence data in an in-memory cache."""

    user_id: snowflakes.Snowflake = attr.field()
    guild_id: snowflakes.Snowflake = attr.field()
    visible_status: typing.Union[presences.Status, str] = attr.field()
    activities: typing.Tuple[RichActivityData, ...] = attr.field()
    client_status: presences.ClientStatus = attr.field()

    @classmethod
    def build_from_entity(cls, presence: presences.MemberPresence, /) -> MemberPresenceData:
        # role_ids and activities are special cases as may be mutable sequences, therefore we want to ensure they're
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
@attr.define(kw_only=True, repr=False, hash=False, weakref_slot=False)
class MentionsData(BaseData[messages.Mentions]):
    """A model for storing message mentions data in an in-memory cache."""

    users: undefined.UndefinedOr[typing.Mapping[snowflakes.Snowflake, RefCell[users_.User]]] = attr.field()
    role_ids: undefined.UndefinedOr[typing.Tuple[snowflakes.Snowflake, ...]] = attr.field()
    channels: undefined.UndefinedOr[typing.Mapping[snowflakes.Snowflake, channels_.PartialChannel]] = attr.field()
    everyone: undefined.UndefinedOr[bool] = attr.field()

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


@attr_extensions.with_copy
@attr.define(kw_only=True, repr=False, hash=False, weakref_slot=False)
class MessageInteractionData(BaseData[messages.MessageInteraction]):
    """A model for storing message interaction data."""

    id: snowflakes.Snowflake = attr.field(hash=True, repr=True)
    type: typing.Union[base_interactions.InteractionType, int] = attr.field(eq=False, repr=True)
    name: str = attr.field(eq=False, repr=True)
    user: RefCell[users_.User] = attr.field(eq=False, repr=True)

    @classmethod
    def build_from_entity(
        cls,
        interaction: messages.MessageInteraction,
        /,
        *,
        user: typing.Optional[RefCell[users_.User]] = None,
    ) -> MessageInteractionData:
        if user is None:
            user = RefCell(interaction.user)

        return MessageInteractionData(id=interaction.id, type=interaction.type, name=interaction.name, user=user)

    def build_entity(self, _: traits.RESTAware, /) -> messages.MessageInteraction:
        return messages.MessageInteraction(id=self.id, type=self.type, name=self.name, user=self.user.copy())


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
        fields=[copy.copy(field) for field in embed.fields],
    )


@attr_extensions.with_copy
@attr.define(kw_only=True, repr=False, hash=False, weakref_slot=False)
class MessageData(BaseData[messages.Message]):
    """A model for storing message data in an in-memory cache."""

    id: snowflakes.Snowflake = attr.field()
    channel_id: snowflakes.Snowflake = attr.field()
    guild_id: typing.Optional[snowflakes.Snowflake] = attr.field()
    author: RefCell[users_.User] = attr.field()
    member: typing.Optional[RefCell[MemberData]] = attr.field()
    content: typing.Optional[str] = attr.field()
    timestamp: datetime.datetime = attr.field()
    edited_timestamp: typing.Optional[datetime.datetime] = attr.field()
    is_tts: bool = attr.field()
    mentions: MentionsData = attr.field()
    attachments: typing.Tuple[messages.Attachment, ...] = attr.field()
    embeds: typing.Tuple[embeds_.Embed, ...] = attr.field()
    reactions: typing.Tuple[messages.Reaction, ...] = attr.field()
    is_pinned: bool = attr.field()
    webhook_id: typing.Optional[snowflakes.Snowflake] = attr.field()
    type: typing.Union[messages.MessageType, int] = attr.field()
    activity: typing.Optional[messages.MessageActivity] = attr.field()
    application: typing.Optional[messages.MessageApplication] = attr.field()
    message_reference: typing.Optional[messages.MessageReference] = attr.field()
    flags: messages.MessageFlag = attr.field()
    stickers: typing.Tuple[stickers_.PartialSticker, ...] = attr.field()
    nonce: typing.Optional[str] = attr.field()
    referenced_message: typing.Optional[RefCell[MessageData]] = attr.field()
    interaction: typing.Optional[MessageInteractionData] = attr.field()
    application_id: typing.Optional[snowflakes.Snowflake] = attr.field()
    components: typing.Tuple[messages.PartialComponent, ...] = attr.field()

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
        interaction_user: typing.Optional[RefCell[users_.User]] = None,
    ) -> MessageData:
        if not member and message.member:
            member = RefCell(MemberData.build_from_entity(message.member))

        if not referenced_message and message.referenced_message:
            referenced_message = RefCell(MessageData.build_from_entity(message.referenced_message))

        interaction: typing.Optional[MessageInteractionData] = None
        if message.interaction:
            interaction = MessageInteractionData.build_from_entity(message.interaction, user=interaction_user)

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
            interaction=interaction,
            application_id=message.application_id,
            components=tuple(message.components),
        )

    def build_entity(self, app: traits.RESTAware, /) -> messages.Message:
        referenced_message: typing.Optional[messages.Message] = None
        if self.referenced_message:
            referenced_message = self.referenced_message.object.build_entity(app)

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
            interaction=self.interaction.build_entity(app) if self.interaction else None,
            application_id=self.application_id,
            components=self.components,
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

        if message.components is not undefined.UNDEFINED:
            self.components = tuple(message.components)

        self.mentions.update(message.mentions, users=mention_users)


@attr_extensions.with_copy
@attr.define(kw_only=True, repr=False, hash=False, weakref_slot=False)
class VoiceStateData(BaseData[voices.VoiceState]):
    """A data model for storing voice state data in an in-memory cache."""

    channel_id: typing.Optional[snowflakes.Snowflake] = attr.field()
    guild_id: snowflakes.Snowflake = attr.field()
    is_guild_deafened: bool = attr.field()
    is_guild_muted: bool = attr.field()
    is_self_deafened: bool = attr.field()
    is_self_muted: bool = attr.field()
    is_streaming: bool = attr.field()
    is_suppressed: bool = attr.field()
    is_video_enabled: bool = attr.field()
    member: RefCell[MemberData] = attr.field()
    session_id: str = attr.field()
    requested_to_speak_at: typing.Optional[datetime.datetime] = attr.field()

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
            requested_to_speak_at=self.requested_to_speak_at,
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
            requested_to_speak_at=voice_state.requested_to_speak_at,
        )


@attr_extensions.with_copy
@attr.define(repr=True, hash=False, weakref_slot=True)
class Cell(typing.Generic[ValueT]):
    """Object used to store mutable references to a value in multiple places."""

    object: ValueT = attr.field(repr=True)

    def copy(self) -> ValueT:
        """Get a copy of the contents of this cell.

        Returns
        -------
        ValueT
            The copied contents of this cell.
        """
        return copy.copy(self.object)


@attr_extensions.with_copy
@attr.define(repr=False, hash=False, weakref_slot=False)
class RefCell(typing.Generic[ValueT]):
    """Object used to track mutable references to a value in multiple places.

    This is intended to enable reference counting for entities that are only kept
    alive by reference (e.g. the unknown emoji objects attached to presence
    activities and user objects) without the use of a "Data" object which lowers
    the time spent building these entities for the objects that reference them.
    """

    object: ValueT = attr.field(repr=True)
    ref_count: int = attr.field(default=0, kw_only=True)

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
    """A special case of the Mapping View which avoids copying the immutable values contained within it."""

    __slots__: typing.Sequence[str] = ()

    @staticmethod
    def _copy(value: cache.CacheView[KeyT, ValueT]) -> cache.CacheView[KeyT, ValueT]:
        return value
