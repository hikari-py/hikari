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
import asyncio
import logging

import typing
import weakref

from hikari.internal_utilities import aio
from hikari.internal_utilities import assertions
from hikari.internal_utilities import loggers

from hikari.core import events


class EventDelegate:
    """Handles storing and dispatching to event listeners and one-time event
    waiters.

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

    __slots__ = ("exception_event", "logger", "_listeners", "_waiters")

    def __init__(self) -> None:
        self._listeners = {}
        self._waiters = {}
        self.logger = loggers.get_named_logger(self)

    def add(self, event: typing.Type[events.HikariEvent], coroutine_function: aio.CoroutineFunctionT) -> None:
        """Register a new event callback to a given event name.

        Parameters
        ----------
        event : :obj:`typing.Type` [ :obj:`events.HikariEvent` ]
            The event to register to.
        coroutine_function
            The event callback to invoke when this event is fired.

        Raises
        ------
        :obj:`TypeError`
            If ``coroutine_function`` is not a coroutine.
        """
        assertions.assert_that(
            asyncio.iscoroutinefunction(coroutine_function), "You must subscribe a coroutine function only", TypeError
        )
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(coroutine_function)

    def remove(self, name: str, coroutine_function: aio.CoroutineFunctionT) -> None:
        """Remove the given coroutine function from the handlers for the given event.

        The name is mandatory to enable supporting registering the same event callback for multiple event types.

        Parameters
        ----------
        name : :obj:`str`
            The event to remove from.
        coroutine_function
            The event callback to remove.
        """
        if name in self._listeners and coroutine_function in self._listeners[name]:
            if len(self._listeners[name]) - 1 == 0:
                del self._listeners[name]
            else:
                self._listeners[name].remove(coroutine_function)

    # Do not add an annotation here, it will mess with type hints in PyCharm which can lead to
    # confusing telepathy comments to the user.
    def dispatch(self, event: events.HikariEvent):
        """Dispatch a given event to all listeners and waiters that are
        applicable.

        Parameters
        ----------
        event : :obj:`events.HikariEvent`
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

        if event_t in self._waiters:
            for future, predicate in tuple(self._waiters[event_t].items()):
                try:
                    if predicate(event):
                        future.set_result(event)
                        del self._waiters[event_t][future]
                except Exception as ex:
                    future.set_exception(ex)
                    del self._waiters[event_t][future]

            if not self._waiters[event_t]:
                del self._waiters[event_t]

        # Hack to stop PyCharm saying you need to await this function when you do not need to await
        # it.
        future: typing.Any

        if event_t in self._listeners:
            coros = (self._catch(callback, event) for callback in self._listeners[event_t])
            future = asyncio.gather(*coros)
        else:
            future = aio.completed_future()

        return future

    async def _catch(self, callback, event):
        try:
            return await callback(event)
        except Exception as ex:
            # Pop the top-most frame to remove this _catch call.
            # The user doesn't need it in their traceback.
            ex.__traceback__ = ex.__traceback__.tb_next
            self.handle_exception(ex, event, callback)

    def handle_exception(
        self, exception: Exception, event: events.HikariEvent, callback: aio.CoroutineFunctionT
    ) -> None:
        """Function that is passed any exception. This allows users to override
        this with a custom implementation if desired.

        This implementation will check to see if the event that triggered the
        exception is an exception event. If this exceptino was caused by the
        ``exception_event``, then nothing is dispatched (thus preventing
        an exception handler recursively re-triggering itself). Otherwise, an
        ``exception_event`` is dispatched with a
        :obj:`EventExceptionContext` as the sole parameter.

        Parameters
        ----------
        exception: :obj:`Exception`
            The exception that triggered this call.
        event: :obj:`events.Event`
            The event that was being dispatched.
        callback
            The callback that threw the exception.
        """
        # Do not recurse if a dodgy exception handler is added.
        if not isinstance(event, events.ExceptionEvent):
            self.logger.exception(
                'Exception occurred in handler for event "%s"', type(event).__name__, exc_info=exception)
            self.dispatch(events.ExceptionEvent(exception=exception, event=event, callback=callback))
        else:
            self.logger.exception(
                'Exception occurred in handler for event "%s", and the exception has been dropped',
                type(event).__name__,
                exc_info=exception,
            )

    def wait_for(
        self,
        event_type: typing.Type[events.HikariEvent],
        *,
        timeout: typing.Optional[float],
        predicate: typing.Callable[..., bool],
    ) -> asyncio.Future:
        """Given an event name, wait for the event to occur once, then return
        the arguments that accompanied the event as the result.

        Events can be filtered using a given predicate function. If unspecified,
        the first event of the given name will be a match.

        Every event that matches the event name that the bot receives will be
        checked. Thus, if you need to wait for events in a specific guild or
        channel, or from a specific person, you want to give a predicate that
        checks this.

        Parameters
        ----------
        event_type : :obj:`typing.Type` [ :obj:`events.HikariEvent` ]
            The name of the event to wait for.
        timeout : :obj:`float`, optional
            The timeout to wait for before cancelling and raising an
            :obj:`asyncio.TimeoutError` instead. If this is `None`, this will
            wait forever. Care must be taken if you use `None` as this may
            leak memory if you do this from an event listener that gets
            repeatedly called. If you want to do this, you should consider
            using an event listener instead of this function.
        predicate : :obj:`typing.Callable` [ ..., :obj:`bool` ]
            A function that takes the arguments for the event and returns True
            if it is a match, or False if it should be ignored.
            This cannot be a coroutine function.

        Returns
        -------
        :obj:`asyncio.Future`
            A future that when awaited will provide a the arguments passed to the
            first matching event. If no arguments are passed to the event, then
            `None` is the result. If one argument is passed to the event, then
            that argument is the result, otherwise a tuple of arguments is the
            result instead.

        Note
        ----
        Awaiting this result will raise an :obj:`asyncio.TimeoutError` if the timeout
        is hit and no match is found. If the predicate throws any exception,
        this is raised immediately.
        """
        future = asyncio.get_event_loop().create_future()
        if event_type not in self._waiters:
            # This is used as a weakref dict to allow automatically tidying up
            # any future that falls out of scope entirely.
            self._waiters[event_type] = weakref.WeakKeyDictionary()
        self._waiters[event_type][future] = predicate
        # noinspection PyTypeChecker
        return asyncio.ensure_future(asyncio.wait_for(future, timeout))
