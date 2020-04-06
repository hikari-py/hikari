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
__all__ = ["TargetUserType", "VanityUrl", "InviteGuild", "Invite", "InviteWithMetadata"]

import datetime
import enum
import typing

import hikari.internal.conversions
from hikari import channels
from hikari import entities
from hikari import guilds
from hikari import users
from hikari.internal import cdn
from hikari.internal import marshaller


@enum.unique
class TargetUserType(enum.IntEnum):
    """The reason a invite targets a user."""

    #: This invite is targeting a "Go Live" stream.
    STREAM = 1


@marshaller.attrs(slots=True)
class VanityUrl(entities.HikariEntity, entities.Deserializable):
    """A special case invite object, that represents a guild's vanity url."""

    #: The code for this invite.
    #:
    #: :type: :obj:`str`
    code: str = marshaller.attrib(deserializer=str)

    #: The amount of times this invite has been used.
    #:
    #: :type: :obj:`int`
    uses: int = marshaller.attrib(deserializer=int)


@marshaller.attrs(slots=True)
class InviteGuild(guilds.PartialGuild):
    """Represents the partial data of a guild that'll be attached to invites."""

    #: The hash of the splash for the guild, if there is one.
    #:
    #: :type: :obj:`str`, optional
    splash_hash: typing.Optional[str] = marshaller.attrib(raw_name="splash", deserializer=str, if_none=None)

    #: The hash for the guild's banner.
    #:
    #: This is only present if :obj:`hikari.guild.GuildFeature.BANNER`
    #: is in the ``features`` for this guild. For all other purposes, it is ``None``.
    #:
    #: :type: :obj:`str`, optional
    banner_hash: typing.Optional[str] = marshaller.attrib(raw_name="banner", if_none=None, deserializer=str)

    #: The guild's description.
    #:
    #: This is only present if certain ``features`` are set in this guild.
    #: Otherwise, this will always be ``None``. For all other purposes, it is
    #: ``None``.
    #:
    #: :type: :obj:`str`, optional
    description: typing.Optional[str] = marshaller.attrib(if_none=None, deserializer=str)

    #: The verification level required for a user to participate in this guild.
    #:
    #: :type: :obj:`hikari.guilds.GuildVerificationLevel`
    verification_level: guilds.GuildVerificationLevel = marshaller.attrib(deserializer=guilds.GuildVerificationLevel)

    #: The vanity URL code for the guild's vanity URL.
    #:
    #: This is only present if :obj:`hikari.guilds.GuildFeature.VANITY_URL`
    #: is in the ``features`` for this guild. If not, this will always be ``None``.
    #:
    #: :type: :obj:`str`, optional
    vanity_url_code: typing.Optional[str] = marshaller.attrib(if_none=None, deserializer=str)

    def format_splash_url(self, fmt: str = "png", size: int = 2048) -> typing.Optional[str]:
        """Generate the URL for this guild's splash, if set.

        Parameters
        ----------
        fmt : :obj:`str`
            The format to use for this URL, defaults to ``png``.
            Supports ``png``, ``jpeg``, ``jpg` and ``webp``.
        size : :obj:`int`
            The size to set for the URL, defaults to ``2048``.
            Can be any power of two between 16 and 2048.

        Returns
        -------
        :obj:`str`, optional
            The string URL.
        """
        if self.splash_hash:
            return cdn.generate_cdn_url("splashes", str(self.id), self.splash_hash, fmt=fmt, size=size)
        return None

    @property
    def splash_url(self) -> typing.Optional[str]:
        """URL for this guild's splash, if set."""
        return self.format_splash_url()

    def format_banner_url(self, fmt: str = "png", size: int = 2048) -> typing.Optional[str]:
        """Generate the URL for this guild's banner, if set.

        Parameters
        ----------
        fmt : :obj:`str`
            The format to use for this URL, defaults to ``png``.
            Supports ``png``, ``jpeg``, ``jpg`` and ``webp``.
        size : :obj:`int`
            The size to set for the URL, defaults to ``2048``.
            Can be any power of two between 16 and 2048.

        Returns
        -------
        :obj:`str`, optional
            The string URL.
        """
        if self.banner_hash:
            return cdn.generate_cdn_url("banners", str(self.id), self.banner_hash, fmt=fmt, size=size)
        return None

    @property
    def banner_url(self) -> typing.Optional[str]:
        """URL for this guild's banner, if set."""
        return self.format_banner_url()


