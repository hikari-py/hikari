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
from __future__ import annotations

import asyncio
import contextlib
import math

import time

import mock
import pytest

from hikari import errors
from hikari.impl import buckets
from hikari.impl import rate_limits
from hikari.internal import routes
from hikari.internal import time as hikari_date


class TestRESTBucket:
    @pytest.fixture
    def template(self):
        return routes.Route("GET", "/foo/bar")

    @pytest.fixture
    def compiled_route(self, template):
        return routes.CompiledRoute("/foo/bar", template, "1a2b3c")

    @pytest.mark.parametrize(
        ("name", "expected"), [("spaghetti", False), ("UNKNoWN hash", False), ("UNKNOWN", True), ("UNKNOWN hash", True)]
    )
    def test_is_unknown(self, name, compiled_route, expected):
        bucket = buckets.RESTBucket(name, compiled_route, mock.Mock(), float("inf"))

        assert bucket.is_unknown is expected

    @pytest.mark.asyncio
    async def test_usage_when_unknown(self, compiled_route):
        bucket = buckets.RESTBucket(buckets.UNKNOWN_HASH, compiled_route, mock.Mock(), float("inf"))
        bucket._lock = mock.Mock(acquire=mock.AsyncMock(), locked=mock.Mock(return_value=False))

        async with bucket:
            bucket._lock.acquire.assert_awaited_once_with()
            bucket._lock.release.assert_not_called()

            bucket._lock.locked.return_value = True

        bucket._lock.acquire.assert_awaited_once_with()
        bucket._lock.release.assert_called_once_with()

    @pytest.mark.asyncio
    async def test_usage_when_resolved(self, compiled_route):
        global_ratelimit = mock.Mock(acquire=mock.AsyncMock(), reset_at=None)
        bucket = buckets.RESTBucket("resolved bucket", compiled_route, global_ratelimit, float("inf"))
        bucket.remaining = 10
        bucket._lock = mock.Mock(acquire=mock.AsyncMock(), locked=mock.Mock(return_value=False))

        async with bucket:
            bucket._lock.acquire.assert_not_called()
            bucket._lock.release.assert_not_called()

        bucket._lock.acquire.assert_not_called()
        bucket._lock.release.assert_not_called()

    def test_update_rate_limit_when_no_issues(self, compiled_route):
        bucket = buckets.RESTBucket("updating ratelimit test", compiled_route, mock.Mock(), float("inf"))
        now = time.time()

        bucket.remaining = 1
        bucket.limit = 2
        bucket.increase_at = now
        bucket.period = 2

        bucket.update_rate_limit(0, 2, now, 4)

        assert bucket.remaining == 1
        assert bucket.limit == 2
        assert bucket.increase_at == now
        assert bucket.period == 2

    @pytest.mark.parametrize("limit", (10, 5))
    def test_update_rate_limit_when_limit_changed(self, compiled_route, limit):
        bucket = buckets.RESTBucket("updating ratelimit test", compiled_route, mock.Mock(), float("inf"))
        now = time.time()

        bucket.remaining = 1
        bucket.limit = 2
        bucket.increase_at = now
        bucket.period = 2

        bucket.update_rate_limit(0, limit, now + 20, 4)

        assert bucket.limit == limit

    def test_update_rate_limit_when_period_far_apart(self, compiled_route):
        bucket = buckets.RESTBucket("updating ratelimit test", compiled_route, mock.Mock(), float("inf"))
        now = 12123123

        bucket.remaining = 1
        bucket.limit = 3
        bucket.increase_at = now
        bucket.period = 2
        bucket._out_of_sync = True

        bucket.update_rate_limit(1, 3, 123123124, 4.5)

        assert bucket.remaining == 1
        assert bucket.limit == 3
        assert bucket.increase_at == 123123121.75
        assert bucket.period == 2.25
        assert bucket._out_of_sync is False

    @pytest.mark.asyncio
    async def test_acquire_when_too_long_ratelimit(self, compiled_route):
        bucket = buckets.RESTBucket("spaghetti", compiled_route, mock.Mock(), 60)
        bucket.increase_at = time.time() + 999999999999999999999999999
        bucket._lock = mock.Mock(acquire=mock.AsyncMock())

        with (
            mock.patch.object(buckets.RESTBucket, "is_rate_limited", return_value=True),
            pytest.raises(errors.RateLimitTooLongError),
        ):
            await bucket.acquire()

        bucket._lock.acquire.assert_not_called()
        bucket._lock.release.assert_not_called()

    @pytest.mark.asyncio
    async def test_acquire_when_too_long_global_ratelimit(self, compiled_route):
        global_ratelimit = mock.Mock(reset_at=time.time() + 999999999999999999999999999)

        bucket = buckets.RESTBucket("spaghetti", compiled_route, global_ratelimit, 1)
        bucket._lock = mock.Mock(acquire=mock.AsyncMock())

        with (
            mock.patch.object(rate_limits.WindowedBurstRateLimiter, "acquire") as super_acquire,
            pytest.raises(errors.RateLimitTooLongError),
        ):
            await bucket.acquire()

        bucket._lock.acquire.assert_not_called()
        bucket._lock.release.assert_not_called()
        super_acquire.assert_called_once_with()
        global_ratelimit.acquire.assert_not_called()

    @pytest.mark.asyncio
    async def test_acquire_when_unknown_bucket(self, compiled_route):
        global_ratelimit = mock.Mock(acquire=mock.AsyncMock(), reset_at=None)

        bucket = buckets.RESTBucket("UNKNOWN", compiled_route, global_ratelimit, float("inf"))
        bucket._lock = mock.Mock(acquire=mock.AsyncMock())

        with mock.patch.object(rate_limits.WindowedBurstRateLimiter, "acquire") as super_acquire:
            await bucket.acquire()

        bucket._lock.acquire.assert_awaited_once_with()
        super_acquire.assert_not_called()
        global_ratelimit.acquire.assert_not_called()

    @pytest.mark.asyncio
    async def test_acquire_when_resolved_while_waiting(self, compiled_route):
        async def resolve_bucket():
            nonlocal lock_acquire_called

            bucket.resolve("some real hash", 1, 2, 3, 4)
            lock_acquire_called += 1

        global_ratelimit = mock.Mock(acquire=mock.AsyncMock(), reset_at=None)
        bucket = buckets.RESTBucket(buckets.UNKNOWN_HASH, compiled_route, global_ratelimit, float("inf"))
        bucket._lock = mock.Mock(acquire=resolve_bucket)
        lock_acquire_called = 0

        with mock.patch.object(rate_limits.WindowedBurstRateLimiter, "acquire") as super_acquire:
            await bucket.acquire()

        super_acquire.assert_awaited_once_with()
        assert lock_acquire_called == 1
        global_ratelimit.acquire.assert_awaited_once_with()

    @pytest.mark.asyncio
    async def test_acquire_when_resolved_bucket(self, compiled_route):
        global_ratelimit = mock.Mock(acquire=mock.AsyncMock(), reset_at=None)
        bucket = buckets.RESTBucket("spaghetti", compiled_route, global_ratelimit, float("inf"))
        bucket._lock = mock.Mock()

        with mock.patch.object(rate_limits.WindowedBurstRateLimiter, "acquire") as super_acquire:
            await bucket.acquire()

        super_acquire.assert_awaited_once_with()
        bucket._lock.acquire.assert_not_called()
        global_ratelimit.acquire.assert_awaited_once_with()

    def test_resolve_when_not_unknown(self, compiled_route):
        bucket = buckets.RESTBucket("spaghetti", compiled_route, mock.Mock(), float("inf"))

        with pytest.raises(RuntimeError, match=r"Cannot resolve known bucket"):
            bucket.resolve("test", 1, 2, 3, 4)

        assert bucket.name == "spaghetti"

    def test_resolve(self, compiled_route):
        bucket = buckets.RESTBucket(buckets.UNKNOWN_HASH, compiled_route, mock.Mock(), float("inf"))

        bucket.resolve("test", 1, 3, 123123124, 4)

        assert bucket.name == "test"
        assert bucket.remaining == 1
        assert bucket.limit == 3
        assert bucket.period == 2
        assert bucket.increase_at == 123123122


