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
"""Event dispatcher implementation."""

from __future__ import annotations

__all__ = ["EventDispatcher"]

import abc
import inspect
import typing

from hikari.internal import conversions

if typing.TYPE_CHECKING:
    from hikari.events import bases
    from hikari.internal import more_typing

    EventT = typing.TypeVar("EventT", bound=bases.HikariEvent)
    PredicateT = typing.Callable[[EventT], typing.Union[more_typing.Coroutine[bool], bool]]
    EventCallbackT = typing.Callable[[EventT], more_typing.Coroutine[typing.Any]]


class EventDispatcher(abc.ABC):
    """Base definition for a conforming event dispatcher implementation.

    This enables users to implement their own event dispatching strategies
    if the base implementation is not suitable. This could be used to write
    a distributed bot dispatcher, for example, or could handle dispatching
    to a set of micro-interpreter instances to achieve greater concurrency.
    """

    __slots__ = ()

    @abc.abstractmethod
    def close(self) -> None:
        """Cancel anything that is waiting for an event to be dispatched."""

    @abc.abstractmethod
    def add_listener(self, event_type: typing.Type[EventT], callback: EventCallbackT, **kwargs) -> EventCallbackT:
        """Register a new event callback to a given event name.

        Parameters
        ----------
        event_type : typing.Type[hikari.events.base.HikariEvent]
            The event to register to.
        callback : `async def callback(event: HikariEvent) -> ...`
            The event callback to invoke when this event is fired.

        Raises
        ------
        TypeError
            If `coroutine_function` is not a coroutine.
        """

    @abc.abstractmethod
    def remove_listener(self, event_type: typing.Type[EventT], callback: EventCallbackT) -> EventCallbackT:
        """Remove the given coroutine function from the handlers for the given event.

        The name is mandatory to enable supporting registering the same event callback for multiple event types.

        Parameters
        ----------
        event_type : typing.Type[hikari.events.base.HikariEvent]
            The type of event to remove the callback from.
        callback : `async def callback(event: HikariEvent) -> ...`
            The event callback to invoke when this event is fired.
        """

    @abc.abstractmethod
    def wait_for(
        self, event_type: typing.Type[EventT], *, timeout: typing.Optional[float], predicate: PredicateT
    ) -> more_typing.Future:
        """Wait for the given event type to occur.

        Parameters
        ----------
        event_type : typing.Type[hikari.events.base.HikariEvent]
            The name of the event to wait for.
        timeout : float, optional
            The timeout to wait for before cancelling and raising an
            `asyncio.TimeoutError` instead. If this is `None`, this
            will wait forever. Care must be taken if you use `None` as this
            may leak memory if you do this from an event listener that gets
            repeatedly called. If you want to do this, you should consider
            using an event listener instead of this function.
        predicate : `def predicate(event) -> bool` or `async def predicate(event) -> bool`
            A function that takes the arguments for the event and returns True
            if it is a match, or False if it should be ignored.
            This can be a coroutine function that returns a boolean, or a
            regular function.

        Returns
        -------
        asyncio.Future
            A future to await. When the given event is matched, this will be
            completed with the corresponding event body.

            If the predicate throws an exception, or the timeout is reached,
            then this will be set as an exception on the returned future.

        !!! note
            The event type is not expected to be considered in a polymorphic
            lookup, but can be implemented this way optionally if documented.
        """

    def on(
        self, event_type: typing.Optional[typing.Type[EventT]] = None  # pylint:disable=unused-argument
    ) -> typing.Callable[[EventCallbackT], EventCallbackT]:
        """Return a decorator equivalent to invoking `EventDispatcher.add_listener`.

        Parameters
        ----------
        event_type : typing.Type[hikari.events.base.HikariEvent], optional
            The event type to register the produced decorator to. If this is not
            specified, then the given function is used instead and the type hint
            of the first argument is considered. If no type hint is present
            there either, then the call will fail.

        Examples
        --------
            # Type-hinted format.
            @bot.on()
            async def on_message(event: hikari.MessageCreatedEvent) -> None:
                print(event.content)

            # Explicit format.
            @bot.on(hikari.MessageCreatedEvent)
            async def on_message(event):
                print(event.content)

        Returns
        -------
        decorator(T) -> T
            A decorator for a coroutine function that registers the given event.
        """

        def decorator(callback: EventCallbackT) -> EventCallbackT:
            nonlocal event_type

            if event_type is None:
                signature = inspect.signature(callback)
                parameters = list(signature.parameters.values())

                # Seems that the `self` gets unbound for methods automatically by
                # inspect.signature. That makes my life two lines easier.
                if len(parameters) == 1:
                    event_param = parameters[0]
                else:
                    raise TypeError(f"Invalid signature for event: async def {callback.__name__}({signature}): ...")

                if event_param.annotation is inspect.Parameter.empty:
                    raise AttributeError(f"No param type hint given for: async def {callback}({signature}): ...")

                frame, *_, = inspect.stack(2)[0]

                try:
                    event_type = conversions.snoop_typehint_from_scope(frame, event_param.annotation)
                finally:
                    del frame, _

            return self.add_listener(event_type, callback, _stack_level=3)

        return decorator

    # Do not add an annotation here, it will mess with type hints in PyCharm which can lead to
    # confusing telepathy comments to the user.
    @abc.abstractmethod
    def dispatch_event(self, event: bases.HikariEvent) -> more_typing.Future[typing.Any]:
        """Dispatch a given event to any listeners and waiters.

        Parameters
        ----------
        event : hikari.events.base.HikariEvent
            The event to dispatch.

        Returns
        -------
        asyncio.Future:
            A future that can be optionally awaited if you need to wait for all
            listener callbacks and waiters to be processed. If this is not
            awaited, the invocation is invoked soon on the current event loop.
        """
