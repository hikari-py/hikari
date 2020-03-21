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

from hikari.core import entities
from hikari.core import snowflakes
from hikari.internal_utilities import cdn
from hikari.internal_utilities import marshaller


@marshaller.attrs(slots=True)
class User(snowflakes.UniqueEntity, entities.Deserializable):
    """Represents a user."""

    #: This user's discriminator.
    #:
    #: :type: :obj:`str`
    discriminator: str = marshaller.attrib(deserializer=str)

    #: This user's username.
    #:
    #: :type: :obj:`str`
    username: str = marshaller.attrib(deserializer=str)

    #: This user's avatar hash, if set.
    #:
    #: :type: :obj:`str`, optional
    avatar_hash: typing.Optional[str] = marshaller.attrib(raw_name="avatar", deserializer=str, if_none=None)

    #: Whether this user is a bot account.
    #:
    #: :type: :obj:`bool`
    is_bot: bool = marshaller.attrib(raw_name="bot", deserializer=bool, if_undefined=lambda: False)

    #: Whether this user is a system account.
    #:
    #: :type: :obj:`bool`
    is_system: bool = marshaller.attrib(raw_name="system", deserializer=bool, if_undefined=lambda: False)

    @property
    def avatar_url(self) -> str:
        """The url for this user's custom avatar if set, else default."""
        return self.format_avatar_url()

    def format_avatar_url(self, fmt: typing.Optional[str] = None, size: int = 2048) -> str:
        """Generate the avatar url for this user's custom avatar if set,
        else their default avatar.

        Parameters
        ----------
        fmt : :obj:`str`
            The format to use for this url, defaults to ``png`` or ``gif``.
            Supports ``png``, ``jpeg``, ``jpg``, ``webp`` and ``gif`` (when
            animated). Will be ignored for default avatars which can only be
            ``png``.
        size : :obj:`int`
            The size to set for the url, defaults to ``2048``.
            Can be any power of two between 16 and 2048.
            Will be ignored for default avatars.

        Returns
        -------
        :obj:`str`
            The string url.
        """

        if not self.avatar_hash:
            return cdn.generate_cdn_url("embed/avatars", str(self.default_avatar), fmt="png", size=None)
        # pylint: disable=E1101:
        if fmt is None and self.avatar_hash.startswith("a_"):
            fmt = "gif"
        elif fmt is None:
            fmt = "png"
        return cdn.generate_cdn_url("avatars", str(self.id), self.avatar_hash, fmt=fmt, size=size)

    @property
    def default_avatar(self) -> int:
        """The number representation of this user's default avatar."""
        return int(self.discriminator) % 5


@enum.unique
class UserFlag(enum.IntFlag):
    """The known user flags that represent account badges."""

    NONE = 0
    DISCORD_EMPLOYEE = 1 << 0
    DISCORD_PARTNER = 1 << 1
    HYPESQUAD_EVENTS = 1 << 2
    BUG_HUNTER_LEVEL_1 = 1 << 3
    HOUSE_BRAVERY = 1 << 6
    HOUSE_BRILLIANCE = 1 << 7
    HOUSE_BALANCE = 1 << 8
    EARLY_SUPPORTER = 1 << 9
    TEAM_USER = 1 << 10
    SYSTEM = 1 << 11
    BUG_HUNTER_LEVEL_2 = 1 << 12


@enum.unique
class PremiumType(enum.IntEnum):
    """The types of Nitro."""

    #: No premium.
    NONE = 0
    #: Premium including basic perks like animated emojis and avatars.
    NITRO_CLASSIC = 1
    #: Premium including all perks (e.g. 2 server boosts).
    NITRO = 2


@marshaller.attrs(slots=True)
class MyUser(User):
    """Represents a user with extended oauth2 information."""

    #: Whether the user's account has 2fa enabled.
    #: Requires the ``identify`` scope.
    #:
    #: :type: :obj:`bool`, optional
    is_mfa_enabled: typing.Optional[bool] = marshaller.attrib(
        raw_name="mfa_enabled", deserializer=bool, if_undefined=None
    )

    #: The user's set language, requires the ``identify`` scope.
    #:
    #: :type: :obj:`str`, optional
    locale: typing.Optional[str] = marshaller.attrib(deserializer=str, if_undefined=None)

    #: Whether the email for this user's account has been verified.
    #: Requires the ``email`` scope.
    #:
    #: :type: :obj:`bool`, optional
    is_verified: typing.Optional[bool] = marshaller.attrib(raw_name="verified", deserializer=bool, if_undefined=None)

    #: The user's set email, requires the ``email`` scope.
    #: This will always be ``None`` for bots.
    #:
    #: :type: :obj:`str`, optional
    email: typing.Optional[str] = marshaller.attrib(deserializer=str, if_undefined=None, if_none=None)

    #: This user account's flags, requires the ``identify`` scope.
    #:
    #: :type: :obj:`UserFlag`, optional
    flags: typing.Optional[UserFlag] = marshaller.attrib(deserializer=UserFlag, if_undefined=None)

    #: The type of Nitro Subscription this user account had.
    #: Requires the ``identify`` scope and will always be ``None`` for bots.
    #:
    #: :type: :obj:`PremiumType`, optional
    premium_type: typing.Optional[PremiumType] = marshaller.attrib(deserializer=PremiumType, if_undefined=None)
