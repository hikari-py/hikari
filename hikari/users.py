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
"""Components and entities that are used to describe Users on Discord."""
__all__ = ["User", "MyUser", "UserFlag", "PremiumType"]

import enum
import typing

import attr

from hikari import entities
from hikari import snowflakes
from hikari.internal import urls
from hikari.internal import marshaller


@enum.unique
class UserFlag(enum.IntFlag):
    """The known user flags that represent account badges."""

    #: None
    NONE = 0

    #: Discord Empoloyee
    DISCORD_EMPLOYEE = 1 << 0

    #: Discord Partner
    DISCORD_PARTNER = 1 << 1

    #: HypeSquad Events
    HYPESQUAD_EVENTS = 1 << 2

    #: Bug Hunter Level 1
    BUG_HUNTER_LEVEL_1 = 1 << 3

    #: House of Bravery
    HOUSE_BRAVERY = 1 << 6

    #: House of Brilliance
    HOUSE_BRILLIANCE = 1 << 7

    #: House of Balance
    HOUSE_BALANCE = 1 << 8

    #: Early Supporter
    EARLY_SUPPORTER = 1 << 9

    #: Team user
    TEAM_USER = 1 << 10

    #: System
    SYSTEM = 1 << 12

    #: Bug Hunter Level 2
    BUG_HUNTER_LEVEL_2 = 1 << 14

    #: Verified Bot
    VERIFIED_BOT = 1 << 16

    #: Verified Bot Developer
    VERIFIED_BOT_DEVELOPER = 1 << 17


@enum.unique
class PremiumType(enum.IntEnum):
    """The types of Nitro."""

    #: No premium.
    NONE = 0

    #: Premium including basic perks like animated emojis and avatars.
    NITRO_CLASSIC = 1

    #: Premium including all perks (e.g. 2 server boosts).
    NITRO = 2


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class User(snowflakes.UniqueEntity, entities.Deserializable):
    """Represents a user."""

    #: This user's discriminator.
    #:
    #: :type: :obj:`~str`
    discriminator: str = marshaller.attrib(deserializer=str)

    #: This user's username.
    #:
    #: :type: :obj:`~str`
    username: str = marshaller.attrib(deserializer=str)

    #: This user's avatar hash, if set.
    #:
    #: :type: :obj:`~str`, optional
    avatar_hash: typing.Optional[str] = marshaller.attrib(raw_name="avatar", deserializer=str, if_none=None)

    #: Whether this user is a bot account.
    #:
    #: :type: :obj:`~bool`
    is_bot: bool = marshaller.attrib(raw_name="bot", deserializer=bool, if_undefined=False, default=False)

    #: Whether this user is a system account.
    #:
    #: :type: :obj:`~bool`
    is_system: bool = marshaller.attrib(raw_name="system", deserializer=bool, if_undefined=False, default=False)

    #: The public flags for this user.
    #:
    #: Note
    #: ----
    #: This will be :obj:`~None` if it's a webhook user.
    #:
    #:
    #: :type: :obj:`~UserFlag`, optional
    flags: typing.Optional[UserFlag] = marshaller.attrib(
        raw_name="public_flags", deserializer=UserFlag, if_undefined=None, default=None
    )

    @property
    def avatar_url(self) -> str:
        """URL for this user's custom avatar if set, else default."""
        return self.format_avatar_url()

    def format_avatar_url(self, fmt: typing.Optional[str] = None, size: int = 4096) -> str:
        """Generate the avatar URL for this user's custom avatar if set, else their default avatar.

        Parameters
        ----------
        fmt : :obj:`~str`
            The format to use for this URL, defaults to ``png`` or ``gif``.
            Supports ``png``, ``jpeg``, ``jpg``, ``webp`` and ``gif`` (when
            animated). Will be ignored for default avatars which can only be
            ``png``.
        size : :obj:`~int`
            The size to set for the URL, defaults to ``4096``.
            Can be any power of two between 16 and 4096.
            Will be ignored for default avatars.

        Returns
        -------
        :obj:`~str`
            The string URL.

        Raises
        ------
        :obj:`~ValueError`
            If ``size`` is not a power of two or not between 16 and 4096.
        """
        if not self.avatar_hash:
            return urls.generate_cdn_url("embed/avatars", str(self.default_avatar), fmt="png", size=None)
        if fmt is None and self.avatar_hash.startswith("a_"):
            fmt = "gif"
        elif fmt is None:
            fmt = "png"
        return urls.generate_cdn_url("avatars", str(self.id), self.avatar_hash, fmt=fmt, size=size)

    @property
    def default_avatar(self) -> int:
        """Integer representation of this user's default avatar."""
        return int(self.discriminator) % 5


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class MyUser(User):
    """Represents a user with extended oauth2 information."""

    #: Whether the user's account has 2fa enabled.
    #:
    #: :type: :obj:`~bool`
    is_mfa_enabled: bool = marshaller.attrib(raw_name="mfa_enabled", deserializer=bool)

    #: The user's set language. This is not provided by the ``READY`` event.
    #:
    #: :type: :obj:`~str`, optional
    locale: typing.Optional[str] = marshaller.attrib(deserializer=str, if_none=None, if_undefined=None, default=None)

    #: Whether the email for this user's account has been verified.
    #: Will be :obj:`~None` if retrieved through the oauth2 flow without the
    #: ``email`` scope.
    #:
    #: :type: :obj:`~bool`, optional
    is_verified: typing.Optional[bool] = marshaller.attrib(
        raw_name="verified", deserializer=bool, if_undefined=None, default=None
    )

    #: The user's set email.
    #: Will be :obj:`~None` if retrieved through the oauth2 flow without the
    #: ``email`` scope and for bot users.
    #:
    #: :type: :obj:`~str`, optional
    email: typing.Optional[str] = marshaller.attrib(deserializer=str, if_undefined=None, if_none=None, default=None)

    #: This user account's flags.
    #:
    #: :type: :obj:`~UserFlag`
    flags: UserFlag = marshaller.attrib(deserializer=UserFlag)

    #: The type of Nitro Subscription this user account had.
    #: This will always be :obj:`~None` for bots.
    #:
    #: :type: :obj:`~PremiumType`, optional
    premium_type: typing.Optional[PremiumType] = marshaller.attrib(
        deserializer=PremiumType, if_undefined=None, default=None
    )
