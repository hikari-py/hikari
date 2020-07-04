# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019-2020
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
import contextlib
import copy
import functools
import inspect
import os
import re
import warnings

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
REASONABLE_SLEEP_TIME = 0.5

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
                _mock = mock.MagicMock()

            copy_.__dict__[name] = _mock

    for expr in also_mock:
        owner, _, attr = ("copy_." + expr).rpartition(".")
        # sue me.
        owner = eval(owner)
        setattr(owner, attr, mock.MagicMock())

    assert not (except_ - checked), f"Some attributes didn't exist, so were not mocked: {except_ - checked}"

    return copy_


def fqn1(obj_):
    return obj_.__module__ + "." + obj_.__qualname__


def fqn2(module, item_identifier):
    return module.__name__ + "." + item_identifier


def unslot_class(klass):
    return type(klass.__name__ + "Unslotted", (klass,), {})


def mock_patch(what, *args, **kwargs):
    # If something refers to a strong reference, e.g. aiofiles.open is just a reference to aiofile.threadpool.open,
    # you will need to pass a string to patch it...
    if isinstance(what, str):
        fqn = what
    else:
        fqn = fqn1(what)

    return mock.patch(fqn, *args, **kwargs)


def todo_implement(fn=...):
    def decorator(fn):
        return pytest.mark.xfail(reason="Code for test case not yet implemented.")(fn)

    return fn is ... and decorator or decorator(fn)


class AssertWarns:
    def __init__(self, *, pattern=r".*", category=Warning):
        self.pattern = pattern
        self.category = category

    def __enter__(self):
        self.old_warning = warnings.warn_explicit
        self.mocked_warning = mock.MagicMock(warnings.warn)
        self.context = mock.patch("warnings.warn", new=self.mocked_warning)
        self.context.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.context.__exit__(exc_type, exc_val, exc_tb)

        calls = []
        for call_args, call_kwargs in self.mocked_warning.call_args_list:
            message, category = call_args[:2]
            calls.append((message, category))
            if re.search(self.pattern, message, re.I) and issubclass(category, self.category):
                self.matched = (message, category)
                return

        assert False, (
            f"No warning with message pattern /{self.pattern}/ig and category subclassing {self.category} "
            f"was found. There were {len(calls)} other warnings invoked in this time:\n"
            + "\n".join(f"Category: {c}, Message: {m}" for m, c in calls)
        )

    def matched_message_contains(self, pattern):
        assert re.search(pattern, self.matched[0], re.I), f"/{pattern}/ig does not match message {self.matched[0]!r}"


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


def set_private_attr(owner, name, value):
    setattr(owner, f"_{type(owner).__name__}__{name}", value)


def get_private_attr(owner, name, **kwargs):
    return getattr(owner, f"_{type(owner).__name__}__{name}", **kwargs)


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
