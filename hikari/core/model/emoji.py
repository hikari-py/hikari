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
Emojis.
"""
__all__ = ()

import typing

from hikari.core.model import base
from hikari.core.model import user
from hikari.core.model import role
from hikari.core.model import model_state
from hikari.core.utils import transform


class PartialEmoji:
    __slots__ = ()


@base.dataclass()
class Emoji:
    __slots__ = (
        "_state",
        "id", 
        "name", 
        "_roles", 
        "user", 
        "require_colons", 
        "managed", 
        "animated"
    )

    _state: typing.Any
    # The id of the emoji
    id: int
    # The name of the emoji
    name: str
    # Role ids the emoji is whitelisted to
    _roles: typing.List[int]
    # The user whom added the emoji
    user: "user.User"
    # Whether the emoji should be wrapped in colons or not
    require_colons: bool
    # Whether the emoji is managed or not
    managed: bool
    # Whether the emoji is animated or not
    animated: bool

    @staticmethod
    def from_dict(global_state: model_state.AbstractModelState, payload):
        """Convert the given payload and state into an object instance."""
        return Emoji(
            _state=global_state,
            id=transform.get_cast(payload, "id", int),
            name=payload.get("name"),
            _roles=transform.get_sequence(payload, "roles", role.Role),
            user=global_state.parse_user(payload.get("user")),
            require_colons=transform.get_cast(payload, "require_colons", bool),
            managed=transform.get_cast(payload, "managed", bool),
            animated=transform.get_cast(payload, "animated", bool)
        )

