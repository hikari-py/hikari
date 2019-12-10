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
"""
Generic users not bound to a guild, and guild-bound member definitions.
"""
from __future__ import annotations

import enum
import typing

from hikari.internal_utilities import auto_repr
from hikari.internal_utilities import data_structures
from hikari.internal_utilities import transformations
from hikari.orm import fabric
from hikari.orm.models import interfaces


class IUser(interfaces.IStatefulModel, interfaces.ISnowflake, interface=True):
    """
    Interface that any type of user account should provide. This is used by
    implementations of object such as those provided by delegates
    (:class:`hikari.orm.models.members.Member`, etc).
    """

    __slots__ = ()

    #: ID of the user.
    #:
    #: :type: :class:`int`
    id: int

    #: The user name.
    #:
    #: :type: :class:`str`
    username: str

    #: The 4-digit discriminator of the object.
    #:
    #: :type: :class:`int`
    discriminator: int

    #: The hash of the user's avatar, or None if they do not have one.
    #:
    #: :type: :class:`str`
    avatar_hash: str

    #: True if the user is a bot, False otherwise
    #:
    #: :type: :class:`bool`
    is_bot: bool

    #: If this is an Official Discord System user (urgent message system).
    #:
    #: :type: :class:`bool`
    is_system: bool

    __repr__ = auto_repr.repr_of("id", "username", "discriminator", "is_bot")


class User(IUser):
    """
    Implementation of the user data type.
    """

    __slots__ = ("_fabric", "id", "username", "discriminator", "avatar_hash", "is_bot", "is_system", "__weakref__")

    # noinspection PyMissingConstructor
    def __init__(self, fabric_obj: fabric.Fabric, payload: data_structures.DiscordObjectT):
        self._fabric = fabric_obj
        self.id = int(payload["id"])
        # We don't expect these to ever change...
        self.is_bot = payload.get("bot", False)
        self.is_system = payload.get("system", False)
        self.update_state(payload)

    def update_state(self, payload: data_structures.DiscordObjectT) -> None:
        self.username = payload.get("username")
        self.discriminator = int(payload["discriminator"])
        self.avatar_hash = payload.get("avatar")


class UserFlag(enum.IntFlag):
    """
    OAuth2-specified user flags. These can be used to find out the badges that a user has on their
    profile, et cetera.
    """

    NONE = 0
    DISCORD_EMPLOYEE = 1 << 0
    DISCORD_PARTNER = 1 << 1
    HYPESQUAD_EVENTS = 1 << 2
    BUG_HUNTER = 1 << 3
    HYPESQUAD_HOUSE_BRAVERY = 1 << 6
    HYPESQUAD_HOUSE_BRILLIANCE = 1 << 7
    HYPESQUAD_HOUSE_BALANCE = 1 << 8
    EARLY_SUPPORTER = 1 << 9
    TEAM_USER = 1 << 10
    System = 1 << 12


class PremiumType(enum.IntEnum):
    #: No premium account.
    NONE = 0
    #: Includes app perks like animated emojis and avatars, but not games or server boosting.
    NITRO_CLASSIC = 1
    #: Includes app perks as well as the games subscription service and server boosting.
    NITRO = 2


class Locale:
    """
    A representation of a locale. This is created by parsing a locale alias.
    """


class OAuth2User(User):
    """
    An extension of a regular user that provides additional OAuth2-scoped information.
    """

    __slots__ = ("is_mfa_enabled", "locale", "is_verified", "email", "flags", "premium_type")

    #: True if the user has multi-factor-authentication enabled.
    #:
    #: Requires the `identify` OAuth2 scope.
    #:
    #: :type: :class:`bool` or `None` if not available.
    is_mfa_enabled: typing.Optional[bool]

    #: The user's chosen language option.
    #:
    #: Requires the `identify` OAuth2 scope.
    #:
    #: :type: :class:`str` or `None` if not available.
    #:
    #: Note:
    #:     If you wish to obtain further information about a locale, and what it provides, you
    #:     should consider using the `babel <http://babel.pocoo.org/>`_ library. This will enable
    #:     you to cater content output formats to specific locales and languages easily.
    #:
    #:     A brief example of that usage would be as follows:
    #:
    #:     .. code-block:: python
    #:
    #:        >>> import babel
    #:        >>>
    #:        >>> locale_string = some_oauth2_user.locale
    #:        >>> # Note the second parameter for the separator!
    #:        >>> locale = babel.core.Locale.parse(locale_string, "-")
    #:        >>>
    #:        >>> # Get the name of the 4th day of the week for that locale
    #:        >>> locale.days['format']['wide'][3]
    #:        "Donnerstag"
    #:        >>> # Get the standard locale currency format
    #:        >>> locale.currency_formats['standard']
    #:        <NumberPattern '#,##0.00\xa0¤'>
    locale: typing.Optional[str]

    #: True if the user has verified their email address.
    #:
    #: Requires the `email` OAuth2 scope.
    #:
    #: :type: :class:`bool` or `None` if not available.
    is_verified: typing.Optional[bool]

    #: The user's email address.
    #:
    #: Requires the `email` OAuth2 scope.
    #:
    #: :type: :class:`str` or `None` if not available`
    email: typing.Optional[str]

    #: The flags on a user's account. Describes the type of badges the user will have on their
    #: profile, amongst other things.
    #:
    #: Requires the `identify` OAuth2 scope.
    #:
    #: :type: :class:`UserFlag` or `None` if not available.
    flags: typing.Optional[UserFlag]

    #: The type of Nitro subscription that the user has.
    #:
    #: Requires the `identify` OAuth2 scope.
    #:
    #: :type: :class:`PremiumType` or `None` if not available.
    premium_type: typing.Optional[PremiumType]

    __repr__ = auto_repr.repr_of("id", "username", "discriminator", "is_bot", "is_verified", "is_mfa_enabled")

    def __init__(self, fabric_obj: fabric.Fabric, payload: data_structures.DiscordObjectT):
        super().__init__(fabric_obj, payload)

    def update_state(self, payload: data_structures.DiscordObjectT) -> None:
        super().update_state(payload)

        self.is_mfa_enabled = payload.get("mfa_enabled")
        self.locale = payload.get("locale")
        self.is_verified = payload.get("verified")
        self.email = payload.get("email")
        self.flags = transformations.nullable_cast(payload.get("flags"), UserFlag)
        self.premium_type = transformations.nullable_cast(payload.get("premium_type"), PremiumType)


def parse_user(fabric_obj: fabric.Fabric, payload: data_structures.DiscordObjectT) -> typing.Union[OAuth2User, User]:
    return (
        OAuth2User(fabric_obj, payload)
        if any(field in OAuth2User.__slots__ for field in payload)
        else User(fabric_obj, payload)
    )


__all__ = ["IUser", "User", "UserFlag", "PremiumType", "OAuth2User"]
