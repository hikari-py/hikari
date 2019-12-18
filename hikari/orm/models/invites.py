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
Invitations to guilds.
"""
from __future__ import annotations

import datetime
import enum
import typing

from hikari.internal_utilities import auto_repr
from hikari.internal_utilities import data_structures
from hikari.internal_utilities import date_helpers
from hikari.internal_utilities import transformations
from hikari.orm import fabric
from hikari.orm import state_registry
from hikari.orm.models import channels
from hikari.orm.models import guilds
from hikari.orm.models import interfaces
from hikari.orm.models import users


class InviteTargetUserType(enum.IntEnum):
    """
    Why an invite targets a user.
    """

    #: Targeting a Go Live stream.
    STREAM = 1


class Invite(interfaces.IModel):
    """
    Represents a code that when used, adds a user to a guild or group DM channel.
    """

    __slots__ = (
        "code",
        "guild",
        "channel",
        "target_user",
        "target_user_type",
        "approximate_presence_count",
        "approximate_member_count",
    )

    #: The unique invite code
    #:
    #: :type: :class:`str`
    code: str

    #: The guild the invite is for
    #:
    #: :type: :class:`hikari.orm.models.guilds.PartialGuild`
    guild: guilds.PartialGuild

    #: The channel the invite points to
    #:
    #: :type: :class:`hikari.orm.models.channels.PartialChannel`
    channel: channels.PartialChannel

    #: The user this invite is targeting.
    #:
    #: :type: :class:`hikari.orm.models.users.IUser` or `None`
    target_user: typing.Optional[users.IUser]

    #: The reason this invite targets a user
    #:
    #: :type: :class:`hikari.orm.models.invites.InviteTargetUserType` or `None`
    target_user_type: typing.Optional[InviteTargetUserType]

    #: Approximate count of online members.
    #:
    #: :type: :class:`int` or `None`
    approximate_presence_count: typing.Optional[int]

    #: Approximate count of total members.
    #:
    #: :type: :class:`int` or `None`
    approximate_member_count: typing.Optional[int]

    __repr__ = auto_repr.repr_of("code", "guild", "channel")

    def __init__(self, fabric_obj: fabric.Fabric, payload: data_structures.DiscordObjectT) -> None:
        self.code = payload["code"]
        self.guild = transformations.nullable_cast(payload.get("guild"), guilds.PartialGuild)
        self.channel = channels.PartialChannel(fabric_obj, payload["channel"])
        self.target_user = transformations.nullable_cast(
            payload.get("target_user"), fabric_obj.state_registry.parse_user
        )
        self.target_user_type = transformations.nullable_cast(payload.get("target_user_type"), InviteTargetUserType)
        self.approximate_presence_count = payload.get("approximate_presence_count")
        self.approximate_member_count = payload.get("approximate_member_count")

    def __str__(self):
        return self.code


class InviteMetadata(interfaces.IModel):
    """
    Metadata relating to a specific invite object.
    """

    __slots__ = ("inviter", "uses", "max_uses", "max_age", "is_temporary", "created_at", "is_revoked")

    _state: state_registry.IStateRegistry

    #: The user who created the invite.
    #:
    #: :type: :class:`hikari.orm.models.users.User`
    inviter: users.User

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
    is_temporary: bool

    #: When the invite was created.
    #:
    #: :type: :class:`datetime.datetime`
    created_at: datetime.datetime

    #: Whether or not the invite has been revoked.
    #:
    #: :type: :class:`bool`
    is_revoked: bool

    __repr__ = auto_repr.repr_of("inviter", "uses", "max_uses", "created_at")

    def __init__(self, fabric_obj: fabric.Fabric, payload: data_structures.DiscordObjectT) -> None:
        self.inviter = fabric_obj.state_registry.parse_user(payload["inviter"])
        self.uses = int(payload["uses"])
        self.max_uses = int(payload["max_uses"])
        self.max_age = int(payload["max_age"])
        self.is_temporary = payload.get("temporary", False)
        self.created_at = date_helpers.parse_iso_8601_ts(payload["created_at"])
        self.is_revoked = payload.get("revoked", False)


#: An :class:`Invite` or the :class:`str` code of an invite object.
InviteLikeT = typing.Union[str, Invite]


__all__ = ["Invite", "InviteMetadata", "InviteTargetUserType", "InviteLikeT"]
