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

from hikari.internal_utilities import assertions
from hikari.internal_utilities import containers
from hikari.internal_utilities import dates
from hikari.internal_utilities import delegate
from hikari.internal_utilities import reprs
from hikari.internal_utilities import transformations
from hikari.orm import fabric
from hikari.orm.models import bases
from hikari.orm.models import guilds
from hikari.orm.models import presences
from hikari.orm.models import roles as _roles
from hikari.orm.models import users


@delegate.delegate_to(users.User, "user")
class Member(users.User, delegate_fabricated=True):
    """
    A specialization of a user which provides implementation details for a specific guild.

    This is a delegate type, meaning it subclasses a :class:`User` and implements it by deferring inherited calls
    and fields to a wrapped user object which is shared with the corresponding member in every guild the user is in.
    """

    __slots__ = ("user", "guild", "roles", "joined_at", "nick", "premium_since", "presence", "is_deaf", "is_mute")

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

    #: Whether the user is deafened in voice.
    #:
    #: :type: :class:`bool`
    is_deaf: bool

    #: Whether the user is muted in voice.
    #:
    #: :type: :class:`bool`
    is_mute: bool

    #: The user's online presence. This will be `None` until populated by a gateway event.
    #:
    #: :type: :class:`hikari.orm.models.presences.Presence` or :class:`None`
    presence: typing.Optional[presences.Presence]

    __copy_by_ref__ = ("presence", "guild")

    __repr__ = reprs.repr_of("id", "username", "discriminator", "is_bot", "guild.id", "guild.name", "nick", "joined_at")

    # noinspection PyMissingConstructor
    def __init__(self, fabric_obj: fabric.Fabric, guild: guilds.Guild, payload: containers.DiscordObjectT) -> None:
        self.presence = None
        self.user = fabric_obj.state_registry.parse_user(payload["user"])
        self.guild = guild
        self.joined_at = dates.parse_iso_8601_ts(payload["joined_at"])

        role_objs = [
            fabric_obj.state_registry.get_role_by_id(self.guild.id, int(rid))
            for rid in payload.get("role_ids", containers.EMPTY_SEQUENCE)
        ]

        self.update_state(role_objs, payload)

    # noinspection PyMethodOverriding
    def update_state(self, role_objs: typing.Sequence[_roles.Role], payload: containers.DiscordObjectT) -> None:
        self.roles = list(role_objs)
        self.premium_since = transformations.nullable_cast(payload.get("premium_since"), dates.parse_iso_8601_ts)
        self.nick = payload.get("nick")
        self.is_deaf = payload.get("deaf", False)
        self.is_mute = payload.get("mute", False)

    def update_presence_state(self, presence_payload: containers.DiscordObjectT = None) -> None:
        user_id = presence_payload["user"]["id"]
        assertions.assert_that(
            int(user_id) == self.id, f"Presence object from User `{user_id}` doesn't match Member `{self.id}`."
        )
        self.presence = self._fabric.state_registry.parse_presence(self, presence_payload)


#: A :class:`Member`, or an :class:`int`/:class:`str` ID of one.
MemberLikeT = typing.Union[bases.RawSnowflakeT, Member]


__all__ = ["Member"]
