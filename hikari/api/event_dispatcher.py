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
"""Core interface for components that dispatch events to the library."""
from __future__ import annotations

__all__: typing.Final[typing.Sequence[str]] = [
    "IEventDispatcherBase",
    "IEventDispatcherApp",
    "IEventDispatcherComponent",
]

import abc
import asyncio
import typing

from hikari.utilities import undefined

if typing.TYPE_CHECKING:
    from hikari.events import base


class IEventDispatcherBase(abc.ABC):
    """Base interface for event dispatcher implementations.

    This is a consumer of a `hikari.events.base.Event` object, and is
    expected to invoke one or more corresponding event listeners where
    appropriate.
    """

    __slots__: typing.Sequence[str] = ()

    if typing.TYPE_CHECKING:
        EventT = typing.TypeVar("EventT", bound=base.Event)
        PredicateT = typing.Callable[[base.Event], typing.Union[bool, typing.Coroutine[None, typing.Any, bool]]]
        SyncCallbackT = typing.Callable[[base.Event], None]
        AsyncCallbackT = typing.Callable[[base.Event], typing.Coroutine[None, typing.Any, None]]
        CallbackT = typing.Union[SyncCallbackT, AsyncCallbackT]

    @abc.abstractmethod
    def dispatch(self, event: base.Event) -> asyncio.Future[typing.Any]:
        """Dispatch an event.

        Parameters
        ----------
        event : hikari.events.base.Event
            The event to dispatch.

        Example
        -------
        We can dispatch custom events by first defining a class that
        derives from `hikari.events.base.Event`.

        ```py
        import attr

        from hikari.events.base import Event
        from hikari.models.users import User
        from hikari.utilities.snowflake import Snowflake

        @attr.s(auto_attribs=True)
        class EveryoneMentionedEvent(Event):
            author: User
            '''The user who mentioned everyone.'''

            content: str
            '''The message that was sent.'''

            message_id: Snowflake
            '''The message ID.'''

            channel_id: Snowflake
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
        `IEventDispatcherBase.subscribe`.

        ```py
        @bot.listen(EveryoneMentionedEvent)
        async def on_everyone_mentioned(event):
            print(event.user, "just pinged everyone in", event.channel_id)
        ```

        Returns
        -------
        asyncio.Future
            A future that can be optionally awaited. If awaited, the future
            will complete once all corresponding event listeners have been
            invoked. If not awaited, this will schedule the dispatch of the
            events in the background for later.

        See Also
        --------
        `hikari.api.event_dispatcher.IEventDispatcherBase.subscribe`
        `hikari.api.event_dispatcher.IEventDispatcherBase.wait_for`
        """

    @abc.abstractmethod
    def subscribe(
        self,
        event_type: typing.Type[EventT],
        callback: typing.Callable[[EventT], typing.Union[typing.Coroutine[None, typing.Any, None], None]],
    ) -> typing.Callable[[EventT], typing.Coroutine[None, typing.Any, None]]:
        """Subscribe a given callback to a given event type.

        Parameters
        ----------
        event_type : typing.Type[hikari.events.base.Event]
            The event type to listen for. This will also listen for any
            subclasses of the given type.
        callback
            Either a function or a coroutine function to invoke. This should
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
        typing.Callable[[T], typing.Coroutine[None, typing.Any, None]
            The event callback. If you did not pass a callback that was a
            coroutine function, then this will be a coroutine function
            wrapping your callback instead. This enables you to correctly
            unsubscribe from the event again later.

        See Also
        --------
        `hikari.api.event_dispatcher.IEventDispatcherBase.listen`
        `hikari.api.event_dispatcher.IEventDispatcherBase.wait_for`
        """

    @abc.abstractmethod
    def get_listeners(
        self, event_type: typing.Type[EventT], *, polymorphic: bool = True,
    ) -> typing.Collection[typing.Callable[[EventT], typing.Coroutine[None, typing.Any, None]]]:
        """Get the listeners for a given event type, if there are any.

        Parameters
        ----------
        event_type : typing.Type[hikari.events.base.Event]
            The event type to look for.
        polymorphic : bool
            If `True`, this will return `True` if a subclass of the given
            event type has a listener registered. If `False`, then only
            listeners for this class specifically are returned. The default
            is `True`.

        Returns
        -------
        typing.Collection[typing.Callable[[EventT], typing.Coroutine[None, typing.Any, None]]
            A copy of the collection of listeners for the event. Will return
            an empty collection if nothing is registered.
        """

    @abc.abstractmethod
    def has_listener(
        self,
        event_type: typing.Type[EventT],
        callback: typing.Callable[[EventT], typing.Coroutine[None, typing.Any, None]],
        *,
        polymorphic: bool = True,
    ) -> bool:
        """Check whether the callback is subscribed to the given event.

        Parameters
        ----------
        event_type : typing.Type[hikari.events.base.Event]
            The event type to look for.
        callback :
            The callback to look for.
        polymorphic : bool
            If `True`, this will return `True` if a subclass of the given
            event type has a listener registered. If `False`, then only
            listeners for this class specifically are checked. The default
            is `True`.
        """

    @abc.abstractmethod
    def unsubscribe(
        self,
        event_type: typing.Type[EventT],
        callback: typing.Callable[[EventT], typing.Coroutine[None, typing.Any, None]],
    ) -> None:
        """Unsubscribe a given callback from a given event type, if present.

        Parameters
        ----------
        event_type : typing.Type[hikari.events.base.Event]
            The event type to unsubscribe from. This must be the same exact
            type as was originally subscribed with to be removed correctly.
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
    def listen(
        self, event_type: typing.Union[undefined.UndefinedType, typing.Type[EventT]] = undefined.UNDEFINED,
    ) -> typing.Callable[[CallbackT], CallbackT]:
        """Generate a decorator to subscribe a callback to an event type.

        This is a second-order decorator.

        Parameters
        ----------
        event_type : hikari.utilities.undefined.UndefinedType or typing.Type[hikari.events.base.Event]
            The event type to subscribe to. The implementation may allow this
            to be undefined. If this is the case, the event type will be inferred
            instead from the type hints on the function signature.

        Returns
        -------
        typing.Callable[[Callback], Callback]
            A decorator for a function or coroutine function that passes it
            to `IEventDispatcherBase.subscribe` before returning the function
            reference.

        See Also
        --------
        `hikari.api.event_dispatcher.IEventDispatcherBase.dispatch`
        `hikari.api.event_dispatcher.IEventDispatcherBase.subscribe`
        `hikari.api.event_dispatcher.IEventDispatcherBase.unsubscribe`
        `hikari.api.event_dispatcher.IEventDispatcherBase.wait_for`
        """

    @abc.abstractmethod
    async def wait_for(
        self, event_type: typing.Type[EventT], predicate: PredicateT, timeout: typing.Union[float, int, None],
    ) -> EventT:
        """Wait for a given event to occur once, then return the event.

        Parameters
        ----------
        event_type : typing.Type[hikari.events.base.Event]
            The event type to listen for. This will listen for subclasses of
            this type additionally.
        predicate
            A function or coroutine taking the event as the single parameter.
            This should return `True` if the event is one you want to return,
            or `False` if the event should not be returned.
        timeout : float or int or None
            The amount of time to wait before raising an `asyncio.TimeoutError`
            and giving up instead. This is measured in seconds. If `None`, then
            no timeout will be waited for (no timeout can result in "leaking" of
            coroutines that never complete if called in an uncontrolled way,
            so is not recommended).

        Returns
        -------
        hikari.events.base.Event
            The event that was provided.

        Raises
        ------
        asyncio.TimeoutError
            If the timeout is not `None` and is reached before an event is
            received that the predicate returns `True` for.

        See Also
        --------
        `hikari.api.event_dispatcher.IEventDispatcherBase.listen`
        `hikari.api.event_dispatcher.IEventDispatcherBase.subscribe`
        `hikari.api.event_dispatcher.IEventDispatcherBase.dispatch`
        """


class IEventDispatcherComponent(IEventDispatcherBase, abc.ABC):
    """Base interface for event dispatcher implementations that are components.

    This is a consumer of a `hikari.events.base.Event` object, and is
    expected to invoke one or more corresponding event listeners where
    appropriate.
    """


class IEventDispatcherApp(IEventDispatcherBase, abc.ABC):
    """Application specialization that supports dispatching of events.

    These events are expected to be instances of
    `hikari.events.base.Event`.

    This may be combined with `IGatewayZookeeperApp` for most single-process
    bots, or may be a specific component for large distributed applications
    that consume events from a message queue, for example.

    This acts as an event dispatcher-like object that can simply delegate to
    the implementation, which makes event-based tasks like adding listeners
    and waiting for events much tidier.

    ```py

    # ... this means we can do this...

    >>> @bot.listen()
    >>> async def on_message(event: hikari.MessageCreateEvent) -> None: ...

    # ...instead of having to do this...

    >>> @bot.event_dispatcher.listen(hikari.MessageCreateEvent)
    >>> async def on_message(event: hikari.MessageCreateEvent) -> None: ...
    ```
    """

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def event_dispatcher(self) -> IEventDispatcherComponent:
        """Event dispatcher and subscription manager.

        This stores every event you subscribe to in your application, and
        manages invoking those subscribed callbacks when the corresponding
        event occurs.

        Event dispatchers also provide a `wait_for` functionality that can be
        used to wait for a one-off event that matches a certain criteria. This
        is useful if waiting for user feedback for a specific procedure being
        performed.

        Users may create their own events and trigger them using this as well,
        thus providing a simple in-process event bus that can easily be extended
        with a little work to span multiple applications in a distributed
        cluster.

        Returns
        -------
        hikari.api.event_dispatcher.IEventDispatcherBase
            The event dispatcher in use.
        """
