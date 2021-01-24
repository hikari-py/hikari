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
"""Core interface for components that manage events in the library."""
from __future__ import annotations

__all__: typing.List[str] = ["EventManager"]

import abc
import asyncio
import typing

if typing.TYPE_CHECKING:
    from hikari import event_stream
    from hikari.api import shard as gateway_shard
    from hikari.events import base_events
    from hikari.internal import data_binding

    EventT_co = typing.TypeVar("EventT_co", bound=base_events.Event, covariant=True)
    EventT_inv = typing.TypeVar("EventT_inv", bound=base_events.Event)
    PredicateT = typing.Callable[[EventT_co], bool]
    CallbackT = typing.Callable[[EventT_inv], typing.Coroutine[typing.Any, typing.Any, None]]
    ConsumerT = typing.Callable[
        [gateway_shard.GatewayShard, data_binding.JSONObject], typing.Coroutine[typing.Any, typing.Any, None]
    ]


class EventManager(abc.ABC):
    """Base interface for event manager implementations.

    This is a listener of a `hikari.events.base_events.Event` object and
    consumer of raw event payloads, and is expected to invoke one or more
    corresponding event listeners where appropriate.
    """

    __slots__: typing.Sequence[str] = ()

    @abc.abstractmethod
    def consume_raw_event(
        self, event_name: str, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> None:
        """Consume a raw event.

        Parameters
        ----------
        event_name : str
            The case-insensitive name of the event being triggered.
        shard : hikari.api.shard.GatewayShard
            Object of the shard that received this event.
        payload : hikari.internal.data_binding.JSONObject
            Payload of the event being triggered.

        Raises
        ------
        builtins.LookupError
            If there is no consumer for the event.
        """

    @abc.abstractmethod
    def dispatch(self, event: EventT_inv) -> asyncio.Future[typing.Any]:
        """Dispatch an event.

        Parameters
        ----------
        event : hikari.events.base_events.Event
            The event to dispatch.

        Example
        -------
        We can dispatch custom events by first defining a class that
        derives from `hikari.events.base_events.Event`.

        ```py
        import attr

        from hikari.traits import RESTAware
        from hikari.events.base_events import Event
        from hikari.users import User
        from hikari.snowflakes import Snowflake

        @attr.s()
        class EveryoneMentionedEvent(Event):
            app: RESTAware = attr.ib()

            author: User = attr.ib()
            '''The user who mentioned everyone.'''

            content: str = attr.ib()
            '''The message that was sent.'''

            message_id: Snowflake = attr.ib()
            '''The message ID.'''

            channel_id: Snowflake = attr.ib()
            '''The channel ID.'''
        ```

        We can then dispatch our event as we see fit.

        ```py
        from hikari.events.messages import MessageCreateEvent

        @bot.listen(MessageCreateEvent)
        async def on_message(event):
            if "@everyone" in event.content or "@here" in event.content:
                event = EveryoneMentionedEvent(
                    author=event.author,
                    content=event.content,
                    message_id=event.id,
                    channel_id=event.channel_id,
                )

                bot.dispatch(event)
        ```

        This event can be listened to elsewhere by subscribing to it with
        `EventManager.subscribe`.

        ```py
        @bot.listen(EveryoneMentionedEvent)
        async def on_everyone_mentioned(event):
            print(event.user, "just pinged everyone in", event.channel_id)
        ```

        Returns
        -------
        asyncio.Future[typing.Any]
            A future that can be optionally awaited. If awaited, the future
            will complete once all corresponding event listeners have been
            invoked. If not awaited, this will schedule the dispatch of the
            events in the background for later.

        See Also
        --------
        Subscribe: `hikari.api.event_manager.EventManager.subscribe`
        Stream: `hikari.api.event_manager.EventManager.stream`
        Wait for: `hikari.api.event_manager.EventManager.wait_for`
        """

    # Yes, this is not generic. The reason for this is MyPy complains about
    # using ABCs that are not concrete in generic types passed to functions.
    # For the sake of UX, I will check this at runtime instead and let the
    # user use a static type checker.
    @abc.abstractmethod
    def subscribe(self, event_type: typing.Type[typing.Any], callback: CallbackT[typing.Any]) -> CallbackT[typing.Any]:
        """Subscribe a given callback to a given event type.

        Parameters
        ----------
        event_type : typing.Type[T]
            The event type to listen for. This will also listen for any
            subclasses of the given type.
            `T` must be a subclass of `hikari.events.base_events.Event`.
        callback
            Must be a coroutine function to invoke. This should
            consume an instance of the given event, or an instance of a valid
            subclass if one exists. Any result is discarded.

        Example
        -------
        The following demonstrates subscribing a callback to message creation
        events.

        ```py
        from hikari.events.messages import MessageCreateEvent

        async def on_message(event):
            ...

        bot.subscribe(MessageCreateEvent, on_message)
        ```

        Returns
        -------
        typing.Callable[[T], typing.Coroutine[typing.Any, typing.Any, builtins.None]
            The event callback that was passed in.

        See Also
        --------
        Listen: `hikari.api.event_manager.EventManager.listen`
        Stream: `hikari.api.event_manager.EventManager.stream`
        Wait for: `hikari.api.event_manager.EventManager.wait_for`
        """

    # Yes, this is not generic. The reason for this is MyPy complains about
    # using ABCs that are not concrete in generic types passed to functions.
    # For the sake of UX, I will check this at runtime instead and let the
    # user use a static type checker.
    @abc.abstractmethod
    def unsubscribe(self, event_type: typing.Type[typing.Any], callback: CallbackT[typing.Any]) -> None:
        """Unsubscribe a given callback from a given event type, if present.

        Parameters
        ----------
        event_type : typing.Type[T]
            The event type to unsubscribe from. This must be the same exact
            type as was originally subscribed with to be removed correctly.
            `T` must derive from `hikari.events.base_events.Event`.
        callback
            The callback to unsubscribe.

        Example
        -------
        The following demonstrates unsubscribing a callback from a message
        creation event.

        ```py
        from hikari.events.messages import MessageCreateEvent

        async def on_message(event):
            ...

        bot.unsubscribe(MessageCreateEvent, on_message)
        ```
        """

    @abc.abstractmethod
    def get_listeners(
        self,
        event_type: typing.Type[EventT_co],
        *,
        polymorphic: bool = True,
    ) -> typing.Collection[CallbackT[EventT_co]]:
        """Get the listeners for a given event type, if there are any.

        Parameters
        ----------
        event_type : typing.Type[T]
            The event type to look for.
            `T` must be a subclass of `hikari.events.base_events.Event`.
        polymorphic : builtins.bool
            If `builtins.True`, this will also return the listeners of the
            subclasses of the given event type. If `builtins.False`, then
            only listeners for this class specifically are returned. The
            default is `builtins.True`.

        Returns
        -------
        typing.Collection[typing.Callable[[T], typing.Coroutine[typing.Any, typing.Any, builtins.None]]
            A copy of the collection of listeners for the event. Will return
            an empty collection if nothing is registered.

            `T` must be a subclass of `hikari.events.base_events.Event`.

        See Also
        --------
        Has listener: `hikari.api.event_manager.EventManager.has_listener`
        """

    @abc.abstractmethod
    def listen(
        self,
        event_type: typing.Optional[typing.Type[EventT_co]] = None,
    ) -> typing.Callable[[CallbackT[EventT_co]], CallbackT[EventT_co]]:
        """Generate a decorator to subscribe a callback to an event type.

        This is a second-order decorator.

        Parameters
        ----------
        event_type : typing.Optional[typing.Type[T]]
            The event type to subscribe to. The implementation may allow this
            to be undefined. If this is the case, the event type will be inferred
            instead from the type hints on the function signature.

            `T` must be a subclass of `hikari.events.base_events.Event`.

        Returns
        -------
        typing.Callable[[T], T]
            A decorator for a coroutine function that passes it to
            `EventManager.subscribe` before returning the function
            reference.

        See Also
        --------
        Dispatch: `hikari.api.event_manager.EventManager.dispatch`
        Stream: `hikari.api.event_manager.EventManager.stream`
        Subscribe: `hikari.api.event_manager.EventManager.subscribe`
        Unsubscribe: `hikari.api.event_manager.EventManager.unsubscribe`
        Wait for: `hikari.api.event_manager.EventManager.wait_for`
        """

    @abc.abstractmethod
    def stream(
        self,
        event_type: typing.Type[EventT_co],
        /,
        timeout: typing.Union[float, int, None],
        limit: typing.Optional[int] = None,
    ) -> event_stream.Streamer[EventT_co]:
        """Return a stream iterator for the given event and sub-events.

        Parameters
        ----------
        event_type : typing.Type[hikari.events.base_events.Event]
            The event type to listen for. This will listen for subclasses of
            this type additionally.
        timeout : typing.Optional[builtins.int, builtins.float]
            How long this streamer should wait for the next event before
            ending the iteration. If `builtins.None` then this will continue
            until explicitly broken from.
        limit : typing.Optional[builtins.int]
            The limit for how many events this should queue at one time before
            dropping extra incoming events, leave this as `builtins.None` for
            the cache size to be unlimited.

        Returns
        -------
        hikari.event_stream.Streamer[hikari.events.base_events.Event]
            The async iterator to handle streamed events. This must be started
            with `async with stream:` or `await stream.open()` before
            asynchronously iterating over it.

        !!! warning
            If you use `await stream.open()` to start the stream then you must
            also close it with `await stream.close()` otherwise it may queue
            events in memory indefinitely.

        Examples
        --------

        ```py
        async with bot.stream(events.ReactionAddEvent, timeout=30).filter(("message_id", message.id)) as stream:
            async for user_id in stream.map("user_id").limit(50):
                ...
        ```

        or using await `open()` and await `close()`

        ```py
        stream = bot.stream(events.ReactionAddEvent, timeout=30).filter(("message_id", message.id))
        await stream.open()

        async for user_id in stream.map("user_id").limit(50)
            ...

        await stream.close()
        ```

        See Also
        --------
        Dispatch: `hikari.api.event_manager.EventManager.dispatch`
        Listen: `hikari.api.event_manager.EventManager.listen`
        Subscribe: `hikari.api.event_manager.EventManager.subscribe`
        Unsubscribe: `hikari.api.event_manager.EventManager.unsubscribe`
        Wait for: `hikari.api.event_manager.EventManager.wait_for`
        """

    @abc.abstractmethod
    async def wait_for(
        self,
        event_type: typing.Type[EventT_co],
        /,
        timeout: typing.Union[float, int, None],
        predicate: typing.Optional[PredicateT[EventT_co]] = None,
    ) -> EventT_co:
        """Wait for a given event to occur once, then return the event.

        Parameters
        ----------
        event_type : typing.Type[hikari.events.base_events.Event]
            The event type to listen for. This will listen for subclasses of
            this type additionally.
        predicate
            A function taking the event as the single parameter.
            This should return `builtins.True` if the event is one you want to
            return, or `builtins.False` if the event should not be returned.
            If left as `None` (the default), then the first matching event type
            that the bot receives (or any subtype) will be the one returned.

            !!! warning
                Async predicates are not supported.
        timeout : typing.Union[builtins.float, builtins.int, builtins.None]
            The amount of time to wait before raising an `asyncio.TimeoutError`
            and giving up instead. This is measured in seconds. If
            `builtins.None`, then no timeout will be waited for (no timeout can
            result in "leaking" of coroutines that never complete if called in
            an uncontrolled way, so is not recommended).

        Returns
        -------
        hikari.events.base_events.Event
            The event that was provided.

        Raises
        ------
        asyncio.TimeoutError
            If the timeout is not `builtins.None` and is reached before an
            event is received that the predicate returns `builtins.True` for.

        See Also
        --------
        Listen: `hikari.api.event_manager.EventManager.listen`
        Stream: `hikari.api.event_manager.EventManager.stream`
        Subscribe: `hikari.api.event_manager.EventManager.subscribe`
        Dispatch: `hikari.api.event_manager.EventManager.dispatch`
        """
