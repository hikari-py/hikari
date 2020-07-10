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

__all__: typing.Final[typing.List[str]] = ["EventManagerCoreComponent"]

import asyncio
import logging
import typing
import warnings

from hikari import errors
from hikari.api.gateway import consumer
from hikari.api.gateway import dispatcher
from hikari.events import base as base_events
from hikari.events import other as other_events
from hikari.models import intents
from hikari.utilities import aio
from hikari.utilities import data_binding
from hikari.utilities import reflect
from hikari.utilities import undefined

if typing.TYPE_CHECKING:
    from hikari.api.gateway import shard as gateway_shard
    from hikari.api.rest import app as rest_app

_LOGGER: typing.Final[logging.Logger] = logging.getLogger("hikari")

if typing.TYPE_CHECKING:
    ListenerMapT = typing.MutableMapping[
        typing.Type[dispatcher.EventT_co], typing.MutableSequence[dispatcher.AsyncCallbackT[dispatcher.EventT_co]]
    ]
    WaiterT = typing.Tuple[dispatcher.PredicateT[dispatcher.EventT_co], asyncio.Future[dispatcher.EventT_co]]
    WaiterMapT = typing.MutableMapping[typing.Type[dispatcher.EventT_co], typing.MutableSet[WaiterT]]


def _default_predicate(_: dispatcher.EventT_inv) -> bool:
    return True


