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
"""Application and entities that are used to describe Users on Discord."""

from __future__ import annotations

__all__ = ["User", "OwnUser", "UserFlag", "PremiumType"]

import enum
import typing

import attr

from hikari.models import bases
from hikari.utilities import cdn


@enum.unique
class UserFlag(enum.IntFlag):
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


@enum.unique
class PremiumType(int, enum.Enum):
    """The types of Nitro."""

    NONE = 0
    """No premium."""

    NITRO_CLASSIC = 1
    """Premium including basic perks like animated emojis and avatars."""

    NITRO = 2
    """Premium including all perks (e.g. 2 server boosts)."""


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class User(bases.Entity, bases.Unique):
    """Represents a user."""

    discriminator: str = attr.ib(eq=False, hash=False, repr=True)
    """This user's discriminator."""

    username: str = attr.ib(eq=False, hash=False, repr=True)
    """This user's username."""

    avatar_hash: typing.Optional[str] = attr.ib(eq=False, hash=False)
    """This user's avatar hash, if set."""

    is_bot: bool = attr.ib(eq=False, hash=False)
    """Whether this user is a bot account."""

    is_system: bool = attr.ib(eq=False, hash=False)
    """Whether this user is a system account."""

    flags: UserFlag = attr.ib(eq=False, hash=False)
    """The public flags for this user."""

    async def fetch_self(self) -> User:
        """Get this user's up-to-date object.

        Returns
        -------
        hikari.models.users.User
            The requested user object.

        Raises
        ------
        hikari.errors.NotFound
            If the user is not found.
        """
        return await self._app.rest.fetch_user(user=self.id)

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
            return self.default_avatar_url

        if format_ is None and self.avatar_hash.startswith("a_"):
            format_ = "gif"
        elif format_ is None:
            format_ = "png"
        return cdn.generate_cdn_url("avatars", str(self.id), self.avatar_hash, format_=format_, size=size)

    @property
    def default_avatar_index(self) -> int:
        """Integer representation of this user's default avatar."""
        return int(self.discriminator) % 5

    @property
    def default_avatar_url(self) -> str:
        """URL for this user's default avatar."""
        return cdn.generate_cdn_url("embed", "avatars", str(self.default_avatar_index), format_="png", size=None)


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class OwnUser(User):
    """Represents a user with extended OAuth2 information."""

    is_mfa_enabled: bool = attr.ib(eq=False, hash=False)
    """Whether the user's account has 2fa enabled."""

    locale: typing.Optional[str] = attr.ib(eq=False, hash=False)
    """The user's set language. This is not provided by the `READY` event."""

    is_verified: typing.Optional[bool] = attr.ib(eq=False, hash=False)
    """Whether the email for this user's account has been verified.

    Will be `None` if retrieved through the oauth2 flow without the `email`
    scope.
    """

    email: typing.Optional[str] = attr.ib(eq=False, hash=False)
    """The user's set email.

    Will be `None` if retrieved through the oauth2 flow without the `email`
    scope and for bot users.
    """

    flags: UserFlag = attr.ib(eq=False, hash=False)
    """This user account's flags."""

    premium_type: typing.Optional[PremiumType] = attr.ib(eq=False, hash=False)
    """The type of Nitro Subscription this user account had.

    This will always be `None` for bots.
    """

    async def fetch_self(self) -> OwnUser:
        """Get this user's up-to-date object.

        Returns
        -------
        hikari.models.users.User
            The requested user object.
        """
        return await self._app.rest.fetch_me()
