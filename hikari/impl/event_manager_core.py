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
"""A base implementation for an event manager."""

from __future__ import annotations

__all__ = ["EventManagerCore"]

import asyncio
import functools
import typing

from hikari.api import event_consumer
from hikari.api import event_dispatcher
from hikari.events import base
from hikari.events import other
from hikari.net import gateway
from hikari.utilities import aio
from hikari.utilities import data_binding
from hikari.utilities import klass
from hikari.utilities import reflect
from hikari.utilities import undefined

if typing.TYPE_CHECKING:
    from hikari.api import app as app_

    _EventT = typing.TypeVar("_EventT", bound=base.HikariEvent, covariant=True)
    _PredicateT = typing.Callable[[_EventT], typing.Union[bool, typing.Coroutine[None, typing.Any, bool]]]
    _SyncCallbackT = typing.Callable[[_EventT], None]
    _AsyncCallbackT = typing.Callable[[_EventT], typing.Coroutine[None, typing.Any, None]]
    _CallbackT = typing.Union[_SyncCallbackT, _AsyncCallbackT]
    _ListenerMapT = typing.MutableMapping[typing.Type[_EventT], typing.MutableSequence[_CallbackT]]
    _WaiterT = typing.Tuple[_PredicateT, aio.Future[_EventT]]
    _WaiterMapT = typing.MutableMapping[typing.Type[_EventT], typing.MutableSet[_WaiterT]]


class EventManagerCore(event_dispatcher.IEventDispatcher, event_consumer.IEventConsumer):
    """Provides functionality to consume and dispatch events.

    Specific event handlers should be in functions named `on_xxx` where `xxx`
    is the raw event name being dispatched in lower-case.
    """

    def __init__(self, app: app_.IApp) -> None:
        self._app = app
        self._listeners: _ListenerMapT = {}
        self._waiters: _WaiterMapT = {}
        self.logger = klass.get_logger(self)

    @property
    def app(self) -> app_.IApp:
        return self._app

    async def consume_raw_event(
        self, shard: gateway.Gateway, event_name: str, payload: data_binding.JSONObject
    ) -> None:
        try:
            callback = getattr(self, "on_" + event_name.lower())
            await callback(shard, payload)
        except AttributeError:
            self.logger.debug("ignoring unknown event %s", event_name)

    def subscribe(
        self,
        event_type: typing.Type[_EventT],
        callback: typing.Callable[[_EventT], typing.Union[typing.Coroutine[None, typing.Any, None], None]],
    ) -> None:
        if event_type not in self._listeners:
            self._listeners[event_type] = []

        if not asyncio.iscoroutinefunction(callback):

            @functools.wraps(callback)
            async def wrapper(event):
                return callback(event)

            self.subscribe(event_type, wrapper)
        else:
            self.logger.debug(
                "subscribing callback 'async def %s%s' to event-type %s.%s",
                getattr(callback, "__name__", "<anon>"),
                reflect.resolve_signature(callback),
                event_type.__module__,
                event_type.__qualname__,
            )
            self._listeners[event_type].append(callback)

    def unsubscribe(
        self,
        event_type: typing.Type[_EventT],
        callback: typing.Callable[[_EventT], typing.Union[typing.Coroutine[None, typing.Any, None], None]],
    ) -> None:
        if event_type in self._listeners:
            self.logger.debug(
                "unsubscribing callback %s%s from event-type %s.%s",
                getattr(callback, "__name__", "<anon>"),
                reflect.resolve_signature(callback),
                event_type.__module__,
                event_type.__qualname__,
            )
            self._listeners[event_type].remove(callback)
            if not self._listeners[event_type]:
                del self._listeners[event_type]

    def listen(
        self, event_type: typing.Union[undefined.Undefined, typing.Type[_EventT]] = undefined.Undefined(),
    ) -> typing.Callable[[_CallbackT], _CallbackT]:
        def decorator(callback: _CallbackT) -> _CallbackT:
            nonlocal event_type

            signature = reflect.resolve_signature(callback)
            params = signature.parameters.values()

            if len(params) != 1:
                raise TypeError("Event listener must have one parameter, the event object.")

            event_param = next(iter(params))

            if event_type is undefined.Undefined():
                if event_param.annotation is event_param.empty:
                    raise TypeError("Must provide the event type in the @listen decorator or as a type hint!")

                event_type = event_param.annotation

            self.subscribe(event_type, callback)
            return callback

        return decorator

    async def wait_for(
        self, event_type: typing.Type[_EventT], predicate: _PredicateT, timeout: typing.Union[float, int, None]
    ) -> _EventT:

        future = asyncio.get_event_loop().create_future()

        if event_type not in self._waiters:
            self._waiters[event_type] = set()

        self._waiters[event_type].add((predicate, future))

        return await asyncio.wait_for(future, timeout=timeout) if timeout is not None else await future

    async def _test_waiter(self, cls, event, predicate, future):
        try:
            result = predicate(event)
            if asyncio.iscoroutinefunction(result):
                result = await result

            if not result:
                return

        except Exception as ex:
            future.set_exception(ex)
        else:
            future.set_result(event)

        self._waiters[cls].remove((predicate, future))
        if not self._waiters[cls]:
            del self._waiters[cls]

    async def _invoke_callback(self, callback: _CallbackT, event: _EventT) -> None:
        try:
            result = callback(event)
            if asyncio.iscoroutine(result):
                await result

        except Exception as ex:
            # Skip the first frame in logs, we don't care for it.
            trio = type(ex), ex, ex.__traceback__.tb_next

            if base.is_no_catch_event(event):
                self.logger.error("an exception occurred handling an event, but it has been ignored", exc_info=trio)
            else:
                self.logger.error("an exception occurred handling an event", exc_info=trio)
                await self.dispatch(other.ExceptionEvent(exception=ex, event=event, callback=callback))

    def dispatch(self, event: base.HikariEvent) -> aio.Future[typing.Any]:
        if not isinstance(event, base.HikariEvent):
            raise TypeError(f"Events must be subclasses of {base.HikariEvent.__name__}, not {type(event).__name__}")

        # We only need to iterate through the MRO until we hit HikariEvent, as
        # anything after that is random garbage we don't care about, as they do
        # not describe event types. This improves efficiency as well.
        mro = type(event).mro()

        tasks = []

        for cls in mro[: mro.index(base.HikariEvent) + 1]:
            cls: typing.Type[_EventT]

            if cls in self._listeners:
                for callback in self._listeners[cls]:
                    tasks.append(self._invoke_callback(callback, event))

            if cls in self._waiters:
                for predicate, future in self._waiters[cls]:
                    tasks.append(self._test_waiter(cls, event, predicate, future))

        return asyncio.gather(*tasks) if tasks else aio.completed_future()
