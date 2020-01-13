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

In this module, we refer to a :class:`CompiledRoute` as a definition of a route with specific major parameter values
included (e.g. `POST /channels/123/messages`), and a :class:`RouteTemplate` as a definition of a route without specific
parameter values included (e.g. `POST /channels/{channel_id}/messages`). We can compile a `CompiledRoute` from a
`RouteTemplate` by providing the corresponding parameters as kwargs.

In this module, a "bucket" is an internal data structure that describes the rate limit state for a specific
:class:`CompiledRoute`, and can manage delaying tasks in the event that we begin to get rate limited. It also supports
providing in-order execution of queued tasks.

Discord allocates types of buckets to routes. If you are making a request and there is a valid rate limit on the route
you hit, you should receive an `X-RateLimit-Bucket` header from the server in your response. This is a hash that
identifies a route based on internal criteria that does not include major parameters. This `X-RateLimitBucket` is
known in this module as an "initial bucket hash".

This means that generally, the route `POST /channels/123/messages` and `POST /channels/456/messages` will usually sit
in the same bucket, but `GET /channels/123/messages/789` and `PATCH /channels/123/messages/789` will usually not share
the same bucket. Discord may or may not change this at any time, so hard coding this logic is not a useful thing to be
doing.

Rate limits, on the other hand, apply to a bucket and are specific to the major parameters of the compiled route. This
means that `POST /channels/123/messages` and `POST /channels/456/messages` do not share the same real bucket, despite
Discord providing the same bucket hash. A :class:`RealBucketHash`, therefore, as the :class:`str` hash of the bucket
that Discord sends us in a response concatenated to the corresponding major parameters. This is used for quick bucket
indexing internally in this module.

One issue that occurs from this is that we cannot effectively hash a :class:`CompiledRoute` that has not yet been hit,
meaning that until we receive a response from this endpoint, we have no idea what our rate limits could be, nor the
bucket that they sit in. This is usually not problematic, as the first request to an endpoint should never be rate
limited unless you are hitting it from elsewhere in the same time window outside your Hikari application. To manage
this situation, unknown endpoints are allocated to a special unlimited bucket until they have an initial bucket hash
code allocated from a response. Once this happens, the route is reallocated a dedicated bucket. Unknown buckets have
a hardcoded initial hash code internally.

Initially acquiring time on a bucket
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Each time you :meth:`RateLimiter.acquire` a request timeslice for a given :class:`CompiledRoute`, several things
happen. The first is that we attempt to find the existing bucket for that route, if there is one, or get an unknown
bucket otherwise. This is done by creating a :class:`RealBucketHash` from the compiled route. The initial hash is
calculated using a lookup table that maps :class:`CompiledRoute` objects to their corresponding initial hash codes,
or to the unknown bucket hash code if not yet known. This initial hash is processed by the :class`CompiledRoute` to
provide the :class:`RealBucketHash` we need to get the route's bucket object internally.

The :meth:`RateLimiter.acquire` method will take the bucket and acquire a new timeslice on it. This takes the form
of a :class:`asyncio.Future` which should be awaited by the caller and will complete once the caller is allowed to make
a request. Most of the time, this is done instantly, but if the bucket has an active rate limit preventing requests
being sent, then the future will be paused until the rate limit is over. This may be longer than the rate limit
period if you have queued a large number of requests during this limit, as it is first-come-first-served.

Acquiring a rate limited bucket will start a bucket-wide task (if not already running) that will wait until the
rate limit has completed before allowing more timeslice futures to complete. This is done while observing the rate
limits again, so can easily begin to re-ratelimit itself if needed. Once the task is complete, it tidies itself up
and disposes of itself. This task will complete once the queue becomes empty.

The result of :meth:`RateLimiter.acquire` is a tuple of a :class:`asyncio.Future` to await on which completes when
you are allowed to proceed with making a request, and a :class`RealBucketHash` which should be stored temporarily.
This will be explained in the next section.

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

Additionally, you need to have the :class:`RealBucketHash` you acquired from the :meth:`RateLimiter.acquire` call
earlier.

Each of the above values should be passed to the :meth:`RateLimiter.update_rate_limits` method to ensure that the
bucket you acquired time from is correctly updated should Discord decide to alter their ratelimits on the fly without
warning (including timings and the bucket).

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
import asyncio
import datetime
import logging
import time
from typing import List
from typing import MutableMapping
from typing import Optional
from typing import Tuple

from hikari.internal_utilities import loggers
from hikari.net import routes

