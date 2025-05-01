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

__all__: typing.Sequence[str] = ("Invite", "InviteCode", "InviteGuild", "InviteWithMetadata", "TargetType", "VanityURL")

import abc
import typing

import attrs

from hikari import guilds
from hikari import undefined
from hikari import urls
from hikari.internal import attrs_extensions
from hikari.internal import deprecation
from hikari.internal import enums
from hikari.internal import routes
from hikari.internal import typing_extensions

if typing.TYPE_CHECKING:
    import datetime

    from hikari import applications
    from hikari import channels
    from hikari import files
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

    @property
    @deprecation.deprecated("Use 'make_splash_url' instead.")
    def splash_url(self) -> files.URL | None:
        """Splash URL for the guild, if set."""
        deprecation.warn_deprecated(
            "splash_url", removal_version="2.5.0", additional_info="Use 'make_splash_url' instead."
        )
        return self.make_splash_url()

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

    @property
    @deprecation.deprecated("Use 'make_banner_url' instead.")
    def banner_url(self) -> files.URL | None:
        """Banner URL for the guild, if set."""
        deprecation.warn_deprecated(
            "banner_url", removal_version="2.5.0", additional_info="Use 'make_banner_url' instead."
        )
        return self.make_banner_url()

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

    channel_id: snowflakes.Snowflake = attrs.field(eq=False, hash=False, repr=True)
    """The ID of the channel this invite targets."""

    inviter: users.User | None = attrs.field(eq=False, hash=False, repr=False)
    """The object of the user who created this invite."""

    target_type: TargetType | int | None = attrs.field(eq=False, hash=False, repr=False)
    """The type of the target of this invite, if applicable."""

    target_user: users.User | None = attrs.field(eq=False, hash=False, repr=False)
    """The object of the user who this invite targets, if set."""

    target_application: applications.InviteApplication | None = attrs.field(eq=False, hash=False, repr=False)
    """The embedded application this invite targets, if applicable."""

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
