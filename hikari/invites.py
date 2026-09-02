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
"""Application and entities that are used to describe invites on Discord."""

from __future__ import annotations

__all__: typing.Sequence[str] = (
    "Invite",
    "InviteCode",
    "InviteFlags",
    "InviteGuild",
    "InviteRole",
    "InviteType",
    "InviteWithMetadata",
    "TargetType",
    "VanityURL",
)

import abc
import typing

import attrs

from hikari import guilds
from hikari import undefined
from hikari import urls
from hikari.internal import attrs_extensions
from hikari.internal import enums
from hikari.internal import routes
from hikari.internal import typing_extensions

if typing.TYPE_CHECKING:
    import datetime

    from hikari import applications
    from hikari import channels
    from hikari import colors as colors_
    from hikari import colours as colours_
    from hikari import emojis as emojis_
    from hikari import files
    from hikari import scheduled_events as scheduled_events_
    from hikari import snowflakes
    from hikari import traits
    from hikari import users


@typing.final
class TargetType(int, enums.Enum):
    """The target of the invite."""

    STREAM = 1
    """This invite is targeting a "Go Live" stream."""

    EMBEDDED_APPLICATION = 2
    """This invite is targeting an embedded application."""


@typing.final
class InviteType(int, enums.Enum):
    """The type of an invite."""

    GUILD = 0
    """This invite is inviting to a guild."""

    GROUP_DM = 1
    """This invite is inviting to a group DM."""

    FRIEND = 2
    """This invite is a friend invite, inviting directly to a user."""


@typing.final
class InviteFlags(enums.Flag):
    """The flags of a guild invite."""

    NONE = 0
    """No flags set."""

    IS_GUEST_INVITE = 1 << 0
    """This invite is a guest invite for a voice channel."""


class InviteCode(abc.ABC):
    """A representation of a guild/channel invite."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def code(self) -> str:
        """Code for this invite."""

    @typing_extensions.override
    def __str__(self) -> str:
        return f"https://discord.gg/{self.code}"


@attrs_extensions.with_copy
@attrs.define(unsafe_hash=True, kw_only=True, weakref_slot=False)
class VanityURL(InviteCode):
    """A special case invite object, that represents a guild's vanity url."""

    app: traits.RESTAware = attrs.field(
        repr=False, eq=False, hash=False, metadata={attrs_extensions.SKIP_DEEP_COPY: True}
    )
    """Client application that models may use for procedures."""

    code: str = attrs.field(hash=True, repr=True)
    """The code for this invite."""

    uses: int = attrs.field(eq=False, hash=False, repr=True)
    """The amount of times this invite has been used."""


