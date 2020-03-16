#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekokatt 2019-2020
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
"""Provides mechanisms to cache results of calls lazily."""
__all__ = [
    "CachedFunctionT",
    "CachedPropertyFunctionT",
    "CachedFunction",
    "CachedProperty",
    "AsyncCachedProperty",
    "cached_function",
    "cached_property",
]

import asyncio
import functools
import inspect
import os
import typing

ReturnT = typing.TypeVar("ReturnT")
ClassT = typing.TypeVar("ClassT")
CallT = typing.Callable[..., ReturnT]
CachedFunctionT = typing.Callable[..., ReturnT]
CachedPropertyFunctionT = typing.Callable[[ClassT], ReturnT]

# Hacky workaround to Sphinx being unable to document cached properties. We simply make the
# decorators return their inputs when this is True.
__is_sphinx = os.getenv("SPHINX_IS_GENERATING_DOCUMENTATION") is not None


def __noop_decorator(func):  # pragma: no cover
    return func


class CachedFunction:
    """Wraps a call, some arguments, and some keyword arguments in a partial and stores the
    result of the call for later invocations.

    Warning
    -------
    This is not thread safe!
    """

    _sentinel = object()
    __slots__ = (
        "_call",
        "_value",
        "__qualname__",  # pylint: disable=class-variable-slots-conflict
        "__dict__",
        "__name__",
    )

    def __init__(self, call, args, kwargs):
        self._value = self._sentinel
        self.__qualname__ = getattr(call, "__qualname__", None)
        self.__name__ = getattr(call, "__name__", None)
        self.__dict__ = getattr(call, "__dict__", None)
        is_coro = inspect.iscoroutinefunction(call)
        call_wrapper = self._coroutine_fn_wrapper if is_coro else self._fn_wrapper
        self._call = call_wrapper(call, args, kwargs)

    def __call__(self) -> ReturnT:
        if self._value is self._sentinel:
            self._call()
        return self._value

    def _coroutine_fn_wrapper(self, call, args, kwargs):
        def fn_wrapper():
            self._value = asyncio.create_task(call(*args, **kwargs), name="pending CachedFunction coroutine completion")

        return fn_wrapper

    def _fn_wrapper(self, call, args, kwargs):
        def fn_wrapper():
            self._value = call(*args, **kwargs)

        return fn_wrapper


class CachedProperty:
    """A get/delete descriptor to wrap a no-args method which can cache the result of the
    call for future retrieval. Calling :func:`del` on the property will flush the cache.

    This will misbehave on class methods and static methods, and will not work on
    non-instance functions. For general functions, you should consider :obj:`CachedFunction`
    instead.
    """

    __slots__ = (
        "func",
        "_cache_attr",
        "__dict__",
        "__name__",
        "__qualname__",  # pylint: disable=class-variable-slots-conflict
    )

    def __init__(self, func: CachedPropertyFunctionT, cache_attr: typing.Optional[str]) -> None:
        self.func = func
        self._cache_attr = cache_attr or "_cp_" + func.__name__
        self.__dict__ = getattr(self.func, "__dict__", None)

    def __get__(self, instance: typing.Optional[ClassT], owner: typing.Type[ClassT]) -> ReturnT:
        if instance is None:
            return typing.cast(ReturnT, self)
        if not hasattr(instance, self._cache_attr):
            setattr(instance, self._cache_attr, self.func(instance))
        return getattr(instance, self._cache_attr)

    def __delete__(self, instance: ClassT):
        try:
            delattr(instance, self._cache_attr)
        except AttributeError:
            pass


class AsyncCachedProperty(CachedProperty):
    """Cached property implementation that supports awaitable coroutines."""

    __slots__ = ()

    def __get__(self, instance: typing.Optional[ClassT], owner: typing.Type[ClassT]) -> typing.Awaitable[ReturnT]:
        if instance is None:
            return typing.cast(ReturnT, self)

        if not hasattr(instance, self._cache_attr):
            setattr(
                instance,
                self._cache_attr,
                asyncio.create_task(self.func(instance), name="pending AsyncCachedProperty coroutine completion"),
            )
        return getattr(instance, self._cache_attr)


def cached_function(*args, **kwargs) -> typing.Callable[[CachedFunctionT], typing.Callable[[], ReturnT]]:
    """Create a wrapped cached call decorator. 
    
    This remembers the last result of the given call forever until cleared.

    Parameters
    -----------
    *args
        Any arguments to call the call with.
    **kwargs
        Any kwargs to call the call with.

    Note
    ----
    This is not useful for instance methods on classes, you should use
    a :obj:`CachedProperty` instead for those. You should also not expect
    thread safety here. Coroutines will be detected and dealt with as futures.
    This is lazily evaluated.
    """

    def decorator(func):
        return functools.wraps(func)(CachedFunction(func, args, kwargs))

    return decorator if not __is_sphinx else __noop_decorator


def cached_property(
    *, cache_name=None
) -> typing.Callable[[CachedPropertyFunctionT], typing.Union[CachedProperty, AsyncCachedProperty]]:
    """Makes a slots-compatible cached property.

    If using slots, you should specify the ``cache_name`` directly.
    """

    def decorator(func: CachedPropertyFunctionT) -> typing.Union[CachedProperty, AsyncCachedProperty]:
        cls = AsyncCachedProperty if asyncio.iscoroutinefunction(func) else CachedProperty
        return typing.cast(
            typing.Union[CachedProperty, AsyncCachedProperty], functools.wraps(func)(cls(func, cache_name))
        )

    return decorator if not __is_sphinx else __noop_decorator
