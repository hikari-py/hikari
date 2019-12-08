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
"""
Provides mechanisms to cache results of calls lazily.
"""
import functools


class CachedCall:
    """
    Wraps a call, some arguments, and some keyword arguments in a partial and stores the
    result of the call for later invocations.

    Warning:
         This is not thread safe!
    """

    _sentinel = object()
    __slots__ = ("_call", "_value", "__qualname__")

    def __init__(self, call, *args, **kwargs):
        self._call = functools.partial(call, *args, **kwargs)
        self._value = self._sentinel
        self.__qualname__ = getattr(call, "__qualname__", None)

    def __call__(self):
        if self._value is self._sentinel:
            self._value = self._call()
        return self._value

    @classmethod
    def wrap(cls, *args, **kwargs):
        """
        Create a wrapped cached call decorator.

        Args:
            *args:
                Any arguments to call the call with.
            **kwargs:
                Any kwargs to call the call with.
        """
        return lambda func: cls(func, *args, **kwargs)


cached_call = CachedCall.wrap
