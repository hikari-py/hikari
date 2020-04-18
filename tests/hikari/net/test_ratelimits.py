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
import asyncio
import contextlib
import datetime
import logging
import math
import statistics
import time

import mock
import pytest

from hikari.net import ratelimits
from hikari.net import routes
from tests.hikari import _helpers


class TestBaseRateLimiter:
    def test_context_management(self):
        class MockedBaseRateLimiter(ratelimits.BaseRateLimiter):
            close = mock.MagicMock()
            acquire = NotImplemented

        with MockedBaseRateLimiter() as m:
            pass

        m.close.assert_called_once()


class TestBurstRateLimiter:
    @pytest.fixture
    def mock_burst_limiter(self):
        class Impl(ratelimits.BurstRateLimiter):
            def acquire(self, *args, **kwargs) -> asyncio.Future:
                raise NotImplementedError

        return Impl(__name__)

    @pytest.mark.parametrize(("queue", "is_empty"), [(["foo", "bar", "baz"], False), ([], True)])
    def test_is_empty(self, queue, is_empty, mock_burst_limiter):
        mock_burst_limiter.queue = queue
        assert mock_burst_limiter.is_empty is is_empty

    def test_close_removes_all_futures_from_queue(self, event_loop, mock_burst_limiter):
        mock_burst_limiter.throttle_task = None
        futures = [event_loop.create_future() for _ in range(10)]
        mock_burst_limiter.queue = list(futures)
        mock_burst_limiter.close()
        assert len(mock_burst_limiter.queue) == 0

    def test_close_cancels_all_futures_pending_when_futures_pending(self, event_loop, mock_burst_limiter):
        mock_burst_limiter.throttle_task = None
        futures = [event_loop.create_future() for _ in range(10)]
        mock_burst_limiter.queue = list(futures)
        mock_burst_limiter.close()
        for i, future in enumerate(futures):
            assert future.cancelled(), f"future {i} was not cancelled"

    def test_close_is_silent_when_no_futures_pending(self, mock_burst_limiter):
        mock_burst_limiter.throttle_task = None
        mock_burst_limiter.queue = []
        mock_burst_limiter.close()
        assert True, "passed successfully"

    def test_close_cancels_throttle_task_if_running(self, event_loop, mock_burst_limiter):
        mock_burst_limiter.throttle_task = event_loop.create_future()
        mock_burst_limiter.close()
        assert mock_burst_limiter.throttle_task.cancelled(), "throttle_task is not cancelled"


class TestManualRateLimiter:
    @pytest.mark.asyncio
    async def test_acquire_returns_completed_future_if_lock_task_is_None(self):
        with ratelimits.ManualRateLimiter() as limiter:
            limiter.throttle_task = None
            future = limiter.acquire()
            assert future.done()

    @pytest.mark.asyncio
    async def test_acquire_returns_incomplete_future_if_lock_task_is_not_None(self):
        with ratelimits.ManualRateLimiter() as limiter:
            limiter.throttle_task = asyncio.get_running_loop().create_future()
            future = limiter.acquire()
            assert not future.done()

    @pytest.mark.asyncio
    async def test_acquire_places_future_on_queue_if_lock_task_is_not_None(self):
        with ratelimits.ManualRateLimiter() as limiter:
            limiter.throttle_task = asyncio.get_running_loop().create_future()
            assert len(limiter.queue) == 0
            future = limiter.acquire()
            assert len(limiter.queue) == 1
            assert future in limiter.queue
            assert not future.done()

    @pytest.mark.asyncio
    async def test_lock_cancels_existing_task(self):
        with ratelimits.ManualRateLimiter() as limiter:
            limiter.throttle_task = asyncio.get_running_loop().create_future()
            old_task = limiter.throttle_task
            limiter.throttle(0)
            assert old_task.cancelled()
            assert old_task is not limiter.throttle_task

    @pytest.mark.asyncio
    async def test_lock_schedules_throttle(self):
        with _helpers.unslot_class(ratelimits.ManualRateLimiter)() as limiter:
            limiter.unlock_later = mock.AsyncMock()
            limiter.throttle(0)
            await limiter.throttle_task
            limiter.unlock_later.assert_called_once_with(0)

    @pytest.mark.asyncio
    async def test_throttle_chews_queue_completing_futures(self, event_loop):
        with ratelimits.ManualRateLimiter() as limiter:
            futures = [event_loop.create_future() for _ in range(10)]
            limiter.queue = list(futures)
            await limiter.unlock_later(0.01)
            for i, future in enumerate(futures):
                assert future.done(), f"future {i} was not done"

    @pytest.mark.asyncio
    async def test_throttle_sleeps_before_popping_queue(self, event_loop):
        # GIVEN
        slept_at = float("nan")
        popped_at = []

        async def mock_sleep(_):
            nonlocal slept_at
            slept_at = time.perf_counter()

        class MockList(list):
            def pop(self, _=-1):
                popped_at.append(time.perf_counter())
                return event_loop.create_future()

        with _helpers.unslot_class(ratelimits.ManualRateLimiter)() as limiter:
            with mock.patch("asyncio.sleep", wraps=mock_sleep):
                limiter.queue = MockList()

                # WHEN
                await limiter.unlock_later(5)

        # THEN
        for i, pop_time in enumerate(popped_at):
            assert slept_at < pop_time, f"future {i} popped before initial sleep"

    @pytest.mark.asyncio
    async def test_throttle_clears_throttle_task(self, event_loop):
        with ratelimits.ManualRateLimiter() as limiter:
            limiter.throttle_task = event_loop.create_future()
            await limiter.unlock_later(0)
        assert limiter.throttle_task is None


