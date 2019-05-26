#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio

import asynctest

from hikari.net import bucket
from tests import _helpers


def teardown_function():
    _helpers.purge_loop()


def test_bucket_level_accessor(event_loop):
    # I know this works. It is a simple accessor.
    assert bucket.LeakyBucket(10, 1, event_loop).level == 0


def test_bucket_backlog_accessor(event_loop):
    # Again, I know this works. It just calls the queue length and if that isn't populated, everything goes to shit.
    b = bucket.LeakyBucket(10, 0.1, event_loop)
    t = 'test'
    b._queue[t] = event_loop.create_future()
    assert b.backlog == 1


@_helpers.non_zombified_async_test()
async def test_bucket_leaks_down_to_zero(event_loop):
    b = bucket.LeakyBucket(10, 0.1, event_loop)
    b._leak()
    b._level = 10
    while b.level > 0:
        # __import__('logging').info("Drip %s", b.level)
        b._leak()
    assert b.level == 0


@_helpers.non_zombified_async_test()
async def test_bucket_has_capacity(event_loop):
    b = bucket.LeakyBucket(10, 0.1, event_loop)
    b._leak()
    b._level = 5
    t = 'test'
    b._queue[t] = event_loop.create_future()
    assert b._is_capacity_available(1)


@_helpers.non_zombified_async_test()
async def test_bucket_does_not_have_capacity(event_loop):
    b = bucket.LeakyBucket(10, 0.1, event_loop)
    b._full_event = asynctest.MagicMock()
    b._leak()
    b._level = 5
    t = 'test'
    b._queue[t] = event_loop.create_future()
    assert not b._is_capacity_available(7)
    b._full_event.set.assert_called_once()


@_helpers.non_zombified_async_test()
async def test_bucket_makes_me_wait_for_it_to_empty_a_bit_first(event_loop):
    b = bucket.LeakyBucket(10, 0.1, event_loop)
    b._full_event = asynctest.MagicMock()
    b._leak()
    b._level = 9.5
    t = 'test'
    b._queue[t] = event_loop.create_future()
    async with b:
        pass
    b._full_event.set.assert_called_once()


@_helpers.non_zombified_async_test()
async def test_bucket_doesnt_deadlock_on_impossible_acquisition(event_loop):
    b = bucket.LeakyBucket(10, 0.1, event_loop)
    b._full_event = asynctest.MagicMock()
    b._leak()
    b._level = 9.5
    try:
        await b.acquire(9999)
        assert False, 'No error raised'
    except ValueError:
        assert True