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
import typing
from unittest import mock

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


def mock_methods_on(obj, except_=(), also_mock=()):
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


def assert_raises(type_):
    def decorator(test):
        @pytest.mark.asyncio
        @functools.wraps(test)
        async def impl(*args, **kwargs):
            try:
                result = test(*args, **kwargs)
                if asyncio.iscoroutinefunction(test):
                    await result
                assert False, f"{type_.__name__} was not raised."
            except type_:
                pass
            except BaseException as ex:
                raise AssertionError(f"Expected {type_.__name__} to be raised but got {type(ex).__name__}") from ex

        return impl

    return decorator


def fqn1(obj_):
    return obj_.__module__ + "." + obj_.__qualname__


def fqn2(module, item_identifier):
    return module.__name__ + "." + item_identifier


T = typing.TypeVar("T")


def mock_model(spec_set: typing.Type[T] = object, **kwargs) -> T:
    # Enables type hinting for my own reference, and quick attribute setting.
    obj = mock.MagicMock(spec_set=spec_set)
    for name, value in kwargs.items():
        setattr(obj, name, value)

    obj.__eq__ = lambda self, other: other is self
    obj.__ne__ = lambda self, other: other is not self
    return obj


def unslot_class(klass):
    return type(klass.__name__ + "Unslotted", (klass,), {})


def mock_patch(what, *args, **kwargs):
    # If something refers to a strong reference, e.g. aiofiles.open is just a reference to aiofile.threadpool.open,
    # you will need to pass a string to patch it...
    if isinstance(what, str):
        fqn = what
    else:
        fqn = fqn1(what)

    return asynctest.patch(fqn, *args, **kwargs)
