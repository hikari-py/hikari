# -*- coding: utf-8 -*-
# cython: language_level=3
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
"""Application and entities that are used to describe audit logs on Discord."""

from __future__ import annotations

__all__: typing.Sequence[str] = (
    "AuditLog",
    "AuditLogChange",
    "AuditLogChangeKey",
    "AuditLogEntry",
    "AuditLogEventType",
    "BaseAuditLogEntryInfo",
    "ChannelOverwriteEntryInfo",
    "MemberDisconnectEntryInfo",
    "MemberMoveEntryInfo",
    "MemberPruneEntryInfo",
    "MessageBulkDeleteEntryInfo",
    "MessageDeleteEntryInfo",
    "MessagePinEntryInfo",
)

import abc
import typing

import attrs

from hikari import channels
from hikari import snowflakes
from hikari.internal import attrs_extensions
from hikari.internal import collections
from hikari.internal import enums

if typing.TYPE_CHECKING:
    import datetime

    from hikari import guilds
    from hikari import messages
    from hikari import traits
    from hikari import users as users_
    from hikari import webhooks as webhooks_


@typing.final
class AuditLogChangeKey(str, enums.Enum):
    """Commonly known and documented keys for audit log change objects.

    Others may exist. These should be expected to default to the raw string
    Discord provided us. These are defined for documentation purposes and
    can be treated as regular strings for all other purposes.
    """

    NAME = "name"
    """Name."""

    DESCRIPTION = "description"
    """Description."""

    ICON_HASH = "icon_hash"
    """Icon Hash."""

    SPLASH_HASH = "splash_hash"
    """Splash Hash."""

    DISCOVERY_SPLASH_HASH = "discovery_splash_hash"
    """Discovery Splash Hash."""

    BANNER_HASH = "banner_hash"
    """Banner Hash."""

    OWNER_ID = "owner_id"
    """Owner ID."""

    REGION = "region"  # TODO: remove when this disappears for the most part
    """Region."""

    PREFERRED_LOCALE = "preferred_locale"
    """Preferred Locale."""

    RTC_REGION = "rtc_region"
    """RTC Region."""

    AFK_CHANNEL_ID = "afk_channel_id"
    """Afk Channel ID."""

    AFK_TIMEOUT = "afk_timeout"
    """Afk Timeout."""

    RULES_CHANNEL_ID = "rules_channel_id"
    """Rules Channel ID."""

    PUBLIC_UPDATES_CHANNEL_ID = "public_updates_channel_id"
    """Public Updates Channel ID."""

    MFA_LEVEL = "mfa_level"
    """Mfa Level."""

    VERIFICATION_LEVEL = "verification_level"
    """Verification Level."""

    EXPLICIT_CONTENT_FILTER = "explicit_content_filter"
    """Explicit Content Filter."""

    DEFAULT_MESSAGE_NOTIFICATIONS = "default_message_notifications"
    """Default Message Notifications."""

    VANITY_URL_CODE = "vanity_url_code"
    """Vanity Url Code."""

    PRUNE_DELETE_DAYS = "prune_delete_days"
    """Prune Delete Days."""

    WIDGET_ENABLED = "widget_enabled"
    """Widget Enabled."""

    WIDGET_CHANNEL_ID = "widget_channel_id"
    """Widget Channel ID."""

    POSITION = "position"
    """Position."""

    TOPIC = "topic"
    """Topic."""

    BITRATE = "bitrate"
    """Bitrate."""

    DEFAULT_AUTO_ARCHIVE_DURATION = "default_auto_archive_duration"
    """Default Auto Archive Duration."""

    PERMISSION_OVERWRITES = "permission_overwrites"
    """Permission Overwrites."""

    NSFW = "nsfw"
    """Nsfw."""

    APPLICATION_ID = "application_id"
    """Application ID."""

    ARCHIVED = "archived"
    """Archived."""

    AUTO_ARCHIVE_DURATION = "auto_archive_duration"
    """Auto Archive Duration."""

    PERMISSIONS = "permissions"
    """Permissions."""

    USER_LIMIT = "user_limit"
    """User Limit."""

    COLOR = "color"
    """Color."""

    COMMAND_ID = "command_id"
    """Command ID."""

    HOIST = "hoist"
    """Hoist."""

    MENTIONABLE = "mentionable"
    """Mentionable."""

    ALLOW = "allow"
    """Allow."""

    DENY = "deny"
    """Deny."""

    INVITE_CODE = "code"
    """Code."""

    CHANNEL_ID = "channel_id"
    """Channel ID."""

    INVITER_ID = "inviter_id"
    """Inviter ID."""

    MAX_USES = "max_uses"
    """Max Uses."""

    USES = "uses"
    """Uses."""

    MAX_AGE = "max_age"
    """Max Age."""

    TEMPORARY = "temporary"
    """Temporary."""

    DEAF = "deaf"
    """Deaf."""

    MUTE = "mute"
    """Mute."""

    NICK = "nick"
    """Nick."""

    AVATAR_HASH = "avatar_hash"
    """Avatar Hash."""

    ID = "id"
    """ID."""

    INVITABLE = "invitable"
    """Invitable."""

    LOCKED = "locked"
    """Locked."""

    TYPE = "type"
    """Type."""

    ENABLE_EMOTICONS = "enable_emoticons"
    """Enable Emoticons."""

    EXPIRE_BEHAVIOR = "expire_behavior"
    """Expire Behavior."""

    EXPIRE_GRACE_PERIOD = "expire_grace_period"
    """Expire Grace Period."""

    RATE_LIMIT_PER_USER = "rate_limit_per_user"
    """Rate Limit Per User."""

    SYSTEM_CHANNEL_ID = "system_channel_id"
    """System Channel ID."""

    TAGS = "tags"
    """Tags."""

    FORMAT_TYPE = "format_type"
    """Format Type."""

    ASSETS = "asset"
    """Asset."""

    AVAILABLE = "available"
    """Available."""

    GUILD_ID = "guild_id"
    """Guild ID."""

    # Who needs consistency?
    ADD_ROLE_TO_MEMBER = "$add"
    """Role added to a member."""

    REMOVE_ROLE_FROM_MEMBER = "$remove"
    """Role removed from a member."""

    COLOUR = COLOR
    """Alias for [`hikari.audit_logs.AuditLogChangeKey.COLOR`][]."""