UNKNOWN_HASH = "UNKNOWN"


class GlobalHTTPRateLimiter:
    """
    Rate limit handler for the global HTTP rate limit.
    """
    __slots__ = ("logger", "lock_task", "queue")

    def __init__(self) -> None:
        self.logger: logging.Logger = loggers.get_named_logger(self)
        self.lock_task: Optional[asyncio.Task] = None
        self.queue: List[asyncio.Future] = []

    def maybe_wait(self) -> asyncio.Future:
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        if self.lock_task is not None:
            self.queue.append(future)
        else:
            future.set_result(None)
        return future

    def lock(self, retry_after: float) -> None:
        if self.lock_task is not None:
            self.lock_task.cancel()

        loop = asyncio.get_running_loop()
        self.lock_task = loop.create_task(self._unlock_later(retry_after))

    async def _unlock_later(self, retry_after: float) -> None:
        self.logger.warning("you are being globally ratelimited for %ss", retry_after)
        await asyncio.sleep(retry_after)
        while self.queue:
            next_future = self.queue.pop(0)
            next_future.set_result(None)
        self.lock_task = None

    def close(self) -> None:
        if self.lock_task is not None:
            self.lock_task.cancel()

        failed_tasks = 0
        while self.queue:
            failed_tasks += 1
            future = self.queue.pop(0)
            # Make the future complete with an exception
            future.cancel()

        if failed_tasks:
            self.logger.error("global HTTP ratelimiter closed with %s pending tasks!", failed_tasks)
        else:
            self.logger.debug("global HTTP ratelimiter closed")


class GatewayRateLimiter:
    """
    Aid to adhere to the 120/60 gateway ratelimit.
    """
    __slots__ = ("logger", "period", "remaining", "limit", "reset_at", "queue", "throttle_task")

    def __init__(self, period: float, limit: int) -> None:
        self.logger: logging.Logger = loggers.get_named_logger(self)
        self.period: float = period
        self.remaining: int = limit
        self.limit: int = limit
        self.reset_at: float = 0
        self.queue: List[asyncio.Future] = []
        self.throttle_task: Optional[asyncio.Task] = None

    def close(self) -> None:
        # These should never occur but it is worth doing them to prevent
        # dependent code deadlocking if there is a logic error missed anywhere
        if self.throttle_task is not None:
            self.throttle_task.cancel()

        failed_tasks = 0
        while self.queue:
            failed_tasks += 1
            future = self.queue.pop(0)
            # Make the future complete with an exception
            future.cancel()

        if failed_tasks:
            self.logger.error("gateway ratelimiter closed with %s pending tasks!", failed_tasks)
        else:
            self.logger.debug("gateway ratelimiter closed")

    def is_empty(self) -> bool:
        return len(self.queue) == 0

    def acquire(self) -> asyncio.Future:
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self._handle_request(loop, future)
        return future

    def _handle_request(self, loop: asyncio.AbstractEventLoop, future: asyncio.Future) -> None:
        # If we are rate limited, delegate invoking this to the throttler and spin it up
        # if it hasn't started. Likewise, if the throttle task is still running, we should
        # delegate releasing the future to the throttler task so that we still process
        # first-come-first-serve
        if self.throttle_task is not None or self._is_ratelimited(time.perf_counter()):
            self.queue.append(future)
            if self.throttle_task is None:
                self.throttle_task = loop.create_task(self._throttle())
        else:
            self._drip()
            future.set_result(None)

    async def _throttle(self) -> None:
        self.logger.warning(
            "you are being ratelimited on a websocket, backing off for %ss", self._get_backoff_time(),
        )

        while self.queue:
            await asyncio.sleep(self._get_time_until_reset(time.perf_counter()))
            future = self.queue.pop(0)
            self._drip()
            future.set_result(None)

        self.throttle_task = None

    def _get_backoff_time(self) -> float:
        now = time.perf_counter()
        return self._get_time_until_reset(now) if self._is_ratelimited(now) else 0

    def _get_time_until_reset(self, now: float) -> float:
        reset_at = 0 if self.reset_at is None else self.reset_at
        return max(0.0, reset_at - now)

    def _is_ratelimited(self, now: float) -> bool:
        reset_at = 0 if self.reset_at is None else self.reset_at
        return reset_at >= now and self.remaining <= 0

    def _drip(self) -> None:
        now = time.perf_counter()
        if self._get_time_until_reset(now) == 0:
            self.reset_at = now + self.period
            self.remaining = self.limit
        self.remaining -= 1


