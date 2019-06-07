#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio

try:
    assert asyncio.create_task
except (AssertionError, AttributeError):
    # 3.6 compat
    asyncio.create_task = lambda coro, **_: asyncio.get_event_loop().create_task(coro)
