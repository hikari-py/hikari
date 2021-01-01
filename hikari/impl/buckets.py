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
"""Rate-limit extensions for RESTful bucketed endpoints.

Provides implementations for the complex rate limiting mechanisms that Discord
requires for rate limit handling that conforms to the passed bucket headers
correctly.

This was initially a bit of a headache for me to understand, personally, since
there is a lot of "implicit detail" that is easy to miss from the documentation.

In an attempt to make this somewhat understandable by anyone else, I have tried
to document the theory of how this is handled here.

What is the theory behind this implementation?
----------------------------------------------

In this module, we refer to a `hikari.internal.routes.CompiledRoute` as a definition
of a route with specific major parameter values included (e.g.
`POST /channels/123/messages`), and a `hikari.internal.routes.Route` as a
definition of a route without specific parameter values included (e.g.
`POST /channels/{channel}/messages`). We can compile a
`hikari.internal.routes.CompiledRoute` from a `hikari.internal.routes.Route`
by providing the corresponding parameters as kwargs, as you may already know.

In this module, a "bucket" is an internal data structure that tracks and
enforces the rate limit state for a specific `hikari.internal.routes.CompiledRoute`,
and can manage delaying tasks in the event that we begin to get rate limited.
It also supports providing in-order execution of queued tasks.

Discord allocates types of buckets to routes. If you are making a request and
there is a valid rate limit on the route you hit, you should receive an
`X-RateLimit-Bucket` header from the server in your response. This is a hash
that identifies a route based on internal criteria that does not include major
parameters. This `X-RateLimitBucket` is known in this module as an "bucket hash".

This means that generally, the route `POST /channels/123/messages` and
`POST /channels/456/messages` will usually sit in the same bucket, but
`GET /channels/123/messages/789` and `PATCH /channels/123/messages/789` will
usually not share the same bucket. Discord may or may not change this at any
time, so hard coding this logic is not a useful thing to be doing.

Rate limits, on the other hand, apply to a bucket and are specific to the major
parameters of the compiled route. This means that `POST /channels/123/messages`
and `POST /channels/456/messages` do not share the same real bucket, despite
Discord providing the same bucket hash. A real bucket hash is the `builtins.str` hash of
the bucket that Discord sends us in a response concatenated to the corresponding
major parameters. This is used for quick bucket indexing internally in this
module.

One issue that occurs from this is that we cannot effectively hash a
`hikari.internal.routes.CompiledRoute` that has not yet been hit, meaning that
until we receive a response from this endpoint, we have no idea what our rate
limits could be, nor the bucket that they sit in. This is usually not
problematic, as the first request to an endpoint should never be rate limited
unless you are hitting it from elsewhere in the same time window outside your
hikari.applications. To manage this situation, unknown endpoints are allocated to
a special unlimited bucket until they have an initial bucket hash code allocated
from a response. Once this happens, the route is reallocated a dedicated bucket.
Unknown buckets have a hardcoded initial hash code internally.

Initially acquiring time on a bucket
------------------------------------

Each time you `BaseRateLimiter.acquire()` a request timeslice for a given
`hikari.internal.routes.Route`, several things happen. The first is that we
attempt to find the existing bucket for that route, if there is one, or get an
unknown bucket otherwise. This is done by creating a real bucket hash from the
compiled route. The initial hash is calculated using a lookup table that maps
`hikari.internal.routes.CompiledRoute` objects to their corresponding initial hash
codes, or to the unknown bucket hash code if not yet known. This initial hash is
processed by the `hikari.internal.routes.CompiledRoute` to provide the real bucket
hash we need to get the route's bucket object internally.

The `BaseRateLimiter.acquire()` method will take the bucket and acquire a new
timeslice on it. This takes the form of a `asyncio.Future` which should be
awaited by the caller and will complete once the caller is allowed to make a
request. Most of the time, this is done instantly, but if the bucket has an
active rate limit preventing requests being sent, then the future will be paused
until the rate limit is over. This may be longer than the rate limit period if
you have queued a large number of requests during this limit, as it is
first-come-first-served.

Acquiring a rate limited bucket will start a bucket-wide task (if not already
running) that will wait until the rate limit has completed before allowing more
futures to complete. This is done while observing the rate limits again, so can
easily begin to re-ratelimit itself if needed. Once the task is complete, it
tidies itself up and disposes of itself. This task will complete once the queue
becomes empty.

The result of `RESTBucketManager.acquire()` is a tuple of a `asyncio.Future` to
await on which completes when you are allowed to proceed with making a request,
and a real bucket hash which should be stored temporarily. This will be
explained in the next section.

Handling the rate limit headers of a response
---------------------------------------------

Once you have received your response, you are expected to extract the values of
the vital rate limit headers manually and parse them to the correct data types.
These headers are:

* `X-RateLimit-Limit`:
    an `builtins.int` describing the max requests in the bucket from empty to
    being rate limited.
* `X-RateLimit-Remaining`:
    an `builtins.int` describing the remaining number of requests before rate
    limiting occurs in the current window.
* `X-RateLimit-Bucket`:
    a `builtins.str` containing the initial bucket hash.
* `x-ratelimit-reset-after`:
    a `builtins.float` containing the number of seconds when the current rate
    limit bucket will reset with decimal millisecond precision.

Each of the above values should be passed to the `update_rate_limits` method to
ensure that the bucket you acquired time from is correctly updated should
Discord decide to alter their ratelimits on the fly without warning (including
timings and the bucket).

This method will manage creating new buckets as needed and resetting vital
information in each bucket you use.

Tidying up
----------

To prevent unused buckets cluttering up memory, each `RESTBucketManager`
instance spins up a `asyncio.Task` that periodically locks the bucket list
(not threadsafe, only using the concept of asyncio not yielding in regular
functions) and disposes of any clearly stale buckets that are no longer needed.
These will be recreated again in the future if they are needed.

When shutting down an application, one must remember to `close()` the
`RESTBucketManager` that has been used. This will ensure the garbage collection
task is stopped, and will also ensure any remaining futures in any bucket queues
have an `asyncio.CancelledError` set on them to prevent deadlocking ratelimited
calls that may be waiting to be unlocked.

Body-field-specific rate limiting
---------------------------------

As of the start of June, 2020, Discord appears to be enforcing another layer
of rate limiting logic to their HTTP APIs which is field-specific. This means
that special rate limits will also exist on some endpoints that limit based
on what attributes you send in a JSON or form data payload.

No information is sent in headers about these specific limits. You will only
be made aware that they exist once you get ratelimited. In the 429 ratelimited
response, you will have the `"global"` attribute set to `builtins.False`, and a
`"reset_after"` attribute that differs entirely to the `x-ratelimit-reset-after`
header. Thus, it is important to not assume the value in the 429 response
for the reset time is the same as the one in the bucket headers. Hikari's
`hikari.api.rest.RESTClient` implementation specifically uses the value furthest
in the future when working out which bucket to adhere to.

It is worth remembering that there is an API limit to the number of 401s,
403s, and 429s you receive, which is around 10,000 per 15 minutes. Passing this
limit results in a soft ban of your account.

At the time of writing, the only example of this appears to be on the
`PATCH /channels/{channel_id}` endpoint. This has a limit of two changes per
10 minutes. More details about how this is implemented have yet to be
released or documented...


Caveats
-------

These implementations rely on Discord sending consistent buckets back to us.

This also begins to crumble if more than one HTTP client is in use, since
there is no performent way to communicate shared rate limits between
distributed applications. The general concept to follow is that if you are
making repeated API calls, or calls that are not event-based (e.g.
fetching messages on a timer), then this can be considered a form of API abuse
and should be used sparingly.
"""

