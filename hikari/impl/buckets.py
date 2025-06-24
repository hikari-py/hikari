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

In this module, we refer to a `CompiledRoute` as a definition
of a route with specific major parameter values included (e.g.
`POST /channels/123/messages`), and a `Route` as a definition of a route
without specific parameter values included
(e.g. `POST /channels/{channel}/messages`). We can create a `CompiledRoute`
from a `Route` by providing the corresponding parameters as kwargs, as you
may already know.

In this module, a "bucket" is an internal data structure that tracks and
enforces the rate limit state for a specific `CompiledRoute`,
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
Discord providing the same bucket hash. A real bucket hash is the string hash of
the bucket that Discord sends us in a response concatenated to the corresponding
major parameters. This is used for quick bucket indexing internally in this
module.

It is important to note that, as of 2022-11-02 @ 14:30 PT, all buckets use a
sliding window/leaky bucket implementation, which means that we can perform
requests quickly and no longer have stick to a strict window timing. Discord
does not unfortunately expose the rate at which buckets refill, so we need
to do some maths to accurately calculate it, which you can find in this
implementation.

This implementation is also built for concurrency, so extra care is taken to
update only specific information about the buckets, and under specific
circumstances, as to avoid Discord changing running buckets, which shouldn't
happen, but better safe than sorry!

One issue that occurs from this is that we cannot effectively hash a
`CompiledRoute` that has not yet been hit, meaning that
until we receive a response from this endpoint, we have no idea what our rate
limits could be, nor the bucket that they sit in. This is usually not
problematic, as the first request to an endpoint should never be rate limited
unless you are hitting it from elsewhere in the same time window outside your
[`hikari.applications`][]. To manage this situation, unknown endpoints are allocated to
a special unlimited bucket until they have an initial bucket hash code allocated
from a response. Once this happens, the route is reallocated a dedicated bucket.
Unknown buckets have a hardcoded initial hash code internally.

Initially acquiring time on a bucket
------------------------------------

Each time you call [`hikari.impl.buckets.RESTBucket.acquire`][] a request
timeslice for a given `Route`, several things happen. The first is that we
attempt to find the existing bucket for that route, if there is one, or get an
unknown bucket otherwise. This is done by creating a real bucket hash from the
compiled route. The initial hash is calculated using a lookup table that maps
`CompiledRoute` objects to their corresponding initial hash
codes, or to the unknown bucket hash code if not yet known. This initial hash is
processed by the `CompiledRoute` to provide the real bucket
hash we need to get the route's bucket object internally.

The [`hikari.impl.buckets.RESTBucket.acquire`][] method will take the
bucket and acquire a new timeslice on it. This takes the form of a
[`asyncio.Future`][] that is awaited and will complete once the caller is allowed
to make a request. Most of the time, this is done instantly, but if the bucket
has an active rate limit preventing requests being sent, then the future will
be paused until the rate limit is over. This may be longer than the rate limit
period if you have queued a large number of requests during this limit, as it
is first-come-first-served.

Acquiring a rate limited bucket will start a bucket-wide task (if not already
running) that will wait until the rate limit has completed before allowing more
futures to complete. This is done while observing the rate limits again, so can
easily begin to re-ratelimit itself if needed. Once the task is complete, it
tidies itself up and disposes of itself. This task will complete once the queue
becomes empty.

The result of [`hikari.impl.buckets.RESTBucketManager.acquire_bucket`][] is an async
context manager that must be acquired during the entirety of the request and
released once it is done (in reality, it is just a
[`hikari.impl.buckets.RESTBucket`][], but we want the ratelimit update to be
forced through [`hikari.impl.buckets.RESTBucketManager.update_rate_limits`][]
to keep proper state)

Handling the rate limit headers of a response
---------------------------------------------

Once you have received your response, you are expected to extract the values of
the vital rate limit headers manually and parse them to the correct data types.
These headers are:

* `X-RateLimit-Limit`:
    an [`int`][] describing the max requests in the bucket from empty to
    being rate limited.
* `X-RateLimit-Remaining`:
    an [`int`][] describing the remaining number of requests before rate
    limiting occurs in the current window.