class TestWindowedBurstRateLimiter:
    @pytest.fixture
    def ratelimiter(self):
        inst = _helpers.unslot_class(ratelimits.WindowedBurstRateLimiter)(__name__, 3, 3)
        yield inst
        with contextlib.suppress(Exception):
            inst.close()

    @pytest.mark.asyncio
    async def test_drip_if_not_throttled_and_not_ratelimited(self, ratelimiter):
        ratelimiter.drip = mock.MagicMock()
        ratelimiter.throttle_task = None
        ratelimiter.is_rate_limited = mock.MagicMock(return_value=False)

        future = ratelimiter.acquire()

        ratelimiter.drip.assert_called_once()
        assert future.done()

    @pytest.mark.asyncio
    async def test_no_drip_if_throttle_task_is_not_None(self, ratelimiter):
        ratelimiter.drip = mock.MagicMock()
        ratelimiter.throttle_task = asyncio.get_running_loop().create_future()
        ratelimiter.is_rate_limited = mock.MagicMock(return_value=False)

        ratelimiter.acquire()

        ratelimiter.drip.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_drip_if_rate_limited(self, ratelimiter):
        ratelimiter.drip = mock.MagicMock()
        ratelimiter.throttle_task = False
        ratelimiter.is_rate_limited = mock.MagicMock(return_value=True)

        ratelimiter.acquire()

        ratelimiter.drip.assert_not_called()

    @pytest.mark.asyncio
    async def test_task_scheduled_if_rate_limited_and_throttle_task_is_None(self, ratelimiter):
        ratelimiter.drip = mock.MagicMock()
        ratelimiter.throttle_task = None
        ratelimiter.throttle = mock.AsyncMock()
        ratelimiter.is_rate_limited = mock.MagicMock(return_value=True)

        ratelimiter.acquire()
        assert ratelimiter.throttle_task is not None

        await asyncio.sleep(0.01)

        ratelimiter.throttle.assert_called()

    @pytest.mark.asyncio
    async def test_task_not_scheduled_if_rate_limited_and_throttle_task_not_None(self, ratelimiter, event_loop):
        ratelimiter.drip = mock.MagicMock()
        ratelimiter.throttle_task = event_loop.create_future()
        old_task = ratelimiter.throttle_task
        ratelimiter.is_rate_limited = mock.MagicMock(return_value=True)

        ratelimiter.acquire()
        assert old_task is ratelimiter.throttle_task, "task was rescheduled, that shouldn't happen :("

    @pytest.mark.asyncio
    async def test_future_is_added_to_queue_if_throttle_task_is_not_None(self, ratelimiter):
        ratelimiter.drip = mock.MagicMock()
        ratelimiter.throttle_task = asyncio.get_running_loop().create_future()
        ratelimiter.is_rate_limited = mock.MagicMock(return_value=False)

        future = ratelimiter.acquire()

        # use slice to prevent aborting test with index error rather than assertion error if this fails.
        assert ratelimiter.queue[-1:] == [future]

    @pytest.mark.asyncio
    async def test_future_is_added_to_queue_if_rate_limited(self, ratelimiter):
        ratelimiter.drip = mock.MagicMock()
        ratelimiter.throttle_task = None
        ratelimiter.is_rate_limited = mock.MagicMock(return_value=True)

        future = ratelimiter.acquire()

        # use slice to prevent aborting test with index error rather than assertion error if this fails.
        assert ratelimiter.queue[-1:] == [future]

    @pytest.mark.asyncio
    async def test_throttle_consumes_queue(self, event_loop):
        with ratelimits.WindowedBurstRateLimiter(__name__, 0.01, 1) as rl:
            rl.queue = [event_loop.create_future() for _ in range(15)]
            old_queue = list(rl.queue)
            await rl.throttle()

        assert len(rl.queue) == 0
        for i, future in enumerate(old_queue):
            assert future.done(), f"future {i} was incomplete!"

    @pytest.mark.asyncio
    @pytest.mark.slow
    @_helpers.retry(5)
    async def test_throttle_sleeps_each_time_limit_is_hit_and_releases_bursts_of_futures_periodically(self, event_loop):
        limit = 5
        period = 3
        total_requests = period * limit * 2
        max_distance_within_window = 0.05
        completion_times = []
        logger = logging.getLogger(__name__)

        def create_task(i):
            logger.info("making task %s", i)
            future = event_loop.create_future()
            future.add_done_callback(lambda _: completion_times.append(time.perf_counter()))
            return future

        with ratelimits.WindowedBurstRateLimiter(__name__, period, limit) as rl:
            futures = [create_task(i) for i in range(total_requests)]
            rl.queue = list(futures)
            rl.reset_at = time.perf_counter()
            logger.info("throttling back")
            await rl.throttle()
            # die if we take too long...
            logger.info("waiting for stuff to finish")
            await asyncio.wait(futures, timeout=period * limit + period)

        assert (
            len(completion_times) == total_requests
        ), f"expected {total_requests} completions but got {len(completion_times)}"

        windows = [completion_times[i : i + limit] for i in range(0, total_requests, limit)]

        for i, window in enumerate(windows):
            logger.info("window %s %s", i, window)
            mode = statistics.mode(window)
            for j, element in enumerate(window):
                assert math.isclose(element, mode, abs_tol=max_distance_within_window), (
                    f"not close! windows[{i}][{j}], future {i * len(window) + j}, "
                    f"val {element}, mode {mode}, max diff {max_distance_within_window}"
                )

        assert len(windows) >= 3, "not enough windows to sample correctly"
        assert len(windows[0]) > 1, "not enough datapoints per window to sample correctly"

        for i in range(1, len(windows)):
            previous_last = windows[i - 1][-1]
            next_first = windows[i][0]
            logger.info("intra-window index=%s value=%s versus index=%s value=%s", i - 1, previous_last, i, next_first)

            assert math.isclose(next_first - previous_last, period, abs_tol=max_distance_within_window), (
                f"distance between windows is not acceptable! {i - 1}={previous_last} {i}={next_first}, "
                f"max diff = {max_distance_within_window}"
            )

    @pytest.mark.asyncio
    async def test_throttle_resets_throttle_task(self, event_loop):
        with ratelimits.WindowedBurstRateLimiter(__name__, 0.01, 1) as rl:
            rl.queue = [event_loop.create_future() for _ in range(15)]
            rl.throttle_task = None
            await rl.throttle()
        assert rl.throttle_task is None

    def test_get_time_until_reset_if_not_rate_limited(self):
        with _helpers.unslot_class(ratelimits.WindowedBurstRateLimiter)(__name__, 0.01, 1) as rl:
            rl.is_rate_limited = mock.MagicMock(return_value=False)
            assert rl.get_time_until_reset(420) == 0.0

    def test_get_time_until_reset_if_rate_limited(self):
        with _helpers.unslot_class(ratelimits.WindowedBurstRateLimiter)(__name__, 0.01, 1) as rl:
            rl.is_rate_limited = mock.MagicMock(return_value=True)
            rl.reset_at = 420.4
            assert rl.get_time_until_reset(69.8) == 420.4 - 69.8

    def test_is_rate_limited_when_rate_limit_expired_resets_self(self):
        with ratelimits.WindowedBurstRateLimiter(__name__, 403, 27) as rl:
            now = 180
            rl.reset_at = 80
            rl.remaining = 4

            assert not rl.is_rate_limited(now)

            assert rl.reset_at == now + 403
            assert rl.remaining == 27

    @pytest.mark.parametrize("remaining", [-1, 0, 1])
    def test_is_rate_limited_when_rate_limit_not_expired_only_returns_expr(self, remaining):
        with ratelimits.WindowedBurstRateLimiter(__name__, 403, 27) as rl:
            now = 420
            rl.reset_at = now + 69
            rl.remaining = remaining
            assert rl.is_rate_limited(now) is (remaining <= 0)


