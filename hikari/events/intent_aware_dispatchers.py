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
"""Event dispatcher implementations that are intent-aware."""
from __future__ import annotations

__all__ = ["IntentAwareEventDispatcherImpl"]

import asyncio
import logging
import typing
import warnings

from hikari import errors
from hikari import intents
from hikari.events import base
from hikari.events import other
from hikari.internal import more_asyncio
from hikari.internal import more_collections
from hikari.events import dispatchers

if typing.TYPE_CHECKING:
    from hikari.internal import more_typing


class IntentAwareEventDispatcherImpl(dispatchers.EventDispatcher):
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

    Events that require a specific intent will trigger warnings on subscription
    if the provided enabled intents are not a superset of this.

    Parameters
    ----------
    enabled_intents : hikari.intents.Intent, optional
        The intents that are enabled for the application. If `None`, then no
        intent checks are performed when subscribing a new event.
    """

    logger: logging.Logger
    """The logger used to write log messages."""

    def __init__(self, enabled_intents: typing.Optional[intents.Intent]) -> None:
        self._enabled_intents = enabled_intents
        self._listeners = {}
        self._waiters = {}
        self.logger = logging.getLogger(type(self).__qualname__)

    def close(self) -> None:
        """Cancel anything that is waiting for an event to be dispatched."""
        self._listeners.clear()
        for waiter in self._waiters.values():
            for future in waiter.keys():
                future.cancel()
        self._waiters.clear()

    def add_listener(
        self, event_type: typing.Type[base.HikariEvent], callback: dispatchers.EventCallbackT, **kwargs
    ) -> dispatchers.EventCallbackT:
        """Register a new event callback to a given event name.

        Parameters
        ----------
        event_type : typing.Type[hikari.events.HikariEvent]
            The event to register to.
        callback : `async def callback(event: HikariEvent) -> ...`
            The event callback to invoke when this event is fired; this can be
            async or non-async.

        Returns
        -------
        async def callback(event: HikariEvent) -> ...
            The callback that was registered.

        Note
        ----
        If you subscribe to an event that requires intents that you do not have
        set, you will receive a warning.
        """
        if not issubclass(event_type, base.HikariEvent):
            raise TypeError("Events must subclass hikari.events.HikariEvent")

        required_intents = base.get_required_intents_for(event_type)
        enabled_intents = self._enabled_intents if self._enabled_intents is not None else 0

        any_intent_match = any(enabled_intents & i == i for i in required_intents)

        if self._enabled_intents is not None and required_intents and not any_intent_match:
            intents_lists = []
            for required in required_intents:
                set_of_intents = []
                for intent in intents.Intent:
                    if required & intent:
                        set_of_intents.append(f"{intent.name} <PRIVILEGED>" if intent.is_privileged else intent.name)
                intents_lists.append(" + ".join(set_of_intents))

            message = (
                f"Event {event_type.__module__}.{event_type.__qualname__} will never be triggered\n"
                f"unless you enable one of the following intents:\n"
                + "\n".join(f"    - {intent_list}" for intent_list in intents_lists)
            )

            warnings.warn(message, category=errors.IntentWarning, stacklevel=kwargs.pop("_stack_level", 1))

        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(callback)

        return callback

    def remove_listener(
        self, event_type: typing.Type[dispatchers.EventT], callback: dispatchers.EventCallbackT
    ) -> None:
        """Remove the given function from the handlers for the given event.

        The name is mandatory to enable supporting registering the same event callback for multiple event types.

        Parameters
        ----------
        event_type : typing.Type[hikari.events.HikariEvent]
            The type of event to remove the callback from.
        callback : `async def callback(event: HikariEvent) -> ...`
            The event callback to remove; this can be async or non-async.
        """
        if event_type in self._listeners and callback in self._listeners[event_type]:
            if len(self._listeners[event_type]) - 1 == 0:
                del self._listeners[event_type]
            else:
                self._listeners[event_type].remove(callback)

    # Do not add an annotation here, it will mess with type hints in PyCharm which can lead to
    # confusing telepathy comments to the user.
    # Additionally, this MUST NOT BE A COROUTINE ITSELF. THIS IS NOT TYPESAFE!
    def dispatch_event(self, event: base.HikariEvent) -> more_typing.Future[typing.Any]:
        """Dispatch a given event to all listeners and waiters that are applicable.

        Parameters
        ----------
        event : hikari.events.HikariEvent
            The event to dispatch.

        Returns
        -------
        asyncio.Future
            This may be a gathering future of the callbacks to invoke, or it may
            be a completed future object. Regardless, this result will be
            scheduled on the event loop automatically, and does not need to be
            awaited. Awaiting this future will await completion of all invoked
            event handlers.
        """
        this_event_type = type(event)
        self.logger.debug("dispatching %s", this_event_type.__name__)

        callback_futures = []

        for base_event_type in this_event_type.mro():
            for callback in self._listeners.get(base_event_type, more_collections.EMPTY_COLLECTION):
                callback_futures.append(asyncio.create_task(self._failsafe_invoke(event, callback)))

            if base_event_type not in self._waiters:
                continue

            # Quicker most of the time to iterate twice, than to copy the entire collection
            # to iterate once after that.
            futures_to_remove = []

            subtype_waiters = self._waiters.get(base_event_type, more_collections.EMPTY_DICT)

            for future, predicate in subtype_waiters.items():
                # We execute async predicates differently to sync, because we hope most of the time
                # these checks will be synchronous only, as these will perform significantly faster.
                # I preferred execution speed over terseness here.
                if asyncio.iscoroutinefunction(predicate):
                    # Reawaken it later once the predicate is complete. We can await this with the
                    # other dispatchers.
                    check_task = asyncio.create_task(self._async_check(future, predicate, event, base_event_type))
                    callback_futures.append(check_task)
                else:
                    try:
                        if predicate(event):
                            # We have to append this to a list, we can't mutate the dict while we iterate over it...
                            future.set_result(event)
                            futures_to_remove.append(future)
                    except Exception as ex:  # pylint:disable=broad-except
                        future.set_exception(ex)
                        futures_to_remove.append(future)

            # We do this after to prevent changes to the dict while iterating causing exceptions.
            for future in futures_to_remove:
                # Off to the garbage collector you go.
                subtype_waiters.pop(future)

            # If there are no waiters left, purge the entire dict.
            if not subtype_waiters:
                self._waiters.pop(base_event_type)

        result = asyncio.gather(*callback_futures) if callback_futures else more_asyncio.completed_future()

        # Stop intellij shenanigans with broken type hints that ruin my day.
        return typing.cast(typing.Any, result)

    async def _async_check(self, future, predicate, event, event_type) -> None:
        # If the predicate returns true, complete the future and pop it from the waiters.
        # By this point we shouldn't be iterating over it anymore, so this is concurrent-modification
        # safe on a single event loop.
        try:
            if await predicate(event):
                future.set_result(event)
                self._waiters[event_type].pop(future)
        except Exception as ex:  # pylint:disable=broad-except
            future.set_exception(ex)
            self._waiters[event_type].pop(future)

    async def _failsafe_invoke(self, event, callback) -> None:
        try:
            result = callback(event)
            if asyncio.iscoroutine(result):
                await result
        except Exception as ex:  # pylint:disable=broad-except
            self.handle_exception(ex, event, callback)

    def handle_exception(
        self,
        exception: Exception,
        event: base.HikariEvent,
        callback: typing.Callable[..., typing.Union[typing.Awaitable[None]]],
    ) -> None:
        """Handle raised exception.

        This allows users to override this with a custom implementation if desired.

        This implementation will check to see if the event that triggered the
        exception is an `hikari.events.ExceptionEvent`. If this
        exception was caused by the `hikari.events.ExceptionEvent`,
        then nothing is dispatched (thus preventing an exception handler recursively
        re-triggering itself). Otherwise, an `hikari.events.ExceptionEvent`
        is dispatched.

        Parameters
        ----------
        exception: Exception
            The exception that triggered this call.
        event: hikari.events.HikariEvent
            The event that was being dispatched.
        callback
            The callback that threw the exception. This may be an event
            callback, or a `wait_for` predicate that threw an exception.
        """
        # Do not recurse if a dodgy exception handler is added.
        if not base.is_no_catch_event(event):
            self.logger.exception(
                'Exception occurred in handler for event "%s"', type(event).__name__, exc_info=exception
            )
            self.dispatch_event(other.ExceptionEvent(exception=exception, event=event, callback=callback))
        else:
            self.logger.exception(
                'Exception occurred in handler for event "%s", and the exception has been dropped',
                type(event).__name__,
                exc_info=exception,
            )

    def wait_for(
        self,
        event_type: typing.Type[dispatchers.EventT],
        *,
        timeout: typing.Optional[float],
        predicate: dispatchers.PredicateT,
    ) -> more_typing.Future:
        """Wait for a event to occur once and then return the arguments the event was called with.

        Events can be filtered using a given predicate function. If unspecified,
        the first event of the given name will be a match.

        Every event that matches the event name that the bot receives will be
        checked. Thus, if you need to wait for events in a specific guild or
        channel, or from a specific person, you want to give a predicate that
        checks this.

        Parameters
        ----------
        event_type : typing.Type[hikari.events.HikariEvent]
            The name of the event to wait for.
        timeout : float, optional
            The timeout to wait for before cancelling and raising an
            `asyncio.TimeoutError` instead. If this is `None`, this will
            wait forever. Care must be taken if you use `None` as this may
            leak memory if you do this from an event listener that gets
            repeatedly called. If you want to do this, you should consider
            using an event listener instead of this function.
        predicate : `def predicate(event) -> bool`
            A function that takes the arguments for the event and returns True
            if it is a match, or False if it should be ignored. This must be
            a regular function.

        Returns
        -------
        asyncio.Future
            A future that when awaited will provide a the arguments passed to
            the first matching event. If no arguments are passed to the event,
            then `None` is the result. If one argument is passed to the event,
            then that argument is the result, otherwise a tuple of arguments is
            the result instead.

        !!! note
            Awaiting this result will raise an `asyncio.TimeoutError` if the
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
