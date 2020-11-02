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
"""A base implementation for an event manager."""

from __future__ import annotations

__all__: typing.List[str] = ["EventManagerBase"]

import asyncio
import inspect
import logging
import typing
import warnings

from hikari import errors
from hikari import event_stream
from hikari import intents as intents_
from hikari import traits
from hikari.api import event_dispatcher
from hikari.events import base_events
from hikari.internal import aio
from hikari.internal import data_binding
from hikari.internal import reflect

if typing.TYPE_CHECKING:
    from hikari.api import shard as gateway_shard

_LOGGER: typing.Final[logging.Logger] = logging.getLogger("hikari")

if typing.TYPE_CHECKING:
    ListenerMapT = typing.MutableMapping[
        typing.Type[event_dispatcher.EventT_co],
        typing.MutableSequence[event_dispatcher.CallbackT[event_dispatcher.EventT_co]],
    ]
    WaiterT = typing.Tuple[
        event_dispatcher.PredicateT[event_dispatcher.EventT_co], asyncio.Future[event_dispatcher.EventT_co]
    ]
    WaiterMapT = typing.MutableMapping[
        typing.Type[event_dispatcher.EventT_co], typing.MutableSet[WaiterT[event_dispatcher.EventT_co]]
    ]


def _default_predicate(_: event_dispatcher.EventT_inv) -> bool:
    return True