@attrs_extensions.with_copy
@attrs.define(hash=False, kw_only=True, weakref_slot=False)
class AuditLogChange:
    """Represents a change made to an audit log entry's target entity."""

    new_value: typing.Optional[typing.Any] = attrs.field(repr=True)
    """The new value of the key, if something was added or changed."""

    old_value: typing.Optional[typing.Any] = attrs.field(repr=True)
    """The old value of the key, if something was removed or changed."""

    key: typing.Union[AuditLogChangeKey, str] = attrs.field(repr=True)
    """The name of the audit log change's key."""


@typing.final
class AuditLogEventType(int, enums.Enum):
    """The type of event that occurred."""

    GUILD_UPDATE = 1
    CHANNEL_CREATE = 10
    CHANNEL_UPDATE = 11
    CHANNEL_DELETE = 12
    CHANNEL_OVERWRITE_CREATE = 13
    CHANNEL_OVERWRITE_UPDATE = 14
    CHANNEL_OVERWRITE_DELETE = 15
    MEMBER_KICK = 20
    MEMBER_PRUNE = 21
    MEMBER_BAN_ADD = 22
    MEMBER_BAN_REMOVE = 23
    MEMBER_UPDATE = 24
    MEMBER_ROLE_UPDATE = 25
    MEMBER_MOVE = 26
    MEMBER_DISCONNECT = 27
    BOT_ADD = 28
    ROLE_CREATE = 30
    ROLE_UPDATE = 31
    ROLE_DELETE = 32
    INVITE_CREATE = 40
    INVITE_UPDATE = 41
    INVITE_DELETE = 42
    WEBHOOK_CREATE = 50
    WEBHOOK_UPDATE = 51
    WEBHOOK_DELETE = 52
    EMOJI_CREATE = 60
    EMOJI_UPDATE = 61
    EMOJI_DELETE = 62
    MESSAGE_DELETE = 72
    MESSAGE_BULK_DELETE = 73
    MESSAGE_PIN = 74
    MESSAGE_UNPIN = 75
    INTEGRATION_CREATE = 80
    INTEGRATION_UPDATE = 81
    INTEGRATION_DELETE = 82
    STICKER_CREATE = 90
    STICKER_UPDATE = 91
    STICKER_DELETE = 92
    GUILD_SCHEDULED_EVENT_CREATE = 100
    GUILD_SCHEDULED_EVENT_UPDATE = 101
    GUILD_SCHEDULED_EVENT_DELETE = 102
    APPLICATION_COMMAND_PERMISSION_UPDATE = 121
    THREAD_CREATE = 110
    THREAD_UPDATE = 111
    THREAD_DELETE = 112
    CREATOR_MONETIZATION_REQUEST_CREATED = 150
    CREATOR_MONETIZATION_TERMS_ACCEPTED = 151


