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

import datetime
import typing

from hikari.core.model import state
from hikari.core.model import base
from hikari.core.model import guild as _guild
from hikari.core.utils import dateutils, transform
from hikari.core.utils import delegate


@base.dataclass()
class User(base.SnowflakeMixin):
    """
    Representation of a user account.
    """

    # TODO: user flags (eventually)
    __slots__ = ("_state", "id", "username", "discriminator", "avatar_hash", "bot")

    _state: state.AbstractState
    #: ID of the user.
    id: int
    #: The user name.
    username: str
    #: The 4-digit discriminator of the object.
    discriminator: int
    #: The hash of the user's avatar, or None if they do not have one.
    avatar_hash: str
    #: True if the user is a bot, False otherwise
    bot: bool

    @staticmethod
    def from_dict(global_state: state.AbstractState, payload):
        return User(
            _state=global_state,
            id=transform.get_cast(payload, "id", int),
            username=payload.get("username"),
            discriminator=transform.get_cast(payload, "discriminator", int),
            avatar_hash=payload.get("avatar"),
            bot=payload.get("bot", False),
        )


@delegate.delegate_members(User, "_user")
@delegate.delegate_safe_dataclass(base.dataclass)
class Member(User):
    """
    A specialization of a user which provides implementation details for a specific guild.

    This is a delegate type, meaning it subclasses a :class:`User` and implements it by deferring inherited calls
    and fields to a wrapped user object which is shared with the corresponding member in every guild the user is in.
    """

    # TODO: voice
    # TODO: statuses from gateway (eventually)
    __slots__ = ("_user", "_guild_id", "_role_ids", "joined_at", "nick", "premium_since")

    #: The underlying user for this member.
    _user: User
    #: The list of role IDs this member has.
    _role_ids: typing.List[int]
    #: The guild this member is in.
    _guild_id: _guild.Guild
    #: The date and time the member joined this guild.
    joined_at: datetime.datetime
    #: The optional nickname of the member.
    nick: typing.Optional[str]
    #: The optional date/time that the member Nitro-boosted the guild.
    premium_since: typing.Optional[datetime.datetime]

    # noinspection PyMethodOverriding
    @staticmethod
    def from_dict(global_state, guild_id, payload):
        return Member(
            _user=global_state.parse_user(payload.get("user")),
            _role_ids=transform.get_sequence(payload, "roles", int),
            _guild_id=guild_id,
            nick=payload.get("nick"),
            joined_at=transform.get_cast(payload, "joined_at", dateutils.parse_iso_8601_datetime),
            premium_since=transform.get_cast(payload, "premium_since", dateutils.parse_iso_8601_datetime),
        )
