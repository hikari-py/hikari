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
"""Streamers used for asynchronously iterating through gateway events."""

from __future__ import annotations

__all__: typing.List[str] = ["Streamer", "EventStream"]

import abc
import asyncio
import logging
import typing
import weakref

from hikari import iterators

if typing.TYPE_CHECKING:
    import types

    from hikari import traits
    from hikari.events import base_events  # noqa F401 - Unused (False positive)

EventT = typing.TypeVar("EventT", bound="base_events.Event")
_LOGGER: typing.Final[logging.Logger] = logging.getLogger("hikari")


class Streamer(iterators.LazyIterator[EventT], abc.ABC):
    """A base abstract class for all event streamers.

    Unlike `hikari.iterators.LazyIterator` (which this extends), an event
    streamer must be started and closed.

    Examples
    --------
    A streamer may either be started and closed using `async with` syntax
    where `Streamer.open` and `Streamer.close` are implicitly called based on
    context.

    ```py
    async with Streamer(app, EventType, timeout=50) as stream:
        async for entry in stream:
            ...
    ```

    A streamer may also be directly started and closed using the `Streamer.close`
    and `Streamer.open`. Note that if you don't call `Streamer.close` after
    opening a streamer when you're finished with it then it may queue events
    events in memory indefinitely.

    ```py
    stream = Streamer(app, EventType, timeout=50)
    await stream.open()
    async for event in stream:
        ...

    await stream.close()
    ```

    See Also
    --------
    LazyIterator: `hikari.iterators.LazyIterator`
    """

    @abc.abstractmethod
    async def close(self) -> None:
        """Mark this streamer as closed to stop it from queueing and receiving events.

        If called on an already closed streamer then this will do nothing.

        !!! note
            `async with streamer` may be used as a short-cut for opening and
            closing a streamer.
        """

    @abc.abstractmethod
    async def open(self) -> None:
        """Mark this streamer as opened to let it start receiving and queueing events.

        If called on an already started streamer then this will do nothing.

        !!! note
            `async with streamer` may be used as a short-cut for opening and
            closing a stream.
        """

    async def __aenter__(self) -> Streamer[EventT]:
        await self.open()
        return self

    async def __aexit__(
        self,
        exc_type: typing.Optional[typing.Type[BaseException]],
        exc: typing.Optional[BaseException],
        exc_tb: typing.Optional[types.TracebackType],
    ) -> None:
        await self.close()

    def __enter__(self) -> typing.NoReturn:
        # This is async only.
        cls = type(self)
        raise TypeError(f"{cls.__module__}.{cls.__qualname__} is async-only, did you mean 'async with'?") from None

    def __exit__(self, exc_type: typing.Type[Exception], exc_val: Exception, exc_tb: types.TracebackType) -> None:
        return None


def _generate_weak_listener(
    reference: weakref.WeakMethod,
) -> typing.Callable[[EventT], typing.Coroutine[typing.Any, typing.Any, None]]:
    async def call_weak_method(event: EventT) -> None:
        method = reference()
        if method is None:
            raise TypeError(
                "dead weak referenced subscriber method cannot be executed, try actually closing your event streamers"
            )

        await method(event)

    return call_weak_method


class EventStream(Streamer[EventT]):
    """An implementation of an event `Streamer` class.

    !!! note
        While calling `EventStream.filter` on an active "opened" event stream
        will return a wrapping lazy iterator, calling it on an inactive "closed"
        event stream will return the event stream and add the given predicates
        to the streamer.
    """

    __slots__ = (
        "_active",
        "_event_manager",
        "_event_type",
        "_filters",
        "_queue",
        "_registered_listener",
        "_timeout",
    )

    def __init__(
        self,
        app: traits.EventManagerAware,
        event_type: typing.Type[EventT],
        *,
        timeout: typing.Union[float, int, None],
        limit: typing.Optional[int] = None,
    ) -> None:
        self._event_manager = app.event_manager
        self._active = False
        self._event_type = event_type
        self._filters: iterators.All[EventT] = iterators.All(())
        # We accept `None` to represent unlimited here to be consistent with how `None` is already used to represent
        # unlimited for timeout in other places.
        self._queue: asyncio.Queue[EventT] = asyncio.Queue(limit or 0)
        self._registered_listener: typing.Optional[
            typing.Callable[[EventT], typing.Coroutine[typing.Any, typing.Any, None]]
        ] = None
        # The registered wrapping function for the weak ref to this class's _listener method.
        self._timeout = timeout

    async def _listener(self, event: EventT) -> None:
        if not self._filters(event):
            return

        try:
            self._queue.put_nowait(event)
        except asyncio.QueueFull:
            pass

    async def __anext__(self) -> EventT:
        if not self._active:
            raise TypeError("stream must be started with `async with` before entering it")

        try:
            return await asyncio.wait_for(self._queue.get(), timeout=self._timeout)
        except asyncio.TimeoutError:
            raise StopAsyncIteration from None

    async def _await_all(self) -> typing.Sequence[EventT]:
        await self.open()
        result = [event async for event in self]
        await self.close()
        return result

    def __await__(self) -> typing.Generator[None, None, typing.Sequence[EventT]]:
        return self._await_all().__await__()

    def __del__(self) -> None:
        # For the sake of protecting highly intelligent people who forget to close this, we register the event listener
        # with a weakref then try to close this on deletion. While this may lead to their consoles being spammed, this
        # is a small price to pay as it'll be way more obvious what's wrong than if we just left them with a vague
        # ominous memory leak.
        if self._active:
            _LOGGER.warning("active %r streamer fell out of scope before being closed", self._event_type.__name__)
            try:
                asyncio.ensure_future(self.close())
            except RuntimeError:
                pass

    async def close(self) -> None:
        if self._active and self._registered_listener is not None:
            try:
                self._event_manager.unsubscribe(self._event_type, self._registered_listener)
            except ValueError:
                pass

            self._registered_listener = None

        self._active = False

    def filter(
        self,
        *predicates: typing.Union[typing.Tuple[str, typing.Any], typing.Callable[[EventT], bool]],
        **attrs: typing.Any,
    ) -> typing.Union[EventStream[EventT], iterators.LazyIterator[EventT]]:
        if self._active:
            return super().filter(*predicates, **attrs)

        self._filters |= self._map_predicates_and_attr_getters("filter", *predicates, **attrs)
        return self

    async def open(self) -> None:
        if not self._active:
            # For the sake of protecting highly intelligent people who forget to close this, we register the event
            # listener with a weakref then try to close this on deletion. While this may lead to their consoles being
            # spammed, this is a small price to pay as it'll be way more obvious what's wrong than if we just left them
            # with a vague ominous memory leak.
            reference = weakref.WeakMethod(self._listener)  # type: ignore[arg-type]
            listener = _generate_weak_listener(reference)
            self._registered_listener = listener
            self._event_manager.subscribe(self._event_type, listener)
            self._active = True
