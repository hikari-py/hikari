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

import enum
import typing

from hikari.internal_utilities import auto_repr
from hikari.internal_utilities import transformations
from hikari.orm.models import interfaces
from hikari.orm.models import users


class WebhookType(enum.IntEnum):
    """
    The type of a webhook.
    """

    # Incoming webhooks that can be posted using Discord's token endpoint.
    INCOMING = 1
    # Channel follows webhooks that are posted to by discord announcement channels.
    CHANNEL_FOLLOWER = 2


class Webhook(interfaces.FabricatedMixin, interfaces.ISnowflake):
    """
    Describes a webhook. This is an HTTP endpoint that can be used to send messages to certain
    channels without spinning up a complete bot implementation elsewhere (such as for CI pipelines).
    """

    __slots__ = ("_fabric", "id", "type", "guild_id", "channel_id", "user", "name", "avatar_hash", "token")
    __copy_by_ref__ = ("user",)

    #: The ID of the guild that the webhook is in.
    guild_id: int

    #: The ID of the channel that the webhook is in.
    channel_id: int

    #: The ID of the webhook.
    #:
    #: :type: :class:`int`
    id: int

    #: The type of the webhook.
    #:
    #: :type:  :class:`hikari.orm.models.webhooks.WebhookType`
    type: WebhookType

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

    def __init__(self, fabric_obj, payload):
        self._fabric = fabric_obj
        self.id = int(payload["id"])
        self.type = transformations.try_cast(payload.get("type"), WebhookType)
        self.guild_id = int(payload["guild_id"])
        self.channel_id = int(payload["channel_id"])
        self.user = fabric_obj.state_registry.parse_user(payload.get("user"))
        self.name = payload.get("name")
        self.avatar_hash = payload.get("avatar_hash")
        self.token = payload.get("token")


__all__ = ["Webhook"]
