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
A role within a guild.
"""
__all__ = ("Role",)

import dataclasses

from hikari import utils
from hikari.model import base
from hikari.model import color as _color
from hikari.model import permission as _permission


@dataclasses.dataclass()
class Role(base.SnowflakeMixin):
    """
    Representation of a role within a guild.
    """

    __slots__ = ("id", "name", "color", "hoist", "position", "permissions", "managed", "mentionable")

    id: int
    name: str
    color: _color.Color
    hoist: bool
    position: int
    permissions: _permission.Permission
    managed: bool
    mentionable: bool

    @staticmethod
    def from_dict(payload):
        return Role(
            id=utils.get_from_map_as(payload, "id", int),
            name=utils.get_from_map_as(payload, "name", str),
            color=utils.get_from_map_as(payload, "color", _color.Color),
            hoist=utils.get_from_map_as(payload, "hoist", bool),
            position=utils.get_from_map_as(payload, "position", int),
            permissions=utils.get_from_map_as(payload, "permissions", _permission.Permission),
            managed=utils.get_from_map_as(payload, "managed", bool),
            mentionable=utils.get_from_map_as(payload, "mentionable", bool),
        )
