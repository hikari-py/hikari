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
import math
import time

import asyncmock as mock
import pytest

from hikari.net import rates
from tests.hikari import _helpers


class UnslottedBase:
    pass


@pytest.fixture
def timed_token_bucket():
    class TimedTokenBucket(rates.TimedTokenBucket, UnslottedBase):
        pass

    return TimedTokenBucket


@pytest.fixture
def timed_latch_bucket():
    class TimedLatchBucket(rates.TimedLatchBucket, UnslottedBase):
        pass

    return TimedLatchBucket


@pytest.fixture
def variable_token_bucket():
    class VariableTokenBucket(rates.VariableTokenBucket, UnslottedBase):
        pass

    return VariableTokenBucket


@pytest.mark.asyncio
@pytest.mark.slow
@pytest.mark.trylast
class TestRates:
    # Easier to test this on the underlying implementation than mock a bunch of stuff, and this ensures the correct
    # behaviour anyway.
    async def test_TimedTokenBucket_acquire_should_decrease_remaining_count_by_1(self, event_loop, timed_token_bucket):
        b = timed_token_bucket(10, 0.25, event_loop)
        await b.acquire()
        assert b._remaining == 9

    async def test_VariableTokenBucket_acquire_should_decrease_remaining_count_by_1(
        self, event_loop, variable_token_bucket
    ):
        b = variable_token_bucket(10, 10, 35, 36, event_loop)
        await b.acquire()
        assert b._remaining == 9

    async def test_TimedTokenBucket_acquire_when_not_rate_limited_with_callback_does_not_call_it(
        self, event_loop, timed_token_bucket
    ):
        b = timed_token_bucket(10, 0.25, event_loop)
        callback = mock.MagicMock()
        await b.acquire(callback)
        assert b._remaining == 9
        callback.assert_not_called()

    async def test_VariableTokenBucket_acquire_when_not_rate_limited_with_callback_does_not_call_it(
        self, event_loop, variable_token_bucket
    ):
        now = time.perf_counter()
        b = variable_token_bucket(10, 10, now, now + 1, event_loop)
        callback = mock.MagicMock()
        await b.acquire(callback)
        assert b._remaining == 9
        callback.assert_not_called()

    async def test_TimedTokenBucket_acquire_when_rate_limiting_without_callback_functions_correctly(
        self, event_loop, timed_token_bucket
    ):
        b = timed_token_bucket(1, 1, event_loop)
        await b.acquire()
        start = time.perf_counter()
        await b.acquire()
        time_taken = time.perf_counter() - start
        assert b._remaining == 0
        assert math.isclose(time_taken, 1, abs_tol=0.25)

    async def test_VariableTokenBucket_acquire_when_rate_limiting_without_callback_functions_correctly(
        self, event_loop, variable_token_bucket
    ):
        now = time.perf_counter()
        b = variable_token_bucket(1, 1, now, now + 1, event_loop)
        await b.acquire()
        start = time.perf_counter()
        await b.acquire()
        time_taken = time.perf_counter() - start
        assert b._remaining == 0
        assert math.isclose(time_taken, 1, abs_tol=0.25)

    # If this begins to fail, change the time to 2s, with abs_tol=1, or something
    async def test_TimedTokenBucket_acquire_when_rate_limiting_with_callback_should_invoke_the_callback_once(
        self, event_loop, timed_token_bucket
    ):
        b = timed_token_bucket(1, 1, event_loop)
        await b.acquire()
        start = time.perf_counter()
        callback = mock.MagicMock()
        await b.acquire(callback)
        time_taken = time.perf_counter() - start
        assert b._remaining == 0

        assert math.isclose(time_taken, 1, abs_tol=0.25)
        callback.assert_called_once()

    async def test_VariableTokenBucket_acquire_when_rate_limiting_with_callback_should_invoke_the_callback_once(
        self, event_loop, variable_token_bucket
    ):
        now = time.perf_counter()
        b = variable_token_bucket(1, 1, now, now + 1, event_loop)
        await b.acquire()
        start = time.perf_counter()
        callback = mock.MagicMock()
        await b.acquire(callback)
        time_taken = time.perf_counter() - start
        assert b._remaining == 0
        # We should have been rate limited by 1 second.
        assert math.isclose(time_taken, 1, abs_tol=0.25)
        callback.assert_called_once()

    async def test_TimedTokenBucket_queue_should_make_an_incomplete_future(self, event_loop, timed_token_bucket):
        b = timed_token_bucket(10, 1, event_loop)
        assert not b._queue
        b._enqueue()
        assert len(b._queue) == 1
        assert isinstance(b._queue.pop(), asyncio.Future)

    async def test_VariableTokenBucket_queue_should_make_an_incomplete_future(self, event_loop, variable_token_bucket):
        b = variable_token_bucket(10, 1, 7, 12, event_loop)
        assert not b._queue
        b._enqueue()
        assert len(b._queue) == 1
        assert isinstance(b._queue.pop(), asyncio.Future)

    async def test_TimedTokenBucket_async_with_context_manager(self, event_loop, timed_token_bucket):
        b = timed_token_bucket(10, 1, event_loop)
        b.acquire = mock.AsyncMock()
        async with b:
            pass

        b.acquire.assert_called_once()

    async def test_VariableTokenBucket_async_with_context_manager(self, event_loop, variable_token_bucket):
        b = variable_token_bucket(10, 1, 7, 12, event_loop)
        b.acquire = mock.AsyncMock()
        async with b:
            pass

        b.acquire.assert_called_once()

    async def test_VariableTokenBucket_update_when_still_under_limit_but_remaining_did_not_change_should_not_reassess(
        self, event_loop, variable_token_bucket
    ):
        now = time.perf_counter()
        b = variable_token_bucket(10, 1, now - 5, now + 5, event_loop)
        b._reassess = mock.MagicMock()
        b.update(15, 1, now, now + 10, False)
        assert b._total == 15
        assert b._remaining == 1
        assert math.isclose(b._per, 10, rel_tol=0.1)
        assert math.isclose(b._reset_at, now + 10, abs_tol=0.25)
        assert math.isclose(b._last_reset_at, now, abs_tol=0.25)
        b._reassess.assert_not_called()

    async def test_VariableTokenBucket_update_when_still_under_limit_but_remaining_did_change_should_reassess(
        self, event_loop, variable_token_bucket
    ):
        now = time.perf_counter()
        b = variable_token_bucket(10, 1, now - 5, now + 5, event_loop)
        b._reassess = mock.MagicMock()
        b.update(15, 15, now, now + 10, False)
        assert b._total == 15
        assert b._remaining == 15
        assert math.isclose(b._per, 10, rel_tol=0.1)
        assert math.isclose(b._reset_at, now + 10, abs_tol=0.25)
        assert math.isclose(b._last_reset_at, now, abs_tol=0.25)
        b._reassess.assert_called_once()

    async def test_VariableTokenBucket_update_when_not_under_limit_but_remaining_did_not_change_should_not_reassess(
        self, event_loop, variable_token_bucket
    ):
        now = time.perf_counter()
        b = variable_token_bucket(10, 1, now - 5, now - 1, event_loop)
        b._reassess = mock.MagicMock()
        b.update(15, 1, now, now + 10, False)
        assert b._total == 15
        assert b._remaining == 1
        assert math.isclose(b._per, 10, rel_tol=0.1)
        assert math.isclose(b._reset_at, now + 10, abs_tol=0.25)
        assert math.isclose(b._last_reset_at, now, abs_tol=0.25)
        b._reassess.assert_not_called()

    async def test_VariableTokenBucket_update_when_not_under_limit_but_remaining_did_change_should_reassess(
        self, event_loop, variable_token_bucket
    ):
        now = time.perf_counter()
        b = variable_token_bucket(10, 1, now - 5, now - 1, event_loop)
        b._reassess = mock.MagicMock()
        b.update(15, 15, now, now + 10, False)
        assert b._total == 15
        assert b._remaining == 15
        assert math.isclose(b._per, 10, rel_tol=0.1)
        assert math.isclose(b._reset_at, now + 10, abs_tol=0.25)
        assert math.isclose(b._last_reset_at, now, abs_tol=0.25)
        b._reassess.assert_called_once()

    async def test_TimedTokenBucket_reassess_when_reset_at_attribute_is_in_the_past_should_update_internal_state(
        self, event_loop, timed_token_bucket
    ):
        with _helpers.mock_patch(time.perf_counter, new=lambda: 10):
            b = timed_token_bucket(10, 1, event_loop)
            b._total = 100
            b._per = 100
            b._remaining = 10
            b.reset_at = -1

            b._reassess()
            assert b._remaining == b._total
            assert b.reset_at == 110

    async def test_VariableTokenBucket_reassess_when_reset_at_attribute_is_in_the_past_should_update_internal_state(
        self, event_loop, variable_token_bucket
    ):
        now = time.perf_counter()
        b = variable_token_bucket(10, 1, now, now + 1, event_loop)

        b._remaining = 0
        b._reset_at = -1

        b._reassess()
        assert b._remaining == b._total
        assert math.isclose(b._reset_at, now + 1, abs_tol=0.25)

    async def test_TimedTokenBucket_reassess_must_run_as_many_tasks_as_possible_in_expected_time(
        self, event_loop, timed_token_bucket
    ):
        b = timed_token_bucket(10, 1, event_loop)

        checked = False

        def assert_locked():
            nonlocal checked
            checked = True
            assert b.is_limiting

        callback = mock.MagicMock(wraps=assert_locked)

        start = time.perf_counter()

        for i in range(25):
            await b.acquire(callback)

        elapsed = time.perf_counter() - start
        callback.assert_called()
        assert checked
        assert math.isclose(elapsed, 2, abs_tol=0.25)

    async def test_VariableTokenBucket_must_run_as_many_tasks_as_possible_in_expected_time(
        self, event_loop, variable_token_bucket
    ):
        now = time.perf_counter()
        b = variable_token_bucket(10, 10, now, now + 1, event_loop)

        checked = False

        def assert_locked():
            nonlocal checked
            checked = True
            assert b.is_limiting

        callback = mock.MagicMock(wraps=assert_locked)

        start = time.perf_counter()

        tasks = []

        for i in range(25):
            tasks.append(b.acquire(callback))

        await asyncio.gather(*tasks)

        elapsed = time.perf_counter() - start

        callback.assert_called()
        assert checked
        assert math.isclose(elapsed, 2, abs_tol=0.25)

    async def test_TimedLatchBucket_when_not_locked_will_return_immediately(self, event_loop, timed_latch_bucket):
        latch = timed_latch_bucket(event_loop)

        start = time.perf_counter()
        callback = mock.MagicMock()
        await latch.acquire(callback)
        end = time.perf_counter()

        callback.assert_not_called()
        # Assert we didn't really wait at all.
        assert math.isclose(end - start, 0, abs_tol=0.1)

    async def test_TimedLatchBucket_when_locked_will_return_after_a_cooldown(self, event_loop, timed_latch_bucket):
        latch = timed_latch_bucket(event_loop)

        checked = False

        def assert_locked(nine, eighteen, foo):
            nonlocal checked
            checked = True
            assert nine == 9
            assert eighteen == 18
            assert foo == 27
            assert latch.is_limiting

        callback = mock.MagicMock(wraps=assert_locked)
        latch.lock(1)
        # Yield for a moment to ensure the routine is triggered before we try to acquire.
        await asyncio.sleep(0.05)
        start = time.perf_counter()
        await latch.acquire(callback, nine=9, eighteen=18, foo=27)
        end = time.perf_counter()

        callback.assert_called_with(nine=9, eighteen=18, foo=27)
        assert checked
        # Assert we waited for about 3 seconds.
        assert math.isclose(end - start, 1, abs_tol=0.25)

    async def test_TimedLatchBucket_when_locked_no_args(self, event_loop, timed_latch_bucket):
        latch = timed_latch_bucket(event_loop)
        latch.lock(1)
        # Yield for a moment to ensure the routine is triggered before we try to acquire.
        await asyncio.sleep(0.05)
        start = time.perf_counter()
        await latch.acquire()
        end = time.perf_counter()

        # Assert we waited for about 3 seconds.
        assert math.isclose(end - start, 1, abs_tol=0.25)

    async def test_TimedLatchBucket_async_with_context_manager(self, event_loop, timed_latch_bucket):
        latch = timed_latch_bucket(event_loop)
        latch.acquire = mock.AsyncMock()
        async with latch:
            pass

        latch.acquire.assert_called()
