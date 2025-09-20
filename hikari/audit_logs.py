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

import typing

import attrs

from hikari import channels
from hikari import snowflakes
from hikari.internal import attrs_extensions
from hikari.internal import collections
from hikari.internal import enums
from hikari.internal import typing_extensions

if typing.TYPE_CHECKING:
    import datetime

    from hikari import auto_mod
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

    COMMUNICATION_DISABLED_UNTIL = "communication_disabled_until"
    """The datetime when a timeout will expire."""

    # Who needs consistency?
    ADD_ROLE_TO_MEMBER = "$add"
    """Role added to a member."""

    REMOVE_ROLE_FROM_MEMBER = "$remove"
    """Role removed from a member."""

    COLOUR = COLOR
    """Alias for [`hikari.audit_logs.AuditLogChangeKey.COLOR`][]."""


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
class AuditLogChange:
    """Represents a change made to an audit log entry's target entity."""

    new_value: typing.Any | None = attrs.field(repr=True)
    """The new value of the key, if something was added or changed."""

    old_value: typing.Any | None = attrs.field(repr=True)
    """The old value of the key, if something was removed or changed."""

    key: AuditLogChangeKey | str = attrs.field(repr=True)
    """The name of the audit log change's key."""


@typing.final
class AuditLogEventType(int, enums.Enum):
    """The type of event that occurred."""

    GUILD_UPDATE = 1
    """Indicates that guild settings were updated."""

    CHANNEL_CREATE = 10
    """Indicates that a channel was created."""

    CHANNEL_UPDATE = 11
    """Indicates that a channel's settings were updated."""

    CHANNEL_DELETE = 12
    """Indicates that a channel was deleted."""

    CHANNEL_OVERWRITE_CREATE = 13
    """Indicates that a permission overwrite was added to a channel."""

    CHANNEL_OVERWRITE_UPDATE = 14
    """Indicates that a permission overwrite was updated for a channel."""

    CHANNEL_OVERWRITE_DELETE = 15
    """Indicates that a permission overwrite was deleted from a channel."""

    MEMBER_KICK = 20
    """Indicates that a member was kicked from guild."""

    MEMBER_PRUNE = 21
    """Indicates that members were pruned from guild."""

    MEMBER_BAN_ADD = 22
    """Indicates that a member was banned from guild."""

    MEMBER_BAN_REMOVE = 23
    """Indicates that guild ban was lifted for a member."""

    MEMBER_UPDATE = 24
    """Indicates that a member was updated in guild."""

    MEMBER_ROLE_UPDATE = 25
    """Indicates that a member was added or removed from a role."""

    MEMBER_MOVE = 26
    """Indicates that a member was moved to a different voice channel."""

    MEMBER_DISCONNECT = 27
    """Indicates that a member was disconnected from a voice channel."""

    BOT_ADD = 28
    """Indicates a bot user was added to guild."""

    ROLE_CREATE = 30
    """Indicates that a role was created."""

    ROLE_UPDATE = 31
    """Indicates that a role was edited."""

    ROLE_DELETE = 32
    """Indicates that a role was deleted."""

    INVITE_CREATE = 40
    """Indicates that a guild invite was created."""

    INVITE_UPDATE = 41
    """Indicates that a guild invite was updated."""

    INVITE_DELETE = 42
    """Indicates that a guild invite was deleted."""

    WEBHOOK_CREATE = 50
    """Indicates that a webhook was created."""

    WEBHOOK_UPDATE = 51
    """Indicates that a webhook properties or channel were updated."""

    WEBHOOK_DELETE = 52
    """Indicates that a webhook was deleted."""

    EMOJI_CREATE = 60
    """Indicates that an emoji was created."""

    EMOJI_UPDATE = 61
    """Indicates that an emoji name was updated."""

    EMOJI_DELETE = 62
    """Indicates that an emoji was deleted."""

    MESSAGE_DELETE = 72
    """Indicates that a single message was deleted."""

    MESSAGE_BULK_DELETE = 73
    """Indicates that multiple messages were deleted."""

    MESSAGE_PIN = 74
    """Indicates that a message was pinned to a channel."""

    MESSAGE_UNPIN = 75
    """Indicates that a message was unpinned from a channel."""

    INTEGRATION_CREATE = 80
    """Indicates that an app was added to guild."""

    INTEGRATION_UPDATE = 81
    """Indicates that an app was updated (i.e., it's scopes were updated)."""

    INTEGRATION_DELETE = 82
    """Indicates that an app was removed from guild."""

    STAGE_INSTANCE_CREATE = 83
    """Indicates that a stage instance was created (stage channel went live)."""

    STAGE_INSTANCE_UPDATE = 84
    """Indicates that a stage instance's details were updated."""

    STAGE_INSTANCE_DELETE = 85
    """Indicates that a stage instance was deleted (stage channel no longer live)."""

    STICKER_CREATE = 90
    """Indicates that a sticker was created."""

    STICKER_UPDATE = 91
    """Indicates that a sticker's details were updated."""

    STICKER_DELETE = 92
    """Indicates that a sticker was deleted."""

    GUILD_SCHEDULED_EVENT_CREATE = 100
    """Indicates that a guild event was created"""

    GUILD_SCHEDULED_EVENT_UPDATE = 101
    """Indicates that a guild event was updated."""

    GUILD_SCHEDULED_EVENT_DELETE = 102
    """Indicates thata guild event was cancelled."""

    THREAD_CREATE = 110
    """Indicates that a thread was created in a channel."""

    THREAD_UPDATE = 111
    """Indicates that a thread was updated."""

    THREAD_DELETE = 112
    """Indicates that a thread was deleted."""

    APPLICATION_COMMAND_PERMISSION_UPDATE = 121
    """Indicates that permissions were updated for a command."""

    SOUNDBOARD_SOUND_CREATE = 130
    """Indicates that a soundboard sound was created."""

    SOUNDBOARD_SOUND_UPDATE = 131
    """Indicates that a soundboard sound was updated"""

    SOUNDBOARD_SOUND_DELETE = 132
    """Indicates that a soundboard sound was deleted."""

    AUTO_MODERATION_RULE_CREATE = 140
    """Indicates that an automod rule was created."""

    AUTO_MODERATION_RULE_UPDATE = 141
    """Indicates that an automod rule was updated."""

    AUTO_MODERATION_RULE_DELETE = 142
    """Indicates that an automod rule was deleted."""

    AUTO_MODERATION_BLOCK_MESSAGE = 143
    """Indicates that a message was blocked by automod."""

    AUTO_MODERATION_FLAG_TO_CHANNEL = 144
    """Indicates that a message was flagged by automod."""

    AUTO_MODERATION_USER_COMMUNICATION_DISABLED = 145
    """Indicates that a member was timed out by automod."""

    CREATOR_MONETIZATION_REQUEST_CREATED = 150
    """Indicates that creator monetization request was created."""

    CREATOR_MONETIZATION_TERMS_ACCEPTED = 151
    """Indicates that creator monetization terms were accepted."""

    ONBOARDING_PROMPT_CREATE = 163
    """Indicates that a guild onboarding question was created."""

    ONBOARDING_PROMPT_UPDATE = 164
    """Indicates that a guild onboarding question was updated."""

    ONBOARDING_PROMPT_DELETE = 165
    """Indicates that a guild onboarding question was deleted."""

    ONBOARDING_CREATE = 166
    """Indicates that guild onboarding was created."""

    ONBOARDING_UPDATE = 167
    """Indicates that guild onboarding was updated."""

    HOME_SETTINGS_CREATE = 190
    """Indicates that guild server guide was created."""

    HOME_SETTINGS_UPDATE = 191
    """Indicates that guild server guide was uodated."""


