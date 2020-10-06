# -*- coding: utf-8 -*-
# Copyright (c) 2020 Nekokatt
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


_stubbed_classes = {}


def _stub_init(self, kwargs: typing.Mapping[str, typing.Any]):
    for attr, value in kwargs.items():
        setattr(self, attr, value)


# TODO: replace all of these with mock_class_namespace
def mock_entire_class_namespace(klass, **kwargs: typing.Any):
    """Get an instance of a class with only attributes provided in the passed kwargs set."""
    if klass not in _stubbed_classes:
        namespace = {"__init__": _stub_init}

        if hasattr(klass, "__slots__"):
            namespace["__slots__"] = ()

        new_klass = type("Stub" + klass.__name__, (klass,), namespace)
    else:
        new_klass = _stubbed_classes[klass]

    return new_klass(kwargs)


def mock_class_namespace(
    klass,
    /,
    *,
    init_: bool = True,
    slots_: typing.Optional[bool] = None,
    implement_abstract_methods_: bool = True,
    rename_impl_: bool = True,
    **namespace: typing.Any,
):
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


def has_sem_open_impl():
    try:
        import multiprocessing

        multiprocessing.RLock()
    except ImportError:
        return False
    else:
        return True


def skip_if_no_sem_open(test):
    return pytest.mark.skipif(not has_sem_open_impl(), reason="Your platform lacks a sem_open implementation")(test)


async def idle(for_=REASONABLE_SLEEP_TIME, /):
    await asyncio.sleep(for_)


@contextlib.contextmanager
def ensure_occurs_quickly():
    with async_timeout.timeout(REASONABLE_QUICK_RESPONSE_TIME):
        yield


def assert_does_not_raise(type_=BaseException):
    def decorator(func):
        @pytest.mark.asyncio
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                await result if inspect.iscoroutine(result) else None
            except type_ as ex:
                assertion_error = AssertionError(
                    f"{type(ex).__name__} was raised, but the test case specified that "
                    f"any derivative of {type_.__name__} must never be raised in this scenario."
                )
                assertion_error.__cause__ = ex
                raise assertion_error from ex

        return wrapper

    if inspect.isfunction(type_) or inspect.ismethod(type_):
        decorated_func = type_
        type_ = BaseException
        return decorator(decorated_func)
    else:
        return decorator


async def gather_all_tasks():
    """Ensure all created tasks except the current are finished before asserting anything."""
    await asyncio.gather(*(task for task in asyncio.all_tasks() if task is not asyncio.current_task()))


def raiser(ex, should_raise=True):
    """Stop lints complaining about unreachable code."""
    if should_raise:
        raise ex


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
