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
import time

import asyncmock as mock
import pytest

from hikari.net import ratelimits
from tests.hikari import _helpers


class TestBaseRateLimiter:
    def test_context_management(self):
        class MockedBaseRateLimiter(ratelimits.IRateLimiter):
            close = mock.MagicMock()
            acquire = NotImplemented

        with MockedBaseRateLimiter() as m:
            pass

        m.close.assert_called_once()


class TestBurstRateLimiter:
    @pytest.fixture()
    def mock_burst_limiter(self):
        class Impl(ratelimits.BurstRateLimiter):
            def acquire(self, *args, **kwargs) -> asyncio.Future:
                raise NotImplementedError
        return Impl(__name__)

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


class TestGlobalHTTPRateLimiter:
    @pytest.mark.asyncio
    async def test_acquire_returns_completed_future_if_lock_task_is_None(self):
        with ratelimits.GlobalHTTPRateLimiter() as limiter:
            limiter.throttle_task = None
            future = limiter.acquire()
            assert future.done()

    @pytest.mark.asyncio
    async def test_acquire_returns_incomplete_future_if_lock_task_is_not_None(self):
        with ratelimits.GlobalHTTPRateLimiter() as limiter:
            limiter.throttle_task = asyncio.get_running_loop().create_future()
            future = limiter.acquire()
            assert not future.done()

    @pytest.mark.asyncio
    async def test_acquire_places_future_on_queue_if_lock_task_is_not_None(self):
        with ratelimits.GlobalHTTPRateLimiter() as limiter:
            limiter.throttle_task = asyncio.get_running_loop().create_future()
            assert len(limiter.queue) == 0
            future = limiter.acquire()
            assert len(limiter.queue) == 1
            assert future in limiter.queue
            assert not future.done()

    @pytest.mark.asyncio
    async def test_lock_cancels_existing_task(self):
        with ratelimits.GlobalHTTPRateLimiter() as limiter:
            limiter.throttle_task = asyncio.get_running_loop().create_future()
            old_task = limiter.throttle_task
            limiter.lock(0)
            assert old_task.cancelled()
            assert old_task is not limiter.throttle_task

    @pytest.mark.asyncio
    async def test_lock_schedules__unlock_later(self):
        with _helpers.unslot_class(ratelimits.GlobalHTTPRateLimiter)() as limiter:
            limiter._unlock_later = mock.AsyncMock()
            limiter.lock(0)
            await limiter.throttle_task
            limiter._unlock_later.assert_called_once_with(0)

    @pytest.mark.asyncio
    async def test__unlock_later_chews_queue_completing_futures(self, event_loop):
        with ratelimits.GlobalHTTPRateLimiter() as limiter:
            futures = [event_loop.create_future() for _ in range(10)]
            limiter.queue = list(futures)
            await limiter._unlock_later(0.01)
            for i, future in enumerate(futures):
                assert future.done(), f"future {i} was not done"

    @pytest.mark.asyncio
    async def test__unlock_later_sleeps_before_popping_queue(self, event_loop):
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

        with _helpers.unslot_class(ratelimits.GlobalHTTPRateLimiter)() as limiter:
            with mock.patch("asyncio.sleep", wraps=mock_sleep):
                limiter.queue = MockList()

                # WHEN
                await limiter._unlock_later(5)

        # THEN
        for i, pop_time in enumerate(popped_at):
            assert slept_at < pop_time, f"future {i} popped before initial sleep"

    @pytest.mark.asyncio
    async def test__unlock_later_clears_throttle_task(self, event_loop):
        with ratelimits.GlobalHTTPRateLimiter() as limiter:
            limiter.throttle_task = event_loop.create_future()
            await limiter._unlock_later(0)
        assert limiter.throttle_task is None
