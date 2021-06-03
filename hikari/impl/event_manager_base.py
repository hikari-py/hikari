# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021 davfsa
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

from hikari import config
from hikari import errors
from hikari import iterators
from hikari import undefined
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

_LOGGER: typing.Final[logging.Logger] = logging.getLogger("hikari.event_manager")

if typing.TYPE_CHECKING:
    ConsumerT = typing.Callable[
        [gateway_shard.GatewayShard, data_binding.JSONObject], typing.Coroutine[typing.Any, typing.Any, None]
    ]
    ListenerMapT = typing.Dict[
        typing.Type[event_manager_.EventT_co],
        typing.List[event_manager_.CallbackT[event_manager_.EventT_co]],
    ]
    WaiterT = typing.Tuple[
        event_manager_.PredicateT[event_manager_.EventT_co], asyncio.Future[event_manager_.EventT_co]
    ]
    WaiterMapT = typing.Dict[typing.Type[event_manager_.EventT_co], typing.Set[WaiterT[event_manager_.EventT_co]]]

    EventManagerBaseT = typing.TypeVar("EventManagerBaseT", bound="EventManagerBase")
    UnboundMethodT = typing.Callable[
        [EventManagerBaseT, gateway_shard.GatewayShard, data_binding.JSONObject],
        typing.Coroutine[typing.Any, typing.Any, None],
    ]


@typing.runtime_checkable
class _FilteredMethodT(fast_protocol.FastProtocolChecking, typing.Protocol):
    async def __call__(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject, /) -> None:
        raise NotImplementedError

    @property
    def __cache_components__(self) -> config.CacheComponents:
        raise NotImplementedError

    @property
    def __event_types__(self) -> typing.Sequence[typing.Type[base_events.Event]]:
        raise NotImplementedError

def _generate_weak_listener(
    reference: weakref.WeakMethod,
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
        "_event_manager",
        "_event_type",
        "_filters",
        "_queue",
        "_registered_listener",
        "_timeout",
    )

    def __init__(
        self,
        event_manager: event_manager_.EventManager,
        event_type: typing.Type[event_manager_.EventT],
        *,
        timeout: typing.Union[float, int, None],
        limit: typing.Optional[int] = None,
    ) -> None:
        self._event_manager = event_manager
        self._active = False
        self._event_type = event_type
        self._filters: iterators.All[event_manager_.EventT] = iterators.All(())
        # We accept `None` to represent unlimited here to be consistent with how `None` is already used to represent
        # unlimited for timeout in other places.
        self._queue: asyncio.Queue[event_manager_.EventT] = asyncio.Queue(limit or 0)
        self._registered_listener: typing.Optional[
            typing.Callable[[event_manager_.EventT], typing.Coroutine[typing.Any, typing.Any, None]]
        ] = None
        # The registered wrapping function for the weak ref to this class's _listener method.
        self._timeout = timeout

    async def __aenter__(self) -> EventStream[event_manager_.EventT]:
        await self.open()
        return self

    async def __aexit__(
        self,
        exc_type: typing.Optional[typing.Type[BaseException]],
        exc: typing.Optional[BaseException],
        exc_tb: typing.Optional[types.TracebackType],
    ) -> None:
        await self.close()

    # These are only included at runtime in-order to avoid the model being typed as a synchronous context manager.
    if not typing.TYPE_CHECKING:

        def __enter__(self) -> typing.NoReturn:
            # This is async only.
            cls = type(self)
            raise TypeError(f"{cls.__module__}.{cls.__qualname__} is async-only, did you mean 'async with'?") from None

        def __exit__(
            self,
            exc_type: typing.Optional[typing.Type[Exception]],
            exc_val: typing.Optional[Exception],
            exc_tb: typing.Optional[types.TracebackType],
        ) -> None:
            return None

    async def __anext__(self) -> event_manager_.EventT:
        if not self._active:
            raise TypeError("stream must be started with `async with` before entering it")

        try:
            return await asyncio.wait_for(self._queue.get(), timeout=self._timeout)
        except asyncio.TimeoutError:
            raise StopAsyncIteration from None

    def __await__(self) -> typing.Generator[None, None, typing.Sequence[event_manager_.EventT]]:
        return self._await_all().__await__()

    def __del__(self) -> None:
        # For the sake of protecting highly intelligent people who forget to close this, we register the event listener
        # with a weakref then try to close this on deletion. While this may lead to their consoles being spammed, this
        # is a small price to pay as it'll be way more obvious what's wrong than if we just left them with a vague
        # ominous memory leak.
        if self._active:
            _LOGGER.warning("active %r streamer fell out of scope before being closed", self._event_type.__name__)
            try:
                asyncio.ensure_future(self.close())
            except RuntimeError:
                pass

    async def _await_all(self) -> typing.Sequence[event_manager_.EventT]:
        await self.open()
        result = [event async for event in self]
        await self.close()
        return result

    async def _listener(self, event: event_manager_.EventT) -> None:
        if not self._filters(event):
            return

        try:
            self._queue.put_nowait(event)
        except asyncio.QueueFull:
            pass

    async def close(self) -> None:
        if self._active and self._registered_listener is not None:
            try:
                self._event_manager.unsubscribe(self._event_type, self._registered_listener)
            except ValueError:
                pass

            self._registered_listener = None

        self._active = False

    def filter(
        self,
        *predicates: typing.Union[typing.Tuple[str, typing.Any], typing.Callable[[event_manager_.EventT], bool]],
        **attrs: typing.Any,
    ) -> typing.Union[EventStream[event_manager_.EventT], iterators.LazyIterator[event_manager_.EventT]]:
        if self._active:
            return super().filter(*predicates, **attrs)

        self._filters |= self._map_predicates_and_attr_getters("filter", *predicates, **attrs)
        return self

    async def open(self) -> None:
        if not self._active:
            # For the sake of protecting highly intelligent people who forget to close this, we register the event
            # listener with a weakref then try to close this on deletion. While this may lead to their consoles being
            # spammed, this is a small price to pay as it'll be way more obvious what's wrong than if we just left them
            # with a vague ominous memory leak.
            reference = weakref.WeakMethod(self._listener)  # type: ignore[arg-type]
            listener = _generate_weak_listener(reference)
            self._registered_listener = listener
            self._event_manager.subscribe(self._event_type, listener)
            self._active = True