class TestRESTBucketManager:
    @pytest.fixture
    def bucket_manager(self):
        manager = buckets.RESTBucketManager(max_rate_limit=float("inf"))
        manager._gc_task = object()

        return manager

    def test_max_rate_limit_property(self, bucket_manager):
        bucket_manager._max_rate_limit = object()

        assert bucket_manager.max_rate_limit is bucket_manager._max_rate_limit

    @pytest.mark.asyncio
    async def test_close(self, bucket_manager):
        class GcTaskMock:
            def __init__(self):
                self._awaited_count = 0
                self.cancel = mock.Mock()

            def __await__(self):
                if False:
                    yield  # Turns it into a generator

                self._awaited_count += 1

            def __call__(self):
                return self

            def assert_awaited_once(self):
                assert self._awaited_count == 1

        buckets_array = [mock.Mock() for _ in range(30)]
        bucket_manager._real_hashes_to_buckets = {f"blah{i}": b for i, b in enumerate(buckets_array)}
        bucket_manager._gc_task = gc_task = GcTaskMock()

        await bucket_manager.close()

        assert bucket_manager._real_hashes_to_buckets == {}

        for i, b in enumerate(buckets_array):
            b.close.assert_called_once(), i

        assert bucket_manager._gc_task is None
        gc_task.cancel.assert_called_once_with()
        gc_task.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_start(self, bucket_manager):
        bucket_manager._gc_task = None

        bucket_manager.start()
        assert bucket_manager._gc_task is not None

        # cancel created task
        bucket_manager._gc_task.cancel()
        try:
            await bucket_manager._gc_task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_start_when_already_started(self, bucket_manager):
        bucket_manager._gc_task = object()

        with pytest.raises(errors.ComponentStateConflictError):
            bucket_manager.start()

    @pytest.mark.asyncio
    async def test_gc_makes_gc_pass(self, bucket_manager):
        class ExitError(Exception): ...

        with mock.patch.object(buckets.RESTBucketManager, "_purge_stale_buckets") as purge_stale_buckets:
            with mock.patch.object(asyncio, "sleep", side_effect=[None, ExitError]):
                with pytest.raises(ExitError):
                    await bucket_manager._gc(0.001, 33)

        purge_stale_buckets.assert_called_with(33)

    @pytest.mark.asyncio
    async def test_purge_stale_buckets_any_buckets_that_are_empty_but_still_rate_limited_are_kept_alive(
        self, bucket_manager
    ):
        bucket = mock.Mock()
        bucket.is_empty = True
        bucket.is_unknown = False
        bucket.increase_at = time.time() + 999999999999999999999999999

        bucket_manager._real_hashes_to_buckets["foobar"] = bucket

        bucket_manager._purge_stale_buckets(0)

        assert "foobar" in bucket_manager._real_hashes_to_buckets
        bucket.close.assert_not_called()

    @pytest.mark.asyncio
    async def test_purge_stale_buckets_any_buckets_that_are_empty_but_not_rate_limited_and_not_expired_are_kept_alive(
        self, bucket_manager
    ):
        bucket = mock.Mock()
        bucket.is_empty = True
        bucket.is_unknown = False
        bucket.increase_at = time.time()

        bucket_manager._real_hashes_to_buckets["foobar"] = bucket

        bucket_manager._purge_stale_buckets(10)

        assert "foobar" in bucket_manager._real_hashes_to_buckets
        bucket.close.assert_not_called()

    @pytest.mark.asyncio
    async def test_purge_stale_buckets_any_buckets_that_are_empty_but_not_rate_limited_and_expired_are_closed(
        self, bucket_manager
    ):
        bucket = mock.Mock()
        bucket.is_empty = True
        bucket.is_unknown = False
        bucket.increase_at = time.time() - 999999999999999999999999999

        bucket_manager._real_hashes_to_buckets["foobar"] = bucket

        bucket_manager._purge_stale_buckets(0)

        assert "foobar" not in bucket_manager._real_hashes_to_buckets
        bucket.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_purge_stale_buckets_any_buckets_that_are_not_empty_are_kept_alive(self, bucket_manager):
        bucket = mock.Mock()
        bucket.is_empty = False
        bucket.is_unknown = True
        bucket.increase_at = time.time()

        bucket_manager._real_hashes_to_buckets["foobar"] = bucket

        bucket_manager._purge_stale_buckets(0)

        assert "foobar" in bucket_manager._real_hashes_to_buckets
        bucket.close.assert_not_called()

    @pytest.mark.asyncio
    async def test_acquire_route_when_not_in_routes_to_real_hashes_makes_new_bucket_using_initial_hash(
        self, bucket_manager
    ):
        route = mock.Mock()

        with mock.patch.object(buckets, "_create_authentication_hash", return_value="auth_hash"):
            with mock.patch.object(
                buckets, "_create_unknown_hash", return_value="UNKNOWN;auth_hash;bobs"
            ) as create_unknown_hash:
                bucket_manager.acquire_bucket(route, "auth")

        assert "UNKNOWN;auth_hash;bobs" in bucket_manager._real_hashes_to_buckets
        assert isinstance(bucket_manager._real_hashes_to_buckets["UNKNOWN;auth_hash;bobs"], buckets.RESTBucket)
        create_unknown_hash.assert_called_once_with(route, "auth_hash")

    @pytest.mark.asyncio
    async def test_acquire_route_when_not_in_routes_to_real_hashes_doesnt_cache_route(self, bucket_manager):
        route = mock.Mock()
        route.create_real_bucket_hash = mock.Mock(wraps=lambda initial_hash, auth: initial_hash + ";" + auth + ";bobs")

        bucket_manager.acquire_bucket(route, "auth")

        assert bucket_manager._route_hash_to_bucket_hash.get(hash(route.route)) is None

    @pytest.mark.asyncio
    async def test_acquire_route_when_route_cached_already_obtains_hash_from_route_and_bucket_from_hash(
        self, bucket_manager
    ):
        mock_route_hash = 123123123
        route = mock.Mock()
        route.route = mock.Mock(__hash__=lambda _: mock_route_hash)
        route.create_real_bucket_hash = mock.Mock(return_value="eat pant;1234")
        bucket = mock.Mock(reset_at=time.time() + 999999999999999999999999999)
        bucket_manager._route_hash_to_bucket_hash[mock_route_hash] = "eat pant"
        bucket_manager._real_hashes_to_buckets["eat pant;1234"] = bucket

        assert bucket_manager.acquire_bucket(route, "auth") is bucket

    @pytest.mark.asyncio
    async def test_acquire_route_returns_context_manager(self, bucket_manager):
        route = mock.Mock()

        bucket = mock.Mock(reset_at=time.time() + 999999999999999999999999999)
        with mock.patch.object(buckets, "RESTBucket", return_value=bucket):
            route.create_real_bucket_hash = mock.Mock(
                wraps=lambda initial_hash, auth: initial_hash + ";" + auth + ";bobs"
            )

            assert bucket_manager.acquire_bucket(route, "auth") is bucket

    @pytest.mark.asyncio
    async def test_acquire_unknown_route_returns_context_manager_for_new_bucket(self, bucket_manager):
        mock_route_hash = 123123123
        route = mock.Mock()
        route.route = mock.Mock(__hash__=lambda _: mock_route_hash)
        route.create_real_bucket_hash = mock.Mock(return_value="eat pant;bobs")
        bucket = mock.Mock(reset_at=time.time() + 999999999999999999999999999)
        bucket_manager._route_hash_to_bucket_hash[mock_route_hash] = "eat pant"
        bucket_manager._real_hashes_to_buckets["eat pant;bobs"] = bucket

        assert bucket_manager.acquire_bucket(route, "auth") is bucket

    @pytest.mark.asyncio
    async def test_update_rate_limits_if_wrong_bucket_hash_reroutes_route(self, bucket_manager):
        mock_route_hash = 123123123
        route = mock.Mock()
        route.route = mock.Mock(__hash__=lambda _: mock_route_hash)
        route.create_real_bucket_hash = mock.Mock(wraps=lambda initial_hash, auth: initial_hash + ";" + auth + ";bobs")
        bucket_manager._route_hash_to_bucket_hash[mock_route_hash] = "123"

        with (
            mock.patch.object(buckets, "_create_authentication_hash", return_value="auth_hash"),
            mock.patch.object(buckets, "RESTBucket") as bucket,
        ):
            bucket_manager.update_rate_limits(route, "auth", "blep", 22, 23, 123123.56, 3.56)

        assert bucket_manager._route_hash_to_bucket_hash[mock_route_hash] == "blep"
        assert bucket_manager._real_hashes_to_buckets["blep;auth_hash;bobs"] is bucket.return_value
        bucket.return_value.update_rate_limit.assert_called_once_with(22, 23, 123123.56, 3.56)

    @pytest.mark.asyncio
    async def test_update_rate_limits_if_unknown_bucket_hash_reroutes_route(self, bucket_manager):
        mock_route_hash = 123123123
        route = mock.Mock()
        route.route = mock.Mock(__hash__=lambda _: mock_route_hash)
        route.create_real_bucket_hash = mock.Mock(wraps=lambda initial_hash, auth: initial_hash + ";" + auth + ";bobs")
        bucket_manager._route_hash_to_bucket_hash[mock_route_hash] = "123"
        bucket = mock.Mock()
        bucket_manager._real_hashes_to_buckets["UNKNOWN;auth_hash;bobs"] = bucket

        with (
            mock.patch.object(
                buckets, "_create_authentication_hash", return_value="auth_hash"
            ) as create_authentication_hash,
            mock.patch.object(
                buckets, "_create_unknown_hash", return_value="UNKNOWN;auth_hash;bobs"
            ) as create_unknown_hash,
        ):
            bucket_manager.update_rate_limits(route, "auth", "blep", 22, 23, 123123.53, 3.56)

        assert bucket_manager._route_hash_to_bucket_hash[mock_route_hash] == "blep"
        assert bucket_manager._real_hashes_to_buckets["blep;auth_hash;bobs"] is bucket
        bucket.resolve.assert_called_once_with("blep;auth_hash;bobs", 22, 23, 123123.53, 3.56)
        bucket.update_rate_limit.assert_called_once_with(22, 23, 123123.53, 3.56)
        create_unknown_hash.assert_called_once_with(route, "auth_hash")
        create_authentication_hash.assert_called_once_with("auth")

    @pytest.mark.asyncio
    async def test_update_rate_limits_if_right_bucket_hash_does_nothing_to_hash(self, bucket_manager):
        route = mock.Mock()
        route.create_real_bucket_hash = mock.Mock(wraps=lambda initial_hash, auth: initial_hash + ";" + auth + ";bobs")
        bucket_manager._route_hash_to_bucket_hash[route.route] = "123"
        bucket = mock.Mock(reset_at=time.time() + 999999999999999999999999999)
        bucket_manager._real_hashes_to_buckets["123;auth_hash;bobs"] = bucket

        with mock.patch.object(buckets, "_create_authentication_hash", return_value="auth_hash"):
            bucket_manager.update_rate_limits(route, "auth", "123", 22, 23, 123123.53, 7.65)

        assert bucket_manager._route_hash_to_bucket_hash[route.route] == "123"
        assert bucket_manager._real_hashes_to_buckets["123;auth_hash;bobs"] is bucket
        bucket.update_rate_limit.assert_called_once_with(22, 23, 123123.53, 7.65)

    @pytest.mark.asyncio
    async def test_update_rate_limits_updates_params(self, bucket_manager):
        route = mock.Mock()
        route.create_real_bucket_hash = mock.Mock(wraps=lambda initial_hash, auth: initial_hash + ";" + auth + ";bobs")
        bucket_manager._route_hash_to_bucket_hash[route.route] = "123"
        bucket = mock.Mock(reset_at=time.time() + 999999999999999999999999999)
        bucket_manager._real_hashes_to_buckets["123;auth_hash;bobs"] = bucket

        with mock.patch.object(buckets, "_create_authentication_hash", return_value="auth_hash"):
            bucket_manager.update_rate_limits(route, "auth", "123", 22, 23, 123123123.53, 5.32)

        bucket.update_rate_limit.assert_called_once_with(22, 23, 123123123.53, 5.32)

    @pytest.mark.parametrize(("gc_task", "is_alive"), [(None, False), ("some", True)])
    def test_is_alive(self, bucket_manager, gc_task, is_alive):
        bucket_manager._gc_task = gc_task
        assert bucket_manager.is_alive is is_alive
