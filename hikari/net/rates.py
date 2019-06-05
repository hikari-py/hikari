#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rate-limiting adherence logic.
"""
import abc
import collections
import time

from hikari.compat import asyncio
from hikari.compat import contextlib
from hikari.compat import typing


class Bucket(contextlib.AbstractAsyncContextManager):
    """Abstract core functionality required by a Bucket implementation."""

    _reset_at: float
    _queue: typing.Deque[asyncio.Future]
    loop: asyncio.AbstractEventLoop

    def __len__(self):
        """Number of elements in the queue backlog."""
        return len(self._queue)

    async def acquire(self) -> None:
        """
        Acquire a slice of time in this bucket. This may return immediately, or it may wait for a slot to become
        available.
        """
        future = self._enqueue()
        try:
            self._maybe_awaken_and_reset(future)
            await future
        finally:
            future.cancel()

    def _enqueue(self) -> asyncio.Future:
        future = self.loop.create_future()
        self._queue.append(future)
        return future

    def _maybe_awaken_and_reset(self, this_future: asyncio.Future):
        """Potentially reset the rate-limits and awaken waiting futures, and reschedule this call if needed later."""
        self._reassess()

        # We can't really use call_at here, since that assumes perf_counter and loop.time produce the same
        # timestamps. We can, however, sleep for an approximate period of time instead.
        # We "recursively" recall later to prevent busy-waiting.
        if not this_future.done():
            now = time.perf_counter()
            delay = max(0.0, self._reset_at - now)
            self.loop.call_later(delay, self._maybe_awaken_and_reset, this_future)

    async def __aenter__(self):
        await self.acquire()
        return None

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    @abc.abstractmethod
    def _reassess(self):
        """Activate any futures required if the time is right."""


class TimedTokenBucket(Bucket):
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
        self._reset_at = time.perf_counter()
        # We repeatedly push to the rear and pop from the front, and iterate. We don't need random access, and O(k)
        # pushes and shifts are more desirable given this is a doubly linked list underneath.
        self._queue = collections.deque()
        self.loop = loop

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


class VariableTokenBucket(Bucket):
    """
    A bucket implementation that has a fixed-width time-frame that a specific number of tasks can run within. Any others
    are forced to wait for a slot to become available in the order that they are requested.

    Args:
        total:
            Total number of tasks to allow to run per window.
        remaining:
            Remaining bucket slots to fill.
        reset_at:
            The time (relative to :func:`time.perf_counter` specifically) to reset the ratelimit at.
        loop:
            Event loop to run on.
    """

    def __init__(self, total: int, remaining: int, reset_at: float, loop: asyncio.AbstractEventLoop) -> None:
        self._total = total
        self._remaining = remaining
        self._last_reset_at = time.perf_counter()
        self._reset_at = reset_at
        # We repeatedly push to the rear and pop from the front, and iterate. We don't need random access, and O(k)
        # pushes and shifts are more desirable given this is a doubly linked list underneath.
        self._queue: typing.Deque[asyncio.Future] = collections.deque()
        self.loop = loop

    def _reassess(self) -> None:
        """Potentially reset the rate limit if we are able to, and possibly reawaken some futures in the process."""
        now = time.perf_counter()

        if self._reset_at < now:
            # Reset the time-slice.
            now = time.perf_counter()
            delta = self._reset_at - self._last_reset_at
            self.update(self._total, self._total, now, delta)

        while self._remaining > 0 and self._queue:
            # Wake up some older tasks while/if we can.
            next_future = self._queue.popleft()
            self._remaining -= 1
            next_future.set_result(None)

    def update(self, total: int, remaining: int, now: float, delta: float):
        """
        Reset the limit data.

        Args:
            total:
                The total slots to allow in the window.
            remaining:
                The remaining number of slots.
            now:
                The current :func:`time.perf_counter` value.
            delta:
                The time to wait before resetting the window.
        """
        should_reassess = remaining > self._remaining

        self._total = total
        self._remaining = remaining
        self._last_reset_at = now
        self._reset_at = now + delta

        if should_reassess:
            self._reassess()