class EventManagerBase(event_dispatcher.EventDispatcher):
    """Provides functionality to consume and dispatch events.

    Specific event handlers should be in functions named `on_xxx` where `xxx`
    is the raw event name being dispatched in lower-case.
    """

    __slots__: typing.Sequence[str] = ("_app", "_intents", "_listeners", "_waiters")

    def __init__(self, app: traits.BotAware, intents: intents_.Intents) -> None:
        self._app = app
        self._intents = intents
        self._listeners: ListenerMapT[base_events.Event] = {}
        self._waiters: WaiterMapT[base_events.Event] = {}

    def consume_raw_event(
        self, shard: gateway_shard.GatewayShard, event_name: str, payload: data_binding.JSONObject
    ) -> None:
        try:
            callback = getattr(self, "on_" + event_name.lower())
        except AttributeError:
            _LOGGER.debug("ignoring unknown event %s:\n    %r", event_name, payload)
        else:
            asyncio.create_task(self._handle_dispatch(callback, shard, payload), name=f"dispatch {event_name}")

    def subscribe(
        self,
        event_type: typing.Type[event_dispatcher.EventT_co],
        callback: event_dispatcher.CallbackT[event_dispatcher.EventT_co],
        *,
        _nested: int = 0,
    ) -> event_dispatcher.CallbackT[event_dispatcher.EventT_co]:
        if not issubclass(event_type, base_events.Event):
            raise TypeError("Cannot subscribe to a non-Event type")

        if not inspect.iscoroutinefunction(callback):
            raise TypeError("Cannot subscribe a non-coroutine function callback")

        # `_nested` is used to show the correct source code snippet if an intent
        # warning is triggered.
        self._check_intents(event_type, _nested)

        if event_type not in self._listeners:
            self._listeners[event_type] = []

        _LOGGER.debug(
            "subscribing callback 'async def %s%s' to event-type %s.%s",
            getattr(callback, "__name__", "<anon>"),
            inspect.signature(callback),
            event_type.__module__,
            event_type.__qualname__,
        )

        self._listeners[event_type].append(callback)  # type: ignore[arg-type]

        return callback

    def _check_intents(self, event_type: typing.Type[event_dispatcher.EventT_co], nested: int) -> None:
        # Collection of combined bitfield combinations of intents that
        # could be enabled to receive this event.
        expected_intent_groups = base_events.get_required_intents_for(event_type)

        if expected_intent_groups:
            for expected_intent_group in expected_intent_groups:
                if (self._intents & expected_intent_group) == expected_intent_group:
                    break
            else:
                expected_intents_str = ", ".join(map(str, expected_intent_groups))

                warnings.warn(
                    f"You have tried to listen to {event_type.__name__}, but this will only ever be triggered if "
                    f"you enable one of the following intents: {expected_intents_str}.",
                    category=errors.MissingIntentWarning,
                    stacklevel=nested + 3,
                )

    def get_listeners(
        self,
        event_type: typing.Type[event_dispatcher.EventT_co],
        *,
        polymorphic: bool = True,
    ) -> typing.Collection[event_dispatcher.CallbackT[event_dispatcher.EventT_co]]:
        if polymorphic:
            listeners: typing.List[event_dispatcher.CallbackT[event_dispatcher.EventT_co]] = []
            for subscribed_event_type, subscribed_listeners in self._listeners.items():
                if issubclass(subscribed_event_type, event_type):
                    listeners += subscribed_listeners
            return listeners
        else:
            items = self._listeners.get(event_type)
            if items is not None:
                return items[:]

            return []

    def unsubscribe(
        self,
        event_type: typing.Type[event_dispatcher.EventT_co],
        callback: event_dispatcher.CallbackT[event_dispatcher.EventT_co],
    ) -> None:
        if event_type in self._listeners:
            _LOGGER.debug(
                "unsubscribing callback %s%s from event-type %s.%s",
                getattr(callback, "__name__", "<anon>"),
                inspect.signature(callback),
                event_type.__module__,
                event_type.__qualname__,
            )
            self._listeners[event_type].remove(callback)  # type: ignore[arg-type]
            if not self._listeners[event_type]:
                del self._listeners[event_type]

    def listen(
        self,
        event_type: typing.Optional[typing.Type[event_dispatcher.EventT_co]] = None,
    ) -> typing.Callable[
        [event_dispatcher.CallbackT[event_dispatcher.EventT_co]],
        event_dispatcher.CallbackT[event_dispatcher.EventT_co],
    ]:
        def decorator(
            callback: event_dispatcher.CallbackT[event_dispatcher.EventT_co],
        ) -> event_dispatcher.CallbackT[event_dispatcher.EventT_co]:
            nonlocal event_type

            signature = reflect.resolve_signature(callback)
            params = signature.parameters.values()

            if len(params) != 1:
                raise TypeError("Event listener must have exactly one parameter, the event object.")

            event_param = next(iter(params))

            if event_type is None:
                if event_param.annotation is event_param.empty:
                    raise TypeError("Must provide the event type in the @listen decorator or as a type hint!")

                event_type = event_param.annotation

            self.subscribe(event_type, callback, _nested=1)
            return callback

        return decorator

    def dispatch(self, event: event_dispatcher.EventT_inv) -> asyncio.Future[typing.Any]:
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
                for predicate, future in tuple(self._waiters[cls]):
                    try:
                        result = predicate(event)
                        if not result:
                            continue
                    except Exception as ex:
                        future.set_exception(ex)
                    else:
                        future.set_result(event)

                    waiter_set = self._waiters[cls]
                    waiter_set.remove((predicate, future))

        return asyncio.gather(*tasks) if tasks else aio.completed_future()

    def stream(
        self,
        event_type: typing.Type[event_dispatcher.EventT_co],
        /,
        timeout: typing.Union[float, int, None],
        limit: typing.Optional[int] = None,
    ) -> event_stream.Streamer[event_dispatcher.EventT_co]:
        self._check_intents(event_type, 1)
        return event_stream.EventStream(self._app, event_type, timeout=timeout, limit=limit)

    async def wait_for(
        self,
        event_type: typing.Type[event_dispatcher.EventT_co],
        /,
        timeout: typing.Union[float, int, None],
        predicate: typing.Optional[event_dispatcher.PredicateT[event_dispatcher.EventT_co]] = None,
    ) -> event_dispatcher.EventT_co:

        if predicate is None:
            predicate = _default_predicate

        self._check_intents(event_type, 1)

        future: asyncio.Future[event_dispatcher.EventT_co] = asyncio.get_event_loop().create_future()

        try:
            waiter_set = self._waiters[event_type]
        except KeyError:
            waiter_set = set()
            self._waiters[event_type] = waiter_set

        pair = (predicate, future)

        waiter_set.add(pair)  # type: ignore[arg-type]
        return await asyncio.wait_for(future, timeout=timeout)

    @staticmethod
    async def _handle_dispatch(
        callback: typing.Callable[
            [gateway_shard.GatewayShard, data_binding.JSONObject], typing.Coroutine[typing.Any, typing.Any, None]
        ],
        shard: gateway_shard.GatewayShard,
        payload: data_binding.JSONObject,
    ) -> None:
        try:
            await callback(shard, payload)
        except asyncio.CancelledError:
            # Skip cancelled errors, likely caused by the event loop being shut down.
            pass
        except BaseException as ex:
            asyncio.get_running_loop().call_exception_handler(
                {
                    "message": "Exception occurred in internal event dispatch conduit",
                    "exception": ex,
                    "task": asyncio.current_task(),
                }
            )

    async def _invoke_callback(
        self, callback: event_dispatcher.CallbackT[event_dispatcher.EventT_inv], event: event_dispatcher.EventT_inv
    ) -> None:
        try:
            await callback(event)
        except Exception as ex:
            # Skip the first frame in logs, we don't care for it.
            trio = type(ex), ex, ex.__traceback__.tb_next if ex.__traceback__ is not None else None

            if base_events.is_no_recursive_throw_event(event):
                _LOGGER.error(
                    "an exception occurred handling an event (%s), but it has been ignored",
                    type(event).__name__,
                    exc_info=trio,
                )
            else:
                exception_event = base_events.ExceptionEvent(
                    exception=ex,
                    failed_event=event,
                    failed_callback=callback,
                )

                log = _LOGGER.debug if self.get_listeners(type(exception_event), polymorphic=True) else _LOGGER.error
                log("an exception occurred handling an event (%s)", type(event).__name__, exc_info=trio)
                await self.dispatch(exception_event)
