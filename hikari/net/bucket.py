#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import collections
import time
import typing

from hikari import compat


class LeakyBucket(compat.contextlib.AbstractAsyncContextManager):
    """
    Implementation of a fixed-rate leaky-bucket rate-limiting algorithm.

    Args:
        max_capacity:
            Max number of items to await the cool-off for before considering the bucket to be full.
        empty_time:
            The time taken to empty a single unit from the bucket after adding it.
        loop:
            The asyncio event loop to run on.

    Inspired by:
        https://stackoverflow.com/a/45502319 - Throttling Async Functions in Python Asyncio (4 Aug 2017)

    Note:
        This algorithm favours small bucket quantities and will have a higher probability of running a smaller
        task before a larger one if the bucket is near to max capacity.
    """

    __slots__ = ("max_capacity", "loop", "_empty_rate", "_level", "_last_check", "_queue", "_full_event")

    def __init__(self, max_capacity: float, empty_time: float, loop: asyncio.AbstractEventLoop) -> None:
        self.max_capacity = max_capacity
        self.loop = loop
        #: Only used during testing.
        self._full_event = asyncio.Event(loop=loop)

        #: The rate at which the bucket empties, per second.
        self._empty_rate = max_capacity / empty_time
        #: A measure of the current "fullness" of the bucket.
        self._level = 0.0
        #: The time the bucket was last checked. Uses the high precision system clock.
        self._last_check = 0
        #: Queue of tasks waiting to do meaningful work.
        self._queue: typing.Dict[asyncio.Task, asyncio.Future] = collections.OrderedDict()

    @property
    def level(self) -> float:
        """Return the bucket current level."""
        return self._level

    @property
    def backlog(self) -> int:
        """Return the number of tasks in the backlog waiting for room to fill the bucket."""
        return len(self._queue)

    def _leak(self) -> None:
        """Empty out the bucket."""
        now = time.perf_counter()

        if self._level > 0:
            # Empty out the next drip.
            time_since_last_drip = now - self._last_check
            quantity_lost = min(self._level, time_since_last_drip * self._empty_rate)
            self._level -= quantity_lost
        self._last_check = time.perf_counter()

    def _is_capacity_available(self, amount: float = 1) -> bool:
        """
        Check if the additional amount is available, and return True if there is space.

        Args:
            amount:
                additional quantity to request.

        Returns:
            True if available space exists, false otherwise.

        Note:
            Calling this check causes the bucket to leak and for other futures to have their state updated.
        """
        self._leak()
        if self._level + amount < self.max_capacity:
            # Find the first future and set it to be ready to run.
            for future in self._queue.values():
                if not future.done():
                    future.set_result(True)
        else:
            self._full_event.set()
            self._full_event.clear()

        return self._level + amount <= self.max_capacity

    async def acquire(self, amount: float = 1) -> None:
        """
        Attempt to acquire a given capacity in the bucket, or wait until it is available otherwise..

        Args:
            amount: the amount to wait for.
        """
        if amount > self.max_capacity:
            raise ValueError("Attempt to acquire more than the bucket can ever fill to")

        task = compat.asyncio.current_task(self.loop)
        while not self._is_capacity_available(amount):
            future = self.loop.create_future()
            self._queue[task] = future

            try:
                shielded_future = asyncio.shield(future)
                # We wait for the estimated time for the bucket to empty, or wait until the future gets notified
                # if it empties quicker than expected.
                await asyncio.wait_for(shielded_future, amount / self._empty_rate, loop=self.loop)
            except asyncio.TimeoutError:
                pass

            future.cancel()

        self._queue.pop(task, None)
        # We now get to fill our bucket and proceed.
        self._level += amount

    async def __aenter__(self) -> "LeakyBucket":
        await self.acquire()
        return self

    async def __aexit__(
        self, exc_type: typing.Type[BaseException], exc_val: BaseException, exc_tb: compat.typing.TracebackType
    ) -> None:
        pass
