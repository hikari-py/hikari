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
from __future__ import annotations

import dataclasses
import typing

from hikari.core.model import base
from hikari.core.model import model_cache
from hikari.core.model import user
from hikari.core.utils import transform


@dataclasses.dataclass()
class Emoji(base.Snowflake):
    """
    Representation of a custom emoji object.
    """

    __slots__ = ("_state", "id", "name", "_role_ids", "_guild_id", "user", "require_colons", "managed", "animated")

    _state: typing.Any
    _role_ids: typing.List[int]
    _guild_id: int

    #: The id of the emoji
    #:
    #: :type: :class:`int`
    id: int

    #: The name of the emoji
    #:
    #: :type: :class:`str`
    name: str

    #: The user whom added the emoji
    #:
    #: :type: :class:`hikari.core.models.user.User`
    user: user.User

    #: Whether the emoji should be wrapped in colons or not
    #:
    #: :type: :class:`bool`
    require_colons: bool

    #: Whether the emoji is managed or not as part of some integration, such as Twitch.
    #:
    #: :type: :class:`bool`
    managed: bool

    #: Whether the emoji is animated or not
    #:
    #: :type: :class:`bool`
    animated: bool

    def __init__(self, global_state: model_cache.AbstractModelCache, payload, guild_id: int):
        """Convert the given payload and state into an object instance."""
        self._state = global_state
        self.id = int(payload["id"])
        self.name = payload["name"]
        self._role_ids = [global_state.parse_role(role).id for role in payload.get("roles", ())]
        self._guild_id = guild_id
        user = payload.get("user")
        self.user = global_state.parse_user(user) if user is not None else None
        self.require_colons = payload.get("require_colons", False)
        self.managed = payload.get("managed", False)
        self.animated = payload.get("animated", False)


__all__ = ["Emoji"]
