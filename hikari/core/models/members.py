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
Members that represent users and their state in specific guilds.
"""
from __future__ import annotations

import dataclasses
import datetime
import typing

from hikari.core.models import guilds
from hikari.core.models import presences
from hikari.core.models import users
from hikari.internal_utilities import auto_repr
from hikari.internal_utilities import data_structures
from hikari.internal_utilities import date_helpers
from hikari.internal_utilities import delegate
from hikari.internal_utilities import transformations


@delegate.delegate_to(users.BaseUser, "_user")
@dataclasses.dataclass()
class Member(users.BaseUser):
    """
    A specialization of a user which provides implementation details for a specific guild.

    This is a delegate type, meaning it subclasses a :class:`User` and implements it by deferring inherited calls
    and fields to a wrapped user object which is shared with the corresponding member in every guild the user is in.
    """

    __slots__ = ("_user", "_guild_id", "_role_ids", "joined_at", "nick", "premium_since", "presence")

    _user: users.User
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
        self.joined_at = date_helpers.parse_iso_8601_ts(payload.get("joined_at"))
        self.premium_since = transformations.nullable_cast(payload.get("premium_since"), date_helpers.parse_iso_8601_ts)
        self.update_state(payload.get("role_ids", data_structures.EMPTY_SEQUENCE), payload.get("nick"))

    # noinspection PyMethodOverriding
    def update_state(self, role_ids, nick) -> None:
        self._role_ids = [int(r) for r in role_ids]
        self.nick = nick

    @property
    def user(self) -> users.User:
        """The internal user object for this member. This is usually only required internally."""
        return self._user

    @property
    def guild(self) -> guilds.Guild:
        """The guild this member is in."""
        return self._state.get_guild_by_id(self._guild_id)


__all__ = ["Member"]
