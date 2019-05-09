#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio


class LeakyBucket:
    """
    A leaky bucket algorithm implementation that uses first-come-first-serve asyncio callbacks that
    lock and unlock a :class:`asyncio.BoundedSemaphore` after a given delay.

    Args:
        limit: an integer limit of items in the bucket before it is full.
        delay: number of seconds the bucket waits before it empties an item put in it.
        loop: the asyncio loop to run on.
        logging_method: method to call to produce logger warnings about ratelimiting.
    """

    __slots__ = ["logging_method", "semaphore", "delay", "loop", "ratelimited_event"]

    def __init__(
        self,
        limit: int,
        delay: float,
        loop: asyncio.AbstractEventLoop,
        logging_method=lambda *a, **k: None,
    ):
        assert limit > 0, "Limit must be greater than zero"
        assert delay > 0, "Delay must be greater than zero"
        self.semaphore = asyncio.BoundedSemaphore(limit, loop=loop)
        self.logging_method = logging_method
        self.delay = delay
        self.loop = loop
        #: An event that gets fired if we get ratelimited. Mostly exists for testing sanity checks.
        self.ratelimited_event = asyncio.Event(loop=loop)

    def submit(self, coroutine, *args, **kwargs) -> asyncio.Task:
        return asyncio.create_task(self._limiter(coroutine, *args, **kwargs))

    async def _limiter(self, coroutine, *args, **kwargs):
        if self.semaphore.locked():
            self.logging_method("You are being ratelimited locally")
            self.ratelimited_event.set()
            self.ratelimited_event.clear()

        async with self.semaphore:
            result = await coroutine(*args, **kwargs)
            await asyncio.sleep(self.delay)
            return result
