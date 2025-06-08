# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021-present davfsa
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

__all__: typing.Sequence[str] = (
    "BaseData",
    "Cache3DMappingView",
    "CacheMappingView",
    "DataT",
    "EmptyCacheView",
    "GuildRecord",
    "InviteData",
    "KeyT",
    "KnownCustomEmojiData",
    "MemberData",
    "MemberPresenceData",
    "MessageData",
    "RefCell",
    "RichActivityData",
    "ValueT",
    "VoiceStateData",
    "copy_guild_channel",
    "unwrap_ref_cell",
)

import abc
import copy
import typing

import attrs

from hikari import embeds as embeds_
from hikari import emojis
from hikari import guilds
from hikari import invites
from hikari import messages
from hikari import presences
from hikari import snowflakes
from hikari import stickers as stickers_
from hikari import undefined
from hikari import voices
from hikari.api import cache
from hikari.internal import attrs_extensions
from hikari.internal import collections

if not typing.TYPE_CHECKING:
    # This is insanely hacky, but it is needed for ruff to not complain until it gets type inference
    from hikari.internal import typing_extensions


if typing.TYPE_CHECKING:
    import datetime

    import typing_extensions  # noqa: TC004
    from typing_extensions import Self

    from hikari import applications
    from hikari import channels as channels_
    from hikari import components as components_
    from hikari import polls as polls_
    from hikari import traits
    from hikari import users as users_
    from hikari.interactions import base_interactions

