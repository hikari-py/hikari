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

from hikari.core.model import base
from hikari.core.model import model_cache
from hikari.core.model import user
from hikari.core.utils import transform


@base.dataclass()
class Webhook(base.Snowflake):
    __slots__ = ("_state", "id", "_guild_id", "_channel_id", "user", "name", "avatar_hash", "token")

    _state: model_cache.AbstractModelCache
    _guild_id: int
    _channel_id: int

    #: The ID of the webhook.
    #:
    #: :type: :class:`int`
    id: int

    #: The optional user for the webhook.
    #:
    #: :type: :class:`hikari.core.model.user.User` or `None`
    user: typing.Optional[user.User]

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

    @staticmethod
    def from_dict(global_state: model_cache.AbstractModelCache, payload):
        return Webhook(
            _state=global_state,
            id=transform.get_cast(payload, "id", int),
            _guild_id=transform.get_cast(payload, "guild_id", int),
            _channel_id=transform.get_cast(payload, "channel_id", int),
            user=global_state.parse_user(payload.get("user")),
            name=payload.get("name"),
            avatar_hash=payload.get("avatar_hash"),
            token=payload.get("token"),
        )


__all__ = ["Webhook"]
