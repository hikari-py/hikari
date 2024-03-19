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
"""Application and entities that are used to describe invites on Discord."""

from __future__ import annotations

__all__: typing.Sequence[str] = ("TargetType", "VanityURL", "InviteGuild", "InviteCode", "Invite", "InviteWithMetadata")

import abc
import typing

import attrs

from hikari import guilds
from hikari import urls
from hikari.internal import attrs_extensions
from hikari.internal import enums
from hikari.internal import routes

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

    def __str__(self) -> str:
        return f"https://discord.gg/{self.code}"


@attrs_extensions.with_copy
@attrs.define(hash=True, kw_only=True, weakref_slot=False)
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


@attrs.define(hash=True, kw_only=True, weakref_slot=False)
class InviteGuild(guilds.PartialGuild):
    """Represents the partial data of a guild that is attached to invites."""

    features: typing.Sequence[typing.Union[str, guilds.GuildFeature]] = attrs.field(eq=False, hash=False, repr=False)
    """A list of the features in this guild."""

    splash_hash: typing.Optional[str] = attrs.field(eq=False, hash=False, repr=False)
    """The hash of the splash for the guild, if there is one."""

    banner_hash: typing.Optional[str] = attrs.field(eq=False, hash=False, repr=False)
    """The hash for the guild's banner.

    This is only present if [`hikari.guilds.GuildFeature.BANNER`][] is in the
    `features` for this guild. For all other purposes, it is [`None`][].
    """

    description: typing.Optional[str] = attrs.field(eq=False, hash=False, repr=False)
    """The guild's description."""

    verification_level: typing.Union[guilds.GuildVerificationLevel, int] = attrs.field(eq=False, hash=False, repr=False)
    """The verification level required for a user to participate in this guild."""

    vanity_url_code: typing.Optional[str] = attrs.field(eq=False, hash=False, repr=True)
    """The vanity URL code for the guild's vanity URL.

    This is only present if [`hikari.guilds.GuildFeature.VANITY_URL`][] is in the
    `features` for this guild. If not, this will always be [`None`][].
    """

    welcome_screen: typing.Optional[guilds.WelcomeScreen] = attrs.field(eq=False, hash=False, repr=False)
    """The welcome screen of a community guild shown to new members, if set."""

    nsfw_level: guilds.GuildNSFWLevel = attrs.field(eq=False, hash=False, repr=False)
    """The NSFW level of the guild."""

    @property
    def splash_url(self) -> typing.Optional[files.URL]:
        """Splash URL for the guild, if set."""
        return self.make_splash_url()

    def make_splash_url(self, *, ext: str = "png", size: int = 4096) -> typing.Optional[files.URL]:
        """Generate the guild's splash image URL, if set.

        Parameters
        ----------
        ext : str
            The extension to use for this URL.
            supports `png`, `jpeg`, `jpg` and `webp`.
        size : int
            The size to set for the URL.
            Can be any power of two between `16` and `4096`.

        Returns
        -------
        typing.Optional[hikari.files.URL]
            The URL to the splash, or [`None`][] if not set.

        Raises
        ------
        ValueError
            If `size` is not a power of two or not between 16 and 4096.
        """
        if self.splash_hash is None:
            return None

        return routes.CDN_GUILD_SPLASH.compile_to_file(
            urls.CDN_URL, guild_id=self.id, hash=self.splash_hash, size=size, file_format=ext
        )

    @property
    def banner_url(self) -> typing.Optional[files.URL]:
        """Banner URL for the guild, if set."""
        return self.make_banner_url()

    def make_banner_url(self, *, ext: typing.Optional[str] = None, size: int = 4096) -> typing.Optional[files.URL]:
        """Generate the guild's banner image URL, if set.

        Parameters
        ----------
        ext : typing.Optional[str]
            The ext to use for this URL.
            Supports `png`, `jpeg`, `jpg`, `webp` and `gif` (when
            animated).

            If [`None`][], then the correct default extension is
            determined based on whether the banner is animated or not.
        size : int
            The size to set for the URL.
            Can be any power of two between `16` and `4096`.

        Returns
        -------
        typing.Optional[hikari.files.URL]
            The URL of the banner, or [`None`][] if no banner is set.

        Raises
        ------
        ValueError
            If `size` is not a power of two or not between 16 and 4096.
        """
        if self.banner_hash is None:
            return None

        if ext is None:
            if self.banner_hash.startswith("a_"):
                ext = "gif"

            else:
                ext = "png"

        return routes.CDN_GUILD_BANNER.compile_to_file(
            urls.CDN_URL, guild_id=self.id, hash=self.banner_hash, size=size, file_format=ext
        )