from __future__ import annotations

__all__: typing.List[str] = ["UNKNOWN_HASH", "RESTBucket", "RESTBucketManager"]

import asyncio
import logging
import typing

from hikari import errors
from hikari.impl import rate_limits
from hikari.internal import aio
from hikari.internal import routes
from hikari.internal import time
from hikari.internal import ux

if typing.TYPE_CHECKING:
    import types

UNKNOWN_HASH: typing.Final[str] = "UNKNOWN"
"""The hash used for an unknown bucket that has not yet been resolved."""

_LOGGER: typing.Final[logging.Logger] = logging.getLogger("hikari.ratelimits")


class RESTBucket(rate_limits.WindowedBurstRateLimiter):
    """Represents a rate limit for an HTTP endpoint.

    Component to represent an active rate limit bucket on a specific HTTP route
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

    __slots__: typing.Sequence[str] = ("compiled_route",)

    compiled_route: typing.Final[routes.CompiledRoute]
    """The compiled route that this rate limit is covering."""

    def __init__(self, name: str, compiled_route: routes.CompiledRoute) -> None:
        super().__init__(name, 1, 1)
        self.compiled_route = compiled_route

    @property
    def is_unknown(self) -> bool:
        """Return `builtins.True` if the bucket represents an `UNKNOWN` bucket."""
        return self.name.startswith(UNKNOWN_HASH)

    def acquire(self) -> asyncio.Future[None]:
        """Acquire time on this rate limiter.

        !!! note
            You should afterwards invoke `RESTBucket.update_rate_limit` to
            update any rate limit information you are made aware of.

        Returns
        -------
        asyncio.Future[builtins.None]
            A future that should be awaited immediately. Once the future completes,
            you are allowed to proceed with your operation.
        """
        return aio.completed_future(None) if self.is_unknown else super().acquire()

    def update_rate_limit(self, remaining: int, limit: int, reset_at: float) -> None:
        """Amend the rate limit.

        Parameters
        ----------
        remaining : builtins.int
            The calls remaining in this time window.
        limit : builtins.int
            The total calls allowed in this time window.
        reset_at : builtins.float
            The epoch at which to reset the limit.

        !!! note
            The `reset_at` epoch is expected to be a `time.monotonic_timestamp`
            monotonic epoch, rather than a `time.time` date-based epoch.
        """
        self.remaining = remaining
        self.limit = limit
        self.reset_at = reset_at
        self.period = max(0.0, self.reset_at - time.monotonic())

    def drip(self) -> None:
        """Decrement the remaining count for this bucket.

        !!! note
            If the bucket is marked as `RESTBucket.is_unknown`, then this will
            not do anything. `Unknown` buckets have infinite rate limits.
        """
        # We don't drip unknown buckets: we cannot rate limit them as we don't know their real bucket hash or
        # the current rate limit values Discord put on them...
        if not self.is_unknown:
            self.remaining -= 1


class RESTBucketManager:
    """The main rate limiter implementation for HTTP clients.

    This is designed to provide bucketed rate limiting for Discord HTTP
    endpoints that respects the `X-RateLimit-Bucket` rate limit header. To do
    this, it makes the assumption that any limit can change at any time.

    Parameters
    ----------
    max_rate_limit : builtins.float
        The max number of seconds to backoff for when rate limited. Anything
        greater than this will instead raise an error.
    """

    _POLL_PERIOD: typing.Final[typing.ClassVar[int]] = 20
    _EXPIRE_PERIOD: typing.Final[typing.ClassVar[int]] = 10

    __slots__: typing.Sequence[str] = (
        "routes_to_hashes",
        "real_hashes_to_buckets",
        "closed_event",
        "gc_task",
        "max_rate_limit",
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

    gc_task: typing.Optional[asyncio.Task[None]]
    """The internal garbage collector task."""

    max_rate_limit: float
    """The max number of seconds to backoff for when rate limited.

    Anything greater than this will instead raise an error.
    """

    def __init__(self, max_rate_limit: float) -> None:
        self.routes_to_hashes = {}
        self.real_hashes_to_buckets = {}
        self.closed_event: asyncio.Event = asyncio.Event()
        self.gc_task: typing.Optional[asyncio.Task[None]] = None
        self.max_rate_limit = max_rate_limit

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
        poll_period : builtins.float
            Period to poll the garbage collector at in seconds. Defaults
            to `20` seconds.
        expire_after : builtins.float
            Time after which the last `reset_at` was hit for a bucket to
            remove it. Higher values will retain unneeded ratelimit info for
            longer, but may produce more effective rate-limiting logic as a
            result. Using `0` will make the bucket get garbage collected as soon
            as the rate limit has reset. Defaults to `10` seconds.
        """
        if not self.gc_task:
            self.gc_task = asyncio.create_task(self.gc(poll_period, expire_after))

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

        if self.gc_task is not None:
            self.gc_task.cancel()
            self.gc_task = None

    # Ignore docstring not starting in an imperative mood
    async def gc(self, poll_period: float, expire_after: float) -> None:  # noqa: D401
        """The garbage collector loop.

        This is designed to run in the background and manage removing unused
        route references from the rate-limiter collection to save memory.

        This will run forever until `RESTBucketManager.closed_event` is set.
        This will invoke `RESTBucketManager.do_gc_pass` periodically.

        Parameters
        ----------
        poll_period : builtins.float
            The period to poll at.
        expire_after : builtins.float
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
        _LOGGER.log(ux.TRACE, "rate limit garbage collector started")
        while not self.closed_event.is_set():
            try:
                await asyncio.wait_for(self.closed_event.wait(), timeout=poll_period)
            except asyncio.TimeoutError:
                _LOGGER.log(ux.TRACE, "performing rate limit garbage collection pass")
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
        expire_after : builtins.float
            Time after which the last `reset_at` was hit for a bucket to\
            remove it. Defaults to `reset_at` + 20 seconds. Higher values will
            retain unneeded ratelimit info for longer, but may produce more
            effective ratelimiting logic as a result.

        !!! warning
            You generally have no need to invoke this directly. Use
            `RESTBucketManager.start` and `RESTBucketManager.close` to control
            this instead.
        """
        buckets_to_purge = []

        now = time.monotonic()

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
                # but we will not know about it.
                buckets_to_purge.append(full_hash)

            if bucket.reset_at >= now:
                active += 1

        dead = len(buckets_to_purge)
        total = len(bucket_pairs)
        survival = total - active - dead

        for full_hash in buckets_to_purge:
            self.real_hashes_to_buckets[full_hash].close()
            del self.real_hashes_to_buckets[full_hash]

        _LOGGER.log(ux.TRACE, "purged %s stale buckets, %s remain in survival, %s active", dead, survival, active)

    def acquire(self, compiled_route: routes.CompiledRoute) -> asyncio.Future[None]:
        """Acquire a bucket for the given route.

        Parameters
        ----------
        compiled_route : hikari.internal.routes.CompiledRoute
            The route to get the bucket for.

        Returns
        -------
        asyncio.Future[builtins.None]
            A future to await that completes when you are allowed to run
            your request logic.

        !!! note
            The returned future MUST be awaited, and will complete when your
            turn to make a call comes along. You are expected to await this and
            then immediately make your HTTP call. The returned future may
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
            _LOGGER.debug("%s is being mapped to existing bucket %s", compiled_route, real_bucket_hash)
        except KeyError:
            _LOGGER.debug("%s is being mapped to new bucket %s", compiled_route, real_bucket_hash)
            bucket = RESTBucket(real_bucket_hash, compiled_route)
            self.real_hashes_to_buckets[real_bucket_hash] = bucket

        now = time.monotonic()
        retry_after = bucket.reset_at - now

        if bucket.is_rate_limited(now) and retry_after > self.max_rate_limit:
            raise errors.RateLimitTooLongError(
                route=compiled_route,
                retry_after=retry_after,
                max_retry_after=self.max_rate_limit,
                reset_at=bucket.reset_at,
                limit=bucket.limit,
                period=bucket.period,
            )

        return bucket.acquire()

    def update_rate_limits(
        self,
        compiled_route: routes.CompiledRoute,
        bucket_header: str,
        remaining_header: int,
        limit_header: int,
        reset_after: float,
    ) -> None:
        """Update the rate limits for a bucket using info from a response.

        Parameters
        ----------
        compiled_route : hikari.internal.routes.CompiledRoute
            The compiled route to get the bucket for.
        bucket_header : typing.Optional[builtins.str]
            The `X-RateLimit-Bucket` header that was provided in the response.
        remaining_header : builtins.int
            The `X-RateLimit-Remaining` header cast to an `builtins.int`.
        limit_header : builtins.int
            The `X-RateLimit-Limit`header cast to an `builtins.int`.
        reset_after : builtins.float
            The `x-ratelimit-reset-after` cast to a `builtins.float`.
        """
        self.routes_to_hashes[compiled_route.route] = bucket_header

        real_bucket_hash = compiled_route.create_real_bucket_hash(bucket_header)

        reset_at_monotonic = time.monotonic() + reset_after

        if real_bucket_hash in self.real_hashes_to_buckets:
            bucket = self.real_hashes_to_buckets[real_bucket_hash]
            _LOGGER.debug(
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
            _LOGGER.debug(
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
        """Return `builtins.True` if the rate limiter GC task is started."""
        return self.gc_task is not None
