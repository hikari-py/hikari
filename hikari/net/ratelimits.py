#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekokatt 2019-2020
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
Provides an implementation for the complex rate limiting mechanisms that Discord requires for
rate limit handling that conforms to the passed bucket headers correctly.

What is the theory behind this implementation?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In this module, we refer to a :class:`hikari.net.routes.CompiledRoute` as a definition of a route with specific major
parameter values included (e.g. `POST /channels/123/messages`), and a :class:`hikari.net.routes.RouteTemplate` as a
definition of a route without specific parameter values included (e.g. `POST /channels/{channel_id}/messages`). We
can compile a `hikari.net.routes.CompiledRoute` from a :class:`hikari.net.routes.RouteTemplate` by providing the
corresponding parameters as kwargs.

In this module, a "bucket" is an internal data structure that describes the rate limit state for a specific
:class:`hikari.net.routes.CompiledRoute`, and can manage delaying tasks in the event that we begin to get rate
limited. It also supports providing in-order execution of queued tasks.

Discord allocates types of buckets to routes. If you are making a request and there is a valid rate limit on the route
you hit, you should receive an `X-RateLimit-Bucket` header from the server in your response. This is a hash that
identifies a route based on internal criteria that does not include major parameters. This `X-RateLimitBucket` is
known in this module as an "initial bucket hash".

This means that generally, the route `POST /channels/123/messages` and `POST /channels/456/messages` will usually sit
in the same bucket, but `GET /channels/123/messages/789` and `PATCH /channels/123/messages/789` will usually not share
the same bucket. Discord may or may not change this at any time, so hard coding this logic is not a useful thing to be
doing.

Rate limits, on the other hand, apply to a bucket and are specific to the major parameters of the compiled route.
This means that `POST /channels/123/messages` and `POST /channels/456/messages` do not share the same real bucket,
despite Discord providing the same bucket hash. A :class:`hikari.net.ratelimits.RealBucketHash`, therefore,
is the :class:`str` hash of the bucket that Discord sends us in a response concatenated to the corresponding major
parameters. This is used for quick bucket indexing internally in this module.

One issue that occurs from this is that we cannot effectively hash a :class:`hikari.net.routes.CompiledRoute`
that has not yet been hit, meaning that until we receive a response from this endpoint, we have no idea what our rate
limits could be, nor the bucket that they sit in. This is usually not problematic, as the first request to an
endpoint should never be rate limited unless you are hitting it from elsewhere in the same time window outside your
Hikari application. To manage this situation, unknown endpoints are allocated to a special unlimited bucket until
they have an initial bucket hash code allocated from a response. Once this happens, the route is reallocated a
dedicated bucket. Unknown buckets have a hardcoded initial hash code internally.

Initially acquiring time on a bucket
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Each time you :meth:`hikari.net.ratelimits.RateLimiter.acquire` a request timeslice for a given
:class:`hikari.net.ratelimits.CompiledRoute`, several things happen. The first is that we attempt to find the
existing bucket for that route, if there is one, or get an unknown bucket otherwise. This is done by creating a
:class:`hikari.net.ratelimits.RealBucketHash` from the compiled route. The initial hash is calculated using a lookup
table that maps :class:`hikari.net.ratelimits.CompiledRoute` objects to their corresponding initial hash codes,
or to the unknown bucket hash code if not yet known. This initial hash is processed by the
:class`hikari.net.ratelimits.CompiledRoute` to provide the :class:`RealBucketHash` we need to get the route's bucket
object internally.

The :meth:`hikari.net.ratelimits.RateLimiter.acquire` method will take the bucket and acquire a new timeslice on it.
This takes the form of a :class:`asyncio.Future` which should be awaited by the caller and will complete once the
caller is allowed to make a request. Most of the time, this is done instantly, but if the bucket has an active rate
limit preventing requests being sent, then the future will be paused until the rate limit is over. This may be longer
than the rate limit period if you have queued a large number of requests during this limit,
as it is first-come-first-served.

Acquiring a rate limited bucket will start a bucket-wide task (if not already running) that will wait until the
rate limit has completed before allowing more timeslice futures to complete. This is done while observing the rate
limits again, so can easily begin to re-ratelimit itself if needed. Once the task is complete, it tidies itself up
and disposes of itself. This task will complete once the queue becomes empty.

