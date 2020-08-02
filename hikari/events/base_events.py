# -*- coding: utf-8 -*-
# cython: language_level=3
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
"""Base types and functions for events in Hikari."""
from __future__ import annotations

__all__: typing.Final[typing.List[str]] = [
    "Event",
    "ExceptionEvent",
    "is_no_recursive_throw_event",
    "no_recursive_throw",
    "get_required_intents_for",
    "requires_intents",
]

import abc
import inspect
import typing

import attr

from hikari.api import shard as gateway_shard
from hikari.models import intents

if typing.TYPE_CHECKING:
    import types

    from hikari.api import event_consumer


T = typing.TypeVar("T")
REQUIRED_INTENTS_ATTR: typing.Final[str] = "___requiresintents___"
NO_RECURSIVE_THROW_ATTR: typing.Final[str] = "___norecursivethrow___"


@attr.s(kw_only=True, slots=True, weakref_slot=False)
class Event(abc.ABC):
    """Base event type that all Hikari events should subclass."""

    @property
    @abc.abstractmethod
    def app(self) -> event_consumer.IEventConsumerApp:
        """App instance for this application.

        Returns
        -------
        hikari.api.event_consumer.IEventConsumerApp
            The app containing the event consumer component.
        """


def get_required_intents_for(event_type: typing.Type[Event]) -> typing.Collection[intents.Intent]:
    """Retrieve the intents that are required to listen to an event type.

    Parameters
    ----------
    event_type : typing.Type[Event]
        The event type to get required intents for.

    Returns
    -------
    typing.Collection[hikari.models.intents.Intent]
        Collection of acceptable subset combinations of intent needed to
        be able to receive the given event type.
    """
    return typing.cast(typing.Collection[typing.Any], getattr(event_type, REQUIRED_INTENTS_ATTR, ()))


def requires_intents(first: intents.Intent, *rest: intents.Intent) -> typing.Callable[[T], T]:
    """Decorate an event type to define what intents it requires.

    Parameters
    ----------
    first : hikari.models.intents.Intent
        First combination of intents that are acceptable in order to receive
        the decorated event type.
    *rest : hikari.models.intents.Intent
        Zero or more additional combinations of intents to require for this
        event to be subscribed to.
    """

    def decorator(cls: T) -> T:
        required_intents = [first, *rest]
        setattr(cls, REQUIRED_INTENTS_ATTR, required_intents)
        doc = inspect.getdoc(cls) or ""
        doc += "\n\nThis requires one of the following combinations of intents in order to be dispatched:\n\n"
        for intent_group in required_intents:
            preview = " + ".join(
                f"`{type(i).__module__}.{type(i).__qualname__}.{i.name}`" for i in intent_group.split()
            )
            doc += f" - {preview}\n"

        cls.__doc__ = doc
        return cls

    return decorator


def no_recursive_throw() -> typing.Callable[[typing.Type[T]], typing.Type[T]]:
    """Decorate an event type to indicate errors should not be handled.

    This is useful for exception event types that you do not want to
    have invoked recursively.
    """

    def decorator(cls: typing.Type[T]) -> typing.Type[T]:
        setattr(cls, NO_RECURSIVE_THROW_ATTR, True)
        doc = inspect.getdoc(cls) or ""
        doc += inspect.cleandoc(
            """\n\n
            !!! warning
                Any exceptions raised by handlers for this event will be dumped to the
                application logger and silently discarded, preventing recursive loops
                produced by faulty exception event handling. Thus, it is imperative
                that you ensure any exceptions are explicitly caught within handlers
                for this event if they may occur.
        """
        )
        cls.__doc__ = doc
        return cls

    return decorator


def is_no_recursive_throw_event(obj: typing.Union[T, typing.Type[T]]) -> bool:
    """Return True if this event is marked as `___norecursivethrow___`."""
    return typing.cast(bool, getattr(obj, NO_RECURSIVE_THROW_ATTR, False))


FailedEventT = typing.TypeVar("FailedEventT", bound=Event)
FailedCallbackT = typing.Callable[[FailedEventT], typing.Coroutine[typing.Any, typing.Any, None]]


@no_recursive_throw()
@attr.s(kw_only=True, slots=True, weakref_slot=False)
class ExceptionEvent(Event, typing.Generic[FailedEventT]):
    """Event that is raised when another event handler raises an `Exception`.

    !!! note
        Only exceptions that derive from `builtins.Exception` will be caught.
        Other exceptions outside this range will propagate past this callback.
        This prevents event handlers interfering with critical exceptions
        such as `KeyboardError` which would have potentially undesired
        side-effects on the application runtime.
    """

    app: event_consumer.IEventConsumerApp = attr.ib()
    # <<inherited docstring from Event>>.

    shard: typing.Optional[gateway_shard.IGatewayShard] = attr.ib()
    """Shard that received the event.

    Returns
    -------
    hikari.api.shard.IGatewayShard
        Shard that raised this exception.

        This may be `builtins.None` if no specific shard was the cause of this
        exception (e.g. when starting up or shutting down).
    """

    exception: Exception = attr.ib()
    """Exception that was raised.

    Returns
    -------
    builtins.Exception
        Exception that was raised in the event handler.
    """

    failed_event: FailedEventT = attr.ib()
    """Event instance that caused the exception.

    Returns
    -------
    hikari.events.base_events.Event
        Event that was being processed when the exception occurred.
    """

    # MyPy thinks the attr.ib type hint on the `failed_callback` implies it is a function
    # defined in class scope, and thus thinks referring to it will make it a bound method.
    # To get around this, we make this attribute hidden and make a property that casts it
    # for us to remove this effect. This functionally changes nothing but it helps MyPy.
    _failed_callback: FailedCallbackT = attr.ib()

    @property
    def failed_callback(self) -> FailedCallbackT:
        """Event callback that threw an exception.

        Returns
        -------
        callback
            Event callback that failed execution.
        """
        return self._failed_callback

    @property
    def exc_info(self) -> typing.Tuple[typing.Type[Exception], Exception, typing.Optional[types.TracebackType]]:
        """Exception triplet that follows the same format as `sys.exc_info`.

        Returns
        -------
        builtins.tuple[typing.Type[Exception], Exception, types.TracebackType or builtins.None]
            The `sys.exc_info`-compatible tuple of the exception type, the
            exception instance, and the traceback of the exception.
        """
        return type(self.exception), self.exception, self.exception.__traceback__

    async def retry(self) -> None:
        """Invoke the failed event again.

        If an exception is thrown this time, it will need to be manually
        caught in-code, or will be discarded.
        """
        await self._failed_callback(self.failed_event)
