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
Webhooks.
"""
from __future__ import annotations

import typing

from hikari import state_registry
from hikari.core.models import base
from hikari.core.models import users
from hikari.internal_utilities import auto_repr


class Webhook(base.HikariModel, base.Snowflake):
    __slots__ = ("_state", "id", "_guild_id", "_channel_id", "user", "name", "avatar_hash", "token")
    __copy_by_ref__ = ("user",)

    _state: state_registry.StateRegistry
    _guild_id: int
    _channel_id: int

    #: The ID of the webhook.
    #:
    #: :type: :class:`int`
    id: int

    #: The optional user for the webhook.
    #:
    #: :type: :class:`hikari.core.models.users.User` or `None`
    user: typing.Optional[users.User]

    #: The name of the webhook.
    #:
    #: :type: :class:`str`
    name: str

    #: The name of the webhook.
    #:
    #: :type: :class:`str` or `None`
    avatar_hash: typing.Optional[str]

    #: The token of the webhook, if available.
    #:
    #: :type: :class:`str` or `None`
    token: typing.Optional[str]

    __repr__ = auto_repr.repr_of("id", "name")

    def __init__(self, global_state: state_registry.StateRegistry, payload):
        self._state = global_state
        self.id = int(payload["id"])
        self._guild_id = int(payload["guild_id"])
        self._channel_id = int(payload["channel_id"])
        self.user = global_state.parse_user(payload.get("user"))
        self.name = payload.get("name")
        self.avatar_hash = payload.get("avatar_hash")
        self.token = payload.get("token")


__all__ = ["Webhook"]
