# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021 davfsa
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Entities directly related to creating and managing gateway shard sessions."""

from __future__ import annotations

__all__: typing.List[str] = ["GatewayBot", "SessionStartLimit"]

import typing

import attr

from hikari.internal import attr_extensions
from hikari.internal import time

if typing.TYPE_CHECKING:
    import datetime


@attr_extensions.with_copy
@attr.s(eq=True, hash=False, init=True, kw_only=True, slots=True, weakref_slot=False)
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

    _created_at: datetime.datetime = attr.ib(factory=time.local_datetime, init=False)

    @property
    def used(self) -> int:
        """Return how many times you have sent an IDENTIFY in the window."""
        return self.total - self.remaining

    @property
    def reset_at(self) -> datetime.datetime:
        """Return the approximate time that the IDENTIFY limit resets at."""
        return self._created_at + self.reset_after


@attr_extensions.with_copy
@attr.s(eq=True, hash=False, init=True, kw_only=True, slots=True, weakref_slot=False)
class GatewayBot:
    """Used to represent gateway information for the connected bot."""

    url: str = attr.ib(repr=True)
    """The WSS URL that can be used for connecting to the gateway."""

    shard_count: int = attr.ib(repr=True)
    """The recommended number of shards to use when connecting to the gateway."""

    session_start_limit: SessionStartLimit = attr.ib(repr=True)
    """Information about the bot's current session start limit."""
