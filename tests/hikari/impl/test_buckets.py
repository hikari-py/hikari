# -*- coding: utf-8 -*-
# Copyright (c) 2020 Nekokatt
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
import asyncio
import datetime
import time

import mock
import pytest

from hikari import errors
from hikari.impl import buckets
from hikari.internal import routes
from hikari.internal import time as hikari_date
from tests.hikari import hikari_test_helpers


class TestRESTBucket:
    @pytest.fixture()
    def template(self):
        return routes.Route("GET", "/foo/bar")

    @pytest.fixture()
    def compiled_route(self, template):
        return routes.CompiledRoute("/foo/bar", template, "1a2b3c")

    @pytest.mark.parametrize("name", ["spaghetti", buckets.UNKNOWN_HASH])
    def test_is_unknown(self, name, compiled_route):
        with buckets.RESTBucket(name, compiled_route) as rl:
            assert rl.is_unknown is (name == buckets.UNKNOWN_HASH)

    def test_update_rate_limit(self, compiled_route):
        with buckets.RESTBucket(__name__, compiled_route) as rl:
            rl.remaining = 1
            rl.limit = 2
            rl.reset_at = 3
            rl.period = 2

            with mock.patch.object(hikari_date, "monotonic", return_value=4.20):
                rl.update_rate_limit(9, 18, 27)

            assert rl.remaining == 9
            assert rl.limit == 18
            assert rl.reset_at == 27
            assert rl.period == 27 - 4.20

    @pytest.mark.parametrize("name", ["spaghetti", buckets.UNKNOWN_HASH])
    def test_drip(self, name, compiled_route):
        with buckets.RESTBucket(name, compiled_route) as rl:
            rl.remaining = 1
            rl.drip()
            assert rl.remaining == 0 if name != buckets.UNKNOWN_HASH else 1


