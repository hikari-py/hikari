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
__all__ = ["EventDispatcher", "EventDispatcherImpl"]

import abc
import asyncio
import logging
import typing

from hikari.internal import assertions
from hikari.internal import more_asyncio
from hikari.internal import more_collections
from hikari.internal import more_logging
from hikari import events

EventT = typing.TypeVar("EventT", bound=events.HikariEvent)
PredicateT = typing.Callable[[EventT], typing.Union[bool, typing.Coroutine[None, None, bool]]]
EventCallbackT = typing.Callable[[EventT], typing.Coroutine[None, None, typing.Any]]


class EventDispatcher(abc.ABC):
    """Base definition for a conforming event dispatcher implementation.

    This enables users to implement their own event dispatching strategies
    if the base implementation is not suitable. This could be used to write
    a distributed bot dispatcher, for example, or could handle dispatching
    to a set of micro-interpreter instances to achieve greater concurrency.
    """

    __slots__ = ()

    @abc.abstractmethod
    def add_listener(self, event_type: typing.Type[EventT], callback: EventCallbackT) -> EventCallbackT:
        """Register a new event callback to a given event name.

        Parameters
        ----------
        event_type : :obj:`typing.Type` [ :obj:`hikari.events.HikariEvent` ]
            The event to register to.
        callback : ``async def callback(event: HikariEvent) -> ...``
            The event callback to invoke when this event is fired.

        Raises
        ------
        :obj:`TypeError`
            If ``coroutine_function`` is not a coroutine.
        """

    @abc.abstractmethod
    def remove_listener(self, event_type: typing.Type[EventT], callback: EventCallbackT,) -> EventCallbackT:
        """Remove the given coroutine function from the handlers for the given event.

        The name is mandatory to enable supporting registering the same event callback for multiple event types.

        Parameters
        ----------
        event_type : :obj:`typing.Type` [ :obj:`hikari.events.HikariEvent` ]
            The type of event to remove the callback from.
        callback : ``async def callback(event: HikariEvent) -> ...``
            The event callback to invoke when this event is fired.
        """

    @abc.abstractmethod
    def wait_for(
        self, event_type: typing.Type[EventT], *, timeout: typing.Optional[float], predicate: PredicateT
    ) -> more_asyncio.Future:
        """Wait for the given event type to occur.

        Parameters
        ----------
        event_type : :obj:`typing.Type` [ :obj:`hikari.events.HikariEvent` ]
            The name of the event to wait for.
        timeout : :obj:`float`, optional
            The timeout to wait for before cancelling and raising an
            :obj:`asyncio.TimeoutError` instead. If this is ``None``, this will
            wait forever. Care must be taken if you use ``None`` as this may
            leak memory if you do this from an event listener that gets
            repeatedly called. If you want to do this, you should consider
            using an event listener instead of this function.
        predicate : ``def predicate(event) -> bool`` or ``async def predicate(event) -> bool``
            A function that takes the arguments for the event and returns True
            if it is a match, or False if it should be ignored.
            This can be a coroutine function that returns a boolean, or a
            regular function.

        Returns
        -------
        :obj:`asyncio.Future`:
            A future to await. When the given event is matched, this will be
            completed with the corresponding event body.

            If the predicate throws an exception, or the timeout is reached,
            then this will be set as an exception on the returned future.

        Notes
        -----
        The event type is not expected to be considered in a polymorphic
        lookup, but can be implemented this way optionally if documented.
        """

    # Ignore docstring not starting in an imperative mood
    def on(self, event_type: typing.Type[EventT]) -> typing.Callable[[EventCallbackT], EventCallbackT]:  # noqa: D401
        """Returns a decorator that is equivalent to invoking :meth:`add_listener`.

        Parameters
        ----------
        event_type : :obj:`typing.Type` [ :obj:`hikari.events.HikariEvent` ]
            The event type to register the produced decorator to.

        Returns
        -------
        coroutine function decorator:
            A decorator for a coroutine function that registers the given event.
        """

        def decorator(callback: EventCallbackT) -> EventCallbackT:
            return self.add_listener(event_type, callback)

        return decorator

    # Do not add an annotation here, it will mess with type hints in PyCharm which can lead to
    # confusing telepathy comments to the user.
    @abc.abstractmethod
    def dispatch_event(self, event: events.HikariEvent) -> more_asyncio.Future[typing.Any]:
        """Dispatch a given event to any listeners and waiters.

        Parameters
        ----------
        event : :obj:`hikari.events.HikariEvent`
            The event to dispatch.

        Returns
        -------
        :obj:`asyncio.Future`:
            a future that can be optionally awaited if you need to wait for all
            listener callbacks and waiters to be processed. If this is not
            awaited, the invocation is invoked soon on the current event loop.
        """


