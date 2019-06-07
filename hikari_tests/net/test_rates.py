#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import math
import time

import asynctest
import pytest

from hikari.net import rates
from hikari_tests import _helpers


# Easier to test this on the underlying implementation than mock a bunch of stuff, and this ensures the correct
# behaviour anyway.
@_helpers.mark_asyncio_with_timeout()
@pytest.mark.slow
async def test_TimedTokenBucket_acquire_should_decrease_remaining_count_by_1(event_loop):
    b = rates.TimedTokenBucket(10, 0.25, event_loop)
    b.ENQUEUE_FUTURE_IS_ALREADY_COMPLETED = True
    await b.acquire()
    assert b._remaining == 9


@_helpers.mark_asyncio_with_timeout()
@pytest.mark.slow
async def test_VariableTokenBucket_acquire_should_decrease_remaining_count_by_1(event_loop):
    b = rates.VariableTokenBucket(10, 10, 35, 36, event_loop)
    b.ENQUEUE_FUTURE_IS_ALREADY_COMPLETED = True
    await b.acquire()
    assert b._remaining == 9


@_helpers.mark_asyncio_with_timeout()
@pytest.mark.slow
async def test_TimedTokenBucket_acquire_when_not_rate_limited_with_callback_does_not_call_it(event_loop):
    b = rates.TimedTokenBucket(10, 0.25, event_loop)
    callback = asynctest.MagicMock()
    await b.acquire(callback)
    assert b._remaining == 9
    callback.assert_not_called()


@_helpers.mark_asyncio_with_timeout()
@pytest.mark.slow
async def test_VariableTokenBucket_acquire_when_not_rate_limited_with_callback_does_not_call_it(event_loop):
    now = time.perf_counter()
    b = rates.VariableTokenBucket(10, 10, now, now + 3, event_loop)
    callback = asynctest.MagicMock()
    await b.acquire(callback)
    assert b._remaining == 9
    callback.assert_not_called()


@_helpers.mark_asyncio_with_timeout()
@pytest.mark.slow
async def test_TimedTokenBucket_acquire_when_rate_limiting_without_callback_functions_correctly(event_loop):
    b = rates.TimedTokenBucket(1, 3, event_loop)
    await b.acquire()
    start = time.perf_counter()
    await b.acquire()
    time_taken = time.perf_counter() - start
    assert b._remaining == 0
    assert math.isclose(time_taken, 3, abs_tol=0.25)


@_helpers.mark_asyncio_with_timeout()
@pytest.mark.slow
async def test_VariableTokenBucket_acquire_when_rate_limiting_without_callback_functions_correctly(event_loop):
    now = time.perf_counter()
    b = rates.VariableTokenBucket(1, 1, now, now + 3, event_loop)
    await b.acquire()
    start = time.perf_counter()
    await b.acquire()
    time_taken = time.perf_counter() - start
    assert b._remaining == 0
    assert math.isclose(time_taken, 3, abs_tol=0.25)


# If this begins to fail, change the time to 2s, with abs_tol=1, or something
@_helpers.mark_asyncio_with_timeout()
@pytest.mark.slow
async def test_TimedTokenBucket_acquire_when_rate_limiting_with_callback_should_invoke_the_callback_once(event_loop):
    b = rates.TimedTokenBucket(1, 3, event_loop)
    await b.acquire()
    start = time.perf_counter()
    callback = asynctest.MagicMock()
    await b.acquire(callback)
    time_taken = time.perf_counter() - start
    assert b._remaining == 0

    assert math.isclose(time_taken, 3, abs_tol=0.25)
    callback.assert_called_once()


@_helpers.mark_asyncio_with_timeout()
@pytest.mark.slow
async def test_VariableTokenBucket_acquire_when_rate_limiting_with_callback_should_invoke_the_callback_once(event_loop):
    now = time.perf_counter()
    b = rates.VariableTokenBucket(1, 1, now, now + 3, event_loop)
    await b.acquire()
    start = time.perf_counter()
    callback = asynctest.MagicMock()
    await b.acquire(callback)
    time_taken = time.perf_counter() - start
    assert b._remaining == 0
    # We should have been rate limited by 1 second.
    assert math.isclose(time_taken, 3, abs_tol=0.25)
    callback.assert_called_once()


@_helpers.mark_asyncio_with_timeout()
@pytest.mark.slow
async def test_TimedTokenBucket_queue_should_make_an_incomplete_future(event_loop):
    b = rates.TimedTokenBucket(10, 1, event_loop)
    assert not b._queue
    b._enqueue()
    assert len(b._queue) == 1
    assert isinstance(b._queue.pop(), asyncio.Future)