class TestRESTBucketManager:
    @pytest.mark.asyncio
    async def test_close_closes_all_buckets(self):
        class MockBucket:
            def __init__(self):
                self.close = mock.Mock()

        buckets_array = [MockBucket() for _ in range(30)]

        mgr = buckets.RESTBucketManager(max_rate_limit=float("inf"))
        mgr.real_hashes_to_buckets = {f"blah{i}": bucket for i, bucket in enumerate(buckets_array)}

        mgr.close()

        for i, bucket in enumerate(buckets_array):
            bucket.close.assert_called_once(), i

    @pytest.mark.asyncio
    async def test_close_sets_closed_event(self):
        mgr = buckets.RESTBucketManager(max_rate_limit=float("inf"))
        assert not mgr.closed_event.is_set()
        mgr.close()
        assert mgr.closed_event.is_set()

    @pytest.mark.asyncio
    async def test_start(self):
        with buckets.RESTBucketManager(max_rate_limit=float("inf")) as mgr:
            assert mgr.gc_task is None
            mgr.start()
            mgr.start()
            mgr.start()
            assert mgr.gc_task is not None

    @pytest.mark.asyncio
    async def test_exit_closes(self):
        with mock.patch.object(buckets.RESTBucketManager, "close") as close:
            with mock.patch.object(buckets.RESTBucketManager, "gc") as gc:
                with buckets.RESTBucketManager(max_rate_limit=float("inf")) as mgr:
                    mgr.start(0.01, 32)
                gc.assert_called_once_with(0.01, 32)
            close.assert_called()

    @pytest.mark.asyncio
    async def test_gc_polls_until_closed_event_set(self):
        # This is shit, but it is good shit.
        with buckets.RESTBucketManager(max_rate_limit=float("inf")) as mgr:
            mgr.start(0.01)
            assert mgr.gc_task is not None
            assert not mgr.gc_task.done()
            await hikari_test_helpers.idle()
            assert mgr.gc_task is not None
            assert not mgr.gc_task.done()
            await hikari_test_helpers.idle()
            mgr.closed_event.set()
            assert mgr.gc_task is not None
            assert not mgr.gc_task.done()
            task = mgr.gc_task
            await hikari_test_helpers.idle()
            assert mgr.gc_task is None
            assert task.done()

    @pytest.mark.asyncio
    async def test_gc_calls_do_pass(self):
        with hikari_test_helpers.mock_class_namespace(buckets.RESTBucketManager, slots_=False)(
            max_rate_limit=float("inf")
        ) as mgr:
            mgr.do_gc_pass = mock.Mock()
            mgr.start(0.01, 33)
            try:
                await hikari_test_helpers.idle()
                mgr.do_gc_pass.assert_called_with(33)
            finally:
                mgr.gc_task.cancel()

    @pytest.mark.asyncio
    async def test_do_gc_pass_any_buckets_that_are_empty_but_still_rate_limited_are_kept_alive(self):
        with hikari_test_helpers.mock_class_namespace(buckets.RESTBucketManager)(max_rate_limit=float("inf")) as mgr:
            bucket = mock.Mock()
            bucket.is_empty = True
            bucket.is_unknown = False
            bucket.reset_at = time.perf_counter() + 999999999999999999999999999

            mgr.real_hashes_to_buckets["foobar"] = bucket

            mgr.do_gc_pass(0)

            assert "foobar" in mgr.real_hashes_to_buckets
            bucket.close.assert_not_called()

    @pytest.mark.asyncio
    async def test_do_gc_pass_any_buckets_that_are_empty_but_not_rate_limited_and_not_expired_are_kept_alive(self):
        with hikari_test_helpers.mock_class_namespace(buckets.RESTBucketManager)(max_rate_limit=float("inf")) as mgr:
            bucket = mock.Mock()
            bucket.is_empty = True
            bucket.is_unknown = False
            bucket.reset_at = time.perf_counter()

            mgr.real_hashes_to_buckets["foobar"] = bucket

            mgr.do_gc_pass(10)

            assert "foobar" in mgr.real_hashes_to_buckets
            bucket.close.assert_not_called()

    @pytest.mark.asyncio
    async def test_do_gc_pass_any_buckets_that_are_empty_but_not_rate_limited_and_expired_are_closed(self):
        with hikari_test_helpers.mock_class_namespace(buckets.RESTBucketManager)(max_rate_limit=float("inf")) as mgr:
            bucket = mock.Mock()
            bucket.is_empty = True
            bucket.is_unknown = False
            bucket.reset_at = time.perf_counter() - 999999999999999999999999999

            mgr.real_hashes_to_buckets["foobar"] = bucket

            mgr.do_gc_pass(0)

            assert "foobar" not in mgr.real_hashes_to_buckets
            bucket.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_do_gc_pass_any_buckets_that_are_not_empty_are_kept_alive(self):
        with hikari_test_helpers.mock_class_namespace(buckets.RESTBucketManager)(max_rate_limit=float("inf")) as mgr:
            bucket = mock.Mock()
            bucket.is_empty = False
            bucket.is_unknown = True
            bucket.reset_at = time.perf_counter()

            mgr.real_hashes_to_buckets["foobar"] = bucket

            mgr.do_gc_pass(0)

            assert "foobar" in mgr.real_hashes_to_buckets
            bucket.close.assert_not_called()

    @pytest.mark.asyncio
    async def test_acquire_route_when_not_in_routes_to_real_hashes_makes_new_bucket_using_initial_hash(self):
        with buckets.RESTBucketManager(max_rate_limit=float("inf")) as mgr:
            route = mock.Mock()
            route.create_real_bucket_hash = mock.Mock(wraps=lambda intial_hash: intial_hash + ";bobs")

            # This isn't a coroutine; why would I await it?
            mgr.acquire(route)

            assert "UNKNOWN;bobs" in mgr.real_hashes_to_buckets
            assert isinstance(mgr.real_hashes_to_buckets["UNKNOWN;bobs"], buckets.RESTBucket)

    @pytest.mark.asyncio
    async def test_acquire_route_when_not_in_routes_to_real_hashes_caches_route(self):
        with buckets.RESTBucketManager(max_rate_limit=float("inf")) as mgr:
            route = mock.Mock()
            route.create_real_bucket_hash = mock.Mock(wraps=lambda intial_hash: intial_hash + ";bobs")

            # This isn't a coroutine; why would I await it?
            mgr.acquire(route)

            assert mgr.routes_to_hashes[route.route] == "UNKNOWN"

    @pytest.mark.asyncio
    async def test_acquire_route_when_route_cached_already_obtains_hash_from_route_and_bucket_from_hash(self):
        with buckets.RESTBucketManager(max_rate_limit=float("inf")) as mgr:
            route = mock.Mock()
            route.create_real_bucket_hash = mock.Mock(return_value="eat pant;1234")
            bucket = mock.Mock(reset_at=time.perf_counter() + 999999999999999999999999999)
            mgr.routes_to_hashes[route] = "eat pant"
            mgr.real_hashes_to_buckets["eat pant;1234"] = bucket

            # This isn't a coroutine; why would I await it?
            mgr.acquire(route)

            # yes i test this twice, sort of. no, there isn't another way to verify this. sue me.
            bucket.acquire.assert_called_once_with(float("inf"))

    @pytest.mark.asyncio
    async def test_acquire_route_returns_acquired_future(self):
        with buckets.RESTBucketManager(max_rate_limit=float("inf")) as mgr:
            route = mock.Mock()

            bucket = mock.Mock(reset_at=time.perf_counter() + 999999999999999999999999999)
            with mock.patch.object(buckets, "RESTBucket", return_value=bucket):
                route.create_real_bucket_hash = mock.Mock(wraps=lambda intial_hash: intial_hash + ";bobs")

                f = mgr.acquire(route)
                assert f is bucket.acquire()

    @pytest.mark.asyncio
    async def test_acquire_route_returns_acquired_future_for_new_bucket(self):
        with buckets.RESTBucketManager(max_rate_limit=float("inf")) as mgr:
            route = mock.Mock()
            route.create_real_bucket_hash = mock.Mock(return_value="eat pant;bobs")
            bucket = mock.Mock(reset_at=time.perf_counter() + 999999999999999999999999999)
            mgr.routes_to_hashes[route.route] = "eat pant"
            mgr.real_hashes_to_buckets["eat pant;bobs"] = bucket

            f = mgr.acquire(route)
            assert f is bucket.acquire()

    @pytest.mark.asyncio
    async def test_acquire_route_when_too_long_ratelimit(self):
        with buckets.RESTBucketManager(max_rate_limit=60) as mgr:
            route = mock.Mock()
            route.create_real_bucket_hash = mock.Mock(return_value="eat pant;bobs")
            bucket = mock.Mock(
                reset_at=time.perf_counter() + 999999999999999999999999999, is_ratelimited=mock.Mock(return_value=True)
            )
            mgr.routes_to_hashes[route.route] = "eat pant"
            mgr.real_hashes_to_buckets["eat pant;bobs"] = bucket

            with pytest.raises(errors.RateLimitTooLongError):
                mgr.acquire(route)

    @pytest.mark.asyncio
    async def test_update_rate_limits_if_wrong_bucket_hash_reroutes_route(self):
        with buckets.RESTBucketManager(max_rate_limit=float("inf")) as mgr:
            route = mock.Mock()
            route.create_real_bucket_hash = mock.Mock(wraps=lambda intial_hash: intial_hash + ";bobs")
            mgr.routes_to_hashes[route.route] = "123"
            mgr.update_rate_limits(route, "blep", 22, 23, datetime.datetime.now(), datetime.datetime.now())
            assert mgr.routes_to_hashes[route.route] == "blep"
            assert isinstance(mgr.real_hashes_to_buckets["blep;bobs"], buckets.RESTBucket)

    @pytest.mark.asyncio
    async def test_update_rate_limits_if_right_bucket_hash_does_nothing_to_hash(self):
        with buckets.RESTBucketManager(max_rate_limit=float("inf")) as mgr:
            route = mock.Mock()
            route.create_real_bucket_hash = mock.Mock(wraps=lambda intial_hash: intial_hash + ";bobs")
            mgr.routes_to_hashes[route.route] = "123"
            bucket = mock.Mock(reset_at=time.perf_counter() + 999999999999999999999999999)
            mgr.real_hashes_to_buckets["123;bobs"] = bucket
            mgr.update_rate_limits(route, "123", 22, 23, datetime.datetime.now(), datetime.datetime.now())
            assert mgr.routes_to_hashes[route.route] == "123"
            assert mgr.real_hashes_to_buckets["123;bobs"] is bucket

    @pytest.mark.asyncio
    async def test_update_rate_limits_updates_params(self):
        with buckets.RESTBucketManager(max_rate_limit=float("inf")) as mgr:
            route = mock.Mock()
            route.create_real_bucket_hash = mock.Mock(wraps=lambda intial_hash: intial_hash + ";bobs")
            mgr.routes_to_hashes[route.route] = "123"
            bucket = mock.Mock(reset_at=time.perf_counter() + 999999999999999999999999999)
            mgr.real_hashes_to_buckets["123;bobs"] = bucket
            date = datetime.datetime.now().replace(year=2004)
            reset_at = datetime.datetime.now()

            with mock.patch.object(hikari_date, "monotonic", return_value=27):
                expect_reset_at_monotonic = 27 + (reset_at - date).total_seconds()
                mgr.update_rate_limits(route, "123", 22, 23, date, reset_at)
                bucket.update_rate_limit.assert_called_once_with(22, 23, expect_reset_at_monotonic)

    @pytest.mark.parametrize(("gc_task", "is_started"), [(None, False), (mock.Mock(spec_set=asyncio.Task), True)])
    def test_is_started(self, gc_task, is_started):
        with buckets.RESTBucketManager(max_rate_limit=float("inf")) as mgr:
            mgr.gc_task = gc_task
            assert mgr.is_started is is_started
