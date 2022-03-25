# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021-present davfsa
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

__all__: typing.List[str] = ["filtered", "EventManagerBase", "EventStream"]

import asyncio
import inspect
import itertools
import logging
import typing
import warnings
import weakref

import attr

from hikari import errors
from hikari import iterators
from hikari.api import config
from hikari.api import event_manager as event_manager_
from hikari.events import base_events
from hikari.events import shard_events
from hikari.internal import aio
from hikari.internal import fast_protocol
from hikari.internal import reflect
from hikari.internal import ux

if typing.TYPE_CHECKING:
    import types

    from hikari import intents as intents_
    from hikari.api import event_factory as event_factory_
    from hikari.api import shard as gateway_shard
    from hikari.internal import data_binding

    ConsumerT = typing.Callable[
        [gateway_shard.GatewayShard, data_binding.JSONObject], typing.Coroutine[typing.Any, typing.Any, None]
    ]
    ListenerMapT = typing.Dict[
        typing.Type[event_manager_.EventT_co],
        typing.List[event_manager_.CallbackT[event_manager_.EventT_co]],
    ]
    WaiterT = typing.Tuple[
        typing.Optional[event_manager_.PredicateT[event_manager_.EventT_co]], asyncio.Future[event_manager_.EventT_co]
    ]
    WaiterMapT = typing.Dict[typing.Type[event_manager_.EventT_co], typing.Set[WaiterT[event_manager_.EventT_co]]]

    EventManagerBaseT = typing.TypeVar("EventManagerBaseT", bound="EventManagerBase")
    UnboundMethodT = typing.Callable[
        [EventManagerBaseT, gateway_shard.GatewayShard, data_binding.JSONObject],
        typing.Coroutine[typing.Any, typing.Any, None],
    ]
    _EventStreamT = typing.TypeVar("_EventStreamT", bound="EventStream[typing.Any]")

_LOGGER: typing.Final[logging.Logger] = logging.getLogger("hikari.event_manager")


@typing.runtime_checkable
class _FilteredMethodT(fast_protocol.FastProtocolChecking, typing.Protocol):
    __slots__: typing.Sequence[str] = ()

    async def __call__(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject, /) -> None:
        raise NotImplementedError

    @property
    def __cache_components__(self) -> config.CacheComponents:
        raise NotImplementedError

    @property
    def __events_bitmask__(self) -> int:
        raise NotImplementedError


def _generate_weak_listener(
    reference: weakref.WeakMethod[typing.Any],
) -> typing.Callable[[event_manager_.EventT], typing.Coroutine[typing.Any, typing.Any, None]]:
    async def call_weak_method(event: event_manager_.EventT) -> None:
        method = reference()
        if method is None:
            raise TypeError(
                "dead weak referenced subscriber method cannot be executed, try actually closing your event streamers"
            )

        await method(event)

    return call_weak_method