* `X-RateLimit-Bucket`:
    a [`str`][] containing the initial bucket hash.
* `X-RateLimit-Reset`:
    a [`float`][] containing the epoch in seconds (with decimal millisecond
    precision) at which the current rate limit bucket will fully reset.
* `X-RateLimit-Reset-After`:
    a [`float`][] containing the number of seconds (with decimal millisecond
    precision) after which the current rate limit bucket will fully reset.

Each of the above values should be passed to the
[`hikari.impl.buckets.RESTBucketManager.update_rate_limits`][] method to
ensure that the bucket you acquired time from is correctly updated should
Discord decide to alter their ratelimits on the fly without warning (including
timings and the bucket).

This method will manage creating new buckets as needed and resetting vital
information in each bucket you use.

Tidying up
----------

To prevent unused buckets cluttering up memory, each [`hikari.impl.buckets.RESTBucketManager`][]
instance spins up a [`asyncio.Task`][] that periodically locks the bucket list
(not threadsafe, only using the concept of asyncio not yielding in regular
functions) and disposes of any clearly stale buckets that are no longer needed.
These will be recreated again in the future if they are needed.

When shutting down an application, one must remember to call
[`hikari.impl.buckets.RESTBucketManager.close`][]. This will ensure the
garbage collection task is stopped, and will also ensure any remaining futures
in any bucket queues have an [`asyncio.CancelledError`][] set on them to prevent
deadlocking ratelimited calls that may be waiting to be unlocked.

Body-field-specific rate limiting
---------------------------------

As of the start of June, 2020, Discord appears to be enforcing another layer
of rate limiting logic to their HTTP APIs which is field-specific. This means
that special rate limits will also exist on some endpoints that limit based
on what attributes you send in a JSON or form data payload.

No information is sent in headers about these specific limits. You will only
be made aware that they exist once you get ratelimited. In the 429 ratelimited
response, you will have the `"global"` attribute set to [`False`][], and a
`"reset_after"` attribute that differs entirely to the `X-RateLimit-Reset-After`
header. Thus, it is important to not assume the value in the 429 response
for the reset time is the same as the one in the bucket headers. hikari's
[`hikari.api.rest.RESTClient`][] implementation specifically uses the value
furthest in the future when working out which bucket to adhere to.

It is worth remembering that there is an API limit to the number of 401s,
403s, and 429s you receive, which is around 10,000 per 15 minutes. Passing this
limit results in a soft ban of your account.

The true nature of these limits are not known and Discord staff have repeatedly
pointed to them never being documented for the sake of system integrity.
These special ratelimits are not something a normal user should encounter
unless they are calling a single route multiple times with the end goal
of editing a single attribute in quick succession. It is up to Discord's
discretion on what is considered as "spammy" behaviour and one they would
not like to allow on their API.

