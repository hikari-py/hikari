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
"""Application and entities that are used to describe guilds on Discord."""

from __future__ import annotations

__all__: typing.List[str] = [
    "Guild",
    "RESTGuild",
    "GatewayGuild",
    "GuildWidget",
    "Role",
    "GuildFeature",
    "GuildFeatureish",
    "GuildSystemChannelFlag",
    "GuildMessageNotificationsLevel",
    "GuildExplicitContentFilterLevel",
    "GuildMFALevel",
    "GuildVerificationLevel",
    "GuildPremiumTier",
    "GuildPreview",
    "GuildMemberBan",
    "Member",
    "Integration",
    "IntegrationAccount",
    "IntegrationType",
    "IntegrationApplication",
    "IntegrationExpireBehaviour",
    "PartialApplication",
    "PartialGuild",
    "PartialIntegration",
    "PartialRole",
    "WelcomeScreen",
    "WelcomeChannel",
]

import abc
import typing

import attr

from hikari import snowflakes
from hikari import traits
from hikari import undefined
from hikari import urls
from hikari import users
from hikari.internal import attr_extensions
from hikari.internal import enums
from hikari.internal import routes

if typing.TYPE_CHECKING:
    import datetime

    from hikari import channels as channels_
    from hikari import colors
    from hikari import colours
    from hikari import emojis as emojis_
    from hikari import files
    from hikari import permissions as permissions_
    from hikari import presences as presences_
    from hikari import voices as voices_
    from hikari.internal import time as time_


@typing.final
class GuildExplicitContentFilterLevel(int, enums.Enum):
    """Represents the explicit content filter setting for a guild."""

    DISABLED = 0
    """No explicit content filter."""

    MEMBERS_WITHOUT_ROLES = 1
    """Filter posts from anyone without a role."""

    ALL_MEMBERS = 2
    """Filter all posts."""


@typing.final
class GuildFeature(str, enums.Enum):
    """Features that a guild can provide."""

    ANIMATED_ICON = "ANIMATED_ICON"
    """Guild has access to set an animated guild icon."""

    BANNER = "BANNER"
    """Guild has access to set a guild banner image."""

    COMMERCE = "COMMERCE"
    """Guild has access to use commerce features (i.e. create store channels)."""

    COMMUNITY = "COMMUNITY"
    """Guild has community features enabled."""

    DISCOVERABLE = "DISCOVERABLE"
    """Guild is able to be discovered in the directory.

    This also implies the guild can be viewed without joining.
    """

    FEATURABLE = "FEATURABLE"
    """Guild is able to be featured in the directory."""

    INVITE_SPLASH = "INVITE_SPLASH"
    """Guild has access to set an invite splash background."""

    MORE_EMOJI = "MORE_EMOJI"
    """More emojis can be hosted in this guild than normal."""

    NEWS = "NEWS"
    """Guild has access to create news channels."""

    PARTNERED = "PARTNERED"
    """Guild is partnered."""

    RELAY_ENABLED = "RELAY_ENABLED"
    """Guild is using relays.

    Relays are new infrastructure designed to handle large guilds more
    efficiently server-side.
    """

    VANITY_URL = "VANITY_URL"
    """Guild has access to set a vanity URL."""

    VERIFIED = "VERIFIED"
    """Guild is verified."""

    VIP_REGIONS = "VIP_REGIONS"
    """Guild has access to set 384kbps bitrate in voice.

    Previously gave access to VIP voice servers.
    """

    WELCOME_SCREEN_ENABLED = "WELCOME_SCREEN_ENABLED"
    """Guild has enabled the welcome screen."""

    MEMBER_VERIFICATION_GATE_ENABLED = "MEMBER_VERIFICATION_GATE_ENABLED"
    """Guild has enabled Membership Screening."""

    PREVIEW_ENABLED = "PREVIEW_ENABLED"
    """Guild can be viewed before Membership Screening is complete."""


GuildFeatureish = typing.Union[str, GuildFeature]
"""Type hint for possible guild features.

Generally these will be of type `GuildFeature`, but undocumented or new
fields may just be `builtins.str` until they are documented and amended to the
library.
"""


@typing.final
class GuildMessageNotificationsLevel(int, enums.Enum):
    """Represents the default notification level for new messages in a guild."""

    ALL_MESSAGES = 0
    """Notify users when any message is sent."""

    ONLY_MENTIONS = 1
    """Only notify users when they are @mentioned."""


@typing.final
class GuildMFALevel(int, enums.Enum):
    """Represents the multi-factor authorization requirement for a guild."""

    NONE = 0
    """No MFA requirement."""

    ELEVATED = 1
    """MFA requirement."""


@typing.final
class GuildPremiumTier(int, enums.Enum):
    """Tier for Discord Nitro boosting in a guild."""

    NONE = 0
    """No Nitro boost level."""

    TIER_1 = 1
    """Level 1 Nitro boost."""

    TIER_2 = 2
    """Level 2 Nitro boost."""

    TIER_3 = 3
    """Level 3 Nitro boost."""


@typing.final
class GuildSystemChannelFlag(enums.Flag):
    """Defines which features are suppressed in the system channel."""

    NONE = 0
    """Nothing is suppressed."""

    SUPPRESS_USER_JOIN = 1 << 0
    """Suppress displaying a message about new users joining."""

    SUPPRESS_PREMIUM_SUBSCRIPTION = 1 << 1
    """Suppress displaying a message when the guild is Nitro boosted."""

    SUPPRESS_GUILD_REMINDER = 1 << 2
    """Suppress displaying messages with guild setup tips."""


@typing.final
class GuildVerificationLevel(int, enums.Enum):
    """Represents the level of verification of a guild."""

    NONE = 0
    """Unrestricted."""

    LOW = 1
    """Must have a verified email on their account."""

    MEDIUM = 2
    """Must have been registered on Discord for more than 5 minutes."""

    HIGH = 3
    """Must also be a member of the guild for longer than 10 minutes."""

    VERY_HIGH = 4
    """Must have a verified phone number."""


@attr_extensions.with_copy
@attr.define(hash=False, kw_only=True, weakref_slot=False)
class GuildWidget:
    """Represents a guild widget."""

    app: traits.RESTAware = attr.field(
        repr=False, eq=False, hash=False, metadata={attr_extensions.SKIP_DEEP_COPY: True}
    )
    """The client application that models may use for procedures."""

    channel_id: typing.Optional[snowflakes.Snowflake] = attr.field(repr=True)
    """The ID of the channel the invite for this embed targets, if enabled."""

    is_enabled: bool = attr.field(repr=True)
    """Whether this embed is enabled."""


