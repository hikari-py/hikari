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
Invitations to guilds.
"""
from __future__ import annotations

import dataclasses
import datetime
import typing

from hikari.core.model import channel
from hikari.core.model import guild
from hikari.core.components import state_registry
from hikari.core.model import user
from hikari.core.utils import date_utils, auto_repr
from hikari.core.utils import transform


@dataclasses.dataclass()
class Invite:
    """
    Represents a code that when used, adds a user to a guild or group DM channel.
    """

    __slots__ = ("_state", "code", "guild", "channel", "approximate_presence_count", "approximate_member_count")

    _state: typing.Any

    #: The unique invite code
    #:
    #: :type: :class:`str`
    code: str

    #: The guild the invite is for
    #:
    #: :type: :class:`hikari.core.model.guild.Guild`
    guild: guild.Guild

    #: The channel the invite points to
    #:
    #: :type: :class:`hikari.core.model.channel.GuildChannel`
    channel: channel.GuildChannel

    #: Approximate count of online members.
    #:
    #: :type: :class:`int` or `None`
    approximate_presence_count: typing.Optional[int]

    #: Approximate count of total members.
    #:
    #: :type: :class:`int` or `None`
    approximate_member_count: typing.Optional[int]

    __repr__ = auto_repr.repr_of("code", "guild", "channel")

    def __init__(self, global_state: state_registry.StateRegistry, payload):
        self._state = global_state
        self.code = payload.get("code")
        self.guild = global_state.parse_guild(payload.get("guild"))
        # noinspection PyTypeChecker
        self.channel = global_state.parse_channel(payload.get("channel"))
        self.approximate_presence_count = transform.nullable_cast(payload.get("approximate_presence_count"), int)
        self.approximate_member_count = transform.nullable_cast(payload.get("approximate_member_count"), int)


@dataclasses.dataclass()
class InviteMetadata:
    """
    Metadata relating to a specific invite object.
    """

    __slots__ = ("_state", "inviter", "uses", "max_uses", "max_age", "temporary", "created_at", "revoked")

    _state: typing.Any

    #: The user who created the invite.
    #:
    #: :type: :class:`hikari.core.model.user.User`
    inviter: user.User

    #: The number of times the invite has been used.
    #:
    #: :type: :class:`int`
    uses: int

    #: The maximum number of times the invite may be used.
    #:
    #: :type: :class:`int`
    max_uses: int

    #: Duration after which the invite expires, in seconds.
    #:
    #: :type: :class:`int`
    max_age: int

    #: Whether or not the invite only grants temporary membership.
    #:
    #: :type: :class:`bool`
    temporary: bool

    #: When the invite was created.
    #:
    #: :type: :class:`datetime.datetime`
    created_at: datetime.datetime

    #: Whether or not the invite has been revoked.
    #:
    #: :type: :class:`bool`
    revoked: bool

    __repr__ = auto_repr.repr_of("inviter", "uses", "max_uses", "created_at")

    def __init__(self, global_state: state_registry.StateRegistry, payload):
        self._state = global_state
        self.inviter = global_state.parse_user(payload["inviter"])
        self.uses = int(payload["uses"])
        self.max_uses = int(payload["max_uses"])
        self.max_age = int(payload["max_age"])
        self.temporary = payload.get("temporary", False)
        self.created_at = date_utils.parse_iso_8601_datetime(payload["created_at"])
        self.revoked = payload.get("revoked", False)


__all__ = ["Invite", "InviteMetadata"]