@attrs.define(unsafe_hash=True, kw_only=True, weakref_slot=False)
class InviteGuild(guilds.PartialGuild):
    """Represents the partial data of a guild that is attached to invites."""

    features: typing.Sequence[str | guilds.GuildFeature] = attrs.field(eq=False, hash=False, repr=False)
    """A list of the features in this guild."""

    splash_hash: str | None = attrs.field(eq=False, hash=False, repr=False)
    """The hash of the splash for the guild, if there is one."""

    banner_hash: str | None = attrs.field(eq=False, hash=False, repr=False)
    """The hash for the guild's banner.

    This is only present if [`hikari.guilds.GuildFeature.BANNER`][] is in the
    `features` for this guild. For all other purposes, it is [`None`][].
    """

    description: str | None = attrs.field(eq=False, hash=False, repr=False)
    """The guild's description."""

    verification_level: guilds.GuildVerificationLevel | int = attrs.field(eq=False, hash=False, repr=False)
    """The verification level required for a user to participate in this guild."""

    vanity_url_code: str | None = attrs.field(eq=False, hash=False, repr=True)
    """The vanity URL code for the guild's vanity URL.

    This is only present if [`hikari.guilds.GuildFeature.VANITY_URL`][] is in the
    `features` for this guild. If not, this will always be [`None`][].
    """

    welcome_screen: guilds.WelcomeScreen | None = attrs.field(eq=False, hash=False, repr=False)
    """The welcome screen of a community guild shown to new members, if set."""

    nsfw_level: guilds.GuildNSFWLevel = attrs.field(eq=False, hash=False, repr=False)
    """The NSFW level of the guild."""

    def make_splash_url(
        self,
        *,
        file_format: typing.Literal["PNG", "JPEG", "JPG", "WEBP"] = "PNG",
        size: int = 4096,
        lossless: bool = True,
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

        return routes.CDN_GUILD_SPLASH.compile_to_file(
            urls.CDN_URL, guild_id=self.id, hash=self.splash_hash, size=size, file_format=file_format, lossless=lossless
        )

    def make_banner_url(
        self,
        *,
        file_format: undefined.UndefinedOr[
            typing.Literal["PNG", "JPEG", "JPG", "WEBP", "AWEBP", "GIF"]
        ] = undefined.UNDEFINED,
        size: int = 4096,
        lossless: bool = True,
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

        if not file_format:
            file_format = "GIF" if self.banner_hash.startswith("a_") else "PNG"

        return routes.CDN_GUILD_BANNER.compile_to_file(
            urls.CDN_URL, guild_id=self.id, hash=self.banner_hash, size=size, file_format=file_format, lossless=lossless
        )


@attrs_extensions.with_copy
@attrs.define(unsafe_hash=True, kw_only=True, weakref_slot=False)
class InviteRole(guilds.PartialRole):
    """Represents the partial role objects attached to an invite.

    These are the roles which will be assigned to the user upon accepting
    the invite.
    """

    color: colors_.Color = attrs.field(eq=False, hash=False, repr=True)
    """The colour of this role."""

    colors: colors_.ColorGradient = attrs.field(eq=False, hash=False, repr=True)
    """The colors of this role.

    Unlike the [`color`][hikari.invites.InviteRole.color] field, this can also
    hold the role's gradient or holographic colors if set.
    """

    position: int = attrs.field(eq=False, hash=False, repr=True)
    """The position of this role in the role hierarchy."""

    icon_hash: str | None = attrs.field(eq=False, hash=False, repr=False)
    """Hash of the role's icon if set, else [`None`][]."""

    unicode_emoji: emojis_.UnicodeEmoji | None = attrs.field(eq=False, hash=False, repr=False)
    """Unicode emoji that makes up the role's icon, if set."""

    @property
    def colour(self) -> colours_.Colour:
        """Alias for the `color` field."""
        return self.color

    @property
    def colours(self) -> colours_.ColourGradient:
        """Alias for the `colors` field."""
        return self.colors

    def make_icon_url(
        self,
        *,
        file_format: typing.Literal["PNG", "JPEG", "JPG", "WEBP"] = "PNG",
        size: int = 4096,
        lossless: bool = True,
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

        return routes.CDN_ROLE_ICON.compile_to_file(
            urls.CDN_URL, role_id=self.id, hash=self.icon_hash, size=size, file_format=file_format, lossless=lossless
        )


@attrs_extensions.with_copy
@attrs.define(unsafe_hash=True, kw_only=True, weakref_slot=False)
class Invite(InviteCode):
    """Represents an invite that's used to add users to a guild or group dm."""

    app: traits.RESTAware = attrs.field(
        repr=False, eq=False, hash=False, metadata={attrs_extensions.SKIP_DEEP_COPY: True}
    )
    """Client application that models may use for procedures."""

    code: str = attrs.field(hash=True, repr=True)
    """The code for this invite."""

    type: InviteType | int = attrs.field(eq=False, hash=False, repr=True)
    """The type of this invite.

    !!! note
        Invite payloads attached to gateway events don't include the type,
        in which case this will default to [`hikari.invites.InviteType.GUILD`][].
    """

    guild: InviteGuild | None = attrs.field(eq=False, hash=False, repr=False)
    """The partial object of the guild this invite belongs to.

    Will be [`None`][] for group DM invites and when attached to a gateway event;
    for invites received over the gateway you should refer to [`hikari.invites.Invite.guild_id`][].
    """

    guild_id: snowflakes.Snowflake | None = attrs.field(eq=False, hash=False, repr=True)
    """The ID of the guild this invite belongs to.

    Will be [`None`][] for group DM invites.
    """

    channel: channels.PartialChannel | None = attrs.field(eq=False, hash=False, repr=False)
    """The partial object of the channel this invite targets.

    Will be [`None`][] for invite objects that are attached to gateway events,
    in which case you should refer to [`hikari.invites.Invite.channel_id`][].
    """

    channel_id: snowflakes.Snowflake | None = attrs.field(eq=False, hash=False, repr=True)
    """The ID of the channel this invite targets.

    Will be [`None`][] for friend invites, which target a user directly
    instead of a channel.
    """

    inviter: users.User | None = attrs.field(eq=False, hash=False, repr=False)
    """The object of the user who created this invite."""

    target_type: TargetType | int | None = attrs.field(eq=False, hash=False, repr=False)
    """The type of the target of this invite, if applicable."""

    target_user: users.User | None = attrs.field(eq=False, hash=False, repr=False)
    """The object of the user who this invite targets, if set."""

    target_application: applications.InviteApplication | None = attrs.field(eq=False, hash=False, repr=False)
    """The embedded application this invite targets, if applicable."""

    guild_scheduled_event: scheduled_events_.ScheduledEvent | None = attrs.field(eq=False, hash=False, repr=False)
    """The scheduled event data attached to this invite, if any."""

    flags: InviteFlags = attrs.field(eq=False, hash=False, repr=False)
    """The flags of this guild invite."""

    roles: typing.Sequence[InviteRole] = attrs.field(eq=False, hash=False, repr=False)
    """The partial objects of the roles assigned to the user upon accepting this invite.

    !!! note
        Invite payloads attached to gateway events only include the role IDs,
        in which case this will be empty and you should refer to
        [`hikari.invites.Invite.role_ids`][].
    """

    role_ids: typing.Sequence[snowflakes.Snowflake] = attrs.field(eq=False, hash=False, repr=False)
    """The IDs of the roles assigned to the user upon accepting this invite."""

    approximate_active_member_count: int | None = attrs.field(eq=False, hash=False, repr=False)
    """The approximate amount of presences in this invite's guild.

    This is only returned by the GET REST Invites endpoint.
    """

    approximate_member_count: int | None = attrs.field(eq=False, hash=False, repr=False)
    """The approximate amount of members in this invite's guild.

    This is only returned by the GET Invites REST endpoint.
    """

    expires_at: datetime.datetime | None = attrs.field(eq=False, hash=False, repr=False)
    """When this invite will expire.

    This field is only returned by the GET Invite REST endpoint and will be
    returned as [`None`][] by said endpoint if the invite doesn't have a set
    expiry date. Other places will always return this as [`None`][].
    """


@attrs.define(unsafe_hash=True, kw_only=True, weakref_slot=False)
class InviteWithMetadata(Invite):
    """Extends the base [`hikari.invites.Invite`][] object with metadata.

    The metadata is only returned when getting an invite with
    guild permissions, rather than it's code.
    """

    uses: int = attrs.field(eq=False, hash=False, repr=True)
    """The amount of times this invite has been used."""

    max_uses: int | None = attrs.field(eq=False, hash=False, repr=True)
    """The limit for how many times this invite can be used before it expires.

    If set to [`None`][] then this is unlimited.
    """

    # TODO: can we use a non-None value to represent infinity here somehow, or
    # make a timedelta that is infinite for comparisons?
    max_age: datetime.timedelta | None = attrs.field(eq=False, hash=False, repr=False)
    """The timedelta of how long this invite will be valid for.

    If set to [`None`][] then this is unlimited.
    """

    is_temporary: bool = attrs.field(eq=False, hash=False, repr=True)
    """Whether this invite grants temporary membership."""

    created_at: datetime.datetime = attrs.field(eq=False, hash=False, repr=False)
    """When this invite was created."""

    expires_at: datetime.datetime | None
    """When this invite will expire.

    If this invite doesn't have a set expiry then this will be [`None`][].
    """

    @property
    def uses_left(self) -> int | None:
        """Return the number of uses left for this invite.

        This will be [`None`][] if the invite has unlimited uses.
        """
        if self.max_uses:
            return self.max_uses - self.uses

        return None
