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

from __future__ import annotations

__all__ = ["User", "MyUser", "UserFlag", "PremiumType"]

import typing

import attr

from hikari import bases
from hikari.internal import marshaller
from hikari.internal import more_enums
from hikari.internal import urls


@more_enums.must_be_unique
class UserFlag(more_enums.IntFlag):
    """The known user flags that represent account badges."""

    NONE = 0
    """None"""

    DISCORD_EMPLOYEE = 1 << 0
    """Discord Employee"""

    DISCORD_PARTNER = 1 << 1
    """Discord Partner"""

    HYPESQUAD_EVENTS = 1 << 2
    """HypeSquad Events"""

    BUG_HUNTER_LEVEL_1 = 1 << 3
    """Bug Hunter Level 1"""

    HOUSE_BRAVERY = 1 << 6
    """House of Bravery"""

    HOUSE_BRILLIANCE = 1 << 7
    """House of Brilliance"""

    HOUSE_BALANCE = 1 << 8
    """House of Balance"""

    EARLY_SUPPORTER = 1 << 9
    """Early Supporter"""

    TEAM_USER = 1 << 10
    """Team user"""

    SYSTEM = 1 << 12
    """System"""

    BUG_HUNTER_LEVEL_2 = 1 << 14
    """Bug Hunter Level 2"""

    VERIFIED_BOT = 1 << 16
    """Verified Bot"""

    VERIFIED_BOT_DEVELOPER = 1 << 17
    """Verified Bot Developer"""


@more_enums.must_be_unique
class PremiumType(int, more_enums.Enum):
    """The types of Nitro."""

    NONE = 0
    """No premium."""

    NITRO_CLASSIC = 1
    """Premium including basic perks like animated emojis and avatars."""

    NITRO = 2
    """Premium including all perks (e.g. 2 server boosts)."""


@marshaller.marshallable()
@attr.s(
    eq=True, hash=True, kw_only=True, slots=True,
)
class User(bases.Unique, marshaller.Deserializable):
    """Represents a user."""

    discriminator: str = marshaller.attrib(deserializer=str, eq=False, hash=False, repr=True)
    """This user's discriminator."""

    username: str = marshaller.attrib(deserializer=str, eq=False, hash=False, repr=True)
    """This user's username."""

    avatar_hash: typing.Optional[str] = marshaller.attrib(
        raw_name="avatar", deserializer=str, if_none=None, eq=False, hash=False
    )
    """This user's avatar hash, if set."""

    is_bot: bool = marshaller.attrib(
        raw_name="bot", deserializer=bool, if_undefined=False, default=False, eq=False, hash=False
    )
    """Whether this user is a bot account."""

    is_system: bool = marshaller.attrib(
        raw_name="system", deserializer=bool, if_undefined=False, default=False, eq=False, hash=False
    )
    """Whether this user is a system account."""

    flags: typing.Optional[UserFlag] = marshaller.attrib(
        raw_name="public_flags", deserializer=UserFlag, if_undefined=None, default=None, eq=False, hash=False
    )
    """The public flags for this user.

    !!! info
        This will be `None` if it's a webhook user.
    """

    @property
    def avatar_url(self) -> str:
        """URL for this user's custom avatar if set, else default."""
        return self.format_avatar_url()

    def format_avatar_url(self, *, format_: typing.Optional[str] = None, size: int = 4096) -> str:
        """Generate the avatar URL for this user's custom avatar if set, else their default avatar.

        Parameters
        ----------
        format_ : str
            The format to use for this URL, defaults to `png` or `gif`.
            Supports `png`, `jpeg`, `jpg`, `webp` and `gif` (when
            animated). Will be ignored for default avatars which can only be
            `png`.
        size : int
            The size to set for the URL, defaults to `4096`.
            Can be any power of two between 16 and 4096.
            Will be ignored for default avatars.

        Returns
        -------
        str
            The string URL.

        Raises
        ------
        ValueError
            If `size` is not a power of two or not between 16 and 4096.
        """
        if not self.avatar_hash:
            return urls.generate_cdn_url("embed/avatars", str(self.default_avatar), format_="png", size=None)
        if format_ is None and self.avatar_hash.startswith("a_"):
            format_ = "gif"
        elif format_ is None:
            format_ = "png"
        return urls.generate_cdn_url("avatars", str(self.id), self.avatar_hash, format_=format_, size=size)

    @property
    def default_avatar(self) -> int:
        """Integer representation of this user's default avatar."""
        return int(self.discriminator) % 5


@marshaller.marshallable()
@attr.s(eq=True, hash=True, kw_only=True, slots=True)
class MyUser(User):
    """Represents a user with extended oauth2 information."""

    is_mfa_enabled: bool = marshaller.attrib(raw_name="mfa_enabled", deserializer=bool, eq=False, hash=False)
    """Whether the user's account has 2fa enabled."""

    locale: typing.Optional[str] = marshaller.attrib(
        deserializer=str, if_none=None, if_undefined=None, default=None, eq=False, hash=False
    )
    """The user's set language. This is not provided by the `READY` event."""

    is_verified: typing.Optional[bool] = marshaller.attrib(
        raw_name="verified", deserializer=bool, if_undefined=None, default=None, eq=False, hash=False
    )
    """Whether the email for this user's account has been verified.

    Will be `None` if retrieved through the oauth2 flow without the `email`
    scope.
    """

    email: typing.Optional[str] = marshaller.attrib(
        deserializer=str, if_undefined=None, if_none=None, default=None, eq=False, hash=False
    )
    """The user's set email.

    Will be `None` if retrieved through the oauth2 flow without the `email`
    scope and for bot users.
    """

    flags: UserFlag = marshaller.attrib(deserializer=UserFlag, eq=False, hash=False)
    """This user account's flags."""

    premium_type: typing.Optional[PremiumType] = marshaller.attrib(
        deserializer=PremiumType, if_undefined=None, default=None, eq=False, hash=False
    )
    """The type of Nitro Subscription this user account had.

    This will always be `None` for bots.
    """
