#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio

import pytest
from hikari.net import bucket


@pytest.mark.asyncio
async def test_submit_returns_task(event_loop):
    b = bucket.LeakyBucket(1, 1, event_loop)

    async def test():
        pass

    f = b.submit(test)

    assert isinstance(f, asyncio.Future)


@pytest.mark.asyncio
async def test_submit_doesnt_ratelimits_after_given_number_of_stacked_calls(event_loop):
    b = bucket.LeakyBucket(10, 10, event_loop)

    async def task():
        await asyncio.sleep(5)

    async def load():
        await asyncio.sleep(0.5)
        for i in range(11):
            b.submit(task)

    async def waiter():
        await b.ratelimited_event.wait()

    await asyncio.gather(waiter(), load())
