#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019
#
# This file is part of Hikari.
#
# Hikari is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hikari is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Hikari. If not, see <https://www.gnu.org/licenses/>.

import asyncio
import copy
import functools
import inspect
import logging
import threading

import asynctest
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


def _terminate_in_10_thread(event: threading.Event, timeout, loop):
    if not event.wait(timeout):
        loop.close()


def mark_asyncio_with_timeout(timeout=10):
    """Marks a test as an asyncio py-test, but also fails the test if it runs for more than the given timeout."""

    def decorator(coro):
        @functools.wraps(coro)
        async def wrapper(event_loop, *args, **kwargs):
            event = threading.Event()
            t = threading.Thread(target=_terminate_in_10_thread, args=[event, timeout, event_loop], daemon=True)
            t.start()
            await coro(event_loop, *args, **kwargs)
            event.set()

        return pytest.mark.asyncio(wrapper)

    return decorator


def _mock_methods_on(obj, except_=(), also_mock=()):
    # Mock any methods we don't care about. also_mock is a collection of attribute names that we can eval to access
    # and mock specific components with a coroutine mock to mock other external components quickly :)
    magics = ["__enter__", "__exit__", "__aenter__", "__aexit__", "__iter__", "__aiter__"]

    except_ = set(except_)
    also_mock = set(also_mock)

    checked = set()

    def predicate(name, member):
        is_callable = callable(member)
        has_name = bool(name)
        name_is_allowed = name not in except_

        if not name_is_allowed:
            checked.add(name)

        is_not_disallowed_magic = not name.startswith("__") or name in magics
        # print(name, is_callable, has_name, name_is_allowed, is_not_disallowed_magic)
        return is_callable and has_name and name_is_allowed and is_not_disallowed_magic

    copy_ = copy.copy(obj)
    for name, method in inspect.getmembers(obj):
        if predicate(name, method):
            # print('Mocking', name, 'on', type(obj))

            if asyncio.iscoroutinefunction(method):
                mock = asynctest.CoroutineMock()
            else:
                mock = asynctest.MagicMock()

            setattr(copy_, name, mock)

    for expr in also_mock:
        owner, _, attr = ("copy_." + expr).rpartition(".")
        # sue me.
        owner = eval(owner)
        setattr(owner, attr, asynctest.CoroutineMock())

    assert not (except_ - checked), f"Some attributes didn't exist, so were not mocked: {except_ - checked}"

    return copy_