@attr_extensions.with_copy
@attr.define(eq=False, hash=False, kw_only=True, weakref_slot=False)
class Member(users.User):
    """Used to represent a guild bound member."""

    guild_id: snowflakes.Snowflake = attr.field(repr=True)
    """The ID of the guild this member belongs to."""

    is_deaf: undefined.UndefinedOr[bool] = attr.field(repr=False)
    """`builtins.True` if this member is deafened in the current voice channel.

    This will be `hikari.undefined.UNDEFINED` if it's state is
    unknown.
    """

    is_mute: undefined.UndefinedOr[bool] = attr.field(repr=False)
    """`builtins.True` if this member is muted in the current voice channel.

    This will be `hikari.undefined.UNDEFINED` if it's state is unknown.
    """

    is_pending: undefined.UndefinedOr[bool] = attr.field(repr=False)
    """Whether the user has passed the guild's membership screening requirements.

    This will be `hikari.undefined.UNDEFINED` if it's state is unknown.
    """

    joined_at: datetime.datetime = attr.field(repr=True)
    """The datetime of when this member joined the guild they belong to."""

    nickname: typing.Optional[str] = attr.field(repr=True)
    """This member's nickname.

    This will be `builtins.None` if not set.
    """

    premium_since: typing.Optional[datetime.datetime] = attr.field(repr=False)
    """The datetime of when this member started "boosting" this guild.

    Will be `builtins.None` if the member is not a premium user.
    """

    role_ids: typing.Sequence[snowflakes.Snowflake] = attr.field(repr=False)
    """A sequence of the IDs of the member's current roles."""

    # This is technically optional, since UPDATE MEMBER and MESSAGE CREATE
    # events do not inject the user into the member payload, but specify it
    # separately. However, to get around this inconsistency, we force the
    # entity factory to always provide the user object in these cases, so we
    # can assume this is always set, and thus we are always able to get info
    # such as the ID of the user this member represents.
    user: users.User = attr.field(repr=True)
    """This member's corresponding user object."""

    @property
    def app(self) -> traits.RESTAware:
        """Return the app that is bound to the user object."""
        return self.user.app

    @property
    def avatar_hash(self) -> typing.Optional[str]:
        return self.user.avatar_hash

    @property
    def avatar_url(self) -> typing.Optional[files.URL]:
        return self.user.avatar_url

    @property
    def default_avatar_url(self) -> files.URL:
        return self.user.default_avatar_url

    @property
    def discriminator(self) -> str:
        return self.user.discriminator

    @property
    def display_name(self) -> str:
        """Return the member's display name.

        If the member has a nickname, this will return that nickname.
        Otherwise, it will return the username instead.

        Returns
        -------
        builtins.str
            The member display name.

        See Also
        --------
        Nickname: `Member.nickname`
        Username: `Member.username`
        """
        return self.nickname if isinstance(self.nickname, str) else self.username

    @property
    def flags(self) -> users.UserFlag:
        return self.user.flags

    @property
    def id(self) -> snowflakes.Snowflake:
        return self.user.id

    @id.setter
    def id(self, value: snowflakes.Snowflake) -> None:
        raise TypeError("Cannot mutate the ID of a member")

    @property
    def is_bot(self) -> bool:
        return self.user.is_bot

    @property
    def is_system(self) -> bool:
        return self.user.is_system

    @property
    def mention(self) -> str:
        """Return a raw mention string for the given member.

        If the member has a known nickname, we always return
        a bang ("`!`") before the ID part of the mention string. This
        mimics the behaviour Discord clients tend to provide.

        Example
        -------

        ```py
        >>> some_member_without_nickname.mention
        '<@123456789123456789>'
        >>> some_member_with_nickname.mention
        '<@!123456789123456789>'
        ```

        Returns
        -------
        builtins.str
            The mention string to use.
        """
        return f"<@!{self.id}>" if self.nickname is not None else self.user.mention

    @property
    def presence(self) -> typing.Optional[presences_.MemberPresence]:
        """Get the cached presence for this member, if known.

        Presence info includes user status and activities.

        This requires the `GUILD_PRESENCES` intent to be enabled.

        Returns
        -------
        typing.Optional[hikari.presences.MemberPresence]
            The member presence, or `builtins.None` if not known.
        """
        if not isinstance(self.user.app, traits.CacheAware):
            return None

        return self.user.app.cache.get_presence(self.guild_id, self.user.id)

    @property
    def roles(self) -> typing.Sequence[Role]:
        """Return the roles the user has.

        This will be empty if the roles are missing from the cache.

        Returns
        -------
        typing.Sequence[hikari.guilds.Role]
            The roles the users has.
        """
        if not isinstance(self.user.app, traits.CacheAware):
            return []

        roles_view = self.user.app.cache.get_roles_view_for_guild(self.guild_id)

        return [r for r in roles_view.values() if r.id in self.role_ids]

    @property
    def top_role(self) -> typing.Optional[Role]:
        """Return the highest role the member has.

        Returns
        -------
        typing.Optional[hikari.guilds.Role]
            `builtins.None` if the cache is missing the roles information or
            the highest role the user has.
        """
        roles = sorted(self.roles, key=lambda r: r.position, reverse=True)

        try:
            return next(iter(roles))
        except StopIteration:
            return None

    @property
    def username(self) -> str:
        return self.user.username

    def make_avatar_url(self, *, ext: typing.Optional[str] = None, size: int = 4096) -> typing.Optional[files.URL]:
        return self.user.make_avatar_url(ext=ext, size=size)

    async def fetch_self(self) -> Member:
        """Fetch an up-to-date view of this member from the API.

        Returns
        -------
        hikari.guilds.Member
            An up-to-date view of this member.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the member is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        return await self.user.app.rest.fetch_member(self.guild_id, self.user.id)

    async def fetch_dm_channel(self) -> channels_.DMChannel:
        return await self.user.fetch_dm_channel()

    async def ban(
        self,
        *,
        delete_message_days: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        """Ban this member from this guild.

        Other Parameters
        ----------------
        delete_message_days : hikari.undefined.UndefinedNoneOr[builtins.int]
            If provided, the number of days to delete messages for.
            This must be between 0 and 7.
        reason : hikari.undefined.UndefinedOr[builtins.str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.ForbiddenError
            If you are missing the `BAN_MEMBERS` permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild or user are not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        await self.user.app.rest.ban_user(
            self.guild_id, self.user.id, delete_message_days=delete_message_days, reason=reason
        )

    def __str__(self) -> str:
        return str(self.user)

    def __hash__(self) -> int:
        return hash(self.user)

    def __eq__(self, other: object) -> bool:
        return self.user == other


@attr_extensions.with_copy
@attr.define(hash=True, kw_only=True, weakref_slot=False)
class PartialRole(snowflakes.Unique):
    """Represents a partial guild bound Role object."""

    app: traits.RESTAware = attr.field(
        repr=False, eq=False, hash=False, metadata={attr_extensions.SKIP_DEEP_COPY: True}
    )
    """The client application that models may use for procedures."""

    id: snowflakes.Snowflake = attr.field(hash=True, repr=True)
    """The ID of this entity."""

    name: str = attr.field(eq=False, hash=False, repr=True)
    """The role's name."""

    def __str__(self) -> str:
        return self.name


@attr.define(hash=True, kw_only=True, weakref_slot=False)
class Role(PartialRole):
    """Represents a guild bound Role object."""

    color: colors.Color = attr.field(eq=False, hash=False, repr=True)
    """The colour of this role.

    This will be applied to a member's name in chat if it's their top coloured role.
    """

    guild_id: snowflakes.Snowflake = attr.field(eq=False, hash=False, repr=True)
    """The ID of the guild this role belongs to"""

    is_hoisted: bool = attr.field(eq=False, hash=False, repr=True)
    """Whether this role is hoisting the members it's attached to in the member list.

    members will be hoisted under their highest role where this is set to `builtins.True`.
    """

    is_managed: bool = attr.field(eq=False, hash=False, repr=False)
    """Whether this role is managed by an integration."""

    is_mentionable: bool = attr.field(eq=False, hash=False, repr=False)
    """Whether this role can be mentioned by all regardless of permissions."""

    permissions: permissions_.Permissions = attr.field(eq=False, hash=False, repr=False)
    """The guild wide permissions this role gives to the members it's attached to,

    This may be overridden by channel overwrites.
    """

    position: int = attr.field(eq=False, hash=False, repr=True)
    """The position of this role in the role hierarchy.

    This will start at `0` for the lowest role (@everyone)
    and increase as you go up the hierarchy.
    """

    bot_id: typing.Optional[snowflakes.Snowflake] = attr.field(eq=False, hash=False, repr=True)
    """The ID of the bot this role belongs to.

    If `builtins.None`, this is not a bot role.
    """

    integration_id: typing.Optional[snowflakes.Snowflake] = attr.field(eq=False, hash=False, repr=True)
    """The ID of the integration this role belongs to.

    If `builtins.None`, this is not a integration role.
    """

    is_premium_subscriber_role: bool = attr.field(eq=False, hash=False, repr=True)
    """Whether this role is the guild's nitro subscriber role."""

    @property
    def colour(self) -> colours.Colour:
        """Alias for the `color` field."""
        return self.color


class IntegrationType(str, enums.Enum):
    """The integration type."""

    TWITCH = "twitch"

    YOUTUBE = "youtube"

    DISCORD_BOT = "discord"


@typing.final
class IntegrationExpireBehaviour(int, enums.Enum):
    """Behavior for expiring integration subscribers."""

    REMOVE_ROLE = 0
    """Remove the role."""

    KICK = 1
    """Kick the subscriber."""


@attr_extensions.with_copy
@attr.define(hash=True, kw_only=True, weakref_slot=False)
class IntegrationAccount:
    """An account that's linked to an integration."""

    id: str = attr.field(hash=True, repr=True)
    """The string ID of this (likely) third party account."""

    name: str = attr.field(eq=False, hash=False, repr=True)
    """The name of this account."""

    def __str__(self) -> str:
        return self.name


# This is here rather than in applications.py to avoid circular imports
@attr_extensions.with_copy
@attr.define(hash=True, kw_only=True, weakref_slot=False)
class PartialApplication(snowflakes.Unique):
    """A partial representation of a Discord application."""

    id: snowflakes.Snowflake = attr.field(hash=True, repr=True)
    """The ID of this entity."""

    name: str = attr.field(eq=False, hash=False, repr=True)
    """The name of this application."""

    description: typing.Optional[str] = attr.field(eq=False, hash=False, repr=False)
    """The description of this application, if any."""

    icon_hash: typing.Optional[str] = attr.field(eq=False, hash=False, repr=False)
    """The CDN hash of this application's icon, if set."""

    summary: typing.Optional[str] = attr.field(eq=False, hash=False, repr=False)
    """This summary for this application's primary SKU if it's sold on Discord, if any."""

    def __str__(self) -> str:
        return self.name

    @property
    def icon_url(self) -> typing.Optional[files.URL]:
        """Team icon URL, if there is one.

        Returns
        -------
        typing.Optional[hikari.files.URL]
            The URL, or `builtins.None` if no icon exists.
        """
        return self.make_icon_url()

    def make_icon_url(self, *, ext: str = "png", size: int = 4096) -> typing.Optional[files.URL]:
        """Generate the icon URL for this application.

        Parameters
        ----------
        ext : builtins.str
            The extension to use for this URL, defaults to `png`.
            Supports `png`, `jpeg`, `jpg` and `webp`.
        size : builtins.int
            The size to set for the URL, defaults to `4096`.
            Can be any power of two between 16 and 4096.

        Returns
        -------
        typing.Optional[hikari.files.URL]
            The URL, or `builtins.None` if no icon exists.

        Raises
        ------
        builtins.ValueError
            If the size is not an integer power of 2 between 16 and 4096
            (inclusive).
        """
        if self.icon_hash is None:
            return None

        return routes.CDN_APPLICATION_ICON.compile_to_file(
            urls.CDN_URL,
            application_id=self.id,
            hash=self.icon_hash,
            size=size,
            file_format=ext,
        )


@attr_extensions.with_copy
@attr.define(hash=True, kw_only=True, weakref_slot=False)
class IntegrationApplication(PartialApplication):
    """An application that's linked to an integration."""

    bot: typing.Optional[users.User] = attr.field(eq=False, hash=False, repr=False)
    """The bot associated with this application."""


@attr_extensions.with_copy
@attr.define(hash=True, kw_only=True, weakref_slot=False)
class PartialIntegration(snowflakes.Unique):
    """A partial representation of an integration, found in audit logs."""

    account: IntegrationAccount = attr.field(eq=False, hash=False, repr=False)
    """The account connected to this integration."""

    id: snowflakes.Snowflake = attr.field(hash=True, repr=True)
    """The ID of this entity."""

    name: str = attr.field(eq=False, hash=False, repr=True)
    """The name of this integration."""

    type: typing.Union[IntegrationType, str] = attr.field(eq=False, hash=False, repr=True)
    """The type of this integration."""

    def __str__(self) -> str:
        return self.name


@attr.define(hash=True, kw_only=True, weakref_slot=False)
class Integration(PartialIntegration):
    """Represents a guild integration object."""

    guild_id: snowflakes.Snowflake = attr.field()
    """The ID of the guild this integration belongs to."""

    expire_behavior: typing.Union[IntegrationExpireBehaviour, int, None] = attr.field(eq=False, hash=False, repr=False)
    """How members should be treated after their connected subscription expires.

    This will not be enacted until after `GuildIntegration.expire_grace_period`
    passes.

    !!! note
        This will always be `builtins.None` for Discord integrations.
    """

    expire_grace_period: typing.Optional[datetime.timedelta] = attr.field(eq=False, hash=False, repr=False)
    """How many days users with expired subscriptions are given until
    `GuildIntegration.expire_behavior` is enacted out on them.

    !!! note
        This will always be `builtins.None` for Discord integrations.
    """

    is_enabled: bool = attr.field(eq=False, hash=False, repr=True)
    """Whether this integration is enabled."""

    is_syncing: typing.Optional[bool] = attr.field(eq=False, hash=False, repr=False)
    """Whether this integration is syncing subscribers/emojis."""

    is_emojis_enabled: typing.Optional[bool] = attr.field(eq=False, hash=False, repr=False)
    """Whether users under this integration are allowed to use it's custom emojis."""

    is_revoked: typing.Optional[bool] = attr.field(eq=False, hash=False, repr=False)
    """Whether the integration has been revoked."""

    last_synced_at: typing.Optional[datetime.datetime] = attr.field(eq=False, hash=False, repr=False)
    """The datetime of when this integration's subscribers were last synced."""

    role_id: typing.Optional[snowflakes.Snowflake] = attr.field(eq=False, hash=False, repr=False)
    """The ID of the managed role used for this integration's subscribers."""

    user: typing.Optional[users.User] = attr.field(eq=False, hash=False, repr=False)
    """The user this integration belongs to."""

    subscriber_count: typing.Optional[int] = attr.field(eq=False, hash=False, repr=False)
    """The number of subscribers this integration has."""

    application: typing.Optional[IntegrationApplication] = attr.field(eq=False, hash=False, repr=False)
    """The bot/OAuth2 application associated with this integration.

    !!! note
        This is only available for Discord integrations.
    """


@attr_extensions.with_copy
@attr.define(hash=False, weakref_slot=False)
class WelcomeChannel:
    """Used to represent channels on guild welcome screens."""

    channel_id: snowflakes.Snowflake = attr.field(hash=False, repr=True)
    """ID of the channel shown in the welcome screen."""

    description: str = attr.field(hash=False, repr=False)
    """The description shown for this channel."""

    emoji: typing.Optional[emojis_.Emoji] = attr.field(default=None, kw_only=True, hash=False, repr=True)
    """The emoji shown in the welcome screen channel if set else `builtins.None`."""


@attr_extensions.with_copy
@attr.define(hash=False, kw_only=True, weakref_slot=False)
class WelcomeScreen:
    """Used to represent guild welcome screens on Discord."""

    description: typing.Optional[str] = attr.field(hash=False, repr=True)
    """The guild's description shown in the welcome screen."""

    channels: typing.Sequence[WelcomeChannel] = attr.field(hash=False, repr=True)
    """An array of up to 5 of the channels shown in the welcome screen."""


@attr_extensions.with_copy
@attr.define(hash=False, kw_only=True, weakref_slot=False)
class GuildMemberBan:
    """Used to represent guild bans."""

    reason: typing.Optional[str] = attr.field(repr=True)
    """The reason for this ban, will be `builtins.None` if no reason was given."""

    user: users.User = attr.field(repr=True)
    """The object of the user this ban targets."""


@attr_extensions.with_copy
@attr.define(hash=True, kw_only=True, weakref_slot=False)
class PartialGuild(snowflakes.Unique):
    """Base object for any partial guild objects."""

    app: traits.RESTAware = attr.field(
        repr=False, eq=False, hash=False, metadata={attr_extensions.SKIP_DEEP_COPY: True}
    )
    """The client application that models may use for procedures."""

    id: snowflakes.Snowflake = attr.field(hash=True, repr=True)
    """The ID of this entity."""

    icon_hash: typing.Optional[str] = attr.field(eq=False, hash=False, repr=False)
    """The hash for the guild icon, if there is one."""

    name: str = attr.field(eq=False, hash=False, repr=True)
    """The name of the guild."""

    def __str__(self) -> str:
        return self.name

    @property
    def icon_url(self) -> typing.Optional[files.URL]:
        """Icon URL for the guild, if set; otherwise `builtins.None`."""
        return self.make_icon_url()

    @property
    def shard_id(self) -> typing.Optional[int]:
        """Return the ID of the shard this guild is served by.

        This may return `None` if the application does not have a gateway
        connection.
        """
        if not isinstance(self.app, traits.ShardAware):
            return None

        shard_count = self.app.shard_count
        assert isinstance(shard_count, int)
        return snowflakes.calculate_shard_id(shard_count, self.id)

    def make_icon_url(self, *, ext: typing.Optional[str] = None, size: int = 4096) -> typing.Optional[files.URL]:
        """Generate the guild's icon URL, if set.

        Parameters
        ----------
        ext : typing.Optional[builtins.str]
            The extension to use for this URL, defaults to `png` or `gif`.
            Supports `png`, `jpeg`, `jpg`, `webp` and `gif` (when
            animated).

            If `builtins.None`, then the correct default extension is
            determined based on whether the icon is animated or not.
        size : builtins.int
            The size to set for the URL, defaults to `4096`.
            Can be any power of two between 16 and 4096.

        Returns
        -------
        typing.Optional[hikari.files.URL]
            The URL to the resource, or `builtins.None` if no icon is set.

        Raises
        ------
        builtins.ValueError
            If `size` is not a power of two or not between 16 and 4096.
        """
        if self.icon_hash is None:
            return None

        if ext is None:
            if self.icon_hash.startswith("a_"):
                ext = "gif"
            else:
                ext = "png"

        return routes.CDN_GUILD_ICON.compile_to_file(
            urls.CDN_URL,
            guild_id=self.id,
            hash=self.icon_hash,
            size=size,
            file_format=ext,
        )


@attr.define(hash=True, kw_only=True, weakref_slot=False)
class GuildPreview(PartialGuild):
    """A preview of a guild with the `GuildFeature.DISCOVERABLE` feature."""

    features: typing.Sequence[GuildFeatureish] = attr.field(eq=False, hash=False, repr=False)
    """A list of the features in this guild."""

    splash_hash: typing.Optional[str] = attr.field(eq=False, hash=False, repr=False)
    """The hash of the splash for the guild, if there is one."""

    discovery_splash_hash: typing.Optional[str] = attr.field(eq=False, hash=False, repr=False)
    """The hash of the discovery splash for the guild, if there is one."""

    emojis: typing.Mapping[snowflakes.Snowflake, emojis_.KnownCustomEmoji] = attr.field(
        eq=False, hash=False, repr=False
    )
    """The mapping of IDs to the emojis this guild provides."""

    approximate_active_member_count: int = attr.field(eq=False, hash=False, repr=True)
    """The approximate amount of presences in this guild."""

    approximate_member_count: int = attr.field(eq=False, hash=False, repr=True)
    """The approximate amount of members in this guild."""

    description: typing.Optional[str] = attr.field(eq=False, hash=False, repr=False)
    """The guild's description, if set."""

    @property
    def discovery_splash_url(self) -> typing.Optional[files.URL]:
        """Discovery URL splash for the guild, if set."""
        return self.make_discovery_splash_url()

    @property
    def splash_url(self) -> typing.Optional[files.URL]:
        """Splash URL for the guild, if set."""
        return self.make_splash_url()

    def make_discovery_splash_url(self, *, ext: str = "png", size: int = 4096) -> typing.Optional[files.URL]:
        """Generate the guild's discovery splash image URL, if set.

        Parameters
        ----------
        ext : builtins.str
            The extension to use for this URL, defaults to `png`.
            Supports `png`, `jpeg`, `jpg` and `webp`.
        size : builtins.int
            The size to set for the URL, defaults to `4096`.
            Can be any power of two between 16 and 4096.

        Returns
        -------
        typing.Optional[hikari.files.URL]
            The string URL.

        Raises
        ------
        builtins.ValueError
            If `size` is not a power of two or not between 16 and 4096.
        """
        if self.discovery_splash_hash is None:
            return None

        return routes.CDN_GUILD_DISCOVERY_SPLASH.compile_to_file(
            urls.CDN_URL,
            guild_id=self.id,
            hash=self.discovery_splash_hash,
            size=size,
            file_format=ext,
        )

    def make_splash_url(self, *, ext: str = "png", size: int = 4096) -> typing.Optional[files.URL]:
        """Generate the guild's splash image URL, if set.

        Parameters
        ----------
        ext : builtins.str
            The extension to use for this URL, defaults to `png`.
            Supports `png`, `jpeg`, `jpg` and `webp`.
        size : builtins.int
            The size to set for the URL, defaults to `4096`.
            Can be any power of two between 16 and 4096.

        Returns
        -------
        typing.Optional[hikari.files.URL]
            The URL to the splash, or `builtins.None` if not set.

        Raises
        ------
        builtins.ValueError
            If `size` is not a power of two or not between 16 and 4096.
        """
        if self.splash_hash is None:
            return None

        return routes.CDN_GUILD_SPLASH.compile_to_file(
            urls.CDN_URL,
            guild_id=self.id,
            hash=self.splash_hash,
            size=size,
            file_format=ext,
        )


@attr.define(hash=True, kw_only=True, weakref_slot=False)
class Guild(PartialGuild, abc.ABC):
    """A representation of a guild on Discord."""

    features: typing.Sequence[GuildFeatureish] = attr.field(eq=False, hash=False, repr=False)
    """A list of the features in this guild."""

    application_id: typing.Optional[snowflakes.Snowflake] = attr.field(eq=False, hash=False, repr=False)
    """The ID of the application that created this guild.

    This will always be `builtins.None` for guilds that weren't created by a bot.
    """

    afk_channel_id: typing.Optional[snowflakes.Snowflake] = attr.field(eq=False, hash=False, repr=False)
    """The ID for the channel that AFK voice users get sent to.

    If `builtins.None`, then no AFK channel is set up for this guild.
    """

    afk_timeout: datetime.timedelta = attr.field(eq=False, hash=False, repr=False)
    """Timeout for activity before a member is classed as AFK.

    How long a voice user has to be AFK for before they are classed as being
    AFK and are moved to the AFK channel (`Guild.afk_channel_id`).
    """

    banner_hash: typing.Optional[str] = attr.field(eq=False, hash=False, repr=False)
    """The hash for the guild's banner.

    This is only present if the guild has `GuildFeature.BANNER` in
    `Guild.features` for this guild. For all other purposes, it is `builtins.None`.
    """

    default_message_notifications: typing.Union[GuildMessageNotificationsLevel, int] = attr.field(
        eq=False, hash=False, repr=False
    )
    """The default setting for message notifications in this guild."""

    description: typing.Optional[str] = attr.field(eq=False, hash=False, repr=False)
    """The guild's description.

    This is only present if certain `GuildFeature`'s are set in
    `Guild.features` for this guild. Otherwise, this will always be `builtins.None`.
    """

    discovery_splash_hash: typing.Optional[str] = attr.field(eq=False, hash=False, repr=False)
    """The hash of the discovery splash for the guild, if there is one."""

    explicit_content_filter: typing.Union[GuildExplicitContentFilterLevel, int] = attr.field(
        eq=False, hash=False, repr=False
    )
    """The setting for the explicit content filter in this guild."""

    is_widget_enabled: typing.Optional[bool] = attr.field(eq=False, hash=False, repr=False)
    """Describes whether the guild widget is enabled or not.

    If this information is not present, this will be `builtins.None`.
    """

    max_video_channel_users: typing.Optional[int] = attr.field(eq=False, hash=False, repr=False)
    """The maximum number of users allowed in a video channel together.

    This information may not be present, in which case, it will be `builtins.None`.
    """

    mfa_level: typing.Union[GuildMFALevel, int] = attr.field(eq=False, hash=False, repr=False)
    """The required MFA level for users wishing to participate in this guild."""

    owner_id: snowflakes.Snowflake = attr.field(eq=False, hash=False, repr=True)
    """The ID of the owner of this guild."""

    preferred_locale: str = attr.field(eq=False, hash=False, repr=False)
    """The preferred locale to use for this guild.

    This can only be change if `GuildFeature.COMMUNITY` is in `Guild.features`
    for this guild and will otherwise default to `en-US`.
    """

    premium_subscription_count: typing.Optional[int] = attr.field(eq=False, hash=False, repr=False)
    """The number of nitro boosts that the server currently has.

    This information may not be present, in which case, it will be `builtins.None`.
    """

    premium_tier: typing.Union[GuildPremiumTier, int] = attr.field(eq=False, hash=False, repr=False)
    """The premium tier for this guild."""

    public_updates_channel_id: typing.Optional[snowflakes.Snowflake] = attr.field(eq=False, hash=False, repr=False)
    """The channel ID of the channel where admins and moderators receive notices
    from Discord.

    This is only present if `GuildFeature.COMMUNITY` is in `Guild.features` for
    this guild. For all other purposes, it should be considered to be `builtins.None`.
    """

    rules_channel_id: typing.Optional[snowflakes.Snowflake] = attr.field(eq=False, hash=False, repr=False)
    """The ID of the channel where guilds with the `GuildFeature.COMMUNITY`
    `features` display rules and guidelines.

    If the `GuildFeature.COMMUNITY` feature is not defined, then this is `builtins.None`.
    """

    splash_hash: typing.Optional[str] = attr.field(eq=False, hash=False, repr=False)
    """The hash of the splash for the guild, if there is one."""

    system_channel_flags: GuildSystemChannelFlag = attr.field(eq=False, hash=False, repr=False)
    """Return flags for the guild system channel.

    These are used to describe which notifications are suppressed.

    Returns
    -------
    GuildSystemChannelFlag
        The system channel flags for this channel.
    """

    system_channel_id: typing.Optional[snowflakes.Snowflake] = attr.field(eq=False, hash=False, repr=False)
    """The ID of the system channel or `builtins.None` if it is not enabled.

    Welcome messages and Nitro boost messages may be sent to this channel.
    """

    vanity_url_code: typing.Optional[str] = attr.field(eq=False, hash=False, repr=False)
    """The vanity URL code for the guild's vanity URL.

    This is only present if `GuildFeature.VANITY_URL` is in `Guild.features` for
    this guild. If not, this will always be `builtins.None`.
    """

    verification_level: typing.Union[GuildVerificationLevel, int] = attr.field(eq=False, hash=False, repr=False)
    """The verification level needed for a user to participate in this guild."""

    widget_channel_id: typing.Optional[snowflakes.Snowflake] = attr.field(eq=False, hash=False, repr=False)
    """The channel ID that the widget's generated invite will send the user to.

    If this information is unavailable or this is not enabled for the guild then
    this will be `builtins.None`.
    """

    is_nsfw: bool = attr.field(eq=False, hash=False, repr=False)
    """Whether the guild is designated as NSFW."""

    @property
    def banner_url(self) -> typing.Optional[files.URL]:
        """Banner URL for the guild, if set."""
        return self.make_banner_url()

    @property
    def discovery_splash_url(self) -> typing.Optional[files.URL]:
        """Discovery splash URL for the guild, if set."""
        return self.make_discovery_splash_url()

    @property
    @abc.abstractmethod
    def emojis(self) -> typing.Mapping[snowflakes.Snowflake, emojis_.KnownCustomEmoji]:
        """Return the emojis in this guild.

        Returns
        -------
        typing.Mapping[hikari.snowflakes.Snowflake, hikari.emojis.KnownCustomEmoji]
            A mapping of emoji IDs to the objects of emojis in this guild.
        """

    @property
    @abc.abstractmethod
    def roles(self) -> typing.Mapping[snowflakes.Snowflake, Role]:
        """Return the roles in this guild.

        Returns
        -------
        typing.Mapping[hikari.snowflakes.Snowflake, Role]
            A mapping of role IDs to the objects of roles in this guild.
        """

    @property
    def splash_url(self) -> typing.Optional[files.URL]:
        """Splash URL for the guild, if set."""
        return self.make_splash_url()

    def make_banner_url(self, *, ext: str = "png", size: int = 4096) -> typing.Optional[files.URL]:
        """Generate the guild's banner image URL, if set.

        Parameters
        ----------
        ext : builtins.str
            The extension to use for this URL, defaults to `png`.
            Supports `png`, `jpeg`, `jpg` and `webp`.
        size : builtins.int
            The size to set for the URL, defaults to `4096`.
            Can be any power of two between 16 and 4096.

        Returns
        -------
        typing.Optional[hikari.files.URL]
            The URL of the banner, or `builtins.None` if no banner is set.

        Raises
        ------
        builtins.ValueError
            If `size` is not a power of two or not between 16 and 4096.
        """
        if self.banner_hash is None:
            return None

        return routes.CDN_GUILD_BANNER.compile_to_file(
            urls.CDN_URL,
            guild_id=self.id,
            hash=self.banner_hash,
            size=size,
            file_format=ext,
        )

    def make_discovery_splash_url(self, *, ext: str = "png", size: int = 4096) -> typing.Optional[files.URL]:
        """Generate the guild's discovery splash image URL, if set.

        Parameters
        ----------
        ext : builtins.str
            The extension to use for this URL, defaults to `png`.
            Supports `png`, `jpeg`, `jpg` and `webp`.
        size : builtins.int
            The size to set for the URL, defaults to `4096`.
            Can be any power of two between 16 and 4096.

        Returns
        -------
        typing.Optional[hikari.files.URL]
            The string URL.

        Raises
        ------
        builtins.ValueError
            If `size` is not a power of two or not between 16 and 4096.
        """
        if self.discovery_splash_hash is None:
            return None

        return routes.CDN_GUILD_DISCOVERY_SPLASH.compile_to_file(
            urls.CDN_URL,
            guild_id=self.id,
            hash=self.discovery_splash_hash,
            size=size,
            file_format=ext,
        )

    def make_splash_url(self, *, ext: str = "png", size: int = 4096) -> typing.Optional[files.URL]:
        """Generate the guild's splash image URL, if set.

        Parameters
        ----------
        ext : builtins.str
            The extension to use for this URL, defaults to `png`.
            Supports `png`, `jpeg`, `jpg` and `webp`.
        size : builtins.int
            The size to set for the URL, defaults to `4096`.
            Can be any power of two between 16 and 4096.

        Returns
        -------
        typing.Optional[hikari.files.URL]
            The URL to the splash, or `builtins.None` if not set.

        Raises
        ------
        builtins.ValueError
            If `size` is not a power of two or not between 16 and 4096.
        """
        if self.splash_hash is None:
            return None

        return routes.CDN_GUILD_SPLASH.compile_to_file(
            urls.CDN_URL,
            guild_id=self.id,
            hash=self.splash_hash,
            size=size,
            file_format=ext,
        )

    @abc.abstractmethod
    def get_emoji(
        self, emoji: snowflakes.SnowflakeishOr[emojis_.CustomEmoji]
    ) -> typing.Optional[emojis_.KnownCustomEmoji]:
        """Get an emoji from the cache by it's ID."""

    @abc.abstractmethod
    def get_role(self, role: snowflakes.SnowflakeishOr[PartialRole]) -> typing.Optional[Role]:
        """Get a role from the cache by it's ID."""


@attr.define(hash=True, kw_only=True, weakref_slot=False)
class RESTGuild(Guild):
    """Guild specialization that is sent via the REST API only."""

    # In a REST-provided guild, we provide these attributes directly, as the API will give them in the response.
    # This is different to Gateway guilds which will perform a cache-hit to handle this usually.
    _emojis: typing.Mapping[snowflakes.Snowflake, emojis_.KnownCustomEmoji] = attr.field(
        eq=False, hash=False, repr=False
    )
    """A mapping of emoji IDs to the objects of the emojis this guild provides."""

    _roles: typing.Mapping[snowflakes.Snowflake, Role] = attr.field(eq=False, hash=False, repr=False)
    """The roles in this guild, represented as a mapping of role ID to role object."""

    approximate_active_member_count: typing.Optional[int] = attr.field(eq=False, hash=False, repr=False)
    """The approximate number of members in the guild that are not offline.

    This will be `builtins.None` when creating a guild.
    """

    approximate_member_count: typing.Optional[int] = attr.field(eq=False, hash=False, repr=False)
    """The approximate number of members in the guild.

    This will be `builtins.None` when creating a guild.
    """

    max_presences: int = attr.field(eq=False, hash=False, repr=False)
    """The maximum number of presences for the guild."""

    max_members: int = attr.field(eq=False, hash=False, repr=False)
    """The maximum number of members allowed in this guild."""

    @property
    def emojis(self) -> typing.Mapping[snowflakes.Snowflake, emojis_.KnownCustomEmoji]:
        # <<inherited docstring from Guild>>.
        return self._emojis

    @property
    def roles(self) -> typing.Mapping[snowflakes.Snowflake, Role]:
        # <<inherited docstring from Guild>>.
        return self._roles

    def get_emoji(
        self, emoji: snowflakes.SnowflakeishOr[emojis_.CustomEmoji]
    ) -> typing.Optional[emojis_.KnownCustomEmoji]:
        # <<inherited docstring from Guild>>.
        return self._emojis.get(snowflakes.Snowflake(emoji))

    def get_role(self, role: snowflakes.SnowflakeishOr[PartialRole]) -> typing.Optional[Role]:
        # <<inherited docstring from Guild>>.
        return self._roles.get(snowflakes.Snowflake(role))


@attr.define(hash=True, kw_only=True, weakref_slot=False)
class GatewayGuild(Guild):
    """Guild specialization that is sent via the gateway only."""

    is_large: typing.Optional[bool] = attr.field(eq=False, hash=False, repr=False)
    """Whether the guild is considered to be large or not.

    This information is only available if the guild was sent via a `GUILD_CREATE`
    event. If the guild is received from any other place, this will always be
    `builtins.None`.

    The implications of a large guild are that presence information will not be
    sent about members who are offline or invisible.
    """

    joined_at: typing.Optional[datetime.datetime] = attr.field(eq=False, hash=False, repr=False)
    """The date and time that the bot user joined this guild.

    This information is only available if the guild was sent via a `GUILD_CREATE`
    event. If the guild is received from any other place, this will always be
    `builtins.None`.
    """

    member_count: typing.Optional[int] = attr.field(eq=False, hash=False, repr=False)
    """The number of members in this guild.

    This information is only available if the guild was sent via a `GUILD_CREATE`
    event. If the guild is received from any other place, this will always be
    `builtins.None`.
    """

    @property
    def channels(self) -> typing.Mapping[snowflakes.Snowflake, channels_.GuildChannel]:
        """Get the channels cached for the guild.

        Returns
        -------
        typing.Mapping[hikari.snowflakes.Snowflake, hikari.channels.GuildChannel]
            A mapping of channel IDs to objects of the channels cached for the
            guild.
        """
        if not isinstance(self.app, traits.CacheAware):
            return {}

        return self.app.cache.get_guild_channels_view_for_guild(self.id)

    @property
    def emojis(self) -> typing.Mapping[snowflakes.Snowflake, emojis_.KnownCustomEmoji]:
        # <<inherited docstring from Guild>>.
        if not isinstance(self.app, traits.CacheAware):
            return {}

        return self.app.cache.get_emojis_view_for_guild(self.id)

    @property
    def members(self) -> typing.Mapping[snowflakes.Snowflake, Member]:
        """Get the members cached for the guild.

        typing.Mapping[hikari.snowflakes.Snowflake, Member]
            A mapping of user IDs to objects of the members cached for the guild.
        """
        if not isinstance(self.app, traits.CacheAware):
            return {}

        return self.app.cache.get_members_view_for_guild(self.id)

    @property
    def presences(self) -> typing.Mapping[snowflakes.Snowflake, presences_.MemberPresence]:
        """Get the presences cached for the guild.

        typing.Mapping[hikari.snowflakes.Snowflake, hikari.presences.MemberPresence]
            A mapping of user IDs to objects of the presences cached for the
            guild.
        """
        if not isinstance(self.app, traits.CacheAware):
            return {}

        return self.app.cache.get_presences_view_for_guild(self.id)

    @property
    def roles(self) -> typing.Mapping[snowflakes.Snowflake, Role]:
        # <<inherited docstring from Guild>>.
        if not isinstance(self.app, traits.CacheAware):
            return {}

        return self.app.cache.get_roles_view_for_guild(self.id)

    @property
    def voice_states(self) -> typing.Mapping[snowflakes.Snowflake, voices_.VoiceState]:
        """Get the voice states cached for the guild.

        Returns
        -------
        typing.Mapping[hikari.snowflakes.Snowflake, hikari.voices.VoiceState]
            A mapping of user IDs to objects of the voice states cached for the
            guild.
        """
        if not isinstance(self.app, traits.CacheAware):
            return {}

        return self.app.cache.get_voice_states_view_for_guild(self.id)

    def get_channel(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.PartialChannel],
    ) -> typing.Optional[channels_.GuildChannel]:
        """Get a cached channel that belongs to the guild by it's ID or object.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.PartialChannel]
            The object or ID of the guild channel to get from the cache.

        Returns
        -------
        typing.Optional[hikari.channels.GuildChannel]
            The object of the guild channel found in cache or `builtins.None.
        """
        if not isinstance(self.app, traits.CacheAware):
            return None

        return self.app.cache.get_guild_channel(channel)

    def get_emoji(
        self, emoji: snowflakes.SnowflakeishOr[emojis_.CustomEmoji]
    ) -> typing.Optional[emojis_.KnownCustomEmoji]:
        """Get a cached role that belongs to the guild by it's ID or object.

        Parameters
        ----------
        emoji : hikari.snowflakes.SnowflakeishOr[hikari.emojis.CustomEmoji]
            The object or ID of the emoji to get from the cache.

        Returns
        -------
        typing.Optional[hikari.emojis.KnownCustomEmoji]
            The object of the custom emoji if found in cache, else
            `builtins.None`.
        """
        if not isinstance(self.app, traits.CacheAware):
            return None

        return self.app.cache.get_emoji(emoji)

    def get_member(self, user: snowflakes.SnowflakeishOr[users.PartialUser]) -> typing.Optional[Member]:
        """Get a cached member that belongs to the guild by it's user ID or object.

        Parameters
        ----------
        user : hikari.snowflakes.SnowflakeishOr[hikari.users.PartialUser]
            The object or ID of the user to get the cached member for.

        Returns
        -------
        typing.Optional[Member]
            The cached member object if found, else `builtins.None`.
        """
        if not isinstance(self.app, traits.CacheAware):
            return None

        return self.app.cache.get_member(self.id, user)

    def get_my_member(self) -> typing.Optional[Member]:
        """Return the cached member for the bot user in this guild, if known.

        Returns
        -------
        typing.Optional[Member]
            The cached member for this guild, or `builtins.None` if not known.
        """
        if not isinstance(self.app, traits.ShardAware):
            return None

        me = self.app.me
        if me is None:
            return None

        return self.get_member(me.id)

    def get_presence(
        self, user: snowflakes.SnowflakeishOr[users.PartialUser]
    ) -> typing.Optional[presences_.MemberPresence]:
        """Get a cached presence that belongs to the guild by it's user ID or object.

        Parameters
        ----------
        user : hikari.snowflakes.SnowflakeishOr[hikari.users.PartialUser]
            The object or ID of the user to get the cached presence for.

        Returns
        -------
        typing.Optional[hikari.presences.MemberPresence]
            The cached presence object if found, else `builtins.None`.
        """
        if not isinstance(self.app, traits.CacheAware):
            return None

        return self.app.cache.get_presence(self.id, user)

    def get_role(self, role: snowflakes.SnowflakeishOr[PartialRole]) -> typing.Optional[Role]:
        """Get a cached role that belongs to the guild by it's ID or object.

        Parameters
        ----------
        role : hikari.snowflakes.SnowflakeishOr[PartialRole]
            The object or ID of the role to get for this guild from the cache.

        Returns
        -------
        typing.Optional[Role]
            The object of the role found in cache, else `builtins.None`.
        """
        if not isinstance(self.app, traits.CacheAware):
            return None

        return self.app.cache.get_role(role)

    def get_voice_state(
        self, user: snowflakes.SnowflakeishOr[users.PartialUser]
    ) -> typing.Optional[voices_.VoiceState]:
        """Get a cached voice state that belongs to the guild by it's user.

        Parameters
        ----------
        user : hikari.snowflakes.SnowflakeishOr[hikari.users.PartialUser]
            The object or ID of the user to get the cached voice state for.

        Returns
        -------
        typing.Optional[hikari.voices.VoiceState]
            The cached voice state object if found, else `builtins.None`.
        """
        if not isinstance(self.app, traits.CacheAware):
            return None

        return self.app.cache.get_voice_state(self.id, user)

    async def ban(
        self,
        member: snowflakes.SnowflakeishOr[users.PartialUser],
        *,
        delete_message_days: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        """Ban the given user from this guild.

        Parameters
        ----------
        member: hikari.snowflakes.Snowflakeish[hikari.users.PartialUser]
            The guild member to ban from the guild

        Other Parameters
        ----------------
        delete_message_days : hikari.undefined.UndefinedNoneOr[builtins.int]
            If provided, the number of days to delete messages for.
            This must be between 0 and 7.
        reason : hikari.undefined.UndefinedOr[builtins.str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.ForbiddenError
            If you are missing the `BAN_MEMBERS` permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild or user are not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        await self.app.rest.ban_user(self.id, member, delete_message_days=delete_message_days, reason=reason)

    async def unban(
        self,
        member: snowflakes.SnowflakeishOr[users.PartialUser],
        *,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        """Unban the given user from this guild.

        Parameters
        ----------
        member: hikari.snowflakes.Snowflakeish[hikari.users.PartialUser]
            The guild member to unban from the guild

        Other Parameters
        ----------------
        reason : hikari.undefined.UndefinedOr[builtins.str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.ForbiddenError
            If you are missing the `BAN_MEMBERS` permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild or user are not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        await self.app.rest.unban_user(self.id, member, reason=reason)

    async def kick(
        self,
        member: snowflakes.SnowflakeishOr[users.PartialUser],
        *,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        """Kicks the given user from this guild.

        Parameters
        ----------
        member: hikari.snowflakes.Snowflakeish[hikari.users.PartialUser]
            The guild member to ban from the guild

        Other Parameters
        ----------------
        reason : hikari.undefined.UndefinedOr[builtins.str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.ForbiddenError
            If you are missing the `KICK_MEMBERS` permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild or user are not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        await self.app.rest.kick_user(self.id, member, reason=reason)

    async def edit(
        self,
        *,
        name: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        verification_level: undefined.UndefinedOr[GuildVerificationLevel] = undefined.UNDEFINED,
        default_message_notifications: undefined.UndefinedOr[GuildMessageNotificationsLevel] = undefined.UNDEFINED,
        explicit_content_filter_level: undefined.UndefinedOr[GuildExplicitContentFilterLevel] = undefined.UNDEFINED,
        afk_channel: undefined.UndefinedOr[
            snowflakes.SnowflakeishOr[channels_.GuildVoiceChannel]
        ] = undefined.UNDEFINED,
        afk_timeout: undefined.UndefinedOr[time_.Intervalish] = undefined.UNDEFINED,
        icon: undefined.UndefinedNoneOr[files.Resourceish] = undefined.UNDEFINED,
        owner: undefined.UndefinedOr[snowflakes.SnowflakeishOr[users.PartialUser]] = undefined.UNDEFINED,
        splash: undefined.UndefinedNoneOr[files.Resourceish] = undefined.UNDEFINED,
        banner: undefined.UndefinedNoneOr[files.Resourceish] = undefined.UNDEFINED,
        system_channel: undefined.UndefinedNoneOr[
            snowflakes.SnowflakeishOr[channels_.GuildTextChannel]
        ] = undefined.UNDEFINED,
        rules_channel: undefined.UndefinedNoneOr[
            snowflakes.SnowflakeishOr[channels_.GuildTextChannel]
        ] = undefined.UNDEFINED,
        public_updates_channel: undefined.UndefinedNoneOr[
            snowflakes.SnowflakeishOr[channels_.GuildTextChannel]
        ] = undefined.UNDEFINED,
        preferred_locale: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> RESTGuild:
        """Edits the guild.

        Parameters
        ----------
        name : hikari.undefined.UndefinedOr[builtins.str]
            If provided, the new name for the guild.
        verification_level : hikari.undefined.UndefinedOr[hikari.guilds.GuildVerificationLevel]
            If provided, the new verification level.
        default_message_notifications : hikari.undefined.UndefinedOr[hikari.guilds.GuildMessageNotificationsLevel]
            If provided, the new default message notifications level.
        explicit_content_filter_level : hikari.undefined.UndefinedOr[hikari.guilds.GuildExplicitContentFilterLevel]
            If provided, the new explicit content filter level.
        afk_channel : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.channels.GuildVoiceChannel]]
            If provided, the new afk channel. Requires `afk_timeout` to
            be set to work.
        afk_timeout : hikari.undefined.UndefinedOr[hikari.internal.time.Intervalish]
            If provided, the new afk timeout.
        icon : hikari.undefined.UndefinedOr[hikari.files.Resourceish]
            If provided, the new guild icon. Must be a 1024x1024 image or can be
            an animated gif when the guild has the `ANIMATED_ICON` feature.
        owner : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.users.PartialUser]]]
            If provided, the new guild owner.

            !!! warning
                You need to be the owner of the server to use this.
        splash : hikari.undefined.UndefinedNoneOr[hikari.files.Resourceish]
            If provided, the new guild splash. Must be a 16:9 image and the
            guild must have the `INVITE_SPLASH` feature.
        banner : hikari.undefined.UndefinedNoneOr[hikari.files.Resourceish]
            If provided, the new guild banner. Must be a 16:9 image and the
            guild must have the `BANNER` feature.
        system_channel : hikari.undefined.UndefinedNoneOr[hikari.snowflakes.SnowflakeishOr[hikari.channels.GuildTextChannel]]
            If provided, the new system channel.
        rules_channel : hikari.undefined.UndefinedNoneOr[hikari.snowflakes.SnowflakeishOr[hikari.channels.GuildTextChannel]]
            If provided, the new rules channel.
        public_updates_channel : hikari.undefined.UndefinedNoneOr[hikari.snowflakes.SnowflakeishOr[hikari.channels.GuildTextChannel]]
            If provided, the new public updates channel.
        preferred_locale : hikari.undefined.UndefinedNoneOr[builtins.str]
            If provided, the new preferred locale.
        reason : hikari.undefined.UndefinedOr[builtins.str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Returns
        -------
        hikari.guilds.RESTGuild
            The edited guild.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value. Or
            you are missing the
        hikari.errors.ForbiddenError
            If you are missing the `MANAGE_GUILD` permission or if you tried to
            pass ownership without being the server owner.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        return await self.app.rest.edit_guild(
            self.id,
            name=name,
            verification_level=verification_level,
            default_message_notifications=default_message_notifications,
            explicit_content_filter_level=explicit_content_filter_level,
            afk_channel=afk_channel,
            afk_timeout=afk_timeout,
            icon=icon,
            owner=owner,
            splash=splash,
            banner=banner,
            system_channel=system_channel,
            rules_channel=rules_channel,
            public_updates_channel=public_updates_channel,
            preferred_locale=preferred_locale,
            reason=reason
        )

    async def fetch_emojis(self) -> typing.Sequence[emojis_.KnownCustomEmoji]:
        """Fetch the emojis of the guild

        Returns
        -------
        typing.Sequence[hikari.emojis.KnownCustomEmoji]
            The requested emojis.

        Raises
        ------
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """        
        return await self.app.rest.fetch_guild_emojis(self.id)

    async def fetch_emoji(self, emoji: snowflakes.SnowflakeishOr[emojis_.CustomEmoji]) -> emojis_.KnownCustomEmoji:
        """Fetch an emoji from the guild.
        Parameters
        ----------
        emoji : hikari.snowflakes.SnowflakeishOr[hikari.emojis.CustomEmoji]
            The emoji to fetch. This can be a `hikari.emojis.CustomEmoji`
            or the ID of an existing emoji.
        Returns
        -------
        hikari.emojis.KnownCustomEmoji
            The requested emoji.
        Raises
        ------
        hikari.errors.NotFoundError
            If the guild or the emoji are not found.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        return await self.app.rest.fetch_emoji(self.id, emoji)