class Bucket:
    """
    Component to represent an active rate limit bucket on a specific HTTP route with a specific major parameter
    combo.
    """

    __slots__ = ("name", "remaining", "limit", "reset_at", "queue", "throttle_task")
    # We want initialization to be as fast as possible, don't faff with loggers per object.
    _LOGGER = loggers.get_named_logger(__name__ + ".Bucket")

    def __init__(self, name: str) -> None:
        self.name: str = name
        self.remaining: int = 1
        self.limit: int = 1
        self.reset_at: float = 0
        self.queue: List[asyncio.Future] = []
        self.throttle_task: Optional[asyncio.Task] = None

    def close(self) -> None:
        # These should never occur but it is worth doing them to prevent
        # dependent code deadlocking if there is a logic error missed anywhere
        if self.throttle_task is not None:
            self.throttle_task.cancel()

        failed_tasks = 0
        while self.queue:
            failed_tasks += 1
            future = self.queue.pop(0)
            # Make the future complete with an exception
            future.set_exception(asyncio.CancelledError(f"bucket {self.name} was closed"))

        if failed_tasks:
            self._LOGGER.error("bucket %s closed with %s pending tasks!", self.name, failed_tasks)
        else:
            self._LOGGER.debug("bucket %s closed", self.name)

    def is_unknown(self) -> bool:
        """Return True if the bucket represents an UNKNOWN bucket."""
        return self.name.startswith(UNKNOWN_HASH)

    def is_empty(self) -> bool:
        """Return True if the bucket is empty of futures."""
        return len(self.queue) == 0

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

    def acquire(self) -> asyncio.Future:
        """
        Acquire a future call slot.

        Returns:
            A future that must be awaited, and will complete when your turn to make a call
            comes along. You are expected to await this and then immediately make your HTTP
            call. The returned future may already be completed if you can make the call
            immediately.
        """
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self._handle_request(loop, future)
        return future

    def _handle_request(self, loop: asyncio.AbstractEventLoop, future: asyncio.Future) -> None:
        # If we are ratelimited, delegate invoking this to the throttler and spin it up
        # if it hasn't started. Likewise, if the throttle task is
        # still running, we should delegate releasing the future to the
        # throttler task so that we still process first-come-first-serve
        if self.throttle_task is not None or self._is_ratelimited(time.perf_counter()):
            self.queue.append(future)
            if self.throttle_task is None:
                self.throttle_task = loop.create_task(self._throttle())
        else:
            self._drip()
            future.set_result(None)

    async def _throttle(self) -> None:
        self._LOGGER.warning(
            "you are being ratelimited on bucket %s, backing off for %ss", self.name, self._get_backoff_time(),
        )

        while self.queue:
            await asyncio.sleep(self._get_time_until_reset(time.perf_counter()))
            self.remaining = self.limit
            future = self.queue.pop(0)
            self._drip()
            future.set_result(None)

        self.throttle_task = None

    def _get_backoff_time(self) -> float:
        now = time.perf_counter()
        return self._get_time_until_reset(now) if self._is_ratelimited(now) else 0

    def _get_time_until_reset(self, now: float) -> float:
        reset_at = 0 if self.reset_at is None else self.reset_at
        return max(0.0, reset_at - now)

    def _is_ratelimited(self, now: float) -> bool:
        reset_at = 0 if self.reset_at is None else self.reset_at
        return reset_at >= now and self.remaining <= 0

    def _drip(self) -> None:
        if not self.is_unknown():
            if self.remaining <= 0:
                self._LOGGER.error(
                    "bucket %s has somehow dripped but was already ratelimited!", self.name,
                )
            self.remaining -= 1


