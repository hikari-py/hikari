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
Webhooks.
"""
from __future__ import annotations

import enum
import typing

from hikari.internal_utilities import containers
from hikari.internal_utilities import reprs
from hikari.internal_utilities import transformations
from hikari.orm import fabric
from hikari.orm.models import bases
from hikari.orm.models import users


class WebhookType(bases.BestEffortEnumMixin, enum.IntEnum):
    """
    The type of a webhook.
    """

    #: Incoming webhooks that can be posted using Discord's token endpoint.
    INCOMING = 1
    #: Channel follows webhooks that are posted to by discord announcement channels.
    CHANNEL_FOLLOWER = 2


class WebhookUser(users.BaseUser):
    """
    The user representation of a webhook.
    """

    __slots__ = ("id", "username", "discriminator", "avatar_hash")

    #: The ID of the webhook user.
    #:
    #: :type: :class:`int`
    id: int

    #: The username of the webhook.
    #:
    #: :type: :class:`str`
    username: str

    #: The discriminator of the webhook user.
    #:
    #: :type: :class:`int`
    discriminator: int

    #: The avatar hash of the webhook.
    #:
    #: :type: :class:`str`
    avatar_hash: str

    def __init__(self, payload: containers.JSONObject) -> None:
        self.id = int(payload["id"])
        self.username = payload["username"]
        self.discriminator = int(payload["discriminator"])
        self.avatar_hash = payload["avatar"]

    @property
    def is_bot(self) -> bool:
        """Webhooks are always bots."""
        return True


class Webhook(bases.BaseModelWithFabric, bases.SnowflakeMixin):
    """
    Describes a webhook. This is an HTTP endpoint that can be used to send messages to certain
    channels without spinning up a complete bot implementation elsewhere (such as for CI pipelines).
    """

    __slots__ = ("_fabric", "id", "type", "guild_id", "channel_id", "user", "name", "avatar_hash", "token")
    __copy_by_ref__ = ("user",)

    #: The ID of the guild that the webhook is in.
    #:
    #: :type: :class:`int`
    guild_id: int

    #: The ID of the channel that the webhook is in.
    #:
    #: :type: :class:`int`
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
    #: :type: :class:`WebhookUser` or `None`
    user: typing.Optional[WebhookUser]

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

    __repr__ = reprs.repr_of("id", "name")

    def __init__(
        self, fabric_obj: fabric.Fabric, payload: containers.JSONObject, guild_id: typing.Optional[int] = None
    ) -> None:
        self._fabric = fabric_obj
        self.id = int(payload["id"])
        self.type = transformations.try_cast(payload.get("type"), WebhookType)
        self.guild_id = int(payload.get("guild_id", guild_id))
        self.channel_id = int(payload["channel_id"])
        self.user = transformations.nullable_cast(payload.get("user"), fabric_obj.state_registry.parse_webhook_user)
        self.name = payload.get("name")
        self.avatar_hash = payload.get("avatar_hash")
        self.token = payload.get("token")


#: A :class:`Webhook` instance, or the :class:`int`/:class:`str` ID of one.
WebhookLikeT = typing.Union[bases.RawSnowflakeT, Webhook]

__all__ = ["WebhookUser", "Webhook", "WebhookLikeT"]