These ratelimits should not be "properly" handled and instead be avoided
completely by the end developer (similar to Cloudflare 429s).
"""

from __future__ import annotations

__all__: typing.Sequence[str] = ("UNKNOWN_HASH", "RESTBucket", "RESTBucketManager")

import asyncio
import logging
import math
import typing

from hikari import errors
from hikari.impl import rate_limits
from hikari.internal import routes
from hikari.internal import time
from hikari.internal import typing_extensions
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

    This is somewhat similar to [`hikari.impl.rate_limits.WindowedBurstRateLimiter`][] in how it
    works, except it uses a sliding window instead, which means that we will gain back the
    ability to make a request based on a recovery rate, rather than being constraint to a full
    window.

    This algorithm will use fixed-period time windows that have a given limit
    (capacity). Each time a task requests processing time, it will drip another
    unit into the bucket. Once the bucket has reached its limit, nothing can
    drip and new tasks will be queued until the time window finishes.

    Once the time window finishes, the bucket will empty, returning the current
    capacity to zero, and tasks that are queued will start being able to drip
    again.

    Additional logic is provided by the [`hikari.impl.buckets.RESTBucket.update_rate_limit`][] call
    which allows dynamically changing the enforced rate limits at any time.
    """

    __slots__: typing.Sequence[str] = (
        "_compiled_route",
        "_global_ratelimit",
        "_lock",
        "_max_rate_limit",
        "_out_of_sync",
    )

    name: str
    # <<inherited docstring from WindowedBurstRateLimiter>>.

    increase_at: float
    # <<inherited docstring from WindowedBurstRateLimiter>>.

    remaining: int
    # <<inherited docstring from WindowedBurstRateLimiter>>.

    period: float
    # <<inherited docstring from WindowedBurstRateLimiter>>.

    limit: int
    # <<inherited docstring from WindowedBurstRateLimiter>>.

    def __init__(
        self,
        name: str,
        compiled_route: routes.CompiledRoute,
        global_ratelimit: rate_limits.ManualRateLimiter,
        max_rate_limit: float,
    ) -> None:
        super().__init__(name, 1, 1)
        self.increase_at = time.time() + self.period
        self._compiled_route = compiled_route
        self._max_rate_limit = max_rate_limit
        self._global_ratelimit = global_ratelimit
        self._lock = asyncio.Lock()
        self._out_of_sync = False

    async def __aenter__(self) -> None:
        await self.acquire()

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None, exc_tb: types.TracebackType | None
    ) -> None:
        self.release()

    @property
    def is_unknown(self) -> bool:
        """Whether it represents an UNKNOWN bucket."""
        return self.name.startswith(UNKNOWN_HASH)

    def release(self) -> None:
        """Release the lock on the bucket."""
        if self._lock.locked():
            self._lock.release()

    @typing_extensions.override
    async def acquire(self) -> None:
        """Acquire time and the lock on this bucket.

        !!! note
            You should afterwards invoke [`hikari.impl.buckets.RESTBucket.update_rate_limit`][] to
            update any rate limit information you are made aware of and
            [`hikari.impl.buckets.RESTBucket.release`][] to release the lock.

        Raises
        ------
        hikari.errors.RateLimitTooLongError
            If the rate limit is longer than `max_rate_limit`.
        """
        if self.is_unknown:
            await self._lock.acquire()

            if self.is_unknown:
                return

        now = time.time()

        if self.remaining == 0 and self.increase_at - now > self._max_rate_limit:
            raise errors.RateLimitTooLongError(
                route=self._compiled_route,
                is_global=False,
                retry_after=self.get_time_until_increase(time.time()),
                max_retry_after=self._max_rate_limit,
                reset_at=self.increase_at,
                limit=self.limit,
                period=self.period,
            )

        await super().acquire()

        global_ratelimit = self._global_ratelimit
        if global_ratelimit.reset_at and (global_ratelimit.reset_at - now) > self._max_rate_limit:
            # Release lock before we error
            raise errors.RateLimitTooLongError(
                route=self._compiled_route,
                is_global=True,
                retry_after=global_ratelimit.reset_at - now,
                max_retry_after=self._max_rate_limit,
                reset_at=global_ratelimit.reset_at,
                limit=None,
                period=None,
            )

        await global_ratelimit.acquire()

    @typing_extensions.override
    def move_window(self, now: float) -> None:
        # If we are out of sync, we shouldn't slide the window along, as we will be off due to
        # network latency.
        # The second part of this 'if' is to account for some cases where there can be a race
        # condition and we receive rate limit updates out of order, and we cannot update `_out_of_sync`
        if not self._out_of_sync or (now - self.increase_at > self.period):
            gain = math.floor((now - self.increase_at) / self.period) + 1
            now_remaining = self.remaining + gain

            self.remaining = min(self.limit, now_remaining)

            if self.remaining == self.limit:
                self.increase_at = now + self.period
                self._out_of_sync = True
            else:
                self.increase_at = self.increase_at + gain * self.period

    def update_rate_limit(self, remaining: int, limit: int, reset_at: float, reset_after: float) -> None:
        """Update the rate limit information.

        Parameters
        ----------
        remaining
            The `X-RateLimit-Remaining` header cast to an [`int`][].
        limit
            The `X-RateLimit-Limit` header cast to an [`int`][].
        reset_at
            The `X-RateLimit-Reset` header cast to a [`float`][].
        reset_after
            The `X-RateLimit-Reset-After` header cast to a [`float`][].
        """
        if remaining == limit:
            # This should never happen, but just in case
            return

        slide_period = reset_after / (limit - remaining)
        next_slide_at = (reset_at - reset_after) + slide_period
        if next_slide_at < self.increase_at:
            # Old ratelimit information (from last window), ignore
            return

        if self.limit != limit:
            if self.limit > limit:
                _LOGGER.warning(
                    "bucket '%s' decreased its limit (%d -> %d). "
                    "It is possible that you will see a small increase in 429s",
                    self.name,
                    self.limit,
                    limit,
                )
            self.limit = limit
            self.remaining = min(self.remaining, self.limit)

        # We want to update the slide period only, and only if:
        #   1. The bucket is out of sync (ie, we reset the full window)
        #   2. We receive the first usage of the bucket, which will always have the most accurate slide period
        #   3. The slide periods differ too much. This is helpful if we diverged too much from the real one
        #      due to network latency, of if the bucket randomly changed
        #      Note: 0.5 and 0.7 are chosen arbitrarily after some testing
        if self._out_of_sync or remaining == limit - 1 or not math.isclose(self.period, slide_period, abs_tol=0.5):
            if not math.isclose(self.period, slide_period, abs_tol=0.7):
                _LOGGER.warning(
                    "bucket '%s' greatly increased its slide period (%s -> %s). "
                    "It is possible that you will see a small increase in 429s",
                    self.name,
                    self.period,
                    slide_period,
                )

            self._out_of_sync = False
            self.period = slide_period
            self.increase_at = next_slide_at

    def resolve(self, real_bucket_hash: str, remaining: int, limit: int, reset_at: float, reset_after: float) -> None:
        """Set the ratelimit information for this bucket.

        Parameters
        ----------
        real_bucket_hash
            The real bucket hash for this bucket.
        remaining
            The `X-RateLimit-Remaining` header cast to an [`int`][].
        limit
            The `X-RateLimit-Limit` header cast to an [`int`][].
        reset_at
            The `X-RateLimit-Reset` header cast to a [`float`][].
        reset_after
            The `X-RateLimit-Reset-After` header cast to a [`float`][].

        Raises
        ------
        RuntimeError
            If the hash of the bucket is already known.
        """
        if not self.is_unknown:
            msg = "Cannot resolve known bucket"
            raise RuntimeError(msg)

        if remaining == limit:
            # This should never happen, but just in case
            return

        slide_period = reset_after / (limit - remaining)
        self.name = real_bucket_hash
        self.remaining = remaining
        self.limit = limit
        self.period = slide_period
        self.increase_at = (reset_at - reset_after) + self.period
        self._out_of_sync = False


