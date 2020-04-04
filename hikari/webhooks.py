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
__all__ = ["WebhookType", "Webhook"]

import enum
import typing

from hikari.internal import marshaller
from hikari import entities
from hikari import snowflakes
from hikari import users


@enum.unique
class WebhookType(enum.IntEnum):
    """Types of webhook."""

    #: Incoming webhook.
    INCOMING = 1
    #: Channel Follower webhook.
    CHANNEL_FOLLOWER = 2


@marshaller.attrs(slots=True)
class Webhook(snowflakes.UniqueEntity, entities.Deserializable):
    """Represents a webhook object on Discord.

    This is an endpoint that can have messages sent to it using standard
    HTTP requests, which enables external services that are not bots to
    send informational messages to specific channels.
    """

    #: The type of the webhook.
    #:
    #: :type: :obj:`WebhookType`
    type: WebhookType = marshaller.attrib(deserializer=WebhookType)

    #: The guild ID of the webhook.
    #:
    #: :type: :obj:`hikari.snowflakes.Snowflake`, optional
    guild_id: typing.Optional[snowflakes.Snowflake] = marshaller.attrib(
        deserializer=snowflakes.Snowflake.deserialize, if_undefined=None
    )

    #: The channel ID this webhook is for.
    #:
    #: :type: :obj:`hikari.snowflakes.Snowflake`
    channel_id: snowflakes.Snowflake = marshaller.attrib(deserializer=snowflakes.Snowflake.deserialize)

    #: The user that created the webhook
    #:
    #: Note
    #: ----
    #: This will be ``None`` when getting a webhook with a token
    #:
    #:
    #: :type: :obj:`hikari.users.User`, optional
    user: typing.Optional[users.User] = marshaller.attrib(deserializer=users.User.deserialize, if_undefined=None)

    #: The default name of the webhook.
    #:
    #: :type: :obj:`str`, optional
    name: typing.Optional[str] = marshaller.attrib(deserializer=str, if_none=None)

    #: The default avatar hash of the webhook.
    #:
    #: :type: :obj:`str`, optional
    avatar_hash: typing.Optional[str] = marshaller.attrib(raw_name="avatar", deserializer=str, if_none=None)

    #: The token of the webhook.
    #:
    #: Note
    #: ----
    #: This is only available for Incoming webhooks.
    #:
    #:
    #: :type: :obj:`str`, optional
    token: typing.Optional[str] = marshaller.attrib(deserializer=str, if_undefined=None)