class EventManagerCoreComponent(dispatcher.IEventDispatcherComponent, consumer.IEventConsumerComponent):
    """Provides functionality to consume and dispatch events.

    Specific event handlers should be in functions named `on_xxx` where `xxx`
    is the raw event name being dispatched in lower-case.
    """

    def __init__(self, app: rest_app.IRESTApp, intents_: typing.Optional[intents.Intent]) -> None:
        self._app = app
        self._intents = intents_
        self._listeners: ListenerMapT = {}
        self._waiters: WaiterMapT = {}

    @property
    @typing.final
    def app(self) -> rest_app.IRESTApp:
        return self._app

    async def consume_raw_event(
        self, shard: gateway_shard.IGatewayShard, event_name: str, payload: data_binding.JSONObject
    ) -> None:
        try:
            callback = getattr(self, "on_" + event_name.lower())
        except AttributeError:
            _LOGGER.debug("ignoring unknown event %s", event_name)
        else:
            await callback(shard, payload)

    def subscribe(
        self,
        event_type: typing.Type[dispatcher.EventT_co],
        callback: dispatcher.AsyncCallbackT[dispatcher.EventT_co],
        *,
        _nested: int = 0,
    ) -> dispatcher.AsyncCallbackT[dispatcher.EventT_co]:
        # `_nested` is used to show the correct source code snippet if an intent
        # warning is triggered.

        # If None, the user is on v6 with intents disabled, so we don't care.
        if self._intents is not None:
            # Collection of combined bitfield combinations of intents that
            # could be enabled to receive this event.
            expected_intent_sets = base_events.get_required_intents_for(event_type)
            if not any(self._intents & expected_intent_set for expected_intent_set in expected_intent_sets):
                expected_intents_str = ", ".join(
                    str(expected_intent_set) for expected_intent_set in expected_intent_sets
                )

                warnings.warn(
                    f"You have tried to listen to {event_type.__name__}, but this will only ever be triggered if you "
                    f"enable one of the following intents: {expected_intents_str}.",
                    category=errors.IntentWarning,
                    stacklevel=_nested + 2,
                )

        if event_type not in self._listeners:
            self._listeners[event_type] = []

        if not asyncio.iscoroutinefunction(callback):
            raise TypeError("Event callbacks must be coroutine functions (`async def')")

        _LOGGER.debug(
            "subscribing callback 'async def %s%s' to event-type %s.%s",
            getattr(callback, "__name__", "<anon>"),
            reflect.resolve_signature(callback),
            event_type.__module__,
            event_type.__qualname__,
        )

        self._listeners[event_type].append(callback)

        return callback

    def get_listeners(
        self, event_type: typing.Type[dispatcher.EventT_co], *, polymorphic: bool = True,
    ) -> typing.Collection[dispatcher.AsyncCallbackT[dispatcher.EventT_co]]:
        if polymorphic:
            listeners: typing.List[dispatcher.AsyncCallbackT[dispatcher.EventT_co]] = []
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
        event_type: typing.Type[dispatcher.EventT_co],
        callback: dispatcher.AsyncCallbackT[dispatcher.EventT_co],
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
        self, event_type: typing.Type[dispatcher.EventT_co], callback: dispatcher.AsyncCallbackT[dispatcher.EventT_co]
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
        self,
        event_type: typing.Union[undefined.UndefinedType, typing.Type[dispatcher.EventT_co]] = undefined.UNDEFINED,
    ) -> typing.Callable[
        [dispatcher.AsyncCallbackT[dispatcher.EventT_co]], dispatcher.AsyncCallbackT[dispatcher.EventT_co]
    ]:
        def decorator(
            callback: dispatcher.AsyncCallbackT[dispatcher.EventT_co],
        ) -> dispatcher.AsyncCallbackT[dispatcher.EventT_co]:
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

                if not isinstance(event_type, type) or not issubclass(event_type, base_events.Event):
                    raise TypeError("Event type must derive from Event")

            self.subscribe(event_type, callback, _nested=1)
            return callback

        return decorator

    async def wait_for(
        self,
        event_type: typing.Type[dispatcher.EventT_co],
        /,
        timeout: typing.Union[float, int, None],
        predicate: typing.Optional[dispatcher.PredicateT[dispatcher.EventT_co]] = None,
    ) -> dispatcher.EventT_co:

        if predicate is None:
            predicate = _default_predicate

        future: asyncio.Future[dispatcher.EventT_co] = asyncio.get_event_loop().create_future()

        if event_type not in self._waiters:
            self._waiters[event_type] = set()

        self._waiters[event_type].add((predicate, future))

        return await asyncio.wait_for(future, timeout=timeout) if timeout is not None else await future

    async def _test_waiter(
        self,
        cls: typing.Type[dispatcher.EventT_inv],
        event: dispatcher.EventT_inv,
        predicate: dispatcher.PredicateT[dispatcher.EventT_inv],
        future: asyncio.Future[dispatcher.EventT_inv],
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

    def dispatch(self, event: dispatcher.EventT_inv) -> asyncio.Future[typing.Any]:
        if not isinstance(event, base_events.Event):
            raise TypeError(f"Events must be subclasses of {base_events.Event.__name__}, not {type(event).__name__}")

        # We only need to iterate through the MRO until we hit Event, as
        # anything after that is random garbage we don't care about, as they do
        # not describe event types. This improves efficiency as well.
        mro = type(event).mro()

        tasks: typing.List[typing.Coroutine[None, typing.Any, None]] = []

        for cls in mro[: mro.index(base_events.Event) + 1]:

            if cls in self._listeners:
                for callback in self._listeners[cls]:
                    tasks.append(self._invoke_callback(callback, event))

            if cls in self._waiters:
                for predicate, future in self._waiters[cls]:
                    # noinspection PyTypeChecker
                    tasks.append(self._test_waiter(cls, event, predicate, future))

        return asyncio.gather(*tasks) if tasks else aio.completed_future()

    async def _invoke_callback(
        self, callback: dispatcher.AsyncCallbackT[dispatcher.EventT_inv], event: dispatcher.EventT_inv
    ) -> None:
        try:
            result = callback(event)
            if asyncio.iscoroutine(result):
                await result

        except Exception as ex:
            # Skip the first frame in logs, we don't care for it.
            trio = type(ex), ex, ex.__traceback__.tb_next if ex.__traceback__ is not None else None

            if base_events.is_no_catch_event(event):
                _LOGGER.error("an exception occurred handling an event, but it has been ignored", exc_info=trio)
            else:
                _LOGGER.error("an exception occurred handling an event", exc_info=trio)
                await self.dispatch(other_events.ExceptionEvent(exception=ex, event=event, callback=callback))
