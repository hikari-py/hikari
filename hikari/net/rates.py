#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rate-limiting adherence logic.
"""
import collections
import time

from hikari.compat import asyncio
from hikari.compat import contextlib
from hikari.compat import typing


class TimedTokenBucket(contextlib.AbstractAsyncContextManager):
    """
    A bucket implementation that has a fixed-width time-frame that a specific number of tasks can run within. Any others
    are forced to wait for a slot to become available in the order that they are requested.

    Args:
        total:
            Total number of tasks to allow to run per window.
        per:
            Time that the limit applies for before resetting.
        loop:
            Event loop to run on.
    """

    def __init__(self, total: int, per: float, loop: asyncio.AbstractEventLoop) -> None:
        self._total = total
        self._per = per
        self._remaining = total
        self._reset_at = time.perf_counter() + per
        # We repeatedly push to the rear and pop from the front, and iterate. We don't need random access, and O(k)
        # pushes and shifts are more desirable given this is a doubly linked list underneath.
        self._queue: typing.Deque[asyncio.Future] = collections.deque()
        self.loop = loop

    async def acquire(self, on_rate_limit: typing.Callable[[], None] = None) -> None:
        """
        Acquire a slice of time in this bucket. This may return immediately, or it may wait for a slot to become
        available.

        Args:
            on_rate_limit:
                Optional callback to invoke if we are being rate-limited.
        """
        future = self._enqueue()
        try:
            if not self._maybe_awaken_and_reset(future) and on_rate_limit is not None:
                on_rate_limit()
            await future
        finally:
            future.cancel()

    def _enqueue(self) -> asyncio.Future:
        future = self.loop.create_future()
        self._queue.append(future)
        return future

    def _reassess(self) -> None:
        """Potentially reset the rate limit if we are able to, and possibly reawaken some futures in the process."""
        now = time.perf_counter()

        if self._reset_at < now:
            # Reset the time-slice.
            self._remaining = self._total
            self._reset_at = now + self._per

        while self._remaining > 0 and self._queue:
            # Wake up some older tasks while/if we can.
            next_future = self._queue.popleft()
            self._remaining -= 1
            next_future.set_result(None)

    def _maybe_awaken_and_reset(self, this_future: asyncio.Future) -> bool:
        """
        Potentially reset the rate-limits and awaken waiting futures, and reschedule this call if needed later.

        Returns:
            True if this future can run immediately, or False if it is rate limited.
        """
        self._reassess()

        # We can't really use call_at here, since that assumes perf_counter and loop.time produce the same
        # timestamps. We can, however, sleep for an approximate period of time instead.
        # We "recursively" recall later to prevent busy-waiting.
        if not this_future.done():
            now = time.perf_counter()
            delay = max(0.0, self._reset_at - now)
            self.loop.call_later(delay, self._maybe_awaken_and_reset, this_future)
            return False
        else:
            return True

    async def __aenter__(self):
        await self.acquire()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class VariableTokenBucket(contextlib.AbstractAsyncContextManager):
    """
    A bucket implementation that has a fixed-width time-frame that a specific number of tasks can run within. Any others
    are forced to wait for a slot to become available in the order that they are requested. This works differently to
    :class:`TimedTokenBucket` in that it can be adjusted to change the rate of limitation.

    Args:
        total:
            Total number of tasks to allow to run per window.
        remaining:
            Remaining bucket slots to fill.
        reset_at:
            The time relative to `now` to reset at.
        loop:
            Event loop to run on.
    """

    def __init__(
        self, total: int, remaining: int, now: float, reset_at: float, loop: asyncio.AbstractEventLoop
    ) -> None:
        self._total = total
        self._remaining = remaining
        real_now = time.perf_counter()
        self._last_reset_at = real_now
        self._reset_at = (reset_at - now) + real_now
        self._per = reset_at - now
        # We repeatedly push to the rear and pop from the front, and iterate. We don't need random access, and O(k)
        # pushes and shifts are more desirable given this is a doubly linked list underneath.
        self._queue: typing.Deque[asyncio.Future] = collections.deque()
        self.loop = loop

    async def acquire(self, on_rate_limit: typing.Callable[[], None] = None) -> None:
        """
        Acquire a slice of time in this bucket. This may return immediately, or it may wait for a slot to become
        available.

        Args:
            on_rate_limit:
                Optional callback to invoke if we are being rate-limited.
        """
        future = self._enqueue()
        try:
            if not self._maybe_awaken_and_reset(future) and on_rate_limit is not None:
                on_rate_limit()
            await future
        finally:
            future.cancel()

    def _enqueue(self) -> asyncio.Future:
        future = self.loop.create_future()
        self._queue.append(future)
        return future

    def _reassess(self) -> None:
        """Potentially reset the rate limit if we are able to, and possibly reawaken some futures in the process."""
        now = time.perf_counter()

        if self._reset_at < now:
            # Reset the time-slice.
            now = time.perf_counter()
            self.update(self._total, self._total, now, self._per, is_nested_call=True)

        while self._remaining > 0 and self._queue:
            # Wake up some older tasks while/if we can.
            next_future = self._queue.popleft()
            self._remaining -= 1
            next_future.set_result(None)

    def _maybe_awaken_and_reset(self, this_future: asyncio.Future) -> bool:
        """
        Potentially reset the rate-limits and awaken waiting futures, and reschedule this call if needed later.

        Returns:
            True if this future can run immediately, or False if it is rate limited.
        """
        self._reassess()

        # We can't really use call_at here, since that assumes perf_counter and loop.time produce the same
        # timestamps. We can, however, sleep for an approximate period of time instead.
        # We "recursively" recall later to prevent busy-waiting.
        if not this_future.done():
            now = time.perf_counter()
            delay = max(0.0, self._reset_at - now)
            self.loop.call_later(delay, self._maybe_awaken_and_reset, this_future)
            return False
        else:
            return True

    def update(self, total: int, remaining: int, now: float, reset_at: float, is_nested_call: bool = False):
        """
        Reset the limit data.

        Args:
            total:
                The total slots to allow in the window.
            remaining:
                The remaining number of slots.
            now:
                The current :func:`time.perf_counter` value.
            reset_at:
                The time to reset the limit again.
            is_nested_call:
                Should always be false, this is only set to `True` internally.
        """
        should_reassess = remaining > self._remaining

        real_now = time.perf_counter()
        self._total = total
        self._remaining = remaining
        self._reset_at = (reset_at - now) + real_now
        self._last_reset_at = real_now

        if should_reassess and not is_nested_call:
            self._reassess()

    async def __aenter__(self):
        await self.acquire()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
