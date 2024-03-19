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
"""Basic lazy ratelimit systems for asyncio.

See [`hikari.impl.buckets`][] for HTTP-specific rate-limiting logic.
"""

from __future__ import annotations

__all__: typing.Sequence[str] = (
    "BaseRateLimiter",
    "BurstRateLimiter",
    "ManualRateLimiter",
    "WindowedBurstRateLimiter",
    "ExponentialBackOff",
)

import abc
import asyncio
import logging
import math
import random
import typing

from hikari.internal import time

if typing.TYPE_CHECKING:
    import types

_LOGGER: typing.Final[logging.Logger] = logging.getLogger("hikari.ratelimits")


class BaseRateLimiter(abc.ABC):
    """Base for any asyncio-based rate limiter being used."""

    __slots__: typing.Sequence[str] = ()

    @abc.abstractmethod
    async def acquire(self) -> None:
        """Acquire permission to perform a task that needs to have rate limit management enforced.

        Calling this function will cause it to block until you are not longer
        being rate limited.
        """

    @abc.abstractmethod
    def close(self) -> None:
        """Close the rate limiter, cancelling any internal tasks that are executing."""

    def __enter__(self) -> BaseRateLimiter:
        return self

    def __exit__(
        self,
        exc_type: typing.Optional[typing.Type[Exception]],
        exc_val: typing.Optional[Exception],
        exc_tb: typing.Optional[types.TracebackType],
    ) -> None:
        self.close()


