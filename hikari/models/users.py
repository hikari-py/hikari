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

__all__: typing.Final[typing.List[str]] = ["PartialUser", "User", "OwnUser", "UserFlag", "PremiumType"]

import abc
import enum
import typing

import attr

from hikari.utilities import constants
from hikari.utilities import files
from hikari.utilities import routes
from hikari.utilities import snowflake
from hikari.utilities import undefined

if typing.TYPE_CHECKING:
    from hikari.api.rest import app as rest_app


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


class User(snowflake.Unique, abc.ABC):
    """Interface for any user-like object.

    This does not include partial users, as they may not be fully formed.
    """

    __slots__ = ()

    @property
    @abc.abstractmethod
    def discriminator(self) -> str:
        """Discriminator for the user."""

    @property
    @abc.abstractmethod
    def username(self) -> str:
        """Username for the user."""

    @property
    @abc.abstractmethod
    def avatar_hash(self) -> typing.Optional[str]:
        """Avatar hash for the user, if they have one, otherwise `builtins.None`."""

    @property
    @abc.abstractmethod
    def is_bot(self) -> bool:
        """`builtins.True` if this user is a bot account, `builtins.False` otherwise."""

    @property
    @abc.abstractmethod
    def is_system(self) -> bool:
        """`builtins.True` if this user is a system account, `builtins.False` otherwise."""

    @property
    @abc.abstractmethod
    def flags(self) -> UserFlag:
        """Flag bits that are set for the user."""

    @property
    @abc.abstractmethod
    def mention(self) -> str:
        """Return a raw mention string for the given user.

        Example
        -------

        ```py
        >>> some_user.mention
        '<@123456789123456789>'
        ```

        Returns
        -------
        builtins.str
            The mention string to use.
        """

    @property
    @abc.abstractmethod
    def avatar(self) -> files.URL:
        """Avatar for the user, or the default avatar if not set."""

    # noinspection PyShadowingBuiltins
    @abc.abstractmethod
    def format_avatar(self, *, format: typing.Optional[str] = None, size: int = 4096) -> typing.Optional[files.URL]:
        """Generate the avatar for this user, if set.

        If no custom avatar is set, this returns `builtins.None`. You can then
        use the `default_avatar_url` attribute instead to fetch the displayed
        URL.

        Parameters
        ----------
        format : builtins.str or builtins.None
            The format to use for this URL, defaults to `png` or `gif`.
            Supports `png`, `jpeg`, `jpg`, `webp` and `gif` (when
            animated). Will be ignored for default avatars which can only be
            `png`.

            If `builtins.None`, then the correct default format is determined
            based on whether the icon is animated or not.
        size : builtins.int
            The size to set for the URL, defaults to `4096`.
            Can be any power of two between 16 and 4096.
            Will be ignored for default avatars.

        Returns
        -------
        hikari.utilities.files.URL or builtins.None
            The URL to the avatar, or `builtins.None` if not present.

        Raises
        ------
        builtins.ValueError
            If `size` is not a power of two or not between 16 and 4096.
        builtins.LookupError
            If the avatar hash is not known. This will occur if `avatar_hash`
            was not provided by Discord, and is
            `hikari.utilities.undefined.UNDEFINED`.
            This will only ever occur for `PartialUser` objects, regular
            `User` objects should never be expected to raise this.
        """

    @property
    @abc.abstractmethod
    def default_avatar(self) -> files.URL:  # noqa: D401 imperative mood check
        """Placeholder default avatar for the user if no avatar is set.

        Raises
        ------
         builtins.LookupError
            If the descriminator is not known. This will occur if
            `discriminator` was not provided by Discord, and is
            `hikari.utilities.undefined.UNDEFINED`.
            This will only ever occur for `PartialUser` objects, regular
            `User` objects should never be expected to raise this.
        """


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class PartialUser(snowflake.Unique):
    """Represents partial information about a user.

    This is pretty much the same as a normal user, but information may not be
    present.
    """

    id: snowflake.Snowflake = attr.ib(
        converter=snowflake.Snowflake, eq=True, hash=True, repr=True, factory=snowflake.Snowflake,
    )
    """The ID of this user."""

    app: rest_app.IRESTApp = attr.ib(default=None, repr=False, eq=False, hash=False)
    """Reference to the client application that models may use for procedures."""

    discriminator: typing.Union[str, undefined.UndefinedType] = attr.ib(eq=False, hash=False, repr=True)
    """Four-digit discriminator for the user."""

    username: typing.Union[str, undefined.UndefinedType] = attr.ib(eq=False, hash=False, repr=True)
    """Username of the user."""

    avatar_hash: typing.Union[None, str, undefined.UndefinedType] = attr.ib(eq=False, hash=False, repr=False)
    """Avatar hash of the user, if a custom avatar is set."""

    is_bot: typing.Union[bool, undefined.UndefinedType] = attr.ib(eq=False, hash=False, repr=False)
    """Whether this user is a bot account."""

    is_system: typing.Union[bool, undefined.UndefinedType] = attr.ib(eq=False, hash=False)
    """Whether this user is a system account."""

    flags: typing.Union[UserFlag, undefined.UndefinedType] = attr.ib(eq=False, hash=False)
    """Public flags for this user."""

    @property
    def mention(self) -> str:
        """Return a raw mention string for the given user.

        Example
        -------

        ```py
        >>> some_user.mention
        '<@123456789123456789>'
        ```

        Returns
        -------
        builtins.str
            The mention string to use.
        """
        return f"<@{self.id}>"

    def __str__(self) -> str:
        if self.username is undefined.UNDEFINED or self.discriminator is undefined.UNDEFINED:
            return f"Partial user ID {self.id}"
        return f"{self.username}#{self.discriminator}"

    async def fetch_self(self) -> UserImpl:
        """Get this user's up-to-date object.

        Returns
        -------
        hikari.models.users.UserImpl
            The requested user object.

        Raises
        ------
        hikari.errors.NotFound
            If the user is not found.
        """
        return await self.app.rest.fetch_user(user=self.id)

    @property
    def avatar(self) -> files.URL:
        """Avatar for the user, or the default avatar if not set."""
        return self.format_avatar() or self.default_avatar

    # noinspection PyShadowingBuiltins
    def format_avatar(self, *, format: typing.Optional[str] = None, size: int = 4096) -> typing.Optional[files.URL]:
        """Generate the avatar for this user, if set.

        If no custom avatar is set, this returns `builtins.None`. You can then
        use the `default_avatar_url` attribute instead to fetch the displayed
        URL.

        Parameters
        ----------
        format : builtins.str or builtins.None
            The format to use for this URL, defaults to `png` or `gif`.
            Supports `png`, `jpeg`, `jpg`, `webp` and `gif` (when
            animated). Will be ignored for default avatars which can only be
            `png`.

            If `builtins.None`, then the correct default format is determined
            based on whether the icon is animated or not.
        size : builtins.int
            The size to set for the URL, defaults to `4096`.
            Can be any power of two between 16 and 4096.
            Will be ignored for default avatars.

        Returns
        -------
        hikari.utilities.files.URL or builtins.None
            The URL to the avatar, or `builtins.None` if not present.

        Raises
        ------
        builtins.ValueError
            If `size` is not a power of two or not between 16 and 4096.
        builtins.LookupError
            If the avatar hash is not known. This will occur if `avatar_hash`
            was not provided by Discord, and is
            `hikari.utilities.undefined.UNDEFINED`.
            This will only ever occur for `PartialUser` objects, regular
            `User` objects should never be expected to raise this.
        """
        if self.avatar_hash is undefined.UNDEFINED:
            raise LookupError("Unknown avatar hash for PartialUser")

        if self.avatar_hash is None:
            return None

        if format is None:
            if self.avatar_hash.startswith("a_"):
                # Ignore the fact this shadows `format`, as it is the parameter
                # name, which shadows it anyway.
                format = "gif"  # noqa: A001 shadowing builtin
            else:
                format = "png"  # noqa: A001 shadowing builtin

        return routes.CDN_USER_AVATAR.compile_to_file(
            constants.CDN_URL, user_id=self.id, hash=self.avatar_hash, size=size, file_format=format,
        )

    @property
    def default_avatar(self) -> files.URL:  # noqa: D401 imperative mood check
        """Placeholder default avatar for the user if no avatar is set.

        Raises
        ------
         builtins.LookupError
            If the descriminator is not known. This will occur if
            `discriminator` was not provided by Discord, and is
            `hikari.utilities.undefined.UNDEFINED`.
            This will only ever occur for `PartialUser` objects, regular
            `User` objects should never be expected to raise this.
        """
        if self.discriminator is undefined.UNDEFINED:
            raise LookupError("Unknown discriminator for PartialUser")

        return routes.CDN_DEFAULT_USER_AVATAR.compile_to_file(
            constants.CDN_URL, discriminator=self.discriminator % 5, file_format="png",
        )


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class UserImpl(PartialUser, User):
    """Concrete implementation of user information."""

    # These are not attribs on purpose. The idea is to narrow the types of
    # these fields without redefining them twice in the slots. This is
    # compatible with MYPY, hence why I have done it like this...

    discriminator: str
    """The user's discriminator."""

    username: str
    """The user's username."""

    avatar_hash: typing.Optional[str]
    """The user's avatar hash, if they have one, otherwise `builtins.None`."""

    is_bot: bool
    """`builtins.True` if this user is a bot account, `builtins.False` otherwise."""

    is_system: bool
    """`builtins.True` if this user is a system account, `builtins.False` otherwise."""

    flags: UserFlag
    """The public flags for this user."""


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class OwnUser(UserImpl):
    """Represents a user with extended OAuth2 information."""

    is_mfa_enabled: bool = attr.ib(eq=False, hash=False, repr=False)
    """Whether the user's account has multi-factor authentication enabled."""

    locale: typing.Optional[str] = attr.ib(eq=False, hash=False, repr=False)
    """The user's set language. This is not provided by the `READY` event."""

    is_verified: typing.Optional[bool] = attr.ib(eq=False, hash=False, repr=False)
    """Whether the email for this user's account has been verified.

    Will be `builtins.None` if retrieved through the OAuth2 flow without the `email`
    scope.
    """

    email: typing.Optional[str] = attr.ib(eq=False, hash=False, repr=False)
    """The user's set email.

    Will be `builtins.None` if retrieved through OAuth2 flow without the `email`
    scope. Will always be `builtins.None` for bot users.
    """

    premium_type: typing.Optional[PremiumType] = attr.ib(eq=False, hash=False, repr=False)
    """The type of Nitro Subscription this user account had.

    This will always be `builtins.None` for bots.
    """

    async def fetch_self(self) -> OwnUser:
        """Get this user's up-to-date object.

        Returns
        -------
        hikari.models.users.UserImpl
            The requested user object.
        """
        return await self.app.rest.fetch_my_user()
