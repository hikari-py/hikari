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
"""Components and entities that are used to describe invites on Discord."""

from __future__ import annotations

__all__ = ["TargetUserType", "VanityUrl", "InviteGuild", "Invite", "InviteWithMetadata"]

import datetime
import typing

import attr

from hikari import bases
from hikari import channels
from hikari import guilds
from hikari import users
from hikari.internal import conversions
from hikari.internal import marshaller
from hikari.internal import more_enums
from hikari.internal import urls


@more_enums.must_be_unique
class TargetUserType(int, more_enums.Enum):
    """The reason a invite targets a user."""

    STREAM = 1
    """This invite is targeting a "Go Live" stream."""


@marshaller.marshallable()
@attr.s(eq=True, hash=True, kw_only=True, slots=True)
class VanityUrl(bases.Entity, marshaller.Deserializable):
    """A special case invite object, that represents a guild's vanity url."""

    code: str = marshaller.attrib(deserializer=str, eq=True, hash=True, repr=True)
    """The code for this invite."""

    uses: int = marshaller.attrib(deserializer=int, eq=False, hash=False, repr=True)
    """The amount of times this invite has been used."""


@marshaller.marshallable()
@attr.s(eq=True, hash=True, kw_only=True, slots=True)
class InviteGuild(guilds.PartialGuild):
    """Represents the partial data of a guild that'll be attached to invites."""

    splash_hash: typing.Optional[str] = marshaller.attrib(
        raw_name="splash", deserializer=str, if_none=None, eq=False, hash=False
    )
    """The hash of the splash for the guild, if there is one."""

    banner_hash: typing.Optional[str] = marshaller.attrib(
        raw_name="banner", deserializer=str, if_none=None, eq=False, hash=False
    )
    """The hash for the guild's banner.

    This is only present if `hikari.guilds.GuildFeature.BANNER` is in the
    `features` for this guild. For all other purposes, it is `None`.
    """

    description: typing.Optional[str] = marshaller.attrib(deserializer=str, if_none=None, eq=False, hash=False)
    """The guild's description.

    This is only present if certain `features` are set in this guild.
    Otherwise, this will always be `None`. For all other purposes, it is `None`.
    """

    verification_level: guilds.GuildVerificationLevel = marshaller.attrib(
        deserializer=guilds.GuildVerificationLevel, eq=False, hash=False
    )
    """The verification level required for a user to participate in this guild."""

    vanity_url_code: typing.Optional[str] = marshaller.attrib(
        if_none=None, deserializer=str, eq=False, hash=False, repr=True
    )
    """The vanity URL code for the guild's vanity URL.

    This is only present if `hikari.guilds.GuildFeature.VANITY_URL` is in the
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
        str, optional
            The string URL.

        Raises
        ------
        ValueError
            If `size` is not a power of two or not between 16 and 4096.
        """
        if self.splash_hash:
            return urls.generate_cdn_url("splashes", str(self.id), self.splash_hash, format_=format_, size=size)
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
        str, optional
            The string URL.

        Raises
        ------
        ValueError
            If `size` is not a power of two or not between 16 and 4096.
        """
        if self.banner_hash:
            return urls.generate_cdn_url("banners", str(self.id), self.banner_hash, format_=format_, size=size)
        return None

    @property
    def banner_url(self) -> typing.Optional[str]:
        """URL for this guild's banner, if set."""
        return self.format_banner_url()


@marshaller.marshallable()
@attr.s(eq=True, hash=True, kw_only=True, slots=True)
class Invite(bases.Entity, marshaller.Deserializable):
    """Represents an invite that's used to add users to a guild or group dm."""

    code: str = marshaller.attrib(deserializer=str, eq=True, hash=True, repr=True)
    """The code for this invite."""

    guild: typing.Optional[InviteGuild] = marshaller.attrib(
        deserializer=InviteGuild.deserialize,
        if_undefined=None,
        inherit_kwargs=True,
        default=None,
        eq=False,
        hash=False,
        repr=True,
    )
    """The partial object of the guild this dm belongs to.

    Will be `None` for group dm invites.
    """

    channel: channels.PartialChannel = marshaller.attrib(
        deserializer=channels.PartialChannel.deserialize, inherit_kwargs=True, eq=False, hash=False, repr=True,
    )
    """The partial object of the channel this invite targets."""

    inviter: typing.Optional[users.User] = marshaller.attrib(
        deserializer=users.User.deserialize, if_undefined=None, inherit_kwargs=True, default=None, eq=False, hash=False,
    )
    """The object of the user who created this invite."""

    target_user: typing.Optional[users.User] = marshaller.attrib(
        deserializer=users.User.deserialize, if_undefined=None, inherit_kwargs=True, default=None, eq=False, hash=False,
    )
    """The object of the user who this invite targets, if set."""

    target_user_type: typing.Optional[TargetUserType] = marshaller.attrib(
        deserializer=TargetUserType, if_undefined=None, default=None, eq=False, hash=False,
    )
    """The type of user target this invite is, if applicable."""

    approximate_presence_count: typing.Optional[int] = marshaller.attrib(
        deserializer=int, if_undefined=None, default=None, eq=False, hash=False,
    )
    """The approximate amount of presences in this invite's guild.

    This is only present when `with_counts` is passed as `True` to the GET
    Invites endpoint.
    """

    approximate_member_count: typing.Optional[int] = marshaller.attrib(
        deserializer=int, if_undefined=None, default=None, eq=False, hash=False,
    )
    """The approximate amount of members in this invite's guild.

    This is only present when `with_counts` is passed as `True` to the GET
    Invites endpoint.
    """


def _max_age_deserializer(age: int) -> datetime.timedelta:
    return datetime.timedelta(seconds=age) if age > 0 else None


@marshaller.marshallable()
@attr.s(eq=True, hash=True, kw_only=True, slots=True)
class InviteWithMetadata(Invite):
    """Extends the base `Invite` object with metadata.

    The metadata is only returned when getting an invite with
    guild permissions, rather than it's code.
    """

    uses: int = marshaller.attrib(deserializer=int, eq=False, hash=False, repr=True)
    """The amount of times this invite has been used."""

    max_uses: int = marshaller.attrib(deserializer=int, eq=False, hash=False, repr=True)
    """The limit for how many times this invite can be used before it expires.

    If set to `0` then this is unlimited.
    """

    max_age: typing.Optional[datetime.timedelta] = marshaller.attrib(
        deserializer=_max_age_deserializer, eq=False, hash=False
    )
    """The timedelta of how long this invite will be valid for.

    If set to `None` then this is unlimited.
    """

    is_temporary: bool = marshaller.attrib(raw_name="temporary", deserializer=bool, eq=False, hash=False, repr=True)
    """Whether this invite grants temporary membership."""

    created_at: datetime.datetime = marshaller.attrib(deserializer=conversions.parse_iso_8601_ts, eq=False, hash=False)
    """When this invite was created."""

    @property
    def expires_at(self) -> typing.Optional[datetime.datetime]:
        """When this invite should expire, if `InviteWithMetadata.max_age` is set.

        If this invite doesn't have a set expiry then this will be `None`.
        """
        if self.max_age:
            return self.created_at + self.max_age
        return None