class TestRESTBucket:
    @pytest.fixture
    def compiled_route(self):
        return routes.CompiledRoute("get", "/foo/bar", "/foo/bar", "1a2b3c")

    @pytest.mark.parametrize("name", ["spaghetti", ratelimits.UNKNOWN_HASH])
    def test_is_unknown(self, name, compiled_route):
        with ratelimits.RESTBucket(name, compiled_route) as rl:
            assert rl.is_unknown is (name == ratelimits.UNKNOWN_HASH)

    def test_update_rate_limit(self, compiled_route):
        with ratelimits.RESTBucket(__name__, compiled_route) as rl:
            rl.remaining = 1
            rl.limit = 2
            rl.reset_at = 3
            rl.period = 2

            with mock.patch("time.perf_counter", return_value=4.20):
                rl.update_rate_limit(9, 18, 27)

            assert rl.remaining == 9
            assert rl.limit == 18
            assert rl.reset_at == 27
            assert rl.period == 27 - 4.20

    @pytest.mark.parametrize("name", ["spaghetti", ratelimits.UNKNOWN_HASH])
    def test_drip(self, name, compiled_route):
        with ratelimits.RESTBucket(name, compiled_route) as rl:
            rl.remaining = 1
            rl.drip()
            assert rl.remaining == 0 if name != ratelimits.UNKNOWN_HASH else 1


