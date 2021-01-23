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
"""Application and entities that are used to describe invites on Discord."""

from __future__ import annotations

__all__: typing.List[str] = [
    "TargetUserType",
    "VanityURL",
    "InviteGuild",
    "Invite",
    "InviteWithMetadata",
    "Inviteish",
]

import abc
import typing

import attr

from hikari import files
from hikari import guilds
from hikari import snowflakes
from hikari import urls
from hikari.internal import attr_extensions
from hikari.internal import enums
from hikari.internal import routes

if typing.TYPE_CHECKING:
    import datetime

    from hikari import channels
    from hikari import traits
    from hikari import users


@typing.final
class TargetUserType(int, enums.Enum):
    """The reason a invite targets a user."""

    STREAM = 1
    """This invite is targeting a "Go Live" stream."""


class InviteCode(abc.ABC):
    """A representation of a guild/channel invite."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def code(self) -> str:
        """Return the code for this invite.

        Returns
        -------
        builtins.str
            The invite code that can be appended to a URL.
        """


@attr_extensions.with_copy
@attr.s(eq=True, hash=True, init=True, kw_only=True, slots=True, weakref_slot=False)
class VanityURL(InviteCode):
    """A special case invite object, that represents a guild's vanity url."""

    app: traits.RESTAware = attr.ib(repr=False, eq=False, hash=False, metadata={attr_extensions.SKIP_DEEP_COPY: True})
    """The client application that models may use for procedures."""

    code: str = attr.ib(eq=True, hash=True, repr=True)
    """The code for this invite."""

    uses: int = attr.ib(eq=False, hash=False, repr=True)
    """The amount of times this invite has been used."""

    def __str__(self) -> str:
        return f"https://discord.gg/{self.code}"


@attr.s(eq=True, hash=True, init=True, kw_only=True, slots=True, weakref_slot=False)
class InviteGuild(guilds.PartialGuild):
    """Represents the partial data of a guild that is attached to invites."""

    features: typing.Sequence[guilds.GuildFeatureish] = attr.ib(eq=False, hash=False, repr=False)
    """A list of the features in this guild."""

    splash_hash: typing.Optional[str] = attr.ib(eq=False, hash=False, repr=False)
    """The hash of the splash for the guild, if there is one."""

    banner_hash: typing.Optional[str] = attr.ib(eq=False, hash=False, repr=False)
    """The hash for the guild's banner.

    This is only present if `hikari.guilds.GuildFeature.BANNER` is in the
    `features` for this guild. For all other purposes, it is `builtins.None`.
    """

    description: typing.Optional[str] = attr.ib(eq=False, hash=False, repr=False)
    """The guild's description.

    This is only present if certain `features` are set in this guild.
    Otherwise, this will always be `builtins.None`. For all other purposes, it is `builtins.None`.
    """

    verification_level: typing.Union[guilds.GuildVerificationLevel, int] = attr.ib(eq=False, hash=False, repr=False)
    """The verification level required for a user to participate in this guild."""

    vanity_url_code: typing.Optional[str] = attr.ib(eq=False, hash=False, repr=True)
    """The vanity URL code for the guild's vanity URL.

    This is only present if `hikari.guilds.GuildFeature.VANITY_URL` is in the
    `features` for this guild. If not, this will always be `builtins.None`.
    """

    welcome_screen: typing.Optional[guilds.WelcomeScreen] = attr.ib(eq=False, hash=False, repr=False)
    """The welcome screen of a community guild shown to new members, if set."""

    @property
    def splash_url(self) -> typing.Optional[files.URL]:
        """Splash for the guild, if set."""
        return self.format_splash()

    def format_splash(self, *, ext: str = "png", size: int = 4096) -> typing.Optional[files.URL]:
        """Generate the guild's splash image, if set.

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

    @property
    def banner(self) -> typing.Optional[files.URL]:
        """Banner for the guild, if set."""
        return self.format_banner()

    def format_banner(self, *, ext: str = "png", size: int = 4096) -> typing.Optional[files.URL]:
        """Generate the guild's banner image, if set.

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