@attrs.define(hash=False, kw_only=True, weakref_slot=False)
class BaseAuditLogEntryInfo(abc.ABC):
    """A base object that all audit log entry info objects will inherit from."""

    app: traits.RESTAware = attrs.field(repr=False, eq=False, metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    """Client application that models may use for procedures."""


@attrs_extensions.with_copy
@attrs.define(hash=False, kw_only=True, weakref_slot=False)
class ChannelOverwriteEntryInfo(BaseAuditLogEntryInfo, snowflakes.Unique):
    """Represents the extra information for overwrite related audit log entries.

    Will be attached to the overwrite create, update and delete audit log
    entries.
    """

    id: snowflakes.Snowflake = attrs.field(hash=True, repr=True)
    """The ID of this entity."""

    type: typing.Union[channels.PermissionOverwriteType, str] = attrs.field(repr=True)
    """The type of entity this overwrite targets."""

    role_name: typing.Optional[str] = attrs.field(repr=True)
    """The name of the role this overwrite targets, if it targets a role."""


@attrs_extensions.with_copy
@attrs.define(hash=False, kw_only=True, weakref_slot=False)
class MessagePinEntryInfo(BaseAuditLogEntryInfo):
    """The extra information for message pin related audit log entries.

    Will be attached to the message pin and message unpin audit log entries.
    """

    channel_id: snowflakes.Snowflake = attrs.field(repr=True)
    """The ID of the text based channel where a pinned message is being targeted."""

    message_id: snowflakes.Snowflake = attrs.field(repr=True)
    """The ID of the message that's being pinned or unpinned."""

    async def fetch_channel(self) -> channels.TextableChannel:
        """Fetch The channel where this message was pinned or unpinned.

        Returns
        -------
        hikari.channels.TextableChannel
            The channel where this message was pinned or unpinned.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.VIEW_CHANNEL`][] permission in the channel.
        hikari.errors.NotFoundError
            If the channel is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        channel = await self.app.rest.fetch_channel(self.channel_id)
        assert isinstance(channel, channels.TextableChannel)
        return channel

    async def fetch_message(self) -> messages.Message:
        """Fetch the object of the message that's being pinned or unpinned.

        Returns
        -------
        hikari.messages.Message
            The message that's being pinned or unpinned.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.VIEW_CHANNEL`][]
            permission in the channel that the message is in.
        hikari.errors.NotFoundError
            If the message is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        return await self.app.rest.fetch_message(self.channel_id, self.message_id)


@attrs_extensions.with_copy
@attrs.define(hash=False, kw_only=True, weakref_slot=False)
class MemberPruneEntryInfo(BaseAuditLogEntryInfo):
    """Extra information attached to guild prune log entries."""

    delete_member_days: datetime.timedelta = attrs.field(repr=True)
    """The timedelta of how many days members were pruned for inactivity based on."""

    members_removed: int = attrs.field(repr=True)
    """The number of members who were removed by this prune."""


@attrs_extensions.with_copy
@attrs.define(hash=False, kw_only=True, weakref_slot=False)
class MessageBulkDeleteEntryInfo(BaseAuditLogEntryInfo):
    """Extra information for the message bulk delete audit entry."""

    count: int = attrs.field(repr=True)
    """The amount of messages that were deleted."""


@attrs_extensions.with_copy
@attrs.define(hash=False, kw_only=True, weakref_slot=False)
class MessageDeleteEntryInfo(MessageBulkDeleteEntryInfo):
    """Extra information attached to the message delete audit entry."""

    channel_id: snowflakes.Snowflake = attrs.field(repr=True)
    """The ID of guild text based channel where these message(s) were deleted."""

    async def fetch_channel(self) -> channels.TextableGuildChannel:
        """Fetch the guild text based channel where these message(s) were deleted.

        Returns
        -------
        hikari.channels.TextableGuildChannel
            The guild text based channel where these message(s) were deleted.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.VIEW_CHANNEL`][] permission in the channel.
        hikari.errors.NotFoundError
            If the channel is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        channel = await self.app.rest.fetch_channel(self.channel_id)
        assert isinstance(channel, channels.TextableGuildChannel)
        return channel


@attrs_extensions.with_copy
@attrs.define(hash=False, kw_only=True, weakref_slot=False)
class MemberDisconnectEntryInfo(BaseAuditLogEntryInfo):
    """Extra information for the voice chat member disconnect entry."""

    count: int = attrs.field(repr=True)
    """The amount of members who were disconnected from voice in this entry."""


@attrs_extensions.with_copy
@attrs.define(hash=False, kw_only=True, weakref_slot=False)
class MemberMoveEntryInfo(MemberDisconnectEntryInfo):
    """Extra information for the voice chat based member move entry."""

    channel_id: snowflakes.Snowflake = attrs.field(repr=True)
    """The channel that the member(s) have been moved to."""

    async def fetch_channel(self) -> channels.GuildVoiceChannel:
        """Fetch the guild voice based channel where the member(s) have been moved to.

        Returns
        -------
        hikari.channels.GuildVoiceChannel
            The guild voice based channel where the member(s) have been moved to.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.VIEW_CHANNEL`][] permission in the channel.
        hikari.errors.NotFoundError
            If the channel is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        channel = await self.app.rest.fetch_channel(self.channel_id)
        assert isinstance(channel, channels.GuildVoiceChannel)
        return channel


@attrs_extensions.with_copy
@attrs.define(hash=True, kw_only=True, weakref_slot=False)
class AuditLogEntry(snowflakes.Unique):
    """Represents an entry in a guild's audit log."""

    app: traits.RESTAware = attrs.field(
        repr=False, eq=False, hash=False, metadata={attrs_extensions.SKIP_DEEP_COPY: True}
    )
    """Client application that models may use for procedures."""

    id: snowflakes.Snowflake = attrs.field(hash=True, repr=True)
    """The ID of this entity."""

    guild_id: snowflakes.Snowflake = attrs.field(eq=False, hash=False, repr=True)
    """ID of the guild this audit log entry is for."""

    target_id: typing.Optional[snowflakes.Snowflake] = attrs.field(eq=False, hash=False, repr=True)
    """The ID of the entity affected by this change, if applicable."""

    changes: typing.Sequence[AuditLogChange] = attrs.field(eq=False, hash=False, repr=False)
    """A sequence of the changes made to [`hikari.audit_logs.AuditLogEntry.target_id`][]."""

    user_id: typing.Optional[snowflakes.Snowflake] = attrs.field(eq=False, hash=False, repr=True)
    """The ID of the user who made this change."""

    action_type: typing.Union[AuditLogEventType, int] = attrs.field(eq=False, hash=False, repr=True)
    """The type of action this entry represents."""

    options: typing.Optional[BaseAuditLogEntryInfo] = attrs.field(eq=False, hash=False, repr=False)
    """Extra information about this entry. Only be provided for certain `event_type`."""

    reason: typing.Optional[str] = attrs.field(eq=False, hash=False, repr=False)
    """The reason for this change, if set (between 0-512 characters)."""

    async def fetch_user(self) -> typing.Optional[users_.User]:
        """Fetch the user who made this change.

        Returns
        -------
        typing.Optional[hikari.users.User]
            The user who made this change, if available.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the user is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        if self.user_id is None:
            return None
        return await self.app.rest.fetch_user(self.user_id)


@attrs_extensions.with_copy
@attrs.define(hash=False, kw_only=True, repr=False, weakref_slot=False)
class AuditLog(typing.Sequence[AuditLogEntry]):
    """Represents a guilds audit log's page."""

    entries: typing.Mapping[snowflakes.Snowflake, AuditLogEntry] = attrs.field(repr=False)
    """A mapping of snowflake IDs to the audit log's entries."""

    integrations: typing.Mapping[snowflakes.Snowflake, guilds.PartialIntegration] = attrs.field(repr=False)
    """A mapping of the partial objects of integrations found in this audit log."""

    threads: typing.Mapping[snowflakes.Snowflake, channels.GuildThreadChannel] = attrs.field(repr=False)
    """A mapping of the objects of threads found in this audit log."""

    users: typing.Mapping[snowflakes.Snowflake, users_.User] = attrs.field(repr=False)
    """A mapping of the objects of users found in this audit log."""

    webhooks: typing.Mapping[snowflakes.Snowflake, webhooks_.PartialWebhook] = attrs.field(repr=False)
    """A mapping of the objects of webhooks found in this audit log."""

    @typing.overload
    def __getitem__(self, index: int, /) -> AuditLogEntry: ...

    @typing.overload
    def __getitem__(self, slice_: slice, /) -> typing.Sequence[AuditLogEntry]: ...

    def __getitem__(
        self, index_or_slice: typing.Union[int, slice], /
    ) -> typing.Union[AuditLogEntry, typing.Sequence[AuditLogEntry]]:
        return collections.get_index_or_slice(self.entries, index_or_slice)

    def __iter__(self) -> typing.Iterator[AuditLogEntry]:
        return iter(self.entries.values())

    def __len__(self) -> int:
        return len(self.entries)
