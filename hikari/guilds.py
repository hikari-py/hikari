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
"""Application and entities that are used to describe guilds on Discord."""

from __future__ import annotations

__all__: typing.Sequence[str] = (
    "GatewayGuild",
    "Guild",
    "GuildBan",
    "GuildExplicitContentFilterLevel",
    "GuildFeature",
    "GuildIncidents",
    "GuildMFALevel",
    "GuildMemberFlags",
    "GuildMessageNotificationsLevel",
    "GuildNSFWLevel",
    "GuildPremiumTier",
    "GuildPreview",
    "GuildSystemChannelFlag",
    "GuildVerificationLevel",
    "GuildWidget",
    "Integration",
    "IntegrationAccount",
    "IntegrationApplication",
    "IntegrationExpireBehaviour",
    "IntegrationType",
    "Member",
    "PartialApplication",
    "PartialGuild",
    "PartialIntegration",
    "PartialRole",
    "RESTGuild",
    "Role",
    "WelcomeChannel",
    "WelcomeScreen",
)

import typing

import attrs

from hikari import channels as channels_
from hikari import snowflakes
from hikari import stickers
from hikari import traits
from hikari import undefined
from hikari import urls
from hikari import users
from hikari.internal import attrs_extensions
from hikari.internal import deprecation
from hikari.internal import enums
from hikari.internal import routes
from hikari.internal import time
from hikari.internal import typing_extensions

if typing.TYPE_CHECKING:
    import datetime

    from hikari import colors
    from hikari import colours
    from hikari import emojis as emojis_
    from hikari import files
    from hikari import locales
    from hikari import permissions as permissions_
    from hikari import presences as presences_
    from hikari import voices as voices_


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
class GuildOnboardingMode(int, enums.Enum):
    """Defines the criteria used to satisfy Onboarding constraints that are required for enabling."""

    ONBOARDING_DEFAULT = 0
    """Counts only Default Channels towards constraints."""

    ONBOARDING_ADVANCED = 1
    """Counts Default Channels and Questions towards constraints."""


@typing.final
class GuildOnboardingPromptType(int, enums.Enum):
    """Guild Onboarding Prompt Type. This is automatically decided by discord."""

    MULTIPLE_CHOICE = 0
    """Multiple fields you can click at."""

    DROPDOWN = 1
    """Similar to a select menu component."""


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

    TICKETED_EVENTS_ENABLED = "TICKETED_EVENTS_ENABLED"
    """Guild has enabled ticketed events."""

    MONETIZATION_ENABLED = "MONETIZATION_ENABLED"
    """Guild has enabled monetization."""

    MORE_STICKERS = "MORE_STICKERS"
    """Guild has an increased custom stickers slots."""

    CREATOR_MONETIZABLE = "CREATOR_MONETIZABLE_PROVISIONAL"
    """Guild has enabled monetization."""

    CREATOR_STORE_PAGE = "CREATOR_STORE_PAGE"
    """Guild has enabled the store page."""

    ROLE_SUBSCRIPTIONS_ENABLED = "ROLE_SUBSCRIPTIONS_ENABLED"
    """Guild has enabled role subscriptions."""

    ROLE_SUBSCRIPTIONS_AVAILABLE_FOR_PURCHASE = "ROLE_SUBSCRIPTIONS_AVAILABLE_FOR_PURCHASE"
    """Guild has role subscriptions available for purchase."""

    INVITES_DISABLED = "INVITES_DISABLED"
    """Guild has paused invites, preventing new users from joining."""

    RAID_ALERTS_DISABLED = "RAID_ALERTS_DISABLED"
    """Guild has disabled alerts for join raids in the configured safety alerts channel."""


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

    SUPPRESS_USER_JOIN_REPLIES = 1 << 3
    """Suppress displaying a reply button on join notifications."""


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


