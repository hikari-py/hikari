# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
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
"""Application and entities that are used to describe Users on Discord."""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = ["PartialUser", "User", "OwnUser", "UserFlag", "PremiumType"]

import abc
import enum
import typing

import attr

from hikari import files
from hikari import snowflakes
from hikari import undefined
from hikari.utilities import attr_extensions
from hikari.utilities import constants
from hikari.utilities import flag
from hikari.utilities import routes

if typing.TYPE_CHECKING:
    from hikari import traits


@enum.unique
@typing.final
class UserFlag(flag.Flag):
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

    EARLY_VERIFIED_DEVELOPER = 1 << 17
    """Verified Bot Developer.

    Only applies to users that verified their account before 20th August 2019.
    """


@enum.unique
@typing.final
class PremiumType(enum.IntEnum):
    """The types of Nitro."""

    NONE = 0
    """No premium."""

    NITRO_CLASSIC = 1
    """Premium including basic perks like animated emojis and avatars."""

    NITRO = 2
    """Premium including all perks (e.g. 2 server boosts)."""

    def __str__(self) -> str:
        return self.name


@attr.s(eq=True, hash=True, init=True, kw_only=True, slots=True, weakref_slot=False)
class PartialUser(snowflakes.Unique, abc.ABC):
    """A partial interface for a user.

    Fields may or may not be present, and must be checked explicitly if so.

    This is pretty much the same as a normal user, but information may not be
    present.
    """

    @property
    @abc.abstractmethod
    def app(self) -> traits.RESTAware:
        """Client application that models may use for procedures."""

    @property
    @abc.abstractmethod
    def discriminator(self) -> undefined.UndefinedOr[str]:
        """Discriminator for the user."""

    @property
    @abc.abstractmethod
    def username(self) -> undefined.UndefinedOr[str]:
        """Username for the user."""

    @property
    @abc.abstractmethod
    def avatar_hash(self) -> undefined.UndefinedNoneOr[str]:
        """Avatar hash for the user, if they have one, otherwise `builtins.None`."""

    @property
    @abc.abstractmethod
    def is_bot(self) -> undefined.UndefinedOr[bool]:
        """`builtins.True` if this user is a bot account, `builtins.False` otherwise."""

    @property
    @abc.abstractmethod
    def is_system(self) -> undefined.UndefinedOr[bool]:
        """`builtins.True` if this user is a system account, `builtins.False` otherwise."""

    @property
    @abc.abstractmethod
    def flags(self) -> undefined.UndefinedOr[UserFlag]:
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


@attr.s(eq=True, hash=True, init=True, kw_only=True, slots=True, weakref_slot=False)
class User(PartialUser, abc.ABC):
    """Interface for any user-like object.

    This does not include partial users, as they may not be fully formed.
    """

    @property
    @abc.abstractmethod
    def app(self) -> traits.RESTAware:
        """Client application that models may use for procedures."""

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
        format : typing.Optional[builtins.str]
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
        typing.Optional[hikari.files.URL]
            The URL to the avatar, or `builtins.None` if not present.

        Raises
        ------
        builtins.ValueError
            If `size` is not a power of two or not between 16 and 4096.
        """
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
        """Placeholder default avatar for the user if no avatar is set."""
        return routes.CDN_DEFAULT_USER_AVATAR.compile_to_file(
            constants.CDN_URL, discriminator=int(self.discriminator) % 5, file_format="png",
        )


@attr_extensions.with_copy
@attr.s(eq=True, hash=True, init=True, kw_only=True, slots=True, weakref_slot=False)
class PartialUserImpl(PartialUser):
    """Implementation for partial information about a user.

    This is pretty much the same as a normal user, but information may not be
    present.
    """

    id: snowflakes.Snowflake = attr.ib(eq=True, hash=True, repr=True)
    """The ID of this user."""

    app: traits.RESTAware = attr.ib(repr=False, eq=False, hash=False, metadata={attr_extensions.SKIP_DEEP_COPY: True})
    """Reference to the client application that models may use for procedures."""

    discriminator: undefined.UndefinedOr[str] = attr.ib(eq=False, hash=False, repr=True)
    """Four-digit discriminator for the user."""

    username: undefined.UndefinedOr[str] = attr.ib(eq=False, hash=False, repr=True)
    """Username of the user."""

    avatar_hash: undefined.UndefinedNoneOr[str] = attr.ib(eq=False, hash=False, repr=False)
    """Avatar hash of the user, if a custom avatar is set."""

    is_bot: undefined.UndefinedOr[bool] = attr.ib(eq=False, hash=False, repr=True)
    """Whether this user is a bot account."""

    is_system: undefined.UndefinedOr[bool] = attr.ib(eq=False, hash=False, repr=False)
    """Whether this user is a system account."""

    flags: undefined.UndefinedOr[UserFlag] = attr.ib(eq=False, hash=False)
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

    async def fetch_self(self) -> User:
        """Get this user's up-to-date object.

        Returns
        -------
        hikari.users.User
            The requested user object.

        Raises
        ------
        hikari.errors.NotFound
            If the user is not found.
        """
        return await self.app.rest.fetch_user(user=self.id)


@attr.s(eq=True, hash=True, init=True, kw_only=True, slots=True, weakref_slot=False)
class UserImpl(PartialUserImpl, User):
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


@attr.s(eq=True, hash=True, init=True, kw_only=True, slots=True, weakref_slot=False)
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
        hikari.users.OwnUser
            The requested user object.
        """
        return await self.app.rest.fetch_my_user()