class EventStream(event_manager_.EventStream[event_manager_.EventT]):
    """An implementation of an event `EventStream` class.

    !!! note
        While calling `EventStream.filter` on an active "opened" event stream
        will return a wrapping lazy iterator, calling it on an inactive "closed"
        event stream will return the event stream and add the given predicates
        to the streamer.
    """

    __slots__: typing.Sequence[str] = (
        "__weakref__",
        "_active",
        "_event",
        "_event_manager",
        "_event_type",
        "_filters",
        "_limit",
        "_queue",
        "_registered_listener",
        "_timeout",
    )

    __weakref__: typing.Optional[weakref.ref[EventStream[event_manager_.EventT]]]

    def __init__(
        self,
        event_manager: event_manager_.EventManager,
        event_type: typing.Type[event_manager_.EventT],
        *,
        timeout: typing.Union[float, int, None],
        limit: typing.Optional[int] = None,
    ) -> None:
        self._active = False
        self._event: typing.Optional[asyncio.Event] = None
        self._event_manager = event_manager
        self._event_type = event_type
        self._filters: iterators.All[event_manager_.EventT] = iterators.All(())
        self._limit = limit
        self._queue: typing.List[event_manager_.EventT] = []
        self._registered_listener: typing.Optional[
            typing.Callable[[event_manager_.EventT], typing.Coroutine[typing.Any, typing.Any, None]]
        ] = None
        # The registered wrapping function for the weak ref to this class's _listener method.
        self._timeout = timeout

    # These are only included at runtime in-order to avoid the model being typed as an asynchronous context manager.
    if not typing.TYPE_CHECKING:

        async def __aenter__(self: _EventStreamT) -> _EventStreamT:
            # This is sync only.
            warnings.warn(
                "Using EventStream as an async context manager has been deprecated since 2.0.0.dev104. "
                "Please use it as a synchronous context manager (e.g. with bot.stream(...)) instead.",
                category=DeprecationWarning,
                stacklevel=2,
            )

            self.open()
            return self

        async def __aexit__(
            self,
            exc_type: typing.Optional[typing.Type[BaseException]],
            exc: typing.Optional[BaseException],
            exc_tb: typing.Optional[types.TracebackType],
        ) -> None:
            self.close()

    def __enter__(self: _EventStreamT) -> _EventStreamT:
        self.open()
        return self

    def __exit__(
        self,
        exc_type: typing.Optional[typing.Type[BaseException]],
        exc_val: typing.Optional[BaseException],
        exc_tb: typing.Optional[types.TracebackType],
    ) -> None:
        self.close()

    async def __anext__(self) -> event_manager_.EventT:
        if not self._active:
            raise TypeError("stream must be started with before entering it")

        while not self._queue:
            if not self._event:
                self._event = asyncio.Event()

            try:
                await asyncio.wait_for(self._event.wait(), timeout=self._timeout)
            except asyncio.TimeoutError:
                raise StopAsyncIteration from None

            self._event.clear()

        return self._queue.pop(0)

    def __await__(self) -> typing.Generator[None, None, typing.Sequence[event_manager_.EventT]]:
        return self._await_all().__await__()

    def __del__(self) -> None:
        # For the sake of protecting highly intelligent people who forget to close this, we register the event listener
        # with a weakref then try to close this on deletion. While this may lead to their consoles being spammed, this
        # is a small price to pay as it'll be way more obvious what's wrong than if we just left them with a vague
        # ominous memory leak.
        if self._active:
            _LOGGER.warning("active %r streamer fell out of scope before being closed", self._event_type.__name__)
            self.close()

    async def _await_all(self) -> typing.Sequence[event_manager_.EventT]:
        self.open()
        result = [event async for event in self]
        self.close()
        return result

    async def _listener(self, event: event_manager_.EventT) -> None:
        if not self._filters(event) or (self._limit is not None and len(self._queue) >= self._limit):
            return

        self._queue.append(event)
        if self._event:
            self._event.set()

    def close(self) -> None:
        if self._active and self._registered_listener is not None:
            try:
                self._event_manager.unsubscribe(self._event_type, self._registered_listener)
            except ValueError:
                pass

            self._registered_listener = None

        self._active = False

    def filter(
        self: _EventStreamT,
        *predicates: typing.Union[typing.Tuple[str, typing.Any], typing.Callable[[event_manager_.EventT], bool]],
        **attrs: typing.Any,
    ) -> _EventStreamT:
        filter_ = self._map_predicates_and_attr_getters("filter", *predicates, **attrs)
        if self._active:
            self._queue = [entry for entry in self._queue if filter_(entry)]

        self._filters |= filter_
        return self

    def open(self) -> None:
        if not self._active:
            # For the sake of protecting highly intelligent people who forget to close this, we register the event
            # listener with a weakref then try to close this on deletion. While this may lead to their consoles being
            # spammed, this is a small price to pay as it'll be way more obvious what's wrong than if we just left them
            # with a vague ominous memory leak.
            reference = weakref.WeakMethod(self._listener)
            listener = _generate_weak_listener(reference)
            self._registered_listener = listener
            self._event_manager.subscribe(self._event_type, listener)
            self._active = True


