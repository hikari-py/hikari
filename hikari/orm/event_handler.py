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
Abstract definition of an event handler.
"""
import abc
import typing

from hikari.net import gateway


class IEventHandler(abc.ABC):
    """
    An abstract interface for an event handler.

    The purpose of this is to provide a single unified interface that any type and shape of event
    handler can implement and automatically be compatible with the rest of Hikari's infrastructure.

    This library provides a :class:`DispatchingEventAdapter` subinterface that is implemented to
    provide capability for single-process bots, but one may choose to extend this in a different
    way to store event payloads on a message queue such as RabbitMQ, ActiveMQ, IBM MQ, etc. This
    would allow a distributed bot to be designed to the user's specific use case, and allows Hikari
    to become much more expandable and flexible for large bots in the future.
    """

    __slots__ = ()

    @abc.abstractmethod
    async def consume_raw_event(self, shard: gateway.GatewayClient, event_name: str, payload: typing.Any) -> None:
        """
        This is invoked by a gateway client instance whenever an event of any type occurs. These are
        defined in :mod:`hikari.events` for convenience and documentation purposes.

        This is a standard method that is expected to handle the given event information in some way.
        How it does this depends on what the implementation is expected to do, but a general pattern
        that will be followed will be to invoke another method elsewhere or schedule an awaitable
        on the running event loop.

        Args:
            shard:
                The gateway client that provided this event.
            event_name:
                The raw event name. See :mod:`hikari.events`.
            payload:
                The raw payload. This will be potentially any form of information and will vary between
                events.
        """
