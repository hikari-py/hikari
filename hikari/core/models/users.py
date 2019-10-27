#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019
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

import dataclasses
import datetime
import typing

from hikari.core.internal import state_registry
from hikari.core.models import base
from hikari.core.models import presences
from hikari.core.utils import date_utils, auto_repr, custom_types
from hikari.core.utils import delegate
from hikari.core.utils import transform


@dataclasses.dataclass()
class User(base.HikariModel, base.Snowflake):
    """
    Representation of a user account.
    """

    __slots__ = ("_state", "id", "username", "discriminator", "avatar_hash", "bot", "__weakref__")

    _state: state_registry.StateRegistry

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
    bot: bool

    __repr__ = auto_repr.repr_of("id", "username", "discriminator", "bot")

    def __init__(self, global_state: state_registry.StateRegistry, payload):
        self._state = global_state
        self.id = int(payload["id"])
        # We don't expect this to ever change...
        self.bot = payload.get("bot", False)
        self.update_state(payload)

    def update_state(self, payload) -> None:
        self.username = payload.get("username")
        self.discriminator = int(payload["discriminator"])
        self.avatar_hash = payload.get("avatar")


@delegate.delegate_to(User, "_user")
@dataclasses.dataclass()
class Member(User):
    """
    A specialization of a user which provides implementation details for a specific guild.

    This is a delegate type, meaning it subclasses a :class:`User` and implements it by deferring inherited calls
    and fields to a wrapped user object which is shared with the corresponding member in every guild the user is in.
    """

    __slots__ = ("_user", "_guild_id", "_role_ids", "joined_at", "nick", "premium_since", "presence")

    _user: User
    _role_ids: typing.MutableSequence[int]
    _guild_id: int

    #: The date and time the member joined this guild.
    #:
    #: :type: :class:`datetime.datetime`
    joined_at: datetime.datetime

    #: The optional nickname of the member.
    #:
    #: :type: :class:`str` or `None`
    nick: typing.Optional[str]

    #: The optional date/time that the member Nitro-boosted the guild.
    #:
    #: :type: :class:`datetime.datetime` or `None`
    premium_since: typing.Optional[datetime.datetime]

    #: The user's online presence.
    #:
    #: :type: :class:`hikari.core.models.presence.Presence`
    presence: presences.Presence

    __copy_by_ref__ = ("presence",)

    __repr__ = auto_repr.repr_of("id", "username", "discriminator", "bot", "guild", "nick", "joined_at")

    # noinspection PyMissingConstructor
    def __init__(self, global_state, guild_id, payload):
        self._user = global_state.parse_user(payload["user"])
        self._guild_id = guild_id
        self.joined_at = date_utils.parse_iso_8601_ts(payload.get("joined_at"))
        self.premium_since = transform.nullable_cast(payload.get("premium_since"), date_utils.parse_iso_8601_ts)
        self.update_state(payload.get("role_ids", custom_types.EMPTY_SEQUENCE), payload.get("nick"))

    # noinspection PyMethodOverriding
    def update_state(self, role_ids, nick) -> None:
        self._role_ids = [int(r) for r in role_ids]
        self.nick = nick

    @property
    def user(self):
        """Returns the internal user object for this member. This is usually only used internally."""
        return self._user


@dataclasses.dataclass()
class BotUser(User):
    """
    A special instance of user to represent the bot that is signed in.
    """

    __slots__ = ("verified", "mfa_enabled")

    #: Whether the account is verified or not.
    #:
    #: :type: :class:`bool`
    verified: bool

    #: Whether MFA is enabled or not.
    #:
    #: :type: :class:`bool`
    mfa_enabled: bool

    __repr__ = auto_repr.repr_of("id", "username", "discriminator", "bot", "verified", "mfa_enabled")

    def __init__(self, global_state: state_registry.StateRegistry, payload):
        super().__init__(global_state, payload)

    def update_state(self, payload) -> None:
        super().update_state(payload)
        self.verified = payload.get("verified", False)
        self.mfa_enabled = payload.get("mfa_enabled", False)


__all__ = ["User", "Member", "BotUser"]
