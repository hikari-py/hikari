#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import functools
import logging

import async_timeout
import pytest

_LOGGER = logging.getLogger(__name__)


def purge_loop():
    """Empties the event loop properly."""
    loop = asyncio.get_event_loop()
    for item in loop._scheduled:
        _LOGGER.info("Cancelling scheduled item in event loop {}", item)
        item.cancel()
    for item in loop._ready:
        _LOGGER.info("Cancelling ready item in event loop {}", item)
        item.cancel()
    loop._scheduled.clear()
    loop._ready.clear()
    loop.close()


def mark_asyncio_with_timeout(timeout=10):
    """Marks a test as an asyncio py-test, but also fails the test if it runs for more than the given timeout."""

    def decorator(coro):
        @functools.wraps(coro)
        async def wrapper(event_loop):
            async with async_timeout.timeout(timeout):
                await coro(event_loop)

        return pytest.mark.asyncio(wrapper)

    return decorator