@_helpers.mark_asyncio_with_timeout()
@pytest.mark.slow
async def test_VariableTokenBucket_queue_should_make_an_incomplete_future(event_loop):
    b = rates.VariableTokenBucket(10, 1, 7, 12, event_loop)
    assert not b._queue
    b._enqueue()
    assert len(b._queue) == 1
    assert isinstance(b._queue.pop(), asyncio.Future)


@_helpers.mark_asyncio_with_timeout()
@pytest.mark.slow
async def test_TimedTokenBucket_async_with_context_manager(event_loop):
    b = rates.TimedTokenBucket(10, 1, event_loop)
    b.acquire = asynctest.CoroutineMock()
    async with b:
        pass

    b.acquire.assert_awaited_once()


@_helpers.mark_asyncio_with_timeout()
@pytest.mark.slow
async def test_VariableTokenBucket_async_with_context_manager(event_loop):
    b = rates.VariableTokenBucket(10, 1, 7, 12, event_loop)
    b.acquire = asynctest.CoroutineMock()
    async with b:
        pass

    b.acquire.assert_awaited_once()


@_helpers.mark_asyncio_with_timeout()
@pytest.mark.slow
async def test_VariableTokenBucket_update_when_still_under_limit_but_remaining_did_not_change_should_not_reassess(
    event_loop
):
    now = time.perf_counter()
    b = rates.VariableTokenBucket(10, 1, now - 5, now + 5, event_loop)
    b._reassess = asynctest.MagicMock()
    b.update(15, 1, now, now + 10, False)
    assert b._total == 15
    assert b._remaining == 1
    assert b._per == 10
    assert math.isclose(b._reset_at, now + 10, abs_tol=0.25)
    assert math.isclose(b._last_reset_at, now, abs_tol=0.25)
    b._reassess.assert_not_called()


@_helpers.mark_asyncio_with_timeout()
@pytest.mark.slow
async def test_VariableTokenBucket_update_when_still_under_limit_but_remaining_did_change_should_reassess(event_loop):
    now = time.perf_counter()
    b = rates.VariableTokenBucket(10, 1, now - 5, now + 5, event_loop)
    b._reassess = asynctest.MagicMock()
    b.update(15, 15, now, now + 10, False)
    assert b._total == 15
    assert b._remaining == 15
    assert b._per == 10
    assert math.isclose(b._reset_at, now + 10, abs_tol=0.25)
    assert math.isclose(b._last_reset_at, now, abs_tol=0.25)
    b._reassess.assert_called_once()


@_helpers.mark_asyncio_with_timeout()
@pytest.mark.slow
async def test_VariableTokenBucket_update_when_not_under_limit_but_remaining_did_not_change_should_not_reassess(
    event_loop
):
    now = time.perf_counter()
    b = rates.VariableTokenBucket(10, 1, now - 5, now - 1, event_loop)
    b._reassess = asynctest.MagicMock()
    b.update(15, 1, now, now + 10, False)
    assert b._total == 15
    assert b._remaining == 1
    assert b._per == 10
    assert math.isclose(b._reset_at, now + 10, abs_tol=0.25)
    assert math.isclose(b._last_reset_at, now, abs_tol=0.25)
    b._reassess.assert_not_called()


@_helpers.mark_asyncio_with_timeout()
@pytest.mark.slow
async def test_VariableTokenBucket_update_when_not_under_limit_but_remaining_did_change_should_reassess(event_loop):
    now = time.perf_counter()
    b = rates.VariableTokenBucket(10, 1, now - 5, now - 1, event_loop)
    b._reassess = asynctest.MagicMock()
    b.update(15, 15, now, now + 10, False)
    assert b._total == 15
    assert b._remaining == 15
    assert b._per == 10
    assert math.isclose(b._reset_at, now + 10, abs_tol=0.25)
    assert math.isclose(b._last_reset_at, now, abs_tol=0.25)
    b._reassess.assert_called_once()


@_helpers.mark_asyncio_with_timeout()
@pytest.mark.slow
async def test_TimedTokenBucket_reassess_when_reset_at_attribute_is_in_the_past_should_update_internal_state(
    event_loop
):
    with asynctest.patch("time.perf_counter", new=lambda: 10):
        b = rates.TimedTokenBucket(10, 1, event_loop)
        b._total = 100
        b._per = 100
        b._remaining = 10
        b._reset_at = -1

        b._reassess()
        assert b._remaining == b._total
        assert b._reset_at == 110


