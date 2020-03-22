#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekokatt 2019-2020
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
"""Asyncio extensions and utilities."""
__all__ = [
    "CoroutineFunctionT",
    "PartialCoroutineProtocolT",
    "EventExceptionContext",
    "EventDelegate",
    "completed_future",
]

import asyncio
import dataclasses
import typing
import logging
import weakref

from hikari.internal_utilities import assertions
from hikari.internal_utilities import loggers

ReturnT = typing.TypeVar("ReturnT", covariant=True)
CoroutineFunctionT = typing.Callable[..., typing.Coroutine[typing.Any, typing.Any, ReturnT]]


class PartialCoroutineProtocolT(typing.Protocol[ReturnT]):
    """Represents the type of a :obj:`functools.partial` wrapping an :mod:`asyncio` coroutine."""

    def __call__(self, *args, **kwargs) -> typing.Coroutine[None, None, ReturnT]:
        ...

    def __await__(self):
        ...


@dataclasses.dataclass(frozen=True)
class EventExceptionContext:
    """A dataclass that contains information about where an exception was thrown from."""

    __slots__ = ("event_name", "callback", "args", "exception")

    #: The name of the event that triggered the exception.
    #:
    #: :type: :obj:`str`
    event_name: str

    #: The event handler that was being invoked.
    #:
    #: :type: :obj:`CoroutineFunctionT`
    callback: CoroutineFunctionT

    #: The arguments passed to the event callback.
    #:
    #: :type: :obj:`typing.Sequence` [ :obj:`typing.Any` ]
    args: typing.Sequence[typing.Any]

    #: The exception that was thrown.
    #:
    #: :type: :obj:`Exception`
    exception: Exception


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

    Parameters
    ----------
    exception_event : :obj:`str`
        The event to invoke if an exception is caught.
    """

    #: The event to invoke if an exception is caught.
    #:
    #: :type: :obj:`str`
    exception_event: str

    #: The logger used to write log messages.
    #:
    #: :type: :obj:`logging.Logger`
    logger: logging.Logger

    __slots__ = ("exception_event", "logger", "_listeners", "_waiters")

    def __init__(self, exception_event: str) -> None:
        self._listeners = {}
        self._waiters = {}
        self.logger = loggers.get_named_logger(self)
        self.exception_event = exception_event

    def add(self, name: str, coroutine_function: CoroutineFunctionT) -> None:
        """Register a new event callback to a given event name.

        Parameters
        ----------
        name : :obj:`str`
            The name of the event to register to.
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
        if name not in self._listeners:
            self._listeners[name] = []
        self._listeners[name].append(coroutine_function)

    def remove(self, name: str, coroutine_function: CoroutineFunctionT) -> None:
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
    def dispatch(self, name: str, *args):
        """Dispatch a given event to all listeners and waiters that are
        applicable.

        Parameters
        ----------
        name: :obj:`str`
            The name of the event to dispatch.
        *args
            The parameters to pass to the event callback.

        Returns
        -------
        :obj:`asyncio.Future`
            This may be a gathering future of the callbacks to invoke, or it may
            be a completed future object. Regardless, this result will be
            scheduled on the event loop automatically, and does not need to be
            awaited. Awaiting this future will await completion of all invoked
            event handlers.
        """
        if name in self._waiters:
            # Unwrap single or no argument events.
            if len(args) == 1:
                waiter_result_args = args[0]
            elif not args:
                waiter_result_args = None
            else:
                waiter_result_args = args

            for future, predicate in tuple(self._waiters[name].items()):
                try:
                    if predicate(*args):
                        future.set_result(waiter_result_args)
                        del self._waiters[name][future]
                except Exception as ex:
                    future.set_exception(ex)
                    del self._waiters[name][future]

            if not self._waiters[name]:
                del self._waiters[name]

        # Hack to stop PyCharm saying you need to await this function when you do not need to await
        # it.
        future: typing.Any

        if name in self._listeners:
            coros = (self._catch(callback, name, args) for callback in self._listeners[name])
            future = asyncio.gather(*coros)
        else:
            future = completed_future()

        return future

    async def _catch(self, callback, name, args):
        try:
            return await callback(*args)
        except Exception as ex:
            # Pop the top-most frame to remove this _catch call.
            # The user doesn't need it in their traceback.
            ex.__traceback__ = ex.__traceback__.tb_next
            self.handle_exception(ex, name, args, callback)

    def handle_exception(
        self, exception: Exception, event_name: str, args: typing.Sequence[typing.Any], callback: CoroutineFunctionT
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
        event_name: :obj:`str`
            The name of the event that triggered the exception.
        args: :obj:`typing.Sequence` [ :obj:`typing.Any` ]
            The arguments passed to the event that threw an exception.
        callback
            The callback that threw the exception.
        """
        # Do not recurse if a dodgy exception handler is added.
        if event_name != self.exception_event:
            self.logger.exception('Exception occurred in handler for event "%s"', event_name, exc_info=exception)
            ctx = EventExceptionContext(event_name, callback, args, exception)
            self.dispatch(self.exception_event, ctx)
        else:
            self.logger.exception(
                'Exception occurred in handler for event "%s", and the exception has been dropped',
                event_name,
                exc_info=exception,
            )

    def wait_for(
        self, name: str, *, timeout: typing.Optional[float], predicate: typing.Callable[..., bool]
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
        name : :obj:`str`
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
        if name not in self._waiters:
            # This is used as a weakref dict to allow automatically tidying up
            # any future that falls out of scope entirely.
            self._waiters[name] = weakref.WeakKeyDictionary()
        self._waiters[name][future] = predicate
        # noinspection PyTypeChecker
        return asyncio.ensure_future(asyncio.wait_for(future, timeout))


def completed_future(result: typing.Any = None) -> asyncio.Future:
    """Create a future on the current running loop that is completed, then return it.

    Parameters
    ---------
    result : :obj:`typing.Any`
        The value to set for the result of the future.

    Returns
    -------
    :obj:`asyncio.Future`
        The completed future.
    """
    future = asyncio.get_event_loop().create_future()
    future.set_result(result)
    return future
