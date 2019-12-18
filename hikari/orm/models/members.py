#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekokatt 2019-2020
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

import datetime
import typing

from hikari.internal_utilities import auto_repr
from hikari.internal_utilities import data_structures
from hikari.internal_utilities import date_helpers
from hikari.internal_utilities import delegate
from hikari.internal_utilities import transformations
from hikari.orm import fabric
from hikari.orm.models import guilds
from hikari.orm.models import interfaces
from hikari.orm.models import presences
from hikari.orm.models import roles as _roles
from hikari.orm.models import users


@delegate.delegate_to(users.IUser, "user")
class Member(users.IUser, delegate_fabricated=True):
    """
    A specialization of a user which provides implementation details for a specific guild.

    This is a delegate type, meaning it subclasses a :class:`User` and implements it by deferring inherited calls
    and fields to a wrapped user object which is shared with the corresponding member in every guild the user is in.
    """

    __slots__ = ("user", "guild", "roles", "joined_at", "nick", "premium_since", "presence", "is_deaf", "is_mute")

    #: The underlying user object.
    user: users.IUser

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

    #: Whether the user is deafened in voice.
    #:
    #: :type: :class:`bool`
    is_deaf: bool

    #: Whether the user is muted in voice.
    #:
    #: :type: :class:`bool`
    is_mute: bool

    #: The user's online presence.
    #:
    #: :type: :class:`hikari.orm.models.presences.Presence`
    presence: presences.Presence

    __copy_by_ref__ = ("presence", "guild")

    __repr__ = auto_repr.repr_of("id", "username", "discriminator", "is_bot", "guild", "nick", "joined_at")

    # noinspection PyMissingConstructor
    def __init__(self, fabric_obj: fabric.Fabric, guild: guilds.Guild, payload: data_structures.DiscordObjectT) -> None:
        self.user = fabric_obj.state_registry.parse_user(payload["user"])
        self.guild = guild
        self.joined_at = date_helpers.parse_iso_8601_ts(payload.get("joined_at"))

        role_objs = [
            fabric_obj.state_registry.get_role_by_id(self.guild.id, int(rid))
            for rid in payload.get("role_ids", data_structures.EMPTY_SEQUENCE)
        ]

        self.update_state(role_objs, payload)

    # noinspection PyMethodOverriding
    def update_state(self, role_objs: typing.Sequence[_roles.Role], payload: data_structures.DiscordObjectT) -> None:
        self.roles = list(role_objs)
        self.premium_since = transformations.nullable_cast(payload.get("premium_since"), date_helpers.parse_iso_8601_ts)
        self.nick = payload.get("nick")
        self.is_deaf = payload.get("deaf", False)
        self.is_mute = payload.get("mute", False)


#: A :class:`Member`, or an :class:`int`/:class:`str` ID of one.
MemberLikeT = typing.Union[interfaces.RawSnowflakeT, Member]


__all__ = ["Member"]
