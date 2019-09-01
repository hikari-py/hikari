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
__all__ = ("Emoji",)

import typing

from hikari.core.model import base
from hikari.core.model import user
from hikari.core.model import model_cache
from hikari.core.utils import transform


@base.dataclass()
class Emoji(base.Snowflake):
    __slots__ = ("_state", "id", "name", "_role_ids", "_guild_id", "user", "require_colons", "managed", "animated")

    _state: typing.Any
    #: The id of the emoji
    id: int
    #: The name of the emoji
    name: str
    # Role ids the emoji is whitelisted to
    _role_ids: typing.List[int]
    #: The owning guild's ID.
    _guild_id: int
    #: The user whom added the emoji
    user: "user.User"
    #: Whether the emoji should be wrapped in colons or not
    require_colons: bool
    #: Whether the emoji is managed or not
    managed: bool
    #: Whether the emoji is animated or not
    animated: bool

    @staticmethod
    def from_dict(global_state: model_cache.AbstractModelCache, payload, guild_id: int):
        """Convert the given payload and state into an object instance."""
        return Emoji(
            _state=global_state,
            id=transform.get_cast(payload, "id", int),
            name=payload.get("name"),
            # Assume these were already cached...
            _role_ids=transform.get_sequence(payload, "roles", lambda r: int(r["id"])),
            _guild_id=guild_id,
            user=global_state.parse_user(payload.get("user")),
            require_colons=transform.get_cast(payload, "require_colons", bool),
            managed=transform.get_cast(payload, "managed", bool),
            animated=transform.get_cast(payload, "animated", bool),
        )
