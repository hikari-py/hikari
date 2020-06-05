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
"""Core interface for components that dispatch events to the library."""
from __future__ import annotations

__all__ = ["IEventDispatcher"]

import abc
import typing

from hikari.api import component
from hikari.utilities import undefined

if typing.TYPE_CHECKING:
    from hikari.events import base
    from hikari.utilities import aio

    _EventT = typing.TypeVar("_EventT", bound=base.HikariEvent, covariant=True)
    _PredicateT = typing.Callable[[_EventT], typing.Union[bool, typing.Coroutine[None, typing.Any, bool]]]
    _SyncCallbackT = typing.Callable[[_EventT], None]
    _AsyncCallbackT = typing.Callable[[_EventT], typing.Coroutine[None, typing.Any, None]]
    _CallbackT = typing.Union[_SyncCallbackT, _AsyncCallbackT]


class IEventDispatcher(component.IComponent, abc.ABC):
    """Interface for event dispatchers.

    This is a consumer of a `hikari.events.base.HikariEvent` object, and is
    expected to invoke one or more corresponding event listeners where
    appropriate.
    """

    __slots__ = ()

    @abc.abstractmethod
    def dispatch(self, event: base.HikariEvent) -> aio.Future[typing.Any]:
        """Dispatch an event.

        Parameters
        ----------
        event : hikari.events.base.HikariEvent
            The event to dispatch.

        Example
        -------
        We can dispatch custom events by first defining a class that
        derives from `hikari.events.base.HikariEvent`.

        ```py
        import attr

        from hikari.events.base import HikariEvent
        from hikari.models.users import User
        from hikari.utilities.snowflake import Snowflake

        @attr.s(auto_attribs=True)
        class EveryoneMentionedEvent(HikariEvent):
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
        `IEventDispatcher.subscribe`.

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
        IEventDispatcher.subscribe
        IEventDispatcher.wait_for
        """

    @abc.abstractmethod
    def subscribe(
        self,
        event_type: typing.Type[_EventT],
        callback: typing.Callable[[_EventT], typing.Union[typing.Coroutine[None, typing.Any, None], None]],
    ) -> None:
        """Subscribe a given callback to a given event type.

        Parameters
        ----------
        event_type : typing.Type[hikari.events.base.HikariEvent]
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

        See Also
        --------
        IEventDispatcher.listen
        IEventDispatcher.wait_for
        """

    @abc.abstractmethod
    def unsubscribe(
        self,
        event_type: typing.Type[_EventT],
        callback: typing.Callable[[_EventT], typing.Union[typing.Coroutine[None, typing.Any, None], None]],
    ) -> None:
        """Unsubscribe a given callback from a given event type, if present.

        Parameters
        ----------
        event_type : typing.Type[hikari.events.base.HikariEvent]
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
        self, event_type: typing.Union[undefined.Undefined, typing.Type[_EventT]] = undefined.Undefined(),
    ) -> typing.Callable[[_CallbackT], _CallbackT]:
        """Generate a decorator to subscribe a callback to an event type.

        This is a second-order decorator.

        Parameters
        ----------
        event_type : hikari.utilities.undefined.Undefined or typing.Type[hikari.events.base.HikariEvent]
            The event type to subscribe to. The implementation may allow this
            to be undefined. If this is the case, the event type will be inferred
            instead from the type hints on the function signature.

        Returns
        -------
        typing.Callable[[Callback], Callback]
            A decorator for a function or coroutine function that passes it
            to `IEventDispatcher.subscribe` before returning the function
            reference.

        See Also
        --------
        IEventDispatcher.dispatch
        IEventDispatcher.subscribe
        IEventDispatcher.unsubscribe
        IEventDispatcher.wait_for
        """

    @abc.abstractmethod
    async def wait_for(
        self, event_type: typing.Type[_EventT], predicate: _PredicateT, timeout: typing.Union[float, int, None],
    ) -> _EventT:
        """Wait for a given event to occur once, then return the event.

        Parameters
        ----------
        event_type : typing.Type[hikari.events.base.HikariEvent]
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
        hikari.events.base.HikariEvent
            The event that was provided.

        Raises
        ------
        asyncio.TimeoutError
            If the timeout is not `None` and is reached before an event is
            received that the predicate returns `True` for.

        See Also
        --------
        IEventDispatcher.listen
        IEventDispatcher.subscribe
        IEventDispatcher.dispatch
        """