class BurstRateLimiter(BaseRateLimiter, abc.ABC):
    """Base implementation for a burst-based rate limiter.

    This provides an internal queue and throttling placeholder, as well as
    complete logic for safely aborting any pending tasks when being shut down.
    """

    __slots__: typing.Sequence[str] = ("name", "throttle_task", "queue")

    name: str
    """The name of the rate limiter."""

    throttle_task: typing.Optional[asyncio.Task[typing.Any]]
    """The throttling task, or [`None`][] if it is not running."""

    queue: typing.List[asyncio.Future[typing.Any]]
    """The queue of any futures under a rate limit."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.throttle_task = None
        self.queue = []

    @abc.abstractmethod
    async def acquire(self) -> None:
        """Acquire time on this rate limiter.

        Calling this function will cause it to block until you are not longer
        being rate limited.
        """

    def close(self) -> None:
        """Close the rate limiter, and shut down any pending tasks."""
        if self.throttle_task is not None:
            self.throttle_task.cancel()
            self.throttle_task = None

        failed_tasks = 0
        while self.queue:
            failed_tasks += 1
            future = self.queue.pop(0)
            # Make the future complete with an exception
            future.cancel()

        if failed_tasks:
            _LOGGER.debug("%s rate limiter closed with %s pending tasks!", self.name, failed_tasks)
        else:
            _LOGGER.debug("%s rate limiter closed", self.name)

    @property
    def is_empty(self) -> bool:
        """Return [`True`][] if no futures are on the queue being rate limited."""
        return len(self.queue) == 0


@typing.final
class ManualRateLimiter(BurstRateLimiter):
    """Rate limit handler for the global HTTP rate limit.

    This is a non-preemptive rate limiting algorithm that will always return
    completed futures until [`hikari.impl.rate_limits.ManualRateLimiter.throttle`][] is invoked. Once this
    is invoked, any subsequent calls to [`hikari.impl.rate_limits.ManualRateLimiter.acquire`][] will return
    incomplete futures that will be enqueued to an internal queue. A task will
    be spun up to wait for a period of time given to the
    [`hikari.impl.rate_limits.ManualRateLimiter.throttle`][]. Once that has passed, the lock will begin to
    re-consume incomplete futures on the queue, completing them.

    Triggering a throttle when it is already set will cancel the current
    throttle task that is sleeping and replace it.

    This is used to enforce the global HTTP rate limit that will occur
    "randomly" during HTTP API interaction.

    Expect random occurrences.
    """

    __slots__: typing.Sequence[str] = ("reset_at",)

    throttle_task: typing.Optional[asyncio.Task[typing.Any]]
    # <<inherited docstring from BurstRateLimiter>>.

    reset_at: typing.Optional[float]
    """The monotonic [`time.monotonic`][] timestamp at which the ratelimit gets lifted."""

    def __init__(self) -> None:
        super().__init__("global")
        self.reset_at = None

    async def acquire(self) -> None:
        """Acquire time on this rate limiter.

        Calling this function will cause it to block until you are not longer
        being rate limited.
        """
        loop = asyncio.get_running_loop()
        future = loop.create_future()

        if self.throttle_task is not None:
            self.queue.append(future)
        else:
            future.set_result(None)

        await future

    def throttle(self, retry_after: float) -> None:
        """Perform the throttling rate limiter logic.

        Iterates repeatedly while the queue is not empty, adhering to any
        rate limits that occur in the meantime.

        !!! note
            This will invoke [`hikari.impl.rate_limits.ManualRateLimiter.unlock_later`][] as a scheduled
            task in the future (it will not await it to finish).

            When the [`hikari.impl.rate_limits.ManualRateLimiter.unlock_later`][] coroutine function
            completes, it should be expected to set the `throttle_task` to
            [`None`][]. This means you can check if throttling is occurring
            by checking if `throttle_task` is not [`None`][].

            If this is invoked while another throttle is in progress, that one
            is cancelled and a new one is started. This enables new rate limits
            to override existing ones.

        Parameters
        ----------
        retry_after : float
            How long to sleep for before unlocking and releasing any futures
            in the queue.
        """
        if self.throttle_task is not None:
            self.throttle_task.cancel()

        loop = asyncio.get_running_loop()
        self.throttle_task = loop.create_task(self.unlock_later(retry_after))

    async def unlock_later(self, retry_after: float) -> None:
        """Sleep for a while, then remove the lock.

        !!! warning
            You should not need to invoke this directly. Call
            [`hikari.impl.rate_limits.ManualRateLimiter.throttle`][] instead.

            When the [`hikari.impl.rate_limits.ManualRateLimiter.unlock_later`][] coroutine function
            completes, it should be expected to set the `throttle_task` to
            [`None`][]. This means you can check if throttling is occurring
            by checking if `throttle_task` is not [`None`][].

        Parameters
        ----------
        retry_after : float
            How long to sleep for before unlocking and releasing any futures
            in the queue.
        """
        _LOGGER.warning("you are being globally rate limited for %ss", retry_after)

        self.reset_at = time.monotonic() + retry_after
        await asyncio.sleep(retry_after)
        self.reset_at = None

        while self.queue:
            next_future = self.queue.pop(0)
            next_future.set_result(None)
        self.throttle_task = None

    def get_time_until_reset(self, now: float) -> float:
        """Determine how long until the current rate limit is reset.

        Parameters
        ----------
        now : float
            The monotonic [`time.monotonic`][] timestamp.

        Returns
        -------
        float
            The time left to sleep before the rate limit is reset. If no rate limit
            is in effect, then this will return `0.0` instead.
        """
        if not self.reset_at:
            return 0.0

        return self.reset_at - now


class WindowedBurstRateLimiter(BurstRateLimiter):
    """Windowed burst rate limiter.

    Rate limiter for rate limits that last fixed periods of time with a
    fixed number of times it can be used in that time frame.

    To use this, you should call [`hikari.impl.rate_limits.WindowedBurstRateLimiter.acquire`][] and await the
    result immediately before performing your rate-limited task.

    If the rate limit has been hit, acquiring time will return an incomplete
    future that is placed on the internal queue. A throttle task is then spun up
    if not already running that will be expected to provide some implementation
    of backing off and sleeping for a given period of time until the limit has
    passed, and then proceed to consume futures from the queue while adhering
    to those rate limits.

    If the throttle task is already running, the acquired future will always be
    incomplete and enqueued regardless of whether the rate limit is actively
    reached or not.

    Acquiring a future from this limiter when no throttling task is running and
    when the rate limit is not reached will always result in the task invoking
    a drip and a completed future being returned.

    Dripping is left to the implementation of this class, but will be expected
    to provide some mechanism for updating the internal statistics to represent
    that a unit has been placed into the bucket.
    """

    __slots__: typing.Sequence[str] = ("reset_at", "remaining", "limit", "period")

    throttle_task: typing.Optional[asyncio.Task[typing.Any]]
    # <<inherited docstring from BurstRateLimiter>>.

    reset_at: float
    """The [`time.monotonic`][] that the limit window ends at."""

    remaining: int
    """The number of [`hikari.impl.rate_limits.WindowedBurstRateLimiter.acquire`][]'s
    left in this window before you will get rate limited."""

    period: float
    """How long the window lasts for from the start in seconds."""

    limit: int
    """The maximum number of [`hikari.impl.rate_limits.WindowedBurstRateLimiter.acquire`][]'s
    allowed in this time window."""

    def __init__(self, name: str, period: float, limit: int) -> None:
        super().__init__(name)
        self.reset_at = 0.0
        self.remaining = 0
        self.limit = limit
        self.period = period

    async def acquire(self) -> None:
        """Acquire time on this rate limiter.

        Calling this function will cause it to block until you are not longer
        being rate limited.
        """
        # If we are rate limited, delegate invoking this to the throttler and spin it up
        # if it hasn't started. Likewise, if the throttle task is still running, we should
        # delegate releasing the future to the throttler task so that we still process
        # first-come-first-serve
        if self.throttle_task is not None or self.is_rate_limited(time.monotonic()):
            loop = asyncio.get_running_loop()
            future = loop.create_future()

            self.queue.append(future)
            if self.throttle_task is None:
                self.throttle_task = loop.create_task(self.throttle())

            await future
        else:
            self.drip()

    def get_time_until_reset(self, now: float) -> float:
        """Determine how long until the current rate limit is reset.

        !!! warning
            Invoking this method will update the internal state if we were
            previously rate limited, but at the given time are no longer under
            that limit. This makes it imperative that you only pass the current
            timestamp to this function, and not past or future timestamps. The
            effects of doing the latter are undefined behaviour.

        Parameters
        ----------
        now : float
            The monotonic [`time.monotonic`][] timestamp.

        Returns
        -------
        float
            The time left to sleep before the rate limit is reset. If no rate limit
            is in effect, then this will return `0.0` instead.
        """
        if not self.is_rate_limited(now):
            return 0.0
        return self.reset_at - now

    def is_rate_limited(self, now: float) -> bool:
        """Determine if we are under a rate limit at the given time.

        !!! warning
            Invoking this method will update the internal state if we were
            previously rate limited, but at the given time are no longer under
            that limit. This makes it imperative that you only pass the current
            timestamp to this function, and not past or future timestamps. The
            effects of doing the latter are undefined behaviour.

        Parameters
        ----------
        now : float
            The monotonic [`time.monotonic`][] timestamp.

        Returns
        -------
        bool
            Whether the bucket is ratelimited.
        """
        if self.reset_at <= now:
            self.remaining = self.limit
            self.reset_at = now + self.period
            return False

        return self.remaining <= 0

    def drip(self) -> None:
        """Decrement the remaining counter."""
        self.remaining -= 1

    async def throttle(self) -> None:
        """Perform the throttling rate limiter logic.

        Iterates repeatedly while the queue is not empty, adhering to any
        rate limits that occur in the mean time.

        !!! note
            You should usually not need to invoke this directly, but if you do,
            ensure to call it using [`asyncio.create_task`][], and store the
            task immediately in
            [`hikari.impl.rate_limits.WindowedBurstRateLimiter.throttle_task`][].

            When this coroutine function completes, it will set the
            [`hikari.impl.rate_limits.WindowedBurstRateLimiter.throttle_task`][]
            to [`None`][]. This means you can check if throttling
            is occurring by checking if it is not [`None`][].
        """
        while self.queue:
            sleep_for = self.get_time_until_reset(time.monotonic())

            if sleep_for > 0:
                _LOGGER.debug("you are being rate limited on bucket %s, backing off for %ss", self.name, sleep_for)
                await asyncio.sleep(sleep_for)

            while self.remaining > 0 and self.queue:
                self.drip()
                self.queue.pop(0).set_result(None)

        self.throttle_task = None


@typing.final
class ExponentialBackOff:
    r"""Implementation of an asyncio-compatible exponential back-off algorithm with random jitter.

    Each backoff will be calculated by raising the `base` to the increment
    (the number of invocations since last reset) and added on to it, the
    jitter, calculated as `jitter_multiplier` times a random number between
    0 and 1.

    Parameters
    ----------
    base : float
        The base to use.
    maximum : float
        The max value the backoff can be in a single iteration.

        All values will be capped to this base value plus some random jitter.
    jitter_multiplier : float
        The multiplier for the random jitter.

        Set to `0` to disable jitter.
    initial_increment : int
        The initial increment to start at.

    Raises
    ------
    ValueError
        If an [`int`][] that's too big to be represented as a
        [`float`][] or a non-finite value is passed in place of a field
        that's annotated as [`float`][].
    """

    __slots__: typing.Sequence[str] = ("base", "increment", "maximum", "jitter_multiplier")

    base: typing.Final[float]
    """The base to use."""

    increment: int
    """The current increment."""

    maximum: float
    """This is the max value the backoff can be in a single iteration before an [`asyncio.TimeoutError`][] is raised."""

    jitter_multiplier: typing.Final[float]
    """The multiplier for the random jitter."""

    def __init__(
        self, base: float = 2.0, maximum: float = 64.0, jitter_multiplier: float = 1.0, initial_increment: int = 0
    ) -> None:
        # https://mypy.readthedocs.io/en/stable/duck_type_compatibility.html
        # Mypy makes the assumption that ints will always be compatible with floats, this isn't the case and could lead
        # to some edge cases that we'd be better off catching earlier on by ensuring these values are actually valid
        # (most notably floats have a system based maximum size whereas integers theoretically don't with implicit
        # conversion to a float raising an error if an integer that's too big to be a float is handled).
        try:
            self.base = float(base)
            self.maximum = float(maximum)
            self.jitter_multiplier = float(jitter_multiplier)
        except OverflowError:
            raise ValueError("int too large to be represented as a float") from None

        if not math.isfinite(self.base):
            raise ValueError("base must be a finite number") from None

        if not math.isfinite(self.maximum):
            raise ValueError("maximum must be a finite number") from None

        if not math.isfinite(self.jitter_multiplier):
            raise ValueError("jitter_multiplier must be a finite number") from None

        self.increment = initial_increment

    def __next__(self) -> float:
        """Get the next back off to sleep by."""
        try:
            value = self.base**self.increment

            if value >= self.maximum:
                value = self.maximum
            else:
                # This should only be incremented after we verify we haven't hit the maximum value.
                self.increment += 1
        except OverflowError:
            # If this happened then we can be sure that we've passed maximum.
            value = self.maximum

        return value + random.random() * self.jitter_multiplier  # noqa: S311 - rng for cryptography

    def __iter__(self) -> ExponentialBackOff:
        """Return this object, as it is an iterator."""
        return self

    def reset(self) -> None:
        """Reset the exponential back-off."""
        self.increment = 0
