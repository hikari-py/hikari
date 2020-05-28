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
from __future__ import annotations

__all__ = ["EventManagerImpl"]

import typing

from hikari import event_consumer
from hikari import event_dispatcher
from hikari.events import base
from hikari.internal import class_helpers
from hikari.internal import more_asyncio
from hikari.internal import unset
from hikari.net import gateway

if typing.TYPE_CHECKING:
    from hikari import app as app_
    from hikari.internal import more_typing

    _EventT = typing.TypeVar("_EventT", bound=base.HikariEvent, covariant=True)
    _PredicateT = typing.Callable[[_EventT], typing.Union[bool, more_typing.Coroutine[bool]]]


class EventManagerImpl(event_dispatcher.IEventDispatcher, event_consumer.IEventConsumer):
    def __init__(self, app: app_.IApp) -> None:
        self._app = app
        self.logger = class_helpers.get_logger(self)

    @property
    def app(self) -> app_.IApp:
        return self._app

    def dispatch(self, event: base.HikariEvent) -> more_typing.Future[typing.Any]:
        # TODO: this
        return more_asyncio.completed_future()

    async def consume_raw_event(self, shard: gateway.Gateway, event_name: str, payload: more_typing.JSONType) -> None:
        try:
            callback = getattr(self, "on_" + event_name.lower())
            await callback(shard, payload)
        except AttributeError:
            self.logger.debug("ignoring unknown event %s", event_name)

    def subscribe(
        self,
        event_type: typing.Type[_EventT],
        callback: typing.Callable[[_EventT], typing.Union[more_typing.Coroutine[None], None]],
    ) -> None:
        pass

    def unsubscribe(
        self,
        event_type: typing.Type[_EventT],
        callback: typing.Callable[[_EventT], typing.Union[more_typing.Coroutine[None], None]],
    ) -> None:
        pass

    def listen(self, event_type: typing.Union[unset.Unset, typing.Type[_EventT]]) -> None:
        pass

    async def wait_for(
        self, event_type: typing.Type[_EventT], predicate: _PredicateT, timeout: typing.Union[float, int, None]
    ) -> _EventT:
        pass