The result of :meth:`hikari.net.ratelimits.RateLimiter.acquire` is a tuple of a :class:`asyncio.Future` to await on
which completes when you are allowed to proceed with making a request, and a :class`RealBucketHash` which should be
stored temporarily. This will be explained in the next section.

When you make your response, you should be sure to set the `X-RateLimit-Precision` header to `millisecond` to ensure
a much greater accuracy against rounding errors for rate limits (reduces the error margin from 1 second to 1
millisecond).

Handling the rate limit headers of a response
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once you have received your response, you are expected to extract the values of the vital rate limit headers manually
and parse them to the correct datatypes. These headers are:

- `Date`: the response date on the server. This should be parsed to a :class:`datetime.datetime` using
    :meth:`email.utils.parsedate_to_datetime`.
- `X-RateLimit-Limit`: an :class:`int` describing the max requests in the bucket from empty to being rate limited.
- `X-RateLimit-Remaining`: an :class:`int` describing the remaining number of requests before rate limiting occurs
    in the current window.
- `X-RateLimit-Bucket`: a :class:`str` containing the initial bucket hash.
- `X-RateLimit-Reset`: a :class:`float` containing the number of seconds since 1st January 1970 at 0:00:00 UTC
    at which the current ratelimit window resets. This should be parsed to a :class:`datetime` using
    :meth:`datetime.datetime.fromtimestamp`, passing :attr:`datetime.timezone.utc` as a second parameter.

Additionally, you need to have the :class:`RealBucketHash` you acquired from the
:meth:`hikari.net.ratelimits.RateLimiter.acquire` call earlier.

Each of the above values should be passed to the :meth:`hikari.net.ratelimits.RateLimiter.update_rate_limits` method
to ensure that the bucket you acquired time from is correctly updated should Discord decide to alter their ratelimits
on the fly without warning (including timings and the bucket).

This method will manage creating new buckets as needed and resetting vital information in each bucket you use.

Tidying up
~~~~~~~~~~

To prevent unused buckets cluttering up memory, each :class:`RateLimiter` instance spins up a :class:`asyncio.Task`
that periodically locks the bucket list (not threadsafe, only using the concept of asyncio not yielding in
regular functions) and disposes of any clearly stale buckets that are no longer needed. These will be recreated again
in the future if they are needed.