ChannelT = typing.TypeVar("ChannelT", bound="channels_.PermissibleGuildChannel")
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
    items
        A mapping of keys to the values in their raw forms, wrapped by a ref
        wrapper or in a data form.
    builder
        The callable used to build entities before they're returned by the
        mapping. This is used to cover the case when items stores [`DataT`][] objects.
    """

    __slots__: typing.Sequence[str] = ("_builder", "_data")

    @typing.overload
    def __init__(self, items: typing.Mapping[KeyT, ValueT]) -> None: ...

    @typing.overload
    def __init__(self, items: typing.Mapping[KeyT, DataT], *, builder: typing.Callable[[DataT], ValueT]) -> None: ...

    def __init__(
        self,
        items: typing.Mapping[KeyT, ValueT] | typing.Mapping[KeyT, DataT],
        *,
        builder: typing.Callable[[DataT], ValueT] | None = None,
    ) -> None:
        self._builder = builder
        self._data = items

    @staticmethod
    def _copy(value: ValueT) -> ValueT:
        return copy.copy(value)

    @typing_extensions.override
    def __contains__(self, key: object) -> bool:
        return key in self._data

    @typing_extensions.override
    def __getitem__(self, key: KeyT) -> ValueT:
        entry = self._data[key]

        if self._builder:
            return self._builder(entry)  # type: ignore[arg-type]

        return self._copy(entry)  # type: ignore[arg-type]

    @typing_extensions.override
    def __iter__(self) -> typing.Iterator[KeyT]:
        return iter(self._data)

    @typing_extensions.override
    def __len__(self) -> int:
        return len(self._data)

    @typing.overload
    def get_item_at(self, index: int, /) -> ValueT: ...

    @typing.overload
    def get_item_at(self, index: slice, /) -> typing.Sequence[ValueT]: ...

    @typing_extensions.override
    def get_item_at(self, index: slice | int, /) -> ValueT | typing.Sequence[ValueT]:
        return collections.get_index_or_slice(self, index)


class EmptyCacheView(cache.CacheView[typing.Any, typing.Any]):
    """An empty cache view implementation."""

    __slots__: typing.Sequence[str] = ()

    @typing_extensions.override
    def __contains__(self, _: object) -> typing.Literal[False]:
        return False

    @typing_extensions.override
    def __getitem__(self, key: object) -> typing.NoReturn:
        raise KeyError(key)

    @typing_extensions.override
    def __iter__(self) -> typing.Iterator[typing.Any]:
        yield from ()

    @typing_extensions.override
    def __len__(self) -> typing.Literal[0]:
        return 0

    @typing_extensions.override
    def get_item_at(self, index: slice | int) -> typing.NoReturn:
        raise IndexError(index)


@attrs_extensions.with_copy
@attrs.define(repr=False, weakref_slot=False)
class GuildRecord:
    """An object used for storing guild specific cached information in-memory.

    This includes references to the cached entities that "belong" to the guild
    by ID if it's globally unique or by object if it's only unique within the
    guild.
    """

    is_available: bool | None = attrs.field(default=None)
    """Whether the cached guild is available or not.

    This will be [`None`][] when no `guild` is also
    [`None`][] else [`bool`][].
    """

    guild: guilds.GatewayGuild | None = attrs.field(default=None)
    """A cached guild object.

    This will be [`None`][] if not cached.
    """

    channels: typing.MutableSet[snowflakes.Snowflake] | None = attrs.field(default=None)
    """A set of the IDs of the guild channels cached for this guild.

    This will be [`None`][] if no channels are cached for this guild.
    """

    threads: typing.MutableSet[snowflakes.Snowflake] | None = attrs.field(default=None)
    """A set of the IDs of the guild threads cached for this guild.

    This will be [`None`][] if no threads are cached for this guild.
    """

    emojis: typing.MutableSet[snowflakes.Snowflake] | None = attrs.field(default=None)
    """A set of the IDs of the emojis cached for this guild.

    This will be [`None`][] if no emojis are cached for this guild.
    """

    stickers: typing.MutableSet[snowflakes.Snowflake] | None = attrs.field(default=None)
    """A sequence of sticker IDs cached for this guild.

    This will be [`None`][] if no stickers are cached for this guild.
    """

    invites: typing.MutableSequence[str] | None = attrs.field(default=None)
    """A set of the [`str`][] codes of the invites cached for this guild.

    This will be [`None`][] if no invites are cached for this guild.
    """

    members: collections.ExtendedMutableMapping[snowflakes.Snowflake, RefCell[MemberData]] | None = attrs.field(
        default=None
    )
    """A mapping of user IDs to the objects of members cached for this guild.

    This will be [`None`][] if no members are cached for this guild.
    """

    presences: collections.ExtendedMutableMapping[snowflakes.Snowflake, MemberPresenceData] | None = attrs.field(
        default=None
    )
    """A mapping of user IDs to objects of the presences cached for this guild.

    This will be [`None`][] if no presences are cached for this guild.
    """

    roles: typing.MutableSet[snowflakes.Snowflake] | None = attrs.field(default=None)
    """A set of the IDs of the roles cached for this guild.

    This will be [`None`][] if no roles are cached for this guild.
    """

    voice_states: collections.ExtendedMutableMapping[snowflakes.Snowflake, VoiceStateData] | None = attrs.field(
        default=None
    )
    """A mapping of user IDs to objects of the voice states cached for this guild.

    This will be [`None`][] if no voice states are cached for this guild.
    """

    def empty(self) -> bool:
        """Check whether this guild record has any resources attached to it.

        Returns
        -------
        bool
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
        app
            The hikari application the built object should be bound to.

        Returns
        -------
        ValueT
            The initialised entity object.
        """

    @classmethod
    @abc.abstractmethod
    def build_from_entity(cls, entity: ValueT, /) -> Self:
        """Build a data object from an initialised entity.

        Parameters
        ----------
        entity
            The entity object to build a data class from.

        Returns
        -------
        DataT
            The built data class.
        """


@attrs_extensions.with_copy
@attrs.define(kw_only=True, repr=False, weakref_slot=False)
class InviteData(BaseData[invites.InviteWithMetadata]):
    """A data model for storing invite data in an in-memory cache."""

    code: str = attrs.field()
    guild_id: snowflakes.Snowflake | None = attrs.field()
    channel_id: snowflakes.Snowflake = attrs.field()
    inviter: RefCell[users_.User] | None = attrs.field()
    target_type: invites.TargetType | int | None = attrs.field()
    target_user: RefCell[users_.User] | None = attrs.field()
    target_application: applications.InviteApplication | None = attrs.field()
    uses: int = attrs.field()
    max_uses: int | None = attrs.field()
    max_age: datetime.timedelta | None = attrs.field()
    is_temporary: bool = attrs.field()
    created_at: datetime.datetime = attrs.field()

    @typing_extensions.override
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
    @typing_extensions.override
    def build_from_entity(
        cls,
        invite: invites.InviteWithMetadata,
        /,
        *,
        inviter: RefCell[users_.User] | None = None,
        target_user: RefCell[users_.User] | None = None,
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


@attrs_extensions.with_copy
@attrs.define(kw_only=True, repr=False, weakref_slot=False)
class MemberData(BaseData[guilds.Member]):
    """A data model for storing member data in an in-memory cache."""

    user: RefCell[users_.User] = attrs.field()
    guild_id: snowflakes.Snowflake = attrs.field()
    nickname: str | None = attrs.field()
    guild_avatar_decoration: users_.AvatarDecoration | None = attrs.field()
    guild_avatar_hash: str | None = attrs.field()
    guild_banner_hash: str | None = attrs.field()
    role_ids: tuple[snowflakes.Snowflake, ...] = attrs.field()
    joined_at: datetime.datetime | None = attrs.field()
    premium_since: datetime.datetime | None = attrs.field()
    is_deaf: undefined.UndefinedOr[bool] = attrs.field()
    is_mute: undefined.UndefinedOr[bool] = attrs.field()
    is_pending: undefined.UndefinedOr[bool] = attrs.field()
    raw_communication_disabled_until: datetime.datetime | None = attrs.field()
    guild_flags: guilds.GuildMemberFlags | int = attrs.field()
    # meta-attribute
    has_been_deleted: bool = attrs.field(default=False, init=False)

    @classmethod
    @typing_extensions.override
    def build_from_entity(cls, member: guilds.Member, /, *, user: RefCell[users_.User] | None = None) -> MemberData:
        return cls(
            guild_id=member.guild_id,
            nickname=member.nickname,
            joined_at=member.joined_at,
            premium_since=member.premium_since,
            guild_avatar_decoration=member.guild_avatar_decoration,
            guild_avatar_hash=member.guild_avatar_hash,
            guild_banner_hash=member.guild_banner_hash,
            is_deaf=member.is_deaf,
            is_mute=member.is_mute,
            is_pending=member.is_pending,
            user=user or RefCell(copy.copy(member.user)),
            raw_communication_disabled_until=member.raw_communication_disabled_until,
            guild_flags=member.guild_flags,
            # role_ids is a special case as it may be mutable so we want to ensure it's
            # immutable when cached.
            role_ids=tuple(member.role_ids),
        )

    @typing_extensions.override
    def build_entity(self, _: traits.RESTAware, /) -> guilds.Member:
        return guilds.Member(
            guild_id=self.guild_id,
            nickname=self.nickname,
            role_ids=self.role_ids,
            joined_at=self.joined_at,
            guild_avatar_decoration=self.guild_avatar_decoration,
            guild_avatar_hash=self.guild_avatar_hash,
            guild_banner_hash=self.guild_banner_hash,
            premium_since=self.premium_since,
            is_deaf=self.is_deaf,
            is_mute=self.is_mute,
            is_pending=self.is_pending,
            raw_communication_disabled_until=self.raw_communication_disabled_until,
            user=self.user.copy(),
            guild_flags=self.guild_flags,
        )


@attrs_extensions.with_copy
@attrs.define(kw_only=True, repr=False, weakref_slot=False)
class KnownCustomEmojiData(BaseData[emojis.KnownCustomEmoji]):
    """A data model for storing known custom emoji data in an in-memory cache."""

    id: snowflakes.Snowflake = attrs.field()
    name: str = attrs.field()
    is_animated: bool = attrs.field()
    guild_id: snowflakes.Snowflake = attrs.field()
    role_ids: tuple[snowflakes.Snowflake, ...] = attrs.field()
    user: RefCell[users_.User] | None = attrs.field()
    is_colons_required: bool = attrs.field()
    is_managed: bool = attrs.field()
    is_available: bool = attrs.field()

    @classmethod
    @typing_extensions.override
    def build_from_entity(
        cls, emoji: emojis.KnownCustomEmoji, /, *, user: RefCell[users_.User] | None = None
    ) -> KnownCustomEmojiData:
        if not user and emoji.user:
            user = RefCell(copy.copy(emoji.user))

        # We ensure that all emojis that will get cached are guild based
        assert emoji.guild_id is not None

        return cls(
            id=emoji.id,
            name=emoji.name,
            is_animated=emoji.is_animated,
            guild_id=emoji.guild_id,
            is_colons_required=emoji.is_colons_required,
            is_managed=emoji.is_managed,
            is_available=emoji.is_available,
            user=user,
            # role_ids is a special case as it may be a mutable sequence so we want to ensure it's
            # immutable when cached.
            role_ids=tuple(emoji.role_ids),
        )

    @typing_extensions.override
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


@attrs_extensions.with_copy
@attrs.define(kw_only=True, repr=False, weakref_slot=False)
class GuildStickerData(BaseData[stickers_.GuildSticker]):
    """A data model for storing sticker data in an in-memory cache."""

    id: snowflakes.Snowflake = attrs.field()
    name: str = attrs.field()
    description: str | None = attrs.field()
    tag: str = attrs.field()
    format_type: stickers_.StickerFormatType | int = attrs.field()
    is_available: bool = attrs.field()
    guild_id: snowflakes.Snowflake = attrs.field()
    user: RefCell[users_.User] | None = attrs.field()

    @classmethod
    @typing_extensions.override
    def build_from_entity(
        cls, sticker: stickers_.GuildSticker, /, *, user: RefCell[users_.User] | None = None
    ) -> GuildStickerData:
        if not user and sticker.user:
            user = RefCell(copy.copy(sticker.user))

        return cls(
            id=sticker.id,
            name=sticker.name,
            description=sticker.description,
            guild_id=sticker.guild_id,
            tag=sticker.tag,
            is_available=sticker.is_available,
            format_type=sticker.format_type,
            user=user,
        )

    @typing_extensions.override
    def build_entity(self, app: traits.RESTAware, /) -> stickers_.GuildSticker:
        return stickers_.GuildSticker(
            id=self.id,
            name=self.name,
            description=self.description,
            guild_id=self.guild_id,
            tag=self.tag,
            is_available=self.is_available,
            format_type=self.format_type,
            user=self.user.copy() if self.user else None,
        )


@attrs_extensions.with_copy
@attrs.define(kw_only=True, repr=False, weakref_slot=False)
class RichActivityData(BaseData[presences.RichActivity]):
    """A data model for storing rich activity data in an in-memory cache."""

    name: str = attrs.field()
    url: str | None = attrs.field()
    type: presences.ActivityType | int = attrs.field()
    created_at: datetime.datetime = attrs.field()
    timestamps: presences.ActivityTimestamps | None = attrs.field()
    application_id: snowflakes.Snowflake | None = attrs.field()
    details: str | None = attrs.field()
    state: str | None = attrs.field()
    emoji: RefCell[emojis.CustomEmoji] | str | None = attrs.field()
    party: presences.ActivityParty | None = attrs.field()
    assets: presences.ActivityAssets | None = attrs.field()
    secrets: presences.ActivitySecret | None = attrs.field()
    is_instance: bool | None = attrs.field()
    flags: presences.ActivityFlag | None = attrs.field()
    buttons: tuple[str, ...] = attrs.field()

    @classmethod
    @typing_extensions.override
    def build_from_entity(
        cls, activity: presences.RichActivity, /, *, emoji: RefCell[emojis.CustomEmoji] | str | None = None
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

    @typing_extensions.override
    def build_entity(self, _: traits.RESTAware, /) -> presences.RichActivity:
        emoji: emojis.Emoji | None = None
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


@attrs_extensions.with_copy
@attrs.define(kw_only=True, repr=False, weakref_slot=False)
class MemberPresenceData(BaseData[presences.MemberPresence]):
    """A data model for storing presence data in an in-memory cache."""

    user_id: snowflakes.Snowflake = attrs.field()
    guild_id: snowflakes.Snowflake = attrs.field()
    visible_status: presences.Status | str = attrs.field()
    activities: tuple[RichActivityData, ...] = attrs.field()
    client_status: presences.ClientStatus = attrs.field()

    @classmethod
    @typing_extensions.override
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

    @typing_extensions.override
    def build_entity(self, app: traits.RESTAware, /) -> presences.MemberPresence:
        return presences.MemberPresence(
            user_id=self.user_id,
            guild_id=self.guild_id,
            visible_status=self.visible_status,
            app=app,
            activities=[activity.build_entity(app) for activity in self.activities],
            client_status=copy.copy(self.client_status),
        )


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


@attrs_extensions.with_copy
@attrs.define(kw_only=True, repr=False, weakref_slot=False)
class MessageData(BaseData[messages.Message]):
    """A model for storing message data in an in-memory cache."""

    id: snowflakes.Snowflake = attrs.field()
    channel_id: snowflakes.Snowflake = attrs.field()
    guild_id: snowflakes.Snowflake | None = attrs.field()
    author: RefCell[users_.User] = attrs.field()
    member: RefCell[MemberData] | None = attrs.field()
    content: str | None = attrs.field()
    timestamp: datetime.datetime = attrs.field()
    edited_timestamp: datetime.datetime | None = attrs.field()
    is_tts: bool = attrs.field()
    user_mentions: undefined.UndefinedOr[typing.Mapping[snowflakes.Snowflake, RefCell[users_.User]]] = attrs.field()
    role_mention_ids: undefined.UndefinedOr[tuple[snowflakes.Snowflake, ...]] = attrs.field()
    channel_mentions: undefined.UndefinedOr[typing.Mapping[snowflakes.Snowflake, channels_.PartialChannel]] = (
        attrs.field()
    )
    mentions_everyone: undefined.UndefinedOr[bool] = attrs.field()
    attachments: tuple[messages.Attachment, ...] = attrs.field()
    embeds: tuple[embeds_.Embed, ...] = attrs.field()
    reactions: tuple[messages.Reaction, ...] = attrs.field()
    poll: polls_.Poll | None = attrs.field()
    is_pinned: bool = attrs.field()
    webhook_id: snowflakes.Snowflake | None = attrs.field()
    type: messages.MessageType | int = attrs.field()
    activity: messages.MessageActivity | None = attrs.field()
    application: messages.MessageApplication | None = attrs.field()
    message_reference: messages.MessageReference | None = attrs.field()
    flags: messages.MessageFlag = attrs.field()
    stickers: tuple[stickers_.PartialSticker, ...] = attrs.field()
    nonce: str | None = attrs.field()
    referenced_message: RefCell[MessageData] | None = attrs.field()
    message_snapshots: tuple[messages.MessageSnapshot, ...] = attrs.field()
    application_id: snowflakes.Snowflake | None = attrs.field()
    components: tuple[components_.TopLevelComponentTypesT, ...] = attrs.field()
    thread: channels_.GuildThreadChannel | None = attrs.field()
    interaction_metadata: base_interactions.PartialInteractionMetadata | None = attrs.field()

    @classmethod
    @typing_extensions.override
    def build_from_entity(
        cls,
        message: messages.Message,
        /,
        *,
        author: RefCell[users_.User] | None = None,
        member: RefCell[MemberData] | None = None,
        user_mentions: undefined.UndefinedOr[
            typing.Mapping[snowflakes.Snowflake, RefCell[users_.User]]
        ] = undefined.UNDEFINED,
        referenced_message: RefCell[MessageData] | None = None,
    ) -> MessageData:
        if not member and message.member:
            member = RefCell(MemberData.build_from_entity(message.member))

        if not user_mentions and message.user_mentions is not undefined.UNDEFINED:
            user_mentions = {user_id: RefCell(copy.copy(user)) for user_id, user in message.user_mentions.items()}

        channel_mentions: undefined.UndefinedOr[typing.Mapping[snowflakes.Snowflake, channels_.PartialChannel]] = (
            {channel_id: copy.copy(channel) for channel_id, channel in message.channel_mentions.items()}
            if message.channel_mentions is not undefined.UNDEFINED
            else undefined.UNDEFINED
        )
        role_mention_ids: undefined.UndefinedOr[tuple[snowflakes.Snowflake, ...]] = (
            tuple(message.role_mention_ids)
            if message.role_mention_ids is not undefined.UNDEFINED
            else undefined.UNDEFINED
        )

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
            user_mentions=user_mentions,
            channel_mentions=channel_mentions,
            role_mention_ids=role_mention_ids,
            mentions_everyone=message.mentions_everyone,
            attachments=tuple(map(copy.copy, message.attachments)),
            embeds=tuple(map(_copy_embed, message.embeds)),
            poll=message.poll,
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
            message_snapshots=tuple(map(copy.copy, message.message_snapshots)),
            application_id=message.application_id,
            components=tuple(message.components),
            thread=message.thread,
            interaction_metadata=message.interaction_metadata,
        )

    @typing_extensions.override
    def build_entity(self, app: traits.RESTAware, /) -> messages.Message:
        channel_mentions: undefined.UndefinedOr[typing.Mapping[snowflakes.Snowflake, channels_.PartialChannel]] = (
            {channel_id: copy.copy(channel) for channel_id, channel in self.channel_mentions.items()}
            if self.channel_mentions is not undefined.UNDEFINED
            else undefined.UNDEFINED
        )
        user_mentions: undefined.UndefinedOr[typing.Mapping[snowflakes.Snowflake, users_.User]] = (
            {user_id: user.copy() for user_id, user in self.user_mentions.items()}
            if self.user_mentions is not undefined.UNDEFINED
            else undefined.UNDEFINED
        )

        return messages.Message(
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
            user_mentions=user_mentions,
            channel_mentions=channel_mentions,
            role_mention_ids=copy.copy(self.role_mention_ids),
            mentions_everyone=self.mentions_everyone,
            attachments=tuple(map(copy.copy, self.attachments)),
            embeds=tuple(map(_copy_embed, self.embeds)),
            poll=self.poll,
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
            referenced_message=self.referenced_message.object.build_entity(app) if self.referenced_message else None,
            message_snapshots=self.message_snapshots,
            application_id=self.application_id,
            components=self.components,
            thread=self.thread,
            interaction_metadata=self.interaction_metadata,
        )

    def update(
        self,
        message: messages.PartialMessage,
        /,
        *,
        user_mentions: undefined.UndefinedOr[
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

        if user_mentions is not undefined.UNDEFINED:
            self.user_mentions = user_mentions
        elif message.user_mentions is not undefined.UNDEFINED:
            self.user_mentions = {user_id: RefCell(copy.copy(user)) for user_id, user in message.user_mentions.items()}

        if message.role_mention_ids is not undefined.UNDEFINED:
            self.role_mention_ids = tuple(message.role_mention_ids)

        if message.channel_mentions is not undefined.UNDEFINED:
            self.channel_mentions = {
                channel_id: copy.copy(channel) for channel_id, channel in message.channel_mentions.items()
            }

        if message.mentions_everyone is not undefined.UNDEFINED:
            self.mentions_everyone = message.mentions_everyone


@attrs_extensions.with_copy
@attrs.define(kw_only=True, repr=False, weakref_slot=False)
class VoiceStateData(BaseData[voices.VoiceState]):
    """A data model for storing voice state data in an in-memory cache."""

    channel_id: snowflakes.Snowflake | None = attrs.field()
    guild_id: snowflakes.Snowflake = attrs.field()
    user_id: snowflakes.Snowflake = attrs.field()
    is_guild_deafened: bool = attrs.field()
    is_guild_muted: bool = attrs.field()
    is_self_deafened: bool = attrs.field()
    is_self_muted: bool = attrs.field()
    is_streaming: bool = attrs.field()
    is_suppressed: bool = attrs.field()
    is_video_enabled: bool = attrs.field()
    member: RefCell[MemberData] | None = attrs.field()
    session_id: str = attrs.field()
    requested_to_speak_at: datetime.datetime | None = attrs.field()

    @typing_extensions.override
    def build_entity(self, app: traits.RESTAware, /) -> voices.VoiceState:
        member = self.member.object.build_entity(app) if self.member else None
        return voices.VoiceState(
            app=app,
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
            member=member,
            requested_to_speak_at=self.requested_to_speak_at,
        )

    @classmethod
    @typing_extensions.override
    def build_from_entity(
        cls, voice_state: voices.VoiceState, /, *, member: RefCell[MemberData] | None = None
    ) -> VoiceStateData:
        return cls(
            channel_id=voice_state.channel_id,
            guild_id=voice_state.guild_id,
            user_id=voice_state.user_id,
            is_self_deafened=voice_state.is_self_deafened,
            is_self_muted=voice_state.is_self_muted,
            is_guild_deafened=voice_state.is_guild_deafened,
            is_guild_muted=voice_state.is_guild_muted,
            is_streaming=voice_state.is_streaming,
            is_suppressed=voice_state.is_suppressed,
            is_video_enabled=voice_state.is_video_enabled,
            member=member,
            session_id=voice_state.session_id,
            requested_to_speak_at=voice_state.requested_to_speak_at,
        )


@attrs_extensions.with_copy
@attrs.define(repr=True, weakref_slot=True)
class Cell(typing.Generic[ValueT]):
    """Object used to store mutable references to a value in multiple places."""

    object: ValueT = attrs.field(repr=True)

    def copy(self) -> ValueT:
        """Get a copy of the contents of this cell.

        Returns
        -------
        ValueT
            The copied contents of this cell.
        """
        return copy.copy(self.object)


@attrs_extensions.with_copy
@attrs.define(repr=False, weakref_slot=False)
class RefCell(typing.Generic[ValueT]):
    """Object used to track mutable references to a value in multiple places.

    This is intended to enable reference counting for entities that are only kept
    alive by reference (e.g. the unknown emoji objects attached to presence
    activities and user objects) without the use of a "Data" object which lowers
    the time spent building these entities for the objects that reference them.
    """

    object: ValueT = attrs.field(repr=True)
    ref_count: int = attrs.field(default=0, kw_only=True)

    def copy(self) -> ValueT:
        """Get a copy of the contents of this cell.

        Returns
        -------
        ValueT
            The copied contents of this cell.
        """
        return copy.copy(self.object)


def unwrap_ref_cell(cell: RefCell[ValueT]) -> ValueT:
    """Unwrap a [`RefCell`][] instance to it's contents.

    Parameters
    ----------
    cell
        The reference cell instance to unwrap.

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
    @typing_extensions.override
    def _copy(value: cache.CacheView[KeyT, ValueT]) -> cache.CacheView[KeyT, ValueT]:
        return value
