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
"""Entities directly related to creating and managing gateway shards."""
__all__ = ["GatewayBot", "GatewayActivity"]

import datetime
import typing

from hikari import entities
from hikari import guilds
from hikari.internal import marshaller


@marshaller.attrs(slots=True)
class SessionStartLimit(entities.HikariEntity, entities.Deserializable):
    """Used to represent information about the current session start limits."""

    #: The total number of session starts the current bot is allowed.
    #:
    #: :type: :obj:`int`
    total: int = marshaller.attrib(deserializer=int)

    #: The remaining number of session starts this bot has.
    #:
    #: :type: :obj:`int`
    remaining: int = marshaller.attrib(deserializer=int)

    #: The timedelta of when :attr:`remaining` will reset back to :attr:`total`
    #: for the current bot.
    #:
    #: :type: :obj:`datetime.timedelta`
    reset_after: datetime.timedelta = marshaller.attrib(
        deserializer=lambda after: datetime.timedelta(milliseconds=after),
    )


@marshaller.attrs(slots=True)
class GatewayBot(entities.HikariEntity, entities.Deserializable):
    """Used to represent gateway information for the connected bot."""

    #: The WSS URL that can be used for connecting to the gateway.
    #:
    #: :type: :obj:`str`
    url: str = marshaller.attrib(deserializer=str)

    #: The recommended number of shards to use when connecting to the gateway.
    #:
    #: :type: :obj:`int`
    shard_count: int = marshaller.attrib(raw_name="shards", deserializer=int)

    #: Information about the bot's current session start limit.
    #:
    #: :type: :obj:`SessionStartLimit`
    session_start_limit: SessionStartLimit = marshaller.attrib(deserializer=SessionStartLimit.deserialize)


@marshaller.attrs(slots=True)
class GatewayActivity(entities.Deserializable, entities.Serializable):
    """An activity that the bot can set for one or more shards.

    This will show the activity as the bot's presence.
    """

    #: The activity name.
    #:
    #: :type: :obj:`str`
    name: str = marshaller.attrib(deserializer=str, serializer=str)

    #: The activity URL. Only valid for ``STREAMING`` activities.
    #:
    #: :type: :obj:`str`, optional
    url: typing.Optional[str] = marshaller.attrib(deserializer=str, serializer=str, if_none=None, if_undefined=None)

    #: The activity type.
    #:
    #: :type: :obj:`hikari.guilds.ActivityType`
    type: guilds.ActivityType = marshaller.attrib(
        deserializer=guilds.ActivityType, serializer=int, if_undefined=lambda: guilds.ActivityType.PLAYING
    )
