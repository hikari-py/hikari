#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019-2020
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
"""Components and entities that are used to describe webhooks on Discord."""

from __future__ import annotations

__all__ = ["WebhookType", "Webhook"]

import typing

import attr

from hikari import bases
from hikari import users
from hikari.internal import marshaller
from hikari.internal import more_enums


@more_enums.must_be_unique
class WebhookType(int, more_enums.Enum):
    """Types of webhook."""

    INCOMING = 1
    """Incoming webhook."""

    CHANNEL_FOLLOWER = 2
    """Channel Follower webhook."""


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class Webhook(bases.Unique, marshaller.Deserializable):
    """Represents a webhook object on Discord.

    This is an endpoint that can have messages sent to it using standard
    HTTP requests, which enables external services that are not bots to
    send informational messages to specific channels.
    """

    type: WebhookType = marshaller.attrib(deserializer=WebhookType, repr=True)
    """The type of the webhook."""

    guild_id: typing.Optional[bases.Snowflake] = marshaller.attrib(
        deserializer=bases.Snowflake, if_undefined=None, default=None, repr=True
    )
    """The guild ID of the webhook."""

    channel_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake, repr=True)
    """The channel ID this webhook is for."""

    user: typing.Optional[users.User] = marshaller.attrib(
        deserializer=users.User.deserialize, if_undefined=None, default=None, inherit_kwargs=True, repr=True
    )
    """The user that created the webhook

    !!! info
        This will be `None` when getting a webhook with bot authorization rather
        than the webhook's token.
    """

    name: typing.Optional[str] = marshaller.attrib(deserializer=str, if_none=None, repr=True)
    """The name of the webhook."""

    avatar_hash: typing.Optional[str] = marshaller.attrib(raw_name="avatar", deserializer=str, if_none=None)
    """The avatar hash of the webhook."""

    token: typing.Optional[str] = marshaller.attrib(deserializer=str, if_undefined=None, default=None)
    """The token for the webhook.

    !!! info
        This is only available for incoming webhooks that are created in the
        channel settings.
    """
