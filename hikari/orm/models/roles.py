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
A role within a guild.
"""
from __future__ import annotations

import typing

from hikari.internal_utilities import containers
from hikari.internal_utilities import reprs
from hikari.orm import fabric
from hikari.orm.models import bases
from hikari.orm.models import colors as _color
from hikari.orm.models import permissions as _permission


class PartialRole(bases.BaseModel, bases.SnowflakeMixin):
    """
    A partial role object where we only know the ID and name. These are usually
    only seen attached to the changes of an audit log entry.
    """

    __slots__ = ("id", "name")

    #: The ID of the role.
    #:
    #: :type: :class:`int`
    id: int

    #: The name of the role.
    #:
    #: :type: :class:`str`
    name: str

    __repr__ = reprs.repr_of("id", "name")

    def __init__(self, payload: containers.DiscordObjectT) -> None:
        self.id = int(payload["id"])
        self.name = payload["name"]


class Role(PartialRole, bases.BaseModelWithFabric):
    """
    Representation of a role within a guild.
    """

    __slots__ = (
        "_fabric",
        "guild_id",
        "color",
        "is_hoisted",
        "position",
        "permissions",
        "is_managed",
        "is_mentionable",
        "__weakref__",
    )

    #: The guild that the role is in.
    #:
    #: :type: :class:`int`
    guild_id: int

    #: The color of the role.
    #:
    #: :type: :class:`hikari.orm.models.colors.Color`
    color: _color.Color

    #: Whether the role will be hoisted (show as a separate list in the member list)
    #:
    #: :type: :class:`bool`
    is_hoisted: bool

    #: The position of the role.
    #:
    #: :type: :class:`int`
    position: int

    #: The permissions for the role.
    #:
    #: :type: :class:`hikari.orm.models.permissions.Permission`
    permissions: _permission.Permission

    #: True if the role is created by an integration or by adding a bot to the server, or False otherwise.
    #:
    #: :type: :class:`bool`
    is_managed: bool

    #: True if you can mention this role and thus ping all members in that role at once, False if you can not.
    #:
    #: :type: :class:`bool`
    is_mentionable: bool

    __repr__ = reprs.repr_of("id", "name", "position", "is_managed", "is_mentionable", "is_hoisted")

    def __init__(self, fabric_obj: fabric.Fabric, payload: containers.DiscordObjectT, guild_id: int) -> None:
        super().__init__(payload)
        self._fabric = fabric_obj
        self.guild_id = guild_id
        self.update_state(payload)

    def update_state(self, payload: containers.DiscordObjectT) -> None:
        self.name = payload["name"]
        self.color = _color.Color(payload["color"])
        self.is_hoisted = payload["hoist"]
        self.position = payload["position"]
        self.permissions = _permission.Permission(payload["permissions"])
        self.is_managed = payload["managed"]
        self.is_mentionable = payload["mentionable"]


#: Any type of :class:`PartialRole` (including :class:`Role`), or the :class:`int`/:class:`str` ID of one.
PartialRoleLikeT = typing.Union[bases.RawSnowflakeT, PartialRole]


#: An instance of :class:`Role`, or the :class:`int`/:class:`str` ID of one.
RoleLikeT = typing.Union[bases.RawSnowflakeT, PartialRole]


__all__ = ["PartialRole", "Role", "PartialRoleLikeT", "RoleLikeT"]