@attrs.define(kw_only=True, weakref_slot=False)
class BaseAuditLogEntryInfo:
    """A base object that all audit log entry info objects will inherit from."""

    app: traits.RESTAware = attrs.field(repr=False, eq=False, metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    """Client application that models may use for procedures."""


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
class ChannelOverwriteEntryInfo(BaseAuditLogEntryInfo, snowflakes.Unique):
    """Represents the extra information for overwrite related audit log entries.

    Will be attached to the overwrite create, update and delete audit log
    entries.
    """

    id: snowflakes.Snowflake = attrs.field(hash=True, repr=True)
    """The ID of this entity."""

    type: channels.PermissionOverwriteType | int = attrs.field(repr=True)
    """The type of entity this overwrite targets."""

    role_name: str | None = attrs.field(repr=True)
    """The name of the role this overwrite targets, if it targets a role."""


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
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
@attrs.define(kw_only=True, weakref_slot=False)
class MemberPruneEntryInfo(BaseAuditLogEntryInfo):
    """Extra information attached to guild prune log entries."""

    delete_member_days: datetime.timedelta = attrs.field(repr=True)
    """The timedelta of how many days members were pruned for inactivity based on."""

    members_removed: int = attrs.field(repr=True)
    """The number of members who were removed by this prune."""


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
class MessageBulkDeleteEntryInfo(BaseAuditLogEntryInfo):
    """Extra information for the message bulk delete audit entry."""

    count: int = attrs.field(repr=True)
    """The amount of messages that were deleted."""


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
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
@attrs.define(kw_only=True, weakref_slot=False)
class MemberDisconnectEntryInfo(BaseAuditLogEntryInfo):
    """Extra information for the voice chat member disconnect entry."""

    count: int = attrs.field(repr=True)
    """The amount of members who were disconnected from voice in this entry."""


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
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
@attrs.define(unsafe_hash=True, kw_only=True, weakref_slot=False)
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

    target_id: snowflakes.Snowflake | None = attrs.field(eq=False, hash=False, repr=True)
    """The ID of the entity affected by this change, if applicable."""

    changes: typing.Sequence[AuditLogChange] = attrs.field(eq=False, hash=False, repr=False)
    """A sequence of the changes made to [`hikari.audit_logs.AuditLogEntry.target_id`][]."""

    user_id: snowflakes.Snowflake | None = attrs.field(eq=False, hash=False, repr=True)
    """The ID of the user who made this change."""

    action_type: AuditLogEventType | int = attrs.field(eq=False, hash=False, repr=True)
    """The type of action this entry represents."""

    options: BaseAuditLogEntryInfo | None = attrs.field(eq=False, hash=False, repr=False)
    """Extra information about this entry. Only be provided for certain `event_type`."""

    reason: str | None = attrs.field(eq=False, hash=False, repr=False)
    """The reason for this change, if set (between 0-512 characters)."""

    async def fetch_user(self) -> users_.User | None:
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
@attrs.define(kw_only=True, repr=False, weakref_slot=False)
class AuditLog(typing.Sequence[AuditLogEntry]):
    """Represents a guilds audit log's page."""

    auto_mod_rules: typing.Mapping[snowflakes.Snowflake, auto_mod.AutoModRule] = attrs.field(repr=False)
    """A mapping of auto-moderation rule objects referenced in this audit log."""

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

    @typing_extensions.override
    def __getitem__(self, index_or_slice: int | slice, /) -> AuditLogEntry | typing.Sequence[AuditLogEntry]:
        return collections.get_index_or_slice(self.entries, index_or_slice)

    @typing_extensions.override
    def __iter__(self) -> typing.Iterator[AuditLogEntry]:
        return iter(self.entries.values())

    @typing_extensions.override
    def __len__(self) -> int:
        return len(self.entries)
