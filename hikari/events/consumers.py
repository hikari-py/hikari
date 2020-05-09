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
"""Definition of the interface a compliant weaving implementation should provide.

State object handle decoding events and managing application state.
"""

from __future__ import annotations

__all__ = ["RawEventConsumer"]

import abc
import typing

if typing.TYPE_CHECKING:
    from hikari.clients import shards


class RawEventConsumer(abc.ABC):
    """Consumer of raw events from Discord.

    RawEventConsumer describes an object that takes any event payloads that
    Discord dispatches over a websocket and decides how to process it further.
    This is used as the core base for any form of event manager type.

    This base may also be used by users to dispatch the event to a completely
    different medium, such as a message queue for distributed applications.
    """

    @abc.abstractmethod
    def process_raw_event(
        self, shard_client_obj: shards.ShardClient, name: str, payload: typing.Mapping[str, str],
    ) -> None:
        """Consume a raw event that was received from a shard connection.

        Parameters
        ----------
        shard_client_obj : hikari.clients.shards.ShardClient
            The client for the shard that received the event.
        name : str
            The raw event name.
        payload : typing.Any
            The raw event payload. Will be a JSON-compatible type.
        """