@attr_extensions.with_copy
@attr.s(eq=True, hash=True, init=True, kw_only=True, slots=True, weakref_slot=False)
class Invite(InviteCode):
    """Represents an invite that's used to add users to a guild or group dm."""

    app: traits.RESTAware = attr.ib(repr=False, eq=False, hash=False, metadata={attr_extensions.SKIP_DEEP_COPY: True})
    """The client application that models may use for procedures."""

    code: str = attr.ib(eq=True, hash=True, repr=True)
    """The code for this invite."""

    guild: typing.Optional[InviteGuild] = attr.ib(eq=False, hash=False, repr=False)
    """The partial object of the guild this invite belongs to.

    Will be `builtins.None` for group DM invites and when attached to a gateway event;
    for invites received over the gateway you should refer to `Invite.guild_id`.
    """

    guild_id: typing.Optional[snowflakes.Snowflake] = attr.ib(eq=False, hash=False, repr=True)
    """The ID of the guild this invite belongs to.

    Will be `builtins.None` for group DM invites.
    """

    channel: typing.Optional[channels.PartialChannel] = attr.ib(eq=False, hash=False, repr=False)
    """The partial object of the channel this invite targets.

    Will be `builtins.None` for invite objects that are attached to gateway events,
    in which case you should refer to `Invite.channel_id`.
    """

    channel_id: snowflakes.Snowflake = attr.ib(eq=False, hash=False, repr=True)
    """The ID of the channel this invite targets."""

    inviter: typing.Optional[users.User] = attr.ib(eq=False, hash=False, repr=False)
    """The object of the user who created this invite."""

    target_user: typing.Optional[users.User] = attr.ib(eq=False, hash=False, repr=False)
    """The object of the user who this invite targets, if set."""

    target_user_type: typing.Union[TargetUserType, int, None] = attr.ib(eq=False, hash=False, repr=False)
    """The type of user target this invite is, if applicable."""

    approximate_active_member_count: typing.Optional[int] = attr.ib(eq=False, hash=False, repr=False)
    """The approximate amount of presences in this invite's guild.

    This is only present when `with_counts` is passed as `builtins.True` to the GET
    Invites endpoint.
    """

    approximate_member_count: typing.Optional[int] = attr.ib(eq=False, hash=False, repr=False)
    """The approximate amount of members in this invite's guild.

    This is only present when `with_counts` is passed as `builtins.True` to the GET
    Invites endpoint.
    """

    def __str__(self) -> str:
        return f"https://discord.gg/{self.code}"


@attr.s(eq=True, hash=True, init=True, kw_only=True, slots=True, weakref_slot=False)
class InviteWithMetadata(Invite):
    """Extends the base `Invite` object with metadata.

    The metadata is only returned when getting an invite with
    guild permissions, rather than it's code.
    """

    uses: int = attr.ib(eq=False, hash=False, repr=True)
    """The amount of times this invite has been used."""

    max_uses: typing.Optional[int] = attr.ib(eq=False, hash=False, repr=True)
    """The limit for how many times this invite can be used before it expires.

    If set to `builtins.None` then this is unlimited.
    """

    # TODO: can we use a non-None value to represent infinity here somehow, or
    # make a timedelta that is infinite for comparisons?
    max_age: typing.Optional[datetime.timedelta] = attr.ib(eq=False, hash=False, repr=False)
    """The timedelta of how long this invite will be valid for.

    If set to `builtins.None` then this is unlimited.
    """

    is_temporary: bool = attr.ib(eq=False, hash=False, repr=True)
    """Whether this invite grants temporary membership."""

    created_at: datetime.datetime = attr.ib(eq=False, hash=False, repr=False)
    """When this invite was created."""

    @property
    def expires_at(self) -> typing.Optional[datetime.datetime]:
        """When this invite should expire, if `InviteWithMetadata.max_age` is set.

        If this invite doesn't have a set expiry then this will be `builtins.None`.
        """
        if self.max_age is not None:
            return self.created_at + self.max_age
        return None


# TODO: converter to remove discord.gg part to allow URLs here too.
Inviteish = typing.Union[str, InviteCode]
"""Type hint for an invite, vanity URL, or invite code.

This must be a representation of an invite that is a `builtins.str` containing
the invite code, an `Invite`/`InviteWithMetadata`, or a `VanityURL` instance.
"""