def _assert_is_listener(parameters: typing.Iterator[inspect.Parameter], /) -> None:
    if next(parameters, None) is None:
        raise TypeError("Event listener must have one positional argument for the event object.")

    if any(param.default is inspect.Parameter.empty for param in parameters):
        raise TypeError("Only the first argument for a listener can be required, the event argument.")


def filtered(
    event_types: typing.Union[typing.Type[base_events.Event], typing.Sequence[typing.Type[base_events.Event]]],
    cache_components: config.CacheComponents = config.CacheComponents.NONE,
    /,
) -> typing.Callable[[UnboundMethodT[EventManagerBaseT]], UnboundMethodT[EventManagerBaseT]]:
    """Add metadata to a consumer method to indicate when it should be unmarshalled and dispatched.

    Parameters
    ----------
    event_types
        Types of the events this raw consumer method may dispatch.
        This may either be a singular type of a sequence of types.

    Other Parameters
    ----------------
    cache_components : hikari.api.config.CacheComponents
        Bitfield of the cache components this event may make altering calls to.
        This defaults to `hikari.api.config.CacheComponents.NONE`.
    """
    if isinstance(event_types, typing.Sequence):
        # dict.fromkeys is used to remove any duplicate entries here
        event_types = tuple(dict.fromkeys(itertools.chain.from_iterable(e.dispatches() for e in event_types)))

    else:
        event_types = event_types.dispatches()

    bitmask = 0
    for event_type in event_types:
        bitmask |= event_type.bitmask()

    # https://github.com/python/mypy/issues/2087
    def decorator(method: UnboundMethodT[EventManagerBaseT], /) -> UnboundMethodT[EventManagerBaseT]:
        method.__cache_components__ = cache_components  # type: ignore[attr-defined]
        method.__events_bitmask__ = bitmask  # type: ignore[attr-defined]
        assert isinstance(method, _FilteredMethodT), "Incorrect attribute(s) set for a filtered method"
        return method  # type: ignore[unreachable]

    return decorator


@attr.define(weakref_slot=False)
class _Consumer:
    callback: ConsumerT = attr.field(hash=True)
    """The callback function for this consumer."""

    events_bitmask: int = attr.field()
    """The registered events bitmask."""

    is_caching: bool = attr.field()
    """Cached value of whether or not this consumer is making cache calls in the current env."""

    listener_group_count: int = attr.field(init=False, default=0)
    """The number of listener groups registered to this consumer."""

    waiter_group_count: int = attr.field(init=False, default=0)
    """The number of waiters groups registered to this consumer."""

    @property
    def is_enabled(self) -> bool:
        return self.is_caching or self.listener_group_count > 0 or self.waiter_group_count > 0


