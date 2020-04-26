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
"""State of a shard."""

from __future__ import annotations

__all__ = ["ShardState"]

from hikari.internal import more_enums


@more_enums.must_be_unique
class ShardState(int, more_enums.Enum):
    """Describes the state of a shard."""

    NOT_RUNNING = 0
    """The shard is not running."""

    CONNECTING = more_enums.generated_value()
    """The shard is undergoing the initial connection handshake."""

    WAITING_FOR_READY = more_enums.generated_value()
    """The initialization handshake has completed.

    We are waiting for the shard to receive the `READY` event.
    """

    READY = more_enums.generated_value()
    """The shard is `READY`."""

    RESUMING = more_enums.generated_value()
    """The shard has sent a request to `RESUME` and is waiting for a response."""

    STOPPING = more_enums.generated_value()
    """The shard is currently shutting down permanently."""

    STOPPED = more_enums.generated_value()
    """The shard has shut down and is no longer connected."""

    def __str__(self) -> str:
        return self.name
