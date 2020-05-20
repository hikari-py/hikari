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

from __future__ import annotations

__all__ = ["GatewayBot", "SessionStartLimit"]

import datetime
import typing

import attr

from hikari.internal import marshaller
from . import bases
from . import guilds


def _rest_after_deserializer(after: int) -> datetime.timedelta:
    return datetime.timedelta(milliseconds=after)


@marshaller.marshallable()
@attr.s(eq=True, hash=False, kw_only=True, slots=True)
class SessionStartLimit(bases.Entity, marshaller.Deserializable):
    """Used to represent information about the current session start limits."""

    total: int = marshaller.attrib(deserializer=int, repr=True)
    """The total number of session starts the current bot is allowed."""

    remaining: int = marshaller.attrib(deserializer=int, repr=True)
    """The remaining number of session starts this bot has."""

    reset_after: datetime.timedelta = marshaller.attrib(deserializer=_rest_after_deserializer, repr=True)
    """When `SessionStartLimit.remaining` will reset for the current bot.

    After it resets it will be set to `SessionStartLimit.total`.
    """


@marshaller.marshallable()
@attr.s(eq=True, hash=False, kw_only=True, slots=True)
class GatewayBot(bases.Entity, marshaller.Deserializable):
    """Used to represent gateway information for the connected bot."""

    url: str = marshaller.attrib(deserializer=str, repr=True)
    """The WSS URL that can be used for connecting to the gateway."""

    shard_count: int = marshaller.attrib(raw_name="shards", deserializer=int, repr=True)
    """The recommended number of shards to use when connecting to the gateway."""

    session_start_limit: SessionStartLimit = marshaller.attrib(
        deserializer=SessionStartLimit.deserialize, inherit_kwargs=True, repr=True
    )
    """Information about the bot's current session start limit."""


def _undefined_type_default() -> typing.Literal[guilds.ActivityType.PLAYING]:
    return guilds.ActivityType.PLAYING
