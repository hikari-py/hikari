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
Webhook model.
"""
__all__ = ("Webhook",)

import typing

from hikari.core.model import base
from hikari.core.model import model_cache
from hikari.core.model import user
from hikari.core.utils import transform


@base.dataclass()
class Webhook(base.SnowflakeMixin):
    __slots__ = ("_state", "id", "guild_id", "channel_id", "user", "name", "avatar_hash", "token")

    _state: typing.Any
    id: int
    guild_id: int
    channel_id: int
    user: typing.Optional["user.User"]
    name: str
    avatar_hash: typing.Optional[str]
    token: str

    @staticmethod
    def from_dict(global_state: model_cache.AbstractModelCache, payload):
        return Webhook(
            _state=global_state,
            id=transform.get_cast(payload, "id", int),
            guild_id=transform.get_cast(payload, "guild_id", int),
            channel_id=transform.get_cast(payload, "channel_id", int),
            user=global_state.parse_user(payload.get("user")),
            name=payload.get("name"),
            avatar_hash=payload.get("avatar_hash"),
            token=payload.get("token"),
        )