class TestRESTBucketManager:
    @pytest.mark.asyncio
    async def test_close_closes_all_buckets(self):
        class MockBucket:
            def __init__(self):
                self.close = mock.MagicMock()

        buckets = [MockBucket() for _ in range(30)]

        mgr = ratelimits.RESTBucketManager()
        mgr.real_hashes_to_buckets = {f"blah{i}": bucket for i, bucket in enumerate(buckets)}

        mgr.close()

        for i, bucket in enumerate(buckets):
            bucket.close.assert_called_once(), i

    @pytest.mark.asyncio
    async def test_close_sets_closed_event(self):
        mgr = ratelimits.RESTBucketManager()
        assert not mgr.closed_event.is_set()
        mgr.close()
        assert mgr.closed_event.is_set()

    @pytest.mark.asyncio
    async def test_start(self):
        with ratelimits.RESTBucketManager() as mgr:
            assert mgr.gc_task is None
            mgr.start()
            mgr.start()
            mgr.start()
            assert mgr.gc_task is not None

    @pytest.mark.asyncio
    async def test_exit_closes(self):
        with mock.patch("hikari.net.ratelimits.RESTBucketManager.close") as close:
            with mock.patch("hikari.net.ratelimits.RESTBucketManager.gc") as gc:
                with ratelimits.RESTBucketManager() as mgr:
                    mgr.start(0.01)
                gc.assert_called_once_with(0.01)
            close.assert_called()

    @pytest.mark.asyncio
    async def test_gc_polls_until_closed_event_set(self):
        # This is shit, but it is good shit.
        with ratelimits.RESTBucketManager() as mgr:
            mgr.start(0.01)
            assert mgr.gc_task is not None
            assert not mgr.gc_task.done()
            await asyncio.sleep(0.1)
            assert mgr.gc_task is not None
            assert not mgr.gc_task.done()
            await asyncio.sleep(0.1)
            mgr.closed_event.set()
            assert mgr.gc_task is not None
            assert not mgr.gc_task.done()
            task = mgr.gc_task
            await asyncio.sleep(0.1)
            assert mgr.gc_task is None
            assert task.done()

    @pytest.mark.asyncio
    async def test_gc_calls_do_pass(self):
        with _helpers.unslot_class(ratelimits.RESTBucketManager)() as mgr:
            mgr.do_gc_pass = mock.MagicMock()
            mgr.start(0.01)
            try:
                await asyncio.sleep(0.1)
                mgr.do_gc_pass.assert_called()
            finally:
                mgr.gc_task.cancel()

    @pytest.mark.asyncio
    async def test_do_gc_pass_any_buckets_that_are_empty_and_unknown_get_closed(self):
        with _helpers.unslot_class(ratelimits.RESTBucketManager)() as mgr:
            bucket = mock.MagicMock()
            bucket.is_empty = True
            bucket.is_unknown = True

            mgr.real_hashes_to_buckets["foobar"] = bucket

            mgr.do_gc_pass()

            assert "foobar" not in mgr.real_hashes_to_buckets
            bucket.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_do_gc_pass_any_buckets_that_are_empty_and_known_but_still_rate_limited_are_kept(self):
        with _helpers.unslot_class(ratelimits.RESTBucketManager)() as mgr:
            bucket = mock.MagicMock()
            bucket.is_empty = True
            bucket.is_unknown = False
            bucket.reset_at = time.perf_counter() + 999999999999999999999999999

            mgr.real_hashes_to_buckets["foobar"] = bucket

            mgr.do_gc_pass()

            assert "foobar" in mgr.real_hashes_to_buckets
            bucket.close.assert_not_called()

    @pytest.mark.asyncio
    async def test_do_gc_pass_any_buckets_that_are_empty_and_known_but_not_rate_limited_are_closed(self):
        with _helpers.unslot_class(ratelimits.RESTBucketManager)() as mgr:
            bucket = mock.MagicMock()
            bucket.is_empty = True
            bucket.is_unknown = False
            bucket.reset_at = time.perf_counter() - 999999999999999999999999999

            mgr.real_hashes_to_buckets["foobar"] = bucket

            mgr.do_gc_pass()

            assert "foobar" not in mgr.real_hashes_to_buckets
            bucket.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_do_gc_pass_any_buckets_that_are_not_empty_are_kept(self):
        with _helpers.unslot_class(ratelimits.RESTBucketManager)() as mgr:
            bucket = mock.MagicMock()
            bucket.is_empty = False
            bucket.is_unknown = True

            mgr.real_hashes_to_buckets["foobar"] = bucket

            mgr.do_gc_pass()

            assert "foobar" in mgr.real_hashes_to_buckets
            bucket.close.assert_not_called()

    @pytest.mark.asyncio
    async def test_acquire_route_when_not_in_routes_to_real_hashes_makes_new_bucket_using_initial_hash(self):
        with ratelimits.RESTBucketManager() as mgr:
            route = mock.MagicMock()
            route.create_real_bucket_hash = mock.MagicMock(wraps=lambda intial_hash: intial_hash + ";bobs")

            # This isn't a coroutine; why would I await it?
            # noinspection PyAsyncCall
            mgr.acquire(route)

            assert "UNKNOWN;bobs" in mgr.real_hashes_to_buckets
            assert isinstance(mgr.real_hashes_to_buckets["UNKNOWN;bobs"], ratelimits.RESTBucket)

    @pytest.mark.asyncio
    async def test_acquire_route_when_not_in_routes_to_real_hashes_caches_route(self):
        with ratelimits.RESTBucketManager() as mgr:
            route = mock.MagicMock()
            route.create_real_bucket_hash = mock.MagicMock(wraps=lambda intial_hash: intial_hash + ";bobs")

            # This isn't a coroutine; why would I await it?
            # noinspection PyAsyncCall
            mgr.acquire(route)

            assert mgr.routes_to_hashes[route] == "UNKNOWN"

    @pytest.mark.asyncio
    async def test_acquire_route_when_route_cached_already_obtains_hash_from_route_and_bucket_from_hash(self):
        with ratelimits.RESTBucketManager() as mgr:
            route = mock.MagicMock()
            route.create_real_bucket_hash = mock.MagicMock(return_value="eat pant;1234")
            bucket = mock.MagicMock()
            mgr.routes_to_hashes[route] = "eat pant"
            mgr.real_hashes_to_buckets["eat pant;1234"] = bucket

            # This isn't a coroutine; why would I await it?
            # noinspection PyAsyncCall
            mgr.acquire(route)

            # yes i test this twice, sort of. no, there isn't another way to verify this. sue me.
            bucket.acquire.assert_called_once()

    @pytest.mark.asyncio
    async def test_acquire_route_returns_acquired_future(self):
        with ratelimits.RESTBucketManager() as mgr:
            route = mock.MagicMock()

            bucket = mock.MagicMock()
            with mock.patch("hikari.net.ratelimits.RESTBucket", return_value=bucket):
                route.create_real_bucket_hash = mock.MagicMock(wraps=lambda intial_hash: intial_hash + ";bobs")

                f = mgr.acquire(route)
                assert f is bucket.acquire()

    @pytest.mark.asyncio
    async def test_acquire_route_returns_acquired_future_for_new_bucket(self):
        with ratelimits.RESTBucketManager() as mgr:
            route = mock.MagicMock()
            route.create_real_bucket_hash = mock.MagicMock(return_value="eat pant;bobs")
            bucket = mock.MagicMock()
            mgr.routes_to_hashes[route] = "eat pant"
            mgr.real_hashes_to_buckets["eat pant;bobs"] = bucket

            f = mgr.acquire(route)
            assert f is bucket.acquire()

    @pytest.mark.asyncio
    async def test_update_rate_limits_if_wrong_bucket_hash_reroutes_route(self):
        with ratelimits.RESTBucketManager() as mgr:
            route = mock.MagicMock()
            route.create_real_bucket_hash = mock.MagicMock(wraps=lambda intial_hash: intial_hash + ";bobs")
            mgr.routes_to_hashes[route] = "123"
            mgr.update_rate_limits(route, "blep", 22, 23, datetime.datetime.now(), datetime.datetime.now())
            assert mgr.routes_to_hashes[route] == "blep"
            assert isinstance(mgr.real_hashes_to_buckets["blep;bobs"], ratelimits.RESTBucket)

    @pytest.mark.asyncio
    async def test_update_rate_limits_if_right_bucket_hash_does_nothing_to_hash(self):
        with ratelimits.RESTBucketManager() as mgr:
            route = mock.MagicMock()
            route.create_real_bucket_hash = mock.MagicMock(wraps=lambda intial_hash: intial_hash + ";bobs")
            mgr.routes_to_hashes[route] = "123"
            bucket = mock.MagicMock()
            mgr.real_hashes_to_buckets["123;bobs"] = bucket
            mgr.update_rate_limits(route, "123", 22, 23, datetime.datetime.now(), datetime.datetime.now())
            assert mgr.routes_to_hashes[route] == "123"
            assert mgr.real_hashes_to_buckets["123;bobs"] is bucket

    @pytest.mark.asyncio
    async def test_update_rate_limits_updates_params(self):
        with ratelimits.RESTBucketManager() as mgr:
            route = mock.MagicMock()
            route.create_real_bucket_hash = mock.MagicMock(wraps=lambda intial_hash: intial_hash + ";bobs")
            mgr.routes_to_hashes[route] = "123"
            bucket = mock.MagicMock()
            mgr.real_hashes_to_buckets["123;bobs"] = bucket
            date = datetime.datetime.now().replace(year=2004)
            reset_at = datetime.datetime.now()

            with mock.patch("time.perf_counter", return_value=27):
                expect_reset_at_monotonic = 27 + (reset_at - date).total_seconds()
                mgr.update_rate_limits(route, "123", 22, 23, date, reset_at)
                bucket.update_rate_limit.assert_called_once_with(22, 23, expect_reset_at_monotonic)


