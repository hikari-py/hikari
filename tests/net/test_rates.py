#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import collections
import math
import time

import asynctest

from tests import _helpers


from hikari.net import rates


class DummyBucket(rates.Bucket):
    ENQUEUE_FUTURE_IS_ALREADY_COMPLETED = False

    def __init__(self, total: int, per: float, loop: asyncio.AbstractEventLoop) -> None:
        self._total = total
        self._per = per
        self._remaining = total
        self._reset_at = time.perf_counter()
        self._queue = collections.deque()
        self.loop = loop
        self._reassess = asynctest.MagicMock()

    def _enqueue(self) -> asyncio.Future:
        f = super()._enqueue()
        if self.ENQUEUE_FUTURE_IS_ALREADY_COMPLETED:
            f.set_result(None)
        return f

    def _reassess(self):
        ...


@_helpers.mark_asyncio_with_timeout()
async def test_Bucket_enqueue(event_loop):
    b = DummyBucket(1, 1, event_loop)
    assert len(b) == 0
    b._enqueue()
    assert len(b) == 1


@_helpers.mark_asyncio_with_timeout()
async def test_Bucket_maybe_reawaken_and_reset_calls_reassess(event_loop):
    b = DummyBucket(1, 1, event_loop)
    b._reassess = asynctest.MagicMock()
    f = event_loop.create_future()
    f.set_result(None)
    b._maybe_awaken_and_reset(f)
    b._reassess.assert_called_once()


@_helpers.mark_asyncio_with_timeout()
async def test_Bucket_maybe_reawaken_and_reset_reinvokes_if_not_done(event_loop):
    b = DummyBucket(1, 0.25, event_loop)
    b._reassess = asynctest.MagicMock()
    f = event_loop.create_future()
    b._maybe_awaken_and_reset(f)
    assert not f.done()
    f.set_result(None)
    await asyncio.sleep(0.4)
    assert f.done()
    # Should have been hit twice by design.
    assert 2 == len(b._reassess.mock_calls)


# Easier to test this on the underlying implementation than mock a bunch of stuff, and this ensures the correct
# behaviour anyway.
@_helpers.mark_asyncio_with_timeout()
async def test_TimedTokenBucket_acquire(event_loop):
    b = rates.TimedTokenBucket(10, 0.25, event_loop)
    b.ENQUEUE_FUTURE_IS_ALREADY_COMPLETED = True
    await b.acquire()
    assert b._remaining == 9


# If this begins to fail, change the time to 2s, with abs_tol=1, or something
@_helpers.mark_asyncio_with_timeout()
async def test_TimedTokenBucket_acquire_when_empty(event_loop):
    b = rates.TimedTokenBucket(1, 0.25, event_loop)
    await b.acquire()
    start = time.perf_counter()
    await b.acquire()
    time_taken = time.perf_counter() - start
    assert b._remaining == 0
    # We should have been rate limited by 1 second.
    assert math.isclose(time_taken, 0.25, abs_tol=0.1)
