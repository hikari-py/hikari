# -*- coding: utf-8 -*-
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021-present davfsa
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import asyncio
import contextlib
import copy
import functools
import inspect
import os
import typing

import async_timeout
import mock
import pytest

# Value that is considered a reasonable time to wait for something asyncio-based
# to occur in the background. This is long enough that a shit computer will
# generally still be able to do some stuff with asyncio even if being tanked,
# but at the same time not so long that the tests take forever to run. I am
# aware waiting for anything in unit tests is evil, but there isn't really a
# good way to advance the state of an asyncio coroutine without manually
# iterating it, which I consider to be far more evil and will vary in results
# if unrelated changes are made in the same function.
REASONABLE_SLEEP_TIME = 0.2

# How long to reasonably expect something to take if it is considered instant.
REASONABLE_QUICK_RESPONSE_TIME = 0.2

# How long to wait for before considering a test to be jammed in an unbreakable
# condition, and thus acceptable to terminate the test and fail it.
REASONABLE_TIMEOUT_AFTER = 10

_T = typing.TypeVar("_T")


def mock_class_namespace(
    klass: typing.Type[_T],
    /,
    *,
    init_: bool = True,
    slots_: typing.Optional[bool] = None,
    implement_abstract_methods_: bool = True,
    rename_impl_: bool = True,
    **namespace: typing.Any,
) -> typing.Type[_T]:
    """Get a version of a class with the provided namespace fields set as class attributes."""
    if slots_ or slots_ is None and hasattr(klass, "__slots__"):
        namespace["__slots__"] = ()

    if init_ is False:
        namespace["__init__"] = lambda _: None

    if implement_abstract_methods_ and hasattr(klass, "__abstractmethods__"):
        for method_name in klass.__abstractmethods__:
            if method_name in namespace:
                continue

            attr = getattr(klass, method_name)

            if inspect.isdatadescriptor(attr) or inspect.isgetsetdescriptor(attr):
                # Do not use property mock here: it prevents us overwriting it later
                # (e.g. when restubbing for specific test cases)
                namespace[method_name] = mock.Mock(__isabstractmethod__=False)
            elif asyncio.iscoroutinefunction(attr):
                namespace[method_name] = mock.AsyncMock(spec_set=attr, __isabstractmethod__=False)
            else:
                namespace[method_name] = mock.Mock(spec_set=attr, __isabstractmethod__=False)

    for attribute in namespace.keys():
        assert hasattr(klass, attribute), f"invalid namespace attribute {attribute!r} provided"

    name = "Mock" + klass.__name__ if rename_impl_ else klass.__name__

    return type(name, (klass,), namespace)


def retry(max_retries):
    def decorator(func):
        assert asyncio.iscoroutinefunction(func), "retry only supports coroutine functions currently"

        @functools.wraps(func)
        async def retry_wrapper(*args, **kwargs):
            ex = None
            for i in range(max_retries + 1):
                if i:
                    print("retry", i, "of", max_retries)  # noqa: T001 - Print found
                try:
                    await func(*args, **kwargs)
                    return
                except AssertionError as exc:
                    ex = exc  # local variable 'ex' referenced before assignment: wtf?
            raise AssertionError(f"all {max_retries} retries failed") from ex

        return retry_wrapper

    return decorator


def timeout(time_period=REASONABLE_TIMEOUT_AFTER):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            thrown_timeout_error = None

            try:
                async with async_timeout.timeout(time_period):
                    try:
                        await func(*args, **kwargs)
                    except asyncio.TimeoutError as ex:
                        thrown_timeout_error = ex
            except asyncio.TimeoutError as ex:
                raise AssertionError(f"Test took too long (> {time_period}s) and thus failed.") from ex

            if thrown_timeout_error is not None:
                raise thrown_timeout_error

        return wrapper

    return decorator


def skip_on_system(os_name: str):
    """Skip a test on certain systems.

    The valid system names are based on `os.system`
    """

    def decorator(test):
        return pytest.mark.skipif(os.name == os_name, reason=f"This test will not pass on {os_name} systems")(test)

    return decorator


async def idle(for_=REASONABLE_SLEEP_TIME, /):
    await asyncio.sleep(for_)


@contextlib.contextmanager
def ensure_occurs_quickly():
    with async_timeout.timeout(REASONABLE_QUICK_RESPONSE_TIME):
        yield


class AsyncContextManagerMock:
    aenter_count = 0
    aexit_count = 0

    async def __aenter__(self):
        self.aenter_count += 1
        return self

    async def __aexit__(self, *args):
        self.aexit_count += 1

    def assert_used_once(self):
        assert self.aenter_count == 1
        assert self.aexit_count == 1


class CopyingAsyncMock(mock.AsyncMock):
    __slots__ = ()

    def __call__(self, *args, **kwargs):
        args = (copy.copy(arg) for arg in args)
        kwargs = {copy.copy(key): copy.copy(value) for key, value in kwargs.items()}
        return super().__call__(*args, **kwargs)
