#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Python3.6 compatibility fixes and patches."""
import asyncio
import typing

if not hasattr(asyncio, "get_running_loop"):
    # Python 3.6 and lower. Not the exact same behaviour but should be fine unless the user is doing voodoo to run
    # more than one loop on the same logical thread (gevent may be an issue, but who cares for now?)
    asyncio.get_running_loop = lambda: asyncio.get_event_loop()
    asyncio.create_task = lambda coro: asyncio.get_running_loop().create_task(coro)

if not hasattr(typing, "NoReturn"):
    # PyPy3.6 fails to implement this correctly despite it being in the Python spec since 3.5.3.
    typing.NoReturn = NotImplemented
