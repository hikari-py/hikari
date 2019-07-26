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
__all__ = ("User", "Member")

import dataclasses
import datetime
import typing

from hikari.model import base
from hikari.model import guild as _guild
from hikari.utils import dateutils, delegate, maps


@dataclasses.dataclass()
class User(base.SnowflakeMixin):
    """
    Representation of a user account.
    """

    # TODO: user flags (eventually)
    __slots__ = ("id", "username", "discriminator", "avatar_hash", "bot")

    id: int
    username: str
    discriminator: int
    avatar_hash: str
    bot: bool

    @staticmethod
    def from_dict(payload):
        return User(
            id=int(payload["id"]),
            username=payload["username"],
            discriminator=int(payload["discriminator"]),
            avatar_hash=payload["avatar"],
            bot=payload.get("bot", False),
        )


@delegate.delegate_members(User, "_user")
@delegate.delegate_safe_dataclass()
class Member(User):
    """
    A specialization of a user which provides implementation details for a specific guild.

    This is a delegate type, meaning it subclasses a :class:`User` and implements it by deferring inherited calls
    and fields to a wrapped user object which is shared with the corresponding member in every guild the user is in.
    """

    # TODO: voice
    # TODO: statuses from gateway (eventually)
    __slots__ = ("_user", "guild", "_roles", "joined_at", "nick", "nitro_boosted_at")

    _user: User
    _roles: typing.List[int]
    guild: _guild.Guild
    joined_at: datetime.datetime
    nick: typing.Optional[str]
    nitro_boosted_at: typing.Optional[datetime.datetime]

    @staticmethod
    def from_dict(payload, user, guild):
        return Member(
            _user=user,
            _roles=[int(r) for r in payload["roles"]],
            nick=payload.get("nick"),
            guild=guild,
            joined_at=dateutils.parse_iso_8601_datetime(payload["joined_at"]),
            nitro_boosted_at=maps.get_from_map_as(payload, "premium_since", dateutils.parse_iso_8601_datetime),
        )
