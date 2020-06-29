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

__all__: typing.Final[typing.Sequence[str]] = ["EventManagerCoreComponent"]

import asyncio
import functools
import logging
import typing

from hikari.api import event_consumer
from hikari.api import event_dispatcher
from hikari.events import base
from hikari.events import other
from hikari.net import gateway
from hikari.utilities import aio
from hikari.utilities import data_binding
from hikari.utilities import reflect
from hikari.utilities import undefined

if typing.TYPE_CHECKING:
    from hikari.api import rest


_LOGGER: typing.Final[logging.Logger] = logging.getLogger("hikari")


if typing.TYPE_CHECKING:
    EventT = typing.TypeVar("EventT", bound=base.Event, contravariant=True)
    PredicateT = typing.Callable[[EventT], typing.Union[bool, typing.Coroutine[None, typing.Any, bool]]]
    SyncCallbackT = typing.Callable[[EventT], None]
    AsyncCallbackT = typing.Callable[[EventT], typing.Coroutine[None, typing.Any, None]]
    CallbackT = typing.Union[SyncCallbackT, AsyncCallbackT]
    ListenerMapT = typing.MutableMapping[typing.Type[EventT], typing.MutableSequence[AsyncCallbackT]]
    WaiterT = typing.Tuple[PredicateT, asyncio.Future[EventT]]
    WaiterMapT = typing.MutableMapping[typing.Type[EventT], typing.MutableSet[WaiterT]]