class EventDispatcherImpl(EventDispatcher):
    """Handles storing and dispatching to event listeners and one-time event waiters.

    Event listeners once registered will be stored until they are manually
    removed. Each time an event is dispatched with a matching name, they will
    be invoked on the event loop.

    One-time event waiters are futures that will be completed when a matching
    event is fired. Once they are matched, they are removed from the listener
    list. Each listener has a corresponding predicate that is invoked prior
    to completing the waiter, with any event parameters being passed to the
    predicate. If the predicate returns False, the waiter is not completed. This
    allows filtering of certain events and conditions in a procedural way.
    """

    #: The logger used to write log messages.
    #:
    #: :type: :obj:`logging.Logger`
    logger: logging.Logger

    def __init__(self) -> None:
        self._listeners: typing.Dict[typing.Type[EventT], typing.List[EventCallbackT]] = {}
        # pylint: disable=E1136
        self._waiters: typing.Dict[
            typing.Type[EventT], more_collections.WeakKeyDictionary[asyncio.Future, PredicateT]
        ] = {}
        # pylint: enable=E1136
        self.logger = more_logging.get_named_logger(self)

    def close(self) -> None:
        """Cancel anything that is waiting for an event to be dispatched."""
        self._listeners.clear()
        for waiter in self._waiters.values():
            for future in waiter.keys():
                future.cancel()
        self._waiters.clear()

    def add_listener(self, event_type: typing.Type[events.HikariEvent], callback: EventCallbackT) -> None:
        """Register a new event callback to a given event name.

        Parameters
        ----------
        event_type : :obj:`typing.Type` [ :obj:`hikari.events.HikariEvent` ]
            The event to register to.
        callback : ``async def callback(event: HikariEvent) -> ...``
            The event callback to invoke when this event is fired.

        Raises
        ------
        :obj:`TypeError`
            If ``coroutine_function`` is not a coroutine.
        """
        assertions.assert_that(
            asyncio.iscoroutinefunction(callback), "You must subscribe a coroutine function only", TypeError
        )
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(callback)

    def remove_listener(self, event_type: typing.Type[EventT], callback: EventCallbackT) -> None:
        """Remove the given coroutine function from the handlers for the given event.

        The name is mandatory to enable supporting registering the same event callback for multiple event types.

        Parameters
        ----------
        event_type : :obj:`typing.Type` [ :obj:`hikari.events.HikariEvent` ]
            The type of event to remove the callback from.
        callback : ``async def callback(event: HikariEvent) -> ...``
            The event callback to remove.
        """
        if event_type in self._listeners and callback in self._listeners[event_type]:
            if len(self._listeners[event_type]) - 1 == 0:
                del self._listeners[event_type]
            else:
                self._listeners[event_type].remove(callback)

    # Do not add an annotation here, it will mess with type hints in PyCharm which can lead to
    # confusing telepathy comments to the user.
    def dispatch_event(self, event: events.HikariEvent):
        """Dispatch a given event to all listeners and waiters that are applicable.

        Parameters
        ----------
        event : :obj:`hikari.events.HikariEvent`
            The event to dispatch.

        Returns
        -------
        :obj:`asyncio.Future`
            This may be a gathering future of the callbacks to invoke, or it may
            be a completed future object. Regardless, this result will be
            scheduled on the event loop automatically, and does not need to be
            awaited. Awaiting this future will await completion of all invoked
            event handlers.
        """
        event_t = type(event)

        futs = []

        if event_t in self._listeners:
            for callback in self._listeners[event_t]:
                futs.append(self._catch(callback, event))

        # Only try to awaken waiters when the waiter is registered as a valid
        # event type and there is more than 0 waiters in that dict.
        if waiters := self._waiters.get(event_t):
            # Run this in the background as a coroutine so that any async predicates
            # can be awaited concurrently.
            futs.append(asyncio.create_task(self._awaken_waiters(waiters, event)))

        result = asyncio.gather(*futs) if futs else more_asyncio.completed_future()  # lgtm [py/unused-local-variable]

        # Stop false positives from linters that now assume this is a coroutine function
        result: typing.Any

        return result

    async def _awaken_waiters(self, waiters, event):
        await asyncio.gather(
            *(self._maybe_awaken_waiter(event, future, predicate) for future, predicate in tuple(waiters.items()))
        )

    async def _maybe_awaken_waiter(self, event, future, predicate):
        delete_waiter = True
        try:
            result = predicate(event)
            if result or asyncio.iscoroutine(result) and await result:
                future.set_result(event)
            else:
                delete_waiter = False
        except Exception as ex:  # pylint:disable=broad-except
            delete_waiter = True
            future.set_exception(ex)

        event_t = type(event)

        if delete_waiter:
            if not len(self._waiters[event_t]) - 1:
                del self._waiters[event_t]
            else:
                del self._waiters[event_t][future]

    async def _catch(self, callback, event):
        try:
            return await callback(event)
        except Exception as ex:  # pylint:disable=broad-except
            # Pop the top-most frame to remove this _catch call.
            # The user doesn't need it in their traceback.
            ex.__traceback__ = ex.__traceback__.tb_next
            self.handle_exception(ex, event, callback)

    def handle_exception(
        self, exception: Exception, event: events.HikariEvent, callback: typing.Callable[..., typing.Awaitable[None]]
    ) -> None:
        """Handle raised exception.

        This allows users to override this with a custom implementation if desired.

        This implementation will check to see if the event that triggered the
        exception is an :obj:`hikari.events.ExceptionEvent`. If this
        exception was caused by the :obj:`hikari.events.ExceptionEvent`,
        then nothing is dispatched (thus preventing an exception handler recursively
        re-triggering itself). Otherwise, an :obj:`hikari.events.ExceptionEvent`
        is dispatched.

        Parameters
        ----------
        exception: :obj:`Exception`
            The exception that triggered this call.
        event: :obj:`hikari.events.HikariEvent`
            The event that was being dispatched.
        callback
            The callback that threw the exception.
        """
        # Do not recurse if a dodgy exception handler is added.
        if not isinstance(event, events.ExceptionEvent):
            self.logger.exception(
                'Exception occurred in handler for event "%s"', type(event).__name__, exc_info=exception
            )
            self.dispatch_event(events.ExceptionEvent(exception=exception, event=event, callback=callback))
        else:
            self.logger.exception(
                'Exception occurred in handler for event "%s", and the exception has been dropped',
                type(event).__name__,
                exc_info=exception,
            )

    def wait_for(
        self, event_type: typing.Type[EventT], *, timeout: typing.Optional[float], predicate: PredicateT,
    ) -> more_asyncio.Future:
        """Wait for a event to occur once and then return the arguments the event was called with.

        Events can be filtered using a given predicate function. If unspecified,
        the first event of the given name will be a match.

        Every event that matches the event name that the bot receives will be
        checked. Thus, if you need to wait for events in a specific guild or
        channel, or from a specific person, you want to give a predicate that
        checks this.

        Parameters
        ----------
        event_type : :obj:`typing.Type` [ :obj:`hikari.events.HikariEvent` ]
            The name of the event to wait for.
        timeout : :obj:`float`, optional
            The timeout to wait for before cancelling and raising an
            :obj:`asyncio.TimeoutError` instead. If this is `None`, this will
            wait forever. Care must be taken if you use `None` as this may
            leak memory if you do this from an event listener that gets
            repeatedly called. If you want to do this, you should consider
            using an event listener instead of this function.
        predicate : ``def predicate(event) -> bool`` or ``async def predicate(event) -> bool``
            A function that takes the arguments for the event and returns True
            if it is a match, or False if it should be ignored.
            This can be a coroutine function that returns a boolean, or a
            regular function.

        Returns
        -------
        :obj:`asyncio.Future`
            A future that when awaited will provide a the arguments passed to
            the first matching event. If no arguments are passed to the event,
            then `None` is the result. If one argument is passed to the event,
            then that argument is the result, otherwise a tuple of arguments is
            the result instead.

        Notes
        -----
        Awaiting this result will raise an :obj:`asyncio.TimeoutError` if the
        timeout is hit and no match is found. If the predicate throws any
        exception, this is raised immediately.
        """
        future = asyncio.get_event_loop().create_future()
        if event_type not in self._waiters:
            # This is used as a weakref dict to allow automatically tidying up
            # any future that falls out of scope entirely.
            self._waiters[event_type] = more_collections.WeakKeyDictionary()
        self._waiters[event_type][future] = predicate
        # noinspection PyTypeChecker
        return asyncio.ensure_future(asyncio.wait_for(future, timeout))