@marshaller.attrs(slots=True)
class Invite(entities.HikariEntity, entities.Deserializable):
    """Represents an invite that's used to add users to a guild or group dm."""

    #: The code for this invite.
    #:
    #: :type: :obj:`str`
    code: str = marshaller.attrib(deserializer=str)

    #: The partial object of the guild this dm belongs to.
    #: Will be ``None`` for group dm invites.
    #:
    #: :type: :obj:`InviteGuild`, optional
    guild: typing.Optional[InviteGuild] = marshaller.attrib(deserializer=InviteGuild.deserialize, if_undefined=None)
    #: The partial object of the channel this invite targets.
    #:
    #: :type: :obj:`hikari.channels.PartialChannel`
    channel: channels.PartialChannel = marshaller.attrib(deserializer=channels.PartialChannel.deserialize)

    #: The object of the user who created this invite.
    #:
    #: :type: :obj:`hikari.users.User`, optional
    inviter: typing.Optional[users.User] = marshaller.attrib(deserializer=users.User.deserialize, if_undefined=None)

    #: The object of the user who this invite targets, if set.
    #:
    #: :type: :obj:`hikari.users.User`, optional
    target_user: typing.Optional[users.User] = marshaller.attrib(deserializer=users.User.deserialize, if_undefined=None)

    #: The type of user target this invite is, if applicable.
    #:
    #: :type: :obj:`TargetUserType`, optional
    target_user_type: typing.Optional[TargetUserType] = marshaller.attrib(
        deserializer=TargetUserType, if_undefined=None
    )

    #: The approximate amount of presences in this invite's guild, only present
    #: when ``with_counts`` is passed as ``True`` to the GET Invites endpoint.
    #:
    #: :type: :obj:`int`, optional
    approximate_presence_count: typing.Optional[int] = marshaller.attrib(deserializer=int, if_undefined=None)

    #: The approximate amount of members in this invite's guild, only present
    #: when ``with_counts`` is passed as ``True`` to the GET Invites endpoint.
    #:
    #: :type: :obj:`int`, optional
    approximate_member_count: typing.Optional[int] = marshaller.attrib(deserializer=int, if_undefined=None)


@marshaller.attrs(slots=True)
class InviteWithMetadata(Invite):
    """Extends the base :obj:`Invite` object with metadata.

    The metadata is only returned when getting an invite with
    guild permissions, rather than it's code.
    """

    #: The amount of times this invite has been used.
    #:
    #: :type: :obj:`int`
    uses: int = marshaller.attrib(deserializer=int)

    #: The limit for how many times this invite can be used before it expires.
    #: If set to ``0`` then this is unlimited.
    #:
    #: :type: :obj:`int`
    max_uses: int = marshaller.attrib(deserializer=int)

    #: The timedelta of how long this invite will be valid for.
    #: If set to ``None`` then this is unlimited.
    #:
    #: :type: :obj:`datetime.timedelta`, optional
    max_age: typing.Optional[datetime.timedelta] = marshaller.attrib(
        deserializer=lambda age: datetime.timedelta(seconds=age) if age > 0 else None
    )

    #: Whether this invite grants temporary membership.
    #:
    #: :type: :obj:`bool`
    is_temporary: bool = marshaller.attrib(raw_name="temporary", deserializer=bool)

    #: When this invite was created.
    #:
    #: :type: :obj:`datetime.datetime`
    created_at: datetime.datetime = marshaller.attrib(deserializer=hikari.internal.conversions.parse_iso_8601_ts)

    @property
    def expires_at(self) -> typing.Optional[datetime.datetime]:
        """When this invite should expire, if ``max_age`` is set. Else ``None``."""
        if self.max_age:
            return self.created_at + self.max_age
        return None