class EventManagerBase(event_manager_.EventManager):
    """Provides functionality to consume and dispatch events.

    Specific event handlers should be in functions named `on_xxx` where `xxx`
    is the raw event name being dispatched in lower-case.
    """

    __slots__: typing.Sequence[str] = (
        "_consumers",
        "_event_factory",
        "_intents",
        "_listeners",
        "_waiters",
    )

    def __init__(
        self,
        event_factory: event_factory_.EventFactory,
        intents: intents_.Intents,
        *,
        cache_components: config.CacheComponents = config.CacheComponents.NONE,
    ) -> None:
        self._consumers: typing.Dict[str, _Consumer] = {}
        self._event_factory = event_factory
        self._intents = intents
        self._listeners: ListenerMapT[base_events.Event] = {}
        self._waiters: WaiterMapT[base_events.Event] = {}

        for name, member in inspect.getmembers(self):
            if name.startswith("on_"):
                event_name = name[3:]
                if isinstance(member, _FilteredMethodT):
                    caching = (member.__cache_components__ & cache_components) != 0

                    self._consumers[event_name] = _Consumer(member, member.__events_bitmask__, caching)

                else:
                    self._consumers[event_name] = _Consumer(member, -1, cache_components != cache_components.NONE)

    def _increment_listener_group_count(
        self, event_type: typing.Type[base_events.Event], count: typing.Literal[-1, 1]
    ) -> None:
        event_bitmask = event_type.bitmask()
        for consumer in self._consumers.values():
            if (consumer.events_bitmask & event_bitmask) == event_bitmask:
                consumer.listener_group_count += count

    def _increment_waiter_group_count(
        self, event_type: typing.Type[base_events.Event], count: typing.Literal[-1, 1]
    ) -> None:
        event_bitmask = event_type.bitmask()
        for consumer in self._consumers.values():
            if (consumer.events_bitmask & event_bitmask) == event_bitmask:
                consumer.waiter_group_count += count

    def _enabled_for_event(self, event_type: typing.Type[base_events.Event], /) -> bool:
        for cls in event_type.dispatches():
            if cls in self._listeners or cls in self._waiters:
                return True

        return False

    def consume_raw_event(
        self, event_name: str, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> None:
        if self._enabled_for_event(shard_events.ShardPayloadEvent):
            payload_event = self._event_factory.deserialize_shard_payload_event(shard, payload, name=event_name)
            self.dispatch(payload_event)
        consumer = self._consumers[event_name.lower()]
        asyncio.create_task(self._handle_dispatch(consumer, shard, payload), name=f"dispatch {event_name}")

    def subscribe(
        self,
        event_type: typing.Type[event_manager_.EventT_co],
        callback: event_manager_.CallbackT[event_manager_.EventT_co],
        *,
        _nested: int = 0,
    ) -> None:
        if not inspect.isclass(event_type) or not issubclass(event_type, base_events.Event):
            raise TypeError("Cannot subscribe to a non-Event type")

        if not inspect.iscoroutinefunction(callback):
            raise TypeError("Cannot subscribe a non-coroutine function callback")

        # `_nested` is used to show the correct source code snippet if an intent
        # warning is triggered.
        self._check_intents(event_type, _nested)

        _LOGGER.debug(
            "subscribing callback 'async def %s%s' to event-type %s.%s",
            getattr(callback, "__name__", "<anon>"),
            inspect.signature(callback),
            event_type.__module__,
            event_type.__qualname__,
        )

        try:
            self._listeners[event_type].append(callback)  # type: ignore[arg-type]
        except KeyError:
            self._listeners[event_type] = [callback]  # type: ignore[list-item]
            self._increment_listener_group_count(event_type, 1)

    def _check_intents(self, event_type: typing.Type[event_manager_.EventT_co], nested: int) -> None:
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
        event_type: typing.Type[event_manager_.EventT_co],
        /,
        *,
        polymorphic: bool = True,
    ) -> typing.Collection[event_manager_.CallbackT[event_manager_.EventT_co]]:
        if polymorphic:
            listeners: typing.List[event_manager_.CallbackT[event_manager_.EventT_co]] = []
            for event in event_type.dispatches():
                if subscribed_listeners := self._listeners.get(event):
                    listeners.extend(subscribed_listeners)

            return listeners

        if items := self._listeners.get(event_type):
            return items.copy()

        return []

    def unsubscribe(
        self,
        event_type: typing.Type[event_manager_.EventT_co],
        callback: event_manager_.CallbackT[event_manager_.EventT_co],
    ) -> None:
        if listeners := self._listeners.get(event_type):
            _LOGGER.debug(
                "unsubscribing callback %s%s from event-type %s.%s",
                getattr(callback, "__name__", "<anon>"),
                inspect.signature(callback),
                event_type.__module__,
                event_type.__qualname__,
            )
            listeners.remove(callback)  # type: ignore[arg-type]
            if not listeners:
                del self._listeners[event_type]
                self._increment_listener_group_count(event_type, -1)

    def listen(
        self,
        event_type: typing.Optional[typing.Type[event_manager_.EventT_co]] = None,
    ) -> typing.Callable[
        [event_manager_.CallbackT[event_manager_.EventT_co]], event_manager_.CallbackT[event_manager_.EventT_co]
    ]:
        def decorator(
            callback: event_manager_.CallbackT[event_manager_.EventT_co],
        ) -> event_manager_.CallbackT[event_manager_.EventT_co]:
            nonlocal event_type

            # Avoid resolving forward references in the function's signature if
            # event_type was explicitly provided as this may lead to errors.
            if event_type is not None:
                _assert_is_listener(iter(inspect.signature(callback).parameters.values()))

            else:
                signature = reflect.resolve_signature(callback)
                params = signature.parameters.values()
                _assert_is_listener(iter(params))
                event_param = next(iter(params))

                if event_param.annotation is event_param.empty:
                    raise TypeError("Must provide the event type in the @listen decorator or as a type hint!")

                event_type = event_param.annotation

            self.subscribe(event_type, callback, _nested=1)
            return callback

        return decorator

    def dispatch(self, event: event_manager_.EventT_inv) -> asyncio.Future[typing.Any]:
        if not isinstance(event, base_events.Event):
            raise TypeError(f"Events must be subclasses of {base_events.Event.__name__}, not {type(event).__name__}")

        tasks: typing.List[typing.Coroutine[None, typing.Any, None]] = []

        for cls in event.dispatches():
            if listeners := self._listeners.get(cls):
                for callback in listeners:
                    tasks.append(self._invoke_callback(callback, event))

            if cls not in self._waiters:
                continue

            waiter_set = self._waiters[cls]
            for waiter in tuple(waiter_set):
                predicate, future = waiter
                if not future.done():
                    try:
                        if predicate and not predicate(event):
                            continue
                    except Exception as ex:
                        future.set_exception(ex)
                    else:
                        future.set_result(event)

                waiter_set.remove(waiter)

            if not waiter_set:
                del self._waiters[cls]
                self._increment_waiter_group_count(cls, -1)

        return asyncio.gather(*tasks) if tasks else aio.completed_future()

    def stream(
        self,
        event_type: typing.Type[event_manager_.EventT_co],
        /,
        timeout: typing.Union[float, int, None],
        limit: typing.Optional[int] = None,
    ) -> event_manager_.EventStream[event_manager_.EventT_co]:
        self._check_intents(event_type, 1)
        return EventStream(self, event_type, timeout=timeout, limit=limit)

    async def wait_for(
        self,
        event_type: typing.Type[event_manager_.EventT_co],
        /,
        timeout: typing.Union[float, int, None],
        predicate: typing.Optional[event_manager_.PredicateT[event_manager_.EventT_co]] = None,
    ) -> event_manager_.EventT_co:
        self._check_intents(event_type, 1)

        future: asyncio.Future[event_manager_.EventT_co] = asyncio.get_running_loop().create_future()

        try:
            waiter_set = self._waiters[event_type]
        except KeyError:
            waiter_set = set()
            self._waiters[event_type] = waiter_set
            self._increment_waiter_group_count(event_type, 1)

        pair = (predicate, future)

        waiter_set.add(pair)  # type: ignore[arg-type]
        try:
            return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            waiter_set.remove(pair)  # type: ignore[arg-type]
            if not waiter_set:
                del self._waiters[event_type]
                self._increment_waiter_group_count(event_type, -1)

            raise

    async def _handle_dispatch(
        self,
        consumer: _Consumer,
        shard: gateway_shard.GatewayShard,
        payload: data_binding.JSONObject,
    ) -> None:
        if not consumer.is_enabled:
            name = consumer.callback.__name__
            _LOGGER.log(
                ux.TRACE, "Skipping raw dispatch for %s due to lack of any registered listeners or cache need", name
            )
            return

        try:
            await consumer.callback(shard, payload)
        except asyncio.CancelledError:
            # Skip cancelled errors, likely caused by the event loop being shut down.
            pass
        except errors.UnrecognisedEntityError:
            _LOGGER.debug("Event referenced an unrecognised entity, discarding")
        except BaseException as ex:
            asyncio.get_running_loop().call_exception_handler(
                {
                    "message": "Exception occurred in raw event dispatch conduit",
                    "exception": ex,
                    "task": asyncio.current_task(),
                }
            )

    async def _invoke_callback(
        self, callback: event_manager_.CallbackT[event_manager_.EventT_inv], event: event_manager_.EventT_inv
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
