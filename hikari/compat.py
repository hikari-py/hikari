#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compatibility components in fake contexts. This is only used internally. Code using this library should not rely on
this module to remain consistent between minor versions.
"""
import asyncio as _asyncio
import contextlib as _contextlib
import typing as _typing


# noinspection PyPep8Naming
class asyncio:
    """Fake namespace for asyncio compatibility components."""

    #: Do not allow initializing of this class.
    __new__, __init__ = NotImplemented, NotImplemented
    #: Not supported before Python3.8, so just no-op if not available.
    set_task_name = getattr(_asyncio.tasks, "_set_task_name", lambda task, name: None)
    #: Not in the same namespace in Python3.7.
    current_task = getattr(_asyncio, "current_task", _asyncio.tasks.Task.current_task)
    #: Not implemented in spec for Python3.6, so we assume it doesn't exist and fall back to
    #: :func:`asyncio.get_event_loop` if required.
    get_running_loop = getattr(_asyncio, "get_running_loop", _asyncio.get_event_loop)
    #: Not implemented in Python3.6. Does not support names in 3.7, so use :attr:`set_task_name` instead to set that.
    create_task = getattr(_asyncio, "create_task", lambda coro: asyncio.get_running_loop().create_task(coro))


# noinspection PyPep8Naming
class contextlib:
    """Fake namespace for contextlib compatibility components."""

    __new__, __init__ = NotImplemented, NotImplemented
    #: Not supported before Python3.7, so just implement `object` if needed.
    AbstractAsyncContextManager = getattr(_contextlib, "AbstractAsyncContextManager", object)


# noinspection PyPep8Naming
class typing:
    """Fake namespace for typing compatibility components."""

    __new__, __init__ = NotImplemented, NotImplemented
    #: Not supported by PyPy3.6
    NoReturn = getattr(_typing, "NoReturn", None)

    #: Type of a traceback.
    TracebackType = ...
    try:
        raise RuntimeError
    except RuntimeError as __ex:
        TracebackType = type(__ex.__traceback__)
        del __ex
