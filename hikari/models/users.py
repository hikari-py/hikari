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

__all__: typing.Final[typing.Sequence[str]] = ["User", "OwnUser", "UserFlag", "PremiumType"]

import enum
import typing

import attr

from hikari.utilities import cdn
from hikari.utilities import files
from hikari.utilities import snowflake
from hikari.utilities import undefined

if typing.TYPE_CHECKING:
    from hikari.api import rest


@enum.unique
@typing.final
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

    def __str__(self) -> str:
        return self.name


@enum.unique
@typing.final
class PremiumType(int, enum.Enum):
    """The types of Nitro."""

    NONE = 0
    """No premium."""

    NITRO_CLASSIC = 1
    """Premium including basic perks like animated emojis and avatars."""

    NITRO = 2
    """Premium including all perks (e.g. 2 server boosts)."""

    def __str__(self) -> str:
        return self.name


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class PartialUser(snowflake.Unique):
    """Represents partial information about a user.

    This is pretty much the same as a normal user, but information may not be
    present.
    """

    id: snowflake.Snowflake = attr.ib(
        converter=snowflake.Snowflake, eq=True, hash=True, repr=True, factory=snowflake.Snowflake,
    )
    """The ID of this entity."""

    app: rest.IRESTClient = attr.ib(default=None, repr=False, eq=False, hash=False)
    """The client application that models may use for procedures."""

    discriminator: typing.Union[str, undefined.UndefinedType] = attr.ib(eq=False, hash=False, repr=True)
    """This user's discriminator."""

    username: typing.Union[str, undefined.UndefinedType] = attr.ib(eq=False, hash=False, repr=True)
    """This user's username."""

    avatar_hash: typing.Union[None, str, undefined.UndefinedType] = attr.ib(eq=False, hash=False, repr=False)
    """This user's avatar hash, if set."""

    is_bot: typing.Union[bool, undefined.UndefinedType] = attr.ib(eq=False, hash=False, repr=False)
    """Whether this user is a bot account."""

    is_system: typing.Union[bool, undefined.UndefinedType] = attr.ib(eq=False, hash=False)
    """Whether this user is a system account."""

    flags: typing.Union[UserFlag, undefined.UndefinedType] = attr.ib(eq=False, hash=False)
    """The public flags for this user."""

    def __str__(self) -> str:
        return f"{self.username}#{self.discriminator}"


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class User(PartialUser):
    """Represents partial information about a user."""

    # These are not attribs on purpose. The idea is to narrow the types of
    # these fields without redefining them twice in the slots. This is
    # compatible with MYPY, hence why I have done it like this...

    discriminator: str
    """This user's discriminator."""

    username: str
    """This user's username."""

    avatar_hash: typing.Optional[str]
    """This user's avatar hash, if they have one, otherwise `None`."""

    is_bot: bool
    """`True` if this user is a bot account, `False` otherwise."""

    is_system: bool
    """`True` if this user is a system account, `False` otherwise."""

    flags: UserFlag
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
        return await self.app.rest.fetch_user(user=self.id)

    @property
    def avatar(self) -> typing.Optional[files.URL]:
        """Avatar for the user if set, else `None`."""
        return self.format_avatar()

    def format_avatar(self, *, format_: typing.Optional[str] = None, size: int = 4096) -> typing.Optional[files.URL]:
        """Generate the avatar for this user, if set.

        If no custom avatar is set, this returns `None`. You can then use the
        `default_avatar_url` attribute instead to fetch the displayed URL.

        Parameters
        ----------
        format_ : str or `None`
            The format to use for this URL, defaults to `png` or `gif`.
            Supports `png`, `jpeg`, `jpg`, `webp` and `gif` (when
            animated). Will be ignored for default avatars which can only be
            `png`.

            If `None`, then the correct default format is determined based on
            whether the icon is animated or not.
        size : int
            The size to set for the URL, defaults to `4096`.
            Can be any power of two between 16 and 4096.
            Will be ignored for default avatars.

        Returns
        -------
        hikari.utilities.files.URL
            The URL to the avatar, or `None` if not present.

        Raises
        ------
        ValueError
            If `size` is not a power of two or not between 16 and 4096.
        """
        if self.avatar_hash is None:
            return None

        if format_ is None:
            if self.avatar_hash.startswith("a_"):
                format_ = "gif"
            else:
                format_ = "png"

        return cdn.generate_cdn_url("avatars", str(self.id), self.avatar_hash, format_=format_, size=size)

    @property
    def default_avatar(self) -> files.URL:  # noqa: D401 imperative mood check
        """Placeholder default avatar for the user."""
        return cdn.get_default_avatar_url(self.discriminator)

    @property
    def default_avatar_index(self) -> int:
        """Integer representation of this user's default avatar."""
        return cdn.get_default_avatar_index(self.discriminator)


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class OwnUser(User):
    """Represents a user with extended OAuth2 information."""

    is_mfa_enabled: bool = attr.ib(eq=False, hash=False, repr=False)
    """Whether the user's account has multi-factor authentication enabled."""

    locale: typing.Optional[str] = attr.ib(eq=False, hash=False, repr=False)
    """The user's set language. This is not provided by the `READY` event."""

    is_verified: typing.Optional[bool] = attr.ib(eq=False, hash=False, repr=False)
    """Whether the email for this user's account has been verified.

    Will be `None` if retrieved through the OAuth2 flow without the `email`
    scope.
    """

    email: typing.Optional[str] = attr.ib(eq=False, hash=False, repr=False)
    """The user's set email.

    Will be `None` if retrieved through OAuth2 flow without the `email`
    scope. Will always be `None` for bot users.
    """

    flags: UserFlag = attr.ib(eq=False, hash=False, repr=False)
    """This user account's flags."""

    premium_type: typing.Optional[PremiumType] = attr.ib(eq=False, hash=False, repr=False)
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
        return await self.app.rest.fetch_my_user()