@typing.final
class GuildNSFWLevel(int, enums.Enum):
    """Represents the NSFW level of a guild."""

    DEFAULT = 0
    """Guild has not been categorized yet."""

    EXPLICIT = 1
    """Guild contains explicit NSFW content."""

    SAFE = 2
    """Guild is safe of NSFW content."""

    AGE_RESTRICTED = 3
    """Guild may contain NSFW content."""


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
class GuildWidget:
    """Represents a guild widget."""

    app: traits.RESTAware = attrs.field(
        repr=False, eq=False, hash=False, metadata={attrs_extensions.SKIP_DEEP_COPY: True}
    )
    """Client application that models may use for procedures."""

    channel_id: snowflakes.Snowflake | None = attrs.field(repr=True)
    """The ID of the channel the invite for this embed targets, if enabled."""

    is_enabled: bool = attrs.field(repr=True)
    """Whether this embed is enabled."""

    async def fetch_channel(self) -> channels_.GuildChannel | None:
        """Fetch the widget channel.

        This will be [`None`][] if not set.

        Returns
        -------
        typing.Optional[hikari.channels.GuildChannel]
            The requested channel.

            You can check the type of the channel by
            using [`isinstance`][].

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
        if not self.channel_id:
            return None

        widget_channel = await self.app.rest.fetch_channel(self.channel_id)
        assert isinstance(widget_channel, channels_.GuildChannel)

        return widget_channel


@typing.final
class GuildMemberFlags(enums.Flag):
    """Represents the flags that a member can have."""

    NONE = 0
    """No flags."""

    DID_REJOIN = 1 << 0
    """Member has left and rejoined the guild."""

    COMPLETED_ONBOARDING = 1 << 1
    """Member has completed onboarding."""

    BYPASSES_VERIFICATION = 1 << 2
    """Member is exempt from guild verification requirements."""

    STARTED_ONBOARDING = 1 << 3
    """Member has started onboarding."""


@attrs.define(kw_only=True, weakref_slot=False)
class GuildIncidents:
    """Represents the incidents of a guild."""

    invites_disabled_until: datetime.datetime | None = attrs.field(repr=True)
    """The datetime when the invites will be enabled again.

    This will be [`None`][] if the invites are not temporarily disabled.

    !!! note
        This is independent of [`hikari.guilds.GuildFeature.INVITES_DISABLED`][] which is
        used to indefinitely disable invites.
    """

    dms_disabled_until: datetime.datetime | None = attrs.field(repr=True)
    """The datetime when direct messages between non-friend guild members will be enabled again.

    This will be [`None`][] if the direct messages are not temporarily disabled.
    """

    dm_spam_detected_at: datetime.datetime | None = attrs.field(repr=True)
    """The datetime when the spam detection was triggered for the current incident session.

    This will be [`None`][] if no spam detection was triggered.
    """

    raid_detected_at: datetime.datetime | None = attrs.field(repr=True)
    """The datetime when the raid was detected for the current incident session.

    This will be [`None`][] if no raid was detected.
    """


@attrs_extensions.with_copy
@attrs.define(eq=False, kw_only=True, weakref_slot=False)
class Member(users.User):
    """Used to represent a guild bound member."""

    guild_id: snowflakes.Snowflake = attrs.field(repr=True)
    """The ID of the guild this member belongs to."""

    is_deaf: undefined.UndefinedOr[bool] = attrs.field(repr=False)
    """[`True`][] if this member is deafened in the current voice channel.

    This will be [`hikari.undefined.UNDEFINED`][] if it's state is
    unknown.
    """

    is_mute: undefined.UndefinedOr[bool] = attrs.field(repr=False)
    """[`True`][] if this member is muted in the current voice channel.

    This will be [`hikari.undefined.UNDEFINED`][] if it's state is unknown.
    """

    is_pending: undefined.UndefinedOr[bool] = attrs.field(repr=False)
    """Whether the user has passed the guild's membership screening requirements.

    This will be [`hikari.undefined.UNDEFINED`][] if it's state is unknown.
    """

    joined_at: datetime.datetime | None = attrs.field(repr=True)
    """The datetime of when this member joined the guild they belong to.

    This will be [`None`][] for guest members that have been temporarily
    invited.
    """

    nickname: str | None = attrs.field(repr=True)
    """This member's nickname.

    This will be [`None`][] if not set.
    """

    premium_since: datetime.datetime | None = attrs.field(repr=False)
    """The datetime of when this member started "boosting" this guild.

    Will be [`None`][] if the member is not a premium user.
    """

    raw_communication_disabled_until: datetime.datetime | None = attrs.field(repr=False)
    """The datetime when this member's timeout will expire.

     Will be [`None`][] if the member is not timed out.

     !!! note
        The datetime might be in the past, so it is recommended to use
        [`hikari.guilds.Member.communication_disabled_until`][] method to check if the member is timed
        out at the time of the call.
     """

    role_ids: typing.Sequence[snowflakes.Snowflake] = attrs.field(repr=False)
    """A sequence of the IDs of the member's current roles."""

    # This is technically optional, since UPDATE MEMBER and MESSAGE CREATE
    # events do not inject the user into the member payload, but specify it
    # separately. However, to get around this inconsistency, we force the
    # entity factory to always provide the user object in these cases, so we
    # can assume this is always set, and thus we are always able to get info
    # such as the ID of the user this member represents.
    user: users.User = attrs.field(repr=True)
    """This member's corresponding user object."""

    guild_avatar_decoration: users.AvatarDecoration | None = attrs.field(eq=False, hash=False, repr=False)
    """Hash of the member's guild avatar decoration if set, else [`None`][].

    !!! note
        This takes precedence over [`hikari.guilds.Member.avatar_decoration`][] in the client.
    """

    guild_avatar_hash: str | None = attrs.field(eq=False, hash=False, repr=False)
    """Hash of the member's guild avatar if set, else [`None`][].

    !!! note
        This takes precedence over [`hikari.guilds.Member.avatar_hash`][] in the client.
    """

    guild_banner_hash: str | None = attrs.field(eq=False, hash=False, repr=False)
    """Hash of the member's guild banner if set, else [`None`][].

    !!! note
        This takes precedence over [`hikari.guilds.Member.banner_hash`][] in the client.
    """

    guild_flags: GuildMemberFlags | int = attrs.field(eq=False, hash=False, repr=False)
    """The flags this member has in the guild."""

    @property
    @typing_extensions.override
    def app(self) -> traits.RESTAware:
        """Return the app that is bound to the user object."""
        return self.user.app

    @property
    @typing_extensions.override
    def avatar_decoration(self) -> users.AvatarDecoration | None:
        return self.user.avatar_decoration

    @property
    @typing_extensions.override
    def avatar_hash(self) -> str | None:
        return self.user.avatar_hash

    @property
    @typing_extensions.override
    @deprecation.deprecated("Use 'make_avatar_url' instead.")
    def avatar_url(self) -> files.URL | None:
        deprecation.warn_deprecated(
            "avatar_url", removal_version="2.5.0", additional_info="Use 'make_avatar_url' instead."
        )
        return self.user.make_avatar_url()

    @property
    def guild_avatar_url(self) -> files.URL | None:
        """Guild Avatar URL for the user, if they have one set."""
        deprecation.warn_deprecated(
            "guild_avatar_url", removal_version="2.5.0", additional_info="Use 'make_guild_avatar_url' instead."
        )
        return self.make_guild_avatar_url()

    @property
    @typing_extensions.override
    def default_avatar_url(self) -> files.URL:
        return self.user.default_avatar_url

    @property
    @typing_extensions.override
    def display_avatar_decoration(self) -> users.AvatarDecoration | None:
        return self.guild_avatar_decoration or self.user.display_avatar_decoration

    @property
    @typing_extensions.override
    def display_avatar_url(self) -> files.URL:
        return self.make_guild_avatar_url() or self.user.display_avatar_url

    @property
    @typing_extensions.override
    def banner_hash(self) -> str | None:
        return self.user.banner_hash

    @property
    @typing_extensions.override
    @deprecation.deprecated("Use 'make_banner_url' instead.")
    def banner_url(self) -> files.URL | None:
        deprecation.warn_deprecated(
            "banner_url", removal_version="2.5.0", additional_info="Use 'make_banner_url' instead."
        )
        return self.user.make_banner_url()

    @property
    def guild_banner_url(self) -> files.URL | None:
        """Guild Banner URL for the user, if they have one set."""
        deprecation.warn_deprecated(
            "guild_banner_url", removal_version="2.5.0", additional_info="Use 'make_guild_banner_url' instead."
        )
        return self.make_guild_banner_url()

    @property
    @typing_extensions.override
    def display_banner_url(self) -> files.URL | None:
        return self.make_guild_banner_url() or self.user.display_banner_url

    @property
    @typing_extensions.override
    def accent_color(self) -> colors.Color | None:
        return self.user.accent_color

    @property
    @typing_extensions.override
    def discriminator(self) -> str:
        return self.user.discriminator

    @property
    @typing_extensions.override
    def display_name(self) -> str:
        """Return the member's display name.

        If the member has a nickname, this will return that nickname.
        If the user has a global name, this will return that global name.
        If the user has neither, the username will be returned instead.

        See Also
        --------
        Nickname: [`Member.nickname`][].
        Username: [`Member.username`][].
        Globalname: [`Member.global_name`][].
        """
        return self.nickname or self.global_name or self.username

    @property
    @typing_extensions.override
    def flags(self) -> users.UserFlag:
        return self.user.flags

    @property
    @typing_extensions.override
    def id(self) -> snowflakes.Snowflake:
        return self.user.id

    @property
    @typing_extensions.override
    def is_bot(self) -> bool:
        return self.user.is_bot

    @property
    @typing_extensions.override
    def is_system(self) -> bool:
        return self.user.is_system

    @property
    @typing_extensions.override
    def mention(self) -> str:
        return self.user.mention

    def communication_disabled_until(self) -> datetime.datetime | None:
        """Return when the timeout for this member ends.

        Unlike `raw_communication_disabled_until`, this will always be
        [`None`][] if the member is not currently timed out.

        !!! note
            The output of this function can depend based on when
            the function is called.
        """
        if (
            self.raw_communication_disabled_until is not None
            and self.raw_communication_disabled_until > time.utc_datetime()
        ):
            return self.raw_communication_disabled_until
        return None

    def get_guild(self) -> Guild | None:
        """Return the guild associated with this member.

        Returns
        -------
        typing.Optional[hikari.guilds.Guild]
            The linked guild object or [`None`][] if it's not cached.
        """
        if not isinstance(self.user.app, traits.CacheAware):
            return None

        return self.user.app.cache.get_guild(self.guild_id)

    def get_presence(self) -> presences_.MemberPresence | None:
        """Get the cached presence for this member, if known.

        Presence info includes user status and activities.

        This requires the [`hikari.intents.Intents.GUILD_PRESENCES`][] intent to be enabled.

        Returns
        -------
        typing.Optional[hikari.presences.MemberPresence]
            The member presence, or [`None`][] if not known.
        """
        if not isinstance(self.user.app, traits.CacheAware):
            return None

        return self.user.app.cache.get_presence(self.guild_id, self.user.id)

    def get_roles(self) -> typing.Sequence[Role]:
        """Return the roles the user has.

        This will be empty if the roles are missing from the cache.

        Returns
        -------
        typing.Sequence[hikari.guilds.Role]
            The roles the users has.
        """
        if not isinstance(self.user.app, traits.CacheAware):
            return []

        return [role for role_id in self.role_ids if (role := self.user.app.cache.get_role(role_id))]

    def get_top_role(self) -> Role | None:
        """Return the highest role the member has.

        Returns
        -------
        typing.Optional[hikari.guilds.Role]
            [`None`][] if the cache is missing the roles information or
            the highest role the user has.
        """
        roles = sorted(self.get_roles(), key=lambda r: r.position, reverse=True)

        try:
            return next(iter(roles))
        except StopIteration:
            return None

    @property
    @typing_extensions.override
    def username(self) -> str:
        return self.user.username

    @property
    @typing_extensions.override
    def global_name(self) -> str | None:
        return self.user.global_name

    @typing_extensions.override
    def make_avatar_url(
        self,
        *,
        file_format: undefined.UndefinedOr[
            typing.Literal["PNG", "JPEG", "JPG", "WEBP", "AWEBP", "GIF"]
        ] = undefined.UNDEFINED,
        size: int = 4096,
        lossless: bool = True,
        ext: str | None | undefined.UndefinedType = undefined.UNDEFINED,
    ) -> files.URL | None:
        return self.user.make_avatar_url(file_format=file_format, size=size, lossless=lossless, ext=ext)

    def make_guild_avatar_url(
        self,
        *,
        file_format: undefined.UndefinedOr[
            typing.Literal["PNG", "JPEG", "JPG", "WEBP", "AWEBP", "GIF"]
        ] = undefined.UNDEFINED,
        size: int = 4096,
        lossless: bool = True,
        ext: str | None | undefined.UndefinedType = undefined.UNDEFINED,
    ) -> files.URL | None:
        """Generate the guild-specific avatar URL for this member, if set.

        If no guild-specific avatar is set, this returns [`None`][].

        Parameters
        ----------
        file_format
            The format to use for this URL.

            Supports `PNG`, `JPEG`, `JPG`, `WEBP`, `AWEBP` and `GIF`.

            If not specified, the format will be determined based on
            whether the avatar is animated or not.
        size
            The size to set for the URL;
            Can be any power of two between `16` and `4096`;
        lossless
            Whether to return a lossless or compressed WEBP image;
            This is ignored if `file_format` is not `WEBP` or `AWEBP`.
        ext
            The ext to use for this URL.
            Supports `png`, `jpeg`, `jpg`, `webp` and `gif` (when
            animated).

            If [`None`][], then the correct default extension is
            determined based on whether the avatar is animated or not.

            !!! deprecated 2.4.0
                This has been replaced with the `file_format` argument.

        Returns
        -------
        typing.Optional[hikari.files.URL]
            The URL, or [`None`][] if no avatar is set.

        Raises
        ------
        TypeError
            If an invalid format is passed for `file_format`;
            If an animated format is requested for a static avatar.
        ValueError
            If `size` is specified but is not a power of two or not between 16 and 4096.
        """
        if self.guild_avatar_hash is None:
            return None

        if ext:
            deprecation.warn_deprecated(
                "ext", removal_version="2.5.0", additional_info="Use 'file_format' argument instead."
            )
            file_format = ext.upper()  # type: ignore[assignment]

        if not file_format:
            file_format = "GIF" if self.guild_avatar_hash.startswith("a_") else "PNG"

        return routes.CDN_MEMBER_AVATAR.compile_to_file(
            urls.CDN_URL,
            guild_id=self.guild_id,
            user_id=self.id,
            hash=self.guild_avatar_hash,
            size=size,
            file_format=file_format,
            lossless=lossless,
        )

    @typing_extensions.override
    def make_banner_url(
        self,
        *,
        file_format: undefined.UndefinedOr[
            typing.Literal["PNG", "JPEG", "JPG", "WEBP", "AWEBP", "GIF"]
        ] = undefined.UNDEFINED,
        size: int = 4096,
        lossless: bool = True,
        ext: str | None | undefined.UndefinedType = undefined.UNDEFINED,
    ) -> files.URL | None:
        return self.user.make_banner_url(file_format=file_format, size=size, lossless=lossless, ext=ext)

    def make_guild_banner_url(
        self,
        *,
        file_format: undefined.UndefinedOr[
            typing.Literal["PNG", "JPEG", "JPG", "WEBP", "AWEBP", "GIF"]
        ] = undefined.UNDEFINED,
        size: int = 4096,
        lossless: bool = True,
        ext: str | None | undefined.UndefinedType = undefined.UNDEFINED,
    ) -> files.URL | None:
        """Generate the guild-specific banner URL for this member, if set.

        If no guild-specific banner is set, this returns [`None`][].

        Parameters
        ----------
        file_format
            The format to use for this URL.

            Supports `PNG`, `JPEG`, `JPG`, `WEBP`, `AWEBP` and `GIF`.

            If not specified, the format will be determined based on
            whether the banner is animated or not.
        size
            The size to set for the URL;
            Can be any power of two between `16` and `4096`;
        lossless
            Whether to return a lossless or compressed WEBP image;
            This is ignored if `file_format` is not `WEBP` or `AWEBP`.
        ext
            The ext to use for this URL.
            Supports `png`, `jpeg`, `jpg`, `webp` and `gif` (when
            animated).

            If [`None`][], then the correct default extension is
            determined based on whether the banner is animated or not.

            !!! deprecated 2.4.0
                This has been replaced with the `file_format` argument.

        Returns
        -------
        typing.Optional[hikari.files.URL]
            The URL to the banner, or [`None`][] if not present.

        Raises
        ------
        TypeError
            If an invalid format is passed for `file_format`;
            If an animated format is requested for a static banner.
        ValueError
            If `size` is specified but is not a power of two or not between 16 and 4096.
        """
        if self.guild_banner_hash is None:
            return None

        if ext:
            deprecation.warn_deprecated(
                "ext", removal_version="2.5.0", additional_info="Use 'file_format' argument instead."
            )
            file_format = ext.upper()  # type: ignore[assignment]

        if not file_format:
            file_format = "GIF" if self.guild_banner_hash.startswith("a_") else "PNG"

        return routes.CDN_MEMBER_BANNER.compile_to_file(
            urls.CDN_URL,
            guild_id=self.guild_id,
            user_id=self.id,
            hash=self.guild_banner_hash,
            size=size,
            file_format=file_format,
            lossless=lossless,
        )

    @typing_extensions.override
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
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        return await self.user.app.rest.fetch_member(self.guild_id, self.user.id)

    @typing_extensions.override
    async def fetch_dm_channel(self) -> channels_.DMChannel:
        return await self.user.fetch_dm_channel()

    async def fetch_roles(self) -> typing.Sequence[Role]:
        """Fetch an up-to-date view of this member's roles from the API.

        Returns
        -------
        typing.Sequence[hikari.guilds.Role]
            An up-to-date view of this member's roles.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the member is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        fetched_roles = await self.app.rest.fetch_roles(self.guild_id)
        return [role for role in fetched_roles if role.id in self.role_ids]

    async def ban(
        self,
        *,
        delete_message_seconds: undefined.UndefinedOr[time.Intervalish] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        """Ban this member from this guild.

        Parameters
        ----------
        delete_message_seconds
            If provided, the number of seconds to delete messages for.
            This can be represented as either an int/float between 0 and 604800 (7 days), or
            a [`datetime.timedelta`][] object.
        reason
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.BAN_MEMBERS`][] permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild or user are not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        await self.user.app.rest.ban_user(
            self.guild_id, self.user.id, delete_message_seconds=delete_message_seconds, reason=reason
        )

    async def unban(self, *, reason: undefined.UndefinedOr[str] = undefined.UNDEFINED) -> None:
        """Unban this member from the guild.

        Parameters
        ----------
        reason
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.BAN_MEMBERS`][] permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild or user are not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        await self.user.app.rest.unban_user(self.guild_id, self.user.id, reason=reason)

    async def kick(self, *, reason: undefined.UndefinedOr[str] = undefined.UNDEFINED) -> None:
        """Kick this member from this guild.

        Parameters
        ----------
        reason
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.KICK_MEMBERS`][] permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild or user are not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        await self.user.app.rest.kick_user(self.guild_id, self.user.id, reason=reason)

    async def add_role(
        self, role: snowflakes.SnowflakeishOr[PartialRole], *, reason: undefined.UndefinedOr[str] = undefined.UNDEFINED
    ) -> None:
        """Add a role to the member.

        Parameters
        ----------
        role
            The role to add. This may be the object or the
            ID of an existing role.
        reason
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.MANAGE_ROLES`][] permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild, user or role are not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        await self.user.app.rest.add_role_to_member(self.guild_id, self.user.id, role, reason=reason)

    async def remove_role(
        self, role: snowflakes.SnowflakeishOr[PartialRole], *, reason: undefined.UndefinedOr[str] = undefined.UNDEFINED
    ) -> None:
        """Remove a role from the member.

        Parameters
        ----------
        role
            The role to remove. This may be the object or the
            ID of an existing role.
        reason
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.MANAGE_ROLES`][] permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild, user or role are not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        await self.user.app.rest.remove_role_from_member(self.guild_id, self.user.id, role, reason=reason)

    async def edit(
        self,
        *,
        nickname: undefined.UndefinedNoneOr[str] = undefined.UNDEFINED,
        roles: undefined.UndefinedOr[snowflakes.SnowflakeishSequence[PartialRole]] = undefined.UNDEFINED,
        mute: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        deaf: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        voice_channel: undefined.UndefinedNoneOr[
            snowflakes.SnowflakeishOr[channels_.GuildVoiceChannel]
        ] = undefined.UNDEFINED,
        communication_disabled_until: undefined.UndefinedNoneOr[datetime.datetime] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> Member:
        """Edit the member.

        Parameters
        ----------
        nickname
            If provided, the new nick for the member. If [`None`][],
            will remove the members nick.

            Requires the [`hikari.permissions.Permissions.MANAGE_NICKNAMES`][] permission.
        roles
            If provided, the new roles for the member.

            Requires the [`hikari.permissions.Permissions.MANAGE_ROLES`][] permission.
        mute
            If provided, the new server mute state for the member.

            Requires the [`hikari.permissions.Permissions.MUTE_MEMBERS`][] permission.
        deaf
            If provided, the new server deaf state for the member.

            Requires the [`hikari.permissions.Permissions.DEAFEN_MEMBERS`][] permission.
        voice_channel
            If provided, [`None`][] or the object or the ID of
            an existing voice channel to move the member to.
            If [`None`][], will disconnect the member from voice.

            Requires the [`hikari.permissions.Permissions.MOVE_MEMBERS`][] permission
            and the [`hikari.permissions.Permissions.CONNECT`][] permission in the
            original voice channel and the target voice channel.

            !!! note
                If the member is not in a voice channel, this will
                take no effect.
        communication_disabled_until
            If provided, the datetime when the timeout (disable communication)
            of the member expires, up to 28 days in the future, or [`None`][]
            to remove the timeout from the member.

            Requires the [`hikari.permissions.Permissions.MODERATE_MEMBERS`][] permission.
        reason
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Returns
        -------
        hikari.guilds.Member
            Object of the member that was updated.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.ForbiddenError
            If you are missing a permission to do an action.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild or the user are not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        return await self.user.app.rest.edit_member(
            self.guild_id,
            self.user.id,
            nickname=nickname,
            roles=roles,
            mute=mute,
            deaf=deaf,
            voice_channel=voice_channel,
            communication_disabled_until=communication_disabled_until,
            reason=reason,
        )

    @typing_extensions.override
    def __str__(self) -> str:
        return str(self.user)

    @typing_extensions.override
    def __hash__(self) -> int:
        return hash(self.user)

    @typing_extensions.override
    def __eq__(self, other: object) -> bool:
        return self.user == other


@attrs_extensions.with_copy
@attrs.define(unsafe_hash=True, kw_only=True, weakref_slot=False)
class PartialRole(snowflakes.Unique):
    """Represents a partial guild bound role object."""

    app: traits.RESTAware = attrs.field(
        repr=False, eq=False, hash=False, metadata={attrs_extensions.SKIP_DEEP_COPY: True}
    )
    """Client application that models may use for procedures."""

    id: snowflakes.Snowflake = attrs.field(hash=True, repr=True)
    """The ID of this entity."""

    name: str = attrs.field(eq=False, hash=False, repr=True)
    """The role's name."""

    @property
    def mention(self) -> str:
        """Return a raw mention string for the role."""
        return f"<@&{self.id}>"

    @typing_extensions.override
    def __str__(self) -> str:
        return self.name


@attrs.define(unsafe_hash=True, kw_only=True, weakref_slot=False)
class Role(PartialRole):
    """Represents a guild bound role object."""

    color: colors.Color = attrs.field(eq=False, hash=False, repr=True)
    """The colour of this role.

    This will be applied to a member's name in chat if it's their top coloured role.
    """

    guild_id: snowflakes.Snowflake = attrs.field(eq=False, hash=False, repr=True)
    """The ID of the guild this role belongs to."""

    is_hoisted: bool = attrs.field(eq=False, hash=False, repr=True)
    """Whether this role is hoisting the members it's attached to in the member list.

    Members will be hoisted under their highest role where this is set to [`True`][].
    """

    icon_hash: str | None = attrs.field(eq=False, hash=False, repr=False)
    """Hash of the role's icon if set, else [`None`][]."""

    unicode_emoji: emojis_.UnicodeEmoji | None = attrs.field(eq=False, hash=False, repr=False)
    """Role's icon as an unicode emoji if set, else [`None`][]."""

    is_managed: bool = attrs.field(eq=False, hash=False, repr=False)
    """Whether this role is managed by an integration."""

    is_mentionable: bool = attrs.field(eq=False, hash=False, repr=False)
    """Whether this role can be mentioned by all regardless of permissions."""

    permissions: permissions_.Permissions = attrs.field(eq=False, hash=False, repr=False)
    """The guild wide permissions this role gives to the members it's attached to.

    This may be overridden by channel overwrites.
    """

    position: int = attrs.field(eq=False, hash=False, repr=True)
    """The position of this role in the role hierarchy.

    This will start at `0` for the lowest role (@everyone)
    and increase as you go up the hierarchy.
    """

    bot_id: snowflakes.Snowflake | None = attrs.field(eq=False, hash=False, repr=True)
    """The ID of the bot this role belongs to.

    If [`None`][], this is not a bot role.
    """

    integration_id: snowflakes.Snowflake | None = attrs.field(eq=False, hash=False, repr=True)
    """The ID of the integration this role belongs to.

    If [`None`][], this is not a integration role.
    """

    is_premium_subscriber_role: bool = attrs.field(eq=False, hash=False, repr=True)
    """Whether this role is the guild's nitro subscriber role."""

    subscription_listing_id: snowflakes.Snowflake | None = attrs.field(eq=False, hash=False, repr=True)
    """The ID of this role's subscription SKU and listing.

    If [`None`][], this is not a purchasable role.
    """

    is_available_for_purchase: bool = attrs.field(eq=False, hash=False, repr=True)
    """Whether this role is available for purchase."""

    is_guild_linked_role: bool = attrs.field(eq=False, hash=False, repr=True)
    """Whether this role is a linked role in the guild."""

    @property
    def colour(self) -> colours.Colour:
        """Alias for the `color` field."""
        return self.color

    @property
    @deprecation.deprecated("Use 'make_icon_url' instead.")
    def icon_url(self) -> files.URL | None:
        """Role icon URL, if there is one."""
        deprecation.warn_deprecated("icon_url", removal_version="2.5.0", additional_info="Use 'make_icon_url' instead.")
        return self.make_icon_url()

    @property
    @typing_extensions.override
    def mention(self) -> str:
        """Return a raw mention string for the role.

        When this role represents @everyone mentions will only work if
        `mentions_everyone` is [`True`][].
        """
        if self.guild_id == self.id:
            return "@everyone"

        return super().mention

    def make_icon_url(
        self,
        *,
        file_format: typing.Literal["PNG", "JPEG", "JPG", "WEBP"] = "PNG",
        size: int = 4096,
        lossless: bool = True,
        ext: str | None | undefined.UndefinedType = undefined.UNDEFINED,
    ) -> files.URL | None:
        """Generate the icon URL for this role, if set.

        If no icon is set, this returns [`None`][].

        Parameters
        ----------
        file_format
            The format to use for this URL.

            Supports `PNG`, `JPEG`, `JPG`, and `WEBP`.

            If not specified, the format will be `PNG`.
        size
            The size to set for the URL;
            Can be any power of two between `16` and `4096`;
        lossless
            Whether to return a lossless or compressed WEBP image;
            This is ignored if `file_format` is not `WEBP`.
        ext
            The extension to use for this URL.
            Supports `png`, `jpeg`, `jpg` and `webp`.

            !!! deprecated 2.4.0
                This has been replaced with the `file_format` argument.

        Returns
        -------
        typing.Optional[hikari.files.URL]
            The URL, or [`None`][] if no icon is set.

        Raises
        ------
        TypeError
            If an invalid format is passed for `file_format`.
        ValueError
            If `size` is specified but is not a power of two or not between 16 and 4096.
        """
        if self.icon_hash is None:
            return None

        if ext:
            deprecation.warn_deprecated(
                "ext", removal_version="2.5.0", additional_info="Use 'file_format' argument instead."
            )
            file_format = ext.upper()  # type: ignore[assignment]

        return routes.CDN_ROLE_ICON.compile_to_file(
            urls.CDN_URL, role_id=self.id, hash=self.icon_hash, size=size, file_format=file_format, lossless=lossless
        )


@typing.final
class IntegrationType(str, enums.Enum):
    """The integration type."""

    TWITCH = "twitch"
    """Twitch."""

    YOUTUBE = "youtube"
    """Youtube."""

    DISCORD_BOT = "discord"
    """Discord bot."""

    GUILD_SUBSCRIPTION = "guild_subscription"
    """Guild subscription."""


@typing.final
class IntegrationExpireBehaviour(int, enums.Enum):
    """Behavior for expiring integration subscribers."""

    REMOVE_ROLE = 0
    """Remove the role."""

    KICK = 1
    """Kick the subscriber."""


@attrs_extensions.with_copy
@attrs.define(unsafe_hash=True, kw_only=True, weakref_slot=False)
class IntegrationAccount:
    """An account that's linked to an integration."""

    id: str = attrs.field(hash=True, repr=True)
    """The string ID of this (likely) third party account."""

    name: str = attrs.field(eq=False, hash=False, repr=True)
    """The name of this account."""

    @typing_extensions.override
    def __str__(self) -> str:
        return self.name


# This is here rather than in applications.py to avoid circular imports
@attrs_extensions.with_copy
@attrs.define(unsafe_hash=True, kw_only=True, weakref_slot=False)
class PartialApplication(snowflakes.Unique):
    """A partial representation of a Discord application."""

    id: snowflakes.Snowflake = attrs.field(hash=True, repr=True)
    """The ID of this entity."""

    name: str = attrs.field(eq=False, hash=False, repr=True)
    """The name of this application."""

    description: str | None = attrs.field(eq=False, hash=False, repr=False)
    """The description of this application, if any."""

    icon_hash: str | None = attrs.field(eq=False, hash=False, repr=False)
    """The CDN hash of this application's icon, if set."""

    @typing_extensions.override
    def __str__(self) -> str:
        return self.name

    @property
    @deprecation.deprecated("Use 'make_icon_url' instead.")
    def icon_url(self) -> files.URL | None:
        """App icon URL, if there is one."""
        deprecation.warn_deprecated("icon_url", removal_version="2.5.0", additional_info="Use 'make_icon_url' instead")
        return self.make_icon_url()

    def make_icon_url(
        self,
        *,
        file_format: typing.Literal["PNG", "JPEG", "JPG", "WEBP"] = "PNG",
        size: int = 4096,
        lossless: bool = True,
        ext: str | None | undefined.UndefinedType = undefined.UNDEFINED,
    ) -> files.URL | None:
        """Generate the icon URL for this application, if set.

        If no icon is set, this returns [`None`][].

        Parameters
        ----------
        file_format
            The format to use for this URL.

            Supports `PNG`, `JPEG`, `JPG`, and `WEBP`.

            If not specified, the format will be `PNG`.
        size
            The size to set for the URL;
            Can be any power of two between `16` and `4096`;
        lossless
            Whether to return a lossless or compressed WEBP image;
            This is ignored if `file_format` is not `WEBP`.
        ext
            The extension to use for this URL.
            Supports `png`, `jpeg`, `jpg` and `webp`.

            !!! deprecated 2.4.0
                This has been replaced with the `file_format` argument.

        Returns
        -------
        typing.Optional[hikari.files.URL]
            The URL, or [`None`][] if no icon exists.

        Raises
        ------
        TypeError
            If an invalid format is passed for `file_format`.
        ValueError
            If `size` is specified but is not a power of two or not between 16 and 4096.
        """
        if self.icon_hash is None:
            return None

        if ext:
            deprecation.warn_deprecated(
                "ext", removal_version="2.5.0", additional_info="Use 'file_format' argument instead."
            )
            file_format = ext.upper()  # type: ignore[assignment]

        return routes.CDN_APPLICATION_ICON.compile_to_file(
            urls.CDN_URL,
            application_id=self.id,
            hash=self.icon_hash,
            size=size,
            file_format=file_format,
            lossless=lossless,
        )


@attrs_extensions.with_copy
@attrs.define(unsafe_hash=True, kw_only=True, weakref_slot=False)
class IntegrationApplication(PartialApplication):
    """An application that's linked to an integration."""

    bot: users.User | None = attrs.field(eq=False, hash=False, repr=False)
    """The bot associated with this application."""


@attrs_extensions.with_copy
@attrs.define(unsafe_hash=True, kw_only=True, weakref_slot=False)
class PartialIntegration(snowflakes.Unique):
    """A partial representation of an integration, found in audit logs."""

    account: IntegrationAccount = attrs.field(eq=False, hash=False, repr=False)
    """The account connected to this integration."""

    id: snowflakes.Snowflake = attrs.field(hash=True, repr=True)
    """The ID of this entity."""

    name: str = attrs.field(eq=False, hash=False, repr=True)
    """The name of this integration."""

    type: IntegrationType | str = attrs.field(eq=False, hash=False, repr=True)
    """The type of this integration."""

    @typing_extensions.override
    def __str__(self) -> str:
        return self.name


@attrs.define(unsafe_hash=True, kw_only=True, weakref_slot=False)
class Integration(PartialIntegration):
    """Represents a guild integration object."""

    guild_id: snowflakes.Snowflake = attrs.field()
    """The ID of the guild this integration belongs to."""

    expire_behavior: IntegrationExpireBehaviour | int | None = attrs.field(eq=False, hash=False, repr=False)
    """How members should be treated after their connected subscription expires.

    This will not be enacted until after `GuildIntegration.expire_grace_period`
    passes.

    !!! note
        This will always be [`None`][] for Discord integrations.
    """

    expire_grace_period: datetime.timedelta | None = attrs.field(eq=False, hash=False, repr=False)
    """How many days users with expired subscriptions are given until the expire behavior is enacted out on them.

    !!! note
        This will always be [`None`][] for Discord integrations.
    """

    is_enabled: bool = attrs.field(eq=False, hash=False, repr=True)
    """Whether this integration is enabled."""

    is_syncing: bool | None = attrs.field(eq=False, hash=False, repr=False)
    """Whether this integration is syncing subscribers/emojis."""

    is_emojis_enabled: bool | None = attrs.field(eq=False, hash=False, repr=False)
    """Whether users under this integration are allowed to use it's custom emojis."""

    is_revoked: bool | None = attrs.field(eq=False, hash=False, repr=False)
    """Whether the integration has been revoked."""

    last_synced_at: datetime.datetime | None = attrs.field(eq=False, hash=False, repr=False)
    """The datetime of when this integration's subscribers were last synced."""

    role_id: snowflakes.Snowflake | None = attrs.field(eq=False, hash=False, repr=False)
    """The ID of the managed role used for this integration's subscribers."""

    user: users.User | None = attrs.field(eq=False, hash=False, repr=False)
    """The user this integration belongs to."""

    subscriber_count: int | None = attrs.field(eq=False, hash=False, repr=False)
    """The number of subscribers this integration has."""

    application: IntegrationApplication | None = attrs.field(eq=False, hash=False, repr=False)
    """The bot/OAuth2 application associated with this integration.

    !!! note
        This is only available for Discord integrations.
    """


@attrs_extensions.with_copy
@attrs.define(weakref_slot=False)
class WelcomeChannel:
    """Used to represent channels on guild welcome screens."""

    channel_id: snowflakes.Snowflake = attrs.field(hash=False, repr=True)
    """ID of the channel shown in the welcome screen."""

    description: str = attrs.field(hash=False, repr=False)
    """The description shown for this channel."""

    emoji_name: str | emojis_.UnicodeEmoji | None = attrs.field(default=None, kw_only=True, hash=False, repr=True)
    """The emoji shown in the welcome screen channel if set to a unicode emoji.

    !!! warning
        While it may also be present for custom emojis, this is neither guaranteed
        to be provided nor accurate.
    """

    emoji_id: snowflakes.Snowflake | None = attrs.field(default=None, kw_only=True, hash=False, repr=True)
    """ID of the emoji shown in the welcome screen channel if it's set to a custom emoji."""


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
class WelcomeScreen:
    """Used to represent guild welcome screens on Discord."""

    description: str | None = attrs.field(hash=False, repr=True)
    """The guild's description shown in the welcome screen."""

    channels: typing.Sequence[WelcomeChannel] = attrs.field(hash=False, repr=True)
    """An array of up to 5 of the channels shown in the welcome screen."""


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
class GuildOnboarding:
    """Used to represent the Guild Onboarding Object."""

    guild_id: snowflakes.Snowflake = attrs.field(hash=True, repr=True)
    """The ID of the Guild this Onboarding belongs to."""

    default_channel_ids: typing.Sequence[snowflakes.Snowflake] = attrs.field(hash=False, repr=True)
    """Channel IDs that members get opted into automatically."""

    enabled: bool = attrs.field(hash=False, repr=True)
    """Whether onboarding is enabled in the guild."""

    mode: GuildOnboardingMode = attrs.field(hash=False, repr=True)
    """Current mode of onboarding."""

    prompts: typing.Sequence[GuildOnboardingPrompt] = attrs.field(hash=False, repr=True)
    """Prompts shown during onboarding and in customize community."""


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
class GuildOnboardingPromptOption(snowflakes.Unique):
    """Used to represent a Guild Onboarding Prompt Option."""

    id: snowflakes.Snowflake = attrs.field(hash=True, repr=True)
    """The ID of the option"""

    channel_ids: typing.Sequence[snowflakes.Snowflake] = attrs.field(hash=False, repr=True)
    """The IDs of the channels a user is opted into when selecting this option."""

    role_ids: typing.Sequence[snowflakes.Snowflake] = attrs.field(hash=False, repr=True)
    """The IDs of the roles a user will get assigned when selecting this option."""

    title: str = attrs.field(hash=False, repr=True)
    """The title of the option."""

    description: str | None = attrs.field(hash=False, repr=True)
    """The description of the option."""

    emoji: emojis_.Emoji = attrs.field(hash=False, repr=False)
    """Emoji of the option."""


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
class GuildOnboardingPrompt(snowflakes.Unique):
    """Used to represent a Guild Onboarding Prompt."""

    id: snowflakes.Snowflake = attrs.field(hash=True, repr=True)
    """The ID of the prompt."""

    type: GuildOnboardingPromptType = attrs.field(hash=False, repr=True)
    """The type of the prompt."""

    options: typing.Sequence[GuildOnboardingPromptOption] = attrs.field(hash=False, repr=True)
    """The options of the prompt."""

    title: str = attrs.field(hash=False, repr=True)
    """The title of the prompt."""

    single_select: bool = attrs.field(hash=False, repr=True)
    """Indicates whether users are limited to selecting one option for the prompt."""

    required: bool = attrs.field(hash=False, repr=True)
    """Indicates whether the prompt is required before a user completes the onboarding flow."""

    in_onboarding: bool = attrs.field(hash=False, repr=True)
    """Indicates whether the prompt is present in the onboarding flow.

    If [`False`][], the prompt will only appear in the Channels & Roles tab
    """


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
class GuildBan:
    """Used to represent guild bans."""

    reason: str | None = attrs.field(repr=True)
    """The reason for this ban, will be [`None`][] if no reason was given."""

    user: users.User = attrs.field(repr=True)
    """The object of the user this ban targets."""


@attrs_extensions.with_copy
@attrs.define(unsafe_hash=True, kw_only=True, weakref_slot=False)
class PartialGuild(snowflakes.Unique):
    """Base object for any partial guild objects."""

    app: traits.RESTAware = attrs.field(
        repr=False, eq=False, hash=False, metadata={attrs_extensions.SKIP_DEEP_COPY: True}
    )
    """Client application that models may use for procedures."""

    id: snowflakes.Snowflake = attrs.field(hash=True, repr=True)
    """The ID of this entity."""

    icon_hash: str | None = attrs.field(eq=False, hash=False, repr=False)
    """The hash for the guild icon, if there is one."""

    name: str = attrs.field(eq=False, hash=False, repr=True)
    """The name of the guild."""

    @typing_extensions.override
    def __str__(self) -> str:
        return self.name

    @property
    def shard_id(self) -> int | None:
        """Return the ID of the shard this guild is served by.

        This may return [`None`][] if the application does not have a gateway
        connection.
        """
        if not isinstance(self.app, traits.ShardAware):
            return None

        shard_count = self.app.shard_count
        assert isinstance(shard_count, int)
        return snowflakes.calculate_shard_id(shard_count, self.id)

    @property
    @deprecation.deprecated("Use 'make_icon_url' instead.")
    def icon_url(self) -> files.URL | None:
        """Icon URL for the guild, if set; otherwise [`None`][]."""
        deprecation.warn_deprecated("icon_url", removal_version="2.5.0", additional_info="Use 'make_icon_url' instead.")
        return self.make_icon_url()

    def make_icon_url(
        self,
        *,
        file_format: undefined.UndefinedOr[
            typing.Literal["PNG", "JPEG", "JPG", "WEBP", "AWEBP", "GIF"]
        ] = undefined.UNDEFINED,
        size: int = 4096,
        lossless: bool = True,
        ext: str | None | undefined.UndefinedType = undefined.UNDEFINED,
    ) -> files.URL | None:
        """Generate the guild's icon URL, if set.

        If no icon is set, this returns [`None`][].

        Parameters
        ----------
        file_format
            The format to use for this URL.

            Supports `PNG`, `JPEG`, `JPG`, `WEBP`, `AWEBP` and `GIF`.

            If not specified, the format will be determined based on
            whether the icon is animated or not.
        size
            The size to set for the URL;
            Can be any power of two between `16` and `4096`.
        lossless
            Whether to return a lossless or compressed WEBP image;
            This is ignored if `file_format` is not `WEBP`.
        ext
            The extension to use for this URL.
            Supports `png`, `jpeg`, `jpg`, `webp`, and `gif` (when animated).

            !!! deprecated 2.4.0
                This has been replaced with the `file_format` argument.

        Returns
        -------
        typing.Optional[hikari.files.URL]
            The URL to the resource, or [`None`][] if no icon is set.

        Raises
        ------
        TypeError
            If an invalid format is passed for `file_format`;
            If an animated format is requested for a static icon.
        ValueError
            If `size` is specified but is not a power of two or not between 16 and 4096.
        """
        if self.icon_hash is None:
            return None

        if ext:
            deprecation.warn_deprecated(
                "ext", removal_version="2.5.0", additional_info="Use 'file_format' argument instead."
            )
            file_format = ext.upper()  # type: ignore[assignment]

        if not file_format:
            file_format = "GIF" if self.icon_hash.startswith("a_") else "PNG"

        return routes.CDN_GUILD_ICON.compile_to_file(
            urls.CDN_URL, guild_id=self.id, hash=self.icon_hash, size=size, file_format=file_format, lossless=lossless
        )

    async def ban(
        self,
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        *,
        delete_message_seconds: undefined.UndefinedOr[time.Intervalish] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        """Ban the given user from this guild.

        Parameters
        ----------
        user
            The user to ban from the guild.
        delete_message_seconds
            If provided, the number of seconds to delete messages for.
            This can be represented as either an int/float between 0 and 604800 (7 days), or
            a [`datetime.timedelta`][] object.
        reason
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.BAN_MEMBERS`][] permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild or user are not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        await self.app.rest.ban_user(self.id, user, delete_message_seconds=delete_message_seconds, reason=reason)

    async def unban(
        self,
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        *,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        """Unban the given user from this guild.

        Parameters
        ----------
        user
            The user to unban from the guild.
        reason
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.BAN_MEMBERS`][] permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild or user are not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        await self.app.rest.unban_user(self.id, user, reason=reason)

    async def kick(
        self,
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        *,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        """Kick the given user from this guild.

        Parameters
        ----------
        user
            The user to kick from the guild.
        reason
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.KICK_MEMBERS`][] permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild or user are not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        await self.app.rest.kick_user(self.id, user, reason=reason)

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
        afk_timeout: undefined.UndefinedOr[time.Intervalish] = undefined.UNDEFINED,
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
        preferred_locale: undefined.UndefinedOr[str | locales.Locale] = undefined.UNDEFINED,
        features: undefined.UndefinedOr[typing.Sequence[GuildFeature]] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> RESTGuild:
        """Edit the guild.

        Parameters
        ----------
        name
            If provided, the new name for the guild.
        verification_level
            If provided, the new verification level.
        default_message_notifications
            If provided, the new default message notifications level.
        explicit_content_filter_level
            If provided, the new explicit content filter level.
        afk_channel
            If provided, the new afk channel. Requires `afk_timeout` to
            be set to work.
        afk_timeout
            If provided, the new afk timeout.
        icon
            If provided, the new guild icon. Must be a 1024x1024 image or can be
            an animated gif when the guild has the [`hikari.guilds.GuildFeature.ANIMATED_ICON`][] feature.
        owner
            If provided, the new guild owner.

            !!! warning
                You need to be the owner of the server to use this.
        splash
            If provided, the new guild splash. Must be a 16:9 image and the
            guild must have the [`hikari.guilds.GuildFeature.INVITE_SPLASH`][] feature.
        banner
            If provided, the new guild banner. Must be a 16:9 image and the
            guild must have the [`hikari.guilds.GuildFeature.BANNER`][] feature.
        system_channel
            If provided, the new system channel.
        rules_channel
            If provided, the new rules channel.
        public_updates_channel
            If provided, the new public updates channel.
        preferred_locale
            If provided, the new preferred locale.
        features
            If provided, the guild features to be enabled. Features not provided will be disabled.
        reason
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
            If you are missing the [`hikari.permissions.Permissions.MANAGE_GUILD`][] permission
            or if you tried to pass ownership without being the server owner.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
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
            features=features,
            reason=reason,
        )

    async def set_incident_actions(
        self,
        *,
        invites_disabled_until: datetime.datetime | None = None,
        dms_disabled_until: datetime.datetime | None = None,
    ) -> GuildIncidents:
        """Set the incident actions for the guild.

        !!! warning
            This endpoint will reset any previous security measures if not specified.
            This is a Discord limitation.

        Parameters
        ----------
        invites_disabled_until
            The datetime when invites will be enabled again.

            If [`None`][], invites will be enabled again immediately.

            !!! note
                If [`hikari.guilds.GuildFeature.INVITES_DISABLED`][] is active, this value will be ignored.
        dms_disabled_until
            The datetime when direct messages between non-friend guild
            members will be enabled again.

            If [`None`][], direct messages will be enabled again immediately.

        Returns
        -------
        hikari.guilds.GuildIncidents
            A guild incidents object with the updated incident actions.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.ForbiddenError
            If you do not have at least one of the following permissions:
            - [`hikari.permissions.Permissions.ADMINISTRATOR`][]
            - [`hikari.permissions.Permissions.KICK_MEMBERS`][]
            - [`hikari.permissions.Permissions.MODERATE_MEMBERS`][]
            - [`hikari.permissions.Permissions.BAN_MEMBERS`][]
            - [`hikari.permissions.Permissions.MANAGE_GUILD`][]
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        return await self.app.rest.set_guild_incident_actions(
            self.id, invites_disabled_until=invites_disabled_until, dms_disabled_until=dms_disabled_until
        )

    async def fetch_emojis(self) -> typing.Sequence[emojis_.KnownCustomEmoji]:
        """Fetch the emojis of the guild.

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
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        return await self.app.rest.fetch_guild_emojis(self.id)

    async def fetch_emoji(self, emoji: snowflakes.SnowflakeishOr[emojis_.CustomEmoji]) -> emojis_.KnownCustomEmoji:
        """Fetch an emoji from the guild.

        Parameters
        ----------
        emoji
            The emoji to fetch. This can be a [`hikari.emojis.CustomEmoji`][]
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
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        return await self.app.rest.fetch_emoji(self.id, emoji)

    async def fetch_stickers(self) -> typing.Sequence[stickers.GuildSticker]:
        """Fetch the stickers of the guild.

        Returns
        -------
        typing.Sequence[hikari.stickers.GuildSticker]
            The requested stickers.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are not part of the server.
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        return await self.app.rest.fetch_guild_stickers(self.id)

    async def fetch_sticker(self, sticker: snowflakes.SnowflakeishOr[stickers.PartialSticker]) -> stickers.GuildSticker:
        """Fetch a sticker from the guild.

        Parameters
        ----------
        sticker
            The sticker to fetch. This can be a sticker object or the
            ID of an existing sticker.

        Returns
        -------
        hikari.stickers.GuildSticker
            The requested sticker.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are not part of the server.
        hikari.errors.NotFoundError
            If the guild or the sticker are not found.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        return await self.app.rest.fetch_guild_sticker(self.id, sticker)

    async def create_sticker(
        self,
        name: str,
        tag: str,
        image: files.Resourceish,
        *,
        description: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> stickers.GuildSticker:
        """Create a sticker in a guild.

        !!! note
            Lottie support is only available for verified and partnered
            servers.

        Parameters
        ----------
        name
            The name for the sticker.
        tag
            The tag for the sticker.
        image
            The 320x320 image for the sticker. Maximum upload size is 500kb.
            This can be a still PNG, an animated PNG, a Lottie, or a GIF.
        description
            If provided, the description of the sticker.
        reason
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Returns
        -------
        hikari.stickers.GuildSticker
            The created sticker.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value or
            if there are no more spaces for the sticker in the guild.
        hikari.errors.ForbiddenError
            If you are missing [`hikari.permissions.Permissions.MANAGE_GUILD_EXPRESSIONS`][]
            in the server.
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        return await self.app.rest.create_sticker(self.id, name, tag, image, description=description, reason=reason)

    async def edit_sticker(
        self,
        sticker: snowflakes.SnowflakeishOr[stickers.PartialSticker],
        *,
        name: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        description: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        tag: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> stickers.GuildSticker:
        """Edit a sticker in a guild.

        Parameters
        ----------
        sticker
            The sticker to edit. This can be a sticker object or the ID of an
            existing sticker.
        name
            If provided, the new name for the sticker.
        description
            If provided, the new description for the sticker.
        tag
            If provided, the new sticker tag.
        reason
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Returns
        -------
        hikari.stickers.GuildSticker
            The edited sticker.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.ForbiddenError
            If you are missing [`hikari.permissions.Permissions.MANAGE_GUILD_EXPRESSIONS`][]
            in the server.
        hikari.errors.NotFoundError
            If the guild or the sticker are not found.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        return await self.app.rest.edit_sticker(
            self.id, sticker, name=name, description=description, tag=tag, reason=reason
        )

    async def delete_sticker(
        self,
        sticker: snowflakes.SnowflakeishOr[stickers.PartialSticker],
        *,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        """Delete a sticker in a guild.

        Parameters
        ----------
        sticker
            The sticker to delete. This can be a sticker object or the ID
            of an existing sticker.
        reason
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are missing [`hikari.permissions.Permissions.MANAGE_GUILD_EXPRESSIONS`][]
            in the server.
        hikari.errors.NotFoundError
            If the guild or the sticker are not found.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        return await self.app.rest.delete_sticker(self.id, sticker, reason=reason)

    async def create_category(
        self,
        name: str,
        *,
        position: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        permission_overwrites: undefined.UndefinedOr[
            typing.Sequence[channels_.PermissionOverwrite]
        ] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> channels_.GuildCategory:
        """Create a category in the guild.

        Parameters
        ----------
        name
            The channels name. Must be between 2 and 1000 characters.
        position
            If provided, the position of the category.
        permission_overwrites
            If provided, the permission overwrites for the category.
        reason
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Returns
        -------
        hikari.channels.GuildCategory
            The created category.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.MANAGE_CHANNELS`][] permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        return await self.app.rest.create_guild_category(
            self.id, name, position=position, permission_overwrites=permission_overwrites, reason=reason
        )

    async def create_text_channel(
        self,
        name: str,
        *,
        position: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        topic: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        nsfw: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        rate_limit_per_user: undefined.UndefinedOr[time.Intervalish] = undefined.UNDEFINED,
        permission_overwrites: undefined.UndefinedOr[
            typing.Sequence[channels_.PermissionOverwrite]
        ] = undefined.UNDEFINED,
        category: undefined.UndefinedOr[snowflakes.SnowflakeishOr[channels_.GuildCategory]] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> channels_.GuildTextChannel:
        """Create a text channel in the guild.

        Parameters
        ----------
        name
            The channels name. Must be between 2 and 1000 characters.
        position
            If provided, the position of the channel (relative to the
            category, if any).
        topic
            If provided, the channels topic. Maximum 1024 characters.
        nsfw
            If provided, whether to mark the channel as NSFW.
        rate_limit_per_user
            If provided, the amount of seconds a user has to wait
            before being able to send another message in the channel.
            Maximum 21600 seconds.
        permission_overwrites
            If provided, the permission overwrites for the channel.
        category
            The category to create the channel under. This may be the
            object or the ID of an existing category.
        reason
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Returns
        -------
        hikari.channels.GuildTextChannel
            The created channel.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.MANAGE_CHANNELS`][] permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        return await self.app.rest.create_guild_text_channel(
            self.id,
            name,
            position=position,
            topic=topic,
            nsfw=nsfw,
            rate_limit_per_user=rate_limit_per_user,
            permission_overwrites=permission_overwrites,
            category=category,
            reason=reason,
        )

    async def create_news_channel(
        self,
        name: str,
        *,
        position: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        topic: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        nsfw: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        rate_limit_per_user: undefined.UndefinedOr[time.Intervalish] = undefined.UNDEFINED,
        permission_overwrites: undefined.UndefinedOr[
            typing.Sequence[channels_.PermissionOverwrite]
        ] = undefined.UNDEFINED,
        category: undefined.UndefinedOr[snowflakes.SnowflakeishOr[channels_.GuildCategory]] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> channels_.GuildNewsChannel:
        """Create a news channel in the guild.

        Parameters
        ----------
        name
            The channels name. Must be between 2 and 1000 characters.
        position
            If provided, the position of the channel (relative to the
            category, if any).
        topic
            If provided, the channels topic. Maximum 1024 characters.
        nsfw
            If provided, whether to mark the channel as NSFW.
        rate_limit_per_user
            If provided, the amount of seconds a user has to wait
            before being able to send another message in the channel.
            Maximum 21600 seconds.
        permission_overwrites
            If provided, the permission overwrites for the channel.
        category
            The category to create the channel under. This may be the
            object or the ID of an existing category.
        reason
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Returns
        -------
        hikari.channels.GuildNewsChannel
            The created channel.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.MANAGE_CHANNELS`][] permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        return await self.app.rest.create_guild_news_channel(
            self.id,
            name,
            position=position,
            topic=topic,
            nsfw=nsfw,
            rate_limit_per_user=rate_limit_per_user,
            permission_overwrites=permission_overwrites,
            category=category,
            reason=reason,
        )

    async def create_forum_channel(
        self,
        name: str,
        *,
        position: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        category: undefined.UndefinedOr[snowflakes.SnowflakeishOr[channels_.GuildCategory]] = undefined.UNDEFINED,
        permission_overwrites: undefined.UndefinedOr[
            typing.Sequence[channels_.PermissionOverwrite]
        ] = undefined.UNDEFINED,
        topic: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        nsfw: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        rate_limit_per_user: undefined.UndefinedOr[time.Intervalish] = undefined.UNDEFINED,
        default_auto_archive_duration: undefined.UndefinedOr[time.Intervalish] = undefined.UNDEFINED,
        default_thread_rate_limit_per_user: undefined.UndefinedOr[time.Intervalish] = undefined.UNDEFINED,
        default_forum_layout: undefined.UndefinedOr[channels_.ForumLayoutType | int] = undefined.UNDEFINED,
        default_sort_order: undefined.UndefinedOr[channels_.ForumSortOrderType | int] = undefined.UNDEFINED,
        available_tags: undefined.UndefinedOr[typing.Sequence[channels_.ForumTag]] = undefined.UNDEFINED,
        default_reaction_emoji: str
        | emojis_.Emoji
        | undefined.UndefinedType
        | snowflakes.Snowflake = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> channels_.GuildForumChannel:
        """Create a forum channel in the guild.

        Parameters
        ----------
        name
            The channels name. Must be between 2 and 1000 characters.
        position
            If provided, the position of the category.
        category
            The category to create the channel under. This may be the
            object or the ID of an existing category.
        permission_overwrites
            If provided, the permission overwrites for the category.
        topic
            If provided, the channels topic. Maximum 1024 characters.
        nsfw
            If provided, whether to mark the channel as NSFW.
        rate_limit_per_user
            If provided, the amount of seconds a user has to wait
            before being able to send another message in the channel.
            Maximum 21600 seconds.
        default_auto_archive_duration
            If provided, the auto archive duration Discord's end user client
            should default to when creating threads in this channel.

            This should be either 60, 1440, 4320 or 10080 minutes and, as of
            writing, ignores the parent channel's set default_auto_archive_duration
            when passed as [`hikari.undefined.UNDEFINED`][].
        default_thread_rate_limit_per_user
            If provided, the ratelimit that should be set in threads created
            from the forum.
        default_forum_layout
            If provided, the default forum layout to show in the client.
        default_sort_order
            If provided, the default sort order to show in the client.
        available_tags
            If provided, the available tags to select from when creating a thread.
        default_reaction_emoji
            If provided, the new default reaction emoji for threads created in a forum channel.
        reason
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Returns
        -------
        hikari.channels.GuildForumChannel
            The created forum channel.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.MANAGE_CHANNELS`][] permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        return await self.app.rest.create_guild_forum_channel(
            self.id,
            name,
            position=position,
            topic=topic,
            nsfw=nsfw,
            rate_limit_per_user=rate_limit_per_user,
            permission_overwrites=permission_overwrites,
            category=category,
            reason=reason,
            default_auto_archive_duration=default_auto_archive_duration,
            default_thread_rate_limit_per_user=default_thread_rate_limit_per_user,
            default_forum_layout=default_forum_layout,
            default_sort_order=default_sort_order,
            available_tags=available_tags,
            default_reaction_emoji=default_reaction_emoji,
        )

    async def create_voice_channel(
        self,
        name: str,
        *,
        position: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        user_limit: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        bitrate: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        video_quality_mode: undefined.UndefinedOr[channels_.VideoQualityMode | int] = undefined.UNDEFINED,
        permission_overwrites: undefined.UndefinedOr[
            typing.Sequence[channels_.PermissionOverwrite]
        ] = undefined.UNDEFINED,
        region: undefined.UndefinedOr[voices_.VoiceRegion | str] = undefined.UNDEFINED,
        category: undefined.UndefinedOr[snowflakes.SnowflakeishOr[channels_.GuildCategory]] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> channels_.GuildVoiceChannel:
        """Create a voice channel in a guild.

        Parameters
        ----------
        name
            The channels name. Must be between 2 and 1000 characters.
        position
            If provided, the position of the channel (relative to the
            category, if any).
        user_limit
            If provided, the maximum users in the channel at once.
            Must be between 0 and 99 with 0 meaning no limit.
        bitrate
            If provided, the bitrate for the channel. Must be
            between 8000 and 96000 or 8000 and 128000 for VIP
            servers.
        video_quality_mode
            If provided, the new video quality mode for the channel.
        permission_overwrites
            If provided, the permission overwrites for the channel.
        region
            If provided, the voice region to for this channel. Passing
            [`None`][] here will set it to "auto" mode where the used
            region will be decided based on the first person who connects to it
            when it's empty.
        category
            The category to create the channel under. This may be the
            object or the ID of an existing category.
        reason
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Returns
        -------
        hikari.channels.GuildVoiceChannel
            The created channel.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.MANAGE_CHANNELS`][] permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the gui  ld is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        return await self.app.rest.create_guild_voice_channel(
            self.id,
            name,
            position=position,
            user_limit=user_limit,
            bitrate=bitrate,
            video_quality_mode=video_quality_mode,
            permission_overwrites=permission_overwrites,
            region=region,
            category=category,
            reason=reason,
        )

    async def create_stage_channel(
        self,
        name: str,
        *,
        position: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        user_limit: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        bitrate: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        permission_overwrites: undefined.UndefinedOr[
            typing.Sequence[channels_.PermissionOverwrite]
        ] = undefined.UNDEFINED,
        region: undefined.UndefinedOr[voices_.VoiceRegion | str] = undefined.UNDEFINED,
        category: undefined.UndefinedOr[snowflakes.SnowflakeishOr[channels_.GuildCategory]] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> channels_.GuildStageChannel:
        """Create a stage channel in the guild.

        Parameters
        ----------
        name
            The channel's name. Must be between 2 and 1000 characters.
        position
            If provided, the position of the channel (relative to the
            category, if any).
        user_limit
            If provided, the maximum users in the channel at once.
            Must be between 0 and 99 with 0 meaning no limit.
        bitrate
            If provided, the bitrate for the channel. Must be
            between 8000 and 96000 or 8000 and 128000 for VIP
            servers.
        permission_overwrites
            If provided, the permission overwrites for the channel.
        region
            If provided, the voice region to for this channel. Passing
            [`None`][] here will set it to "auto" mode where the used
            region will be decided based on the first person who connects to it
            when it's empty.
        category
            The category to create the channel under. This may be the
            object or the ID of an existing category.
        reason
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Returns
        -------
        hikari.channels.GuildStageChannel
            The created channel.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.MANAGE_CHANNELS`][] permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        return await self.app.rest.create_guild_stage_channel(
            self.id,
            name,
            position=position,
            user_limit=user_limit,
            bitrate=bitrate,
            permission_overwrites=permission_overwrites,
            region=region,
            category=category,
            reason=reason,
        )

    async def delete_channel(
        self, channel: snowflakes.SnowflakeishOr[channels_.GuildChannel]
    ) -> channels_.GuildChannel:
        """Delete a channel in the guild.

        !!! note
            This method can also be used for deleting guild categories as well.

        !!! note
            For Public servers, the set 'Rules' or 'Guidelines' channels and the
            'Public Server Updates' channel cannot be deleted.

        Parameters
        ----------
        channel
            The channel or category to delete. This may be the object or the ID of an
            existing channel.

        Returns
        -------
        hikari.channels.GuildChannel
            Object of the channel or category that was deleted.

        Raises
        ------
        hikari.errors.UnauthorizedError, or close a DM.
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.MANAGE_CHANNELS`][] permission in the channel.
        hikari.errors.NotFoundError
            If the channel is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        deleted_channel = await self.app.rest.delete_channel(channel)
        assert isinstance(deleted_channel, channels_.GuildChannel)

        return deleted_channel

    async def fetch_self(self) -> RESTGuild:
        """Fetch the guild.

        Returns
        -------
        hikari.guilds.RESTGuild
            The requested guild.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are not part of the guild.
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        return await self.app.rest.fetch_guild(self.id)

    async def fetch_roles(self) -> typing.Sequence[Role]:
        """Fetch the roles of the guild.

        Returns
        -------
        typing.Sequence[hikari.guilds.Role]
            The requested roles.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        return await self.app.rest.fetch_roles(self.id)


@attrs.define(unsafe_hash=True, kw_only=True, weakref_slot=False)
class GuildPreview(PartialGuild):
    """A preview of a guild with the [`hikari.guilds.GuildFeature.DISCOVERABLE`][] feature."""

    features: typing.Sequence[str | GuildFeature] = attrs.field(eq=False, hash=False, repr=False)
    """A list of the features in this guild."""

    splash_hash: str | None = attrs.field(eq=False, hash=False, repr=False)
    """The hash of the splash for the guild, if there is one."""

    discovery_splash_hash: str | None = attrs.field(eq=False, hash=False, repr=False)
    """The hash of the discovery splash for the guild, if there is one."""

    emojis: typing.Mapping[snowflakes.Snowflake, emojis_.KnownCustomEmoji] = attrs.field(
        eq=False, hash=False, repr=False
    )
    """The mapping of IDs to the emojis this guild provides."""

    approximate_active_member_count: int = attrs.field(eq=False, hash=False, repr=True)
    """The approximate amount of presences in this guild."""

    approximate_member_count: int = attrs.field(eq=False, hash=False, repr=True)
    """The approximate amount of members in this guild."""

    description: str | None = attrs.field(eq=False, hash=False, repr=False)
    """The guild's description, if set."""

    @property
    @deprecation.deprecated("Use 'make_discovery_splash_url' instead")
    def discovery_splash_url(self) -> files.URL | None:
        """Discovery URL splash for the guild, if set."""
        deprecation.warn_deprecated(
            "discovery_splash_url", removal_version="2.5.0", additional_info="Use 'make_discovery_splash_url' instead"
        )
        return self.make_discovery_splash_url()

    @property
    @deprecation.deprecated("Use 'make_splash_url' instead")
    def splash_url(self) -> files.URL | None:
        """Splash URL for the guild, if set."""
        deprecation.warn_deprecated(
            "splash_url", removal_version="2.5.0", additional_info="Use 'make_splash_url' instead"
        )
        return self.make_splash_url()

    def make_discovery_splash_url(
        self,
        *,
        file_format: typing.Literal["PNG", "JPEG", "JPG", "WEBP"] = "PNG",
        size: int = 4096,
        lossless: bool = True,
        ext: str | None | undefined.UndefinedType = undefined.UNDEFINED,
    ) -> files.URL | None:
        """Generate the discovery splash URL for this guild, if set.

        If no discovery splash is set, this returns [`None`][].

        Parameters
        ----------
        file_format
            The format to use for this URL.

            Supports `PNG`, `JPEG`, `JPG`, and `WEBP`.

            If not specified, the format will be `PNG`.
        size
            The size to set for the URL;
            Can be any power of two between `16` and `4096`;
        lossless
            Whether to return a lossless or compressed WEBP image;
            This is ignored if `file_format` is not `WEBP`.
        ext
            The extension to use for this URL.
            Supports `png`, `jpeg`, `jpg` and `webp`.

            !!! deprecated 2.4.0
                This has been replaced with the `file_format` argument.

        Returns
        -------
        typing.Optional[hikari.files.URL]
            The URL, or [`None`][] if no discovery splash is set.

        Raises
        ------
        TypeError
            If an invalid format is passed for `file_format`.
        ValueError
            If `size` is specified but is not a power of two or not between 16 and 4096.
        """
        if self.discovery_splash_hash is None:
            return None

        if ext:
            deprecation.warn_deprecated(
                "ext", removal_version="2.5.0", additional_info="Use 'file_format' argument instead."
            )
            file_format = ext.upper()  # type: ignore[assignment]

        return routes.CDN_GUILD_DISCOVERY_SPLASH.compile_to_file(
            urls.CDN_URL,
            guild_id=self.id,
            hash=self.discovery_splash_hash,
            size=size,
            file_format=file_format,
            lossless=lossless,
        )

    def make_splash_url(
        self,
        *,
        file_format: typing.Literal["PNG", "JPEG", "JPG", "WEBP"] = "PNG",
        size: int = 4096,
        lossless: bool = True,
        ext: str | None | undefined.UndefinedType = undefined.UNDEFINED,
    ) -> files.URL | None:
        """Generate the splash URL for this guild, if set.

        If no splash is set, this returns [`None`][].

        Parameters
        ----------
        file_format
            The format to use for this URL.

            Supports `PNG`, `JPEG`, `JPG`, and `WEBP`.

            If not specified, the format will be `PNG`.
        size
            The size to set for the URL;
            Can be any power of two between `16` and `4096`;
        lossless
            Whether to return a lossless or compressed WEBP image;
            This is ignored if `file_format` is not `WEBP`.
        ext
            The extension to use for this URL.
            Supports `png`, `jpeg`, `jpg` and `webp`.

            !!! deprecated 2.4.0
                This has been replaced with the `file_format` argument.

        Returns
        -------
        typing.Optional[hikari.files.URL]
            The URL, or [`None`][] if no splash is set.

        Raises
        ------
        TypeError
            If an invalid format is passed for `file_format`.
        ValueError
            If `size` is specified but is not a power of two or not between 16 and 4096.
        """
        if self.splash_hash is None:
            return None

        if ext:
            deprecation.warn_deprecated(
                "ext", removal_version="2.5.0", additional_info="Use 'file_format' argument instead."
            )
            file_format = ext.upper()  # type: ignore[assignment]

        return routes.CDN_GUILD_SPLASH.compile_to_file(
            urls.CDN_URL, guild_id=self.id, hash=self.splash_hash, size=size, file_format=file_format, lossless=lossless
        )


@attrs.define(unsafe_hash=True, kw_only=True, weakref_slot=False)
class Guild(PartialGuild):
    """A representation of a guild on Discord."""

    features: typing.Sequence[str | GuildFeature] = attrs.field(eq=False, hash=False, repr=False)
    """A list of the features in this guild."""

    incidents: GuildIncidents = attrs.field(eq=False, hash=False, repr=False)
    """The state of the active incidents in this guild."""

    application_id: snowflakes.Snowflake | None = attrs.field(eq=False, hash=False, repr=False)
    """The ID of the application that created this guild.

    This will always be [`None`][] for guilds that weren't created by a bot.
    """

    afk_channel_id: snowflakes.Snowflake | None = attrs.field(eq=False, hash=False, repr=False)
    """The ID for the channel that AFK voice users get sent to.

    If [`None`][], then no AFK channel is set up for this guild.
    """

    afk_timeout: datetime.timedelta = attrs.field(eq=False, hash=False, repr=False)
    """Timeout for activity before a member is classed as AFK.

    How long a voice user has to be AFK for before they are classed as being
    AFK and are moved to the AFK channel ([`hikari.guilds.Guild.afk_channel_id`][]).
    """

    banner_hash: str | None = attrs.field(eq=False, hash=False, repr=False)
    """The hash for the guild's banner.

    This is only present if the guild has [`hikari.guilds.GuildFeature.BANNER`][] in
    [`hikari.guilds.Guild.features`][] for this guild. For all other purposes, it is [`None`][].
    """

    default_message_notifications: GuildMessageNotificationsLevel | int = attrs.field(eq=False, hash=False, repr=False)
    """The default setting for message notifications in this guild."""

    description: str | None = attrs.field(eq=False, hash=False, repr=False)
    """The guild's description.

    This is only present if certain [`hikari.guilds.GuildFeature`][]'s are set in
    [`hikari.guilds.Guild.features`][] for this guild. Otherwise, this will always be [`None`][].
    """

    discovery_splash_hash: str | None = attrs.field(eq=False, hash=False, repr=False)
    """The hash of the discovery splash for the guild, if there is one."""

    explicit_content_filter: GuildExplicitContentFilterLevel | int = attrs.field(eq=False, hash=False, repr=False)
    """The setting for the explicit content filter in this guild."""

    is_widget_enabled: bool | None = attrs.field(eq=False, hash=False, repr=False)
    """Describes whether the guild widget is enabled or not.

    If this information is not present, this will be [`None`][].
    """

    max_video_channel_users: int | None = attrs.field(eq=False, hash=False, repr=False)
    """The maximum number of users allowed in a video channel together.

    This information may not be present, in which case, it will be [`None`][].
    """

    mfa_level: GuildMFALevel | int = attrs.field(eq=False, hash=False, repr=False)
    """The required MFA level for users wishing to participate in this guild."""

    owner_id: snowflakes.Snowflake = attrs.field(eq=False, hash=False, repr=True)
    """The ID of the owner of this guild."""

    preferred_locale: str | locales.Locale = attrs.field(eq=False, hash=False, repr=False)
    """The preferred locale to use for this guild.

    This can only be change if [`hikari.guilds.GuildFeature.COMMUNITY`][] is in [`hikari.guilds.Guild.features`][]
    for this guild and will otherwise default to `en-US`.
    """

    premium_subscription_count: int | None = attrs.field(eq=False, hash=False, repr=False)
    """The number of nitro boosts that the server currently has.

    This information may not be present, in which case, it will be [`None`][].
    """

    premium_tier: GuildPremiumTier | int = attrs.field(eq=False, hash=False, repr=False)
    """The premium tier for this guild."""

    public_updates_channel_id: snowflakes.Snowflake | None = attrs.field(eq=False, hash=False, repr=False)
    """The channel ID of the channel where admins and moderators receive notices from Discord.

    This is only present if [`hikari.guilds.GuildFeature.COMMUNITY`][] is in [`hikari.guilds.Guild.features`][] for
    this guild. For all other purposes, it should be considered to be [`None`][].
    """

    rules_channel_id: snowflakes.Snowflake | None = attrs.field(eq=False, hash=False, repr=False)
    """The ID of the channel where rules and guidelines will be displayed.

    If the [`hikari.guilds.GuildFeature.COMMUNITY`][] feature is not defined, then this is [`None`][].
    """

    splash_hash: str | None = attrs.field(eq=False, hash=False, repr=False)
    """The hash of the splash for the guild, if there is one."""

    system_channel_flags: GuildSystemChannelFlag = attrs.field(eq=False, hash=False, repr=False)
    """Return flags for the guild system channel.

    These are used to describe which notifications are suppressed.
    """

    system_channel_id: snowflakes.Snowflake | None = attrs.field(eq=False, hash=False, repr=False)
    """The ID of the system channel or [`None`][] if it is not enabled.

    Welcome messages and Nitro boost messages may be sent to this channel.
    """

    vanity_url_code: str | None = attrs.field(eq=False, hash=False, repr=False)
    """The vanity URL code for the guild's vanity URL.

    This is only present if [`hikari.guilds.GuildFeature.VANITY_URL`][] is in [`hikari.guilds.Guild.features`][] for
    this guild. If not, this will always be [`None`][].
    """

    verification_level: GuildVerificationLevel | int = attrs.field(eq=False, hash=False, repr=False)
    """The verification level needed for a user to participate in this guild."""

    widget_channel_id: snowflakes.Snowflake | None = attrs.field(eq=False, hash=False, repr=False)
    """The channel ID that the widget's generated invite will send the user to.

    If this information is unavailable or this is not enabled for the guild then
    this will be [`None`][].
    """

    nsfw_level: GuildNSFWLevel = attrs.field(eq=False, hash=False, repr=False)
    """The NSFW level of the guild."""

    @property
    @deprecation.deprecated("Use 'make_banner_url' instead")
    def banner_url(self) -> files.URL | None:
        """Banner URL for the guild, if set."""
        deprecation.warn_deprecated(
            "banner_url", removal_version="2.5.0", additional_info="Use 'make_banner_url' instead"
        )
        return self.make_banner_url()

    @property
    @deprecation.deprecated("Use 'make_discovery_splash_url' instead")
    def discovery_splash_url(self) -> files.URL | None:
        """Discovery splash URL for the guild, if set."""
        deprecation.warn_deprecated(
            "discovery_splash_url", removal_version="2.5.0", additional_info="Use 'make_discovery_splash_url' instead"
        )
        return self.make_discovery_splash_url()

    @property
    @deprecation.deprecated("Use 'make_splash_url' instead")
    def splash_url(self) -> files.URL | None:
        """Splash URL for the guild, if set."""
        deprecation.warn_deprecated(
            "splash_url", removal_version="2.5.0", additional_info="Use 'make_splash_url' instead"
        )
        return self.make_splash_url()

    @property
    def invites_disabled(self) -> bool:
        """Return whether the guild has invites disabled.

        Returns
        -------
        bool
            [`True`][] if `self.incidents.invites_disabled_until` is set, or if
            [`hikari.guilds.GuildFeature.INVITES_DISABLED`][] is in `self.features`.
            [`False`][] otherwise.
        """
        return self.incidents.invites_disabled_until is not None or GuildFeature.INVITES_DISABLED in self.features

    def get_members(self) -> typing.Mapping[snowflakes.Snowflake, Member]:
        """Get the members cached for the guild.

        Returns
        -------
        typing.Mapping[hikari.snowflakes.Snowflake, Member]
            A mapping of user IDs to objects of the members cached for the guild.
        """
        if not isinstance(self.app, traits.CacheAware):
            return {}

        return self.app.cache.get_members_view_for_guild(self.id)

    def get_presences(self) -> typing.Mapping[snowflakes.Snowflake, presences_.MemberPresence]:
        """Get the presences cached for the guild.

        Returns
        -------
        typing.Mapping[hikari.snowflakes.Snowflake, hikari.presences.MemberPresence]
            A mapping of user IDs to objects of the presences cached for the
            guild.
        """
        if not isinstance(self.app, traits.CacheAware):
            return {}

        return self.app.cache.get_presences_view_for_guild(self.id)

    def get_channels(self) -> typing.Mapping[snowflakes.Snowflake, channels_.PermissibleGuildChannel]:
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

    def get_voice_states(self) -> typing.Mapping[snowflakes.Snowflake, voices_.VoiceState]:
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

    def get_emojis(self) -> typing.Mapping[snowflakes.Snowflake, emojis_.KnownCustomEmoji]:
        """Return the emojis in this guild.

        Returns
        -------
        typing.Mapping[hikari.snowflakes.Snowflake, hikari.emojis.KnownCustomEmoji]
            A mapping of emoji IDs to the objects of emojis in this guild.
        """
        if not isinstance(self.app, traits.CacheAware):
            return {}

        return self.app.cache.get_emojis_view_for_guild(self.id)

    def get_stickers(self) -> typing.Mapping[snowflakes.Snowflake, stickers.GuildSticker]:
        """Return the stickers in this guild.

        Returns
        -------
        typing.Mapping[hikari.snowflakes.Snowflake, hikari.stickers.GuildSticker]
            A mapping of sticker IDs to the objects of sticker in this guild.
        """
        if not isinstance(self.app, traits.CacheAware):
            return {}

        return self.app.cache.get_stickers_view_for_guild(self.id)

    def get_roles(self) -> typing.Mapping[snowflakes.Snowflake, Role]:
        """Return the roles in this guild.

        Returns
        -------
        typing.Mapping[hikari.snowflakes.Snowflake, Role]
            A mapping of role IDs to the objects of roles in this guild.
        """
        if not isinstance(self.app, traits.CacheAware):
            return {}

        return self.app.cache.get_roles_view_for_guild(self.id)

    def make_banner_url(
        self,
        *,
        file_format: undefined.UndefinedOr[
            typing.Literal["PNG", "JPEG", "JPG", "WEBP", "AWEBP", "GIF"]
        ] = undefined.UNDEFINED,
        size: int = 4096,
        lossless: bool = True,
        ext: str | None | undefined.UndefinedType = undefined.UNDEFINED,
    ) -> files.URL | None:
        """Generate the banner URL for this guild, if set.

        If no banner is set, this returns [`None`][].

        Parameters
        ----------
        file_format
            The format to use for this URL.

            Supports `PNG`, `JPEG`, `JPG`, `WEBP`, `AWEBP` and `GIF`.

            If not specified, the format will be determined based on
            whether the banner is animated or not.
        size
            The size to set for the URL;
            Can be any power of two between `16` and `4096`;
        lossless
            Whether to return a lossless or compressed WEBP image;
            This is ignored if `file_format` is not `WEBP` or `AWEBP`.
        ext
            The ext to use for this URL.
            Supports `png`, `jpeg`, `jpg`, `webp` and `gif` (when
            animated).

            If [`None`][], then the correct default extension is
            determined based on whether the banner is animated or not.

            !!! deprecated 2.4.0
                This has been replaced with the `file_format` argument.

        Returns
        -------
        typing.Optional[hikari.files.URL]
            The URL, or [`None`][] if no banner is set.

        Raises
        ------
        TypeError
            If an invalid format is passed for `file_format`;
            If an animated format is requested for a static banner.
        ValueError
            If `size` is specified but is not a power of two or not between 16 and 4096.
        """
        if self.banner_hash is None:
            return None

        if ext:
            deprecation.warn_deprecated(
                "ext", removal_version="2.5.0", additional_info="Use 'file_format' argument instead."
            )
            file_format = ext.upper()  # type: ignore[assignment]

        if not file_format:
            file_format = "GIF" if self.banner_hash.startswith("a_") else "PNG"

        return routes.CDN_GUILD_BANNER.compile_to_file(
            urls.CDN_URL, guild_id=self.id, hash=self.banner_hash, size=size, file_format=file_format, lossless=lossless
        )

    def make_discovery_splash_url(
        self,
        *,
        file_format: typing.Literal["PNG", "JPEG", "JPG", "WEBP"] = "PNG",
        size: int = 4096,
        lossless: bool = True,
        ext: str | None | undefined.UndefinedType = undefined.UNDEFINED,
    ) -> files.URL | None:
        """Generate the discovery splash URL for this guild, if set.

        If no discovery splash is set, this returns [`None`][].

        Parameters
        ----------
        file_format
            The format to use for this URL.

            Supports `PNG`, `JPEG`, `JPG`, and `WEBP`.

            If not specified, the format will be `PNG`.
        size
            The size to set for the URL;
            Can be any power of two between `16` and `4096`;
        lossless
            Whether to return a lossless or compressed WEBP image;
            This is ignored if `file_format` is not `WEBP`.
        ext
            The extension to use for this URL.
            Supports `png`, `jpeg`, `jpg` and `webp`.

            !!! deprecated 2.4.0
                This has been replaced with the `file_format` argument.

        Returns
        -------
        typing.Optional[hikari.files.URL]
            The URL, or [`None`][] if no discovery splash is set.

        Raises
        ------
        TypeError
            If an invalid format is passed for `file_format`.
        ValueError
            If `size` is specified but is not a power of two or not between 16 and 4096.
        """
        if self.discovery_splash_hash is None:
            return None

        if ext:
            deprecation.warn_deprecated(
                "ext", removal_version="2.5.0", additional_info="Use 'file_format' argument instead."
            )
            file_format = ext.upper()  # type: ignore[assignment]

        return routes.CDN_GUILD_DISCOVERY_SPLASH.compile_to_file(
            urls.CDN_URL,
            guild_id=self.id,
            hash=self.discovery_splash_hash,
            size=size,
            file_format=file_format,
            lossless=lossless,
        )

    def make_splash_url(
        self,
        *,
        file_format: typing.Literal["PNG", "JPEG", "JPG", "WEBP"] = "PNG",
        size: int = 4096,
        lossless: bool = True,
        ext: str | None | undefined.UndefinedType = undefined.UNDEFINED,
    ) -> files.URL | None:
        """Generate the splash URL for this guild, if set.

        If no splash is set, this returns [`None`][].

        Parameters
        ----------
        file_format
            The format to use for this URL.

            Supports `PNG`, `JPEG`, `JPG`, and `WEBP`.

            If not specified, the format will be `PNG`.
        size
            The size to set for the URL;
            Can be any power of two between `16` and `4096`;
        lossless
            Whether to return a lossless or compressed WEBP image;
            This is ignored if `file_format` is not `WEBP`.
        ext
            The extension to use for this URL.
            Supports `png`, `jpeg`, `jpg` and `webp`.

            !!! deprecated 2.4.0
                This has been replaced with the `file_format` argument.

        Returns
        -------
        typing.Optional[hikari.files.URL]
            The URL, or [`None`][] if no splash is set.

        Raises
        ------
        TypeError
            If an invalid format is passed for `file_format`.
        ValueError
            If `size` is specified but is not a power of two or not between 16 and 4096.
        """
        if self.splash_hash is None:
            return None

        if ext:
            deprecation.warn_deprecated(
                "ext", removal_version="2.5.0", additional_info="Use 'file_format' argument instead."
            )
            file_format = ext.upper()  # type: ignore[assignment]

        return routes.CDN_GUILD_SPLASH.compile_to_file(
            urls.CDN_URL, guild_id=self.id, hash=self.splash_hash, size=size, file_format=file_format, lossless=lossless
        )

    def get_channel(
        self, channel: snowflakes.SnowflakeishOr[channels_.PartialChannel]
    ) -> channels_.PermissibleGuildChannel | None:
        """Get a cached channel that belongs to the guild by it's ID or object.

        Parameters
        ----------
        channel
            The object or ID of the guild channel to get from the cache.

        Returns
        -------
        typing.Optional[hikari.channels.GuildChannel]
            The object of the guild channel found in cache or [`None`][].
        """
        if not isinstance(self.app, traits.CacheAware):
            return None

        channel_ = self.app.cache.get_guild_channel(channel)
        if channel_ and channel_.guild_id == self.id:
            return channel_

        return None

    def get_member(self, user: snowflakes.SnowflakeishOr[users.PartialUser]) -> Member | None:
        """Get a cached member that belongs to the guild by it's user ID or object.

        Parameters
        ----------
        user
            The object or ID of the user to get the cached member for.

        Returns
        -------
        typing.Optional[Member]
            The cached member object if found, else [`None`][].
        """
        if not isinstance(self.app, traits.CacheAware):
            return None

        return self.app.cache.get_member(self.id, user)

    def get_my_member(self) -> Member | None:
        """Return the cached member for the bot user in this guild, if known.

        Returns
        -------
        typing.Optional[Member]
            The cached member for this guild, or [`None`][] if not known.
        """
        if not isinstance(self.app, traits.ShardAware):
            return None

        me = self.app.get_me()
        if me is None:
            return None

        return self.get_member(me.id)

    def get_presence(self, user: snowflakes.SnowflakeishOr[users.PartialUser]) -> presences_.MemberPresence | None:
        """Get a cached presence that belongs to the guild by it's user ID or object.

        Parameters
        ----------
        user
            The object or ID of the user to get the cached presence for.

        Returns
        -------
        typing.Optional[hikari.presences.MemberPresence]
            The cached presence object if found, else [`None`][].
        """
        if not isinstance(self.app, traits.CacheAware):
            return None

        return self.app.cache.get_presence(self.id, user)

    def get_voice_state(self, user: snowflakes.SnowflakeishOr[users.PartialUser]) -> voices_.VoiceState | None:
        """Get a cached voice state that belongs to the guild by it's user.

        Parameters
        ----------
        user
            The object or ID of the user to get the cached voice state for.

        Returns
        -------
        typing.Optional[hikari.voices.VoiceState]
            The cached voice state object if found, else [`None`][].
        """
        if not isinstance(self.app, traits.CacheAware):
            return None

        return self.app.cache.get_voice_state(self.id, user)

    def get_emoji(self, emoji: snowflakes.SnowflakeishOr[emojis_.CustomEmoji]) -> emojis_.KnownCustomEmoji | None:
        """Get a cached emoji that belongs to the guild by it's ID or object.

        Parameters
        ----------
        emoji
            The object or ID of the emoji to get from the cache.

        Returns
        -------
        typing.Optional[hikari.emojis.KnownCustomEmoji]
            The object of the custom emoji if found in cache, else
            [`None`][].
        """
        if not isinstance(self.app, traits.CacheAware):
            return None

        emoji_ = self.app.cache.get_emoji(emoji)
        if emoji_ and emoji_.guild_id == self.id:
            return emoji_

        return None

    def get_sticker(self, sticker: snowflakes.SnowflakeishOr[stickers.GuildSticker]) -> stickers.GuildSticker | None:
        """Get a cached sticker that belongs to the guild by it's ID or object.

        Parameters
        ----------
        sticker
            The object or ID of the sticker to get from the cache.

        Returns
        -------
        typing.Optional[hikari.stickers.GuildSticker]
            The object of the sticker if found in cache, else
            [`None`][].
        """
        if not isinstance(self.app, traits.CacheAware):
            return None

        sticker_ = self.app.cache.get_sticker(sticker)
        if sticker_ and sticker_.guild_id == self.id:
            return sticker_

        return None

    def get_role(self, role: snowflakes.SnowflakeishOr[PartialRole]) -> Role | None:
        """Get a cached role that belongs to the guild by it's ID or object.

        Parameters
        ----------
        role
            The object or ID of the role to get for this guild from the cache.

        Returns
        -------
        typing.Optional[Role]
            The object of the role found in cache, else [`None`][].
        """
        if not isinstance(self.app, traits.CacheAware):
            return None

        role_ = self.app.cache.get_role(role)
        if role_ and role_.guild_id == self.id:
            return role_

        return None

    async def fetch_owner(self) -> Member:
        """Fetch the owner of the guild.

        Returns
        -------
        hikari.guilds.Member
            The guild owner.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild or the user are not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        return await self.app.rest.fetch_member(self.id, self.owner_id)

    async def fetch_widget_channel(self) -> channels_.GuildChannel | None:
        """Fetch the widget channel.

        This will be [`None`][] if not set.

        Returns
        -------
        typing.Optional[hikari.channels.GuildChannel]
            The channel the widget is linked to or else [`None`][].

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
        if not self.widget_channel_id:
            return None

        widget_channel = await self.app.rest.fetch_channel(self.widget_channel_id)
        assert isinstance(widget_channel, channels_.GuildChannel)
        return widget_channel

    async def fetch_afk_channel(self) -> channels_.GuildVoiceChannel | None:
        """Fetch the channel that AFK voice users get sent to.

        Returns
        -------
        typing.Optional[hikari.channels.GuildVoiceChannel]
            The AFK channel or [`None`][] if not enabled.

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
        if not self.afk_channel_id:
            return None

        afk_channel = await self.app.rest.fetch_channel(self.afk_channel_id)
        assert isinstance(afk_channel, channels_.GuildVoiceChannel)
        return afk_channel

    async def fetch_system_channel(self) -> channels_.GuildTextChannel | None:
        """Fetch the system channel.

        Returns
        -------
        typing.Optional[hikari.channels.GuildTextChannel]
            The system channel for this guild or [`None`][] if not
            enabled.

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
        if not self.system_channel_id:
            return None

        system_channel = await self.app.rest.fetch_channel(self.system_channel_id)
        assert isinstance(system_channel, channels_.GuildTextChannel)
        return system_channel

    async def fetch_rules_channel(self) -> channels_.GuildTextChannel | None:
        """Fetch the channel where guilds display rules and guidelines.

        If the [`hikari.guilds.GuildFeature.COMMUNITY`][] feature is not defined, then this is [`None`][].

        Returns
        -------
        typing.Optional[hikari.channels.GuildTextChannel]
            The channel where the rules of the guild are specified or else [`None`][].

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
        if not self.rules_channel_id:
            return None

        rules_channel = await self.app.rest.fetch_channel(self.rules_channel_id)
        assert isinstance(rules_channel, channels_.GuildTextChannel)
        return rules_channel

    async def fetch_public_updates_channel(self) -> channels_.GuildTextChannel | None:
        """Fetch channel ID of the channel where admins and moderators receive notices from Discord.

        This is only present if [`hikari.guilds.GuildFeature.COMMUNITY`][] is in [`hikari.guilds.Guild.features`][] for
        this guild. For all other purposes, it should be considered to be [`None`][].

        Returns
        -------
        typing.Optional[hikari.channels.GuildTextChannel]
            The channel where discord sends relevant updates to moderators and admins.

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
        if not self.public_updates_channel_id:
            return None

        updates_channel = await self.app.rest.fetch_channel(self.public_updates_channel_id)
        assert isinstance(updates_channel, channels_.GuildTextChannel)
        return updates_channel


@attrs.define(unsafe_hash=True, kw_only=True, weakref_slot=False)
class RESTGuild(Guild):
    """Guild specialization that is sent via the REST API only."""

    emojis: typing.Mapping[snowflakes.Snowflake, emojis_.KnownCustomEmoji] = attrs.field(
        eq=False, hash=False, repr=False
    )
    """A mapping of emoji IDs to the objects of the emojis this guild provides."""

    stickers: typing.Mapping[snowflakes.Snowflake, stickers.GuildSticker] = attrs.field(
        eq=False, hash=False, repr=False
    )
    """A mapping of sticker IDs to the objects of the stickers this guild provides."""

    roles: typing.Mapping[snowflakes.Snowflake, Role] = attrs.field(eq=False, hash=False, repr=False)
    """The roles in this guild, represented as a mapping of role ID to role object."""

    approximate_active_member_count: int | None = attrs.field(eq=False, hash=False, repr=False)
    """The approximate number of members in the guild that are not offline.

    This will be [`None`][] when creating a guild.
    """

    approximate_member_count: int | None = attrs.field(eq=False, hash=False, repr=False)
    """The approximate number of members in the guild.

    This will be [`None`][] when creating a guild.
    """

    max_presences: int | None = attrs.field(eq=False, hash=False, repr=False)
    """The maximum number of presences for the guild.

    If [`None`][], then there is no limit.
    """

    max_members: int = attrs.field(eq=False, hash=False, repr=False)
    """The maximum number of members allowed in this guild."""


@attrs.define(unsafe_hash=True, kw_only=True, weakref_slot=False)
class GatewayGuild(Guild):
    """Guild specialization that is sent via the gateway only."""

    is_large: bool | None = attrs.field(eq=False, hash=False, repr=False)
    """Whether the guild is considered to be large or not.

    This information is only available if the guild was sent via a `GUILD_CREATE`
    event. If the guild is received from any other place, this will always be
    [`None`][].

    The implications of a large guild are that presence information will not be
    sent about members who are offline or invisible.
    """

    joined_at: datetime.datetime | None = attrs.field(eq=False, hash=False, repr=False)
    """The date and time that the bot user joined this guild.

    This information is only available if the guild was sent via a `GUILD_CREATE`
    event. If the guild is received from any other place, this will always be
    [`None`][].
    """

    member_count: int | None = attrs.field(eq=False, hash=False, repr=False)
    """The number of members in this guild.

    This information is only available if the guild was sent via a `GUILD_CREATE`
    event. If the guild is received from any other place, this will always be
    [`None`][].
    """
