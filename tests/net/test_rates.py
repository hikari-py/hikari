#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import math
import time

import asynctest
import pytest

from hikari.net import rates
from tests import _helpers


# Easier to test this on the underlying implementation than mock a bunch of stuff, and this ensures the correct
# behaviour anyway.
@_helpers.mark_asyncio_with_timeout()
async def test_TimedTokenBucket_acquire(event_loop):
    b = rates.TimedTokenBucket(10, 0.25, event_loop)
    b.ENQUEUE_FUTURE_IS_ALREADY_COMPLETED = True
    await b.acquire()
    assert b._remaining == 9


@_helpers.mark_asyncio_with_timeout()
async def test_VariableTokenBucket_acquire(event_loop):
    b = rates.VariableTokenBucket(10, 10, 35, 36, event_loop)
    b.ENQUEUE_FUTURE_IS_ALREADY_COMPLETED = True
    await b.acquire()
    assert b._remaining == 9


@_helpers.mark_asyncio_with_timeout()
async def test_TimedTokenBucket_acquire_with_callback(event_loop):
    b = rates.TimedTokenBucket(10, 0.25, event_loop)
    callback = asynctest.MagicMock()
    await b.acquire(callback)
    assert b._remaining == 9
    callback.assert_not_called()


@_helpers.mark_asyncio_with_timeout()
async def test_VariableTokenBucket_acquire_with_callback(event_loop):
    b = rates.VariableTokenBucket(10, 10, 35, 36, event_loop)
    callback = asynctest.MagicMock()
    await b.acquire(callback)
    assert b._remaining == 9
    callback.assert_not_called()


# If this begins to fail, change the time to 2s, with abs_tol=1, or something
@_helpers.mark_asyncio_with_timeout()
async def test_TimedTokenBucket_acquire_when_empty(event_loop):
    b = rates.TimedTokenBucket(1, 0.25, event_loop)
    await b.acquire()
    start = time.perf_counter()
    await b.acquire()
    time_taken = time.perf_counter() - start
    assert b._remaining == 0
    # We should have been rate limited by 0.25s second.
    assert math.isclose(time_taken, 0.25, abs_tol=0.1)


@_helpers.mark_asyncio_with_timeout()
async def test_VariableTokenBucket_acquire_when_empty(event_loop):
    b = rates.VariableTokenBucket(1, 1, 35, 36, event_loop)
    await b.acquire()
    start = time.perf_counter()
    await b.acquire()
    time_taken = time.perf_counter() - start
    assert b._remaining == 0
    # We should have been rate limited by 1 second.
    assert math.isclose(time_taken, 1, abs_tol=0.1)


# If this begins to fail, change the time to 2s, with abs_tol=1, or something
@_helpers.mark_asyncio_with_timeout()
async def test_TimedTokenBucket_acquire_when_empty_with_callback(event_loop):
    b = rates.TimedTokenBucket(1, 0.25, event_loop)
    await b.acquire()
    start = time.perf_counter()
    callback = asynctest.MagicMock()
    await b.acquire(callback)
    time_taken = time.perf_counter() - start
    assert b._remaining == 0
    # We should have been rate limited by 0.25s second.
    assert math.isclose(time_taken, 0.25, abs_tol=0.1)
    callback.assert_called_once()


@_helpers.mark_asyncio_with_timeout()
async def test_VariableTokenBucket_acquire_when_empty_with_callback(event_loop):
    b = rates.VariableTokenBucket(1, 1, 35, 36, event_loop)
    await b.acquire()
    start = time.perf_counter()
    callback = asynctest.MagicMock()
    await b.acquire(callback)
    time_taken = time.perf_counter() - start
    assert b._remaining == 0
    # We should have been rate limited by 1 second.
    assert math.isclose(time_taken, 1, abs_tol=0.1)
    callback.assert_called_once()


@_helpers.mark_asyncio_with_timeout()
async def test_TimedTokenBucket_queue(event_loop):
    b = rates.TimedTokenBucket(10, 1, event_loop)
    assert not b._queue
    b._enqueue()
    assert len(b._queue) == 1


@_helpers.mark_asyncio_with_timeout()
async def test_VariableTokenBucket_queue(event_loop):
    b = rates.VariableTokenBucket(10, 1, 7, 12, event_loop)
    assert not b._queue
    b._enqueue()
    assert len(b._queue) == 1


@_helpers.mark_asyncio_with_timeout()
async def test_TimedTokenBucket_async_ctx(event_loop):
    b = rates.TimedTokenBucket(10, 1, event_loop)
    b.acquire = asynctest.CoroutineMock()
    async with b:
        pass

    b.acquire.assert_awaited_once()


@_helpers.mark_asyncio_with_timeout()
async def test_VariableTokenBucket_async_ctx(event_loop):
    b = rates.VariableTokenBucket(10, 1, 7, 12, event_loop)
    b.acquire = asynctest.CoroutineMock()
    async with b:
        pass

    b.acquire.assert_awaited_once()


@_helpers.mark_asyncio_with_timeout()
async def test_TimedTokenBucket_reassess_when_reset_at_is_in_past(event_loop):
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
async def test_VariableTokenBucket_reassess_when_reset_at_is_in_past(event_loop):
    with asynctest.patch("time.perf_counter", new=lambda: 10):
        b = rates.VariableTokenBucket(10, 1, 0, 110, event_loop)

        b._remaining = 0
        b._reset_at = -1

        b._reassess()
        assert b._remaining == b._total
        assert b._reset_at == 110


@_helpers.mark_asyncio_with_timeout()
async def test_TimedTokenBucket_reassess_runs_as_many_tasks_as_possible(event_loop):
    b = rates.TimedTokenBucket(10, 3, event_loop)
    # b = rates.VariableTokenBucket(10, 10, 0, 10, event_loop)
    for i in range(15):
        b.acquire()
