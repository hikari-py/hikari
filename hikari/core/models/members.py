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

from hikari import state_registry
from hikari.core.models import guilds
from hikari.core.models import presences
from hikari.core.models import roles as _roles
from hikari.core.models import users
from hikari.internal_utilities import auto_repr
from hikari.internal_utilities import data_structures
from hikari.internal_utilities import date_helpers
from hikari.internal_utilities import delegate
from hikari.internal_utilities import transformations


@delegate.delegate_to(users.BaseUser, "user")
@dataclasses.dataclass()
class Member(users.BaseUser):
    """
    A specialization of a user which provides implementation details for a specific guild.

    This is a delegate type, meaning it subclasses a :class:`User` and implements it by deferring inherited calls
    and fields to a wrapped user object which is shared with the corresponding member in every guild the user is in.
    """

    __slots__ = ("user", "guild", "roles", "joined_at", "nick", "premium_since", "presence")

    #: The underlying user object.
    user: users.User

    #: The guild that the member is in.
    guild: guilds.Guild

    #: The roles that the member is in.
    roles: typing.MutableSequence[_roles.Role]

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
    #: :type: :class:`hikari.core.models.presences.Presence`
    presence: presences.Presence

    __copy_by_ref__ = ("presence", "guild")

    __repr__ = auto_repr.repr_of("id", "username", "discriminator", "bot", "guild", "nick", "joined_at")

    # noinspection PyMissingConstructor
    def __init__(
        self, global_state: state_registry.StateRegistry, guild: guilds.Guild, payload: data_structures.DiscordObjectT
    ) -> None:
        self.user = global_state.parse_user(payload["user"])
        self.guild = guild
        self.joined_at = date_helpers.parse_iso_8601_ts(payload.get("joined_at"))
        self.premium_since = transformations.nullable_cast(payload.get("premium_since"), date_helpers.parse_iso_8601_ts)

        role_objs = [
            global_state.get_role_by_id(self.guild.id, int(rid))
            for rid in payload.get("role_ids", data_structures.EMPTY_SEQUENCE)
        ]

        self.update_state(role_objs, payload.get("nick"))

    # noinspection PyMethodOverriding
    def update_state(self, role_objs: typing.Sequence[_roles.Role], nick: typing.Optional[str]) -> None:
        self.roles = list(role_objs)
        self.nick = nick


__all__ = ["Member"]
