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

__all__: typing.Final[typing.Sequence[str]] = ["GatewayBot", "SessionStartLimit"]

import typing

import attr

if typing.TYPE_CHECKING:
    import datetime


@attr.s(eq=True, hash=False, init=False, kw_only=True, slots=True)
class SessionStartLimit:
    """Used to represent information about the current session start limits."""

    total: int = attr.ib(repr=True)
    """The total number of session starts the current bot is allowed."""

    remaining: int = attr.ib(repr=True)
    """The remaining number of session starts this bot has."""

    reset_after: datetime.timedelta = attr.ib(repr=True)
    """When `SessionStartLimit.remaining` will reset for the current bot.

    After it resets it will be set to `SessionStartLimit.total`.
    """

    # This is not documented at the time of writing, but is a confirmed API
    # feature, so I have included it for completeness.
    max_concurrency: int = attr.ib(repr=True)
    """Maximum connection concurrency.

    This defines how many shards can be started at once within a 5 second
    window. For most bots, this will always be `1`, but for very large bots,
    this may be increased to reduce startup times. Contact Discord for
    more information.
    """


@attr.s(eq=True, hash=False, init=False, kw_only=True, slots=True)
class GatewayBot:
    """Used to represent gateway information for the connected bot."""

    url: str = attr.ib(repr=True)
    """The WSS URL that can be used for connecting to the gateway."""

    shard_count: int = attr.ib(repr=True)
    """The recommended number of shards to use when connecting to the gateway."""

    session_start_limit: SessionStartLimit = attr.ib(repr=True)
    """Information about the bot's current session start limit."""
