# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
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
"""Core interface for components that consume raw API event payloads."""
from __future__ import annotations

__all__: typing.Final[typing.List[str]] = ["IEventConsumerComponent", "IEventConsumerApp"]

import abc
import typing

from hikari.api import component
from hikari.api import rest as rest_api

if typing.TYPE_CHECKING:
    from hikari.api import event_factory as event_factory_
    from hikari.api import shard as gateway_shard
    from hikari.utilities import data_binding


class IEventConsumerComponent(component.IComponent, abc.ABC):
    """Interface describing a component that can consume raw gateway events.

    Implementations will usually want to combine this with a
    `hikari.api.event_dispatcher.IEventDispatcherBase` for a basic in-memory
    single-app event management system. You may in some cases implement this
    separately if you are passing events onto a system such as a message queue.
    """

    __slots__: typing.Sequence[str] = ()

    @abc.abstractmethod
    async def consume_raw_event(
        self, shard: gateway_shard.IGatewayShard, event_name: str, payload: data_binding.JSONObject
    ) -> None:
        """Process a raw event from a gateway shard and process it.

        Parameters
        ----------
        shard : hikari.api.shard.IGatewayShard
            The gateway shard that emitted the event.
        event_name : builtins.str
            The event name.
        payload : hikari.utilities.data_binding.JSONObject
            The payload provided with the event.
        """


# TODO: generify and remove requirement for REST for event handling only.
class IEventConsumerApp(rest_api.IRESTApp, abc.ABC):
    """Application specialization that supports consumption of raw events.

    This may be combined with `IGatewayZookeeperApp` for most single-process
    bots, or may be a specific component for large distributed applications
    that consume events from a message queue, for example.
    """

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def event_consumer(self) -> IEventConsumerComponent:
        """Raw event consumer.

        This should be passed raw event payloads from your gateway
        websocket implementation.

        Returns
        -------
        hikari.api.event_consumer.IEventConsumerComponent
            The event consumer implementation in-use.
        """

    @property
    @abc.abstractmethod
    def event_factory(self) -> event_factory_.IEventFactoryComponent:
        """Event factory.

        This is a component that builds event models.

        Returns
        -------
        hikari.api.event_factory.IEventFactory
            The model factory for events.
        """