class HTTPRateLimiter:
    """
    The main rate limiter implementation to provide bucketed rate limiting for Discord HTTP endpoints that respects
    the bucket rate limit header.
    """

    __slots__ = (
        "routes_to_real_hashes",
        "real_hashes_to_buckets",
        "closed_event",
        "gc_task",
        "logger",
    )

    def __init__(self) -> None:
        self.routes_to_real_hashes: MutableMapping[routes.CompiledRoute, str] = {}
        self.real_hashes_to_buckets: MutableMapping[str, Bucket] = {}
        self.closed_event: asyncio.Event = asyncio.Event()
        self.gc_task: asyncio.Task = asyncio.get_running_loop().create_task(self._garbage_collector())
        self.logger: logging.Logger = loggers.get_named_logger(self)

    def close(self) -> None:
        """
        Close the garbage collector and kill any tasks waiting on rate limits.
        """

        self.closed_event.set()
        for bucket in self.real_hashes_to_buckets.values():
            bucket.close()

    async def _garbage_collector(self) -> None:
        # Prevent filling memory increasingly until we run out by removing dead buckets every 20s
        # Allocations are somewhat cheap if we only do them every so-many seconds, afterall.
        self.logger.debug("ratelimit garbage collector started")
        while not self.closed_event.is_set():
            try:
                await asyncio.wait_for(self.closed_event.wait(), timeout=20)
            except asyncio.TimeoutError:
                self.logger.debug("performing ratelimit garbage collection pass")

                try:
                    buckets_to_purge = []

                    # Discover and purge
                    for full_hash, bucket in self.real_hashes_to_buckets.items():
                        if bucket.is_empty() and (bucket.is_unknown() or bucket.reset_at < time.perf_counter()):
                            # If it is still running a throttle and is in memory, it will remain in memory
                            # but we won't know about it.
                            buckets_to_purge.append(full_hash)

                    for full_hash in buckets_to_purge:
                        self.real_hashes_to_buckets[full_hash].close()
                        del self.real_hashes_to_buckets[full_hash]
                    self.logger.debug("purged %s stale buckets", len(buckets_to_purge))
                except Exception as ex:
                    self.logger.exception("ignoring garbage collection error for rate limits", exc_info=ex)

    def acquire(self, compiled_route: routes.CompiledRoute) -> Tuple[asyncio.Future, str]:
        """
        Acquire a bucket for the given route.

        Args:
            compiled_route:
                The route to get the bucket for.

        Returns:
            A future to await that completes when you are allowed to run your request logic, and a bucket
            hash to pass to the :meth:`update_rate_limits` method afterwards.

            The returned future MUST be awaited, and will complete when your turn to make a call
            comes along. You are expected to await this and then immediately make your HTTP
            call. The returned future may already be completed if you can make the call
            immediately.
        """
        # Returns a future to await on to wait to be allowed to send the request, and a
        # bucket hash to use to update rate limits later.
        if compiled_route not in self.routes_to_real_hashes:
            real_bucket_hash = compiled_route.create_real_bucket_hash(UNKNOWN_HASH)
        else:
            real_bucket_hash = self.routes_to_real_hashes[compiled_route]

        if compiled_route not in self.routes_to_real_hashes:
            self.routes_to_real_hashes[compiled_route] = real_bucket_hash

        bucket = self._get_bucket_for_real_hash(real_bucket_hash, True)
        return bucket.acquire(), real_bucket_hash

    def update_rate_limits(
        self,
        compiled_route: routes.CompiledRoute,
        real_bucket_hash: str,
        bucket_header: str,
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
            real_bucket_hash:
                The hash returned by :meth:`acquire`
            bucket_header:
                The X-RateLimit-Bucket header.
            remaining_header:
                The X-RateLimit-Remaining header cast to an :class:`int`.
            limit_header:
                The X-RateLimit-Limit header cast to an :class:`int`.
            date_header:
                The Date header value as a :class:`datetime.datetime`.
            reset_at_header:
                The X-RateLimit-Reset header value as a :class:`datetime.datetime`.
        """
        bucket = self.real_hashes_to_buckets.get(real_bucket_hash)
        if bucket is None or not real_bucket_hash.startswith(bucket_header):
            if compiled_route in self.routes_to_real_hashes:
                del self.routes_to_real_hashes[compiled_route]

            # Recompute vital hashes.
            real_bucket_hash = compiled_route.create_real_bucket_hash(bucket_header)

            self.routes_to_real_hashes[compiled_route] = real_bucket_hash
            bucket = self._get_bucket_for_real_hash(real_bucket_hash, True)
            self.real_hashes_to_buckets[real_bucket_hash] = bucket

        reset_after = (reset_at_header - date_header).total_seconds()
        reset_at_monotonic = time.perf_counter() + reset_after
        bucket.update_rate_limit(remaining_header, limit_header, reset_at_monotonic)

    def _get_bucket_for_real_hash(self, real_bucket_hash: str, create_if_not_present: bool) -> Bucket:
        if create_if_not_present and real_bucket_hash not in self.real_hashes_to_buckets:
            self.logger.debug("creating new bucket for %s", real_bucket_hash)
            bucket = Bucket(real_bucket_hash)
            self.real_hashes_to_buckets[real_bucket_hash] = bucket
            return bucket
        else:
            return self.real_hashes_to_buckets[real_bucket_hash]