def _default_predicate(_: event_manager_.EventT_inv) -> bool:
    return True


def _assert_is_listener(parameters: typing.Iterator[inspect.Parameter], /) -> None:
    if next(parameters, None) is None:
        raise TypeError("Event listener must have one positional argument for the event object.")

    if any(param.default is not inspect.Parameter.empty for param in parameters):
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
    cache_components : hikari.config.CacheComponents
        Bitfield of the cache components this event may make altering calls to.
        This defaults to `hikari.config.CacheComponents.NONE`.
    """
    if isinstance(event_types, typing.Sequence):
        # dict.fromkeys is used to remove any duplicate entries here
        event_types = tuple(dict.fromkeys(itertools.chain.from_iterable(e.dispatches() for e in event_types)))

    else:
        event_types = event_types.dispatches()

    def decorator(method: UnboundMethodT[EventManagerBaseT], /) -> UnboundMethodT[EventManagerBaseT]:
        method.__cache_components__ = cache_components  # type: ignore[attr-defined]
        method.__event_types__ = event_types  # type: ignore[attr-defined]
        assert isinstance(method, _FilteredMethodT), "Incorrect attribute(s) set for a filtered method"
        return method  # type: ignore[unreachable]

    return decorator


@attr.frozen()
class _Consumer:
    callback: ConsumerT = attr.ib()
    """The callback function for this consumer."""

    cache_components: undefined.UndefinedOr[config.CacheComponents] = attr.ib()
    """Bitfield of the cache components this consumer makes modifying calls to, if set."""

    event_types: undefined.UndefinedOr[typing.Sequence[typing.Type[base_events.Event]]] = attr.ib()
    """A sequence of the types of events this consumer dispatches to, if set."""

    def __attrs_post_init__(self) -> None:
        # Letting only one be UNDEFINED just doesn't make sense as either being undefined leads to filtering being
        # skipped all together making the other redundant.
        if undefined.count(self.cache_components, self.event_types) == 1:
            raise ValueError("cache_components and event_types must both either be undefined or defined")


class EventManagerBase(event_manager_.EventManager):
    """Provides functionality to consume and dispatch events.

    Specific event handlers should be in functions named `on_xxx` where `xxx`
    is the raw event name being dispatched in lower-case.
    """

    __slots__: typing.Sequence[str] = ("_event_factory", "_intents", "_consumers", "_enabled_consumers_cache", "_listeners", "_waiters")

    def __init__(self, event_factory: event_factory_.EventFactory, intents: intents_.Intents) -> None:
        self._dispatches_for_cache: typing.Dict[_Consumer, bool] = {}
        self._consumers: typing.Dict[str, _Consumer] = {}
        self._enabled_consumers_cache: typing.Dict[_Consumer, bool] = {}
        self._event_factory = event_factory
        self._intents = intents
        self._listeners: ListenerMapT[base_events.Event] = {}
        self._waiters: WaiterMapT[base_events.Event] = {}

        for name, member in inspect.getmembers(self):
            if name.startswith("on_"):
                event_name = name[3:]
                if isinstance(member, _FilteredMethodT):
                    self._consumers[event_name] = _Consumer(member, member.__cache_components__, member.__event_types__)

                else:
                    self._consumers[event_name] = _Consumer(member, undefined.UNDEFINED, undefined.UNDEFINED)

    def _clear_enabled_cache(self) -> None:
        self._enabled_consumers_cache = {}

    def _enabled_for_event(self, event_type: typing.Type[base_events.Event], /) -> bool:
        for cls in event_type.dispatches():
            if cls in self._listeners or cls in self._waiters:
                return True

        return False

    def _enabled_for_consumer(self, consumer: _Consumer, /) -> bool:
        # If undefined then we can only assume that this may link to registered listeners.
        if consumer.event_types is undefined.UNDEFINED:
            return True

        # If event_types is not UNDEFINED then cache_components shouldn't ever be undefined.
        assert consumer.cache_components is not undefined.UNDEFINED
        if (cached_value := self._enabled_consumers_cache.get(consumer)) is True:
            return True

        if cached_value is None:
            # The behaviour here where an empty sequence for event_types will lead to this always
            # being skipped unless there's a relevant enabled cache resource is intended behaviour.
            for event_type in consumer.event_types:
                if event_type in self._listeners or event_type in self._waiters:
                    self._enabled_consumers_cache[consumer] = True
                    return True

            self._enabled_consumers_cache[consumer] = False

        # If cache_components is NONE then it doesn't make any altering state calls.
        return (
            consumer.cache_components != config.CacheComponents.NONE
            and (consumer.cache_components & self._app.cache.settings.components) != 0
        )

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
        if not issubclass(event_type, base_events.Event):
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
            self._clear_enabled_cache()

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
            listeners: typing.List[event_manager.CallbackT[event_manager.EventT_co]] = []
            for cls in event_type.dispatches():
                listeners.extend(self._listeners[cls])

            return listeners

        else:
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
                self._clear_enabled_cache()

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
        clear_cache = False

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
                        result = predicate(event)
                        if not result:
                            continue
                    except Exception as ex:
                        future.set_exception(ex)
                    else:
                        future.set_result(event)

                waiter_set.remove(waiter)

            if not waiter_set:
                del self._waiters[cls]
                clear_cache = True

        if clear_cache:
            self._clear_enabled_cache()

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
        if predicate is None:
            predicate = _default_predicate

        self._check_intents(event_type, 1)

        future: asyncio.Future[event_manager_.EventT_co] = asyncio.get_running_loop().create_future()

        try:
            waiter_set = self._waiters[event_type]
        except KeyError:
            self._clear_enabled_cache()
            waiter_set = set()
            self._waiters[event_type] = waiter_set

        pair = (predicate, future)

        waiter_set.add(pair)  # type: ignore[arg-type]
        try:
            return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            waiter_set.remove(pair)  # type: ignore[arg-type]
            if not waiter_set:
                del self._waiters[event_type]
                self._clear_enabled_cache()

            raise

    async def _handle_dispatch(
        self,
        consumer: _Consumer,
        shard: gateway_shard.GatewayShard,
        payload: data_binding.JSONObject,
    ) -> None:
        if not self._enabled_for_consumer(consumer):
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
