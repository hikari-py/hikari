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
"""
Additional types used for specific HTTP call responses, etc.
"""
from __future__ import annotations

import datetime

from hikari.internal_utilities import data_structures
from hikari.orm.models import interfaces


class GatewayBot(interfaces.IModel):
    """
    Gateway Bot connection recommendations by Discord.

    This should not be cached.
    """

    __slots__ = ("url", "shards", "session_start_limit")

    #: The URL to connect to.
    url: str

    #: The number of shards to use.
    shards: int

    #: The remaining limits for starting a gateway session.
    session_start_limit: SessionStartLimit

    def __init__(self, payload: data_structures.DiscordObjectT) -> None:
        self.url = payload["url"]
        self.shards = int(payload["shards"])
        self.session_start_limit = SessionStartLimit(payload["session_start_limit"])


class SessionStartLimit(interfaces.IModel):
    """
    Describes how many more times you can identify with the gateway within a given time window.

    If you exceed this, you will have your token reset by Discord.
    """

    __slots__ = ("total", "remaining", "reset_at")

    #: Total number of times you can IDENTIFY with the gateway.
    #:
    #: :type: :class:`int`
    total: int

    #: How many more times you can IDENTIFY with the gateway before your token is reset in the
    #: given time window.
    #:
    #: :type: :class:`int`
    remaining: int

    #: When the limit will be reset.
    #:
    #: :type: :class:`datetime.datetime`
    reset_at: datetime.datetime

    def __init__(self, payload: data_structures.DiscordObjectT) -> None:
        self.total = int(payload["total"])
        self.remaining = int(payload["remaining"])
        reset_after = float(payload["reset_after"])
        self.reset_at = datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(milliseconds=reset_after)

    @property
    def used(self) -> int:
        """The number of times you have IDENTIFIED in this time window."""
        return self.total - self.remaining


__all__ = ["GatewayBot", "SessionStartLimit"]
