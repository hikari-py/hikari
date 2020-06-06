#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019-2020
#
# This file is part of Hikari.
#
# Hikari is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hikari is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Hikari. If not, see <https://www.gnu.org/licenses/>.
"""Application and entities that are used to describe invites on Discord."""

from __future__ import annotations

__all__ = ["TargetUserType", "VanityURL", "InviteGuild", "Invite", "InviteWithMetadata"]

import enum
import typing

import attr

from hikari.models import bases
from hikari.models import guilds
from hikari.utilities import cdn

if typing.TYPE_CHECKING:
    import datetime

    from hikari.models import channels
    from hikari.models import users
    from hikari.utilities import snowflake


@enum.unique
class TargetUserType(int, enum.Enum):
    """The reason a invite targets a user."""

    STREAM = 1
    """This invite is targeting a "Go Live" stream."""


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class VanityURL(bases.Entity):
    """A special case invite object, that represents a guild's vanity url."""

    code: str = attr.ib(eq=True, hash=True, repr=True)
    """The code for this invite."""

    uses: int = attr.ib(eq=False, hash=False, repr=True)
    """The amount of times this invite has been used."""


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class InviteGuild(guilds.PartialGuild):
    """Represents the partial data of a guild that'll be attached to invites."""

    splash_hash: typing.Optional[str] = attr.ib(eq=False, hash=False)
    """The hash of the splash for the guild, if there is one."""

    banner_hash: typing.Optional[str] = attr.ib(eq=False, hash=False)
    """The hash for the guild's banner.

    This is only present if `hikari.models.guilds.GuildFeature.BANNER` is in the
    `features` for this guild. For all other purposes, it is `None`.
    """

    description: typing.Optional[str] = attr.ib(eq=False, hash=False)
    """The guild's description.

    This is only present if certain `features` are set in this guild.
    Otherwise, this will always be `None`. For all other purposes, it is `None`.
    """

    verification_level: guilds.GuildVerificationLevel = attr.ib(eq=False, hash=False)
    """The verification level required for a user to participate in this guild."""

    vanity_url_code: typing.Optional[str] = attr.ib(eq=False, hash=False, repr=True)
    """The vanity URL code for the guild's vanity URL.

    This is only present if `hikari.models.guilds.GuildFeature.VANITY_URL` is in the
    `features` for this guild. If not, this will always be `None`.
    """

    def format_splash_url(self, *, format_: str = "png", size: int = 4096) -> typing.Optional[str]:
        """Generate the URL for this guild's splash, if set.

        Parameters
        ----------
        format_ : str
            The format to use for this URL, defaults to `png`.
            Supports `png`, `jpeg`, `jpg` and `webp`.
        size : int
            The size to set for the URL, defaults to `4096`.
            Can be any power of two between 16 and 4096.

        Returns
        -------
        str or None
            The string URL.

        Raises
        ------
        ValueError
            If `size` is not a power of two or not between 16 and 4096.
        """
        if self.splash_hash:
            return cdn.generate_cdn_url("splashes", str(self.id), self.splash_hash, format_=format_, size=size)
        return None

    @property
    def splash_url(self) -> typing.Optional[str]:
        """URL for this guild's splash, if set."""
        return self.format_splash_url()

    def format_banner_url(self, *, format_: str = "png", size: int = 4096) -> typing.Optional[str]:
        """Generate the URL for this guild's banner, if set.

        Parameters
        ----------
        format_ : str
            The format to use for this URL, defaults to `png`.
            Supports `png`, `jpeg`, `jpg` and `webp`.
        size : int
            The size to set for the URL, defaults to `4096`.
            Can be any power of two between 16 and 4096.

        Returns
        -------
        str or None
            The string URL.

        Raises
        ------
        ValueError
            If `size` is not a power of two or not between 16 and 4096.
        """
        if self.banner_hash:
            return cdn.generate_cdn_url("banners", str(self.id), self.banner_hash, format_=format_, size=size)
        return None

    @property
    def banner_url(self) -> typing.Optional[str]:
        """URL for this guild's banner, if set."""
        return self.format_banner_url()


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class Invite(bases.Entity):
    """Represents an invite that's used to add users to a guild or group dm."""

    code: str = attr.ib(eq=True, hash=True, repr=True)
    """The code for this invite."""

    guild: typing.Optional[InviteGuild] = attr.ib(eq=False, hash=False, repr=False)
    """The partial object of the guild this invite belongs to.

    Will be `None` for group DM invites and when attached to a gateway event;
    for invites received over the gateway you should refer to `Invite.guild_id`.
    """

    guild_id: typing.Optional[snowflake.Snowflake] = attr.ib(eq=False, hash=False, repr=True)
    """The ID of the guild this invite belongs to.

    Will be `None` for group DM invites.
    """

    channel: typing.Optional[channels.PartialChannel] = attr.ib(eq=False, hash=False, repr=False)
    """The partial object of the channel this invite targets.

    Will be `None` for invite objects that are attached to gateway events,
    in which case you should refer to `Invite.channel_id`.
    """

    channel_id: snowflake.Snowflake = attr.ib(eq=False, hash=False, repr=True)
    """The ID of the channel this invite targets."""

    inviter: typing.Optional[users.User] = attr.ib(eq=False, hash=False)
    """The object of the user who created this invite."""

    target_user: typing.Optional[users.User] = attr.ib(eq=False, hash=False)
    """The object of the user who this invite targets, if set."""

    target_user_type: typing.Optional[TargetUserType] = attr.ib(eq=False, hash=False)
    """The type of user target this invite is, if applicable."""

    approximate_presence_count: typing.Optional[int] = attr.ib(eq=False, hash=False)
    """The approximate amount of presences in this invite's guild.

    This is only present when `with_counts` is passed as `True` to the GET
    Invites endpoint.
    """

    approximate_member_count: typing.Optional[int] = attr.ib(eq=False, hash=False)
    """The approximate amount of members in this invite's guild.

    This is only present when `with_counts` is passed as `True` to the GET
    Invites endpoint.
    """


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class InviteWithMetadata(Invite):
    """Extends the base `Invite` object with metadata.

    The metadata is only returned when getting an invite with
    guild permissions, rather than it's code.
    """

    uses: int = attr.ib(eq=False, hash=False, repr=True)
    """The amount of times this invite has been used."""

    max_uses: int = attr.attrib(eq=False, hash=False, repr=True)
    """The limit for how many times this invite can be used before it expires.

    If set to `0` then this is unlimited.
    """

    max_age: typing.Optional[datetime.timedelta] = attr.attrib(eq=False, hash=False)
    """The timedelta of how long this invite will be valid for.

    If set to `None` then this is unlimited.
    """

    is_temporary: bool = attr.attrib(eq=False, hash=False, repr=True)
    """Whether this invite grants temporary membership."""

    created_at: datetime.datetime = attr.attrib(eq=False, hash=False)
    """When this invite was created."""

    @property
    def expires_at(self) -> typing.Optional[datetime.datetime]:
        """When this invite should expire, if `InviteWithMetadata.max_age` is set.

        If this invite doesn't have a set expiry then this will be `None`.
        """
        if self.max_age:
            return self.created_at + self.max_age
        return None