When shutting down an application, one must remember to :class:`close` the :class:`RateLimiter` that has been used.
This will ensure the garbage collection task is stopped, and will also ensure any remaining futures in any bucket
queues have an :class:`asyncio.CancelledException` set on them to prevent deadlocking ratelimited calls that may
be waiting to be unlocked.
"""
from __future__ import annotations

import abc
import asyncio
import random
import time
import typing
import weakref

from hikari.internal_utilities import aio

from hikari.internal_utilities import loggers

if typing.TYPE_CHECKING:
    import datetime
    import logging

    from hikari.internal_utilities import type_hints
    from hikari.net import routes

UNKNOWN_HASH = "UNKNOWN"


class IRateLimiter(abc.ABC):
    """
    Base for any asyncio-based rate limiter being used. Supports being used as a synchronous context manager.
    """

    __slots__ = ()

    @abc.abstractmethod
    def acquire(self) -> asyncio.Future:
        """
        Acquire permission to perform a task that needs to have rate limit management enforced.

        Returns:
            A future that should be awaited. Once the future is complete, you can proceed to execute your
            rate-limited task.
        """

    @abc.abstractmethod
    def close(self) -> None:
        """
        Close the rate limiter, cancelling any internal tasks that are executing.
        """

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class BurstRateLimiter(IRateLimiter, abc.ABC):
    """
    Base implementation for a burst-based rate limiter. This provides an internal queue and
    throttling placeholder, as well as complete logic for safely aborting any pending tasks
    when being shut down.
    """

    __slots__ = ("name", "throttle_task", "queue", "logger")

    def __init__(self, name):
        self.name = name
        self.throttle_task: type_hints.Nullable[asyncio.Task] = None
        self.queue = []
        self.logger: logging.Logger = loggers.get_named_logger(self)

    @abc.abstractmethod
    def acquire(self) -> asyncio.Future:
        ...

    def close(self) -> None:
        if self.throttle_task is not None:
            self.throttle_task.cancel()

        failed_tasks = 0
        while self.queue:
            failed_tasks += 1
            future = self.queue.pop(0)
            # Make the future complete with an exception
            future.cancel()

        if failed_tasks:
            self.logger.error("%s rate limiter closed with %s pending tasks!", self.name, failed_tasks)
        else:
            self.logger.debug("%s rate limiter closed", self.name)

    @property
    def is_empty(self) -> bool:
        """Return True if no futures are on the queue being rate limited."""
        return len(self.queue) == 0


class ManualRateLimiter(BurstRateLimiter):
    """
    Rate limit handler for the global HTTP rate limit.

    This is a non-preemptive rate limiting algorithm that will always return completed
    futures until :meth:`throttle` is invoked. Once this is invoked, any subsequent calls to
    :meth:`acquire` will return incomplete futures that will be enqueued to an internal queue.
    A task will be spun up to wait for a period of time given to the :meth:`throttle`. Once that
    has passed, the lock will begin to re-consume incomplete futures on the queue, completing them.

    Triggering a throttle when it is already set will cancel the current throttle task that is
    sleeping and replace it.

    This is used to enforce the global HTTP rate limit that will occur "randomly" during HTTP
    API interaction.
    """

    __slots__ = ()

    def __init__(self) -> None:
        super().__init__("global HTTP")

    def acquire(self) -> asyncio.Future:
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        if self.throttle_task is not None:
            self.queue.append(future)
        else:
            future.set_result(None)
        return future

    def throttle(self, retry_after: float) -> None:
        if self.throttle_task is not None:
            self.throttle_task.cancel()

        loop = asyncio.get_running_loop()
        self.throttle_task = loop.create_task(self.unlock_later(retry_after))

    async def unlock_later(self, retry_after: float) -> None:
        self.logger.warning("you are being globally rate limited for %ss", retry_after)
        await asyncio.sleep(retry_after)
        while self.queue:
            next_future = self.queue.pop(0)
            next_future.set_result(None)
        self.throttle_task = None


class WindowedBurstRateLimiter(BurstRateLimiter):
    """
    Main implementation for time-window-oriented throttling in bursts.

    This is an abstract base that provides common acquisition and scheduling logic.

    If the rate limit has been hit, acquiring time will return an incomplete future that is placed
    on the internal queue. A throttle task is then spun up if not already running that will be
    expected to provide some implementation of backing off and sleeping for a given period of time
    until the limit has passed, and then proceed to consume futures from the queue while adhering
    to those rate limits.

    If the throttle task is already running, the acquired future will always be incomplete and
    enqueued regardless of whether the rate limit is actively reached or not.

    Acquiring a future from this limiter when no throttling task is running and when the rate
    limit is not reached will always result in the task invoking a drip and a completed future
    being returned.

    Dripping is left to the implementation of this class, but will be expected to provide some
    mechanism for updating the internal statistics to represent that a unit has been placed into
    the bucket.
    """

    __slots__ = ("reset_at", "remaining", "limit", "period")

    def __init__(self, name: str, period: float, limit: int) -> None:
        super().__init__(name)
        self.reset_at = 0.0
        self.remaining = 0
        self.limit = limit
        self.period = period

    def acquire(self) -> asyncio.Future:
        loop = asyncio.get_running_loop()
        future = loop.create_future()

        # If we are rate limited, delegate invoking this to the throttler and spin it up
        # if it hasn't started. Likewise, if the throttle task is still running, we should
        # delegate releasing the future to the throttler task so that we still process
        # first-come-first-serve
        if self.throttle_task is not None or self.is_rate_limited(time.perf_counter()):
            self.queue.append(future)
            if self.throttle_task is None:
                self.throttle_task = loop.create_task(self.throttle())
        else:
            self.drip()
            future.set_result(None)

        return future

    def get_time_until_reset(self, now: float) -> float:
        if not self.is_rate_limited(now):
            return 0.0
        return self.reset_at - now

    def is_rate_limited(self, now: float) -> bool:
        if self.reset_at <= now:
            self.remaining = self.limit
            self.reset_at = now + self.period
            return False

        return self.remaining <= 0

    def drip(self):
        self.remaining -= 1

    async def throttle(self) -> None:
        self.logger.warning(
            "you are being rate limited on bucket %s, backing off for %ss",
            self.name,
            self.get_time_until_reset(time.perf_counter()),
        )

        while self.queue:
            sleep_for = self.get_time_until_reset(time.perf_counter())
            await asyncio.sleep(sleep_for)

            while self.remaining > 0 and self.queue:
                self.drip()
                self.queue.pop(0).set_result(None)

        self.throttle_task = None


class HTTPBucketRateLimiter(WindowedBurstRateLimiter):
    """
    Component to represent an active rate limit bucket on a specific HTTP route with a specific major parameter
    combo.

    This is somewhat similar to the :class:`WindowedBurstRateLimiter` in how it works:

    This algorithm will use fixed-period time windows that have a given limit (capacity). Each time a task requests
    processing time, it will drip another unit into the bucket. Once the bucket has reached its limit, nothing
    can drip and new tasks will be queued until the time window finishes.

    Once the time window finishes, the bucket will empty, returning the current capacity to zero, and tasks that
    are queued will start being able to drip again.

    Additional logic is provided by the :meth:`update_rate_limit` call which allows dynamically changing the
    enforced rate limits at any time.
    """

    __slots__ = ("compiled_route",)

    def __init__(self, name: str, compiled_route: routes.CompiledRoute) -> None:
        super().__init__(name, 1, 1)
        # We store this since the compiled route mapping acts as a weak key dictionary to aid in auto garbage
        # collecting itself; this acts as our solid reference.
        self.compiled_route = compiled_route

    @property
    def is_unknown(self) -> bool:
        """Return True if the bucket represents an UNKNOWN bucket."""
        return self.name.startswith(UNKNOWN_HASH)

    def update_rate_limit(self, remaining: int, limit: int, reset_at: float) -> None:
        """
        Amend the rate limit.

        Args:
            remaining:
                The calls remaining in this time window.
            limit:
                The total calls allowed in this time window.
            reset_at:
                The epoch at which to reset the limit.
        """
        self.remaining = remaining
        self.limit = limit
        self.reset_at = reset_at
        self.period = max(0.0, self.reset_at - time.perf_counter())

    def acquire(self) -> asyncio.Future:
        return aio.completed_future(None) if self.is_unknown else super().acquire()

    def drip(self) -> None:
        # We don't drip unknown buckets: we can't rate limit them as we don't know their real bucket hash or
        # the current rate limit values Discord put on them...
        if not self.is_unknown:
            self.remaining -= 1


class HTTPBucketRateLimiterManager:
    """
    The main rate limiter implementation to provide bucketed rate limiting for Discord HTTP endpoints that respects
    the bucket rate limit header.
    """

    __slots__ = (
        "routes_to_hashes",
        "real_hashes_to_buckets",
        "closed_event",
        "gc_task",
        "logger",
    )

    def __init__(self) -> None:
        self.routes_to_hashes: typing.MutableMapping[routes.CompiledRoute, str] = weakref.WeakKeyDictionary()
        self.real_hashes_to_buckets: typing.MutableMapping[str, HTTPBucketRateLimiter] = {}
        self.closed_event: asyncio.Event = asyncio.Event()
        self.gc_task: type_hints.Nullable[asyncio.Task] = None
        self.logger: logging.Logger = loggers.get_named_logger(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def start(self, poll_period: float = 20):
        if not self.gc_task:
            self.gc_task = asyncio.get_running_loop().create_task(self.gc(poll_period))

    def close(self) -> None:
        """
        Close the garbage collector and kill any tasks waiting on rate limits.
        """

        self.closed_event.set()
        for bucket in self.real_hashes_to_buckets.values():
            bucket.close()

    async def gc(self, poll_period: float = 20) -> None:
        # Prevent filling memory increasingly until we run out by removing dead buckets every 20s
        # Allocations are somewhat cheap if we only do them every so-many seconds, after all.
        self.logger.debug("rate limit garbage collector started")
        while not self.closed_event.is_set():
            try:
                await asyncio.wait_for(self.closed_event.wait(), timeout=poll_period)
            except asyncio.TimeoutError:
                try:
                    self.logger.debug("performing rate limit garbage collection pass")
                    await self.do_gc_pass()
                except Exception as ex:
                    self.logger.exception("ignoring garbage collection error for rate limits", exc_info=ex)
        self.gc_task = None

    async def do_gc_pass(self):
        buckets_to_purge = []

        # Discover and purge
        for full_hash, bucket in self.real_hashes_to_buckets.items():
            if bucket.is_empty and (bucket.is_unknown or bucket.reset_at < time.perf_counter()):
                # If it is still running a throttle and is in memory, it will remain in memory
                # but we won't know about it.
                buckets_to_purge.append(full_hash)

        for full_hash in buckets_to_purge:
            self.real_hashes_to_buckets[full_hash].close()
            del self.real_hashes_to_buckets[full_hash]

        self.logger.debug("purged %s stale buckets", len(buckets_to_purge))

    def acquire(self, compiled_route: routes.CompiledRoute) -> asyncio.Future:
        """
        Acquire a bucket for the given route.

        Args:
            compiled_route:
                The route to get the bucket for.

        Returns:
            A future to await that completes when you are allowed to run your request logic.

            The returned future MUST be awaited, and will complete when your turn to make a call
            comes along. You are expected to await this and then immediately make your HTTP
            call. The returned future may already be completed if you can make the call
            immediately.
        """
        # Returns a future to await on to wait to be allowed to send the request, and a
        # bucket hash to use to update rate limits later.
        if compiled_route in self.routes_to_hashes:
            bucket_hash = self.routes_to_hashes[compiled_route]
        else:
            bucket_hash = UNKNOWN_HASH

        real_bucket_hash = compiled_route.create_real_bucket_hash(bucket_hash)

        try:
            bucket = self.real_hashes_to_buckets[real_bucket_hash]
        except KeyError:
            self.logger.debug("creating new bucket for %s", real_bucket_hash)
            bucket = HTTPBucketRateLimiter(real_bucket_hash, compiled_route)
            self.real_hashes_to_buckets[real_bucket_hash] = bucket

        return bucket.acquire()

    def update_rate_limits(
        self,
        compiled_route: routes.CompiledRoute,
        bucket_header: type_hints.Nullable[str],
        remaining_header: int,
        limit_header: int,
        date_header: datetime.datetime,
        reset_at_header: datetime.datetime,
    ) -> None:
        """
        Update the rate limits for a bucket using info from a response.

        Args:
            compiled_route:
                The route to get the bucket for.
            bucket_header:
                The X-RateLimit-Bucket header that was provided in the response, or `None` if not present.
            remaining_header:
                The X-RateLimit-Remaining header cast to an :class:`int`.
            limit_header:
                The X-RateLimit-Limit header cast to an :class:`int`.
            date_header:
                The Date header value as a :class:`datetime.datetime`.
            reset_at_header:
                The X-RateLimit-Reset header value as a :class:`datetime.datetime`.
        """
        if compiled_route not in self.routes_to_hashes:
            self.routes_to_hashes[compiled_route] = bucket_header

        real_bucket_hash = compiled_route.create_real_bucket_hash(bucket_header)

        if real_bucket_hash not in self.real_hashes_to_buckets:
            bucket = HTTPBucketRateLimiter(real_bucket_hash, compiled_route)
            self.real_hashes_to_buckets[real_bucket_hash] = bucket
        else:
            bucket = self.real_hashes_to_buckets[real_bucket_hash]

        reset_after = (reset_at_header - date_header).total_seconds()
        reset_at_monotonic = time.perf_counter() + reset_after
        bucket.update_rate_limit(remaining_header, limit_header, reset_at_monotonic)


class ExponentialBackOff:
    """
    Implementation of an asyncio-compatible exponential back-off algorithm with random jitter.

    Set `maximum` to -1 to prevent an upper limit.
    """

    __slots__ = ("base", "increment", "maximum", "jitter_multiplier")

    def __init__(self, base: float = 2, maximum: float = 64, jitter_multiplier: float = 1) -> None:
        self.base = base
        self.maximum = maximum
        self.increment = 0
        self.jitter_multiplier = jitter_multiplier

    def __next__(self) -> float:
        """
        Get the next back off to sleep by.
        """
        value = self.base ** self.increment

        self.increment += 1

        if value == self.maximum:
            raise asyncio.TimeoutError()

        value += random.random() * self.jitter_multiplier  # nosec
        return value

    def __iter__(self):
        return self

    def reset(self) -> None:
        self.increment = 0


__all__ = [
    "IRateLimiter",
    "BurstRateLimiter",
    "ManualRateLimiter",
    "WindowedBurstRateLimiter",
    "HTTPBucketRateLimiter",
    "HTTPBucketRateLimiterManager",
    "ExponentialBackOff",
]
