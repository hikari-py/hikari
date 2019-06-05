#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Asyncio compatibility methods.
"""
import asyncio as _asyncio

# noinspection PyUnresolvedReferences
from asyncio import *

#: Not supported before Python3.8, so just no-op if not available.
set_task_name = getattr(_asyncio.tasks, "_set_task_name", lambda task, name: None)

#: Not in the same namespace in Python3.7.
current_task = getattr(_asyncio, "current_task", _asyncio.tasks.Task.current_task)

#: Not implemented in spec for Python3.6, so we assume it doesn't exist and fall back to
#: :func:`asyncio.get_event_loop` if required.
get_running_loop = getattr(_asyncio, "get_running_loop", _asyncio.get_event_loop)

#: Not implemented in Python3.6. Does not support names in 3.7, so use :attr:`set_task_name` instead to set that.
create_task = getattr(_asyncio, "create_task", lambda coro: get_running_loop().create_task(coro))
