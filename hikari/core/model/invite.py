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
__all__ = ()

import enum
import typing
import datetime

from hikari.core.model import base
from hikari.core.model import guild
from hikari.core.model import channel
from hikari.core.model import user
from hikari.core.model import model_state
from hikari.core.utils import transform
from hikari.core.utils import dateutils


@base.dataclass()
class Invite:
    __slots__ = (
        "_state",
        "code",
        "guild",
        "channel",
        "target_user",
        "target_user_type",
        "approximate_presence_count",
        "approximate_member_count",
    )

    _state: typing.Any
    # The unique invite code
    code: str
    # The guild the invite is for
    guild: "guild.Guild"
    # The channel the invite points to
    channel: "channel.Channel"
    # The target user for the invite
    target_user: "user.User"
    # The type of target user for the invite
    target_user_type: int
    # Approximate count of online members
    approximate_presence_count: typing.Optional[int]
    # Approximate count of total members
    approximate_member_count: typing.Optional[int]

    @staticmethod
    def from_dict(global_state: model_state.AbstractModelState, payload):
        return Invite(
            _state=global_state,
            code=payload.get("code"),
            guild=global_state.parse_guild(payload.get("guild")),
            channel=global_state.parse_channel(payload.get("channel")),
            target_user=global_state.parse_user(payload.get("target_user")),
            target_user_type=transform.get_cast(payload, "target_user_type", int),
            approximate_presence_count=transform.get_cast(payload, "approximate_presence_count", int),
            approximate_member_count=transform.get_cast(payload, "approximate_member_count", int),
        )


class TargetUserType(enum.IntEnum):
    ...


@base.dataclass()
class InviteMetadata:
    __slots__ = ("_state", "inviter", "uses", "max_uses", "max_age", "temporary", "created_at", "revoked")

    _state: typing.Any
    # The user who created the invite
    inviter: "user.User"
    # The number of times the invite has been used
    uses: int
    # The maximum number of times the invite may be used
    max_uses: int
    # Duration after which the invite expires, in seconds
    max_age: int
    # Whether or not the invite only grants temporary membership
    temporary: bool
    # When the invite was created
    created_at: datetime.datetime
    # Whether or not the invite has been revoked
    revoked: bool

    @staticmethod
    def from_dict(global_state: model_state.AbstractModelState, payload):
        return InviteMetadata(
            _state=global_state,
            inviter=global_state.parse_user(payload.get("inviter")),
            uses=transform.get_cast(payload, "uses", int),
            max_uses=transform.get_cast(payload, "max_uses", int),
            max_age=transform.get_cast(payload, "max_age", int),
            temporary=transform.get_cast(payload, "temporary", bool),
            created_at=transform.get_cast(payload, "created_at", dateutils.parse_iso_8601_datetime),
            revoked=transform.get_cast(payload, "revoked", bool),
        )
