#!/usr/bin/env python3
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
import copy
import functools
import inspect
import logging
import os
import queue
import re
import threading
import time
import typing
import warnings
import weakref

import async_timeout
import mock
import pytest

from hikari.models import bases

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

            setattr(copy_, name, _mock)

    for expr in also_mock:
        owner, _, attr = ("copy_." + expr).rpartition(".")
        # sue me.
        owner = eval(owner)
        setattr(owner, attr, mock.MagicMock())

    assert not (except_ - checked), f"Some attributes didn't exist, so were not mocked: {except_ - checked}"

    return copy_


def assert_raises(test=None, *, type_, checks=()):
    def decorator(test):
        @pytest.mark.asyncio
        @functools.wraps(test)
        async def impl(*args, **kwargs):
            try:
                result = test(*args, **kwargs)
                if asyncio.iscoroutine(result):
                    await result
                assert False, f"{type_.__name__} was not raised."
            except type_ as ex:
                logging.exception("Caught exception within test type raising bounds", exc_info=ex)
                for i, check in enumerate(checks, start=1):
                    assert check(ex), f"Check #{i} ({check}) failed"
            except AssertionError as ex:
                raise ex
            except BaseException as ex:
                raise AssertionError(f"Expected {type_.__name__} to be raised but got {type(ex).__name__}") from ex

        return impl

    if test is not None:
        return decorator(test)
    else:
        return decorator


def assert_does_not_raise(test=None, *, type_=Exception, excludes=(AssertionError,)):
    def decorator(test):
        @pytest.mark.asyncio
        @functools.wraps(test)
        async def impl(*args, **kwargs):
            try:
                result = test(*args, **kwargs)
                if asyncio.iscoroutine(result):
                    await result
            except type_ as ex:
                if not any(isinstance(ex, exclude) for exclude in excludes):
                    assert False, f"{type_.__qualname__} thrown unexpectedly"
                else:
                    raise ex

        return impl

    if test is not None:
        return decorator(test)
    else:
        return decorator


def fqn1(obj_):
    return obj_.__module__ + "." + obj_.__qualname__


def fqn2(module, item_identifier):
    return module.__name__ + "." + item_identifier


T = typing.TypeVar("T")


def _can_weakref(spec_set):
    for cls in spec_set.mro()[:-1]:
        if "__weakref__" in getattr(cls, "__slots__", ()):
            return True
    return False


def mock_model(spec_set: typing.Type[T] = object, hash_code_provider=None, **kwargs) -> T:
    # Enables type hinting for my own reference, and quick attribute setting.
    obj = mock.MagicMock(spec_set)
    for name, value in kwargs.items():
        setattr(obj, name, value)

    obj.__eq__ = lambda self, other: other is self
    obj.__ne__ = lambda self, other: other is not self
    obj.__hash__ = hash_code_provider or spec_set.__hash__

    special_attrs = ["__int__"]
    for attr in special_attrs:
        if hasattr(spec_set, attr):
            setattr(obj, attr, lambda *args, **kws: getattr(spec_set, attr)(*args, **kws))
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

    return mock.patch(fqn, *args, **kwargs)


class StrongWeakValuedDict(typing.MutableMapping):
    def __init__(self):
        self.strong = {}
        self.weak = weakref.WeakValueDictionary()

    def __setitem__(self, k, v) -> None:
        self.strong[k] = v
        self.weak[k] = v

    def __delitem__(self, k) -> None:
        del self.strong[k]

    def __getitem__(self, k):
        return self.strong[k]

    def __len__(self) -> int:
        assert len(self.strong) == len(self.weak)
        return len(self.strong)

    def __iter__(self) -> typing.Iterator:
        return iter(self.strong)


def _maybe_mock_type_name(value):
    # noinspection PyProtectedMember
    return (
        value._spec_class.__name__
        if any(mro.__name__ == "MagicMock" for mro in type(value).mro())
        else type(value).__name__
    )


def _parameterize_ids_id(param_name):
    def ids(param):
        type_name = type(param).__name__ if isinstance(param, (str, int)) else _maybe_mock_type_name(param)
        return f" type({param_name}) is {type_name} "

    return ids