@_helpers.mark_asyncio_with_timeout()
@pytest.mark.slow
async def test_VariableTokenBucket_reassess_when_reset_at_attribute_is_in_the_past_should_update_internal_state(
    event_loop
):
    now = time.perf_counter()
    b = rates.VariableTokenBucket(10, 1, now, now + 3, event_loop)

    b._remaining = 0
    b._reset_at = -1

    b._reassess()
    assert b._remaining == b._total
    assert math.isclose(b._reset_at, now + 3, abs_tol=0.25)


@_helpers.mark_asyncio_with_timeout()
@pytest.mark.slow
async def test_TimedTokenBucket_reassess_must_run_as_many_tasks_as_possible_in_expected_time(event_loop):
    b = rates.TimedTokenBucket(10, 3, event_loop)

    checked = False

    def assert_locked():
        print("You are being ratelimited")
        nonlocal checked
        checked = True
        assert b.is_limiting

    callback = asynctest.MagicMock(wraps=assert_locked)

    start = time.perf_counter()

    for i in range(25):
        await b.acquire(callback)

    elapsed = time.perf_counter() - start
    callback.assert_called()
    assert checked
    assert math.isclose(elapsed, 6, abs_tol=0.25)


@_helpers.mark_asyncio_with_timeout()
@pytest.mark.slow
async def test_VariableTokenBucket_must_run_as_many_tasks_as_possible_in_expected_time(event_loop):
    now = time.perf_counter()
    b = rates.VariableTokenBucket(10, 10, now, now + 3, event_loop)

    checked = False

    def assert_locked():
        print("You are being ratelimited", b.is_limiting, b._per, b._remaining, b._last_reset_at, b._reset_at, b._total)
        nonlocal checked
        checked = True
        assert b.is_limiting

    callback = asynctest.MagicMock(wraps=assert_locked)

    start = time.perf_counter()

    tasks = []

    for i in range(25):
        tasks.append(b.acquire(callback))

    await asyncio.gather(*tasks)

    elapsed = time.perf_counter() - start

    callback.assert_called()
    assert checked
    assert math.isclose(elapsed, 6, abs_tol=0.25)


@_helpers.mark_asyncio_with_timeout()
@pytest.mark.slow
async def test_TimedLatchBucket_when_not_locked_will_return_immediately(event_loop):
    latch = rates.TimedLatchBucket(event_loop)

    start = time.perf_counter()
    callback = asynctest.MagicMock()
    await latch.acquire(callback)
    end = time.perf_counter()

    callback.assert_not_called()
    # Assert we didn't really wait at all.
    assert math.isclose(end - start, 0, abs_tol=0.1)


@_helpers.mark_asyncio_with_timeout()
@pytest.mark.slow
async def test_TimedLatchBucket_when_locked_will_return_after_a_cooldown(event_loop):
    latch = rates.TimedLatchBucket(event_loop)

    checked = False

    def assert_locked(nine, eighteen, foo):
        nonlocal checked
        print("You are being ratelimitied")
        checked = True
        assert nine == 9
        assert eighteen == 18
        assert foo == 27
        assert latch.is_limiting

    callback = asynctest.MagicMock(wraps=assert_locked)
    latch.lock(3)
    # Yield for a moment to ensure the routine is triggered before we try to acquire.
    await asyncio.sleep(0.05)
    start = time.perf_counter()
    await latch.acquire(callback, 9, 18, foo=27)
    end = time.perf_counter()

    callback.assert_called_with(9, 18, foo=27)
    assert checked
    # Assert we waited for about 3 seconds.
    assert math.isclose(end - start, 3, abs_tol=0.25)


@_helpers.mark_asyncio_with_timeout()
@pytest.mark.slow
async def test_TimedLatchBucket_when_locked_no_args(event_loop):
    latch = rates.TimedLatchBucket(event_loop)
    latch.lock(3)
    # Yield for a moment to ensure the routine is triggered before we try to acquire.
    await asyncio.sleep(0.05)
    start = time.perf_counter()
    await latch.acquire()
    end = time.perf_counter()
    # Assert we waited for about 3 seconds.
    assert math.isclose(end - start, 3, abs_tol=0.25)


@_helpers.mark_asyncio_with_timeout()
@pytest.mark.slow
async def test_TimedLatchBucket_async_with_context_manager(event_loop):
    latch = rates.TimedLatchBucket(event_loop)
    latch.acquire = asynctest.CoroutineMock()
    async with latch:
        pass

    latch.acquire.assert_awaited()
