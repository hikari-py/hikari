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
"""Rate-limit implementations for the RESTSession clients."""

from __future__ import annotations

import asyncio
import datetime
import logging
import time
import types
import typing

from hikari.internal import more_asyncio
from hikari.internal import more_typing
from hikari.internal import ratelimits

from . import routes

UNKNOWN_HASH: typing.Final[str] = "UNKNOWN"
"""The hash used for an unknown bucket that has not yet been resolved."""


class RESTBucket(ratelimits.WindowedBurstRateLimiter):
    """Represents a rate limit for an RESTSession endpoint.

    Component to represent an active rate limit bucket on a specific RESTSession route
    with a specific major parameter combo.

    This is somewhat similar to the `WindowedBurstRateLimiter` in how it
    works.

    This algorithm will use fixed-period time windows that have a given limit
    (capacity). Each time a task requests processing time, it will drip another
    unit into the bucket. Once the bucket has reached its limit, nothing can
    drip and new tasks will be queued until the time window finishes.

    Once the time window finishes, the bucket will empty, returning the current
    capacity to zero, and tasks that are queued will start being able to drip
    again.

    Additional logic is provided by the `RESTBucket.update_rate_limit` call
    which allows dynamically changing the enforced rate limits at any time.
    """

    __slots__ = ("compiled_route",)

    compiled_route: typing.Final[routes.CompiledRoute]
    """The compiled route that this rate limit is covering."""

    def __init__(self, name: str, compiled_route: routes.CompiledRoute) -> None:
        super().__init__(name, 1, 1)
        self.compiled_route = compiled_route

    @property
    def is_unknown(self) -> bool:
        """Return `True` if the bucket represents an `UNKNOWN` bucket."""
        return self.name.startswith(UNKNOWN_HASH)

    def acquire(self) -> more_typing.Future[None]:
        """Acquire time on this rate limiter.

        !!! note
            You should afterwards invoke `RESTBucket.update_rate_limit` to
            update any rate limit information you are made aware of.

        Returns
        -------
        asyncio.Future
            A future that should be awaited immediately. Once the future completes,
            you are allowed to proceed with your operation.
        """
        return more_asyncio.completed_future(None) if self.is_unknown else super().acquire()

    def update_rate_limit(self, remaining: int, limit: int, reset_at: float) -> None:
        """Amend the rate limit.

        Parameters
        ----------
        remaining : int
            The calls remaining in this time window.
        limit : int
            The total calls allowed in this time window.
        reset_at : float
            The epoch at which to reset the limit.

        !!! note
            The `reset_at` epoch is expected to be a `time.perf_counter`
            monotonic epoch, rather than a `time.time` date-based epoch.
        """
        self.remaining = remaining
        self.limit = limit
        self.reset_at = reset_at
        self.period = max(0.0, self.reset_at - time.perf_counter())

    def drip(self) -> None:
        """Decrement the remaining count for this bucket.

        !!! note
            If the bucket is marked as `RESTBucket.is_unknown`, then this will
            not do anything. `Unknown` buckets have infinite rate limits.
        """
        # We don't drip unknown buckets: we can't rate limit them as we don't know their real bucket hash or
        # the current rate limit values Discord put on them...
        if not self.is_unknown:
            self.remaining -= 1