def parametrize_valid_id_formats_for_models(param_name, id, model_type1, *model_types, **kwargs):
    """
    @pytest.mark.parameterize for a param that is an id-able object, but could be the ID in a string, the ID in an int,
    or the ID in a given model type...

    For example

    >>> @parametrize_valid_id_formats_for_models("guild", 1234, guilds.Guild, unavailable=False)

    ...would be the same as...

    >>> @pytest.mark.parametrize(
    ...     "guild",
    ...     [
    ...         1234,
    ...         snowflakes.Snowflake(1234),
    ...         mock_model(guilds.Guild, id=snowflakes.Snowflake(1234), unavailable=False)
    ...     ],
    ...     id=lambda ...: ...
    ... )

    These are stackable as long as the parameter name is unique, as expected.
    """
    model_types = [model_type1, *model_types]

    def decorator(func):
        mock_models = []
        for model_type in model_types:
            assert bases.Unique.__name__ in map(
                lambda mro: mro.__name__, model_type.mro()
            ), f"model must be a {bases.Unique.__name__} derivative"
            mock_models.append(mock_model(model_type, id=bases.Snowflake(id), **kwargs))

        return pytest.mark.parametrize(
            param_name, [int(id), bases.Snowflake(id), *mock_models], ids=_parameterize_ids_id(param_name)
        )(func)

    return decorator


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


def run_in_own_thread(func):
    assert not asyncio.iscoroutinefunction(func), "Cannot run coroutine in thread directly"

    @functools.wraps(func)
    def delegator(*args, **kwargs):
        q = queue.SimpleQueue()

        class Raiser:
            def __init__(self, ex):
                self.ex = ex

            def raise_again(self):
                raise self.ex

        def consumer():
            try:
                q.put(func(*args, **kwargs))
            except BaseException as ex:
                q.put(Raiser(ex))

        t = threading.Thread(target=consumer, daemon=True)
        t.start()
        t.join()
        result = q.get()
        if isinstance(result, Raiser):
            result.raise_again()

    return delegator


class AwaitableMock:
    def __init__(self, return_value=None):
        self.await_count = 0
        self.return_value = return_value

    def _is_exception(self, obj):
        return isinstance(obj, BaseException) or isinstance(obj, type) and issubclass(obj, BaseException)

    def __await__(self):
        if False:
            yield
        self.await_count += 1
        if self._is_exception(self.return_value):
            raise self.return_value
        return self.return_value

    def assert_awaited_once(self):
        assert self.await_count == 1

    def assert_not_awaited(self):
        assert self.await_count == 0

    is_resolved = False


class AsyncWithContextMock:
    def __init__(self, return_value=None):
        self.return_value = return_value

    async def __aenter__(self):
        return self.return_value

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


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


class AsyncContextManagerMock:
    def __init__(self, callback=lambda: None):
        self.awaited_aenter = False
        self.awaited_aexit = False
        self.called = False
        self.call_args = []
        self.call_kwargs = {}
        self.aexit_exc = None
        self.callback = callback

    async def __aenter__(self):
        self.awaited_aenter = time.perf_counter()
        return self.callback()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.aexit_exc = exc_val
        self.awaited_aexit = time.perf_counter()

    def __call__(self, *args, **kwargs):
        self.called = time.perf_counter()
        self.call_args = args
        self.call_kwargs = kwargs
        return self


def timeout_after(time_period):
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


def patch_marshal_attr(target_entity, field_name, *args, deserializer=None, serializer=None, **kwargs):
    if not (deserializer or serializer):
        raise TypeError("patch_marshal_attr() Missing required keyword-only argument: 'deserializer' or 'serializer'")
    if deserializer and serializer:
        raise TypeError(
            "patch_marshal_attr() Expected one of either keyword-arguments 'deserializer' or 'serializer', not both."
        )

    target_type = "deserializer" if deserializer else "serializer"
    # noinspection PyProtectedMember
    for attr in marshaller.HIKARI_ENTITY_MARSHALLER._registered_entities[target_entity].attribs:
        if attr.field_name == field_name and (serializer or deserializer) == getattr(attr, target_type):
            target = attr
            break
        elif attr.field_name == field_name:
            raise TypeError(
                f"{target_type.capitalize()} mismatch found on `{target_entity.__name__}"
                f".{attr.field_name}`; expected `{deserializer or serializer}` but got `{getattr(attr, target_type)}`."
            )
    else:
        raise LookupError(f"Failed to find a `{field_name}` field on `{target_entity.__name__}`.")
    return mock.patch.object(target, target_type, *args, **kwargs)


def min_python_version(*mmm):
    return pytest.mark.skipif(f"__import__('sys').version_info < {mmm!r}", reason="Unsupported for your Python version")


def max_python_version(*mmm):
    return pytest.mark.skipif(f"__import__('sys').version_info > {mmm!r}", reason="Unsupported for your Python version")


def set_private_attr(owner, name, value):
    setattr(owner, f"_{type(owner).__name__}__{name}", value)


def get_private_attr(owner, name, **kwargs):
    return getattr(owner, f"_{type(owner).__name__}__{name}", **kwargs)
