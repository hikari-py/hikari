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
Models for the Teams API for OAuth2 applications.
"""
from __future__ import annotations

import enum
import typing

from hikari.internal_utilities import data_structures
from hikari.internal_utilities import delegate
from hikari.internal_utilities import transformations
from hikari.orm import fabric

from hikari.orm.models import interfaces
from hikari.orm.models import users


class Team(interfaces.IStatefulModel, interfaces.ISnowflake):
    """
    A representation of a team that can contain one or more members in a managed application.
    """
    __slots__ = ("_fabric", "id", "icon", "members", "owner_user_id")

    #: The ID of the team.
    #:
    #: :type: :class:`int`
    id: int

    #: The optional hashcode of the icon for the team.
    #:
    #: :type: :class:`str` or `None`
    icon: typing.Optional[str]

    #: The members in the team.
    #:
    #: :type: :class:`typing.Mapping` of :class:`int` IDs to :class:`TeamMember`
    members: typing.Mapping[int, TeamMember]

    #: The ID of the owner of the team.
    #:
    #: :type: :class:`int`
    owner_user_id: int

    def __init__(self, fabric_obj: fabric.Fabric, payload: data_structures.DiscordObjectT) -> None:
        self._fabric = fabric_obj
        self.id = int(payload["id"])
        self.icon = payload.get("icon")
        self.members = transformations.id_map(TeamMember(fabric_obj, member) for member in payload["members"])
        self.owner_user_id = int(payload["owner_user_id"])


@delegate.delegate_to(users.IUser, "user")
class TeamMember(users.IUser, delegate_fabricated=True):
    """
    A representation of a team member.
    """
    __slots__ = ("team_id", "permissions", "membership_state", "user")

    #: The ID of the team the member is in.
    #:
    #: :type: :class:`int`.
    team_id: int

    #: The permissions the member has.
    #:
    #: This is always a `*` currently.
    #:
    #: :type: :class:`typing.Set` of :class:`str`
    permissions: typing.Set[str]

    #: The state of membership for the user.
    #:
    #: :type: :class:`MembershipState`
    membership_state: MembershipState

    #: The underlying user.
    #:
    #: :type: :class:`IUser`
    user: users.IUser

    def __init__(self, fabric_obj: fabric.Fabric, payload: data_structures.DiscordObjectT) -> None:
        self.team_id = int(payload["team_id"])
        self.permissions = set(payload["permissions"])
        self.membership_state = MembershipState(payload["membership_state"])
        self.user = fabric_obj.state_registry.parse_user(payload["user"])


class MembershipState(enum.IntEnum):
    """
    The state of membership for a team member.
    """
    #: The user has been invited but has not yet responded.
    INVITED = 1
    #: The user has accepted an invite and is a team member officially.
    ACCEPTED = 2


__all__ = ["MembershipState", "TeamMember", "Team"]
