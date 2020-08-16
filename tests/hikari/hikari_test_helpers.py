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
REASONABLE_SLEEP_TIME = 0.05

# How long to reasonably expect something to take if it is considered instant.
REASONABLE_QUICK_RESPONSE_TIME = 0.05

# How long to wait for before considering a test to be jammed in an unbreakable
# condition, and thus acceptable to terminate the test and fail it.
REASONABLE_TIMEOUT_AFTER = 10


def mock_methods_on(obj, except_=(), also_mock=()):
    # Mock any methods we don't care about. also_mock is a collection of attribute names that we can eval to access
    # and mock specific application with a coroutine mock to mock other external application quickly :)
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
                _mock = mock.AsyncMock()
            else:
                _mock = mock.Mock()

            copy_.__dict__[name] = _mock

    for expr in also_mock:
        owner, _, attr = ("copy_." + expr).rpartition(".")
        # sue me.
        owner = eval(owner)
        setattr(owner, attr, mock.Mock())

    assert not (except_ - checked), f"Some attributes didn't exist, so were not mocked: {except_ - checked}"

    return copy_


def fqn1(obj_):
    return obj_.__module__ + "." + obj_.__qualname__


def fqn2(module, item_identifier):
    return module.__name__ + "." + item_identifier


_unslotted_classes = {}


def unslot_class(klass):
    """Get a modified version of a class without slots."""
    if klass not in _unslotted_classes:
        _unslotted_classes[klass] = type(klass.__name__ + "Unslotted", (klass,), {})
    return _unslotted_classes[klass]


_stubbed_classes = {}


def _stub_init(self, kwargs: typing.Mapping[str, typing.Any]):
    for attr, value in kwargs.items():
        setattr(self, attr, value)


def stub_class(klass, **kwargs: typing.Any):
    """Get an instance of a class with only attributes provided in the passed kwargs set."""
    if klass not in _stubbed_classes:
        namespace = {"__init__": _stub_init}

        if hasattr(klass, "__slots__"):
            namespace["__slots__"] = ()

        new_klass = type("Stub" + klass.__name__, (klass,), namespace)
    else:
        new_klass = _stubbed_classes[klass]

    return new_klass(kwargs)


def mock_class_namespace(klass, *, init: bool = True, slots: typing.Optional[bool] = None, **namespace: typing.Any):
    """Get a version of a class with the provided namespace fields set as class attributes."""
    if slots or slots is None and hasattr(klass, "__slots__"):
        namespace["__slots__"] = ()

    if init is False:
        namespace["__init__"] = lambda _: None

    return type("Mock" + klass.__name__, (klass,), namespace)


def retry(max_retries):
    def decorator(func):
        assert asyncio.iscoroutinefunction(func), "retry only supports coroutine functions currently"

        @functools.wraps(func)
        async def retry_wrapper(*args, **kwargs):
            ex = None
            for i in range(max_retries + 1):
                if i:
                    print("retry", i, "of", max_retries)
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


def stupid_windows_please_stop_breaking_my_tests(test):
    return pytest.mark.skipif(os.name == "nt", reason="This test will not pass on Windows :(")(test)


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


async def idle():
    await asyncio.sleep(REASONABLE_SLEEP_TIME)


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