class EventManagerCoreComponent(event_dispatcher.IEventDispatcherComponent, event_consumer.IEventConsumerComponent):
    """Provides functionality to consume and dispatch events.

    Specific event handlers should be in functions named `on_xxx` where `xxx`
    is the raw event name being dispatched in lower-case.
    """

    def __init__(self, app: rest.IRESTClient) -> None:
        self._app = app
        self._listeners: ListenerMapT = {}
        self._waiters: WaiterMapT = {}

    @property
    @typing.final
    def app(self) -> rest.IRESTClient:
        return self._app

    async def consume_raw_event(
        self, shard: gateway.Gateway, event_name: str, payload: data_binding.JSONObject
    ) -> None:
        try:
            callback = getattr(self, "on_" + event_name.lower())
            await callback(shard, payload)
        except AttributeError:
            _LOGGER.debug("ignoring unknown event %s", event_name)

    def subscribe(
        self,
        event_type: typing.Type[EventT],
        callback: typing.Callable[[EventT], typing.Union[typing.Coroutine[None, typing.Any, None], None]],
    ) -> typing.Callable[[EventT], typing.Coroutine[None, typing.Any, None]]:
        if event_type not in self._listeners:
            self._listeners[event_type] = []

        if not asyncio.iscoroutinefunction(callback):

            @functools.wraps(callback)
            async def wrapper(event: EventT) -> None:
                callback(event)

            self.subscribe(event_type, wrapper)

            return wrapper
        else:
            _LOGGER.debug(
                "subscribing callback 'async def %s%s' to event-type %s.%s",
                getattr(callback, "__name__", "<anon>"),
                reflect.resolve_signature(callback),
                event_type.__module__,
                event_type.__qualname__,
            )

            callback = typing.cast("typing.Callable[[EventT], typing.Coroutine[None, typing.Any, None]]", callback)
            self._listeners[event_type].append(callback)

            return callback

    def get_listeners(
        self, event_type: typing.Type[EventT], *, polymorphic: bool = True,
    ) -> typing.Collection[typing.Callable[[EventT], typing.Coroutine[None, typing.Any, None]]]:
        if polymorphic:
            listeners: typing.List[typing.Callable[[EventT], typing.Coroutine[None, typing.Any, None]]] = []
            for subscribed_event_type, subscribed_listeners in self._listeners.items():
                if issubclass(subscribed_event_type, event_type):
                    listeners += subscribed_listeners
            return listeners
        else:
            items = self._listeners.get(event_type)
            if items is not None:
                return items[:]

            return []

    def has_listener(
        self,
        event_type: typing.Type[EventT],
        callback: typing.Callable[[EventT], typing.Coroutine[None, typing.Any, None]],
        *,
        polymorphic: bool = True,
    ) -> bool:
        if polymorphic:
            for subscribed_event_type, listeners in self._listeners.items():
                if issubclass(subscribed_event_type, event_type) and callback in listeners:
                    return True
            return False
        else:
            if event_type not in self._listeners:
                return False
            return callback in self._listeners[event_type]

    def unsubscribe(
        self,
        event_type: typing.Type[EventT],
        callback: typing.Callable[[EventT], typing.Coroutine[None, typing.Any, None]],
    ) -> None:
        if event_type in self._listeners:
            _LOGGER.debug(
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
        self, event_type: typing.Union[undefined.UndefinedType, typing.Type[EventT]] = undefined.UNDEFINED,
    ) -> typing.Callable[[CallbackT], CallbackT]:
        def decorator(callback: CallbackT) -> CallbackT:
            nonlocal event_type

            signature = reflect.resolve_signature(callback)
            params = signature.parameters.values()

            if len(params) != 1:
                raise TypeError("Event listener must have exactly one parameter, the event object.")

            event_param = next(iter(params))

            if event_type is undefined.UNDEFINED:
                if event_param.annotation is event_param.empty:
                    raise TypeError("Must provide the event type in the @listen decorator or as a type hint!")

                event_type = event_param.annotation

                if not isinstance(event_type, type) or not issubclass(event_type, base.Event):
                    raise TypeError("Event type must derive from Event")

            self.subscribe(event_type, callback)
            return callback

        return decorator

    async def wait_for(
        self, event_type: typing.Type[EventT], predicate: PredicateT, timeout: typing.Union[float, int, None]
    ) -> EventT:

        future: asyncio.Future[EventT] = asyncio.get_event_loop().create_future()

        if event_type not in self._waiters:
            self._waiters[event_type] = set()

        self._waiters[event_type].add((predicate, future))

        return await asyncio.wait_for(future, timeout=timeout) if timeout is not None else await future

    async def _test_waiter(
        self, cls: typing.Type[EventT], event: EventT, predicate: PredicateT, future: asyncio.Future[EventT]
    ) -> None:
        try:
            result = predicate(event)
            if asyncio.iscoroutine(result):
                result = await result  # type: ignore

            if not result:
                return

        except Exception as ex:
            future.set_exception(ex)
        else:
            future.set_result(event)

        self._waiters[cls].remove((predicate, future))
        if not self._waiters[cls]:
            del self._waiters[cls]

    def dispatch(self, event: base.Event) -> asyncio.Future[typing.Any]:
        if not isinstance(event, base.Event):
            raise TypeError(f"Events must be subclasses of {base.Event.__name__}, not {type(event).__name__}")

        # We only need to iterate through the MRO until we hit Event, as
        # anything after that is random garbage we don't care about, as they do
        # not describe event types. This improves efficiency as well.
        mro = type(event).mro()

        tasks: typing.List[typing.Coroutine[None, typing.Any, None]] = []

        for cls in mro[: mro.index(base.Event) + 1]:

            if cls in self._listeners:
                for callback in self._listeners[cls]:
                    tasks.append(self._invoke_callback(callback, event))

            if cls in self._waiters:
                for predicate, future in self._waiters[cls]:
                    # noinspection PyTypeChecker
                    tasks.append(self._test_waiter(cls, event, predicate, future))

        return asyncio.gather(*tasks) if tasks else aio.completed_future()

    async def _invoke_callback(self, callback: AsyncCallbackT, event: EventT) -> None:
        try:
            result = callback(event)
            if asyncio.iscoroutine(result):
                await result

        except Exception as ex:
            # Skip the first frame in logs, we don't care for it.
            trio = type(ex), ex, ex.__traceback__.tb_next if ex.__traceback__ is not None else None

            if base.is_no_catch_event(event):
                _LOGGER.error("an exception occurred handling an event, but it has been ignored", exc_info=trio)
            else:
                _LOGGER.error("an exception occurred handling an event", exc_info=trio)
                await self.dispatch(other.ExceptionEvent(exception=ex, event=event, callback=callback))
