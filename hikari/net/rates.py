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
"""
Rate-limiting adherence logic.
"""
from __future__ import annotations

import asyncio
import collections
import contextlib
import time
import typing

from hikari.internal_utilities import assertions


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

    __slots__ = ["_total", "_per", "_remaining", "reset_at", "_queue", "loop"]

    def __init__(self, total: int, per: float, loop: asyncio.AbstractEventLoop) -> None:
        self._total = total
        self._per = per
        self._remaining = total
        self.reset_at = time.perf_counter() + per
        # We repeatedly push to the rear and pop from the front, and iterate. We don't need random access, and O(k)
        # pushes and shifts are more desirable given this is a doubly linked list underneath.
        self._queue: typing.Deque[asyncio.Future] = collections.deque()
        self.loop = assertions.assert_not_none(loop)

    @property
    def is_limiting(self) -> bool:
        """True if the rate limit is preventing any requests for now, or False if it is yet to lock down."""
        return not self._remaining

    async def acquire(self, on_rate_limit: typing.Callable[[], None] = None, **kwargs) -> None:
        """
        Acquire a slice of time in this bucket. This may return immediately, or it may wait for a slot to become
        available.

        Args:
            on_rate_limit:
                Optional callback to invoke if we are being rate-limited.
            **kwargs:
                kwargs to call the callback with.
        """
        future = self._enqueue()
        try:
            if not self._maybe_awaken_and_reset(future) and on_rate_limit is not None:
                on_rate_limit(**kwargs)
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

        if self.reset_at < now:
            # Reset the time-slice.
            self._remaining = self._total
            self.reset_at = now + self._per

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
            delay = max(0.0, self.reset_at - now)
            self.loop.call_later(delay, self._maybe_awaken_and_reset, this_future)
            return False
        return True

    async def __aenter__(self) -> "TimedTokenBucket":
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
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

    __slots__ = ["_total", "_remaining", "_last_reset_at", "_reset_at", "_per", "_queue", "loop"]

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
        self.loop = assertions.assert_not_none(loop)

    @property
    def is_limiting(self) -> bool:
        """True if the rate limit is preventing any requests for now, or False if it is yet to lock down."""
        return not self._remaining

    async def acquire(self, on_rate_limit: typing.Callable[[], None] = None, **kwargs) -> None:
        """
        Acquire a slice of time in this bucket. This may return immediately, or it may wait for a slot to become
        available.

        Args:
            on_rate_limit:
                Optional callback to invoke if we are being rate-limited.
            **kwargs:
                kwargs to call the callback with.
        """
        future = self._enqueue()
        try:
            if not self._maybe_awaken_and_reset(future) and on_rate_limit is not None:
                on_rate_limit(**kwargs)
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
            self.update(self._total, self._total, now, now + self._per, is_nested_call=True)

        while self._remaining > 0 and self._queue:
            # Wake up some older tasks while/if we can.
            self._remaining -= 1
            next_future = self._queue.popleft()
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
        self._per = reset_at - now
        self._reset_at = real_now + self._per
        self._last_reset_at = real_now

        if should_reassess and not is_nested_call:
            self._reassess()

    async def __aenter__(self) -> "VariableTokenBucket":
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        pass


class TimedLatchBucket(contextlib.AbstractAsyncContextManager):
    """
    A global latch that can be locked for a given time. If the latch is open, then
    acquiring the latch does not do anything and finishes immediately. If the latch is
    locked, then acquiring the latch will force the caller to wait until it is unlocked.

    Args:
        loop:
            The loop to run on.
    """

    __slots__ = ["_locked", "_unlock_event", "loop"]

    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        self._locked = False
        self._unlock_event = asyncio.Event()
        self.loop = assertions.assert_not_none(loop)

    @property
    def is_limiting(self) -> bool:
        """True if the latch is preventing any requests for now, or False if it is yet to lock down."""
        return self._locked

    async def acquire(self, if_locked: typing.Callable[..., None] = None, **kwargs):
        """
        Either continue silently if the latch is unlocked, or wait for it to unlock first if locked.

        Args:
            if_locked:
                callback to invoke when the latch is locked.
            **kwargs:
                kwargs to call the callback with.

        """
        if self._locked:
            if if_locked is not None:
                if_locked(**kwargs)
            await self._unlock_event.wait()

    def lock(self, unlock_after: float) -> None:
        """
        Acquire the lock on the given TimedLatchBucket, and request that it is revoked after a given period of time.

        Args:
            unlock_after:
                The time in seconds to remove the lock after.
        """
        self._locked = True
        self._unlock_event.clear()
        task = asyncio.shield(asyncio.sleep(unlock_after))
        task.add_done_callback(lambda *_: self.unlock())

    def unlock(self) -> None:
        """
        Manually unlock the TimedLatchBucket.
        """
        self._locked = False
        self._unlock_event.set()

    async def __aenter__(self) -> "TimedLatchBucket":
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


__all__ = ("TimedLatchBucket", "TimedTokenBucket", "VariableTokenBucket")