class RESTBucketManager:
    """The main rate limiter implementation for RESTSession clients.

    This is designed to provide bucketed rate limiting for Discord RESTSession
    endpoints that respects the `X-RateLimit-Bucket` rate limit header. To do
    this, it makes the assumption that any limit can change at any time.
    """

    _POLL_PERIOD: typing.Final[typing.ClassVar[int]] = 20
    _EXPIRE_PERIOD: typing.Final[typing.ClassVar[int]] = 10

    __slots__ = (
        "routes_to_hashes",
        "real_hashes_to_buckets",
        "closed_event",
        "gc_task",
        "logger",
    )

    routes_to_hashes: typing.Final[typing.MutableMapping[routes.Route, str]]
    """Maps routes to their `X-RateLimit-Bucket` header being used."""

    real_hashes_to_buckets: typing.Final[typing.MutableMapping[str, RESTBucket]]
    """Maps full bucket hashes (`X-RateLimit-Bucket` appended with a hash of
    major parameters used in that compiled route) to their corresponding rate
    limiters.
    """

    closed_event: typing.Final[asyncio.Event]
    """An internal event that is set when the object is shut down."""

    gc_task: typing.Optional[more_typing.Task[None]]
    """The internal garbage collector task."""

    logger: typing.Final[logging.Logger]
    """The logger to use for this object."""

    def __init__(self) -> None:
        self.routes_to_hashes = {}
        self.real_hashes_to_buckets = {}
        self.closed_event: asyncio.Event = asyncio.Event()
        self.gc_task: typing.Optional[asyncio.Task] = None
        self.logger = logging.getLogger("hikari.rest.buckets.RESTBucketManager")

    def __enter__(self) -> RESTBucketManager:
        return self

    def __exit__(self, exc_type: typing.Type[Exception], exc_val: Exception, exc_tb: types.TracebackType) -> None:
        self.close()

    def __del__(self) -> None:
        self.close()

    def start(self, poll_period: float = _POLL_PERIOD, expire_after: float = _EXPIRE_PERIOD) -> None:
        """Start this ratelimiter up.

        This spins up internal garbage collection logic in the background to
        keep memory usage to an optimal level as old routes and bucket hashes
        get discarded and replaced.

        Parameters
        ----------
        poll_period : float
            Period to poll the garbage collector at in seconds. Defaults
            to `20` seconds.
        expire_after : float
            Time after which the last `reset_at` was hit for a bucket to
            remove it. Higher values will retain unneeded ratelimit info for
            longer, but may produce more effective ratelimiting logic as a
            result. Using `0` will make the bucket get garbage collected as soon
            as the rate limit has reset. Defaults to `10` seconds.
        """
        if not self.gc_task:
            self.gc_task = asyncio.get_running_loop().create_task(self.gc(poll_period, expire_after))

    def close(self) -> None:
        """Close the garbage collector and kill any tasks waiting on ratelimits.

        Once this has been called, this object is considered to be effectively
        dead. To reuse it, one should create a new instance.
        """
        self.closed_event.set()
        for bucket in self.real_hashes_to_buckets.values():
            bucket.close()
        self.real_hashes_to_buckets.clear()
        self.routes_to_hashes.clear()

    # Ignore docstring not starting in an imperative mood
    async def gc(self, poll_period: float, expire_after: float) -> None:  # noqa: D401
        """The garbage collector loop.

        This is designed to run in the background and manage removing unused
        route references from the rate-limiter collection to save memory.

        This will run forever until `RESTBucketManager. closed_event` is set.
        This will invoke `RESTBucketManager.do_gc_pass` periodically.

        Parameters
        ----------
        poll_period : float
            The period to poll at.
        expire_after : float
            Time after which the last `reset_at` was hit for a bucket to
            remove it. Higher values will retain unneeded ratelimit info for
            longer, but may produce more effective ratelimiting logic as a
            result. Using `0` will make the bucket get garbage collected as soon
            as the rate limit has reset.

        !!! warning
            You generally have no need to invoke this directly. Use
            `RESTBucketManager.start` and `RESTBucketManager.close` to control
            this instead.
        """
        # Prevent filling memory increasingly until we run out by removing dead buckets every 20s
        # Allocations are somewhat cheap if we only do them every so-many seconds, after all.
        self.logger.debug("rate limit garbage collector started")
        while not self.closed_event.is_set():
            try:
                await asyncio.wait_for(self.closed_event.wait(), timeout=poll_period)
            except asyncio.TimeoutError:
                self.logger.debug("performing rate limit garbage collection pass")
                self.do_gc_pass(expire_after)
        self.gc_task = None

    def do_gc_pass(self, expire_after: float) -> None:
        """Perform a single garbage collection pass.

        This will assess any routes stored in the internal mappings of this
        object and remove any that are deemed to be inactive or dead in order
        to save memory.

        If the removed routes are used again in the future, they will be
        re-cached automatically.

        Parameters
        ----------
        expire_after : float
            Time after which the last `reset_at` was hit for a bucket to
            remove it. Defaults to `reset_at` + 20 seconds. Higher values will
            retain unneeded ratelimit info for longer, but may produce more
            effective ratelimiting logic as a result.

        !!! warning
            You generally have no need to invoke this directly. Use
            `RESTBucketManager.start` and `RESTBucketManager.close` to control
            this instead.
        """
        buckets_to_purge = []

        now = time.perf_counter()

        # We have three main states that a bucket can be in:
        # 1. active - the bucket is active and is not at risk of deallocation
        # 2. survival - the bucket is inactive but is still fresh enough to be kept alive.
        # 3. death - the bucket has been inactive for too long.
        active = 0

        # Discover and purge
        bucket_pairs = self.real_hashes_to_buckets.items()

        for full_hash, bucket in bucket_pairs:
            if bucket.is_empty and bucket.reset_at + expire_after < now:
                # If it is still running a throttle and is in memory, it will remain in memory
                # but we won't know about it.
                buckets_to_purge.append(full_hash)

            if bucket.reset_at >= now:
                active += 1

        dead = len(buckets_to_purge)
        total = len(bucket_pairs)
        survival = total - active - dead

        for full_hash in buckets_to_purge:
            self.real_hashes_to_buckets[full_hash].close()
            del self.real_hashes_to_buckets[full_hash]

        self.logger.debug("purged %s stale buckets, %s remain in survival, %s active", dead, survival, active)

    def acquire(self, compiled_route: routes.CompiledRoute) -> more_typing.Future[None]:
        """Acquire a bucket for the given route.

        Parameters
        ----------
        compiled_route : hikari.rest.routes.CompiledRoute
            The route to get the bucket for.

        Returns
        -------
        asyncio.Future
            A future to await that completes when you are allowed to run
            your request logic.

        !!! note
            The returned future MUST be awaited, and will complete when your
            turn to make a call comes along. You are expected to await this and
            then immediately make your RESTSession call. The returned future may
            already be completed if you can make the call immediately.
        """
        # Returns a future to await on to wait to be allowed to send the request, and a
        # bucket hash to use to update rate limits later.
        template = compiled_route.route

        if template in self.routes_to_hashes:
            bucket_hash = self.routes_to_hashes[template]
        else:
            bucket_hash = UNKNOWN_HASH
            self.routes_to_hashes[template] = bucket_hash

        real_bucket_hash = compiled_route.create_real_bucket_hash(bucket_hash)

        try:
            bucket = self.real_hashes_to_buckets[real_bucket_hash]
            self.logger.debug("%s is being mapped to existing bucket %s", compiled_route, real_bucket_hash)
        except KeyError:
            self.logger.debug("%s is being mapped to new bucket %s", compiled_route, real_bucket_hash)
            bucket = RESTBucket(real_bucket_hash, compiled_route)
            self.real_hashes_to_buckets[real_bucket_hash] = bucket

        return bucket.acquire()

    def update_rate_limits(
        self,
        compiled_route: routes.CompiledRoute,
        bucket_header: typing.Optional[str],
        remaining_header: int,
        limit_header: int,
        date_header: datetime.datetime,
        reset_at_header: datetime.datetime,
    ) -> None:
        """Update the rate limits for a bucket using info from a response.

        Parameters
        ----------
        compiled_route : hikari.rest.routes.CompiledRoute
            The compiled route to get the bucket for.
        bucket_header : str, optional
            The `X-RateLimit-Bucket` header that was provided in the response,
            or `None` if not present.
        remaining_header : int
            The `X-RateLimit-Remaining` header cast to an `int`.
        limit_header : int
            The `X-RateLimit-Limit`header cast to an `int`.
        date_header : datetime.datetime
            The `Date` header value as a `datetime.datetime`.
        reset_at_header : datetime.datetime
            The `X-RateLimit-Reset` header value as a `datetime.datetime`.
        """
        self.routes_to_hashes[compiled_route.route] = bucket_header

        real_bucket_hash = compiled_route.create_real_bucket_hash(bucket_header)

        reset_after = (reset_at_header - date_header).total_seconds()
        reset_at_monotonic = time.perf_counter() + reset_after

        if real_bucket_hash in self.real_hashes_to_buckets:
            bucket = self.real_hashes_to_buckets[real_bucket_hash]
            self.logger.debug(
                "updating %s with bucket %s [reset-after:%ss, limit:%s, remaining:%s]",
                compiled_route,
                real_bucket_hash,
                reset_after,
                limit_header,
                remaining_header,
            )
        else:
            bucket = RESTBucket(real_bucket_hash, compiled_route)
            self.real_hashes_to_buckets[real_bucket_hash] = bucket
            self.logger.debug(
                "remapping %s with bucket %s [reset-after:%ss, limit:%s, remaining:%s]",
                compiled_route,
                real_bucket_hash,
                reset_after,
                limit_header,
                remaining_header,
            )

        bucket.update_rate_limit(remaining_header, limit_header, reset_at_monotonic)

    @property
    def is_started(self) -> bool:
        """Return `True` if the rate limiter GC task is started."""
        return self.gc_task is not None