@attrs_extensions.with_copy
@attrs.define(hash=True, kw_only=True, weakref_slot=False)
class Invite(InviteCode):
    """Represents an invite that's used to add users to a guild or group dm."""

    app: traits.RESTAware = attrs.field(
        repr=False, eq=False, hash=False, metadata={attrs_extensions.SKIP_DEEP_COPY: True}
    )
    """Client application that models may use for procedures."""

    code: str = attrs.field(hash=True, repr=True)
    """The code for this invite."""

    guild: typing.Optional[InviteGuild] = attrs.field(eq=False, hash=False, repr=False)
    """The partial object of the guild this invite belongs to.

    Will be [`None`][] for group DM invites and when attached to a gateway event;
    for invites received over the gateway you should refer to [`hikari.invites.Invite.guild_id`][].
    """

    guild_id: typing.Optional[snowflakes.Snowflake] = attrs.field(eq=False, hash=False, repr=True)
    """The ID of the guild this invite belongs to.

    Will be [`None`][] for group DM invites.
    """

    channel: typing.Optional[channels.PartialChannel] = attrs.field(eq=False, hash=False, repr=False)
    """The partial object of the channel this invite targets.

    Will be [`None`][] for invite objects that are attached to gateway events,
    in which case you should refer to [`hikari.invites.Invite.channel_id`][].
    """

    channel_id: snowflakes.Snowflake = attrs.field(eq=False, hash=False, repr=True)
    """The ID of the channel this invite targets."""

    inviter: typing.Optional[users.User] = attrs.field(eq=False, hash=False, repr=False)
    """The object of the user who created this invite."""

    target_type: typing.Union[TargetType, int, None] = attrs.field(eq=False, hash=False, repr=False)
    """The type of the target of this invite, if applicable."""

    target_user: typing.Optional[users.User] = attrs.field(eq=False, hash=False, repr=False)
    """The object of the user who this invite targets, if set."""

    target_application: typing.Optional[applications.InviteApplication] = attrs.field(eq=False, hash=False, repr=False)
    """The embedded application this invite targets, if applicable."""

    approximate_active_member_count: typing.Optional[int] = attrs.field(eq=False, hash=False, repr=False)
    """The approximate amount of presences in this invite's guild.

    This is only returned by the GET REST Invites endpoint.
    """

    approximate_member_count: typing.Optional[int] = attrs.field(eq=False, hash=False, repr=False)
    """The approximate amount of members in this invite's guild.

    This is only returned by the GET Invites REST endpoint.
    """

    expires_at: typing.Optional[datetime.datetime] = attrs.field(eq=False, hash=False, repr=False)
    """When this invite will expire.

    This field is only returned by the GET Invite REST endpoint and will be
    returned as [`None`][] by said endpoint if the invite doesn't have a set
    expiry date. Other places will always return this as [`None`][].
    """


@attrs.define(hash=True, kw_only=True, weakref_slot=False)
class InviteWithMetadata(Invite):
    """Extends the base [`hikari.invites.Invite`][] object with metadata.

    The metadata is only returned when getting an invite with
    guild permissions, rather than it's code.
    """

    uses: int = attrs.field(eq=False, hash=False, repr=True)
    """The amount of times this invite has been used."""

    max_uses: typing.Optional[int] = attrs.field(eq=False, hash=False, repr=True)
    """The limit for how many times this invite can be used before it expires.

    If set to [`None`][] then this is unlimited.
    """

    # TODO: can we use a non-None value to represent infinity here somehow, or
    # make a timedelta that is infinite for comparisons?
    max_age: typing.Optional[datetime.timedelta] = attrs.field(eq=False, hash=False, repr=False)
    """The timedelta of how long this invite will be valid for.

    If set to [`None`][] then this is unlimited.
    """

    is_temporary: bool = attrs.field(eq=False, hash=False, repr=True)
    """Whether this invite grants temporary membership."""

    created_at: datetime.datetime = attrs.field(eq=False, hash=False, repr=False)
    """When this invite was created."""

    expires_at: typing.Optional[datetime.datetime]
    """When this invite will expire.

    If this invite doesn't have a set expiry then this will be [`None`][].
    """

    @property
    def uses_left(self) -> typing.Optional[int]:
        """Return the number of uses left for this invite.

        This will be [`None`][] if the invite has unlimited uses.
        """
        if self.max_uses:
            return self.max_uses - self.uses

        return None