def _create_authentication_hash(authentication: str | None) -> str:
    return str(hash(authentication))


def _create_unknown_hash(route: routes.CompiledRoute, authentication_hash: str) -> str:
    return f"{UNKNOWN_HASH}{routes.HASH_SEPARATOR}{authentication_hash}{routes.HASH_SEPARATOR}{hash(route.route)!s}"


class RESTBucketManager:
    """The main rate limiter implementation for HTTP clients.

    This is designed to provide bucketed rate limiting for Discord HTTP
    endpoints that respects the `X-RateLimit-Bucket` rate limit header. To do
    this, it makes the assumption that any limit can change at any time.

    Parameters
    ----------
    max_rate_limit
        The max number of seconds to backoff for when rate limited. Anything
        greater than this will instead raise an error.
    """

    __slots__: typing.Sequence[str] = (
        "_gc_task",
        "_global_ratelimit",
        "_max_rate_limit",
        "_real_hashes_to_buckets",
        "_route_hash_to_bucket_hash",
    )

    def __init__(self, max_rate_limit: float) -> None:
        self._route_hash_to_bucket_hash: dict[int, str] = {}
        self._real_hashes_to_buckets: dict[str, RESTBucket] = {}
        self._gc_task: asyncio.Task[None] | None = None
        self._max_rate_limit = max_rate_limit
        self._global_ratelimit = rate_limits.ManualRateLimiter()

    @property
    def max_rate_limit(self) -> float:
        return self._max_rate_limit

    @property
    def is_alive(self) -> bool:
        """Whether the component is alive."""
        return self._gc_task is not None

    def start(self, poll_period: float = 20.0, expire_after: float = 10.0) -> None:
        """Start this ratelimiter up.

        This spins up internal garbage collection logic in the background to
        keep memory usage to an optimal level as old routes and bucket hashes
        get discarded and replaced.

        Parameters
        ----------
        poll_period
            Period to poll the garbage collector at in seconds.
        expire_after
            Time after which the last [`hikari.impl.buckets.RESTBucket.reset_at`][] was hit for a bucket to
            remove it. Higher values will retain unneeded ratelimit info for
            longer, but may produce more effective rate-limiting logic as a
            result. Using `0` will make the bucket get garbage collected as soon
            as the rate limit has reset.
        """
        if self._gc_task:
            msg = "Cannot start an active bucket manager"
            raise errors.ComponentStateConflictError(msg)

        # Assert is in running loop
        asyncio.get_running_loop()

        self._gc_task = asyncio.create_task(self._gc(poll_period, expire_after))

    async def close(self) -> None:
        """Close the garbage collector and kill any tasks waiting on ratelimits."""
        if not self._gc_task:
            msg = "Cannot interact with an inactive bucket manager"
            raise errors.ComponentStateConflictError(msg)

        for bucket in self._real_hashes_to_buckets.values():
            bucket.close()

        self._global_ratelimit.close()
        self._real_hashes_to_buckets.clear()
        self._route_hash_to_bucket_hash.clear()

        self._gc_task.cancel()

        try:
            await self._gc_task
        except asyncio.CancelledError:
            pass

        self._gc_task = None

    async def _gc(self, poll_period: float, expire_after: float) -> None:
        # Prevent filling memory increasingly until we run out by removing dead buckets every 20s
        # Allocations are somewhat cheap if we only do them every so-many seconds, after all.
        _LOGGER.log(ux.TRACE, "rate limit garbage collector started")

        while True:
            await asyncio.sleep(poll_period)
            _LOGGER.log(ux.TRACE, "performing rate limit garbage collection pass")
            self._purge_stale_buckets(expire_after)

    def _purge_stale_buckets(self, expire_after: float) -> None:
        buckets_to_purge: list[str] = []

        now = time.time()

        # We have three main states that a bucket can be in:
        # 1. active - the bucket is active and is not at risk of deallocation
        # 2. survival - the bucket is inactive but is still fresh enough to be kept alive.
        # 3. death - the bucket has been inactive for too long.
        active = 0

        # Discover and purge
        bucket_pairs = self._real_hashes_to_buckets.items()

        for full_hash, bucket in bucket_pairs:
            if bucket.is_empty and bucket.increase_at + expire_after < now:
                # If it is still running a throttle and is in memory, it will remain in memory
                # but we will not know about it.
                buckets_to_purge.append(full_hash)

            if now > bucket.increase_at:
                active += 1

        dead = len(buckets_to_purge)
        total = len(bucket_pairs)
        survival = total - active - dead

        for full_hash in buckets_to_purge:
            self._real_hashes_to_buckets[full_hash].close()
            del self._real_hashes_to_buckets[full_hash]

        if dead:
            _LOGGER.debug("purged %s stale buckets, %s remain in survival, %s active", dead, survival, active)
        else:
            _LOGGER.log(ux.TRACE, "no buckets purged, %s remain in survival, %s active", survival, active)

    def acquire_bucket(
        self, compiled_route: routes.CompiledRoute, authentication: str | None
    ) -> typing.AsyncContextManager[None]:
        """Acquire a bucket for the given route.

        !!! note
            You MUST keep the context manager acquired during the full duration
            of the request: from making the request until you call
            [`hikari.impl.buckets.RESTBucket.update_rate_limit`][].

        Parameters
        ----------
        compiled_route
            The route to get the bucket for.
        authentication
            The authentication that will be used in the request.

        Returns
        -------
        typing.AsyncContextManager
            The context manager to use during the duration of the request.
        """
        if not self._gc_task:
            msg = "Cannot interact with an inactive bucket manager"
            raise errors.ComponentStateConflictError(msg)

        authentication_hash = _create_authentication_hash(authentication)

        if bucket_hash := self._route_hash_to_bucket_hash.get(hash(compiled_route.route)):
            real_bucket_hash = compiled_route.create_real_bucket_hash(bucket_hash, authentication_hash)
        else:
            real_bucket_hash = _create_unknown_hash(compiled_route, authentication_hash)

        if bucket := self._real_hashes_to_buckets.get(real_bucket_hash):
            _LOGGER.debug("%s is being mapped to existing bucket %s", compiled_route, real_bucket_hash)
        else:
            _LOGGER.debug("%s is being mapped to new bucket %s", compiled_route, real_bucket_hash)
            bucket = RESTBucket(real_bucket_hash, compiled_route, self._global_ratelimit, self._max_rate_limit)
            self._real_hashes_to_buckets[real_bucket_hash] = bucket

        return bucket

    def update_rate_limits(
        self,
        compiled_route: routes.CompiledRoute,
        authentication: str | None,
        bucket_header: str,
        remaining_header: int,
        limit_header: int,
        reset_at: float,
        reset_after: float,
    ) -> None:
        """Update the rate limits for a bucket using info from a response.

        Parameters
        ----------
        compiled_route
            The compiled route to get the bucket for.
        authentication
            The authentication that was used in the request.
        bucket_header
            The `X-RateLimit-Bucket` header that was provided in the response.
        remaining_header
            The `X-RateLimit-Remaining` header cast to an [`int`][].
        limit_header
            The `X-RateLimit-Limit` header cast to an [`int`][].
        reset_at
            The `X-RateLimit-Reset` header cast to a [`float`][].
        reset_after
            The `X-RateLimit-Reset-After` header cast to a [`float`][].
        """
        if not self._gc_task:
            msg = "Cannot interact with an inactive bucket manager"
            raise errors.ComponentStateConflictError(msg)

        self._route_hash_to_bucket_hash[hash(compiled_route.route)] = bucket_header
        authentication_hash = _create_authentication_hash(authentication)
        real_bucket_hash = compiled_route.create_real_bucket_hash(bucket_header, authentication_hash)

        if bucket := self._real_hashes_to_buckets.get(real_bucket_hash):
            _LOGGER.debug(
                "updating %s with bucket %s [reset-after:%ss, limit:%s, remaining:%s]",
                compiled_route,
                real_bucket_hash,
                reset_after,
                limit_header,
                remaining_header,
            )
        else:
            unknown_bucket_hash = _create_unknown_hash(compiled_route, authentication_hash)

            if bucket := self._real_hashes_to_buckets.pop(unknown_bucket_hash, None):
                _LOGGER.debug(
                    "remapping %s with existing bucket %s [reset-after:%ss, limit:%s, remaining:%s]",
                    compiled_route,
                    unknown_bucket_hash,
                    reset_after,
                    limit_header,
                    remaining_header,
                )

            else:
                _LOGGER.debug(
                    "remapping %s with new bucket %s [reset-after:%ss, limit:%s, remaining:%s]",
                    compiled_route,
                    real_bucket_hash,
                    reset_after,
                    limit_header,
                    remaining_header,
                )
                bucket = RESTBucket(UNKNOWN_HASH, compiled_route, self._global_ratelimit, self._max_rate_limit)

            bucket.resolve(real_bucket_hash, remaining_header, limit_header, reset_at, reset_after)

            self._real_hashes_to_buckets[real_bucket_hash] = bucket

        bucket.update_rate_limit(remaining_header, limit_header, reset_at, reset_after)

    def throttle(self, retry_after: float) -> None:
        """Throttle the global ratelimit for the buckets.

        Parameters
        ----------
        retry_after
            How long to throttle for.
        """
        self._global_ratelimit.throttle(retry_after)
