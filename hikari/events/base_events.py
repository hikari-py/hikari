# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021-present davfsa
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
"""Base types and functions for events in Hikari."""
from __future__ import annotations

__all__: typing.Sequence[str] = (
    "Event",
    "ExceptionEvent",
    "EventT",
    "is_no_recursive_throw_event",
    "no_recursive_throw",
    "get_required_intents_for",
    "requires_intents",
)

import abc
import inspect
import typing

import attrs

from hikari import intents
from hikari import traits
from hikari.api import shard as gateway_shard
from hikari.internal import attrs_extensions

if typing.TYPE_CHECKING:
    import types

    _T = typing.TypeVar("_T")

REQUIRED_INTENTS_attrs: typing.Final[str] = "___requiresintents___"
NO_RECURSIVE_THROW_attrs: typing.Final[str] = "___norecursivethrow___"

_id_counter = 1  # We start at 1 since Event is 0


class Event(abc.ABC):
    """Base event type that all Hikari events should subclass."""

    __slots__: typing.Sequence[str] = ()

    __dispatches: typing.ClassVar[typing.Tuple[typing.Type[Event], ...]]
    __bitmask: typing.ClassVar[int]

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        # hasattr doesn't work with private variables in this case so we use a try except.
        # We need to set Event's __dispatches when the first subclass is made as Event cannot
        # be included in a tuple literal on itself due to not existing yet.
        try:
            Event.__dispatches
        except AttributeError:
            Event.__dispatches = (Event,)
            Event.__bitmask = 1 << 0

        global _id_counter

        mro = cls.mro()
        # We don't have to explicitly include Event here as issubclass(Event, Event) returns True.
        # Non-event classes should be ignored.
        cls.__dispatches = tuple(sub_cls for sub_cls in mro if issubclass(sub_cls, Event))
        cls.__bitmask = 1 << _id_counter
        _id_counter += 1

    @property
    @abc.abstractmethod
    def app(self) -> traits.RESTAware:
        """App instance for this application."""

    @classmethod
    def dispatches(cls) -> typing.Sequence[typing.Type[Event]]:
        """Sequence of the event classes this event is dispatched as."""
        return cls.__dispatches

    @classmethod
    def bitmask(cls) -> int:
        """Bitmask for this event."""
        return cls.__bitmask


def get_required_intents_for(event_type: typing.Type[Event]) -> typing.Collection[intents.Intents]:
    """Retrieve the intents that are required to listen to an event type.

    Parameters
    ----------
    event_type : typing.Type[Event]
        The event type to get required intents for.

    Returns
    -------
    typing.Collection[hikari.intents.Intents]
        Collection of acceptable subset combinations of intent needed to
        be able to receive the given event type.
    """
    result = getattr(event_type, REQUIRED_INTENTS_attrs, ())
    assert isinstance(result, typing.Collection)
    return result


def requires_intents(first: intents.Intents, *rest: intents.Intents) -> typing.Callable[[_T], _T]:
    """Decorate an event type to define what intents it requires.

    Parameters
    ----------
    first : hikari.intents.Intents
        First combination of intents that are acceptable in order to receive
        the decorated event type.
    *rest : hikari.intents.Intents
        Zero or more additional combinations of intents to require for this
        event to be subscribed to.
    """

    def decorator(cls: _T) -> _T:
        required_intents = [first, *rest]
        setattr(cls, REQUIRED_INTENTS_attrs, required_intents)
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


def no_recursive_throw() -> typing.Callable[[_T], _T]:
    """Decorate an event type to indicate errors should not be handled.

    This is useful for exception event types that you do not want to
    have invoked recursively.
    """

    def decorator(cls: _T) -> _T:
        setattr(cls, NO_RECURSIVE_THROW_attrs, True)
        doc = inspect.getdoc(cls) or ""
        doc += (
            "\n"
            "!!! warning\n"
            "    Any exceptions raised by handlers for this event will be dumped to the\n"
            "    application logger and silently discarded, preventing recursive loops\n"
            "    produced by faulty exception event handling. Thus, it is imperative\n"
            "    that you ensure any exceptions are explicitly caught within handlers\n"
            "    for this event if they may occur.\n"
        )
        cls.__doc__ = doc
        return cls

    return decorator


def is_no_recursive_throw_event(obj: typing.Union[_T, typing.Type[_T]]) -> bool:
    """Whether the event is marked as `___norecursivethrow___`."""
    result = getattr(obj, NO_RECURSIVE_THROW_attrs, False)
    assert isinstance(result, bool)
    return result


EventT = typing.TypeVar("EventT", bound=Event)
FailedCallbackT = typing.Callable[[EventT], typing.Coroutine[typing.Any, typing.Any, None]]


@no_recursive_throw()
@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
class ExceptionEvent(Event, typing.Generic[EventT]):
    """Event that is raised when another event handler raises an [`Exception`][].

    !!! note
        Only exceptions that derive from [`Exception`][] will be caught.
        Other exceptions outside this range will propagate past this callback.
        This prevents event handlers interfering with critical exceptions
        such as [`KeyboardInterrupt`][] which would have potentially undesired
        side-effects on the application runtime.
    """

    exception: Exception = attrs.field()
    """Exception that was raised."""

    failed_event: EventT = attrs.field()
    """Event instance that caused the exception."""

    failed_callback: FailedCallbackT[EventT] = attrs.field()
    """Event callback that threw an exception."""

    @property
    def app(self) -> traits.RESTAware:
        # <<inherited docstring from Event>>.
        return self.failed_event.app

    @property
    def shard(self) -> typing.Optional[gateway_shard.GatewayShard]:
        """Shard that received the event, if there was one associated.

        This may be [`None`][] if no specific shard was the cause of this
        exception (e.g. when starting up or shutting down).
        """
        shard = getattr(self.failed_event, "shard", None)
        if isinstance(shard, gateway_shard.GatewayShard):
            return shard
        return None

    @property
    def exc_info(self) -> typing.Tuple[typing.Type[Exception], Exception, typing.Optional[types.TracebackType]]:
        """Exception triplet that follows the same format as [`sys.exc_info`][].

        The [`sys.exc_info`][] triplet consists of the exception type, the exception
        instance, and the traceback of the exception.
        """
        return type(self.exception), self.exception, self.exception.__traceback__

    async def retry(self) -> None:
        """Invoke the failed event again.

        If an exception is thrown this time, it will need to be manually
        caught in-code, or will be discarded.
        """
        await self.failed_callback(self.failed_event)