class TestExponentialBackOff:
    def test_reset(self):
        eb = ratelimits.ExponentialBackOff()
        eb.increment = 10
        eb.reset()
        assert eb.increment == 0

    @pytest.mark.parametrize(["iteration", "backoff"], enumerate((1, 2, 4, 8, 16, 32)))
    def test_increment_linear(self, iteration, backoff):
        eb = ratelimits.ExponentialBackOff(2, 64, 0)

        for _ in range(iteration):
            next(eb)

        assert next(eb) == backoff

    def test_increment_maximum(self):
        max_bound = 64
        eb = ratelimits.ExponentialBackOff(2, max_bound, 0)
        iterations = math.ceil(math.log2(max_bound))
        for _ in range(iterations):
            next(eb)

        try:
            next(eb)
            assert False, ":("
        except asyncio.TimeoutError:
            assert True

    @pytest.mark.parametrize(["iteration", "backoff"], enumerate((1, 2, 4, 8, 16, 32)))
    def test_increment_jitter(self, iteration, backoff):
        abs_tol = 1
        eb = ratelimits.ExponentialBackOff(2, 64, abs_tol)

        for _ in range(iteration):
            next(eb)

        assert math.isclose(next(eb), backoff, abs_tol=abs_tol)

    def test_iter_returns_self(self):
        eb = ratelimits.ExponentialBackOff(2, 64, 123)
        assert iter(eb) is eb
